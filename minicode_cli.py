import argparse
import os
import sys
from contextlib import contextmanager
from pathlib import Path


__version__ = "0.2.1"


def resolve_app_root():
    return Path(__file__).resolve().parent


def build_task_parser():
    parser = argparse.ArgumentParser(
        prog="minicode",
        description="受控的本地 CLI Coding Agent",
    )
    parser.add_argument(
        "-w",
        "--workspace",
        type=Path,
        help="要分析的目标项目目录，默认使用当前目录",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="输出安全的调试诊断信息",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="强制使用 Mock 模式，不调用真实模型",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"MiniCode {__version__}",
    )
    parser.add_argument("query", nargs="*", help="要执行的自然语言任务")
    return parser


def build_doctor_parser():
    parser = argparse.ArgumentParser(
        prog="minicode doctor",
        description="检查 MiniCode 运行配置",
    )
    parser.add_argument(
        "-w",
        "--workspace",
        type=Path,
        help="要检查的目标项目目录，默认使用当前目录",
    )
    return parser


def resolve_workspace(path):
    workspace = (path or Path.cwd()).expanduser().resolve()
    if not workspace.is_dir():
        raise ValueError(f"工作区不存在或不是目录：{workspace}")
    return workspace


@contextmanager
def scoped_environment(debug=False, mock=False):
    names = (
        "MINICODE_DEBUG",
        "MINICODE_API_KEY",
        "MINICODE_BASE_URL",
        "MINICODE_MODEL",
    )
    previous = {name: os.environ.get(name) for name in names}
    try:
        if debug:
            os.environ["MINICODE_DEBUG"] = "1"
        if mock:
            for name in names[1:]:
                os.environ.pop(name, None)
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def doctor_output(app_root, workspace):
    skills_path = app_root / "skills" / "skills.json"
    memory_path = app_root / "data" / "memory.json"
    llm_mode = (
        "real"
        if os.environ.get("MINICODE_API_KEY")
        and os.environ.get("MINICODE_BASE_URL")
        else "mock"
    )
    return "\n".join(
        (
            "MiniCode doctor",
            f"Python: {sys.version.split()[0]}",
            f"app_root: {app_root}",
            f"workspace: {workspace}",
            f"skills.json: {'found' if skills_path.is_file() else 'missing'}",
            f"memory path: {memory_path}",
            f"LLM mode: {llm_mode}",
        )
    )


def main(argv=None, loop_factory=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    is_doctor = bool(argv and argv[0] == "doctor")
    parser = build_doctor_parser() if is_doctor else build_task_parser()
    parse_argv = argv[1:] if is_doctor else argv
    try:
        args = parser.parse_args(parse_argv)
    except SystemExit as error:
        return int(error.code)

    try:
        workspace = resolve_workspace(args.workspace)
    except ValueError as error:
        print(f"minicode: error: {error}", file=sys.stderr)
        return 2

    app_root = resolve_app_root()
    if is_doctor:
        print(doctor_output(app_root, workspace))
        return 0

    if not args.query:
        print("minicode: error: 需要提供任务", file=sys.stderr)
        parser.print_usage(sys.stderr)
        return 2

    if loop_factory is None:
        from agent.loop import QueryLoop

        loop_factory = QueryLoop

    with scoped_environment(debug=args.debug, mock=args.mock):
        loop = loop_factory(app_root, workspace)
        result = loop.run(" ".join(args.query).strip())
    print(result)
    return 0
