# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Source-equation checks for the Type 1/2 wind shaft."""

import math

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Templates.Rms import (
    InternationalStandardModel,
    build_international_standard_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.wt12t1_drive_train import (
    Wt12t1DriveTrainSettings,
    build_wt12t1_drive_train_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def _parameter_bindings(block: Block) -> dict[int, float]:
    """Bind the physical constants for state-equation evaluation.

    :param block: WT12T1 controller block.
    :return: UID bindings for source parameters.
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


def test_wt12t1_torque_balance_and_initial_slip() -> None:
    """Keep the Type 1/2 torque interface and four-state shaft equilibrium.

    :return: None.
    """
    block: Block = build_wt12t1_drive_train_template(
        VarFactory(), settings=Wt12t1DriveTrainSettings(h=4., htfrac=.25,
                                                         freq1=2., dshaft=1.,
                                                         initial_speed=1.03),
    ).block
    assert len(block.state_vars) == 4
    assert block.in_vars[0].name.startswith('ElectricalTorquePu_')
    assert block.in_vars[1].name.startswith('MechanicalTorquePu_')
    bindings: dict[int, float] = _parameter_bindings(block)
    bindings[block.in_vars[0].uid] = .4
    bindings[block.in_vars[1].uid] = .4
    stiffness: float = 2. * 1. * 3. * (2. * math.pi * 2.) ** 2 / 4.
    bindings[block.state_vars[0].uid] = .4 * 2. * math.pi * 50. / stiffness
    bindings[block.state_vars[1].uid] = 1.03
    bindings[block.state_vars[2].uid] = 1.03
    bindings[block.state_vars[3].uid] = 0.
    equation: Expr
    for equation in block.state_eqs:
        assert equation.eval_uid(bindings) == pytest.approx(0.)
    bindings[block.in_vars[1].uid] = .5
    assert block.state_eqs[1].eval_uid(bindings) == pytest.approx(.05)
    bindings[block.in_vars[1].uid] = .4
    bindings[block.in_vars[0].uid] = .5
    assert block.state_eqs[2].eval_uid(bindings) == pytest.approx(-.1 / 6.)
    bindings[block.in_vars[0].uid] = .4
    bindings[block.state_vars[0].uid] += .01
    relative_acceleration: float = 2. * math.pi * 50. * (
        float(block.state_eqs[1].eval_uid(bindings))
        - float(block.state_eqs[2].eval_uid(bindings))
    )
    assert relative_acceleration == pytest.approx(-(2. * math.pi * 2.) ** 2 * .01)
    bindings[block.state_vars[2].uid] = 1.04
    assert block.state_eqs[3].eval_uid(bindings) == pytest.approx(2. * math.pi * 50. * .01)


def test_wt12t1_zero_turbine_fraction_has_one_speed_state() -> None:
    """Use the source's one-mass reduction for zero Htfrac.

    :return: None.
    """
    block: Block = build_wt12t1_drive_train_template(
        VarFactory(), settings=Wt12t1DriveTrainSettings(htfrac=0., initial_speed=1.02),
    ).block
    assert len(block.state_vars) == 2
    assert len(block.algebraic_vars) == 1
    bindings: dict[int, float] = _parameter_bindings(block)
    bindings[block.in_vars[0].uid] = .4
    bindings[block.in_vars[1].uid] = .5
    bindings[block.state_vars[0].uid] = 1.02
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(.0125)


def test_wt12t1_is_available_through_the_native_standard_factory() -> None:
    """Expose the sourced shaft equations through the native model factory.

    :return: None.
    """
    template: RmsModelTemplate = build_international_standard_template(
        InternationalStandardModel.WT12T1, VarFactory(), 'WT12T1_catalogue',
    )
    assert template.name == 'WT12T1_catalogue'
    assert len(template.block.state_vars) == 4
    assert template.block.in_vars[0].name.startswith('ElectricalTorquePu_')
    assert template.block.in_vars[1].name.startswith('MechanicalTorquePu_')


@pytest.mark.parametrize('settings', (
    Wt12t1DriveTrainSettings(h=0.),
    Wt12t1DriveTrainSettings(htfrac=1.),
    Wt12t1DriveTrainSettings(freq1=0.),
    Wt12t1DriveTrainSettings(initial_speed=0.),
))
def test_wt12t1_rejects_invalid_shaft_data(settings: Wt12t1DriveTrainSettings) -> None:
    """Reject singular shaft cases before making a model graph.

    :param settings: Invalid physical parameter set.
    :return: None.
    """
    with pytest.raises(ValueError):
        build_wt12t1_drive_train_template(VarFactory(), settings=settings)
