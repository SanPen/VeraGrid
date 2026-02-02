# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import rlcompleter
from typing import Dict, Any, List

from PySide6.QtCore import Qt, QEvent, QStringListModel
from PySide6.QtGui import QTextCursor, QFont
from PySide6.QtWidgets import QPlainTextEdit, QCompleter
from VeraGrid.Gui.python_highlighter import PythonHighlighter
from VeraGrid.Gui.font_config import CONSOLE_TEXT_SIZE


class PythonCodeEditor(QPlainTextEdit):
    """
    QPlainTextEdit with runtime Python autocomplete using rlcompleter.
    Same mechanism as the interactive console.
    """

    def __init__(
            self,
            parent=None,
            vars_dict: Dict[str, Any] | None = None, ):
        """

        :param parent:
        :param vars_dict:
        """
        super().__init__(parent)

        font = QFont("Consolas", CONSOLE_TEXT_SIZE)
        self.setFont(font)

        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        # VERY IMPORTANT: Tab must NOT move focus
        self.setTabChangesFocus(False)

        PythonHighlighter(self.document())

        # Normalize namespace exactly like the console
        self._vars_dict = dict() if vars_dict is None else vars_dict

        self._vars_dict["__builtins__"] = __builtins__  # dict or module, both fine]

        self._namespace = self._normalize_namespace(self._vars_dict)

        # rlcompleter backend (same as console)
        self._completer_backend = rlcompleter.Completer(self._namespace)

        # Qt popup completer
        self._qt_completer = QCompleter(self)
        self._qt_completer.setWidget(self)
        self._qt_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._qt_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._qt_completer.activated.connect(self._insert_completion)

        self._model = QStringListModel(self)
        self._qt_completer.setModel(self._model)

        # Remember what we replace
        self._last_prefix = ""

    def add_var(self, name: str, val: Any) -> None:
        """
        Add variable to the interpreter
        :param name: name of the variable
        :param val: value or pointer
        """
        self._vars_dict[name] = val
        self._namespace = self._normalize_namespace(self._vars_dict)
        self._completer_backend = rlcompleter.Completer(self._namespace)

    @staticmethod
    def _normalize_namespace(ns: Dict[str, Any]) -> Dict[str, Any]:
        builtins_obj = ns.get("__builtins__", __builtins__)
        builtins_dict = (
            builtins_obj if isinstance(builtins_obj, dict)
            else builtins_obj.__dict__
        )

        out = dict(ns)
        out["__builtins__"] = builtins_dict
        return out

    # ------------------------------------------------------------------
    # THIS is the key part: intercept Tab at event() level
    # ------------------------------------------------------------------

    def event(self, e: QEvent):
        if e.type() == QEvent.Type.KeyPress:

            popup = self._qt_completer.popup()

            # --------------------------------------------------
            # If completion popup is visible → handle selection
            # --------------------------------------------------
            if popup.isVisible():
                if e.key() in (Qt.Key.Key_Tab, Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    # current = self._qt_completer.currentCompletion()
                    # if current:
                    #     self._insert_completion(current)
                    popup = self._qt_completer.popup()
                    index = popup.currentIndex()
                    if index.isValid():
                        completion = index.data()
                        self._insert_completion(completion)
                    popup.hide()
                    return True

                if e.key() == Qt.Key.Key_Escape:
                    popup.hide()
                    return True

                # Let popup handle navigation keys
                if e.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_PageUp, Qt.Key.Key_PageDown,):
                    return super().event(e)

            # --------------------------------------------------
            # No popup → trigger completion
            # --------------------------------------------------
            if e.key() == Qt.Key.Key_Tab and e.modifiers() == Qt.KeyboardModifier.NoModifier:
                self._trigger_completion()
                return True

            if e.key() == Qt.Key.Key_Space and e.modifiers() & Qt.KeyboardModifier.ControlModifier:
                self._trigger_completion()
                return True

        return super().event(e)

    # ------------------------------------------------------------------
    # Completion logic (console-style)
    # ------------------------------------------------------------------

    def _trigger_completion(self):
        prefix = self._extract_prefix()
        if not prefix:
            return

        self._last_prefix = prefix

        matches: List[str] = []
        i = 0
        while True:
            m = self._completer_backend.complete(prefix, i)
            if m is None:
                break
            matches.append(m)
            i += 1

        if not matches:
            return

        # Remove duplicates, keep order
        seen = set()
        uniq = []
        for m in matches:
            if m not in seen:
                seen.add(m)
                uniq.append(m)

        if len(uniq) == 1:
            self._replace_prefix(uniq[0])
            return

        self._model.setStringList(uniq)

        rect = self.cursorRect()
        rect.setWidth(
            self._qt_completer.popup().sizeHintForColumn(0)
            + self._qt_completer.popup().verticalScrollBar().sizeHint().width()
        )
        self._qt_completer.complete(rect)

    # ------------------------------------------------------------------
    # Prefix handling (critical – NOT WordUnderCursor)
    # ------------------------------------------------------------------

    def _extract_prefix(self) -> str:
        cursor = self.textCursor()
        pos = cursor.position()
        text = self.toPlainText()

        i = pos - 1
        while i >= 0:
            ch = text[i]
            if ch.isalnum() or ch in "._":
                i -= 1
            else:
                break

        return text[i + 1:pos]

    def _replace_prefix(self, completion: str):
        cursor = self.textCursor()
        cursor.beginEditBlock()

        cursor.movePosition(
            QTextCursor.MoveOperation.Left,
            QTextCursor.MoveMode.KeepAnchor,
            len(self._last_prefix),
        )
        cursor.removeSelectedText()
        cursor.insertText(completion)

        cursor.endEditBlock()
        self.setTextCursor(cursor)

    def _insert_completion(self, text: str):
        self._replace_prefix(text)


if __name__ == "__main__":
    import sys
    import numpy as np
    from PySide6.QtWidgets import QApplication, QMainWindow


    class ConsoleMainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("PySide6 Python Console")
            console = PythonCodeEditor(
                vars_dict={
                    "__builtins__": __builtins__,  # dict or module, both fine
                    "app": self,
                    "np": np,
                },
            )
            self.setCentralWidget(console)


    app = QApplication(sys.argv)
    window = ConsoleMainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
