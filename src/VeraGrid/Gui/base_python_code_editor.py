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
    """Common Python editing surface with indentation and optional line numbers."""

    # PySide/Shiboken does not safely support non-empty ``__slots__`` on an
    # intermediate QWidget class that is subclassed again in Python. Repeated
    # creation/destruction otherwise corrupts the binary wrapper. The concrete
    # editor subclasses remain final and slotted where Shiboken supports it.
    __slots__ = ()

    def __init__(
            self,
            parent: QtWidgets.QWidget | None = None,
            show_line_numbers: bool = True,
    ) -> None:
        """Create the shared source editor behavior.

        :param parent: Optional owning Qt widget.
        :param show_line_numbers: Whether the editor reserves and paints a gutter.
        :return: None.
        """
        super().__init__(parent)
        self._tab_text: str = "    "
        self._show_line_numbers: bool = show_line_numbers
        self._line_number_area: PythonLineNumberArea | None = None
        self._applying_editor_palette: bool = False
        self._line_number_gutter_color: QtGui.QColor = QtGui.QColor(240, 242, 245)
        self._line_number_text_color: QtGui.QColor = QtGui.QColor(95, 100, 110)
        if self._show_line_numbers:
            self._line_number_area = PythonLineNumberArea(self)
        else:
            pass

        # Both specialized editors display Python-like source. A fixed-width
        # font, four-space tabs, and no wrapping preserve source alignment.
        editor_font: QtGui.QFont = QtGui.QFont("Consolas", CONSOLE_TEXT_SIZE)
        self.setFont(editor_font)
        self.setTabStopDistance(float(self.fontMetrics().horizontalAdvance(self._tab_text)))
        self.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)
        self.setTabChangesFocus(False)
        BasePythonCodeEditor.set_light_mode(self)

        # Keep the gutter synchronized with document growth and scrolling only
        # for editors that actually display line numbers.
        if self._show_line_numbers:
            self.blockCountChanged.connect(self.update_line_number_area_width)
            self.updateRequest.connect(self.update_line_number_area)
        else:
            pass
        self.update_line_number_area_width(0)

    def apply_editor_theme(self, dark_theme: bool) -> None:
        """Apply explicit editor and gutter colors.

        :param dark_theme: Whether to use dark editor colors.
        :return: None.
        """
        if self._applying_editor_palette:
            return
        else:
            pass

        self._applying_editor_palette = True
        editor_palette: QtGui.QPalette = QtGui.QPalette(self.palette())

        if dark_theme:
            base_color: QtGui.QColor = QtGui.QColor(30, 30, 30)
            gutter_color: QtGui.QColor = QtGui.QColor(37, 37, 38)
            text_color: QtGui.QColor = QtGui.QColor(245, 245, 245)
            gutter_text_color: QtGui.QColor = QtGui.QColor(160, 165, 175)
        else:
            base_color = QtGui.QColor(255, 255, 255)
            gutter_color = QtGui.QColor(240, 242, 245)
            text_color = QtGui.QColor(20, 20, 20)
            gutter_text_color = QtGui.QColor(95, 100, 110)

        self._line_number_gutter_color = QtGui.QColor(gutter_color)
        self._line_number_text_color = QtGui.QColor(gutter_text_color)

        color_groups: tuple[QtGui.QPalette.ColorGroup, ...] = (
            QtGui.QPalette.ColorGroup.Active,
            QtGui.QPalette.ColorGroup.Inactive,
            QtGui.QPalette.ColorGroup.Disabled,
        )
        color_group: QtGui.QPalette.ColorGroup
        for color_group in color_groups:
            editor_palette.setColor(color_group, QtGui.QPalette.ColorRole.Base, base_color)
            editor_palette.setColor(color_group, QtGui.QPalette.ColorRole.Window, base_color)
            editor_palette.setColor(color_group, QtGui.QPalette.ColorRole.Text, text_color)
            editor_palette.setColor(color_group, QtGui.QPalette.ColorRole.WindowText, text_color)
            editor_palette.setColor(color_group, QtGui.QPalette.ColorRole.AlternateBase, gutter_color)
            editor_palette.setColor(color_group, QtGui.QPalette.ColorRole.PlaceholderText, gutter_text_color)
        self.setPalette(editor_palette)
        self.viewport().setAutoFillBackground(True)
        self.viewport().setBackgroundRole(QtGui.QPalette.ColorRole.Base)
        self.viewport().setPalette(editor_palette)
        self.setStyleSheet(
            f"background-color: {base_color.name()};"
            f"color: {text_color.name()};"
        )
        self.viewport().setStyleSheet(f"background-color: {base_color.name()};")

        if self._line_number_area is not None:
            self._line_number_area.setPalette(editor_palette)
            self._line_number_area.setStyleSheet(f"background-color: {gutter_color.name()};")
            self._line_number_area.update()
        else:
            pass
        self._applying_editor_palette = False

    def set_dark_mode(self) -> None:
        """Apply the dark editor theme.

        :return: None.
        """
        self.apply_editor_theme(dark_theme=True)

    def set_light_mode(self) -> None:
        """Apply the light editor theme.

        :return: None.
        """
        self.apply_editor_theme(dark_theme=False)

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
        if self._show_line_numbers:
            self.setViewportMargins(self.get_line_number_area_width(), 0, 0, 0)
        else:
            self.setViewportMargins(0, 0, 0, 0)

    @QtCore.Slot(QtCore.QRect, int)
    def update_line_number_area(self, rectangle: QtCore.QRect, vertical_delta: int) -> None:
        """Scroll or repaint the gutter together with the text viewport.

        :param rectangle: Viewport region that changed.
        :param vertical_delta: Vertical scroll displacement.
        :return: None.
        """
        if not self._show_line_numbers or self._line_number_area is None:
            pass
        elif vertical_delta != 0:
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
        if self._show_line_numbers and self._line_number_area is not None:
            contents_rectangle: QtCore.QRect = self.contentsRect()
            self._line_number_area.setGeometry(
                QtCore.QRect(
                    contents_rectangle.left(),
                    contents_rectangle.top(),
                    self.get_line_number_area_width(),
                    contents_rectangle.height(),
                )
            )
        else:
            pass

    def paint_line_number_area(self, event: QtGui.QPaintEvent) -> None:
        """Paint line numbers for every visible text block.

        :param event: Gutter repaint event.
        :return: None.
        """
        if self._line_number_area is None:
            return
        else:
            pass
        painter: QtGui.QPainter = QtGui.QPainter(self._line_number_area)
        painter.fillRect(event.rect(), self._line_number_gutter_color)
        painter.setPen(self._line_number_text_color)
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
