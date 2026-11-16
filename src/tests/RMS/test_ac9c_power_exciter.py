# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Check the connected AC9C power-stage, feedback and field section."""

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_field_feedback import (
    Ac9cFieldFeedbackSettings,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_freewheel_voltage import (
    Ac9cFreewheelVoltageSettings,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_power_exciter import (
    build_ac9c_power_exciter_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_power_stage import (
    Ac9cPowerStageType,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_rotating_exciter import (
    Ac9cRotatingExciterSettings,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def make_ac9c_partial_bindings(block: Block, vct: float, vavr: float, ifd: float,
                               state_values: tuple[float, ...],
                               algebraic_values: tuple[float, ...]) -> dict[int, float]:
    """Bind connected AC9C component parameters, ports and internal values.

    :param block: Connected AC9C power/exciter block.
    :param vct: Potential-source rectifier voltage.
    :param vavr: Field-current regulator output.
    :param ifd: Generator field current.
    :param state_values: State values in composed block order.
    :param algebraic_values: Algebraic values in composed block order.
    :return: UID-keyed numeric expression bindings.
    """
    bindings: dict[int, float] = dict()
    parameter: Var
    value: Expr
    variable: Var
    for parameter, value in block.event_dict.items():
        if isinstance(value, Const):
            bindings[parameter.uid] = float(value.value)
        else:
            pass
    bindings[block.in_vars[0].uid] = vct
    bindings[block.in_vars[1].uid] = vavr
    bindings[block.in_vars[2].uid] = ifd
    for index, variable in enumerate(block.state_vars):
        bindings[variable.uid] = state_values[index]
    for index, variable in enumerate(block.algebraic_vars):
        bindings[variable.uid] = algebraic_values[index]
    return bindings


def make_ac9c_power_exciter() -> Block:
    """Build a chopper chain whose feedback-loop operating point is balanced.

    :return: Connected native AC9C block.
    """
    return build_ac9c_power_exciter_template(
        vf=VarFactory(), stage_type=Ac9cPowerStageType.CHOPPER,
        field_feedback_settings=Ac9cFieldFeedbackSettings(
            kf=1., tf=.1, signal0=1., feedback0=1.,
        ),
        freewheel_settings=Ac9cFreewheelVoltageSettings(
            kfw=.5, vfwmax=1., vfwmin=0., feedback0=1., vfw0=.5,
        ),
        exciter_settings=Ac9cRotatingExciterSettings(
            kc=.2, kd=.1, ke=1., te=.5, vfemax=5., vemin=.1,
            efe0=1., ifd0=0., ve0=1.,
        ),
    ).block


def test_ac9c_power_exciter_connects_feedback_and_initializes_balanced() -> None:
    """Close VFE to KF/TF to KFW, power-stage and exciter feedback paths.

    :return: None.
    """
    block: Block = make_ac9c_power_exciter()
    assert len(block.in_vars) == 3
    assert len(block.state_vars) == 2
    bindings: dict[int, float] = make_ac9c_partial_bindings(
        block, vct=.9, vavr=.1, ifd=0., state_values=(1., 1.),
        algebraic_values=(.9, .1, 0., 1., 1., .5),
    )
    assert all(equation.eval_uid(bindings) == pytest.approx(0.) for equation in block.state_eqs)
    assert all(equation.eval_uid(bindings) == pytest.approx(0.) for equation in block.algebraic_eqs)


def test_ac9c_power_exciter_routes_chopper_and_field_dynamics() -> None:
    """Route both chopper regions into exciter EFE after closing VFE feedback.

    :return: None.
    """
    block: Block = make_ac9c_power_exciter()
    bindings: dict[int, float] = make_ac9c_partial_bindings(
        block, vct=.7, vavr=-.05, ifd=0., state_values=(1., 1.),
        algebraic_values=(0., -.05, 0., 1., 1., .5),
    )
    assert block.algebraic_eqs[0].eval_uid(bindings) == pytest.approx(0.)
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(-2.1)
    bindings[block.in_vars[1].uid] = -.2
    bindings[block.algebraic_vars[0].uid] = -.5
    bindings[block.algebraic_vars[1].uid] = -.2
    assert block.algebraic_eqs[0].eval_uid(bindings) == pytest.approx(0.)
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(-3.4)
