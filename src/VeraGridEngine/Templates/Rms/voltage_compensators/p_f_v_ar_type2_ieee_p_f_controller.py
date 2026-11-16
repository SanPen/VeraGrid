# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""CGMES IEEE PF controller Type II equations."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def build_p_f_v_ar_type2_i_e_e_e_p_f_controller_template(
        vfactory: VarFactory,
        name: str | None = None,
        pfref: float = 1.0,
        vref: float = 1.0,
        vclmt: float = 0.1,
        kp: float = 0.02,
        ki: float = 2.0,
        vs: float = 1.0,
        exlon: bool = True,
) -> RmsModelTemplate:
    """Build the IEEE 421.5 Type II power-factor PI loop.

    :param vfactory: Factory used to allocate the controller symbols.
    :param name: Optional runtime model name.
    :param pfref: Canonical signed power-factor-angle setpoint.
    :param vref: Canonical voltage-reference operating point.
    :param vclmt: Symmetric voltage-reference correction limit.
    :param kp: Proportional gain.
    :param ki: Integral gain.
    :param vs: Canonical generator sensing-voltage parameter retained as metadata.
    :param exlon: Whether excitation limiters permit integral action.
    :return: Load-flow reference plus bounded PF correction with limiter-gated integration.
    """
    template_name: str = 'PFVArType2IEEEPFController' if name is None else name
    if vclmt <= 0.0 or kp < 0.0 or ki < 0.0:
        raise ValueError('Type II PF controller requires positive VCLMT and nonnegative gains')
    else:
        pass
    model: ControlRealization = ControlRealization(vfactory, template_name)
    model.parameter('PFVArType2IEEEPFController.enabled', 1.0)
    pf_reference: Var = model.parameter('PFVArType2IEEEPFController.pfref', pfref)
    regulator_reference: Var = model.parameter('PFVArType2IEEEPFController.vref', vref)
    output_limit: Var = model.parameter('PFVArType2IEEEPFController.vclmt', vclmt)
    proportional_gain: Var = model.parameter('PFVArType2IEEEPFController.kp', kp)
    integral_gain: Var = model.parameter('PFVArType2IEEEPFController.ki', ki)
    model.parameter('PFVArType2IEEEPFController.vs', vs)
    integration_enable: Var = model.parameter('PFVArType2IEEEPFController.exlon', float(exlon))
    power_factor: Var = model.input('PFpu', Const(1.0))
    error: Expr = pf_reference - power_factor

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
        'VPFPu',
        regulator_reference + sym.hard_sat(controller_correction, -output_limit, output_limit),
        regulator_reference,
    )
    return model.finish((controller_output,), 'IEEE 421.5-2005 Figure 11-4 PF Type II PI controller')
