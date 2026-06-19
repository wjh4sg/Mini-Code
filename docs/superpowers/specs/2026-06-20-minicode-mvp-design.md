# MiniCode MVP v0.1.1 Design

## 1. Objective

Build the complete P0–P4 scope from the provided MiniCode MVP SPEC v0.1.1.

MiniCode is a local Python CLI coding-agent MVP that:

1. accepts a natural-language task;
2. classifies it into one of four supported skills;
3. safely reads relevant project context;
4. builds a compressed prompt;
5. calls a mock or OpenAI-compatible model;
6. formats an explainable result; and
7. stores a task memory record.

The MVP is read-only. It may analyze projects, diagnose errors, plan small
features, and suggest patches, but it must never modify the analyzed workspace,
run shell commands, run tests, or perform Git operations on behalf of the CLI
user.

## 2. Scope

### Included

- Complete P0–P4 implementation from the source SPEC.
- Python 3.10+ CLI.
- Four skills:
  - `explain_project`
  - `fix_error`
  - `small_feature_plan`
  - `patch_suggestion`
- Read-only tools:
  - `list_files`
  - `read_file`
  - `search_code`
- Workspace boundary and sensitive-file protection.
- Prompt construction with fixed-size context compression.
- Deterministic mock model mode.
- OpenAI-compatible `/chat/completions` mode with safe fallback.
- Structured CLI output.
- JSON task-memory persistence.
- Debug output controlled by `MINICODE_DEBUG=1`.
- Demonstration project.
- Automated `unittest` coverage and the four required demo commands.
- README suitable for GitHub and interview demonstration.

### Excluded

- Writing or deleting workspace files.
- Shell execution and test execution by MiniCode.
- Automatic Git operations by MiniCode.
- Web UI, IDE extension, MCP server, multi-agent workflows.
- Vector database, memory retrieval, semantic code search.
- Tree-sitter, repo maps, token accounting, automatic repair loops.
- Typer, Rich, Pydantic, httpx, the OpenAI SDK, or other runtime dependencies.

## 3. Implementation Approach

Use the modular architecture specified by the source document and keep the
runtime dependency-free by relying on the Python standard library.

This approach is preferred over a condensed single-file implementation because
the project is intended to demonstrate agent architecture. It is preferred over
a framework-heavy implementation because external packages would exceed the
MVP boundary and make offline demonstration less reliable.

Automated tests use `unittest`, temporary directories, and injected or patched
HTTP behavior. Tests must not require a real API key or external network access.

## 4. Repository Layout

```text
minicode/
  main.py

  agent/
    __init__.py
    loop.py
    skill_router.py
    context_builder.py
    llm_client.py
    response_formatter.py

  tools/
    __init__.py
    file_tools.py
    search_tools.py
    tool_executor.py

  safety/
    __init__.py
    permission_checker.py

  memory/
    __init__.py
    memory_writer.py

  skills/
    skills.json

  data/
    memory.json

  examples/
    sample_project/
      .env
      README.md
      requirements.txt
      app/
        main.py
        user_router.py
        user_service.py
        user_schema.py
      tests/
        test_user.py

  tests/
    __init__.py
    test_context_builder.py
    test_file_tools.py
    test_llm_client.py
    test_memory_writer.py
    test_permission_checker.py
    test_query_loop.py
    test_search_tools.py
    test_skill_router.py

  README.md
```

The repository root is the MiniCode application root. A user workspace is the
current working directory from which `main.py` is invoked.

## 5. Architecture

### 5.1 Entry Layer

`main.py` joins command-line arguments into one query, computes:

```text
app_root = directory containing main.py
workspace = current working directory
```

It creates `QueryLoop`, runs the task, and prints the final response. Missing
input produces usage guidance without a traceback.

### 5.2 Orchestration Layer

`QueryLoop` owns the task session and coordinates all components. It:

1. creates a task dictionary;
2. routes the query;
3. executes the skill-specific read-only tool strategy;
4. builds model context;
5. obtains a mock or real model response;
6. formats output;
7. saves memory; and
8. returns a string.

Module failures are converted to structured failures. A single tool failure
does not abort the task. A missing `skills.json` is a fatal configuration error
for the task but still produces a readable CLI error.

### 5.3 Routing Layer

`SkillRouter` loads `skills/skills.json` from `app_root`, validates that it is a
list of skill objects, and applies deterministic priority rules.

Routing priority:

1. Explicit sensitive-file requests follow the read/patch path so the permission
   rejection is observable.
2. Explicit patch/diff phrases or a recognized file path select
   `patch_suggestion`.
3. Error terms select `fix_error`.
4. feature terms select `small_feature_plan`.
5. project-analysis terms select `explain_project`.
6. otherwise return an in-memory `unknown` skill.

The word “修改” alone never selects `patch_suggestion`. Therefore “增加修改昵称
接口” selects `small_feature_plan`.

### 5.4 Tool and Safety Layer

`ToolExecutor` is the only tool interface used by `QueryLoop`. It owns the
workspace and one `PermissionChecker`.

`PermissionChecker`:

- resolves candidate paths;
- rejects paths outside the resolved workspace;
- rejects sensitive directories, names, suffixes, and filename keywords;
- handles nonexistent paths without allowing path traversal; and
- returns `(allowed, reason)` instead of raising expected access errors.

`list_files` is metadata-only and performs depth-limited traversal while
skipping ignored directories. It does not read file contents. Its requested
root must still remain within the workspace.

`read_file` checks permission before reading, only accepts approved text
suffixes, rejects files larger than 1 MiB, reads UTF-8 with ignored decoding
errors, and returns at most the requested line limit.

`search_code` checks every candidate file with the same permission checker
before reading. Rejected files are reported separately, oversized files are
skipped, and matching stops at the result limit.

Symlinks are evaluated by their resolved targets. A symlink that resolves
outside the workspace is denied.

### 5.5 Context Layer

`ContextBuilder` turns task, skill, and tool dictionaries into a plain-text
prompt. It includes:

- user task;
- selected skill and description;
- tool summaries;
- file summaries;
- search matches and file snippets;
- requested output sections; and
- explicit non-hallucination/read-only constraints.

Fixed compression limits:

- first 80 listed paths;
- first 10 matches per search result;
- first 80 lines per read result;
- no more than five related files selected by the loop.

### 5.6 Model Layer

`LLMClient` reads:

- `MINICODE_API_KEY`
- `MINICODE_BASE_URL`
- `MINICODE_MODEL`

If the API key or base URL is absent, it returns a deterministic,
skill-specific mock response containing every required output heading.

If real mode is configured, the client uses `urllib.request` to POST JSON to
`{base_url}/chat/completions`. The base URL is normalized to prevent a duplicate
slash before `chat/completions`.

Network, timeout, HTTP, decoding, authentication, and response-shape failures
return a visible failure notice followed by the mock response. No exception
escapes into the CLI for these expected failures.

### 5.7 Output Layer

`ResponseFormatter` always produces:

```text
【任务类型】
【执行过程】
【分析结果】
【风险检查】
【记忆保存】
```

The process section reflects each tool result. The risk section aggregates
permission-denied tool results and `rejected_files`. The memory section states
the application-level memory path.

For an unknown task, no tools are called and the analysis asks the user to
clarify which supported task they intend.

### 5.8 Memory Layer

`MemoryWriter` stores an array in `app_root/data/memory.json`.

It:

- creates the parent directory if necessary;
- treats a missing, malformed, or non-array JSON file as an empty array;
- extracts successful read paths and search-match paths;
- excludes rejected files;
- deduplicates while preserving order;
- stores at most 20 related paths;
- generates a deterministic experience sentence per skill; and
- writes UTF-8 JSON with readable indentation.

A memory-write failure is appended as a warning to the final response and does
not replace the analysis result.

## 6. Skill Tool Strategies

### `explain_project`

- List the workspace to depth two.
- Read present project descriptors in the SPEC-defined order.
- Build an overview of purpose, stack, structure, startup, and reading order.

### `fix_error`

- Extract useful error tokens.
- Search the first three tokens.
- Read present dependency manifests.
- Describe the error class, likely causes, related files, and repair guidance.

### `small_feature_plan`

- Extract query fragments.
- Expand known Chinese domain terms into code keywords.
- Search the first six unique keywords.
- Rank matching paths by router/controller, service, schema/model, then test.
- Read at most five unique related files.

### `patch_suggestion`

- Extract an explicit supported file path and read it.
- If no path is present, search extracted keywords and read selected context.
- Return a proposed diff or patch as text only.

### Sensitive-file demonstration

When the query explicitly names a sensitive target, the loop deliberately sends
that target to `read_file`. The permission checker denies it, and the formatter
shows the refusal. This is not a bypass; it is an observable safety test.

## 7. Error Handling

Expected user and environmental errors become structured output:

- unknown query: guidance, no tools;
- missing file: failed tool result;
- unsupported or oversized file: failed tool result;
- sensitive or out-of-workspace path: denied tool result;
- malformed skills configuration: readable task failure;
- malformed model response or HTTP failure: mock fallback;
- malformed memory JSON: reinitialize as an empty list;
- memory write failure: warning while preserving the main result;
- decoding issues: ignored for workspace text reads and handled for HTTP JSON.

Unexpected orchestration exceptions set task status to `failed`, format a clear
error response, and attempt memory persistence without masking the original
failure.

## 8. Debug Behavior

With `MINICODE_DEBUG=1`, diagnostics are written to standard error so the normal
formatted answer remains usable on standard output.

Debug output includes:

- application root;
- workspace;
- selected skill and routing reason;
- compact tool-result summaries;
- first 1000 prompt characters; and
- memory path.

Secrets and full environment-variable values are never printed.

## 9. Testing Strategy

Use `python -m unittest discover -v`.

Automated tests cover:

- all routing priorities and the nickname regression;
- workspace boundary checks, absolute paths, traversal, symlinks, and every
  required sensitive pattern;
- file listing depth, ignores, limits, missing paths, and boundary enforcement;
- file reads, suffix validation, truncation, size rejection, and decoding;
- case-insensitive search, result limits, rejected-file reporting, and ignored
  directories;
- context headings and compression limits;
- mock output for all skills;
- real-model request shape through a mocked opener;
- malformed/failed model calls and fallback;
- memory extraction, deduplication, corruption recovery, and write failure;
- query-loop output sections, tool strategies, memory saving, unknown handling,
  and sensitive-file demonstration;
- running from `examples/sample_project` while loading skills and memory from
  `app_root`.

Final verification also runs the four commands from the SPEC inside
`examples/sample_project` and checks that all required output sections appear.

The example project’s own test file is intentionally simple and is included as
workspace content for MiniCode analysis. The MiniCode test suite does not
require FastAPI to be installed.

## 10. Delivery Sequence

### P0

Create repository structure, entry point, README skeleton, and explicit
`app_root`/`workspace` handling.

### P1

Implement skills configuration, router, task session, and orchestration shell.

### P2

Implement permission checking and all read-only tools.

### P3

Implement context building, mock/real model client, formatting, persistence, and
the complete loop.

### P4

Add demonstration project, complete README, automated tests, and execute the
manual demo matrix.

Implementation follows test-driven development: each behavior is introduced by
a failing focused test, followed by the minimum implementation and regression
verification.

## 11. Acceptance

Delivery is complete only when:

- `python -m unittest discover -v` passes;
- all four demo commands run without tracebacks;
- the nickname query routes to `small_feature_plan`;
- sensitive files and workspace escapes are denied;
- search never reads denied files;
- mock mode works without credentials;
- configured model failures fall back safely;
- every final response contains the five required sections;
- memory is written under `app_root/data`, even when invoked from the sample
  workspace; and
- the implementation performs no workspace writes.
