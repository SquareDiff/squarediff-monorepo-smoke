import sys

payload = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read().strip()
print(f"target-agent|input={payload}")
