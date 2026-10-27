/**
 * Agent Lifecycle: create, publish, chat, stream, inspect, delete.
 *
 * Demonstrates the full lifecycle of an agent in the Meibel platform.
 * Uses top-level await (ESM).
 */

import { MeibelClient } from "meibel";

const client = new MeibelClient({ apiKey: process.env.MEIBEL_API_KEY! });

// 1. Create an agent
const agent = await client.agents.create({
  displayName: "Contract Analyst",
  instructions:
    "You are a legal contract analyst. Extract key terms, obligations, and deadlines from documents.",
  description: "Analyzes legal contracts and extracts key terms",
  llmModel: "gpt-4o",
});
const agentId = agent.id;
console.log(`Created agent: ${agentId} (${agent.displayName})`);

// 2. Publish the agent
const published = await client.agents.publish(agentId, {
  commitMessage: "Initial release",
});
console.log(`Published version: ${published.version}`);

// 3. Create a session
const session = await client.agents.sessions.create(agentId);
const sessionId = session.sessionId;
console.log(`Created session: ${sessionId}`);

// 4. Send a chat message (synchronous)
const response = await client.agents.sessions.sendChatMessage(sessionId, {
  userMessage: "What are the typical sections in an NDA?",
});
console.log(`Response: ${response.assistantResponse}`);

// Show sources if present
if (response.response.sources?.length) {
  console.log("\nSources:");
  for (const source of response.response.sources) {
    console.log(`  - ${source.title}`);
  }
}

// 5. Stream a chat response
console.log("\nStreaming response:");
for await (const event of client.agents.sessions.sendChatMessageStream(
  sessionId,
  undefined, // files (not needed for text-only chat)
  undefined, // filesName
  { userMessage: "Summarize the key risks in a typical NDA." },
)) {
  if ("partialText" in event) {
    process.stdout.write(event.partialText ?? "");
  }
}
console.log(); // newline after stream

// 6. Retrieve session message history
const messages = await client.sessions.getMessages(sessionId);
console.log(`\nSession has ${messages.messages.length} messages`);
for (const msg of messages.messages) {
  console.log(`  [${msg.type}] ${msg.message?.slice(0, 80) ?? "(no text)"}...`);
}

// 7. Cleanup -- delete the agent
await client.agents.delete(agentId);
console.log(`Deleted agent: ${agentId}`);
