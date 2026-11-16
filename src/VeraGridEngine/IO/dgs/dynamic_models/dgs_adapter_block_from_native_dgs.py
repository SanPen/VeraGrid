# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Controller-independent RMS blocks for native PowerFactory equipment.

Builders consume physical values, never DGS tables or a controller hierarchy.
Port order is documented by each builder. Construction parameters are symbolic
constants; only genuinely time-dependent quantities are states or inputs.
The importer remains responsible for matching slots and connecting identities.
"""

from __future__ import annotations

import math
from typing import Dict, Iterable, List, Tuple

from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.enumerations import (
    ParamPowerFlowReferenceType,
    SynchronousMachineSpeedVariationMode,
    VarPowerFlowReferenceType,
)


def _validate_native_parameters(
        positive: tuple[float, ...],
        nonnegative: tuple[float, ...] = tuple(),
        finite: tuple[float, ...] = tuple(),
) -> None:
    """Reject undefined physical equations before allocating a symbolic graph.

    :param positive: Strictly positive bases, time constants or capacitances.
    :param nonnegative: Nonnegative losses, gains or delays.
    :param finite: Signed parameters which must still be finite.
    :return: None.
    """
    if all(math.isfinite(value) and value > 0.0 for value in positive):
        pass
    else:
        raise ValueError("Native equipment requires finite positive bases and constants")
    if all(math.isfinite(value) and value >= 0.0 for value in nonnegative):
        pass
    else:
        raise ValueError("Native equipment requires finite nonnegative physical parameters")
    if all(math.isfinite(value) for value in finite):
        pass
    else:
        raise ValueError("Native equipment parameters must be finite")


def build_dgs_regc_voltage_source_block(
        delay_seconds: float,
        resistance_pu: float,
        reactance_pu: float,
        name: str = "REGC voltage source",
) -> Block:
    """Build the protected REGC voltage-behind-impedance equations.

    :param delay_seconds: Te; zero selects the exact algebraic realization.
    :param resistance_pu: re on the converter base.
    :param reactance_pu: xe on the converter base.
    :param name: Block display name.
    :return: Inputs (ur, ui, id_ref, iq_ref, is_blocked), outputs (ur_ref, ui_ref).
    """
    _validate_native_parameters(tuple(), (delay_seconds, resistance_pu, reactance_pu))
    ur: Var = Var("ur")
    ui: Var = Var("ui")
    direct_current: Var = Var("id_ref")
    quadrature_current: Var = Var("iq_ref")
    blocked: Var = Var("is_blocked")
    source_real: Var = Var("ur_ref")
    source_imaginary: Var = Var("ui_ref")
    filtered_real: Var = Var("x_lpf_d")
    filtered_imaginary: Var = Var("x_lpf_q")
    # E = V + ZI is evaluated before the optional lag and blocking selector.
    command_real: Expr = ur + resistance_pu * direct_current - reactance_pu * quadrature_current
    command_imaginary: Expr = ui + resistance_pu * quadrature_current + reactance_pu * direct_current
    output_real: Expr = (1.0 - blocked) * filtered_real + blocked * ur
    output_imaginary: Expr = (1.0 - blocked) * filtered_imaginary + blocked * ui
    initial: dict[Var, Expr] = dict((
        (filtered_real, command_real), (filtered_imaginary, command_imaginary),
        (source_real, output_real), (source_imaginary, output_imaginary),
    ))
    block: Block = Block(
        name=name,
        in_vars=list((ur, ui, direct_current, quadrature_current, blocked)),
        out_vars=list((source_real, source_imaginary)),
        algebraic_vars=list((source_real, source_imaginary)),
        algebraic_eqs=list((source_real - output_real, source_imaginary - output_imaginary)),
        init_eqs=initial, post_init_seed_eqs=dict(initial),
    )
    if delay_seconds > 0.0:
        block.state_vars = list((filtered_real, filtered_imaginary))
        block.state_eqs = list(((command_real - filtered_real) / delay_seconds,
                               (command_imaginary - filtered_imaginary) / delay_seconds))
        block.diff_vars = list((Var("dx_lpf_d_dt", base_var=filtered_real),
                                Var("dx_lpf_q_dt", base_var=filtered_imaginary)))
    else:
        # Te=0 must not leave a frozen state or divide by a zero time constant.
        block.algebraic_vars.extend((filtered_real, filtered_imaginary))
        block.algebraic_eqs.extend((filtered_real - command_real, filtered_imaginary - command_imaginary))
    return block


def build_dgs_regc_current_pll_block(
        proportional_gain: float,
        integral_gain: float,
        freeze_voltage_pu: float,
        minimum_speed: float,
        maximum_speed: float,
        name: str = "REGC current PLL",
) -> Block:
    """Build the protected current-frame PLL, including low-voltage freezing.

    :param proportional_gain: Kppll, applied to quadrature voltage in p.u.
    :param integral_gain: Kipll, applied to quadrature voltage in p.u.
    :param freeze_voltage_pu: Vpllfrz on the terminal voltage base.
    :param minimum_speed: wmin for the angle derivative in rad/s.
    :param maximum_speed: wmax for the angle derivative in rad/s.
    :param name: Block display name.
    :return: Inputs (ir, ii, ur, ui, u), outputs (id, iq); states (x0, x1).
    """
    _validate_native_parameters(tuple(), (proportional_gain, integral_gain, freeze_voltage_pu),
                                (minimum_speed, maximum_speed))
    if minimum_speed <= 0.0 <= maximum_speed:
        pass
    else:
        raise ValueError("PLL speed limits must contain the locked zero-speed correction")
    ir: Var = Var("ir")
    ii: Var = Var("ii")
    ur: Var = Var("ur")
    ui: Var = Var("ui")
    magnitude: Var = Var("u")
    direct_current: Var = Var("id")
    quadrature_current: Var = Var("iq")
    integrator: Var = Var("x0")
    angle: Var = Var("x1")
    # Use the native voltage error, not an additional magnitude normalization.
    cosine: Expr = sym.cos(angle)
    sine: Expr = sym.sin(angle)
    error: Expr = ui * cosine - ur * sine
    enabled: Expr = sym.heaviside(magnitude - freeze_voltage_pu)
    speed: Expr = sym.hard_sat(integrator + proportional_gain * error,
                               Const(minimum_speed), Const(maximum_speed))
    current_d: Expr = ir * cosine + ii * sine
    current_q: Expr = ii * cosine - ir * sine
    return Block(
        name=name, in_vars=list((ir, ii, ur, ui, magnitude)),
        out_vars=list((direct_current, quadrature_current)),
        state_vars=list((integrator, angle)),
        state_eqs=list((enabled * integral_gain * error, enabled * speed)),
        diff_vars=list((Var("dx0_dt", base_var=integrator), Var("dx1_dt", base_var=angle))),
        algebraic_vars=list((direct_current, quadrature_current)),
        algebraic_eqs=list((direct_current - current_d, quadrature_current - current_q)),
        init_eqs=dict(((integrator, Const(0.0)), (angle, sym.atan2(ui, ur)),
                       (direct_current, current_d), (quadrature_current, current_q))),
        post_init_seed_eqs=dict(((direct_current, current_d), (quadrature_current, current_q))),
    )


def build_dgs_elmgenstat_block(
        system_base_mva: float,
        equipment_base_mva: float,
        angle_delay_seconds: float = 0.0,
        name: str = "ElmGenstat",
) -> Block:
    """Build an equipment-base current injection on the system power base.

    :param system_base_mva: Circuit apparent-power base in MVA.
    :param equipment_base_mva: Generator apparent-power base in MVA.
    :param angle_delay_seconds: Optional lag on terminal-frame sine/cosine.
    :param name: Block display name.
    :return: Inputs (Vm, Va, id_ref, iq_ref), outputs (Pg, Qg, Pe, Qgen,
        Vt_r, Vt_i, It_r, It_i). Positive Pg/Qg inject into the network.
    """
    _validate_native_parameters((system_base_mva, equipment_base_mva), (angle_delay_seconds,))
    voltage: Var = Var("Vm", reference=VarPowerFlowReferenceType.Vm)
    angle: Var = Var("Va", reference=VarPowerFlowReferenceType.Va)
    id_ref: Var = Var("id_ref")
    iq_ref: Var = Var("iq_ref")
    pg: Var = Var("Pg", reference=VarPowerFlowReferenceType.P)
    qg: Var = Var("Qg", reference=VarPowerFlowReferenceType.Q)
    pe: Var = Var("Pe")
    qe: Var = Var("Qgen")
    ur: Var = Var("Vt_r")
    ui: Var = Var("Vt_i")
    ir: Var = Var("It_r")
    ii: Var = Var("It_i")
    gain: float = equipment_base_mva / system_base_mva
    cosine: Expr = sym.cos(angle)
    sine: Expr = sym.sin(angle)
    states: list[Var] = list()
    derivatives: list[Expr] = list()
    initial: dict[Var, Expr] = dict()
    if angle_delay_seconds > 0.0:
        delayed_cosine: Var = Var("dq_angle_cosine_delayed")
        delayed_sine: Var = Var("dq_angle_sine_delayed")
        states = list((delayed_cosine, delayed_sine))
        derivatives = list(((cosine - delayed_cosine) / angle_delay_seconds,
                            (sine - delayed_sine) / angle_delay_seconds))
        initial[delayed_cosine] = cosine
        initial[delayed_sine] = sine
        reference_cosine: Expr = delayed_cosine
        reference_sine: Expr = delayed_sine
    else:
        reference_cosine = cosine
        reference_sine = sine
    # Current commands and terminal-current outputs stay on the equipment base.
    current_real: Expr = id_ref * reference_cosine - iq_ref * reference_sine
    current_imaginary: Expr = id_ref * reference_sine + iq_ref * reference_cosine
    active: Expr = voltage * (current_real * cosine + current_imaginary * sine) * gain
    reactive: Expr = voltage * (current_real * sine - current_imaginary * cosine) * gain
    values: tuple[Expr, ...] = (active, reactive, pg / gain, qg / gain,
                                voltage * cosine, voltage * sine, current_real, current_imaginary)
    outputs: list[Var] = list((pg, qg, pe, qe, ur, ui, ir, ii))
    equations: list[Expr] = list()
    variable: Var
    expression: Expr
    for variable, expression in zip(outputs, values):
        equations.append(variable - expression)
        if variable is pg or variable is qg:
            # P/Q are seeded by load flow, not recomputed from unseeded orders.
            pass
        else:
            initial[variable] = expression
    initial[id_ref] = pg / (gain * voltage)
    initial[iq_ref] = -qg / (gain * voltage)
    return Block(
        name=name, in_vars=list((voltage, angle, id_ref, iq_ref)), out_vars=outputs,
        state_vars=states, state_eqs=derivatives,
        algebraic_vars=list(outputs), algebraic_eqs=equations,
        init_eqs=initial, post_init_seed_eqs=dict(initial),
        external_mapping=dict(((VarPowerFlowReferenceType.Vm, voltage),
                               (VarPowerFlowReferenceType.Va, angle),
                               (VarPowerFlowReferenceType.P, pg), (VarPowerFlowReferenceType.Q, qg))),
    )


def build_dgs_elmgenstat_voltage_block(system_base_mva: float, equipment_base_mva: float,
                                     name: str = "ElmGenstat voltage source") -> Block:
    """Build an ideal positive-sequence voltage source with terminal power unknowns.

    The external DGS network contains the series impedances; none is invented
    inside this native source. Current outputs remain on the equipment base.

    :param system_base_mva: Network apparent-power base.
    :param equipment_base_mva: Native source apparent-power base.
    :param name: Block display name.
    :return: Native block commanded by u1r_in and u1i_in.
    """
    _validate_native_parameters((system_base_mva, equipment_base_mva), tuple())
    vm: Var = Var("Vm", reference=VarPowerFlowReferenceType.Vm)
    va: Var = Var("Va", reference=VarPowerFlowReferenceType.Va)
    er: Var = Var("u1r_in")
    ei: Var = Var("u1i_in")
    pg: Var = Var("Pg", reference=VarPowerFlowReferenceType.P)
    qg: Var = Var("Qg", reference=VarPowerFlowReferenceType.Q)
    pe: Var = Var("Pe")
    qe: Var = Var("Qgen")
    ur: Var = Var("Vt_r")
    ui: Var = Var("Vt_i")
    ir: Var = Var("It_r")
    ii: Var = Var("It_i")
    gain: float = equipment_base_mva / system_base_mva
    cosine: Expr = sym.cos(va)
    sine: Expr = sym.sin(va)
    # Two voltage constraints replace prescribed-current equations. P/Q and
    # terminal currents are determined jointly by the connected network.
    equations: list[Expr] = list((pg - gain * vm * (ir * cosine + ii * sine),
                                  qg - gain * vm * (ir * sine - ii * cosine),
                                  pe - pg / gain, qe - qg / gain,
                                  ur - vm * cosine, ui - vm * sine, ur - er, ui - ei))
    initial: dict[Var, Expr] = dict(((pe, pg / gain), (qe, qg / gain),
        (ur, vm * cosine), (ui, vm * sine),
        (ir, (pg * cosine + qg * sine) / (gain * vm)),
        (ii, (pg * sine - qg * cosine) / (gain * vm)), (er, vm * cosine), (ei, vm * sine)))
    return Block(name=name, in_vars=list((vm, va, er, ei)),
                 out_vars=list((pg, qg, pe, qe, ur, ui, ir, ii)),
                 algebraic_vars=list((pg, qg, pe, qe, ur, ui, ir, ii)), algebraic_eqs=equations,
                 init_eqs=initial, post_init_seed_eqs=dict(initial),
                 external_mapping=dict(((VarPowerFlowReferenceType.Vm, vm), (VarPowerFlowReferenceType.Va, va),
                                        (VarPowerFlowReferenceType.P, pg), (VarPowerFlowReferenceType.Q, qg))))


def build_dgs_elmgenstat_voltage_source_block(
        system_base_mva: float, equipment_base_mva: float,
        short_circuit_impedance_percent: float, copper_losses_kw: float,
        name: str = "ElmGenstat voltage source",
) -> Block:
    """Build PF2024 ElmGenstat section 6.2 on the equipment current base.

    Voltage commands are rectangular positive-sequence phasors. The series
    reactor uses uk in percent and Pcu in kW on the single-unit sgn MVA base.
    """
    _validate_native_parameters((system_base_mva, equipment_base_mva,
                                 short_circuit_impedance_percent), (copper_losses_kw,))
    impedance = short_circuit_impedance_percent / 100.0
    resistance = copper_losses_kw / (1000.0 * equipment_base_mva)
    if resistance > impedance:
        raise ValueError("ElmGenstat copper losses exceed series impedance magnitude")
    reactance = math.sqrt(impedance * impedance - resistance * resistance)
    block = build_dgs_elmgenstat_block(system_base_mva, equipment_base_mva, name=name)
    voltage, angle, old_id, old_iq = block.in_vars
    pg, qg, pe, qe, ur, ui, ir, ii = block.out_vars
    real_command, imaginary_command = Var('u1r_in'), Var('u1i_in')
    gain = equipment_base_mva / system_base_mva
    terminal_real, terminal_imaginary = voltage * sym.cos(angle), voltage * sym.sin(angle)
    delta_real = real_command - terminal_real
    delta_imaginary = imaginary_command - terminal_imaginary
    current_real = (resistance * delta_real + reactance * delta_imaginary) / (impedance * impedance)
    current_imaginary = (resistance * delta_imaginary - reactance * delta_real) / (impedance * impedance)
    active = (terminal_real * current_real + terminal_imaginary * current_imaginary) * gain
    reactive = (terminal_imaginary * current_real - terminal_real * current_imaginary) * gain
    expressions = [active, reactive, pg / gain, qg / gain, terminal_real,
                   terminal_imaginary, current_real, current_imaginary]
    block.in_vars = [voltage, angle, real_command, imaginary_command]
    block.algebraic_eqs = [variable - expression for variable, expression in zip(block.out_vars, expressions)]
    # Reverse E = V + Z I at the load-flow operating point to initialize the
    # controller boundary. P/Q are system-base quantities, I equipment-base.
    initial_real = (pg * sym.cos(angle) + qg * sym.sin(angle)) / (gain * voltage)
    initial_imaginary = (pg * sym.sin(angle) - qg * sym.cos(angle)) / (gain * voltage)
    block.init_eqs = {variable: expression for variable, expression in zip(block.out_vars[2:], expressions[2:])}
    block.init_eqs[real_command] = terminal_real + resistance * initial_real - reactance * initial_imaginary
    block.init_eqs[imaginary_command] = terminal_imaginary + reactance * initial_real + resistance * initial_imaginary
    block.post_init_seed_eqs = dict(block.init_eqs)
    return block


def build_dgs_elmsvs_block(
        system_base_mva: float,
        reactor_mvar: float,
        capacitor_mvar: float,
        fixed_capacitor_mvar: float,
        capacitor_count: float,
        fixed_capacitor_count: float,
        name: str = "ElmSvs",
) -> Block:
    """Build the native SVC susceptibility-to-reactive-power boundary.

    :param system_base_mva: Circuit power base in MVA.
    :param reactor_mvar: Exported tcrmax, exposed as qreact.
    :param capacitor_mvar: Exported qmin, exposed as qcap, with its native sign.
    :param fixed_capacitor_mvar: Exported Qfixcap, exposed as qfixcap.
    :param capacitor_count: Exported nxcap.
    :param fixed_capacitor_count: Exported nfixcap.
    :param name: Block display name.
    :return: Inputs (Vm, Va, bsvs), outputs (Psvs, Qsvs, ysvs, qreact,
        qcap, qfixcap, nxcap, nfixcap); bsvs is MVAr at unit voltage.
    """
    _validate_native_parameters((system_base_mva,), (capacitor_count, fixed_capacitor_count),
                                (reactor_mvar, capacitor_mvar, fixed_capacitor_mvar))
    voltage: Var = Var("Vm", reference=VarPowerFlowReferenceType.Vm)
    angle: Var = Var("Va", reference=VarPowerFlowReferenceType.Va)
    susceptance: Var = Var("bsvs")
    active: Var = Var("Psvs", reference=VarPowerFlowReferenceType.P)
    reactive: Var = Var("Qsvs", reference=VarPowerFlowReferenceType.Q)
    ysvs: Var = Var("ysvs")
    qreact: Var = Var("qreact")
    qcap: Var = Var("qcap")
    qfixcap: Var = Var("qfixcap")
    nxcap: Var = Var("nxcap")
    nfixcap: Var = Var("nfixcap")
    injection: Expr = susceptance * voltage * voltage / system_base_mva
    initial: dict[Var, Expr] = dict(((active, Const(0.0)),
                                     (susceptance, reactive * system_base_mva / (voltage * voltage + 1e-12)),
                                     (ysvs, susceptance)))
    return Block(
        name=name, in_vars=list((voltage, angle, susceptance)),
        out_vars=list((active, reactive, ysvs, qreact, qcap, qfixcap, nxcap, nfixcap)),
        algebraic_vars=list((active, reactive, ysvs)),
        algebraic_eqs=list((active, reactive - injection, ysvs - susceptance)),
        parameters=dict(((qreact, Const(reactor_mvar)), (qcap, Const(capacitor_mvar)),
                         (qfixcap, Const(fixed_capacitor_mvar)), (nxcap, Const(capacitor_count)),
                         (nfixcap, Const(fixed_capacitor_count)))),
        init_eqs=initial, post_init_seed_eqs=dict(initial),
        external_mapping=dict(((VarPowerFlowReferenceType.Vm, voltage),
                               (VarPowerFlowReferenceType.Va, angle),
                               (VarPowerFlowReferenceType.P, active), (VarPowerFlowReferenceType.Q, reactive))),
    )


def build_dgs_elmvscmono_block(
        system_base_mva: float,
        equipment_base_mva: float,
        ac_base_kv: float,
        dc_bus_base_kv: float,
        dc_converter_base_kv: float,
        resistance_pu: float,
        reactance_pu: float,
        dc_capacitance_uf: float = 0.0,
        name: str = "ElmVscmono",
) -> Block:
    """Build a monopolar bridge with equipment-base dq modulation inputs.

    :param system_base_mva: Circuit power base in MVA.
    :param equipment_base_mva: Converter rating in MVA.
    :param ac_base_kv: AC line-to-line voltage base in kV.
    :param dc_bus_base_kv: Network DC voltage base in kV.
    :param dc_converter_base_kv: Controller DC voltage base in kV.
    :param resistance_pu: Physical reactor resistance on the converter base.
    :param reactance_pu: Physical reactor reactance on the converter base.
    :param dc_capacitance_uf: DC terminal capacitance in microfarads; zero disables it.
    :param name: Block display name.
    :return: Inputs (Vdc, Vm, Va, Pmd, Pmq, cosref, sinref), outputs
        (id, iq, uDC, Pdc, Pac, Qac, Iac, Idc_network, Pdc_conversion).
        Positive terminal power is injected into the respective network.
    """
    _validate_native_parameters((system_base_mva, equipment_base_mva, ac_base_kv,
                                 dc_bus_base_kv, dc_converter_base_kv, reactance_pu),
                                (resistance_pu, dc_capacitance_uf))
    vdc: Var = Var("Vdc", reference=VarPowerFlowReferenceType.Vf_dc)
    vm: Var = Var("Vm", reference=VarPowerFlowReferenceType.Vmt)
    va: Var = Var("Va", reference=VarPowerFlowReferenceType.Vat)
    pmd: Var = Var("Pmd")
    pmq: Var = Var("Pmq")
    cosref: Var = Var("cosref")
    sinref: Var = Var("sinref")
    current_d: Var = Var("id")
    current_q: Var = Var("iq")
    controller_dc_voltage: Var = Var("uDC")
    pdc: Var = Var("Pdc", reference=VarPowerFlowReferenceType.Pf)
    conversion_power: Var = Var("Pdc_conversion")
    pac: Var = Var("Pac", reference=VarPowerFlowReferenceType.Pt)
    qac: Var = Var("Qac", reference=VarPowerFlowReferenceType.Qt)
    iac: Var = Var("Iac", reference=VarPowerFlowReferenceType.Im)
    idc: Var = Var("Idc_network", reference=VarPowerFlowReferenceType.Idc)
    voltage_real: Expr = vm * sym.cos(va)
    voltage_imaginary: Expr = vm * sym.sin(va)
    voltage_d: Expr = voltage_real * cosref + voltage_imaginary * sinref
    voltage_q: Expr = -voltage_real * sinref + voltage_imaginary * cosref
    gain: float = equipment_base_mva / system_base_mva
    modulation_gain: float = math.sqrt(3.0 / 8.0) * dc_converter_base_kv / ac_base_kv
    dc_gain: float = dc_bus_base_kv / dc_converter_base_kv
    copper_loss: Expr = resistance_pu * (current_d * current_d + current_q * current_q) * gain
    # The bridge solves currents from modulation voltage and physical impedance;
    # Pmd/Pmq must never be interpreted directly as current commands.
    equations: list[Expr] = list((
        modulation_gain * controller_dc_voltage * pmd - voltage_d - resistance_pu * current_d + reactance_pu * current_q,
        modulation_gain * controller_dc_voltage * pmq - voltage_q - reactance_pu * current_d - resistance_pu * current_q,
        controller_dc_voltage - vdc * dc_gain,
        pac + (voltage_d * current_d + voltage_q * current_q) * gain,
        qac + (voltage_q * current_d - voltage_d * current_q) * gain,
        iac - sym.sqrt(current_d * current_d + current_q * current_q + 1e-12) * gain,
        conversion_power + pac - copper_loss,
        idc - pdc / (vdc + 1e-12),
    ))
    differential_variables: list[Var] = list()
    initial_derivatives: dict[Var, Expr] = dict()
    if dc_capacitance_uf > 0.0:
        # Terminal current differs from conversion current while the terminal
        # capacitor charges. The assembler must keep the shared DC voltage and
        # its derivative identity consistent across all devices on that bus.
        derivative: Var = Var("dVdc_dt", base_var=vdc)
        differential_variables = list((derivative,))
        capacitance_gain: float = dc_capacitance_uf * 1e-6 * dc_bus_base_kv ** 2 / system_base_mva
        equations.append(pdc - conversion_power - capacitance_gain * vdc * derivative)
        initial_derivatives[derivative] = Const(0.0)
    else:
        equations.append(pdc - conversion_power)
    voltage_squared: Expr = voltage_d * voltage_d + voltage_q * voltage_q + 1e-12
    initial: dict[Var, Expr] = dict((
        (controller_dc_voltage, vdc * dc_gain),
        (current_d, (-voltage_d * pac - voltage_q * qac) / (gain * voltage_squared)),
        (current_q, (-voltage_q * pac + voltage_d * qac) / (gain * voltage_squared)),
        (pmd, (voltage_d + resistance_pu * current_d - reactance_pu * current_q)
         / (modulation_gain * controller_dc_voltage + 1e-12)),
        (pmq, (voltage_q + reactance_pu * current_d + resistance_pu * current_q)
         / (modulation_gain * controller_dc_voltage + 1e-12)),
        (iac, sym.sqrt(current_d * current_d + current_q * current_q + 1e-12) * gain),
        (conversion_power, copper_loss - pac), (pdc, conversion_power),
        (idc, pdc / (vdc + 1e-12)),
    ))
    outputs: list[Var] = list((current_d, current_q, controller_dc_voltage, pdc, pac, qac, iac, idc, conversion_power))
    return Block(
        name=name, in_vars=list((vdc, vm, va, pmd, pmq, cosref, sinref)),
        out_vars=outputs, algebraic_vars=list(outputs), algebraic_eqs=equations,
        diff_vars=differential_variables, diff_init_eqs=initial_derivatives,
        init_eqs=initial, post_init_seed_eqs=dict(initial),
        external_mapping=dict(((VarPowerFlowReferenceType.Vf_dc, vdc),
                               (VarPowerFlowReferenceType.Vmt, vm), (VarPowerFlowReferenceType.Vat, va),
                               (VarPowerFlowReferenceType.Pf, pdc), (VarPowerFlowReferenceType.Pt, pac),
                               (VarPowerFlowReferenceType.Qt, qac), (VarPowerFlowReferenceType.Idc, idc),
                               (VarPowerFlowReferenceType.Im, iac))),
    )


def build_dgs_elmvsc_two_level_block(
        system_base_mva: float,
        equipment_base_mva: float,
        ac_base_kv: float,
        dc_positive_base_kv: float,
        dc_negative_base_kv: float,
        resistance_pu: float,
        reactance_pu: float,
        idle_loss_pu: float = 0.0,
        linear_loss_pu: float = 0.0,
        quadratic_loss_pu: float = 0.0,
        name: str = "ElmVsc two-level",
) -> Block:
    """Build a two-level averaged PWM bridge between two DC poles and AC.

    Modulation uses the same stationary real/imaginary coordinates as the MMC,
    but its voltage source is the terminal DC span, with no arm-energy state.
    Terminal capacitances belong to the network's DC bus models.

    :param system_base_mva: Network power base.
    :param equipment_base_mva: Converter power base for series impedance.
    :param ac_base_kv: AC line-to-line voltage base.
    :param dc_positive_base_kv: Positive-pole voltage base as a magnitude.
    :param dc_negative_base_kv: Negative-pole voltage base as a magnitude.
    :param resistance_pu: Series resistance on the equipment base.
    :param reactance_pu: Series reactance on the equipment base.
    :param idle_loss_pu: No-load loss on the system power base.
    :param linear_loss_pu: Linear AC-current loss coefficient.
    :param quadratic_loss_pu: Quadratic AC-current loss excluding the explicit series resistance.
    :param name: Physical block display name.
    :return: Algebraic bridge with Pmr/Pmi commands and physical terminal probes.
    """
    _validate_native_parameters((system_base_mva, equipment_base_mva, ac_base_kv,
                                 dc_positive_base_kv, dc_negative_base_kv),
                                (resistance_pu, reactance_pu, idle_loss_pu, linear_loss_pu, quadratic_loss_pu))
    positive: Var = Var("Vdc_positive", reference=VarPowerFlowReferenceType.Vf_dc)
    negative: Var = Var("Vdc_negative", reference=VarPowerFlowReferenceType.Vt_dc)
    vm: Var = Var("Vm", reference=VarPowerFlowReferenceType.Vmt)
    va: Var = Var("Va", reference=VarPowerFlowReferenceType.Vat)
    pmr: Var = Var("Pmr")
    pmi: Var = Var("Pmi")
    pac: Var = Var("Pac", reference=VarPowerFlowReferenceType.Pt)
    qac: Var = Var("Qac", reference=VarPowerFlowReferenceType.Qt)
    pdc: Var = Var("Pdc", reference=VarPowerFlowReferenceType.Pf)
    iac: Var = Var("Iac", reference=VarPowerFlowReferenceType.Im)
    idc: Var = Var("Idc_network", reference=VarPowerFlowReferenceType.Idc)
    dc_span: Expr = positive * dc_positive_base_kv - negative * dc_negative_base_kv
    dc_network_span: Expr = positive - negative
    vr: Expr = vm * sym.cos(va)
    vi: Expr = vm * sym.sin(va)
    # AC current and terminal powers are positive into the converter, matching
    # the existing equipment boundary and the RMS network injection convention.
    ir: Expr = (pac * vr + qac * vi) / (vm * vm + 1e-9)
    ii: Expr = (pac * vi - qac * vr) / (vm * vm + 1e-9)
    resistance: float = resistance_pu * system_base_mva / equipment_base_mva
    reactance: float = reactance_pu * system_base_mva / equipment_base_mva
    er: Expr = vr - resistance * ir + reactance * ii
    ei: Expr = vi - reactance * ir - resistance * ii
    modulation_gain: float = math.sqrt(3.0 / 8.0) / ac_base_kv
    # Pcu is represented by the series impedance, not by an MMC arm capacitor.
    # Its dissipation must also appear in the bridge's steady energy balance.
    copper: Expr = resistance * (ir * ir + ii * ii)
    losses: Expr = idle_loss_pu + linear_loss_pu * iac + quadratic_loss_pu * iac * iac
    current_magnitude: Expr = sym.sqrt(pac * pac + qac * qac + 1e-9) / (vm + 1e-9)
    initial: dict[Var, Expr] = dict((
        (pmr, er / (modulation_gain * dc_span + 1e-12)),
        (pmi, ei / (modulation_gain * dc_span + 1e-12)),
        (iac, current_magnitude), (pdc, losses + copper - pac),
        (idc, pdc / (dc_network_span + 1e-9)),
    ))
    outputs: list[Var] = list((pac, qac, pdc, iac, idc))
    return Block(
        name=name, in_vars=list((positive, negative, vm, va, pmr, pmi)),
        out_vars=outputs, algebraic_vars=list(outputs),
        algebraic_eqs=list((
            er - modulation_gain * dc_span * pmr,
            ei - modulation_gain * dc_span * pmi,
            pdc + pac - copper - losses,
            iac - current_magnitude, idc - pdc / (dc_network_span + 1e-9),
        )),
        init_eqs=initial, post_init_seed_eqs=dict(initial),
        external_mapping=dict((
            (VarPowerFlowReferenceType.Vf_dc, positive), (VarPowerFlowReferenceType.Vt_dc, negative),
            (VarPowerFlowReferenceType.Vmt, vm), (VarPowerFlowReferenceType.Vat, va),
            (VarPowerFlowReferenceType.Pf, pdc), (VarPowerFlowReferenceType.Pt, pac),
            (VarPowerFlowReferenceType.Qt, qac), (VarPowerFlowReferenceType.Im, iac),
            (VarPowerFlowReferenceType.Idc, idc),
        )),
    )


def build_dgs_elmvsc_block(
        system_base_mva: float,
        equipment_base_mva: float,
        ac_base_kv: float,
        dc_positive_base_kv: float,
        dc_negative_base_kv: float,
        nominal_cell_voltage_kv: float,
        arm_capacitance_uf: float,
        resistance_pu: float,
        reactance_pu: float,
        idle_loss_pu: float = 0.0,
        linear_loss_pu: float = 0.0,
        quadratic_loss_pu: float = 0.0,
        name: str = "ElmVsc",
) -> Block:
    """Build the bipolar MMC bridge and its physical capacitor-energy state.

    :param system_base_mva: Circuit power base in MVA.
    :param equipment_base_mva: Converter rating in MVA.
    :param ac_base_kv: AC line-to-line voltage base in kV.
    :param dc_positive_base_kv: Positive pole voltage base in kV.
    :param dc_negative_base_kv: Negative pole voltage base in kV, as a magnitude.
    :param nominal_cell_voltage_kv: Nominal aggregate internal capacitor voltage.
    :param arm_capacitance_uf: Physical arm capacitance; Ceq = 6 Carm.
    :param resistance_pu: Physical series resistance on the equipment base.
    :param reactance_pu: Physical series reactance on the equipment base.
    :param idle_loss_pu: No-load loss on the system base at nominal cell voltage.
    :param linear_loss_pu: Linear coefficient for system-base AC current magnitude.
    :param quadratic_loss_pu: Quadratic coefficient for system-base AC current.
    :param name: Block display name.
    :return: Inputs (Vdc_positive, Vdc_negative, Vm, Va, Pmr, Pmi, mdc),
        outputs (iDC, Ucap, Pdc, Pac, Qac, Iac, Idc_network, ElmVsc_iDC_equipment).
        Positive AC/DC terminal powers enter the internal energy balance.
    """
    _validate_native_parameters((system_base_mva, equipment_base_mva, ac_base_kv,
                                 dc_positive_base_kv, dc_negative_base_kv, nominal_cell_voltage_kv,
                                 arm_capacitance_uf, reactance_pu),
                                (resistance_pu, idle_loss_pu, linear_loss_pu, quadratic_loss_pu))
    positive_voltage: Var = Var("Vdc_positive", reference=VarPowerFlowReferenceType.Vf_dc)
    negative_voltage: Var = Var("Vdc_negative", reference=VarPowerFlowReferenceType.Vt_dc)
    vm: Var = Var("Vm", reference=VarPowerFlowReferenceType.Vmt)
    va: Var = Var("Va", reference=VarPowerFlowReferenceType.Vat)
    pmr: Var = Var("Pmr")
    pmi: Var = Var("Pmi")
    mdc: Var = Var("mdc")
    controller_current: Var = Var("iDC")
    cell_voltage: Var = Var("Ucap")
    pdc: Var = Var("Pdc", reference=VarPowerFlowReferenceType.Pf)
    pac: Var = Var("Pac", reference=VarPowerFlowReferenceType.Pt)
    qac: Var = Var("Qac", reference=VarPowerFlowReferenceType.Qt)
    iac: Var = Var("Iac", reference=VarPowerFlowReferenceType.Im)
    idc: Var = Var("Idc_network", reference=VarPowerFlowReferenceType.Idc)
    observer: Var = Var("ElmVsc_iDC_equipment")
    base_ratio: float = system_base_mva / equipment_base_mva
    resistance: float = resistance_pu * base_ratio
    reactance: float = reactance_pu * base_ratio
    physical_span: Expr = positive_voltage * dc_positive_base_kv - negative_voltage * dc_negative_base_kv
    network_span: Expr = positive_voltage - negative_voltage
    voltage_real: Expr = vm * sym.cos(va)
    voltage_imaginary: Expr = vm * sym.sin(va)
    current_real: Expr = (pac * voltage_real + qac * voltage_imaginary) / (vm * vm + 1e-9)
    current_imaginary: Expr = (pac * voltage_imaginary - qac * voltage_real) / (vm * vm + 1e-9)
    internal_real: Expr = voltage_real - resistance * current_real + reactance * current_imaginary
    internal_imaginary: Expr = voltage_imaginary - reactance * current_real - resistance * current_imaginary
    loss: Expr = idle_loss_pu * cell_voltage * cell_voltage / (nominal_cell_voltage_kv ** 2 + 1e-9) \
        + linear_loss_pu * iac + quadratic_loss_pu * iac * iac
    # The state is in kV, capacitance in uF, and the surplus power in system p.u.
    energy_derivative: Expr = (pdc + pac - loss) * system_base_mva * 1e6 \
        / (6.0 * arm_capacitance_uf * cell_voltage + 1e-9)
    current_gain: float = base_ratio * nominal_cell_voltage_kv / dc_positive_base_kv
    current_magnitude: Expr = sym.sqrt(pac * pac + qac * qac + 1e-9) / (vm + 1e-9)
    initial: dict[Var, Expr] = dict((
        (cell_voltage, Const(nominal_cell_voltage_kv)),
        (mdc, physical_span / nominal_cell_voltage_kv),
        (pmr, internal_real * ac_base_kv / (math.sqrt(3.0 / 8.0) * nominal_cell_voltage_kv)),
        (pmi, internal_imaginary * ac_base_kv / (math.sqrt(3.0 / 8.0) * nominal_cell_voltage_kv)),
        (iac, current_magnitude), (pdc, loss - pac),
        (idc, pdc / (network_span + 1e-9)),
        (controller_current, -idc * current_gain), (observer, controller_current),
    ))
    return Block(
        name=name, in_vars=list((positive_voltage, negative_voltage, vm, va, pmr, pmi, mdc)),
        out_vars=list((controller_current, cell_voltage, pdc, pac, qac, iac, idc, observer)),
        state_vars=list((cell_voltage,)), state_eqs=list((energy_derivative,)),
        algebraic_vars=list((controller_current, observer, idc, pdc, pac, qac, iac)),
        algebraic_eqs=list((
            internal_real - math.sqrt(3.0 / 8.0) * cell_voltage * pmr / ac_base_kv,
            internal_imaginary - math.sqrt(3.0 / 8.0) * cell_voltage * pmi / ac_base_kv,
            mdc * cell_voltage - physical_span,
            iac - current_magnitude, idc - pdc / (network_span + 1e-9),
            controller_current + idc * current_gain, observer - controller_current,
        )),
        init_eqs=initial, post_init_seed_eqs=dict(initial),
        external_mapping=dict(((VarPowerFlowReferenceType.Vf_dc, positive_voltage),
                               (VarPowerFlowReferenceType.Vt_dc, negative_voltage),
                               (VarPowerFlowReferenceType.Vmt, vm), (VarPowerFlowReferenceType.Vat, va),
                               (VarPowerFlowReferenceType.Pf, pdc), (VarPowerFlowReferenceType.Pt, pac),
                               (VarPowerFlowReferenceType.Qt, qac), (VarPowerFlowReferenceType.Idc, idc),
                               (VarPowerFlowReferenceType.Im, iac))),
    )



class DgsElmSymMachineParameters:
    """Typed physical ElmSym values independent of DGS rows and controllers.

    Reactances are on the machine MVA base and times are in seconds. Native
    saturation selectors retain their exported integer encoding.
    """

    __slots__ = ('Snom', 'rated_power_factor', 'Rs', 'Xd', 'Xq', 'Xd_prime', 'Xq_prime', 'Xd_2prime', 'Xq_2prime', 'Xl', 'Td0_prime', 'Tq0_prime', 'Td0_2prime', 'Tq0_2prime', 'rms_acceleration_time_constant', 'rms_dpu', 'rms_dkd', 'rms_dpe', 'rms_rotor_coupling_reactance_d', 'rms_rotor_coupling_reactance_q', 'rms_td_prime_short_circuit', 'rms_tq_prime_short_circuit', 'rms_td_2prime_short_circuit', 'rms_tq_2prime_short_circuit', 'rms_excitation_current_base', 'rms_excitation_voltage_base_ratio', 'rms_excitation_gain', 'rms_rated_field_voltage', 'rms_saturation_curve_type', 'rms_saturation_axis_mode', 'rms_saturation_smoothing_factor', 'rms_speed_variation_mode', 'rms_saturation_sg10', 'rms_saturation_sg12', 'rms_saturation_sg10q', 'rms_saturation_sg12q', 'rms_saturation_voltage_points', 'rms_saturation_excitation_points', 'rms_saturation_q_voltage_points', 'rms_saturation_q_excitation_points')

    def __init__(
            self,
            Snom: float,
            rated_power_factor: float,
            Rs: float,
            Xd: float,
            Xq: float,
            Xd_prime: float,
            Xq_prime: float,
            Xd_2prime: float,
            Xq_2prime: float,
            Xl: float,
            Td0_prime: float,
            Tq0_prime: float,
            Td0_2prime: float,
            Tq0_2prime: float,
            rms_acceleration_time_constant: float,
            rms_dpu: float,
            rms_dkd: float,
            rms_dpe: float,
            rms_rotor_coupling_reactance_d: float,
            rms_rotor_coupling_reactance_q: float,
            rms_td_prime_short_circuit: float,
            rms_tq_prime_short_circuit: float,
            rms_td_2prime_short_circuit: float,
            rms_tq_2prime_short_circuit: float,
            rms_excitation_current_base: float,
            rms_excitation_voltage_base_ratio: float,
            rms_excitation_gain: float,
            rms_rated_field_voltage: float,
            rms_saturation_curve_type: int,
            rms_saturation_axis_mode: int,
            rms_saturation_smoothing_factor: float,
            rms_speed_variation_mode: SynchronousMachineSpeedVariationMode,
            rms_saturation_sg10: float,
            rms_saturation_sg12: float,
            rms_saturation_sg10q: float,
            rms_saturation_sg12q: float,
            rms_saturation_voltage_points: tuple[float, ...],
            rms_saturation_excitation_points: tuple[float, ...],
            rms_saturation_q_voltage_points: tuple[float, ...],
            rms_saturation_q_excitation_points: tuple[float, ...],
    ) -> None:
        """Store one explicit native machine parameter contract.

        :param Snom: Native machine Snom.
        :param rated_power_factor: Native machine rated power factor.
        :param Rs: Native machine Rs.
        :param Xd: Native machine Xd.
        :param Xq: Native machine Xq.
        :param Xd_prime: Native machine Xd prime.
        :param Xq_prime: Native machine Xq prime.
        :param Xd_2prime: Native machine Xd 2prime.
        :param Xq_2prime: Native machine Xq 2prime.
        :param Xl: Native machine Xl.
        :param Td0_prime: Native machine Td0 prime.
        :param Tq0_prime: Native machine Tq0 prime.
        :param Td0_2prime: Native machine Td0 2prime.
        :param Tq0_2prime: Native machine Tq0 2prime.
        :param rms_acceleration_time_constant: Native machine rms acceleration time constant.
        :param rms_dpu: Native machine rms dpu.
        :param rms_dkd: Native machine rms dkd.
        :param rms_dpe: Native machine rms dpe.
        :param rms_rotor_coupling_reactance_d: Native machine rms rotor coupling reactance d.
        :param rms_rotor_coupling_reactance_q: Native machine rms rotor coupling reactance q.
        :param rms_td_prime_short_circuit: Native machine rms td prime short circuit.
        :param rms_tq_prime_short_circuit: Native machine rms tq prime short circuit.
        :param rms_td_2prime_short_circuit: Native machine rms td 2prime short circuit.
        :param rms_tq_2prime_short_circuit: Native machine rms tq 2prime short circuit.
        :param rms_excitation_current_base: Native machine rms excitation current base.
        :param rms_excitation_voltage_base_ratio: Native machine rms excitation voltage base ratio.
        :param rms_excitation_gain: Native machine rms excitation gain.
        :param rms_rated_field_voltage: Native machine rms rated field voltage.
        :param rms_saturation_curve_type: Native machine rms saturation curve type.
        :param rms_saturation_axis_mode: Native machine rms saturation axis mode.
        :param rms_saturation_smoothing_factor: Native machine rms saturation smoothing factor.
        :param rms_speed_variation_mode: Native machine rms speed variation mode.
        :param rms_saturation_sg10: Native machine rms saturation sg10.
        :param rms_saturation_sg12: Native machine rms saturation sg12.
        :param rms_saturation_sg10q: Native machine rms saturation sg10q.
        :param rms_saturation_sg12q: Native machine rms saturation sg12q.
        :param rms_saturation_voltage_points: Native machine rms saturation voltage points.
        :param rms_saturation_excitation_points: Native machine rms saturation excitation points.
        :param rms_saturation_q_voltage_points: Native machine rms saturation q voltage points.
        :param rms_saturation_q_excitation_points: Native machine rms saturation q excitation points.
        :return: None.
        """
        # Keep source values typed and separate from symbolic runtime variables.
        self.Snom: float = Snom
        self.rated_power_factor: float = rated_power_factor
        self.Rs: float = Rs
        self.Xd: float = Xd
        self.Xq: float = Xq
        self.Xd_prime: float = Xd_prime
        self.Xq_prime: float = Xq_prime
        self.Xd_2prime: float = Xd_2prime
        self.Xq_2prime: float = Xq_2prime
        self.Xl: float = Xl
        self.Td0_prime: float = Td0_prime
        self.Tq0_prime: float = Tq0_prime
        self.Td0_2prime: float = Td0_2prime
        self.Tq0_2prime: float = Tq0_2prime
        self.rms_acceleration_time_constant: float = rms_acceleration_time_constant
        self.rms_dpu: float = rms_dpu
        self.rms_dkd: float = rms_dkd
        self.rms_dpe: float = rms_dpe
        self.rms_rotor_coupling_reactance_d: float = rms_rotor_coupling_reactance_d
        self.rms_rotor_coupling_reactance_q: float = rms_rotor_coupling_reactance_q
        self.rms_td_prime_short_circuit: float = rms_td_prime_short_circuit
        self.rms_tq_prime_short_circuit: float = rms_tq_prime_short_circuit
        self.rms_td_2prime_short_circuit: float = rms_td_2prime_short_circuit
        self.rms_tq_2prime_short_circuit: float = rms_tq_2prime_short_circuit
        self.rms_excitation_current_base: float = rms_excitation_current_base
        self.rms_excitation_voltage_base_ratio: float = rms_excitation_voltage_base_ratio
        self.rms_excitation_gain: float = rms_excitation_gain
        self.rms_rated_field_voltage: float = rms_rated_field_voltage
        self.rms_saturation_curve_type: int = rms_saturation_curve_type
        self.rms_saturation_axis_mode: int = rms_saturation_axis_mode
        self.rms_saturation_smoothing_factor: float = rms_saturation_smoothing_factor
        self.rms_speed_variation_mode: SynchronousMachineSpeedVariationMode = rms_speed_variation_mode
        self.rms_saturation_sg10: float = rms_saturation_sg10
        self.rms_saturation_sg12: float = rms_saturation_sg12
        self.rms_saturation_sg10q: float = rms_saturation_sg10q
        self.rms_saturation_sg12q: float = rms_saturation_sg12q
        self.rms_saturation_voltage_points: tuple[float, ...] = rms_saturation_voltage_points
        self.rms_saturation_excitation_points: tuple[float, ...] = rms_saturation_excitation_points
        self.rms_saturation_q_voltage_points: tuple[float, ...] = rms_saturation_q_voltage_points
        self.rms_saturation_q_excitation_points: tuple[float, ...] = rms_saturation_q_excitation_points


def _float_tuple(values: Iterable[float]) -> Tuple[float, ...]:
    """Copy an iterable into an immutable tuple of floats.

    :param values: Numeric source values.
    :return: Immutable float tuple.
    """
    result_values: List[float] = list()
    source_value: float
    for source_value in values:
        result_values.append(float(source_value))
    else:
        pass
    return tuple(result_values)


def _machine_parameter_contract_is_valid(machine_parameters: DgsElmSymMachineParameters) -> bool:
    """Validate parameters required by the supported standard RMS machine.

    :param machine_parameters: Native synchronous-machine physical values.
    :return: ``True`` when the DGS contains a finite physical parameter set.
    """
    strictly_positive_values: Tuple[float, ...] = (
        float(machine_parameters.rms_acceleration_time_constant),
        float(machine_parameters.Snom),
        float(machine_parameters.rated_power_factor),
        float(machine_parameters.Xd),
        float(machine_parameters.Xq),
        float(machine_parameters.Xd_prime),
        float(machine_parameters.Xd_2prime),
        float(machine_parameters.Xq_2prime),
        float(machine_parameters.Td0_prime),
        float(machine_parameters.Td0_2prime),
        float(machine_parameters.Tq0_2prime),
    )
    nonnegative_values: Tuple[float, ...] = (
        float(machine_parameters.Rs),
        float(machine_parameters.Xl),
        float(machine_parameters.Tq0_prime),
        float(machine_parameters.rms_dpu),
        float(machine_parameters.rms_dkd),
        float(machine_parameters.rms_dpe),
        float(machine_parameters.rms_rotor_coupling_reactance_d),
        float(machine_parameters.rms_rotor_coupling_reactance_q),
        float(machine_parameters.rms_td_prime_short_circuit),
        float(machine_parameters.rms_tq_prime_short_circuit),
        float(machine_parameters.rms_td_2prime_short_circuit),
        float(machine_parameters.rms_tq_2prime_short_circuit),
    )
    value: float

    for value in strictly_positive_values:
        if math.isfinite(value) and value > 0.0:
            pass
        else:
            return False
    for value in nonnegative_values:
        if math.isfinite(value) and value >= 0.0:
            pass
        else:
            return False
    if float(machine_parameters.Xd) >= float(machine_parameters.Xd_prime) >= float(machine_parameters.Xd_2prime):
        pass
    else:
        return False
    if float(machine_parameters.Xq) >= float(machine_parameters.Xq_2prime):
        pass
    else:
        return False
    if float(machine_parameters.Tq0_prime) > 0.0:
        return float(machine_parameters.Xq_prime) >= float(machine_parameters.Xq_2prime)
    else:
        return True


class _PowerFactoryEquivalentCircuit:
    """Hold the exact rotor circuit derived from one ``TypSym`` record."""

    __slots__ = (
        "xad", "xaq", "xrld", "xrlq", "xfd", "x1d", "x1q", "x2q",
        "t_sigma_fd", "t_sigma_1d", "t_sigma_1q", "t_sigma_2q",
        "excitation_current_base", "excitation_voltage_base_ratio",
        "saturation_curve_type", "saturation_axis_mode",
        "saturation_smoothing_factor",
        "speed_variation_mode",
        "saturation_voltage_points", "saturation_excitation_points",
        "saturation_sg10", "saturation_sg12",
        "saturation_q_voltage_points", "saturation_q_excitation_points",
        "saturation_sg10q", "saturation_sg12q",
    )

    def __init__(
            self,
            xad: float,
            xaq: float,
            xrld: float,
            xrlq: float,
            xfd: float,
            x1d: float,
            x1q: float,
            x2q: float,
            t_sigma_fd: float,
            t_sigma_1d: float,
            t_sigma_1q: float,
            t_sigma_2q: float,
            excitation_current_base: float,
            excitation_voltage_base_ratio: float,
            saturation_curve_type: int,
            saturation_axis_mode: int,
            saturation_smoothing_factor: float,
            speed_variation_mode: SynchronousMachineSpeedVariationMode,
            saturation_voltage_points: Tuple[float, ...],
            saturation_excitation_points: Tuple[float, ...],
            saturation_sg10: float,
            saturation_sg12: float,
            saturation_q_voltage_points: Tuple[float, ...],
            saturation_q_excitation_points: Tuple[float, ...],
            saturation_sg10q: float,
            saturation_sg12q: float,
    ) -> None:
        """Create an immutable-size equivalent-circuit value object.

        :param xad: d-axis mutual reactance in p.u.
        :param xaq: q-axis mutual reactance in p.u.
        :param xrld: Field-to-damper coupling reactance in p.u.
        :param xrlq: q-axis damper coupling reactance in p.u.
        :param xfd: Field-winding leakage reactance in p.u.
        :param x1d: d-axis damper leakage reactance in p.u.
        :param x1q: First q-axis damper leakage reactance in p.u.
        :param x2q: Second q-axis damper leakage reactance in p.u.
        :param t_sigma_fd: Field-winding rotor time constant in seconds.
        :param t_sigma_1d: d-axis damper rotor time constant in seconds.
        :param t_sigma_1q: First q-axis damper time constant in seconds.
        :param t_sigma_2q: Second q-axis damper time constant in seconds.
        :param excitation_current_base: Reciprocal excitation-current base.
        :param excitation_voltage_base_ratio: Exciter voltage base ratio.
        :param saturation_curve_type: Native saturation-curve selector.
        :param saturation_axis_mode: Native saturation-axis selector.
        :param saturation_smoothing_factor: Native tabular smoothing factor.
        :param speed_variation_mode: Native speed treatment in stator-voltage equations.
        :param saturation_voltage_points: Main-flux curve coordinates.
        :param saturation_excitation_points: Excitation-current coordinates.
        :param saturation_sg10: Saturation coefficient at 1.0 p.u. flux.
        :param saturation_sg12: Saturation coefficient at 1.2 p.u. flux.
        :param saturation_q_voltage_points: q-axis curve coordinates.
        :param saturation_q_excitation_points: q-axis excitation coordinates.
        :param saturation_sg10q: q-axis saturation at 1.0 p.u. flux.
        :param saturation_sg12q: q-axis saturation at 1.2 p.u. flux.
        :return: None.
        """
        self.xad: float = float(xad)
        self.xaq: float = float(xaq)
        self.xrld: float = float(xrld)
        self.xrlq: float = float(xrlq)
        self.xfd: float = float(xfd)
        self.x1d: float = float(x1d)
        self.x1q: float = float(x1q)
        self.x2q: float = float(x2q)
        self.t_sigma_fd: float = float(t_sigma_fd)
        self.t_sigma_1d: float = float(t_sigma_1d)
        self.t_sigma_1q: float = float(t_sigma_1q)
        self.t_sigma_2q: float = float(t_sigma_2q)
        self.excitation_current_base: float = float(excitation_current_base)
        self.excitation_voltage_base_ratio: float = float(
            excitation_voltage_base_ratio
        )
        self.saturation_curve_type: int = int(saturation_curve_type)
        self.saturation_axis_mode: int = int(saturation_axis_mode)
        self.saturation_smoothing_factor: float = float(
            saturation_smoothing_factor
        )
        self.speed_variation_mode: SynchronousMachineSpeedVariationMode = (
            speed_variation_mode
        )
        self.saturation_voltage_points: Tuple[float, ...] = tuple(
            saturation_voltage_points
        )
        self.saturation_excitation_points: Tuple[float, ...] = tuple(
            saturation_excitation_points
        )
        self.saturation_sg10: float = float(saturation_sg10)
        self.saturation_sg12: float = float(saturation_sg12)
        self.saturation_q_voltage_points: Tuple[float, ...] = tuple(
            saturation_q_voltage_points
        )
        self.saturation_q_excitation_points: Tuple[float, ...] = tuple(
            saturation_q_excitation_points
        )
        self.saturation_sg10q: float = float(saturation_sg10q)
        self.saturation_sg12q: float = float(saturation_sg12q)


def _build_raised_cosine_smoothed_positive_part(
        displacement: Expr,
        half_width: float,
) -> Expr:
    """Build the native compact positive-part transition at one corner.

    Native ordinate-perturbation sweeps identify a raised-cosine derivative
    inside the smoothing interval.  Integrating that derivative produces a
    compact transition which is exactly zero below the interval and exactly
    linear above it.  Its scale depends only on the exported smoothing factor
    and adjacent DGS abscissae; no machine-specific coefficient is fitted.

    :param displacement: Runtime abscissa relative to the curve corner.
    :param half_width: Positive half-width of the compact transition.
    :return: Smoothed equivalent of ``max(displacement, 0)``.
    """
    half_width_expr: Const = Const(half_width)
    negative_half_width_expr: Const = Const(-half_width)
    clamped_displacement: Expr = sym.max(
        negative_half_width_expr,
        sym.min(displacement, half_width_expr),
    )
    positive_linear_tail: Expr = sym.max(
        displacement - half_width_expr,
        Const(0.0),
    )
    smoothed_positive_part: Expr = (
        positive_linear_tail
        + Const(0.5) * (clamped_displacement + half_width_expr)
        - Const(half_width / math.pi)
        * sym.cos(
            Const(math.pi / (2.0 * half_width)) * clamped_displacement
        )
    )
    return smoothed_positive_part


def _build_tabular_saturation_coefficient(
        flux_magnitude: Expr,
        voltage_points: Tuple[float, ...],
        excitation_points: Tuple[float, ...],
        smoothing_factor: float = 0.0,
) -> Expr:
    """Build the native tabular ``SG(u)`` curve as a continuous expression.

    PowerFactory serialises ``TypSym.satv`` as magnetising flux and
    ``TypSym.satse`` as the normalised saturation ordinate ``SG(u)``.  The
    native curve interpolates the physical saturation increment
    ``delta_psi = psi * SG(psi)`` and divides the result by the instantaneous
    flux afterwards.  Interpolating ``SG`` directly changes the in-segment
    law even when the native smoothing factor is zero.

    Linear continuation outside the table preserves the end-segment law from
    the DGS without a case-specific clamp.

    :param flux_magnitude: Runtime magnetising-flux magnitude in p.u.
    :param voltage_points: Strictly increasing curve abscissae.
    :param excitation_points: Aligned native ``SG(u)`` ordinates.
    :param smoothing_factor: Native smoothing interval in percent.
    :return: Runtime saturation coefficient ``csat``.
    """
    zero: Const = Const(0.0)
    point_count: int = min(len(voltage_points), len(excitation_points))
    valid_curve: bool = point_count >= 2
    point_index: int
    if valid_curve:
        for point_index in range(1, point_count):
            if voltage_points[point_index] > voltage_points[point_index - 1]:
                pass
            else:
                valid_curve = False
        else:
            pass
    else:
        pass
    if valid_curve:
        # Reconstruct the physical saturation increment stored implicitly by
        # every normalised DGS point.  PowerFactory interpolates this quantity,
        # which preserves the electromagnetic meaning of the saturation table.
        saturation_increment_points: List[float] = list(
            voltage_points[point_index] * excitation_points[point_index]
            for point_index in range(point_count)
        )
        first_slope: float = (
            saturation_increment_points[1] - saturation_increment_points[0]
        ) / (
            voltage_points[1] - voltage_points[0]
        )
        saturation_increment_curve: Expr = (
            Const(saturation_increment_points[0])
            + Const(first_slope)
            * (flux_magnitude - Const(voltage_points[0]))
        )
        previous_slope: float = first_slope
        bounded_smoothing_factor: float = min(
            100.0,
            max(0.0, float(smoothing_factor)),
        )
        for point_index in range(1, point_count - 1):
            next_slope: float = (
                saturation_increment_points[point_index + 1]
                - saturation_increment_points[point_index]
            ) / (
                voltage_points[point_index + 1]
                - voltage_points[point_index]
            )
            corner_displacement: Expr = (
                flux_magnitude - Const(voltage_points[point_index])
            )
            if bounded_smoothing_factor > 0.0:
                # Convert the exported percentage to the compact transition
                # half-width on the smaller adjacent segment.  The native
                # interval spans the requested percentage in total, half on
                # either side of the slope corner.
                left_interval: float = (
                    voltage_points[point_index]
                    - voltage_points[point_index - 1]
                )
                right_interval: float = (
                    voltage_points[point_index + 1]
                    - voltage_points[point_index]
                )
                smoothing_half_width: float = (
                    0.5
                    * bounded_smoothing_factor
                    / 100.0
                    * min(left_interval, right_interval)
                )
                rounded_positive_part: Expr = (
                    _build_raised_cosine_smoothed_positive_part(
                        displacement=corner_displacement,
                        half_width=smoothing_half_width,
                    )
                )
            else:
                rounded_positive_part = sym.max(corner_displacement, zero)
            saturation_increment_curve = (
                saturation_increment_curve
                + Const(next_slope - previous_slope)
                * rounded_positive_part
            )
            previous_slope = next_slope
        else:
            pass
        # Convert the interpolated physical increment back to the normalised
        # coefficient used by the machine equations.  The flux expression is
        # already regularised at construction, while the epsilon protects this
        # helper when it is exercised independently by importing tests.
        epsilon: Const = Const(1.0e-12)
        coefficient: Expr = sym.max(
            saturation_increment_curve / (flux_magnitude + epsilon),
            zero,
        )
    else:
        coefficient = zero
    return coefficient


def _build_analytic_saturation_coefficient(
        flux_magnitude: Expr,
        curve_type: int,
        sg10: float,
        sg12: float,
) -> Expr:
    """Build a quadratic or exponential two-point saturation law.

    :param flux_magnitude: Runtime magnetising-flux magnitude in p.u.
    :param curve_type: Native curve selector, zero quadratic and one exponential.
    :param sg10: Saturation value at 1.0 p.u. flux.
    :param sg12: Saturation value at 1.2 p.u. flux.
    :return: Runtime saturation coefficient ``csat``.
    """
    zero: Const = Const(0.0)
    epsilon: Const = Const(1.0e-12)
    valid_points: bool = bool(sg10 > 0.0 and sg12 > 0.0)
    if valid_points and curve_type == 1:
        exponent: float = math.log(1.2 * sg12 / sg10) / math.log(1.2)
        coefficient: Expr = (
            Const(sg10) * flux_magnitude ** Const(exponent)
        )
    else:
        if valid_points:
            saturation_ratio_root: float = math.sqrt(1.2 * sg12 / sg10)
            denominator: float = 1.0 - saturation_ratio_root
            if abs(denominator) > 1.0e-12:
                intercept: float = (1.2 - saturation_ratio_root) / denominator
                gain: float = sg10 / ((1.0 - intercept) ** 2)
                coefficient = (
                    Const(gain)
                    * sym.max(flux_magnitude - Const(intercept), zero) ** Const(2.0)
                    / (flux_magnitude + epsilon)
                )
            else:
                coefficient = zero
        else:
            coefficient = zero
    return coefficient


def _build_saturation_coefficient(
        flux_magnitude: Expr,
        curve_type: int,
        voltage_points: Tuple[float, ...],
        excitation_points: Tuple[float, ...],
        smoothing_factor: float,
        sg10: float,
        sg12: float,
) -> Expr:
    """Select the native main-flux saturation curve representation.

    :param flux_magnitude: Runtime magnetising-flux magnitude in p.u.
    :param curve_type: Native curve selector.
    :param voltage_points: Optional tabular abscissae.
    :param excitation_points: Optional tabular ordinates.
    :param smoothing_factor: Native tabular smoothing interval in percent.
    :param sg10: Saturation at 1.0 p.u. flux.
    :param sg12: Saturation at 1.2 p.u. flux.
    :return: Runtime saturation coefficient ``csat``.
    """
    if curve_type < 0:
        coefficient: Expr = Const(0.0)
    elif curve_type == 2:
        coefficient = _build_tabular_saturation_coefficient(
            flux_magnitude=flux_magnitude,
            voltage_points=voltage_points,
            excitation_points=excitation_points,
            smoothing_factor=smoothing_factor,
        )
    else:
        coefficient = _build_analytic_saturation_coefficient(
            flux_magnitude=flux_magnitude,
            curve_type=curve_type,
            sg10=sg10,
            sg12=sg12,
        )
    return coefficient


def _calculate_two_loop_equivalent_axis(
        synchronous_reactance: float,
        transient_reactance: float,
        subtransient_reactance: float,
        leakage_reactance: float,
        coupling_reactance: float,
        transient_short_circuit_time: float,
        subtransient_short_circuit_time: float,
) -> Tuple[float, float, float, float] | None:
    """Apply PowerFactory equations 49--53 to one two-loop rotor axis.

    :param synchronous_reactance: Axis synchronous reactance in p.u.
    :param transient_reactance: Axis transient reactance in p.u.
    :param subtransient_reactance: Axis subtransient reactance in p.u.
    :param leakage_reactance: Stator leakage reactance in p.u.
    :param coupling_reactance: Coupling reactance between rotor windings in p.u.
    :param transient_short_circuit_time: Short-circuit transient constant in seconds.
    :param subtransient_short_circuit_time: Short-circuit subtransient constant in seconds.
    :return: Slow/fast leakage reactances and time constants, or ``None``.
    """
    epsilon: float = 1.0e-12
    magnetizing_reactance: float = synchronous_reactance - leakage_reactance
    x1_help: float = magnetizing_reactance + coupling_reactance
    x2_help: float = (
        x1_help
        - magnetizing_reactance * magnetizing_reactance / synchronous_reactance
    )
    subtransient_ratio: float = (
        subtransient_reactance / synchronous_reactance
    )
    x3_denominator: float = 1.0 - subtransient_ratio
    if abs(x3_denominator) > epsilon:
        x3_help: float = (
            x2_help - x1_help * subtransient_ratio
        ) / x3_denominator
    else:
        return None
    time_1: float = (
        synchronous_reactance / transient_reactance
        * transient_short_circuit_time
        + (
            1.0
            - synchronous_reactance / transient_reactance
            + synchronous_reactance / subtransient_reactance
        ) * subtransient_short_circuit_time
    )
    time_2: float = (
        transient_short_circuit_time + subtransient_short_circuit_time
    )
    x12_difference: float = x1_help - x2_help
    x32_difference: float = x3_help - x2_help
    if abs(x12_difference) > epsilon and abs(x32_difference) > epsilon:
        quadratic_a: float = (
            x2_help * time_1 - x1_help * time_2
        ) / x12_difference
        quadratic_b: float = (
            x3_help / x32_difference
            * transient_short_circuit_time
            * subtransient_short_circuit_time
        )
        discriminant: float = quadratic_a * quadratic_a / 4.0 - quadratic_b
    else:
        return None
    if discriminant >= 0.0:
        discriminant_root: float = math.sqrt(discriminant)
        slow_time: float = -quadratic_a / 2.0 + discriminant_root
        fast_time: float = -quadratic_a / 2.0 - discriminant_root
    else:
        return None
    time_difference: float = time_1 - time_2
    if abs(time_difference) > epsilon and abs(x3_help) > epsilon:
        slow_denominator: float = (
            time_difference / x12_difference + fast_time / x3_help
        )
        fast_denominator: float = (
            time_difference / x12_difference + slow_time / x3_help
        )
    else:
        return None
    if abs(slow_denominator) > epsilon and abs(fast_denominator) > epsilon:
        slow_reactance: float = (
            slow_time - fast_time
        ) / slow_denominator
        fast_reactance: float = (
            fast_time - slow_time
        ) / fast_denominator
    else:
        return None
    candidate_values: Tuple[float, ...] = (
        slow_reactance, fast_reactance, slow_time, fast_time,
    )
    candidate_value: float
    for candidate_value in candidate_values:
        if math.isfinite(candidate_value) and candidate_value > 0.0:
            pass
        else:
            return None
    else:
        pass
    return slow_reactance, fast_reactance, slow_time, fast_time


def _calculate_powerfactory_equivalent_circuit(
        machine_parameters: DgsElmSymMachineParameters,
) -> _PowerFactoryEquivalentCircuit | None:
    """Convert the stored DGS short-circuit contract to rotor parameters.

    The computation follows the public PowerFactory 2025 synchronous-machine
    technical reference exactly.  It is intentionally performed from the DGS
    values at RMS preparation time, so normal conversion never needs the
    licensed API and edits to the static machine remain effective.

    :param machine_parameters: Importer-local physical parameters built from
        the exact source ``ElmSym`` and ``TypSym`` rows.
    :return: Exact equivalent circuit, or ``None`` for invalid source data.
    """
    direct_transient_short_time: float = float(
        machine_parameters.rms_td_prime_short_circuit
    )
    if direct_transient_short_time > 0.0:
        pass
    else:
        direct_transient_short_time = (
            float(machine_parameters.Td0_prime) * float(machine_parameters.Xd_prime)
            / float(machine_parameters.Xd)
        )
    direct_subtransient_short_time: float = float(
        machine_parameters.rms_td_2prime_short_circuit
    )
    if direct_subtransient_short_time > 0.0:
        pass
    else:
        direct_subtransient_short_time = (
            float(machine_parameters.Td0_2prime) * float(machine_parameters.Xd_2prime)
            / float(machine_parameters.Xd_prime)
        )
    round_rotor: bool = float(machine_parameters.Tq0_prime) > 0.0
    quadrature_transient_short_time: float = float(
        machine_parameters.rms_tq_prime_short_circuit
    )
    if quadrature_transient_short_time > 0.0 or not round_rotor:
        pass
    else:
        quadrature_transient_short_time = (
            float(machine_parameters.Tq0_prime) * float(machine_parameters.Xq_prime)
            / float(machine_parameters.Xq)
        )
    quadrature_subtransient_short_time: float = float(
        machine_parameters.rms_tq_2prime_short_circuit
    )
    if quadrature_subtransient_short_time > 0.0:
        pass
    else:
        if round_rotor:
            quadrature_subtransient_numerator: float = float(machine_parameters.Xq_prime)
        else:
            quadrature_subtransient_numerator = float(machine_parameters.Xq)
        quadrature_subtransient_short_time = (
            float(machine_parameters.Tq0_2prime) * float(machine_parameters.Xq_2prime)
            / quadrature_subtransient_numerator
        )

    d_axis: Tuple[float, float, float, float] | None = (
        _calculate_two_loop_equivalent_axis(
            synchronous_reactance=float(machine_parameters.Xd),
            transient_reactance=float(machine_parameters.Xd_prime),
            subtransient_reactance=float(machine_parameters.Xd_2prime),
            leakage_reactance=float(machine_parameters.Xl),
            coupling_reactance=float(machine_parameters.rms_rotor_coupling_reactance_d),
            transient_short_circuit_time=direct_transient_short_time,
            subtransient_short_circuit_time=direct_subtransient_short_time,
        )
    )
    if d_axis is None:
        return None
    else:
        xfd: float = d_axis[0]
        x1d: float = d_axis[1]
        t_sigma_fd: float = d_axis[2]
        t_sigma_1d: float = d_axis[3]

    if round_rotor:
        q_axis: Tuple[float, float, float, float] | None = (
            _calculate_two_loop_equivalent_axis(
                synchronous_reactance=float(machine_parameters.Xq),
                transient_reactance=float(machine_parameters.Xq_prime),
                subtransient_reactance=float(machine_parameters.Xq_2prime),
                leakage_reactance=float(machine_parameters.Xl),
                coupling_reactance=float(
                    machine_parameters.rms_rotor_coupling_reactance_q
                ),
                transient_short_circuit_time=quadrature_transient_short_time,
                subtransient_short_circuit_time=(
                    quadrature_subtransient_short_time
                ),
            )
        )
        if q_axis is None:
            return None
        else:
            x1q: float = q_axis[0]
            x2q: float = q_axis[1]
            t_sigma_1q: float = q_axis[2]
            t_sigma_2q: float = q_axis[3]
    else:
        q_axis_denominator: float = float(machine_parameters.Xq) - float(machine_parameters.Xq_2prime)
        if q_axis_denominator > 1.0e-12:
            x1q = (
                (float(machine_parameters.Xq) - float(machine_parameters.Xl))
                * (float(machine_parameters.Xq_2prime) - float(machine_parameters.Xl))
                / q_axis_denominator
            )
        else:
            return None
        rotor_rate: float = (
            float(machine_parameters.Xq_2prime) / float(machine_parameters.Xq)
            * (float(machine_parameters.Xq) - float(machine_parameters.Xl) + x1q)
            / quadrature_subtransient_short_time
        )
        if x1q > 0.0 and rotor_rate > 0.0 and math.isfinite(rotor_rate):
            t_sigma_1q = x1q / rotor_rate
            x2q = 0.0
            t_sigma_2q = 0.0
        else:
            return None

    equivalent: _PowerFactoryEquivalentCircuit = _PowerFactoryEquivalentCircuit(
        xad=float(machine_parameters.Xd) - float(machine_parameters.Xl),
        xaq=float(machine_parameters.Xq) - float(machine_parameters.Xl),
        xrld=float(machine_parameters.rms_rotor_coupling_reactance_d),
        xrlq=float(machine_parameters.rms_rotor_coupling_reactance_q),
        xfd=xfd,
        x1d=x1d,
        x1q=x1q,
        x2q=x2q,
        t_sigma_fd=t_sigma_fd,
        t_sigma_1d=t_sigma_1d,
        t_sigma_1q=t_sigma_1q,
        t_sigma_2q=t_sigma_2q,
        excitation_current_base=max(
            1.0e-12,
            float(machine_parameters.rms_excitation_current_base),
        ),
        excitation_voltage_base_ratio=max(
            1.0e-12,
            float(machine_parameters.rms_excitation_voltage_base_ratio),
        ),
        saturation_curve_type=int(machine_parameters.rms_saturation_curve_type),
        saturation_axis_mode=int(machine_parameters.rms_saturation_axis_mode),
        saturation_smoothing_factor=float(
            machine_parameters.rms_saturation_smoothing_factor
        ),
        speed_variation_mode=machine_parameters.rms_speed_variation_mode,
        saturation_voltage_points=_float_tuple(
            values=machine_parameters.rms_saturation_voltage_points
        ),
        saturation_excitation_points=_float_tuple(
            values=machine_parameters.rms_saturation_excitation_points
        ),
        saturation_sg10=float(machine_parameters.rms_saturation_sg10),
        saturation_sg12=float(machine_parameters.rms_saturation_sg12),
        saturation_q_voltage_points=_float_tuple(
            values=machine_parameters.rms_saturation_q_voltage_points
        ),
        saturation_q_excitation_points=_float_tuple(
            values=machine_parameters.rms_saturation_q_excitation_points
        ),
        saturation_sg10q=float(machine_parameters.rms_saturation_sg10q),
        saturation_sg12q=float(machine_parameters.rms_saturation_sg12q),
    )
    return equivalent


def _calculate_unsaturated_rated_field_voltage(machine_parameters: DgsElmSymMachineParameters) -> float:
    """Calculate the native ``ve_rated`` signal from the rated machine point.

    PowerFactory's unsaturated ``ElmSym`` exposes the excitation voltage needed
    at rated terminal voltage, rated apparent power and rated power factor.  The
    DGS already carries the complete stator and reactance data, so this interface
    value is reproducible offline and must not default to one per unit.

    :param machine_parameters: Synchronous generator with a validated physical contract.
    :return: Positive rated field voltage in the machine excitation coordinate.
    """
    rated_power_factor: float = abs(float(machine_parameters.rated_power_factor))
    rated_reactive_power: float = math.sqrt(
        max(0.0, 1.0 - rated_power_factor * rated_power_factor)
    )
    stator_resistance: float = float(machine_parameters.Rs)
    quadrature_reactance: float = float(machine_parameters.Xq)
    direct_reactance: float = float(machine_parameters.Xd)

    # At rated terminal voltage the internal q-axis phasor behind Xq fixes the
    # rotor reference.  Resolve it in rectangular coordinates to preserve the
    # correct quadrant without an avoidable inverse-trigonometric round trip.
    internal_voltage_real: float = (
        1.0
        + stator_resistance * rated_power_factor
        + quadrature_reactance * rated_reactive_power
    )
    internal_voltage_imaginary: float = (
        quadrature_reactance * rated_power_factor
        - stator_resistance * rated_reactive_power
    )
    internal_voltage_magnitude: float = math.hypot(
        internal_voltage_real,
        internal_voltage_imaginary,
    )
    if internal_voltage_magnitude > 1.0e-12:
        rotor_sine: float = (
            internal_voltage_imaginary / internal_voltage_magnitude
        )
        rotor_cosine: float = internal_voltage_real / internal_voltage_magnitude
        direct_current: float = (
            rated_power_factor * rotor_sine
            + rated_reactive_power * rotor_cosine
        )
        quadrature_current: float = (
            rated_power_factor * rotor_cosine
            - rated_reactive_power * rotor_sine
        )
        air_gap_base_field_voltage: float = (
            rotor_cosine
            + direct_reactance * direct_current
            + stator_resistance * quadrature_current
        )
        excitation_base_scale: float = (
            max(1.0e-12, float(machine_parameters.rms_excitation_current_base))
            * max(
                1.0e-12,
                float(machine_parameters.rms_excitation_voltage_base_ratio),
            )
        )
        rated_field_voltage: float = (
            air_gap_base_field_voltage / excitation_base_scale
        )
    else:
        rated_field_voltage = float("nan")

    if math.isfinite(rated_field_voltage) and rated_field_voltage > 1.0e-12:
        return rated_field_voltage
    else:
        return 1.0


def _calculate_machine_active_base_factor(machine_parameters: DgsElmSymMachineParameters) -> float:
    """Return the non-singular active-power base used by machine dynamics.

    PowerFactory exports synchronous condensers with ``cosn`` close to zero so
    controllers can still recognize their nominal active-power capability.
    Rotor torque and electrical power remain expressed on the machine MVA base
    for that device class; dividing those equations by the near-zero marker
    would create a numerical singularity that is absent from the native model.

    :param machine_parameters: Configured synchronous-machine physical values.
    :return: Rated power factor for generators, or unity for a zero-P machine.
    """
    rated_power_factor: float = abs(float(machine_parameters.rated_power_factor))
    if rated_power_factor > 1.0e-6:
        return rated_power_factor
    else:
        return 1.0


def build_dgs_elmsym_block(
        machine_parameters: DgsElmSymMachineParameters,
        system_base_mva: float,
        frequency_hz: float,
        name: str = "ElmSym",
) -> Block:
    """Build the native flux-linkage synchronous machine without its controllers.

    :param machine_parameters: Validated physical source values on the machine base.
    :param system_base_mva: Network apparent-power base in MVA.
    :param frequency_hz: Nominal electrical frequency in Hz.
    :param name: Block display name.
    :return: Inputs (Vm, Va, pt, ve); outputs (Pg, Qg, speed, IFDIEEE,
        RPOWER, Vm, VTD, VTQ, ID, IQ, SG, cosn, Gm, VFDrated, Td0_prime).
        pt/RPOWER use the native rated active-power base, ve the excitation base.
    """
    _validate_native_parameters((system_base_mva, frequency_hz))
    if _machine_parameter_contract_is_valid(machine_parameters):
        pass
    else:
        raise ValueError("Invalid native synchronous-machine parameter contract")
    equivalent_circuit: _PowerFactoryEquivalentCircuit | None = (
        _calculate_powerfactory_equivalent_circuit(machine_parameters))
    if equivalent_circuit is not None:
        pass
    else:
        raise ValueError("Native machine rotor circuit cannot be reconstructed")
    round_rotor: bool = machine_parameters.Tq0_prime > 0.0
    pt: Var = Var("pt")
    ve: Var = Var("ve")
    wrapper_block: Block = _build_native_synchronous_machine_equations(
        equivalent_circuit, round_rotor, pt, ve, name)
    # Every physical parameter is final here; no later host configuration or
    # controller mutation is needed to make the equipment equations runnable.
    supplied_values: dict[str, float] = dict((
        ("fn", frequency_hz), ("omega_base", 2.0 * math.pi * frequency_hz),
        ("Sbase", system_base_mva), ("SG", machine_parameters.Snom),
        ("M", machine_parameters.rms_acceleration_time_constant),
        ("Rs", machine_parameters.Rs), ("Xd", machine_parameters.Xd), ("Xq", machine_parameters.Xq),
        ("Xd_prime", machine_parameters.Xd_prime), ("Xq_prime", machine_parameters.Xq_prime),
        ("Xd_2prime", machine_parameters.Xd_2prime), ("Xq_2prime", machine_parameters.Xq_2prime),
        ("Xl", machine_parameters.Xl), ("Td0_prime", machine_parameters.Td0_prime),
        ("Tq0_prime", machine_parameters.Tq0_prime), ("Td0_2prime", machine_parameters.Td0_2prime),
        ("Tq0_2prime", machine_parameters.Tq0_2prime), ("dpu", machine_parameters.rms_dpu),
        ("dkd", machine_parameters.rms_dkd), ("dpe", machine_parameters.rms_dpe),
        ("cosn", machine_parameters.rated_power_factor),
        ("machine_active_base_factor", _calculate_machine_active_base_factor(machine_parameters)),
        ("Gm", machine_parameters.rms_excitation_gain if machine_parameters.rms_excitation_gain > 1e-12 else 1.0),
        ("VFDrated", machine_parameters.rms_rated_field_voltage if machine_parameters.rms_rated_field_voltage > 1e-12
         else _calculate_unsaturated_rated_field_voltage(machine_parameters)),
    ))
    parameter_variable: Var
    for parameter_variable in wrapper_block.parameters:
        supplied_value: float | None = supplied_values.get(parameter_variable.name, None)
        if supplied_value is not None:
            wrapper_block.parameters[parameter_variable] = Const(supplied_value)
        else:
            pass
    return wrapper_block



def _build_native_synchronous_machine_equations(
        equivalent_circuit: _PowerFactoryEquivalentCircuit,
        round_rotor: bool,
        pt: Var,
        ve: Var,
        name: str,
) -> Block:
    """Build flux-linkage equations shared by standalone and legacy callers.

    :param equivalent_circuit: Resolved physical rotor-winding circuit.
    :param round_rotor: Whether a second quadrature damper winding exists.
    :param pt: Mechanical power port on the rated active-power base.
    :param ve: Excitation-voltage port on the native excitation base.
    :param name: Equipment display name.
    :return: Equipment-only block with the public ElmSym port contract.
    """
    # Network-facing variables use the ordinary Generator RMS contract.
    terminal_voltage: Var = Var(
        name="Vm",
        reference=VarPowerFlowReferenceType.Vm,
    )
    terminal_angle: Var = Var(
        name="Va",
        reference=VarPowerFlowReferenceType.Va,
    )
    active_power_system: Var = Var(
        name="Pg",
        reference=VarPowerFlowReferenceType.P,
    )
    reactive_power_system: Var = Var(
        name="Qg",
        reference=VarPowerFlowReferenceType.Q,
    )

    # PowerFactory's standard model integrates physical rotor flux linkages.
    # Retaining those same states is essential during faults: an equivalent
    # transient-emf model has the same steady state but a different trajectory.
    rotor_angle: Var = Var(name="phi")
    speed: Var = Var(name="speed")
    field_flux: Var = Var(name="psifd")
    direct_damper_flux: Var = Var(name="psi1d")
    first_quadrature_damper_flux: Var = Var(name="psi1q")
    # The second q-axis damper loop exists only in the round-rotor topology.
    # A salient machine must not expose a dummy state constrained to zero.
    if round_rotor:
        second_quadrature_damper_flux: Var = Var(name="psi2q")
    else:
        pass

    # Algebraic outputs define both the network injection and native frame IO.
    active_power_machine: Var = Var(name="P_machine")
    reactive_power_machine: Var = Var(name="Q_machine")
    direct_voltage: Var = Var(name="VTD")
    quadrature_voltage: Var = Var(name="VTQ")
    direct_current: Var = Var(name="ID")
    quadrature_current: Var = Var(name="IQ")
    electrical_torque: Var = Var(name="Te")
    excitation_current: Var = Var(name="IFDIEEE")
    electrical_power_active_base: Var = Var(name="RPOWER")
    reciprocal_field_current: Var = Var(name="ifd")
    direct_damper_current: Var = Var(name="i1d")
    first_quadrature_damper_current: Var = Var(name="i1q")
    if round_rotor:
        second_quadrature_damper_current: Var = Var(name="i2q")
    else:
        pass
    direct_subtransient_flux: Var = Var(name="psi_d_2prime")
    quadrature_subtransient_flux: Var = Var(name="psi_q_2prime")
    direct_stator_flux: Var = Var(name="psi_d")
    quadrature_stator_flux: Var = Var(name="psi_q")
    main_flux_saturation_coefficient: Var = Var(name="csat")
    direct_saturation_factor: Var = Var(name="satd")
    quadrature_saturation_factor: Var = Var(name="satq")
    saturated_direct_mutual_reactance: Var = Var(name="xad_sat")
    saturated_quadrature_mutual_reactance: Var = Var(name="xaq_sat")
    saturated_direct_subtransient_reactance: Var = Var(name="Xd_2prime_sat")
    saturated_quadrature_subtransient_reactance: Var = Var(name="Xq_2prime_sat")

    # Static DGS machine parameters remain editable and are assigned through
    # Generator GCProp dynamic references during RMS compilation.
    nominal_frequency: Var = Var(name="fn")
    angular_frequency: Var = Var(name="omega_base")
    acceleration_time: Var = Var(name="M")
    stator_resistance: Var = Var(name="Rs")
    xd: Var = Var(name="Xd")
    xq: Var = Var(name="Xq")
    xd_transient: Var = Var(name="Xd_prime")
    xq_transient: Var = Var(name="Xq_prime")
    xd_subtransient: Var = Var(name="Xd_2prime")
    xq_subtransient: Var = Var(name="Xq_2prime")
    leakage_reactance: Var = Var(name="Xl")
    td_transient: Var = Var(name="Td0_prime")
    tq_transient: Var = Var(name="Tq0_prime")
    td_subtransient: Var = Var(name="Td0_2prime")
    tq_subtransient: Var = Var(name="Tq0_2prime")
    damping_friction: Var = Var(name="dpu")
    damping_torque: Var = Var(name="dkd")
    damping_power: Var = Var(name="dpe")
    system_power_base: Var = Var(name="Sbase")
    machine_power_base: Var = Var(name="SG")
    rated_power_factor: Var = Var(name="cosn")
    machine_active_base_factor: Var = Var(name="machine_active_base_factor")
    excitation_gain: Var = Var(name="Gm")
    rated_field_voltage: Var = Var(name="VFDrated")
    direct_mutual_reactance: Var = Var(name="xadu")
    quadrature_mutual_reactance: Var = Var(name="xaqu")
    direct_rotor_coupling_reactance: Var = Var(name="xrld")
    quadrature_rotor_coupling_reactance: Var = Var(name="xrlq")
    field_leakage_reactance: Var = Var(name="xfd")
    direct_damper_leakage_reactance: Var = Var(name="x1d")
    first_quadrature_damper_leakage_reactance: Var = Var(name="x1q")
    field_rotor_time: Var = Var(name="T_sigma_fd")
    direct_damper_rotor_time: Var = Var(name="T_sigma_1d")
    first_quadrature_damper_rotor_time: Var = Var(name="T_sigma_1q")
    if round_rotor:
        second_quadrature_damper_leakage_reactance: Var = Var(name="x2q")
        second_quadrature_damper_rotor_time: Var = Var(name="T_sigma_2q")
    else:
        pass
    field_coupling_factor: Var = Var(name="kfd")
    direct_damper_coupling_factor: Var = Var(name="k1d")
    first_quadrature_coupling_factor: Var = Var(name="k1q")
    direct_rotor_determinant: Var = Var(name="xdet_d")
    if round_rotor:
        second_quadrature_coupling_factor: Var = Var(name="k2q")
        quadrature_rotor_determinant: Var = Var(name="xdet_q")
    else:
        pass

    epsilon: Const = Const(1.0e-12)
    excitation_current_base_expr: Const = Const(
        equivalent_circuit.excitation_current_base
    )
    excitation_voltage_base_ratio_expr: Const = Const(
        equivalent_circuit.excitation_voltage_base_ratio
    )
    initial_stator_speed: Expr = (
        angular_frequency
        / (Const(2.0 * math.pi) * nominal_frequency)
    )
    if (
            equivalent_circuit.speed_variation_mode
            is SynchronousMachineSpeedVariationMode.Considered
    ):
        subtransient_flux_speed: Expr = speed
        subtransient_current_speed: Expr = speed
    elif (
            equivalent_circuit.speed_variation_mode
            is SynchronousMachineSpeedVariationMode.PartiallyNeglected
    ):
        # Native partial mode retains instantaneous speed on the subtransient
        # flux terms while freezing only the x'' current terms at initial speed.
        subtransient_flux_speed = speed
        subtransient_current_speed = initial_stator_speed
    else:
        # Native neglected mode freezes both stator-voltage contributions at
        # initial synchronous speed, derived from exported frequency symbols.
        subtransient_flux_speed = initial_stator_speed
        subtransient_current_speed = initial_stator_speed
    # PowerFactory applies ``i_speedVar`` to the stator-voltage equations but
    # evaluates the RMS main-flux dependency curve in its nominal-frequency
    # coordinate.  Native trajectory inversion across a dynamic AVR stimulus
    # confirms that this coordinate remains the initialized synchronous speed
    # even when instantaneous speed is retained in the voltage equations.
    saturation_speed: Expr = initial_stator_speed
    # The curve then uses the instantaneous voltage and current operating point
    # together with the complete TypSym table retained in the DGS.
    direct_magnetising_flux: Expr = (
        (
            quadrature_voltage
            + stator_resistance * quadrature_current
        ) / (saturation_speed + epsilon)
        + leakage_reactance * direct_current
    )
    quadrature_magnetising_flux: Expr = (
        -(
            direct_voltage + stator_resistance * direct_current
        ) / (saturation_speed + epsilon)
        + leakage_reactance * quadrature_current
    )
    magnetising_flux_magnitude: Expr = sym.sqrt(
        direct_magnetising_flux * direct_magnetising_flux
        + quadrature_magnetising_flux * quadrature_magnetising_flux
        + epsilon
    )
    direct_flux_magnitude: Expr = sym.sqrt(
        direct_magnetising_flux * direct_magnetising_flux + epsilon
    )
    quadrature_flux_magnitude: Expr = sym.sqrt(
        quadrature_magnetising_flux * quadrature_magnetising_flux + epsilon
    )
    common_saturation_coefficient_expr: Expr = _build_saturation_coefficient(
        flux_magnitude=magnetising_flux_magnitude,
        curve_type=equivalent_circuit.saturation_curve_type,
        voltage_points=equivalent_circuit.saturation_voltage_points,
        excitation_points=equivalent_circuit.saturation_excitation_points,
        smoothing_factor=equivalent_circuit.saturation_smoothing_factor,
        sg10=equivalent_circuit.saturation_sg10,
        sg12=equivalent_circuit.saturation_sg12,
    )
    direct_component_saturation_coefficient: Expr = (
        _build_saturation_coefficient(
            flux_magnitude=direct_flux_magnitude,
            curve_type=equivalent_circuit.saturation_curve_type,
            voltage_points=equivalent_circuit.saturation_voltage_points,
            excitation_points=equivalent_circuit.saturation_excitation_points,
            smoothing_factor=equivalent_circuit.saturation_smoothing_factor,
            sg10=equivalent_circuit.saturation_sg10,
            sg12=equivalent_circuit.saturation_sg12,
        )
    )
    quadrature_component_saturation_coefficient: Expr = (
        _build_saturation_coefficient(
            flux_magnitude=quadrature_flux_magnitude,
            curve_type=equivalent_circuit.saturation_curve_type,
            voltage_points=equivalent_circuit.saturation_q_voltage_points,
            excitation_points=equivalent_circuit.saturation_q_excitation_points,
            smoothing_factor=equivalent_circuit.saturation_smoothing_factor,
            sg10=equivalent_circuit.saturation_sg10q,
            sg12=equivalent_circuit.saturation_sg12q,
        )
    )
    saturation_axis_mode: int = equivalent_circuit.saturation_axis_mode
    if saturation_axis_mode == 4:
        direct_saturation_coefficient_expr: Expr = common_saturation_coefficient_expr
        quadrature_saturation_coefficient_expr: Expr = common_saturation_coefficient_expr
    elif saturation_axis_mode == 1:
        direct_saturation_coefficient_expr = common_saturation_coefficient_expr
        quadrature_saturation_coefficient_expr = Const(0.0)
    elif saturation_axis_mode == 2:
        direct_saturation_coefficient_expr = direct_component_saturation_coefficient
        quadrature_saturation_coefficient_expr = quadrature_component_saturation_coefficient
    elif saturation_axis_mode == 3:
        direct_saturation_coefficient_expr = direct_component_saturation_coefficient
        quadrature_saturation_coefficient_expr = Const(0.0)
    else:
        # Native mode zero uses one magnitude curve and scales q-axis
        # saturation by the unsaturated mutual-reactance ratio (equation 129).
        direct_saturation_coefficient_expr = common_saturation_coefficient_expr
        quadrature_saturation_coefficient_expr = (
            quadrature_mutual_reactance
            / (direct_mutual_reactance + epsilon)
            * common_saturation_coefficient_expr
        )
    mechanical_torque: Expr = (
        pt / (speed + epsilon)
        - damping_friction * speed
    )
    damping_torque_expr: Expr = damping_torque * (speed - Const(1.0))
    damping_power_expr: Expr = (
        damping_power
        * (speed - Const(1.0))
        / (speed + epsilon)
    )
    state_vars: List[Var] = list([
        rotor_angle,
        speed,
        field_flux,
        direct_damper_flux,
        first_quadrature_damper_flux,
    ])
    state_eqs: List[Expr] = list([
        angular_frequency * (speed - Const(1.0)),
        (
            mechanical_torque
            - electrical_torque
            - damping_torque_expr
            - damping_power_expr
        ) / acceleration_time,
        (
            field_leakage_reactance / field_rotor_time
            * (
                ve
                * excitation_current_base_expr
                * excitation_voltage_base_ratio_expr
                / direct_mutual_reactance
                - reciprocal_field_current
            )
        ),
        -direct_damper_leakage_reactance
        / direct_damper_rotor_time
        * direct_damper_current,
        -first_quadrature_damper_leakage_reactance
        / first_quadrature_damper_rotor_time
        * first_quadrature_damper_current,
    ])
    if round_rotor:
        state_vars.append(second_quadrature_damper_flux)
        state_eqs.append(
            -second_quadrature_damper_leakage_reactance
            / second_quadrature_damper_rotor_time
            * second_quadrature_damper_current
        )
    else:
        pass

    field_loop_reactance: Expr = (
        saturated_direct_mutual_reactance
        + direct_rotor_coupling_reactance
        + field_leakage_reactance
    )
    direct_damper_loop_reactance: Expr = (
        saturated_direct_mutual_reactance
        + direct_rotor_coupling_reactance
        + direct_damper_leakage_reactance
    )
    first_quadrature_loop_reactance: Expr = (
        saturated_quadrature_mutual_reactance
        + quadrature_rotor_coupling_reactance
        + first_quadrature_damper_leakage_reactance
    )
    if round_rotor:
        second_quadrature_loop_reactance: Expr = (
            saturated_quadrature_mutual_reactance
            + quadrature_rotor_coupling_reactance
            + second_quadrature_damper_leakage_reactance
        )
    else:
        pass

    algebraic_eqs: List[Expr] = list([
        main_flux_saturation_coefficient
        - common_saturation_coefficient_expr,
        direct_saturation_factor - (
            Const(1.0) / (Const(1.0) + direct_saturation_coefficient_expr)
        ),
        quadrature_saturation_factor - (
            Const(1.0) / (Const(1.0) + quadrature_saturation_coefficient_expr)
        ),
        saturated_direct_mutual_reactance - (
            direct_saturation_factor * direct_mutual_reactance
        ),
        saturated_quadrature_mutual_reactance - (
            quadrature_saturation_factor * quadrature_mutual_reactance
        ),
        direct_rotor_determinant - (
            (
                saturated_direct_mutual_reactance
                + direct_rotor_coupling_reactance
            ) * (
                direct_damper_leakage_reactance
                + field_leakage_reactance
            )
            + field_leakage_reactance
            * direct_damper_leakage_reactance
        ),
        field_coupling_factor - (
            saturated_direct_mutual_reactance
            * direct_damper_leakage_reactance
            / direct_rotor_determinant
        ),
        direct_damper_coupling_factor - (
            saturated_direct_mutual_reactance
            * field_leakage_reactance
            / direct_rotor_determinant
        ),
        saturated_direct_subtransient_reactance - (
            saturated_direct_mutual_reactance
            + leakage_reactance
            - (field_coupling_factor + direct_damper_coupling_factor)
            * saturated_direct_mutual_reactance
        ),
        direct_voltage - (-terminal_voltage * sym.sin(terminal_angle - rotor_angle)),
        quadrature_voltage - terminal_voltage * sym.cos(terminal_angle - rotor_angle),
        active_power_machine - (
            direct_voltage * direct_current
            + quadrature_voltage * quadrature_current
        ),
        reactive_power_machine - (
            quadrature_voltage * direct_current
            - direct_voltage * quadrature_current
        ),
        direct_voltage - (
            -subtransient_flux_speed * quadrature_subtransient_flux
            + subtransient_current_speed
            * saturated_quadrature_subtransient_reactance
            * quadrature_current
            - stator_resistance * direct_current
        ),
        quadrature_voltage - (
            subtransient_flux_speed * direct_subtransient_flux
            - subtransient_current_speed
            * saturated_direct_subtransient_reactance
            * direct_current
            - stator_resistance * quadrature_current
        ),
        active_power_system - (
            active_power_machine * machine_power_base / system_power_base
        ),
        reactive_power_system - (
            reactive_power_machine * machine_power_base / system_power_base
        ),
        electrical_torque - (
            (
                quadrature_current * direct_stator_flux
                - direct_current * quadrature_stator_flux
            ) / machine_active_base_factor
        ),
        excitation_current - (
            direct_mutual_reactance
            * reciprocal_field_current
            / excitation_current_base_expr
        ),
        electrical_power_active_base - (
            active_power_machine / machine_active_base_factor
        ),
        reciprocal_field_current - (
            field_coupling_factor * direct_current
            + (
                direct_damper_loop_reactance * field_flux
                - (
                    saturated_direct_mutual_reactance
                    + direct_rotor_coupling_reactance
                ) * direct_damper_flux
            ) / direct_rotor_determinant
        ),
        direct_damper_current - (
            direct_damper_coupling_factor * direct_current
            + (
                field_loop_reactance * direct_damper_flux
                - (
                    saturated_direct_mutual_reactance
                    + direct_rotor_coupling_reactance
                ) * field_flux
            ) / direct_rotor_determinant
        ),
        direct_subtransient_flux - (
            field_coupling_factor * field_flux
            + direct_damper_coupling_factor * direct_damper_flux
        ),
        direct_stator_flux - (
            direct_subtransient_flux
            - saturated_direct_subtransient_reactance * direct_current
        ),
        quadrature_stator_flux - (
            quadrature_subtransient_flux
            - saturated_quadrature_subtransient_reactance * quadrature_current
        ),
    ])
    if round_rotor:
        algebraic_eqs.append(
            quadrature_rotor_determinant - (
                (
                    saturated_quadrature_mutual_reactance
                    + quadrature_rotor_coupling_reactance
                ) * (
                    second_quadrature_damper_leakage_reactance
                    + first_quadrature_damper_leakage_reactance
                )
                + second_quadrature_damper_leakage_reactance
                * first_quadrature_damper_leakage_reactance
            )
        )
        algebraic_eqs.append(
            first_quadrature_coupling_factor - (
                saturated_quadrature_mutual_reactance
                * second_quadrature_damper_leakage_reactance
                / quadrature_rotor_determinant
            )
        )
        algebraic_eqs.append(
            second_quadrature_coupling_factor - (
                saturated_quadrature_mutual_reactance
                * first_quadrature_damper_leakage_reactance
                / quadrature_rotor_determinant
            )
        )
        algebraic_eqs.append(
            saturated_quadrature_subtransient_reactance - (
                saturated_quadrature_mutual_reactance
                + leakage_reactance
                - (
                    first_quadrature_coupling_factor
                    + second_quadrature_coupling_factor
                ) * saturated_quadrature_mutual_reactance
            )
        )
        algebraic_eqs.append(
            first_quadrature_damper_current - (
                first_quadrature_coupling_factor * quadrature_current
                + (
                    second_quadrature_loop_reactance
                    * first_quadrature_damper_flux
                    - (
                        saturated_quadrature_mutual_reactance
                        + quadrature_rotor_coupling_reactance
                    ) * second_quadrature_damper_flux
                ) / quadrature_rotor_determinant
            )
        )
        algebraic_eqs.append(
            second_quadrature_damper_current - (
                second_quadrature_coupling_factor * quadrature_current
                + (
                    first_quadrature_loop_reactance
                    * second_quadrature_damper_flux
                    - (
                        saturated_quadrature_mutual_reactance
                        + quadrature_rotor_coupling_reactance
                    ) * first_quadrature_damper_flux
                ) / quadrature_rotor_determinant
            )
        )
        algebraic_eqs.append(
            quadrature_subtransient_flux - (
                first_quadrature_coupling_factor
                * first_quadrature_damper_flux
                + second_quadrature_coupling_factor
                * second_quadrature_damper_flux
            )
        )
    else:
        algebraic_eqs.append(
            first_quadrature_coupling_factor - (
                saturated_quadrature_mutual_reactance
                / first_quadrature_loop_reactance
            )
        )
        algebraic_eqs.append(
            saturated_quadrature_subtransient_reactance - (
                saturated_quadrature_mutual_reactance
                + leakage_reactance
                - first_quadrature_coupling_factor
                * saturated_quadrature_mutual_reactance
            )
        )
        algebraic_eqs.append(
            first_quadrature_damper_current - (
                first_quadrature_coupling_factor * quadrature_current
                + first_quadrature_damper_flux
                / first_quadrature_loop_reactance
            )
        )
        algebraic_eqs.append(
            quadrature_subtransient_flux - (
                first_quadrature_coupling_factor
                * first_quadrature_damper_flux
            )
        )
    algebraic_vars: List[Var] = list([
        active_power_system,
        reactive_power_system,
        active_power_machine,
        reactive_power_machine,
        direct_voltage,
        quadrature_voltage,
        direct_current,
        quadrature_current,
        electrical_torque,
        excitation_current,
        electrical_power_active_base,
        reciprocal_field_current,
        direct_damper_current,
        first_quadrature_damper_current,
        direct_subtransient_flux,
        quadrature_subtransient_flux,
        direct_stator_flux,
        quadrature_stator_flux,
        main_flux_saturation_coefficient,
        direct_saturation_factor,
        quadrature_saturation_factor,
        saturated_direct_mutual_reactance,
        saturated_quadrature_mutual_reactance,
        saturated_direct_subtransient_reactance,
        saturated_quadrature_subtransient_reactance,
        field_coupling_factor,
        direct_damper_coupling_factor,
        first_quadrature_coupling_factor,
        direct_rotor_determinant,
    ])
    if round_rotor:
        algebraic_vars.append(second_quadrature_coupling_factor)
        algebraic_vars.append(quadrature_rotor_determinant)
        algebraic_vars.append(second_quadrature_damper_current)
    else:
        pass

    machine_active_power_initial: Expr = (
        active_power_system * system_power_base / machine_power_base
    )
    machine_reactive_power_initial: Expr = (
        reactive_power_system * system_power_base / machine_power_base
    )
    complex_power_initial: Expr = (
        machine_active_power_initial
        + Const(1j) * machine_reactive_power_initial
    )
    terminal_phasor_initial: Expr = (
        terminal_voltage * sym.exp(Const(1j) * terminal_angle)
    )
    stator_current_initial: Expr = sym.conj(complex_power_initial) / (
        sym.conj(terminal_phasor_initial) + epsilon
    )
    internal_voltage_imaginary: Expr = (
        terminal_voltage * sym.sin(terminal_angle)
        + sym.imag(stator_current_initial) * stator_resistance
        + sym.real(stator_current_initial)
        * (leakage_reactance + saturated_quadrature_mutual_reactance)
    )
    internal_voltage_real: Expr = (
        terminal_voltage * sym.cos(terminal_angle)
        + sym.real(stator_current_initial) * stator_resistance
        - sym.imag(stator_current_initial)
        * (leakage_reactance + saturated_quadrature_mutual_reactance)
    )
    initial_eqs: Dict[Var, Expr] = dict()
    # Derive initial per-unit rotor speed from the physical frequency base.
    # This anchors every RMS island without a fitted state value or a dummy
    # constant variable; both frequency quantities remain DGS-bound symbols.
    initial_eqs[speed] = (
        angular_frequency
        / (Const(2.0 * math.pi) * nominal_frequency)
    )
    # The network phase of an island can legitimately lie in any quadrant.
    # ``atan(y/x)`` loses that quadrant and can invert Eq/EFD by pi even when
    # the static terminal solution is exact, so retain the full phasor angle.
    initial_eqs[rotor_angle] = sym.atan2(
        internal_voltage_imaginary,
        internal_voltage_real,
    )
    initial_eqs[direct_voltage] = (
        -terminal_voltage * sym.sin(terminal_angle - rotor_angle)
    )
    initial_eqs[quadrature_voltage] = (
        terminal_voltage * sym.cos(terminal_angle - rotor_angle)
    )
    initial_eqs[active_power_machine] = machine_active_power_initial
    initial_eqs[reactive_power_machine] = machine_reactive_power_initial
    initial_eqs[direct_current] = (
        active_power_machine * direct_voltage
        + reactive_power_machine * quadrature_voltage
    ) / (
        direct_voltage * direct_voltage
        + quadrature_voltage * quadrature_voltage
        + epsilon
    )
    initial_eqs[quadrature_current] = (
        active_power_machine * quadrature_voltage
        - reactive_power_machine * direct_voltage
    ) / (
        direct_voltage * direct_voltage
        + quadrature_voltage * quadrature_voltage
        + epsilon
    )
    initial_eqs[main_flux_saturation_coefficient] = (
        common_saturation_coefficient_expr
    )
    initial_eqs[direct_saturation_factor] = (
        Const(1.0) / (Const(1.0) + direct_saturation_coefficient_expr)
    )
    initial_eqs[quadrature_saturation_factor] = (
        Const(1.0) / (Const(1.0) + quadrature_saturation_coefficient_expr)
    )
    initial_eqs[saturated_direct_mutual_reactance] = (
        direct_saturation_factor * direct_mutual_reactance
    )
    initial_eqs[saturated_quadrature_mutual_reactance] = (
        quadrature_saturation_factor * quadrature_mutual_reactance
    )
    initial_eqs[direct_rotor_determinant] = (
        (
            saturated_direct_mutual_reactance
            + direct_rotor_coupling_reactance
        ) * (
            direct_damper_leakage_reactance + field_leakage_reactance
        )
        + field_leakage_reactance * direct_damper_leakage_reactance
    )
    initial_eqs[field_coupling_factor] = (
        saturated_direct_mutual_reactance
        * direct_damper_leakage_reactance
        / direct_rotor_determinant
    )
    initial_eqs[direct_damper_coupling_factor] = (
        saturated_direct_mutual_reactance
        * field_leakage_reactance
        / direct_rotor_determinant
    )
    initial_eqs[saturated_direct_subtransient_reactance] = (
        saturated_direct_mutual_reactance
        + leakage_reactance
        - (field_coupling_factor + direct_damper_coupling_factor)
        * saturated_direct_mutual_reactance
    )
    if round_rotor:
        initial_eqs[quadrature_rotor_determinant] = (
            (
                saturated_quadrature_mutual_reactance
                + quadrature_rotor_coupling_reactance
            ) * (
                second_quadrature_damper_leakage_reactance
                + first_quadrature_damper_leakage_reactance
            )
            + second_quadrature_damper_leakage_reactance
            * first_quadrature_damper_leakage_reactance
        )
        initial_eqs[first_quadrature_coupling_factor] = (
            saturated_quadrature_mutual_reactance
            * second_quadrature_damper_leakage_reactance
            / quadrature_rotor_determinant
        )
        initial_eqs[second_quadrature_coupling_factor] = (
            saturated_quadrature_mutual_reactance
            * first_quadrature_damper_leakage_reactance
            / quadrature_rotor_determinant
        )
    else:
        initial_eqs[first_quadrature_coupling_factor] = (
            saturated_quadrature_mutual_reactance
            / first_quadrature_loop_reactance
        )
    if round_rotor:
        initial_eqs[saturated_quadrature_subtransient_reactance] = (
            saturated_quadrature_mutual_reactance
            + leakage_reactance
            - (
                first_quadrature_coupling_factor
                + second_quadrature_coupling_factor
            ) * saturated_quadrature_mutual_reactance
        )
    else:
        initial_eqs[saturated_quadrature_subtransient_reactance] = (
            saturated_quadrature_mutual_reactance
            + leakage_reactance
            - first_quadrature_coupling_factor
            * saturated_quadrature_mutual_reactance
        )
    initial_eqs[direct_subtransient_flux] = (
        (
            quadrature_voltage
            + stator_resistance * quadrature_current
        ) / (initial_stator_speed + epsilon)
        + saturated_direct_subtransient_reactance * direct_current
    )
    initial_eqs[quadrature_subtransient_flux] = (
        -(
            direct_voltage
            + stator_resistance * direct_current
        ) / (initial_stator_speed + epsilon)
        + saturated_quadrature_subtransient_reactance * quadrature_current
    )
    initial_eqs[direct_stator_flux] = (
        direct_subtransient_flux
        - saturated_direct_subtransient_reactance * direct_current
    )
    initial_eqs[quadrature_stator_flux] = (
        quadrature_subtransient_flux
        - saturated_quadrature_subtransient_reactance * quadrature_current
    )
    initial_eqs[reciprocal_field_current] = (
        direct_stator_flux
        + (leakage_reactance + saturated_direct_mutual_reactance)
        * direct_current
    ) / saturated_direct_mutual_reactance
    initial_eqs[field_flux] = (
        -saturated_direct_mutual_reactance * direct_current
        + field_loop_reactance * reciprocal_field_current
    )
    initial_eqs[direct_damper_flux] = (
        -saturated_direct_mutual_reactance * direct_current
        + (
            saturated_direct_mutual_reactance
            + direct_rotor_coupling_reactance
        ) * reciprocal_field_current
    )
    initial_eqs[first_quadrature_damper_flux] = (
        -saturated_quadrature_mutual_reactance * quadrature_current
    )
    if round_rotor:
        initial_eqs[second_quadrature_damper_flux] = (
            -saturated_quadrature_mutual_reactance * quadrature_current
        )
    else:
        pass
    # Damper currents are consequences of the solved flux linkages.  Reusing
    # the physical rotor-circuit equations keeps initialization symbolic and
    # lets their zero steady-state value emerge without a numeric seed.
    initial_eqs[direct_damper_current] = (
        direct_damper_coupling_factor * direct_current
        + (
            field_loop_reactance * direct_damper_flux
            - (
                saturated_direct_mutual_reactance
                + direct_rotor_coupling_reactance
            ) * field_flux
        ) / direct_rotor_determinant
    )
    if round_rotor:
        initial_eqs[first_quadrature_damper_current] = (
            first_quadrature_coupling_factor * quadrature_current
            + (
                second_quadrature_loop_reactance
                * first_quadrature_damper_flux
                - (
                    saturated_quadrature_mutual_reactance
                    + quadrature_rotor_coupling_reactance
                ) * second_quadrature_damper_flux
            ) / quadrature_rotor_determinant
        )
        initial_eqs[second_quadrature_damper_current] = (
            second_quadrature_coupling_factor * quadrature_current
            + (
                first_quadrature_loop_reactance
                * second_quadrature_damper_flux
                - (
                    saturated_quadrature_mutual_reactance
                    + quadrature_rotor_coupling_reactance
                ) * first_quadrature_damper_flux
            ) / quadrature_rotor_determinant
        )
    else:
        initial_eqs[first_quadrature_damper_current] = (
            first_quadrature_coupling_factor * quadrature_current
            + first_quadrature_damper_flux
            / first_quadrature_loop_reactance
        )
    initial_eqs[electrical_torque] = (
        (
            quadrature_current * direct_stator_flux
            - direct_current * quadrature_stator_flux
        ) / machine_active_base_factor
    )
    initial_eqs[excitation_current] = (
        direct_mutual_reactance
        * reciprocal_field_current
        / excitation_current_base_expr
    )
    initial_eqs[electrical_power_active_base] = (
        active_power_machine / machine_active_base_factor
    )
    # PowerFactory initializes controller outputs from the solved machine
    # operating point before evaluating the first state derivative.  The DGS
    # controller can contain a local fallback for these shared cables, but the
    # physical ElmSym shell owns their unique equilibrium values.
    initial_eqs[ve] = (
        excitation_current / excitation_voltage_base_ratio_expr
    )
    initial_eqs[pt] = (
        (speed + epsilon)
        * (
            electrical_torque
            + damping_friction * speed
            + damping_torque_expr
            + damping_power_expr
        )
    )

    # The coupling reactances come from the importer-local equivalent circuit.
    # Their numeric values are frozen only for this compiled template instance.
    direct_coupling_value: float = equivalent_circuit.xrld
    quadrature_coupling_value: float = equivalent_circuit.xrlq

    parameters: Dict[Var, Expr] = dict()
    parameters[nominal_frequency] = Const(50.0)
    parameters[angular_frequency] = Const(2.0 * math.pi * 50.0)
    parameters[acceleration_time] = Const(1.0)
    parameters[stator_resistance] = Const(0.0)
    parameters[xd] = Const(1.0)
    parameters[xq] = Const(1.0)
    parameters[xd_transient] = Const(0.3)
    parameters[xq_transient] = Const(0.3)
    parameters[xd_subtransient] = Const(0.2)
    parameters[xq_subtransient] = Const(0.2)
    parameters[leakage_reactance] = Const(0.1)
    parameters[td_transient] = Const(1.0)
    parameters[tq_transient] = Const(1.0)
    parameters[td_subtransient] = Const(0.1)
    parameters[tq_subtransient] = Const(0.1)
    parameters[damping_friction] = Const(0.0)
    parameters[damping_torque] = Const(0.0)
    parameters[damping_power] = Const(0.0)
    parameters[system_power_base] = Const(100.0)
    parameters[machine_power_base] = Const(100.0)
    parameters[rated_power_factor] = Const(1.0)
    parameters[machine_active_base_factor] = Const(1.0)
    # Air-gap-line excitation base is mathematically unity. Non-default base
    # modes require explicit exported metadata and are rejected by later model
    # extensions rather than inferred from a project name.
    parameters[excitation_gain] = Const(1.0)
    parameters[rated_field_voltage] = Const(1.0)
    parameters[direct_mutual_reactance] = Const(equivalent_circuit.xad)
    parameters[quadrature_mutual_reactance] = Const(equivalent_circuit.xaq)
    parameters[direct_rotor_coupling_reactance] = Const(direct_coupling_value)
    parameters[quadrature_rotor_coupling_reactance] = Const(
        quadrature_coupling_value
    )
    parameters[field_leakage_reactance] = Const(equivalent_circuit.xfd)
    parameters[direct_damper_leakage_reactance] = Const(
        equivalent_circuit.x1d
    )
    parameters[first_quadrature_damper_leakage_reactance] = Const(
        equivalent_circuit.x1q
    )
    parameters[field_rotor_time] = Const(equivalent_circuit.t_sigma_fd)
    parameters[direct_damper_rotor_time] = Const(
        equivalent_circuit.t_sigma_1d
    )
    parameters[first_quadrature_damper_rotor_time] = Const(
        equivalent_circuit.t_sigma_1q
    )
    if round_rotor:
        parameters[second_quadrature_damper_leakage_reactance] = Const(
            equivalent_circuit.x2q
        )
        parameters[second_quadrature_damper_rotor_time] = Const(
            equivalent_circuit.t_sigma_2q
        )
    else:
        pass
    api_mapping: Dict[ParamPowerFlowReferenceType, Var] = dict()
    api_mapping[ParamPowerFlowReferenceType.freq] = nominal_frequency
    api_mapping[ParamPowerFlowReferenceType.omega_base] = angular_frequency
    api_mapping[ParamPowerFlowReferenceType.Sbase] = system_power_base
    api_mapping[ParamPowerFlowReferenceType.generator_snom_mva] = machine_power_base

    wrapper_block: Block = Block(
        name=name,
        in_vars=list((terminal_voltage, terminal_angle, pt, ve)),
        out_vars=list((active_power_system, reactive_power_system, speed,
                       excitation_current, electrical_power_active_base,
                       terminal_voltage, direct_voltage, quadrature_voltage,
                       direct_current, quadrature_current, machine_power_base,
                       rated_power_factor, excitation_gain, rated_field_voltage,
                       td_transient)),
        state_vars=state_vars,
        state_eqs=state_eqs,
        algebraic_vars=algebraic_vars,
        algebraic_eqs=algebraic_eqs,
        init_eqs=initial_eqs,
        post_init_seed_eqs=dict(initial_eqs),
        parameters=parameters,
        external_mapping=dict([
            (VarPowerFlowReferenceType.P, active_power_system),
            (VarPowerFlowReferenceType.Q, reactive_power_system),
            (VarPowerFlowReferenceType.Vm, terminal_voltage),
            (VarPowerFlowReferenceType.Va, terminal_angle),
        ]),
        api_obj_mapping=api_mapping,
    )
    return wrapper_block
