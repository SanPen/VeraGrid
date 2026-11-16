# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Converter-stage checks before PSS/E REGCA1 high-voltage binding is enabled."""

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Templates.Rms.renewable_controls.regca1_low_voltage import (
    Regca1LowVoltageSettings,
    build_regca1_low_voltage_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.enumerations import VarPowerFlowReferenceType


def test_regca1_low_voltage_has_three_memories_and_zero_filter_reduction() -> None:
    """Keep source state count and reduce only the zero-time voltage filter.

    :return: None.
    """
    template: RmsModelTemplate = build_regca1_low_voltage_template(vf=VarFactory())
    block: Block = template.block
    assert len(block.state_vars) == len(block.state_eqs) == 3
    assert len(block.diff_vars) == 3
    assert tuple(variable.name for variable in block.state_vars) == (
        'ConverterActiveCurrent_REGCA1 low-voltage converter',
        'ConverterReactiveCurrent_REGCA1 low-voltage converter',
        'FilteredVoltage_REGCA1 low-voltage converter',
    )
    assert tuple(variable.base_var.name for variable in block.diff_vars) == tuple(
        variable.name for variable in block.state_vars
    )
    zero_settings: Regca1LowVoltageSettings = Regca1LowVoltageSettings(tfltr=0.)
    zero_template: RmsModelTemplate = build_regca1_low_voltage_template(vf=VarFactory(), settings=zero_settings)
    assert len(zero_template.block.state_vars) == 2
    assert len(zero_template.block.algebraic_vars) == len(zero_template.block.algebraic_eqs) == 6


def test_regca1_high_voltage_current_uses_khv_and_iolim() -> None:
    """Check the KHV current correction and its IOLIM bound.

    :return: None.
    """
    settings: Regca1LowVoltageSettings = Regca1LowVoltageSettings(
        iolim=-.5, khv=.7, accel=.4,
    )
    block: Block = build_regca1_low_voltage_template(
        vf=VarFactory(), name='High-voltage current law', settings=settings,
    ).block
    bindings: dict[int, float] = dict()
    parameter: Var
    value: Expr
    for parameter, value in block.event_dict.items():
        if isinstance(value, Const):
            bindings[parameter.uid] = float(value.value)
        else:
            pass
    voltage: Var = block.external_mapping[VarPowerFlowReferenceType.Vm]
    correction: Var = block.algebraic_vars[-1]
    reactive_state: Var = block.state_vars[1]
    equation: Expr = block.algebraic_eqs[-1]
    bindings[reactive_state.uid] = .5
    voltage_value: float
    correction_value: float
    for voltage_value, correction_value in ((1., 0.), (1.1, 0.), (1.2, .07), (3., 1.)):
        bindings[voltage.uid] = voltage_value
        bindings[correction.uid] = correction_value
        assert equation.eval_uid(bindings) == pytest.approx(0.)
    accel: Var | None = None
    for parameter in block.event_dict:
        if parameter.name.startswith('ACCEL_'):
            accel = parameter
            break
        else:
            pass
    assert accel is not None
    bindings[voltage.uid] = 1.2
    bindings[correction.uid] = .2
    bindings[accel.uid] = .9
    assert equation.eval_uid(bindings) == pytest.approx(.13)
    bindings[block.out_vars[3].uid] = .3
    assert block.algebraic_eqs[1].eval_uid(bindings) == pytest.approx(0.)


def test_regca1_low_voltage_rejects_zero_current_lag_with_finite_rates() -> None:
    """Require a hybrid current memory before accepting zero converter lag.

    :return: None.
    """
    with pytest.raises(ValueError, match='Zero converter time'):
        build_regca1_low_voltage_template(
            vf=VarFactory(), settings=Regca1LowVoltageSettings(tg=0.),
        )


def test_regca1_low_voltage_uses_filtered_lvpl_and_live_terminal_multiplier() -> None:
    """Verify a moving LVPL ceiling, active-rate bound and live-voltage multiplier.

    :return: None.
    """
    settings: Regca1LowVoltageSettings = Regca1LowVoltageSettings(
        tg=.1, rrpwr=.5, brkpt=.9, zerox=.4, lvpl1=1.,
        lvpnt0=.4, lvpnt1=.8, tfltr=.02,
    )
    block: Block = build_regca1_low_voltage_template(
        vf=VarFactory(), name='Converter test', settings=settings,
    ).block
    bindings: dict[int, float] = dict()
    parameter: Var
    value: Expr
    for parameter, value in block.event_dict.items():
        if isinstance(value, Const):
            bindings[parameter.uid] = float(value.value)
        else:
            pass
    order: Var = list(block.event_dict)[0]
    terminal: Var = block.external_mapping[VarPowerFlowReferenceType.Vm]
    active_state: Var = block.state_vars[0]
    filtered: Var = block.state_vars[2]
    bindings[order.uid] = 1.
    bindings[terminal.uid] = .6
    bindings[filtered.uid] = 1.
    bindings[active_state.uid] = .6
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(.5)
    output_bindings: dict[int, float] = dict(bindings)
    output_bindings[block.out_vars[2].uid] = .3
    assert block.algebraic_eqs[0].eval_uid(output_bindings) == pytest.approx(0.)

    # The filtered-voltage LVPL drops immediately; the active-current state
    # sees a downward demand without the upward-only recovery rate bound.
    bindings[filtered.uid] = .5
    output_bindings[filtered.uid] = .5
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(-4.)
    assert block.algebraic_eqs[0].eval_uid(output_bindings) == pytest.approx(0.)


def test_regca1_active_current_state_initializes_to_moving_lvpl_ceiling() -> None:
    """Seed the converter lag from the filtered-voltage-limited command.

    :return: None.
    """
    settings: Regca1LowVoltageSettings = Regca1LowVoltageSettings(
        brkpt=.99, zerox=.4, lvpl1=.5,
    )
    block: Block = build_regca1_low_voltage_template(
        vf=VarFactory(), name='LVPL initialization', settings=settings,
    ).block
    bindings: dict[int, float] = dict()
    parameter: Var
    value: Expr
    for parameter, value in block.event_dict.items():
        if isinstance(value, Const):
            bindings[parameter.uid] = float(value.value)
        else:
            pass
    ip_order: Var = list(block.event_dict)[0]
    filtered_voltage: Var = block.state_vars[2]
    active_state: Var = block.state_vars[0]
    reactive_order: Var = list(block.event_dict)[1]
    bindings[ip_order.uid] = 1.1
    bindings[reactive_order.uid] = -.2
    bindings[filtered_voltage.uid] = .887786205553784
    initial_active: Expr = block.init_eqs[active_state]
    assert initial_active.eval_uid(bindings) == pytest.approx(
        .5 * (.887786205553784 - .4) / (.99 - .4),
    )
    assert block.init_eqs[block.state_vars[1]].eval_uid(bindings) == pytest.approx(-.2)


def test_regca1_reactive_recovery_uses_initial_power_sign() -> None:
    """Choose only the recovery-side reactive rate bound from initial Q.

    :return: None.
    """
    settings: Regca1LowVoltageSettings = Regca1LowVoltageSettings(
        tg=.1, iqrmax=.3, iqrmin=-.4,
    )
    block: Block = build_regca1_low_voltage_template(
        vf=VarFactory(), name='Recovery test', settings=settings,
    ).block
    bindings: dict[int, float] = dict()
    parameter: Var
    value: Expr
    for parameter, value in block.event_dict.items():
        if isinstance(value, Const):
            bindings[parameter.uid] = float(value.value)
        else:
            pass
    order: Var = list(block.event_dict)[1]
    initial_q: Var = list(block.event_dict)[2]
    reactive_state: Var = block.state_vars[1]
    bindings[initial_q.uid] = .2
    bindings[order.uid] = .8
    bindings[reactive_state.uid] = .2
    assert block.state_eqs[1].eval_uid(bindings) == pytest.approx(.3)
    bindings[order.uid] = -.8
    assert block.state_eqs[1].eval_uid(bindings) == pytest.approx(-10.)
    bindings[initial_q.uid] = -.2
    bindings[reactive_state.uid] = -.2
    assert block.state_eqs[1].eval_uid(bindings) == pytest.approx(-.4)


def test_regca1_active_recovery_limit_follows_current_direction() -> None:
    """Apply the source ramp bound when active current reverses.

    :return: None.
    """
    settings: Regca1LowVoltageSettings = Regca1LowVoltageSettings(
        tg=.1, rrpwr=.5, lvplsw=False,
    )
    block: Block = build_regca1_low_voltage_template(
        vf=VarFactory(), name='Reverse active current', settings=settings,
    ).block
    bindings: dict[int, float] = dict()
    parameter: Var
    value: Expr
    for parameter, value in block.event_dict.items():
        if isinstance(value, Const):
            bindings[parameter.uid] = float(value.value)
        else:
            pass
    order: Var = list(block.event_dict)[0]
    active_state: Var = block.state_vars[0]
    bindings[order.uid] = -.8
    bindings[active_state.uid] = -.2
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(-.5)
    bindings[order.uid] = .8
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(10.)
    bindings[active_state.uid] = 0.
    bindings[order.uid] = -.8
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(-.5)
    bindings[order.uid] = .8
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(.5)


def test_regca1_low_voltage_rejects_invalid_breakpoints() -> None:
    """Reject a zero-width voltage segment before building its division.

    :return: None.
    """
    with pytest.raises(ValueError, match='breakpoints'):
        build_regca1_low_voltage_template(
            vf=VarFactory(), settings=Regca1LowVoltageSettings(brkpt=.4, zerox=.4),
        )


def test_regca1_high_voltage_rejects_nonnegative_iolim() -> None:
    """Require the source-specified negative high-voltage current limit.

    :return: None.
    """
    with pytest.raises(ValueError, match='High-voltage correction settings'):
        build_regca1_low_voltage_template(
            vf=VarFactory(), settings=Regca1LowVoltageSettings(iolim=0.),
        )
