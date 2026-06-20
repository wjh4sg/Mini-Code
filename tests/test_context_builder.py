import unittest

from agent.context_builder import ContextBuilder


class ContextBuilderTests(unittest.TestCase):
    def test_builds_required_prompt_sections_and_compresses_results(self):
        task = {"user_query": "分析项目", "selected_skill": "explain_project"}
        skill = {
            "name": "explain_project",
            "description": "分析项目",
            "output_schema": ["项目用途", "技术栈"],
        }
        tool_results = [
            {
                "tool": "list_files",
                "success": True,
                "result": [f"file-{index}.py" for index in range(100)],
                "summary": "扫描完成",
            },
            {
                "tool": "search_code",
                "success": True,
                "keyword": "user",
                "matches": [
                    {"path": "app.py", "line": index, "text": f"match-{index}"}
                    for index in range(15)
                ],
                "rejected_files": [],
                "summary": "搜索完成",
            },
            {
                "tool": "read_file",
                "success": True,
                "path": "app.py",
                "line_count": 100,
                "truncated": False,
                "content": "\n".join(f"line-{index}" for index in range(100)),
                "summary": "读取完成",
            },
        ]

        prompt = ContextBuilder().build(task, skill, tool_results)

        for heading in (
            "用户任务：",
            "当前 Skill：",
            "已调用工具：",
            "项目上下文：",
            "相关代码片段：",
            "输出要求：",
            "回答约束：",
        ):
            self.assertIn(heading, prompt)
        self.assertIn("file-79.py", prompt)
        self.assertNotIn("file-80.py", prompt)
        self.assertIn("match-9", prompt)
        self.assertNotIn("match-10", prompt)
        self.assertIn("line-79", prompt)
        self.assertNotIn("line-80", prompt)
