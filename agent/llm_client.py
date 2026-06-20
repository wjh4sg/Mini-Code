import json
import os
import urllib.error
import urllib.request


class LLMClient:
    def __init__(self, environ=None, opener=None, timeout=20):
        self.environ = os.environ if environ is None else environ
        self.opener = urllib.request.urlopen if opener is None else opener
        self.timeout = timeout

    def chat(self, prompt, skill):
        api_key = self.environ.get("MINICODE_API_KEY")
        base_url = self.environ.get("MINICODE_BASE_URL")
        if not api_key or not base_url:
            return self._mock_response(skill)

        try:
            return self._real_response(prompt, skill, api_key, base_url)
        except (
            OSError,
            TimeoutError,
            urllib.error.URLError,
            urllib.error.HTTPError,
            json.JSONDecodeError,
            KeyError,
            IndexError,
            TypeError,
            ValueError,
        ) as error:
            return (
                "【模型调用失败】\n"
                f"原因：{error}\n"
                "已降级为 Mock 模式返回示例分析结果。\n\n"
                + self._mock_response(skill)
            )

    def _real_response(self, prompt, skill, api_key, base_url):
        payload = {
            "model": self.environ.get("MINICODE_MODEL", "gpt-4o-mini"),
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个谨慎的本地代码项目分析助手。",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        request = urllib.request.Request(
            base_url.rstrip("/") + "/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with self.opener(request, timeout=self.timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        if not isinstance(content, str) or not content.strip():
            raise ValueError("模型响应内容为空")
        return content

    def _mock_response(self, skill):
        schema = skill.get("output_schema") or self._default_schema(skill.get("name"))
        sections = []
        for heading in schema:
            sections.append(f"【{heading}】\nMock 模式示例：请结合上方项目上下文进行判断。")
        return "\n\n".join(sections) or "Mock 模式：暂无可用输出结构。"

    @staticmethod
    def _default_schema(skill_name):
        return {
            "explain_project": ["项目用途", "技术栈", "目录结构", "启动方式", "建议阅读顺序"],
            "fix_error": ["错误类型", "可能原因", "相关文件", "修复建议"],
            "small_feature_plan": ["任务理解", "可能涉及文件", "实现步骤", "测试建议", "风险点"],
            "patch_suggestion": ["修改原因", "Patch 建议", "影响范围", "注意事项"],
            "unknown": ["任务说明"],
        }.get(skill_name, ["任务说明"])
