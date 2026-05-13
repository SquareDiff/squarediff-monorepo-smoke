import sys
import anthropic
import opentelemetry.trace as trace
from opentelemetry.trace import ProxyTracerProvider
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

if isinstance(trace.get_tracer_provider(), ProxyTracerProvider):
    _provider = TracerProvider()
    _provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(_provider)

SYSTEM_PROMPT = (
    "You are a helpful and accurate assistant. "
    "Answer the user's question directly and concisely. "
    "State your answer on the first line without preamble, filler, or conversational framing. "
    "If the question has a specific factual answer, give it. "
    "If it requires reasoning, reason briefly then state your conclusion. "
    "When asked to list multiple items, format them as a numbered list (1. item) or bulleted list (- item), one item per line."
)


def extract_text(response):
    parts = [block.text for block in response.content if block.type == "text"]
    return " ".join(parts).strip()


if __name__ == "__main__":
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": sys.argv[1]}],
    )
    print(extract_text(response) or "I could not determine the answer.")
