"""
Generate ASCII folder structure map for any project.
Excludes common development artifacts and focuses on source files.

=============================================================================
USAGE
=============================================================================
Place this script in your project's _claude_notes/claude_tools/ folder:

    [project]/
    └── _claude_notes/
        └── claude_tools/
            └── generate_folder_structure.py

Run with:
    python generate_folder_structure.py              # Default: scan current repo
    python generate_folder_structure.py --org        # Scan parent org (one level up)
    python generate_folder_structure.py --path C:/some/path  # Scan custom path

Or edit MODE below:
    MODE = "repo"      # Scan the repo containing this script
    MODE = "org"       # Scan parent org (one level up from repo)
    MODE = "custom"    # Use CUSTOM_PATH below
=============================================================================
"""

import sys
import io
import argparse
from pathlib import Path
from datetime import datetime

# ============================================================================
# OUTPUT NOTE
# Output always lands in <this_script>/../_claude_outputs/folder_structure.md
# — i.e. the _claude_notes/_claude_outputs/ folder of whichever project hosts
# this script. This is intentional: the tool lives in your notes folder and
# writes its results there. Even --path <external> writes output here, not to
# the target project.
# ============================================================================

# ============================================================================
# USER SETTINGS - Edit these values or use command-line arguments
# ============================================================================

# Mode: "repo" | "org" | "custom"
MODE = "repo"

# Custom path (used when MODE = "custom")
CUSTOM_PATH = ""
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
    parser = argparse.ArgumentParser(description="Generate folder structure map")
    parser.add_argument('--org', action='store_true', help='Scan parent organization (one level up from repo)')
    parser.add_argument('--path', type=str, help='Scan custom path')
    args = parser.parse_args()

    # Determine mode
    if args.path:
        mode = "custom"
        target = Path(args.path)
    elif args.org:
        mode = "org"
    else:
        mode = MODE

    # Resolve scan target and output directory.
    # Output always lands in _claude_notes/_claude_outputs/ next to this script —
    # see the OUTPUT NOTE at the top of the file.
    script_path = Path(__file__).resolve()
    output_dir = script_path.parent.parent / '_claude_outputs'

    if mode == "custom":
        title = f"{target.name} Folder Structure"
    elif mode == "org":
        # script -> claude_tools -> _claude_notes -> repo -> org
        target = script_path.parent.parent.parent.parent
        title = f"{target.name} Organization Structure"
    else:
        # Repo mode: script -> claude_tools -> _claude_notes -> repo
        target = script_path.parent.parent.parent
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
        "- Output always written to _claude_notes/_claude_outputs/ of the host project",
        "- Generated by: `generate_folder_structure.py`",
    ]

    output_file = output_dir / 'folder_structure.md'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))

    print(f"\nFolder map generated: {output_file}")
    print(f"Directories: {dir_count}, Files: {file_count}")
    print("\n" + "\n".join(output))


if __name__ == "__main__":
    main()
