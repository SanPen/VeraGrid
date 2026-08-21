# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""PDF export support for equations selected in the Dynamic Model Editor."""

from __future__ import annotations

from datetime import datetime
from typing import List, Mapping, Sequence

from PySide6 import QtCore, QtGui, QtSvg

from VeraGrid.Gui.DynamicModelEditor.dynamic_latex_renderer import LatexRenderer, RenderedSvgEquation
from VeraGridEngine.enumerations import EquationExportSection
from VeraGridEngine.Utils.Symbolic.latex_printer import symbolic_to_latex
from VeraGridEngine.Utils.Symbolic.symbolic import Expr, Var, symbolic_to_string


def build_equation_pdf_suggested_name(root_block_name: str) -> str:
    """Return the default file name for one rendered equation document.

    :param root_block_name: Top-level block described by the document.
    :return: Suggested PDF file name identifying the rendered presentation.
    """
    return f"{root_block_name}_dynamic_equations_latex_rendered.pdf"


class EquationExportEntry:
    """One equation together with its block and equation-group metadata."""

    __slots__ = ("_block_name", "_section", "_latex")

    def __init__(self, block_name: str, section: EquationExportSection, latex: str) -> None:
        """Store one immutable equation export entry.

        :param block_name: Name of the internal block owning the equation.
        :param section: Semantic equation group.
        :param latex: Equation represented in LaTeX source.
        :return: None.
        """
        self._block_name: str = block_name
        self._section: EquationExportSection = section
        self._latex: str = latex

    def get_block_name(self) -> str:
        """
        :return: The equation-owner block name.
        """
        return self._block_name

    def get_section(self) -> EquationExportSection:
        """
        :return: The semantic equation section.
        """
        return self._section

    def get_latex(self) -> str:
        """
        :return: The equation LaTeX source.
        """
        return self._latex


def build_latex_source(entries: Sequence[EquationExportEntry]) -> str:
    """Build copy-ready LaTeX display blocks for selected equations.

    Block and equation-group headings are emitted as comments, so users can
    paste the complete result directly into a LaTeX document without removing
    VeraGrid metadata. Every equation receives its own display-math delimiters
    to avoid introducing a dependency on an additional alignment package.

    :param entries: Selected equations in their displayed export order.
    :return: Copy-ready LaTeX source for the selected equation groups.
    """
    source_lines: List[str] = list()
    previous_block_name: str = ""
    previous_section: EquationExportSection | None = None
    entry: EquationExportEntry
    for entry in entries:
        starts_new_group: bool = (
            entry.get_block_name() != previous_block_name
            or entry.get_section() != previous_section
        )
        if starts_new_group:
            if len(source_lines) > 0:
                source_lines.append("")
            else:
                pass
            safe_block_name: str = entry.get_block_name().replace("\r", " ").replace("\n", " ")
            source_lines.append(f"% {safe_block_name} - {entry.get_section().value}")
            previous_block_name = entry.get_block_name()
            previous_section = entry.get_section()
        else:
            pass
        source_lines.append(r"\[")
        source_lines.append(entry.get_latex())
        source_lines.append(r"\]")
    return "\n".join(source_lines)


def get_safe_equation_latex(expression: Expr) -> str:
    """Convert one expression to LaTeX with a lossless text fallback.

    :param expression: Symbolic expression to export.
    :return: LaTeX source accepted by the editor equation renderer.
    """
    try:
        result: str = symbolic_to_latex(expression)
    except (NotImplementedError, RuntimeError, TypeError, ValueError):
        result = symbolic_to_string(expression)
    return result


def build_list_equation_entries(block_name: str,
                                section: EquationExportSection,
                                expressions: Sequence[Expr]) -> List[EquationExportEntry]:
    """Build residual-form export entries from one equation sequence.

    :param block_name: Name of the equation owner.
    :param section: Semantic sequence category.
    :param expressions: Residual expressions equal to zero.
    :return: Ordered equation entries.
    """
    result: List[EquationExportEntry] = list()
    expression: Expr
    for expression in expressions:
        # Sequence equations are residuals in VeraGrid, so the PDF makes the
        # implicit equality explicit for readers outside the source code.
        equation_latex: str = f"0 = {get_safe_equation_latex(expression)}"
        result.append(EquationExportEntry(block_name, section, equation_latex))
    return result


def build_state_equation_entries(
        block_name: str,
        expressions: Sequence[Expr],
        differential_variables: Sequence[Var | None]) -> List[EquationExportEntry]:
    """Build state equations from differential left sides and stored right sides.

    ``Block.state_eqs`` stores only the right-hand side. Its same-position
    differential variable is the left-hand side when explicitly available;
    otherwise VeraGrid's exported equation uses zero as the implicit left side.

    :param block_name: Name of the equation owner.
    :param expressions: Ordered state-equation right-hand sides.
    :param differential_variables: Ordered explicit differential variables.
    :return: Ordered state-equation export entries.
    """
    result: List[EquationExportEntry] = list()
    expression_index: int
    expression: Expr
    for expression_index, expression in enumerate(expressions):
        differential_variable: Var | None = None
        if expression_index < len(differential_variables):
            differential_variable = differential_variables[expression_index]
        else:
            pass

        # Only an explicit derivative can form the left side. Missing
        # derivatives keep the documented implicit ``0 = rhs`` convention.
        if isinstance(differential_variable, Var):
            left_latex: str = get_safe_equation_latex(differential_variable)
        else:
            left_latex = "0"
        equation_latex: str = f"{left_latex} = {get_safe_equation_latex(expression)}"
        result.append(
            EquationExportEntry(
                block_name,
                EquationExportSection.STATE,
                equation_latex,
            )
        )
    return result


def order_state_differential_variables(
        state_variables: Sequence[Var],
        differential_variables: Sequence[Var]) -> List[Var | None]:
    """Align explicit state variables with their derivative identities.

    ``Block.diff_vars`` may also contain derivatives of implicit algebraic
    variables, so its raw list position is not a safe state-equation mapping.

    :param state_variables: Ordered explicit state variables.
    :param differential_variables: All differential variables owned by a block.
    :return: One matching derivative or ``None`` for every explicit state.
    """
    result: List[Var | None] = list()
    state_variable: Var
    for state_variable in state_variables:
        matching_variable: Var | None = None
        differential_variable: Var
        for differential_variable in differential_variables:
            base_variable: Var | None = differential_variable.base_var
            if (base_variable is state_variable
                    or (base_variable is not None
                        and base_variable.non_mutable_uid == state_variable.non_mutable_uid)):
                matching_variable = differential_variable
            else:
                pass
        result.append(matching_variable)
    return result


def build_mapping_equation_entries(block_name: str,
                                   section: EquationExportSection,
                                   expressions: Mapping[Var, Expr]) -> List[EquationExportEntry]:
    """Build assignment-form export entries from one initialization mapping.

    :param block_name: Name of the equation owner.
    :param section: Semantic mapping category.
    :param expressions: Variable-to-expression mapping.
    :return: Ordered equation entries.
    """
    result: List[EquationExportEntry] = list()
    variable: Var
    expression: Expr
    for variable, expression in expressions.items():
        equation_latex: str = (
            f"{get_safe_equation_latex(variable)} = {get_safe_equation_latex(expression)}"
        )
        result.append(EquationExportEntry(block_name, section, equation_latex))
    return result


def split_latex_at_safe_spaces(latex: str) -> List[str]:
    """Split LaTeX only at spaces outside command brace groups.

    :param latex: Equation source emitted by the symbolic printer.
    :return: Segments that can be recombined with ordinary spaces.
    """
    segments: List[str] = list()
    characters: List[str] = list()
    brace_depth: int = 0
    character: str
    for character in latex:
        if character == "{":
            brace_depth += 1
        elif character == "}":
            brace_depth = max(0, brace_depth - 1)
        else:
            pass
        if character.isspace() and brace_depth == 0:
            segment: str = "".join(characters).strip()
            if len(segment) > 0:
                segments.append(segment)
            else:
                pass
            characters = list()
        else:
            characters.append(character)
    final_segment: str = "".join(characters).strip()
    if len(final_segment) > 0:
        segments.append(final_segment)
    else:
        pass
    return segments


def get_latex_group_end(source: str, opening_index: int) -> int | None:
    """Find the closing brace paired with one LaTeX opening brace.

    :param source: Complete LaTeX source.
    :param opening_index: Index expected to contain ``{``.
    :return: Matching closing index, or ``None`` for malformed source.
    """
    if opening_index < 0 or opening_index >= len(source) or source[opening_index] != "{":
        return None
    else:
        pass
    depth: int = 0
    character_index: int
    for character_index in range(opening_index, len(source)):
        character: str = source[character_index]
        if character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return character_index
            else:
                pass
        else:
            pass
    return None


def expand_latex_fractions_for_wrapping(latex: str) -> str:
    """Convert fractions to equivalent slash notation for multiline display.

    A large ``\\frac`` is one indivisible brace group for MathText. Converting
    only the wrapped visual representation to parenthesized slash notation
    exposes safe operator spaces while the copyable source PDF retains the
    original LaTeX unchanged.

    :param latex: Original equation source.
    :return: Visually equivalent source with expandable fraction groups.
    """
    result_parts: List[str] = list()
    source_index: int = 0
    prefix: str = r"\frac"
    while source_index < len(latex):
        if latex.startswith(prefix, source_index):
            numerator_open: int = source_index + len(prefix)
            numerator_close: int | None = get_latex_group_end(latex, numerator_open)
            if numerator_close is not None and numerator_close + 1 < len(latex):
                denominator_open: int = numerator_close + 1
                denominator_close: int | None = get_latex_group_end(latex, denominator_open)
            else:
                denominator_open = -1
                denominator_close = None
            if numerator_close is not None and denominator_close is not None:
                numerator: str = latex[numerator_open + 1:numerator_close]
                denominator: str = latex[denominator_open + 1:denominator_close]
                expanded_numerator: str = expand_latex_fractions_for_wrapping(numerator)
                expanded_denominator: str = expand_latex_fractions_for_wrapping(denominator)
                result_parts.append(f"(({expanded_numerator}) / ({expanded_denominator}))")
                source_index = denominator_close + 1
            else:
                result_parts.append(latex[source_index])
                source_index += 1
        else:
            result_parts.append(latex[source_index])
            source_index += 1
    return "".join(result_parts)


def expand_latex_square_roots_for_wrapping(latex: str) -> str:
    """Convert square roots to equivalent powers for multiline rendering.

    MathText cannot render one square-root bar across independent pixmap
    lines. The equivalent parenthesized power notation exposes the terms as
    safe line-break candidates without changing the symbolic expression.

    :param latex: LaTeX source after scalable delimiters were normalized.
    :return: Equivalent source whose long radicand can span several lines.
    """
    result_parts: List[str] = list()
    source_index: int = 0
    prefix: str = r"\sqrt"
    while source_index < len(latex):
        if latex.startswith(prefix, source_index):
            radicand_open: int = source_index + len(prefix)
            radicand_close: int | None = get_latex_group_end(latex, radicand_open)
            if radicand_close is not None:
                radicand: str = latex[radicand_open + 1:radicand_close]
                expanded_radicand: str = expand_latex_square_roots_for_wrapping(radicand)
                result_parts.append(f"(({expanded_radicand})^{{1/2}})")
                source_index = radicand_close + 1
            else:
                result_parts.append(latex[source_index])
                source_index += 1
        else:
            result_parts.append(latex[source_index])
            source_index += 1
    return "".join(result_parts)


def render_wrapped_equation(renderer: LatexRenderer,
                            latex: str,
                            maximum_width: int) -> List[RenderedSvgEquation]:
    """Render one equation as vector lines that fit the available width.

    Safe top-level spaces are preferred as line boundaries. Scaling is only a
    final fallback for one indivisible LaTeX group, never the primary layout
    mechanism for a long equation.

    :param renderer: Ten-point equation renderer.
    :param latex: Raw equation LaTeX.
    :param maximum_width: Available equation width in painter pixels.
    :return: Ordered SVG equations, each guaranteed to fit the available width.
    """
    complete_render: RenderedSvgEquation = renderer.render_svg(latex)
    if (
            complete_render.get_uses_mathtext()
            and complete_render.get_size().width() <= maximum_width
    ):
        return list((complete_render,))
    elif (
            not complete_render.get_uses_mathtext()
            and len(latex) <= renderer.get_maximum_mathtext_length()
    ):
        raise ValueError(f"Invalid LaTeX equation generated for PDF export: {latex}")
    else:
        pass

    # MathText requires paired scalable delimiters. Ordinary parentheses can
    # be distributed over continuation lines, so remove only the sizing hints.
    delimiter_source: str = latex.replace(r"\left", "").replace(r"\right", "")
    fraction_source: str = expand_latex_fractions_for_wrapping(delimiter_source)
    line_break_source: str = expand_latex_square_roots_for_wrapping(fraction_source)
    segments: List[str] = split_latex_at_safe_spaces(line_break_source)
    line_sources: List[str] = list()
    current_source: str = ""
    segment: str
    for segment in segments:
        if len(current_source) == 0:
            candidate: str = segment
        else:
            candidate = f"{current_source} {segment}"
        candidate_render: RenderedSvgEquation = renderer.render_svg(candidate)
        if (
                not candidate_render.get_uses_mathtext()
                and len(candidate) > renderer.get_maximum_mathtext_length()
                and len(current_source) > 0
        ):
            line_sources.append(current_source)
            current_source = segment
        elif not candidate_render.get_uses_mathtext():
            raise ValueError(
                f"Invalid wrapped LaTeX equation generated for PDF export: {candidate}"
            )
        elif candidate_render.get_size().width() <= maximum_width:
            current_source = candidate
        elif len(current_source) > 0:
            line_sources.append(current_source)
            current_source = segment
        else:
            current_source = segment
    if len(current_source) > 0:
        line_sources.append(current_source)
    else:
        pass
    if len(line_sources) == 0:
        line_sources.append(line_break_source)
    else:
        pass

    result: List[RenderedSvgEquation] = list()
    line_source: str
    for line_source in line_sources:
        line_render: RenderedSvgEquation = renderer.render_svg(line_source)
        if not line_render.get_uses_mathtext():
            raise ValueError(
                f"Invalid wrapped LaTeX equation generated for PDF export: {line_source}"
            )
        else:
            pass
        line_size: QtCore.QSize = line_render.get_size()
        if line_size.width() > maximum_width:
            scale: float = float(maximum_width) / float(line_size.width())
            displayed_render: RenderedSvgEquation = RenderedSvgEquation(
                data=line_render.get_data(),
                size=QtCore.QSize(
                    maximum_width,
                    max(1, int(round(float(line_size.height()) * scale))),
                ),
                uses_mathtext=True,
            )
        else:
            displayed_render = line_render
        result.append(displayed_render)
    return result


class EquationPdfDocumentPainter:
    """Paginated painter for compiled equation PDF documents."""

    __slots__ = (
        "_writer",
        "_painter",
        "_renderer",
        "_plain_renderer",
        "_root_block_name",
        "_created_at",
        "_page_number",
        "_content_rect",
        "_cursor_y",
    )

    def __init__(self,
                 file_path: str,
                 root_block_name: str) -> None:
        """Open an A4 PDF writer and prepare its first page.

        :param file_path: Destination PDF path selected by the user.
        :param root_block_name: Top-level block described by the document.
        :return: None.
        """
        self._writer: QtGui.QPdfWriter = QtGui.QPdfWriter(file_path)
        self._writer.setResolution(96)
        self._writer.setPageSize(QtGui.QPageSize(QtGui.QPageSize.PageSizeId.A4))
        self._writer.setPageMargins(
            QtCore.QMarginsF(0.0, 0.0, 0.0, 0.0),
            QtGui.QPageLayout.Unit.Millimeter,
        )
        self._writer.setTitle(f"Dynamic equations - {root_block_name}")
        self._writer.setCreator("VeraGrid Dynamic Model Editor")
        self._painter: QtGui.QPainter = QtGui.QPainter(self._writer)
        # Render at the same resolution used by the PDF painter. Rendering
        # ten-point glyphs at 144 DPI and painting them on a 96-DPI page made
        # all raster-backed text and equations appear fifty percent too large.
        self._renderer: LatexRenderer = LatexRenderer(font_size=10, dpi=96)
        # Labels use embedded SVG glyph paths rather than platform fonts. This
        # stays vectorial while avoiding missing-font squares in PDF viewers.
        self._plain_renderer: LatexRenderer = LatexRenderer(font_size=10, dpi=96)
        self._root_block_name: str = root_block_name
        # A stable numeric local timestamp stays compact in every locale and
        # does not let a translated time-zone name overflow the PDF header.
        self._created_at: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._page_number: int = 1
        full_page_rect: QtCore.QRect = self._writer.pageLayout().fullRectPixels(
            self._writer.resolution()
        )
        self._content_rect: QtCore.QRect = full_page_rect.adjusted(60, 57, -60, -57)
        self._cursor_y: int = self._content_rect.top()
        self._draw_page_header()

    def _draw_plain_text(self,
                         text: str,
                         x_pos: int,
                         y_pos: int,
                         maximum_width: int) -> int:
        """Draw one ten-point label as scale-independent SVG glyph paths.

        :param text: Literal label text.
        :param x_pos: Left painter coordinate.
        :param y_pos: Top painter coordinate.
        :param maximum_width: Maximum permitted label width.
        :return: Height of the drawn label.
        """
        rendered: RenderedSvgEquation = self._plain_renderer.render_plain_text_svg(text)
        intrinsic_size: QtCore.QSize = rendered.get_size()
        if intrinsic_size.width() > maximum_width:
            scale: float = float(maximum_width) / float(intrinsic_size.width())
            displayed_size: QtCore.QSize = QtCore.QSize(
                maximum_width,
                max(1, int(round(float(intrinsic_size.height()) * scale))),
            )
        else:
            displayed_size = intrinsic_size
        svg_renderer: QtSvg.QSvgRenderer = QtSvg.QSvgRenderer(rendered.get_data())
        svg_renderer.render(
            self._painter,
            QtCore.QRectF(
                float(x_pos),
                float(y_pos),
                float(displayed_size.width()),
                float(displayed_size.height()),
            ),
        )
        return displayed_size.height()

    def _draw_page_header(self) -> None:
        """
        Draw document metadata and initialize the page body cursor.

        :return: None.
        """
        left: int = self._content_rect.left()

        # The compact ten-point header identifies detached pages without
        # competing visually with the equations.
        cursor_y: int = self._content_rect.top() + 8
        cursor_y += self._draw_plain_text(
            "VeraGrid dynamic equations",
            left,
            cursor_y,
            self._content_rect.width(),
        )
        metadata: str = (
            f"Block: {self._root_block_name} | Generated: {self._created_at}"
        )
        cursor_y += self._draw_plain_text(
            metadata,
            left,
            cursor_y + 2,
            self._content_rect.width(),
        )
        cursor_y += self._draw_plain_text(
            "Format: Rendered equations",
            left,
            cursor_y + 2,
            self._content_rect.width(),
        )
        self._cursor_y = cursor_y + 14

    def _draw_page_footer(self) -> None:
        """
        Draw the current page number below the usable body area.

        :return: None.
        """
        footer_text: str = str(self._page_number)
        footer_render: RenderedSvgEquation = self._plain_renderer.render_plain_text_svg(
            footer_text
        )
        footer_size: QtCore.QSize = footer_render.get_size()
        self._draw_plain_text(
            footer_text,
            self._content_rect.right() - footer_size.width(),
            self._content_rect.bottom() - footer_size.height(),
            footer_size.width(),
        )

    def _start_new_page(self) -> None:
        """
        Close the current page and initialize the next one.

        :return: None.
        """
        self._draw_page_footer()
        self._writer.newPage()
        self._page_number += 1
        full_page_rect: QtCore.QRect = self._writer.pageLayout().fullRectPixels(
            self._writer.resolution()
        )
        self._content_rect = full_page_rect.adjusted(60, 57, -60, -57)
        self._draw_page_header()

    def _ensure_space(self, required_height: int) -> None:
        """Advance to a fresh page when the requested vertical space does not fit.

        :param required_height: Required body height in painter pixels.
        :return: None.
        """
        body_bottom: int = self._content_rect.bottom() - 30
        if self._cursor_y + required_height > body_bottom:
            self._start_new_page()
        else:
            pass

    def draw_group_heading(self, block_name: str, section: EquationExportSection) -> None:
        """Draw a block-and-section heading before its selected equations.

        :param block_name: Internal equation-owner name.
        :param section: Selected equation section.
        :return: None.
        """
        self._ensure_space(42)
        heading_text: str = f"{block_name} - {section.value}"
        heading_height: int = self._draw_plain_text(
            heading_text,
            self._content_rect.left(),
            self._cursor_y,
            self._content_rect.width(),
        )
        self._cursor_y += heading_height + 8

    def draw_equation(self, latex: str, equation_index: int) -> None:
        """Draw one numbered equation in the selected presentation style.

        :param latex: Equation LaTeX source.
        :param equation_index: One-based number inside the selected export.
        :return: None.
        """
        self._draw_rendered_equation(latex, equation_index)

    def _draw_rendered_equation(self, latex: str, equation_index: int) -> None:
        """Draw one MathText-rendered equation as scale-independent SVG paths.

        :param latex: Raw LaTeX equation source.
        :param equation_index: One-based equation number.
        :return: None.
        """
        available_width: int = self._content_rect.width() - 68
        equation_lines: List[RenderedSvgEquation] = render_wrapped_equation(
            self._renderer,
            latex,
            available_width,
        )
        equation_height: int = 0
        equation_line: RenderedSvgEquation
        for equation_line in equation_lines:
            equation_height += equation_line.get_size().height() + 5
        required_height: int = max(32, equation_height + 10)
        self._ensure_space(required_height)
        self._draw_plain_text(
            f"[{equation_index}]",
            self._content_rect.left(),
            self._cursor_y + 3,
            45,
        )
        image_x: int = self._content_rect.left() + 55
        image_y: int = self._cursor_y + 3
        for equation_line in equation_lines:
            line_size: QtCore.QSize = equation_line.get_size()
            svg_renderer: QtSvg.QSvgRenderer = QtSvg.QSvgRenderer(equation_line.get_data())
            svg_renderer.render(
                self._painter,
                QtCore.QRectF(
                    float(image_x),
                    float(image_y),
                    float(line_size.width()),
                    float(line_size.height()),
                ),
            )
            image_y += line_size.height() + 5
        self._cursor_y += required_height

    def finish(self) -> None:
        """
        Finalize the last footer and close the active PDF painter.

        :return: None.
        """
        self._draw_page_footer()
        self._painter.end()


def write_equation_pdf(file_path: str,
                       root_block_name: str,
                       entries: Sequence[EquationExportEntry]) -> None:
    """Write selected equations to a rendered metadata-rich PDF document.

    :param file_path: Destination selected by the user.
    :param root_block_name: Root block represented by the editor dialogue.
    :param entries: Selected equations in display order.
    :return: None.
    """
    rendered_document: EquationPdfDocumentPainter = EquationPdfDocumentPainter(
        file_path=file_path,
        root_block_name=root_block_name,
    )
    previous_block_name: str = ""
    previous_section: EquationExportSection | None = None
    equation_index: int = 0
    entry: EquationExportEntry
    for entry in entries:
        if entry.get_block_name() != previous_block_name or entry.get_section() != previous_section:
            rendered_document.draw_group_heading(entry.get_block_name(), entry.get_section())
            previous_block_name = entry.get_block_name()
            previous_section = entry.get_section()
        else:
            pass
        equation_index += 1
        rendered_document.draw_equation(entry.get_latex(), equation_index)
    rendered_document.finish()
