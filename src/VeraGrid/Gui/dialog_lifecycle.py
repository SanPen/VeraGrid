# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import shiboken6
from PySide6 import QtCore, QtWidgets


def is_dialog_available(dialog: QtWidgets.QWidget | None) -> bool:
    """
    Return whether a stored Qt widget pointer still wraps a live C++ widget.

    :param dialog: Stored Qt widget pointer.
    :return: ``True`` when the pointer can be reused.
    """
    if dialog is None:
        result: bool = False
    else:
        result = shiboken6.isValid(dialog)

    return result


def delete_dialog_safely(dialog: object) -> None:
    """
    Schedule one Qt dialog/widget for deletion and flush deferred delete events.

    :param dialog: Qt widget to delete.
    :return: None.
    """
    if isinstance(dialog, QtWidgets.QWidget):
        if shiboken6.isValid(dialog):
            dialog.deleteLater()
            app: QtWidgets.QApplication | None = QtWidgets.QApplication.instance()
            if app is not None:
                QtCore.QCoreApplication.sendPostedEvents(dialog, QtCore.QEvent.Type.DeferredDelete)
                app.processEvents()
            else:
                pass
        else:
            pass
    else:
        pass


def exec_dialog_safely(dialog: QtWidgets.QDialog) -> int:
    """
    Execute one modal dialog and always schedule it for deletion afterwards.

    :param dialog: Modal dialog to execute.
    :return: Qt dialog result code.
    """
    try:
        result: int = int(dialog.exec())
    finally:
        delete_dialog_safely(dialog=dialog)

    return result
