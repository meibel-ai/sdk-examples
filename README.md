# Meibel SDK Examples

End-to-end lifecycle examples for the Meibel API across Python, TypeScript, Go, and CLI. Each example creates a resource, uses it, and cleans up.

## Prerequisites

- A Meibel API key from [console.meibel.ai](https://console.meibel.ai)
- A sample PDF file for document/datasource examples

## Setup

### Python

```bash
cd python
pip install meibel
export MEIBEL_API_KEY="your-api-key"
python agent_lifecycle.py
```

### TypeScript

```bash
cd typescript
npm install
export MEIBEL_API_KEY="your-api-key"
npx tsx agent-lifecycle.ts
```

### Go

```bash
cd go
go mod tidy
export MEIBEL_API_KEY="your-api-key"
go run agent_lifecycle.go
```

### CLI

```bash
brew install meibel-ai/tap/meibel
export MEIBEL_API_KEY="your-api-key"
bash cli/agent_lifecycle.sh
```

## Examples

| Example | What it demonstrates |
|---------|---------------------|
| `agent_lifecycle` | Create agent → publish → create session → chat → stream response → inspect messages → delete |
| `datasource_lifecycle` | Create datasource → upload files → trigger ingest → list data elements → search → export → delete |
| `document_lifecycle` | Parse document (async) → poll status → get results (markdown/JSON) → list children → sync parse → stream trace |
| `document_transform` | Extract structured data from a document using a typed model, a raw JSON Schema, or a registered artifact schema |
| `artifact_lifecycle` | Create artifact schemas of every type, with and without typed models |
| `artifact_schema` | Define typed output schemas for agents |

Python-only examples:

| Example | What it demonstrates |
|---------|---------------------|
| `bulk_upload.py` | Upload a folder of PDFs concurrently to one datasource, ingest, and report timing (`UPLOAD_FOLDER`) |
| `datasource_bulk_upload_benchmark.py` | Benchmark massively parallel uploads of a directory tree (`--dir`) |
| `deep_transform.py` | Submit a schema-guided deep transform job |
| `structured_and_move.py` | Fetch a typed structured parse result and move documents |
| `list_agents.py` / `version.py` | List agents; print the installed SDK version |

Examples that read a local file take its path from `DOCUMENT_FILE`:

```bash
export DOCUMENT_FILE="path/to/sample.pdf"
```

## SDK Links

- [Python SDK](https://github.com/meibel-ai/meibel-python)
- [TypeScript SDK](https://github.com/meibel-ai/meibel-typescript)
- [Go SDK](https://github.com/meibel-ai/meibel-go)
- [CLI](https://github.com/meibel-ai/meibel-cli)
- [Documentation](https://docs.meibel.ai)

## License

[MIT](LICENSE)
