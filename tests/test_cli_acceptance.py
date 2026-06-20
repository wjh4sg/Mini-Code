import os
import subprocess
import sys
import unittest
from pathlib import Path


class CLIAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.workspace = self.root / "examples" / "sample_project"
        self.env = os.environ.copy()
        self.env["PYTHONIOENCODING"] = "utf-8"
        for name in ("MINICODE_API_KEY", "MINICODE_BASE_URL", "MINICODE_MODEL"):
            self.env.pop(name, None)

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
