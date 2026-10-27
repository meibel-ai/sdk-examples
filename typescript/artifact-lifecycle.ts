/**
 * Artifact Lifecycle: define schema, create, attach to agent, chat, inspect output, delete.
 */

import { z } from "zod";
import { MeibelClient, artifactSchemaFromZod } from "meibel";

const client = new MeibelClient({ apiKey: process.env.MEIBEL_API_KEY! });

// 1. Define the artifact schema as a Zod schema
const ContractSummary = z.object({
  parties: z.array(z.string()).describe("Names of all contracting parties"),
  effectiveDate: z.string().describe("Contract effective date (YYYY-MM-DD)"),
  expirationDate: z.string().optional().describe("Contract expiration date (YYYY-MM-DD)"),
  keyObligations: z.array(z.string()).describe("Main obligations of each party"),
  terminationClauses: z.array(z.string()).describe("Conditions under which the contract can be terminated"),
  governingLaw: z.string().describe("Jurisdiction governing the contract"),
});

// 2. Create the artifact schema on the platform
const schema = await client.artifactSchemas.create(
  artifactSchemaFromZod(ContractSummary, {
    displayName: "Contract Summary",
    description: "Structured summary extracted from legal contracts",
    required: true,
  }) as any,
);
const artifactName = schema.name;
console.log(`Created artifact schema: ${artifactName} (id: ${schema.id})`);

// 3. Verify it was created
const retrieved = await client.artifactSchemas.get(schema.id);
console.log(`Retrieved: ${retrieved.displayName} (type: ${retrieved.type})`);

// 4. Create an agent that produces this artifact
const agent = await client.agents.create({
  displayName: "Contract Analyst",
  description: "Analyzes legal contracts and produces structured summaries",
  instructions:
    "You are a legal contract analyst. When given a contract, extract the key information " +
    "and produce a structured Contract Summary artifact.",
  llmModel: "claude-haiku-4-5",
  artifacts: [artifactName],
});
const agentId = agent.id;
console.log(`Created agent: ${agentId} with artifact: ${artifactName}`);

// 5. Publish the agent
const published = await client.agents.publish(agentId, {
  commitMessage: "Initial release with contract summary artifact",
});
console.log(`Published version: ${published.version}`);

// 6. Chat with the agent — it should produce the artifact
const session = await client.agents.sessions.create(agentId);
const sessionId = session.sessionId;
console.log(`Created session: ${sessionId}`);

const response = await client.agents.sessions.sendChatMessage(sessionId, {
  userMessage:
    "Analyze this contract excerpt:\n\n" +
    "This Agreement is entered into by Acme Corp and Beta LLC, effective January 1, 2025. " +
    "Acme agrees to provide consulting services. Beta agrees to pay $10,000/month. " +
    "Either party may terminate with 30 days written notice. " +
    "This agreement is governed by the laws of Delaware.",
});
console.log(`Response: ${response.assistantResponse?.slice(0, 200)}...`);

// 7. Check for artifacts in the response
if (response.response.artifacts?.length) {
  console.log("\nArtifacts produced:");
  for (const artifact of response.response.artifacts) {
    console.log(`  - ${artifact.filename}: ${JSON.stringify(artifact.content).slice(0, 100)}...`);
  }
}

// 8. Update the artifact schema
await client.artifactSchemas.update(schema.id, {
  description: "Structured summary extracted from legal contracts — v2 with improved extraction",
});
console.log("Updated artifact schema description");

// 9. List all artifact schemas
console.log("\nAll artifact schemas:");
for await (const s of client.artifactSchemas.list()) {
  console.log(`  - ${s.name}: ${s.description}`);
}

// 10. Cleanup
await client.agents.delete(agentId);
console.log(`\nDeleted agent: ${agentId}`);

await client.artifactSchemas.delete(schema.id);
console.log(`Deleted artifact schema: ${schema.id}`);
