# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Construction checks for the Colib GENTPJ template."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.synchronous_machines.gentpj import (
    build_gentpj_template,
)


def test_gentpj_has_the_six_machine_states() -> None:
    """Ensure GENTPJ delegates to the native subtransient machine core."""
    variable_factory: VarFactory = VarFactory()
    template: RmsModelTemplate = build_gentpj_template(vf=variable_factory)

    assert len(template.block.children[0].state_vars) == 6


def test_gentpj_exposes_the_stator_current_saturation_gain() -> None:
    """GENTPJ must expose the Colib parameter that differentiates GENTPF.

    :return: ``None``.
    """
    variable_factory: VarFactory = VarFactory()
    template: RmsModelTemplate = build_gentpj_template(vf=variable_factory)
    parameter_names: set[str] = set(
        parameter.name for parameter in template.block.children[0].event_dict
    )

    assert 'K_is' in parameter_names
