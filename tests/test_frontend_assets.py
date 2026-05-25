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


if __name__ == "__main__":
    unittest.main()
