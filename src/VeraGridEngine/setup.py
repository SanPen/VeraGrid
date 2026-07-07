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
import ast
from pathlib import Path
from setuptools import setup, find_packages

description = 'VeraGrid is a Power Systems simulation program intended for professional use and research'


def read_module_constant(constant_name: str) -> str:
    src_root = Path(__file__).resolve().parent

    for candidate in (
        src_root / '__version__.py',
        src_root / 'VeraGridEngine' / '__version__.py',
    ):
        if candidate.exists():
            module_ast = ast.parse(candidate.read_text(encoding='utf-8'), filename=str(candidate))

            for node in module_ast.body:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == constant_name:
                            return str(ast.literal_eval(node.value))
        else:
            pass

    raise FileNotFoundError(f'{constant_name} source file not found next to setup.py or in VeraGridEngine/')


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
__VeraGridEngine_VERSION__ = read_module_constant('__VeraGridEngine_VERSION__')

pkgs_to_exclude = ['docs', 'research', 'tests', 'tutorials', 'VeraGrid']

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

package_data = {'VeraGridEngine': ['LICENSE.txt', 'setup.py'], }

dependencies = ["numpy>=2.2.0",
                "autograd>=1.7.0",
                "scipy>=1.10.0",
                "networkx>=3.6.1",
                "pandas>=2.2.3",
                "highspy>=1.8.0",
                "xlwt>=1.3.0",
                "xlrd>=2.0.2",
                "matplotlib>=3.10.0",
                "openpyxl>=3.1.5",
                "chardet>=5.2.0",  # for the psse files character detection
                "scikit-learn>=1.5.0",
                "geopy>=2.4.1",
                "h5py>=3.12.0",
                "numba>=0.61",  # to compile routines natively
                "pyproj>=3.7.2",
                "pulp>=3.3.0",
                "pyarrow>=23.0.1",
                "windpowerlib>=0.2.2",
                "pvlib>=0.14.0",
                "rdflib>=7.5.0",
                "pymoo>=0.6",
                "websockets>=9.1",
                "brotli>=1.2.0",
                "opencv-python>=4.10.0.84",
                "fmpy>=0.3.22"
                ]

extras_require = {
    'gch5 files': ["tables"]  # this is for h5 compatibility
}
# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.

setup(
    name='VeraGridEngine',  # Required
    version=__VeraGridEngine_VERSION__,  # Required
    license='MPL2',
    description=description,  # Optional
    long_description=long_description,  # Optional
    long_description_content_type='text/markdown',  # Optional (see note above)
    url='https://github.com/SanPen/VeraGrid',  # Optional
    author='Santiago Peñate Vera et. Al.',  # Optional
    author_email='spenate@eroots.tech',  # Optional
    classifiers=[
        'Programming Language :: Python :: 3.8',
    ],
    keywords='power systems planning',  # Optional
    packages=packages2,  # Required
    package_dir={'': '.'},
    include_package_data=True,
    python_requires='>=3.8',
    install_requires=dependencies,
    extras_require=extras_require,
    package_data=package_data,
)
