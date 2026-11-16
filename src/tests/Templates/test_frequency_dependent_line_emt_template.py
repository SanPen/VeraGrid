# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Tests for the Colib frequency-dependent line template."""

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.line.frequency_dependent_line_emt_template import (
    get_frequency_dependent_line_emt_template,
)


def test_frequency_dependent_line_has_three_phase_norton_history() -> None:
    """The Martí entry must retain Norton history currents for both line ends.

    :return: ``None``.
    """
    variable_factory: VarFactory = VarFactory()
    template: EmtModelTemplate = get_frequency_dependent_line_emt_template(vf=variable_factory)

    assert len(template.block.event_dict) == 6
