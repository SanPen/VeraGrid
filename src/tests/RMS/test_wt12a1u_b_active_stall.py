# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Continuous equation checks for the Type 1/2 active-stall controller."""

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.procedural_logic import ProceduralLogicCodec, TimedPulseLogic
from VeraGridEngine.Templates.Rms.renewable_controls.wt12a1u_b_active_stall import (
    Wt12a1uBSettings,
    build_wt12a1u_b_active_stall_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from tests.symbolic_block_roundtrip import roundtrip_block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def _parameter_bindings(block: Block) -> dict[int, float]:
    """Bind source constants for stand-alone expression evaluation.

    :param block: WT12A1U_B controller block.
    :return: Numeric UID bindings.
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


def test_wt12a1u_b_ramp_filter_and_qualification() -> None:
    """Apply rmin to the output-feedback error while SW1 selects Pmin.

    :return: None.
    """
    block: Block = build_wt12a1u_b_active_stall_template(
        VarFactory(), settings=Wt12a1uBSettings(
            tr=.1, rmax=.4, rmin=.3, t0=.2, pmin=.1, pset=.8,
            curve=((.1, 4.), (.3, 3.), (.5, 2.), (.7, 1.)),
        ),
    ).block
    assert tuple(state.name.split('_')[0] for state in block.state_vars) == (
        'PowerRampPu', 'MechanicalPowerPu', 'FilteredVoltagePu',
    )
    bindings: dict[int, float] = _parameter_bindings(block)
    bindings[block.in_vars[0].uid] = .2
    bindings[block.in_vars[1].uid] = .9
    switch: Var = next(iter(block.mode_dict))
    bindings[switch.uid] = 1.
    assert len(block.procedural_logic) == 1
    restored: Block = roundtrip_block(block, ProceduralLogicCodec())
    assert isinstance(restored.procedural_logic[0], TimedPulseLogic)
    bindings[block.state_vars[0].uid] = .8
    bindings[block.state_vars[1].uid] = .8
    bindings[block.state_vars[2].uid] = .4
    bindings[block.algebraic_vars[0].uid] = 0.
    bindings[block.algebraic_vars[1].uid] = 0.
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(-.3)
    assert block.state_eqs[1].eval_uid(bindings) == pytest.approx(0.)
    assert block.state_eqs[2].eval_uid(bindings) == pytest.approx(-2.)
    assert -block.algebraic_eqs[0].eval_uid(bindings) == pytest.approx(2.)
    assert -block.algebraic_eqs[1].eval_uid(bindings) == pytest.approx(1.)
    bindings[block.in_vars[1].uid] = .8
    assert -block.algebraic_eqs[1].eval_uid(bindings) == pytest.approx(1.)
    bindings[block.in_vars[1].uid] = .79
    assert -block.algebraic_eqs[1].eval_uid(bindings) == pytest.approx(0.)
    bindings[block.in_vars[1].uid] = .9
    bindings[switch.uid] = 0.
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(.1)


@pytest.mark.parametrize('voltage,expected', (
    (0., 4.), (.2, 3.), (.4, 2.), (.6, 1.), (.8, 0.),
))
def test_wt12a1u_b_voltage_duration_bins(voltage: float, expected: float) -> None:
    """Select the source's four step durations by filtered voltage.

    :param voltage: Filtered terminal voltage in per unit.
    :param expected: Duration in seconds, zero above VT4.
    :return: None.
    """
    block: Block = build_wt12a1u_b_active_stall_template(
        VarFactory(), settings=Wt12a1uBSettings(
            curve=((.1, 4.), (.3, 3.), (.5, 2.), (.7, 1.)),
        ),
    ).block
    bindings: dict[int, float] = _parameter_bindings(block)
    bindings[block.state_vars[2].uid] = voltage
    bindings[block.algebraic_vars[0].uid] = 0.
    assert -block.algebraic_eqs[0].eval_uid(bindings) == pytest.approx(expected)


def test_wt12a1u_b_zero_filters_and_invalid_curve() -> None:
    """Reduce zero-time lags and reject an unordered source lookup.

    :return: None.
    """
    block: Block = build_wt12a1u_b_active_stall_template(
        VarFactory(), settings=Wt12a1uBSettings(tr=0., t0=0.),
    ).block
    assert len(block.state_vars) == 1
    with pytest.raises(ValueError, match='voltages'):
        build_wt12a1u_b_active_stall_template(
            VarFactory(), settings=Wt12a1uBSettings(
                curve=((.1, 4.), (.3, 3.), (.2, 2.), (.7, 1.)),
            ),
        )
