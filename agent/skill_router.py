import json
import re
from pathlib import Path


class SkillConfigError(Exception):
    pass


class SkillRouter:
    SENSITIVE_REQUEST_TERMS = (
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
    PATCH_TERMS = ("patch", "diff", "改这个文件", "修这个函数", "给出 patch")
    ERROR_TERMS = (
        "报错",
        "错误",
        "error",
        "exception",
        "failed",
        "traceback",
        "失败",
        "modulenotfounderror",
    )
    FEATURE_TERMS = (
        "新增",
        "增加",
        "添加",
        "接口",
        "功能",
        "页面",
        "分页",
        "搜索",
        "模块",
    )
    PROJECT_TERMS = ("分析", "项目", "结构", "目录", "启动", "技术栈", "看一下")
    FILE_PATH_PATTERN = re.compile(
        r"(?:^|[\s\"'（(])"
        r"([A-Za-z0-9_.-]+(?:[\\/][A-Za-z0-9_.-]+)*"
        r"\.(?:py|js|ts|java|go|md|json|yaml|yml))"
        r"(?=$|[\s\"'，。；:：）)])",
        re.IGNORECASE,
    )

    def __init__(self, app_root):
        self.config_path = Path(app_root) / "skills" / "skills.json"
        self.skills = self._load_skills()
        self.skills_by_name = {skill["name"]: skill for skill in self.skills}

    def _load_skills(self):
        if not self.config_path.exists():
            raise SkillConfigError(f"找不到 Skill 配置：{self.config_path}")
        try:
            skills = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise SkillConfigError(f"Skill 配置读取失败：{error}") from error
        if not isinstance(skills, list):
            raise SkillConfigError("Skill 配置必须是列表")
        for skill in skills:
            if not isinstance(skill, dict) or "name" not in skill:
                raise SkillConfigError("Skill 配置项格式无效")
        return skills

    def _matched(self, name, reason):
        skill = dict(self.skills_by_name[name])
        skill["reason"] = reason
        return skill

    def route(self, query):
        lowered = query.lower()
        if any(term in lowered for term in self.SENSITIVE_REQUEST_TERMS):
            return self._matched("patch_suggestion", "检测到敏感文件访问请求")
        if (
            any(term in lowered for term in self.PATCH_TERMS)
            or self.FILE_PATH_PATTERN.search(query)
        ):
            return self._matched("patch_suggestion", "检测到明确 Patch 或文件路径")
        if any(term in lowered for term in self.ERROR_TERMS):
            return self._matched("fix_error", "命中报错分析关键词")
        if any(term in lowered for term in self.FEATURE_TERMS):
            return self._matched("small_feature_plan", "命中小功能计划关键词")
        if any(term in lowered for term in self.PROJECT_TERMS):
            return self._matched("explain_project", "命中项目分析关键词")
        return {
            "name": "unknown",
            "description": "无法识别任务类型",
            "keywords": [],
            "tools": [],
            "output_schema": [],
            "reason": "未命中任何 Skill",
        }
