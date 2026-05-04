"""
Benchmark local Ollama models across context and prompt sizes.

This script assumes an Ollama server is already running. It does not start,
stop, or reconfigure Ollama; use ollama_bench_orchestrator.py for that.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_MODELS = ["qwen3.5:4b", "qwen3.5:9b", "qwen2.5:14b"]
DEFAULT_CONTEXTS = [4096, 8192, 16384, 32768, 65536]
DEFAULT_PROMPT_TARGETS = [512, 4096, 16000]

FIELDNAMES = [
    "timestamp",
    "profile",
    "model",
    "num_ctx",
    "target_prompt_tokens",
    "trial",
    "wall_sec",
    "total_duration_sec",
    "load_duration_sec",
    "prompt_eval_count",
    "prompt_eval_duration_sec",
    "prompt_tokens_per_sec",
    "eval_count",
    "eval_duration_sec",
    "eval_tokens_per_sec",
    "done_reason",
    "error",
]


def parse_csv_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_int_list(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def ns_to_sec(value: Any) -> float:
    return float(value or 0) / 1_000_000_000


def tokens_per_second(count: Any, duration_ns: Any) -> float:
    seconds = ns_to_sec(duration_ns)
    if not count or seconds <= 0:
        return 0.0
    return float(count) / seconds


def approx_token_text(target_tokens: int) -> str:
    block = """\
# File: benchmark_module.py

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple


@dataclass
class WindowState:
    handle: int
    title: str
    rect: Tuple[int, int, int, int]
    visible: bool = True


class WindowManager:
    def __init__(self) -> None:
        self.windows: Dict[int, WindowState] = {}
        self.history: List[Tuple[str, int]] = []

    def register_window(self, handle: int, title: str, rect: Tuple[int, int, int, int]) -> None:
        action = "update" if handle in self.windows else "create"
        self.history.append((action, handle))
        self.windows[handle] = WindowState(handle=handle, title=title, rect=rect)

    def find_by_title(self, query: str) -> List[WindowState]:
        query = query.lower()
        return [
            window
            for window in self.windows.values()
            if query in window.title.lower()
        ]

    def visible_windows(self) -> Iterable[WindowState]:
        return (window for window in self.windows.values() if window.visible)

    def restore_layout(self) -> None:
        for window in self.visible_windows():
            x, y, width, height = window.rect
            if width <= 0 or height <= 0:
                continue
            # Platform-specific placement would happen here.


def summarize_changes(old_state: dict, new_state: dict) -> list:
    changes = []
    for key, value in new_state.items():
        if old_state.get(key) != value:
            changes.append((key, old_state.get(key), value))
    return changes

"""
    repeats = max(1, (target_tokens * 4) // len(block))
    return block * repeats


def build_prompt(target_prompt_tokens: int) -> str:
    context = approx_token_text(target_prompt_tokens)
    return f"""\
You are benchmarking local LLM coding performance.

Analyze the following Python code context and answer with:
1. The likely bottlenecks.
2. One concrete refactor.
3. A short corrected code snippet.

Context:

{context}

Now provide the answer.
"""


def post_json(url: str, payload: dict[str, Any], timeout_sec: int) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_sec) as response:
        return json.loads(response.read().decode("utf-8"))


def completed_keys(output: Path) -> set[tuple[str, str, int, int, int]]:
    if not output.exists():
        return set()

    keys: set[tuple[str, str, int, int, int]] = set()
    with output.open("r", newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("error"):
                continue
            keys.add(
                (
                    row["profile"],
                    row["model"],
                    int(row["num_ctx"]),
                    int(row["target_prompt_tokens"]),
                    int(row["trial"]),
                )
            )
    return keys


def append_row(output: Path, row: dict[str, Any]) -> None:
    exists = output.exists()
    with output.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def run_one(
    base_url: str,
    profile: str,
    model: str,
    num_ctx: int,
    target_prompt_tokens: int,
    trial: int,
    max_tokens: int,
    temperature: float,
    keep_alive: str,
    timeout_sec: int,
    output: Path,
) -> None:
    payload = {
        "model": model,
        "prompt": build_prompt(target_prompt_tokens),
        "stream": False,
        "keep_alive": keep_alive,
        "options": {
            "num_ctx": num_ctx,
            "num_predict": max_tokens,
            "temperature": temperature,
        },
    }

    print(
        f"RUN profile={profile} model={model} "
        f"ctx={num_ctx} prompt~{target_prompt_tokens} trial={trial}",
        flush=True,
    )

    started = time.time()
    result: dict[str, Any] = {}
    error = ""

    try:
        result = post_json(f"{base_url.rstrip('/')}/api/generate", payload, timeout_sec)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        error = str(exc)

    wall_sec = time.time() - started
    row = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "profile": profile,
        "model": model,
        "num_ctx": num_ctx,
        "target_prompt_tokens": target_prompt_tokens,
        "trial": trial,
        "wall_sec": round(wall_sec, 3),
        "total_duration_sec": round(ns_to_sec(result.get("total_duration")), 3),
        "load_duration_sec": round(ns_to_sec(result.get("load_duration")), 3),
        "prompt_eval_count": result.get("prompt_eval_count", ""),
        "prompt_eval_duration_sec": round(ns_to_sec(result.get("prompt_eval_duration")), 3),
        "prompt_tokens_per_sec": round(
            tokens_per_second(result.get("prompt_eval_count"), result.get("prompt_eval_duration")),
            2,
        ),
        "eval_count": result.get("eval_count", ""),
        "eval_duration_sec": round(ns_to_sec(result.get("eval_duration")), 3),
        "eval_tokens_per_sec": round(
            tokens_per_second(result.get("eval_count"), result.get("eval_duration")),
            2,
        ),
        "done_reason": result.get("done_reason", ""),
        "error": error,
    }
    append_row(output, row)

    if error:
        print(f"  ERROR {error}", flush=True)
    else:
        print(
            f"  eval={row['eval_tokens_per_sec']} tok/s, "
            f"prompt={row['prompt_tokens_per_sec']} tok/s, wall={row['wall_sec']}s",
            flush=True,
        )


def write_summary(output: Path, summary_output: Path) -> None:
    if not output.exists():
        return

    grouped: dict[tuple[str, str, int, int], list[dict[str, str]]] = {}
    with output.open("r", newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("error"):
                continue
            key = (
                row["profile"],
                row["model"],
                int(row["num_ctx"]),
                int(row["target_prompt_tokens"]),
            )
            grouped.setdefault(key, []).append(row)

    fieldnames = [
        "profile",
        "model",
        "num_ctx",
        "target_prompt_tokens",
        "trials",
        "avg_eval_tokens_per_sec",
        "avg_prompt_tokens_per_sec",
        "avg_wall_sec",
    ]
    rows = []
    for key, values in grouped.items():
        profile, model, num_ctx, target_prompt_tokens = key
        rows.append(
            {
                "profile": profile,
                "model": model,
                "num_ctx": num_ctx,
                "target_prompt_tokens": target_prompt_tokens,
                "trials": len(values),
                "avg_eval_tokens_per_sec": round(
                    statistics.mean(float(row["eval_tokens_per_sec"]) for row in values),
                    2,
                ),
                "avg_prompt_tokens_per_sec": round(
                    statistics.mean(float(row["prompt_tokens_per_sec"]) for row in values),
                    2,
                ),
                "avg_wall_sec": round(statistics.mean(float(row["wall_sec"]) for row in values), 3),
            }
        )

    rows.sort(
        key=lambda row: (
            str(row["profile"]),
            str(row["model"]),
            int(row["num_ctx"]),
            int(row["target_prompt_tokens"]),
        )
    )

    with summary_output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_benchmark(args: argparse.Namespace) -> None:
    models = parse_csv_list(args.models)
    contexts = parse_int_list(args.contexts)
    prompt_targets = parse_int_list(args.prompt_targets)
    output = Path(args.output)
    done = completed_keys(output)

    for model in models:
        for num_ctx in contexts:
            for target_prompt_tokens in prompt_targets:
                if target_prompt_tokens >= num_ctx:
                    print(
                        f"SKIP profile={args.profile} model={model} "
                        f"ctx={num_ctx} prompt~{target_prompt_tokens} exceeds context",
                        flush=True,
                    )
                    continue

                for trial in range(1, args.trials + 1):
                    key = (args.profile, model, num_ctx, target_prompt_tokens, trial)
                    if key in done:
                        print(f"RESUME SKIP {key}", flush=True)
                        continue

                    run_one(
                        base_url=args.base_url,
                        profile=args.profile,
                        model=model,
                        num_ctx=num_ctx,
                        target_prompt_tokens=target_prompt_tokens,
                        trial=trial,
                        max_tokens=args.max_tokens,
                        temperature=args.temperature,
                        keep_alive=args.keep_alive,
                        timeout_sec=args.timeout_sec,
                        output=output,
                    )

    if args.summary_output:
        write_summary(output, Path(args.summary_output))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark a running Ollama server.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--profile", default="manual")
    parser.add_argument("--models", default=",".join(DEFAULT_MODELS))
    parser.add_argument("--contexts", default=",".join(str(item) for item in DEFAULT_CONTEXTS))
    parser.add_argument(
        "--prompt-targets",
        default=",".join(str(item) for item in DEFAULT_PROMPT_TARGETS),
    )
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--keep-alive", default="10m")
    parser.add_argument("--timeout-sec", type=int, default=1800)
    parser.add_argument("--output", default="ollama_bench_results.csv")
    parser.add_argument("--summary-output", default="")
    return parser


def main() -> None:
    run_benchmark(build_parser().parse_args())


if __name__ == "__main__":
    main()
