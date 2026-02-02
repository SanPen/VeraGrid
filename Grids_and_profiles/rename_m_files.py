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


if __name__ == "__main__":
    # Change this to your target directory
    TARGET_DIR = "./grids"

    rename_m_to_matpower(TARGET_DIR)