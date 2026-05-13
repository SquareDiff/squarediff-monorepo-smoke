import sys
import anthropic

payload = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read().strip()

client = anthropic.Anthropic()

message = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=128,
    system="Answer concisely. Provide only the final answer with no explanation, no preamble, and no hedging.",
    messages=[{"role": "user", "content": payload}],
)

print(message.content[0].text)
