from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path


def _find_tool(tool_name: str) -> str:
    """
    Resolve one Qt translation tool from PATH.

    :param tool_name: Executable name.
    :returns: Executable path or the original name.
    """
    resolved_path: str | None = shutil.which(tool_name)
    if resolved_path is None:
        return tool_name
    else:
        return resolved_path


def _run_command(arguments: list[str]) -> None:
    """
    Run one subprocess and fail fast on errors.

    :param arguments: Command arguments.
    :returns: Nothing.
    """
    subprocess.run(arguments, check=True)


def _get_translation_source_files(translations_dir: Path) -> list[Path]:
    """
    Return every translation source file stored in the translations directory.

    :param translations_dir: Directory containing ``.ts`` files.
    :returns: Sorted translation source files.
    """
    ts_files: list[Path] = sorted(translations_dir.glob("*.ts"))
    return ts_files


def _reactivate_manual_context_translations(ts_file: Path) -> None:
    """
    Restore manual translation contexts after ``lupdate`` marks them vanished.

    :param ts_file: Translation source file to patch.
    :returns: Nothing.
    """
    contents: str = ts_file.read_text(encoding="utf-8")
    context_name: str
    context_pattern: str
    context_match: re.Match[str] | None
    original_block: str
    updated_block: str
    updated_contents: str = contents

    for context_name in ["ContextMenu", "ConfigurationMain", "messages"]:
        context_pattern = rf"<context>\s*<name>{context_name}</name>.*?</context>"
        context_match = re.search(context_pattern, updated_contents, re.DOTALL)

        if context_match is None:
            pass
        else:
            original_block = context_match.group(0)
            updated_block = original_block.replace('<translation type="vanished">', "<translation>")
            updated_block = re.sub(
                r'<translation type="unfinished">([^<]+)</translation>',
                r"<translation>\1</translation>",
                updated_block,
            )
            updated_contents = updated_contents.replace(original_block, updated_block, 1)

    if updated_contents == contents:
        return
    else:
        pass

    # Only the manual runtime contexts are rewritten so translator-managed
    # formatting outside those catalogs remains untouched.
    ts_file.write_text(updated_contents, encoding="utf-8")


def update_translations() -> None:
    """
    Refresh every application ``.ts`` file and compile matching ``.qm`` outputs.

    :returns: Nothing.
    """
    gui_root: Path = Path(__file__).resolve().parent
    translations_dir: Path = gui_root / "translations"
    ts_files: list[Path]

    translations_dir.mkdir(parents=True, exist_ok=True)
    ts_files = _get_translation_source_files(translations_dir=translations_dir)

    if len(ts_files) == 0:
        return
    else:
        pass

    # Update all catalogs in one lupdate pass so every translation file sees the same source tree.
    _run_command(
        list(
            [
            _find_tool("pyside6-lupdate"),
            str(gui_root),
            "-ts",
            ]
        ) + [str(ts_file) for ts_file in ts_files]
    )

    ts_file: Path
    for ts_file in ts_files:
        _reactivate_manual_context_translations(ts_file=ts_file)

    # Compile each catalog to the qm file with the same stem in the same folder.
    for ts_file in ts_files:
        qm_file: Path = ts_file.with_suffix(".qm")
        _run_command(
            [
                _find_tool("pyside6-lrelease"),
                str(ts_file),
                "-qm",
                str(qm_file),
            ]
        )


if __name__ == "__main__":
    update_translations()
