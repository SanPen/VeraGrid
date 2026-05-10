# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.enumerations import DeviceType, VarPowerFlowRefferenceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.block_helpers import tf_to_block


def FrequencyLoadBuild(vfactory: VarFactory, name: str = "", Pl0=1.0, Ql0=0.1) -> RmsModelTemplate:
    """
     generator with quadratic saturation
    """
    templ = RmsModelTemplate()
    templ.tpe = DeviceType.LoadDevice
    inputs = [vfactory.add_var("Vm_"), vfactory.add_var('Va_')]

    # Vars:
    m = vfactory.add_var('m')
    P = vfactory.add_var('P')
    Q = vfactory.add_var('Q')
    Va = inputs[1]

    # Parameters:
    P0 = vfactory.add_var('Pl0')
    Q0 = vfactory.add_var('Ql0')
    V0 = vfactory.add_var('V0')
    Kd = vfactory.add_var('Kd')
    Ki = vfactory.add_var('Ki')
    alpha_p = vfactory.add_var('alpha_p')
    alpha_q = vfactory.add_var('alpha_q')
    beta_p = vfactory.add_var('beta_p')
    beta_q = vfactory.add_var('beta_q')
    Tf = vfactory.add_var('Tf')
    theta0 = vfactory.add_var('theta0')

    block1, d_omega = tf_to_block(
        vfactory,
        num=[0, vfactory.add_const(1)],
        den=[vfactory.add_const(1), Tf],
        x=(Va - theta0),
        name="frequency_measure"

    )
    # ZIP coefficients (classic formulation)
    event_dict = {
        P0: vfactory.add_const(Pl0),
        Q0: vfactory.add_const(Ql0),
        V0: vfactory.add_const(None),

        # Exponential Parameters
        alpha_p: vfactory.add_const(1.2),
        alpha_q: vfactory.add_const(1.2),
        beta_p: vfactory.add_const(1.2),
        beta_q: vfactory.add_const(1.2),

        Tf: vfactory.add_const(0.1),
        theta0: vfactory.add_const(None),
    }

    init_eqs = {
        V0: inputs[0],
        theta0: inputs[1],
        P: P0,
        Q: Q0,
    }
    templ.block = Block(
        algebraic_eqs=[
            P - P0 * (inputs[0]) ** alpha_p * (vfactory.add_const(1) + d_omega) ** beta_p,
            Q - Q0 * (inputs[0]) ** alpha_q * (vfactory.add_const(1) + d_omega) ** beta_q,
        ],
        algebraic_vars=[P, Q],
        init_eqs=init_eqs,
        event_dict=event_dict,
        children=[block1, ]
    )

    templ.block.external_mapping = {
        VarPowerFlowRefferenceType.P: P,
        VarPowerFlowRefferenceType.Q: Q,
        VarPowerFlowRefferenceType.Vm: inputs[0],
    }

    templ.block.in_vars = inputs

    return templ
