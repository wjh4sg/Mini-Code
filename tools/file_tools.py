from pathlib import Path


IGNORED_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    "dist",
    "build",
    ".venv",
    "venv",
    ".idea",
    ".vscode",
}

TEXT_SUFFIXES = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".json",
    ".md",
    ".txt",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".java",
    ".go",
    ".html",
    ".css",
    ".scss",
    ".vue",
}


def _resolve_within_workspace(workspace, path):
    workspace = Path(workspace).resolve()
    candidate = Path(path)
    target = candidate.resolve() if candidate.is_absolute() else (workspace / candidate).resolve()
    try:
        target.relative_to(workspace)
    except ValueError:
        return workspace, None
    return workspace, target


def list_files(workspace, path=".", max_depth=2, max_items=200):
    workspace, root = _resolve_within_workspace(workspace, path)
    if root is None:
        return {
            "tool": "list_files",
            "success": False,
            "path": str(path),
            "reason": "禁止访问项目目录外路径",
        }
    if not root.exists():
        return {
            "tool": "list_files",
            "success": False,
            "path": str(path),
            "reason": "路径不存在",
        }
    if not root.is_dir():
        return {
            "tool": "list_files",
            "success": False,
            "path": str(path),
            "reason": "路径不是目录",
        }

    results = []

    def visit(directory, depth):
        for child in sorted(directory.iterdir(), key=lambda item: item.name.lower()):
            if len(results) >= max_items:
                return
            if child.is_dir() and child.name in IGNORED_DIRS:
                continue
            try:
                relative = child.relative_to(workspace).as_posix()
            except ValueError:
                continue
            if child.is_dir():
                results.append(relative + "/")
                if depth < max_depth:
                    visit(child, depth + 1)
            else:
                results.append(relative)

    visit(root, 0)
    return {
        "tool": "list_files",
        "success": True,
        "path": str(path),
        "result": results,
        "summary": f"扫描到 {len(results)} 个文件或目录",
    }


def read_file(
    workspace,
    path,
    permission_checker,
    max_lines=200,
    max_file_size=1048576,
):
    allowed, reason = permission_checker.check_path(Path(path))
    if not allowed:
        return {
            "tool": "read_file",
            "success": False,
            "path": str(path),
            "reason": reason,
        }

    workspace, target = _resolve_within_workspace(workspace, path)
    if target is None:
        return {
            "tool": "read_file",
            "success": False,
            "path": str(path),
            "reason": "禁止访问项目目录外路径",
        }
    if not target.exists():
        return {
            "tool": "read_file",
            "success": False,
            "path": str(path),
            "reason": "文件不存在",
        }
    if not target.is_file():
        return {
            "tool": "read_file",
            "success": False,
            "path": str(path),
            "reason": "路径不是文件",
        }
    if target.suffix.lower() not in TEXT_SUFFIXES:
        return {
            "tool": "read_file",
            "success": False,
            "path": str(path),
            "reason": "不支持的文本文件类型",
        }
    if target.stat().st_size > max_file_size:
        return {
            "tool": "read_file",
            "success": False,
            "path": str(path),
            "reason": "文件过大，超过 1MB，跳过读取",
        }

    text = target.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    selected = lines[:max_lines]
    return {
        "tool": "read_file",
        "success": True,
        "path": target.relative_to(workspace).as_posix(),
        "content": "\n".join(selected),
        "line_count": len(lines),
        "truncated": len(lines) > max_lines,
        "summary": f"读取 {target.relative_to(workspace).as_posix()} 成功，共 {len(lines)} 行",
    }
