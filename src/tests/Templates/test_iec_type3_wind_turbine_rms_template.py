# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Tests for the composite IEC Type-3 wind-turbine template."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.wind_generation.iec_type3_wind_turbine_rms_template import (
    get_iec_type3_wind_turbine_rms_template,
)


def test_iec_type3_wind_turbine_composes_controls_generator_and_drivetrain() -> None:
    """The composite must expose plant commands and generated electrical/mechanical signals.

    :return: ``None``.
    """
    variable_factory: VarFactory = VarFactory()
    template: RmsModelTemplate = get_iec_type3_wind_turbine_rms_template(vf=variable_factory)

    assert len(template.block.in_vars) == 7
    assert len(template.block.out_vars) == 6
    assert len(template.block.state_vars) > 5
    assert len(template.block.external_mapping) == 2
