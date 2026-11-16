# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Tests for the Colib pi-equivalent line template."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.line.pi_equivalent_line_rms_template import (
    get_pi_equivalent_line_rms_template,
)


def test_pi_equivalent_line_has_four_terminal_current_equations() -> None:
    """The pi line must expose real and imaginary current at both terminals.

    :return: ``None``.
    """
    variable_factory: VarFactory = VarFactory()
    template: RmsModelTemplate = get_pi_equivalent_line_rms_template(vf=variable_factory)

    assert len(template.block.algebraic_eqs) == 4
