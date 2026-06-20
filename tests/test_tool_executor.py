import tempfile
import unittest
from pathlib import Path

from tools.tool_executor import ToolExecutor


class ToolExecutorTests(unittest.TestCase):
    def test_facade_uses_one_workspace_and_permission_checker(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            (workspace / "README.md").write_text("MiniCode", encoding="utf-8")
            executor = ToolExecutor(workspace)

            self.assertEqual(executor.workspace, workspace.resolve())
            self.assertTrue(executor.list_files()["success"])
            self.assertTrue(executor.read_file("README.md")["success"])
            self.assertTrue(executor.search_code("MiniCode")["success"])
