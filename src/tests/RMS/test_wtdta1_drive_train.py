# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Source-equation checks for the native WTDTA1 shaft stage."""

import math

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.renewable_controls.wtdta1_drive_train import (
    Wtdta1DriveTrainSettings,
    build_wtdta1_drive_train_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def _parameter_bindings(block: Block) -> dict[int, float]:
    """Evaluate constant construction parameters for equation checks.

    :param block: Drive-train block under test.
    :return: Symbol UID to physical default value.
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


def test_wtdta1_two_mass_equilibrium_and_power_steps() -> None:
    """Retain the four source memories and separate turbine/generator swing.

    :return: None.
    """
    block: Block = build_wtdta1_drive_train_template(
        vf=VarFactory(),
        settings=Wtdta1DriveTrainSettings(h=4., htfrac=.25, freq1=2., dshaft=1.),
    ).block
    assert len(block.state_vars) == len(block.state_eqs) == 4
    assert block.state_vars[0].name.startswith('ShaftTwistAngle_')
    assert block.state_vars[1].name.startswith('TurbineSpeedPu_')
    assert block.state_vars[2].name.startswith('GeneratorSpeedPu_')
    bindings: dict[int, float] = _parameter_bindings(block)
    electrical_power: Var = block.in_vars[0]
    mechanical_power: Var = block.in_vars[1]
    bindings[electrical_power.uid] = .4
    bindings[mechanical_power.uid] = .4
    stiffness: float = 2. * 1. * 3. * (2. * math.pi * 2.) ** 2 / 4.
    bindings[block.state_vars[0].uid] = .4 * 2. * math.pi * 50. / stiffness
    bindings[block.state_vars[1].uid] = 1.
    bindings[block.state_vars[2].uid] = 1.
    bindings[block.state_vars[3].uid] = 0.
    equation: Expr
    for equation in block.state_eqs:
        assert equation.eval_uid(bindings) == pytest.approx(0.)
    bindings[mechanical_power.uid] = .5
    assert block.state_eqs[1].eval_uid(bindings) == pytest.approx(.05)
    assert block.state_eqs[2].eval_uid(bindings) == pytest.approx(0.)
    bindings[mechanical_power.uid] = .4
    bindings[electrical_power.uid] = .5
    assert block.state_eqs[1].eval_uid(bindings) == pytest.approx(0.)
    assert block.state_eqs[2].eval_uid(bindings) == pytest.approx(-.1 / 6.)
    # An isolated twist perturbation must restore at the named shaft frequency.
    bindings[electrical_power.uid] = .4
    bindings[block.state_vars[0].uid] += .01
    relative_acceleration: float = 2. * math.pi * 50. * (
        float(block.state_eqs[1].eval_uid(bindings))
        - float(block.state_eqs[2].eval_uid(bindings))
    )
    assert relative_acceleration == pytest.approx(-(2. * math.pi * 2.) ** 2 * .01)


def test_wtdta1_zero_turbine_fraction_reduces_to_one_mass() -> None:
    """Remove the singular shaft/turbine states when Htfrac is zero.

    :return: None.
    """
    block: Block = build_wtdta1_drive_train_template(
        vf=VarFactory(), settings=Wtdta1DriveTrainSettings(htfrac=0.),
    ).block
    assert len(block.state_vars) == 2
    assert len(block.algebraic_vars) == 1
    bindings: dict[int, float] = _parameter_bindings(block)
    bindings[block.in_vars[0].uid] = .4
    bindings[block.in_vars[1].uid] = .5
    bindings[block.state_vars[0].uid] = 1.
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(.0125)
    bindings[block.algebraic_vars[0].uid] = 1.
    assert block.algebraic_eqs[0].eval_uid(bindings) == pytest.approx(0.)


def test_wtdta1_rejects_singular_physical_settings() -> None:
    """Reject zero inertia and a zero two-mass shaft frequency.

    :return: None.
    """
    with pytest.raises(ValueError, match='inertia'):
        build_wtdta1_drive_train_template(
            vf=VarFactory(), settings=Wtdta1DriveTrainSettings(h=0.),
        )
    with pytest.raises(ValueError, match='shaft frequency'):
        build_wtdta1_drive_train_template(
            vf=VarFactory(), settings=Wtdta1DriveTrainSettings(freq1=0.),
        )
