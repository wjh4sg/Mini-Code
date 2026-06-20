import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from safety.permission_checker import PermissionChecker
from tools.search_tools import search_code


class SearchToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name)
        (self.workspace / "app").mkdir()
        (self.workspace / ".git").mkdir()
        (self.workspace / "app" / "user_service.py").write_text(
            "class UserService:\n"
            "    nickname = 'Mini User'\n"
            "    def get_user(self):\n"
            "        return self.nickname\n",
            encoding="utf-8",
        )
        (self.workspace / ".env").write_text("USER_TOKEN=secret\n", encoding="utf-8")
        (self.workspace / ".git" / "hidden.py").write_text(
            "user = 'hidden'\n",
            encoding="utf-8",
        )
        self.checker = PermissionChecker(self.workspace)

    def tearDown(self):
        self.temp.cleanup()

    def test_search_is_case_insensitive_and_reports_rejected_files(self):
        result = search_code(self.workspace, "USER", self.checker, max_results=10)

        self.assertTrue(result["success"])
        self.assertEqual(result["matches"][0]["path"], "app/user_service.py")
        self.assertEqual(result["matches"][0]["line"], 1)
        self.assertTrue(
            any(item["path"] == ".env" for item in result["rejected_files"])
        )
        self.assertFalse(
            any(".git" in item["path"] for item in result["matches"])
        )

    def test_search_respects_result_and_file_size_limits(self):
        limited = search_code(self.workspace, "user", self.checker, max_results=1)
        self.assertEqual(len(limited["matches"]), 1)

        oversized = search_code(
            self.workspace,
            "user",
            self.checker,
            max_file_size=1,
        )
        self.assertEqual(oversized["matches"], [])

    def test_search_rejects_empty_keyword(self):
        result = search_code(self.workspace, "", self.checker)

        self.assertFalse(result["success"])
        self.assertIn("不能为空", result["reason"])

    def test_filesystem_error_returns_structured_failure(self):
        with patch("pathlib.Path.iterdir", side_effect=OSError("denied")):
            result = search_code(self.workspace, "user", self.checker)

        self.assertFalse(result["success"])
        self.assertIn("denied", result["reason"])
