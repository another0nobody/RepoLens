from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from repolens.codeview import CodeViewError, read_code_window


class CodeViewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "src").mkdir()
        (self.root / "src" / "app.py").write_text(
            "line one\nline two\npassword = 'secret-value'\nline four\nline five\n",
            encoding="utf-8",
        )
        (self.root / ".env").write_text("API_KEY=secret\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_reads_window_with_highlight(self):
        data = read_code_window(self.root, "src/app.py", line=3, context=1)
        self.assertEqual(data["start"], 2)
        self.assertEqual(data["end"], 4)
        self.assertEqual([line["number"] for line in data["lines"]], [2, 3, 4])
        self.assertTrue(next(line for line in data["lines"] if line["number"] == 3)["highlight"])
        self.assertTrue(data["masked"])

    def test_rejects_path_escape(self):
        with self.assertRaises(CodeViewError) as context:
            read_code_window(self.root, "../outside.py", line=1)
        self.assertEqual(context.exception.status, 403)

    def test_rejects_sensitive_file(self):
        with self.assertRaises(CodeViewError) as context:
            read_code_window(self.root, ".env", line=1)
        self.assertEqual(context.exception.status, 403)

    def test_rejects_git_metadata(self):
        (self.root / ".git").mkdir()
        (self.root / ".git" / "config").write_text("[remote]\n", encoding="utf-8")
        with self.assertRaises(CodeViewError) as context:
            read_code_window(self.root, ".git/config", line=1)
        self.assertEqual(context.exception.status, 403)

    def test_missing_file(self):
        with self.assertRaises(CodeViewError) as context:
            read_code_window(self.root, "src/missing.py", line=1)
        self.assertEqual(context.exception.status, 404)
