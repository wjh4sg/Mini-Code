import re
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

from agent.context_builder import ContextBuilder
from agent.llm_client import LLMClient
from agent.response_formatter import ResponseFormatter
from agent.skill_router import SkillConfigError, SkillRouter
from memory.memory_writer import MemoryWriter
from tools.tool_executor import ToolExecutor


class QueryLoop:
    FEATURE_KEYWORD_MAP = {
        "用户": ["user", "account", "profile"],
        "昵称": ["nickname", "display_name", "username", "name"],
        "接口": ["router", "controller", "api", "route"],
        "登录": ["login", "auth", "token"],
        "分页": ["page", "pagination", "limit", "offset"],
        "搜索": ["search", "query", "keyword"],
    }
    SENSITIVE_TERMS = (
        ".env",
        "id_rsa",
        ".pem",
        ".key",
        "credentials",
        "token",
        "secret",
        "password",
        "api_key",
        "access_key",
    )
    FILE_PATTERN = re.compile(
        r"[A-Za-z0-9_.-]+(?:[\\/][A-Za-z0-9_.-]+)*"
        r"\.(?:py|js|ts|java|go|md|json|yaml|yml)",
        re.IGNORECASE,
    )
    PROJECT_FILES = (
        "README.md",
        "readme.md",
        "package.json",
        "requirements.txt",
        "pyproject.toml",
        "pom.xml",
        "go.mod",
    )

    def __init__(self, app_root, workspace, llm_client=None, memory_writer=None):
        self.app_root = Path(app_root).resolve()
        self.workspace = Path(workspace).resolve()
        self.tools = ToolExecutor(self.workspace)
        self.context_builder = ContextBuilder()
        self.llm_client = llm_client or LLMClient()
        self.formatter = ResponseFormatter()
        self.memory_writer = memory_writer or MemoryWriter(self.app_root)
        self.router = None
        self.router_error = None
        try:
            self.router = SkillRouter(self.app_root)
        except SkillConfigError as error:
            self.router_error = error

    def run(self, user_query):
        task = self._create_task(user_query)
        memory_warning = None
        try:
            task["status"] = "running"
            if self.router_error:
                raise self.router_error
            skill = self.router.route(user_query)
            task["selected_skill"] = skill["name"]
            task["skill_reason"] = skill.get("reason", "")
            task["tool_results"] = self._run_tools_by_skill(skill, user_query)
            task["context"] = self.context_builder.build(
                task,
                skill,
                task["tool_results"],
            )
            if skill["name"] == "unknown":
                task["llm_response"] = (
                    "暂时无法识别任务类型。请明确你是要分析项目、分析报错、"
                    "生成小功能计划，还是生成 Patch 建议。"
                )
            else:
                task["llm_response"] = self.llm_client.chat(task["context"], skill)
            task["status"] = "done"
        except Exception as error:
            task["status"] = "failed"
            task["llm_response"] = f"任务执行失败：{error}"

        self._debug(task)
        try:
            self.memory_writer.save(task)
        except Exception as error:
            memory_warning = str(error)

        task["final_answer"] = self.formatter.format(
            task,
            str(self.memory_writer.memory_path),
            memory_warning,
        )
        return task["final_answer"]

    def _create_task(self, user_query):
        return {
            "task_id": uuid.uuid4().hex[:12],
            "user_query": user_query,
            "app_root": str(self.app_root),
            "workspace": str(self.workspace),
            "selected_skill": "unknown",
            "tool_results": [],
            "context": "",
            "llm_response": "",
            "final_answer": "",
            "status": "created",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _run_tools_by_skill(self, skill, user_query):
        name = skill["name"]
        if name == "explain_project":
            return self._run_explain_project_tools()
        if name == "fix_error":
            return self._run_fix_error_tools(user_query)
        if name == "small_feature_plan":
            return self._run_small_feature_plan_tools(user_query)
        if name == "patch_suggestion":
            return self._run_patch_suggestion_tools(user_query)
        return []

    def _run_explain_project_tools(self):
        results = [self.tools.list_files(".")]
        available = set(results[0].get("result", [])) if results[0].get("success") else set()
        for path in self.PROJECT_FILES:
            if path in available:
                results.append(self.tools.read_file(path))
        return results

    def _run_fix_error_tools(self, user_query):
        results = []
        keywords = self._extract_keywords(user_query)[:3]
        for keyword in keywords:
            results.append(self.tools.search_code(keyword))
        for path in self.PROJECT_FILES[2:]:
            if (self.workspace / path).is_file():
                results.append(self.tools.read_file(path))
        return results

    def _run_small_feature_plan_tools(self, user_query):
        results = [
            self.tools.search_code(keyword)
            for keyword in self._expand_feature_keywords(user_query)[:6]
        ]
        for path in self._collect_related_files_from_search(results):
            results.append(self.tools.read_file(path))
        return results

    def _run_patch_suggestion_tools(self, user_query):
        sensitive = self._detect_sensitive_file_request(user_query)
        if sensitive:
            return [self.tools.read_file(sensitive)]
        paths = self._extract_file_paths(user_query)
        if paths:
            return [self.tools.read_file(paths[0])]
        results = [
            self.tools.search_code(keyword)
            for keyword in self._extract_keywords(user_query)[:3]
        ]
        for path in self._collect_related_files_from_search(results):
            results.append(self.tools.read_file(path))
        return results

    def _debug(self, task):
        if os.environ.get("MINICODE_DEBUG") != "1":
            return
        summaries = [
            {
                "tool": item.get("tool"),
                "success": item.get("success"),
                "summary": item.get("summary") or item.get("reason"),
            }
            for item in task.get("tool_results", [])
        ]
        print(f"[debug] app_root={self.app_root}", file=sys.stderr)
        print(f"[debug] workspace={self.workspace}", file=sys.stderr)
        print(f"[debug] selected_skill={task.get('selected_skill')}", file=sys.stderr)
        print(f"[debug] skill_reason={task.get('skill_reason', '')}", file=sys.stderr)
        print(f"[debug] tool_results={summaries}", file=sys.stderr)
        print(f"[debug] prompt_preview={task.get('context', '')[:1000]}", file=sys.stderr)
        print(f"[debug] memory_path={self.memory_writer.memory_path}", file=sys.stderr)

    def _extract_keywords(self, text):
        parts = re.split(r"[\s,，:：]+", text)
        return [part for part in parts if len(part) >= 2]

    def _expand_feature_keywords(self, text):
        keywords = []
        for chinese, expanded in self.FEATURE_KEYWORD_MAP.items():
            if chinese in text:
                keywords.extend(expanded)
        keywords.extend(self._extract_keywords(text))
        return list(dict.fromkeys(keywords))

    def _collect_related_files_from_search(self, results):
        first_seen = {}
        for result in results:
            if result.get("tool") != "search_code" or not result.get("success"):
                continue
            for match in result.get("matches", []):
                path = match.get("path")
                if path and path not in first_seen:
                    first_seen[path] = len(first_seen)

        def rank(path):
            lowered = path.lower()
            if "router" in lowered or "controller" in lowered:
                return 0
            if "service" in lowered:
                return 1
            if "schema" in lowered or "model" in lowered:
                return 2
            if "test" in lowered:
                return 3
            return 4

        return sorted(first_seen, key=lambda path: (rank(path), first_seen[path]))[:5]

    def _extract_file_paths(self, text):
        return self.FILE_PATTERN.findall(text)

    def _detect_sensitive_file_request(self, text):
        lowered = text.lower()
        candidates = re.findall(r"[A-Za-z0-9_./\\-]+", text)
        for candidate in candidates:
            candidate_lower = candidate.lower()
            if any(term in candidate_lower for term in self.SENSITIVE_TERMS):
                return candidate
        for term in self.SENSITIVE_TERMS:
            if term in lowered:
                return term
        return None
