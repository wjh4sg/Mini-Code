import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import main
import minicode_cli


class MiniCodeCLITests(unittest.TestCase):
    def test_legacy_main_delegates_to_new_cli(self):
        self.assertIs(main.main, minicode_cli.main)

    def test_version_prints_current_version(self):
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            code = minicode_cli.main(["--version"])

        self.assertEqual(code, 0)
        self.assertEqual(stdout.getvalue().strip(), "MiniCode 0.2.1")

    def test_query_uses_explicit_workspace(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            loop = Mock()
            loop.run.return_value = "answer"
            factory = Mock(return_value=loop)
            stdout = io.StringIO()

            with patch("sys.stdout", stdout):
                code = minicode_cli.main(
                    ["-w", str(workspace), "分析", "项目"],
                    loop_factory=factory,
                )

        self.assertEqual(code, 0)
        self.assertEqual(stdout.getvalue().strip(), "answer")
        self.assertEqual(loop.run.call_args.args, ("分析 项目",))
        self.assertEqual(factory.call_args.args[1], workspace.resolve())

    def test_query_defaults_workspace_to_cwd(self):
        loop = Mock()
        loop.run.return_value = "answer"
        factory = Mock(return_value=loop)

        with patch("sys.stdout", io.StringIO()):
            minicode_cli.main(["hello"], loop_factory=factory)

        self.assertEqual(factory.call_args.args[1], Path.cwd().resolve())

    def test_debug_and_mock_are_scoped_to_execution(self):
        loop = Mock()
        execution_environment = {}

        def run(_query):
            execution_environment.update(
                {
                    "MINICODE_DEBUG": os.environ.get("MINICODE_DEBUG"),
                    "MINICODE_API_KEY": os.environ.get("MINICODE_API_KEY"),
                    "MINICODE_BASE_URL": os.environ.get("MINICODE_BASE_URL"),
                    "MINICODE_MODEL": os.environ.get("MINICODE_MODEL"),
                }
            )
            return "answer"

        loop.run.side_effect = run
        factory = Mock(return_value=loop)
        original = {
            "MINICODE_DEBUG": os.environ.get("MINICODE_DEBUG"),
            "MINICODE_API_KEY": os.environ.get("MINICODE_API_KEY"),
            "MINICODE_BASE_URL": os.environ.get("MINICODE_BASE_URL"),
            "MINICODE_MODEL": os.environ.get("MINICODE_MODEL"),
        }

        with patch.dict(
            os.environ,
            {
                "MINICODE_API_KEY": "key",
                "MINICODE_BASE_URL": "https://example.test",
                "MINICODE_MODEL": "model",
            },
            clear=False,
        ):
            with patch("sys.stdout", io.StringIO()):
                minicode_cli.main(
                    ["--debug", "--mock", "hello"],
                    loop_factory=factory,
                )
            self.assertEqual(execution_environment["MINICODE_DEBUG"], "1")
            self.assertIsNone(execution_environment["MINICODE_API_KEY"])
            self.assertIsNone(execution_environment["MINICODE_BASE_URL"])
            self.assertIsNone(execution_environment["MINICODE_MODEL"])
            self.assertEqual(os.environ.get("MINICODE_API_KEY"), "key")
            self.assertEqual(os.environ.get("MINICODE_BASE_URL"), "https://example.test")
            self.assertEqual(os.environ.get("MINICODE_MODEL"), "model")
            self.assertEqual(os.environ.get("MINICODE_DEBUG"), original["MINICODE_DEBUG"])

    def test_invalid_workspace_returns_nonzero_without_traceback(self):
        stderr = io.StringIO()
        with patch("sys.stderr", stderr):
            code = minicode_cli.main(["-w", "missing-workspace", "hello"])

        self.assertEqual(code, 2)
        self.assertIn("工作区不存在或不是目录", stderr.getvalue())

    def test_missing_query_returns_usage_error(self):
        stderr = io.StringIO()
        with patch("sys.stderr", stderr):
            code = minicode_cli.main([])

        self.assertEqual(code, 2)
        self.assertIn("需要提供任务", stderr.getvalue())

    def test_doctor_reports_configuration_without_creating_loop(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            stdout = io.StringIO()
            factory = Mock(side_effect=AssertionError("doctor must not build QueryLoop"))

            with patch("sys.stdout", stdout):
                code = minicode_cli.main(
                    ["doctor", "-w", str(workspace)],
                    loop_factory=factory,
                )

        output = stdout.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("MiniCode doctor", output)
        self.assertIn("Python:", output)
        self.assertIn("app_root:", output)
        self.assertIn(f"workspace: {workspace.resolve()}", output)
        self.assertIn("skills.json: found", output)
        self.assertIn("memory path:", output)
        self.assertIn("LLM mode:", output)
