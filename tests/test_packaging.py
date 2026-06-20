import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def test_pyproject_declares_installable_minicode_command(self):
        pyproject = (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")

        self.assertIn('name = "minicode-agent"', pyproject)
        self.assertIn('version = "0.2.1"', pyproject)
        self.assertIn('requires-python = ">=3.10"', pyproject)
        self.assertIn('minicode = "minicode_cli:main"', pyproject)

    def test_runtime_modules_and_skills_data_are_packaged(self):
        pyproject = (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")

        self.assertIn('py-modules = ["minicode_cli", "main"]', pyproject)
        self.assertIn('"agent"', pyproject)
        self.assertIn('"memory"', pyproject)
        self.assertIn('"safety"', pyproject)
        self.assertIn('"skills"', pyproject)
        self.assertIn('"tools"', pyproject)
        self.assertIn('skills = ["skills.json"]', pyproject)
        self.assertTrue((REPOSITORY_ROOT / "skills" / "__init__.py").is_file())

    def test_readme_documents_installed_and_source_invocation(self):
        readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("python -m pip install --upgrade pip", readme)
        self.assertIn("python -m pip install -e .", readme)
        self.assertIn('minicode -w examples/sample_project "帮我分析这个项目"', readme)
        self.assertIn("minicode doctor", readme)
        self.assertIn('python main.py "帮我分析这个项目"', readme)


if __name__ == "__main__":
    unittest.main()
