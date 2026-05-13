import sys
import anthropic

task = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read().strip()

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=256,
    system="Answer the following question.",
    messages=[{"role": "user", "content": task}],
)
print(response.content[0].text)
