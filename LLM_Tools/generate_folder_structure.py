"""
LLM_Tools folder map generator.

What it does
  Builds a Markdown tree for a repository, organization/workspace folder, or
  explicit path. The output is meant for humans and LLM agents that need a
  quick project inventory without cache folders, virtual environments, build
  outputs, or other noisy development artifacts.

Default behavior
  From this public PythonTools repo, the script assumes this layout:

      PythonTools/
      |-- LLM_Tools/
      |   |-- generate_folder_structure.py
      |   `-- Data/
      `-- README.md

  Repo mode scans the PythonTools repository root.
  Org mode scans the parent folder above PythonTools.
  Custom mode scans the path supplied with --path.
  Output defaults to LLM_Tools/Data/folder_structure.md.

Usage
  python LLM_Tools/generate_folder_structure.py
  python LLM_Tools/generate_folder_structure.py --org
  python LLM_Tools/generate_folder_structure.py --path /some/project
  python LLM_Tools/generate_folder_structure.py --path C:/some/project --out map.md

Notes for agents
  This tool is intentionally generic. It no longer depends on, writes to, or
  assumes a Claude-specific notes folder. Use --out when a calling project
  wants the generated map somewhere else.
"""

import sys
import io
import argparse
from pathlib import Path
from datetime import datetime

# ============================================================================
# USER SETTINGS - Edit these values or use command-line arguments
# ============================================================================

# Mode: "repo" | "org" | "custom"
MODE = "repo"

# Custom path (used when MODE = "custom")
CUSTOM_PATH = ""

# Default output path, relative to this script's directory.
DEFAULT_OUTPUT = "Data/folder_structure.md"
# ============================================================================

# Directories excluded everywhere in the tree regardless of depth.
# These are always-junk: caches, VCS internals, dependency installs, tooling.
EXCLUDE_ALWAYS = {
    '__pycache__',
    '.git',
    '.vscode',
    '.idea',
    'venv',
    '.venv',
    'env',
    'node_modules',
    '.mypy_cache',
    '.pytest_cache',
    '.tox',
    'htmlcov',
    '.claude',
}

# Directories excluded only when they appear as a direct child of the scan
# target. The same name nested deeper is kept — e.g. mylib/lib/ stays visible
# while a top-level /build/ or /dist/ is hidden.
EXCLUDE_ROOT_ONLY = {
    'dist',
    'build',
    'eggs',
    '.eggs',
    'lib',
    'lib64',
    'parts',
    'sdist',
    'var',
    'wheels',
    'logs',
}

# File extensions to exclude
EXCLUDE_EXTENSIONS = {
    '.pyc',
    '.pyo',
    '.pyd',
    '.so',
    '.dll',
    '.dylib',
    '.log',
    '.pid',
    '.egg-info',
    '.coverage',
    '.cache'
}

# Files to exclude
EXCLUDE_FILES = {
    '.DS_Store',
    'Thumbs.db',
    'desktop.ini',
    '.gitignore'
}


def should_include(path: Path, scan_root: Path) -> bool:
    """Check if a path should be included in the tree.

    Directories named in EXCLUDE_ALWAYS are dropped at any depth.
    Directories named in EXCLUDE_ROOT_ONLY are dropped only when they are
    immediate children of scan_root (e.g. top-level /build/ is hidden but
    mypackage/build/ is kept).
    """
    if path.is_dir():
        if path.name in EXCLUDE_ALWAYS:
            return False
        if path.name in EXCLUDE_ROOT_ONLY and path.parent == scan_root:
            return False

    if path.is_file():
        if path.suffix in EXCLUDE_EXTENSIONS:
            return False
        if path.name in EXCLUDE_FILES:
            return False

    return True


def generate_tree(directory: Path, scan_root: Path, prefix: str = "") -> list:
    """Generate ASCII tree structure recursively."""
    lines = []

    try:
        items = sorted(
            [p for p in directory.iterdir() if should_include(p, scan_root)],
            key=lambda x: (not x.is_dir(), x.name.lower())
        )

        for i, item in enumerate(items):
            is_last_item = i == len(items) - 1
            connector = "└── " if is_last_item else "├── "
            extension = "    " if is_last_item else "│   "

            name = f"📁 {item.name}/" if item.is_dir() else item.name
            lines.append(f"{prefix}{connector}{name}")

            if item.is_dir():
                lines.extend(generate_tree(item, scan_root, prefix + extension))

    except PermissionError:
        pass

    return lines


def count_files_and_dirs(directory: Path, scan_root: Path) -> tuple:
    """Count included files and directories recursively.

    Walks manually (not rglob) so that excluded directories are pruned before
    descending into them — keeping the count consistent with the tree output.
    """
    file_count = 0
    dir_count = 0

    try:
        for item in directory.iterdir():
            if not should_include(item, scan_root):
                continue
            if item.is_file():
                file_count += 1
            elif item.is_dir():
                dir_count += 1
                sub_files, sub_dirs = count_files_and_dirs(item, scan_root)
                file_count += sub_files
                dir_count += sub_dirs
    except PermissionError:
        pass

    return file_count, dir_count


def main():
    # UTF-8 stdout for emoji support on Windows — done here, not at import time,
    # so importing this module never silently hijacks another process's stdout.
    if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Generate a Markdown folder structure map")
    parser.add_argument('--org', action='store_true', help='Scan parent organization (one level up from repo)')
    parser.add_argument('--path', type=str, help='Scan custom path')
    parser.add_argument('--out', type=str, help='Output Markdown file path')
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    tool_dir = script_path.parent
    repo_root = tool_dir.parent

    # Determine mode
    target = None
    if args.path:
        mode = "custom"
        target = Path(args.path)
    elif args.org:
        mode = "org"
    else:
        mode = MODE

    output_file = Path(args.out).expanduser() if args.out else tool_dir / DEFAULT_OUTPUT
    if not output_file.is_absolute():
        output_file = Path.cwd() / output_file

    if mode == "custom":
        if target is None:
            target = Path(CUSTOM_PATH)
        if not str(target):
            raise SystemExit("Custom mode requires --path or a CUSTOM_PATH value.")
        title = f"{target.name} Folder Structure"
    elif mode == "org":
        target = repo_root.parent
        title = f"{target.name} Organization Structure"
    else:
        target = repo_root
        title = f"{target.name} Folder Structure"

    scan_root = target.resolve()

    print(f"Scanning {scan_root}...")
    tree_lines = [f"📁 {scan_root.name}/"]
    tree_lines.extend(generate_tree(scan_root, scan_root))

    file_count, dir_count = count_files_and_dirs(scan_root, scan_root)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    output = [
        f"# {title}",
        "",
        f"**Generated**: {timestamp}",
        f"**Mode**: {mode}",
        f"**Total Directories**: {dir_count}",
        f"**Total Files**: {file_count}",
        "",
        "```",
        *tree_lines,
        "```",
        "",
        "---",
        "",
        "## Notes",
        "- Excludes (always): __pycache__, .git, .venv, node_modules, and other dev artifacts",
        "- Excludes (root-only): dist, build, lib, var, logs, and other top-level build outputs",
        f"- Output written to: {output_file}",
        "- Generated by: `generate_folder_structure.py`",
    ]

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))

    print(f"\nFolder map generated: {output_file}")
    print(f"Directories: {dir_count}, Files: {file_count}")
    print("\n" + "\n".join(output))


if __name__ == "__main__":
    main()
