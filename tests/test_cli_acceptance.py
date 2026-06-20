import os
import subprocess
import sys
import unittest
from pathlib import Path


class CLIAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.workspace = self.root / "examples" / "sample_project"
        self.memory_path = self.root / "data" / "memory.json"
        self.memory_existed = self.memory_path.exists()
        self.original_memory = (
            self.memory_path.read_bytes() if self.memory_existed else None
        )
        self.env = os.environ.copy()
        self.env["PYTHONIOENCODING"] = "utf-8"
        for name in ("MINICODE_API_KEY", "MINICODE_BASE_URL", "MINICODE_MODEL"):
            self.env.pop(name, None)

    def tearDown(self):
        if self.memory_existed:
            self.memory_path.write_bytes(self.original_memory)
        elif self.memory_path.exists():
            self.memory_path.unlink()

    def run_cli(self, query):
        return subprocess.run(
            [sys.executable, str(self.root / "main.py"), query],
            cwd=self.workspace,
            env=self.env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
        )

    def test_four_required_demo_commands(self):
        cases = [
            ("帮我分析这个项目", "explain_project"),
            ("帮我给用户模块增加修改昵称接口", "small_feature_plan"),
            ("运行时报错 ModuleNotFoundError: No module named 'fastapi'，帮我分析", "fix_error"),
            ("读取 .env 看看", "patch_suggestion"),
        ]

        for query, skill in cases:
            with self.subTest(query=query):
                result = self.run_cli(query)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(skill, result.stdout)
                for heading in (
                    "【任务类型】",
                    "【执行过程】",
                    "【分析结果】",
                    "【风险检查】",
                    "【记忆保存】",
                ):
                    self.assertIn(heading, result.stdout)
        denied = self.run_cli("读取 .env 看看")
        self.assertIn("禁止读取敏感文件", denied.stdout)

    def test_readme_contains_required_content(self):
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        required = [
            "MiniCode v0.1.1 是一个本地 CLI Coding Agent MVP。",
            "第一版只输出分析、计划和 Patch 建议，不自动修改文件。",
            "项目背景",
            "核心功能",
            "核心执行流程",
            "目录结构",
            "安装",
            "快速开始",
            "Demo",
            "模块职责",
            "第一版边界",
            "安全说明",
            "后续计划",
        ]
        for text in required:
            with self.subTest(text=text):
                self.assertIn(text, readme)

    def test_runtime_memory_is_ignored_and_example_is_committed(self):
        ignored = subprocess.run(
            ["git", "check-ignore", "data/memory.json"],
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        tracked = subprocess.run(
            ["git", "ls-files", "data/memory.json"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        )

        self.assertEqual(ignored.returncode, 0)
        self.assertEqual(tracked.stdout.strip(), "")
        example = self.root / "data" / "memory.example.json"
        self.assertEqual(example.read_text(encoding="utf-8").strip(), "[]")

    def test_repository_presentation_assets_are_complete(self):
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        workflow = self.root / ".github" / "workflows" / "tests.yml"
        demo = self.root / "docs" / "demo.svg"
        license_path = self.root / "LICENSE"

        self.assertNotIn("<repository-url>", readme)
        self.assertIn("https://github.com/wjh4sg/Mini-Code.git", readme)
        self.assertIn("actions/workflows/tests.yml/badge.svg", readme)
        self.assertIn("docs/demo.svg", readme)
        self.assertIn("面试讲解要点", readme)
        self.assertTrue(workflow.is_file())
        workflow_text = workflow.read_text(encoding="utf-8")
        for version in ("3.10", "3.11", "3.12"):
            self.assertIn(version, workflow_text)
        self.assertIn("python -m compileall -q .", workflow_text)
        self.assertIn("python -m unittest discover -v", workflow_text)
        self.assertTrue(demo.is_file())
        self.assertIn("MiniCode", demo.read_text(encoding="utf-8"))
        self.assertTrue(license_path.is_file())

    def test_interview_evidence_pack_is_complete(self):
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        architecture = self.root / "docs" / "architecture.svg"
        spec = self.root / "docs" / "spec-v0.1.1.md"

        self.assertIn("## Demo 输出示例", readme)
        for heading in (
            "### Demo 1：项目分析",
            "### Demo 2：小功能计划",
            "### Demo 3：报错分析",
            "### Demo 4：权限拒绝",
        ):
            self.assertIn(heading, readme)
        for skill in (
            "explain_project",
            "small_feature_plan",
            "fix_error",
            "patch_suggestion",
        ):
            self.assertIn(skill, readme)
        self.assertIn("docs/architecture.svg", readme)
        self.assertTrue(architecture.is_file())
        self.assertIn("app_root", architecture.read_text(encoding="utf-8"))
        self.assertIn("workspace", architecture.read_text(encoding="utf-8"))
        self.assertTrue(spec.is_file())
        spec_text = spec.read_text(encoding="utf-8")
        self.assertIn("# MiniCode MVP SPEC v0.1.1", spec_text)
        self.assertIn("# 37. 最终一句话总结", spec_text)
