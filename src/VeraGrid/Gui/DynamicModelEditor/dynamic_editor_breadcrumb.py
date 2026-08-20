# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import List

from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont

from VeraGridEngine.Utils.Symbolic.block import Block


class _BreadcrumbClickHandler(QtCore.QObject):
    """
    Bind one breadcrumb button to one block instance.

    The breadcrumb recreates buttons often while navigating. Using an explicit
    QObject slot avoids lambda-based captures and keeps the click lifetime tied
    to the Qt parent/child ownership tree.

    :param owner: Breadcrumb widget that will emit the navigation signal.
    :param block: Block associated with one button.
    """

    __slots__ = ("_owner", "_block")

    def __init__(self, owner: "DynamicEditorBreadcrumb", block: Block) -> None:
        """
        Initialize one click handler.

        :param owner: Breadcrumb widget that owns the handler.
        :param block: Block emitted when the button is clicked.
        :return: None.
        """
        super().__init__(owner)
        self._owner: DynamicEditorBreadcrumb = owner
        self._block: Block = block

    def emit_block_clicked(self) -> None:
        """
        Forward the stored block through the breadcrumb signal.

        :return: None.
        """
        self._owner.blockClicked.emit(self._block)


class DynamicEditorBreadcrumb(QtWidgets.QWidget):
    """
    Visual breadcrumb showing the path from the root block to the current block.

    Each block in the path is rendered as a ``QToolButton`` separated by a
    disabled ``QToolButton`` showing ``>``.  Clicking a block button emits
    :pyattr:`blockClicked` with the corresponding :class:`Block`.

    The breadcrumb items occupy only the width they need and are left-aligned.
    Remaining space is left empty on the right, like a file-manager path bar.
    """

    __slots__ = ()

    blockClicked = Signal(object)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Create an empty breadcrumb container.

        :param parent: Owning editor tab.
        :return: None.
        """
        super().__init__(parent)
        self.setFixedHeight(22)
        self._click_handlers: List[_BreadcrumbClickHandler] = list()

        # Shared font — one point smaller than the default.
        self._font = QFont(self.font())
        self._font.setPointSize(self._font.pointSize() - 1)

        # Inner container that holds only the breadcrumb items.
        self._container = QtWidgets.QWidget()
        self._container_layout = QtWidgets.QHBoxLayout(self._container)
        self._container_layout.setContentsMargins(0, 0, 0, 0)
        self._container_layout.setSpacing(0)

        # Main layout: container on the left, stretch on the right.
        self._layout = QtWidgets.QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self._container)
        self._layout.addStretch(1)

    def set_path(self, blocks: List[Block]) -> None:
        """
        Replace the current breadcrumb with a new path.

        :param blocks: Ordered list of blocks from root to current.
        :return: None.
        """
        self._clear()

        for i, block in enumerate(blocks):
            if i > 0:
                sep = self._make_separator()
                self._container_layout.addWidget(sep)
            else:
                pass

            button = self._make_block_button(block, is_last=(i == len(blocks) - 1))
            self._container_layout.addWidget(button)

    def prepare_to_delete(self) -> None:
        """
        Delete the runtime-created breadcrumb buttons and their handlers.

        :return: None.
        """
        self._clear()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _make_block_button(self, block: Block, is_last: bool = False) -> QtWidgets.QToolButton:
        """
        Create a breadcrumb button for *block*.

        :param block: Symbolic block used by the operation.
        :param is_last: Whether this is the final breadcrumb item.
        :return: Breadcrumb button associated with *block*.
        """
        button = QtWidgets.QToolButton()
        button.setText(block.name)
        button.setAutoRaise(True)
        button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextOnly)
        button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        button.setFont(self._font)
        button.setStyleSheet(
            "QToolButton {"
            "  border: none; background: transparent;"
            "  padding: 0 2px;"
            "}"
            "QToolButton:hover { text-decoration: underline; }"
        )
        button.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        if is_last:
            bold = QFont(self._font)
            bold.setBold(True)
            button.setFont(bold)
        else:
            pass

        click_handler = _BreadcrumbClickHandler(self, block)
        self._click_handlers.append(click_handler)
        button.clicked.connect(click_handler.emit_block_clicked)
        return button

    def _make_separator(self) -> QtWidgets.QToolButton:
        """
        Create a disabled separator button showing ``>``.

        :return: Disabled separator button showing ``>``.
        """
        sep = QtWidgets.QToolButton()
        sep.setText(">")
        sep.setAutoRaise(True)
        sep.setEnabled(False)
        sep.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextOnly)
        sep.setFont(self._font)
        sep.setStyleSheet(
            "QToolButton {"
            "  border: none; background: transparent;"
            "  padding: 0 2px; color: #888;"
            "}"
        )
        sep.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        return sep

    def _clear(self) -> None:
        """
        Remove all widgets from the container layout.

        :return: None.
        """
        self._click_handlers.clear()
        while self._container_layout.count() > 0:
            item = self._container_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                # Detach each button explicitly so Qt does not keep parent-child
                # ownership alive longer than the breadcrumb path that created it.
                widget.setParent(None)
                widget.deleteLater()
            else:
                pass
