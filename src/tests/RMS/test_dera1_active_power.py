# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Check the source frequency response and active-power order of DERA1."""

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.renewable_controls.dera1_active_power import (
    Dera1ActivePowerSettings,
    build_dera1_active_power_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def evaluate_state_derivative(
        block: Block,
        state_fragment: str,
        frequency: float,
        reference: float,
) -> float:
    """Evaluate one state derivative at the initialized feedback operating point.

    :param block: Native DERA1 active-power block.
    :param state_fragment: Unique state-name fragment to evaluate.
    :param frequency: Frequency deviation in pu.
    :param reference: Active-power reference in pu.
    :return: State derivative in pu per second.
    """
    values: dict[int, float] = dict()
    parameter: Var
    expression: Expr
    for parameter, expression in block.event_dict.items():
        if isinstance(expression, Const):
            values[parameter.uid] = float(expression.value)
        else:
            pass
    values[block.in_vars[0].uid] = frequency
    values[block.in_vars[1].uid] = reference
    for state in block.state_vars:
        initial: Expr = block.init_eqs[state]
        values[state.uid] = initial.eval_uid(values)
    signal: Var
    algebraic_equation: Expr
    for signal, algebraic_equation in zip(block.algebraic_vars, block.algebraic_eqs):
        values[signal.uid] = 0.0
        values[signal.uid] = -algebraic_equation.eval_uid(values)
    else:
        pass
    state: Var
    equation: Expr
    for state, equation in zip(block.state_vars, block.state_eqs):
        if state_fragment in state.name:
            return equation.eval_uid(values)
        else:
            pass
    raise AssertionError('Requested DERA1 state was not created')


def test_dera1_frequency_droop_reduces_power_above_nominal() -> None:
    """Over-frequency response reduces the active-power order."""
    settings: Dera1ActivePowerSettings = Dera1ActivePowerSettings(
        ddn=1.0, fdbd1=-0.02, fdbd2=0.02, pmin=0.0, pmax=1.0,
        trf=0.0, tp=0.1, tpord=0.1, kig=1.0, initial_active_power=0.5,
    )
    block: Block = build_dera1_active_power_template(
        VarFactory(), settings=settings, frequency_control=False,
    ).block
    assert evaluate_state_derivative(
        block, 'FrequencyPowerIntegral', 0.12, 0.5,
    ) == pytest.approx(-0.1)


def test_dera1_frequency_droop_increases_power_below_nominal() -> None:
    """Under-frequency response increases the active-power order."""
    settings: Dera1ActivePowerSettings = Dera1ActivePowerSettings(
        dup=1.0, fdbd1=-0.02, fdbd2=0.02, pmin=0.0, pmax=1.0,
        trf=0.0, tp=0.1, tpord=0.1, kig=1.0, initial_active_power=0.5,
    )
    block: Block = build_dera1_active_power_template(
        VarFactory(), settings=settings,
    ).block
    assert evaluate_state_derivative(
        block, 'FrequencyPowerIntegral', -0.12, 0.5,
    ) == pytest.approx(0.1)


def test_dera1_power_reference_is_used_when_frequency_control_is_disabled() -> None:
    """FreqFlag selects the direct Pref-to-Pord path."""
    settings: Dera1ActivePowerSettings = Dera1ActivePowerSettings(
        ddn=1.0, dup=1.0, fdbd1=-0.02, fdbd2=0.02,
        trf=0.0, tp=0.1, tpord=0.1, pmin=0.0, pmax=1.0,
        initial_active_power=0.5,
    )
    block: Block = build_dera1_active_power_template(
        VarFactory(), settings=settings, frequency_control=False,
    ).block
    assert evaluate_state_derivative(
        block, 'RateLimitedPowerCommandPu', 0.5, 0.7,
    ) == pytest.approx(1.0)


def test_dera1_active_power_path_includes_source_ramp_limits() -> None:
    """Apply the configured dPmin/dPmax stage before the Tpord lag."""
    settings: Dera1ActivePowerSettings = Dera1ActivePowerSettings(
        dpmax=0.3, dpmin=-0.2, initial_active_power=0.5,
    )
    block: Block = build_dera1_active_power_template(
        VarFactory(), settings=settings, frequency_control=False,
    ).block
    assert evaluate_state_derivative(
        block, 'RateLimitedPowerCommandPu', 0.0, 0.7,
    ) == pytest.approx(0.3)
