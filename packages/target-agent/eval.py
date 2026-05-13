#!/usr/bin/env python3
"""Eval harness for target-agent: format-aware graders, 3-tier test suite."""

import os
import re
import subprocess
import sys
from pathlib import Path

AGENT_DIR = Path(__file__).parent
AGENT_CMD = [sys.executable, str(AGENT_DIR / "agent.py")]

PREAMBLE_TOKENS = [
    "sure", "of course", "certainly", "great question",
    "absolutely", "happy to", "i'd be", "i would be",
]


def run_agent(prompt: str) -> str:
    result = subprocess.run(
        AGENT_CMD + [prompt],
        capture_output=True,
        text=True,
        cwd=str(AGENT_DIR),
        timeout=30,
        env=os.environ.copy(),
    )
    return result.stdout.strip()


def format_check(response: str, config: dict) -> dict:
    """
    Deterministic format-aware grader.

    Supported config keys:
      required_line_1_token  str   – keyword that must appear on first non-empty line
      max_line_count         int   – non-empty line count must be ≤ this value
      check_no_question      bool  – response must contain no '?'
      check_no_preamble      bool  – first line must not start with a preamble token
      disallowed_patterns    list  – regex patterns that must NOT appear in response
      required_patterns      list  – regex patterns that MUST appear in response
    """
    non_empty = [l for l in response.strip().split("\n") if l.strip()]
    first_line = non_empty[0] if non_empty else ""

    criteria: dict[str, bool] = {}
    passed = True

    if "required_line_1_token" in config:
        ok = config["required_line_1_token"].lower() in first_line.lower()
        criteria["required_line_1_token"] = ok
        passed = passed and ok

    if "max_line_count" in config:
        ok = len(non_empty) <= config["max_line_count"]
        criteria["max_line_count"] = ok
        passed = passed and ok

    if config.get("check_no_question", False):
        ok = "?" not in response
        criteria["check_no_question"] = ok
        passed = passed and ok

    if config.get("check_no_preamble", False):
        first_lower = first_line.strip().lower()
        ok = not any(first_lower.startswith(tok) for tok in PREAMBLE_TOKENS)
        criteria["check_no_preamble"] = ok
        passed = passed and ok

    for pattern in config.get("disallowed_patterns", []):
        ok = not bool(re.search(pattern, response, re.IGNORECASE | re.MULTILINE))
        criteria[f"disallowed:{pattern}"] = ok
        passed = passed and ok

    for pattern in config.get("required_patterns", []):
        ok = bool(re.search(pattern, response, re.IGNORECASE | re.MULTILINE))
        criteria[f"required:{pattern}"] = ok
        passed = passed and ok

    return {"pass": passed, "criteria": criteria}


# ---------------------------------------------------------------------------
# Test suite
# ---------------------------------------------------------------------------

TEST_CASES = [
    # ── Tier 1: Format compliance (terse single-line answers) ────────────────
    # Grader: keyword on line 1, ≤ 2 lines, no '?', no preamble token.
    {
        "tier": 1,
        "id": "T1-capital-france",
        "prompt": "What is the capital of France?",
        "grader": {
            "required_line_1_token": "Paris",
            "max_line_count": 2,
            "check_no_question": True,
            "check_no_preamble": True,
        },
    },
    {
        "tier": 1,
        "id": "T1-atomic-number-6",
        "prompt": "What element has atomic number 6?",
        "grader": {
            "required_line_1_token": "Carbon",
            "max_line_count": 2,
            "check_no_question": True,
            "check_no_preamble": True,
        },
    },
    {
        "tier": 1,
        "id": "T1-boiling-point-water",
        "prompt": "What is the boiling point of water in Celsius?",
        "grader": {
            "required_line_1_token": "100",
            "max_line_count": 2,
            "check_no_question": True,
            "check_no_preamble": True,
        },
    },
    {
        "tier": 1,
        "id": "T1-python-creator",
        "prompt": "Who created the Python programming language?",
        "grader": {
            "required_line_1_token": "Guido",
            "max_line_count": 2,
            "check_no_question": True,
            "check_no_preamble": True,
        },
    },
    # ── Tier 2: Behavioral regression / negative-example detection ───────────
    # Grader: response must NOT contain '?' or hedging/clarification phrases.
    {
        "tier": 2,
        "id": "T2-berlin-wall-year",
        "prompt": "Tell me the year the Berlin Wall fell.",
        "grader": {
            "check_no_question": True,
            "disallowed_patterns": [
                r"i'?m not sure",
                r"could you clarify",
                r"can you clarify",
                r"would you like",
                r"do you want",
                r"please clarify",
            ],
        },
    },
    {
        "tier": 2,
        "id": "T2-largest-planet",
        "prompt": "Name the largest planet in our solar system.",
        "grader": {
            "check_no_question": True,
            "disallowed_patterns": [
                r"i'?m not sure",
                r"could you clarify",
                r"can you clarify",
                r"would you like",
                r"do you want",
                r"please clarify",
            ],
        },
    },
    # ── Tier 3: Medium-complexity structured output ───────────────────────────
    # Grader: structural token (bullet/numbered list or code fence) + content.
    {
        "tier": 3,
        "id": "T3-first-5-primes",
        "prompt": "List the first 5 prime numbers.",
        "grader": {
            "required_patterns": [
                r"^\s*(?:[-*•]|\d+[.\)])\s",  # at least one list item
                r"\b2\b",
                r"\b3\b",
                r"\b5\b",
                r"\b7\b",
                r"\b11\b",
            ],
        },
    },
    {
        "tier": 3,
        "id": "T3-python-is-even",
        "prompt": (
            "Write a Python function named `is_even` that takes one integer "
            "argument and returns True if it is even, False otherwise."
        ),
        "grader": {
            "required_patterns": [
                r"```(?:python)?",           # code fence opened
                r"def\s+is_even\s*\(",       # correct function signature
                r"return\b",                 # contains a return statement
                r"%\s*2",                    # uses modulo-2 parity check
            ],
        },
    },
    {
        "tier": 3,
        "id": "T3-planets-ordered",
        "prompt": (
            "List the eight planets of the solar system in order from the Sun."
        ),
        "grader": {
            "required_patterns": [
                r"^\s*(?:[-*•]|\d+[.\)])\s",  # list structure
                r"Mercury",
                r"Venus",
                r"Earth",
                r"Mars",
                r"Jupiter",
                r"Saturn",
                r"Uranus",
                r"Neptune",
            ],
        },
    },
]


def run_eval() -> tuple[int, int]:
    results = []
    for tc in TEST_CASES:
        try:
            response = run_agent(tc["prompt"])
            grade = format_check(response, tc["grader"])
        except subprocess.TimeoutExpired:
            response = "<timeout>"
            grade = {"pass": False, "criteria": {"timeout": False}}
        except Exception as exc:
            response = f"<error: {exc}>"
            grade = {"pass": False, "criteria": {"error": str(exc)}}

        results.append(
            {
                "id": tc["id"],
                "tier": tc["tier"],
                "prompt": tc["prompt"],
                "response": response,
                "result": grade,
            }
        )

    total = len(results)
    passed = sum(1 for r in results if r["result"]["pass"])

    print(f"Eval: {passed}/{total} passed\n")
    print(f"{'ID':<35} {'Tier'} {'Status'}")
    print("-" * 60)
    for r in results:
        status = "PASS" if r["result"]["pass"] else "FAIL"
        print(f"{r['id']:<35} T{r['tier']}   {status}")

    # Failure details
    failures = [r for r in results if not r["result"]["pass"]]
    if failures:
        print()
        for r in failures:
            failed_criteria = [k for k, v in r["result"]["criteria"].items() if not v]
            print(f"FAIL [{r['id']}]")
            print(f"  prompt   : {r['prompt']}")
            print(f"  response : {r['response'][:300]!r}")
            print(f"  failed   : {failed_criteria}")

    return passed, total


if __name__ == "__main__":
    passed, total = run_eval()
    sys.exit(0 if passed == total else 1)
