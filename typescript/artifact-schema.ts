/**
 * Artifact Schema: define typed output schemas for agents using Zod.
 *
 * Demonstrates JSON, CSV, Markdown, and freeform artifact creation.
 */

import { z } from "zod";
import { MeibelClient, artifactSchemaFromZod } from "meibel";

const client = new MeibelClient({ apiKey: process.env.MEIBEL_API_KEY! });

// ---------------------------------------------------------------------------
// Example 1: JSON artifact from a Zod schema
// ---------------------------------------------------------------------------

const InvoiceOutput = z.object({
  vendorName: z.string().describe("Name of the vendor or supplier"),
  invoiceNumber: z.string().describe("Invoice reference number"),
  totalAmount: z.number().describe("Total amount due"),
  currency: z.string().describe("ISO 4217 currency code"),
  dueDate: z.string().optional().describe("Payment due date (YYYY-MM-DD)"),
  lineItems: z.array(z.string()).describe("Extracted line item descriptions"),
});

const jsonRequest = artifactSchemaFromZod(InvoiceOutput, {
  displayName: "Invoice Output",
  description: "Structured invoice data extracted from documents",
  required: true,
});
console.log("JSON artifact schema_def:");
console.log(jsonRequest.schemaDef);
console.log();

// ---------------------------------------------------------------------------
// Example 2: CSV artifact — fields flattened to columns
// ---------------------------------------------------------------------------

const ContactRow = z.object({
  name: z.string().describe("Full name"),
  email: z.string().describe("Email address"),
  company: z.string().describe("Company name"),
  title: z.string().optional().describe("Job title"),
});

const csvRequest = artifactSchemaFromZod(ContactRow, {
  displayName: "Contact List",
  type: "csv",
  description: "Extracted contact information as CSV",
});
console.log("CSV artifact schema_def:");
console.log(csvRequest.schemaDef);
console.log();

// ---------------------------------------------------------------------------
// Example 3: Markdown artifact with structured sections
// ---------------------------------------------------------------------------

const AnalysisReport = z.object({
  executiveSummary: z.string().describe("High-level summary of findings"),
  methodology: z.string().describe("Approach and methods used"),
  keyFindings: z.string().describe("Detailed findings and observations"),
  recommendations: z.string().describe("Actionable recommendations"),
});

const markdownRequest = artifactSchemaFromZod(AnalysisReport, {
  displayName: "Analysis Report",
  type: "markdown",
  description: "Structured analysis report with sections",
});
console.log("Markdown artifact schema_def:");
console.log(markdownRequest.schemaDef);
console.log();

// ---------------------------------------------------------------------------
// Example 4: Freeform markdown — no schema, agent has full discretion
// ---------------------------------------------------------------------------

const freeformRequest = artifactSchemaFromZod(null, {
  displayName: "Exploration Notes",
  type: "markdown",
  description: "Open-ended exploration and research notes",
});
console.log("Freeform markdown schema_def:");
console.log(freeformRequest.schemaDef);
console.log();

// ---------------------------------------------------------------------------
// Example 5: Nested schema — demonstrates recursive generation
// ---------------------------------------------------------------------------

const Address = z.object({
  street: z.string().describe("Street address"),
  city: z.string().describe("City"),
  state: z.string().describe("State or province"),
  zipCode: z.string().describe("ZIP or postal code"),
});

const CustomerProfile = z.object({
  name: z.string().describe("Customer full name"),
  email: z.string().describe("Primary email address"),
  address: Address.describe("Mailing address"),
  loyaltyTier: z.string().optional().describe("Loyalty program tier"),
});

const nestedRequest = artifactSchemaFromZod(CustomerProfile, {
  displayName: "Customer Profile",
  description: "Customer profile with address",
});
console.log("Nested JSON artifact schema_def:");
console.log(nestedRequest.schemaDef);
console.log();

// CSV with nested schema — flattens to dot notation
const nestedCsv = artifactSchemaFromZod(CustomerProfile, {
  displayName: "Customer CSV",
  type: "csv",
});
console.log("Nested CSV artifact schema_def:");
console.log(nestedCsv.schemaDef);
console.log();

// ---------------------------------------------------------------------------
// Example 6: Create an artifact schema on the platform
// ---------------------------------------------------------------------------

// Uncomment to actually create:
// const result = await client.artifactSchemas.create(jsonRequest as any);
// console.log(`Created artifact schema: ${result.id}`);
