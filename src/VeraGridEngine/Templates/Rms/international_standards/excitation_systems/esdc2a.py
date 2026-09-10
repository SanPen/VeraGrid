# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""IEEE DC2A direct-current commutator exciter (ESDC2A interface)."""

from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const
from VeraGridEngine.Utils.Symbolic.symbolic import Expr
from VeraGridEngine.Utils.Symbolic.symbolic import Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.enumerations import DeviceType

def build_esdc2a_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """
    Build the five-state IEEE DC2A sensing, regulator, exciter, and washout chain.

    :param vf: Variable factory that owns the exciter symbols.
    :type vf: VarFactory
    :param name: Optional runtime instance name.
    :type name: str | None
    :return: Materialized IEEE DC2A exciter model.
    :rtype: RmsModelTemplate
    """
    template_name: str
    if name is None:
        template_name: str = 'ESDC2A'
    else:
        template_name: str = name

    # Allocate the template and public control inputs before assembling the control chain.
    templ: RmsModelTemplate = RmsModelTemplate(name=template_name)
    templ.tpe = DeviceType.GeneratorDevice

    upss: Var = vf.add_var(name=f"UPssPu_{template_name}")
    uuel: Var = vf.add_var(name=f"UUelPu_{template_name}")
    us: Var = vf.add_var(name=f"UsPu_{template_name}")
    us_ref: Var = vf.add_var(name=f"UsRefPu_{template_name}")
    inputs: list[Var] = list([upss, uuel, us, us_ref])

    lg_y: Var = vf.add_var(name=f"LG_y_{template_name}")
    ll_x: Var = vf.add_var(name=f"LL_x_{template_name}")
    la_y: Var = vf.add_var(name=f"LA_y_{template_name}")
    int_y: Var = vf.add_var(name=f"INT_y_{template_name}")
    wf_x: Var = vf.add_var(name=f"WF_x_{template_name}")
    state_vars: list[Var] = list([lg_y, ll_x, la_y, int_y, wf_x])
    diff_vars: list[Var] = list([
        vf.add_diff_var(name=f"d_{lg_y.name}", base_var=lg_y),
        vf.add_diff_var(name=f"d_{ll_x.name}", base_var=ll_x),
        vf.add_diff_var(name=f"d_{la_y.name}", base_var=la_y),
        vf.add_diff_var(name=f"d_{int_y.name}", base_var=int_y),
        vf.add_diff_var(name=f"d_{wf_x.name}", base_var=wf_x),
    ])

    vi: Var = vf.add_var(name=f"ViPu_{template_name}")
    ll_y: Var = vf.add_var(name=f"LL_y_{template_name}")
    vr: Var = vf.add_var(name=f"VrPu_{template_name}")
    se: Var = vf.add_var(name=f"SePu_{template_name}")
    vfe: Var = vf.add_var(name=f"VfePu_{template_name}")
    wf_y: Var = vf.add_var(name=f"WF_y_{template_name}")
    efd: Var = vf.add_var(name=f"EfdPu_{template_name}")

    tr: Var = vf.add_var(name=f"TR_{template_name}")
    ka: Var = vf.add_var(name=f"KA_{template_name}")
    ta: Var = vf.add_var(name=f"TA_{template_name}")
    tb: Var = vf.add_var(name=f"TB_{template_name}")
    tc: Var = vf.add_var(name=f"TC_{template_name}")
    vrmax: Var = vf.add_var(name=f"VRMAX_{template_name}")
    vrmin: Var = vf.add_var(name=f"VRMIN_{template_name}")
    ke: Var = vf.add_var(name=f"KE_{template_name}")
    te: Var = vf.add_var(name=f"TE_{template_name}")
    kf: Var = vf.add_var(name=f"KF_{template_name}")
    tf1: Var = vf.add_var(name=f"TF1_{template_name}")
    e1: Var = vf.add_var(name=f"E1_{template_name}")
    se1: Var = vf.add_var(name=f"SE1_{template_name}")
    e2: Var = vf.add_var(name=f"E2_{template_name}")
    se2: Var = vf.add_var(name=f"SE2_{template_name}")
    efd0: Var = vf.add_var(name=f"Efd0Pu_{template_name}")
    us0: Var = vf.add_var(name=f"Us0Pu_{template_name}")

    event_dict: dict[Var, Expr | Const] = dict({
        tr: vf.add_const(value=0.01),
        ka: vf.add_const(value=80.0),
        ta: vf.add_const(value=0.04),
        tb: vf.add_const(value=1.0),
        tc: vf.add_const(value=1.0),
        vrmax: vf.add_const(value=7.3),
        vrmin: vf.add_const(value=-7.3),
        ke: vf.add_const(value=1.0),
        te: vf.add_const(value=0.8),
        kf: vf.add_const(value=0.1),
        tf1: vf.add_const(value=1.0),
        e1: vf.add_const(value=0.0),
        se1: vf.add_const(value=0.0),
        e2: vf.add_const(value=0.0),
        se2: vf.add_const(value=0.0),
        efd0: vf.add_const(value=1.0),
        us0: vf.add_const(value=1.0),
    })

    zero: Const = vf.add_const(value=0.0)
    one: Const = vf.add_const(value=1.0)
    eps: Const = vf.add_const(value=1.0e-9)
    huge_limit: Const = vf.add_const(value=999.0)

    # Guard time constants and inactive limits before constructing the continuous equations.
    tr_safe: Expr = sym.max(tr, eps)
    ta_safe: Expr = sym.max(ta, eps)
    tb_safe: Expr = sym.max(tb, eps)
    te_safe: Expr = sym.max(te, eps)
    tf1_safe: Expr = sym.max(tf1, eps)
    tb_active: Expr = sym.heaviside(tb - eps)
    vrmax_active: Expr = sym.heaviside(vrmax - eps)
    vrmax_effective: Expr = vrmax_active * vrmax + (one - vrmax_active) * huge_limit

    sat_root_1: Expr = sym.sqrt(sym.max(se1, zero))
    sat_root_2: Expr = sym.sqrt(sym.max(se2, zero))
    sat_slope: Expr = (sat_root_2 - sat_root_1) / sym.max(e2 - e1, eps)
    sat_slope_safe: Expr = sym.max(sat_slope, eps)
    sat_a: Expr = e1 - sat_root_1 / sat_slope_safe
    sat_b: Expr = sat_slope * sat_slope
    sat_enabled: Expr = sym.heaviside(se2 - eps) * sym.heaviside(e2 - e1 - eps)
    se_expr: Expr = sat_enabled * sat_b * sym.max(int_y - sat_a, zero) ** 2

    vfe_expr: Expr = ke * int_y + se
    wf_y_expr: Expr = (kf / tf1_safe) * (int_y - wf_x)
    vi_expr: Expr = us_ref + upss + uuel - lg_y - wf_y
    ll_y_dynamic: Expr = (tc / tb_safe) * vi + (one - tc / tb_safe) * ll_x
    ll_y_expr: Expr = tb_active * ll_y_dynamic + (one - tb_active) * vi
    vr_expr: Expr = sym.hard_sat(la_y, vrmin, vrmax_effective)

    regulator_raw_dot: Expr = (ka * ll_y - la_y) / ta_safe
    block_upper: Expr = sym.heaviside(la_y - vrmax_effective + eps) * sym.heaviside(regulator_raw_dot)
    block_lower: Expr = sym.heaviside(vrmin - la_y + eps) * sym.heaviside(-regulator_raw_dot)
    regulator_dot: Expr = (one - block_upper) * (one - block_lower) * regulator_raw_dot

    state_eqs: list[Expr] = list([
        (us - lg_y) / tr_safe,
        tb_active * (vi - ll_x) / tb_safe,
        regulator_dot,
        (vr - vfe) / te_safe,
        (int_y - wf_x) / tf1_safe,
    ])

    se0_expr: Expr = sat_enabled * sat_b * sym.max(efd0 - sat_a, zero) ** 2
    vfe0_expr: Expr = ke * efd0 + se0_expr
    vi0_expr: Expr = vfe0_expr / sym.max(ka, eps)

    templ.block = Block(
        state_vars=state_vars,
        state_eqs=state_eqs,
        algebraic_vars=[vi, ll_y, vr, se, vfe, wf_y, efd],
        algebraic_eqs=[
            vi - vi_expr,
            ll_y - ll_y_expr,
            vr - vr_expr,
            se - se_expr,
            vfe - vfe_expr,
            wf_y - wf_y_expr,
            efd - int_y,
        ],
        diff_vars=diff_vars,
        init_eqs={
            upss: zero,
            uuel: zero,
            us: us0,
            us_ref: us0 + vi0_expr,
            lg_y: us0,
            ll_x: vi0_expr,
            la_y: vfe0_expr,
            int_y: efd0,
            wf_x: efd0,
            vi: vi0_expr,
            ll_y: vi0_expr,
            vr: sym.hard_sat(vfe0_expr, vrmin, vrmax_effective),
            se: se0_expr,
            vfe: vfe0_expr,
            wf_y: zero,
            efd: efd0,
        },
        event_dict=event_dict,
        in_vars=inputs,
        out_vars=[efd],
        name=template_name,
    )
    templ.comment = 'Generator AVR/exciter ESDC2A'
    return templ
