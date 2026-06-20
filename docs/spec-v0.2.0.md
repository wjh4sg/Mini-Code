# MiniCode SPEC v0.2.0

## 文档定位

本文件是 [MiniCode MVP SPEC v0.1.1](spec-v0.1.1.md) 的增量规格。
v0.1.1 定义 Agent 核心链路、工具能力和只读安全边界；v0.2.0 在这些能力
保持不变的前提下，将源码脚本升级为可安装的本地 CLI 工具。

## 版本目标

v0.2.0 解决“必须知道 `main.py` 绝对路径才能运行”的入口问题，使 MiniCode
可以安装后在任意项目目录调用，同时继续区分：

- `app_root`：MiniCode 自身配置、Skill 和 memory 所在目录；
- `workspace`：用户指定的只读项目分析范围。

## 新增能力

### Installable CLI

```bash
python -m pip install --upgrade pip
python -m pip install -e .
minicode --version
```

`pyproject.toml` 通过 console script 暴露：

```toml
[project.scripts]
minicode = "minicode_cli:main"
```

### Workspace 参数

```bash
minicode -w examples/sample_project "帮我分析这个项目"
```

未传 `-w/--workspace` 时使用当前目录。

### 运行模式

```bash
minicode --debug "帮我分析这个项目"
minicode --mock "帮我分析这个项目"
```

`--debug` 只输出安全诊断信息；`--mock` 只在当前执行中忽略真实模型配置。

### Doctor

```bash
minicode doctor -w examples/sample_project
```

输出 Python、app root、workspace、Skill 文件、memory 路径和 LLM 模式。

### 源码兼容入口

```bash
python main.py "帮我分析这个项目"
```

`main.py` 继续保留，并委托给与 `minicode` 相同的 CLI 实现。

## 安全边界

v0.2.0 完整继承 v0.1.1 的只读安全边界：

- 不自动修改或删除目标项目文件；
- 不执行 Shell；
- 不运行目标项目测试；
- 不执行 Git commit 或 push；
- 所有文件内容读取继续经过 `PermissionChecker`；
- workspace 外路径和敏感文件继续被拒绝。

CLI 产品化没有扩大 Agent 权限。

## 验收标准

- editable install 后可运行 `minicode`；
- `minicode --version` 返回当前版本；
- `-w/--workspace` 正确设置只读分析范围；
- `--debug` 与 `--mock` 只在单次执行内生效；
- `doctor` 不创建 QueryLoop 或调用模型；
- `python main.py ...` 保持兼容；
- Python 3.10、3.11、3.12 CI 均执行安装、命令冒烟测试和完整单元测试。
