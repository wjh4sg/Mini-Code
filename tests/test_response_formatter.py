import unittest

from agent.response_formatter import ResponseFormatter


class ResponseFormatterTests(unittest.TestCase):
    def test_formats_five_sections_and_risk_details(self):
        task = {
            "selected_skill": "patch_suggestion",
            "llm_response": "analysis",
            "tool_results": [
                {"tool": "read_file", "success": True, "path": "README.md"},
                {
                    "tool": "read_file",
                    "success": False,
                    "path": ".env",
                    "reason": "禁止读取敏感文件：.env",
                },
                {
                    "tool": "search_code",
                    "success": True,
                    "keyword": "token",
                    "rejected_files": [
                        {"path": "secret.key", "reason": "禁止读取敏感文件：secret.key"}
                    ],
                },
            ],
        }

        output = ResponseFormatter().format(task, "data/memory.json")

        for heading in ("【任务类型】", "【执行过程】", "【分析结果】", "【风险检查】", "【记忆保存】"):
            self.assertIn(heading, output)
        self.assertIn('read_file("README.md") success', output)
        self.assertIn(".env", output)
        self.assertIn("secret.key", output)

    def test_clean_task_reports_no_sensitive_access(self):
        task = {
            "selected_skill": "unknown",
            "llm_response": "clarify",
            "tool_results": [],
        }

        output = ResponseFormatter().format(task)

        self.assertIn("未发现敏感文件读取行为。", output)
