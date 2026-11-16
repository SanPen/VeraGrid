# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Tests for the Colib single-cage induction-motor template."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.induction_machines.single_cage_induction_motor_rms_template import (
    get_single_cage_induction_motor_rms_template,
)


def test_single_cage_motor_uses_the_third_order_reduction() -> None:
    """The Colib entry must remove the duplicated second-cage states.

    :return: ``None``.
    """
    variable_factory: VarFactory = VarFactory()
    template: RmsModelTemplate = get_single_cage_induction_motor_rms_template(vf=variable_factory)
    total_states: int = sum(
        len(block.state_vars) for block in template.block.get_all_blocks()
    )

    assert total_states == 3
