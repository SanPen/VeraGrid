# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""
A setuptools based setup module.
"""

from pathlib import Path
from setuptools import setup, find_packages
from VeraGridMcp.__version__ import __VeraGridMcp_VERSION__

description = 'VeraGrid MCP server integration'


def read_long_description() -> str:
    """
    Read the package long description from the nearest README.

    :returns: Package long description.
    """
    src_root: Path = Path(__file__).resolve().parent

    for candidate in (
        src_root / 'README.md',
        src_root.parent / 'README.md',
        src_root.parent.parent / 'README.md',
    ):
        if candidate.exists():
            return candidate.read_text(encoding='utf-8')
        else:
            pass

    return description


long_description: str = read_long_description()

packages: list[str] = find_packages(include=['VeraGridMcp', 'VeraGridMcp.*'])

package_data: dict[str, list[str]] = {
    'VeraGridMcp': ['LICENSE.txt', 'setup.py'],
    'VeraGridMcp.knowledge': ['*.md'],
}

dependencies: list[str] = [
    "VeraGridEngine==" + __VeraGridMcp_VERSION__,
    "mcp>=2.2.0,<3",
]


setup(
    name='VeraGridMcp',
    version=__VeraGridMcp_VERSION__,
    license='MPL2',
    description=description,
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/SanPen/VeraGrid',
    author='Santiago Penate Vera et. Al.',
    author_email='spenate@eroots.tech',
    classifiers=[
        'Programming Language :: Python :: 3.10',
    ],
    keywords='power systems mcp',
    packages=packages,
    include_package_data=True,
    python_requires='>=3.10',
    install_requires=dependencies,
    package_data=package_data,
    entry_points={
        'console_scripts': [
            'veragridmcp = VeraGridMcp.cli:main',
            'veragridmcp-server = VeraGridMcp.mcp_server:run_server',
            'veragridmcp-register = VeraGridMcp.cli:main',
        ],
    },
)
