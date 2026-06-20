from pathlib import Path

from tools.file_tools import IGNORED_DIRS


SEARCH_SUFFIXES = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".java",
    ".go",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".html",
    ".css",
    ".vue",
}


def search_code(
    workspace,
    keyword,
    permission_checker,
    max_results=20,
    max_file_size=1048576,
):
    if not keyword or not keyword.strip():
        return {
            "tool": "search_code",
            "success": False,
            "keyword": keyword,
            "reason": "搜索关键词不能为空",
        }

    workspace = Path(workspace).resolve()
    matches = []
    rejected_files = []
    needle = keyword.lower()

    def walk(directory):
        for child in sorted(directory.iterdir(), key=lambda item: item.name.lower()):
            if child.is_dir():
                if child.name in IGNORED_DIRS:
                    continue
                walk(child)
                if len(matches) >= max_results:
                    return
                continue

            relative = child.relative_to(workspace).as_posix()
            allowed, reason = permission_checker.check_path(Path(relative))
            if not allowed:
                rejected_files.append({"path": relative, "reason": reason})
                continue
            if child.suffix.lower() not in SEARCH_SUFFIXES:
                continue
            if child.stat().st_size > max_file_size:
                continue

            text = child.read_text(encoding="utf-8", errors="ignore")
            for line_number, line in enumerate(text.splitlines(), start=1):
                if needle in line.lower():
                    matches.append(
                        {
                            "path": relative,
                            "line": line_number,
                            "text": line.strip(),
                        }
                    )
                    if len(matches) >= max_results:
                        return

    try:
        walk(workspace)
    except OSError as error:
        return {
            "tool": "search_code",
            "success": False,
            "keyword": keyword,
            "matches": matches,
            "rejected_files": rejected_files,
            "reason": f"代码搜索失败：{error}",
        }
    return {
        "tool": "search_code",
        "success": True,
        "keyword": keyword,
        "matches": matches,
        "rejected_files": rejected_files,
        "summary": (
            f"搜索关键词 {keyword}，找到 {len(matches)} 条结果"
            f"，跳过 {len(rejected_files)} 个敏感文件"
        ),
    }
