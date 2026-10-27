/**
 * Document Lifecycle: parse (async + sync), poll, get results, trace.
 *
 * Demonstrates the full lifecycle of document parsing in the Meibel platform.
 * Uses top-level await (ESM).
 */

import { readFile } from "node:fs/promises";
import { MeibelClient } from "meibel";

const client = new MeibelClient({ apiKey: process.env.MEIBEL_API_KEY! });

// Read a local PDF once; reuse for each example
const pdfBuffer = await readFile("report.pdf");
const pdfBlob = new Blob([pdfBuffer], { type: "application/pdf" });

// --- Async parsing flow ---

// 1. Parse a document asynchronously (returns a job ID immediately)
const parseResult = await client.documents.parse(pdfBlob, "report.pdf");
const jobId = parseResult.jobId;
console.log(`Parse job started: ${jobId} (status: ${parseResult.status})`);

// 2. Poll for document status
let status = await client.documents.getStatus(jobId);
while (status.status !== "completed" && status.status !== "failed") {
  console.log(`  Status: ${status.status}`);
  await new Promise((resolve) => setTimeout(resolve, 2000));
  status = await client.documents.getStatus(jobId);
}
console.log(`Parsing finished: ${status.status}`);
if (status.pages != null) {
  console.log(`  Pages: ${status.pages}, Tables: ${status.tables}, Elements: ${status.elements}`);
}

// 3. Get result as markdown
const markdownResult = await client.documents.getResult(jobId, {
  format: "markdown",
});
console.log(`\nMarkdown result (${markdownResult.length} chars):`);
console.log(markdownResult.slice(0, 500));

// 4. Get result as JSON (structured)
const jsonResult = await client.documents.getResult(jobId, {
  format: "json",
});
console.log(`\nJSON result (${jsonResult.length} chars)`);

// 5. List child documents (for containers like ZIP, TAR, EML)
const children = await client.documents.listChildren(jobId);
console.log(`\nChild documents: ${children.length}`);
for (const child of children) {
  console.log(`  - ${child.filename} (${child.status}, ${child.mediaType})`);
}

// --- Sync parsing flow ---

// 6. Process a document synchronously (blocks until complete)
const freshBlob = new Blob([pdfBuffer], { type: "application/pdf" });
const syncResult = await client.documents.process(freshBlob, "report.pdf");
console.log(`\nSync parse complete: job ${syncResult.jobId}, status ${syncResult.status}`);

// The result is either a MeibelDocumentResult (object) or a markdown string
if (typeof syncResult.result === "string") {
  console.log(`  Markdown (${syncResult.result.length} chars)`);
} else {
  console.log(`  Structured: ${syncResult.result.pages} pages, ${syncResult.result.tables} tables, ${syncResult.result.elements.length} elements`);
}

// --- Streaming trace ---

// 7. Stream trace events for real-time parsing progress (SSE)
const traceBlob = new Blob([pdfBuffer], { type: "application/pdf" });
const traceJob = await client.documents.parse(traceBlob, "report.pdf");
console.log(`\nTrace events for job ${traceJob.jobId}:`);
for await (const event of client.documents.streamTrace(traceJob.jobId)) {
  console.log(`  ${JSON.stringify(event)}`);
}
