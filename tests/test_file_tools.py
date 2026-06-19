import tempfile
import unittest
from pathlib import Path

from safety.permission_checker import PermissionChecker
from tools.file_tools import list_files, read_file


class FileToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name)
        (self.workspace / "src" / "deep").mkdir(parents=True)
        (self.workspace / ".git").mkdir()
        (self.workspace / "README.md").write_text("line 1\nline 2\n", encoding="utf-8")
        (self.workspace / "src" / "app.py").write_text("print('app')\n", encoding="utf-8")
        (self.workspace / "src" / "deep" / "module.py").write_text(
            "print('deep')\n",
            encoding="utf-8",
        )
        (self.workspace / ".git" / "config").write_text("hidden", encoding="utf-8")
        (self.workspace / ".env").write_text("TOKEN=secret", encoding="utf-8")
        (self.workspace / "binary.bin").write_bytes(b"\x00\x01")
        (self.workspace / "large.txt").write_text("0123456789", encoding="utf-8")
        self.checker = PermissionChecker(self.workspace)

    def tearDown(self):
        self.temp.cleanup()

    def test_list_files_is_depth_limited_and_ignores_directories(self):
        result = list_files(self.workspace, ".", max_depth=1, max_items=20)

        self.assertTrue(result["success"])
        self.assertIn("README.md", result["result"])
        self.assertIn("src/", result["result"])
        self.assertIn("src/app.py", result["result"])
        self.assertIn("src/deep/", result["result"])
        self.assertNotIn("src/deep/module.py", result["result"])
        self.assertFalse(any(path.startswith(".git") for path in result["result"]))

    def test_list_files_enforces_limits_and_workspace_boundary(self):
        result = list_files(self.workspace, ".", max_depth=5, max_items=2)
        self.assertEqual(len(result["result"]), 2)
        self.assertFalse(list_files(self.workspace, "..")["success"])
        self.assertFalse(list_files(self.workspace, "missing")["success"])

    def test_read_file_reports_full_line_count_and_truncation(self):
        result = read_file(
            self.workspace,
            "README.md",
            self.checker,
            max_lines=1,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["line_count"], 2)
        self.assertEqual(result["content"], "line 1")
        self.assertTrue(result["truncated"])

    def test_read_file_rejects_sensitive_unsupported_large_and_missing_files(self):
        self.assertFalse(read_file(self.workspace, ".env", self.checker)["success"])
        self.assertFalse(read_file(self.workspace, "binary.bin", self.checker)["success"])
        self.assertFalse(
            read_file(
                self.workspace,
                "large.txt",
                self.checker,
                max_file_size=4,
            )["success"]
        )
        self.assertFalse(read_file(self.workspace, "missing.txt", self.checker)["success"])
        self.assertFalse(read_file(self.workspace, "src", self.checker)["success"])

    def test_read_file_ignores_invalid_utf8_bytes(self):
        (self.workspace / "broken.txt").write_bytes(b"hello\xffworld")

        result = read_file(self.workspace, "broken.txt", self.checker)

        self.assertTrue(result["success"])
        self.assertEqual(result["content"], "helloworld")
