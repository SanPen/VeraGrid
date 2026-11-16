# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Native TGOV3 state, initialization, and plotted valve-flow characteristic."""
from __future__ import annotations

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.governors.tgov3 import (
    Tgov3Parameters,
    build_tgov3_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var


def evaluate_algebraic_output(block: Block, name: str, values: dict[int, float]) -> float:
    """Evaluate a named output equation using explicitly supplied symbol values.

    :param block: Native TGOV3 equation graph.
    :param name: Algebraic variable name.
    :param values: Symbol UID to numeric value bindings.
    :return: Evaluated right-hand side.
    """
    for index, variable in enumerate(block.algebraic_vars):
        if variable.name == name:
            return float(block.algebraic_eqs[index].right.eval_uid(values))
        else:
            pass
    raise AssertionError('TGOV3 algebraic output is missing: ' + name)


def test_tgov3_has_six_ordered_memories_and_steady_initial_power() -> None:
    """Preserve the PSS/E state ordering and generator-base operating point.

    :return: None.
    """
    template = build_tgov3_template(
        VarFactory(),
        parameters=Tgov3Parameters(t1=.02, ti=2.0, ta=.1, tb=.3, tc=.8),
    )
    block: Block = template.block
    assert tuple(variable.name for variable in block.state_vars) == (
        'TGOV3SpeedFilterPu_TGOV3',
        'TGOV3GovernorOutputPu_TGOV3',
        'TGOV3TurbineT4Pu_TGOV3',
        'TGOV3ReheatIntegratorPu_TGOV3',
        'TGOV3TurbineT6Pu_TGOV3',
        'TGOV3InterceptValvePositionPu_TGOV3',
    )
    assert len(block.state_eqs) == 6
    assert tuple(variable.name for variable in block.in_vars) == (
        'SpeedDeviationPu_TGOV3', 'ReferencePu_TGOV3',
    )
    initial_power: Const = block.init_eqs[block.out_vars[0]]
    assert isinstance(initial_power, Const)
    assert initial_power.value == pytest.approx(.8)


def test_tgov3d_applies_the_asymmetric_speed_deadband() -> None:
    """Apply DBH/DBL to speed deviation before the governor speed filter.

    :return: None.
    """
    template = build_tgov3_template(
        VarFactory(),
        parameters=Tgov3Parameters(deadband_high=.05, deadband_low=-.04),
    )
    block: Block = template.block
    speed: Var = block.in_vars[0]
    parameter_values: dict[int, float] = dict(
        (parameter.uid, float(expression.value))
        for parameter, expression in block.event_dict.items()
    )
    cases: tuple[tuple[float, float], ...] = (
        (-.10, -.06), (-.02, 0.0), (.02, 0.0), (.08, .03),
    )
    for input_speed, expected in cases:
        values: dict[int, float] = dict(parameter_values)
        values[speed.uid] = input_speed
        assert evaluate_algebraic_output(
            block, 'ControlledSpeedDeviationPu_TGOV3', values,
        ) == pytest.approx(expected)


@pytest.mark.parametrize(
    ('position', 'expected_flow'),
    ((0.0, 0.0), (0.3, 0.8), (0.65, 0.9), (1.0, 1.0)),
)
def test_tgov3_plotted_intercept_valve_flow_points(
        position: float,
        expected_flow: float,
) -> None:
    """Match the PSS/E 33.10 figure endpoints and its marked interior point.

    :param position: Intercept valve position in pu.
    :param expected_flow: Flow read from the source chart in pu.
    :return: None.
    """
    template = build_tgov3_template(VarFactory())
    block: Block = template.block
    valve: Var = next(
        variable for variable in block.state_vars
        if variable.name == 'TGOV3InterceptValvePositionPu_TGOV3'
    )
    assert evaluate_algebraic_output(
        block,
        'TGOV3ValveFlowPu_TGOV3',
        {valve.uid: position},
    ) == pytest.approx(expected_flow)


@pytest.mark.parametrize(
    'parameters',
    (
        Tgov3Parameters(k=0.0),
        Tgov3Parameters(t1=0.0, t2=.1),
        Tgov3Parameters(uc=0.0),
        Tgov3Parameters(ta=.4, tb=.3),
        Tgov3Parameters(k1=.2, k2=.2, k3=.2),
    ),
)
def test_tgov3_rejects_invalid_source_constants(parameters: Tgov3Parameters) -> None:
    """Reject invalid source time, rate, and power-fraction combinations.

    :param parameters: Deliberately invalid TGOV3 settings.
    :return: None.
    """
    with pytest.raises(ValueError):
        build_tgov3_template(VarFactory(), parameters=parameters)
