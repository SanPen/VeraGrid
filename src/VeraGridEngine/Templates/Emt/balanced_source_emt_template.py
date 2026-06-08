# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Expr, Var
from VeraGridEngine.Utils.Symbolic import symbolic as sym
from VeraGridEngine.enumerations import DeviceType, VarPowerFlowReferenceType


def _phase_angle_expression(theta_var: Var, phase_a_deg_var: Var, phase_shift_deg: float) -> Expr:
    """
    Return one balanced three-phase angle expression.

    :param theta_var: Common electrical angle state.
    :param phase_a_deg_var: Phase-A angle offset in degrees.
    :param phase_shift_deg: Relative balanced phase shift in degrees.
    :return: Angle expression in rad.
    """
    deg_to_rad: Expr = sym.Const(3.141592653589793) / sym.Const(180.0)
    return theta_var + deg_to_rad * (phase_a_deg_var + sym.Const(float(phase_shift_deg)))


def _build_external_mapping(v_a: Var, v_b: Var, v_c: Var, i_a: Var, i_b: Var, i_c: Var) -> dict[VarPowerFlowReferenceType, Var | None]:
    """
    Build one ABC external mapping for a balanced source.

    :param v_a: Phase-A bus voltage.
    :param v_b: Phase-B bus voltage.
    :param v_c: Phase-C bus voltage.
    :param i_a: Phase-A injected current.
    :param i_b: Phase-B injected current.
    :param i_c: Phase-C injected current.
    :return: External mapping dictionary.
    """
    return {
        VarPowerFlowReferenceType.v_N: None,
        VarPowerFlowReferenceType.v_A: v_a,
        VarPowerFlowReferenceType.v_B: v_b,
        VarPowerFlowReferenceType.v_C: v_c,
        VarPowerFlowReferenceType.i_N: None,
        VarPowerFlowReferenceType.i_A: i_a,
        VarPowerFlowReferenceType.i_B: i_b,
        VarPowerFlowReferenceType.i_C: i_c,
    }


def get_balanced_3ph_current_source_emt_template(vf: VarFactory,
                                                 amplitude_value: float = 1.0,
                                                 frequency_hz: float = 50.0,
                                                 phase_a_deg: float = 0.0,
                                                 offset_value: float = 0.0,
                                                 name: str = "balanced_3ph_current_source_emt") -> EmtModelTemplate:
    """
    Build one balanced three-phase sinusoidal EMT current source.

    :param vf: EMT variable factory.
    :param amplitude_value: Common phase amplitude.
    :param frequency_hz: Common sinusoidal frequency.
    :param phase_a_deg: Phase-A angle offset in degrees.
    :param offset_value: Common phase offset.
    :param name: Symbolic block name.
    :return: Configured EMT template.
    """
    templ = EmtModelTemplate()
    templ.tpe = DeviceType.GeneratorDevice
    templ.name = name
    templ.block.name = name

    v_a: Var = vf.add_var(name=f"v_A_{name}", reference=VarPowerFlowReferenceType.v_A)
    v_b: Var = vf.add_var(name=f"v_B_{name}", reference=VarPowerFlowReferenceType.v_B)
    v_c: Var = vf.add_var(name=f"v_C_{name}", reference=VarPowerFlowReferenceType.v_C)
    i_a: Var = vf.add_var(name=f"i_A_{name}", reference=VarPowerFlowReferenceType.i_A)
    i_b: Var = vf.add_var(name=f"i_B_{name}", reference=VarPowerFlowReferenceType.i_B)
    i_c: Var = vf.add_var(name=f"i_C_{name}", reference=VarPowerFlowReferenceType.i_C)
    theta_var: Var = vf.add_var(name=f"theta_src_{name}")
    d_theta_var: Var = vf.add_diff_var(name=f"d_theta_src_{name}", base_var=theta_var)
    frequency_var: Var = vf.add_var(name=f"f_src_{name}")
    amplitude_var: Var = vf.add_var(name=f"I_amp_{name}")
    phase_a_deg_var: Var = vf.add_var(name=f"phi_deg_A_{name}")
    offset_var: Var = vf.add_var(name=f"I_offset_{name}")

    templ.block.event_dict[frequency_var] = vf.add_const(float(frequency_hz))
    templ.block.event_dict[amplitude_var] = vf.add_const(float(amplitude_value))
    templ.block.event_dict[phase_a_deg_var] = vf.add_const(float(phase_a_deg))
    templ.block.event_dict[offset_var] = vf.add_const(float(offset_value))

    templ.block.in_vars = [v_a, v_b, v_c]
    templ.block.state_vars = [theta_var]
    templ.block.diff_vars = [d_theta_var]
    templ.block.state_eqs = [sym.Const(2.0) * sym.Const(3.141592653589793) * frequency_var]
    templ.block.algebraic_vars = [i_a, i_b, i_c]
    templ.block.algebraic_eqs = [
        i_a - (offset_var + amplitude_var * sym.sin(_phase_angle_expression(theta_var, phase_a_deg_var, 0.0))),
        i_b - (offset_var + amplitude_var * sym.sin(_phase_angle_expression(theta_var, phase_a_deg_var, -120.0))),
        i_c - (offset_var + amplitude_var * sym.sin(_phase_angle_expression(theta_var, phase_a_deg_var, 120.0))),
    ]
    templ.block.out_vars = [i_a, i_b, i_c]
    templ.block.external_mapping = _build_external_mapping(v_a, v_b, v_c, i_a, i_b, i_c)
    templ.block.init_eqs = {theta_var: sym.Const(0.0), i_a: offset_var, i_b: offset_var, i_c: offset_var}
    return templ


def get_controlled_balanced_3ph_current_source_emt_template(vf: VarFactory,
                                                            frequency_hz: float = 50.0,
                                                            phase_a_deg: float = 0.0,
                                                            offset_value: float = 0.0,
                                                            name: str = "controlled_balanced_3ph_current_source_emt") -> EmtModelTemplate:
    """
    Build one balanced three-phase sinusoidal EMT current source with amplitude command.

    :param vf: EMT variable factory.
    :param frequency_hz: Common sinusoidal frequency.
    :param phase_a_deg: Phase-A angle offset in degrees.
    :param offset_value: Common phase offset.
    :param name: Symbolic block name.
    :return: Configured EMT template.
    """
    templ = EmtModelTemplate()
    templ.tpe = DeviceType.GeneratorDevice
    templ.name = name
    templ.block.name = name

    v_a: Var = vf.add_var(name=f"v_A_{name}", reference=VarPowerFlowReferenceType.v_A)
    v_b: Var = vf.add_var(name=f"v_B_{name}", reference=VarPowerFlowReferenceType.v_B)
    v_c: Var = vf.add_var(name=f"v_C_{name}", reference=VarPowerFlowReferenceType.v_C)
    i_amp_cmd: Var = vf.add_var(name=f"i_amp_cmd_{name}")
    i_a: Var = vf.add_var(name=f"i_A_{name}", reference=VarPowerFlowReferenceType.i_A)
    i_b: Var = vf.add_var(name=f"i_B_{name}", reference=VarPowerFlowReferenceType.i_B)
    i_c: Var = vf.add_var(name=f"i_C_{name}", reference=VarPowerFlowReferenceType.i_C)
    theta_var: Var = vf.add_var(name=f"theta_src_{name}")
    d_theta_var: Var = vf.add_diff_var(name=f"d_theta_src_{name}", base_var=theta_var)
    frequency_var: Var = vf.add_var(name=f"f_src_{name}")
    phase_a_deg_var: Var = vf.add_var(name=f"phi_deg_A_{name}")
    offset_var: Var = vf.add_var(name=f"I_offset_{name}")

    templ.block.event_dict[frequency_var] = vf.add_const(float(frequency_hz))
    templ.block.event_dict[phase_a_deg_var] = vf.add_const(float(phase_a_deg))
    templ.block.event_dict[offset_var] = vf.add_const(float(offset_value))

    templ.block.in_vars = [v_a, v_b, v_c, i_amp_cmd]
    templ.block.state_vars = [theta_var]
    templ.block.diff_vars = [d_theta_var]
    templ.block.state_eqs = [sym.Const(2.0) * sym.Const(3.141592653589793) * frequency_var]
    templ.block.algebraic_vars = [i_a, i_b, i_c]
    templ.block.algebraic_eqs = [
        i_a - (offset_var + i_amp_cmd * sym.sin(_phase_angle_expression(theta_var, phase_a_deg_var, 0.0))),
        i_b - (offset_var + i_amp_cmd * sym.sin(_phase_angle_expression(theta_var, phase_a_deg_var, -120.0))),
        i_c - (offset_var + i_amp_cmd * sym.sin(_phase_angle_expression(theta_var, phase_a_deg_var, 120.0))),
    ]
    templ.block.out_vars = [i_a, i_b, i_c]
    templ.block.external_mapping = _build_external_mapping(v_a, v_b, v_c, i_a, i_b, i_c)
    templ.block.init_eqs = {theta_var: sym.Const(0.0), i_a: offset_var, i_b: offset_var, i_c: offset_var}
    return templ


def get_balanced_3ph_voltage_source_emt_template(vf: VarFactory,
                                                 amplitude_value: float = 1.0,
                                                 frequency_hz: float = 50.0,
                                                 phase_a_deg: float = 0.0,
                                                 offset_value: float = 0.0,
                                                 source_conductance_value: float = 100.0,
                                                 name: str = "balanced_3ph_voltage_source_emt") -> EmtModelTemplate:
    """
    Build one balanced three-phase sinusoidal EMT voltage source using one Norton equivalent.

    :param vf: EMT variable factory.
    :param amplitude_value: Common phase amplitude.
    :param frequency_hz: Common sinusoidal frequency.
    :param phase_a_deg: Phase-A angle offset in degrees.
    :param offset_value: Common phase offset.
    :param source_conductance_value: Norton conductance.
    :param name: Symbolic block name.
    :return: Configured EMT template.
    """
    templ = EmtModelTemplate()
    templ.tpe = DeviceType.GeneratorDevice
    templ.name = name
    templ.block.name = name

    v_a: Var = vf.add_var(name=f"v_A_{name}", reference=VarPowerFlowReferenceType.v_A)
    v_b: Var = vf.add_var(name=f"v_B_{name}", reference=VarPowerFlowReferenceType.v_B)
    v_c: Var = vf.add_var(name=f"v_C_{name}", reference=VarPowerFlowReferenceType.v_C)
    i_a: Var = vf.add_var(name=f"i_A_{name}", reference=VarPowerFlowReferenceType.i_A)
    i_b: Var = vf.add_var(name=f"i_B_{name}", reference=VarPowerFlowReferenceType.i_B)
    i_c: Var = vf.add_var(name=f"i_C_{name}", reference=VarPowerFlowReferenceType.i_C)
    theta_var: Var = vf.add_var(name=f"theta_src_{name}")
    d_theta_var: Var = vf.add_diff_var(name=f"d_theta_src_{name}", base_var=theta_var)
    frequency_var: Var = vf.add_var(name=f"f_src_{name}")
    amplitude_var: Var = vf.add_var(name=f"V_amp_{name}")
    phase_a_deg_var: Var = vf.add_var(name=f"phi_deg_A_{name}")
    offset_var: Var = vf.add_var(name=f"V_offset_{name}")
    conductance_var: Var = vf.add_var(name=f"g_src_{name}")

    templ.block.event_dict[frequency_var] = vf.add_const(float(frequency_hz))
    templ.block.event_dict[amplitude_var] = vf.add_const(float(amplitude_value))
    templ.block.event_dict[phase_a_deg_var] = vf.add_const(float(phase_a_deg))
    templ.block.event_dict[offset_var] = vf.add_const(float(offset_value))
    templ.block.event_dict[conductance_var] = vf.add_const(float(source_conductance_value))

    v_src_a: Expr = offset_var + amplitude_var * sym.sin(_phase_angle_expression(theta_var, phase_a_deg_var, 0.0))
    v_src_b: Expr = offset_var + amplitude_var * sym.sin(_phase_angle_expression(theta_var, phase_a_deg_var, -120.0))
    v_src_c: Expr = offset_var + amplitude_var * sym.sin(_phase_angle_expression(theta_var, phase_a_deg_var, 120.0))

    templ.block.in_vars = [v_a, v_b, v_c]
    templ.block.state_vars = [theta_var]
    templ.block.diff_vars = [d_theta_var]
    templ.block.state_eqs = [sym.Const(2.0) * sym.Const(3.141592653589793) * frequency_var]
    templ.block.algebraic_vars = [i_a, i_b, i_c]
    templ.block.algebraic_eqs = [
        i_a - conductance_var * (v_src_a - v_a),
        i_b - conductance_var * (v_src_b - v_b),
        i_c - conductance_var * (v_src_c - v_c),
    ]
    templ.block.out_vars = [i_a, i_b, i_c]
    templ.block.external_mapping = _build_external_mapping(v_a, v_b, v_c, i_a, i_b, i_c)
    templ.block.init_eqs = {theta_var: sym.Const(0.0), i_a: conductance_var * (offset_var - v_a), i_b: conductance_var * (offset_var - v_b), i_c: conductance_var * (offset_var - v_c)}
    return templ


def get_controlled_balanced_3ph_voltage_source_emt_template(vf: VarFactory,
                                                            frequency_hz: float = 50.0,
                                                            phase_a_deg: float = 0.0,
                                                            offset_value: float = 0.0,
                                                            source_conductance_value: float = 100.0,
                                                            name: str = "controlled_balanced_3ph_voltage_source_emt") -> EmtModelTemplate:
    """
    Build one balanced three-phase sinusoidal EMT voltage source with amplitude command.

    :param vf: EMT variable factory.
    :param frequency_hz: Common sinusoidal frequency.
    :param phase_a_deg: Phase-A angle offset in degrees.
    :param offset_value: Common phase offset.
    :param source_conductance_value: Norton conductance.
    :param name: Symbolic block name.
    :return: Configured EMT template.
    """
    templ = EmtModelTemplate()
    templ.tpe = DeviceType.GeneratorDevice
    templ.name = name
    templ.block.name = name

    v_a: Var = vf.add_var(name=f"v_A_{name}", reference=VarPowerFlowReferenceType.v_A)
    v_b: Var = vf.add_var(name=f"v_B_{name}", reference=VarPowerFlowReferenceType.v_B)
    v_c: Var = vf.add_var(name=f"v_C_{name}", reference=VarPowerFlowReferenceType.v_C)
    v_amp_cmd: Var = vf.add_var(name=f"v_amp_cmd_{name}")
    i_a: Var = vf.add_var(name=f"i_A_{name}", reference=VarPowerFlowReferenceType.i_A)
    i_b: Var = vf.add_var(name=f"i_B_{name}", reference=VarPowerFlowReferenceType.i_B)
    i_c: Var = vf.add_var(name=f"i_C_{name}", reference=VarPowerFlowReferenceType.i_C)
    theta_var: Var = vf.add_var(name=f"theta_src_{name}")
    d_theta_var: Var = vf.add_diff_var(name=f"d_theta_src_{name}", base_var=theta_var)
    frequency_var: Var = vf.add_var(name=f"f_src_{name}")
    phase_a_deg_var: Var = vf.add_var(name=f"phi_deg_A_{name}")
    offset_var: Var = vf.add_var(name=f"V_offset_{name}")
    conductance_var: Var = vf.add_var(name=f"g_src_{name}")

    templ.block.event_dict[frequency_var] = vf.add_const(float(frequency_hz))
    templ.block.event_dict[phase_a_deg_var] = vf.add_const(float(phase_a_deg))
    templ.block.event_dict[offset_var] = vf.add_const(float(offset_value))
    templ.block.event_dict[conductance_var] = vf.add_const(float(source_conductance_value))

    v_src_a: Expr = offset_var + v_amp_cmd * sym.sin(_phase_angle_expression(theta_var, phase_a_deg_var, 0.0))
    v_src_b: Expr = offset_var + v_amp_cmd * sym.sin(_phase_angle_expression(theta_var, phase_a_deg_var, -120.0))
    v_src_c: Expr = offset_var + v_amp_cmd * sym.sin(_phase_angle_expression(theta_var, phase_a_deg_var, 120.0))

    templ.block.in_vars = [v_a, v_b, v_c, v_amp_cmd]
    templ.block.state_vars = [theta_var]
    templ.block.diff_vars = [d_theta_var]
    templ.block.state_eqs = [sym.Const(2.0) * sym.Const(3.141592653589793) * frequency_var]
    templ.block.algebraic_vars = [i_a, i_b, i_c]
    templ.block.algebraic_eqs = [
        i_a - conductance_var * (v_src_a - v_a),
        i_b - conductance_var * (v_src_b - v_b),
        i_c - conductance_var * (v_src_c - v_c),
    ]
    templ.block.out_vars = [i_a, i_b, i_c]
    templ.block.external_mapping = _build_external_mapping(v_a, v_b, v_c, i_a, i_b, i_c)
    templ.block.init_eqs = {theta_var: sym.Const(0.0), i_a: conductance_var * (offset_var - v_a), i_b: conductance_var * (offset_var - v_b), i_c: conductance_var * (offset_var - v_c)}
    return templ
