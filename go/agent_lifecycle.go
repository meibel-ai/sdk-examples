// Agent Lifecycle: create, publish, chat, stream, inspect, delete.
package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"strings"

	meibel "github.com/meibel-ai/meibel-go/v2"
)

func main() {
	ctx := context.Background()
	client := meibel.NewClient(meibel.WithAPIKey(os.Getenv("MEIBEL_API_KEY")))

	// 1. Create an agent
	description := "Analyzes legal contracts and extracts key terms"
	agent, err := client.Agents.Create(ctx, meibel.CreateAgentDefinitionRequest{
		DisplayName:  "Contract Analyst",
		Description:  &description,
		Instructions: "You are a legal contract analyst. Extract key terms, obligations, and deadlines from documents.",
	})
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Created agent: %s\n", agent.Id)

	// 2. Publish the agent
	published, err := client.Agents.Publish(ctx, agent.Id, meibel.PublishAgentDefinitionRequest{
		CommitMessage: "Initial release",
	}, nil)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Published version: %s\n", published.Version)

	// 3. Create a session
	session, err := client.Agents.Sessions.Create(ctx, agent.Id, nil)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Created session: %s\n", session.SessionId)

	// 4. Send a chat message
	response, err := client.Agents.Sessions.SendChatMessage(ctx, session.SessionId, meibel.ChatMessageRequest{
		UserMessage: "What are the typical sections in an NDA?",
	})
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Response: %s\n", response.AssistantResponse)

	// 5. Stream a chat response (no file attached)
	fmt.Println("\nStreaming response:")
	stream, err := client.Agents.Sessions.SendChatMessageStream(ctx, session.SessionId,
		strings.NewReader(""), "",
		"Summarize the key obligations in a standard NDA.",
		0, false, false, nil,
	)
	if err != nil {
		log.Fatal(err)
	}
	for event := range stream.Events() {
		fmt.Print(event)
	}
	stream.Close()
	fmt.Println()

	// 6. Get session messages
	messages, err := client.Sessions.GetMessages(ctx, session.SessionId)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("\nSession has %d messages\n", len(messages.Messages))

	// 7. Cleanup
	err = client.Agents.Delete(ctx, agent.Id)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Deleted agent: %s\n", agent.Id)
}
