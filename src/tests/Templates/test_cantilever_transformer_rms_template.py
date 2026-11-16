# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Tests for the Colib cantilever transformer template."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.transformers.cantilever_transformer_rms_template import (
    get_cantilever_transformer_rms_template,
)


def test_cantilever_transformer_has_terminal_power_equations() -> None:
    """The steady-state transformer must expose all four terminal powers.

    :return: ``None``.
    """
    variable_factory: VarFactory = VarFactory()
    template: RmsModelTemplate = get_cantilever_transformer_rms_template(vf=variable_factory)

    assert len(template.block.children[0].algebraic_eqs) == 4
