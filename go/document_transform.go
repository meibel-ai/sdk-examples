// Document Transform: three ways to extract structured data from documents.
//
// Demonstrates client.Documents.Transform() with:
//  1. A Go struct (auto-converts to JSON Schema via reflect)
//  2. A raw JSON Schema map
//  3. An artifact schema ID string
package main

import (
	"context"
	"fmt"
	"log"
	"os"

	meibel "github.com/meibel-ai/meibel-go/v2"
)

// SubstratePreparation represents a single substrate preparation entry.
type SubstratePreparation struct {
	SubstrateType                  *string `json:"substrate_type" desc:"Type of substrate (e.g., steel, masonry, plastic)"`
	CleaningMethod                 *string `json:"cleaning_method" desc:"Surface cleaning method (e.g., solvent wipe, blast cleaning)"`
	AbradingMethod                 *string `json:"abrading_method" desc:"Surface abrading method (e.g., sanding, mechanical etching)"`
	PrimingMethod                  *string `json:"priming_method" desc:"Specific primer for the substrate listed"`
	PretreatmentMethod             *string `json:"pretreatment_method" desc:"Pretreatment method (e.g., chemical etching)"`
	MinPreparationStandard         *string `json:"min_preparation_standard" desc:"Minimum preparation standard (e.g., NACE No. 2, SSPC-SP10)"`
	GeneralPreparationInstructions *string `json:"general_preparation_instructions" desc:"General preparation instructions"`
}

// SubstratePreparations is the top-level extraction schema.
type SubstratePreparations struct {
	SubstratePreparations []SubstratePreparation `json:"substrate_preparations" desc:"List of substrate preparation methods and their attributes"`
}

func main() {
	ctx := context.Background()
	client := meibel.NewClient(meibel.WithAPIKey(os.Getenv("MEIBEL_API_KEY")))
	file := os.Getenv("DOCUMENT_FILE")
	if file == "" {
		log.Fatal("Set DOCUMENT_FILE to the path of a PDF")
	}

	// -------------------------------------------------------------------
	// Way 1: Go struct — the most ergonomic approach
	// -------------------------------------------------------------------

	fmt.Println("=== Way 1: Go struct ===")
	result1, err := client.Documents.Transform(ctx, meibel.DocumentsTransformOptions{
		File:   file,
		Schema: SubstratePreparations{},
	})
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Execution: %s\n", result1.ExecutionId)
	printPreparations(result1.Data)

	// -------------------------------------------------------------------
	// Way 2: Raw JSON Schema map — for dynamic or externally-defined schemas
	// -------------------------------------------------------------------

	jsonSchema := map[string]interface{}{
		"type": "object",
		"properties": map[string]interface{}{
			"substrate_preparations": map[string]interface{}{
				"type":        "array",
				"description": "List of substrate preparation methods and their attributes",
				"items": map[string]interface{}{
					"type": "object",
					"properties": map[string]interface{}{
						"substrate_type":                   map[string]interface{}{"type": "string", "description": "Type of substrate"},
						"cleaning_method":                  map[string]interface{}{"type": "string", "description": "Surface cleaning method"},
						"abrading_method":                  map[string]interface{}{"type": "string", "description": "Surface abrading method"},
						"priming_method":                   map[string]interface{}{"type": "string", "description": "Specific primer for the substrate"},
						"pretreatment_method":              map[string]interface{}{"type": "string", "description": "Pretreatment method"},
						"min_preparation_standard":         map[string]interface{}{"type": "string", "description": "Minimum preparation standard"},
						"general_preparation_instructions": map[string]interface{}{"type": "string", "description": "General preparation instructions"},
					},
				},
			},
		},
		"additionalProperties": false,
	}

	fmt.Println("\n=== Way 2: Raw JSON Schema map ===")
	result2, err := client.Documents.Transform(ctx, meibel.DocumentsTransformOptions{
		File:   file,
		Schema: jsonSchema,
	})
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Execution: %s\n", result2.ExecutionId)
	printPreparations(result2.Data)

	// -------------------------------------------------------------------
	// Way 3: Artifact schema ID — for schemas registered on the platform
	// -------------------------------------------------------------------

	// First register the schema (or use an existing one):
	//   schema, _ := client.ArtifactSchemas.Create(ctx, ...)
	//   schemaID := schema.Id

	// For this example, assume a pre-registered schema ID:
	schemaID := "your-artifact-schema-id"

	fmt.Println("\n=== Way 3: Artifact schema ID ===")
	result3, err := client.Documents.Transform(ctx, meibel.DocumentsTransformOptions{
		File:   file,
		Schema: schemaID,
	})
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Execution: %s\n", result3.ExecutionId)
	printPreparations(result3.Data)
}

func printPreparations(data map[string]interface{}) {
	preps, ok := data["substrate_preparations"].([]interface{})
	if !ok {
		fmt.Println("  (no preparations found)")
		return
	}
	for _, p := range preps {
		prep, _ := p.(map[string]interface{})
		fmt.Printf("  - %v: %v\n", prep["substrate_type"], prep["cleaning_method"])
	}
}
