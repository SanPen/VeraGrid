# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Check AC9C's source-defined bridge and chopper selection logic."""

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_power_stage import (
    Ac9cPowerStageType,
    ac9c_power_stage_type_from_psse,
    build_ac9c_power_stage_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def get_ac9c_power_stage_output(block: Block, vct: float, vfw: float,
                                vavr: float) -> float:
    """Evaluate the declared power-stage equation for one input point.

    :param block: AC9C power-stage block.
    :param vct: Controlled-rectifier voltage, per unit.
    :param vfw: Freewheel voltage, per unit.
    :param vavr: Voltage regulator signal, per unit.
    :return: Calculated rectifier output voltage, per unit.
    """
    bindings: dict[int, float] = dict()
    parameter: Var
    value: Expr
    for parameter, value in block.event_dict.items():
        if isinstance(value, Const):
            bindings[parameter.uid] = float(value.value)
        else:
            pass
    bindings[block.in_vars[0].uid] = vct
    bindings[block.in_vars[1].uid] = vfw
    bindings[block.in_vars[2].uid] = vavr
    bindings[block.algebraic_vars[0].uid] = 0.0
    return -float(block.algebraic_eqs[0].eval_uid(bindings))


def test_ac9c_thyristor_bridge_passes_converter_voltage() -> None:
    """The thyristor bridge output is VCT independently of VAVR and VFW.

    :return: None.
    """
    block: Block = build_ac9c_power_stage_template(
        vf=VarFactory(), stage_type=Ac9cPowerStageType.THYRISTOR_BRIDGE,
    ).block
    assert get_ac9c_power_stage_output(block, .7, .2, -.5) == pytest.approx(.7)


def test_ac9c_chopper_selects_voltage_blocking_and_freewheel_regions() -> None:
    """Preserve the strict upper/lower comparisons from the data-sheet note.

    :return: None.
    """
    block: Block = build_ac9c_power_stage_template(
        vf=VarFactory(), stage_type=Ac9cPowerStageType.CHOPPER,
        vlim1=0.0, vlim2=-0.1,
    ).block
    assert get_ac9c_power_stage_output(block, .8, .3, .2) == pytest.approx(.8)
    assert get_ac9c_power_stage_output(block, .8, .3, -.05) == pytest.approx(0.0)
    assert get_ac9c_power_stage_output(block, .8, .3, -.1) == pytest.approx(-.3)
    assert get_ac9c_power_stage_output(block, .8, .3, -.2) == pytest.approx(-.3)


def test_ac9c_power_stage_rejects_invalid_threshold_order() -> None:
    """Require the upper chopper threshold to exceed the lower threshold.

    :return: None.
    """
    with pytest.raises(ValueError, match='VLIM1 greater than VLIM2'):
        build_ac9c_power_stage_template(
            vf=VarFactory(), stage_type=Ac9cPowerStageType.CHOPPER,
            vlim1=-.2, vlim2=-.1,
        )


@pytest.mark.parametrize(
    'sct,expected',
    ((0.0, Ac9cPowerStageType.CHOPPER),
     (1.0, Ac9cPowerStageType.THYRISTOR_BRIDGE),
     (-1.0, Ac9cPowerStageType.THYRISTOR_BRIDGE)),
)
def test_psse_sct_selects_the_documented_ac9c_power_stage(
        sct: float, expected: Ac9cPowerStageType,
) -> None:
    """Preserve PSS/E's zero-chopper and nonzero-thyristor convention."""
    assert ac9c_power_stage_type_from_psse(sct) is expected
