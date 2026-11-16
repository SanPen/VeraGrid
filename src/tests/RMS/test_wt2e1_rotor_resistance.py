# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Source-equation checks for the WT2E1 rotor-resistance controller."""

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.renewable_controls.wt2e1_rotor_resistance import (
    Wt2e1Settings,
    build_wt2e1_rotor_resistance_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def _parameter_bindings(block: Block) -> dict[int, float]:
    """Bind WT2E1 source constants for direct equation checks.

    :param block: WT2E1 symbolic block.
    :return: UID-to-scalar parameter values.
    """
    bindings: dict[int, float] = dict()
    parameter: Var
    value: Expr
    for parameter, value in block.event_dict.items():
        if isinstance(value, Const):
            bindings[parameter.uid] = float(value.value)
        else:
            pass
    return bindings


def test_wt2e1_power_slip_symmetry_and_bounded_pi() -> None:
    """Interpolate both slip signs, initialize the offset and stop windup.

    :return: None.
    """
    block: Block = build_wt2e1_rotor_resistance_template(
        VarFactory(), settings=Wt2e1Settings(tsp=0., tpe=0., rotrv_max=.2),
    ).block
    assert len(block.state_vars) == 1
    assert len(block.in_vars) == 3
    assert len(block.event_dict) == 16
    bindings: dict[int, float] = _parameter_bindings(block)
    speed: Var = block.in_vars[0]
    power: Var = block.in_vars[1]
    offset: Var = block.in_vars[2]
    resistance: Var = block.out_vars[0]
    filtered_speed: Var = block.out_vars[1]
    filtered_power: Var = block.out_vars[2]
    integral: Var = block.state_vars[0]
    bindings[speed.uid] = 1.02
    bindings[power.uid] = .9988
    bindings[offset.uid] = 0.
    bindings[filtered_speed.uid] = 1.02
    bindings[filtered_power.uid] = .9988
    bindings[integral.uid] = .02
    bindings[resistance.uid] = .12
    assert block.algebraic_eqs[-1].eval_uid(bindings) == pytest.approx(0.)
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(.1)
    bindings[speed.uid] = .98
    bindings[power.uid] = -.7988
    bindings[filtered_speed.uid] = .98
    bindings[filtered_power.uid] = -.7988
    assert block.algebraic_eqs[-1].eval_uid(bindings) == pytest.approx(0.)
    bindings[integral.uid] = .15
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(0.)
    bindings[speed.uid] = 1.03
    bindings[power.uid] = .8994
    bindings[filtered_speed.uid] = 1.03
    bindings[filtered_power.uid] = .8994
    bindings[integral.uid] = .02
    bindings[resistance.uid] = .02
    assert block.algebraic_eqs[-1].eval_uid(bindings) == pytest.approx(0.)
    bindings[speed.uid] = 1.2
    bindings[power.uid] = .905
    bindings[filtered_speed.uid] = 1.2
    bindings[filtered_power.uid] = .905
    assert block.algebraic_eqs[-1].eval_uid(bindings) == pytest.approx(0.)


def test_wt2e1_three_states_and_operating_point_offset() -> None:
    """Keep the source's three memories and balance a nonzero initial point.

    :return: None.
    """
    block: Block = build_wt2e1_rotor_resistance_template(
        VarFactory(), settings=Wt2e1Settings(
            initial_speed=1.02, initial_power=.9, initial_fraction=.05,
        ),
    ).block
    assert len(block.state_vars) == 3
    assert block.in_vars[2].name.startswith('PowerCurveOffsetPu_')
    bindings: dict[int, float] = _parameter_bindings(block)
    assert block.init_eqs[block.in_vars[2]].eval_uid(bindings) == pytest.approx(.0012)


@pytest.mark.parametrize('settings', (
    Wt2e1Settings(ti=0.),
    Wt2e1Settings(tsp=-.01),
    Wt2e1Settings(rotrv_max=0.),
    Wt2e1Settings(initial_fraction=2.),
    Wt2e1Settings(curve=((.001, .01), (.0054, .0217), (.02, .8988), (.04, .9), (.1, .905))),
    Wt2e1Settings(curve=((0., 0.), (.02, .1), (.01, .2), (.04, .3), (.1, .4))),
))
def test_wt2e1_rejects_invalid_source_or_host_values(settings: Wt2e1Settings) -> None:
    """Reject singular controller settings and unordered machine curve points.

    :param settings: Invalid source or initial host data.
    :return: None.
    """
    with pytest.raises(ValueError):
        build_wt2e1_rotor_resistance_template(VarFactory(), settings=settings)
