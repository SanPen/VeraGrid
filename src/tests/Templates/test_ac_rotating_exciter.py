# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Tests for the Colib AC rotating-exciter template."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.excitation_systems.ac_rotating_exciter import (
    build_ac_rotating_exciter_template,
)


def test_ac_rotating_exciter_exposes_field_outputs_and_state() -> None:
    """The Colib submodel must expose the two outputs and exciter state.

    :return: ``None``.
    """
    variable_factory: VarFactory = VarFactory()
    template: RmsModelTemplate = build_ac_rotating_exciter_template(vf=variable_factory)
    block = template.block

    assert len(block.out_vars) == 2
    assert len(block.state_vars) == 1
