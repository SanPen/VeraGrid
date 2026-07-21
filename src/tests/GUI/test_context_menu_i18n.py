from pathlib import Path
import re

from PySide6 import QtWidgets

from VeraGrid.Gui.gui_functions import add_menu_entry


def test_add_menu_entry_preserves_caller_text(qt_app: object) -> None:
    """
    Menu helpers should use the translated text provided by the caller as-is.
    """
    _unused_qt_app = qt_app
    menu = QtWidgets.QMenu()

    add_menu_entry(menu=menu, text="Eliminar")

    assert menu.actions()[0].text() == "Eliminar"


def test_roseta_context_menu_handler_executes_menu() -> None:
    """
    The Roseta properties context-menu handler should still translate the action label and execute the menu.
    """
    gui_root = Path(__file__).resolve().parents[2] / "VeraGrid" / "Gui"
    roseta_file = gui_root / "FileDialogues" / "RosetaExplorer" / "RosetaExplorer.py"
    text = roseta_file.read_text(encoding="utf-8")
    match = re.search(
        r"def show_objects_context_menu\(self, pos: QtCore\.QPoint\):(.*?)def copy_table_to_clipboard",
        text,
        re.S,
    )

    assert match is not None
    assert 'text=self.tr("Copy")' in match.group(1)
    assert "context_menu.exec(" in match.group(1)


def test_context_menu_sources_use_explicit_translation_calls() -> None:
    """
    Runtime menus should not hide raw string literals behind helper wrappers.
    """
    gui_root = Path(__file__).resolve().parents[2] / "VeraGrid" / "Gui"
    roots = [
        gui_root / "Diagrams",
        gui_root / "Main" / "SubClasses",
        gui_root / "FileDialogues" / "RosetaExplorer",
    ]
    literal_patterns = [
        r"add_menu_entry\([^)]*text\s*=\s*['\"]",
        r"add_sub_menu\([^)]*text\s*=\s*['\"]",
        r"\.addSection\(\s*['\"]",
        r"\.addAction\(\s*['\"]",
        r"\.addMenu\(\s*['\"]",
    ]

    offenders: list[str] = []
    for root in roots:
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for pattern in literal_patterns:
                if re.search(pattern, text, re.S):
                    offenders.append(path.relative_to(gui_root.parent.parent).as_posix())
                    break

    assert offenders == []
