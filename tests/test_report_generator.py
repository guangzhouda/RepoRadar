from datetime import date
import unittest

from app.models.report import CandidateAssessment, ResearchReport
from app.models.repo import RepositoryCandidate
from app.models.skill_card import Evidence, RepoSkillCard
from app.services.report_generator import ReportGenerator
from app.services.scoring import ScoringEngine


class ReportGeneratorTests(unittest.TestCase):
    def test_generate_markdown_includes_scores_cards_and_recommendation(self):
        candidate = RepositoryCandidate(
            full_name="owner/repo",
            url="https://github.com/owner/repo",
            stars=500,
            forks=50,
            language="Python",
            license="MIT",
            pushed_at="2026-05-01T00:00:00Z",
        )
        card = RepoSkillCard(
            repo="owner/repo",
            name="repo",
            summary="Converts ebooks into narrated audio.",
            input_formats=("EPUB",),
            output_formats=("MP3", "SRT"),
            interfaces=("cli",),
            core_capabilities=("ebook to audio",),
            limitations=("PDF quality varies",),
            evidence=(Evidence(source="README.md", quote="Converts EPUB to audio", confidence=0.9),),
            confidence=0.85,
        )
        report = ResearchReport(
            idea="Build an EPUB to audiobook tool",
            queries=("epub tts audiobook in:readme",),
            candidates=(candidate,),
            skill_cards=(card,),
            assessments=(CandidateAssessment(full_name="owner/repo", relevance_score=0.9, decision="keep"),),
        )

        markdown = ReportGenerator(ScoringEngine(today=date(2026, 5, 24))).generate_markdown(report)

        self.assertIn("# RepoRadar Research Report", markdown)
        self.assertIn("Build an EPUB to audiobook tool", markdown)
        self.assertIn("| Repo | Decision | Score |", markdown)
        self.assertIn("owner/repo", markdown)
        self.assertIn("ebook to audio", markdown)
        self.assertIn("PDF quality varies", markdown)
        self.assertIn("## Recommendation", markdown)

    def test_generate_markdown_handles_empty_candidates(self):
        report = ResearchReport(idea="Build a niche tool")

        markdown = ReportGenerator(ScoringEngine(today=date(2026, 5, 24))).generate_markdown(report)

        self.assertIn("No candidate repositories were provided.", markdown)
        self.assertIn("Run repository search", markdown)


if __name__ == "__main__":
    unittest.main()
