import os
import sys
import time

import anthropic

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 128


def make_client():
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def run_single(task: str) -> None:
    client = make_client()
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": task}],
    )
    print(response.content[0].text)


def run_batch(input_file: str) -> None:
    with open(input_file) as f:
        tasks = [line.rstrip("\n") for line in f if line.strip()]

    if not tasks:
        return

    client = make_client()

    batch_requests = [
        {
            "custom_id": f"case-{i}",
            "params": {
                "model": MODEL,
                "max_tokens": MAX_TOKENS,
                "messages": [{"role": "user", "content": task}],
            },
        }
        for i, task in enumerate(tasks)
    ]

    batch = client.beta.messages.batches.create(requests=batch_requests)
    batch_id = batch.id

    # Poll with exponential backoff until processing_status == "ended"
    delay = 1
    elapsed = 0
    max_wait = 30 * 60  # 30 minutes per Batches API SLA
    while True:
        status = client.beta.messages.batches.retrieve(batch_id)
        if status.processing_status == "ended":
            break
        if elapsed >= max_wait:
            raise TimeoutError(
                f"Batch {batch_id} did not complete within {max_wait}s"
            )
        time.sleep(delay)
        elapsed += delay
        delay = min(delay * 2, 60)

    # Collect results keyed by custom_id
    results: dict[str, str] = {}
    for result in client.beta.messages.batches.results(batch_id):
        if result.result.type == "succeeded":
            results[result.custom_id] = result.result.message.content[0].text
        else:
            sys.stderr.write(
                f"batch case {result.custom_id} errored: {result.result.type}\n"
            )
            results[result.custom_id] = ""

    # Emit one line per task in original order
    for i in range(len(tasks)):
        print(results.get(f"case-{i}", ""))


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--batch-input":
        run_batch(sys.argv[2])
    elif len(sys.argv) >= 2:
        run_single(sys.argv[1])
    else:
        run_single(sys.stdin.read().strip())
