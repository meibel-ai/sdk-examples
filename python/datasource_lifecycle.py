"""Datasource Lifecycle: create, upload, ingest, query, export, delete."""

import os
import time
from meibel import MeibelClient
from meibel.models import CreateDatasourceRequest, ConnectorConfig, DataElementSearchRequest

client = MeibelClient(api_key=os.environ["MEIBEL_API_KEY"])

file_path = os.environ["DOCUMENT_FILE"]


# 1. Create a datasource
datasource = client.datasources.create(
    name="sdk test",
    description="Test datasource created via SDK",
)
datasource_id = datasource.id


# 2. Upload files
with open(file_path, "rb") as f:
    upload = client.datasources.file_uploads.upload_content(
        datasource_id=datasource.id,
        files=f,
        files_name=os.path.basename(file_path)
    )
    datasource_id = upload.datasource_id

print(f"Uploaded file: {upload}")

# 3. Trigger ingestion
client.datasources.ingest.trigger(datasource_id=datasource_id)
print("Ingestion triggered")

# 4. Wait for ingestion (poll status)
status = client.datasources.ingest.get_status(datasource_id=datasource_id)

time.sleep(10)

# 5. List data elements
print("\nData elements:")
for element in client.datasources.data_elements.list(datasource_id=datasource_id):
    print(f"  - {element.id}: {element.name}")

# 6. Search data elements
results = client.datasources.data_elements.search(
    datasource_id=datasource_id,
    body=DataElementSearchRequest(regex_filter="termination"),
)
print(f"\nSearch returned {len(results.items)} results")

# 7. Export the datasource
export = client.datasources.downloads.process(datasource_id=datasource_id)
if isinstance(export, bytes):
    out_path = f"/tmp/{datasource_id}_export.zip"
    with open(out_path, "wb") as f:
        f.write(export)
    print(f"Export saved: {out_path} ({len(export)} bytes)")
else:
    print(f"Export: {type(export)} ({len(str(export))} chars)")

# 8. Cleanup — delete the datasource
client.datasources.delete(datasource_id=datasource_id)
print(f"Deleted datasource: {datasource_id}")
