# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""IEEE 1981 voltage-regulator current-compensation model (IEEEVC)."""

from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const
from VeraGridEngine.Utils.Symbolic.symbolic import Expr
from VeraGridEngine.Utils.Symbolic.symbolic import Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.enumerations import DeviceType

def build_ieeevc_1981_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """
    Build ``VComp = |Vt + (Rc + j Xc) It|`` in rectangular coordinates.

    :param vf: Variable factory that owns the compensator symbols.
    :type vf: VarFactory
    :param name: Optional runtime instance name.
    :type name: str | None
    :return: Materialized IEEE 1981 current-compensation model.
    :rtype: RmsModelTemplate
    """
    template_name: str
    if name is None:
        template_name: str = 'IEEEVC_1981'
    else:
        template_name: str = name

    # Allocate the externally supplied phasor components before deriving compensation.
    templ: RmsModelTemplate = RmsModelTemplate(name=template_name)
    templ.tpe = DeviceType.GeneratorDevice

    ut_re: Var = vf.add_var(name=f"UtRePu_{template_name}")
    ut_im: Var = vf.add_var(name=f"UtImPu_{template_name}")
    it_re: Var = vf.add_var(name=f"ItRePu_{template_name}")
    it_im: Var = vf.add_var(name=f"ItImPu_{template_name}")
    inputs: list[Var] = list([ut_re, ut_im, it_re, it_im])

    vcomp_re: Var = vf.add_var(name=f"VCompRePu_{template_name}")
    vcomp_im: Var = vf.add_var(name=f"VCompImPu_{template_name}")
    vcomp: Var = vf.add_var(name=f"VCompPu_{template_name}")

    rc: Var = vf.add_var(name=f"RcPu_{template_name}")
    xc: Var = vf.add_var(name=f"XcPu_{template_name}")
    event_dict: dict[Var, Expr | Const] = dict({
        rc: vf.add_const(value=0.0),
        xc: vf.add_const(value=0.0),
    })

    # Apply the documented rectangular complex multiplication before taking magnitude.
    vcomp_re_expr: Expr = ut_re + rc * it_re - xc * it_im
    vcomp_im_expr: Expr = ut_im + rc * it_im + xc * it_re
    vcomp_expr: Expr = sym.sqrt(vcomp_re * vcomp_re + vcomp_im * vcomp_im)

    templ.block = Block(
        algebraic_vars=[vcomp_re, vcomp_im, vcomp],
        algebraic_eqs=[
            vcomp_re - vcomp_re_expr,
            vcomp_im - vcomp_im_expr,
            vcomp - vcomp_expr,
        ],
        init_eqs={
            ut_re: vf.add_const(value=1.0),
            ut_im: vf.add_const(value=0.0),
            it_re: vf.add_const(value=0.0),
            it_im: vf.add_const(value=0.0),
            vcomp_re: vcomp_re_expr,
            vcomp_im: vcomp_im_expr,
            vcomp: vcomp_expr,
        },
        event_dict=event_dict,
        in_vars=inputs,
        out_vars=[vcomp],
        name=template_name,
    )
    templ.comment = 'Generator voltage compensator IEEEVC 1981'
    return templ
