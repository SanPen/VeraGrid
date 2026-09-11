# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.001--.0-
from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets


class DeviceSelectionLabel(QtWidgets.QLabel):
    """Label that requests device selection through pointer or keyboard input."""

    __slots__ = ()

    clicked = QtCore.Signal()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """Emit the selection request for a left-button click.

        :param event: Incoming label mouse event.
        :return: None.
        """
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.clicked.emit()
            event.accept()
        else:
            QtWidgets.QLabel.mousePressEvent(self, event)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """Emit the selection request for Enter, Return or Space.

        :param event: Incoming label key event.
        :return: None.
        """
        selection_keys: tuple[QtCore.Qt.Key, ...] = (
            QtCore.Qt.Key.Key_Enter,
            QtCore.Qt.Key.Key_Return,
            QtCore.Qt.Key.Key_Space,
        )
        if event.key() in selection_keys:
            self.clicked.emit()
            event.accept()
        else:
            QtWidgets.QLabel.keyPressEvent(self, event)
