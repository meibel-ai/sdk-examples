/**
 * Document Transform: three ways to extract structured data from documents.
 *
 * Demonstrates client.documents.transform() with:
 *   1. A Zod schema (auto-converts to JSON Schema)
 *   2. A raw JSON Schema object
 *   3. An artifact schema ID (pre-registered on the platform)
 */

import { z } from "zod";
import { MeibelClient } from "meibel";

const client = new MeibelClient({ apiKey: process.env.MEIBEL_API_KEY! });

const FILE = process.env.DOCUMENT_FILE!;

// ---------------------------------------------------------------------------
// Way 1: Zod schema — the most ergonomic approach
// ---------------------------------------------------------------------------

const SubstratePreparation = z.object({
  substrate_type: z
    .string()
    .nullable()
    .describe("Type of substrate (e.g., steel, masonry, plastic)"),
  cleaning_method: z
    .string()
    .nullable()
    .describe("Surface cleaning method (e.g., solvent wipe, blast cleaning)"),
  abrading_method: z
    .string()
    .nullable()
    .describe("Surface abrading method (e.g., sanding, mechanical etching)"),
  priming_method: z
    .string()
    .nullable()
    .describe("Specific primer for the substrate listed"),
  pretreatment_method: z
    .string()
    .nullable()
    .describe("Pretreatment method (e.g., chemical etching)"),
  min_preparation_standard: z
    .string()
    .nullable()
    .describe("Minimum preparation standard (e.g., NACE No. 2, SSPC-SP10)"),
  general_preparation_instructions: z
    .string()
    .nullable()
    .describe("General preparation instructions"),
});

const SubstratePreparations = z.object({
  substrate_preparations: z
    .array(SubstratePreparation)
    .nullable()
    .describe(
      "List of substrate preparation methods and their attributes"
    ),
});

type PrepData = z.infer<typeof SubstratePreparations>;

console.log("=== Way 1: Zod schema ===");
const result1 = await client.documents.transform({
  file: FILE,
  schema: SubstratePreparations,
});
console.log(`Execution: ${result1.executionId}`);
const data1 = result1.data as PrepData;
for (const prep of data1.substrate_preparations ?? []) {
  console.log(`  - ${prep.substrate_type}: ${prep.cleaning_method}`);
}

// ---------------------------------------------------------------------------
// Way 2: Raw JSON Schema object — for dynamic or externally-defined schemas
// ---------------------------------------------------------------------------

const jsonSchema = {
  type: "object",
  properties: {
    substrate_preparations: {
      type: "array",
      description:
        "List of substrate preparation methods and their attributes",
      items: {
        type: "object",
        properties: {
          substrate_type: {
            type: "string",
            description: "Type of substrate",
          },
          cleaning_method: {
            type: "string",
            description: "Surface cleaning method",
          },
          abrading_method: {
            type: "string",
            description: "Surface abrading method",
          },
          priming_method: {
            type: "string",
            description: "Specific primer for the substrate",
          },
          pretreatment_method: {
            type: "string",
            description: "Pretreatment method",
          },
          min_preparation_standard: {
            type: "string",
            description: "Minimum preparation standard",
          },
          general_preparation_instructions: {
            type: "string",
            description: "General preparation instructions",
          },
        },
      },
    },
  },
  additionalProperties: false,
};

console.log("\n=== Way 2: Raw JSON Schema object ===");
const result2 = await client.documents.transform({
  file: FILE,
  schema: jsonSchema,
});
console.log(`Execution: ${result2.executionId}`);
const data2 = result2.data as PrepData;
for (const prep of data2.substrate_preparations ?? []) {
  console.log(`  - ${prep.substrate_type}: ${prep.cleaning_method}`);
}

// ---------------------------------------------------------------------------
// Way 3: Artifact schema ID — for schemas registered on the platform
// ---------------------------------------------------------------------------

// First register the schema (or use an existing one):
// const schema = await client.artifactSchemas.create({ ... });
// const SCHEMA_ID = schema.id;

// For this example, assume a pre-registered schema ID:
const SCHEMA_ID = "your-artifact-schema-id";

console.log("\n=== Way 3: Artifact schema ID ===");
const result3 = await client.documents.transform({
  file: FILE,
  schema: SCHEMA_ID,
});
console.log(`Execution: ${result3.executionId}`);
const data3 = result3.data as PrepData;
for (const prep of data3.substrate_preparations ?? []) {
  console.log(`  - ${prep.substrate_type}: ${prep.cleaning_method}`);
}
