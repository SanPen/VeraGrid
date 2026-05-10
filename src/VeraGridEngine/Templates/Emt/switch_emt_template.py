# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Dict, List

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import DeviceType, ParamPowerFlowRefferenceType, VarPowerFlowRefferenceType
from VeraGridEngine.Utils.procedural_logic import sampled_value
from VeraGridEngine.Utils.Symbolic.symbolic import CmpOp, Comparison, Const, Expr, Var


def _get_active_phases(phA: bool, phB: bool, phC: bool) -> List[str]:
    """
    Return the enabled phase labels in strict A-B-C order.

    :param phA: True when phase A is active.
    :param phB: True when phase B is active.
    :param phC: True when phase C is active.
    :return: Ordered list with the active phase labels.
    """
    active_phases: List[str] = list()

    if phA:
        active_phases.append("A")
    else:
        pass

    if phB:
        active_phases.append("B")
    else:
        pass

    if phC:
        active_phases.append("C")
    else:
        pass

    if len(active_phases) == 0:
        raise ValueError("At least one phase must be enabled for an EMT switch template")
    else:
        return active_phases


def _get_from_voltage_reference(phase_label: str) -> VarPowerFlowRefferenceType:
    if phase_label == "A":
        return VarPowerFlowRefferenceType.vf_A
    else:
        if phase_label == "B":
            return VarPowerFlowRefferenceType.vf_B
        else:
            if phase_label == "C":
                return VarPowerFlowRefferenceType.vf_C
            else:
                raise ValueError(f"Unsupported phase label '{phase_label}'")


def _get_to_voltage_reference(phase_label: str) -> VarPowerFlowRefferenceType:
    if phase_label == "A":
        return VarPowerFlowRefferenceType.vt_A
    else:
        if phase_label == "B":
            return VarPowerFlowRefferenceType.vt_B
        else:
            if phase_label == "C":
                return VarPowerFlowRefferenceType.vt_C
            else:
                raise ValueError(f"Unsupported phase label '{phase_label}'")


def _get_from_current_reference(phase_label: str) -> VarPowerFlowRefferenceType:
    if phase_label == "A":
        return VarPowerFlowRefferenceType.if_A
    else:
        if phase_label == "B":
            return VarPowerFlowRefferenceType.if_B
        else:
            if phase_label == "C":
                return VarPowerFlowRefferenceType.if_C
            else:
                raise ValueError(f"Unsupported phase label '{phase_label}'")


def _get_to_current_reference(phase_label: str) -> VarPowerFlowRefferenceType:
    if phase_label == "A":
        return VarPowerFlowRefferenceType.it_A
    else:
        if phase_label == "B":
            return VarPowerFlowRefferenceType.it_B
        else:
            if phase_label == "C":
                return VarPowerFlowRefferenceType.it_C
            else:
                raise ValueError(f"Unsupported phase label '{phase_label}'")


def get_switch_emt_template(
    vf: VarFactory,
    phA: bool = True,
    phB: bool = True,
    phC: bool = True,
    signal_controlled: bool = False,
    seed_from_pf_active: bool = True,
    initial_closed: bool = True,
    use_device_conductance: bool = True,
    manual_closed_conductance: float = 1.0e4,
    open_conductance: float = 1.0e-8,
    switch_time_constant: float = 1.0e-4,
    command_threshold: float = 0.5,
    name: str = "switch_emt_template",
) -> EmtModelTemplate:
    """
    Build one phase-selective EMT switch branch template.

    :param vf: EMT variable factory.
    :param phA: Enable phase A.
    :param phB: Enable phase B.
    :param phC: Enable phase C.
    :param signal_controlled: If True, expose one control input and procedural logic.
    :param seed_from_pf_active: If True, seed the closed/open mode from `Switch.active`.
    :param initial_closed: Default closed state when PF seeding is disabled.
    :param use_device_conductance: If True, use the switch static `R/X` to derive the closed conductance.
    :param manual_closed_conductance: Manual closed conductance fallback.
    :param open_conductance: Open-state leakage conductance.
    :param switch_time_constant: First-order current time constant.
    :param command_threshold: Control threshold for the external command.
    :param name: Symbolic model name.
    :return: EMT switch template.
    """
    active_phases: List[str] = _get_active_phases(phA=phA, phB=phB, phC=phC)
    templ: EmtModelTemplate = EmtModelTemplate()
    templ.tpe = DeviceType.SwitchDevice
    templ.name = name
    templ.block.name = name

    closed_mode: Var = vf.add_var(f"switch_closed_mode_{name}")
    templ.block.mode_dict[closed_mode] = Const(1.0 if initial_closed else 0.0, name="switch_closed_mode")

    g_device: Var = vf.add_var(f"switch_closed_g_api_{name}")
    g_manual: Var = vf.add_var(f"switch_closed_g_manual_{name}")
    g_open: Var = vf.add_var(f"switch_open_g_{name}")
    tau_var: Var = vf.add_var(f"switch_tau_{name}")
    seed_from_pf_var: Var = vf.add_var(f"switch_seed_from_pf_{name}")

    templ.block.parameters[g_device] = Const(0.0, name="switch_closed_g_api")
    templ.block.api_obj_mapping[ParamPowerFlowRefferenceType.g] = g_device
    templ.block.event_dict[g_manual] = Const(float(manual_closed_conductance), name="switch_closed_g_manual")
    templ.block.event_dict[g_open] = Const(float(open_conductance), name="switch_open_g")
    templ.block.event_dict[tau_var] = Const(float(switch_time_constant), name="switch_tau")
    templ.block.event_dict[seed_from_pf_var] = Const(1.0 if seed_from_pf_active else 0.0, name="switch_seed_from_pf")

    g_closed_eff: Expr = seed_from_pf_var * g_device + (Const(1.0) - seed_from_pf_var) * g_manual
    g_eff: Expr = closed_mode * g_closed_eff + (Const(1.0) - closed_mode) * g_open

    in_vars: List[Var] = list()
    state_vars: List[Var] = list()
    diff_vars: List[Var] = list()
    algebraic_vars: List[Var] = list()
    algebraic_eqs: List[Expr] = list()
    state_eqs: List[Expr] = list()
    out_vars: List[Var] = list()
    external_mapping: Dict[VarPowerFlowRefferenceType, Var | None] = dict({
        VarPowerFlowRefferenceType.vf_N: None,
        VarPowerFlowRefferenceType.vf_A: None,
        VarPowerFlowRefferenceType.vf_B: None,
        VarPowerFlowRefferenceType.vf_C: None,
        VarPowerFlowRefferenceType.vt_N: None,
        VarPowerFlowRefferenceType.vt_A: None,
        VarPowerFlowRefferenceType.vt_B: None,
        VarPowerFlowRefferenceType.vt_C: None,
        VarPowerFlowRefferenceType.if_N: None,
        VarPowerFlowRefferenceType.if_A: None,
        VarPowerFlowRefferenceType.if_B: None,
        VarPowerFlowRefferenceType.if_C: None,
        VarPowerFlowRefferenceType.it_N: None,
        VarPowerFlowRefferenceType.it_A: None,
        VarPowerFlowRefferenceType.it_B: None,
        VarPowerFlowRefferenceType.it_C: None,
        VarPowerFlowRefferenceType.Sf_A: None,
        VarPowerFlowRefferenceType.Sf_B: None,
        VarPowerFlowRefferenceType.Sf_C: None,
        VarPowerFlowRefferenceType.St_A: None,
        VarPowerFlowRefferenceType.St_B: None,
        VarPowerFlowRefferenceType.St_C: None,
        VarPowerFlowRefferenceType.d_v_N_f: None,
        VarPowerFlowRefferenceType.d_v_A_f: None,
        VarPowerFlowRefferenceType.d_v_B_f: None,
        VarPowerFlowRefferenceType.d_v_C_f: None,
        VarPowerFlowRefferenceType.d_v_N_t: None,
        VarPowerFlowRefferenceType.d_v_A_t: None,
        VarPowerFlowRefferenceType.d_v_B_t: None,
        VarPowerFlowRefferenceType.d_v_C_t: None,
    })

    if signal_controlled:
        command_input = vf.add_var(f"switch_cmd_{name}")
        threshold_var = vf.add_var(f"switch_cmd_threshold_{name}")
        templ.block.event_dict[threshold_var] = Const(float(command_threshold), name="switch_cmd_threshold")
        templ.block.procedural_logic.append(
            sampled_value(output=closed_mode, source=Comparison(lhs=command_input, op=CmpOp.GE, rhs=threshold_var))
        )
        in_vars.append(command_input)
    else:
        pass

    phase_label: str
    for phase_label in active_phases:
        v_from = vf.add_var(f"vf_{phase_label}_{name}", reference=_get_from_voltage_reference(phase_label))
        v_to = vf.add_var(f"vt_{phase_label}_{name}", reference=_get_to_voltage_reference(phase_label))
        i_state = vf.add_var(f"i_{phase_label}_{name}")
        di_state = vf.add_diff_var(name=f"di_{phase_label}_{name}", base_var=i_state)
        i_from = vf.add_var(f"if_{phase_label}_{name}", reference=_get_from_current_reference(phase_label))
        i_to = vf.add_var(f"it_{phase_label}_{name}", reference=_get_to_current_reference(phase_label))

        in_vars.extend(list([v_from, v_to]))
        state_vars.append(i_state)
        diff_vars.append(di_state)
        algebraic_vars.extend(list([i_from, i_to]))
        state_eqs.append((g_eff * (v_from - v_to) - i_state) / tau_var)
        algebraic_eqs.append(i_from - i_state)
        algebraic_eqs.append(i_to + i_state)
        out_vars.extend(list([i_from, i_to]))
        external_mapping[_get_from_voltage_reference(phase_label)] = v_from
        external_mapping[_get_to_voltage_reference(phase_label)] = v_to
        external_mapping[_get_from_current_reference(phase_label)] = i_from
        external_mapping[_get_to_current_reference(phase_label)] = i_to

    init_eqs: Dict[Var, Expr | Const] = dict()
    diff_init_eqs: Dict[Var, Expr | Const] = dict()
    state_var: Var
    state_eq: Expr

    for state_var in state_vars:
        init_eqs[state_var] = Const(0.0)

    for di_var, state_eq in zip(diff_vars, state_eqs):
        diff_init_eqs[di_var] = state_eq

    templ.block.in_vars = in_vars
    templ.block.state_vars = state_vars
    templ.block.diff_vars = diff_vars
    templ.block.algebraic_vars = algebraic_vars
    templ.block.state_eqs = state_eqs
    templ.block.algebraic_eqs = algebraic_eqs
    templ.block.out_vars = out_vars
    templ.block.external_mapping = external_mapping
    templ.block.init_eqs = init_eqs
    templ.block.diff_init_eqs = diff_init_eqs
    return templ
