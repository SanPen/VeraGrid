# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Tests for the Colib WECC rotor-flux motor template."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.induction_machines.wecc_rotor_flux_induction_motor_rms_template import (
    get_wecc_rotor_flux_induction_motor_rms_template,
)


def test_wecc_motor_uses_the_fifth_order_flux_state_set() -> None:
    """The WECC entry must retain four flux and one rotor-speed state.

    :return: ``None``.
    """
    variable_factory: VarFactory = VarFactory()
    template: RmsModelTemplate = get_wecc_rotor_flux_induction_motor_rms_template(
        vf=variable_factory,
    )
    total_states: int = sum(
        len(block.state_vars) for block in template.block.get_all_blocks()
    )

    assert total_states == 5
