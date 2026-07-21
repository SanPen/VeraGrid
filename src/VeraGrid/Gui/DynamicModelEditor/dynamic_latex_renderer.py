# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
LaTeX equation rendering for the Dynamic Block Editor equations table.

Architecture::

    LaTeX string
        ↓
    LatexRenderer  (matplotlib → QPixmap + QSize, cached)
        ↓
    LatexEquationDelegate  (sizeHint + paint, no scaling)
        ↓
    QTableView  (ResizeToContents on vertical header)
        ↓
    Row height adapts to the real equation size.

This module lives entirely on the GUI side and never touches the
symbolic expression tree.
"""

from __future__ import annotations

from io import BytesIO
from typing import NamedTuple

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

_MIN_ROW_HEIGHT = 24


class RenderedEquation(NamedTuple):
    pixmap: QPixmap
    size: QtCore.QSize


# ---------------------------------------------------------------------------
# LatexRenderer  –  matplotlib mathtext → QPixmap with cache
# ---------------------------------------------------------------------------


class LatexRenderer:
    """
    Render a LaTeX math string into a :class:`QPixmap` using matplotlib.

    The pixmap has a fully transparent background so Qt's native
    selection / hover / alternating-row painting shows through.

    Uses ``bbox_inches='tight'`` with ``pad_inches=0`` so the image
    occupies exactly the real space of the equation — no white margins.

    A dictionary cache keyed by the raw LaTeX string avoids re-rendering
    the same equation on every repaint / sizeHint query.
    """

    def __init__(self, font_size: int = 12, dpi: int = 96) -> None:
        self._font_size = font_size
        self._dpi = dpi
        self._cache: dict[str, RenderedEquation] = dict()

    # -- public API --------------------------------------------------------

    def render(self, latex: str) -> RenderedEquation:
        """
        Return a cached :class:`RenderedEquation` for *latex*.

        If not yet in the cache it is rendered with matplotlib and stored.
        """
        cached = self._cache.get(latex)
        if cached is not None:
            return cached

        rendered = self._render_to_pixmap(latex)
        self._cache[latex] = rendered
        return rendered

    def invalidate(self, latex: str) -> None:
        """Remove one entry from the cache (called after an edit)."""
        self._cache.pop(latex, None)

    def clear(self) -> None:
        """Drop the entire cache."""
        self._cache.clear()

    # -- internals ---------------------------------------------------------

    def _render_to_pixmap(self, latex: str) -> RenderedEquation:
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg

        fig = Figure(dpi=self._dpi)
        FigureCanvasAgg(fig)
        fig.patch.set_alpha(0.0)

        # Use fig.text (not ax.text) so bbox_inches='tight' computes the
        # bounding box from the text glyphs alone, without axes geometry.
        self._draw_text(fig, latex)

        buf = BytesIO()
        fig.savefig(buf, format="png", transparent=True,
                    bbox_inches="tight", pad_inches=0)
        fig.clear()

        buf.seek(0)
        image = QtGui.QImage()
        image.loadFromData(buf.read())
        pixmap = QPixmap.fromImage(image)
        size = QtCore.QSize(pixmap.width(),
                            max(pixmap.height() + 4, _MIN_ROW_HEIGHT))
        return RenderedEquation(pixmap=pixmap, size=size)

    def _draw_text(self, fig, latex: str):
        """Draw the LaTeX text on *fig*, returning the text artist."""
        try:
            return fig.text(0, 0, f"${latex}$",
                            fontsize=self._font_size,
                            ha="left", va="baseline")
        except Exception:
            return fig.text(0, 0, latex,
                            fontsize=self._font_size,
                            ha="left", va="baseline")


# ---------------------------------------------------------------------------
# LatexEquationDelegate  –  sizeHint + paint, no scaling
# ---------------------------------------------------------------------------

_global_renderer: LatexRenderer | None = None


def _get_renderer() -> LatexRenderer:
    """Lazy singleton so every delegate shares one cache."""
    global _global_renderer
    if _global_renderer is None:
        _global_renderer = LatexRenderer()
    return _global_renderer


class LatexEquationDelegate(QtWidgets.QStyledItemDelegate):
    """
    Delegate that renders LaTeX equations in the equations table.

    Implements ``sizeHint()`` using the same cached render that
    ``paint()`` uses, so Qt can set the row height to the real
    equation size via ``ResizeToContents``.

    ``paint()`` never scales the pixmap — it centres the original-
    size image inside the cell rectangle.
    """

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._renderer = _get_renderer()

    # -- sizeHint ----------------------------------------------------------

    def sizeHint(self, option, index) -> QtCore.QSize:
        text = index.data(Qt.ItemDataRole.DisplayRole)
        if not text:
            return super().sizeHint(option, index)
        rendered = self._renderer.render(str(text))
        return rendered.size

    # -- paint -------------------------------------------------------------

    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex,
    ) -> None:
        self.initStyleOption(option, index)
        style = (option.widget.style() if option.widget
                 else QtWidgets.QApplication.style())
        style.drawPrimitive(
            QtWidgets.QStyle.PrimitiveElement.PE_PanelItemViewItem,
            option, painter, option.widget,
        )

        text = index.data(Qt.ItemDataRole.DisplayRole)
        if not text:
            return

        rendered = self._renderer.render(str(text))
        pixmap = rendered.pixmap

        rect = option.rect
        x = rect.x() + (rect.width() - pixmap.width()) // 2
        y = rect.y() + (rect.height() - pixmap.height()) // 2
        painter.drawPixmap(x, y, pixmap)

    # -- cache management --------------------------------------------------

    def invalidate(self, latex: str) -> None:
        """Drop one cached entry after the underlying data changes."""
        self._renderer.invalidate(latex)

    def clear_cache(self) -> None:
        """Drop the entire rendering cache."""
        self._renderer.clear()
