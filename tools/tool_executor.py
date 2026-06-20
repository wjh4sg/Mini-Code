from pathlib import Path

from safety.permission_checker import PermissionChecker
from tools.file_tools import list_files, read_file
from tools.search_tools import search_code


class ToolExecutor:
    def __init__(self, workspace):
        self.workspace = Path(workspace).resolve()
        self.permission_checker = PermissionChecker(self.workspace)

    def list_files(self, path="."):
        return list_files(self.workspace, path)

    def read_file(self, path):
        return read_file(self.workspace, path, self.permission_checker)

    def search_code(self, keyword):
        return search_code(self.workspace, keyword, self.permission_checker)
