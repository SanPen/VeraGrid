# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Phase-selective EMT exponential-load template."""

from typing import Dict, List, Tuple

import numpy as np

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.load_RLC_emt_template import _get_active_phases, _get_phase_count_name
from VeraGridEngine.Utils.Symbolic.block import Expr, Var
from VeraGridEngine.enumerations import DeviceType, ParamPowerFlowRefferenceType, VarPowerFlowRefferenceType


def _get_voltage_reference(phase_label: str) -> VarPowerFlowRefferenceType:
    """Return the EMT voltage enum for one active phase.

    :param phase_label: Phase label in ``A``, ``B`` or ``C``.
    :return: Matching voltage reference enum.
    """
    if phase_label == "A":
        reference: VarPowerFlowRefferenceType = VarPowerFlowRefferenceType.v_A
    else:
        if phase_label == "B":
            reference = VarPowerFlowRefferenceType.v_B
        else:
            if phase_label == "C":
                reference = VarPowerFlowRefferenceType.v_C
            else:
                raise ValueError(f"Unsupported phase label '{phase_label}'")

    return reference


def _get_api_power_references(phase_label: str) -> Tuple[ParamPowerFlowRefferenceType, ParamPowerFlowRefferenceType]:
    """Return the API active/reactive power enums for one active phase.

    :param phase_label: Phase label in ``A``, ``B`` or ``C``.
    :return: Tuple with API active-power and reactive-power reference enums.
    """
    if phase_label == "A":
        p_reference: ParamPowerFlowRefferenceType = ParamPowerFlowRefferenceType.Pl0_A
        q_reference: ParamPowerFlowRefferenceType = ParamPowerFlowRefferenceType.Ql0_A
    else:
        if phase_label == "B":
            p_reference = ParamPowerFlowRefferenceType.Pl0_B
            q_reference = ParamPowerFlowRefferenceType.Ql0_B
        else:
            if phase_label == "C":
                p_reference = ParamPowerFlowRefferenceType.Pl0_C
                q_reference = ParamPowerFlowRefferenceType.Ql0_C
            else:
                raise ValueError(f"Unsupported phase label '{phase_label}'")

    return p_reference, q_reference


def get_exponential_load_emt(
    vf: VarFactory,
    phA: bool = True,
    phB: bool = True,
    phC: bool = True,
    name: str = "EXP_Load_EMT_3ph",
) -> EmtModelTemplate:
    """Build the phase-selective EMT exponential-load template.

    The load keeps the original per-phase SOGI state model and exponential
    voltage dependence, but instantiates those equations only for the phases
    enabled by ``phA``, ``phB`` and ``phC``.

    :param vf: EMT variable factory.
    :param phA: True when phase A is active.
    :param phB: True when phase B is active.
    :param phC: True when phase C is active.
    :param name: Symbolic block name.
    :return: Configured EMT template.
    """
    active_phases: List[str] = _get_active_phases(phA=phA, phB=phB, phC=phC)
    phase_count: int = len(active_phases)
    resolved_name: str = _get_phase_count_name(base_name="EXP_Load_EMT", phase_count=phase_count, requested_name=name)

    templ: EmtModelTemplate = EmtModelTemplate()
    templ.tpe = DeviceType.LoadDevice
    templ.name = resolved_name
    templ.block.name = resolved_name

    # Shared constants stay scalar because every per-phase equation reuses the
    # same EMT formulation and only the active phase list changes the sizing.
    c2: Expr = vf.add_const(2.0)
    c05: Expr = vf.add_const(0.5)

    # Runtime parameters remain global to the load object because they are fed by
    # the EMT initialization workflow and reused across all active phases.
    v0: Var = vf.add_var(name=f"V0_{resolved_name}")
    alpha_p: Var = vf.add_var(name=f"a_{resolved_name}")
    alpha_q: Var = vf.add_var(name=f"b_{resolved_name}")
    k_sogi: Var = vf.add_var(name=f"k_sogi_{resolved_name}")
    eps: Var = vf.add_var(name=f"eps_{resolved_name}")
    omega: Var = vf.add_var(name=f"omega_{resolved_name}")

    templ.block.event_dict[v0] = vf.add_const(float(np.sqrt(2.0)))
    templ.block.event_dict[alpha_p] = vf.add_const(2.0)
    templ.block.event_dict[alpha_q] = vf.add_const(2.0)
    templ.block.event_dict[k_sogi] = vf.add_const(float(np.sqrt(2.0)))
    templ.block.event_dict[eps] = vf.add_const(1e-12)
    templ.block.event_dict[omega] = vf.add_const(2.0 * np.pi * 50.0)

    # All phase-indexed structures are built from the active phase list so the
    # block sizes, names and ordering match the electrical connection exactly.
    voltage_vars: Dict[str, Var] = dict()
    voltage_derivative_vars: Dict[str, Var] = dict()
    p0_vars: Dict[str, Var] = dict()
    q0_vars: Dict[str, Var] = dict()
    u_vars: Dict[str, Var] = dict()
    q_vars: Dict[str, Var] = dict()
    d_u_vars: Dict[str, Var] = dict()
    d_q_vars: Dict[str, Var] = dict()
    v2_vars: Dict[str, Var] = dict()
    vm_vars: Dict[str, Var] = dict()
    ratio_vars: Dict[str, Var] = dict()
    p_vars: Dict[str, Var] = dict()
    q_load_vars: Dict[str, Var] = dict()
    current_vars: Dict[str, Var] = dict()

    in_vars: List[Var] = list()
    state_vars: List[Var] = list()
    diff_vars: List[Var] = list()
    state_eqs: List[Expr] = list()
    algebraic_vars: List[Var] = list()
    algebraic_eqs: List[Expr] = list()
    init_eqs: Dict[Var, Expr] = dict()
    diff_init_eqs: Dict[Var, Expr] = dict()

    phase_label: str
    for phase_label in active_phases:
        # These are the only bus-voltage inputs created, which is what makes the
        # symbolic block itself phase-selective without any EMT core changes.
        voltage_var: Var = vf.add_var(
            name=f"v_{phase_label}_{resolved_name}",
            reference=_get_voltage_reference(phase_label=phase_label),
        )
        voltage_derivative_var: Var = vf.add_var(name=f"d_v_{phase_label}_{resolved_name}")
        p0_var: Var = vf.add_var(name=f"P0_{phase_label}_{resolved_name}")
        q0_var: Var = vf.add_var(name=f"Q0_{phase_label}_{resolved_name}")

        templ.block.event_dict[voltage_derivative_var] = vf.add_const(None)
        templ.block.event_dict[p0_var] = vf.add_const(0.1 / 3.0)
        templ.block.event_dict[q0_var] = vf.add_const(0.01 / 3.0)

        voltage_vars[phase_label] = voltage_var
        voltage_derivative_vars[phase_label] = voltage_derivative_var
        p0_vars[phase_label] = p0_var
        q0_vars[phase_label] = q0_var
        in_vars.append(voltage_var)

        # Each active phase keeps the original two SOGI states and two dynamic
        # equations, so the ABC case remains mathematically identical.
        u_var: Var = vf.add_var(name=f"u_{phase_label}_{resolved_name}")
        q_var: Var = vf.add_var(name=f"q_{phase_label}_{resolved_name}")
        d_u_var: Var = vf.add_diff_var(name=f"d_u_{phase_label}_{resolved_name}", base_var=u_var)
        d_q_var: Var = vf.add_diff_var(name=f"d_q_{phase_label}_{resolved_name}", base_var=q_var)

        u_vars[phase_label] = u_var
        q_vars[phase_label] = q_var
        d_u_vars[phase_label] = d_u_var
        d_q_vars[phase_label] = d_q_var
        state_vars.append(u_var)
        state_vars.append(q_var)
        diff_vars.append(d_u_var)
        diff_vars.append(d_q_var)
        state_eqs.append(k_sogi * omega * (voltage_var - u_var) - omega * q_var)
        state_eqs.append(omega * u_var)

        # The algebraic layer is also instantiated strictly per active phase so
        # there are no inactive placeholders or index gaps in AC/BC-style cases.
        v2_var: Var = vf.add_var(name=f"V{phase_label}2_{resolved_name}")
        vm_var: Var = vf.add_var(name=f"Vm{phase_label}_{resolved_name}")
        ratio_var: Var = vf.add_var(name=f"r{phase_label}_{resolved_name}")
        p_var: Var = vf.add_var(name=f"P_{phase_label}_{resolved_name}")
        q_load_var: Var = vf.add_var(name=f"Q_{phase_label}_{resolved_name}")
        current_var: Var = vf.add_var(name=f"i_{phase_label}_{resolved_name}")

        v2_vars[phase_label] = v2_var
        vm_vars[phase_label] = vm_var
        ratio_vars[phase_label] = ratio_var
        p_vars[phase_label] = p_var
        q_load_vars[phase_label] = q_load_var
        current_vars[phase_label] = current_var
        algebraic_vars.append(v2_var)
        algebraic_vars.append(vm_var)
        algebraic_vars.append(ratio_var)
        algebraic_vars.append(p_var)
        algebraic_vars.append(q_load_var)
        algebraic_vars.append(current_var)

        algebraic_eqs.append(v2_var - (u_var * u_var + q_var * q_var))
        algebraic_eqs.append(vm_var - ((v2_var + eps) ** c05))
        algebraic_eqs.append(ratio_var - (vm_var / v0))
        algebraic_eqs.append(p_var + (p0_var * (ratio_var ** alpha_p)))
        algebraic_eqs.append(q_load_var + (q0_var * (ratio_var ** alpha_q)))
        algebraic_eqs.append(current_var - (c2 * (u_var * p_var + q_var * q_load_var) / (v2_var + eps)))

        # The explicit initializer consumes these seeds phase by phase using the
        # same formulas as before, now limited to the active subset.
        init_eqs[u_var] = voltage_var
        init_eqs[q_var] = -voltage_derivative_var / omega
        init_eqs[v2_var] = u_var * u_var + q_var * q_var
        init_eqs[vm_var] = (v2_var + eps) ** c05
        init_eqs[ratio_var] = vm_var / v0
        init_eqs[p_var] = -(p0_var * (ratio_var ** alpha_p))
        init_eqs[q_load_var] = -(q0_var * (ratio_var ** alpha_q))
        init_eqs[current_var] = c2 * (u_var * p_var + q_var * q_load_var) / (v2_var + eps)

        diff_init_eqs[d_u_var] = voltage_derivative_var
        diff_init_eqs[d_q_var] = omega * u_var

    templ.block.in_vars = in_vars
    templ.block.out_vars = list(current_vars[phase_label] for phase_label in active_phases)
    templ.block.state_vars = state_vars
    templ.block.diff_vars = diff_vars
    templ.block.state_eqs = state_eqs
    templ.block.algebraic_vars = algebraic_vars
    templ.block.algebraic_eqs = algebraic_eqs
    templ.block.init_eqs = init_eqs
    templ.block.diff_init_eqs = diff_init_eqs

    # The external mapping keeps the fixed EMT enum contract, but only active
    # phases publish concrete variables. Inactive phases are explicit ``None``.
    external_mapping: Dict[VarPowerFlowRefferenceType, Var | None] = dict({
        VarPowerFlowRefferenceType.v_N: None,
        VarPowerFlowRefferenceType.v_A: voltage_vars.get("A", None),
        VarPowerFlowRefferenceType.v_B: voltage_vars.get("B", None),
        VarPowerFlowRefferenceType.v_C: voltage_vars.get("C", None),
        VarPowerFlowRefferenceType.P: None,
        VarPowerFlowRefferenceType.Q: None,
        VarPowerFlowRefferenceType.P_N: None,
        VarPowerFlowRefferenceType.Q_N: None,
        VarPowerFlowRefferenceType.P_A: p_vars.get("A", None),
        VarPowerFlowRefferenceType.Q_A: q_load_vars.get("A", None),
        VarPowerFlowRefferenceType.P_B: p_vars.get("B", None),
        VarPowerFlowRefferenceType.Q_B: q_load_vars.get("B", None),
        VarPowerFlowRefferenceType.P_C: p_vars.get("C", None),
        VarPowerFlowRefferenceType.Q_C: q_load_vars.get("C", None),
        VarPowerFlowRefferenceType.i_N: None,
        VarPowerFlowRefferenceType.i_A: current_vars.get("A", None),
        VarPowerFlowRefferenceType.i_B: current_vars.get("B", None),
        VarPowerFlowRefferenceType.i_C: current_vars.get("C", None),
        VarPowerFlowRefferenceType.phi_v: None,
        VarPowerFlowRefferenceType.phi: None,
        VarPowerFlowRefferenceType.Vpk: None,
        VarPowerFlowRefferenceType.Ipk: None,
        VarPowerFlowRefferenceType.d_v_N: None,
        VarPowerFlowRefferenceType.d_v_A: voltage_derivative_vars.get("A", None),
        VarPowerFlowRefferenceType.d_v_B: voltage_derivative_vars.get("B", None),
        VarPowerFlowRefferenceType.d_v_C: voltage_derivative_vars.get("C", None),
    })
    templ.block.external_mapping = external_mapping

    # The load initializer writes only the active per-phase parameters into the
    # block, which keeps template metadata aligned with the generated equations.
    api_obj_mapping: Dict[ParamPowerFlowRefferenceType, Var | None] = dict({
        ParamPowerFlowRefferenceType.omega_base: omega,
    })

    for phase_label in active_phases:
        p_reference: ParamPowerFlowRefferenceType
        q_reference: ParamPowerFlowRefferenceType
        p_reference, q_reference = _get_api_power_references(phase_label=phase_label)
        api_obj_mapping[p_reference] = p0_vars[phase_label]
        api_obj_mapping[q_reference] = q0_vars[phase_label]

    templ.block.api_obj_mapping = api_obj_mapping

    return templ
