// Datasource Lifecycle: create, upload, ingest, query, export, delete.
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

	// 1. Create a datasource
	desc := "Contracts and agreements for analysis"
	ds, err := client.Datasources.Create(ctx, meibel.DatasourcesCreateOptions{
		Name:        "Legal Documents",
		Description: &desc,
	})
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Created datasource: %s\n", ds.Id)

	// 2. Upload a file
	file, err := os.Open(path)
	if err != nil {
		log.Fatal(err)
	}
	defer file.Close()

	upload, err := client.Datasources.FileUploads.UploadContent(ctx, ds.Id, file, filepath.Base(path))
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Uploaded: %s (upload ID: %s)\n", upload.Message, upload.UploadId)

	// 3. Trigger ingestion
	_, err = client.Datasources.Ingest.Trigger(ctx, ds.Id)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println("Ingestion triggered")

	// 4. Wait for ingestion to finish
	for {
		status, err := client.Datasources.Ingest.GetStatus(ctx, ds.Id)
		if err != nil {
			log.Fatal(err)
		}
		fmt.Printf("  Status: %s\n", status.Status)
		if status.Status == meibel.IngestStatusCompleted || status.Status == meibel.IngestStatusFailed ||
			status.Status == meibel.IngestStatusCanceled || status.Status == meibel.IngestStatusTimedOut ||
			status.Status == meibel.IngestStatusTerminated {
			break
		}
		time.Sleep(5 * time.Second)
	}

	// 5. List data elements
	iter := client.Datasources.DataElements.List(ctx, ds.Id, nil)
	fmt.Println("\nData elements:")
	for iter.Next(ctx) {
		elem := iter.Item()
		fmt.Printf("  - %s\n", elem.Id)
	}
	if err := iter.Err(); err != nil {
		log.Fatal(err)
	}

	// 6. Export
	export, err := client.Datasources.Downloads.Process(ctx, ds.Id, nil)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Export: %d bytes\n", len(*export))

	// 7. Cleanup
	_, err = client.Datasources.Delete(ctx, ds.Id)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Deleted datasource: %s\n", ds.Id)
}
