# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Construction checks for the Colib flywheel RMS template."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.synchronous_machines.flywheel_rms_template import get_flywheel_rms_template


def test_flywheel_has_soc_state() -> None:
    """Ensure the flywheel exposes the Colib storage state."""
    variable_factory: VarFactory = VarFactory()
    template: RmsModelTemplate = get_flywheel_rms_template(vf=variable_factory)
    names: set[str] = set(
        variable.name for variable in template.block.children[0].state_vars
    )

    assert 'Soc' in names


def test_flywheel_has_a_configurable_soc_loss_curve() -> None:
    """Ensure the Colib standing-loss term is configurable.

    :return: ``None``.
    """
    variable_factory: VarFactory = VarFactory()
    template: RmsModelTemplate = get_flywheel_rms_template(vf=variable_factory)
    parameter_names: set[str] = set(
        parameter.name for parameter in template.block.children[0].parameters
    )

    assert 'P_loss_coeff' in parameter_names
