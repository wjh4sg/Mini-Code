import json
import unittest
import urllib.error

from agent.llm_client import LLMClient


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.body


class LLMClientTests(unittest.TestCase):
    def test_mock_mode_contains_skill_output_sections(self):
        schemas = {
            "explain_project": ["项目用途", "技术栈"],
            "fix_error": ["错误类型", "可能原因"],
            "small_feature_plan": ["任务理解", "实现步骤"],
            "patch_suggestion": ["修改原因", "Patch 建议"],
            "unknown": ["任务说明"],
        }
        client = LLMClient(environ={})

        for skill, headings in schemas.items():
            with self.subTest(skill=skill):
                answer = client.chat("prompt", {"name": skill, "output_schema": headings})
                for heading in headings:
                    self.assertIn(heading, answer)

    def test_real_mode_sends_openai_compatible_request(self):
        captured = {}

        def opener(request, timeout):
            captured["request"] = request
            captured["timeout"] = timeout
            return FakeResponse(
                json.dumps(
                    {"choices": [{"message": {"content": "real answer"}}]}
                ).encode()
            )

        client = LLMClient(
            environ={
                "MINICODE_API_KEY": "key",
                "MINICODE_BASE_URL": "https://example.test/v1/",
                "MINICODE_MODEL": "demo-model",
            },
            opener=opener,
            timeout=7,
        )

        answer = client.chat("prompt", {"name": "explain_project", "output_schema": []})

        self.assertEqual(answer, "real answer")
        self.assertEqual(captured["request"].full_url, "https://example.test/v1/chat/completions")
        self.assertEqual(captured["request"].method, "POST")
        self.assertEqual(captured["timeout"], 7)
        payload = json.loads(captured["request"].data.decode())
        self.assertEqual(payload["model"], "demo-model")
        self.assertEqual(payload["temperature"], 0.2)
        self.assertEqual(
            captured["request"].headers["Authorization"],
            "Bearer key",
        )

    def test_real_mode_failures_fall_back_to_mock(self):
        failures = [
            lambda request, timeout: (_ for _ in ()).throw(TimeoutError("slow")),
            lambda request, timeout: FakeResponse(b"{bad"),
            lambda request, timeout: FakeResponse(b'{"choices": []}'),
            lambda request, timeout: FakeResponse(
                b'{"choices": [{"message": {}}]}'
            ),
        ]
        skill = {"name": "fix_error", "output_schema": ["错误类型"]}
        environ = {
            "MINICODE_API_KEY": "key",
            "MINICODE_BASE_URL": "https://example.test/v1",
        }

        for opener in failures:
            with self.subTest(opener=opener):
                answer = LLMClient(environ=environ, opener=opener).chat("prompt", skill)
                self.assertIn("【模型调用失败】", answer)
                self.assertIn("错误类型", answer)
