# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Executable CGMES ExcSEXS excitation-system model."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def build_exc_s_e_x_s_template(
        vfactory: VarFactory,
        name: str | None = None,
        tc_value: float = 0.0,
) -> RmsModelTemplate:
    """Build the standalone ExcSEXS parameter template.

    :param vfactory: Factory used to allocate the template parameters.
    :param name: Optional runtime model name.
    :param tc_value: Imported T_C, used to remove the PI integrator when disabled.
    :return: Model-specific template retaining this class parameter surface.
    """
    if not math.isfinite(tc_value) or tc_value < 0.0:
        raise ValueError('ExcSEXS T_C must be finite and nonnegative')
    else:
        pass
    template_name: str = 'ExcSEXS' if name is None else name
    template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    template.comment = "CGMES ExcSEXS: voltage error, lead-lag, limited exciter lag, and field output."
    block: Block = Block(name=template_name)

    # CGMES parameters remain event values so imported settings can be edited.
    parameter_names: tuple[str, ...] = ('enabled', 'tatb', 'tb', 'k', 'te', 'emin', 'emax', 'kc', 'tc', 'efdmin', 'efdmax')
    parameters: dict[str, object] = dict()
    for parameter_name in parameter_names:
        variable_name: str = f"ExcSEXS.{parameter_name}_{template_name}"
        parameter_variable = vfactory.add_var(variable_name)
        block.event_dict[parameter_variable] = vfactory.add_const(value=None, name=variable_name)
        parameters[parameter_name] = parameter_variable

    # SEXS 2005 uses voltage error, lead-lag, PI action, gain/lag, then output clipping.
    voltage = vfactory.add_var(f"ExcSEXS.UsPu_{template_name}")
    reference = vfactory.add_var(f"ExcSEXS.UsRefPu_{template_name}")
    stabilizer = vfactory.add_var(f"ExcSEXS.UpssPu_{template_name}")
    field_voltage = vfactory.add_var(f"ExcSEXS.EfdPu_{template_name}")
    lead_lag_state = vfactory.add_var(f"ExcSEXS.LeadLagState_{template_name}")
    exciter_state = vfactory.add_var(f"ExcSEXS.ExciterState_{template_name}")
    lead_lag_output = vfactory.add_var(f"ExcSEXS.LeadLagOutput_{template_name}")
    exciter_input = vfactory.add_var(f"ExcSEXS.ExciterInput_{template_name}")
    voltage_error = reference - voltage + stabilizer
    lead_time = parameters['tatb'] * parameters['tb']
    block.state_vars = list((lead_lag_state, exciter_state))
    block.state_eqs = list((
        (voltage_error - lead_lag_state) / parameters['tb'],
        (parameters['k'] * lead_lag_output - exciter_state) / parameters['te'],
    ))
    if tc_value > 0.0:
        pi_state = vfactory.add_var(f"ExcSEXS.PIState_{template_name}")
        block.state_vars.insert(1, pi_state)
        block.state_eqs.insert(1, lead_lag_output / parameters['tc'])
        block.state_eqs[2] = (
            parameters['k'] * parameters['kc'] * (lead_lag_output + pi_state) - exciter_state
        ) / parameters['te']
    else:
        pass
    block.algebraic_vars = list((lead_lag_output, exciter_input, field_voltage))
    block.algebraic_eqs = list((
        lead_lag_output - (lead_time * voltage_error + (parameters['tb'] - lead_time) * lead_lag_state) / parameters['tb'],
        exciter_input - sym.hard_sat(exciter_state, parameters['emin'], parameters['emax']),
        field_voltage - sym.hard_sat(exciter_input, parameters['efdmin'], parameters['efdmax']),
    ))
    block.in_vars = list((voltage, reference, stabilizer))
    block.out_vars = list((field_voltage,))
    block.init_eqs[lead_lag_state] = voltage_error
    block.init_eqs[exciter_state] = parameters['k'] * voltage_error
    block.init_eqs[stabilizer] = vfactory.add_const(value=0.0, name=f"ExcSEXS.Upss0Pu_{template_name}")
    if tc_value > 0.0:
        block.init_eqs[pi_state] = vfactory.add_const(
            value=0.0,
            name=f"ExcSEXS.PIState0_{template_name}",
        )
    else:
        pass
    template.block.children.append(block)
    template.block.name = template_name
    return template
