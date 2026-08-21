# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import io
import sys
from typing import Any
import code
import contextlib
import rlcompleter
import traceback

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWidgets import QCompleter
from PySide6.QtCore import QStringListModel
from VeraGrid.Gui.base_python_code_editor import BasePythonCodeEditor
from VeraGrid.Gui.python_highlighter import PythonHighlighter


class _GuiOutput(QObject):
    written = Signal(str)


class ConsoleInterpreter(code.InteractiveInterpreter):
    def __init__(self, locals=None, write_callback=None):
        super().__init__(locals=locals or {})
        self._write_callback = write_callback

    def write(self, data: str):
        # InteractiveInterpreter uses this for tracebacks, etc.
        if self._write_callback:
            self._write_callback(data)

    def showtraceback(self):
        tb = traceback.format_exc()
        self.write(tb)


class _BufferStream(io.TextIOBase):
    """File-like stream to capture stdout/stderr during execution."""

    def __init__(self, write_fn):
        super().__init__()
        self._write_fn = write_fn

    def write(self, s):
        self._write_fn(s)
        return len(s)

    def flush(self):
        pass


class PythonConsole(BasePythonCodeEditor):
    PROMPT_PRIMARY = ">>> "
    PROMPT_SECONDARY = "... "

    def __init__(self, banner="", locals=None, parent=None):
        """

        :param banner:
        :param locals:
        :param parent:
        """
        super().__init__(parent=parent, show_line_numbers=False)
        self.setUndoRedoEnabled(False)

        PythonHighlighter(self.document())

        self._history = []
        self._history_index = 0
        self._buffer = []  # multiline buffer
        self._input_start_pos = 0

        # GUI-thread output marshalling
        self._gui_out = _GuiOutput()
        self._gui_out.written.connect(self._append_output)

        self._interpreter = ConsoleInterpreter(
            locals=locals,
            write_callback=self._emit_output,
        )
        self._completer = QCompleter(self)
        self._completer.setWidget(self)
        self._completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._completer.activated.connect(self._insert_completion)

        if banner:
            self._append_output(banner + "\n")

        self._insert_prompt(primary=True)
        self.cursorPositionChanged.connect(self._enforce_cursor)

    def reset(self):
        self.document().clear()
        self._insert_prompt(primary=True)
        self.cursorPositionChanged.connect(self._enforce_cursor)

    def add_var(self, name: str, val: Any) -> None:
        """
        Add variable to the interpreter
        :param name: name of the variable
        :param val: value or pointer
        """
        self._interpreter.locals[name] = val

    def append_output(self, text: str):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        self.setTextCursor(cursor)

        # After output, input must start at the end of document
        self._input_start_pos = self.document().characterCount() - 1

    def execute(self, command: str):
        """
        Run a command and display output.
        """

        try:
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = io.StringIO()
            sys.stderr = io.StringIO()

            success = self._interpreter.runcode(command)
            stdout_output = sys.stdout.getvalue()
            stderr_output = sys.stderr.getvalue()
            sys.stdout = old_stdout
            sys.stderr = old_stderr

            if stdout_output:
                self.append_output(stdout_output)
            if stderr_output:
                self.append_output(stderr_output)

        except Exception as e:
            self.append_output(str(e))

    # ----------------------------
    # Prompt + input boundary
    # ----------------------------
    def _safe_input_start_pos(self) -> int:
        doc = self.document()
        # characterCount() includes a trailing '\n'
        return min(self._input_start_pos, doc.characterCount() - 1)

    def _insert_prompt(self, primary: bool):
        prompt = self.PROMPT_PRIMARY if primary else self.PROMPT_SECONDARY
        self.moveCursor(QTextCursor.MoveOperation.End)
        self.insertPlainText(prompt)
        self._input_start_pos = self.textCursor().position()
        self.moveCursor(QTextCursor.MoveOperation.End)

    def _current_input(self) -> str:
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine, QTextCursor.MoveMode.KeepAnchor)
        line = cursor.selectedText()
        # Remove prompt prefix
        if line.startswith(self.PROMPT_PRIMARY):
            return line[len(self.PROMPT_PRIMARY):]
        if line.startswith(self.PROMPT_SECONDARY):
            return line[len(self.PROMPT_SECONDARY):]
        return line

    def _replace_current_line(self, text: str):
        cursor = self.textCursor()

        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()

        prompt = self.PROMPT_SECONDARY if self._buffer else self.PROMPT_PRIMARY
        cursor.insertText(prompt + text)

        # Recompute input boundary *after prompt only*
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor, len(prompt))
        self._input_start_pos = cursor.position()

        self.setTextCursor(cursor)

    # ----------------------------
    # Thread-safe output
    # ----------------------------

    def _emit_output(self, text: str):
        # Always go through a signal (safe even if called from worker threads)
        self._gui_out.written.emit(text)

    def _append_output(self, text: str):
        self.moveCursor(QTextCursor.MoveOperation.End)
        self.insertPlainText(text)
        self.moveCursor(QTextCursor.MoveOperation.End)

    # ----------------------------
    # Hard prompt protection
    # ----------------------------

    def _enforce_cursor(self):
        safe_pos = self._safe_input_start_pos()
        c = self.textCursor()
        if c.position() < safe_pos:
            c.setPosition(safe_pos)
            self.setTextCursor(c)

    def _selection_crosses_prompt(self) -> bool:
        c = self.textCursor()
        return c.hasSelection() and c.selectionStart() < self._input_start_pos

    def _accept_completion_from_popup(self):
        popup = self._completer.popup()
        index = popup.currentIndex()
        if not index.isValid():
            popup.hide()
            return

        completion = index.data()

        # Save cursor position *before* modifying text
        cursor = self.textCursor()
        cursor.beginEditBlock()

        self._replace_current_line(completion)

        cursor.endEditBlock()

        # IMPORTANT: restore cursor explicitly to end of inserted text
        self.moveCursor(QTextCursor.MoveOperation.End)

        popup.hide()

    # ----------------------------
    # Key handling
    # ----------------------------

    def keyPressEvent(self, event):
        # -------------------------------------------------
        # If autocomplete popup is visible → accept / close
        # -------------------------------------------------
        popup = self._completer.popup()
        if popup.isVisible():
            if event.key() in (Qt.Key.Key_Tab, Qt.Key.Key_Return, Qt.Key.Key_Enter):
                # Accept the current completion
                self._accept_completion_from_popup()
                return

            if event.key() == Qt.Key.Key_Escape:
                # Close the popup
                popup.hide()
                return

            # Let the popup handle navigation keys (Up/Down/PageUp/PageDown)
            if event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_PageUp, Qt.Key.Key_PageDown):
                return super().keyPressEvent(event)

            # Prevent Left and Right Arrow keys from inserting characters
            if event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Right):
                return  # Don't allow Left/Right Arrow to insert text while popup is visible

            # Update the completion model as text changes (only when popup is visible)
            self._autocomplete()

        # -------------------------------------------------
        # Insert tab space or trigger completion when popup is NOT visible
        # -------------------------------------------------
        elif event.key() == Qt.Key.Key_Tab:
            # Insert four spaces instead of a literal tab character so console
            # input always uses the requested indentation width.
            cursor = self.textCursor()
            cursor.insertText(self._tab_text)
            self.setTextCursor(cursor)
            return

        # Trigger completion popup when Ctrl + Space is pressed
        elif (
            event.key() == Qt.Key.Key_Space
            and event.modifiers() == Qt.KeyboardModifier.ControlModifier
        ):
            # Windows reports AltGr as Ctrl+Alt on many layouts. Requiring the
            # exact Ctrl modifier keeps completion from swallowing text input
            # for characters such as "]".
            self._autocomplete()
            return

        c = self.textCursor()

        # Prevent any edits that would touch the prompt or earlier output
        if self._selection_crosses_prompt():
            if event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete) or event.text():
                return

        if event.key() == Qt.Key.Key_Backspace:
            safe_pos = self._safe_input_start_pos()
            if c.position() <= safe_pos:
                return

        if event.key() == Qt.Key.Key_Delete:
            safe_pos = self._safe_input_start_pos()
            if c.position() < safe_pos:
                return

        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._handle_enter()
            return

        if event.key() == Qt.Key.Key_Up:
            self._history_prev()
            return

        if event.key() == Qt.Key.Key_Down:
            self._history_next()
            return

        if event.key() == Qt.Key.Key_Tab:
            self._autocomplete()
            return

        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self._enforce_cursor()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self._enforce_cursor()

    def insertFromMimeData(self, source):
        # Block paste that would overwrite prompt/output
        if self._selection_crosses_prompt():
            return
        super().insertFromMimeData(source)

    # ----------------------------
    # Execution (safe redirection)
    # ----------------------------

    def _handle_enter(self):
        line = self._current_input()
        self._history.append(line)
        self._history_index = len(self._history)

        self._buffer.append(line)
        source = "\n".join(self._buffer)

        self._append_output("\n")

        out_stream = _BufferStream(self._emit_output)
        err_stream = _BufferStream(self._emit_output)

        # Redirect ONLY during execution; do NOT touch global sys.stdout permanently.
        with contextlib.redirect_stdout(out_stream), contextlib.redirect_stderr(err_stream):
            more = self._interpreter.runsource(source)

        if more:
            self._insert_prompt(primary=False)
        else:
            self._buffer.clear()
            self._insert_prompt(primary=True)

    # ----------------------------
    # History
    # ----------------------------

    def _history_prev(self):
        if not self._history:
            return
        self._history_index = max(0, self._history_index - 1)
        self._replace_current_line(self._history[self._history_index])

    def _history_next(self):
        if not self._history:
            return
        self._history_index = min(len(self._history), self._history_index + 1)
        text = "" if self._history_index == len(self._history) else self._history[self._history_index]
        self._replace_current_line(text)

    # ----------------------------
    # Autocomplete
    # ----------------------------

    def _insert_completion(self, completion: str):
        self._replace_current_line(completion)

    def _autocomplete(self):
        text = self._current_input()
        if not text:
            return

        completer = rlcompleter.Completer(self._interpreter.locals)

        matches = list()
        i = 0
        while True:
            m = completer.complete(text, i)
            if m is None:
                break
            matches.append(m)
            i += 1

        if not matches:
            return

        if len(matches) == 1:
            self._replace_current_line(matches[0])
            return

        # Multiple matches → popup
        model = QStringListModel(matches, self._completer)
        self._completer.setModel(model)

        cursor = self.textCursor()
        cr = self.cursorRect(cursor)
        cr.setWidth(self._completer.popup().sizeHintForColumn(0) +
                    self._completer.popup().verticalScrollBar().sizeHint().width())

        self._completer.complete(cr)


if __name__ == "__main__":
    import numpy as np

    class ConsoleMainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("PySide6 Python Console")
            console = PythonConsole(banner="Welcome to Python Console!")
            self.setCentralWidget(console)

            console.add_var("np", np)


    app = QApplication(sys.argv)
    window = ConsoleMainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
