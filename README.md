# PythonTools

Public drawer for small Python utilities, diagnostics, experiments, and script
templates.

This is not a single polished application. It is a lightweight collection of
tools that are useful enough to keep public, but not necessarily large enough
to deserve their own repository.

Some tools that started here have graduated:

- `ArchiveUpdater` moved to `gitSpecOps`.
- `github-org-duplicator` lives in `gitSpecOps`.
- `PixelViewer` moved into `DesktopOpener`.

---

## LLM_Tools

Utilities for local LLM work, hardware context, and agent-friendly reporting.

### `generate_folder_structure.py`

Generates a Markdown folder tree for a target project. Excludes common
development artifacts such as `.git`, `.venv`, `__pycache__`, and build
outputs.

```powershell
python LLM_Tools\generate_folder_structure.py --path T:\Github\MyProject
python LLM_Tools\generate_folder_structure.py --org
```

Generated maps are written to `_claude_outputs/folder_structure.md`, which is
kept local and ignored by Git.

### `hardware_detector.py`

Detects hardware and formats output for humans, compact LLM context, or verbose
debugging.

```powershell
python LLM_Tools\hardware_detector.py
python LLM_Tools\hardware_detector.py --mode llm
python LLM_Tools\hardware_detector.py --mode verbose --save
```

No required third-party dependency. Uses `psutil` opportunistically if it is
installed.

### `sensor_monitor.py`

Reads live hardware sensor data from existing monitor streams when available:
HWiNFO64 shared memory, MSI Afterburner shared memory, LibreHardwareMonitor or
OpenHardwareMonitor WMI, `nvidia-smi`, and Windows thermal fallbacks.

```powershell
python LLM_Tools\sensor_monitor.py
python LLM_Tools\sensor_monitor.py --mode llm
python LLM_Tools\sensor_monitor.py --stream --out sensors.jsonl
```

Standard-library Python. Best results require one of the external sensor tools
above to already be running.

### `Local_Benchmark`

Ollama benchmark scripts for comparing local models across context sizes,
prompt sizes, and launch profiles.

```powershell
python LLM_Tools\Local_Benchmark\ollama_bench.py --models qwen3.5:4b,qwen2.5:14b --contexts 4096,16384
python LLM_Tools\Local_Benchmark\ollama_bench_orchestrator.py --profiles nvidia,cpu
```

The worker expects an Ollama server to already be running. The orchestrator can
restart Ollama with profile-specific environment variables.

---

## Explorations

Small standalone explorations that are polished enough to keep around, but are
not general utilities yet.

### `collatz.py`

Interactive Collatz conjecture explorer. Plots one or more sequences on a
zoomable, log-scale tkinter canvas with animation and an interactive legend.

```powershell
python Explorations\collatz.py
```

Uses only the Python standard library.

---

## Scraps

Scratch scripts, templates, old experiments, and one-off probes. These are kept
for reference and future salvage, not presented as stable public tools.

Several scripts in this folder have extra dependencies such as `pandas`,
`pyautogui`, `PyQt5`, `pyvda`, `pygetwindow`, or `screeninfo`.

---

## Dependency Notes

The repo does not currently define one authoritative environment for every
script. Treat each folder as a small tool area:

- Most `LLM_Tools` scripts use only the standard library.
- `hardware_detector.py` can use `psutil` when available.
- `Local_Benchmark` uses standard-library Python but requires Ollama for real
  benchmark runs.
- `Scraps` contains mixed experiments with mixed dependencies.

For this reason, this repo does not currently ship one root dependency file.

---

## Folder Map

Regenerate the repository map with:

```powershell
python LLM_Tools\generate_folder_structure.py --path T:\Github\sb4ssman\PythonTools
```

Local output:

```text
_claude_outputs\folder_structure.md
```
