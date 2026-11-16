# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Repository contracts required by the published Python packages."""

from pathlib import Path

from upload_to_pypi import SRC_ROOT, search_text_in_python_files
from veragrid_packaging import check_all_folders_contain_init_py


def test_published_package_release_checks() -> None:
    """Run the release-time source and package-layout checks during pytest.

    :return: None.
    """
    package_rules: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("VeraGrid", ("__pycache__", "icons", "svg")),
        ("VeraGridEngine", ("__pycache__", "data/fmu", "data/native_worker")),
        ("VeraGridServer", ("__pycache__",)),
        ("VeraGridMcp", ("__pycache__",)),
    )
    forbidden_text: list[str] = list()
    source_root: Path = Path(SRC_ROOT)
    package_rule: tuple[str, tuple[str, ...]]
    package_name: str
    exceptions: tuple[str, ...]

    # Keep the published code independent of development modules before building a release.
    forbidden_text.append("from trunk")
    forbidden_text.append("import trunk")
    forbidden_text.append("from tests")
    forbidden_text.append("from matplotlib")
    forbidden_text.append("import matplotlib")
    forbidden_text.append("import tests")
    for package_rule in package_rules:
        package_name = package_rule[0]
        search_text_in_python_files(
            directory=str(source_root / package_name),
            search_terms=forbidden_text,
        )

    # Reuse the package builder's exact initializer checks and resource exclusions.
    for package_rule in package_rules:
        package_name = package_rule[0]
        exceptions = package_rule[1]
        assert check_all_folders_contain_init_py(
            directory=str(source_root / package_name),
            exceptions=exceptions,
        )
