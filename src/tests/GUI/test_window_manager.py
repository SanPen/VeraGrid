# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from VeraGrid.Gui.Main.SubClasses.window_manager import WindowManager


def test_window_manager_reuses_and_replaces_closed_keyed_windows(qt_app: QtWidgets.QApplication) -> None:
    """Keyed windows reopen consistently after close and deferred deletion.

    :param qt_app: Shared Qt application.
    :return: None.
    """
    parent_window: QtWidgets.QMainWindow = QtWidgets.QMainWindow()
    window_manager: WindowManager = WindowManager(main_window=parent_window)
    first_dialog: QtWidgets.QDialog = QtWidgets.QDialog(parent_window)

    registered_dialog: QtWidgets.QMainWindow | QtWidgets.QDialog = window_manager.show(
        win=first_dialog,
        key="sigma_analysis_dialogue",
    )
    assert registered_dialog is first_dialog

    redundant_dialog: QtWidgets.QDialog = QtWidgets.QDialog(parent_window)
    reused_dialog: QtWidgets.QMainWindow | QtWidgets.QDialog = window_manager.show(
        win=redundant_dialog,
        key="sigma_analysis_dialogue",
    )
    assert reused_dialog is first_dialog
    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)

    first_dialog.close()
    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
    qt_app.processEvents()
    assert window_manager.get(key="sigma_analysis_dialogue") is None

    replacement_dialog: QtWidgets.QDialog = QtWidgets.QDialog(parent_window)
    replacement_window: QtWidgets.QMainWindow | QtWidgets.QDialog = window_manager.show(
        win=replacement_dialog,
        key="sigma_analysis_dialogue",
    )
    assert replacement_window is replacement_dialog

    replacement_dialog.close()
    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
    parent_window.close()


def test_window_manager_retains_persistent_dialogue(qt_app: QtWidgets.QApplication) -> None:
    """Persistent dialogues (e.g. AI dialogue) are retained when delete_on_close is False.

    :param qt_app: Shared Qt application.
    :return: None.
    """
    parent_window: QtWidgets.QMainWindow = QtWidgets.QMainWindow()
    window_manager: WindowManager = WindowManager(main_window=parent_window)
    persistent_dialog: QtWidgets.QDialog = QtWidgets.QDialog(parent_window)

    window_manager.show(
        win=persistent_dialog,
        key="AI_chat",
        delete_on_close=False,
    )
    assert window_manager.has(key="AI_chat")
    assert window_manager.get(key="AI_chat") is persistent_dialog

    # Simulating hide or close without WA_DeleteOnClose
    persistent_dialog.hide()
    assert window_manager.has(key="AI_chat")
    assert window_manager.get(key="AI_chat") is persistent_dialog

    # Re-showing the persistent dialogue reuses it
    shown: QtWidgets.QMainWindow | QtWidgets.QDialog = window_manager.show(
        win=persistent_dialog,
        key="AI_chat",
        delete_on_close=False,
    )
    assert shown is persistent_dialog
    assert len(window_manager.get_all_windows()) == 1

    persistent_dialog.deleteLater()
    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
    qt_app.processEvents()
    assert not window_manager.has(key="AI_chat")
    assert window_manager.get(key="AI_chat") is None
    parent_window.close()

