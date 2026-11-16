# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Published block-diagram checks for the WTARA1 aerodynamic stage."""

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.renewable_controls.wtara1_aerodynamic import (
    Wtara1AerodynamicSettings,
    build_wtara1_aerodynamic_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def test_wtara1_pitch_product_preserves_initial_mechanical_power() -> None:
    """Evaluate the two-angle product and its equilibrium pitch point.

    :return: None.
    """
    block: Block = build_wtara1_aerodynamic_template(
        vf=VarFactory(), settings=Wtara1AerodynamicSettings(ka=.007, theta0=2.),
    ).block
    bindings: dict[int, float] = dict()
    parameter: Var
    value: Expr
    for parameter, value in block.event_dict.items():
        if isinstance(value, Const):
            bindings[parameter.uid] = float(value.value)
        else:
            pass
    bindings[block.in_vars[0].uid] = 2.
    bindings[block.in_vars[1].uid] = .5
    bindings[block.out_vars[0].uid] = 0.
    assert -block.algebraic_eqs[0].eval_uid(bindings) == pytest.approx(.5)
    bindings[block.in_vars[0].uid] = 5.
    assert -block.algebraic_eqs[0].eval_uid(bindings) == pytest.approx(.395)
    bindings[block.in_vars[0].uid] = 1.
    assert -block.algebraic_eqs[0].eval_uid(bindings) == pytest.approx(.507)


def test_wtara1_rejects_invalid_gain_and_initial_pitch() -> None:
    """Reject nonphysical source settings before construction.

    :return: None.
    """
    with pytest.raises(ValueError, match='pitch gain'):
        build_wtara1_aerodynamic_template(
            vf=VarFactory(), settings=Wtara1AerodynamicSettings(ka=0.),
        )
    with pytest.raises(ValueError, match='initial angle'):
        build_wtara1_aerodynamic_template(
            vf=VarFactory(), settings=Wtara1AerodynamicSettings(theta0=-1.),
        )
