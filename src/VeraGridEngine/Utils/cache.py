# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from os import PathLike
from pathlib import Path
from shutil import rmtree


def clean_pycache_folders(path: str | PathLike[str]) -> int:
    """
    Remove all ``__pycache__`` folders inside a path.

    :param path: Folder to clean, or one ``__pycache__`` folder to remove.
    :return: Number of removed ``__pycache__`` folders.
    """
    root_path: Path = Path(path)
    removed_count: int = 0

    # If the requested folder is itself a cache folder, delete only that tree.
    if root_path.is_dir():
        if root_path.name == "__pycache__":
            rmtree(root_path)
            removed_count = 1
        else:
            # Walk the tree and remove every Python bytecode cache folder found.
            pycache_path: Path
            for pycache_path in root_path.rglob("__pycache__"):
                if pycache_path.is_dir():
                    rmtree(pycache_path)
                    removed_count += 1
                else:
                    pass
    else:
        pass

    return removed_count
