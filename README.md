# MiniCode

MiniCode v0.1.1 是一个本地 CLI Coding Agent MVP。
第一版只输出分析、计划和 Patch 建议，不自动修改文件。

## 项目背景

普通代码问答依赖用户手动复制项目结构和源码，也难以验证模型提到的
文件是否真实存在。MiniCode 让 Agent 在明确的安全边界内主动读取本地
项目上下文，再生成可解释、可追踪的分析结果。

## 核心功能

- 项目分析：识别用途、技术栈、目录结构和启动方式。
- 报错分析：搜索错误关键词和依赖声明，给出排查建议。
- 小功能计划：定位相关 router、service、schema 和测试文件。
- Patch 建议：读取明确目标文件并给出文本 Patch，不写入文件。
- 权限审查：拒绝敏感文件、私钥和工作区外路径。
- Mock/真实模型：没有密钥也能演示，模型失败自动降级。
- 任务记忆：将任务类型、相关文件和经验保存到 `data/memory.json`。

## 核心执行流程

```mermaid
flowchart LR
    A[用户任务] --> B[SkillRouter]
    B --> C[ToolExecutor]
    C --> D[PermissionChecker]
    D --> E[项目上下文]
    E --> F[ContextBuilder]
    F --> G[Mock / Real LLM]
    G --> H[ResponseFormatter]
    H --> I[MemoryWriter]
```

## 目录结构

```text
main.py
agent/       调度、路由、Prompt、模型和输出
tools/       文件扫描、读取和代码搜索
safety/      路径边界与敏感文件检查
memory/      JSON 任务记忆
skills/      Skill 配置
data/        应用级记忆文件
examples/    演示工作区
tests/       unittest 测试
```

## 安装

运行环境为 Python 3.10+。MiniCode 自身只使用标准库，无需安装依赖：

```bash
git clone <repository-url>
cd minicode
python --version
```

`examples/sample_project/requirements.txt` 只描述示例 FastAPI 项目，
运行 MiniCode 测试不需要安装它。

## 快速开始

在你希望分析的项目根目录运行 MiniCode 的 `main.py`：

```bash
python /path/to/minicode/main.py "帮我分析这个项目"
```

MiniCode 区分两个路径：

- `app_root`：MiniCode 自身目录，用于读取 `skills/` 和写入 `data/`。
- `workspace`：当前工作目录，也是只读分析范围。

## Demo

```bash
cd examples/sample_project

python ../../main.py "帮我分析这个项目"
python ../../main.py "帮我给用户模块增加修改昵称接口"
python ../../main.py "运行时报错 ModuleNotFoundError: No module named 'fastapi'，帮我分析"
python ../../main.py "读取 .env 看看"
```

最后一条命令会尝试读取演示 `.env`，随后由 `PermissionChecker` 明确拒绝。

## 模块职责

| 模块 | 职责 |
| --- | --- |
| `main.py` | 接收 CLI 输入，计算应用根目录与工作区 |
| `QueryLoop` | 创建任务会话并串联完整执行流程 |
| `SkillRouter` | 将自然语言任务路由到四类 Skill |
| `ToolExecutor` | 提供统一的只读工具入口 |
| `PermissionChecker` | 拒绝越界和敏感路径 |
| `ContextBuilder` | 压缩工具结果并构建 Prompt |
| `LLMClient` | 调用 Mock 或 OpenAI-compatible API |
| `ResponseFormatter` | 输出固定五段结果 |
| `MemoryWriter` | 保存任务记录和相关文件 |

## 真实模型配置

默认使用 Mock 模式。配置以下环境变量可调用 OpenAI-compatible API：

```text
MINICODE_API_KEY
MINICODE_BASE_URL
MINICODE_MODEL
```

请求发送到 `{MINICODE_BASE_URL}/chat/completions`。网络、鉴权或响应解析失败
都会显示错误原因并自动回退到 Mock。

## Debug 模式

```bash
MINICODE_DEBUG=1 python main.py "帮我分析这个项目"
```

Debug 信息写入标准错误，包括路径、Skill、工具摘要、Prompt 预览和 memory
路径，不输出 API Key。

## 安全说明

所有文件内容读取都必须经过 `PermissionChecker`。第一版拒绝：

- `.env`、`.env.local` 等环境文件；
- `.ssh/`、`.gnupg/`；
- `*.pem`、`*.key`、`*.crt`、`*.p12`；
- 名称包含 token、secret、password、credential、private、api_key 或
  access_key 的文件；
- 解析后位于 workspace 外的路径和符号链接。

`search_code` 对每个候选文件执行同样的检查，因此不能借搜索绕过权限。

## 测试

```bash
python -m compileall -q .
python -m unittest discover -v
```

测试覆盖路由优先级、文件边界、敏感数据、工具、Prompt 压缩、模型降级、
记忆恢复和四条 CLI Demo。

## 第一版边界

MiniCode v0.1.1 不自动修改或删除文件，不执行 shell，不运行目标项目测试，
不进行 Git commit/push，不提供 Web UI、IDE 插件、MCP、多 Agent、向量库、
Tree-sitter 或自动修复闭环。

## 后续计划

- 关键词打分路由和 dataclass 数据模型；
- SQLite/JSONL 记忆与召回；
- ripgrep、Tree-sitter 和真实 repo map；
- token budget、重试与结构化日志；
- 经用户确认的测试执行、Git diff 和 apply_patch；
- Rich CLI 与项目根目录自动识别。
