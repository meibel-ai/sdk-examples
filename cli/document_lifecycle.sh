#!/usr/bin/env bash
# Document Lifecycle: parse, poll, get results, sync process.
set -euo pipefail

# 1. Parse a document (async)
PARSE=$(meibel documents parse --file report.pdf)
JOB_ID=$(echo "$PARSE" | jq -r '.job_id')
echo "Parse job: $JOB_ID"

# 2. Poll for status
while true; do
  STATUS=$(meibel documents get-status "$JOB_ID" | jq -r '.status')
  echo "Status: $STATUS"
  [[ "$STATUS" == "completed" || "$STATUS" == "failed" ]] && break
  sleep 2
done

# 3. Get result as markdown
echo -e "\nMarkdown result:"
meibel documents get-result "$JOB_ID"

# 4. Get result as JSON
echo -e "\nJSON result:"
meibel documents get-result "$JOB_ID"

# 5. List children
echo -e "\nChildren:"
meibel documents list-children "$JOB_ID"

# 6. Process document synchronously
echo -e "\nSync parse:"
meibel documents parse --file report.pdf --wait
