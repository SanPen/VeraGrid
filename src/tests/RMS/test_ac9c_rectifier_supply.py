# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Check AC9C loaded-source rectifier equations and capability limits."""

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_rectifier_supply import (
    Ac9cRectifierSupplySettings,
    build_ac9c_rectifier_supply_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def ac9c_supply_output(block: Block, source: float, ve: float) -> float:
    """Evaluate a channel output at supplied source and exciter voltages.

    :param block: Native rectifier supply channel.
    :param source: Potential-source voltage magnitude.
    :param ve: Exciter field-voltage state.
    :return: Available channel voltage.
    """
    bindings: dict[int, float] = dict()
    for parameter, value in block.event_dict.items():
        if isinstance(value, Const):
            bindings[parameter.uid] = float(value.value)
        else:
            pass
    bindings[block.in_vars[0].uid] = source
    bindings[block.in_vars[1].uid] = ve
    bindings[block.algebraic_vars[0].uid] = 0.0
    return -float(block.algebraic_eqs[0].eval_uid(bindings))


def test_ac9c_rectifier_supply_applies_loading_and_capability() -> None:
    """Apply the PSS/E FEX formula and channel-specific upper bound."""
    block: Block = build_ac9c_rectifier_supply_template(
        VarFactory(), settings=Ac9cRectifierSupplySettings(
            kc=.2, vbmax=.8, source0=.5, ve0=1.0,
        ),
    ).block
    assert ac9c_supply_output(block, .5, 1.0) == pytest.approx(.5 * (1.0 - .577 * .1))
    assert ac9c_supply_output(block, 1.0, 1.0) == pytest.approx(.8)


def test_ac9c_rectifier_supply_is_finite_when_exciter_voltage_collapses() -> None:
    """Use the existing zero-supply loading convention at VE equal to zero."""
    block: Block = build_ac9c_rectifier_supply_template(
        VarFactory(), settings=Ac9cRectifierSupplySettings(
            kc=.2, vbmax=5.0, source0=.5, ve0=1.0,
        ),
    ).block
    assert ac9c_supply_output(block, .5, 0.0) == pytest.approx(.47115)


def test_ac9c_rectifier_supply_rejects_zero_initial_exciter_voltage() -> None:
    """Keep the documented normalized-loading initialization well-defined."""
    with pytest.raises(ValueError, match='requires positive VE'):
        build_ac9c_rectifier_supply_template(
            VarFactory(), settings=Ac9cRectifierSupplySettings(ve0=0.0),
        )
