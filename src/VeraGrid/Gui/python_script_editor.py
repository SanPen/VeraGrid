# SPDX-License-Identifier: MPL-2.0
"""Executable Scripting editor specialization."""

from __future__ import annotations

import builtins
import rlcompleter
from types import ModuleType
from typing import Any, Dict, Mapping, List

from PySide6 import QtCore, QtGui, QtWidgets

from VeraGrid.Gui.base_python_code_editor import BasePythonCodeEditor
from VeraGrid.Gui.python_highlighter import PythonHighlighter


def normalize_scripting_namespace(namespace: Mapping[str, Any]) -> Dict[str, Any]:
    """Return an rlcompleter-compatible namespace with explicit builtins.

    :param namespace: Objects exposed by the Scripting controller.
    :return: Detached namespace accepted by ``rlcompleter``.
    """
    normalized_namespace: Dict[str, Any] = dict(namespace)
    builtins_object: object = normalized_namespace.get("__builtins__", builtins)
    if isinstance(builtins_object, dict):
        builtins_dictionary: Dict[str, Any] = builtins_object
    elif isinstance(builtins_object, ModuleType):
        builtins_dictionary = builtins_object.__dict__
    else:
        builtins_dictionary = builtins.__dict__
    normalized_namespace["__builtins__"] = builtins_dictionary
    return normalized_namespace


class ScriptingPythonEditor(BasePythonCodeEditor):
    """Python editor with executable namespace awareness and completion."""

    __slots__ = (
        "_highlighter",
        "_vars_dict",
        "_namespace",
        "_completer_backend",
        "_qt_completer",
        "_completion_model",
        "_completion_shortcut",
        "_last_prefix",
    )

    def __init__(
            self,
            parent: QtWidgets.QWidget | None = None,
            vars_dict: Mapping[str, Any] | None = None,
    ) -> None:
        """Create the Scripting editor and its runtime completion namespace.

        Actual execution remains in the Scripting controller, which forwards
        the source to the shared Python console. Keeping execution outside the
        visual editor prevents an editing widget from owning application flow.

        :param parent: Optional owning Qt widget.
        :param vars_dict: Initial objects exposed to completion and execution.
        :return: None.
        """
        super().__init__(parent)
        self._highlighter: PythonHighlighter = PythonHighlighter(self.document())
        if vars_dict is None:
            self._vars_dict: Dict[str, Any] = dict()
        else:
            self._vars_dict = dict(vars_dict)
        self._vars_dict["__builtins__"] = builtins
        self._namespace: Dict[str, Any] = normalize_scripting_namespace(self._vars_dict)
        self._completer_backend: rlcompleter.Completer = rlcompleter.Completer(self._namespace)

        # The Qt popup is only a view over matches produced by rlcompleter; it
        # does not execute or inspect DAE symbolic expressions.
        self._qt_completer: QtWidgets.QCompleter = QtWidgets.QCompleter(self)
        self._qt_completer.setWidget(self)
        self._qt_completer.setCompletionMode(
            QtWidgets.QCompleter.CompletionMode.PopupCompletion
        )
        self._qt_completer.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self._qt_completer.activated.connect(self._insert_completion)
        self._completion_model: QtCore.QStringListModel = QtCore.QStringListModel(self)
        self._qt_completer.setModel(self._completion_model)
        self._completion_shortcut: QtGui.QShortcut = QtGui.QShortcut(
            QtGui.QKeySequence("Ctrl+Space"),
            self,
        )
        self._completion_shortcut.setContext(QtCore.Qt.ShortcutContext.WidgetShortcut)
        self._completion_shortcut.activated.connect(self._trigger_completion)
        self._last_prefix: str = ""

    def set_dark_mode(self) -> None:
        """Apply dark mode to the editor and syntax highlighter.

        :return: None.
        """
        BasePythonCodeEditor.set_dark_mode(self)
        self._highlighter.set_dark_mode()

    def set_light_mode(self) -> None:
        """Apply light mode to the editor and syntax highlighter.

        :return: None.
        """
        BasePythonCodeEditor.set_light_mode(self)
        self._highlighter.set_light_mode()

    def add_var(self, name: str, val: Any) -> None:
        """Expose one object to Scripting completion and execution.

        :param name: Python identifier used by scripts.
        :param val: Runtime object bound to the identifier.
        :return: None.
        """
        self._vars_dict[name] = val
        self._namespace = normalize_scripting_namespace(self._vars_dict)
        self._completer_backend = rlcompleter.Completer(self._namespace)

    def get_execution_namespace(self) -> Dict[str, Any]:
        """Return a detached view of the namespace exposed to Scripting.

        The Scripting controller remains responsible for executing the source.
        Returning a copy prevents callers from bypassing :meth:`add_var` and
        leaving the completion backend out of sync.

        :return: Current executable Python namespace.
        """
        return dict(self._namespace)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """Coordinate completion keys before using the shared editor behavior.

        :param event: Incoming keyboard event.
        :return: None.
        """
        popup: QtWidgets.QAbstractItemView = self._qt_completer.popup()
        pressed_key: int = event.key()
        popup_visible: bool = popup.isVisible()
        pressed_text: str = event.text()
        completion_keys: tuple[QtCore.Qt.Key, ...] = (
            QtCore.Qt.Key.Key_Tab,
            QtCore.Qt.Key.Key_Return,
            QtCore.Qt.Key.Key_Enter,
        )
        navigation_keys: tuple[QtCore.Qt.Key, ...] = (
            QtCore.Qt.Key.Key_Up,
            QtCore.Qt.Key.Key_Down,
            QtCore.Qt.Key.Key_PageUp,
            QtCore.Qt.Key.Key_PageDown,
        )
        horizontal_keys: tuple[QtCore.Qt.Key, ...] = (
            QtCore.Qt.Key.Key_Left,
            QtCore.Qt.Key.Key_Right,
        )
        inserts_printable_text: bool = (
            len(pressed_text) > 0
            and pressed_text.isprintable()
            and pressed_key not in completion_keys
            and pressed_key != QtCore.Qt.Key.Key_Escape
        )

        # Printable text must always reach the editor first. On Windows many
        # layouts emit AltGr characters through Ctrl+Alt key events.
        if inserts_printable_text:
            BasePythonCodeEditor.keyPressEvent(self, event)
            if popup_visible:
                self._trigger_completion()
            else:
                pass
        elif popup_visible and pressed_key in completion_keys:
            completion_index: QtCore.QModelIndex = popup.currentIndex()
            if completion_index.isValid():
                completion_text: str = str(completion_index.data())
                self._insert_completion(completion_text)
            else:
                pass
            popup.hide()
            event.accept()
        elif popup_visible and pressed_key == QtCore.Qt.Key.Key_Escape:
            popup.hide()
            event.accept()
        elif popup_visible and pressed_key in navigation_keys:
            # QCompleter installs its own event filter and consumes navigation
            # before normal editor movement is considered.
            QtWidgets.QPlainTextEdit.event(self, event)
        elif popup_visible and pressed_key in horizontal_keys:
            event.accept()
        else:
            BasePythonCodeEditor.keyPressEvent(self, event)
            if popup_visible:
                self._trigger_completion()
            else:
                pass

    def event(self, event: QtCore.QEvent) -> bool:
        """Keep printable text out of Qt shortcut resolution.

        :param event: Qt event routed to the editor.
        :return: ``True`` when the event is fully handled.
        """
        if event.type() == QtCore.QEvent.Type.ShortcutOverride and isinstance(event, QtGui.QKeyEvent):
            pressed_text: str = event.text()
            is_ctrl_space: bool = (
                event.key() == QtCore.Qt.Key.Key_Space
                and event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier
            )

            # Accepting ShortcutOverride tells Qt that the editor owns this key
            # sequence, so AltGr-generated text is not stolen by shortcuts.
            if is_ctrl_space:
                return BasePythonCodeEditor.event(self, event)
            elif len(pressed_text) > 0 and pressed_text.isprintable():
                event.accept()
                return True
            else:
                pass
        else:
            pass

        return BasePythonCodeEditor.event(self, event)

    def _trigger_completion(self) -> None:
        """Populate or directly apply matches for the current source prefix.

        :return: None.
        """
        prefix: str = self._extract_prefix()
        if len(prefix) == 0:
            pass
        else:
            self._last_prefix = prefix
            matches: List[str] = list()
            completion_index: int = 0
            completion: str | None = self._completer_backend.complete(
                prefix,
                completion_index,
            )
            while completion is not None:
                matches.append(completion)
                completion_index += 1
                completion = self._completer_backend.complete(prefix, completion_index)

            # rlcompleter can repeat candidates through different resolution
            # routes. Preserve its useful order while removing duplicates.
            unique_matches: List[str] = list()
            seen_matches: set[str] = set()
            match: str
            for match in matches:
                if match not in seen_matches:
                    seen_matches.add(match)
                    unique_matches.append(match)
                else:
                    pass

            if len(unique_matches) == 0:
                pass
            elif len(unique_matches) == 1:
                self._replace_prefix(unique_matches[0])
            else:
                self._completion_model.setStringList(unique_matches)
                completion_rectangle: QtCore.QRect = self.cursorRect()
                completion_rectangle.setWidth(
                    self._qt_completer.popup().sizeHintForColumn(0)
                    + self._qt_completer.popup().verticalScrollBar().sizeHint().width()
                )
                self._qt_completer.complete(completion_rectangle)

    def _extract_prefix(self) -> str:
        """Return the dotted Python expression directly before the cursor.

        :return: Completion prefix.
        """
        text_cursor: QtGui.QTextCursor = self.textCursor()
        cursor_position: int = text_cursor.position()
        source_text: str = self.toPlainText()
        start_position: int = cursor_position - 1
        prefix_complete: bool = False
        while start_position >= 0 and not prefix_complete:
            character: str = source_text[start_position]
            if character.isalnum() or character in "._":
                start_position -= 1
            else:
                prefix_complete = True
        return source_text[start_position + 1:cursor_position]

    def _replace_prefix(self, completion: str) -> None:
        """Replace the remembered prefix with one completion candidate.

        :param completion: Complete Python name selected by the user.
        :return: None.
        """
        text_cursor: QtGui.QTextCursor = self.textCursor()
        text_cursor.beginEditBlock()
        text_cursor.movePosition(
            QtGui.QTextCursor.MoveOperation.Left,
            QtGui.QTextCursor.MoveMode.KeepAnchor,
            len(self._last_prefix),
        )
        text_cursor.removeSelectedText()
        text_cursor.insertText(completion)
        text_cursor.endEditBlock()
        self.setTextCursor(text_cursor)

    @QtCore.Slot(str)
    def _insert_completion(self, text: str) -> None:
        """Insert the completion emitted by the popup.

        :param text: Selected completion string.
        :return: None.
        """
        self._replace_prefix(text)
