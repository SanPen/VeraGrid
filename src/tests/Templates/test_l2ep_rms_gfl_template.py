# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Tests for the L2EP RMS grid-following VSC template."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.renewable_controls.l2ep_rms_gfl_template import get_l2ep_rms_gfl_template


def test_l2ep_template_retains_transformer_current_dynamics() -> None:
    """The L2EP entry must retain the RMS current differential equations.

    :return: ``None``.
    """
    variable_factory: VarFactory = VarFactory()

    # Building verifies that the named L2EP entry exposes the native GFL core.
    template: RmsModelTemplate = get_l2ep_rms_gfl_template(vf=variable_factory)

    total_differential_variables: int = sum(
        len(block.diff_vars) for block in template.block.get_all_blocks()
    )

    assert total_differential_variables >= 2


def test_l2ep_template_latches_pll_blocking_on_voltage_thresholds() -> None:
    """The L2EP PLL must contain its voltage block/restart latch.

    :return: ``None``.
    """
    variable_factory: VarFactory = VarFactory()
    template: RmsModelTemplate = get_l2ep_rms_gfl_template(vf=variable_factory)
    gfl_block = template.block.children[0]
    mode_names: set[str] = set(variable.name for variable in gfl_block.mode_dict)

    assert 'PLL_blocked' in mode_names
    assert len(gfl_block.procedural_logic) == 1
