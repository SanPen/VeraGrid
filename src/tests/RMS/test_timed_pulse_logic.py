# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Runtime and persistence checks for the one-shot procedural pulse."""

import numpy as np
import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Utils.procedural_logic import (
    BlockProceduralLogicUpdater,
    ProceduralLogicCodec,
    TimedPulseLogic,
    build_boundary_updater_from_block,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from tests.symbolic_block_roundtrip import roundtrip_block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var


class PulseProblem(EmtProblemTemplate):
    """Use the existing DAE runtime mappings for a procedural pulse check."""

    __slots__ = ()


def test_timed_pulse_samples_duration_and_expires_during_sustained_trigger() -> None:
    """Keep a sampled deadline even when duration changes or voltage recovers.

    :return: None.
    """
    vf: VarFactory = VarFactory()
    trigger: Var = vf.add_var('PulseTrigger')
    duration: Var = vf.add_var('PulseDuration')
    pulse: Var = vf.add_var('PulseMode')
    block: Block = Block(
        name='Timed pulse runtime check',
        state_vars=list((trigger, duration)),
        diff_vars=list((vf.add_diff_var('d_PulseTrigger', base_var=trigger),
                        vf.add_diff_var('d_PulseDuration', base_var=duration))),
        state_eqs=list((Const(0.), Const(0.))),
        init_eqs=dict(((trigger, Const(0.)), (duration, Const(.2)))),
        mode_dict=dict(((pulse, Const(0.)),)),
        procedural_logic=list((TimedPulseLogic(pulse.name, trigger, duration),)),
    )
    parsed: Block = roundtrip_block(block, ProceduralLogicCodec())
    problem: PulseProblem = PulseProblem(
        sys_block=parsed, glob_time=vf.add_var('PulseGlobalTime'),
        static_parameter_values_mapping=dict(),
    )
    updater: BlockProceduralLogicUpdater | None = build_boundary_updater_from_block(problem)
    assert updater is not None
    assert isinstance(updater.logic_entries[0], TimedPulseLogic)
    state: np.ndarray = problem.get_x0().copy()
    parameters: np.ndarray = problem.event_params_values.copy()
    trigger_idx: int = problem.get_var_idx(trigger)
    duration_idx: int = problem.get_var_idx(duration)
    pulse_idx: int = problem.uid2idx_event_params[pulse.uid]
    state[trigger_idx] = 0.
    state[duration_idx] = .2
    updater.update(0., state, parameters)
    assert parameters[pulse_idx] == pytest.approx(0.)
    state[trigger_idx] = 1.
    updater.update(.1, state, parameters)
    assert parameters[pulse_idx] == pytest.approx(1.)
    assert updater.get_next_forced_event_time(.1, .5) == pytest.approx(.3)
    state[duration_idx] = .01
    updater.update(.15, state, parameters)
    assert updater.get_next_forced_event_time(.15, .5) == pytest.approx(.3)
    state[trigger_idx] = 0.
    updater.update(.2, state, parameters)
    assert parameters[pulse_idx] == pytest.approx(1.)
    state[trigger_idx] = 1.
    updater.update(.25, state, parameters)
    assert updater.get_next_forced_event_time(.25, .5) == pytest.approx(.3)
    updater.update(.3, state, parameters)
    assert parameters[pulse_idx] == pytest.approx(0.)
    updater.update(.31, state, parameters)
    assert parameters[pulse_idx] == pytest.approx(0.)
    state[trigger_idx] = 0.
    updater.update(.32, state, parameters)
    state[trigger_idx] = 1.
    state[duration_idx] = .05
    updater.update(.33, state, parameters)
    assert parameters[pulse_idx] == pytest.approx(1.)
    assert updater.get_next_forced_event_time(.33, .5) == pytest.approx(.38)
    updater.reset()
    updater.update(0., state, parameters)
    assert parameters[pulse_idx] == pytest.approx(0.)
