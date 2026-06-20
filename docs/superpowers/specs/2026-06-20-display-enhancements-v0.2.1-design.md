# MiniCode v0.2.1 展示增强设计

## 背景

MiniCode v0.2.0 已完成 CLI 产品化：提供可安装的 `minicode` 命令、
workspace 参数、Mock/Debug 模式、`doctor` 诊断和多 Python 版本 CI。
当前仓库的主要短板不在运行能力，而在展示证据：

- README 的完整执行示例主要来自 Mock，不能体现真实模型的分析质量；
- v0.2.0 缺少独立版本说明文档，版本演进需要结合 v0.1.1 SPEC 理解；
- CLI 已具备正式入口，但 README 缺少直观的终端展示图；
- `doctor` 和 `--help` 已实现，但展示信息分散。

v0.2.1 定位为纯展示增强版本，不扩展 Agent 权限或运行能力。

## 目标

1. 使用阿里云百炼 `deepseek-v4-flash` 产生一份可复现、可核验的真实模型
   “小功能计划”示例。
2. 在 README 中同时展示真实模型效果和 CLI 工具化体验。
3. 新增 v0.2.0 版本规格增量文档，说明它与 v0.1.1 核心 SPEC 的关系。
4. 将项目版本统一更新为 v0.2.1。
5. 保持 CLI、Agent、安全边界和 `doctor` 行为不变。

## 非目标

v0.2.1 不包含以下内容：

- 不增强 `doctor` 检查项；
- 不修改 Skill 路由、Prompt、ContextBuilder、工具或 memory；
- 不增加自动写文件、执行测试、Git 操作或多 Agent；
- 不增加 GIF、录屏或依赖外部托管的图片；
- 不把阿里云 API Key、请求头或其他凭据写入仓库；
- 不用 Mock 输出冒充真实模型输出。

## 方案

### 1. 真实模型示例

使用现有 OpenAI-compatible 客户端，不修改业务代码。采集时仅在当前子进程
内映射环境变量：

```text
DASHSCOPE_API_KEY -> MINICODE_API_KEY
MINICODE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MINICODE_MODEL=deepseek-v4-flash
```

运行目标为 `examples/sample_project`，任务固定为：

```text
帮我给用户模块增加修改昵称接口
```

该任务能展示 `search_code`、相关文件读取、结构化输出和真实模型分析质量。
采集结果保存为 `docs/real-llm-example.md`，内容包含：

- 模型与服务说明；
- 可复现命令模板，Key 仅以环境变量名出现；
- 实际执行过程和模型输出；
- 采集日期；
- “输出可能随模型服务变化”的说明。

采集前后均检查文件内容，不允许出现 API Key、Authorization header 或完整
本机用户路径。若调用失败、发生 Mock 降级或模型 ID 不可用，则停止采集并
报告实际错误，不生成伪造示例。

### 2. CLI 终端展示图

新增 `docs/cli-showcase.svg`，沿用仓库现有深色终端风格，静态展示三组已实现
命令：

1. `minicode --help`：展示参数入口；
2. `minicode doctor -w examples/sample_project`：展示环境诊断；
3. `minicode --mock -w examples/sample_project "读取 .env 看看"`：
   展示敏感文件拒绝。

SVG 中的绝对路径统一替换为 `<repo>`，避免绑定开发机。图片只表达已经由
测试覆盖的行为，不展示未实现功能。

### 3. 版本增量文档

新增 `docs/spec-v0.2.0.md`，作为 `docs/spec-v0.1.1.md` 的增量说明，不复制
完整核心 SPEC。文档明确：

- v0.1.1 定义 Agent 核心与安全边界；
- v0.2.0 新增 installable CLI、workspace、debug/mock、doctor 和兼容入口；
- v0.2.0 没有扩大文件、Shell 或 Git 权限；
- 安装、命令和验收标准。

README 的规格链接调整为同时指向核心 SPEC 与 v0.2.0 增量规格。

### 4. README 展示结构

README 保留现有 Mock Demo，增加以下内容：

- 在项目简介下展示 `docs/cli-showcase.svg`；
- 新增“真实模型输出示例”小节，说明模型为阿里云百炼
  `deepseek-v4-flash`，摘录 `docs/real-llm-example.md` 中最有代表性的输出；
- 新增 `doctor` 输出示例；
- 将版本定位更新为 v0.2.1，并说明本版本只增强展示证据；
- 链接完整真实输出和 v0.2.0 增量规格。

README 不写入真实 API Key，不要求读者拥有阿里云账号才能理解示例。

### 5. 版本元数据

以下位置统一更新为 `0.2.1`：

- `minicode_cli.__version__`；
- `pyproject.toml` 的 `project.version`；
- README 当前版本描述；
- 架构图标题；
- 对应版本测试断言。

命令行为保持不变，`minicode --version` 输出 `MiniCode 0.2.1`。

## 文件变更

新增：

- `docs/real-llm-example.md`
- `docs/cli-showcase.svg`
- `docs/spec-v0.2.0.md`

修改：

- `README.md`
- `minicode_cli.py`
- `pyproject.toml`
- `docs/architecture.svg`
- `tests/test_cli_acceptance.py`
- `tests/test_minicode_cli.py`
- `tests/test_packaging.py`

不修改：

- `agent/`
- `tools/`
- `safety/`
- `memory/`
- `skills/skills.json`

## 测试与验收

自动测试新增或更新以下断言：

- CLI 与 package 版本均为 `0.2.1`；
- README 链接 `docs/cli-showcase.svg`、`docs/real-llm-example.md` 和
  `docs/spec-v0.2.0.md`；
- 三个新增展示文件存在且非空；
- 真实模型文档包含 `deepseek-v4-flash`、固定示例任务和结构化输出标题；
- 展示文件不包含 `DASHSCOPE_API_KEY` 的值、`Authorization: Bearer` 或
  `C:\Users\` 本机路径；
- `docs/spec-v0.2.0.md` 明确继承 v0.1.1 安全边界；
- 原有 58 项测试继续通过；
- `python -m compileall -q .` 通过；
- `python main.py --version` 输出 `MiniCode 0.2.1`；
- editable install 后 `minicode --version` 和 `minicode doctor` 冒烟测试通过。

## 发布边界

实现完成后创建独立 PR，等待 Python 3.10、3.11、3.12 CI 全绿后合并，并
从合并后的 `main` 发布 v0.2.1 Release。Release 说明将其定位为
“展示增强版”，不宣称 Agent 能力升级。
