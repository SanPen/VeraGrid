# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Exercise local DSL assignment events using the existing reset logic."""

import numpy as np
import pytest

from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
from VeraGridEngine.IO.dgs.dgs_objects import BlkDef
from VeraGridEngine.IO.dgs.dgs_to_blocks import (
    ParsedDgsBlockDefinition, UnsupportedDgsExpression, build_standalone_blkdef_block_from_parsed_block,
    parse_dgs_block_definitions_from_circuit,
)
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.Utils.procedural_logic import (
    BlockProceduralLogicUpdater, ProceduralLogicCodec, ResetOnRisingEdgeLogic,
    build_boundary_updater_from_block,
)
from tests.symbolic_block_roundtrip import roundtrip_block


def _parse_assignment(statement: str) -> ParsedDgsBlockDefinition:
    """Build a source whose changing state is sampled into a retained signal.

    :param statement: DSL event statement under test.
    :return: Parsed source with symbolic dependencies and initialization.
    """
    definition: BlkDef = BlkDef()
    definition.ID = 'capture'
    definition.loc_name = 'Capture'
    definition.states = list(('x',))
    definition.outputs = list(('y',))
    definition.internals = list(('RV_Hold',))
    definition.equations_raw = list(('inc(x)=0', 'x.=1', 'inc(RV_Hold)=0', 'y=RV_Hold', statement))
    circuit: DgsCircuit = DgsCircuit()
    circuit.blkdefs.append(definition)
    return parse_dgs_block_definitions_from_circuit(circuit)['capture']


def test_local_event_parses_into_reset_and_retained_mode() -> None:
    """Retain the initial destination and keep the source as a state.

    :return: None.
    """
    parsed: ParsedDgsBlockDefinition = _parse_assignment(
        "event(1,time()>=0.75, 'name=this value=x variable=RV_Hold')")
    assert parsed.unsupported_lines == list()
    assert len(parsed.discrete_event_actions) == 0
    assert len(parsed.procedural_logic) == 1
    logic: ResetOnRisingEdgeLogic = parsed.procedural_logic[0]
    assert isinstance(logic, ResetOnRisingEdgeLogic)
    assert logic.target_var_uid == parsed.symbol_table['RV_Hold'].uid
    assert logic.accepted_boundary_only
    assert logic.forced_event_time == 0.75
    assert parsed.symbol_table['RV_Hold'] in parsed.mode_dict
    assert parsed.symbol_table['x'] not in parsed.mode_dict
    assert 'x' in parsed.state_rhs


@pytest.mark.parametrize('statement', (
    "event(1,time()>=0.75, 'name=another value=x variable=RV_Hold')",
    "event(x,time()>=0.75, 'name=this value=x variable=RV_Hold')",
    "event(1,time()>=0, 'name=this value=x variable=RV_Hold')",
    "event(1,time()>0.75, 'name=this value=x variable=RV_Hold')",
))
def test_unsupported_assignment_variants_remain_visible(statement: str) -> None:
    """Fail closed rather than discarding unresolved assignment semantics.

    :param statement: Unsupported target, guard or temporal form.
    :return: None.
    """
    parsed: ParsedDgsBlockDefinition = _parse_assignment(statement)
    assert statement in parsed.unsupported_lines
    assert len(parsed.procedural_logic) == 0


def test_capture_uses_accepted_state_then_holds_and_resets() -> None:
    """Roundtrip, remap and execute without consuming speculative updates.

    :return: None.
    """
    parsed: ParsedDgsBlockDefinition = _parse_assignment(
        "event(1,time()>=0.75, 'name=this value=x variable=RV_Hold')")
    block: Block = build_standalone_blkdef_block_from_parsed_block(parsed)
    restored: Block = roundtrip_block(block, ProceduralLogicCodec())
    clock: Var = Var('test_time')
    problem: EmtProblemTemplate = EmtProblemTemplate(
        sys_block=restored, glob_time=clock, static_parameter_values_mapping=dict())
    updater: BlockProceduralLogicUpdater | None = build_boundary_updater_from_block(problem)
    assert updater is not None
    state: np.ndarray = problem.get_x0().copy()
    parameters: np.ndarray = problem.event_params_values.copy()
    source_index: int = problem.get_var_idx(restored.state_vars[0])
    destination: Var = next(iter(restored.mode_dict))
    destination_index: int = problem.uid2idx_event_params[destination.uid]
    parameters[destination_index] = 0.0
    updater.initialize_modes(0.0, state, parameters)
    assert updater.get_next_forced_event_time(0.6, 0.9) == 0.75
    state[source_index] = 100.0
    updater.update(0.75, state, parameters)
    updater.update(0.9, state, parameters)
    assert parameters[destination_index] == 0.0
    state[source_index] = 0.75
    updater.commit_boundary(0.75, state, parameters)
    assert parameters[destination_index] == pytest.approx(0.75)
    state[source_index] = 2.0
    updater.commit_boundary(0.75, state, parameters)
    updater.commit_boundary(1.0, state, parameters)
    assert parameters[destination_index] == pytest.approx(0.75)
    updater.reset()
    parameters[destination_index] = 0.0
    state[source_index] = 0.0
    updater.initialize_modes(0.0, state, parameters)
    state[source_index] = 3.0
    updater.commit_boundary(0.75, state, parameters)
    assert parameters[destination_index] == pytest.approx(3.0)


def test_unknown_destination_is_deferred_but_rejected_without_instance_evidence() -> None:
    """Keep a possible state alias pending without accepting an arbitrary target.

    :return: None.
    """
    parsed: ParsedDgsBlockDefinition = _parse_assignment(
        "event(1,time()>=0.75, 'name=this value=x variable=missing')")
    assert parsed.unsupported_lines == list()
    assert len(parsed.deferred_assignment_logic) == 1
    assert 'missing' not in parsed.symbol_table
    with pytest.raises(UnsupportedDgsExpression, match='exact BlkRef state binding'):
        build_standalone_blkdef_block_from_parsed_block(parsed)
