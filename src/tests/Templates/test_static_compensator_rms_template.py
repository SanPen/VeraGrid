# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Tests for the Colib static-compensator RMS template."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.voltage_compensators.static_compensator_rms_template import (
    get_static_compensator_rms_template,
)


def test_static_compensator_has_reactive_power_equation() -> None:
    """The compensator must expose the fixed-shunt reactive injection.

    :return: ``None``.
    """
    variable_factory: VarFactory = VarFactory()
    template: RmsModelTemplate = get_static_compensator_rms_template(vf=variable_factory)

    assert len(template.block.algebraic_eqs) == 2
