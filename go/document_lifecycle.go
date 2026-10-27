// Document Lifecycle: parse, poll, get results, sync process, trace.
package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"time"

	meibel "github.com/meibel-ai/meibel-go/v2"
)

func main() {
	ctx := context.Background()
	client := meibel.NewClient(meibel.WithAPIKey(os.Getenv("MEIBEL_API_KEY")))

	path := os.Getenv("DOCUMENT_FILE")
	if path == "" {
		log.Fatal("Set DOCUMENT_FILE to the path of a PDF")
	}
	fileName := filepath.Base(path)

	// --- Async parsing ---

	// 1. Parse a document
	file, err := os.Open(path)
	if err != nil {
		log.Fatal(err)
	}
	result, err := client.Documents.Parse(ctx, file, fileName)
	file.Close()
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Parse job: %s\n", result.JobId)

	// 2. Poll for status
	for {
		status, err := client.Documents.GetStatus(ctx, result.JobId)
		if err != nil {
			log.Fatal(err)
		}
		fmt.Printf("Status: %s\n", status.Status)
		if status.Status == "completed" || status.Status == "failed" {
			break
		}
		time.Sleep(2 * time.Second)
	}

	// 3. Get result as markdown
	markdownFmt := "markdown"
	md, err := client.Documents.GetResult(ctx, result.JobId, &meibel.DocumentsGetResultOptions{
		Format: &markdownFmt,
	})
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("\nMarkdown (%d chars)\n", len(*md))

	// 4. Get result as JSON
	jsonFmt := "json"
	jsonResult, err := client.Documents.GetResult(ctx, result.JobId, &meibel.DocumentsGetResultOptions{
		Format: &jsonFmt,
	})
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("JSON (%d chars)\n", len(*jsonResult))

	// 5. List children
	children, err := client.Documents.ListChildren(ctx, result.JobId)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Children: %d\n", len(*children))

	// --- Sync parsing ---

	// 6. Process document synchronously
	file2, err := os.Open(path)
	if err != nil {
		log.Fatal(err)
	}
	syncResult, err := client.Documents.Process(ctx, file2, fileName, nil)
	file2.Close()
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("\nSync result: job %s (%s)\n", syncResult.JobId, syncResult.Status)
}
