# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""
Repository-root packaging shim.

The real distributable packages live under:
- src/VeraGrid
- src/VeraGridEngine
- src/VeraGridServer

Read the Docs installs doc/requirements.txt directly, so the repository root
must not advertise a stale runtime dependency set.
"""

from pathlib import Path

from setuptools import setup

from src.VeraGrid.__version__ import __VeraGrid_VERSION__


ROOT = Path(__file__).resolve().parent


setup(
    name="VeraGrid-doc-meta",
    version=__VeraGrid_VERSION__,
    description="Repository metadata shim for VeraGrid documentation builds",
    long_description=(ROOT / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    url="https://github.com/SanPen/VeraGrid",
    author="Santiago Penate Vera et. al.",
    license="MPL-2.0",
    python_requires=">=3.8",
    packages=[],
    py_modules=[],
)
