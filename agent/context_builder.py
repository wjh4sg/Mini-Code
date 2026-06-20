class ContextBuilder:
    def build(self, task, skill, tool_results):
        tool_summaries = []
        project_context = []
        code_snippets = []

        for result in tool_results:
            status = "success" if result.get("success") else "failed"
            summary = result.get("summary") or result.get("reason", "")
            tool_summaries.append(f"- {result.get('tool')} {status}: {summary}")

            if result.get("tool") == "list_files" and result.get("success"):
                project_context.append(
                    "目录结构：\n" + "\n".join(result.get("result", [])[:80])
                )
            elif result.get("tool") == "read_file" and result.get("success"):
                project_context.append(
                    f"- {result['path']}：共 {result.get('line_count', 0)} 行，"
                    f"truncated={str(result.get('truncated', False)).lower()}"
                )
                lines = result.get("content", "").splitlines()[:80]
                code_snippets.append(
                    f"文件：{result['path']}\n[代码片段]\n" + "\n".join(lines)
                )
            elif result.get("tool") == "search_code" and result.get("success"):
                matches = result.get("matches", [])[:10]
                rendered = [
                    f"- {item['path']}:{item['line']}  {item['text']}"
                    for item in matches
                ]
                code_snippets.append(
                    f"关键词 {result.get('keyword')} 的搜索结果：\n"
                    + "\n".join(rendered)
                )

        output_schema = "\n".join(f"- {item}" for item in skill.get("output_schema", []))
        return (
            "你是 MiniCode，一个本地代码项目分析助手。\n\n"
            f"用户任务：\n{task.get('user_query', '')}\n\n"
            f"当前 Skill：\n{skill.get('name', '')}\n\n"
            f"Skill 说明：\n{skill.get('description', '')}\n\n"
            "已调用工具：\n"
            + ("\n".join(tool_summaries) or "- 未调用工具")
            + "\n\n项目上下文：\n"
            + ("\n".join(project_context) or "未获取项目上下文")
            + "\n\n相关代码片段：\n"
            + ("\n\n".join(code_snippets) or "未获取相关代码片段")
            + f"\n\n输出要求：\n{output_schema or '- 清晰说明结果'}\n\n"
            "回答约束：\n"
            "1. 只能基于提供的项目上下文回答。\n"
            "2. 不要编造不存在的文件、函数、接口。\n"
            "3. 如果上下文不足，需要明确说明。\n"
            "4. 如果涉及修改，只给计划或 Patch 建议，不直接修改文件。\n"
            "5. 输出要清晰分段。"
        )
