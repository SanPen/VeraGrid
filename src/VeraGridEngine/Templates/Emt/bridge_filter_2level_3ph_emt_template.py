# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Tuple

import numpy as np

import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.bridge_2level_3ph_emt_template import get_bridge_2level_3ph_emt_template
from VeraGridEngine.Utils.Symbolic.block import Block, find_name_in_block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.enumerations import DeviceType


def _build_phase_to_dq0_measurements(
        i_A: Var,
        i_B: Var,
        i_C: Var,
        v_A: Var,
        v_B: Var,
        v_C: Var,
        theta_pll: Var,
) -> Tuple[Expr, Expr, Expr, Expr, Expr, Expr]:
    """
    Build dq0 measurement expressions from abc phase quantities.

    :param i_A: Phase-A current.
    :param i_B: Phase-B current.
    :param i_C: Phase-C current.
    :param v_A: Phase-A voltage.
    :param v_B: Phase-B voltage.
    :param v_C: Phase-C voltage.
    :param theta_pll: Electrical angle.
    :return: Tuple ``(i_d, i_q, i_0, v_d, v_q, v_0)``.
    """
    c13: Const = Const(1.0 / 3.0)
    c23: Const = Const(2.0 / 3.0)
    shift: Const = Const(2.0 * np.pi / 3.0)
    theta_b: Expr = theta_pll - shift
    theta_c: Expr = theta_pll + shift

    # The dq0 reconstruction follows the same convention used across the EMT converter templates.
    i_d_expr: Expr = c23 * (sym.sin(theta_pll) * i_A + sym.sin(theta_b) * i_B + sym.sin(theta_c) * i_C)
    i_q_expr: Expr = -c23 * (sym.cos(theta_pll) * i_A + sym.cos(theta_b) * i_B + sym.cos(theta_c) * i_C)
    i_0_expr: Expr = c13 * (i_A + i_B + i_C)

    v_d_expr: Expr = c23 * (sym.sin(theta_pll) * v_A + sym.sin(theta_b) * v_B + sym.sin(theta_c) * v_C)
    v_q_expr: Expr = -c23 * (sym.cos(theta_pll) * v_A + sym.cos(theta_b) * v_B + sym.cos(theta_c) * v_C)
    v_0_expr: Expr = c13 * (v_A + v_B + v_C)

    return i_d_expr, i_q_expr, i_0_expr, v_d_expr, v_q_expr, v_0_expr


def get_bridge_filter_2level_3ph_emt_template(vf: VarFactory,
                                              name: str = "bridge_filter_2level_3ph_emt") -> EmtModelTemplate:
    """
    Build a standalone 2-level bridge with a three-phase RL AC filter.

    The bridge itself is the validated standalone block with procedural PWM. On
    top of that, this template adds one per-phase RL filter so we can validate
    the electrical interaction between switched converter voltages and an AC-side
    network before reintegrating everything into a full VSC template.

    :param vf: Shared EMT variable factory.
    :param name: Symbolic model name.
    :return: Standalone bridge + filter EMT template.
    """
    templ: EmtModelTemplate = EmtModelTemplate()
    templ.tpe = DeviceType.DynamicModelHostDevice
    templ.name = name
    templ.block.name = name

    # ------------------------------------------------------------------
    # External inputs.
    # ------------------------------------------------------------------
    theta_pll: Var = vf.add_var(name=f"theta_pll_in_{name}")
    omega_base: Var = vf.add_var(name=f"omega_base_in_{name}")
    v_A: Var = vf.add_var(name=f"v_A_in_{name}")
    v_B: Var = vf.add_var(name=f"v_B_in_{name}")
    v_C: Var = vf.add_var(name=f"v_C_in_{name}")
    v_cmd_d: Var = vf.add_var(name=f"v_cmd_d_in_{name}")
    v_cmd_q: Var = vf.add_var(name=f"v_cmd_q_in_{name}")
    v_cmd_0: Var = vf.add_var(name=f"v_cmd_0_in_{name}")
    v_dc: Var = vf.add_var(name=f"v_dc_in_{name}")
    k_v_conv: Var = vf.add_var(name=f"k_v_conv_in_{name}")
    m_max: Var = vf.add_var(name=f"m_max_in_{name}")
    vdc_floor: Var = vf.add_var(name=f"vdc_floor_in_{name}")
    omega_sw: Var = vf.add_var(name=f"omega_sw_in_{name}")
    carrier_phase: Var = vf.add_var(name=f"carrier_phase_in_{name}")
    R_f: Var = vf.add_var(name=f"R_f_in_{name}")
    L_f: Var = vf.add_var(name=f"L_f_in_{name}")

    # ------------------------------------------------------------------
    # Bridge child block.
    # ------------------------------------------------------------------
    bridge_block: Block = get_bridge_2level_3ph_emt_template(vf=vf, name=f"{name}_bridge").block
    bridge_block.connect(
        bridge_block.in_vars,
        list([
            theta_pll,
            omega_base,
            v_cmd_d,
            v_cmd_q,
            v_cmd_0,
            v_dc,
            k_v_conv,
            m_max,
            vdc_floor,
            omega_sw,
            carrier_phase,
        ]),
    )

    gate_a: Var = bridge_block.out_vars[0]
    gate_b: Var = bridge_block.out_vars[1]
    gate_c: Var = bridge_block.out_vars[2]
    v_conv_a: Var = bridge_block.out_vars[3]
    v_conv_b: Var = bridge_block.out_vars[4]
    v_conv_c: Var = bridge_block.out_vars[5]

    # ------------------------------------------------------------------
    # Filter states.
    # ------------------------------------------------------------------
    i_A: Var = vf.add_var(name=f"i_A_{name}")
    i_B: Var = vf.add_var(name=f"i_B_{name}")
    i_C: Var = vf.add_var(name=f"i_C_{name}")
    d_i_A: Var = vf.add_diff_var(name=f"d_i_A_{name}", base_var=i_A)
    d_i_B: Var = vf.add_diff_var(name=f"d_i_B_{name}", base_var=i_B)
    d_i_C: Var = vf.add_diff_var(name=f"d_i_C_{name}", base_var=i_C)

    # ------------------------------------------------------------------
    # Filter measurements.
    # ------------------------------------------------------------------
    i_d: Var = vf.add_var(name=f"i_d_{name}")
    i_q: Var = vf.add_var(name=f"i_q_{name}")
    i_0: Var = vf.add_var(name=f"i_0_{name}")
    v_d: Var = vf.add_var(name=f"v_d_{name}")
    v_q: Var = vf.add_var(name=f"v_q_{name}")
    v_0: Var = vf.add_var(name=f"v_0_{name}")

    i_d_expr: Expr
    i_q_expr: Expr
    i_0_expr: Expr
    v_d_expr: Expr
    v_q_expr: Expr
    v_0_expr: Expr
    i_d_expr, i_q_expr, i_0_expr, v_d_expr, v_q_expr, v_0_expr = _build_phase_to_dq0_measurements(
        i_A=i_A,
        i_B=i_B,
        i_C=i_C,
        v_A=v_A,
        v_B=v_B,
        v_C=v_C,
        theta_pll=theta_pll,
    )

    templ.block = Block(
        name=name,
        children=list([bridge_block]),
        state_eqs=list([
            # Each phase filter current is defined with the same sign convention used by the pseudo-EMT
            # converter interface: positive current enters the AC bus from the converter branch. With
            # that convention the RL branch dynamics are driven by ``v_bus - v_conv``.
            omega_base * (v_A - v_conv_a - R_f * i_A) / L_f,
            omega_base * (v_B - v_conv_b - R_f * i_B) / L_f,
            omega_base * (v_C - v_conv_c - R_f * i_C) / L_f,
        ]),
        state_vars=list([i_A, i_B, i_C]),
        diff_vars=list([d_i_A, d_i_B, d_i_C]),
        algebraic_eqs=list([
            i_d - i_d_expr,
            i_q - i_q_expr,
            i_0 - i_0_expr,
            v_d - v_d_expr,
            v_q - v_q_expr,
            v_0 - v_0_expr,
        ]),
        algebraic_vars=list([i_d, i_q, i_0, v_d, v_q, v_0]),
        init_eqs=dict([
            (i_A, Const(0.0)),
            (i_B, Const(0.0)),
            (i_C, Const(0.0)),
            (i_d, Const(0.0)),
            (i_q, Const(0.0)),
            (i_0, Const(0.0)),
            (v_d, v_d_expr),
            (v_q, v_q_expr),
            (v_0, v_0_expr),
        ]),
        diff_init_eqs=dict([
            (d_i_A, Const(0.0)),
            (d_i_B, Const(0.0)),
            (d_i_C, Const(0.0)),
        ]),
        in_vars=list([
            theta_pll,
            omega_base,
            v_A,
            v_B,
            v_C,
            v_cmd_d,
            v_cmd_q,
            v_cmd_0,
            v_dc,
            k_v_conv,
            m_max,
            vdc_floor,
            omega_sw,
            carrier_phase,
            R_f,
            L_f,
        ]),
        out_vars=list([
            i_A,
            i_B,
            i_C,
            i_d,
            i_q,
            i_0,
            v_d,
            v_q,
            v_0,
            gate_a,
            gate_b,
            gate_c,
            v_conv_a,
            v_conv_b,
            v_conv_c,
        ]),
    )

    return templ
