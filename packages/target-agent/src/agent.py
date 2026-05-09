import os
import sys

from shared_lib import marker


def main() -> None:
    payload = sys.stdin.read().strip() or (sys.argv[1] if len(sys.argv) > 1 else "")
    cwd = os.path.relpath(os.getcwd(), start=os.environ.get("REPO_ROOT", os.getcwd()))
    print(f"python-shared-lib|input={payload}|marker={marker()}|cwd={cwd}")


if __name__ == "__main__":
    main()
