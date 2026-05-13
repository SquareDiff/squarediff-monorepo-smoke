import sys
import anthropic

PROMPT_STRATEGIES = {
    "factual": (
        "You are a precise and knowledgeable assistant. Answer questions with accurate, "
        "well-sourced factual information. Be concise and direct. Cite relevant details "
        "and avoid speculation."
    ),
    "mathematical": (
        "You are an expert mathematician and problem solver. Work through problems "
        "step-by-step, showing your reasoning clearly. Check your work, use precise "
        "notation, and provide exact answers where possible."
    ),
    "creative": (
        "You are a creative and imaginative assistant. Embrace originality, vivid "
        "language, and expressive ideas. Think outside conventional boundaries and "
        "produce engaging, inventive responses."
    ),
    "conversational": (
        "You are a friendly and approachable conversational assistant. Respond naturally "
        "and warmly, matching the tone of the user. Keep replies concise and human."
    ),
}

CATEGORIES = set(PROMPT_STRATEGIES.keys())


def classify_task(client: anthropic.Anthropic, user_message: str) -> str:
    meta_prompt = (
        "Classify the following task into exactly one of these categories: "
        "factual, mathematical, creative, conversational. "
        "Reply with only the category word."
    )
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=10,
        messages=[
            {
                "role": "user",
                "content": f"{meta_prompt}\n\nTask: {user_message}",
            }
        ],
    )
    raw = response.content[0].text.strip().lower()
    return raw if raw in CATEGORIES else "factual"


def execute_task(client: anthropic.Anthropic, category: str, user_message: str) -> str:
    system_prompt = PROMPT_STRATEGIES.get(category, PROMPT_STRATEGIES["factual"])
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


def main() -> None:
    user_message = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read().strip()
    client = anthropic.Anthropic()
    category = classify_task(client, user_message)
    result = execute_task(client, category, user_message)
    print(result)


if __name__ == "__main__":
    main()
