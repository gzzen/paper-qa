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

## Use from DSH

Install the optional MCP dependency and start the stdio server:

```bash
uv sync --no-dev --extra mcp
uv run --extra mcp paperqa-mcp
```

The server exposes one tool, `paperqa_ask`, which returns `answer`,
`formatted_answer`, `status`, `cost`, and `source_count`. It uses the `deepseek`
settings preset by default. Override the preset or its paper folder with:

```bash
PAPERQA_SETTINGS=deepseek \
PAPERQA_PAPER_DIRECTORY=/path/to/papers \
uv run --extra mcp paperqa-mcp
```

`PQA_HOME` and `TMPDIR` retain their existing PaperQA behavior. Queries in one
server process are serialized because the underlying search and answer indexes
are not safe for concurrent writes.

The checked-in overlay targets DSH `0.2.2-rc.5`. From this repository root:

```bash
mkdir -p .tmp
npm install --global @deepseek-ai/dsh@0.2.2-rc.5
dsh web --patch "$PWD/examples/dsh-paperqa.cordis.yml"
```

DSH scrubs credential-like environment variables from stdio MCP children, so
the overlay explicitly passes `DEEPSEEK_API_KEY`. It also keeps PaperQA's index
and temporary state in ignored project-local directories. DSH discovers the
tool as `mcp__paperqa__paperqa_ask` and allows up to ten minutes per call.

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

## Settings Cheatsheet

| Setting                                      | Default                                | Description                                                                                                                   |
| -------------------------------------------- | -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `llm`                                        | `"openai/gpt-6.1-sol"`                 | LLM for general use including metadata inference (see Docs.aadd) and answer generation (see Docs.aquery and gen_answer tool). |
| `llm_config`                                 | `None`                                 | Optional configuration for `llm`.                                                                                             |
| `summary_llm`                                | `"openai/gpt-6-luna"`                  | LLM for creating contextual summaries (see Docs.aget_evidence and gather_evidence tool).                                      |
| `summary_llm_config`                         | `None`                                 | Optional configuration for `summary_llm`.                                                                                     |
| `embedding`                                  | `"text-embedding-3-small"`             | Embedding model for embedding text chunks when adding papers.                                                                 |
| `embedding_config`                           | `None`                                 | Optional configuration for `embedding`.                                                                                       |
| `temperature`                                | `None`                                 | Optional temperature for LLMs; omitted when unset.                                                                            |
| `batch_size`                                 | `1`                                    | Batch size for calling LLMs.                                                                                                  |
| `texts_index_mmr_lambda`                     | `1.0`                                  | Lambda for MMR in text index.                                                                                                 |
| `verbosity`                                  | `0`                                    | Integer verbosity level for logging (0-3). 3 = all LLM/Embeddings calls logged.                                               |
| `custom_context_serializer`                  | `None`                                 | Custom async function (see typing for signature) to override the default answer context serialization.                        |
| `answer.evidence_k`                          | `10`                                   | Number of evidence pieces to retrieve.                                                                                        |
| `answer.evidence_retrieval`                  | `True`                                 | Use retrieval vs processing all docs.                                                                                         |
| `answer.evidence_summary_length`             | `"about 100 words"`                    | Length of evidence summary.                                                                                                   |
| `answer.evidence_skip_summary`               | `False`                                | Whether to skip summarization.                                                                                                |
| `answer.evidence_text_only_fallback`         | `False`                                | Whether to allow context creation to retry without media present.                                                             |
| `answer.answer_max_sources`                  | `5`                                    | Max number of sources for an answer.                                                                                          |
| `answer.max_answer_attempts`                 | `None`                                 | Max attempts to generate an answer.                                                                                           |
| `answer.answer_length`                       | `"about 200 words, but can be longer"` | Length of final answer.                                                                                                       |
| `answer.max_concurrent_requests`             | `4`                                    | Max concurrent requests to LLMs.                                                                                              |
| `answer.answer_filter_extra_background`      | `False`                                | Whether to cite background info from model.                                                                                   |
| `answer.get_evidence_if_no_contexts`         | `True`                                 | Allow lazy evidence gathering.                                                                                                |
| `answer.group_contexts_by_question`          | `False`                                | Groups the final contexts by the underlying `gather_evidence` question in the final context prompt.                           |
| `answer.evidence_relevance_score_cutoff`     | `1`                                    | Cutoff evidence relevance score to include in the answer context (inclusive)                                                  |
| `answer.skip_evidence_citation_strip`        | `False`                                | Skip removal of citations from the `gather_evidence` contexts                                                                 |
| `parsing.page_size_limit`                    | `1,280,000`                            | Character limit per page.                                                                                                     |
| `parsing.use_doc_details`                    | `True`                                 | Whether to get metadata details for docs.                                                                                     |
| `parsing.reader_config`                      | `dict`                                 | Optional keyword arguments for the document reader.                                                                           |
| `parsing.multimodal`                         | `True`                                 | Control to parse both text and media from applicable documents, as well as potentially enriching them with text descriptions. |
| `parsing.defer_embedding`                    | `False`                                | Whether to defer embedding until summarization.                                                                               |
| `parsing.parse_pdf`                          | `paperqa_pypdf.parse_pdf_to_pages`     | Function to parse PDF files.                                                                                                  |
| `parsing.configure_pdf_parser`               | No-op                                  | Callable to configure the PDF parser within `parse_pdf`, useful for behaviors such as enabling logging.                       |
| `parsing.doc_filters`                        | `None`                                 | Optional filters for allowed documents.                                                                                       |
| `parsing.use_human_readable_clinical_trials` | `False`                                | Parse clinical trial JSONs into readable text.                                                                                |
| `parsing.enrichment_llm`                     | `"openai/gpt-6.1-sol"`                 | LLM for media enrichment.                                                                                                     |
| `parsing.enrichment_llm_config`              | `None`                                 | Optional configuration for `enrichment_llm`.                                                                                  |
| `parsing.enrichment_page_radius`             | `1`                                    | Page radius for context text in enrichment.                                                                                   |
| `parsing.enrichment_prompt`                  | `image_enrichment_prompt_template`     | Prompt template for enriching media.                                                                                          |
| `parsing.citation_prompt`                    | `citation_prompt`                      | Prompt to create citation from peeking one chunk.                                                                             |
| `parsing.structured_citation_prompt`         | `structured_citation_prompt`           | Prompt to create a citation (in JSON) from peeking one chunk.                                                                 |
| `parsing.disable_doc_valid_check`            | `False`                                | Flag to disable checking if a document looks like text (was parsed correctly).                                                |
| `prompts.summary`                            | `summary_prompt`                       | Template for summarizing text, must contain variables matching `summary_prompt`.                                              |
| `prompts.qa`                                 | `qa_prompt`                            | Template for QA, must contain variables matching `qa_prompt`.                                                                 |
| `prompts.select`                             | `select_paper_prompt`                  | Template for selecting papers, must contain variables matching `select_paper_prompt`.                                         |
| `prompts.pre`                                | `None`                                 | Optional pre-prompt templated with just the original question to append information before a qa prompt.                       |
| `prompts.post`                               | `None`                                 | Optional post-processing prompt that can access PQASession fields.                                                            |
| `prompts.system`                             | `default_system_prompt`                | System prompt for the model.                                                                                                  |
| `prompts.use_json`                           | `True`                                 | Whether to use JSON formatting.                                                                                               |
| `prompts.summary_json`                       | `summary_json_prompt`                  | JSON-specific summary prompt.                                                                                                 |
| `prompts.summary_json_system`                | `summary_json_system_prompt`           | System prompt for JSON summaries.                                                                                             |
| `prompts.context_outer`                      | `CONTEXT_OUTER_PROMPT`                 | Prompt for how to format all contexts in generate answer.                                                                     |
| `prompts.context_inner`                      | `CONTEXT_INNER_PROMPT`                 | Prompt for how to format a single context in generate answer. Must contain 'name' and 'text' variables.                       |
| `prompts.answer_iteration_prompt`            | `answer_iteration_prompt_template`     | Prompt to inject existing prior answers to allow iteration. Default injects no prior answers.                                 |
| `agent.agent_llm`                            | `"openai/gpt-6-sol"`                   | LLM inside the agent making tool selections.                                                                                  |
| `agent.agent_llm_config`                     | `None`                                 | Optional configuration for `agent_llm`.                                                                                       |
| `agent.agent_type`                           | `"ToolSelector"`                       | Type of agent to use.                                                                                                         |
| `agent.agent_config`                         | `None`                                 | Optional kwarg for AGENT constructor.                                                                                         |
| `agent.agent_system_prompt`                  | `env_system_prompt`                    | Optional system prompt message.                                                                                               |
| `agent.agent_prompt`                         | `env_reset_prompt`                     | Agent prompt.                                                                                                                 |
| `agent.return_paper_metadata`                | `False`                                | Whether to include paper title/year in search tool results.                                                                   |
| `agent.search_count`                         | `8`                                    | Search count.                                                                                                                 |
| `agent.timeout`                              | `500.0`                                | Timeout on agent execution (seconds).                                                                                         |
| `agent.tool_names`                           | `None`                                 | Optional override on tools to provide the agent.                                                                              |
| `agent.max_timesteps`                        | `None`                                 | Optional upper limit on environment steps.                                                                                    |
| `agent.agent_evidence_n`                     | `1`                                    | Top n ranked evidences shown to the agent after gathering evidence.                                                           |
| `agent.rebuild_index`                        | `True`                                 | Flag to rebuild the index at the start of agent runners.                                                                      |
| `agent.callbacks`                            | `{}`                                   | Named lists of callables to be invoked with environment state.                                                                |
| `agent.index.name`                           | `None`                                 | Optional name of the index.                                                                                                   |
| `agent.index.paper_directory`                | `Current working directory`            | Directory containing papers to be indexed.                                                                                    |
| `agent.index.manifest_file`                  | `None`                                 | Path to manifest CSV with document attributes.                                                                                |
| `agent.index.index_directory`                | `pqa_directory("indexes")`             | Directory to store PQA indexes.                                                                                               |
| `agent.index.use_absolute_paper_directory`   | `False`                                | Whether to use absolute paper directory path.                                                                                 |
| `agent.index.recurse_subdirectories`         | `True`                                 | Whether to recurse into subdirectories when indexing.                                                                         |
| `agent.index.concurrency`                    | `5`                                    | Number of concurrent filesystem reads.                                                                                        |
| `agent.index.sync_with_paper_directory`      | `True`                                 | Whether to sync index with paper directory on load.                                                                           |
| `agent.index.batch_size`                     | `1`                                    | Number of files to process before committing to the index.                                                                    |
| `agent.index.files_filter`                   | `lambda f: f.suffix in {...}`          | Filter function to mark files in the paper directory to index.                                                                |
