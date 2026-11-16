# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Colib flywheel storage RMS template."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.battery_energy_storage.esd1_rms_template import get_esd1_rms_template


def get_flywheel_rms_template(vf: VarFactory, name: str = 'Flywheel') -> RmsModelTemplate:
    """Build the Colib flywheel state-of-charge storage model.

    The native storage core provides the required energy state, separate charge
    and discharge efficiencies, active-power direction convention, and output
    power limits. Its capacity and efficiency parameters represent Colib's
    ``Emax`` and ``eta`` functions. Colib leaves the SOC loss curve open, so
    this entry supplies a configurable linear loss coefficient as the default
    realization, which can be replaced by a fitted curve when data is present.

    :param vf: Variable factory used to allocate symbolic variables.
    :param name: Unique template instance name.
    :return: RMS flywheel storage template.
    """
    template: RmsModelTemplate = get_esd1_rms_template(vfactory=vf, name=name)
    storage_block = template.block.children[0]
    loss_power_coefficient = vf.add_var('P_loss_coeff')
    energy_capacity_hours = next(
        parameter for parameter in storage_block.parameters if parameter.name == 'ecap_h'
    )

    # Add the Colib SOC-dependent standing loss to the native storage balance.
    storage_block.state_eqs[2] = storage_block.state_eqs[2] - (
        loss_power_coefficient * storage_block.state_vars[2]
        / (energy_capacity_hours * vf.add_const(3600.0))
    )
    storage_block.parameters[loss_power_coefficient] = vf.add_const(0.0)
    template.comment = 'Colib flywheel SOC storage realization with linear SOC loss'
    return template
