// Artifact Lifecycle: define schema, create, attach to agent, chat, inspect output, delete.
package main

import (
	"context"
	"fmt"
	"log"
	"os"

	meibel "github.com/meibel-ai/meibel-go/v2"
)

// 1. Define the artifact schema as a Go struct
type ContractSummary struct {
	Parties            []string `json:"parties"             desc:"Names of all contracting parties"`
	EffectiveDate      string   `json:"effective_date"      desc:"Contract effective date (YYYY-MM-DD)"`
	ExpirationDate     *string  `json:"expiration_date"     desc:"Contract expiration date (YYYY-MM-DD)"`
	KeyObligations     []string `json:"key_obligations"     desc:"Main obligations of each party"`
	TerminationClauses []string `json:"termination_clauses" desc:"Conditions under which the contract can be terminated"`
	GoverningLaw       string   `json:"governing_law"       desc:"Jurisdiction governing the contract"`
}

func main() {
	ctx := context.Background()
	client := meibel.NewClient(meibel.WithAPIKey(os.Getenv("MEIBEL_API_KEY")))

	// 2. Create the artifact schema on the platform
	req, err := meibel.ArtifactSchemaFromStruct[ContractSummary](
		"Contract Summary",
		meibel.WithArtifactDescription("Structured summary extracted from legal contracts"),
		meibel.WithArtifactRequired(true),
	)
	if err != nil {
		log.Fatal(err)
	}

	schema, err := client.ArtifactSchemas.Create(ctx, meibel.ArtifactSchemasCreateOptions{
		DisplayName: req.DisplayName,
		Type:        &req.Type,
		Description: req.Description,
		Required:    req.Required,
		Schema:      req.SchemaDef,
	})
	if err != nil {
		log.Fatal(err)
	}
	artifactName := schema.Name
	fmt.Printf("Created artifact schema: %s (id: %s)\n", artifactName, schema.Id)

	// 3. Verify it was created
	retrieved, err := client.ArtifactSchemas.Get(ctx, schema.Id)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Retrieved: %s (type: %s)\n", retrieved.DisplayName, retrieved.Type)

	// 4. Create an agent that produces this artifact
	agentDescription := "Analyzes legal contracts and produces structured summaries"
	agent, err := client.Agents.Create(ctx, meibel.CreateAgentDefinitionRequest{
		DisplayName: "Contract Analyst",
		Description: &agentDescription,
		Instructions: "You are a legal contract analyst. When given a contract, extract the key information " +
			"and produce a structured Contract Summary artifact.",
		Artifacts: []string{artifactName},
	})
	if err != nil {
		log.Fatal(err)
	}
	agentId := agent.Id
	fmt.Printf("Created agent: %s with artifact: %s\n", agentId, artifactName)

	// 5. Publish the agent
	published, err := client.Agents.Publish(ctx, agentId, meibel.PublishAgentDefinitionRequest{
		CommitMessage: "Initial release with contract summary artifact",
	}, nil)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Published version: %s\n", published.Version)

	// 6. Chat with the agent — it should produce the artifact
	session, err := client.Agents.Sessions.Create(ctx, agentId, nil)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Created session: %s\n", session.SessionId)

	response, err := client.Agents.Sessions.SendChatMessage(ctx, session.SessionId, meibel.ChatMessageRequest{
		UserMessage: "Analyze this contract excerpt:\n\n" +
			"This Agreement is entered into by Acme Corp and Beta LLC, effective January 1, 2025. " +
			"Acme agrees to provide consulting services. Beta agrees to pay $10,000/month. " +
			"Either party may terminate with 30 days written notice. " +
			"This agreement is governed by the laws of Delaware.",
	})
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Response: %.200s...\n", response.AssistantResponse)

	// 7. Check for artifacts in the response
	if len(response.Response.Artifacts) > 0 {
		fmt.Println("\nArtifacts produced:")
		for _, a := range response.Response.Artifacts {
			fmt.Printf("  - %s (%s)\n", a.Filename, a.MimeType)
		}
	}

	// 8. Update the artifact schema
	newDescription := "Structured summary extracted from legal contracts — v2 with improved extraction"
	_, err = client.ArtifactSchemas.Update(ctx, schema.Id, meibel.UpdateAgentArtifactRequest{
		Description: &newDescription,
	})
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println("Updated artifact schema description")

	// 9. List all artifact schemas
	fmt.Println("\nAll artifact schemas:")
	iter := client.ArtifactSchemas.List(ctx, nil)
	for iter.Next(ctx) {
		s := iter.Item()
		fmt.Printf("  - %s: %s\n", s.Name, s.Description)
	}
	if err := iter.Err(); err != nil {
		log.Fatal(err)
	}

	// 10. Cleanup
	err = client.Agents.Delete(ctx, agentId)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("\nDeleted agent: %s\n", agentId)

	err = client.ArtifactSchemas.Delete(ctx, schema.Id)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Deleted artifact schema: %s\n", schema.Id)
}
