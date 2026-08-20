# SPDX-License-Identifier: MPL-2.0
"""Shared visual foundation for VeraGrid Python source editors."""

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets

from VeraGrid.Gui.font_config import CONSOLE_TEXT_SIZE


class PythonLineNumberArea(QtWidgets.QWidget):
    """Gutter that delegates line-number geometry and painting to its editor."""

    __slots__ = ("_editor",)

    def __init__(self, editor: "BasePythonCodeEditor") -> None:
        """Create a gutter owned by one Python editor.

        :param editor: Editor whose visible text blocks are numbered.
        :return: None.
        """
        super().__init__(editor)
        self._editor: BasePythonCodeEditor = editor

    def sizeHint(self) -> QtCore.QSize:
        """Return the width required by the editor's current line count.

        :return: Gutter size hint.
        """
        return QtCore.QSize(self._editor.get_line_number_area_width(), 0)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        """Delegate visible line-number painting to the editor.

        :param event: Gutter repaint request.
        :return: None.
        """
        self._editor.paint_line_number_area(event)


class BasePythonCodeEditor(QtWidgets.QPlainTextEdit):
    """Common Python editing surface with indentation and line numbers."""

    # PySide/Shiboken does not safely support non-empty ``__slots__`` on an
    # intermediate QWidget class that is subclassed again in Python. Repeated
    # creation/destruction otherwise corrupts the binary wrapper. The concrete
    # editor subclasses remain final and slotted where Shiboken supports it.
    __slots__ = ()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Create the shared source editor behavior.

        :param parent: Optional owning Qt widget.
        :return: None.
        """
        super().__init__(parent)
        self._tab_text: str = "    "
        self._line_number_area: PythonLineNumberArea = PythonLineNumberArea(self)

        # Both specialized editors display Python-like source. A fixed-width
        # font, four-space tabs, and no wrapping preserve source alignment.
        editor_font: QtGui.QFont = QtGui.QFont("Consolas", CONSOLE_TEXT_SIZE)
        self.setFont(editor_font)
        self.setTabStopDistance(float(self.fontMetrics().horizontalAdvance(self._tab_text)))
        self.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)
        self.setTabChangesFocus(False)

        # Keep the gutter synchronized with document growth and scrolling.
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.update_line_number_area_width(0)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """Insert four spaces for Tab and delegate every other key.

        :param event: Incoming keyboard event.
        :return: None.
        """
        if event.key() == QtCore.Qt.Key.Key_Tab:
            text_cursor: QtGui.QTextCursor = self.textCursor()
            text_cursor.insertText(self._tab_text)
            self.setTextCursor(text_cursor)
            event.accept()
        else:
            QtWidgets.QPlainTextEdit.keyPressEvent(self, event)

    def get_line_number_area_width(self) -> int:
        """Return the gutter width required by the largest line number.

        :return: Gutter width in pixels.
        """
        digit_count: int = 1
        maximum_line: int = max(1, self.blockCount())
        while maximum_line >= 10:
            maximum_line //= 10
            digit_count += 1
        spacing: int = 10 + self.fontMetrics().horizontalAdvance("9") * digit_count
        return spacing

    @QtCore.Slot(int)
    def update_line_number_area_width(self, unused_block_count: int) -> None:
        """Reserve viewport space after the document line count changes.

        :param unused_block_count: Qt-provided line count.
        :return: None.
        """
        _unused_block_count: int = unused_block_count
        self.setViewportMargins(self.get_line_number_area_width(), 0, 0, 0)

    @QtCore.Slot(QtCore.QRect, int)
    def update_line_number_area(self, rectangle: QtCore.QRect, vertical_delta: int) -> None:
        """Scroll or repaint the gutter together with the text viewport.

        :param rectangle: Viewport region that changed.
        :param vertical_delta: Vertical scroll displacement.
        :return: None.
        """
        if vertical_delta != 0:
            self._line_number_area.scroll(0, vertical_delta)
        else:
            self._line_number_area.update(
                0,
                rectangle.y(),
                self._line_number_area.width(),
                rectangle.height(),
            )
        if rectangle.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)
        else:
            pass

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        """Keep the gutter aligned with the editor contents rectangle.

        :param event: Editor resize event.
        :return: None.
        """
        QtWidgets.QPlainTextEdit.resizeEvent(self, event)
        contents_rectangle: QtCore.QRect = self.contentsRect()
        self._line_number_area.setGeometry(
            QtCore.QRect(
                contents_rectangle.left(),
                contents_rectangle.top(),
                self.get_line_number_area_width(),
                contents_rectangle.height(),
            )
        )

    def paint_line_number_area(self, event: QtGui.QPaintEvent) -> None:
        """Paint line numbers for every visible text block.

        :param event: Gutter repaint event.
        :return: None.
        """
        painter: QtGui.QPainter = QtGui.QPainter(self._line_number_area)
        painter.fillRect(event.rect(), self.palette().alternateBase())
        painter.setPen(self.palette().placeholderText().color())
        text_block: QtGui.QTextBlock = self.firstVisibleBlock()
        block_number: int = text_block.blockNumber()
        top: int = int(self.blockBoundingGeometry(text_block).translated(self.contentOffset()).top())
        bottom: int = top + int(self.blockBoundingRect(text_block).height())

        # Only visible blocks are visited, so numbering remains inexpensive for
        # long scripts and generated DAE source.
        while text_block.isValid() and top <= event.rect().bottom():
            if text_block.isVisible() and bottom >= event.rect().top():
                line_number: str = str(block_number + 1)
                painter.drawText(
                    0,
                    top,
                    self._line_number_area.width() - 5,
                    self.fontMetrics().height(),
                    QtCore.Qt.AlignmentFlag.AlignRight,
                    line_number,
                )
            else:
                pass
            text_block = text_block.next()
            top = bottom
            if text_block.isValid():
                bottom = top + int(self.blockBoundingRect(text_block).height())
            else:
                pass
            block_number += 1
