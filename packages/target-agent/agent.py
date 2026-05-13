import sys
import anthropic

SYSTEM_PROMPT = (
    "You are a helpful and accurate assistant. "
    "Place your answer on the first line. Do not use preamble, hedging, or transition phrases before the answer. "
    "Respond in a single sentence or phrase unless the task explicitly requires more. Never add trailing explanation unless asked. "
    "Do not ask follow-up questions. Do not end your response with a question mark. "
    "If the task is ambiguous, make your best inference and answer — do not ask for clarification. "
    "If it requires reasoning, reason briefly then state your conclusion on the first line.\n\n"
    "BAD: 'That's a great question! The capital of France is Paris, but let me know if you need more details?'\n"
    "GOOD: 'Paris.'"
)


def extract_text(response):
    parts = [block.text for block in response.content if block.type == "text"]
    return " ".join(parts).strip()


if __name__ == "__main__":
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": sys.argv[1]}],
    )
    print(extract_text(response) or "I could not determine the answer.")
