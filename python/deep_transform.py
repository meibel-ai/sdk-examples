"""Deep Transform: submit a document for schema-guided extraction.

Usage:
    export MEIBEL_API_KEY="..."
    export DOCUMENT_FILE="path/to/document.pdf"
    export SCHEMA_FILE="path/to/schema.json"
    export GUIDANCE_FILE="path/to/guidance.md"
    python deep_transform.py
"""

import json
import os
from meibel import MeibelClient

client = MeibelClient(api_key=os.environ["MEIBEL_API_KEY"])

file = os.environ["DOCUMENT_FILE"]
schema_file = os.environ["SCHEMA_FILE"]
guidance_file = os.environ["GUIDANCE_FILE"]

with open(schema_file) as f:
    schema = json.load(f)

with open(guidance_file) as f:
    guidance = f.read()

job = client.documents.submit_deep_transform(
    file=file,
    schema=schema,
    root_name=os.environ.get("ROOT_NAME", "Document"),
    guidance=guidance,
)

print("Job submitted:", job.job_id)
