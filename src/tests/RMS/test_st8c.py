# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Native PSS/E ST8C structure and selector coverage."""
from __future__ import annotations

import pytest

from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.excitation_systems.st8c import (
    St8cLimiterLocation,
    St8cParameters,
    build_st8c_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_rectifier_sources import (
    Ac9cPotentialSourceSelection,
)


def test_st8c_preserves_five_source_states_and_public_signals() -> None:
    """Expose the five PSS/E memories and complete host/source interface.

    :return: None.
    """
    template = build_st8c_template(VarFactory())
    block = template.block

    assert len(block.state_vars) == 5
    assert len(block.in_vars) == 10
    assert len(block.out_vars) == 6
    assert any('SensedVoltagePu' in state.name for state in block.state_vars)
    assert any('PIDIntegratorPu' in state.name for state in block.state_vars)
    assert any('CurrentRegulatorIntegratorPu' in state.name for state in block.state_vars)
    assert any('VAPu' in state.name for state in block.state_vars)
    assert any('FilteredFeedbackPu' in state.name for state in block.state_vars)


@pytest.mark.parametrize(
    'source_selection,oel_location,uel_location',
    (
        (Ac9cPotentialSourceSelection.TERMINAL_FED,
         St8cLimiterLocation.SUMMATION, St8cLimiterLocation.SUMMATION),
        (Ac9cPotentialSourceSelection.INDEPENDENT,
         St8cLimiterLocation.TAKEOVER_GATE, St8cLimiterLocation.SUMMATION),
        (Ac9cPotentialSourceSelection.TERMINAL_FED,
         St8cLimiterLocation.SUMMATION, St8cLimiterLocation.TAKEOVER_GATE),
    ),
)
def test_st8c_builds_documented_source_and_limiter_positions(
        source_selection: Ac9cPotentialSourceSelection,
        oel_location: St8cLimiterLocation,
        uel_location: St8cLimiterLocation,
) -> None:
    """Build both SW1 source modes and the documented separate gate choices.

    :param source_selection: Terminal-fed or independent potential source.
    :param oel_location: Additive or low-value limiter insertion.
    :param uel_location: Additive or high-value limiter insertion.
    :return: None.
    """
    template = build_st8c_template(
        VarFactory(), source_selection=source_selection,
        oel_location=oel_location, uel_location=uel_location,
    )

    assert len(template.block.state_vars) == 5
    assert len(template.block.in_vars) == 10


def test_st8c_rejects_invalid_constants_and_selectors() -> None:
    """Reject invalid physical bounds and undefined source selector positions.

    :return: None.
    """
    with pytest.raises(ValueError, match='bounds must be ordered'):
        St8cParameters(vpimax=-5.0, vpimin=5.0)
    with pytest.raises(ValueError, match='SW1 source selection'):
        build_st8c_template(VarFactory(), source_selection=object())


def test_st8c_connected_equilibrium_satisfies_all_five_states() -> None:
    """Check field-current, bridge and source states at a nominal point.

    :return: None.
    """
    block: Block = build_st8c_template(VarFactory()).block
    bindings: dict[int, float] = dict()
    input_values: tuple[float, ...] = (1.0, 1.0, 0.0, 0.0, 0.0,
                                       1.0, 1.0, 0.0, 0.0, 0.0)
    state_values: tuple[float, ...] = (1.0, 1.05, 1.0, 1.0, 0.05)
    for variable, value in zip(block.in_vars, input_values):
        bindings[variable.uid] = value
    for variable, value in zip(block.state_vars, state_values):
        bindings[variable.uid] = value
    parameter: Var
    expression: Expr
    for parameter, expression in block.event_dict.items():
        if isinstance(expression, Const):
            bindings[parameter.uid] = float(expression.value)
        else:
            pass
    for variable, equation in zip(block.algebraic_vars, block.algebraic_eqs):
        bindings[variable.uid] = equation.right.eval_uid(bindings)

    assert all(equation.eval_uid(bindings) == pytest.approx(0.0)
               for equation in block.state_eqs)
    assert all(equation.eval_uid(bindings) == pytest.approx(0.0)
               for equation in block.algebraic_eqs)
    assert bindings[block.out_vars[0].uid] == pytest.approx(1.001)
    assert bindings[block.out_vars[1].uid] == pytest.approx(1.05)


def test_st8c_rectifier_channels_load_from_field_current_and_own_sources() -> None:
    """Use IFD over each channel's independent terminal/current source.

    :return: None.
    """
    block: Block = build_st8c_template(
        VarFactory(),
        parameters=St8cParameters(kc1=0.1, kc2=0.2, ki2=0.5),
    ).block
    bindings: dict[int, float] = dict()
    input_values: tuple[float, ...] = (1.0, 1.0, 0.0, 0.0, 0.0,
                                       1.0, 1.0, 0.0, 1.0, 0.0)
    state_values: tuple[float, ...] = (1.0, 1.05, 0.5, 1.0, 0.05)
    for variable, value in zip(block.in_vars, input_values):
        bindings[variable.uid] = value
    for variable, value in zip(block.state_vars, state_values):
        bindings[variable.uid] = value
    for parameter, expression in block.event_dict.items():
        if isinstance(expression, Const):
            bindings[parameter.uid] = float(expression.value)
        else:
            pass
    for variable, equation in zip(block.algebraic_vars, block.algebraic_eqs):
        bindings[variable.uid] = equation.right.eval_uid(bindings)

    assert bindings[next(
        variable.uid for variable in block.algebraic_vars
        if 'AvailableVoltagePu_ST8C channel 1' in variable.name
    )] == pytest.approx(1.0 * (1.0 - 0.577 * 0.1))
    assert bindings[next(
        variable.uid for variable in block.algebraic_vars
        if 'AvailableVoltagePu_ST8C channel 2' in variable.name
    )] == pytest.approx(0.5 * (1.0 - 0.577 * 0.4))

