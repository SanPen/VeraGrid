# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Phase-selective EMT ZIP-load template."""

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


def get_load_ZIP_emt_template(
    vf: VarFactory,
    phA: bool = True,
    phB: bool = True,
    phC: bool = True,
    name: str = "ZIP_Load_EMT_3ph",
) -> EmtModelTemplate:
    """Build the phase-selective EMT ZIP-load template.

    The original per-phase SOGI filter and ZIP polynomial are reused without
    changing their formulas. Only the number and ordering of the generated phase
    blocks now follow the explicit ``phA``/``phB``/``phC`` selection.

    :param vf: EMT variable factory.
    :param phA: True when phase A is active.
    :param phB: True when phase B is active.
    :param phC: True when phase C is active.
    :param name: Symbolic block name.
    :return: Configured EMT template.
    """
    active_phases: List[str] = _get_active_phases(phA=phA, phB=phB, phC=phC)
    phase_count: int = len(active_phases)
    resolved_name: str = _get_phase_count_name(base_name="ZIP_Load_EMT", phase_count=phase_count, requested_name=name)

    templ: EmtModelTemplate = EmtModelTemplate()
    templ.tpe = DeviceType.LoadDevice
    templ.name = resolved_name
    templ.block.name = resolved_name

    # Shared constants are reused by every active phase and keep the original ZIP
    # formulation numerically identical when all three phases are enabled.
    c2: Expr = vf.add_const(2.0)
    c05: Expr = vf.add_const(0.5)

    # ZIP coefficients remain device-wide EMT parameters because the existing load
    # model uses one coefficient set for all active phase equations.
    v0: Var = vf.add_var(name=f"V0_{resolved_name}")
    a1: Var = vf.add_var(name=f"a1_{resolved_name}")
    a2: Var = vf.add_var(name=f"a2_{resolved_name}")
    a3: Var = vf.add_var(name=f"a3_{resolved_name}")
    a4: Var = vf.add_var(name=f"a4_{resolved_name}")
    a5: Var = vf.add_var(name=f"a5_{resolved_name}")
    a6: Var = vf.add_var(name=f"a6_{resolved_name}")
    k_sogi: Var = vf.add_var(name=f"k_sogi_{resolved_name}")
    eps: Var = vf.add_var(name=f"eps_{resolved_name}")
    omega: Var = vf.add_var(name=f"omega_{resolved_name}")

    templ.block.event_dict[v0] = vf.add_const(float(np.sqrt(2.0)))
    templ.block.event_dict[k_sogi] = vf.add_const(float(np.sqrt(2.0)))
    templ.block.event_dict[eps] = vf.add_const(1e-12)
    templ.block.event_dict[a1] = vf.add_const(1.0)
    templ.block.event_dict[a2] = vf.add_const(0.0)
    templ.block.event_dict[a3] = vf.add_const(0.0)
    templ.block.event_dict[a4] = vf.add_const(1.0)
    templ.block.event_dict[a5] = vf.add_const(0.0)
    templ.block.event_dict[a6] = vf.add_const(0.0)

    # Every phase-indexed structure is instantiated strictly in filtered A-B-C
    # order so 1-phase and 2-phase realizations have compact indexing.
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
        # These inputs are the only terminal voltages exposed to the bus model, so
        # the block connectivity automatically shrinks to the active phase set.
        voltage_var: Var = vf.add_var(
            name=f"v_{phase_label}_{resolved_name}",
            reference=_get_voltage_reference(phase_label=phase_label),
        )
        voltage_derivative_var: Var = vf.add_var(name=f"d_v_{phase_label}_{resolved_name}")
        p0_var: Var = vf.add_var(name=f"P0_{phase_label}_{resolved_name}")
        q0_var: Var = vf.add_var(name=f"Q0_{phase_label}_{resolved_name}")

        templ.block.event_dict[voltage_derivative_var] = vf.add_const(None)

        voltage_vars[phase_label] = voltage_var
        voltage_derivative_vars[phase_label] = voltage_derivative_var
        p0_vars[phase_label] = p0_var
        q0_vars[phase_label] = q0_var
        in_vars.append(voltage_var)

        # Each active phase preserves the original SOGI pair and differential
        # equations, which is why the ABC realization remains numerically stable.
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

        # The ZIP polynomial and current injection are created per active phase so
        # there are no inactive entries hidden in the algebraic system size.
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

        # algebraic_eqs.append(v2_var - (u_var ** 2 + q_var ** 2))
        # algebraic_eqs.append(vm_var - ((v2_var + eps) ** c05))
        # algebraic_eqs.append(ratio_var - (vm_var / v0))
        # algebraic_eqs.append(p_var + (p0_var * (a1 * ratio_var ** 2 + a2 * ratio_var + a3)))
        # algebraic_eqs.append(q_load_var + (q0_var * (a4 * ratio_var ** 2 + a5 * ratio_var + a6)))
        # algebraic_eqs.append(current_var + (c2 * (u_var * (-p_var) + q_var * (-q_load_var)) / (v2_var + eps)))
        # The squared voltage magnitude remains available as an algebraic output, but the
        # voltage magnitude itself is computed directly from the SOGI orthogonal states.
        # This avoids taking the square root of an independent algebraic iterate that may
        # become temporarily negative during Newton iterations.
        algebraic_eqs.append(v2_var - (u_var ** 2 + q_var ** 2))

        # The magnitude is evaluated from the physically non-negative quantity u^2 + q^2.
        algebraic_eqs.append(vm_var - ((u_var ** 2 + q_var ** 2 + eps) ** c05))

        # The ZIP ratio uses the positive magnitude variable.
        algebraic_eqs.append(ratio_var - (vm_var / v0))

        # The active and reactive ZIP powers keep the original polynomial structure.
        algebraic_eqs.append(p_var + (p0_var * (a1 * ratio_var ** 2 + a2 * ratio_var + a3)))
        algebraic_eqs.append(q_load_var + (q0_var * (a4 * ratio_var ** 2 + a5 * ratio_var + a6)))

        # The injected current is also evaluated with the guaranteed non-negative squared
        # magnitude to prevent sign-inconsistent or undefined denominators during Newton.
        algebraic_eqs.append(
            current_var + (c2 * (u_var * (-p_var) + q_var * (-q_load_var)) / (u_var ** 2 + q_var ** 2 + eps))
        )

        # The initializer keeps the same seeds as the legacy ZIP template so the
        # change stays limited to phase-selective sizing and naming.
        init_eqs[u_var] = voltage_var
        init_eqs[q_var] = -voltage_derivative_var / omega
        init_eqs[v2_var] = u_var ** 2 + q_var ** 2
        init_eqs[vm_var] = (v2_var + eps) ** c05
        init_eqs[ratio_var] = vm_var / v0

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

    # The external mapping stays compatible with the fixed EMT enum contract, but
    # only active phases carry symbolic variables into the topology assembler.
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

    # Only active per-phase load powers are published to the EMT initializer, and
    # the shared omega parameter remains mapped exactly as in the 3-phase model.
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
