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
            delete_child_widgets_safely(widget=dialog)
            try:
                dialog.deleteLater()
                QtCore.QCoreApplication.sendPostedEvents(dialog, QtCore.QEvent.Type.DeferredDelete)
            except Exception:
                pass
            else:
                pass
        else:
            pass
    else:
        pass


def delete_child_widgets_safely(widget: QtWidgets.QWidget) -> None:
    """
    Schedule every child widget owned by a Qt widget for deferred deletion.

    :param widget: Parent widget whose owned children must be released.
    :return: None.
    """
    children: list[QtWidgets.QWidget] = widget.findChildren(QtWidgets.QWidget)
    child: QtWidgets.QWidget

    for child in children:
        if shiboken6.isValid(child):
            child.close()
            try:
                child.deleteLater()
            except Exception:
                pass
            else:
                pass
        else:
            pass

    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)


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
