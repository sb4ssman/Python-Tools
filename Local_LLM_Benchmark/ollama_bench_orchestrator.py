"""
Run ollama_bench.py across one or more Ollama launch profiles.

The benchmark worker measures models and contexts. This orchestrator only
restarts Ollama with profile-specific environment variables and invokes the
worker for each profile.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = "http://127.0.0.1:11434"

PROFILES: dict[str, dict[str, str | None]] = {
    "nvidia": {
        "CUDA_VISIBLE_DEVICES": "0",
        "OLLAMA_VISIBLE_DEVICES": "0",
        "OLLAMA_NO_GPU": None,
        "OLLAMA_VULKAN": None,
        "GGML_VK_VISIBLE_DEVICES": None,
    },
    "cpu": {
        "CUDA_VISIBLE_DEVICES": None,
        "OLLAMA_VISIBLE_DEVICES": None,
        "OLLAMA_NO_GPU": "1",
        "OLLAMA_VULKAN": None,
        "GGML_VK_VISIBLE_DEVICES": None,
    },
    "vulkan": {
        "CUDA_VISIBLE_DEVICES": None,
        "OLLAMA_VISIBLE_DEVICES": None,
        "OLLAMA_NO_GPU": None,
        "OLLAMA_VULKAN": "1",
        "GGML_VK_VISIBLE_DEVICES": None,
    },
}


def parse_csv_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def tags_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}/api/tags"


def is_ollama_ready(base_url: str) -> bool:
    try:
        with urllib.request.urlopen(tags_url(base_url), timeout=2) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def wait_for_ollama(proc: subprocess.Popen[Any], base_url: str, timeout_sec: int) -> None:
    started = time.time()
    while time.time() - started < timeout_sec:
        if proc.poll() is not None:
            raise RuntimeError(f"Ollama exited before becoming ready with code {proc.returncode}.")
        if is_ollama_ready(base_url):
            return
        time.sleep(1)
    raise TimeoutError(f"Ollama did not become ready at {base_url} within {timeout_sec}s.")


def kill_ollama() -> None:
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/IM", "ollama.exe", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        subprocess.run(
            ["pkill", "-f", "ollama serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    time.sleep(2)


def build_env(args: argparse.Namespace, profile: str) -> dict[str, str]:
    env = os.environ.copy()
    env["OLLAMA_HOST"] = args.ollama_host
    env["OLLAMA_DEBUG"] = "1" if args.debug else env.get("OLLAMA_DEBUG", "")
    env["OLLAMA_KEEP_ALIVE"] = args.keep_alive

    if args.ollama_models:
        env["OLLAMA_MODELS"] = args.ollama_models

    for key, value in PROFILES[profile].items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value

    return env


def start_ollama(args: argparse.Namespace, profile: str) -> subprocess.Popen[Any]:
    env = build_env(args, profile)
    log_path = Path(args.log_dir) / f"ollama_{profile}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_handle = log_path.open("a", encoding="utf-8")
    log_handle.write(f"\n\n=== START {profile} {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    log_handle.flush()

    proc = subprocess.Popen(
        [args.ollama_exe, "serve"],
        stdin=subprocess.DEVNULL,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        env=env,
        text=True,
    )
    proc._ollama_log_handle = log_handle  # type: ignore[attr-defined]
    wait_for_ollama(proc, args.base_url, args.startup_timeout_sec)
    return proc


def stop_ollama(proc: subprocess.Popen[Any] | None) -> None:
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=8)

    if proc and hasattr(proc, "_ollama_log_handle"):
        proc._ollama_log_handle.close()  # type: ignore[attr-defined]

    kill_ollama()


def run_benchmark_script(args: argparse.Namespace, profile: str) -> None:
    command = [
        sys.executable,
        str(Path(args.benchmark_script)),
        "--base-url",
        args.base_url,
        "--profile",
        profile,
        "--models",
        args.models,
        "--contexts",
        args.contexts,
        "--prompt-targets",
        args.prompt_targets,
        "--trials",
        str(args.trials),
        "--max-tokens",
        str(args.max_tokens),
        "--temperature",
        str(args.temperature),
        "--keep-alive",
        args.keep_alive,
        "--timeout-sec",
        str(args.request_timeout_sec),
        "--output",
        args.output,
    ]

    if args.summary_output:
        command.extend(["--summary-output", args.summary_output])

    print(f"BENCH profile={profile}", flush=True)
    subprocess.run(command, check=True)


def run(args: argparse.Namespace) -> None:
    profiles = parse_csv_list(args.profiles)
    invalid = [profile for profile in profiles if profile not in PROFILES]
    if invalid:
        raise ValueError(f"Unknown profiles: {invalid}. Valid profiles: {', '.join(PROFILES)}")

    proc: subprocess.Popen[Any] | None = None
    try:
        for profile in profiles:
            print(f"\n=== START PROFILE {profile} ===", flush=True)
            kill_ollama()
            proc = start_ollama(args, profile)
            run_benchmark_script(args, profile)
            stop_ollama(proc)
            proc = None
            print(f"=== END PROFILE {profile} ===", flush=True)
    finally:
        stop_ollama(proc)

    print(f"\nDone. Results: {Path(args.output).resolve()}", flush=True)
    if args.summary_output:
        print(f"Summary: {Path(args.summary_output).resolve()}", flush=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Orchestrate Ollama benchmark profiles.")
    parser.add_argument("--profiles", default="nvidia")
    parser.add_argument("--models", default="qwen3.5:4b,qwen3.5:9b,qwen2.5:14b")
    parser.add_argument("--contexts", default="4096,8192,16384,32768,65536")
    parser.add_argument("--prompt-targets", default="512,4096,16000")
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--keep-alive", default="10m")
    parser.add_argument("--output", default="ollama_bench_combined.csv")
    parser.add_argument("--summary-output", default="ollama_bench_summary.csv")
    parser.add_argument("--benchmark-script", default="ollama_bench.py")
    parser.add_argument("--ollama-exe", default="ollama")
    parser.add_argument("--ollama-models", default="")
    parser.add_argument("--ollama-host", default="127.0.0.1:11434")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--log-dir", default="ollama_bench_logs")
    parser.add_argument("--startup-timeout-sec", type=int, default=60)
    parser.add_argument("--request-timeout-sec", type=int, default=1800)
    parser.add_argument("--debug", action="store_true")
    return parser


def main() -> None:
    run(build_parser().parse_args())


if __name__ == "__main__":
    main()
