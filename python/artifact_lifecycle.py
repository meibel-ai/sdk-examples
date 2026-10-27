"""Artifact Lifecycle: create schemas of every type, with and without Pydantic models."""

import os
from typing import List, Optional

from pydantic import BaseModel, Field

from meibel import MeibelClient
from meibel.models import UpdateAgentArtifactRequest

client = MeibelClient(
    api_key=os.environ["MEIBEL_API_KEY"],
)

created_ids = []


# ── JSON with Pydantic model ─────────────────────────────────────────────────

class ContractSummary(BaseModel):
    """Structured contract analysis output."""
    parties: List[str] = Field(description="Names of all contracting parties")
    effective_date: str = Field(description="Contract effective date (YYYY-MM-DD)")
    expiration_date: Optional[str] = Field(default=None, description="Contract expiration date")
    key_obligations: List[str] = Field(description="Main obligations of each party")
    governing_law: str = Field(description="Jurisdiction governing the contract")


print("=== JSON artifact (Pydantic) ===")
schema = client.artifact_schemas.create(
    display_name="Contract Summary 2",
    schema=ContractSummary,
    description="Structured summary extracted from legal contracts",
)

print(f"  Created: {schema.name} (id: {schema.id})")
created_ids.append(schema.id)


# ── JSON with raw dict ────────────────────────────────────────────────────────

print("\n=== JSON artifact (raw dict) ===")
schema = client.artifact_schemas.create(
    display_name="Invoice Line Items",
    schema={
        "type": "object",
        "properties": {
            "vendor": {"type": "string", "description": "Vendor name"},
            "line_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "quantity": {"type": "number"},
                        "unit_price": {"type": "number"},
                    },
                },
            },
            "total": {"type": "number", "description": "Invoice total"},
        },
    },
    description="Line items extracted from invoices",
)
print(f"  Created: {schema.name} (id: {schema.id})")
created_ids.append(schema.id)


# ── CSV with Pydantic model ───────────────────────────────────────────────────

class SalesRow(BaseModel):
    """A single row of sales data."""
    region: str = Field(description="Sales region")
    product: str = Field(description="Product name")
    revenue: float = Field(description="Revenue amount in USD")
    units_sold: int = Field(description="Number of units sold")


print("\n=== CSV artifact (Pydantic) ===")
schema = client.artifact_schemas.create(
    display_name="Sales Report",
    schema=SalesRow,
    type="csv",
    description="Weekly sales data by region and product",
)
print(f"  Created: {schema.name} (id: {schema.id})")
created_ids.append(schema.id)


# ── CSV with raw dict ─────────────────────────────────────────────────────────

print("\n=== CSV artifact (raw dict) ===")
schema = client.artifact_schemas.create(
    display_name="Inventory Check",
    schema={
        "type": "object",
        "properties": {
            "sku": {"type": "string", "description": "Stock keeping unit"},
            "location": {"type": "string", "description": "Warehouse location"},
            "quantity_on_hand": {"type": "integer", "description": "Current stock"},
            "reorder_needed": {"type": "boolean", "description": "Whether reorder is needed"},
        },
    },
    type="csv",
    description="Inventory status per warehouse location",
)
print(f"  Created: {schema.name} (id: {schema.id})")
created_ids.append(schema.id)


# ── YAML with Pydantic model ─────────────────────────────────────────────────

class DeploymentConfig(BaseModel):
    """Kubernetes deployment configuration."""
    service_name: str = Field(description="Name of the service")
    replicas: int = Field(description="Number of replicas")
    image: str = Field(description="Container image with tag")
    env_vars: Optional[List[str]] = Field(default=None, description="Environment variables")
    resource_limits: Optional[str] = Field(default=None, description="CPU/memory limits")


print("\n=== YAML artifact (Pydantic) ===")
schema = client.artifact_schemas.create(
    display_name="Deployment Config",
    schema=DeploymentConfig,
    type="yaml",
    description="Generated k8s deployment config from requirements",
)
print(f"  Created: {schema.name} (id: {schema.id})")
created_ids.append(schema.id)


# ── YAML with raw dict ───────────────────────────────────────────────────────

print("\n=== YAML artifact (raw dict) ===")
schema = client.artifact_schemas.create(
    display_name="CI Pipeline",
    schema={
        "type": "object",
        "properties": {
            "stages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "script": {"type": "string"},
                        "timeout_minutes": {"type": "integer"},
                    },
                },
            },
            "trigger": {"type": "string", "description": "Branch or tag trigger"},
        },
    },
    type="yaml",
    description="CI/CD pipeline config generated from project analysis",
)
print(f"  Created: {schema.name} (id: {schema.id})")
created_ids.append(schema.id)


# ── Markdown (freeform, no schema) ────────────────────────────────────────────

print("\n=== Markdown artifact (no schema) ===")
schema = client.artifact_schemas.create(
    display_name="Executive Summary",
    schema={},
    type="markdown",
    description="Free-form executive summary report",
)
print(f"  Created: {schema.name} (id: {schema.id})")
created_ids.append(schema.id)


# ── List, update, verify ─────────────────────────────────────────────────────

print("\n=== All artifact schemas ===")
for s in client.artifact_schemas.list():
    print(f"  - [{s.type}] {s.name}: {s.description}")

# Update one
print(f"\n=== Updating first schema ===")
updated = client.artifact_schemas.update(
    artifact_id=created_ids[0],
    body=UpdateAgentArtifactRequest(
        description="Structured summary extracted from legal contracts — updated",
    ),
)
print(f"  Updated version: {updated.version}")

# Get details
retrieved = client.artifact_schemas.get(artifact_id=created_ids[0])
print(f"  Verified: {retrieved.display_name} — {retrieved.description}")


# ── Cleanup ───────────────────────────────────────────────────────────────────

print(f"\n=== Cleanup ({len(created_ids)} schemas) ===")
for aid in created_ids:
    client.artifact_schemas.delete(artifact_id=aid)
    print(f"  Deleted: {aid}")

print("\nDone.")
