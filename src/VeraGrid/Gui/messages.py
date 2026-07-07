# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0


from PySide6 import QtWidgets


class CenteredMessageBox(QtWidgets.QMessageBox):
    def __init__(self, parent=None):
        super().__init__(parent)

    def showEvent(self, event):
        super().showEvent(event)
        if self.parent():
            parent_geo = self.parent().geometry()
            self.move(
                parent_geo.center().x() - self.width() // 2,
                parent_geo.center().y() - self.height() // 2
            )


def info_msg(text, title="Information"):
    """
    Message box
    :param text: Text to display
    :param title: Name of the window
    """
    msg = CenteredMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Icon.Information)
    msg.setText(text)
    msg.setWindowTitle(title)
    msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
    return msg.exec()


def warning_msg(text: str, title: str = "Warning") -> int:
    """
    Message box
    :param text: Text to display
    :param title: Name of the window
    """
    msg = CenteredMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
    msg.setText(text)
    msg.setWindowTitle(title)
    msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
    return msg.exec()


def error_msg(text: str, title: str = "Error") -> int:
    """
    Message box
    :param text: Text to display
    :param title: Name of the window
    """
    msg = CenteredMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Icon.Critical)
    msg.setText(text)
    msg.setWindowTitle(title)
    msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
    return msg.exec()


def yes_no_question(text: str, title: str = 'Question') -> bool:
    """
    Question message
    :param text:
    :param title:
    :return: True / False
    """
    buttonReply = QtWidgets.QMessageBox.question(
        None,
        title,
        text,
        QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
        QtWidgets.QMessageBox.StandardButton.No
    )
    return buttonReply == QtWidgets.QMessageBox.StandardButton.Yes.value
