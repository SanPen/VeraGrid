# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Connected unsaturated Type 2 wind plant core checks."""

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.renewable_controls.wt12t1_drive_train import Wt12t1DriveTrainSettings
from VeraGridEngine.Templates.Rms.renewable_controls.wt2_unsaturated_chain import (
    build_wt2_unsaturated_chain,
)
from VeraGridEngine.Templates.Rms.renewable_controls.wt2_active_stall_chain import build_wt2_active_stall_chain
from VeraGridEngine.Templates.Rms.renewable_controls.wt2e1_rotor_resistance import Wt2e1Settings
from VeraGridEngine.Utils.Symbolic.block import Block
from tests.symbolic_block_roundtrip import roundtrip_block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.Utils.procedural_logic import ProceduralLogicCodec, TimedPulseLogic


def _resolved_initial_values(block: Block) -> dict[int, float]:
    """Resolve the acyclic constant operating-point expressions in a block.

    :param block: Connected Type 2 block.
    :return: UID values for every source parameter and initialized variable.
    """
    values: dict[int, float] = dict()
    parameter: Var
    parameter_value: Expr
    for parameter, parameter_value in block.event_dict.items():
        if isinstance(parameter_value, Const):
            values[parameter.uid] = float(parameter_value.value)
        else:
            pass
    for parameter, parameter_value in block.mode_dict.items():
        if isinstance(parameter_value, Const):
            values[parameter.uid] = float(parameter_value.value)
        else:
            pass
    index: int
    variable: Var
    expression: Expr
    for index in range(len(block.init_eqs)):
        for variable, expression in block.init_eqs.items():
            if all(dependency.uid in values for dependency in expression.get_vars()):
                values[variable.uid] = float(expression.eval_uid(values))
            else:
                pass
    assert all(variable.uid in values for variable in block.init_eqs)
    return values


def test_wt2_connected_core_initializes_and_closes_machine_loops() -> None:
    """Balance all thirteen states and eight algebraic constraints together.

    :return: None.
    """
    block: Block = build_wt2_unsaturated_chain(VarFactory()).block
    assert len(block.state_vars) == 13
    assert len(block.algebraic_vars) == 8
    assert len(block.in_vars) == 5
    values: dict[int, float] = _resolved_initial_values(block)
    assert values[block.out_vars[0].uid] > 0.
    assert values[block.out_vars[1].uid] < 0.
    assert values[block.out_vars[-1].uid] == pytest.approx(.2)
    equation: Expr
    for equation in block.state_eqs:
        assert equation.eval_uid(values) == pytest.approx(0., abs=1e-10)
    for equation in block.algebraic_eqs:
        assert equation.eval_uid(values) == pytest.approx(0., abs=1e-10)
    values[block.in_vars[1].uid] = .9
    assert block.algebraic_eqs[1].eval_uid(values) != pytest.approx(0.)
    restored: Block = roundtrip_block(block)
    assert len(restored.state_vars) == 13
    assert len(restored.in_vars) == 5


def test_wt2_connected_core_rejects_mismatched_operating_points() -> None:
    """Require one initial slip and rotor resistance across machine and controls.

    :return: None.
    """
    with pytest.raises(ValueError, match='initial speeds'):
        build_wt2_unsaturated_chain(
            VarFactory(), shaft_settings=Wt12t1DriveTrainSettings(initial_speed=1.03),
        )
    with pytest.raises(ValueError, match='initial values'):
        build_wt2_unsaturated_chain(
            VarFactory(), resistance_settings=Wt2e1Settings(
                initial_speed=1.02, initial_power=.9, initial_fraction=.2,
            ),
        )


def test_wt2_active_stall_chain_closes_live_voltage_and_shaft_torque() -> None:
    """Balance the active-stall variant and retain its timed source switch.

    :return: None.
    """
    block: Block = build_wt2_active_stall_chain(VarFactory()).block
    assert len(block.in_vars) == 3
    assert len(block.procedural_logic) == 1
    assert isinstance(block.procedural_logic[0], TimedPulseLogic)
    values: dict[int, float] = _resolved_initial_values(block)
    missing: set[str] = set(variable.name for equation in block.state_eqs + block.algebraic_eqs
                            for variable in equation.get_vars() if variable.uid not in values)
    assert not missing
    equation: Expr
    for equation in block.state_eqs:
        assert equation.eval_uid(values) == pytest.approx(0., abs=1e-9)
    for equation in block.algebraic_eqs:
        assert equation.eval_uid(values) == pytest.approx(0., abs=1e-9)
    terminal_voltage: Var = next(variable for variable in block.algebraic_vars
                                  if variable.name.startswith('TerminalVoltagePu_'))
    values[block.in_vars[1].uid] = .5
    assert block.algebraic_eqs[1].eval_uid(values) != pytest.approx(0.)
    restored: Block = roundtrip_block(block, ProceduralLogicCodec())
    assert len(restored.procedural_logic) == 1
    assert terminal_voltage in block.algebraic_vars
