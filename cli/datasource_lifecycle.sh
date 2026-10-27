#!/usr/bin/env bash
# Datasource Lifecycle: create, upload, ingest, query, export, delete.
set -euo pipefail

# 1. Create a datasource
DS=$(meibel datasources create \
  --data '{"name":"Legal Documents","description":"Contracts and agreements","connector":{"type":"managed"}}')
DS_ID=$(echo "$DS" | jq -r '.datasource_id')
echo "Created datasource: $DS_ID"

# 2. Upload a file
meibel content upload --file contract.pdf
echo "Uploaded file"

# 3. Trigger ingestion and wait
meibel content trigger-ingest "$DS_ID"
echo "Waiting for ingestion..."
sleep 10

# 4. List data elements
echo -e "\nData elements:"
meibel data-elements list

# 5. Search data elements
meibel data-elements search \
  --data '{"regex_filter":"termination"}'

# 6. Export
meibel downloads process "$DS_ID"

# 7. Cleanup
meibel datasources delete "$DS_ID"
echo "Deleted datasource: $DS_ID"
