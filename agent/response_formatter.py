class ResponseFormatter:
    def format(self, task, memory_path=None, memory_warning=None):
        process_lines = []
        denied = []
        for result in task.get("tool_results", []):
            tool = result.get("tool", "unknown")
            argument = result.get("path") or result.get("keyword")
            label = f'{tool}("{argument}")' if argument else tool
            if result.get("success"):
                process_lines.append(f"- {label} success")
            else:
                reason = result.get("reason", "未知错误")
                process_lines.append(f"- {label} failed: {reason}")
                if "禁止" in reason:
                    denied.append(f"- {result.get('path', argument)}: {reason}")
            for item in result.get("rejected_files", []):
                reason = item.get("reason", "禁止访问")
                denied.append(f"- {item.get('path')}: {reason}")

        process = "\n".join(process_lines) or "- 未调用工具"
        risk = (
            "检测到被拒绝的访问：\n" + "\n".join(dict.fromkeys(denied))
            if denied
            else "未发现敏感文件读取行为。"
        )
        memory_text = f"任务执行完成后将保存到 {memory_path or 'app_root/data/memory.json'}"
        if memory_warning:
            memory_text += f"\n警告：{memory_warning}"
        return (
            f"【任务类型】\n{task.get('selected_skill', 'unknown')}\n\n"
            f"【执行过程】\n{process}\n\n"
            f"【分析结果】\n{task.get('llm_response', '')}\n\n"
            f"【风险检查】\n{risk}\n\n"
            f"【记忆保存】\n{memory_text}"
        )
