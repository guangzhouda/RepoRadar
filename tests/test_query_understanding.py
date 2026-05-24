import unittest

from app.services.query_understanding import build_search_queries, extract_seed_terms


class QueryUnderstandingTests(unittest.TestCase):
    def test_extract_seed_terms_supports_chinese_tts_idea(self):
        terms = extract_seed_terms("我想做一个把 EPUB/PDF 转成 TTS 音频，并生成同步字幕的工具")

        self.assertIn("epub", terms)
        self.assertIn("pdf", terms)
        self.assertIn("tts", terms)
        self.assertIn("subtitle", terms)

    def test_build_search_queries_adds_github_filters(self):
        queries = build_search_queries("EPUB PDF TTS subtitles", max_queries=3)

        self.assertEqual(len(queries), 3)
        self.assertTrue(all("in:name,description,readme" in query for query in queries))
        self.assertTrue(all("archived:false" in query for query in queries))
        self.assertTrue(all("fork:false" in query for query in queries))

    def test_extract_seed_terms_rejects_empty_idea(self):
        with self.assertRaises(ValueError):
            extract_seed_terms("  ")


if __name__ == "__main__":
    unittest.main()
