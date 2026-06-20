import sys
from pathlib import Path


def resolve_roots():
    return Path(__file__).resolve().parent, Path.cwd().resolve()


def main():
    if len(sys.argv) < 2:
        print('用法: python main.py "你的任务"')
        return 1

    from agent.loop import QueryLoop

    user_query = " ".join(sys.argv[1:]).strip()
    app_root, workspace = resolve_roots()
    loop = QueryLoop(app_root, workspace)
    print(loop.run(user_query))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
