from pathlib import Path


class PermissionChecker:
    SENSITIVE_NAMES = {
        ".env",
        ".env.local",
        ".env.production",
        "id_rsa",
        "id_dsa",
        "credentials",
        "credential",
        "token",
        "secret",
    }
    SENSITIVE_DIRS = {".ssh", ".gnupg"}
    SENSITIVE_SUFFIXES = {".pem", ".key", ".crt", ".p12"}
    SENSITIVE_KEYWORDS = {
        "token",
        "secret",
        "password",
        "passwd",
        "credential",
        "credentials",
        "private",
        "api_key",
        "access_key",
    }

    def __init__(self, workspace):
        self.workspace = Path(workspace).resolve()

    def check_path(self, path):
        candidate = Path(path)
        if candidate.is_absolute():
            target = candidate.resolve()
        else:
            target = (self.workspace / candidate).resolve()

        try:
            relative = target.relative_to(self.workspace)
        except ValueError:
            return False, f"禁止访问项目目录外路径：{path}"

        lowered_parts = {part.lower() for part in relative.parts}
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
