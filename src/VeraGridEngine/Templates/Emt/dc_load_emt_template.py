# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can see it at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0



from VeraGridEngine.enumerations import DeviceType, ParamPowerFlowReferenceType, VarPowerFlowReferenceType
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Utils.Symbolic.block import Var

"""
EMT DC load template.

The load follows the EMT injection convention used by the rest of the
framework: current and power are positive when entering the bus. A consuming DC
load therefore has negative ``i_dc`` and negative ``p_dc``.
"""

def get_dc_load_emt_template(
    vf: VarFactory,
    name: str = "dc_load_emt_template"
) -> EmtModelTemplate:
    """
    Build an EMT DC load model.

    Static parameters are provided through ``api_obj_mapping`` using the
    associated load device.

    Args:
        vf: Variable factory
        name: Name for the model

    Returns:
        EmtModelTemplate with the DC load block
    """
    templ = EmtModelTemplate()
    templ.tpe = DeviceType.LoadDevice
    templ.name = name

    templ.block.name = name

    p_dc_static = vf.add_var(name=f"Pl0_{name}")
    g_dc_static = vf.add_var(name=f"g_{name}")
    templ.block.parameters[p_dc_static] = vf.add_const(0.0)
    templ.block.parameters[g_dc_static] = vf.add_const(0.0)

    v_dc = vf.add_var(name=f"v_dc_{name}", reference=VarPowerFlowReferenceType.Vdc)

    i_dc = vf.add_var(name=f"i_dc_{name}", reference=VarPowerFlowReferenceType.Idc)
    p_dc = vf.add_var(name=f"p_dc_{name}", reference=VarPowerFlowReferenceType.P)

    templ.block.in_vars = [v_dc]
    templ.block.algebraic_vars = [i_dc, p_dc]

    eps = vf.add_const(1e-10)
    templ.block.algebraic_eqs = [
        i_dc + p_dc_static / (v_dc + eps) + g_dc_static * v_dc,
        p_dc - v_dc * i_dc,
    ]

    templ.block.out_vars = [i_dc]

    templ.block.external_mapping = {
        VarPowerFlowReferenceType.Vdc: v_dc,
        VarPowerFlowReferenceType.Idc: i_dc,
        VarPowerFlowReferenceType.P: p_dc,
    }

    templ.block.api_obj_mapping = {
        ParamPowerFlowReferenceType.Pl0: p_dc_static,
        ParamPowerFlowReferenceType.g: g_dc_static,
    }

    templ.block.init_eqs = {
        i_dc: -(p_dc_static / (v_dc + eps) + g_dc_static * v_dc),
        p_dc: -v_dc * (p_dc_static / (v_dc + eps) + g_dc_static * v_dc),
    }

    return templ


