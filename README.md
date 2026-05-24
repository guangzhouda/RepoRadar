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
- `scripts/analyze_idea.py` 的 Phase 0 seed query 预览。
- DeepSeek / OpenAI 兼容 LLM 的通用配置项。
- 标准库 `unittest` bootstrap 测试。

部分实现：

- Query understanding 目前是简单英文 token 规则，尚未覆盖中文 idea。
- Repo Skill Card、报告、GitHub/LLM provider 只有边界占位。

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

Phase 0 idea 分析预览：

```powershell
py -3.14 scripts\analyze_idea.py --idea "I want to build a tool that converts EPUB/PDF files into TTS audio with synchronized subtitles." --max-repos 10
```

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
py -3.14 scripts\analyze_idea.py --idea "project idea" --max-repos 10
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

项目处于 Phase 0 bootstrap 完成、Phase 1 CLI 闭环待实现的状态。

依据：

- `app/main.py` 可输出配置健康状态。
- `scripts/analyze_idea.py` 只生成 seed queries，不调用 GitHub 或 LLM。
- `app/providers/*` 和多个 `app/services/*` 方法仍抛出 `NotImplementedError`。
- `tests/test_bootstrap.py` 仅覆盖配置读取和 bootstrap query。

规划文档中的 v0.1 验收目标尚未完成：输入 TTS audiobook idea 后，搜索到 Abogen / ebook2audiobook / Podcastfy，生成能力卡、Markdown 对比报告，并给出是否建议从零做的判断。

## Local Documentation

`docs/` 和 `AGENTS.md` 是本地规划/交接资料，当前不进入版本控制。仓库的可追踪入口以本 README、源码、配置和测试为准。
