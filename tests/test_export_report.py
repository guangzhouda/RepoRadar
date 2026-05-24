import unittest

from app.models.report import ResearchReport
from scripts.export_report import build_report_from_payload


class ExportReportTests(unittest.TestCase):
    def test_build_report_from_payload_reads_analysis_json(self):
        report = build_report_from_payload(
            {
                "idea": "Build an EPUB audiobook tool",
                "queries": ["epub tts audiobook in:readme"],
                "candidates": [
                    {
                        "full_name": "owner/repo",
                        "url": "https://github.com/owner/repo",
                        "stars": 42,
                        "forks": 7,
                        "license": "MIT",
                        "relevance_score": 0.9,
                        "decision": "keep",
                        "skill_card_error": "cached miss",
                        "skill_card": {
                            "repo": "owner/repo",
                            "name": "repo",
                            "summary": "Converts ebooks into audio.",
                            "core_capabilities": ["ebook to audio"],
                            "confidence": 0.8,
                        },
                    }
                ],
            }
        )

        self.assertIsInstance(report, ResearchReport)
        self.assertEqual(report.idea, "Build an EPUB audiobook tool")
        self.assertEqual(report.queries, ("epub tts audiobook in:readme",))
        self.assertEqual(report.candidates[0].full_name, "owner/repo")
        self.assertEqual(report.assessments[0].decision, "keep")
        self.assertEqual(report.assessments[0].skill_card_error, "cached miss")
        self.assertEqual(report.skill_cards[0].core_capabilities, ("ebook to audio",))

    def test_build_report_from_payload_requires_candidates_list(self):
        with self.assertRaises(ValueError):
            build_report_from_payload({"candidates": "not a list"})


if __name__ == "__main__":
    unittest.main()
