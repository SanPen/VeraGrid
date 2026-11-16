# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""CGMES IEEE reactive-power controller Type II equations."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def build_p_f_v_ar_type2_i_e_e_e_v_ar_controller_template(
        vfactory: VarFactory,
        name: str | None = None,
        qref: float = 0.0,
        vref: float = 1.0,
        vclmt: float = 0.1,
        kp: float = 0.02,
        ki: float = 2.0,
        vs: float = 1.0,
        exlon: bool = True,
) -> RmsModelTemplate:
    """Build the IEEE 421.5 Type II reactive-power PI loop.

    :param vfactory: Factory used to allocate the controller symbols.
    :param name: Optional runtime model name.
    :param qref: Canonical reactive-power setpoint.
    :param vref: Canonical voltage-reference operating point.
    :param vclmt: Symmetric voltage-reference correction limit.
    :param kp: Proportional gain.
    :param ki: Integral gain.
    :param vs: Canonical generator sensing-voltage parameter retained as metadata.
    :param exlon: Whether excitation limiters permit integral action.
    :return: Load-flow reference plus bounded Q correction with limiter-gated integration.
    """
    template_name: str = 'PFVArType2IEEEVArController' if name is None else name
    if vclmt <= 0.0 or kp < 0.0 or ki < 0.0:
        raise ValueError('Type II VAr controller requires positive VCLMT and nonnegative gains')
    else:
        pass
    model: ControlRealization = ControlRealization(vfactory, template_name)
    model.parameter('PFVArType2IEEEVArController.enabled', 1.0)
    reactive_reference: Var = model.parameter('PFVArType2IEEEVArController.qref', qref)
    regulator_reference: Var = model.parameter('PFVArType2IEEEVArController.vref', vref)
    output_limit: Var = model.parameter('PFVArType2IEEEVArController.vclmt', vclmt)
    proportional_gain: Var = model.parameter('PFVArType2IEEEVArController.kp', kp)
    integral_gain: Var = model.parameter('PFVArType2IEEEVArController.ki', ki)
    model.parameter('PFVArType2IEEEVArController.vs', vs)
    integration_enable: Var = model.parameter('PFVArType2IEEEVArController.exlon', float(exlon))
    reactive_power: Var = model.input('QPu', Const(0.0))
    error: Expr = reactive_reference - reactive_power

    # IEEE Type II disables integral accumulation while an excitation limiter is active.
    integral_state: Var = vfactory.add_var(f'IntegralStatePu_{template_name}')
    model.differential(
        integral_state,
        integration_enable * integral_gain * error,
        -proportional_gain * error,
        -output_limit - proportional_gain * error,
        output_limit - proportional_gain * error,
    )
    controller_correction: Expr = proportional_gain * error + integral_state
    controller_output: Var = model.algebraic(
        'VVARPu',
        regulator_reference + sym.hard_sat(controller_correction, -output_limit, output_limit),
        regulator_reference,
    )
    return model.finish((controller_output,), 'IEEE 421.5-2005 Figure 11-5 VAr Type II PI controller')
