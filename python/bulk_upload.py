"""Bulk Upload: create a datasource, upload a folder of files concurrently, ingest, report timing."""

import asyncio
import os
import time
from pathlib import Path

from meibel import AsyncMeibelClient

FOLDER = Path(os.environ["UPLOAD_FOLDER"])
MAX_CONCURRENT = int(os.environ.get("UPLOAD_CONCURRENCY", "20"))


async def main():
    client = AsyncMeibelClient(api_key=os.environ["MEIBEL_API_KEY"])

    # Collect PDF files
    files = sorted(FOLDER.glob("*.pdf"))
    total_bytes = sum(f.stat().st_size for f in files)
    print(f"Found {len(files)} PDFs ({total_bytes / 1024 / 1024:.1f} MB) in {FOLDER.name}")

    # ── 1. Create empty datasource ───────────────────────────────────────────

    t0 = time.time()

    ds = await client.datasources.create(
        name=f"SDK Bulk Upload — {FOLDER.name}",
        description=f"{len(files)} PDFs uploaded via SDK bulk_upload example",
    )
    datasource_id = ds.id
    print(f"\nCreated datasource: {datasource_id} ({time.time() - t0:.1f}s)")

    # ── 2. Upload files concurrently ─────────────────────────────────────────

    t_upload_start = time.time()
    uploaded = 0
    failed = 0
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    async def upload_one(filepath: Path) -> bool:
        nonlocal uploaded, failed
        async with semaphore:
            try:
                with open(filepath, "rb") as f:
                    await client.datasources.file_uploads.upload_content(
                        files=f,
                        files_name=filepath.name,
                        datasource_id=datasource_id,
                    )
                uploaded += 1
                return True
            except Exception as e:
                failed += 1
                print(f"  FAILED {filepath.name}: {e}")
                return False

    # Launch all uploads concurrently (bounded by semaphore)
    print(f"\nUploading {len(files)} files (concurrency={MAX_CONCURRENT})...")
    tasks = [upload_one(f) for f in files]

    # Report progress while uploads run
    gather_task = asyncio.ensure_future(asyncio.gather(*tasks))
    while not gather_task.done():
        await asyncio.sleep(1)
        elapsed = time.time() - t_upload_start
        rate = uploaded / elapsed if elapsed > 0 else 0
        print(f"  {uploaded}/{len(files)} uploaded ({rate:.1f} files/s)", end="\r")
    await gather_task

    t_upload_end = time.time()
    upload_duration = t_upload_end - t_upload_start
    print(f"\n\nUpload complete: {uploaded} succeeded, {failed} failed")
    print(f"  {upload_duration:.1f}s ({uploaded / upload_duration:.1f} files/s)")

    # ── 3. Trigger ingestion ─────────────────────────────────────────────────

    t_ingest_start = time.time()
    await client.datasources.ingest.trigger(datasource_id=datasource_id)
    print("\nIngestion triggered")

    # ── 4. Poll for ingestion completion ─────────────────────────────────────

    max_ingest_wait = 600
    while True:
        status = await client.datasources.ingest.get_status(datasource_id=datasource_id)
        elapsed = time.time() - t_ingest_start
        raw = status.status.value if hasattr(status.status, "value") else str(status.status)
        print(f"  Status: {raw} ({elapsed:.0f}s)")
        if raw in ("completed", "failed", "canceled", "timed_out", "terminated"):
            break
        if elapsed > max_ingest_wait:
            print(f"  Timed out waiting after {max_ingest_wait}s")
            break
        await asyncio.sleep(5)

    t_ingest_end = time.time()
    ingest_duration = t_ingest_end - t_ingest_start
    final = status.status.value if hasattr(status.status, "value") else str(status.status)
    print(f"\nIngestion complete: {final}")
    print(f"  {ingest_duration:.1f}s")

    # ── 5. Verify data elements ──────────────────────────────────────────────

    element_count = 0
    elements = await client.datasources.data_elements.list(datasource_id=datasource_id)
    async for _ in elements:
        element_count += 1
    print(f"\nData elements: {element_count}")

    # ── 6. Summary ───────────────────────────────────────────────────────────

    total_duration = time.time() - t0
    mb = total_bytes / 1024 / 1024
    print(f"\n{'=' * 50}")
    print(f"  Files:       {len(files)} ({mb:.1f} MB)")
    print(f"  Uploaded:    {uploaded}")
    print(f"  Upload:      {upload_duration:.1f}s ({uploaded / upload_duration:.1f} files/s, {mb / upload_duration:.1f} MB/s)")
    print(f"  Ingest:      {ingest_duration:.1f}s")
    print(f"  Total:       {total_duration:.1f}s")
    print(f"  DS ID:       {datasource_id}")
    print(f"{'=' * 50}")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
