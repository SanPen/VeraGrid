# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import DeviceType, ParamPowerFlowRefferenceType, VarPowerFlowRefferenceType
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def get_dc_line_emt_template(vf: VarFactory, name: str = "dc_line_emt_template") -> EmtModelTemplate:
    """
    Build a DC EMT line with the same symbolic structure as the AC PI line template.

    The static DC line data currently exposes only the series resistance. To keep
    the EMT implementation aligned with the existing AC PI code structure without
    adding new static parameters, the template models:

    - one series current state,
    - one explicit shunt leg per terminal,
    - one tiny fixed electrical time constant that regularizes the series branch
      and makes it behave like a near-resistive PI section.

    With zero shunt capacitance the EMT steady state remains consistent with the
    static PF model, while the code layout stays close to ``pi_line_emt_template``.

    :param vf: Shared EMT variable factory.
    :param name: Symbolic model name.
    :return: EMT DC line template.
    """
    templ: EmtModelTemplate = EmtModelTemplate()
    templ.tpe = DeviceType.DCLineDevice
    templ.name = name
    templ.block.name = name

    c0: Const = Const(0.0)
    tau_series: Const = Const(5.0e-5)
    g_damp: Const = Const(1.0e-8)
    c_shunt: Const = Const(0.0)

    # ------------------------------------------------------------------
    # External terminal voltages.
    # ------------------------------------------------------------------
    v_f_dc: Var = vf.add_var(name=f"v_f_dc_{name}", reference=VarPowerFlowRefferenceType.Vf_dc)
    v_t_dc: Var = vf.add_var(name=f"v_t_dc_{name}", reference=VarPowerFlowRefferenceType.Vt_dc)

    # ------------------------------------------------------------------
    # API-mapped electrical parameter.
    # ------------------------------------------------------------------
    g_ser: Var = vf.add_var(name=f"g_ser_{name}")
    templ.block.parameters[g_ser] = Const(0.0)

    # ------------------------------------------------------------------
    # PI-structure variables.
    # ------------------------------------------------------------------
    i_ser: Var = vf.add_var(name=f"i_ser_{name}")
    q_f: Var = vf.add_var(name=f"q_f_{name}")
    q_t: Var = vf.add_var(name=f"q_t_{name}")

    di_ser: Var = vf.add_diff_var(name=f"di_ser_{name}", base_var=i_ser)
    dq_f: Var = vf.add_diff_var(name=f"dq_f_{name}", base_var=q_f)
    dq_t: Var = vf.add_diff_var(name=f"dq_t_{name}", base_var=q_t)

    i_cap_f: Var = vf.add_var(name=f"i_cap_f_{name}")
    i_cap_t: Var = vf.add_var(name=f"i_cap_t_{name}")
    i_f_dc: Var = vf.add_var(name=f"i_f_dc_{name}", reference=VarPowerFlowRefferenceType.If_dc)
    i_t_dc: Var = vf.add_var(name=f"i_t_dc_{name}", reference=VarPowerFlowRefferenceType.It_dc)
    p_f: Var = vf.add_var(name=f"p_f_dc_{name}", reference=VarPowerFlowRefferenceType.Pf)
    p_t: Var = vf.add_var(name=f"p_t_dc_{name}", reference=VarPowerFlowRefferenceType.Pt)

    # ------------------------------------------------------------------
    # Series-branch dynamics.
    # ------------------------------------------------------------------
    # The reduced-order DC PI line uses a fixed tiny time constant so the series
    # current tracks the resistive PF solution quickly without becoming algebraic.
    di_ser_expression: Expr = (g_ser * (v_f_dc - v_t_dc) - i_ser) / tau_series

    templ.block.in_vars = list([v_f_dc, v_t_dc])
    templ.block.state_vars = list([i_ser, q_f, q_t])
    templ.block.diff_vars = list([di_ser, dq_f, dq_t])
    templ.block.algebraic_vars = list([i_cap_f, i_cap_t, i_f_dc, i_t_dc, p_f, p_t])

    templ.block.state_eqs = list([
        di_ser_expression,
        i_cap_f,
        i_cap_t,
    ])

    templ.block.algebraic_eqs = list([
        q_f - c_shunt * v_f_dc,
        q_t - c_shunt * v_t_dc,
        i_f_dc - (i_ser + i_cap_f + g_damp * v_f_dc),
        i_t_dc - (-i_ser + i_cap_t + g_damp * v_t_dc),
        p_f - v_f_dc * i_f_dc,
        p_t - v_t_dc * i_t_dc,
    ])

    templ.block.out_vars = list([i_f_dc, i_t_dc, p_f, p_t])

    templ.block.external_mapping = dict([
        (VarPowerFlowRefferenceType.Vf_dc, v_f_dc),
        (VarPowerFlowRefferenceType.Vt_dc, v_t_dc),
        (VarPowerFlowRefferenceType.Vdc, v_f_dc),
        (VarPowerFlowRefferenceType.If_dc, i_f_dc),
        (VarPowerFlowRefferenceType.It_dc, i_t_dc),
        (VarPowerFlowRefferenceType.Idc, i_f_dc),
        (VarPowerFlowRefferenceType.Pf, p_f),
        (VarPowerFlowRefferenceType.Pt, p_t),
    ])

    templ.block.api_obj_mapping = dict([
        (ParamPowerFlowRefferenceType.g, g_ser),
    ])

    templ.block.init_eqs = dict([
        (q_f, c_shunt * v_f_dc),
        (q_t, c_shunt * v_t_dc),
        (i_cap_f, c0),
        (i_cap_t, c0),
        (i_ser, i_f_dc - i_cap_f - g_damp * v_f_dc),
        (p_f, v_f_dc * i_f_dc),
        (p_t, v_t_dc * i_t_dc),
    ])

    templ.block.diff_init_eqs = dict([
        (di_ser, di_ser_expression),
        (dq_f, i_cap_f),
        (dq_t, i_cap_t),
    ])

    return templ
