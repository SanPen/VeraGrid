# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""AC9C controller interconnection checks."""
from __future__ import annotations

import math

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c import (
    build_ac9c_controller_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_current_regulator import (
    Ac9cCurrentRegulatorSettings,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_field_feedback import (
    Ac9cFieldFeedbackSettings,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_freewheel_voltage import (
    Ac9cFreewheelVoltageSettings,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_pid import (
    Ac9cPidSettings,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_potential_source import (
    Ac9cPotentialSourceSettings,
    build_ac9c_potential_source_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_rectifier_supply import (
    Ac9cRectifierSupplySettings,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_power_stage import (
    Ac9cPowerStageType,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_rectifier_bridge import (
    Ac9cRectifierBridgeSettings,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_rotating_exciter import (
    Ac9cRotatingExciterSettings,
)
from VeraGridEngine.Templates.Rms import (
    build_international_standard_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.enumerations import InternationalStandardModel


def make_ac9c_controller() -> Block:
    """Build a nontrivial AC9C chain with all dynamic state sections enabled.

    :return: Connected controller block.
    """
    template = build_ac9c_controller_template(
        vf=VarFactory(),
        tr=.1,
        sensed_voltage0=1.,
        pid_settings=Ac9cPidSettings(
            kpr=2., kir=3., kdr=1., tdr=.2,
            vpidmax=4., vpidmin=-4., error0=0., vpid0=.09,
        ),
        current_settings=Ac9cCurrentRegulatorSettings(
            kpa=2., kia=3., vamax=4., vamin=-4., error0=0., vavr0=0.,
        ),
        bridge_settings=Ac9cRectifierBridgeSettings(
            ka=2., ta=.3, vrmax=5., vrmin=-5., vavr0=0., va0=0.,
        ),
        field_feedback_settings=Ac9cFieldFeedbackSettings(
            kf=.1, tf=.4, signal0=.9, feedback0=.09,
        ),
        freewheel_settings=Ac9cFreewheelVoltageSettings(
            kfw=1., vfwmax=2., vfwmin=0., feedback0=.09, vfw0=.09,
        ),
        exciter_settings=Ac9cRotatingExciterSettings(
            kc=.1, kd=.1, ke=1., te=.5, vfemax=5., vemin=0.,
            efe0=.9, ifd0=0., ve0=.9,
        ),
        potential_source_settings=Ac9cPotentialSourceSettings(
            kp=.9, ki1=0., ki2=1., xl=0., theta_p=0.,
        ),
        channel1_settings=Ac9cRectifierSupplySettings(
            kc=0., vbmax=5., source0=.9, ve0=.9,
        ),
        channel2_settings=Ac9cRectifierSupplySettings(
            kc=0., vbmax=5., source0=1., ve0=.9,
        ),
        stage_type=Ac9cPowerStageType.THYRISTOR_BRIDGE,
    )
    return template.block


def make_ac9c_bindings(block: Block, voltage_error: float,
                       states: tuple[float, ...]) -> dict[int, float]:
    """Bind one operating point for residual checks.

    :param block: Connected AC9C controller block.
    :param voltage_error: Voltage reference minus sensed voltage.
    :param states: State values in source order.
    :return: Symbol UID-to-value bindings.
    """
    bindings: dict[int, float] = dict()
    bindings[block.in_vars[0].uid] = 1.
    bindings[block.in_vars[1].uid] = 1. + voltage_error
    bindings[block.in_vars[2].uid] = 0.
    bindings[block.in_vars[3].uid] = 0.0
    bindings[block.in_vars[4].uid] = 0.0
    bindings[block.in_vars[5].uid] = 1.0
    bindings[block.in_vars[6].uid] = 0.0
    bindings[block.in_vars[7].uid] = 1.0
    bindings[block.in_vars[8].uid] = 0.0
    bindings[block.in_vars[9].uid] = 0.0
    for index, variable in enumerate(block.state_vars):
        bindings[variable.uid] = states[index]
    parameter: Var
    expression: Expr
    for parameter, expression in block.event_dict.items():
        if isinstance(expression, Const):
            bindings[parameter.uid] = float(expression.value)
        else:
            pass
    for variable, equation in zip(block.algebraic_vars, block.algebraic_eqs):
        bindings[variable.uid] = equation.right.eval_uid(bindings)
    return bindings


def evaluate_ac9c_potential_source(block: Block, voltage: complex,
                                   current: complex) -> tuple[float, float]:
    """Evaluate the stateless potential source at one pair of phasors.

    :param block: Native AC9C potential-source block.
    :param voltage: Terminal-voltage phasor.
    :param current: Terminal-current phasor.
    :return: Terminal-derived source magnitudes in output order.
    """
    bindings: dict[int, float] = dict()
    for parameter, expression in block.event_dict.items():
        assert isinstance(expression, Const)
        bindings[parameter.uid] = float(expression.value)
    inputs: tuple[float, ...] = (voltage.real, voltage.imag, current.real, current.imag)
    for variable, value in zip(block.in_vars, inputs):
        bindings[variable.uid] = value
    for variable, equation in zip(block.algebraic_vars, block.algebraic_eqs):
        bindings[variable.uid] = equation.right.eval_uid(bindings)
    assert all(equation.eval_uid(bindings) == pytest.approx(0.)
               for equation in block.algebraic_eqs)
    return tuple(bindings[variable.uid] for variable in block.out_vars)


def test_ac9c_controller_matches_source_state_order_and_connections() -> None:
    """Check source state order and closed terminal/PID/field-current paths.

    :return: None.
    """
    block: Block = make_ac9c_controller()
    assert len(block.in_vars) == 10
    assert len(block.state_vars) == 7
    assert [variable.name.split('_')[0] for variable in block.state_vars] == [
        'SensedVoltagePu', 'PIDIntegratorPu', 'PIDDerivativeMemoryPu',
        'CurrentRegulatorIntegratorPu', 'VAPu',
        'ExciterFieldVoltagePu', 'FilteredFeedbackPu',
    ]
    bindings: dict[int, float] = make_ac9c_bindings(
        block, voltage_error=0.,
        states=(1., .09, 0., 0., 0., .9, .09),
    )
    assert all(equation.eval_uid(bindings) == pytest.approx(0.)
               for equation in block.state_eqs)
    assert all(equation.eval_uid(bindings) == pytest.approx(0.)
               for equation in block.algebraic_eqs)
    bindings[block.in_vars[1].uid] = 1.2
    for variable, equation in zip(block.algebraic_vars, block.algebraic_eqs):
        bindings[variable.uid] = equation.right.eval_uid(bindings)
    assert bindings[block.out_vars[0].uid] == pytest.approx(1.49)


def test_ac9c_international_catalogue_dispatches_complete_controller() -> None:
    """Check the public international-model catalogue exposes AC9C."""
    template = build_international_standard_template(
        InternationalStandardModel.AC9C, VarFactory(), 'catalogue AC9C',
    )

    assert len(template.block.state_vars) == 5
    assert len(template.block.in_vars) == 10


def test_ac9c_terminal_potential_sources_follow_phasor_equations() -> None:
    """Check the two primary-diagram voltage magnitudes and frame rotation."""
    voltage: complex = 1.02 + .08j
    current: complex = .31 - .17j
    settings: Ac9cPotentialSourceSettings = Ac9cPotentialSourceSettings(
        kp=1.2, ki1=.08, ki2=.24, xl=.13, theta_p=17.,
    )
    block: Block = build_ac9c_potential_source_template(
        VarFactory(), settings=settings,
    ).block
    rotated_voltage: complex = voltage * complex(.6, .8)
    rotated_current: complex = current * complex(.6, .8)

    kp: complex = settings.kp * complex(
        math.cos(settings.theta_p * math.pi / 180.),
        math.sin(settings.theta_p * math.pi / 180.),
    )
    expected_first: float = abs(
        kp * voltage + 1j * (settings.ki1 + kp * settings.xl) * current
    )
    expected_second: float = abs(settings.ki2 * current)
    assert evaluate_ac9c_potential_source(block, voltage, current) == pytest.approx(
        (expected_first, expected_second),
    )
    assert evaluate_ac9c_potential_source(block, rotated_voltage, rotated_current) == pytest.approx(
        (expected_first, expected_second),
    )
    zero_current: tuple[float, float] = evaluate_ac9c_potential_source(
        block, voltage, 0j,
    )
    assert zero_current[1] == pytest.approx(0.001)
