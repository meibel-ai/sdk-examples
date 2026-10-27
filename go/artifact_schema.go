// Artifact Schema: define typed output schemas for agents using Go structs.
package main

import (
	"encoding/json"
	"fmt"
	"log"

	meibel "github.com/meibel-ai/meibel-go/v2"
)

// ---------------------------------------------------------------------------
// Example 1: JSON artifact from a Go struct
// ---------------------------------------------------------------------------

type InvoiceOutput struct {
	VendorName    string   `json:"vendor_name"    desc:"Name of the vendor or supplier"`
	InvoiceNumber string   `json:"invoice_number" desc:"Invoice reference number"`
	TotalAmount   float64  `json:"total_amount"   desc:"Total amount due"`
	Currency      string   `json:"currency"       desc:"ISO 4217 currency code"`
	DueDate       *string  `json:"due_date"       desc:"Payment due date (YYYY-MM-DD)"`
	LineItems     []string `json:"line_items"     desc:"Extracted line item descriptions"`
}

// ---------------------------------------------------------------------------
// Example 2: CSV artifact — fields as columns
// ---------------------------------------------------------------------------

type ContactRow struct {
	Name    string  `json:"name"    desc:"Full name"`
	Email   string  `json:"email"   desc:"Email address"`
	Company string  `json:"company" desc:"Company name"`
	Title   *string `json:"title"   desc:"Job title"`
}

// ---------------------------------------------------------------------------
// Example 3: Markdown artifact with sections
// ---------------------------------------------------------------------------

type AnalysisReport struct {
	ExecutiveSummary string `json:"executive_summary" desc:"High-level summary of findings"`
	Methodology      string `json:"methodology"       desc:"Approach and methods used"`
	KeyFindings      string `json:"key_findings"      desc:"Detailed findings and observations"`
	Recommendations  string `json:"recommendations"   desc:"Actionable recommendations"`
}

// ---------------------------------------------------------------------------
// Example 5: Nested struct
// ---------------------------------------------------------------------------

type Address struct {
	Street  string `json:"street"   desc:"Street address"`
	City    string `json:"city"     desc:"City"`
	State   string `json:"state"    desc:"State or province"`
	ZipCode string `json:"zip_code" desc:"ZIP or postal code"`
}

type CustomerProfile struct {
	Name        string  `json:"name"         desc:"Customer full name"`
	Email       string  `json:"email"        desc:"Primary email address"`
	Address     Address `json:"address"      desc:"Mailing address"`
	LoyaltyTier *string `json:"loyalty_tier" desc:"Loyalty program tier"`
}

func main() {
	// Example 1: JSON artifact
	jsonReq, err := meibel.ArtifactSchemaFromStruct[InvoiceOutput](
		"Invoice Output",
		meibel.WithArtifactDescription("Structured invoice data extracted from documents"),
		meibel.WithArtifactRequired(true),
	)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println("JSON artifact schema_def:")
	prettyPrint(jsonReq.SchemaDef)
	fmt.Println()

	// Example 2: CSV artifact
	csvReq, err := meibel.ArtifactSchemaFromStruct[ContactRow](
		"Contact List",
		meibel.WithArtifactType(meibel.ArtifactTypeCsv),
		meibel.WithArtifactDescription("Extracted contact information as CSV"),
	)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println("CSV artifact schema_def:")
	prettyPrint(csvReq.SchemaDef)
	fmt.Println()

	// Example 3: Markdown with sections
	mdReq, err := meibel.ArtifactSchemaFromStruct[AnalysisReport](
		"Analysis Report",
		meibel.WithArtifactType(meibel.ArtifactTypeMarkdown),
		meibel.WithArtifactDescription("Structured analysis report with sections"),
	)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println("Markdown artifact schema_def:")
	prettyPrint(mdReq.SchemaDef)
	fmt.Println()

	// Example 4: Freeform markdown — no struct, agent has full discretion
	freeformReq, err := meibel.FreeformArtifactSchema(
		"Exploration Notes",
		meibel.WithArtifactType(meibel.ArtifactTypeMarkdown),
		meibel.WithArtifactDescription("Open-ended exploration and research notes"),
	)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println("Freeform markdown schema_def:")
	prettyPrint(freeformReq.SchemaDef)
	fmt.Println()

	// Example 5: Nested struct
	nestedReq, err := meibel.ArtifactSchemaFromStruct[CustomerProfile](
		"Customer Profile",
		meibel.WithArtifactDescription("Customer profile with address"),
	)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println("Nested JSON artifact schema_def:")
	prettyPrint(nestedReq.SchemaDef)
	fmt.Println()

	// CSV with nested struct — flattens to dot notation
	nestedCsv, err := meibel.ArtifactSchemaFromStruct[CustomerProfile](
		"Customer CSV",
		meibel.WithArtifactType(meibel.ArtifactTypeCsv),
	)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println("Nested CSV artifact schema_def:")
	prettyPrint(nestedCsv.SchemaDef)
	fmt.Println()

	// ---------------------------------------------------------------------------
	// Example 6: Create on the platform
	// ---------------------------------------------------------------------------
	// Uncomment to actually create:
	// ctx := context.Background()
	// client := meibel.NewClient(meibel.WithAPIKey(os.Getenv("MEIBEL_API_KEY")))
	// result, err := client.ArtifactSchemas.Create(ctx, meibel.ArtifactSchemasCreateOptions{
	// 	DisplayName: jsonReq.DisplayName,
	// 	Schema:      jsonReq.SchemaDef,
	// })
	// fmt.Printf("Created artifact schema: %s\n", result.Id)
}

func prettyPrint(schemaDef map[string]interface{}) {
	b, _ := json.MarshalIndent(schemaDef, "", "  ")
	fmt.Println(string(b))
}
