# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Compare compiled and interpreted procedural binding on all RMS assemblers."""

import numpy as np
import pytest

from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae import RmsProblemDae
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae_vectorized import RmsProblemDaeVec
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae_full_vectorized import RmsProblemDaeFullVec
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var, real
from VeraGridEngine.Utils.procedural_logic import (
    BlockProceduralLogicUpdater,
    ProceduralExpressionMode,
    build_boundary_updater_from_block,
    hard_saturation,
    sampled_value,
)


@pytest.mark.parametrize("problem_class", (RmsProblemDae, RmsProblemDaeVec, RmsProblemDaeFullVec))
@pytest.mark.parametrize("fused", (True, False))
def test_rms_compiled_procedural_equivalence(
        problem_class: type[RmsProblemDae] | type[RmsProblemDaeVec] | type[RmsProblemDaeFullVec],
        fused: bool,
) -> None:
    """Preserve ordered expressions, time, resets and replaced parameter layouts.

    :param problem_class: RMS assembler whose production binding is exercised.
    :param fused: Whether every declaration supports a fused boundary kernel.
    :return: None.
    """
    source: Var = Var("source")
    gain: Var = Var("gain")
    bias: Var = Var("bias")
    first: Var = Var("first")
    second: Var = Var("second")
    target_time: Var = Var("glob_time")
    sample_time: Var = Var("time")
    # RMS states and outputs are real, while symbolic intermediates can be complex.
    expression: Expr = real(source * Const(1.0 + 2.0j)) * gain + bias + target_time + sample_time
    block: Block = Block(
        name="RMS procedural equivalence",
        algebraic_vars=list((source,)),
        parameters=dict(((gain, Const(2.0)),)),
        event_dict=dict(((bias, Const(0.5)),)),
        mode_dict=dict(((first, Const(0.0)), (second, Const(0.0)))),
        procedural_logic=list((
            sampled_value(output=first, source=expression),
            sampled_value(output=second, source=first * Const(2.0)),
        )),
    )
    if fused:
        pass
    else:
        # A mixed declaration list must compile individual evaluators in order.
        block.procedural_logic[1] = hard_saturation(
            output=second, u=first * Const(2.0), u_min=Const(-100.0), u_max=Const(100.0),
        )

    # Isolate the numerical binding from power-flow and device initialization.
    problem: RmsProblemDae | RmsProblemDaeVec | RmsProblemDaeFullVec = problem_class.__new__(problem_class)
    problem.sys_block = block
    problem._glob_time = target_time
    problem._uid2idx_vars = dict(((source.uid, 0),))
    problem._uid2idx_params = dict(((gain.uid, 0),))
    problem._uid2idx_event_params = dict(((bias.uid, 0), (first.uid, 1), (second.uid, 2)))
    problem._parameters_values = list((Const(2.0),))
    problem._variable_parameters = list((bias, first, second))
    problem._procedural_expression_compiler = None
    problem._initialize_procedural_logic_updater()
    compiled: BlockProceduralLogicUpdater | None = problem._procedural_logic_updater
    interpreted: BlockProceduralLogicUpdater | None = build_boundary_updater_from_block(
        problem=problem, expression_mode=ProceduralExpressionMode.Interpreted,
    )
    assert compiled is not None
    assert interpreted is not None
    assert (compiled._compiled_plan is not None) == fused
    states: np.ndarray = np.array((3.0,), dtype=np.float64)
    compiled_parameters: np.ndarray = np.array((0.5, 0.0, 0.0), dtype=np.float64)
    interpreted_parameters: np.ndarray = compiled_parameters.copy()
    # A new iterate at the same timestamp and a reset must both retain semantics.
    iteration: int
    for iteration in range(3):
        if iteration == 2:
            compiled.reset()
            interpreted.reset()
        else:
            pass
        states[0] = 3.0 + iteration
        compiled.get_next_forced_event_time(0.1, 0.2)
        interpreted.get_next_forced_event_time(0.1, 0.2)
        compiled.update(0.2, states, compiled_parameters)
        interpreted.update(0.2, states, interpreted_parameters)
        np.testing.assert_allclose(compiled_parameters, interpreted_parameters, atol=1e-12, rtol=0)
        assert compiled_parameters[1] == pytest.approx(states[0] * 2.0 + 0.8)
        assert compiled_parameters[2] == pytest.approx(compiled_parameters[1] * 2.0)

    # Rebinding after an event-layout change must discard all old index snapshots.
    problem._uid2idx_event_params = dict(((second.uid, 0), (bias.uid, 1), (first.uid, 2)))
    problem._variable_parameters = list((second, bias, first))
    problem._parameters_values = list((Const(4.0),))
    problem._initialize_procedural_logic_updater()
    rebuilt: BlockProceduralLogicUpdater | None = problem._procedural_logic_updater
    assert rebuilt is not None
    parameters: np.ndarray = np.array((0.0, 1.0, 0.0), dtype=np.float64)
    rebuilt.update(0.0, states, parameters)
    assert parameters[2] == pytest.approx(21.0)
    assert parameters[0] == pytest.approx(42.0)
