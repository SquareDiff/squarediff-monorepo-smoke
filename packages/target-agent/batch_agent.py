import sys
import json
import os
import time
import anthropic

SYSTEM_PROMPT = "Answer concisely. Provide only the final answer with no explanation, no preamble, and no hedging."
MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 128
POLL_INTERVAL = int(os.environ.get("BATCH_POLL_INTERVAL", "5"))
BATCH_TIMEOUT = int(os.environ.get("BATCH_TIMEOUT", "1800"))


def _message_params(content):
    return {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": content}],
    }


def run_sync(client, payload):
    """Single synchronous call — fallback for interactive/debug use."""
    msg = client.messages.create(**_message_params(payload))
    print(msg.content[0].text)


def run_batch(client, cases):
    """Submit all cases via Message Batches API for 50% cost reduction."""
    requests = [
        {"custom_id": f"case-{i}", "params": _message_params(case)}
        for i, case in enumerate(cases)
    ]

    batch = client.beta.messages.batches.create(requests=requests)
    batch_id = batch.id

    deadline = time.time() + BATCH_TIMEOUT
    while True:
        status = client.beta.messages.batches.retrieve(batch_id)
        if status.processing_status == "ended":
            break
        if time.time() >= deadline:
            # Timeout: fall back to synchronous for all cases
            results = [
                client.messages.create(**_message_params(case)).content[0].text
                for case in cases
            ]
            print(json.dumps(results))
            return
        time.sleep(POLL_INTERVAL)

    results = [None] * len(cases)
    for result in client.beta.messages.batches.results(batch_id):
        idx = int(result.custom_id.split("-", 1)[1])
        if result.result.type == "succeeded":
            results[idx] = result.result.message.content[0].text
        else:
            results[idx] = None

    print(json.dumps(results))


def main():
    args = sys.argv[1:]

    force_batch = os.environ.get("BATCH_MODE", "").lower() in ("1", "true", "yes")
    if "--batch" in args:
        force_batch = True
        args = [a for a in args if a != "--batch"]

    payload = args[0] if args else sys.stdin.read().strip()

    client = anthropic.Anthropic()

    # Auto-detect batch mode from JSON array input
    cases = None
    try:
        parsed = json.loads(payload)
        if isinstance(parsed, list):
            cases = parsed
    except (json.JSONDecodeError, ValueError):
        pass

    if cases is not None or force_batch:
        if cases is None:
            cases = [payload]
        run_batch(client, cases)
    else:
        run_sync(client, payload)


if __name__ == "__main__":
    main()
