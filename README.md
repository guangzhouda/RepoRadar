# RepoRadar

RepoRadar 是一个面向开发者的 GitHub 开源项目发现与能力分析工具。

## Project Overview

RepoRadar 的目标是：给定一个项目想法，帮助用户发现相似 GitHub 仓库，分析仓库 README、文档、源码和元数据，生成结构化能力卡和横向对比报告，从而判断应该复用、fork、集成还是从零开发。

当前代码依据：`README.md`、`pyproject.toml`、`app/main.py`、`scripts/analyze_idea.py`、`app/services/*`、`tests/test_bootstrap.py`。
本地开发环境可能包含 `docs/` 和 `repo_radar_project_planning_document.md` 作为规划资料；它们按仓库策略不追踪、不推送。

## Features

已实现：

- Python 包骨架和命令入口。
- `.env` 配置读取，且进程环境变量覆盖 `.env`。
- `--check-config` 配置健康检查。
- `scripts/analyze_idea.py` 的 Phase 1 LLM query planning + GitHub repository search CLI。
- 多 query 生成、候选仓库标准化、去重、排序和 JSON 缓存。
- LLM 候选相关性评审，输出 `relevance_score`、`decision`、`reject_reason` 和 `rationale`。
- 候选列表保留 `reject` 项用于人工审查，不在展示层直接隐藏。
- `scripts/fetch_repo.py` 的 Phase 2 仓库抓取 CLI，可抓取仓库元数据和 MVP README/docs/config 文件。
- LLM Repo Skill Card 抽取，输出项目类别、输入/输出格式、接口形态、核心能力、限制、证据和置信度。
- DeepSeek / OpenAI 兼容 LLM 的通用配置项。
- 标准库 `unittest` bootstrap 测试。

部分实现：

- Query understanding 的规则实现仍保留为 `--query-mode rules` 诊断 fallback，默认路径已经使用 LLM。
- Repo Skill Card 已有单仓库抽取 CLI，但还没有接入批量候选分析流水线。
- 报告、证据校验、评分模块仍是后续阶段占位。

待确认：

- 最终 CLI 输出格式是否同时包含 JSON 和 Markdown。
- 是否使用 `unittest` 继续扩展，还是切换到 `pytest`。
- Streamlit demo 是否在 v0.1 后立即推进，规划文档将其列为第 4 阶段。

## Quick Start

```powershell
py -3.14 -m venv .venv
.venv\Scripts\Activate.ps1
py -3.14 -m pip install -e .
Copy-Item .env.example .env
py -3.14 -m app.main --check-config
```

LLM query 预览：

```powershell
py -3.14 scripts\analyze_idea.py --idea "I want to build a tool that converts EPUB/PDF files into TTS audio with synchronized subtitles." --max-repos 10 --offline
```

规则 fallback 预览，仅用于诊断或没有 LLM key 时：

```powershell
py -3.14 scripts\analyze_idea.py --idea "project idea" --offline --query-mode rules
```

运行 GitHub 搜索：

```powershell
py -3.14 scripts\analyze_idea.py --idea "I want to build a tool that converts EPUB/PDF files into TTS audio with synchronized subtitles." --max-repos 10
```

Markdown 输出：

```powershell
py -3.14 scripts\analyze_idea.py --idea "project idea" --max-repos 10 --format markdown
```

抓取单个仓库的 README/docs/config 摘要：

```powershell
py -3.14 scripts\fetch_repo.py --repo denizsafak/abogen
```

抓取单个仓库并用 LLM 生成 Repo Skill Card：

```powershell
py -3.14 scripts\fetch_repo.py --repo denizsafak/abogen --extract-card
```

搜索候选仓库并为保留候选生成 Repo Skill Card：

```powershell
py -3.14 scripts\analyze_idea.py --idea "project idea" --max-repos 5 --extract-cards --card-limit 2
```

## Configuration

`.env.example` 包含当前支持的配置项：

- `GITHUB_TOKEN`
- `GITHUB_API_BASE_URL`
- `GITHUB_SEARCH_PER_PAGE`
- `LLM_PROVIDER`
- `LLM_API_KEY`
- `LLM_BASE_URL`
- `LLM_MODEL`
- `REPORADAR_CACHE_DIR`
- `REPORADAR_LOG_LEVEL`

## Project Structure

```text
app/        应用代码；按 api/core/models/services/providers/db 分层
scripts/    命令行入口和后续脚本
tests/      标准库 unittest 测试
examples/   示例输入和占位报告
frontend/   Streamlit UI 占位
docs/       本地规划/交接文档，不进入版本控制
```

## Development Commands

安装：

```powershell
py -3.14 -m pip install -e .
```

运行健康检查：

```powershell
py -3.14 -m app.main --check-config
```

运行 idea 预览：

```powershell
py -3.14 scripts\analyze_idea.py --idea "project idea" --max-repos 10 --offline
```

运行单仓库抓取：

```powershell
py -3.14 scripts\fetch_repo.py --repo owner/repo
```

测试：

```powershell
py -3.14 -m unittest discover
```

编译检查：

```powershell
py -3.14 -m compileall app scripts tests
```

Lint / format / build：

【待确认】当前仓库未配置 ruff、black、mypy 或 build 脚本。

## Current Status

项目处于 Phase 1 CLI 搜索闭环已实现、Phase 2 单仓库 README 抓取与 LLM 能力卡生成已实现的状态。

依据：

- `app/main.py` 可输出配置健康状态。
- `scripts/analyze_idea.py` 可生成 queries，并在非 `--offline` 模式调用 GitHub repository search。
- 默认 query generation 和候选解释使用 LLM；`--query-mode rules` 仅作为诊断 fallback。
- `app/providers/github_rest_provider.py` 实现 GitHub REST repository search。
- `app/services/github_search.py` 实现候选标准化、去重、排序和缓存。
- `scripts/fetch_repo.py`、`app/services/repo_collector.py` 和 `app/services/capability_extractor.py` 实现单仓库内容抓取和 LLM Repo Skill Card 抽取。
- `scripts/analyze_idea.py --extract-cards` 可把 Phase 2 能力卡生成接入候选仓库分析结果。
- `app/services/evidence_verifier.py`、`scoring.py`、`report_generator.py` 仍是后续阶段占位。
- 测试覆盖配置读取、query generation、候选标准化、搜索去重、仓库内容收集和能力卡抽取。

规划文档中的 v0.1 验收目标尚未完成：输入 TTS audiobook idea 后，搜索到 Abogen / ebook2audiobook / Podcastfy，批量生成能力卡、Markdown 对比报告，并给出是否建议从零做的判断。

## Local Documentation

`docs/` 和 `AGENTS.md` 是本地规划/交接资料，当前不进入版本控制。仓库的可追踪入口以本 README、源码、配置和测试为准。
