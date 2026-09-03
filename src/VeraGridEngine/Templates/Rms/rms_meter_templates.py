from __future__ import annotations

import math
from typing import Dict

import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block, RmsPhysicalMeasurementPoint
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.enumerations import RmsPhysicalMeterKind, RmsTerminalSide


RMS_VOLTAGE_METER_OUTPUT_NAMES: tuple[str, ...] = (
    "ur", "ui", "u", "u2r", "u2i", "u2", "u0r", "u0i", "u0",
    "fref", "fe", "du", "dur", "dui", "du2", "du2r", "du2i", "du0", "du0r", "du0i",
    "ur_A", "ur_B", "ur_C", "ui_A", "ui_B", "ui_C", "dur_A", "dur_B", "dur_C", "dui_A", "dui_B", "dui_C",
)

RMS_POWER_METER_OUTPUT_NAMES: tuple[str, ...] = ("p", "q", "p2", "q2", "p0", "q0")

RMS_CURRENT_METER_OUTPUT_NAMES: tuple[str, ...] = (
    "ir", "ii", "i", "i2r", "i2i", "i2", "i0r", "i0i", "i0",
    "ir_A", "ir_B", "ir_C", "ii_A", "ii_B", "ii_C",
)

RMS_PLL_METER_OUTPUT_NAMES: tuple[str, ...] = ("Fmeas", "fmeas", "cosphi", "sinphi")

RMS_BALANCED_BASIC_VOLTAGE_OUTPUT_NAMES: tuple[str, ...] = (
    "ur", "ui", "u", "fref", "fe",
)
RMS_BALANCED_BASIC_CURRENT_OUTPUT_NAMES: tuple[str, ...] = ("ir", "ii", "i")
RMS_BALANCED_BASIC_POWER_OUTPUT_NAMES: tuple[str, ...] = ("p", "q")
RMS_BALANCED_BASIC_PLL_OUTPUT_NAMES: tuple[str, ...] = RMS_PLL_METER_OUTPUT_NAMES


def select_basic_balanced_rms_meter_outputs(
        signal_expressions: Dict[str, Expr],
        meter_kind: RmsPhysicalMeterKind,
) -> Dict[str, Expr]:
    """Select only quantities represented by the balanced RMS problem.

    The current RMS bus state owns one positive-sequence magnitude and angle;
    it has no negative- or zero-sequence state. Native basic meters therefore
    must not advertise synthetic sequence channels. Import adapters can still
    request the wider compatibility set explicitly when an imported controller
    contract requires those aliases.

    :param signal_expressions: Complete compatibility output lookup.
    :param meter_kind: Physical quantity family produced by the meter.
    :return: Ordered basic balanced-RMS output lookup.
    """
    if meter_kind is RmsPhysicalMeterKind.VOLTAGE:
        selected_names: tuple[str, ...] = RMS_BALANCED_BASIC_VOLTAGE_OUTPUT_NAMES
    elif meter_kind is RmsPhysicalMeterKind.CURRENT:
        selected_names = RMS_BALANCED_BASIC_CURRENT_OUTPUT_NAMES
    elif meter_kind is RmsPhysicalMeterKind.POWER:
        selected_names = RMS_BALANCED_BASIC_POWER_OUTPUT_NAMES
    else:
        selected_names = RMS_BALANCED_BASIC_PLL_OUTPUT_NAMES

    result: Dict[str, Expr] = dict()
    selected_name: str
    for selected_name in selected_names:
        selected_expression: Expr | None = signal_expressions.get(
            selected_name,
            None,
        )
        if selected_expression is None:
            raise KeyError(
                f"Balanced RMS meter output '{selected_name}' is unavailable."
            )
        else:
            result[selected_name] = selected_expression
    return result


def normalize_rms_meter_symbol_fragment(fragment: str) -> str:
    """Normalize one human-facing meter label for use in a DAE symbol.

    Block names remain untouched for presentation. Only the variable fragment
    is restricted to ASCII letters, digits, and underscores so the generated
    equations can always be reopened in the Python-based DAE editor.

    :param fragment: Human-facing output or block-name fragment.
    :return: Non-empty fragment that is safe inside a Python identifier.
    """
    normalized_characters: list[str] = list()
    character: str
    for character in fragment.strip():
        if character.isascii() and (character.isalnum() or character == "_"):
            normalized_characters.append(character)
        else:
            normalized_characters.append("_")
    normalized_fragment: str = "".join(normalized_characters).strip("_")
    if len(normalized_fragment) == 0:
        result: str = "meter"
    elif normalized_fragment[0].isdigit():
        result = "_" + normalized_fragment
    else:
        result = normalized_fragment
    return result


def _rotate_complex_components(real_part: Expr, imag_part: Expr, angle_rad: float) -> tuple[Expr, Expr]:
    """
    Rotate one complex quantity by one fixed phase angle.

    :param real_part: Real component.
    :param imag_part: Imaginary component.
    :param angle_rad: Rotation angle in radians.
    :return: Rotated ``(real, imag)`` pair.
    """
    cos_a: Const = Const(math.cos(angle_rad))
    sin_a: Const = Const(math.sin(angle_rad))
    rotated_real: Expr = (real_part * cos_a) - (imag_part * sin_a)
    rotated_imag: Expr = (real_part * sin_a) + (imag_part * cos_a)
    return rotated_real, rotated_imag


def build_rms_voltage_meter_outputs_from_polar(vm: Expr,
                                               va: Expr,
                                               measured_frequency_hz: Expr,
                                               nominal_frequency_hz: Expr) -> Dict[str, Expr]:
    """
    Build the VeraGrid RMS output set of one AC voltage meter.

    :param vm: Voltage magnitude.
    :param va: Voltage angle in radians.
    :param measured_frequency_hz: Measured frequency in Hz.
    :param nominal_frequency_hz: Nominal frequency in Hz.
    :return: Signal-name to expression mapping.
    """
    zero: Const = Const(0.0)
    ur: Expr = vm * sym.cos(va)
    ui: Expr = vm * sym.sin(va)
    ur_b: Expr
    ui_b: Expr
    ur_c: Expr
    ui_c: Expr
    ur_b, ui_b = _rotate_complex_components(ur, ui, -2.0 * math.pi / 3.0)
    ur_c, ui_c = _rotate_complex_components(ur, ui, 2.0 * math.pi / 3.0)

    # Stable RMS names let native and imported controls consume the same meter.
    return {
        "ur": ur,
        "ui": ui,
        "u": vm,
        "u2r": zero,
        "u2i": zero,
        "u2": zero,
        "u0r": zero,
        "u0i": zero,
        "u0": zero,
        "fref": nominal_frequency_hz,
        "fe": measured_frequency_hz,
        "du": zero,
        "dur": zero,
        "dui": zero,
        "du2": zero,
        "du2r": zero,
        "du2i": zero,
        "du0": zero,
        "du0r": zero,
        "du0i": zero,
        "ur_A": ur,
        "ur_B": ur_b,
        "ur_C": ur_c,
        "ui_A": ui,
        "ui_B": ui_b,
        "ui_C": ui_c,
        "dur_A": zero,
        "dur_B": zero,
        "dur_C": zero,
        "dui_A": zero,
        "dui_B": zero,
        "dui_C": zero,
    }


def build_rms_voltage_meter_outputs_from_dc(vdc: Expr,
                                            nominal_frequency_hz: Expr) -> Dict[str, Expr]:
    """
    Build the VeraGrid RMS output set of one DC voltage meter.

    :param vdc: DC voltage magnitude.
    :param nominal_frequency_hz: Nominal frequency in Hz.
    :return: Signal-name to expression mapping.
    """
    zero: Const = Const(0.0)

    # The DC meter reuses the RMS names with zero quadrature and sequence channels.
    return {
        "ur": vdc,
        "ui": zero,
        "u": vdc,
        "u2r": zero,
        "u2i": zero,
        "u2": zero,
        "u0r": zero,
        "u0i": zero,
        "u0": zero,
        "fref": nominal_frequency_hz,
        "fe": nominal_frequency_hz,
        "du": zero,
        "dur": zero,
        "dui": zero,
        "du2": zero,
        "du2r": zero,
        "du2i": zero,
        "du0": zero,
        "du0r": zero,
        "du0i": zero,
        "ur_A": vdc,
        "ur_B": vdc,
        "ur_C": vdc,
        "ui_A": zero,
        "ui_B": zero,
        "ui_C": zero,
        "dur_A": zero,
        "dur_B": zero,
        "dur_C": zero,
        "dui_A": zero,
        "dui_B": zero,
        "dui_C": zero,
    }


def build_rms_current_meter_outputs_from_pq(vm: Expr,
                                            va: Expr,
                                            p: Expr,
                                            q: Expr) -> Dict[str, Expr]:
    """
    Build the VeraGrid RMS current outputs from ``P/Q`` and ``V``.

    :param vm: Voltage magnitude.
    :param va: Voltage angle in radians.
    :param p: Active power.
    :param q: Reactive power.
    :return: Signal-name to expression mapping.
    """
    zero: Const = Const(0.0)
    eps: Const = Const(1e-9)
    ur: Expr = vm * sym.cos(va)
    ui: Expr = vm * sym.sin(va)
    denom: Expr = (vm * vm) + eps
    ir: Expr = (p * ur + q * ui) / denom
    ii: Expr = (p * ui - q * ur) / denom
    ir_b: Expr
    ii_b: Expr
    ir_c: Expr
    ii_c: Expr
    ir_b, ii_b = _rotate_complex_components(ir, ii, -2.0 * math.pi / 3.0)
    ir_c, ii_c = _rotate_complex_components(ir, ii, 2.0 * math.pi / 3.0)

    # Aggregate and phase channels share one physically consistent phasor.
    return {
        "ir": ir,
        "ii": ii,
        "i": sym.sqrt((ir * ir) + (ii * ii) + eps),
        "i2r": zero,
        "i2i": zero,
        "i2": zero,
        "i0r": zero,
        "i0i": zero,
        "i0": zero,
        "ir_A": ir,
        "ir_B": ir_b,
        "ir_C": ir_c,
        "ii_A": ii,
        "ii_B": ii_b,
        "ii_C": ii_c,
    }


def build_rms_power_meter_outputs_from_pq(p: Expr, q: Expr) -> Dict[str, Expr]:
    """
    Build the VeraGrid RMS active/reactive power outputs.

    :param p: Active power.
    :param q: Reactive power.
    :return: Signal-name to expression mapping.
    """
    zero: Const = Const(0.0)
    return {
        "p": p,
        "q": q,
        "p2": zero,
        "q2": zero,
        "p0": zero,
        "q0": zero,
    }


def build_rms_pll_meter_outputs(va: Expr,
                                measured_frequency_hz: Expr,
                                nominal_frequency_hz: Expr) -> Dict[str, Expr]:
    """
    Build the VeraGrid RMS output set of one PLL/phase meter.

    :param va: Local phase angle in radians.
    :param measured_frequency_hz: Measured frequency in Hz.
    :param nominal_frequency_hz: Nominal frequency in Hz.
    :return: Signal-name to expression mapping.
    """
    return {
        "Fmeas": measured_frequency_hz,
        "fmeas": measured_frequency_hz / nominal_frequency_hz,
        "cosphi": sym.cos(va),
        "sinphi": sym.sin(va),
    }


def build_rms_phase_locked_loop_block(
        vf: VarFactory,
        va: Expr,
        proportional_gain: float,
        integral_gain: float,
        nominal_frequency_hz: float,
        name: str,
) -> tuple[Block, Dict[str, Var]]:
    """
    Build one stateful VeraGrid synchronous-reference RMS phase measurement.

    The native equipment is a second-order synchronous-reference PLL. Its
    exported ``Kp`` and ``Ki`` gains act on the phase-detector error in radians;
    the resulting angular-speed deviation is therefore expressed in rad/s.

    :param vf: Circuit variable factory that owns the generated symbols.
    :param va: Measured positive-sequence voltage angle in radians.
    :param proportional_gain: Native ``ElmPhi.Kp`` proportional gain.
    :param integral_gain: Native ``ElmPhi.Ki`` integral gain.
    :param nominal_frequency_hz: RMS synchronous-reference frequency in Hz.
    :param name: Human-readable stable block name.
    :return: Pair ``(PLL block, output variable by native signal name)``.
    """
    phase: Var = vf.add_var(f"phase_{name}")
    integral_state: Var = vf.add_var(f"phase_error_integral_{name}")
    kp: Var = vf.add_var(f"Kp_{name}")
    ki: Var = vf.add_var(f"Ki_{name}")
    nominal_frequency: Var = vf.add_var(f"fn_{name}")
    measured_frequency: Var = vf.add_var(
        f"Fmeas_{name}",
        shared_reference=f"{name}:Fmeas",
    )
    measured_frequency_pu: Var = vf.add_var(
        f"fmeas_{name}",
        shared_reference=f"{name}:fmeas",
    )
    cosine: Var = vf.add_var(
        f"cosphi_{name}",
        shared_reference=f"{name}:cosphi",
    )
    sine: Var = vf.add_var(
        f"sinphi_{name}",
        shared_reference=f"{name}:sinphi",
    )

    # The wrapped sine detector remains continuous when the bus angle crosses
    # +/-pi and matches the native small-signal phase detector near lock.
    phase_error: Expr = sym.sin(va - phase)
    angular_speed_deviation: Expr = (kp * phase_error) + (ki * integral_state)
    frequency_expression: Expr = (
        nominal_frequency
        + (angular_speed_deviation / Const(2.0 * math.pi))
    )

    output_by_signal_name: Dict[str, Var] = dict()
    output_by_signal_name["Fmeas"] = measured_frequency
    output_by_signal_name["fmeas"] = measured_frequency_pu
    output_by_signal_name["cosphi"] = cosine
    output_by_signal_name["sinphi"] = sine

    # Explicit locked initialization makes the PLL neutral at the converged
    # power-flow point while preserving the measured absolute phase.
    init_eqs: Dict[Var, Expr] = dict()
    init_eqs[phase] = va
    init_eqs[integral_state] = Const(0.0)
    # Static parameters are assembled after device-local explicit equations.
    # Seed the known locked solution directly, avoiding any ordering dependency
    # on the later global parameter vector.
    init_eqs[measured_frequency] = Const(nominal_frequency_hz)
    init_eqs[measured_frequency_pu] = Const(1.0)
    init_eqs[cosine] = sym.cos(phase)
    init_eqs[sine] = sym.sin(phase)

    parameters: Dict[Var, Const] = dict()
    parameters[kp] = Const(proportional_gain)
    parameters[ki] = Const(integral_gain)
    parameters[nominal_frequency] = Const(nominal_frequency_hz)

    block: Block = Block(
        state_vars=list([phase, integral_state]),
        state_eqs=list([angular_speed_deviation, phase_error]),
        algebraic_vars=list([
            measured_frequency,
            measured_frequency_pu,
            cosine,
            sine,
        ]),
        algebraic_eqs=list([
            measured_frequency - frequency_expression,
            measured_frequency_pu - (measured_frequency / nominal_frequency),
            cosine - sym.cos(phase),
            sine - sym.sin(phase),
        ]),
        parameters=parameters,
        init_eqs=init_eqs,
        in_vars=list([va]),
        out_vars=list([
            measured_frequency,
            measured_frequency_pu,
            cosine,
            sine,
        ]),
        name=name,
    )
    return block, output_by_signal_name


def build_signal_meter_block(
        vf: VarFactory,
        signal_expressions: Dict[str, Expr],
        name: str,
        output_signal_names: tuple[str, ...] | None = None,
        symbol_suffix: str | None = None,
) -> tuple[Block, Dict[str, Var]]:
    """
    Materialize one reusable dynamic measurement block from named expressions.

    :param vf: Shared variable factory.
    :param signal_expressions: Signal-name to expression mapping.
    :param name: Block name suffix.
    :param output_signal_names: Optional user-facing output names paired by
        insertion order with ``signal_expressions``.
    :param symbol_suffix: Optional parser-safe suffix for generated variables.
        ``None`` preserves established imported symbolic identities.
    :return: Pair ``(block, output_var_by_signal_name)``.
    """
    algebraic_vars: list[Var] = list()
    algebraic_eqs: list[Expr] = list()
    out_vars: list[Var] = list()
    output_var_by_signal_name: Dict[str, Var] = dict()
    signal_name: str
    signal_expr: Expr
    output_var: Var
    output_signal_name: str
    output_index: int = 0

    if output_signal_names is None:
        resolved_output_signal_names: tuple[str, ...] = tuple(
            signal_expressions.keys()
        )
    else:
        resolved_output_signal_names = output_signal_names
    if (
            len(resolved_output_signal_names) == len(signal_expressions)
            and len(set(resolved_output_signal_names)) == len(
                resolved_output_signal_names
            )
            and all(
                signal_name.strip() != ""
                for signal_name in resolved_output_signal_names
            )
    ):
        pass
    else:
        raise ValueError(
            "Meter output names must pair uniquely with signal expressions"
        )

    # Native construction can separate the presentation name from its DAE
    # suffix. Existing imported models retain their established identities.
    if symbol_suffix is None:
        resolved_symbol_suffix: str = name
    else:
        resolved_symbol_suffix = normalize_rms_meter_symbol_fragment(symbol_suffix)

    # Each visible output owns one residual against the physical expression.
    # Imported aliases remain lookup keys only and cannot leak into the block UI.
    for signal_name, signal_expr in signal_expressions.items():
        output_signal_name = resolved_output_signal_names[output_index]
        output_var = vf.add_var(
            f"{output_signal_name}_{resolved_symbol_suffix}",
            shared_reference=f"{name}:{signal_name}",
        )
        algebraic_vars.append(output_var)
        algebraic_eqs.append(output_var - signal_expr)
        out_vars.append(output_var)
        output_var_by_signal_name[signal_name] = output_var
        output_index += 1

    block: Block = Block(
        name=name,
        algebraic_vars=algebraic_vars,
        algebraic_eqs=algebraic_eqs,
        out_vars=out_vars,
    )
    return block, output_var_by_signal_name


def build_rms_physical_signal_meter_block(
        vf: VarFactory,
        signal_expressions: Dict[str, Expr],
        output_signal_names: tuple[str, ...],
        name: str,
        source_fid: str,
        target_fid: str,
        terminal_side: RmsTerminalSide,
        meter_kind: RmsPhysicalMeterKind,
        symbol_suffix: str | None = None,
) -> tuple[Block, Dict[str, Var]]:
    """Build one canonical physical RMS meter with equations and identity.

    This constructor is source-format independent. Importers normalize their
    aliases before calling it, while native editors and scripts can call the
    same function directly.

    :param vf: Circuit variable factory that owns the generated symbols.
    :param signal_expressions: Lookup aliases paired with physical expressions.
    :param output_signal_names: VeraGrid-facing output names in lookup order.
    :param name: VeraGrid-facing meter block name.
    :param source_fid: Stable identity of the measurement declaration.
    :param target_fid: Stable identity of the measured bus or device.
    :param terminal_side: Physical terminal selected by the meter.
    :param meter_kind: Physical quantity family produced by the meter.
    :param symbol_suffix: Optional parser-safe variable suffix for native use.
    :return: Pair ``(meter block, output variable by lookup alias)``.
    """
    meter_block: Block
    output_by_alias_name: Dict[str, Var]
    meter_block, output_by_alias_name = build_signal_meter_block(
        vf=vf,
        signal_expressions=signal_expressions,
        name=name,
        output_signal_names=output_signal_names,
        symbol_suffix=symbol_suffix,
    )

    # Startup values use the same physical expressions as the algebraic
    # residuals, so opening the block exposes a complete, inspectable model.
    alias_name: str
    source_expression: Expr
    selected_output_names: list[str] = list()
    selected_output_uids: list[int] = list()
    for alias_name, source_expression in signal_expressions.items():
        output_var: Var | None = output_by_alias_name.get(alias_name, None)
        if output_var is None:
            raise KeyError("RMS meter output lookup is incomplete")
        else:
            meter_block.init_eqs[output_var] = source_expression
            selected_output_names.append(output_var.name)
            selected_output_uids.append(output_var.uid)

    meter_block.dynamic_model_contract.rms_physical_measurement_point = (
        RmsPhysicalMeasurementPoint(
            source_fid=source_fid,
            target_fid=target_fid,
            terminal_side=terminal_side,
            meter_kind=meter_kind,
            output_signal_names=tuple(selected_output_names),
            output_var_uids=tuple(selected_output_uids),
        )
    )
    return meter_block, output_by_alias_name


def build_rms_station_meter_bundle(vf: VarFactory,
                                   label: str,
                                   dc_plus_v: Expr,
                                   dc_minus_v: Expr,
                                   dc_current: Expr,
                                   nominal_frequency_hz: Expr,
                                   local_vm: Expr,
                                   local_va: Expr,
                                   local_p: Expr,
                                   local_q: Expr,
                                   poc1_vm: Expr,
                                   poc1_va: Expr,
                                   poc1_p: Expr,
                                   poc1_q: Expr,
                                   poc2_vm: Expr,
                                   poc2_va: Expr,
                                   poc2_p: Expr,
                                   poc2_q: Expr,
                                   ucap: Expr | None = None,
                                   measured_frequency_hz: Expr | None = None) -> tuple[list[Block], Dict[str, Var]]:
    """
    Build a complete VeraGrid RMS station measurement bundle.

    :param vf: Shared variable factory.
    :param label: Stable suffix appended to generated block names.
    :param dc_plus_v: Positive DC terminal voltage.
    :param dc_minus_v: Negative DC terminal voltage.
    :param dc_current: DC current seen by the control.
    :param nominal_frequency_hz: Nominal frequency in Hz.
    :param local_vm: Local AC voltage magnitude.
    :param local_va: Local AC voltage angle.
    :param local_p: Local active power.
    :param local_q: Local reactive power.
    :param poc1_vm: PoC1 voltage magnitude.
    :param poc1_va: PoC1 voltage angle.
    :param poc1_p: PoC1 active power.
    :param poc1_q: PoC1 reactive power.
    :param poc2_vm: PoC2 voltage magnitude.
    :param poc2_va: PoC2 voltage angle.
    :param poc2_p: PoC2 active power.
    :param poc2_q: PoC2 reactive power.
    :param ucap: Optional capacitor-voltage proxy.
    :param measured_frequency_hz: Optional measured frequency override.
    :return: Pair ``(measurement_blocks, signal_output_by_name)``.
    """
    blocks: list[Block] = list()
    signal_output_by_name: Dict[str, Var] = dict()
    resolved_measured_frequency_hz: Expr = nominal_frequency_hz if measured_frequency_hz is None else measured_frequency_hz
    resolved_ucap: Expr = Const(1.0) if ucap is None else ucap
    block: Block
    outputs: Dict[str, Var]

    # One station owns DC, local AC, point-of-connection and phase measurements.
    block, outputs = build_signal_meter_block(
        vf,
        {"udc_p": build_rms_voltage_meter_outputs_from_dc(dc_plus_v, nominal_frequency_hz)["ur"]},
        f"DCPlusMeas_{label}",
    )
    blocks.append(block)
    signal_output_by_name.update(outputs)

    block, outputs = build_signal_meter_block(
        vf,
        {"udc_n": build_rms_voltage_meter_outputs_from_dc(dc_minus_v, nominal_frequency_hz)["ur"]},
        f"DCMinusMeas_{label}",
    )
    blocks.append(block)
    signal_output_by_name.update(outputs)

    block, outputs = build_signal_meter_block(
        vf,
        {
            "idc_in": dc_current,
            "Ucap": resolved_ucap,
            "f_Hz_in": resolved_measured_frequency_hz,
            "fn_Hz_in": nominal_frequency_hz,
        },
        f"DCCurrentMeas_{label}",
    )
    blocks.append(block)
    signal_output_by_name.update(outputs)

    block, outputs = build_signal_meter_block(
        vf,
        {
            "u1r_loc": build_rms_voltage_meter_outputs_from_polar(local_vm, local_va, resolved_measured_frequency_hz, nominal_frequency_hz)["ur"],
            "u1i_loc": build_rms_voltage_meter_outputs_from_polar(local_vm, local_va, resolved_measured_frequency_hz, nominal_frequency_hz)["ui"],
        },
        f"LocalVMeas_{label}",
    )
    blocks.append(block)
    signal_output_by_name.update(outputs)

    block, outputs = build_signal_meter_block(
        vf,
        {
            "i1r_loc": build_rms_current_meter_outputs_from_pq(local_vm, local_va, local_p, local_q)["ir"],
            "i1i_loc": build_rms_current_meter_outputs_from_pq(local_vm, local_va, local_p, local_q)["ii"],
        },
        f"LocalIMeas_{label}",
    )
    blocks.append(block)
    signal_output_by_name.update(outputs)

    block, outputs = build_signal_meter_block(
        vf,
        {
            "u1r_poc": build_rms_voltage_meter_outputs_from_polar(poc1_vm, poc1_va, resolved_measured_frequency_hz, nominal_frequency_hz)["ur"],
            "u1i_poc": build_rms_voltage_meter_outputs_from_polar(poc1_vm, poc1_va, resolved_measured_frequency_hz, nominal_frequency_hz)["ui"],
            "u1r_poc2": build_rms_voltage_meter_outputs_from_polar(poc2_vm, poc2_va, resolved_measured_frequency_hz, nominal_frequency_hz)["ur"],
            "u1i_poc2": build_rms_voltage_meter_outputs_from_polar(poc2_vm, poc2_va, resolved_measured_frequency_hz, nominal_frequency_hz)["ui"],
        },
        f"PocVMeas_{label}",
    )
    blocks.append(block)
    signal_output_by_name.update(outputs)

    block, outputs = build_signal_meter_block(
        vf,
        {
            "i1r_poc": build_rms_current_meter_outputs_from_pq(poc1_vm, poc1_va, poc1_p, poc1_q)["ir"],
            "i1i_poc": build_rms_current_meter_outputs_from_pq(poc1_vm, poc1_va, poc1_p, poc1_q)["ii"],
            "i1r_poc2": build_rms_current_meter_outputs_from_pq(poc2_vm, poc2_va, poc2_p, poc2_q)["ir"],
            "i1i_poc2": build_rms_current_meter_outputs_from_pq(poc2_vm, poc2_va, poc2_p, poc2_q)["ii"],
        },
        f"PocIMeas_{label}",
    )
    blocks.append(block)
    signal_output_by_name.update(outputs)

    block, outputs = build_signal_meter_block(
        vf,
        build_rms_pll_meter_outputs(local_va, resolved_measured_frequency_hz, nominal_frequency_hz),
        f"PLLMeas_{label}",
    )
    blocks.append(block)
    signal_output_by_name.update(outputs)

    return blocks, signal_output_by_name


def connect_meter_signal_outputs_to_block_inputs(block: Block,
                                                 signal_output_by_name: Dict[str, Var],
                                                 var_factory: VarFactory) -> None:
    """
    Connect block input variables to one signal dictionary by exact name.

    :param block: Target block receiving the signals.
    :param signal_output_by_name: Signal-name to source-variable mapping.
    :param var_factory: Shared variable factory.
    :return: None.
    """
    input_var: Var
    source_var: Var | None

    # Name-based connection keeps source interfaces stable without per-signal plumbing.
    for input_var in block.in_vars:
        source_var = signal_output_by_name.get(input_var.name, None)
        if source_var is None:
            pass
        else:
            var_factory.add_connections([input_var], [source_var])
