# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""REECA1 immediate fault-current injection checks."""

import numpy as np
import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Templates.Rms.renewable_controls.reeca1_voltage_support import (
    Reeca1VoltageSupportSettings,
    build_reeca1_voltage_support_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from tests.symbolic_block_roundtrip import roundtrip_block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.Utils.procedural_logic import (
    BlockProceduralLogicUpdater, PickupDropoffLogic, ProceduralLogicCodec,
    build_boundary_updater_from_block,
)


def _fault_injection(block: Block, voltage: float, filtered: float,
                     reference: float, held: float = 0.) -> float:
    """Evaluate the source voltage-support algebraic output.

    :param block: Stand-alone voltage-support block.
    :param voltage: Live terminal voltage in per unit.
    :param filtered: Filtered terminal voltage in per unit.
    :param reference: Fixed voltage reference in per unit.
    :param held: Procedural recovery state for positive Thld.
    :return: Signed injected reactive current in per unit.
    """
    bindings: dict[int, float] = dict()
    parameter: Var
    value: Expr
    for parameter, value in block.event_dict.items():
        if isinstance(value, Const):
            bindings[parameter.uid] = float(value.value)
        else:
            pass
    bindings[block.in_vars[0].uid] = voltage
    bindings[block.in_vars[1].uid] = filtered
    bindings[block.in_vars[2].uid] = reference
    mode: Var
    for mode in block.mode_dict:
        bindings[mode.uid] = held
    bindings[block.out_vars[0].uid] = 0.
    return -float(block.algebraic_eqs[0].eval_uid(bindings))


class RecoveryProblem(EmtProblemTemplate):
    """Bind the actual REECA1 recovery logic to a minimal voltage state."""

    __slots__ = ()


def test_reeca1_voltage_fault_injection_uses_live_gate_and_filtered_error() -> None:
    """Apply strict fault pickup, deadband and signed current limits.

    :return: None.
    """
    block: Block = build_reeca1_voltage_support_template(
        vf=VarFactory(),
        settings=Reeca1VoltageSupportSettings(
            vdip=.9, vup=1.1, dbd1=-.02, dbd2=.02,
            kqv=2., iql1=-.3, iqh1=.3,
        ),
    ).block
    assert _fault_injection(block, 1., .8, 1.) == pytest.approx(0.)
    assert _fault_injection(block, .9, .8, 1.) == pytest.approx(.3)
    assert _fault_injection(block, 1.1, 1.2, 1.) == pytest.approx(-.3)
    assert _fault_injection(block, .8, .95, 1.) == pytest.approx(.06)
    assert _fault_injection(block, .8, .8, 1.) == pytest.approx(.3)
    assert _fault_injection(block, 1.2, 1.2, 1.) == pytest.approx(-.3)


def test_reeca1_voltage_support_rejects_invalid_thresholds() -> None:
    """Prevent overlapping fault windows and inverted injection bounds.

    :return: None.
    """
    with pytest.raises(ValueError, match='thresholds'):
        build_reeca1_voltage_support_template(
            vf=VarFactory(), settings=Reeca1VoltageSupportSettings(vdip=1.1, vup=.9),
        )
    with pytest.raises(ValueError, match='limits'):
        build_reeca1_voltage_support_template(
            vf=VarFactory(), settings=Reeca1VoltageSupportSettings(iql1=.1),
        )


def test_reeca1_positive_thld_holds_iqfrz_until_exact_dropoff() -> None:
    """Retain recovery current after fault clearance and schedule its expiry.

    :return: None.
    """
    vf: VarFactory = VarFactory()
    block: Block = build_reeca1_voltage_support_template(
        vf=vf, settings=Reeca1VoltageSupportSettings(
            thld=.2, iqfrz=.15, kqv=2.,
        ),
    ).block
    assert len(block.procedural_logic) == 1
    assert isinstance(block.procedural_logic[0], PickupDropoffLogic)
    assert _fault_injection(block, .8, .8, 1., held=1.) == pytest.approx(.4)
    assert _fault_injection(block, 1., 1., 1., held=1.) == pytest.approx(.15)
    assert _fault_injection(block, 1., 1., 1., held=0.) == pytest.approx(0.)
    voltage: Var = block.in_vars[0]
    mode: Var = next(iter(block.mode_dict))
    runtime_block: Block = Block(
        name='REECA1 recovery runtime',
        state_vars=list((voltage,)),
        diff_vars=list((vf.add_diff_var('d_RecoveryVoltage', base_var=voltage),)),
        state_eqs=list((Const(0.),)),
        init_eqs=dict(((voltage, Const(1.)),)),
        event_dict=block.event_dict,
        mode_dict=block.mode_dict,
        procedural_logic=block.procedural_logic,
    )
    restored: Block = roundtrip_block(runtime_block, ProceduralLogicCodec())
    problem: RecoveryProblem = RecoveryProblem(
        sys_block=restored, glob_time=vf.add_var('RecoveryTime'),
        static_parameter_values_mapping=dict(),
    )
    updater: BlockProceduralLogicUpdater | None = build_boundary_updater_from_block(problem)
    assert updater is not None
    state: np.ndarray = problem.get_x0().copy()
    parameters: np.ndarray = problem.event_params_values.copy()
    voltage_index: int = problem.get_var_idx(voltage)
    mode_index: int = problem.uid2idx_event_params[mode.uid]
    updater.update(0., state, parameters)
    state[voltage_index] = .8
    updater.update(.1, state, parameters)
    assert parameters[mode_index] == pytest.approx(1.)
    state[voltage_index] = 1.
    updater.update(.15, state, parameters)
    assert parameters[mode_index] == pytest.approx(1.)
    assert updater.get_next_forced_event_time(.15, .5) == pytest.approx(.35)
    updater.update(.35, state, parameters)
    assert parameters[mode_index] == pytest.approx(0.)


def test_reeca1_negative_thld_retains_live_iqv_after_fault_clearance() -> None:
    """Keep state 1 and its filtered-voltage current during signed hold.

    :return: None.
    """
    block: Block = build_reeca1_voltage_support_template(
        vf=VarFactory(), settings=Reeca1VoltageSupportSettings(
            thld=-.2, iqfrz=.7, kqv=2.,
        ),
    ).block
    assert len(block.procedural_logic) == 1
    assert isinstance(block.procedural_logic[0], PickupDropoffLogic)
    assert _fault_injection(block, 1., .9, 1., held=1.) == pytest.approx(.2)
    assert _fault_injection(block, 1., .9, 1., held=0.) == pytest.approx(0.)
