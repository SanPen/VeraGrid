from __future__ import annotations

import argparse
import shutil
from pathlib import Path

def get_repository_plugin_templates_root() -> Path:
    """
    Return the repository directory containing sparse-solver plugin templates.

    :return: Repository plugin-template directory.
    :rtype: Path
    """
    return Path(__file__).resolve().parent / "plugin_templates"


def get_default_plugin_destination_root() -> Path:
    """
    Return the default sparse-solver plugin destination directory.

    :return: Default plugin destination directory.
    :rtype: Path
    """
    plugin_root: Path = Path.home() / ".VeraGrid" / "plugins" / "sparse_solvers"
    plugin_root.mkdir(parents=True, exist_ok=True)
    return plugin_root


def install_sparse_solver_plugin(plugin_name: str, destination_root: str = "") -> Path:
    """
    Install one repository sparse-solver plugin template into the VeraGrid plugin folder.

    :param plugin_name: Plugin template name.
    :type plugin_name: str
    :param destination_root: Optional destination-root override.
    :type destination_root: str
    :return: Installed plugin directory.
    :rtype: Path
    """
    source_directory: Path = get_repository_plugin_templates_root() / plugin_name

    if source_directory.exists():
        pass
    else:
        raise FileNotFoundError(f"Sparse solver plugin template not found: {source_directory}")

    if len(destination_root) > 0:
        destination_directory_root: Path = Path(destination_root)
    else:
        destination_directory_root = get_default_plugin_destination_root()

    destination_directory_root.mkdir(parents=True, exist_ok=True)
    destination_directory: Path = destination_directory_root / plugin_name

    if destination_directory.exists():
        shutil.rmtree(destination_directory)
    else:
        pass

    shutil.copytree(source_directory, destination_directory, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return destination_directory


def build_argument_parser() -> argparse.ArgumentParser:
    """
    Build the command-line parser.

    :return: Argument parser.
    :rtype: argparse.ArgumentParser
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(description="Install external sparse solver plugin templates")
    parser.add_argument("plugin_name", help="Repository plugin template name")
    parser.add_argument("--destination-root", default="", help="Optional destination root for sparse solver plugins")
    return parser


def main() -> None:
    """
    Install one sparse-solver plugin template from the repository.

    :return: None.
    :rtype: None
    """
    parser: argparse.ArgumentParser = build_argument_parser()
    args: argparse.Namespace = parser.parse_args()
    installed_path: Path = install_sparse_solver_plugin(args.plugin_name, args.destination_root)
    print(installed_path)


if __name__ == "__main__":
    main()
