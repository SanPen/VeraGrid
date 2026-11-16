# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""The packages contain no file or folder name that Windows cannot create, so the tree checks out on every platform."""

from __future__ import annotations

from importlib.resources.abc import Traversable
from pathlib import Path
from typing import List, Tuple

import pytest

from VeraGridEngine.IO.fmu.Elements.inspection import FmuArchiveInspectionPolicy, _portable_entry_name


def _is_portable_path(path: str) -> bool:
    """
    Return whether every component of a relative path can be created on Windows.

    The rule is the FMU inspector's portable-entry check: no reserved device stem (text before the first dot), no
    trailing dot or space, no reserved or control character.

    :param path: Slash-separated relative path.
    :return: True when the path is portable.
    """
    portable: bool = True
    try:
        _portable_entry_name(path, FmuArchiveInspectionPolicy())
    except ValueError:
        portable = False
    return portable


def _non_portable_entries(root: Traversable, label: str) -> List[str]:
    """
    List every entry below a package resource root whose name is not portable.

    :param root: Package resource root.
    :param label: Package name used to label the reported entries.
    :return: Sorted labels of the non-portable entries.
    """
    found: List[str] = list()
    pending: List[Tuple[Traversable, str]] = list(((root, label),))
    while len(pending) > 0:
        node: Traversable
        node_label: str
        node, node_label = pending.pop()
        child: Traversable
        for child in node.iterdir():
            if child.name == '__pycache__':
                pass
            else:
                child_label: str = node_label + "/" + child.name
                if not _is_portable_path(child_label):
                    found.append(child_label)
                else:
                    pass
                if child.is_dir():
                    pending.append((child, child_label))
                else:
                    pass
    return sorted(found)


@pytest.mark.parametrize("package", ("VeraGridEngine", "VeraGrid", "VeraGridMcp", "VeraGridServer", "VeraGridWeb", "tests"))
def test_packages_have_portable_entry_names(package: str) -> None:
    """
    Every file and folder name in the package can be created on Windows.

    :param package: Importable package name.
    :return: None.
    """
    package_root: Path = Path(__file__).resolve().parents[2] / package
    assert _non_portable_entries(package_root, package) == list()


def test_portable_path_rule_reports_the_former_contingency_modules() -> None:
    """
    The rule reports the five former PSS/E contingency modules and other non-portable names, and accepts their replacements.

    :return: None.
    """
    folder: str = "src/VeraGridEngine/IO/raw/versioned/"
    former: List[str] = list(folder + version + "/con.py" for version in ("base", "v33", "v34", "v35", "v36"))
    rejected: List[str] = list(("src/VeraGridEngine/IO/raw/CON.TXT.bak", "src/a/trailing./b.py", "src/a/b<c.py"))
    accepted: List[str] = list(("src/VeraGridEngine/IO/raw/con_parser.py", folder + "v35/contingency.py"))
    reported: List[str] = list()
    path: str
    for path in former + rejected + accepted:
        if _is_portable_path(path):
            pass
        else:
            reported.append(path)
    assert reported == former + rejected
