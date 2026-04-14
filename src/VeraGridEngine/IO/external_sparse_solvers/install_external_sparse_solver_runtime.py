from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def get_default_runtime_root() -> Path:
    """
    Return the default root directory for external sparse-solver Python runtimes.

    :return: Default runtime-root directory.
    :rtype: Path
    """
    return Path.home() / ".VeraGrid" / "external_python_packages"


def build_plugin_runtime_directory(plugin_name: str, destination_root: str) -> Path:
    """
    Build the runtime installation directory for one plugin.

    :param plugin_name: Plugin name.
    :type plugin_name: str
    :param destination_root: Optional destination-root override.
    :type destination_root: str
    :return: Runtime installation directory.
    :rtype: Path
    """
    root_directory: Path

    if len(destination_root) > 0:
        root_directory = Path(destination_root)
    else:
        root_directory = get_default_runtime_root()

    root_directory.mkdir(parents=True, exist_ok=True)
    runtime_directory: Path = root_directory / plugin_name
    runtime_directory.mkdir(parents=True, exist_ok=True)
    return runtime_directory


def install_plugin_runtime(plugin_name: str, package_name: str, destination_root: str = "") -> Path:
    """
    Install one sparse-solver runtime package to an external directory.

    :param plugin_name: Plugin name.
    :type plugin_name: str
    :param package_name: Python package name to install.
    :type package_name: str
    :param destination_root: Optional destination-root override.
    :type destination_root: str
    :return: Runtime installation directory.
    :rtype: Path
    """
    runtime_directory: Path = build_plugin_runtime_directory(plugin_name, destination_root)
    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        "--target",
        str(runtime_directory),
        package_name,
    ]
    subprocess.run(command, check=True)
    return runtime_directory


def build_argument_parser() -> argparse.ArgumentParser:
    """
    Build the command-line parser.

    :return: Argument parser.
    :rtype: argparse.ArgumentParser
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(description="Install external sparse solver runtimes")
    parser.add_argument("plugin_name", help="Plugin name")
    parser.add_argument("package_name", help="Python package name to install")
    parser.add_argument("--destination-root", default="", help="Optional destination root for runtime packages")
    return parser


def main() -> None:
    """
    Install one external sparse-solver runtime package.

    :return: None.
    :rtype: None
    """
    parser: argparse.ArgumentParser = build_argument_parser()
    args: argparse.Namespace = parser.parse_args()
    install_path: Path = install_plugin_runtime(args.plugin_name, args.package_name, args.destination_root)
    print(install_path)


if __name__ == "__main__":
    main()
