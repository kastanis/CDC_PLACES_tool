# Optional LLM Parser

The tool has two parsing modes:

- `rules`: deterministic parser, default
- `ollama`: free local LLM parser
- `openai`: hosted OpenAI parser
- `auto`: try Ollama first, fall back to rules if unavailable

The LLM does not answer questions. It only returns structured JSON intent.

Example intent:

```json
{
  "operation": "rank",
  "measure_id": "uninsured",
  "state": "CA",
  "direction": "highest",
  "limit": 10,
  "confidence": "high"
}
```

The semantic layer still decides whether that intent is valid.

## Local Setup

Install Ollama and pull a small local model:

```bash
ollama pull llama3.2
```

Make sure Ollama is running, then try:

```bash
places ask --parser ollama "Show me where insurance access looks worst in California"
```

Optional environment variables:

```text
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
OLLAMA_TIMEOUT=20
```

## Hosted OpenAI Parser

```bash
export OPENAI_API_KEY="..."
export OPENAI_MODEL="gpt-4o-mini"
places ask --parser openai "Show me where insurance access looks worst in California"
```

The OpenAI parser uses the Responses API with structured JSON output.

## Streamlit

The Streamlit app includes a parser toggle in the Ask tab:

- Rules
- Local LLM via Ollama
- OpenAI
- Auto fallback

For Streamlit Community Cloud, local Ollama will not be available unless you run the app on infrastructure that also runs Ollama. In hosted Streamlit, use the rules parser by default.

OpenAI parser mode can work in hosted Streamlit if you add the key to Streamlit secrets. It will use API credits.
