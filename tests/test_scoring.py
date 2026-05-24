from datetime import date
import unittest

from app.models.repo import RepositoryCandidate
from app.models.skill_card import Evidence, RepoSkillCard
from app.services.scoring import SCORING_WEIGHTS, ScoringEngine


class ScoringTests(unittest.TestCase):
    def test_scoring_engine_returns_weighted_breakdown(self):
        candidate = RepositoryCandidate(
            full_name="owner/repo",
            url="https://github.com/owner/repo",
            stars=1000,
            forks=100,
            license="MIT",
            pushed_at="2026-05-01T00:00:00Z",
        )
        card = RepoSkillCard(
            repo="owner/repo",
            name="repo",
            summary="Converts ebooks into narrated audio.",
            input_formats=("EPUB", "PDF"),
            output_formats=("MP3", "SRT"),
            interfaces=("cli",),
            core_capabilities=("ebook to audio",),
            deployment=("pip",),
            evidence=(Evidence(source="README.md", quote="EPUB to audio", confidence=0.9),),
            confidence=0.82,
        )

        score = ScoringEngine(today=date(2026, 5, 24)).score(candidate, card, relevance_score=0.9)

        self.assertEqual(set(SCORING_WEIGHTS), {"relevance", "maturity", "activity", "reusability", "documentation", "license"})
        self.assertEqual(score.repo, "owner/repo")
        self.assertEqual(score.relevance, 0.9)
        self.assertEqual(score.activity, 1.0)
        self.assertGreater(score.overall, 0.75)

    def test_scoring_engine_uses_conservative_defaults_for_missing_data(self):
        candidate = RepositoryCandidate(full_name="owner/repo", url="https://github.com/owner/repo")

        score = ScoringEngine(today=date(2026, 5, 24)).score(candidate)

        self.assertEqual(score.overall, 0.0)
        self.assertIn("license missing", score.notes)
        self.assertIn("skill card missing", score.notes)


if __name__ == "__main__":
    unittest.main()
