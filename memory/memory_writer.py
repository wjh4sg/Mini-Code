import json
from pathlib import Path


EXPERIENCES = {
    "explain_project": "项目分析任务通常优先查看 README、依赖文件和核心目录。",
    "fix_error": "报错分析任务通常优先检查错误关键词、依赖声明、配置文件和相关源码。",
    "small_feature_plan": "小功能计划任务通常需要定位相关模块文件。",
    "patch_suggestion": "Patch 建议任务通常需要明确目标文件、修改点和影响范围。",
    "unknown": "未识别任务类型，未产生有效经验。",
}


class MemoryWriter:
    def __init__(self, app_root):
        self.memory_path = Path(app_root) / "data" / "memory.json"

    def save(self, task):
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        existing = self._load_existing()
        item = {
            "task_id": task.get("task_id"),
            "task_type": task.get("selected_skill", "unknown"),
            "query": task.get("user_query", ""),
            "workspace": str(task.get("workspace", "")),
            "related_files": self._related_files(task.get("tool_results", [])),
            "experience": EXPERIENCES.get(
                task.get("selected_skill"),
                EXPERIENCES["unknown"],
            ),
            "success": task.get("status") == "done",
            "created_at": task.get("created_at"),
        }
        existing.append(item)
        self.memory_path.write_text(
            json.dumps(existing, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return item

    def _load_existing(self):
        if not self.memory_path.exists():
            return []
        try:
            value = json.loads(self.memory_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        return value if isinstance(value, list) else []

    @staticmethod
    def _related_files(results):
        files = []
        for result in results:
            if not result.get("success"):
                continue
            if result.get("tool") == "read_file" and result.get("path"):
                files.append(result["path"])
            if result.get("tool") == "search_code":
                files.extend(
                    match["path"]
                    for match in result.get("matches", [])
                    if match.get("path")
                )
        return list(dict.fromkeys(files))[:20]
