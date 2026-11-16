# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import Dict
from uuid import uuid4
import shiboken6
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QDialog


class WindowManager:
    """
    Manager for application secondary windows and dialogues.
    """

    __slots__ = ("__parent", "__win", "__weakref__")

    def __init__(self, main_window: QMainWindow):
        """
        Constructor.

        :param main_window: Main window using this manager.
        """
        self.__parent: QMainWindow = main_window
        self.__win: Dict[str, QMainWindow | QDialog] = dict()

    def _handle_window_destroyed(self, destroyed_object: object = None) -> None:
        """
        Callback function on window deletion to remove its reference.

        :param destroyed_object: Qt destroyed object pointer.
        :return: None.
        """
        # Collect dead keys where the widget matches destroyed object or is invalidated
        dead_keys: list[str] = list()
        key_name: str
        managed_window: QMainWindow | QDialog
        for key_name, managed_window in list(self.__win.items()):
            if managed_window is destroyed_object or not shiboken6.isValid(managed_window):
                dead_keys.append(key_name)

        # Pop all dead references from the registry
        dead_key: str
        for dead_key in dead_keys:
            self.__win.pop(dead_key, None)

    def get(self, key: str) -> QMainWindow | QDialog | None:
        """
        Try to obtain a window by its key.

        :param key: Key to refer to the window.
        :return: Window or None if not found.
        """
        win: QMainWindow | QDialog | None = self.__win.get(key, None)
        if win is not None and not shiboken6.isValid(win):
            self.__win.pop(key, None)
            return None
        return win

    def has(self, key: str) -> bool:
        """
        Check whether a valid window is currently registered under key.

        :param key: Key to refer to the window.
        :return: True if registered and valid, False otherwise.
        """
        return self.get(key=key) is not None

    def remove(self, key: str) -> None:
        """
        Remove a window reference from management.

        :param key: Key to refer to the window.
        :return: None.
        """
        self.__win.pop(key, None)

    def get_all_windows(self) -> list[QMainWindow | QDialog]:
        """
        Return all valid registered windows.

        :return: List of active windows.
        """
        active: list[QMainWindow | QDialog] = list()
        key: str
        win: QMainWindow | QDialog
        for key, win in list(self.__win.items()):
            if win is not None and shiboken6.isValid(win):
                active.append(win)
            else:
                self.__win.pop(key, None)
        return active

    def close_all(self) -> bool:
        """
        Close all active managed windows.

        :return: True if all accepted close, False otherwise.
        """
        all_closed: bool = True
        win: QMainWindow | QDialog
        for win in self.get_all_windows():
            if not win.close():
                all_closed = False
        return all_closed

    def show(self,
             win: QMainWindow | QDialog,
             key: str | None = None,
             delete_on_close: bool = True) -> QMainWindow | QDialog:
        """
        Safely display a window.

        :param win: Window instance.
        :param key: Key to refer to the window.
        :param delete_on_close: Whether the window is deleted when closed.
        :return: Passed window if not registered, existing window if existing.
        """
        # Assign generated key if none was provided
        if key is None:
            key = f"{win.__class__.__name__}_{id(win)}_{uuid4().hex}"

        # Reuse existing window if already present and valid
        existing_window: QMainWindow | QDialog | None = self.get(key=key)
        if existing_window is not None and shiboken6.isValid(existing_window):
            if existing_window is not win:
                win.deleteLater()

            existing_window.show()
            existing_window.raise_()
            existing_window.activateWindow()
            return existing_window
        else:
            self.__win.pop(key, None)

        # Hook destroyed signal to remove reference from tracking without lambdas
        win.destroyed.connect(self._handle_window_destroyed)

        # Ensure the properly declared parent is actually the parent
        if win.parent() is not self.__parent:
            win.setParent(self.__parent)

        # Enforce Window Flags & Deletion Attribute
        win.setWindowFlags(win.windowFlags() | Qt.WindowType.Window)
        win.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, delete_on_close)

        # Store and display
        self.__win[key] = win
        win.show()
        win.raise_()
        win.activateWindow()
        return win
