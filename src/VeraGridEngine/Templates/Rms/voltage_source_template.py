# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import DeviceType, VarPowerFlowReferenceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Utils.Symbolic.block import Block
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def VoltageSourceBuild(
    vfactory: VarFactory,
    name: str = "",
) -> RmsModelTemplate:
    """
    Build an RMS voltage-source template with P/Q capability limits.

    Control logic:
    - Q within limits  -> enforce Vm = Vg0
    - Q at limit       -> enforce Q = clamp(Q, Qmin_G, Qmax_G)
    - P within limits  -> enforce Va = Ag0
    - P at limit       -> enforce P = clamp(P, Pmin_G, Pmax_G)
    """
    templ = RmsModelTemplate()
    templ.tpe = DeviceType.ExternalGridDevice

    Vm = vfactory.add_var("Vm", VarPowerFlowReferenceType.Vm)
    Va = vfactory.add_var("Va", VarPowerFlowReferenceType.Va)
    inputs = [Vm, Va]

    P = vfactory.add_var("P")
    Q = vfactory.add_var("Q")

    Vg0 = vfactory.add_var("Vg0")
    Ag0 = vfactory.add_var("Ag0")

    Pmax_G = vfactory.add_var("Pmax_G")
    Pmin_G = vfactory.add_var("Pmin_G")
    Qmax_G = vfactory.add_var("Qmax_G")
    Qmin_G = vfactory.add_var("Qmin_G")

    event_dict = {
        Vg0: vfactory.add_const(None),
        Ag0: vfactory.add_const(None),
        Pmax_G: vfactory.add_const(9.999),
        Pmin_G: vfactory.add_const(-9.999),
        Qmax_G: vfactory.add_const(9.999),
        Qmin_G: vfactory.add_const(-9.999),
    }

    init_eqs = {
        Vg0: Vm,
        Ag0: Va,
    }

    p_within_limits = ((Pmax_G - P) >= 0).to_expression() * (0 <= (P - Pmin_G)).to_expression()
    q_within_limits = ((Qmax_G - Q) >= 0).to_expression() * (0 <= (Q - Qmin_G)).to_expression()

    p_sat = sym.max(Pmin_G, sym.min(P, Pmax_G))
    q_sat = sym.max(Qmin_G, sym.min(Q, Qmax_G))

    templ.block = Block(
        algebraic_eqs=[
            (Va - Ag0) * p_within_limits + (P - p_sat) * (1 - p_within_limits),
            (Vm - Vg0) * q_within_limits + (Q - q_sat) * (1 - q_within_limits),
        ],
        algebraic_vars=[P, Q],
        init_eqs=init_eqs,
        event_dict=event_dict,
    )

    templ.block.name = "Voltage Source"
    templ.block.external_mapping = {
        VarPowerFlowReferenceType.P: P,
        VarPowerFlowReferenceType.Q: Q,
        VarPowerFlowReferenceType.Vm: Vm,
        VarPowerFlowReferenceType.Va: Va,
    }
    templ.block.in_vars = inputs

    return templ
