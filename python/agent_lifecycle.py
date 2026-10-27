"""Agent Lifecycle: create, publish, chat, stream, inspect, delete."""

import os
from meibel import MeibelClient
from meibel.models import (
    CreateAgentDefinitionRequest,
    PublishAgentDefinitionRequest,
    ChatMessageRequest,
)

client = MeibelClient(
    api_key=os.environ["MEIBEL_API_KEY"],
)

# 1. Create an agent
agent = client.agents.create(
    body=CreateAgentDefinitionRequest(
        display_name="Contract Analyst",
        description="Analyzes legal contracts and extracts key terms",
        instructions="You are a legal contract analyst. Extract key terms, obligations, and deadlines from documents.",
        llm_model="claude-haiku-4-5"
    )
)


agent_id = agent.id
print(f"Created agent: {agent_id}")

# 2. Publish the agent
published = client.agents.publish(
    agent_id=agent_id,
    body=PublishAgentDefinitionRequest(
        commit_message="Initial release",
    ),
)
print(f"Published version: {published.version}")

# 3. Create a session
session = client.agents.sessions.create(agent_id=agent_id)


session_id = session.session_id
print(f"Created session: {session_id}")

# # 4. Send a chat message (synchronous)
# response = client.agents.sessions.send_chat_message(
#     session_id=session_id,
#     body=ChatMessageRequest(user_message="What are the typical sections in an NDA?"),
# )
# print(f"Response: {response.assistant_response}")

# 5. Stream a chat response (SSE)
print("\nStreaming response:")
for event in client.agents.sessions.send_chat_message_stream(
    session_id=session_id,
    user_message="Summarize the key obligations in a standard NDA."
):
    print(event, end="\n", flush=True)
print()

# 6. Retrieve session message history
messages = client.sessions.get_messages(session_id=session_id)
print(f"\nSession has {len(messages.messages)} messages")

# 7. Cleanup — delete the agent
client.agents.delete(agent_id=agent_id)
print(f"Deleted agent: {agent_id}")
