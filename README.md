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
- `app/services/idea_analysis.py` 承接 idea 分析主流程，CLI 入口保持薄层。
- 多 query 生成、候选仓库标准化、去重、排序和 JSON 缓存。
- LLM 候选相关性评审，输出 `relevance_score`、`decision`、`reject_reason` 和 `rationale`。
- 候选列表保留 `reject` 项用于人工审查，不在展示层直接隐藏。
- `scripts/fetch_repo.py` 的 Phase 2 仓库抓取 CLI，可抓取仓库元数据和 MVP README/docs/config 文件。
- LLM Repo Skill Card 抽取，输出项目类别、输入/输出格式、接口形态、核心能力、限制、证据和置信度。
- Repo Skill Card 结果会按 repo、LLM model 和仓库内容指纹缓存，重复分析时复用已生成能力卡。
- Phase 3 评分引擎，按 relevance、maturity、activity、reusability、documentation、license 生成综合分。
- 确定性 evidence verifier，检查缺失、低置信、重复和可疑 instruction-like evidence，并影响报告风险提示。
- `app/services/reuse_advisor.py` 根据评分和能力卡生成复用/自研建议。
- `scripts/export_report.py` 可把分析 JSON 导出为 Markdown 对比报告。
- DeepSeek / OpenAI 兼容 LLM 的通用配置项。
- OpenAI-compatible LLM 调用使用流式响应读取，默认 timeout 为 300 秒，适配长上下文能力卡抽取。
- `frontend/index.html` 提供零依赖静态 UI MVP，覆盖 idea 输入、运行状态、候选列表、能力卡、报告预览和设置页。
- 标准库 `unittest` bootstrap 测试。

部分实现：

- Query understanding 的规则实现仍保留为 `--query-mode rules` 诊断 fallback，默认路径已经使用 LLM。
- Repo Skill Card 已接入批量候选分析流水线，但仍是 `--extract-cards` opt-in。
- Evidence verifier 仍是后续阶段占位。

待确认：

- 最终 CLI 输出格式是否同时包含 JSON 和 Markdown。
- 是否使用 `unittest` 继续扩展，还是切换到 `pytest`。
- 静态 UI MVP 后续是接入本地 API/CLI bridge，还是切换到 Streamlit/FastAPI。

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

把分析 JSON 导出为 Markdown 对比报告：

```powershell
py -3.14 scripts\analyze_idea.py --idea "project idea" --max-repos 5 --extract-cards --card-limit 2 --output analysis.json
py -3.14 scripts\export_report.py --input analysis.json --output report.md
```

Live smoke 验证完整搜索、能力卡和报告导出链路：

```powershell
py -3.14 scripts\analyze_idea.py --idea "I want to build a tool that converts EPUB/PDF files into TTS audio with synchronized subtitles." --max-repos 3 --max-queries 2 --extract-cards --card-limit 1 --output .reporadar_cache\live-analysis.json
py -3.14 scripts\export_report.py --input .reporadar_cache\live-analysis.json --output .reporadar_cache\live-report.md
```

本地打开静态 UI MVP：

```powershell
Invoke-Item frontend\index.html
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
scripts/    命令行入口；只做参数解析、调用 service 和输出
tests/      标准库 unittest 测试
examples/   示例输入和示例报告
frontend/   零依赖静态 UI MVP，后续接入 CLI/API
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

项目处于 Phase 1 CLI 搜索闭环、Phase 2 仓库抓取/能力卡生成、Phase 3 初版评分、evidence verification 与 Markdown 报告导出已实现的状态。

依据：

- `app/main.py` 可输出配置健康状态。
- `scripts/analyze_idea.py` 是薄 CLI；`app/services/idea_analysis.py` 负责编排 query planning、GitHub search、LLM review 和可选能力卡生成。
- 默认 query generation 和候选解释使用 LLM；`--query-mode rules` 仅作为诊断 fallback。
- `app/providers/github_rest_provider.py` 实现 GitHub REST repository search。
- `app/services/github_search.py` 实现候选标准化、去重、排序和缓存。
- `scripts/fetch_repo.py`、`app/services/repo_collector.py` 和 `app/services/capability_extractor.py` 实现单仓库内容抓取和 LLM Repo Skill Card 抽取；LLM provider 使用流式响应读取和 300 秒默认 timeout。
- `app/services/skill_card_cache.py` 缓存 LLM Repo Skill Card，`app/services/llm_candidate_reviewer.py` 默认按 5 个候选一批做 LLM review，并隔离失败批次。
- `scripts/analyze_idea.py --extract-cards` 可把 Phase 2 能力卡生成接入候选仓库分析结果。
- `app/services/evidence_verifier.py` 实现确定性 evidence quality 检查。
- `app/services/scoring.py` 实现初版综合评分并使用 evidence verifier 调整 documentation score。
- `app/services/reuse_advisor.py` 生成复用/自研建议，`app/services/report_generator.py` 和 `scripts/export_report.py` 实现 Markdown 报告导出。
- `frontend/index.html`、`frontend/styles.css` 和 `frontend/app.js` 提供可直接打开的静态前端原型，目前使用示例数据模拟 CLI 结果。
- 测试覆盖配置读取、query generation、候选标准化、搜索去重、idea 分析编排、仓库内容收集、能力卡抽取、evidence verification、评分和报告生成。

规划文档中的 v0.1 验收目标已具备 CLI 路径，但仍需更多 live 验证：输入 TTS audiobook idea 后，搜索候选项目，批量生成能力卡，导出 Markdown 对比报告，并给出是否建议从零做的判断。

## Local Documentation

`docs/` 和 `AGENTS.md` 是本地规划/交接资料，当前不进入版本控制。仓库的可追踪入口以本 README、源码、配置和测试为准。
