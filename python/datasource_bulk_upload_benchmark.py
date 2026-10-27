"""Benchmark: massively parallel file upload to a single datasource.

Measures how long it takes to upload every file under a directory tree to one
datasource, using the async SDK client with a bounded concurrency pool.

Usage:
    MEIBEL_API_KEY=... python datasource_bulk_upload_benchmark.py \
        --dir ./my-files \
        [--concurrency 32] \
        [--keep]            # don't delete the datasource afterwards
"""

import argparse
import asyncio
import io
import os
import time
from pathlib import Path

from meibel import AsyncMeibelClient

DEFAULT_CONCURRENCY = 32


def collect_files(root: Path) -> list[Path]:
    """All regular files under root (skipping dotfiles like .DS_Store), sorted."""
    return sorted(
        p for p in root.rglob("*")
        if p.is_file() and not any(part.startswith(".") for part in p.relative_to(root).parts)
    )


def upload_name(path: Path, root: Path) -> str:
    """Relative path used as the content path inside the datasource.

    Filenames repeat across subdirs (e.g. every cik=* dir has facts.csv), so we
    send the full relative path (e.g. cik=40545/facts.csv). The server keeps
    this as the content path, preserving the folder structure — list_content's
    `prefix` filter then lets you browse it by directory.
    """
    return path.relative_to(root).as_posix()


async def await_upload_complete(client: AsyncMeibelClient, upload_id: str,
                                timeout: float = 180.0) -> None:
    """Consume the upload's progress stream until the ProgressTracker reports
    stream_complete. This is the authoritative "this upload finished persisting"
    signal — far better than polling list_content.

    The server replays stored events on connect (and emits stream_complete
    immediately if the upload already finished), so attaching after a fast
    upload won't hang. The wait_for timeout is defense-in-depth; the real edge
    is the tracker's 6h Redis TTL — attach later than that and the progress
    endpoint 404s (raises, not hangs)."""
    async def _consume() -> None:
        async for ev in await client.datasources.file_uploads.stream_upload_progress(upload_id):
            try:
                data = ev.json() if ev.data else {}
            except Exception:  # noqa: BLE001 - tolerate non-JSON keep-alives
                data = {}
            etype = data.get("type") or ev.event
            if etype in ("stream_complete", "complete"):
                return
            if etype == "error":
                raise RuntimeError(data.get("message") or data.get("detail") or "upload processing error")
    await asyncio.wait_for(_consume(), timeout=timeout)


async def list_all_files(client: AsyncMeibelClient, datasource_id: str,
                         prefix: str | None = None) -> list[str]:
    """Recursively enumerate every file path in the datasource. list_content is
    not recursive — it returns the immediate children of a prefix — so we walk
    into each directory entry."""
    paths: list[str] = []
    async for item in await client.datasources.file_uploads.list_content(
        datasource_id=datasource_id, prefix=prefix
    ):
        if item.type == "directory":
            paths.extend(await list_all_files(client, datasource_id, prefix=item.path))
        else:
            paths.append(item.path)
    return paths


async def print_content_tree(client: AsyncMeibelClient, datasource_id: str,
                             sample_per_dir: int = 3) -> None:
    """Render the recorded folder structure from a recursive content listing."""
    all_paths = await list_all_files(client, datasource_id)
    tree: dict[str, list[str]] = {}
    for path in all_paths:
        top, _, rest = path.partition("/")
        if rest:
            tree.setdefault(top, []).append(rest)
        else:
            tree.setdefault("(root)", []).append(top)

    print("\n" + "=" * 50)
    print(f"DATASOURCE CONTENT ({len(all_paths)} files, {len(tree)} top-level folders)")
    print("=" * 50)
    for top in sorted(tree):
        children = sorted(tree[top])
        print(f"{top}/  ({len(children)} files)")
        for child in children[:sample_per_dir]:
            print(f"    {child}")
        if len(children) > sample_per_dir:
            print(f"    ... and {len(children) - sample_per_dir} more")


async def upload_one(
    client: AsyncMeibelClient,
    sem: asyncio.Semaphore,
    path: Path,
    root: Path,
    datasource_id: str,
) -> tuple[Path, float, float, int, Exception | None]:
    """Upload a single file, then wait on its progress stream until the server
    reports completion. Returns (path, accept_latency, complete_latency, size, error):
    accept = streaming upload finished; complete = server-side persistence done.
    """
    name = upload_name(path, root)
    size = path.stat().st_size
    # Read off the event loop so disk I/O doesn't serialize the uploads.
    data = await asyncio.to_thread(path.read_bytes)
    start = time.perf_counter()
    try:
        # The semaphore gates only the upload itself, so the per-file
        # persistence wait (below) doesn't tie up an upload slot — that keeps a
        # full `concurrency` uploads genuinely in flight.
        async with sem:
            resp = await client.datasources.file_uploads.upload_content(
                datasource_id=datasource_id,
                files=io.BytesIO(data),
                files_name=name,
            )
        accept = time.perf_counter() - start
        # Completion wait runs outside the upload slot.
        await await_upload_complete(client, resp.upload_id)
        return path, accept, time.perf_counter() - start, size, None
    except Exception as exc:  # noqa: BLE001 - benchmark records, doesn't crash
        elapsed = time.perf_counter() - start
        return path, elapsed, elapsed, size, exc


async def run(directory: str, concurrency: int, keep: bool,
              limit: int | None = None) -> None:
    root = Path(directory)
    if not root.is_dir():
        raise SystemExit(f"Not a directory: {root}")

    files = collect_files(root)
    if limit is not None:
        files = files[:limit]
        print(f"[sample run] limiting to first {len(files)} files\n")
    total_bytes = sum(p.stat().st_size for p in files)
    if not files:
        raise SystemExit(f"No files found under {root}")

    print(f"Directory:    {root}")
    print(f"Files:        {len(files)}")
    print(f"Total size:   {total_bytes / 1024 / 1024:.1f} MiB")
    print(f"Concurrency:  {concurrency}")
    print()

    client = AsyncMeibelClient(
        api_key=os.environ["MEIBEL_API_KEY"],
        base_url=os.environ.get("MEIBEL_BASE_URL", "https://api.meibel.ai/v2"),
        timeout=300.0,
    )

    # Create the datasource up front (create-on-upload was removed), then fan
    # out all uploads against its id. Datasource creation is not part of the
    # upload timing — the wall clock starts once the fan-out begins.
    created = await client.datasources.create(
        name=f"bulk-upload-benchmark {root.name}",
        description="Throughput benchmark — safe to delete.",
    )
    datasource_id = created.id
    print(f"Datasource:   {datasource_id}\n")

    wall_start = time.perf_counter()

    sem = asyncio.Semaphore(concurrency)
    tasks = [upload_one(client, sem, p, root, datasource_id) for p in files]

    done = 0
    accept_latencies: list[float] = []
    complete_latencies: list[float] = []
    failures: list[tuple[Path, Exception]] = []
    uploaded_bytes = 0

    for coro in asyncio.as_completed(tasks):
        path, accept, complete, size, err = await coro
        done += 1
        if err is None:
            accept_latencies.append(accept)
            complete_latencies.append(complete)
            uploaded_bytes += size
        else:
            failures.append((path, err))
        if done % 25 == 0 or done == len(tasks):
            print(f"  {done}/{len(files)} done ({len(failures)} failed)")

    wall = time.perf_counter() - wall_start
    ok = len(files) - len(failures)

    def pctl(xs: list[float], q: float) -> float:
        return sorted(xs)[min(int(len(xs) * q), len(xs) - 1)]

    print("\n" + "=" * 50)
    print("RESULTS")
    print("=" * 50)
    print(f"Total wall time:    {wall:.2f} s  (upload + server-side persistence)")
    print(f"Files completed:    {ok}/{len(files)}")
    print(f"Throughput:         {ok / wall:.1f} files/s | {uploaded_bytes / 1024 / 1024 / wall:.2f} MiB/s")
    if accept_latencies:
        print(f"Upload (accept):    "
              f"median {pctl(accept_latencies, 0.5):.2f}s | p95 {pctl(accept_latencies, 0.95):.2f}s | max {max(accept_latencies):.2f}s")
    if complete_latencies:
        print(f"End-to-end (done):  "
              f"median {pctl(complete_latencies, 0.5):.2f}s | p95 {pctl(complete_latencies, 0.95):.2f}s | max {max(complete_latencies):.2f}s")
    if failures:
        print(f"\n{len(failures)} failures (showing up to 10):")
        for path, err in failures[:10]:
            print(f"  - {path.name}: {type(err).__name__}: {err}")

    # All uploads reported stream_complete, so the content is fully persisted.
    try:
        await print_content_tree(client, datasource_id)
    except Exception as exc:  # noqa: BLE001 - don't crash the report on a flaky gateway
        print(f"\n(could not list content: {type(exc).__name__}: {exc})")

    if not keep:
        print(f"\nDeleting datasource {datasource_id} ...")
        await client.datasources.delete(datasource_id=datasource_id)
        print("Deleted.")
    else:
        print(f"\nKept datasource {datasource_id} (--keep).")

    await client.close()


async def list_only(datasource_id: str) -> None:
    """List a datasource's content store — no uploading. Ground-truth check."""
    client = AsyncMeibelClient(
        api_key=os.environ["MEIBEL_API_KEY"],
        base_url=os.environ.get("MEIBEL_BASE_URL", "https://api.meibel.ai/v2"),
        timeout=60.0,
    )
    print(f"Listing content of datasource {datasource_id} ...\n")
    count = 0
    async for item in await client.datasources.file_uploads.list_content(
        datasource_id=datasource_id
    ):
        count += 1
        print(f"  {item.path}  ({item.size} bytes, type={item.type})")
    print(f"\nTotal content items: {count}")
    await client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", required=True, help="Directory to upload")
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY,
                        help="Max simultaneous uploads")
    parser.add_argument("--keep", action="store_true",
                        help="Do not delete the datasource when done")
    parser.add_argument("--limit", type=int, default=None,
                        help="Only upload the first N files (quick sample run)")
    parser.add_argument("--list", metavar="DATASOURCE_ID", default=None,
                        help="List a datasource's content and exit (no upload)")
    args = parser.parse_args()
    if args.list:
        asyncio.run(list_only(args.list))
    else:
        asyncio.run(run(args.dir, args.concurrency, args.keep, args.limit))


if __name__ == "__main__":
    main()