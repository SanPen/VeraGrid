# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Generate one auditable Markdown page per Basic Block Catalog template."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Sequence

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.BasicBlockCatalog import (
    BasicBlockTemplateDescriptor,
    get_editor_ready_basic_block_catalog_descriptors,
    load_basic_block_catalog_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.latex_printer import symbolic_to_latex
from VeraGridEngine.Utils.Symbolic.symbolic import Expr, Var, get_expression_vars


class DocumentationTopic(Enum):
    """Technical domains used to explain dynamic-library blocks."""

    SYNCHRONIZATION = 1
    REFERENCE_FRAME = 2
    FEEDBACK_CONTROL = 3
    NONLINEAR_CONSTRAINT = 4
    INTERPOLATION = 5
    HYBRID_LOGIC = 6
    ELECTRICAL_SOURCE = 7
    PASSIVE_NETWORK = 8
    ELECTROMECHANICAL = 9
    POWER_ELECTRONICS = 10
    ENERGY_RESOURCE = 11
    LOAD_MODEL = 12
    MEASUREMENT = 13
    UNIT_CONVERSION = 14
    SIGNAL_ALGEBRA = 15
    WAVEFORM = 16
    GENERIC_DYNAMICS = 17


def classify_documentation_topic(title: str,
                                 category_path: Sequence[str]) -> DocumentationTopic:
    """Classify one block by its physical, mathematical, or control purpose.

    :param title: Human-readable block title.
    :param category_path: Library or documentation hierarchy for the block.
    :return: Technical topic used for explanatory documentation.
    """
    searchable_text: str = (title + " " + " ".join(category_path)).lower()
    if "phase locked" in searchable_text or "pll" in searchable_text or "phase detector" in searchable_text:
        result: DocumentationTopic = DocumentationTopic.SYNCHRONIZATION
    elif any(token in searchable_text for token in (
            "clarke", "park", "dq0", "abc->", "abc to", "sequence", "polar", "cartesian")):
        result = DocumentationTopic.REFERENCE_FRAME
    elif any(token in searchable_text for token in (
            "converter", "inverter", "vsc", "pwm", "modulation", "modulator")):
        result = DocumentationTopic.POWER_ELECTRONICS
    elif any(token in searchable_text for token in (
            "battery", "bess", "photovoltaic", "pv ", " pv", "storage")):
        result = DocumentationTopic.ENERGY_RESOURCE
    elif "load" in searchable_text:
        result = DocumentationTopic.LOAD_MODEL
    elif any(token in searchable_text for token in (
            "voltage source", "current source", "thevenin", "surge", "heidler", "double exponential")):
        result = DocumentationTopic.ELECTRICAL_SOURCE
    elif any(token in searchable_text for token in (
            "transformer", "xfmr", "line", "fault", "ground", "rlc", "resistor", "inductor", "capacitor", "shunt")):
        result = DocumentationTopic.PASSIVE_NETWORK
    elif any(token in searchable_text for token in (
            "generator", "genrou", "genrow", "genqec", "motor", "turbine", "governor", "stabilizer",
            "exciter", "gear", "drive train", "torque")):
        result = DocumentationTopic.ELECTROMECHANICAL
    elif any(token in searchable_text for token in (
            "controller", "control", "droop", "integrator", "washout", "lead lag", "transfer function", "pi ")):
        result = DocumentationTopic.FEEDBACK_CONTROL
    elif any(token in searchable_text for token in (
            "limit", "lim ", "saturation", "deadband", "backlash", "nonlinear", "absolute value", "rate")):
        result = DocumentationTopic.NONLINEAR_CONSTRAINT
    elif any(token in searchable_text for token in ("lookup", "interpol", "array", "matrix", "table")):
        result = DocumentationTopic.INTERPOLATION
    elif any(token in searchable_text for token in (
            "switch", "select", "selfix", "set if", "from goto", "signal pair", "last value", "enable",
            "timer", "delay", "sample", "hold", "flip", "latch", "boolean", "greater", "less", "equal",
            "logic", "event")):
        result = DocumentationTopic.HYBRID_LOGIC
    elif any(token in searchable_text for token in (
            "measurement", "rms value", "electrical power", "el. power", "pq", "frequency measurement",
            "moving average")):
        result = DocumentationTopic.MEASUREMENT
    elif any(token in searchable_text for token in (
            "to pu", "to-pu", "pu to", "pu-to", "p.u.", "-> abs", "-> rad", "-> deg", "-> hz",
            "-> rpm", "rad to", "rad-to", "deg to", "deg-to", "rpm", "hz to", "hz-to", "nm ->",
            "power base")):
        result = DocumentationTopic.UNIT_CONVERSION
    elif any(token in searchable_text for token in (
            "sine wave", "square wave", "triangle wave", "sawtooth", "ramp", "step", "waveform", "clock", "time")):
        result = DocumentationTopic.WAVEFORM
    elif any(token in searchable_text for token in (
            "arithmetic", "sum", "product", "gain", "bias", "balanced", "scaling", "constant", "complex",
            "math", "sqrt", "exponential")):
        result = DocumentationTopic.SIGNAL_ALGEBRA
    else:
        result = DocumentationTopic.GENERIC_DYNAMICS
    return result


def build_block_explanation(topic: DocumentationTopic,
                            title: str) -> tuple[str, str, str]:
    """Build domain context and two practical-use recommendations.

    :param topic: Classified engineering domain.
    :param title: Human-readable block title included in the explanation.
    :return: Context paragraph and two distinct usage recommendations.
    """
    if topic == DocumentationTopic.SYNCHRONIZATION:
        context: str = (
            f"**{title}** belongs to the synchronization layer of a power-system controller. "
            "A phase-locked loop compares a measured voltage reference with an internally generated angle, "
            "filters the phase error, and integrates the resulting frequency correction. It lets grid-following "
            "controls express currents and voltages in a rotating frame aligned with the network."
        )
        first_use: str = "Use it when a controller must track grid angle and frequency rather than establish them."
        second_use: str = (
            "Check loop bandwidth and damping against grid strength; an aggressive PLL can amplify disturbances "
            "or interact with converter current control."
        )
    elif topic == DocumentationTopic.REFERENCE_FRAME:
        context = (
            f"**{title}** is a coordinate-transformation block. In three-phase analysis, Clarke and Park transforms "
            "separate stationary or rotating components so sinusoidal phase quantities can be controlled as nearly "
            "constant d-q signals. The selected scaling determines whether amplitude or instantaneous power is preserved."
        )
        first_use = "Use it to connect phase-domain electrical quantities with d-q or sequence-domain control laws."
        second_use = "Keep angle orientation, axis alignment, phase order, and power/amplitude convention consistent."
    elif topic == DocumentationTopic.FEEDBACK_CONTROL:
        context = (
            f"**{title}** implements a feedback-control relation. Such blocks turn tracking error into an actuator "
            "command and may contain proportional, integral, filtering, or dynamic compensation terms. Their gains "
            "set closed-loop speed and damping rather than changing the underlying network physics directly."
        )
        first_use = "Use it inside voltage, current, power, speed, excitation, or governor control loops."
        second_use = "Coordinate gains, limits, and time constants with the actuator and plant bandwidth."
    elif topic == DocumentationTopic.NONLINEAR_CONSTRAINT:
        context = (
            f"**{title}** represents a nonlinear control constraint or piecewise characteristic. Limits, deadbands, "
            "rate bounds, and hysteresis reproduce actuator capability and protection logic that a purely linear model "
            "cannot represent. The active branch can change when a threshold is crossed."
        )
        first_use = "Use it to model physical saturation, insensitive regions, slew limits, or bounded commands."
        second_use = "Choose thresholds in consistent units and inspect behavior exactly at switching boundaries."
    elif topic == DocumentationTopic.INTERPOLATION:
        context = (
            f"**{title}** evaluates a tabulated characteristic instead of assuming one closed-form equation. "
            "Interpolation maps measured or commanded inputs to empirical outputs such as efficiency, saturation, "
            "capability, or control schedules while preserving the supplied breakpoints."
        )
        first_use = "Use it when manufacturer data or a calibrated characteristic is available as points or a matrix."
        second_use = "Keep breakpoints ordered and decide deliberately whether values outside the table clip or extrapolate."
    elif topic == DocumentationTopic.HYBRID_LOGIC:
        context = (
            f"**{title}** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches "
            "signals according to conditions, so its result depends on discrete mode or accepted simulation history in "
            "addition to the instantaneous continuous variables."
        )
        first_use = "Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer."
        second_use = "Define initial mode and boundary behavior explicitly to avoid unintended event chattering."
    elif topic == DocumentationTopic.ELECTRICAL_SOURCE:
        context = (
            f"**{title}** imposes or controls an electrical excitation in an EMT network. Depending on the variant, "
            "it prescribes voltage or current directly or through a source-equivalent impedance. It is used to represent "
            "the grid, a controlled converter terminal, or a standardized transient waveform."
        )
        first_use = "Use it as a network boundary, disturbance source, or controlled electrical terminal."
        second_use = "Match polarity, phase convention, grounding, and source impedance to the connected topology."
    elif topic == DocumentationTopic.PASSIVE_NETWORK:
        context = (
            f"**{title}** represents passive network physics through resistance, inductance, capacitance, coupling, "
            "or switching topology. Its equations enforce voltage-current constitutive relations and therefore affect "
            "energy storage, damping, propagation, fault current, or grounding behavior."
        )
        first_use = "Use it to reproduce the electrical path between sources, converters, machines, and loads."
        second_use = "Keep phases, terminal orientation, connection type, and SI/per-unit parameter bases consistent."
    elif topic == DocumentationTopic.ELECTROMECHANICAL:
        context = (
            f"**{title}** belongs to an electromechanical machine or prime-mover model. It links electrical torque and "
            "flux with rotor speed, angle, mechanical power, or actuator dynamics, making it central to frequency, "
            "voltage, and rotor-angle stability studies."
        )
        first_use = "Use it when electrical transients must interact with rotating mass or machine controls."
        second_use = "Initialize torque, power, flux, and speed consistently with the solved power flow."
    elif topic == DocumentationTopic.POWER_ELECTRONICS:
        context = (
            f"**{title}** represents a power-electronic conversion or modulation function. Converter models translate "
            "control references into AC/DC electrical quantities, while averaged and switched variants retain different "
            "levels of switching detail and therefore require different simulation time steps."
        )
        first_use = "Use averaged models for control and system studies, and switched models when waveform detail matters."
        second_use = "Coordinate reference frames, modulation limits, DC-side energy, and current-control bandwidth."
    elif topic == DocumentationTopic.ENERGY_RESOURCE:
        context = (
            f"**{title}** represents an energy resource and its interface controls. Storage and photovoltaic models "
            "combine source-side energy or power limits with converter commands, so available active power, DC voltage, "
            "and reactive-power control must remain mutually consistent."
        )
        first_use = "Use it to study renewable or storage response to voltage, frequency, and power-reference disturbances."
        second_use = "Respect energy, current, DC-voltage, and active/reactive capability limits during initialization."
    elif topic == DocumentationTopic.LOAD_MODEL:
        context = (
            f"**{title}** describes how electrical demand responds to terminal voltage, frequency, or internal states. "
            "Static impedance/current/power components and dynamic load states produce different fault and recovery "
            "behavior, so the selected formulation materially changes system damping and voltage stability."
        )
        first_use = "Use the formulation that matches the time scale and measured behavior of the represented demand."
        second_use = "Initialize active and reactive demand from the power flow and verify the voltage-dependence convention."
    elif topic == DocumentationTopic.MEASUREMENT:
        context = (
            f"**{title}** derives a control or monitoring quantity from electrical signals. Measurement blocks may "
            "calculate RMS magnitude, active/reactive power, frequency, or filtered values; their window and sign "
            "conventions determine delay and interpretation downstream."
        )
        first_use = "Use it to provide physically meaningful feedback signals to protection and control blocks."
        second_use = "Check scaling, sign, averaging window, and phase convention before connecting the result."
    elif topic == DocumentationTopic.UNIT_CONVERSION:
        context = (
            f"**{title}** converts an engineering quantity between unit systems or reference bases. These blocks do not "
            "add physical dynamics, but they make dimensional assumptions explicit and prevent gains or thresholds from "
            "silently mixing hertz, radians per second, rpm, degrees, absolute units, and per-unit values."
        )
        first_use = "Use it at interfaces where a model and its data source use different units or bases."
        second_use = "Verify the nominal base quantity and angular-frequency convention used by both sides."
    elif topic == DocumentationTopic.SIGNAL_ALGEBRA:
        context = (
            f"**{title}** is a mathematical signal-processing primitive. It forms an algebraic relation between inputs, "
            "parameters, and outputs and is commonly combined with dynamic and nonlinear blocks to construct larger "
            "control equations without introducing an independent physical state."
        )
        first_use = "Use it to express the exact algebraic operation required by a controller or measurement chain."
        second_use = "Check signal dimensions, signs, and zero-division or domain restrictions where applicable."
    elif topic == DocumentationTopic.WAVEFORM:
        context = (
            f"**{title}** generates or evaluates a deterministic time waveform. Waveform blocks provide repeatable "
            "references and disturbances for controller tests, EMT source profiles, and event-sequence validation."
        )
        first_use = "Use it to apply controlled steps, ramps, periodic signals, clocks, or test trajectories."
        second_use = "Choose amplitude, offset, phase, start time, and frequency consistently with simulation units."
    else:
        context = (
            f"**{title}** is a reusable symbolic building block for dynamic models. Its inputs, outputs, parameters, "
            "equations, and runtime logic define a mathematical signal relation that can be composed with network, "
            "machine, converter, and control subsystems."
        )
        first_use = "Use it when assembling or extending a dynamic model with the documented symbolic relation."
        second_use = "Inspect equations and interface units before connecting it to blocks from another physical domain."
    return context, first_use, second_use


def build_block_introduction_markdown(title: str,
                                      category_path: Sequence[str]) -> str:
    """Build a natural block introduction followed by practical guidance.

    :param title: Human-readable block title.
    :param category_path: Library or documentation hierarchy.
    :return: Marked, replaceable Markdown section.
    """
    topic: DocumentationTopic = classify_documentation_topic(title, category_path)
    context: str
    first_use: str
    second_use: str
    context, first_use, second_use = build_block_explanation(topic, title)
    lines: list[str] = list()
    lines.append("<!-- veragrid-block-introduction:start -->")
    lines.append(context)
    lines.append("")
    lines.append("## Typical use")
    lines.append("")
    lines.append("- " + first_use)
    lines.append("- " + second_use)
    lines.append("<!-- veragrid-block-introduction:end -->")
    return "\n".join(lines)


def escape_markdown_table_text(value: str) -> str:
    """Escape text before placing it inside a Markdown table cell.

    :param value: Raw text.
    :return: Markdown-safe table text.
    """
    result: str = value.replace("|", "\\|").replace("\n", " ").strip()
    return result


def build_category_explanation(category_path: Sequence[str]) -> str:
    """Return a category-specific explanation of a catalogue block's role.

    :param category_path: Hierarchical library category.
    :return: Human-readable purpose sentence.
    """
    category_text: str = " ".join(category_path).lower()
    if "arithmetic" in category_text:
        result: str = "It performs a scalar arithmetic transformation on its input signals."
    elif "array" in category_text or "matrix" in category_text or "lookup" in category_text:
        result = "It evaluates tabulated or array-based data using the selected lookup formulation."
    elif "continuous" in category_text:
        result = "It represents a continuous-time dynamic operation, including any declared internal states."
    elif "control" in category_text or "measurement" in category_text:
        result = "It processes measurement or control signals for use inside a dynamic control model."
    elif "logic" in category_text or "event" in category_text:
        result = "It implements logical or event-driven signal behaviour."
    elif "limit" in category_text or "nonlinear" in category_text:
        result = "It applies the declared limiting or nonlinear relation to its input signals."
    elif "math" in category_text:
        result = "It evaluates the mathematical function identified by the block name."
    elif "transform" in category_text:
        result = "It converts signals between the coordinate systems or units identified by the block name."
    elif "complex" in category_text:
        result = "It processes real and imaginary components of complex-valued signals."
    elif "waveform" in category_text or "time" in category_text:
        result = "It generates or evaluates a time-dependent waveform."
    elif "mechanical" in category_text or "drive train" in category_text:
        result = "It represents a mechanical or drive-train relation used by rotating-machine models."
    else:
        result = "It implements the symbolic signal relation identified by its catalogue definition."
    return result


def append_interface_rows(lines: list[str], category: str, names: Sequence[str], meaning: str) -> None:
    """Append one group of interface rows to a Markdown document.

    :param lines: Document lines being assembled.
    :param category: Interface category label.
    :param names: Symbol names in this category.
    :param meaning: Meaning shared by the symbols.
    :return: None.
    """
    name: str
    for name in names:
        safe_name: str = escape_markdown_table_text(name)
        lines.append(f"| {category} | `{safe_name}` | {meaning} | model-dependent |")


def append_equation(lines: list[str], latex: str) -> None:
    """Append one display equation to a Markdown document.

    :param lines: Document lines being assembled.
    :param latex: Equation body without display delimiters.
    :return: None.
    """
    lines.append("$$")
    lines.append(latex)
    lines.append("$$")
    lines.append("")


def build_readable_variable(variable: Var, block_name: str) -> Var:
    """Build a documentation-only variable without generated name affixes.

    :param variable: Runtime variable emitted by the catalogue builder.
    :param block_name: Generated block name used as prefix and suffix.
    :return: Detached variable with a compact documentation name.
    """
    readable_name: str = variable.name
    suffix: str = "_" + block_name
    block_name_head: str
    block_name_separator: str
    block_name_tail: str
    block_name_head, block_name_separator, block_name_tail = block_name.rpartition("__")
    if len(block_name_separator) > 0 and block_name_tail.isdigit():
        base_block_name: str = block_name_head
    else:
        base_block_name = block_name
    prefix: str = base_block_name + "__"
    if readable_name.endswith(suffix):
        readable_name = readable_name[:-len(suffix)]
    else:
        pass
    if readable_name.startswith(prefix):
        readable_name = readable_name[len(prefix):]
    else:
        pass
    result: Var = Var(readable_name)
    return result


def build_readable_expression(expression: Expr, block_name: str) -> Expr:
    """Replace generated runtime variable names in one documentation equation.

    :param expression: Runtime symbolic expression.
    :param block_name: Generated block name used as prefix and suffix.
    :return: Equivalent expression with compact variable names.
    """
    replacements: dict[Var, Var] = dict()
    expression_variable: Var
    for expression_variable in get_expression_vars(expression):
        replacements[expression_variable] = build_readable_variable(expression_variable, block_name)
    if len(replacements) > 0:
        result: Expr = expression.subs(replacements)
    else:
        result = expression
    return result


def append_block_equations(lines: list[str], block: Block) -> int:
    """Append the symbolic equations directly owned by one block.

    :param lines: Document lines being assembled.
    :param block: Symbolic block whose equations are documented.
    :return: Number of equations appended.
    """
    equation_count: int = 0
    equation_index: int
    equation: Expr
    state_variable: Var
    differential_variable: Var
    init_variable: Var
    init_expression: Expr

    for equation_index, equation in enumerate(block.state_eqs):
        readable_equation: Expr = build_readable_expression(equation, block.name)
        if equation_index < len(block.state_vars):
            state_variable = block.state_vars[equation_index]
            readable_state_variable: Var = build_readable_variable(state_variable, block.name)
            append_equation(
                lines,
                "\\frac{d " + symbolic_to_latex(readable_state_variable) + "}{dt} = "
                + symbolic_to_latex(readable_equation),
            )
        else:
            append_equation(lines, "0 = " + symbolic_to_latex(readable_equation))
        equation_count += 1

    for equation in block.algebraic_eqs:
        readable_equation = build_readable_expression(equation, block.name)
        append_equation(lines, "0 = " + symbolic_to_latex(readable_equation))
        equation_count += 1

    for equation_index, equation in enumerate(block.differential_eqs):
        readable_equation = build_readable_expression(equation, block.name)
        if equation_index < len(block.diff_vars):
            differential_variable = block.diff_vars[equation_index]
            readable_differential_variable: Var = build_readable_variable(differential_variable, block.name)
            append_equation(
                lines,
                symbolic_to_latex(readable_differential_variable) + " = "
                + symbolic_to_latex(readable_equation),
            )
        else:
            append_equation(lines, "0 = " + symbolic_to_latex(readable_equation))
        equation_count += 1

    for init_variable, init_expression in block.init_eqs.items():
        readable_init_variable: Var = build_readable_variable(init_variable, block.name)
        readable_init_expression: Expr = build_readable_expression(init_expression, block.name)
        append_equation(
            lines,
            symbolic_to_latex(readable_init_variable) + "(t_0) = "
            + symbolic_to_latex(readable_init_expression),
        )
        equation_count += 1

    return equation_count


def build_catalogue_markdown(descriptor: BasicBlockTemplateDescriptor,
                             template: EmtModelTemplate) -> str:
    """Build one complete Markdown page for a catalogue template.

    :param descriptor: Static catalogue description.
    :param template: Materialized symbolic template.
    :return: Markdown document.
    """
    lines: list[str] = list()
    category_label: str = " / ".join(descriptor.category_path)
    source_name: str = descriptor.blkdef_name.strip()
    title: str = descriptor.display_label.strip()
    if len(title) == 0:
        title = source_name
    else:
        pass

    lines.append("# " + title)
    lines.append("")
    lines.append(
        f"This is Basic Block Catalog type `{descriptor.typ_id}` (`{escape_markdown_table_text(source_name)}`). "
        + build_category_explanation(descriptor.category_path)
    )
    lines.append("")
    # Every generated catalogue page must explain the technical reason for
    # the block, not merely repeat the imported interface and equations.
    block_introduction: str = build_block_introduction_markdown(
        title,
        descriptor.category_path,
    )
    lines.extend(block_introduction.splitlines())
    lines.append("")
    lines.append("## Behaviour")
    lines.append("")
    lines.append(f"- Library location: `{escape_markdown_table_text(category_label)}`.")
    lines.append(f"- Inputs: {len(descriptor.inputs)}.")
    lines.append(f"- Outputs: {len(descriptor.outputs)}.")
    lines.append(f"- Declared states: {len(descriptor.states)}.")
    lines.append(f"- Configurable parameters: {len(descriptor.params)}.")
    if len(descriptor.unsupported_lines) == 0:
        lines.append("- The imported definition is fully supported by the Dynamic Editor catalogue.")
    else:
        lines.append("- The catalogue importer reports unsupported source statements; inspect validation before use.")
    lines.append("")
    lines.append("## Characteristic equations")
    lines.append("")

    equation_count: int = 0
    child_block: Block
    for child_block in template.block.get_all_blocks():
        equation_count += append_block_equations(lines, child_block)
    if equation_count == 0:
        lines.append(
            "This block has no continuous DAE equation. Its behaviour is defined by its event, mode, "
            "lookup, or procedural logic fields."
        )
        lines.append("")
    else:
        pass

    lines.append("## Interface table")
    lines.append("")
    lines.append("| Category | Name | Meaning | Units |")
    lines.append("| --- | --- | --- | --- |")
    append_interface_rows(lines, "Input", descriptor.inputs, "Input signal consumed by the block")
    append_interface_rows(lines, "Output", descriptor.outputs, "Output signal produced by the block")
    append_interface_rows(lines, "State", descriptor.states, "Internal dynamic state")
    append_interface_rows(lines, "Parameter", descriptor.params, "Configurable model parameter")
    if len(descriptor.inputs) + len(descriptor.outputs) + len(descriptor.states) + len(descriptor.params) == 0:
        lines.append("| Internal | — | The block has no externally declared symbolic interface | — |")
    else:
        pass

    lines.append("")
    lines.append("## Editing notes")
    lines.append("")
    lines.append(
        "Use General options for numeric parameter values and the DAE tab for symbolic variables and equations. "
        "Changing an Output flag only controls whether a variable is exported; it does not remove the variable "
        "from the model."
    )
    lines.append("")
    return "\n".join(lines)


def generate_catalogue_documentation(repository_root: Path) -> int:
    """Generate every per-template catalogue Markdown file.

    :param repository_root: VeraGrid repository root.
    :return: Number of generated pages.
    """
    output_directory: Path = (
        repository_root / "doc" / "md_source" / "dyn_templates" / "library" / "catalog"
    )
    output_directory.mkdir(parents=True, exist_ok=True)

    generated_count: int = 0
    descriptor: BasicBlockTemplateDescriptor
    for descriptor in get_editor_ready_basic_block_catalog_descriptors():
        template: EmtModelTemplate = load_basic_block_catalog_template(
            descriptor=descriptor,
            var_factory=VarFactory(),
        )
        markdown: str = build_catalogue_markdown(descriptor=descriptor, template=template)
        output_path: Path = output_directory / f"typ_{descriptor.typ_id}.md"
        output_path.write_text(markdown, encoding="utf-8")
        generated_count += 1
    return generated_count


def get_markdown_title(markdown: str, fallback_title: str) -> str:
    """Return the first level-one Markdown heading or a filename fallback.

    :param markdown: Complete Markdown document.
    :param fallback_title: Human-readable title derived from the filename.
    :return: Document title without the heading marker.
    """
    result: str = fallback_title
    line: str
    found: bool = False
    for line in markdown.splitlines():
        if line.startswith("# ") and not found:
            result = line[2:].strip()
            found = True
        else:
            pass
    return result


def insert_block_introduction(markdown: str,
                              title: str,
                              category_path: Sequence[str]) -> str:
    """Insert or refresh the generated explanatory introduction.

    :param markdown: Existing hand-maintained block documentation.
    :param title: Human-readable block title.
    :param category_path: Documentation hierarchy used for classification.
    :return: Markdown with exactly one current explanatory introduction.
    """
    start_marker: str = "<!-- veragrid-block-introduction:start -->"
    end_marker: str = "<!-- veragrid-block-introduction:end -->"
    legacy_start_marker: str = "<!-- veragrid-engineering-context:start -->"
    legacy_end_marker: str = "<!-- veragrid-engineering-context:end -->"
    introduction_markdown: str = build_block_introduction_markdown(title, category_path)
    start_index: int = markdown.find(start_marker)
    end_index: int = markdown.find(end_marker)
    active_end_marker: str = end_marker
    if start_index >= 0 and end_index >= start_index:
        pass
    else:
        start_index = markdown.find(legacy_start_marker)
        end_index = markdown.find(legacy_end_marker)
        active_end_marker = legacy_end_marker
    if start_index >= 0 and end_index >= start_index:
        # Replace the generated region in place while preserving every
        # hand-authored paragraph before and after it.
        end_offset: int = end_index + len(active_end_marker)
        result: str = markdown[:start_index] + introduction_markdown + markdown[end_offset:]
    else:
        # Place context directly after the title so readers understand the
        # block before reaching equations and interface tables.
        lines: list[str] = markdown.splitlines()
        heading_index: int = -1
        line_index: int
        line: str
        for line_index, line in enumerate(lines):
            if line.startswith("# ") and heading_index < 0:
                heading_index = line_index
            else:
                pass
        if heading_index >= 0:
            insertion_index: int = heading_index + 1
            if insertion_index < len(lines) and len(lines[insertion_index].strip()) == 0:
                insertion_index += 1
            else:
                pass
            lines.insert(insertion_index, introduction_markdown + "\n")
            result = "\n".join(lines)
        else:
            result = "# " + title + "\n\n" + introduction_markdown + "\n\n" + markdown
    if result.endswith("\n"):
        pass
    else:
        result += "\n"
    return result


def enrich_static_dynamic_documentation(repository_root: Path) -> int:
    """Add engineering context to every non-catalogue dynamic block page.

    :param repository_root: VeraGrid repository root.
    :return: Number of inspected non-index Markdown pages.
    """
    documentation_root: Path = repository_root / "doc" / "md_source" / "dyn_templates"
    enriched_count: int = 0
    documentation_path: Path
    for documentation_path in documentation_root.rglob("*.md"):
        relative_path: Path = documentation_path.relative_to(documentation_root)
        is_index: bool = documentation_path.name == "dynamic_model_library_index.md"
        is_generated_catalogue: bool = "catalog" in relative_path.parts
        if is_index or is_generated_catalogue:
            pass
        else:
            markdown: str = documentation_path.read_text(encoding="utf-8")
            fallback_title: str = documentation_path.stem.replace("_", " ").replace("-", " ").title()
            title: str = get_markdown_title(markdown, fallback_title)
            category_path: tuple[str, ...] = tuple(relative_path.parent.parts)
            enriched_markdown: str = insert_block_introduction(markdown, title, category_path)
            documentation_path.write_text(enriched_markdown, encoding="utf-8")
            enriched_count += 1
    return enriched_count


def main() -> None:
    """Generate documentation relative to this repository checkout.

    :return: None.
    """
    repository_root: Path = Path(__file__).resolve().parents[1]
    generated_count: int = generate_catalogue_documentation(repository_root=repository_root)
    enriched_count: int = enrich_static_dynamic_documentation(repository_root=repository_root)
    print(f"Generated {generated_count} Basic Block Catalog Markdown pages.")
    print(f"Enriched {enriched_count} native, template, and runtime-logic Markdown pages.")


if __name__ == "__main__":
    main()
else:
    pass
