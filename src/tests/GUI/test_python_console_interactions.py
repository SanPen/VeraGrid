# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Regression tests for the embedded Python console interactions."""

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets

from VeraGrid.Gui.python_console import PythonConsole


def get_qt_application() -> QtWidgets.QApplication:
    """Return the process-wide Qt application required by widget tests.

    :return: Existing or newly created Qt application.
    """
    application: QtWidgets.QApplication | None = QtWidgets.QApplication.instance()
    if application is None:
        return QtWidgets.QApplication(list())
    else:
        return application


def press_key(console: PythonConsole, key: QtCore.Qt.Key, text: str = "") -> None:
    """Send one plain key press to the console.

    :param console: Console receiving the key event.
    :param key: Qt key code to send.
    :param text: Text carried by the key event.
    :return: None.
    """
    # The console overrides key handling, so direct event delivery keeps the
    # test focused on the same method used by Qt.
    event: QtGui.QKeyEvent = QtGui.QKeyEvent(
        QtCore.QEvent.Type.KeyPress,
        key,
        QtCore.Qt.KeyboardModifier.NoModifier,
        text,
    )
    console.keyPressEvent(event)


def press_control_key(console: PythonConsole, key: QtCore.Qt.Key, text: str = "") -> None:
    """Send one Control-modified key press to the console.

    :param console: Console receiving the key event.
    :param key: Qt key code to send.
    :param text: Text carried by the key event.
    :return: None.
    """
    event: QtGui.QKeyEvent = QtGui.QKeyEvent(
        QtCore.QEvent.Type.KeyPress,
        key,
        QtCore.Qt.KeyboardModifier.ControlModifier,
        text,
    )
    console.keyPressEvent(event)


def press_modified_key(
        console: PythonConsole,
        key: QtCore.Qt.Key,
        modifiers: QtCore.Qt.KeyboardModifier,
        text: str = "",
) -> None:
    """Send one modified key press to the console.

    :param console: Console receiving the key event.
    :param key: Qt key code to send.
    :param modifiers: Keyboard modifiers carried by the event.
    :param text: Text carried by the key event.
    :return: None.
    """
    event: QtGui.QKeyEvent = QtGui.QKeyEvent(
        QtCore.QEvent.Type.KeyPress,
        key,
        modifiers,
        text,
    )
    console.keyPressEvent(event)


def select_previous_output(console: PythonConsole) -> None:
    """Select the previous output text in the prepared console.

    :param console: Console whose transcript starts with ``old output``.
    :return: None.
    """
    cursor: QtGui.QTextCursor = console.textCursor()
    cursor.setPosition(0)
    cursor.setPosition(len("old output"), QtGui.QTextCursor.MoveMode.KeepAnchor)
    console.setTextCursor(cursor)


def restore_console_text(console: PythonConsole, text: str) -> None:
    """Restore prepared console text and its editable prompt boundary.

    :param console: Console to restore.
    :param text: Full console text containing the live prompt.
    :return: None.
    """
    console.setPlainText(text)
    console._input_start_pos = text.rfind(PythonConsole.PROMPT_PRIMARY) + len(PythonConsole.PROMPT_PRIMARY)
    cursor: QtGui.QTextCursor = console.textCursor()
    cursor.setPosition(len(text))
    console.setTextCursor(cursor)


def close_active_popup() -> None:
    """Close the active Qt popup menu if one is open.

    :return: None.
    """
    popup_widget: QtWidgets.QWidget | None = QtWidgets.QApplication.activePopupWidget()
    if popup_widget is not None:
        popup_widget.close()
    else:
        pass


def test_console_keeps_transcript_copyable_and_prompt_editable() -> None:
    """Verify transcript selection behaves like a console, not an editor.

    :return: None.
    """
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    console: PythonConsole = PythonConsole()
    console.document().clear()
    console._append_output("old output\n")
    console._insert_prompt(primary=True)
    assert console._interpreter.locals["describe"] is not None
    console.add_var("press_key", press_key)
    console.execute("describe(press_key)")
    assert "Arguments for press_key:" in console.toPlainText()
    assert "console" in console.toPlainText()
    console.document().clear()
    console._append_output("old output\n")
    console._insert_prompt(primary=True)

    safe_position: int = console._safe_input_start_pos()
    press_key(console=console, key=QtCore.Qt.Key.Key_A, text="a")
    press_key(console=console, key=QtCore.Qt.Key.Key_B, text="b")
    press_key(console=console, key=QtCore.Qt.Key.Key_C, text="c")
    assert console.toPlainText().endswith(">>> abc")

    cursor: QtGui.QTextCursor = console.textCursor()
    cursor.setPosition(safe_position)
    console.setTextCursor(cursor)
    press_key(console=console, key=QtCore.Qt.Key.Key_Backspace)
    assert console.toPlainText().endswith(">>> abc")

    press_key(console=console, key=QtCore.Qt.Key.Key_Delete)
    assert console.toPlainText().endswith(">>> bc")

    cursor = console.textCursor()
    cursor.setPosition(console._safe_input_start_pos())
    cursor.setPosition(console._safe_input_start_pos() + 1, QtGui.QTextCursor.MoveMode.KeepAnchor)
    console.setTextCursor(cursor)
    press_key(console=console, key=QtCore.Qt.Key.Key_Delete)
    assert console.toPlainText().endswith(">>> c")

    press_modified_key(
        console=console,
        key=QtCore.Qt.Key.Key_Control,
        modifiers=QtCore.Qt.KeyboardModifier.ControlModifier,
    )
    cursor = console.textCursor()
    cursor.setPosition(console._safe_input_start_pos())
    console.setTextCursor(cursor)
    press_key(console=console, key=QtCore.Qt.Key.Key_Delete)
    assert console.toPlainText().endswith(">>> ")

    press_key(console=console, key=QtCore.Qt.Key.Key_End)
    assert console.textCursor().position() == len(console.toPlainText())

    press_key(console=console, key=QtCore.Qt.Key.Key_Home)
    assert console.textCursor().position() == console._safe_input_start_pos()

    cursor = console.textCursor()
    cursor.setPosition(0)
    console.setTextCursor(cursor)
    console._enforce_cursor()
    assert console.textCursor().position() == console._safe_input_start_pos()

    select_previous_output(console=console)
    console._enforce_cursor()
    assert console.textCursor().hasSelection()

    text_before: str = console.toPlainText()
    press_key(console=console, key=QtCore.Qt.Key.Key_X, text="x")
    assert console.toPlainText().startswith("old output\n")
    assert console.toPlainText().endswith(">>> x")

    restore_console_text(console=console, text=text_before)
    select_previous_output(console=console)
    QtWidgets.QApplication.clipboard().clear()
    press_control_key(console=console, key=QtCore.Qt.Key.Key_C, text="c")
    assert QtWidgets.QApplication.clipboard().text() == "old output"

    restore_console_text(console=console, text=text_before)
    select_previous_output(console=console)
    press_modified_key(
        console=console,
        key=QtCore.Qt.Key.Key_Control,
        modifiers=QtCore.Qt.KeyboardModifier.ControlModifier,
    )
    assert console.textCursor().hasSelection()
    QtWidgets.QApplication.clipboard().clear()
    press_modified_key(
        console=console,
        key=QtCore.Qt.Key.Key_C,
        modifiers=QtCore.Qt.KeyboardModifier.ControlModifier,
        text="c",
    )
    assert QtWidgets.QApplication.clipboard().text() == "old output"

    copy_variants: list[tuple[QtCore.Qt.KeyboardModifier, str]] = list((
        (QtCore.Qt.KeyboardModifier.ControlModifier, ""),
        (QtCore.Qt.KeyboardModifier.ControlModifier, "\x03"),
        (QtCore.Qt.KeyboardModifier.ControlModifier | QtCore.Qt.KeyboardModifier.ShiftModifier, "c"),
    ))
    copy_modifiers: QtCore.Qt.KeyboardModifier
    copy_text: str
    for copy_modifiers, copy_text in copy_variants:
        restore_console_text(console=console, text=text_before)
        select_previous_output(console=console)
        QtWidgets.QApplication.clipboard().clear()
        press_modified_key(
            console=console,
            key=QtCore.Qt.Key.Key_C,
            modifiers=copy_modifiers,
            text=copy_text,
        )
        assert QtWidgets.QApplication.clipboard().text() == "old output"

    mime_data: QtCore.QMimeData = QtCore.QMimeData()
    mime_data.setText("PASTE")
    console.insertFromMimeData(mime_data)
    assert console.toPlainText() == text_before

    protected_keys: list[QtCore.Qt.Key] = list((
        QtCore.Qt.Key.Key_Tab,
        QtCore.Qt.Key.Key_Return,
        QtCore.Qt.Key.Key_Enter,
        QtCore.Qt.Key.Key_Up,
        QtCore.Qt.Key.Key_Down,
        QtCore.Qt.Key.Key_Backspace,
        QtCore.Qt.Key.Key_Delete,
    ))
    console._history.append("history")
    console._history_index = len(console._history)
    protected_key: QtCore.Qt.Key
    for protected_key in protected_keys:
        restore_console_text(console=console, text=text_before)
        console._history_index = len(console._history)
        select_previous_output(console=console)
        press_key(console=console, key=protected_key)
        assert console.toPlainText().startswith("old output\n")

    restore_console_text(console=console, text=text_before)
    mime_data.setText("PASTE")
    console.insertFromMimeData(mime_data)
    assert console.toPlainText().endswith(">>> PASTE")

    restore_console_text(console=console, text=text_before)
    select_previous_output(console=console)
    QtCore.QTimer.singleShot(0, close_active_popup)
    context_event: QtGui.QContextMenuEvent = QtGui.QContextMenuEvent(
        QtGui.QContextMenuEvent.Reason.Mouse,
        QtCore.QPoint(0, 0),
        QtCore.QPoint(0, 0),
    )
    console.contextMenuEvent(context_event)
    assert console.toPlainText() == text_before

    console.deleteLater()
    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
    application.processEvents()


def test_console_reset_discards_pending_multiline_state() -> None:
    """Verify reset clears invisible command state as well as visible text.

    :return: None.
    """
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    console: PythonConsole = PythonConsole()
    console._buffer.append("if True:")
    console._selecting_previous_text = True

    console.reset()

    assert console.toPlainText() == ">>> "
    assert len(console._buffer) == 0
    assert not console._selecting_previous_text

    console.deleteLater()
    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
    application.processEvents()
