class QueryLoop:
    def __init__(self, app_root, workspace):
        self.app_root = app_root
        self.workspace = workspace

    def run(self, user_query):
        return f"MiniCode received: {user_query}"
