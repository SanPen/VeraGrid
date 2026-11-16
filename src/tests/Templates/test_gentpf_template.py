# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Tests for the Colib GENTPF machine template."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.synchronous_machines.gentpf import (
    build_gentpf_template,
)


def test_gentpf_has_the_round_rotor_state_set() -> None:
    """GENTPF must retain the native six-state saturated machine dynamics.

    :return: ``None``.
    """
    variable_factory: VarFactory = VarFactory()
    template: RmsModelTemplate = build_gentpf_template(vf=variable_factory)

    assert len(template.block.children[0].state_vars) == 6
