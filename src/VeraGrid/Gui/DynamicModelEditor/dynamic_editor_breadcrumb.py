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


class DynamicEditorBreadcrumb(QtWidgets.QWidget):
    """
    Visual breadcrumb showing the path from the root block to the current block.

    Each block in the path is rendered as a ``QToolButton`` separated by a
    disabled ``QToolButton`` showing ``>``.  Clicking a block button emits
    :pyattr:`blockClicked` with the corresponding :class:`Block`.

    The breadcrumb items occupy only the width they need and are left-aligned.
    Remaining space is left empty on the right, like a file-manager path bar.
    """

    blockClicked = Signal(object)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(22)

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

            button = self._make_block_button(block, is_last=(i == len(blocks) - 1))
            self._container_layout.addWidget(button)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _make_block_button(self, block: Block, is_last: bool = False) -> QtWidgets.QToolButton:
        """Create a breadcrumb button for *block*."""
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

        button.clicked.connect(
            lambda _checked=False, b=block: self.blockClicked.emit(b)
        )
        return button

    def _make_separator(self) -> QtWidgets.QToolButton:
        """Create a disabled separator button showing ``>``."""
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
        """Remove all widgets from the container layout."""
        while self._container_layout.count() > 0:
            item = self._container_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                pass
