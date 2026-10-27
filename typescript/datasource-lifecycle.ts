/**
 * Datasource Lifecycle: create, upload, ingest, query, export, delete.
 *
 * Demonstrates the full lifecycle of a datasource in the Meibel platform.
 * Uses top-level await (ESM).
 */

import { readFile } from "node:fs/promises";
import { MeibelClient } from "meibel";

const client = new MeibelClient({ apiKey: process.env.MEIBEL_API_KEY! });

// 1. Create a datasource (connector config is required)
const datasource = await client.datasources.create({
  name: "Legal Documents",
  description: "Contracts and agreements for analysis",
  connector: {
    type: "cloud_storage",
    cloudStorage: {
      provider: "s3",
      bucket: "my-legal-docs",
      region: "us-east-1",
    },
  },
});
const datasourceId = datasource.id;
console.log(`Created datasource: ${datasourceId}`);

// 2. Upload a file
const fileBuffer = await readFile("contract.pdf");
const fileBlob = new Blob([fileBuffer], { type: "application/pdf" });

const upload = await client.datasources.fileUploads.uploadContent(fileBlob, "contract.pdf", {
  datasourceId,
});
console.log(`Uploaded file (upload ID: ${upload.uploadId})`);

// 3. Stream upload progress (SSE)
console.log("Upload progress:");
for await (const event of client.datasources.fileUploads.streamUploadProgress(upload.uploadId)) {
  console.log(`  ${JSON.stringify(event)}`);
}

// 4. Trigger ingestion
await client.datasources.ingest.trigger(datasourceId);
console.log("Ingestion triggered");

// 5. Poll ingest status until complete
let ingestStatus = await client.datasources.ingest.getStatus(datasourceId);
while (ingestStatus.status !== "completed" && ingestStatus.status !== "failed") {
  console.log(`  Ingest status: ${ingestStatus.status}`);
  await new Promise((resolve) => setTimeout(resolve, 3000));
  ingestStatus = await client.datasources.ingest.getStatus(datasourceId);
}
console.log(`Ingest finished: ${ingestStatus.status}`);

// 6. List data elements (async iterable -- automatically paginates)
console.log("\nData elements:");
for await (const element of client.datasources.dataElements.list(datasourceId)) {
  console.log(`  - ${element.id}: ${element.name}`);
}

// 7. Search data elements
const results = await client.datasources.dataElements.search(datasourceId, {
  regexFilter: ".*contract.*",
});
console.log(`\nSearch returned ${results.items.length} results`);

// 8. Export / download the datasource (sync)
const exportResult = await client.datasources.downloads.process(datasourceId);
console.log(`Export: ${exportResult}`);

// 9. Cleanup -- delete the datasource
await client.datasources.delete(datasourceId);
console.log(`Deleted datasource: ${datasourceId}`);
