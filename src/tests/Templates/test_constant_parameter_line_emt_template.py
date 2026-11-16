# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Tests for the Colib constant-parameter line template."""

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.line.constant_parameter_line_emt_template import (
    get_constant_parameter_line_emt_template,
)


def test_constant_parameter_line_has_three_phase_terminal_history() -> None:
    """The Bergeron line must retain a history value at both ends of each phase.

    :return: ``None``.
    """
    variable_factory: VarFactory = VarFactory()
    template: EmtModelTemplate = get_constant_parameter_line_emt_template(vf=variable_factory)
    history_block = template.block.children[0]

    assert len(history_block.event_dict) == 6
