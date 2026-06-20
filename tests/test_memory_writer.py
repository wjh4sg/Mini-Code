import json
import tempfile
import unittest
from pathlib import Path

from memory.memory_writer import MemoryWriter


class MemoryWriterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app_root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_saves_deduplicated_related_files_and_excludes_rejected(self):
        task = {
            "task_id": "task-1",
            "selected_skill": "small_feature_plan",
            "user_query": "新增接口",
            "workspace": "/workspace",
            "created_at": "2026-06-20 12:00:00",
            "status": "done",
            "tool_results": [
                {"tool": "read_file", "success": True, "path": "app/a.py"},
                {
                    "tool": "search_code",
                    "success": True,
                    "matches": [
                        {"path": "app/a.py"},
                        {"path": "app/b.py"},
                    ],
                    "rejected_files": [{"path": ".env"}],
                },
            ],
        }

        item = MemoryWriter(self.app_root).save(task)
        saved = json.loads((self.app_root / "data" / "memory.json").read_text(encoding="utf-8"))

        self.assertEqual(item["related_files"], ["app/a.py", "app/b.py"])
        self.assertEqual(saved, [item])
        self.assertNotIn(".env", item["related_files"])
        self.assertIn("定位相关模块", item["experience"])

    def test_recovers_from_corrupt_or_non_list_memory(self):
        path = self.app_root / "data" / "memory.json"
        path.parent.mkdir()
        for existing in ("{bad", "{}"):
            path.write_text(existing, encoding="utf-8")
            MemoryWriter(self.app_root).save(self._minimal_task())
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(len(saved), 1)

    def test_limits_related_files_to_twenty(self):
        task = self._minimal_task()
        task["tool_results"] = [
            {
                "tool": "search_code",
                "success": True,
                "matches": [{"path": f"app/{index}.py"} for index in range(30)],
            }
        ]

        item = MemoryWriter(self.app_root).save(task)

        self.assertEqual(len(item["related_files"]), 20)

    @staticmethod
    def _minimal_task():
        return {
            "task_id": "task",
            "selected_skill": "unknown",
            "user_query": "hello",
            "workspace": "/workspace",
            "created_at": "2026-06-20 12:00:00",
            "status": "done",
            "tool_results": [],
        }
