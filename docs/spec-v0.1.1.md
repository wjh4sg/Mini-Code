# MiniCode MVP SPEC v0.1.1

## 0. 文档信息

| 项目     | 内容                           |
| ------ | ---------------------------- |
| 项目名称   | MiniCode                     |
| 版本     | MVP v0.1.1                   |
| 项目类型   | 本地 CLI Coding Agent MVP      |
| 主要语言   | Python 3.10+                 |
| 目标用户   | 开发者、学生、面试项目展示                |
| 核心目标   | 跑通一个受控的本地 Coding Agent 执行闭环  |
| 第一版边界  | 只分析、只建议、不自动修改代码              |
| 本版重点修正 | 路径边界、安全审查、路由误判、错误处理、Demo 稳定性 |

---

# 1. 项目定位

MiniCode 是一个面向本地代码项目的小任务 AI Coding Agent MVP。

它不是完整复刻 Claude Code、OpenHands、Aider、Cline 或 OpenCode，而是参考这些 Coding Agent 的核心思想，做一个最小可运行版本。

MiniCode v0.1.1 重点验证下面这条链路：

```text
用户输入任务
→ 创建任务会话
→ 识别任务类型
→ 根据任务类型调用工具
→ 读取项目上下文
→ 进行权限审查
→ 构建压缩上下文
→ 调用 Mock / 真实模型
→ 格式化输出
→ 保存任务记忆
```

第一版的核心价值不是自动写代码，而是实现一个**受控、可解释、能演示的 Agent 执行框架**。

---

# 2. 项目背景

普通大模型代码问答有几个问题：

```text
1. 用户需要手动复制代码、报错和文件结构
2. 模型不知道真实项目上下文
3. 模型容易编造不存在的文件和函数
4. 用户不知道应该提供哪些文件
5. 模型不能主动搜索项目
6. 如果直接给 Agent 文件权限，又可能误读敏感文件
7. 普通问答不会沉淀任务经验
```

MiniCode 要解决的是：

```text
1. 让 Agent 主动读取本地项目上下文
2. 根据不同任务调用不同工具
3. 在工具调用前做权限审查
4. 把工具结果压缩成模型可用的 Prompt
5. 输出结构化、可追踪的分析结果
6. 保存任务执行记录，为后续记忆系统做准备
```

---

# 3. 第一版目标

MiniCode v0.1.1 需要完成 4 类任务。

| 任务类型     | Skill 名称           | 说明              | 第一版目标                            |
| -------- | ------------------ | --------------- | -------------------------------- |
| 项目分析     | explain_project    | 分析项目结构、技术栈、启动方式 | 能读取 README、依赖文件和目录结构，输出项目概览      |
| 报错分析     | fix_error          | 根据报错信息搜索相关文件    | 能根据报错关键词搜索代码和依赖文件，输出排查建议         |
| 小功能计划    | small_feature_plan | 根据需求生成实现计划      | 能搜索相关模块，输出涉及文件、实现步骤和风险点          |
| Patch 建议 | patch_suggestion   | 针对目标文件给出修改建议    | 能读取目标文件，输出 diff / patch 建议，不写入文件 |

---

# 4. 第一版非目标

第一版明确不做：

```text
1. 不自动修改文件
2. 不自动执行 shell 命令
3. 不自动运行测试
4. 不自动 git commit / push
5. 不做 Web UI
6. 不做 IDE 插件
7. 不做 MCP Server
8. 不做多 Agent 协作
9. 不接向量数据库
10. 不做长期记忆召回
11. 不做复杂代码语义分析
12. 不做 Tree-sitter 结构解析
13. 不做真实 repo map
14. 不做自动修复闭环
```

这些能力放入第二版或后续版本。

---

# 5. 技术栈

第一版优先使用 Python 标准库，降低实现成本和调试成本。

| 模块       | 第一版选择                        | 原因              |
| -------- | ---------------------------- | --------------- |
| 语言       | Python 3.10+                 | 开发快，文件操作方便      |
| 入口       | CLI                          | 最容易实现，适合面试展示    |
| 配置       | JSON                         | 简单直观            |
| Skill 配置 | skills/skills.json           | 可读、可改、可展示       |
| 任务状态     | dict                         | 第一版实现快          |
| 工具结果     | dict                         | 第一版简单灵活         |
| 文件扫描     | pathlib                      | 标准库即可           |
| 权限匹配     | pathlib + fnmatch            | 标准库即可           |
| 模型调用     | Mock + OpenAI-compatible API | 有无 API Key 都能演示 |
| HTTP 请求  | urllib.request               | 第一版不额外依赖        |
| 记忆存储     | data/memory.json             | 直观可查看           |
| 输出       | 纯文本                          | CLI 友好          |

第二版可以升级为：

```text
argparse / Typer
Rich
Pydantic
httpx
openai SDK
tenacity
SQLite
ripgrep
Tree-sitter
```

---

# 6. 路径模型：app_root 与 workspace

## 6.1 设计原因

MiniCode 有两个不同路径概念，必须分开：

```text
app_root：MiniCode 自己的源码根目录
workspace：用户要分析的目标项目目录
```

如果不区分，用户在 `examples/sample_project` 中运行：

```bash
cd examples/sample_project
python ../../main.py "帮我分析这个项目"
```

此时：

```text
workspace = examples/sample_project
app_root = MiniCode 项目根目录
```

如果混用路径，就会出现：

```text
skills/skills.json 找不到
data/memory.json 写到目标项目里
```

因此 v0.1.1 明确区分 `app_root` 和 `workspace`。

---

## 6.2 app_root

### 定义

```text
app_root = Path(__file__).resolve().parent
```

如果 `main.py` 位于 MiniCode 根目录，则 `app_root` 就是 MiniCode 项目根路径。

### 用途

```text
1. 读取 skills/skills.json
2. 读写 data/memory.json
3. 定位 MiniCode 自身配置
4. 定位 examples/sample_project
```

---

## 6.3 workspace

### 定义

```text
workspace = Path.cwd().resolve()
```

### 用途

```text
1. list_files 扫描目标项目
2. read_file 读取目标项目文件
3. search_code 搜索目标项目代码
4. PermissionChecker 限制目标项目边界
```

---

## 6.4 路径使用规则

| 模块                | 使用路径                            |
| ----------------- | ------------------------------- |
| SkillRouter       | app_root / "skills/skills.json" |
| MemoryWriter      | app_root / "data/memory.json"   |
| ToolExecutor      | workspace                       |
| PermissionChecker | workspace                       |
| list_files        | workspace                       |
| read_file         | workspace                       |
| search_code       | workspace                       |

---

## 6.5 第一版限制

v0.1.1 默认：

```text
用户必须在目标项目根目录执行命令。
```

不做项目根目录自动识别。

第二版再实现：

```text
向上查找 .git、package.json、pyproject.toml、requirements.txt、pom.xml、go.mod 等项目根标志文件。
```

---

# 7. 项目目录结构

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
      README.md
      requirements.txt
      app/
        main.py
        user_router.py
        user_service.py
        user_schema.py
      tests/
        test_user.py

  README.md
```

---

# 8. 总体架构

MiniCode v0.1.1 分为 5 层：

```text
入口层
- User Query
- main.py
- Task Session

调度层
- QueryLoop
- SkillRouter
- skills.json

执行层
- ToolExecutor
- list_files
- read_file
- search_code
- PermissionChecker

模型层
- ContextBuilder
- Prompt
- LLMClient
- Mock / Real LLM

输出层
- ResponseFormatter
- Final Answer
- MemoryWriter
```

---

# 9. 核心执行流程

用户执行：

```bash
python main.py "帮我给用户模块增加修改昵称接口"
```

系统内部流程：

```text
1. main.py 接收用户输入
2. 计算 app_root
3. 计算 workspace
4. 创建 Task Session
5. QueryLoop 开始执行任务
6. SkillRouter 读取 app_root/skills/skills.json
7. SkillRouter 判断任务类型
8. 识别为 small_feature_plan
9. QueryLoop 根据 Skill 选择工具策略
10. 提取关键词：用户、昵称、接口
11. 扩展代码关键词：user、profile、nickname、router、api
12. ToolExecutor 调用 search_code
13. search_code 搜索前对每个候选文件经过 PermissionChecker
14. 根据搜索结果选择相关文件
15. ToolExecutor 调用 read_file
16. read_file 前经过 PermissionChecker
17. ContextBuilder 整理工具结果，生成 Prompt
18. LLMClient 调用 Mock 或真实模型
19. 如果真实模型失败，降级为 Mock 或返回模型错误提示
20. ResponseFormatter 统一格式化输出
21. MemoryWriter 保存任务记录到 app_root/data/memory.json
22. CLI 输出最终结果
```

---

# 10. 核心数据结构

## 10.1 Task Session

第一版使用 dict。

字段：

| 字段             | 类型         | 说明                                |
| -------------- | ---------- | --------------------------------- |
| task_id        | string     | 任务 ID                             |
| user_query     | string     | 用户输入                              |
| app_root       | string     | MiniCode 源码根目录                    |
| workspace      | string     | 当前目标项目路径                          |
| selected_skill | string     | 识别出的 Skill                        |
| tool_results   | list[dict] | 工具执行结果                            |
| context        | string     | 构建后的 Prompt                       |
| llm_response   | string     | 模型返回结果                            |
| final_answer   | string     | 格式化后的最终输出                         |
| status         | string     | created / running / done / failed |
| created_at     | string     | 创建时间                              |

示例：

```json
{
  "task_id": "task_001",
  "user_query": "帮我给用户模块增加修改昵称接口",
  "app_root": "/path/to/minicode",
  "workspace": "/path/to/project",
  "selected_skill": "small_feature_plan",
  "tool_results": [],
  "context": "",
  "llm_response": "",
  "final_answer": "",
  "status": "created",
  "created_at": "2026-06-20 12:00:00"
}
```

---

## 10.2 Skill Config

Skill 配置存在 `skills/skills.json`。

字段：

| 字段            | 类型           | 说明       |
| ------------- | ------------ | -------- |
| name          | string       | Skill 名称 |
| description   | string       | Skill 说明 |
| keywords      | list[string] | 路由关键词    |
| tools         | list[string] | 默认使用工具   |
| output_schema | list[string] | 输出结构要求   |

示例：

```json
{
  "name": "small_feature_plan",
  "description": "生成小功能实现计划",
  "keywords": ["新增", "增加", "接口", "功能", "页面"],
  "tools": ["search_code", "read_file"],
  "output_schema": ["任务理解", "可能涉及文件", "实现步骤", "测试建议", "风险点"]
}
```

---

## 10.3 Tool Result

第一版每个工具返回 dict。

通用字段：

| 字段             | 类型     | 说明                      |
| -------------- | ------ | ----------------------- |
| tool           | string | 工具名                     |
| success        | bool   | 是否成功                    |
| summary        | string | 简短摘要                    |
| reason         | string | 失败原因                    |
| path           | string | 文件路径，部分工具有              |
| result         | any    | 结果数据，部分工具有              |
| content        | string | 文件内容，read_file 有        |
| matches        | list   | 搜索结果，search_code 有      |
| rejected_files | list   | 被权限拒绝的文件，search_code 可选 |

示例：

```json
{
  "tool": "search_code",
  "success": true,
  "keyword": "user",
  "matches": [
    {
      "path": "app/user_service.py",
      "line": 1,
      "text": "class UserService:"
    }
  ],
  "rejected_files": [],
  "summary": "搜索关键词 user，找到 1 条结果"
}
```

---

## 10.4 Search Match

```json
{
  "path": "app/user_service.py",
  "line": 12,
  "text": "class UserService:"
}
```

---

## 10.5 Memory Item

任务完成后保存到 `app_root/data/memory.json`。

字段：

| 字段            | 类型           | 说明       |
| ------------- | ------------ | -------- |
| task_id       | string       | 任务 ID    |
| task_type     | string       | Skill 名称 |
| query         | string       | 用户原始任务   |
| workspace     | string       | 目标项目路径   |
| related_files | list[string] | 相关文件     |
| experience    | string       | 经验总结     |
| success       | bool         | 是否执行成功   |
| created_at    | string       | 创建时间     |

示例：

```json
{
  "task_id": "task_001",
  "task_type": "small_feature_plan",
  "query": "帮我给用户模块增加修改昵称接口",
  "workspace": "/path/to/project",
  "related_files": [
    "app/user_router.py",
    "app/user_service.py",
    "app/user_schema.py"
  ],
  "experience": "小功能计划任务通常需要定位 router、service、schema 和 test 文件。",
  "success": true,
  "created_at": "2026-06-20 12:00:00"
}
```

---

# 11. main.py SPEC

## 11.1 功能

CLI 入口。

负责：

```text
1. 接收用户输入
2. 计算 app_root
3. 获取当前 workspace
4. 创建 QueryLoop
5. 执行任务
6. 输出结果
```

---

## 11.2 输入

命令行参数：

```bash
python main.py "帮我分析这个项目"
```

---

## 11.3 输出

标准输出文本。

---

## 11.4 使用库

```text
sys
pathlib
```

---

## 11.5 第一版逻辑

```text
如果没有输入任务：
  输出使用说明
否则：
  user_query = 命令行参数拼接
  app_root = Path(__file__).resolve().parent
  workspace = Path.cwd().resolve()
  loop = QueryLoop(app_root, workspace)
  result = loop.run(user_query)
  print(result)
```

---

## 11.6 验收

命令：

```bash
python main.py "hello"
```

程序不崩溃，能正常返回结果或 unknown 任务提示。

---

# 12. QueryLoop SPEC

## 12.1 功能

QueryLoop 是 MiniCode 的任务总调度器。

它负责把下面模块串起来：

```text
SkillRouter
ToolExecutor
ContextBuilder
LLMClient
ResponseFormatter
MemoryWriter
```

---

## 12.2 输入

```text
app_root: Path
workspace: Path
user_query: string
```

---

## 12.3 输出

```text
final_answer: string
```

---

## 12.4 执行流程

```text
1. 创建 Task Session
2. task.status = running
3. 调用 SkillRouter.route(user_query)
4. 保存 selected_skill
5. 根据 Skill 调用对应工具策略
6. 获得 tool_results
7. 调用 ContextBuilder.build(task, skill, tool_results)
8. 调用 LLMClient.chat(context, skill)
9. 保存 llm_response
10. 设置 task.status = done
11. 调用 ResponseFormatter.format(task)
12. 调用 MemoryWriter.save(task)
13. 返回 final_answer
```

---

## 12.5 异常处理

QueryLoop 不应该因为单个模块失败直接崩溃。

第一版要求：

```text
1. SkillRouter 失败 → 返回 unknown 或错误提示
2. 工具调用失败 → 保存 success=false 的 Tool Result，继续执行
3. ContextBuilder 失败 → 返回错误说明
4. LLMClient 失败 → 降级 Mock 或返回模型错误提示
5. MemoryWriter 失败 → 输出提示，但不影响 final_answer
```

---

## 12.6 Skill 到工具策略

QueryLoop 内部需要实现：

```text
_run_tools_by_skill(skill, user_query)
_run_explain_project_tools()
_run_fix_error_tools(user_query)
_run_small_feature_plan_tools(user_query)
_run_patch_suggestion_tools(user_query)
_extract_keywords(text)
_expand_feature_keywords(text)
_collect_related_files_from_search(results)
_extract_file_paths(text)
_detect_sensitive_file_request(text)
```

---

# 13. SkillRouter SPEC

## 13.1 功能

将用户自然语言任务路由到一个 Skill。

---

## 13.2 输入

```text
query: string
```

---

## 13.3 输出

```text
skill: dict
```

---

## 13.4 第一版算法

使用：

```text
规则匹配 + 优先级
```

优先级：

```text
1. 明确敏感文件访问请求 → file_access / patch_suggestion 读取流程，由 PermissionChecker 拒绝
2. patch / diff / 明确文件路径 / 改这个文件 / 修这个函数 → patch_suggestion
3. error / exception / failed / traceback / 报错 / 错误 → fix_error
4. 新增 / 增加 / 添加 / 接口 / 功能 / 页面 / 分页 → small_feature_plan
5. 分析 / 项目 / 结构 / 目录 / 启动 / 技术栈 → explain_project
6. 否则 unknown
```

---

## 13.5 Patch 路由修正规则

为了避免误判，第一版不允许仅因为出现“修改”二字就命中 patch_suggestion。

### patch_suggestion 触发条件

必须满足以下任意一项：

```text
1. 包含 patch
2. 包含 diff
3. 包含明确文件路径，例如 src/config.py
4. 包含“改这个文件”
5. 包含“修这个函数”
6. 包含“给出 patch”
```

### 不应该触发 patch_suggestion 的例子

```text
帮我给用户模块增加修改昵称接口
```

该任务应命中：

```text
small_feature_plan
```

---

## 13.6 文件路径识别

判断用户输入中是否包含常见文件后缀：

```text
.py
.js
.ts
.java
.go
.md
.json
.yaml
.yml
```

如果包含，则优先认为是 patch_suggestion。

---

## 13.7 失败情况

如果无法识别，返回：

```json
{
  "name": "unknown",
  "description": "无法识别任务类型",
  "keywords": [],
  "tools": [],
  "output_schema": [],
  "reason": "未命中任何 Skill"
}
```

---

# 14. skills.json SPEC

路径：

```text
app_root/skills/skills.json
```

内容：

```json
[
  {
    "name": "explain_project",
    "description": "分析项目结构、技术栈和启动方式",
    "keywords": ["分析", "项目", "结构", "目录", "启动", "技术栈", "看一下"],
    "tools": ["list_files", "read_file"],
    "output_schema": ["项目用途", "技术栈", "目录结构", "启动方式", "建议阅读顺序"]
  },
  {
    "name": "fix_error",
    "description": "分析运行、构建或测试报错",
    "keywords": ["报错", "错误", "error", "exception", "failed", "traceback", "失败", "ModuleNotFoundError"],
    "tools": ["search_code", "read_file", "list_files"],
    "output_schema": ["错误类型", "可能原因", "相关文件", "修复建议"]
  },
  {
    "name": "small_feature_plan",
    "description": "生成小功能实现计划",
    "keywords": ["新增", "增加", "添加", "接口", "功能", "页面", "分页", "搜索", "模块"],
    "tools": ["search_code", "read_file"],
    "output_schema": ["任务理解", "可能涉及文件", "实现步骤", "测试建议", "风险点"]
  },
  {
    "name": "patch_suggestion",
    "description": "针对指定文件生成局部 Patch 建议",
    "keywords": ["patch", "diff", "改这个文件", "修这个函数", "改成", "给出 patch"],
    "tools": ["read_file", "search_code"],
    "output_schema": ["修改原因", "Patch 建议", "影响范围", "注意事项"]
  }
]
```

---

# 15. ToolExecutor SPEC

## 15.1 功能

ToolExecutor 是工具门面层，统一封装底层工具。

QueryLoop 不直接调用 `file_tools.py` 或 `search_tools.py`，而是调用 ToolExecutor。

---

## 15.2 持有状态

```text
workspace: Path
permission_checker: PermissionChecker
```

---

## 15.3 方法

```text
list_files(path=".")
read_file(path)
search_code(keyword)
```

---

## 15.4 作用

```text
1. 隔离上层调度和底层工具实现
2. 后续方便增加 run_tests、git_diff、apply_patch
3. 工具调用入口统一
4. 所有读取文件内容的工具都必须接入 PermissionChecker
```

---

# 16. list_files SPEC

## 16.1 功能

扫描项目目录，返回相对路径列表。

---

## 16.2 输入

| 参数        | 类型     | 默认值 | 说明      |
| --------- | ------ | --- | ------- |
| workspace | Path   | 必填  | 目标项目根目录 |
| path      | string | "." | 扫描路径    |
| max_depth | int    | 2   | 最大递归深度  |
| max_items | int    | 200 | 最大返回数量  |

---

## 16.3 输出

成功：

```json
{
  "tool": "list_files",
  "success": true,
  "path": ".",
  "result": [
    "README.md",
    "requirements.txt",
    "app/",
    "app/main.py"
  ],
  "summary": "扫描到 20 个文件或目录"
}
```

失败：

```json
{
  "tool": "list_files",
  "success": false,
  "path": ".",
  "reason": "路径不存在"
}
```

---

## 16.4 算法

使用受限深度 DFS。

```text
1. root = workspace / path
2. 判断 root 是否存在
3. 遍历当前目录
4. 跳过忽略目录
5. 记录相对路径
6. 如果是目录，且 depth 未超过 max_depth，继续递归
7. 如果结果数量达到 max_items，停止
```

---

## 16.5 忽略目录

```text
.git
node_modules
__pycache__
dist
build
.venv
venv
.idea
.vscode
```

---

# 17. read_file SPEC

## 17.1 功能

读取项目中的文本文件。

---

## 17.2 输入

| 参数                 | 类型                | 默认值     | 说明            |
| ------------------ | ----------------- | ------- | ------------- |
| workspace          | Path              | 必填      | 目标项目根目录       |
| path               | string            | 必填      | 文件路径          |
| permission_checker | PermissionChecker | 必填      | 权限检查器         |
| max_lines          | int               | 200     | 最大读取行数        |
| max_file_size      | int               | 1048576 | 最大文件大小，默认 1MB |

---

## 17.3 输出

成功：

```json
{
  "tool": "read_file",
  "success": true,
  "path": "README.md",
  "content": "...",
  "line_count": 80,
  "truncated": false,
  "summary": "读取 README.md 成功，共 80 行"
}
```

权限拒绝：

```json
{
  "tool": "read_file",
  "success": false,
  "path": ".env",
  "reason": "禁止读取敏感文件：.env"
}
```

普通失败：

```json
{
  "tool": "read_file",
  "success": false,
  "path": "abc.txt",
  "reason": "文件不存在"
}
```

文件过大：

```json
{
  "tool": "read_file",
  "success": false,
  "path": "large.log",
  "reason": "文件过大，超过 1MB，跳过读取"
}
```

---

## 17.4 算法

```text
1. target = Path(path)
2. 调用 PermissionChecker.check_path(target)
3. 如果不允许，返回失败
4. resolve 出真实路径
5. 判断文件是否存在
6. 判断是否为文件
7. 判断后缀是否在文本白名单
8. 判断文件大小是否超过 max_file_size
9. 使用 UTF-8 读取，errors="ignore"
10. 只保留前 max_lines 行
11. 返回结构化结果
```

---

## 17.5 文本后缀白名单

```text
.py
.js
.ts
.tsx
.jsx
.json
.md
.txt
.yaml
.yml
.toml
.ini
.cfg
.java
.go
.html
.css
.scss
.vue
```

---

# 18. search_code SPEC

## 18.1 功能

根据关键词搜索项目中的代码行。

---

## 18.2 输入

| 参数                 | 类型                | 默认值     | 说明        |
| ------------------ | ----------------- | ------- | --------- |
| workspace          | Path              | 必填      | 目标项目根目录   |
| keyword            | string            | 必填      | 搜索关键词     |
| permission_checker | PermissionChecker | 必填      | 权限检查器     |
| max_results        | int               | 20      | 最大结果数     |
| max_file_size      | int               | 1048576 | 单文件最大读取大小 |

---

## 18.3 输出

```json
{
  "tool": "search_code",
  "success": true,
  "keyword": "user",
  "matches": [
    {
      "path": "app/user_service.py",
      "line": 1,
      "text": "class UserService:"
    }
  ],
  "rejected_files": [
    {
      "path": ".env",
      "reason": "禁止读取敏感文件：.env"
    }
  ],
  "summary": "搜索关键词 user，找到 1 条结果，跳过 1 个敏感文件"
}
```

---

## 18.4 算法

第一版使用线性扫描 + 子串匹配。

```text
1. 遍历 workspace 下所有文本代码文件
2. 跳过忽略目录
3. 对每个候选文件调用 PermissionChecker.check_path
4. 如果权限拒绝，加入 rejected_files，跳过
5. 判断文件大小是否超过 max_file_size，超过则跳过
6. 读取文件内容
7. 逐行判断 keyword.lower() in line.lower()
8. 命中则保存 path、line、text
9. 达到 max_results 后停止
```

---

## 18.5 搜索文件后缀

```text
.py
.js
.ts
.tsx
.jsx
.java
.go
.md
.json
.yaml
.yml
.toml
.html
.css
.vue
```

---

## 18.6 第一版限制

```text
1. 不支持正则
2. 不支持语义搜索
3. 不支持模糊匹配
4. 不支持函数级定位
5. 不支持 BM25
```

---

# 19. PermissionChecker SPEC

## 19.1 功能

防止 Agent 读取敏感文件和项目目录外文件。

---

## 19.2 输入

```text
path: Path
```

---

## 19.3 输出

```text
allowed: bool
reason: string
```

示例：

```text
(True, "allowed")
(False, "禁止读取敏感文件：.env")
```

---

## 19.4 算法

使用：

```text
路径规范化 + 项目边界检查 + 黑名单匹配
```

流程：

```text
1. 将 path resolve 成真实绝对路径
2. 检查真实路径是否在 workspace 内
3. 检查路径中是否包含敏感目录
4. 检查文件名是否命中敏感文件名
5. 检查文件名是否命中敏感后缀模式
6. 检查文件名是否包含敏感关键词
7. 返回 allowed / denied
```

---

## 19.5 敏感文件名

```text
.env
.env.local
.env.production
id_rsa
id_dsa
credentials
credential
token
secret
```

---

## 19.6 敏感目录

```text
.ssh
.gnupg
```

---

## 19.7 敏感后缀

```text
*.pem
*.key
*.crt
*.p12
```

---

## 19.8 敏感关键词

如果文件名中包含以下词，也拒绝：

```text
token
secret
password
passwd
credential
credentials
private
api_key
access_key
```

---

## 19.9 必须拦截

```text
.env
../.env
../../.ssh/id_rsa
/home/user/.ssh/id_rsa
private.key
config.secret.json
aws_credentials
database_password.txt
```

---

## 19.10 安全策略原则

第一版采用保守策略：

```text
宁可误拒绝可疑文件，也不放行潜在敏感文件。
```

---

# 20. 关键词提取与扩展 SPEC

## 20.1 功能

从用户输入中提取适合搜索代码的关键词。

---

## 20.2 第一版策略

```text
字符串切分 + 中文关键词映射
```

---

## 20.3 基础提取

将用户输入按空格、逗号、冒号进行切分。

保留长度大于等于 2 的片段。

---

## 20.4 中文关键词映射

| 中文词 | 英文代码关键词                                |
| --- | -------------------------------------- |
| 用户  | user, account, profile                 |
| 昵称  | nickname, display_name, username, name |
| 接口  | router, controller, api, route         |
| 登录  | login, auth, token                     |
| 分页  | page, pagination, limit, offset        |
| 搜索  | search, query, keyword                 |

---

## 20.5 示例

输入：

```text
帮我给用户模块增加修改昵称接口
```

输出关键词：

```text
user
account
profile
nickname
display_name
username
name
router
controller
api
route
```

---

## 20.6 限制

第一版最多使用前 6 个关键词搜索。

---

# 21. 相关文件选择 SPEC

## 21.1 功能

从 search_code 的结果中选择最相关的文件进行 read_file。

---

## 21.2 输入

```text
search_results: list[dict]
```

---

## 21.3 输出

```text
related_files: list[string]
```

---

## 21.4 第一版排序规则

根据路径关键词排序。

优先级：

```text
router / controller
service
schema / model
test
```

---

## 21.5 规则

```text
路径中包含 router 或 controller → 高优先级
路径中包含 service → 高优先级
路径中包含 schema 或 model → 中高优先级
路径中包含 test → 中优先级
```

---

## 21.6 限制

最多读取前 5 个相关文件。

---

# 22. Skill 工具策略 SPEC

## 22.1 explain_project

用户示例：

```text
帮我分析这个项目
```

工具策略：

```text
1. list_files(".")
2. 如果存在 README.md，read_file("README.md")
3. 如果存在 readme.md，read_file("readme.md")
4. 如果存在 package.json，read_file("package.json")
5. 如果存在 requirements.txt，read_file("requirements.txt")
6. 如果存在 pyproject.toml，read_file("pyproject.toml")
7. 如果存在 pom.xml，read_file("pom.xml")
8. 如果存在 go.mod，read_file("go.mod")
```

输出目标：

```text
项目用途
技术栈
目录结构
启动方式
建议阅读顺序
```

---

## 22.2 fix_error

用户示例：

```text
运行时报错 ModuleNotFoundError: No module named 'fastapi'，帮我分析
```

工具策略：

```text
1. 从报错文本中提取关键词
2. 对前 3 个关键词执行 search_code
3. 读取依赖文件：
   - requirements.txt
   - pyproject.toml
   - package.json
   - pom.xml
   - go.mod
```

输出目标：

```text
错误类型
可能原因
相关文件
修复建议
```

---

## 22.3 small_feature_plan

用户示例：

```text
帮我给用户模块增加修改昵称接口
```

工具策略：

```text
1. 从需求中提取关键词
2. 通过关键词映射扩展英文代码词
3. 对前 6 个关键词执行 search_code
4. 从搜索结果中收集相关文件
5. 优先读取 router、controller、service、schema、model、test 相关文件
6. 最多读取 5 个文件
```

输出目标：

```text
任务理解
可能涉及文件
实现步骤
测试建议
风险点
```

---

## 22.4 patch_suggestion

用户示例：

```text
帮我修改 src/config.py，让默认端口改成 8080，给出 patch
```

工具策略：

```text
1. 如果用户输入中包含文件路径，read_file(path)
2. 如果没有明确文件路径，提取关键词并 search_code
3. 输出 Patch 建议
4. 不自动写入文件
```

输出目标：

```text
修改原因
Patch 建议
影响范围
注意事项
```

---

## 22.5 权限演示特殊策略

为保证权限演示稳定，第一版可以做一个特殊处理。

如果用户输入中包含以下敏感文件或敏感关键词：

```text
.env
id_rsa
.pem
.key
credentials
token
secret
password
api_key
access_key
```

则尝试触发 `read_file`，由 PermissionChecker 拒绝，并在风险检查中展示。

示例：

```bash
python main.py "读取 .env 看看"
```

预期：

```text
read_file(".env") failed: 禁止读取敏感文件：.env
```

---

# 23. ContextBuilder SPEC

## 23.1 功能

将工具结果转成模型 Prompt。

---

## 23.2 输入

```text
task: dict
skill: dict
tool_results: list[dict]
```

---

## 23.3 输出

```text
prompt: string
```

---

## 23.4 Prompt 结构

```text
你是 MiniCode，一个本地代码项目分析助手。

用户任务：
{user_query}

当前 Skill：
{skill_name}

Skill 说明：
{skill_description}

已调用工具：
{tool_summary}

项目上下文：
{file_summaries}

相关代码片段：
{code_snippets}

输出要求：
{output_schema}

回答约束：
1. 只能基于提供的项目上下文回答。
2. 不要编造不存在的文件、函数、接口。
3. 如果上下文不足，需要明确说明。
4. 如果涉及修改，只给计划或 Patch 建议，不直接修改文件。
5. 输出要清晰分段。
```

---

## 23.5 工具摘要格式

```text
- list_files success: 扫描到 20 个文件或目录
- read_file success: 读取 README.md 成功，共 30 行
- search_code success: 搜索关键词 user，找到 4 条结果
- search_code skipped: 跳过 1 个敏感文件
```

---

## 23.6 文件摘要格式

```text
- README.md：共 30 行，truncated=false
- requirements.txt：共 3 行，truncated=false
- app/user_router.py：共 20 行，truncated=false
```

---

## 23.7 代码片段格式

```text
关键词 user 的搜索结果：
- app/user_router.py:4  router = APIRouter(prefix="/user")
- app/user_service.py:1  class UserService:
```

读取文件片段：

```text
文件：app/user_router.py
[代码片段]
from fastapi import APIRouter
...
```

---

## 23.8 压缩规则

第一版使用固定截断：

```text
list_files 结果最多保留前 80 个
search_code 每个关键词最多保留前 10 条
read_file 每个文件最多保留前 80 行
最多读取 5 个相关文件
```

第一版不做 token 计算。

---

# 24. LLMClient SPEC

## 24.1 功能

封装模型调用。

---

## 24.2 输入

```text
prompt: string
skill: string
```

---

## 24.3 输出

```text
llm_response: string
```

---

## 24.4 模式

第一版支持两种模式：

```text
Mock 模式
真实模型模式
```

---

## 24.5 Mock 模式

如果没有配置 API Key 或 Base URL，返回固定示例结果。

用途：

```text
1. 没有 API Key 也能跑 Demo
2. 网络失败也能演示主流程
3. 降低开发调试成本
4. 保证面试展示稳定
```

---

## 24.6 真实模型模式

使用 OpenAI-compatible API。

环境变量：

```text
MINICODE_API_KEY
MINICODE_BASE_URL
MINICODE_MODEL
```

请求路径：

```text
{MINICODE_BASE_URL}/chat/completions
```

请求结构：

```json
{
  "model": "gpt-4o-mini",
  "messages": [
    {
      "role": "system",
      "content": "你是一个谨慎的本地代码项目分析助手。"
    },
    {
      "role": "user",
      "content": "{prompt}"
    }
  ],
  "temperature": 0.2
}
```

第一版使用库：

```text
os
json
urllib.request
```

---

## 24.7 失败降级策略

真实模型调用时，如果发生：

```text
网络失败
超时
API Key 错误
API 返回非 200
响应结构异常
```

则不能让程序崩溃。

第一版处理方式：

```text
1. 捕获异常
2. 在 llm_response 中说明模型调用失败原因
3. 降级返回 Mock 结果，或提示用户检查配置
4. QueryLoop 继续执行 ResponseFormatter 和 MemoryWriter
```

示例输出：

```text
【模型调用失败】
原因：请求超时。
已降级为 Mock 模式返回示例分析结果。
```

---

# 25. ResponseFormatter SPEC

## 25.1 功能

统一格式化最终输出。

---

## 25.2 输入

```text
task: dict
```

---

## 25.3 输出

```text
final_answer: string
```

---

## 25.4 输出模板

```text
【任务类型】
{selected_skill}

【执行过程】
{tool_process}

【分析结果】
{llm_response}

【风险检查】
{risk_summary}

【记忆保存】
任务执行完成后将保存到 app_root/data/memory.json
```

---

## 25.5 执行过程格式

```text
- list_files success
- search_code("user") success
- read_file("app/user_router.py") success
- read_file(".env") failed: 禁止读取敏感文件：.env
```

---

## 25.6 风险检查逻辑

从 `tool_results` 中查找：

```text
success = false
reason 中包含 “禁止”
```

以及 `search_code.rejected_files` 中被拒绝的记录。

如果存在，输出：

```text
检测到被拒绝的访问：
- .env: 禁止读取敏感文件：.env
```

如果不存在，输出：

```text
未发现敏感文件读取行为。
```

---

# 26. MemoryWriter SPEC

## 26.1 功能

保存任务执行记录。

---

## 26.2 存储文件

```text
app_root/data/memory.json
```

---

## 26.3 保存内容

```json
{
  "task_id": "task_001",
  "task_type": "small_feature_plan",
  "query": "帮我给用户模块增加修改昵称接口",
  "workspace": "/path/to/project",
  "related_files": [
    "app/user_router.py",
    "app/user_service.py",
    "app/user_schema.py"
  ],
  "experience": "小功能计划任务通常需要定位相关模块文件。",
  "success": true,
  "created_at": "2026-06-20 12:00:00"
}
```

---

## 26.4 保存策略

```text
1. 从 tool_results 中提取 related_files
2. 根据 selected_skill 生成 experience
3. 读取已有 memory.json
4. 如果 memory.json 损坏，则初始化为空数组
5. append 新记录
6. 写回 memory.json
```

---

## 26.5 related_files 提取规则

```text
1. read_file 成功的 path 加入 related_files
2. search_code 成功的 matches.path 加入 related_files
3. 去重
4. 最多保存前 20 个
5. rejected_files 不加入 related_files
```

---

## 26.6 experience 生成规则

| Skill              | experience                        |
| ------------------ | --------------------------------- |
| explain_project    | 项目分析任务通常优先查看 README、依赖文件和核心目录。    |
| fix_error          | 报错分析任务通常优先检查错误关键词、依赖声明、配置文件和相关源码。 |
| small_feature_plan | 小功能计划任务通常需要定位相关模块文件。              |
| patch_suggestion   | Patch 建议任务通常需要明确目标文件、修改点和影响范围。    |
| unknown            | 未识别任务类型，未产生有效经验。                  |

---

# 27. 统一错误处理策略

第一版必须保证：**局部失败不导致整体程序崩溃**。

---

## 27.1 工具失败

工具失败时返回：

```json
{
  "tool": "read_file",
  "success": false,
  "path": "abc.txt",
  "reason": "文件不存在"
}
```

不能直接抛异常中断程序。

---

## 27.2 权限拒绝

权限拒绝不算程序崩溃。

它应该：

```text
1. 以 success=false 返回 Tool Result
2. 在 ResponseFormatter 的风险检查中展示
3. 不进入 related_files
```

---

## 27.3 unknown 任务

如果 SkillRouter 返回 unknown：

```text
1. 不调用工具
2. 返回提示用户补充任务
3. 仍可保存一条 memory 记录
```

输出示例：

```text
【任务类型】
unknown

【分析结果】
暂时无法识别任务类型。请明确你是要分析项目、分析报错、生成小功能计划，还是生成 Patch 建议。
```

---

## 27.4 LLM 失败

真实模型调用失败：

```text
1. 捕获异常
2. 返回模型失败提示
3. 可降级 Mock
4. 程序继续输出和保存 memory
```

---

## 27.5 memory.json 损坏

如果 memory.json 读取失败：

```text
1. 不让程序崩溃
2. 初始化为空数组
3. 写入新的记录
```

---

## 27.6 skills.json 缺失

如果 skills.json 缺失：

```text
1. 返回清晰错误提示
2. 不继续执行 Agent 流程
```

---

# 28. Debug 策略

第一版不做完整日志系统，但提供简单 Debug 模式。

---

## 28.1 环境变量

```text
MINICODE_DEBUG=1
```

---

## 28.2 开启后输出

```text
1. app_root
2. workspace
3. selected_skill
4. skill reason
5. tool_results 简要信息
6. prompt 前 1000 字符预览
7. memory_path
```

---

## 28.3 作用

```text
1. 方便开发调试
2. 方便面试时展示 Agent 执行过程
3. 方便定位路径错误和工具调用错误
```

---

# 29. Demo 项目 SPEC

## 29.1 目录

```text
examples/sample_project/
  README.md
  requirements.txt
  app/
    main.py
    user_router.py
    user_service.py
    user_schema.py
  tests/
    test_user.py
```

---

## 29.2 README.md 内容要求

包含：

```text
项目说明
技术栈
启动方式
```

---

## 29.3 requirements.txt 内容

```text
fastapi
uvicorn
pydantic
```

---

## 29.4 user_router.py 要求

包含：

```text
APIRouter
/user prefix
get_user 接口
UserService 调用
```

---

## 29.5 user_service.py 要求

包含：

```text
UserService
get_user 方法
nickname 字段
```

---

## 29.6 user_schema.py 要求

包含：

```text
UserProfile
nickname 字段
```

---

## 29.7 tests/test_user.py 要求

包含一个简单测试函数。

---

## 29.8 .env 演示文件

sample_project 中可以创建一个 `.env` 文件用于安全演示。

内容可以是假的：

```text
FAKE_API_KEY=demo
```

该文件必须被 PermissionChecker 拒绝读取。

---

# 30. 开发批次

## P0：项目初始化

目标：

```text
项目能启动，CLI 能接收输入
```

任务：

```text
1. 创建目录结构
2. 添加 __init__.py
3. 编写 main.py 最小版本
4. 创建 README.md
5. 明确 app_root 和 workspace
```

验收：

```bash
python main.py "hello"
```

能输出用户输入、app_root 和 workspace。

---

## P1：任务会话 + Skill Router

目标：

```text
自然语言任务 → Skill 类型
```

任务：

```text
1. 编写 skills/skills.json
2. 实现 SkillRouter
3. 实现 QueryLoop 基础版本
4. 创建 Task Session
5. 修正 patch_suggestion 路由条件，避免“修改昵称接口”误判
```

验收命令：

```bash
python main.py "帮我分析这个项目"
python main.py "运行时报错 ModuleNotFoundError，帮我分析"
python main.py "帮我给用户模块增加修改昵称接口"
python main.py "帮我修改 src/config.py"
```

期望分别识别：

```text
explain_project
fix_error
small_feature_plan
patch_suggestion
```

其中：

```text
帮我给用户模块增加修改昵称接口
```

必须识别为：

```text
small_feature_plan
```

---

## P2：工具调用 + 权限审查

目标：

```text
Agent 能读取项目上下文，并拒绝敏感文件
```

任务：

```text
1. 实现 PermissionChecker
2. 实现 list_files
3. 实现 read_file
4. 实现 search_code
5. 实现 ToolExecutor
6. 确保 read_file 和 search_code 都经过 PermissionChecker
7. read_file 增加 max_file_size 限制
```

验收：

```bash
python main.py "帮我分析这个项目"
python main.py "读取 .env 看看"
```

必须能：

```text
扫描目录
读取普通文件
搜索关键词
拒绝 .env
search_code 不扫描敏感文件
```

---

## P3：Agent 闭环

目标：

```text
工具结果 → Prompt → 模型输出 → 格式化输出 → 保存记忆
```

任务：

```text
1. 实现 ContextBuilder
2. 实现 LLMClient Mock
3. 实现真实模型调用失败降级
4. 实现 ResponseFormatter
5. 实现 MemoryWriter
6. QueryLoop 串完整流程
7. 实现统一错误处理策略
```

验收：

```bash
python main.py "帮我给用户模块增加修改昵称接口"
```

必须输出：

```text
任务类型
执行过程
分析结果
风险检查
记忆保存
```

并生成：

```text
app_root/data/memory.json
```

---

## P4：Demo 和包装

目标：

```text
项目可以展示、可以放 GitHub、可以支撑简历
```

任务：

```text
1. 准备 examples/sample_project
2. 写 README
3. 写 Demo 命令
4. 写最小测试矩阵
5. 截图或录制演示
6. 修复输出格式问题
```

验收：

4 个 Demo 命令全部跑通：

```bash
cd examples/sample_project

python ../../main.py "帮我分析这个项目"

python ../../main.py "帮我给用户模块增加修改昵称接口"

python ../../main.py "运行时报错 ModuleNotFoundError: No module named 'fastapi'，帮我分析"

python ../../main.py "读取 .env 看看"
```

---

# 31. 第一版验收标准

## 31.1 功能验收

必须满足：

```text
1. CLI 可以接收用户任务
2. app_root 和 workspace 正确区分
3. SkillRouter 可以识别 4 类任务
4. “修改昵称接口”不会误判为 patch_suggestion
5. list_files 可以扫描项目目录
6. read_file 可以读取普通文本文件
7. read_file 会拒绝读取 .env 等敏感文件
8. read_file 会拒绝读取超过 1MB 的文件
9. search_code 可以搜索关键词
10. search_code 不会扫描敏感文件
11. small_feature_plan 可以搜索 user / nickname 相关文件
12. ContextBuilder 可以生成结构化 Prompt
13. LLMClient 支持 Mock 模式
14. 真实模型失败不会导致程序崩溃
15. ResponseFormatter 可以输出统一格式
16. MemoryWriter 可以保存 memory.json
17. 4 个 Demo 命令可以跑通
```

---

## 31.2 输出验收

最终输出必须包含：

```text
【任务类型】
【执行过程】
【分析结果】
【风险检查】
【记忆保存】
```

---

## 31.3 安全验收

必须拒绝：

```text
.env
.env.local
id_rsa
*.pem
*.key
.ssh/
config.secret.json
database_password.txt
项目目录外路径
```

---

## 31.4 稳定性验收

不能出现：

```text
1. 用户输入 unknown 任务时程序崩溃
2. 文件不存在时程序崩溃
3. 编码异常时程序崩溃
4. 权限拒绝时程序崩溃
5. 没有 API Key 时程序崩溃
6. API 调用失败时程序崩溃
7. memory.json 损坏时程序崩溃
8. 在 examples/sample_project 中运行时找不到 skills.json
```

---

# 32. 最小测试矩阵

第一版至少需要手动测试以下用例。

| 模块                | 输入                             | 期望                                                 |
| ----------------- | ------------------------------ | -------------------------------------------------- |
| main.py           | hello                          | 不崩溃，返回 unknown 或提示                                 |
| 路径模型              | cd examples/sample_project 后运行 | workspace 是 sample_project，app_root 是 MiniCode 根目录 |
| SkillRouter       | 帮我分析这个项目                       | explain_project                                    |
| SkillRouter       | 运行时报错 error                    | fix_error                                          |
| SkillRouter       | 帮我给用户模块增加修改昵称接口                | small_feature_plan                                 |
| SkillRouter       | 帮我修改 src/config.py             | patch_suggestion                                   |
| PermissionChecker | README.md                      | allowed                                            |
| PermissionChecker | .env                           | denied                                             |
| PermissionChecker | ../.env                        | denied                                             |
| PermissionChecker | private.key                    | denied                                             |
| list_files        | .                              | 返回项目文件                                             |
| read_file         | README.md                      | success=true                                       |
| read_file         | 不存在文件                          | success=false                                      |
| read_file         | .env                           | success=false                                      |
| search_code       | user                           | 返回匹配行                                              |
| search_code       | token                          | 不读取敏感文件                                            |
| ContextBuilder    | tool_results                   | 生成 Prompt                                          |
| LLMClient         | 无 API Key                      | Mock 输出                                            |
| LLMClient         | 错误 API Key                     | 不崩溃                                                |
| MemoryWriter      | 正常任务                           | memory.json 有记录                                    |
| MemoryWriter      | memory.json 损坏                 | 不崩溃，重新初始化                                          |
| Demo              | 4 个演示命令                        | 全部跑通                                               |

---

# 33. README 第一版要求

README 必须包含：

```text
1. 项目一句话介绍
2. 项目背景
3. 核心功能
4. 核心执行流程图
5. 目录结构
6. 安装方式
7. 快速开始
8. 4 个 Demo 命令
9. 每个模块职责
10. 第一版边界
11. 安全说明
12. 后续计划
```

README 中必须明确写：

```text
MiniCode v0.1.1 是一个本地 CLI Coding Agent MVP。
第一版只输出分析、计划和 Patch 建议，不自动修改文件。
```

---

# 34. 第一版技术边界

第一版可以接受：

```text
1. Skill Router 偶尔误判
2. search_code 只支持关键词搜索
3. ContextBuilder 只做固定截断
4. memory.json 只保存不召回
5. Mock 输出不完全准确
6. 项目根目录默认使用当前目录
```

第一版不能接受：

```text
1. 主流程跑不通
2. 4 个 Demo 命令跑不通
3. 读取 .env 没有被拒绝
4. search_code 绕过权限审查
5. app_root 和 workspace 混用
6. 没有保存任务记录
7. 工具失败导致程序崩溃
8. 输出没有执行过程
```

---

# 35. 第二版优化方向

第二版再做：

```text
1. Skill Router 改成关键词打分制
2. TaskSession 改成 dataclass
3. ToolResult 统一数据结构
4. memory.json 改成 memory.jsonl 或 SQLite
5. search_code 改成 ripgrep
6. ContextBuilder 按 Skill 拆 Prompt 模板
7. 增加 token budget
8. 增加 run_tests 工具
9. 增加 git_diff 工具
10. 增加 apply_patch，但必须用户确认
11. 增加真实模型失败重试
12. 增加日志系统
13. 增加项目根目录自动识别
14. 增加 Rich CLI 输出
15. 增加 Tree-sitter 结构解析
```

---

# 36. 面试讲法

## 36.1 30 秒版本

```text
MiniCode 是一个本地代码项目的小任务 AI Coding Agent MVP。

用户输入任务后，系统会通过 Skill Router 判断任务类型，比如项目分析、报错分析、小功能计划或 Patch 建议。

然后系统根据任务类型调用 list_files、read_file、search_code 等工具读取项目上下文。

所有读取文件内容的工具都会经过 PermissionChecker，避免访问 .env、私钥、token 和项目目录外路径。

工具结果会被 ContextBuilder 压缩成结构化 Prompt，再交给 Mock 或真实模型生成结果。

最后系统通过 ResponseFormatter 输出结果，并用 MemoryWriter 保存任务记录。
```

---

## 36.2 技术难点版本

```text
这个项目的难点不是简单调用大模型，而是让 Agent 在本地代码项目中可控地执行任务。

我主要处理了五个问题：

第一，任务怎么路由。我设计了 Skill Router，把用户任务分成项目分析、报错分析、小功能计划和 Patch 建议四类，并修正了“修改昵称接口”这类容易误判的场景。

第二，项目上下文怎么获取。我实现了 list_files、read_file、search_code，让 Agent 可以主动读取项目结构和相关代码。

第三，安全边界怎么控制。read_file 和 search_code 都经过 PermissionChecker，禁止读取 .env、私钥、token、密码文件和项目目录外路径。

第四，路径边界怎么处理。我区分了 app_root 和 workspace，避免在 Demo 项目中运行时找不到 skills.json 或把 memory 写到错误目录。

第五，上下文怎么压缩。工具结果不能全部塞给模型，所以我用 ContextBuilder 整理成文件路径、摘要和关键片段，再生成 Prompt。

最后，我用 MemoryWriter 保存任务类型、相关文件和经验总结，形成完整执行闭环。
```

---

# 37. 最终一句话总结

MiniCode v0.1.1 的目标是：

```text
用最小实现跑通一个受控的本地 Coding Agent 核心执行闭环。
```

它证明：

```text
自然语言任务可以被路由成 Skill；
Skill 可以驱动工具调用；
工具可以读取真实项目上下文；
读取文件内容前有权限审查；
app_root 和 workspace 可以正确隔离；
工具结果可以被压缩成模型上下文；
模型输出可以被统一格式化；
任务经验可以被保存。
```

第一版不追求复杂智能，追求：

```text
能跑通
能演示
能解释
能支撑简历
```
