import json
import tempfile
import unittest
from pathlib import Path

from agent.skill_router import SkillConfigError, SkillRouter


SKILLS = [
    {
        "name": "explain_project",
        "description": "分析项目结构、技术栈和启动方式",
        "keywords": ["分析", "项目"],
        "tools": ["list_files", "read_file"],
        "output_schema": ["项目用途"],
    },
    {
        "name": "fix_error",
        "description": "分析运行、构建或测试报错",
        "keywords": ["报错", "error"],
        "tools": ["search_code", "read_file"],
        "output_schema": ["错误类型"],
    },
    {
        "name": "small_feature_plan",
        "description": "生成小功能实现计划",
        "keywords": ["新增", "接口"],
        "tools": ["search_code", "read_file"],
        "output_schema": ["任务理解"],
    },
    {
        "name": "patch_suggestion",
        "description": "针对指定文件生成局部 Patch 建议",
        "keywords": ["patch", "diff"],
        "tools": ["read_file", "search_code"],
        "output_schema": ["修改原因"],
    },
]


class SkillRouterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app_root = Path(self.temp.name)
        (self.app_root / "skills").mkdir()
        (self.app_root / "skills" / "skills.json").write_text(
            json.dumps(SKILLS, ensure_ascii=False),
            encoding="utf-8",
        )
        self.router = SkillRouter(self.app_root)

    def tearDown(self):
        self.temp.cleanup()

    def test_routes_supported_queries_by_priority(self):
        cases = {
            "帮我分析这个项目": "explain_project",
            "运行时报错 ModuleNotFoundError": "fix_error",
            "帮我给用户模块增加修改昵称接口": "small_feature_plan",
            "帮我修改 src/config.py": "patch_suggestion",
            r"帮我修改 src\config.py": "patch_suggestion",
            "给出 patch": "patch_suggestion",
            "读取 .env 看看": "patch_suggestion",
            "登录 token 报错": "fix_error",
            "hello": "unknown",
        }

        for query, expected in cases.items():
            with self.subTest(query=query):
                routed = self.router.route(query)
                self.assertEqual(routed["name"], expected)
                self.assertIn("reason", routed)

    def test_missing_skills_file_raises_clear_error(self):
        missing_root = self.app_root / "missing"
        with self.assertRaisesRegex(SkillConfigError, "skills.json"):
            SkillRouter(missing_root)

    def test_malformed_skills_file_raises_clear_error(self):
        path = self.app_root / "skills" / "skills.json"
        path.write_text("{bad json", encoding="utf-8")

        with self.assertRaisesRegex(SkillConfigError, "配置"):
            SkillRouter(self.app_root)

    def test_non_list_skill_config_is_rejected(self):
        path = self.app_root / "skills" / "skills.json"
        path.write_text("{}", encoding="utf-8")

        with self.assertRaisesRegex(SkillConfigError, "列表"):
            SkillRouter(self.app_root)
