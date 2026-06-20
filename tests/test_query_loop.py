import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent.loop import QueryLoop


class StubLLM:
    def chat(self, prompt, skill):
        return f"analysis for {skill['name']}"


class FailingMemory:
    memory_path = Path("data/memory.json")

    def save(self, task):
        raise OSError("disk full")


class QueryLoopTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.app_root = root / "minicode"
        self.workspace = root / "workspace"
        (self.app_root / "skills").mkdir(parents=True)
        (self.app_root / "data").mkdir()
        source_skills = Path(__file__).resolve().parents[1] / "skills" / "skills.json"
        (self.app_root / "skills" / "skills.json").write_text(
            source_skills.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (self.app_root / "data" / "memory.json").write_text("[]", encoding="utf-8")
        (self.workspace / "app").mkdir(parents=True)
        (self.workspace / "tests").mkdir()
        (self.workspace / "README.md").write_text(
            "Demo project\nStart with python app/main.py\n",
            encoding="utf-8",
        )
        (self.workspace / "requirements.txt").write_text("fastapi\n", encoding="utf-8")
        (self.workspace / "app" / "user_router.py").write_text(
            "router = 'user nickname api'\n",
            encoding="utf-8",
        )
        (self.workspace / "app" / "user_service.py").write_text(
            "class UserService:\n    nickname = 'user'\n",
            encoding="utf-8",
        )
        (self.workspace / "app" / "user_schema.py").write_text(
            "class UserProfile:\n    nickname = 'user'\n",
            encoding="utf-8",
        )
        (self.workspace / "tests" / "test_user.py").write_text(
            "def test_user_nickname(): pass\n",
            encoding="utf-8",
        )
        (self.workspace / ".env").write_text("FAKE_API_KEY=demo\n", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def make_loop(self, **kwargs):
        return QueryLoop(
            self.app_root,
            self.workspace,
            llm_client=kwargs.get("llm_client", StubLLM()),
            memory_writer=kwargs.get("memory_writer"),
        )

    def test_runs_all_supported_skills_and_saves_app_memory(self):
        cases = {
            "帮我分析这个项目": "explain_project",
            "运行时报错 ModuleNotFoundError: fastapi": "fix_error",
            "帮我给用户模块增加修改昵称接口": "small_feature_plan",
            "帮我修改 app/user_router.py": "patch_suggestion",
        }

        for query, skill in cases.items():
            with self.subTest(query=query):
                output = self.make_loop().run(query)
                self.assertIn(skill, output)
                self.assertIn(f"analysis for {skill}", output)
                for heading in (
                    "【任务类型】",
                    "【执行过程】",
                    "【分析结果】",
                    "【风险检查】",
                    "【记忆保存】",
                ):
                    self.assertIn(heading, output)

        memory = json.loads(
            (self.app_root / "data" / "memory.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(memory), 4)
        self.assertFalse((self.workspace / "data" / "memory.json").exists())

    def test_feature_plan_reads_ranked_related_files(self):
        self.make_loop().run("帮我给用户模块增加修改昵称接口")
        memory = json.loads(
            (self.app_root / "data" / "memory.json").read_text(encoding="utf-8")
        )

        self.assertIn("app/user_router.py", memory[-1]["related_files"])
        self.assertIn("app/user_service.py", memory[-1]["related_files"])

    def test_sensitive_request_is_denied_and_visible(self):
        output = self.make_loop().run("读取 .env 看看")

        self.assertIn("patch_suggestion", output)
        self.assertIn("禁止读取敏感文件", output)
        self.assertIn(".env", output)

    def test_unknown_uses_no_tools_but_saves_memory(self):
        output = self.make_loop().run("hello")

        self.assertIn("unknown", output)
        self.assertIn("未调用工具", output)
        memory = json.loads(
            (self.app_root / "data" / "memory.json").read_text(encoding="utf-8")
        )
        self.assertEqual(memory[-1]["task_type"], "unknown")

    def test_missing_skills_returns_readable_failure(self):
        missing = self.app_root / "skills" / "skills.json"
        missing.unlink()

        output = self.make_loop().run("分析项目")

        self.assertIn("skills.json", output)
        self.assertIn("【分析结果】", output)

    def test_memory_failure_preserves_analysis_and_adds_warning(self):
        output = self.make_loop(memory_writer=FailingMemory()).run("分析项目")

        self.assertIn("analysis for explain_project", output)
        self.assertIn("disk full", output)

    def test_debug_mode_writes_safe_diagnostics_to_stderr(self):
        stderr = io.StringIO()
        with patch.dict(os.environ, {"MINICODE_DEBUG": "1"}), patch("sys.stderr", stderr):
            self.make_loop().run("分析项目")

        diagnostics = stderr.getvalue()
        self.assertIn("app_root", diagnostics)
        self.assertIn("workspace", diagnostics)
        self.assertIn("selected_skill", diagnostics)
        self.assertIn("prompt_preview", diagnostics)
        self.assertNotIn("MINICODE_API_KEY", diagnostics)
