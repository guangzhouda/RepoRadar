import unittest

from app.models.repo import RepositoryCandidate
from app.services.llm_candidate_reviewer import LLMCandidateReviewer
from app.services.llm_query_planner import LLMQueryPlanner


class FakeLLMProvider:
    def __init__(self, response):
        self.response = response
        self.prompts = []

    def complete(self, prompt):
        self.prompts.append(prompt)
        return self.response


class LLMServiceTests(unittest.TestCase):
    def test_llm_query_planner_returns_unique_queries(self):
        provider = FakeLLMProvider(
            '{"queries": ["epub tts audiobook in:readme", "epub tts audiobook in:readme", "pdf tts srt in:readme"]}'
        )

        queries = LLMQueryPlanner(provider).build_queries("tts idea", max_queries=5)

        self.assertEqual(queries, ["epub tts audiobook in:readme", "pdf tts srt in:readme"])
        self.assertIn("GitHub repository search query", provider.prompts[0])

    def test_llm_candidate_reviewer_merges_reviews_and_sorts(self):
        provider = FakeLLMProvider(
            """
            {
              "candidates": [
                {"full_name": "awesome/list", "relevance_score": 0.1, "decision": "reject", "reject_reason": "awesome list", "rationale": "not a tool"},
                {"full_name": "tool/tts", "relevance_score": 0.92, "decision": "keep", "reject_reason": "", "rationale": "matches TTS audiobook"}
              ]
            }
            """
        )
        candidates = [
            RepositoryCandidate(full_name="awesome/list", url="https://github.com/awesome/list", stars=1000),
            RepositoryCandidate(full_name="tool/tts", url="https://github.com/tool/tts", stars=10),
        ]
        reviewer = LLMCandidateReviewer(provider)

        reviews = reviewer.review("tts audiobook idea", candidates)
        enriched = reviewer.apply_reviews(candidates, reviews, limit=2)

        self.assertEqual(enriched[0]["full_name"], "tool/tts")
        self.assertEqual(enriched[0]["decision"], "keep")
        self.assertEqual(enriched[1]["reject_reason"], "awesome list")


if __name__ == "__main__":
    unittest.main()
