# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""
A setuptools based setup module.
See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from pathlib import Path
from setuptools import setup, find_packages
from VeraGridServer.__version__ import __VeraGridServer_VERSION__

description = 'VeraGrid is a Power Systems simulation program intended for professional use and research'


def read_long_description() -> str:
    src_root = Path(__file__).resolve().parent

    for candidate in (
        src_root / 'README.md',
        src_root.parent / 'README.md',
        src_root.parent.parent / 'README.md',
    ):
        if candidate.exists():
            return candidate.read_text(encoding='utf-8')

    return description


long_description = read_long_description()

pkgs_to_exclude = ['docs', 'research', 'tests', 'tutorials', 'VeraGridEngine']

packages = find_packages(exclude=pkgs_to_exclude)

# ... so we have to do the filtering ourselves
packages2 = list()
for package in packages:
    elms = package.split('.')
    excluded = False
    for exclude in pkgs_to_exclude:
        if exclude in elms:
            excluded = True

    if not excluded:
        packages2.append(package)

package_data = {'VeraGridServer': ['*.md',
                                  '*.rst',
                                  'LICENSE.txt',
                                  'setup.py',
                                  'data/VeraGrid_icon.ico'],
                }

dependencies = ["numpy>=2.2.0,<3",
                "fastapi>=0.109.1",
                "uvicorn>=0.11.7",
                "h11>=0.16.0",
                "requests>=2.33.0",
                "websockets>=9.1",
                "cryptography>=46.0.7",
                "psycopg[binary]>=3.3.4",
                "VeraGridEngine==" + __VeraGridServer_VERSION__,  # the VeraGridEngine version must be exactly the same
                ]

extras_require = {
    'gch5 files': ["tables"]  # this is for h5 compatibility
}
# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.

setup(
    name='VeraGridServer',  # Required
    version=__VeraGridServer_VERSION__,  # Required
    license='MPL2',
    description=description,  # Optional
    long_description=long_description,  # Optional
    long_description_content_type='text/markdown',  # Optional (see note above)
    url='https://github.com/SanPen/VeraGrid',  # Optional
    author='Santiago Peñate Vera et. Al.',  # Optional
    author_email='spenate@eroots.tech',  # Optional
    classifiers=[
        'Programming Language :: Python :: 3.10',
    ],
    keywords='power systems planning',  # Optional
    packages=packages2,  # Required
    include_package_data=True,
    python_requires='>=3.10',
    install_requires=dependencies,
    extras_require=extras_require,
    package_data=package_data,
    entry_points={
        'console_scripts': [
            'veragridserver = VeraGridServer.run:start_server',
        ],
    },
)
