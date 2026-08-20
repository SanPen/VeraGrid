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

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.text import Text
from PySide6 import QtCore, QtGui, QtSvg, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap


class RenderedEquation:
    """Rendered equation image and its preferred Qt cell size."""

    __slots__ = ("_pixmap", "_size", "_uses_mathtext")

    def __init__(self,
                 pixmap: QPixmap,
                 size: QtCore.QSize,
                 uses_mathtext: bool) -> None:
        """Store one immutable rendering result.

        :param pixmap: Equation image.
        :param size: Preferred table-cell size.
        :param uses_mathtext: Whether mathematical parsing succeeded.
        :return: None.
        """
        self._pixmap: QPixmap = pixmap
        self._size: QtCore.QSize = size
        self._uses_mathtext: bool = uses_mathtext

    def get_pixmap(self) -> QPixmap:
        """
        :return: The rendered equation image.
        """
        return self._pixmap

    def get_size(self) -> QtCore.QSize:
        """
        :return: The preferred table-cell size.
        """
        return self._size

    def get_uses_mathtext(self) -> bool:
        """
        :return: Whether the source compiled instead of using plain text.
        """
        return self._uses_mathtext


class RenderedSvgEquation:
    """Self-contained vector equation and its intrinsic document size."""

    __slots__ = ("_data", "_size", "_uses_mathtext")

    def __init__(self,
                 data: QtCore.QByteArray,
                 size: QtCore.QSize,
                 uses_mathtext: bool) -> None:
        """Store one immutable SVG rendering result.

        :param data: Complete SVG document payload.
        :param size: Intrinsic logical display size.
        :param uses_mathtext: Whether mathematical parsing succeeded.
        :return: None.
        """
        self._data: QtCore.QByteArray = data
        self._size: QtCore.QSize = size
        self._uses_mathtext: bool = uses_mathtext

    def get_data(self) -> QtCore.QByteArray:
        """
        :return: The self-contained SVG document payload.
        """
        return self._data

    def get_size(self) -> QtCore.QSize:
        """
        :return: The intrinsic SVG display size.
        """
        return self._size

    def get_uses_mathtext(self) -> bool:
        """
        :return: Whether the SVG contains compiled mathematical glyphs.
        """
        return self._uses_mathtext


def normalize_mathtext_latex(latex: str) -> str:
    """Separate delimiter commands from adjacent symbolic variable names.

    VeraGrid's LaTeX printer may emit strings such as ``\\lvertVm`` when an
    absolute-value delimiter directly precedes ``Vm``. TeX understands where
    the command ends from broader parsing context, while Matplotlib MathText
    treats the complete ``lvertVm`` token as one unknown command.

    :param latex: LaTeX emitted by the symbolic printer.
    :return: MathText-compatible LaTeX with unambiguous delimiter tokens.
    """
    # Matplotlib MathText does not implement ``\lvert`` or ``\rvert`` even
    # though they are standard LaTeX. Its supported scalable equivalents
    # preserve the same absolute-value semantics and compile reliably.
    normalized: str = latex.replace(r"\lvert", r"\left|")
    normalized = normalized.replace(r"\rvert", r"\right|")
    return normalized


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

    __slots__ = (
        "_font_size",
        "_dpi",
        "_minimum_row_height",
        "_maximum_mathtext_length",
        "_cache",
        "_svg_cache",
    )

    def __init__(self, font_size: int = 12, dpi: int = 96) -> None:
        """Create a renderer with an isolated image cache.

        :param font_size: Equation font size in points.
        :param dpi: Raster rendering resolution.
        :return: None.
        """
        self._font_size: int = font_size
        self._dpi: int = dpi
        self._minimum_row_height: int = 24
        self._maximum_mathtext_length: int = 2000
        self._cache: dict[str, RenderedEquation] = dict()
        self._svg_cache: dict[str, RenderedSvgEquation] = dict()

    # -- public API --------------------------------------------------------

    def render(self, latex: str) -> RenderedEquation:
        """
        Return a cached :class:`RenderedEquation` for *latex*.

        If not yet in the cache it is rendered with matplotlib and stored.

        :param latex: LaTeX source handled by the operation.
        :return: A cached :class:`RenderedEquation` for *latex*.
        """
        cached: RenderedEquation | None = self._cache.get(latex, None)
        if cached is not None:
            return cached
        else:
            normalized_latex: str = normalize_mathtext_latex(latex)
            if len(normalized_latex) > self._maximum_mathtext_length:
                # Rendering an enormous symbolic expansion as one raster image
                # can abort a native graphics backend before Python receives an
                # exception. The complete source remains available in Python.
                preview_message: str = (
                    f"Equation is too large for graphical preview ({len(latex)} characters). "
                    "See Python code."
                )
                rendered: RenderedEquation = self._render_to_pixmap(preview_message, False)
            else:
                try:
                    rendered = self._render_to_pixmap(normalized_latex, True)
                except (RuntimeError, ValueError):
                    # A valid VeraGrid expression must never make Qt's delegate
                    # fail merely because MathText supports a smaller TeX subset.
                    rendered = self._render_to_pixmap(latex, False)
            self._cache[latex] = rendered
            return rendered

    def render_plain_text(self, text: str) -> RenderedEquation:
        """Render literal text without asking MathText to parse TeX commands.

        This is used by PDF metadata and LaTeX-source exports so the result is
        independent from Qt's platform font discovery.

        :param text: Literal text to rasterize.
        :return: Rendered text image and preferred size.
        """
        cache_key: str = f"__plain__:{text}"
        cached: RenderedEquation | None = self._cache.get(cache_key, None)
        if cached is not None:
            return cached
        else:
            rendered: RenderedEquation = self._render_to_pixmap(text, False)
            self._cache[cache_key] = rendered
            return rendered

    def render_svg(self, latex: str) -> RenderedSvgEquation:
        """Return a cached, scale-independent SVG equation.

        :param latex: Mathematical source without outer dollar delimiters.
        :return: Self-contained SVG and its intrinsic logical size.
        """
        cached: RenderedSvgEquation | None = self._svg_cache.get(latex, None)
        if cached is not None:
            return cached
        else:
            normalized_latex: str = normalize_mathtext_latex(latex)
            if len(normalized_latex) > self._maximum_mathtext_length:
                preview_message: str = (
                    f"Equation is too large for graphical preview ({len(latex)} characters). "
                    "See Python code."
                )
                rendered: RenderedSvgEquation = self._render_to_svg(preview_message, False)
            else:
                try:
                    rendered = self._render_to_svg(normalized_latex, True)
                except (RuntimeError, ValueError):
                    rendered = self._render_to_svg(latex, False)
            self._svg_cache[latex] = rendered
            return rendered

    def render_plain_text_svg(self, text: str) -> RenderedSvgEquation:
        """Return literal text as self-contained vector glyph paths.

        :param text: Literal label text without mathematical interpretation.
        :return: Scale-independent SVG label and its logical size.
        """
        cache_key: str = f"__plain_svg__:{text}"
        cached: RenderedSvgEquation | None = self._svg_cache.get(cache_key, None)
        if cached is not None:
            return cached
        else:
            rendered: RenderedSvgEquation = self._render_to_svg(text, False)
            self._svg_cache[cache_key] = rendered
            return rendered

    def invalidate(self, latex: str) -> None:
        """
        Remove one entry from the cache (called after an edit).

        :param latex: LaTeX source handled by the operation.
        :return: None.
        """
        self._cache.pop(latex, None)
        self._svg_cache.pop(latex, None)

    def clear(self) -> None:
        """
        Drop the entire cache.

        :return: None.
        """
        self._cache.clear()
        self._svg_cache.clear()

    def get_maximum_mathtext_length(self) -> int:
        """
        Return the safe single-expression MathText character limit.

        :return: The safe single-expression MathText character limit.
        """
        return self._maximum_mathtext_length

    # -- internals ---------------------------------------------------------

    def _render_to_pixmap(self, latex: str, use_mathtext: bool) -> RenderedEquation:
        """Render one equation through MathText or the safe plain-text path.

        :param latex: Equation source.
        :param use_mathtext: Whether to ask Matplotlib to parse math commands.
        :return: Rendered Qt image and preferred size.
        """
        fig: Figure = Figure(dpi=self._dpi)
        FigureCanvasAgg(fig)
        fig.patch.set_alpha(0.0)

        # Use fig.text (not ax.text) so bbox_inches='tight' computes the
        # bounding box from the text glyphs alone, without axes geometry.
        self._draw_text(fig, latex, use_mathtext)

        buf: BytesIO = BytesIO()
        fig.savefig(buf, format="png", transparent=True,
                    bbox_inches="tight", pad_inches=0)
        fig.clear()

        buf.seek(0)
        image: QtGui.QImage = QtGui.QImage()
        image.loadFromData(buf.read())
        pixmap: QPixmap = QPixmap.fromImage(image)
        size: QtCore.QSize = QtCore.QSize(
            pixmap.width(),
            max(pixmap.height() + 4, self._minimum_row_height),
        )
        return RenderedEquation(
            pixmap=pixmap,
            size=size,
            uses_mathtext=use_mathtext,
        )

    def _render_to_svg(self, latex: str, use_mathtext: bool) -> RenderedSvgEquation:
        """Render one equation into self-contained vector paths.

        :param latex: Equation source.
        :param use_mathtext: Whether Matplotlib should compile math commands.
        :return: Vector equation payload and intrinsic logical size.
        """
        # A frameless figure prevents QSvgRenderer from interpreting the
        # transparent Matplotlib canvas patch as a visible outline in PDF.
        fig: Figure = Figure(dpi=self._dpi, frameon=False)
        FigureCanvasAgg(fig)
        self._draw_text(fig, latex, use_mathtext)

        buffer: BytesIO = BytesIO()
        fig.savefig(
            buffer,
            format="svg",
            transparent=True,
            bbox_inches="tight",
            pad_inches=0,
        )
        fig.clear()
        svg_data: QtCore.QByteArray = QtCore.QByteArray(buffer.getvalue())
        svg_renderer: QtSvg.QSvgRenderer = QtSvg.QSvgRenderer(svg_data)
        if svg_renderer.isValid():
            intrinsic_size: QtCore.QSize = svg_renderer.defaultSize()
            # Matplotlib expresses SVG dimensions in 72-dpi points, whereas
            # the previous document preview used renderer-dpi screen pixels.
            # Scale only the logical box; SVG paths remain fully vectorial.
            logical_scale: float = float(self._dpi) / 72.0
            size: QtCore.QSize = QtCore.QSize(
                max(1, int(round(intrinsic_size.width() * logical_scale))),
                max(1, int(round(intrinsic_size.height() * logical_scale))),
            )
        else:
            raise ValueError("Matplotlib produced an invalid SVG equation")
        return RenderedSvgEquation(
            data=svg_data,
            size=size,
            uses_mathtext=use_mathtext,
        )

    def _draw_text(self, fig: Figure, latex: str, use_mathtext: bool) -> Text:
        """Draw math or literal source on the transparent figure.

        :param fig: Matplotlib figure receiving the text artist.
        :param latex: Equation source.
        :param use_mathtext: Whether to surround the source with math markers.
        :return: Created Matplotlib text artist.
        """
        if use_mathtext:
            displayed_text: str = f"${latex}$"
        else:
            displayed_text = latex
        return fig.text(
            0,
            0,
            displayed_text,
            fontsize=self._font_size,
            ha="left",
            va="baseline",
        )


# ---------------------------------------------------------------------------
# LatexEquationDelegate  –  sizeHint + paint, no scaling
# ---------------------------------------------------------------------------

class LatexEquationDelegate(QtWidgets.QStyledItemDelegate):
    """
    Delegate that renders LaTeX equations in the equations table.

    Implements ``sizeHint()`` using the same cached render that
    ``paint()`` uses, so Qt can set the row height to the real
    equation size via ``ResizeToContents``.

    ``paint()`` never scales the pixmap — it centres the original-
    size image inside the cell rectangle.
    """

    __slots__ = ("_renderer",)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Create a delegate with an explicitly owned renderer cache.

        :param parent: Owning table widget.
        :return: None.
        """
        super().__init__(parent)
        self._renderer: LatexRenderer = LatexRenderer()

    # -- sizeHint ----------------------------------------------------------

    def sizeHint(self,
                 option: QtWidgets.QStyleOptionViewItem,
                 index: QtCore.QModelIndex) -> QtCore.QSize:
        """Return the real cached image dimensions for a table cell.

        :param option: Qt style information.
        :param index: Equation model index.
        :return: Preferred equation-cell size.
        """
        text: object = index.data(Qt.ItemDataRole.DisplayRole)
        if not text:
            return super().sizeHint(option, index)
        else:
            rendered: RenderedEquation = self._renderer.render(str(text))
            return rendered.get_size()

    # -- paint -------------------------------------------------------------

    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex,
    ) -> None:
        """Paint the cached equation image over Qt's native cell background.

        :param painter: Active table-view painter.
        :param option: Qt style and geometry information.
        :param index: Equation model index.
        :return: None.
        """
        self.initStyleOption(option, index)
        style: QtWidgets.QStyle = (
            option.widget.style() if option.widget else QtWidgets.QApplication.style()
        )
        style.drawPrimitive(
            QtWidgets.QStyle.PrimitiveElement.PE_PanelItemViewItem,
            option, painter, option.widget,
        )

        text: object = index.data(Qt.ItemDataRole.DisplayRole)
        if not text:
            return
        else:
            rendered: RenderedEquation = self._renderer.render(str(text))
            pixmap: QPixmap = rendered.get_pixmap()

            rect: QtCore.QRect = option.rect
            x_pos: int = rect.x() + (rect.width() - pixmap.width()) // 2
            y_pos: int = rect.y() + (rect.height() - pixmap.height()) // 2
            painter.drawPixmap(x_pos, y_pos, pixmap)

    # -- cache management --------------------------------------------------

    def invalidate(self, latex: str) -> None:
        """
        Drop one cached entry after the underlying data changes.

        :param latex: LaTeX source handled by the operation.
        :return: None.
        """
        self._renderer.invalidate(latex)

    def clear_cache(self) -> None:
        """
        Drop the entire rendering cache.

        :return: None.
        """
        self._renderer.clear()
