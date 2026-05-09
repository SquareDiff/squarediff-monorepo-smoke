import os
import sys


payload = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read().strip()
print(f"python-nested-cwd|input={payload}|cwd={os.path.basename(os.getcwd())}")
