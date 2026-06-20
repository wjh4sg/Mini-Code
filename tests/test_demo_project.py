import unittest
from pathlib import Path


class DemoProjectTests(unittest.TestCase):
    def test_demo_contains_required_files_and_content(self):
        root = Path(__file__).resolve().parents[1] / "examples" / "sample_project"
        requirements = (root / "requirements.txt").read_text(encoding="utf-8")
        user_router = (root / "app" / "user_router.py").read_text(encoding="utf-8")
        user_service = (root / "app" / "user_service.py").read_text(encoding="utf-8")
        user_schema = (root / "app" / "user_schema.py").read_text(encoding="utf-8")
        demo_test = (root / "tests" / "test_user.py").read_text(encoding="utf-8")
        env_text = (root / ".env").read_text(encoding="utf-8")

        self.assertIn("fastapi", requirements)
        self.assertIn("uvicorn", requirements)
        self.assertIn("pydantic", requirements)
        self.assertIn("APIRouter", user_router)
        self.assertIn('prefix="/user"', user_router)
        self.assertIn("class UserService", user_service)
        self.assertIn("nickname", user_service)
        self.assertIn("class UserProfile", user_schema)
        self.assertIn("def test_", demo_test)
        self.assertIn("FAKE_API_KEY=demo", env_text)
