#!/usr/bin/env python3
"""
Two new document endpoints in the Meibel Python SDK, using the STRONGLY TYPED
Parse schema throughout -- no dict access, no getattr, no stringly-typed
labels. Every field below is a typed attribute your IDE and type checker know
about.

  1. client.documents.get_structured_result(job_id) -> ParseStructuredDocument
     GET /documents/{job_id}/structured
     Pages, typed elements, a layout-label enum, float bounding boxes, and
     typed chart/table sub-structures.

  2. client.documents.move(MoveDocumentsRequest(...)) -> MoveDocumentsResponse
     POST /documents/move

This example reuses an EXISTING parse job id -- it does not parse from scratch.

Usage:
    export MEIBEL_API_KEY="..."
    export JOB_ID="<an existing parse job id>"
    python structured_and_move.py
"""

import os
import sys
from collections import Counter

from meibel import MeibelClient
from meibel.models import (
    MoveDocumentsRequest,
    MoveDocumentsResponse,
    ParseBBox,
    ParseDocumentElement,
    ParseLayoutLabel,
    ParseStructuredDocument,
    ParseStructuredPage,
)


def fmt_bbox(bbox: ParseBBox) -> str:
    """ParseBBox has typed float corners -- x0/y0/x1/y1, not a dict."""
    return f"[{bbox.x0:7.1f}, {bbox.y0:7.1f}, {bbox.x1:7.1f}, {bbox.y1:7.1f}]"


def describe_element(element: ParseDocumentElement) -> None:
    # `label` is the ParseLayoutLabel enum -- compare against members, not strings.
    heading = f" H{element.heading_level}" if element.heading_level is not None else ""
    print(
        f"    #{element.reading_order:<2} {element.label.value:<14}{heading:<4} "
        f"conf={element.confidence:.2f}  bbox={fmt_bbox(element.bbox)}"
    )

    # Typed drill-down: chart_data / table are their own models, present only
    # for the matching label. The enum drives the branch.
    if element.label == ParseLayoutLabel.CHART and element.chart_data:
        cd = element.chart_data
        print(
            f"         chart: {cd.chart_type.value} ({cd.modality.value}), "
            f"{len(cd.series)} series, overall_conf={cd.overall_confidence:.2f}"
        )
    elif element.label == ParseLayoutLabel.TABLE and element.table:
        tbl = element.table
        print(f"         table: {tbl.num_rows}x{tbl.num_cols}, {len(tbl.cells)} cells")


def main() -> int:
    api_key = os.environ.get("MEIBEL_API_KEY")
    job_id = os.environ.get("JOB_ID")
    if not api_key or not job_id:
        print("Set MEIBEL_API_KEY and JOB_ID in your environment.", file=sys.stderr)
        return 1

    client = MeibelClient(api_key=api_key)

    # 1. Structured result -- fully typed ParseStructuredDocument -----------
    print(f"GET /documents/{job_id}/structured")
    doc: ParseStructuredDocument = client.documents.get_structured_result(job_id)

    # `confidence` is a ParseConfidenceScores model, not a dict.
    c = doc.confidence
    print(f"  format={doc.format}  gpu_ms={doc.gpu_ms}  num_pages={doc.num_pages}")
    print(
        f"  confidence: mean={c.mean_layout_confidence:.3f} "
        f"min={c.min_layout_confidence:.3f} "
        f"elements={c.num_elements} tables={c.num_tables}"
    )

    # Count elements by the enum itself (keys are ParseLayoutLabel members).
    by_label: Counter[ParseLayoutLabel] = Counter(
        element.label for page in doc.pages for element in page.elements
    )
    print("  elements by label:")
    for label, count in by_label.most_common():
        print(f"    {label.name:16} {count}")

    # Walk pages -> elements, all typed.
    page: ParseStructuredPage
    for page in doc.pages:
        size = f"{page.image_size[0]}x{page.image_size[1]}px" if page.image_size else "?"
        print(f"\n  page {page.page_number} ({size}, {len(page.elements)} elements)")
        for element in page.elements:
            describe_element(element)

    # 2. Move -- typed request in, typed response out --------------------------
    ds_name = "sdk-example-move"
    print(f"\nPOST /documents/move  (job {job_id} -> new datasource {ds_name!r})")
    moved: MoveDocumentsResponse = client.documents.move(
        MoveDocumentsRequest(documents=[job_id], new_datasource_name=ds_name)
    )
    print(
        f"  datasource_id={moved.datasource_id}  "
        f"workflow_id={moved.workflow_id}  count={moved.documents_count}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
