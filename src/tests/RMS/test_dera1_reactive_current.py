# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""DERA1 constant-Q/PF and voltage-support current path checks."""

import math

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.renewable_controls.dera1_reactive_current import (
    Dera1ReactiveCurrentSettings,
    build_dera1_reactive_current_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def evaluate_current(block: Block, voltage: float, active_order: float,
                     reactive_reference: float) -> tuple[float, float]:
    """Evaluate the algebraic outputs using caller-supplied open input ports.

    :param block: Native DERA1 reactive-current block.
    :param voltage: Filtered terminal voltage in pu.
    :param active_order: Active-power order in pu.
    :param reactive_reference: Constant-Q reference in pu.
    :return: Reactive current command and voltage-support injection.
    """
    values: dict[int, float] = dict()
    for parameter, expression in block.event_dict.items():
        assert isinstance(expression, Const)
        values[parameter.uid] = float(expression.value)
    values[block.in_vars[0].uid] = voltage
    values[block.in_vars[1].uid] = active_order
    values[block.in_vars[2].uid] = reactive_reference
    signal: Var
    equation: Expr
    for signal, equation in zip(block.algebraic_vars, block.algebraic_eqs):
        values[signal.uid] = 0.0
        values[signal.uid] = -equation.eval_uid(values)
    return (values[block.out_vars[0].uid], values[block.out_vars[1].uid])


def test_dera1_constant_q_adds_bounded_voltage_support() -> None:
    """Voltage droop adds to Q/V current after the asymmetric deadband."""
    settings: Dera1ReactiveCurrentSettings = Dera1ReactiveCurrentSettings(
        dbd1=-0.02, dbd2=0.02, kqv=2.0, vref0=1.0, tiq=0.0,
        iqll=-0.1, iqhl=0.1, initial_voltage=1.0,
        initial_reactive_power=0.2,
    )
    block: Block = build_dera1_reactive_current_template(
        VarFactory(), settings=settings,
    ).block
    current, injection = evaluate_current(block, 0.9, 0.5, 0.2)
    assert injection == pytest.approx(0.1)
    assert current == pytest.approx(0.2 / 0.9 + 0.1)


def test_dera1_constant_pf_scales_q_reference_with_active_order() -> None:
    """PF mode derives Qref from Pord and the solved power-factor angle."""
    angle: float = math.atan(0.2)
    settings: Dera1ReactiveCurrentSettings = Dera1ReactiveCurrentSettings(
        pf_control=True, kqv=0.0, tiq=0.0, initial_voltage=1.0,
        initial_active_power=0.5, initial_reactive_power=0.1, pf_angle=angle,
    )
    block: Block = build_dera1_reactive_current_template(
        VarFactory(), settings=settings,
    ).block
    current, injection = evaluate_current(block, 1.0, 0.8, 0.1)
    assert current == pytest.approx(0.16)
    assert injection == pytest.approx(0.0)


def test_dera1_reactive_current_lag_tracks_q_order() -> None:
    """Tiq creates the source first-order state on the base Q-current path."""
    settings: Dera1ReactiveCurrentSettings = Dera1ReactiveCurrentSettings(
        tiq=0.5, initial_voltage=1.0, initial_reactive_power=0.2,
    )
    block: Block = build_dera1_reactive_current_template(
        VarFactory(), settings=settings,
    ).block
    assert len(block.state_vars) == 1
    values: dict[int, float] = dict()
    for parameter, expression in block.event_dict.items():
        assert isinstance(expression, Const)
        values[parameter.uid] = float(expression.value)
    values[block.in_vars[0].uid] = 1.0
    values[block.in_vars[1].uid] = 0.0
    values[block.in_vars[2].uid] = 0.4
    values[block.state_vars[0].uid] = 0.2
    assert block.state_eqs[0].eval_uid(values) == pytest.approx(0.4)


def test_dera1_corrects_out_of_deadband_initial_voltage_reference() -> None:
    """A nonzero Kqv reference outside its deadband seeds from solved voltage."""
    settings: Dera1ReactiveCurrentSettings = Dera1ReactiveCurrentSettings(
        dbd1=-0.02, dbd2=0.02, kqv=2.0, vref0=1.1, tiq=0.0,
        initial_voltage=1.0,
    )
    block: Block = build_dera1_reactive_current_template(
        VarFactory(), settings=settings,
    ).block
    reference: Var
    expression: Expr | Const
    for reference, expression in block.event_dict.items():
        if reference.name.startswith('VREF0_'):
            assert isinstance(expression, Const)
            assert expression.value == pytest.approx(1.0)
        else:
            pass
