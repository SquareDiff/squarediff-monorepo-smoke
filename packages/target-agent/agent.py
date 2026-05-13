import sys
import anthropic

SYSTEM_PROMPT = (
    "You are a helpful and accurate assistant. "
    "Answer the user's question directly and concisely. "
    "State your answer on the first line without preamble, filler, or conversational framing. "
    "If the question has a specific factual answer, give it. "
    "If it requires reasoning, reason briefly then state your conclusion."
)


def extract_text(response):
    parts = [block.text for block in response.content if block.type == "text"]
    return " ".join(parts).strip()


if __name__ == "__main__":
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": sys.argv[1]}],
        temperature=0,
    )
    print(extract_text(response) or "I could not determine the answer.")
