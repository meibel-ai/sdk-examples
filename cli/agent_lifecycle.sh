#!/usr/bin/env bash
# Agent Lifecycle: create, publish, chat, stream, inspect, delete.
set -euo pipefail

# 1. Create an agent
AGENT=$(meibel agents create \
  --data '{"display_name":"Contract Analyst","description":"Analyzes contracts","instructions":"You are a legal contract analyst."}')
AGENT_ID=$(echo "$AGENT" | jq -r '.agent_id')
echo "Created agent: $AGENT_ID"

# 2. Publish the agent
meibel agents publish "$AGENT_ID" \
  --data '{"commit_message":"Initial release"}'
echo "Published agent"

# 3. Create a session
SESSION=$(meibel agents create-session "$AGENT_ID")
SESSION_ID=$(echo "$SESSION" | jq -r '.session_id')
echo "Created session: $SESSION_ID"

# 4. Send a chat message
RESPONSE=$(meibel sessions send-chat-message "$SESSION_ID" \
  --data '{"user_message":"What are the typical sections in an NDA?"}')
echo "Response: $(echo "$RESPONSE" | jq -r '.assistant_response')"

# 5. Stream a chat response
echo -e "\nStreaming response:"
meibel sessions send-chat-message-stream "$SESSION_ID" \
  --data '{"user_message":"Summarize the key obligations in a standard NDA."}'

# 6. Get session messages
MESSAGES=$(meibel sessions get-session-messages "$SESSION_ID")
echo -e "\nMessages: $(echo "$MESSAGES" | jq '.messages | length')"

# 7. Cleanup
meibel agents delete "$AGENT_ID"
echo "Deleted agent: $AGENT_ID"
