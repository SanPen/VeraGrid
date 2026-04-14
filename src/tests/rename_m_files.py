import os
from pathlib import Path


def rename_m_to_matpower(root_dir: str) -> None:
    root = Path(root_dir)

    if not root.is_dir():
        raise ValueError(f"{root_dir} is not a valid directory")

    for path in root.rglob("*.m"):
        new_path = path.with_suffix(".matpower")

        if new_path.exists():
            print(f"Skipping (already exists): {new_path}")
            continue

        path.rename(new_path)
        print(f"Renamed: {path} -> {new_path}")


import re
from pathlib import Path


# Matches .m only when it looks like a filename
M_FILE_PATTERN = re.compile(
    r'(?P<name>[A-Za-z0-9_\-/\\.]+)\.m(?=["\'\s,\)\]])'
)


def update_m_references(root_dir: str, dry_run: bool = True) -> None:
    root = Path(root_dir)

    if not root.is_dir():
        raise ValueError(f"{root_dir} is not a valid directory")

    for py_file in root.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        updated = M_FILE_PATTERN.sub(r"\g<name>.matpower", text)

        if updated != text:
            if dry_run:
                print(f"[DRY-RUN] Would update: {py_file}")
            else:
                py_file.write_text(updated, encoding="utf-8")
                print(f"Updated: {py_file}")


if __name__ == "__main__":
    # Change this to your target directory
    TARGET_DIR = "."

    rename_m_to_matpower(TARGET_DIR)

    # Change to False once you verify the dry run
    update_m_references(TARGET_DIR, dry_run=False)