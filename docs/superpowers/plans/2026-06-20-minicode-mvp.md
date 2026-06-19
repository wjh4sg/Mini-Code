# MiniCode MVP v0.1.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify the complete read-only MiniCode CLI coding-agent MVP described in the approved v0.1.1 design.

**Architecture:** `main.py` creates a `QueryLoop` with separate application-root and workspace paths. The loop routes the task, calls read-only tools through a permission-checking facade, builds compressed model context, obtains a mock or OpenAI-compatible response, formats the result, and writes task memory under the application root.

**Tech Stack:** Python 3.10+ standard library, `unittest`, JSON, `pathlib`, `urllib.request`, Git.

---

## File Map

| Path | Responsibility |
| --- | --- |
| `main.py` | CLI argument handling and root-path setup |
| `agent/loop.py` | Task session and orchestration |
| `agent/skill_router.py` | Deterministic task classification |
| `agent/context_builder.py` | Prompt construction and truncation |
| `agent/llm_client.py` | Mock and OpenAI-compatible model calls |
| `agent/response_formatter.py` | Stable five-section CLI response |
| `tools/file_tools.py` | Depth-limited listing and safe text reads |
| `tools/search_tools.py` | Permission-aware line search |
| `tools/tool_executor.py` | Read-only tool facade |
| `safety/permission_checker.py` | Workspace and sensitive-path enforcement |
| `memory/memory_writer.py` | JSON memory persistence |
| `skills/skills.json` | Four supported skill definitions |
| `examples/sample_project/` | Demonstration workspace |
| `tests/` | Unit and integration tests |
| `README.md` | User, architecture, safety, and demo documentation |

## Task 1: Repository Scaffold and CLI Path Model

**Files:**
- Create: `main.py`
- Create: `agent/__init__.py`
- Create: `tools/__init__.py`
- Create: `safety/__init__.py`
- Create: `memory/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/test_main.py`
- Create: `data/memory.json`

- [ ] **Step 1: Write failing CLI-path tests**

```python
# tests/test_main.py
import io
import unittest
from pathlib import Path
from unittest.mock import patch

import main


class MainTests(unittest.TestCase):
    def test_missing_query_prints_usage(self):
        output = io.StringIO()
        with patch("sys.argv", ["main.py"]), patch("sys.stdout", output):
            code = main.main()
        self.assertEqual(code, 1)
        self.assertIn("用法", output.getvalue())

    def test_app_root_is_main_directory_and_workspace_is_cwd(self):
        app_root, workspace = main.resolve_roots()
        self.assertEqual(app_root, Path(main.__file__).resolve().parent)
        self.assertEqual(workspace, Path.cwd().resolve())
```

- [ ] **Step 2: Verify the tests fail**

Run:

```powershell
python -m unittest tests.test_main -v
```

Expected: import or attribute failures because `main.py` does not exist.

- [ ] **Step 3: Implement the minimal CLI**

```python
# main.py
import sys
from pathlib import Path


def resolve_roots():
    return Path(__file__).resolve().parent, Path.cwd().resolve()


def main():
    if len(sys.argv) < 2:
        print('用法: python main.py "你的任务"')
        return 1
    from agent.loop import QueryLoop

    query = " ".join(sys.argv[1:]).strip()
    app_root, workspace = resolve_roots()
    print(QueryLoop(app_root, workspace).run(query))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Create empty package markers and initialize `data/memory.json` to:

```json
[]
```

- [ ] **Step 4: Add a temporary orchestration shell**

```python
# agent/loop.py
class QueryLoop:
    def __init__(self, app_root, workspace):
        self.app_root = app_root
        self.workspace = workspace

    def run(self, user_query):
        return f"MiniCode received: {user_query}"
```

- [ ] **Step 5: Run the focused test and smoke command**

Run:

```powershell
python -m unittest tests.test_main -v
python main.py "hello"
```

Expected: two tests pass and the command prints `MiniCode received: hello`.

- [ ] **Step 6: Commit P0 scaffold**

```powershell
git add main.py agent tools safety memory tests data
git commit -m "feat: scaffold MiniCode CLI"
```

## Task 2: Workspace and Sensitive-Path Permission Checking

**Files:**
- Create: `safety/permission_checker.py`
- Create: `tests/test_permission_checker.py`

- [ ] **Step 1: Write failing permission tests**

```python
# tests/test_permission_checker.py
import tempfile
import unittest
from pathlib import Path

from safety.permission_checker import PermissionChecker


class PermissionCheckerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name)
        self.checker = PermissionChecker(self.workspace)

    def tearDown(self):
        self.temp.cleanup()

    def test_allows_normal_workspace_file(self):
        self.assertEqual(self.checker.check_path(Path("README.md")), (True, "allowed"))

    def test_denies_required_sensitive_patterns(self):
        denied = [
            ".env", ".env.local", "private.key", "config.secret.json",
            "aws_credentials", "database_password.txt", ".ssh/id_rsa",
        ]
        for path in denied:
            with self.subTest(path=path):
                self.assertFalse(self.checker.check_path(Path(path))[0])

    def test_denies_traversal_and_absolute_external_paths(self):
        self.assertFalse(self.checker.check_path(Path("../.env"))[0])
        outside = self.workspace.parent / "outside.txt"
        self.assertFalse(self.checker.check_path(outside)[0])
```

- [ ] **Step 2: Verify the tests fail**

Run:

```powershell
python -m unittest tests.test_permission_checker -v
```

Expected: module import failure.

- [ ] **Step 3: Implement `PermissionChecker`**

Implement:

```python
class PermissionChecker:
    SENSITIVE_NAMES = {
        ".env", ".env.local", ".env.production", "id_rsa", "id_dsa",
        "credentials", "credential", "token", "secret",
    }
    SENSITIVE_DIRS = {".ssh", ".gnupg"}
    SENSITIVE_SUFFIXES = {".pem", ".key", ".crt", ".p12"}
    SENSITIVE_KEYWORDS = {
        "token", "secret", "password", "passwd", "credential",
        "credentials", "private", "api_key", "access_key",
    }

    def __init__(self, workspace):
        self.workspace = Path(workspace).resolve()

    def check_path(self, path):
        candidate = Path(path)
        target = candidate.resolve() if candidate.is_absolute() else (self.workspace / candidate).resolve()
        try:
            target.relative_to(self.workspace)
        except ValueError:
            return False, f"禁止访问项目目录外路径：{path}"
        lowered_parts = {part.lower() for part in target.parts}
        if lowered_parts & self.SENSITIVE_DIRS:
            return False, f"禁止读取敏感目录：{path}"
        name = target.name.lower()
        if name in self.SENSITIVE_NAMES:
            return False, f"禁止读取敏感文件：{path}"
        if target.suffix.lower() in self.SENSITIVE_SUFFIXES:
            return False, f"禁止读取敏感文件：{path}"
        if any(keyword in name for keyword in self.SENSITIVE_KEYWORDS):
            return False, f"禁止读取敏感文件：{path}"
        return True, "allowed"
```

- [ ] **Step 4: Add symlink escape coverage where supported**

Create a symlink inside the temporary workspace that points outside. Skip only
when Windows denies symlink creation. Assert `check_path` denies it.

- [ ] **Step 5: Run focused tests**

Run:

```powershell
python -m unittest tests.test_permission_checker -v
```

Expected: all permission tests pass.

- [ ] **Step 6: Commit**

```powershell
git add safety/permission_checker.py tests/test_permission_checker.py
git commit -m "feat: enforce workspace read boundaries"
```

## Task 3: File Listing and Safe File Reading

**Files:**
- Create: `tools/file_tools.py`
- Create: `tests/test_file_tools.py`

- [ ] **Step 1: Write failing tests for listing and reading**

Tests must create a temporary project containing:

```text
README.md
src/app.py
src/deep/module.py
.git/config
.env
binary.bin
large.txt
```

Test these exact behaviors:

```python
result = list_files(workspace, ".", max_depth=1, max_items=20)
self.assertTrue(result["success"])
self.assertIn("README.md", result["result"])
self.assertIn("src/", result["result"])
self.assertNotIn(".git/", result["result"])

read = read_file(workspace, "README.md", checker, max_lines=1)
self.assertTrue(read["success"])
self.assertEqual(read["line_count"], 2)
self.assertTrue(read["truncated"])

self.assertFalse(read_file(workspace, ".env", checker)["success"])
self.assertFalse(read_file(workspace, "binary.bin", checker)["success"])
self.assertFalse(read_file(workspace, "large.txt", checker, max_file_size=4)["success"])
self.assertFalse(list_files(workspace, "..")["success"])
```

- [ ] **Step 2: Verify failures**

Run:

```powershell
python -m unittest tests.test_file_tools -v
```

Expected: import failure.

- [ ] **Step 3: Implement `list_files`**

Use a deterministic, case-insensitive name sort. Return relative POSIX-style
paths, append `/` to directories, skip:

```python
IGNORED_DIRS = {
    ".git", "node_modules", "__pycache__", "dist", "build",
    ".venv", "venv", ".idea", ".vscode",
}
```

Reject a requested root outside the workspace. Stop at `max_items`. A
`max_depth` of zero records only direct children and does not recurse.

- [ ] **Step 4: Implement `read_file`**

Use:

```python
TEXT_SUFFIXES = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".md", ".txt",
    ".yaml", ".yml", ".toml", ".ini", ".cfg", ".java", ".go",
    ".html", ".css", ".scss", ".vue",
}
```

Call `permission_checker.check_path` before existence checks. Reject missing,
non-file, unsupported suffix, and oversized targets with `success=False`.
Read UTF-8 with `errors="ignore"`, report the full source `line_count`, and put
only the first `max_lines` lines in `content`.

- [ ] **Step 5: Run tests**

Run:

```powershell
python -m unittest tests.test_file_tools -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```powershell
git add tools/file_tools.py tests/test_file_tools.py
git commit -m "feat: add safe workspace file tools"
```

## Task 4: Permission-Aware Code Search and Tool Facade

**Files:**
- Create: `tools/search_tools.py`
- Create: `tools/tool_executor.py`
- Create: `tests/test_search_tools.py`
- Create: `tests/test_tool_executor.py`

- [ ] **Step 1: Write failing search tests**

Create `app/user_service.py` containing both `UserService` and `nickname`,
`.env` containing `USER_TOKEN`, and an ignored `.git/hidden.py`.

Assert:

```python
result = search_code(workspace, "user", checker, max_results=10)
self.assertTrue(result["success"])
self.assertEqual(result["matches"][0]["path"], "app/user_service.py")
self.assertEqual(result["matches"][0]["line"], 1)
self.assertTrue(any(item["path"] == ".env" for item in result["rejected_files"]))
self.assertFalse(any(".git" in item["path"] for item in result["matches"]))
```

Also test case-insensitive matching, empty keywords, oversized files, and
`max_results`.

- [ ] **Step 2: Verify failures**

Run:

```powershell
python -m unittest tests.test_search_tools tests.test_tool_executor -v
```

Expected: import failures.

- [ ] **Step 3: Implement `search_code`**

Scan only:

```python
SEARCH_SUFFIXES = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go",
    ".md", ".json", ".yaml", ".yml", ".toml", ".html", ".css", ".vue",
}
```

Walk deterministically, prune ignored directories, call the permission checker
for every candidate file before size or content access, collect rejected paths,
read UTF-8 with ignored errors, perform lowercase substring matching, and stop
at `max_results`.

- [ ] **Step 4: Implement `ToolExecutor`**

```python
class ToolExecutor:
    def __init__(self, workspace):
        self.workspace = Path(workspace).resolve()
        self.permission_checker = PermissionChecker(self.workspace)

    def list_files(self, path="."):
        return list_files(self.workspace, path)

    def read_file(self, path):
        return read_file(self.workspace, path, self.permission_checker)

    def search_code(self, keyword):
        return search_code(self.workspace, keyword, self.permission_checker)
```

- [ ] **Step 5: Run focused tests**

Run:

```powershell
python -m unittest tests.test_search_tools tests.test_tool_executor -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```powershell
git add tools/search_tools.py tools/tool_executor.py tests/test_search_tools.py tests/test_tool_executor.py
git commit -m "feat: add permission-aware code search"
```

## Task 5: Skill Configuration and Deterministic Router

**Files:**
- Create: `skills/skills.json`
- Create: `agent/skill_router.py`
- Create: `tests/test_skill_router.py`

- [ ] **Step 1: Write failing routing tests**

Cover:

```python
self.assertEqual(router.route("帮我分析这个项目")["name"], "explain_project")
self.assertEqual(router.route("运行时报错 ModuleNotFoundError")["name"], "fix_error")
self.assertEqual(router.route("帮我给用户模块增加修改昵称接口")["name"], "small_feature_plan")
self.assertEqual(router.route("帮我修改 src/config.py")["name"], "patch_suggestion")
self.assertEqual(router.route("hello")["name"], "unknown")
self.assertEqual(router.route("读取 .env 看看")["name"], "patch_suggestion")
```

Also assert a missing or malformed skills file raises `SkillConfigError` with a
clear Chinese message.

- [ ] **Step 2: Verify failures**

Run:

```powershell
python -m unittest tests.test_skill_router -v
```

Expected: import failure.

- [ ] **Step 3: Create `skills/skills.json`**

Use the exact four skill objects and output schemas from source SPEC section 14.

- [ ] **Step 4: Implement router priority**

Compile recognized file extensions into a regex that accepts slash-separated
or backslash-separated relative paths. Implement:

```python
SENSITIVE_REQUEST_TERMS = (
    ".env", "id_rsa", ".pem", ".key", "credentials",
    "token", "secret", "password", "api_key", "access_key",
)
PATCH_TERMS = ("patch", "diff", "改这个文件", "修这个函数", "给出 patch")
ERROR_TERMS = ("报错", "错误", "error", "exception", "failed", "traceback", "失败", "modulenotfounderror")
FEATURE_TERMS = ("新增", "增加", "添加", "接口", "功能", "页面", "分页", "搜索", "模块")
PROJECT_TERMS = ("分析", "项目", "结构", "目录", "启动", "技术栈", "看一下")
```

Return a copy of the matched skill plus `reason`. For unknown, return the exact
unknown shape from the SPEC.

- [ ] **Step 5: Run tests**

Run:

```powershell
python -m unittest tests.test_skill_router -v
```

Expected: all routing tests pass, including the nickname regression.

- [ ] **Step 6: Commit**

```powershell
git add skills/skills.json agent/skill_router.py tests/test_skill_router.py
git commit -m "feat: route MiniCode task skills"
```

## Task 6: Context Builder and Keyword/File Selection Helpers

**Files:**
- Create: `agent/context_builder.py`
- Create: `tests/test_context_builder.py`
- Create: `tests/test_loop_helpers.py`
- Modify: `agent/loop.py`

- [ ] **Step 1: Write failing context tests**

Build sample task and tool results and assert the prompt contains:

```text
用户任务：
当前 Skill：
已调用工具：
项目上下文：
相关代码片段：
输出要求：
回答约束：
```

Create 100 listed paths, 15 search matches, and 100 read lines. Assert only 80,
10, and 80 respectively appear.

- [ ] **Step 2: Write failing helper tests**

Instantiate `QueryLoop` with a temporary app/workspace and test:

```python
keywords = loop._expand_feature_keywords("帮我给用户增加昵称接口")
self.assertEqual(
    keywords[:6],
    ["user", "account", "profile", "nickname", "display_name", "username"],
)

files = loop._collect_related_files_from_search(results)
self.assertEqual(
    files,
    ["app/user_router.py", "app/user_service.py", "app/user_schema.py", "tests/test_user.py"],
)

self.assertEqual(loop._extract_file_paths("修改 src/config.py"), ["src/config.py"])
```

- [ ] **Step 3: Verify failures**

Run:

```powershell
python -m unittest tests.test_context_builder tests.test_loop_helpers -v
```

Expected: missing implementation failures.

- [ ] **Step 4: Implement `ContextBuilder`**

Create `ContextBuilder.build(task, skill, tool_results) -> str`. Format tool
summaries, list results, read snippets, and search matches using the approved
design headings and fixed limits.

- [ ] **Step 5: Implement loop helper methods**

Add constants for Chinese mappings and dependency/project descriptor files.
Implement:

```python
_extract_keywords(text)
_expand_feature_keywords(text)
_collect_related_files_from_search(results)
_extract_file_paths(text)
_detect_sensitive_file_request(text)
```

Preserve insertion order while removing duplicates. `_collect_related_files`
uses path-category rank followed by first-seen order and returns at most five.

- [ ] **Step 6: Run focused tests**

Run:

```powershell
python -m unittest tests.test_context_builder tests.test_loop_helpers -v
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```powershell
git add agent/context_builder.py agent/loop.py tests/test_context_builder.py tests/test_loop_helpers.py
git commit -m "feat: build compressed project context"
```

## Task 7: Mock and OpenAI-Compatible Model Client

**Files:**
- Create: `agent/llm_client.py`
- Create: `tests/test_llm_client.py`

- [ ] **Step 1: Write failing model tests**

Test no-credential mock output for every skill and assert each configured output
heading is included.

Patch `urllib.request.urlopen` with a context manager returning:

```json
{"choices":[{"message":{"content":"real answer"}}]}
```

Assert the request URL is `https://example.test/v1/chat/completions`, method is
POST, the JSON body has model/messages/temperature, and the result is
`real answer`.

Patch timeouts, HTTP errors, invalid JSON, empty choices, and absent message
content. Assert each response contains `【模型调用失败】` and a mock result.

- [ ] **Step 2: Verify failures**

Run:

```powershell
python -m unittest tests.test_llm_client -v
```

Expected: import failure.

- [ ] **Step 3: Implement `LLMClient`**

Use constructor dependency injection:

```python
class LLMClient:
    def __init__(self, environ=None, opener=None, timeout=20):
        self.environ = os.environ if environ is None else environ
        self.opener = urllib.request.urlopen if opener is None else opener
        self.timeout = timeout
```

`chat(prompt, skill)` chooses mock mode unless both key and base URL exist.
Real mode sends:

```python
{
    "model": environ.get("MINICODE_MODEL", "gpt-4o-mini"),
    "messages": [
        {"role": "system", "content": "你是一个谨慎的本地代码项目分析助手。"},
        {"role": "user", "content": prompt},
    ],
    "temperature": 0.2,
}
```

The Authorization header is `Bearer <key>`. Catch expected request and decode
exceptions and return `failure notice + mock response`.

- [ ] **Step 4: Run focused tests**

Run:

```powershell
python -m unittest tests.test_llm_client -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```powershell
git add agent/llm_client.py tests/test_llm_client.py
git commit -m "feat: add resilient model client"
```

## Task 8: Response Formatting and Task Memory

**Files:**
- Create: `agent/response_formatter.py`
- Create: `memory/memory_writer.py`
- Create: `tests/test_response_formatter.py`
- Create: `tests/test_memory_writer.py`

- [ ] **Step 1: Write failing formatter tests**

Create a task with successful and denied results. Assert all five required
sections appear, each tool appears in execution order, and denied `read_file`
plus search `rejected_files` appear under risk checking.

For a clean task assert:

```text
未发现敏感文件读取行为。
```

- [ ] **Step 2: Write failing memory tests**

Use a temporary app root. Assert:

- successful read paths and search paths are stored;
- duplicates are removed in first-seen order;
- rejected files are absent;
- more than 20 paths are truncated;
- malformed JSON becomes a new one-item array;
- parent directories are created;
- each supported skill gets the exact experience sentence from the SPEC.

- [ ] **Step 3: Verify failures**

Run:

```powershell
python -m unittest tests.test_response_formatter tests.test_memory_writer -v
```

Expected: import failures.

- [ ] **Step 4: Implement `ResponseFormatter`**

Provide:

```python
class ResponseFormatter:
    def format(self, task, memory_path=None, memory_warning=None):
        ...
```

Generate the exact five headings. Use tool name plus path/keyword in process
lines. Aggregate denied reasons without duplication. Add a memory warning after
the target path when supplied.

- [ ] **Step 5: Implement `MemoryWriter`**

Provide:

```python
class MemoryWriter:
    def __init__(self, app_root):
        self.memory_path = Path(app_root) / "data" / "memory.json"

    def save(self, task):
        ...
```

Write JSON using `ensure_ascii=False, indent=2`. Return the created memory item.
Let unexpected filesystem write exceptions propagate so `QueryLoop` can show a
nonfatal warning.

- [ ] **Step 6: Run tests**

Run:

```powershell
python -m unittest tests.test_response_formatter tests.test_memory_writer -v
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```powershell
git add agent/response_formatter.py memory/memory_writer.py tests/test_response_formatter.py tests/test_memory_writer.py
git commit -m "feat: format responses and persist task memory"
```

## Task 9: Complete QueryLoop Orchestration and Debug Mode

**Files:**
- Modify: `agent/loop.py`
- Modify: `main.py`
- Create: `tests/test_query_loop.py`

- [ ] **Step 1: Write failing end-to-end loop tests**

Build temporary app and workspace trees with copied `skills.json`. Inject a
stub LLM returning `"analysis"`.

Test:

1. each of the four queries selects the expected skill;
2. feature planning searches and reads router/service/schema/test files;
3. `.env` request records a denied tool result and risk message;
4. unknown calls no tools and still stores memory;
5. missing skills returns a readable error without traceback;
6. memory write failure preserves the analysis and adds a warning;
7. `MINICODE_DEBUG=1` writes roots, skill, tool summaries, prompt preview, and
   memory path to stderr;
8. memory is written under app root, not workspace.

- [ ] **Step 2: Verify failures**

Run:

```powershell
python -m unittest tests.test_query_loop -v
```

Expected: orchestration assertions fail.

- [ ] **Step 3: Construct dependencies in `QueryLoop.__init__`**

```python
self.router = SkillRouter(app_root)
self.tools = ToolExecutor(workspace)
self.context_builder = ContextBuilder()
self.llm_client = llm_client or LLMClient()
self.formatter = ResponseFormatter()
self.memory_writer = memory_writer or MemoryWriter(app_root)
```

- [ ] **Step 4: Implement task creation**

Use `uuid.uuid4().hex[:12]`, local timestamp
`datetime.now().strftime("%Y-%m-%d %H:%M:%S")`, stringified roots, empty
context/response fields, and status transitions `created -> running -> done` or
`failed`.

- [ ] **Step 5: Implement four tool strategies**

Implement exactly:

```python
_run_explain_project_tools()
_run_fix_error_tools(user_query)
_run_small_feature_plan_tools(user_query)
_run_patch_suggestion_tools(user_query)
_run_tools_by_skill(skill, user_query)
```

Avoid reading a file twice. Use existence information from `list_files` for
project descriptors. Every read and search goes through `ToolExecutor`.

- [ ] **Step 6: Implement `run` and nonfatal memory behavior**

Route, execute, build, call model, format, save memory, and reformat with a
warning only if memory saving fails. For configuration or unexpected failures,
populate a clear `llm_response`, mark failed, format, and attempt memory.

- [ ] **Step 7: Implement debug output**

When `MINICODE_DEBUG == "1"`, write diagnostics to `sys.stderr`. Never print API
keys, authorization headers, or full environment values.

- [ ] **Step 8: Run focused and accumulated tests**

Run:

```powershell
python -m unittest tests.test_query_loop -v
python -m unittest discover -v
```

Expected: all tests pass.

- [ ] **Step 9: Commit**

```powershell
git add main.py agent/loop.py tests/test_query_loop.py
git commit -m "feat: complete MiniCode agent loop"
```

## Task 10: Demonstration Workspace

**Files:**
- Create: `examples/sample_project/.env`
- Create: `examples/sample_project/README.md`
- Create: `examples/sample_project/requirements.txt`
- Create: `examples/sample_project/app/main.py`
- Create: `examples/sample_project/app/user_router.py`
- Create: `examples/sample_project/app/user_service.py`
- Create: `examples/sample_project/app/user_schema.py`
- Create: `examples/sample_project/tests/test_user.py`
- Create: `tests/test_demo_project.py`

- [ ] **Step 1: Write failing demo-content tests**

Assert all required paths exist and required text is present:

```python
self.assertIn("fastapi", requirements)
self.assertIn("APIRouter", user_router)
self.assertIn('prefix="/user"', user_router)
self.assertIn("class UserService", user_service)
self.assertIn("nickname", user_service)
self.assertIn("class UserProfile", user_schema)
self.assertIn("def test_", demo_test)
self.assertIn("FAKE_API_KEY=demo", env_text)
```

- [ ] **Step 2: Verify failures**

Run:

```powershell
python -m unittest tests.test_demo_project -v
```

Expected: missing-path failures.

- [ ] **Step 3: Create the demo application**

The demo code must be syntactically valid but need not be imported by MiniCode
tests. Implement:

```python
# app/user_schema.py
from pydantic import BaseModel


class UserProfile(BaseModel):
    user_id: int
    nickname: str
```

```python
# app/user_service.py
from .user_schema import UserProfile


class UserService:
    def get_user(self, user_id: int) -> UserProfile:
        return UserProfile(user_id=user_id, nickname="Mini User")
```

```python
# app/user_router.py
from fastapi import APIRouter
from .user_service import UserService

router = APIRouter(prefix="/user")
service = UserService()


@router.get("/{user_id}")
def get_user(user_id: int):
    return service.get_user(user_id)
```

Create a FastAPI app including the router, a simple service unit test, the three
requirements, explanatory README, and fake `.env`.

- [ ] **Step 4: Run demo-content and safety tests**

Run:

```powershell
python -m unittest tests.test_demo_project tests.test_permission_checker -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```powershell
git add examples tests/test_demo_project.py
git commit -m "feat: add MiniCode demo workspace"
```

## Task 11: README and Acceptance-Test Harness

**Files:**
- Create: `README.md`
- Create: `tests/test_cli_acceptance.py`

- [ ] **Step 1: Write failing README and CLI acceptance tests**

README tests assert it contains all 12 required sections/concepts from SPEC
section 33 and the exact boundary statement:

```text
MiniCode v0.1.1 是一个本地 CLI Coding Agent MVP。
第一版只输出分析、计划和 Patch 建议，不自动修改文件。
```

CLI acceptance tests use `subprocess.run` with:

```python
[
    "帮我分析这个项目",
    "帮我给用户模块增加修改昵称接口",
    "运行时报错 ModuleNotFoundError: No module named 'fastapi'，帮我分析",
    "读取 .env 看看",
]
```

Run from `examples/sample_project`, invoke the repository `main.py`, clear real
model environment variables, and assert exit code zero plus all five required
headings. Assert the four expected skill names and the `.env` denial.

- [ ] **Step 2: Verify failures**

Run:

```powershell
python -m unittest tests.test_cli_acceptance -v
```

Expected: README or acceptance assertions fail.

- [ ] **Step 3: Write complete README**

Include:

1. one-sentence introduction;
2. background;
3. features;
4. Mermaid execution flow;
5. repository tree;
6. installation;
7. quick start;
8. four demo commands;
9. module responsibilities;
10. MVP boundaries;
11. safety rules;
12. future plan;
13. debug and real-model environment variables;
14. test command.

- [ ] **Step 4: Run acceptance tests**

Run:

```powershell
python -m unittest tests.test_cli_acceptance -v
```

Expected: all four CLI scenarios pass.

- [ ] **Step 5: Commit**

```powershell
git add README.md tests/test_cli_acceptance.py
git commit -m "docs: add MiniCode usage and acceptance coverage"
```

## Task 12: Full Verification and Cleanup

**Files:**
- Modify only files required by failing verification.

- [ ] **Step 1: Run syntax compilation**

```powershell
python -m compileall -q .
```

Expected: exit code 0 with no syntax errors.

- [ ] **Step 2: Run the complete automated suite**

```powershell
python -m unittest discover -v
```

Expected: all tests pass with zero errors and zero failures.

- [ ] **Step 3: Run the four manual demos**

From `examples/sample_project`:

```powershell
python ..\..\main.py "帮我分析这个项目"
python ..\..\main.py "帮我给用户模块增加修改昵称接口"
python ..\..\main.py "运行时报错 ModuleNotFoundError: No module named 'fastapi'，帮我分析"
python ..\..\main.py "读取 .env 看看"
```

Expected:

- every command exits zero;
- every output has the five headings;
- the skills are respectively `explain_project`, `small_feature_plan`,
  `fix_error`, and `patch_suggestion`;
- the last output visibly denies `.env`;
- `data/memory.json` under the application root gains records;
- no memory file is created under the sample workspace.

- [ ] **Step 4: Inspect repository state**

```powershell
git status --short
git log --oneline --decorate -12
```

Expected: only intentional final changes are present and the history shows
focused P0–P4 commits.

- [ ] **Step 5: Commit any verification-only correction**

If verification required a correction:

```powershell
git add <exact corrected files>
git commit -m "fix: satisfy MiniCode acceptance checks"
```

If no correction was required, do not create an empty commit.

- [ ] **Step 6: Re-run final evidence commands**

```powershell
python -m compileall -q .
python -m unittest discover -v
git status --short
```

Expected: compilation and tests exit zero; the working tree is clean.
