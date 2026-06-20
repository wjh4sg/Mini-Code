import re


class QueryLoop:
    FEATURE_KEYWORD_MAP = {
        "用户": ["user", "account", "profile"],
        "昵称": ["nickname", "display_name", "username", "name"],
        "接口": ["router", "controller", "api", "route"],
        "登录": ["login", "auth", "token"],
        "分页": ["page", "pagination", "limit", "offset"],
        "搜索": ["search", "query", "keyword"],
    }
    SENSITIVE_TERMS = (
        ".env",
        "id_rsa",
        ".pem",
        ".key",
        "credentials",
        "token",
        "secret",
        "password",
        "api_key",
        "access_key",
    )
    FILE_PATTERN = re.compile(
        r"[A-Za-z0-9_.-]+(?:[\\/][A-Za-z0-9_.-]+)*"
        r"\.(?:py|js|ts|java|go|md|json|yaml|yml)",
        re.IGNORECASE,
    )

    def __init__(self, app_root, workspace):
        self.app_root = app_root
        self.workspace = workspace

    def run(self, user_query):
        return f"MiniCode received: {user_query}"

    def _extract_keywords(self, text):
        parts = re.split(r"[\s,，:：]+", text)
        return [part for part in parts if len(part) >= 2]

    def _expand_feature_keywords(self, text):
        keywords = []
        for chinese, expanded in self.FEATURE_KEYWORD_MAP.items():
            if chinese in text:
                keywords.extend(expanded)
        keywords.extend(self._extract_keywords(text))
        return list(dict.fromkeys(keywords))

    def _collect_related_files_from_search(self, results):
        first_seen = {}
        for result in results:
            if result.get("tool") != "search_code" or not result.get("success"):
                continue
            for match in result.get("matches", []):
                path = match.get("path")
                if path and path not in first_seen:
                    first_seen[path] = len(first_seen)

        def rank(path):
            lowered = path.lower()
            if "router" in lowered or "controller" in lowered:
                return 0
            if "service" in lowered:
                return 1
            if "schema" in lowered or "model" in lowered:
                return 2
            if "test" in lowered:
                return 3
            return 4

        return sorted(first_seen, key=lambda path: (rank(path), first_seen[path]))[:5]

    def _extract_file_paths(self, text):
        return self.FILE_PATTERN.findall(text)

    def _detect_sensitive_file_request(self, text):
        lowered = text.lower()
        for term in self.SENSITIVE_TERMS:
            if term in lowered:
                return term
        return None
