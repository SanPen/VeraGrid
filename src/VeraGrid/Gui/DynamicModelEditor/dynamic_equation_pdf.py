# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""PDF export support for equations selected in the Dynamic Model Editor."""

from __future__ import annotations

from datetime import datetime
from typing import BinaryIO, List, Mapping, Sequence

from PySide6 import QtCore, QtGui, QtSvg

from VeraGrid.Gui.DynamicModelEditor.dynamic_latex_renderer import LatexRenderer, RenderedSvgEquation
from VeraGridEngine.enumerations import EquationExportSection, EquationPdfStyle
from VeraGridEngine.Utils.Symbolic.latex_printer import symbolic_to_latex
from VeraGridEngine.Utils.Symbolic.symbolic import Expr, Var, symbolic_to_string


def build_equation_pdf_suggested_name(root_block_name: str,
                                      style: EquationPdfStyle) -> str:
    """Return an unambiguous default file name for one equation PDF style.

    :param root_block_name: Top-level block described by the document.
    :param style: Source-code or rendered-equation presentation.
    :return: Suggested PDF file name with a style-specific suffix.
    """
    if style == EquationPdfStyle.LATEX_SOURCE:
        style_suffix: str = "latex_source"
    else:
        style_suffix = "latex_rendered"
    return f"{root_block_name}_dynamic_equations_{style_suffix}.pdf"


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


def get_pdf_sans_text_width(text: str, font_size: float) -> float:
    """Estimate standard Helvetica text width in PDF points.

    The source PDF uses the built-in Helvetica face so it remains selectable
    without a new runtime dependency or an external font file. Conservative
    glyph widths ensure wrapped lines remain inside the page margin.

    :param text: Literal text to measure.
    :param font_size: Font size in PDF points.
    :return: Conservative horizontal extent in PDF points.
    """
    width_units: float = 0.0
    character: str
    for character in text:
        if character in " il.,'`|!:;":
            width_units += 0.32
        elif character in "mwMW@%":
            width_units += 0.95
        elif character.isupper():
            width_units += 0.76
        elif character in "[]{}()\\/":
            width_units += 0.50
        else:
            width_units += 0.62
    return width_units * font_size


def wrap_pdf_source_text(text: str, font_size: float, maximum_width: float) -> List[str]:
    """Wrap LaTeX source without splitting commands or identifiers.

    :param text: Source line to wrap.
    :param font_size: Helvetica size in points.
    :param maximum_width: Available width in PDF points.
    :return: Ordered lines that fit the page.
    """
    words: List[str] = text.split()
    result: List[str] = list()
    current_line: str = ""
    word: str
    for word in words:
        if len(current_line) == 0:
            candidate: str = word
        else:
            candidate = f"{current_line} {word}"
        if get_pdf_sans_text_width(candidate, font_size) <= maximum_width:
            current_line = candidate
        elif len(current_line) > 0:
            result.append(current_line)
            current_line = word
        else:
            current_line = word
    if len(current_line) > 0:
        result.append(current_line)
    else:
        pass
    if len(result) == 0:
        result.append("")
    else:
        pass
    return result


def encode_pdf_literal(text: str) -> bytes:
    """Encode one selectable PDF literal string safely.

    :param text: Source text limited to the catalogue's Latin text surface.
    :return: Parenthesized and escaped PDF string bytes.
    """
    escaped: str = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    payload: bytes = escaped.encode("latin-1", errors="replace")
    return b"(" + payload + b")"


class SelectableLatexSourcePdfDocument:
    """Dependency-free PDF writer for selectable LaTeX source."""

    __slots__ = (
        "_file_path",
        "_root_block_name",
        "_created_at",
        "_pages",
        "_current_page",
        "_cursor_y",
        "_font_size",
        "_line_height",
        "_left",
        "_right",
        "_body_bottom",
    )

    def __init__(self, file_path: str, root_block_name: str) -> None:
        """Initialize a selectable A4 source document.

        :param file_path: Destination PDF path.
        :param root_block_name: Top-level block represented by the export.
        :return: None.
        """
        self._file_path: str = file_path
        self._root_block_name: str = root_block_name
        self._created_at: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._pages: List[List[tuple[str, float, float, bool]]] = list()
        self._current_page: List[tuple[str, float, float, bool]] = list()
        self._cursor_y: float = 0.0
        self._font_size: float = 10.0
        self._line_height: float = 14.0
        self._left: float = 45.0
        self._right: float = 550.0
        self._body_bottom: float = 48.0
        self._start_new_page()

    def _append_line(self, text: str, bold: bool = False, x_pos: float | None = None) -> None:
        """Append one positioned line and advance the body cursor.

        :param text: Selectable line text.
        :param bold: Whether to use the bold VeraGrid-style sans face.
        :param x_pos: Optional horizontal position.
        :return: None.
        """
        if x_pos is None:
            line_x: float = self._left
        else:
            line_x = x_pos
        self._current_page.append((text, line_x, self._cursor_y, bold))
        self._cursor_y -= self._line_height

    def _start_new_page(self) -> None:
        """
        Create a page with compact ten-point metadata and no separator rule.

        :return: None.
        """
        if len(self._current_page) > 0:
            self._pages.append(self._current_page)
        else:
            pass
        self._current_page = list()
        self._cursor_y = 800.0
        self._append_line("% VeraGrid dynamic equations", bold=True)
        self._append_line(
            f"% Block: {self._root_block_name} | Generated: {self._created_at}"
        )
        self._append_line("% Format: LaTeX source")
        self._cursor_y -= 10.0

    def _ensure_line_capacity(self, line_count: int) -> None:
        """Start a page before a complete source block would overflow.

        :param line_count: Number of body lines required together.
        :return: None.
        """
        required_height: float = line_count * self._line_height
        if self._cursor_y - required_height < self._body_bottom:
            self._start_new_page()
        else:
            pass

    def draw_group_heading(self, block_name: str, section: EquationExportSection) -> None:
        """Append one valid LaTeX comment as a section heading.

        :param block_name: Internal equation-owner name.
        :param section: Selected equation category.
        :return: None.
        """
        self._ensure_line_capacity(2)
        self._append_line(f"% {block_name} - {section.value}", bold=True)
        self._cursor_y -= 3.0

    def draw_equation(self, latex: str) -> None:
        """Append one copy-ready display-math block without boxes or numbering.

        :param latex: Equation LaTeX source.
        :return: None.
        """
        available_width: float = self._right - self._left - 14.0
        wrapped_lines: List[str] = wrap_pdf_source_text(
            latex,
            self._font_size,
            available_width,
        )
        self._ensure_line_capacity(len(wrapped_lines) + 3)
        self._append_line(r"\[")
        wrapped_line: str
        for wrapped_line in wrapped_lines:
            self._append_line(f"  {wrapped_line}", x_pos=self._left + 8.0)
        self._append_line(r"\]")
        self._cursor_y -= 5.0

    def finish(self) -> None:
        """
        Serialize all laid-out pages into one standards-compliant PDF.

        :return: None.
        """
        if len(self._current_page) > 0:
            self._pages.append(self._current_page)
            self._current_page = list()
        else:
            pass
        pdf_payload: bytes = build_selectable_source_pdf_payload(
            self._pages,
            self._root_block_name,
            self._font_size,
        )
        stream: BinaryIO
        with open(self._file_path, "wb") as stream:
            stream.write(pdf_payload)


def build_selectable_source_pdf_payload(
        pages: Sequence[Sequence[tuple[str, float, float, bool]]],
        root_block_name: str,
        font_size: float) -> bytes:
    """Build a selectable multi-page PDF using standard sans-serif fonts.

    :param pages: Positioned lines for every page.
    :param root_block_name: Block name stored in document metadata.
    :param font_size: Text size in PDF points.
    :return: Complete PDF byte stream.
    """
    page_count: int = len(pages)
    object_count: int = 5 + page_count * 2
    objects: List[bytes] = list((b"",)) * (object_count + 1)
    objects[1] = b"<< /Type /Catalog /Pages 2 0 R >>"
    page_reference_values: List[str] = list(("",)) * page_count
    page_index: int
    for page_index in range(page_count):
        page_reference_values[page_index] = f"{6 + page_index * 2} 0 R"
    page_references: str = " ".join(page_reference_values)
    objects[2] = f"<< /Type /Pages /Count {page_count} /Kids [{page_references}] >>".encode("ascii")
    objects[3] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    objects[4] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>"
    objects[5] = (
        b"<< /Title " + encode_pdf_literal(f"Dynamic equations - {root_block_name}")
        + b" /Creator " + encode_pdf_literal("VeraGrid Dynamic Model Editor") + b" >>"
    )

    for page_index in range(page_count):
        page_object_number: int = 6 + page_index * 2
        content_object_number: int = page_object_number + 1
        objects[page_object_number] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595.28 841.89] "
            f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> "
            f"/Contents {content_object_number} 0 R >>"
        ).encode("ascii")
        content_parts: List[bytes] = list()
        line: tuple[str, float, float, bool]
        for line in pages[page_index]:
            font_name: str
            if line[3]:
                font_name = "F2"
            else:
                font_name = "F1"
            content_parts.append(
                b"BT /" + font_name.encode("ascii") + f" {font_size:.1f} Tf ".encode("ascii")
                + f"1 0 0 1 {line[1]:.2f} {line[2]:.2f} Tm ".encode("ascii")
                + encode_pdf_literal(line[0]) + b" Tj ET\n"
            )
        footer_text: str = str(page_index + 1)
        footer_width: float = get_pdf_sans_text_width(footer_text, font_size)
        content_parts.append(
            f"BT /F1 {font_size:.1f} Tf 1 0 0 1 {550.0 - footer_width:.2f} 28.0 Tm ".encode("ascii")
            + encode_pdf_literal(footer_text) + b" Tj ET\n"
        )
        content: bytes = b"".join(content_parts)
        objects[content_object_number] = (
            f"<< /Length {len(content)} >>\nstream\n".encode("ascii")
            + content
            + b"endstream"
        )

    output: bytearray = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets: List[int] = list((0,)) * (object_count + 1)
    object_number: int
    for object_number in range(1, object_count + 1):
        offsets[object_number] = len(output)
        output.extend(f"{object_number} 0 obj\n".encode("ascii"))
        output.extend(objects[object_number])
        output.extend(b"\nendobj\n")
    xref_offset: int = len(output)
    output.extend(f"xref\n0 {object_count + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for object_number in range(1, object_count + 1):
        output.extend(f"{offsets[object_number]:010d} 00000 n \n".encode("ascii"))
    output.extend(
        f"trailer\n<< /Size {object_count + 1} /Root 1 0 R /Info 5 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return bytes(output)


class EquationPdfDocumentPainter:
    """Paginated painter for compiled equation PDF documents."""

    __slots__ = (
        "_writer",
        "_painter",
        "_renderer",
        "_plain_renderer",
        "_root_block_name",
        "_created_at",
        "_style",
        "_page_number",
        "_content_rect",
        "_cursor_y",
    )

    def __init__(self,
                 file_path: str,
                 root_block_name: str,
                 style: EquationPdfStyle) -> None:
        """Open an A4 PDF writer and prepare its first page.

        :param file_path: Destination PDF path selected by the user.
        :param root_block_name: Top-level block described by the document.
        :param style: Source-code or rendered-equation presentation.
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
        self._style: EquationPdfStyle = style
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
            f"Format: {self._style.value}",
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
                       entries: Sequence[EquationExportEntry],
                       style: EquationPdfStyle) -> None:
    """Write selected equations to a metadata-rich PDF document.

    :param file_path: Destination selected by the user.
    :param root_block_name: Root block represented by the editor dialogue.
    :param entries: Selected equations in display order.
    :param style: LaTeX-source or rendered-equation output.
    :return: None.
    """
    if style == EquationPdfStyle.LATEX_SOURCE:
        source_document: SelectableLatexSourcePdfDocument | None = SelectableLatexSourcePdfDocument(
            file_path=file_path,
            root_block_name=root_block_name,
        )
        rendered_document: EquationPdfDocumentPainter | None = None
    else:
        source_document = None
        rendered_document = EquationPdfDocumentPainter(
            file_path=file_path,
            root_block_name=root_block_name,
            style=style,
        )
    previous_block_name: str = ""
    previous_section: EquationExportSection | None = None
    equation_index: int = 0
    entry: EquationExportEntry
    for entry in entries:
        if entry.get_block_name() != previous_block_name or entry.get_section() != previous_section:
            if source_document is not None:
                source_document.draw_group_heading(entry.get_block_name(), entry.get_section())
            elif rendered_document is not None:
                rendered_document.draw_group_heading(entry.get_block_name(), entry.get_section())
            else:
                raise RuntimeError("Equation PDF document was not initialized")
            previous_block_name = entry.get_block_name()
            previous_section = entry.get_section()
        else:
            pass
        equation_index += 1
        if source_document is not None:
            source_document.draw_equation(entry.get_latex())
        elif rendered_document is not None:
            rendered_document.draw_equation(entry.get_latex(), equation_index)
        else:
            raise RuntimeError("Equation PDF document was not initialized")
    if source_document is not None:
        source_document.finish()
    elif rendered_document is not None:
        rendered_document.finish()
    else:
        raise RuntimeError("Equation PDF document was not initialized")
