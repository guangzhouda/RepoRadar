from pathlib import Path
import re
import unittest


class FrontendAssetTests(unittest.TestCase):
    def test_index_references_existing_frontend_scripts_in_order(self):
        root = Path(__file__).resolve().parents[1]
        index = (root / "frontend" / "index.html").read_text(encoding="utf-8")
        scripts = re.findall(r'<script src="([^"]+)"></script>', index)

        expected = [
            "js/i18n.js",
            "js/sample-data.js",
            "js/formatters.js",
            "js/api.js",
            "js/candidate-views.js",
            "js/report.js",
            "js/app.js",
        ]
        self.assertEqual(scripts[-7:], expected)
        for script in expected:
            self.assertTrue((root / "frontend" / script).is_file(), script)

    def test_run_title_is_dynamic_not_i18n_literal(self):
        root = Path(__file__).resolve().parents[1]
        index = (root / "frontend" / "index.html").read_text(encoding="utf-8")
        app = (root / "frontend" / "js" / "app.js").read_text(encoding="utf-8")

        self.assertIn('id="run-title"', index)
        self.assertNotIn('data-i18n="status.runningAnalysisTitle"', index)
        self.assertIn("runTitle.textContent = currentIdeaTitle();", app)

    def test_candidate_description_translation_ui_is_wired(self):
        root = Path(__file__).resolve().parents[1]
        i18n = (root / "frontend" / "js" / "i18n.js").read_text(encoding="utf-8")
        api = (root / "frontend" / "js" / "api.js").read_text(encoding="utf-8")
        app = (root / "frontend" / "js" / "app.js").read_text(encoding="utf-8")
        views = (root / "frontend" / "js" / "candidate-views.js").read_text(encoding="utf-8")

        self.assertIn('"action.translate"', i18n)
        self.assertIn('"action.showOriginal"', i18n)
        self.assertIn('requestJson(\n      "/api/localize"', api)
        self.assertIn("toggleCandidateDescription", app)
        self.assertIn("data-description-action", views)


if __name__ == "__main__":
    unittest.main()
