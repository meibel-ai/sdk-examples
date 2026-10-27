"""Artifact Schema: define typed output schemas for agents using Pydantic models."""

import os
from pydantic import BaseModel, Field
from typing import Optional, List

from meibel import MeibelClient, artifact_schema_from_model

client = MeibelClient(
    api_key=os.environ["MEIBEL_API_KEY"],
)

# ---------------------------------------------------------------------------
# Example 1: JSON artifact from a Pydantic model
# ---------------------------------------------------------------------------

class InvoiceOutput(BaseModel):
    """Structured invoice extraction result."""
    vendor_name: str = Field(description="Name of the vendor or supplier")
    invoice_number: str = Field(description="Invoice reference number")
    total_amount: float = Field(description="Total amount due")
    currency: str = Field(description="ISO 4217 currency code")
    due_date: Optional[str] = Field(default=None, description="Payment due date (YYYY-MM-DD)")
    line_items: List[str] = Field(description="Extracted line item descriptions")

json_request = artifact_schema_from_model(
    InvoiceOutput,
    display_name="Invoice Output",
    description="Structured invoice data extracted from documents",
    required=True,
)
print("JSON artifact schema_def:")
print(json_request.schema_def)
print()

# ---------------------------------------------------------------------------
# Example 2: CSV artifact — fields flattened to columns
# ---------------------------------------------------------------------------

class ContactRow(BaseModel):
    """A single contact record for CSV export."""
    name: str = Field(description="Full name")
    email: str = Field(description="Email address")
    company: str = Field(description="Company name")
    title: Optional[str] = Field(default=None, description="Job title")

csv_request = artifact_schema_from_model(
    ContactRow,
    display_name="Contact List",
    type="csv",
    description="Extracted contact information as CSV",
)
print("CSV artifact schema_def:")
print(csv_request.schema_def)
print()

# ---------------------------------------------------------------------------
# Example 3: Markdown artifact with structured sections
# ---------------------------------------------------------------------------

class AnalysisReport(BaseModel):
    """Structured analysis report."""
    executive_summary: str = Field(description="High-level summary of findings")
    methodology: str = Field(description="Approach and methods used")
    key_findings: str = Field(description="Detailed findings and observations")
    recommendations: str = Field(description="Actionable recommendations")

markdown_request = artifact_schema_from_model(
    AnalysisReport,
    display_name="Analysis Report",
    type="markdown",
    description="Structured analysis report with sections",
)
print("Markdown artifact schema_def:")
print(markdown_request.schema_def)
print()

# ---------------------------------------------------------------------------
# Example 4: Freeform markdown — no model, agent has full discretion
# ---------------------------------------------------------------------------

freeform_request = artifact_schema_from_model(
    display_name="Exploration Notes",
    type="markdown",
    description="Open-ended exploration and research notes",
)
print("Freeform markdown schema_def:")
print(freeform_request.schema_def)
print()

# ---------------------------------------------------------------------------
# Example 5: Nested model — demonstrates recursive schema generation
# ---------------------------------------------------------------------------

class Address(BaseModel):
    street: str = Field(description="Street address")
    city: str = Field(description="City")
    state: str = Field(description="State or province")
    zip_code: str = Field(description="ZIP or postal code")

class CustomerProfile(BaseModel):
    """Customer profile with nested address."""
    name: str = Field(description="Customer full name")
    email: str = Field(description="Primary email address")
    address: Address = Field(description="Mailing address")
    loyalty_tier: Optional[str] = Field(default=None, description="Loyalty program tier")

nested_request = artifact_schema_from_model(
    CustomerProfile,
    display_name="Customer Profile",
    description="Customer profile with address",
)
print("Nested JSON artifact schema_def:")
print(nested_request.schema_def)
print()

# CSV with nested model — flattens to dot notation
nested_csv = artifact_schema_from_model(
    CustomerProfile,
    display_name="Customer CSV",
    type="csv",
)
print("Nested CSV artifact schema_def:")
print(nested_csv.schema_def)
print()

# ---------------------------------------------------------------------------
# Example 6: Create an artifact schema on the platform
# ---------------------------------------------------------------------------

# Uncomment to actually create:
# result = client.artifact_schema_from_models.create(body=json_request)
# print(f"Created artifact schema: {result.id}")
