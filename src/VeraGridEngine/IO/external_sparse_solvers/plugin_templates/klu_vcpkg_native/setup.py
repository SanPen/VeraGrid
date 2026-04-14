from __future__ import annotations

from pathlib import Path

from setuptools import Extension, setup


def get_vcpkg_root() -> Path:
    """
    Return the default vcpkg install root used by the native KLU plugin build.

    :return: vcpkg install root.
    :rtype: Path
    """
    return Path.home() / ".VeraGrid" / "external_native" / "vcpkg" / "installed" / "x64-windows"


plugin_root: Path = Path(__file__).resolve().parent
vcpkg_root: Path = get_vcpkg_root()

extension = Extension(
    name="klu_native_backend",
    sources=["klu_native_backend.c"],
    include_dirs=[str(vcpkg_root / "include" / "suitesparse")],
    library_dirs=[str(vcpkg_root / "lib")],
    libraries=["klu", "amd", "colamd", "btf", "suitesparseconfig"],
)

setup(
    name="veragrid-klu-vcpkg-native",
    version="1.0",
    ext_modules=[extension],
)
