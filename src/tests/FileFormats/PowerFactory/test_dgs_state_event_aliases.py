# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Bind deferred FRT events to the state of their exact graphical occurrence."""

import numpy as np
import pytest

from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
from VeraGridEngine.IO.dgs.dgs_objects import BlkDef, BlkRef
from VeraGridEngine.IO.dgs.dgs_to_blocks import (
    ParsedDgsBlockDefinition, UnsupportedDgsExpression, _build_block_from_parsed,
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


def _parse_frt() -> ParsedDgsBlockDefinition:
    """Declare a local timer whose event names an exported parent state alias.

    :return: Parsed definition with an unresolved x1 event and no invented state.
    """
    definition: BlkDef = BlkDef()
    definition.ID = 'frt'
    definition.loc_name = 'FRT'
    definition.states = list(('x',))
    definition.outputs = list(('FRT',))
    definition.equations_raw = list((
        'inc(x)=0', 'x.=1', 'FRT=x',
        "event(1,time()>=0.75, 'name=this value=0 variable=x1')",
    ))
    source: DgsCircuit = DgsCircuit()
    source.blkdefs.append(definition)
    return parse_dgs_block_definitions_from_circuit(source)['frt']


def _reference(identifier: str, bindings: list[str]) -> BlkRef:
    """Describe one exact graphical occurrence of the shared FRT definition.

    :param identifier: Occurrence FID.
    :param bindings: Exported state names in declaration order.
    :return: Reference carrying instance-local state bindings.
    """
    reference: BlkRef = BlkRef()
    reference.ID = identifier
    reference.typ_id = 'frt'
    reference.states = bindings
    return reference


def test_state_alias_is_resolved_after_materialization_by_exact_uid() -> None:
    """Resolve x1 to the local timer without renaming or editing the definition.

    :return: None.
    """
    parsed: ParsedDgsBlockDefinition = _parse_frt()
    assert parsed.unsupported_lines == list()
    assert len(parsed.deferred_assignment_logic) == 1
    assert len(parsed.procedural_logic) == 0
    assert 'x1' not in parsed.symbol_table
    first: Block = _build_block_from_parsed(parsed, dict(), reference=_reference('634', list(('x1',))))
    second: Block = _build_block_from_parsed(parsed, dict(), reference=_reference('other_instance', list(('x1',))))
    first_logic: ResetOnRisingEdgeLogic = first.procedural_logic[0]
    second_logic: ResetOnRisingEdgeLogic = second.procedural_logic[0]
    assert first_logic.target_var_uid == first.state_vars[0].uid
    assert second_logic.target_var_uid == second.state_vars[0].uid
    assert first_logic.target_var_uid != second_logic.target_var_uid
    assert first_logic is not second_logic
    assert parsed.deferred_assignment_logic[0].target_var_uid is None
    assert parsed.deferred_assignment_logic[0].target_var_name == 'x1'


@pytest.mark.parametrize(('bindings', 'message'), (
    (list(), 'incomplete'),
    (list(('x2',)), 'no matching sStates alias'),
    (list(('x1', 'x2')), 'incomplete'),
))
def test_unproven_instance_aliases_are_rejected(bindings: list[str], message: str) -> None:
    """Do not infer a destination from state count or another instance's alias.

    :param bindings: Missing, incompatible or oversized instance state bindings.
    :param message: Expected fail-closed diagnostic.
    :return: None.
    """
    parsed: ParsedDgsBlockDefinition = _parse_frt()
    with pytest.raises((ValueError, UnsupportedDgsExpression), match=message):
        _build_block_from_parsed(parsed, dict(), reference=_reference('634', bindings))


def test_duplicate_state_aliases_are_rejected() -> None:
    """Never choose the first of two local states with the same parent alias.

    :return: None.
    """
    parsed: ParsedDgsBlockDefinition = _parse_frt()
    parsed.blkdef.states.append('z')
    with pytest.raises(ValueError, match='ambiguous state alias'):
        _build_block_from_parsed(parsed, dict(), reference=_reference('634', list(('x1', 'x1'))))


def test_resolved_state_event_roundtrips_and_resets_only_its_timer() -> None:
    """Persist the canonical target and execute at the accepted event boundary.

    :return: None.
    """
    block: Block = _build_block_from_parsed(_parse_frt(), dict(), reference=_reference('634', list(('x1',))))
    restored: Block = roundtrip_block(block, ProceduralLogicCodec())
    problem: EmtProblemTemplate = EmtProblemTemplate(
        sys_block=restored, glob_time=Var('test_time'), static_parameter_values_mapping=dict())
    updater: BlockProceduralLogicUpdater | None = build_boundary_updater_from_block(problem)
    assert updater is not None
    state: np.ndarray = problem.get_x0().copy()
    parameters: np.ndarray = problem.event_params_values.copy()
    timer_index: int = problem.get_var_idx(restored.state_vars[0])
    updater.initialize_modes(0.0, state, parameters)
    assert updater.get_next_forced_event_time(0.6, 0.9) == 0.75
    state[timer_index] = 0.75
    updater.update(0.75, state, parameters)
    assert state[timer_index] == pytest.approx(0.75)
    updater.commit_boundary(0.75, state, parameters)
    assert state[timer_index] == pytest.approx(0.0)
    state[timer_index] = 0.2
    updater.commit_boundary(1.0, state, parameters)
    assert state[timer_index] == pytest.approx(0.2)
