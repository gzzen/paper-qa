# PaperQA Local Quick Start

Run PaperQA against papers stored on your machine, using DeepSeek for language
model calls and local sparse embeddings for document retrieval.

The `deepseek` preset:

- Uses `deepseek/deepseek-flash` for answering, summaries, and agent decisions.
- Builds embeddings locally with the built-in `sparse` model.
- Disables Crossref and Semantic Scholar metadata lookups.
- Disables media extraction and enrichment.
- Indexes papers from `data.mock/` by default.

Document text is sent to DeepSeek when PaperQA extracts citations, summarizes
evidence, or answers a question. Your paper folder and search index remain local.

## Requirements

- Python 3.11 through 3.14
- [uv](https://docs.astral.sh/uv/)
- A DeepSeek API key
- PDFs or other supported documents in a local folder

Supported inputs include PDF, text, Markdown, HTML, DOCX, XLSX, and PPTX.

## 1. Install

From the repository root:

```bash
uv sync --no-dev
```

## 2. Configure DeepSeek

Create your local environment file:

```bash
cp .env.example .env
```

Set your key in `.env`:

```dotenv
DEEPSEEK_API_KEY=your_deepseek_api_key
```

PaperQA loads `.env` from the current directory or a parent directory. Variables
exported by your shell take precedence over values in `.env`.

No OpenAI, Crossref, or Semantic Scholar key is required.

## 3. Add papers

The bundled `deepseek` preset uses:

```text
data.mock/
```

Place papers there, including in subdirectories. To use another folder without
editing configuration, pass it on the command line:

```bash
pqa -s deepseek \
  --agent.index.paper_directory /path/to/papers \
  ask "What are the main findings?"
```

Relative paths are resolved from the directory where you run `pqa`.

## 4. Ask a question

```bash
pqa -s deepseek ask "What are the main findings?"
```

PaperQA builds or updates the local index automatically, retrieves relevant
passages, summarizes them, and produces a cited answer.

Always include `-s deepseek`. Running plain `pqa ask` selects another preset and
may attempt to use OpenAI or external metadata services.

## Inspect the configuration

```bash
pqa -s deepseek view
```

The important settings should show:

```text
llm            deepseek/deepseek-flash
summary_llm    deepseek/deepseek-flash
embedding      sparse
use_doc_details false
multimodal     false
```