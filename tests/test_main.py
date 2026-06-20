import io
import unittest
from pathlib import Path
from unittest.mock import patch

import main


class MainTests(unittest.TestCase):
    def test_missing_query_prints_usage(self):
        output = io.StringIO()
        with patch("sys.argv", ["main.py"]), patch("sys.stdout", output):
            code = main.main()

        self.assertEqual(code, 1)
        self.assertIn("用法", output.getvalue())

    def test_app_root_is_main_directory_and_workspace_is_cwd(self):
        app_root, workspace = main.resolve_roots()

        self.assertEqual(app_root, Path(main.__file__).resolve().parent)
        self.assertEqual(workspace, Path.cwd().resolve())
