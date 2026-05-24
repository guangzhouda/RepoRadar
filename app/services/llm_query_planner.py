"""LLM-backed query planning for GitHub repository search.

The planner turns a natural-language idea into multiple GitHub search queries.
It is used by the CLI in normal mode; deterministic rule generation remains
available only for diagnostics and tests.
"""

from __future__ import annotations

from app.providers.llm_base import LLMProvider
from app.services.llm_json import parse_json_object


class LLMQueryPlanner:
    """Build GitHub search queries with an LLM."""

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def build_queries(self, idea: str, max_queries: int = 6) -> list[str]:
        """Return LLM-generated GitHub repository search queries."""

        if not idea.strip():
            raise ValueError("idea must not be empty")

        prompt = f"""
你是 RepoRadar 的 GitHub repository search query planner。

目标：把用户项目想法转换成 {max_queries} 条以内的 GitHub repository search query。

要求：
- 只返回严格 JSON，不要解释。
- JSON schema: {{"queries": ["..."]}}
- query 必须适合 GitHub repository search。
- 使用能力组合，不要只依赖一个关键词。
- 不要使用 OR、括号或复杂布尔表达式；每条 query 应该用空格组合 3-6 个必须同时出现的核心英文关键词。
- 避免过宽泛的 awesome/list/newsletter/resource 查询。
- 优先真实工具项目，而不是资料集合。
- 可使用 in:name,description,readme、stars、pushed、archived:false、fork:false、language、topic 等 GitHub 搜索限定词。
- 对 TTS/有声书场景，优先组合 epub/pdf/ebook、tts/text-to-speech、audiobook、subtitle/srt/m4b 等关键词。
- 高精度示例：epub pdf tts subtitle in:name,description,readme stars:>5 pushed:>2022-01-01 archived:false fork:false
- 高精度示例：ebook audiobook srt m4b language:python stars:>5 archived:false fork:false

用户想法：
{idea}
""".strip()
        response = parse_json_object(self.provider.complete(prompt))
        raw_queries = response.get("queries", [])
        if not isinstance(raw_queries, list):
            raise ValueError("LLM query response must include a queries list")

        queries: list[str] = []
        seen: set[str] = set()
        for raw_query in raw_queries:
            if not isinstance(raw_query, str):
                continue
            query = " ".join(raw_query.split())
            if query and query not in seen:
                seen.add(query)
                queries.append(query)
            if len(queries) >= max_queries:
                break

        if not queries:
            raise ValueError("LLM did not return any usable GitHub search queries")
        return queries
