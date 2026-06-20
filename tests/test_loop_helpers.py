import tempfile
import unittest
from pathlib import Path

from agent.loop import QueryLoop


class LoopHelperTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.loop = QueryLoop(self.root, self.root)

    def tearDown(self):
        self.temp.cleanup()

    def test_expands_feature_keywords_in_stable_order(self):
        keywords = self.loop._expand_feature_keywords("帮我给用户增加昵称接口")
        self.assertEqual(
            keywords[:6],
            ["user", "account", "profile", "nickname", "display_name", "username"],
        )

    def test_ranks_and_deduplicates_related_files(self):
        results = [
            {
                "tool": "search_code",
                "success": True,
                "matches": [
                    {"path": "tests/test_user.py"},
                    {"path": "app/user_schema.py"},
                    {"path": "app/user_service.py"},
                    {"path": "app/user_router.py"},
                    {"path": "app/user_service.py"},
                ],
            }
        ]

        self.assertEqual(
            self.loop._collect_related_files_from_search(results),
            [
                "app/user_router.py",
                "app/user_service.py",
                "app/user_schema.py",
                "tests/test_user.py",
            ],
        )

    def test_extracts_supported_file_paths(self):
        self.assertEqual(
            self.loop._extract_file_paths("修改 src/config.py 和 app\\main.ts"),
            ["src/config.py", "app\\main.ts"],
        )

    def test_detects_sensitive_request(self):
        self.assertEqual(self.loop._detect_sensitive_file_request("读取 .env 看看"), ".env")
        self.assertEqual(
            self.loop._detect_sensitive_file_request("读取 config.secret.json 看看"),
            "config.secret.json",
        )
