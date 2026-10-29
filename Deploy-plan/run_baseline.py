#!/usr/bin/env python3
"""Run a small, repeatable thesis-oriented baseline against a local Ollama API."""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS_PATH = ROOT / "experiments" / "baseline_questions.json"
OUTPUT_DIR = ROOT / "results" / "baseline"
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:1.7b")
SYSTEM = (
    "You are assisting with a master's thesis on pairwise choice models, including "
    "Bradley-Terry and context-dependent models. Answer the question directly and "
    "show reasoning or calculations when requested. Separate general theory from "
    "claims about the user's experiments. Do not invent papers, citations, results, "
    "or access to files that were not provided. Prefer a clear answer under 180 words."
)


def call_ollama(question: str) -> tuple[dict, float]:
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": question},
        ],
        "stream": False,
        "options": {"temperature": 0},
    }
    request = Request(
        f"{OLLAMA_URL}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    with urlopen(request, timeout=600) as response:
        result = json.loads(response.read())
    wall_seconds = time.perf_counter() - started
    return result, wall_seconds


def rate_per_second(count: int | None, duration_ns: int | None) -> float | None:
    if not count or not duration_ns:
        return None
    return count / (duration_ns / 1_000_000_000)


def main() -> int:
    try:
        questions = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
        # Fail early if Ollama is unreachable or the model tag is wrong.
        with urlopen(f"{OLLAMA_URL}/api/tags", timeout=5) as response:
            installed = json.loads(response.read()).get("models", [])
    except (OSError, ValueError, HTTPError, URLError) as exc:
        print(f"Cannot reach Ollama at {OLLAMA_URL}: {exc}", file=sys.stderr)
        print("Start Ollama and confirm the model with: ollama list", file=sys.stderr)
        return 1

    installed_names = {item.get("name", "") for item in installed}
    if MODEL not in installed_names:
        print(f"Model '{MODEL}' is not installed. Installed: {', '.join(sorted(installed_names)) or '(none)'}", file=sys.stderr)
        print(f"Pull it with: ollama pull {MODEL}", file=sys.stderr)
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    run = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "model": MODEL,
        "ollama_url": OLLAMA_URL,
        "temperature": 0,
        "system_prompt": SYSTEM,
        "items": [],
    }

    print(f"Baseline run: {MODEL} | {len(questions)} questions")
    for number, item in enumerate(questions, start=1):
        print(f"\n[{number}/{len(questions)}] {item['id']}")
        try:
            result, wall_seconds = call_ollama(item["question"])
        except (OSError, ValueError, HTTPError, URLError) as exc:
            print(f"Request failed: {exc}", file=sys.stderr)
            return 1
        answer = result.get("message", {}).get("content", "")
        metrics = {
            "wall_seconds": round(wall_seconds, 3),
            "prompt_tokens": result.get("prompt_eval_count"),
            "prompt_tokens_per_second": rate_per_second(
                result.get("prompt_eval_count"), result.get("prompt_eval_duration")
            ),
            "generated_tokens": result.get("eval_count"),
            "generated_tokens_per_second": rate_per_second(
                result.get("eval_count"), result.get("eval_duration")
            ),
            "load_seconds": (result.get("load_duration") or 0) / 1_000_000_000,
        }
        run["items"].append({
            "id": item["id"],
            "question": item["question"],
            "answer": answer,
            "metrics": metrics,
            "manual_review": {"correctness_0_to_2": None, "clarity_0_to_2": None, "honesty_0_to_2": None, "notes": ""},
        })
        print(answer)
        print(
            "Metrics: "
            f"wall={metrics['wall_seconds']}s, "
            f"prompt={metrics['prompt_tokens_per_second'] or 0:.2f} tok/s, "
            f"generation={metrics['generated_tokens_per_second'] or 0:.2f} tok/s, "
            f"load={metrics['load_seconds']:.2f}s"
        )

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path = OUTPUT_DIR / f"qwen3-1.7b-{stamp}.json"
    output_path.write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nSaved answers and timing metadata to: {output_path}")
    print("Review each answer manually; this run does not automatically certify correctness.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
