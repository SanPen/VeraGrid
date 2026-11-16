# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""CGMES PFVAr Type 2 common PI controller equations."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def build_p_f_v_ar_type2_common1_template(
        vfactory: VarFactory,
        name: str | None = None,
) -> RmsModelTemplate:
    """Build the EA1390 selectable reactive-power/power-factor PI controller.

    :param vfactory: Factory that owns the equation variables.
    :param name: Optional runtime template name.
    :return: Controller with reactive-power and power-factor inputs and a bounded output.
    """
    template_name: str = 'PFVArType2Common1' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    selector: Var = model.parameter('PFVArType2Common1.j', 0.0)
    proportional_gain: Var = model.parameter('PFVArType2Common1.kp', 0.0)
    integral_gain: Var = model.parameter('PFVArType2Common1.ki', 0.0)
    maximum_output: Var = model.parameter('PFVArType2Common1.max', 0.0)
    reference: Var = model.parameter('PFVArType2Common1.ref', 0.0)
    # The EA selector chooses reactive-power feedback when true and power-factor feedback otherwise.
    reactive_power: Var = model.input('QPu', Const(0.0))
    power_factor: Var = model.input('PowerFactorPu', Const(1.0))
    selected_feedback: Expr = selector * reactive_power + (Const(1.0) - selector) * power_factor
    error: Expr = reference - selected_feedback

    # The diagram places an integrator in parallel with proportional gain before the symmetric clamp.
    integral_state: Var = vfactory.add_var(f'IntegralStatePu_{template_name}')
    integral_derivative: Var = vfactory.add_diff_var(
        f'd_IntegralStatePu_{template_name}',
        base_var=integral_state,
    )
    model.block.state_vars.append(integral_state)
    model.block.diff_vars.append(integral_derivative)
    model.block.state_eqs.append(integral_derivative - integral_gain * error)
    # Cancel the proportional term at the construction operating point so VsPu starts at zero.
    model.block.init_eqs[integral_state] = -proportional_gain * error
    unclamped_output: Expr = proportional_gain * error + integral_state
    output: Var = model.algebraic(
        'VsPu',
        sym.hard_sat(unclamped_output, -maximum_output, maximum_output),
        Const(0.0),
    )
    return model.finish((output,), 'CGMES EA1390 PF/VAr selectable PI controller')
