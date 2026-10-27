"""Document Transform: three ways to extract structured data from a document.

Demonstrates client.documents.transform() with:
  1. A Pydantic model (auto-converts to JSON Schema)
  2. A raw JSON Schema dict
  3. A registered artifact schema, referenced by name
Plus an async variant.

The document is a public IPEX ball valve product data sheet, so this runs end
to end with only MEIBEL_API_KEY set.

Usage:
    export MEIBEL_API_KEY="..."
    python document_transform.py
"""

import asyncio
import os
import urllib.request
from typing import List, Optional

from pydantic import BaseModel, Field

from meibel import AsyncMeibelClient, MeibelClient

SPEC_URL = "https://ipexna.com/wp-content/uploads/2022/08/product-data-us-ipex-mp.pdf"
FILE = "valve-spec.pdf"

client = MeibelClient(api_key=os.environ["MEIBEL_API_KEY"], timeout=600.0)


# A list of objects: one entry per part-number row on the sheet.
class PartNumber(BaseModel):
    size: Optional[str] = Field(default=None, description="Nominal valve size in inches")
    body_material: Optional[str] = Field(default=None, description="Body material, e.g. Sch 40 PVC")
    ips_socket_part_number: Optional[str] = Field(default=None, description="IPS socket part number")
    fnpt_threaded_part_number: Optional[str] = Field(default=None, description="FNPT threaded part number")


class ValveParts(BaseModel):
    part_numbers: Optional[List[PartNumber]] = Field(
        default=None, description="One entry per part-number row on the sheet"
    )


def show(data: dict) -> None:
    parts = data.get("part_numbers") or []
    print(f"  {len(parts)} part numbers")
    for p in parts[:3]:
        print(f"    {p.get('size')} {p.get('body_material')}: IPS {p.get('ips_socket_part_number')}")


def main() -> int:
    urllib.request.urlretrieve(SPEC_URL, FILE)
    try:
        # Way 1: Pydantic model — the most ergonomic approach ----------------
        print("=== Way 1: Pydantic model ===")
        result = client.documents.transform(file=FILE, schema=ValveParts)
        parsed = ValveParts.model_validate(result.data)
        print(f"  validated {len(parsed.part_numbers or [])} part numbers")
        show(result.data)

        # Way 2: Raw JSON Schema dict — for dynamic/external schemas ---------
        json_schema = {
            "type": "object",
            "properties": {
                "part_numbers": {
                    "type": "array",
                    "description": "One entry per part-number row on the sheet",
                    "items": {
                        "type": "object",
                        "properties": {
                            "size": {"type": "string", "description": "Nominal valve size in inches"},
                            "body_material": {"type": "string", "description": "Body material, e.g. Sch 40 PVC"},
                            "ips_socket_part_number": {"type": "string", "description": "IPS socket part number"},
                            "fnpt_threaded_part_number": {"type": "string", "description": "FNPT threaded part number"},
                        },
                    },
                },
            },
            "additionalProperties": False,
        }
        print("\n=== Way 2: Raw JSON Schema dict ===")
        result = client.documents.transform(file=FILE, schema=json_schema)
        print(f"  execution: {result.execution_id}")
        show(result.data)

        # Way 3: Registered artifact schema, referenced by name -------------
        # transform() resolves a string schema reference by NAME (or a "urn:"
        # catalog URN), never by the UUID id — so pass created.name.
        created = client.artifact_schemas.create(
            display_name="Valve Part Numbers",
            schema=json_schema,
            description="Part-number rows extracted from a valve product data sheet",
        )
        print("\n=== Way 3: Registered artifact schema (by name) ===")
        print(f"  registered: id={created.id} name={created.name}")
        try:
            result = client.documents.transform(file=FILE, schema=created.name)
            print(f"  execution: {result.execution_id}")
            show(result.data)
        finally:
            client.artifact_schemas.delete(artifact_id=created.id)
            print(f"  deleted artifact schema {created.id}")

        # Async variant — same methods, just awaitable ----------------------
        async def transform_async() -> None:
            async with AsyncMeibelClient(
                api_key=os.environ["MEIBEL_API_KEY"], timeout=600.0
            ) as async_client:
                result = await async_client.documents.transform(
                    file=FILE, schema=ValveParts
                )
                show(result.data)

        print("\n=== Async variant ===")
        asyncio.run(transform_async())

        return 0
    finally:
        if os.path.exists(FILE):
            os.remove(FILE)


if __name__ == "__main__":
    raise SystemExit(main())
