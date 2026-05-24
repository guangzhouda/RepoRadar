# RepoRadar

RepoRadar helps developers avoid reinventing the wheel.

Given a project idea, it searches GitHub for related repositories, analyzes their README, docs, source files, and metadata, generates structured capability cards, and produces a comparison report to help decide whether to reuse, fork, integrate, or build from scratch.

## Current Status

This repository is at MVP phase 0: project bootstrap.

Available now:

- Python project structure
- Environment variable template
- Minimal runnable CLI health check
- Placeholder modules for the planned MVP pipeline

Planned next:

- Project idea understanding
- GitHub Search API integration
- README and docs collection
- Repo Skill Card generation
- Evidence-based capability extraction
- Repository scoring
- Markdown report export
- Streamlit demo UI

## Requirements

- Python 3.11 or newer is the target runtime
- Git
- A GitHub token for GitHub API calls in later phases
- An LLM API key for extraction in later phases

The bootstrap code uses only the Python standard library.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e .
Copy-Item .env.example .env
```

Edit `.env` and set credentials when you start implementing API-backed stages.

## Run

```bash
python -m app.main --check-config
```

You can also use the planned analysis entry point. At phase 0 it returns a bootstrap preview and does not call GitHub or an LLM.

```bash
python scripts/analyze_idea.py --idea "I want to build a tool that converts EPUB/PDF files into TTS audio with synchronized subtitles."
```

## Configuration

The project reads these variables from the process environment:

- `GITHUB_TOKEN`
- `GITHUB_SEARCH_PER_PAGE`
- `LLM_PROVIDER`
- `LLM_API_KEY`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `REPORADAR_CACHE_DIR`
- `REPORADAR_LOG_LEVEL`

Use `.env.example` as the source of truth for local configuration.

## Project Layout

```text
app/
  api/          API route modules planned for FastAPI
  core/         configuration, logging, and shared errors
  models/       repository, skill card, and report data structures
  services/     query, search, collection, extraction, scoring, reports
  providers/    GitHub and LLM provider boundaries
  db/           persistence boundary for later phases
docs/           architecture and schema notes
examples/       input ideas and sample outputs
frontend/       Streamlit UI placeholder
scripts/        command-line entry points
tests/          bootstrap regression tests
```

## Roadmap

- [ ] CLI prototype
- [ ] GitHub Search API integration
- [ ] Repo Skill Card schema
- [ ] LLM capability extraction
- [ ] Evidence verification
- [ ] Comparison report generation
- [ ] Streamlit UI
- [ ] GitHub MCP integration
