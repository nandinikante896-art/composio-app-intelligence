# Composio App Intelligence Agent

## Objective

Build an evidence-led, reproducible research pipeline for 100 applications and assess authentication, developer access, API surface, MCP status, and integration buildability. The system preserves unknowns and never presents unverified facts as complete research.

## Workspace gap and implementation

The original workspace was a Node.js evidence checker and static HTML prototype. This project now adds:

- a Python/Pydantic 100-app pipeline;
- no-key web search through DDGS and structured extraction through local Ollama;
- field-level quote citations and a separate model verification pass;
- bounded retries, a seven-day source cache, and resumable checkpoints;
- an optional official Composio Python SDK session/MCP endpoint check;
- HTTPX/BeautifulSoup evidence retrieval;
- checkpoints and bounded concurrency;
- JSON, CSV, JSONL, metrics, insights, audit, and dashboard outputs;
- honest human-verification and no-fabrication safeguards.

## Architecture

- `data/apps.csv`: exactly 100 unique applications.
- `src/agents/researcher.py`: source discovery, retrieval, and structured extraction.
- `src/agents/verifier.py`: second-pass verification and error recording.
- `src/tools/search.py`: DDGS web-search adapter; no search API key is required.
- `src/tools/browser.py`: bounded HTTP retrieval and text extraction.
- `src/tools/composio_tools.py`: honest optional Composio status.
- `src/pipeline/orchestrator.py`: pipeline, checkpoints, exports, and validation.
- `src/analysis/`: insights, metrics, and dashboard generation.
- `src/schemas/research.py`: Pydantic evidence and application models.

## Installation

Use a stable Python 3.11–3.13 runtime. Preview Python runtimes may not have compatible native wheels for Pydantic and provider SDKs.

```sh
python -m pip install -r requirements.txt
python main.py --prepare-data
python -m pytest tests -q
```

PowerShell:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and supply only credentials you own. `main.py` loads the `.env` file when starting.

## Environment

Supported variables:

- `OLLAMA_BASE_URL` (defaults to `http://localhost:11434`)
- `OLLAMA_MODEL` (defaults to `qwen2.5:3b`)
- `COMPOSIO_API_KEY`

Research uses the local Ollama API and DDGS, so OpenAI and Tavily API keys are not required. The configured Ollama model must be downloaded and the Ollama service must be running.

## Run

Before research starts, the pipeline checks that Ollama is reachable and the configured model is installed. On failure it stops before changing the research result files.

Three-app pilot (written to an isolated timestamped folder under `output/pilots/`):

```sh
python main.py --limit 3
```

Ten-app pilot:

```sh
python main.py --limit 10 --workers 3
```

Inspect both pilot result JSON/CSV files before moving on. Run a full pass only after the pilot produces cited findings:

```sh
python main.py --limit 100 --workers 3
```

Resume an interrupted run from its checkpoint:

```sh
python main.py --limit 100 --workers 3 --resume
```

Generate the dashboard:

```sh
python main.py --generate-report
```

Open `dashboard/index.html`.

Audit existing JSON/CSV results and create a 10-app, one-per-category manual-review sample:

```sh
python main.py --audit-quality
```

This writes `output/data_quality_report.json` and `output/verification_sample.csv` without rewriting `research_results.json` or `research_results.csv`. Reviewers must replace `PENDING` only after checking the sources and findings.

## Human verification

Complete `output/verification_sample.csv` after reviewing the sources:

1. Review `original_findings` and the official documentation URLs for each application.
2. Enter the human-adjudicated findings in `verified_findings`.
3. Set `reviewer_decision` to `correct`, `incorrect`, or `unknown`.
4. Record evidence gaps or corrections in `correction_notes`.
5. Change `review_status` from `PENDING` to `COMPLETED` only after a human has reviewed the record.

The sample contains the first application in each of the 10 categories; it is not random. Run `python main.py --audit-quality` to refresh the audit report after review. Accuracy remains unmeasured until human adjudication is actually recorded.

## Composio and MCP

### SDK/MCP usage status

| Item | Current status |
|---|---|
| Official Composio SDK inspected | Yes; current Python v3 quickstart and sessions-via-MCP documentation |
| SDK installed | Optional; install `requirements-composio.txt` to enable it |
| `COMPOSIO_API_KEY` configured | No |
| Live Composio tool call executed | No |
| Composio MCP integration used | No |
| Vendor MCP research completed | Depends on configured research providers; results carry field-level citations |
| Human MCP verification completed | No |

The official Python SDK docs use `from composio import Composio`, `client.sessions.create(user_id=..., mcp=True)`, and `session.tools()`. This project follows that API for a real, non-destructive tool-discovery check; it does not read or modify connected app data. Official references:

- [Composio Python quickstart](https://docs.composio.dev/docs/quickstart)
- [Composio sessions via MCP](https://docs.composio.dev/docs/sessions-via-mcp)

To install the optional SDK and execute the check:

```sh
python -m pip install -r requirements-composio.txt
python main.py --check-composio
```

The check creates one SDK session, enumerates its tools, and requests an MCP endpoint. It does not connect an MCP protocol client, invoke app tools, or claim a live app integration. Without `COMPOSIO_API_KEY`, it skips and reports that fact.

Each app uses one Ollama generation call for extraction; verification is deterministic and does not make another model call. The researcher searches with DDGS, fetches official vendor documentation, and sends only bounded relevant excerpts to Ollama. Citation URL existence, fetch status, quote matching, vendor-domain match, and field-specific relevance are recorded independently. These provenance checks do not prove semantic support: claim semantics remain pending human review. MCP always means the Model Context Protocol.

Ollama calls use `qwen2.5:3b`, temperature 0, `num_predict=700`, `num_ctx=4096`, one-at-a-time inference, and a per-request timeout. Progress and research outputs are flushed after each app; interrupted runs can resume from their checkpoint.

## Required outputs

- `output/research_results.json`
- `output/research_results.csv`
- `output/evidence_log.jsonl`
- `output/verification_sample.csv`
- `output/verification_metrics.json`
- `output/insights.json`
- `output/data_quality_report.json`
- `output/checkpoints/resume.json`

Pilot runs are isolated under `output/pilots/`. A full run archives existing result files under `output/archive/` before replacing them.

## GitHub Pages

1. Create a GitHub repository and push the project.
2. Open **Repository Settings → Pages**.
3. Set source to the default branch and root, or deploy `dashboard/index.html` through GitHub Actions.
4. GitHub will provide the live URL after a successful Pages deployment.

No live URL is claimed until that deployment actually exists.

## Limitations

- Vendor URLs may change or block automated retrieval.
- HTTP success and quote matching verify provenance only, not whether a claim is semantically correct; human review is still required.
- Access tiers, MCP provenance, pricing, and partner gates require current source/human review.
- Partial runs preserve checkpoints; use `--resume` to continue.
- The project uses DDGS without a search API key. Ollama must be running locally and have the selected model available; `COMPOSIO_API_KEY` is only needed for the optional Composio SDK check.
- The workspace virtual environment is Python 3.15 preview, where the installed Pydantic native core fails to load. The test suite passed on the available Python 3.13.9 Anaconda interpreter; use a stable interpreter for research runs.
