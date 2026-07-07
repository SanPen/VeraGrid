# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

from PySide6 import QtWidgets
from PySide6.QtCore import QCoreApplication, QT_TRANSLATE_NOOP

# ponytail: keep these stock message-box titles visible to lupdate so the
# compiled catalog always contains the "messages" context used at runtime.
MESSAGE_TRANSLATION_KEYS: tuple[str, str, str, str] = (
    QT_TRANSLATE_NOOP("messages", "Information"),
    QT_TRANSLATE_NOOP("messages", "Warning"),
    QT_TRANSLATE_NOOP("messages", "Error"),
    QT_TRANSLATE_NOOP("messages", "Question"),
)


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


def info_msg(text, title=None):
    """
    Message box
    :param text: Text to display
    :param title: Name of the window
    """
    msg = CenteredMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Icon.Information)
    msg.setText(text)
    default_title: str = QCoreApplication.translate("messages", "Information")
    if title is None:
        window_title: str = default_title
    else:
        window_title = title
    msg.setWindowTitle(window_title)
    msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
    return msg.exec()


def warning_msg(text: str, title: str | None = None) -> int:
    """
    Message box
    :param text: Text to display
    :param title: Name of the window
    """
    msg = CenteredMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
    msg.setText(text)
    default_title: str = QCoreApplication.translate("messages", "Warning")
    if title is None:
        window_title: str = default_title
    else:
        window_title = title
    msg.setWindowTitle(window_title)
    msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
    return msg.exec()


def error_msg(text: str, title: str | None = None) -> int:
    """
    Message box
    :param text: Text to display
    :param title: Name of the window
    """
    msg = CenteredMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Icon.Critical)
    msg.setText(text)
    default_title: str = QCoreApplication.translate("messages", "Error")
    if title is None:
        window_title: str = default_title
    else:
        window_title = title
    msg.setWindowTitle(window_title)
    msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
    return msg.exec()


def yes_no_question(text: str, title: str | None = None) -> bool:
    """
    Question message
    :param text:
    :param title:
    :return: True / False
    """
    default_title: str = QCoreApplication.translate("messages", "Question")
    if title is None:
        window_title: str = default_title
    else:
        window_title = title
    buttonReply = QtWidgets.QMessageBox.question(
        None,
        window_title,
        text,
        QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
        QtWidgets.QMessageBox.StandardButton.No
    )
    return buttonReply == QtWidgets.QMessageBox.StandardButton.Yes.value
