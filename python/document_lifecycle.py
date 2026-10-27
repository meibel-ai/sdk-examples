"""Document Lifecycle: parse (async + sync), poll, get results, trace."""

import os
import time
from meibel import MeibelClient

client = MeibelClient(
    api_key=os.environ["MEIBEL_API_KEY"],
)

FILE = os.environ["DOCUMENT_FILE"]
FILE_NAME = os.path.basename(FILE)

# --- Async parsing flow ---

# 1. Parse a document asynchronously (returns job_id)
with open(FILE, "rb") as f:
    parse_result = client.documents.parse(file=f, file_name=FILE_NAME)
job_id = parse_result.job_id
print(f"Parse job started: {job_id}")

# 2. Poll for document status
while True:
    status = client.documents.get_status(job_id=job_id)
    print(f"Status: {status.status}")
    if status.status in ("completed", "failed"):
        break
    time.sleep(1)

# 3. Get result as markdown
markdown_result = client.documents.get_result(job_id=job_id, format="markdown")
if markdown_result:
    print(f"\nMarkdown result ({len(markdown_result)} chars):")
    print(markdown_result[:500])
else:
    # SDK bug: get_result returns None for text/plain responses (markdown).
    # Workaround: use the JSON format which returns a parseable response.
    print("\nMarkdown result: (returned None — SDK text/plain parsing issue)")

# 4. Get result as JSON
json_result = client.documents.get_result(job_id=job_id, format="json")
if json_result:
    print(f"\nJSON result: {type(json_result)}")
    if isinstance(json_result, dict):
        print(f"  Keys: {list(json_result.keys())}")
    elif isinstance(json_result, str):
        print(f"  ({len(json_result)} chars)")
else:
    print("\nJSON result: None")

# 5. List child documents (for multi-page/compound documents)
children = client.documents.list_children(job_id=job_id)
print(f"\nChild documents: {len(children)}")

# --- Sync parsing flow ---

# 6. Process a document synchronously (blocks until complete)
print("\nStarting sync parse...")
with open(FILE, "rb") as f:
    result = client.documents.process(file=f, file_name=FILE_NAME)
print(f"Sync parse complete: status={result.status}, job_id={result.job_id}")
print(f"""
{result.result}
""")
