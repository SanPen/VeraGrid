# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Reconstruct nested graphical instances rather than empty public interfaces."""
from __future__ import annotations

from pathlib import Path

import pytest

from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
from VeraGridEngine.IO.dgs.dgs_objects import BlkDef, BlkRef, BlkSig, BlkSlot, ElmComp, ElmDsl
from VeraGridEngine.IO.dgs.dgs_to_blocks import (
    DgsRootBlockResult, build_dgs_root_block_from_circuit, build_direct_root_elmcomp_block,
    parse_dgs_block_definitions_from_circuit,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Expr, Var


def cable(identifier: str, source: str, target: str, source_port: int = 0,
          target_port: int = 0, source_kind: int = 2, target_kind: int = 1) -> BlkSig:
    """Declare an exact graphical port connection.

    :param identifier: Source cable identifier.
    :param source: Source node identifier.
    :param target: Target node identifier.
    :param source_port: Source connector ordinal.
    :param target_port: Target connector ordinal.
    :param source_kind: Input or output connector code.
    :param target_kind: Input or output connector code.
    :return: Source cable.
    """
    result: BlkSig = BlkSig()
    result.ID = identifier
    result.pnodfrom = source
    result.pnodto = target
    result.inodfrom = source_port
    result.inodto = target_port
    result.iconfrom = source_kind
    result.iconto = target_kind
    result.loc_name = identifier
    return result


def nested_source() -> DgsCircuit:
    """Create two occurrences of one graphical macro with independent gains.

    :return: Complete source with a direct ElmDsl slot and nested BlkRefs.
    """
    source: DgsCircuit = DgsCircuit()
    identifier: str
    inputs: list[str]
    outputs: list[str]
    params: list[str]
    equations: list[str]
    for identifier, inputs, outputs, params, equations in (
        ('frame', list(('u',)), list(('a', 'b')), list(), list()),
        ('outer', list(('u',)), list(('a', 'b')), list(), list()),
        ('nested', list(('x',)), list(('y',)), list(('K',)), list()),
        ('gain', list(('v',)), list(('z',)), list(('g',)), list(('z=g*v',))),
    ):
        definition: BlkDef = BlkDef()
        definition.ID = identifier
        definition.loc_name = identifier
        definition.isMacro = 1
        definition.inputs = inputs
        definition.outputs = outputs
        definition.params = params
        definition.equations_raw = equations
        source.blkdefs.append(definition)
    root: ElmComp = ElmComp()
    root.ID = 'root'
    root.loc_name = 'Nested example'
    root.typ_id = 'frame'
    root.pblk = list(('slot',))
    root.pelm = list(('dsl',))
    source.elmcomps.append(root)
    instance: ElmDsl = ElmDsl()
    instance.ID = 'dsl'
    instance.typ_id = 'outer'
    instance.loc_name = 'outer'
    instance.fold_id = 'root'
    source.elmdsls.append(instance)
    slot: BlkSlot = BlkSlot()
    slot.ID = 'slot'
    slot.loc_name = 'outer'
    slot.filtmod = 'ElmDsl*'
    slot.inputs = list(('u',))
    slot.outputs = list(('a', 'b'))
    source.blkslots.append(slot)
    gain: str
    for identifier, gain in (('first', '2'), ('second', '3')):
        reference: BlkRef = BlkRef()
        reference.ID = identifier
        reference.typ_id = 'nested'
        reference.cdisName = identifier
        reference.params = list((gain,))
        source.blkrefs.append(reference)
        output_port: int = 0 if identifier == 'first' else 1
        source.blksigs.extend((cable(f'in_{identifier}', 'outer', identifier, source_kind=1),
                               cable(f'out_{identifier}', identifier, 'outer', target_port=output_port, target_kind=2)))
    leaf: BlkRef = BlkRef()
    leaf.ID = 'leaf'
    leaf.typ_id = 'gain'
    leaf.cdisName = 'Gain'
    leaf.params = list(('K',))
    source.blkrefs.append(leaf)
    source.blksigs.extend((cable('nested_in', 'nested', 'leaf', source_kind=1),
                           cable('nested_out', 'leaf', 'nested', target_kind=2)))
    return source


def materialize(source: DgsCircuit) -> Block:
    """Run the production direct-root construction path.

    :param source: Complete source circuit.
    :return: Direct dynamic controller.
    """
    root: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        source, parse_dgs_block_definitions_from_circuit(source), root_name='Nested example', root_dgs_id='root')
    return build_direct_root_elmcomp_block(source, root).root_block.children[0]


@pytest.mark.parametrize("extra_depth", (0, 1, 2))
def test_nested_macros_keep_equations_parameters_and_independent_instances(extra_depth: int) -> None:
    """Both macro outputs must be produced by their own bound formula leaves.

    :param extra_depth: Additional graphical containers before the formula leaf.
    :return: None.
    """
    source: DgsCircuit = nested_source()
    previous_type: str = 'gain'
    depth: int
    for depth in range(extra_depth):
        wrapper: BlkDef = BlkDef()
        wrapper.ID = f'wrapper_{depth}'
        wrapper.loc_name = wrapper.ID
        wrapper.inputs = list(('input',))
        wrapper.outputs = list(('output',))
        wrapper.params = list(('M',))
        source.blkdefs.append(wrapper)
        reference: BlkRef = BlkRef()
        reference.ID = f'wrapper_ref_{depth}'
        reference.typ_id = previous_type
        reference.cdisName = reference.ID
        reference.params = list(('M',))
        source.blkrefs.append(reference)
        source.blksigs.extend((cable(f'wrapper_in_{depth}', wrapper.ID, reference.ID, source_kind=1),
                               cable(f'wrapper_out_{depth}', reference.ID, wrapper.ID, target_kind=2)))
        previous_type = wrapper.ID
    original_leaf: BlkRef = next(reference for reference in source.blkrefs if reference.ID == 'leaf')
    original_leaf.typ_id = previous_type
    block: Block = materialize(source)
    assert len(block.children) == 2
    first: Block = block.children[0]
    second: Block = block.children[1]
    assert first.out_vars[0].uid != second.out_vars[0].uid
    nested: Block
    gain: float
    for nested, gain in zip(block.children, (2.0, 3.0)):
        assert len(nested.children) == 1
        leaf: Block = nested.get_all_blocks()[-1]
        assert nested.out_vars[0] is leaf.algebraic_vars[0]
        assert leaf.in_vars[0].uid == block.in_vars[0].uid
        bindings: dict[int, float] = dict(((block.in_vars[0].uid, 4.0),))
        owner: Block
        variable: Var
        expression: Expr
        for owner in nested.get_all_blocks():
            for variable, expression in owner.event_dict.items():
                bindings[variable.uid] = expression.eval_uid(bindings)
        output: Var = nested.out_vars[0]
        bindings[output.uid] = 4.0 * gain
        assert leaf.algebraic_eqs[0].eval_uid(bindings) == pytest.approx(0.0)


def test_recursive_graphical_definition_is_rejected_with_its_path() -> None:
    """Detect recursive containment without confusing independent occurrences.

    :return: None.
    """
    source: DgsCircuit = nested_source()
    leaf: BlkRef = next(reference for reference in source.blkrefs if reference.ID == 'leaf')
    leaf.typ_id = 'nested'
    with pytest.raises(ValueError, match='Recursive graphical BlkRef containment: outer -> nested -> nested'):
        materialize(source)


def test_dfig_nested_rotations_have_real_output_owners_before_partition() -> None:
    """Both exported dq rotations must retain executable Cartesian output equations.

    :return: None.
    """
    path: Path = Path(__file__).resolve().parents[4] / 'trunk/dynamics/DFIG_RMS_v5_Export.dgs'
    if not path.is_file():
        pytest.skip('Local PowerFactory DFIG export is unavailable')
    else:
        pass
    source: DgsCircuit = DgsCircuit()
    source.parse_dgs(str(path))
    root: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        source, parse_dgs_block_definitions_from_circuit(source), root_name='RMS', root_dgs_id='947')
    model: Block = build_direct_root_elmcomp_block(source, root).root_block
    rotations: list[Block] = list(child for child in model.get_all_blocks() if child.name == 'dqg-dqs_sub')
    assert len(rotations) == 2
    owned_uids: set[int] = set(variable.uid for child in model.get_all_blocks()
                                for variable in child.algebraic_vars)
    rotation: Block
    for rotation in rotations:
        assert len(rotation.children) == 0
        assert len(rotation.algebraic_eqs) == 2
        assert all(variable.uid in owned_uids for variable in rotation.out_vars)
        assert all(any(variable.uid == solved.uid for child in rotation.get_all_blocks()
                       for solved in child.algebraic_vars) for variable in rotation.out_vars)


def test_state_initializers_follow_nested_instance_aliases_and_connected_inputs() -> None:
    """Materialize symbolic conditions with executable state and input objects.

    :return: None.
    """
    source: DgsCircuit = nested_source()
    definitions: dict[str, BlkDef] = dict((definition.ID, definition) for definition in source.blkdefs)
    # Export the same local state through two independent occurrences. The
    # outer initialization also depends on a state belonging to its sibling.
    definitions['outer'].states = list(('first_state', 'second_state'))
    definitions['outer'].equations_raw = list(('inc(first_state)=5', 'inc(second_state)=first_state+u'))
    definitions['nested'].states = list(('nested_state',))
    definitions['gain'].states = list(('local_state',))
    definitions['gain'].equations_raw = list(('local_state.=g*v', 'z=local_state', 'inc(z)=v*g'))
    reference: BlkRef
    for reference in source.blkrefs:
        if reference.ID == 'first':
            reference.states = list(('first_state',))
        elif reference.ID == 'second':
            reference.states = list(('second_state',))
        else:
            reference.states = list(('nested_state',))
    model: Block = materialize(source)
    first: Block = model.children[0].get_all_blocks()[-1]
    second: Block = model.children[1].get_all_blocks()[-1]
    first_state: Var = first.state_vars[0]
    second_state: Var = second.state_vars[0]
    assert first_state.uid != second_state.uid
    # Dictionary keys use the executable objects, so duplication cannot split
    # an initialized alias from its owning state by stable identity.
    assert next(variable for variable in model.init_eqs if variable.uid == first_state.uid) is first_state
    assert next(variable for variable in model.init_eqs if variable.uid == second_state.uid) is second_state
    assert model.init_eqs[first_state].eval_uid(dict()) == pytest.approx(5.0)
    dependencies: list[Var] = model.init_eqs[second_state].get_vars()
    assert any(variable is first_state for variable in dependencies)
    assert any(variable is model.in_vars[0] for variable in dependencies)
    assert model.init_eqs[second_state].eval_uid(
        dict(((first_state.uid, 5.0), (model.in_vars[0].uid, 2.0)))) == pytest.approx(7.0)
    child: Block
    for child in (first, second):
        expression: Expr = child.init_eqs[child.out_vars[0]]
        assert any(variable is model.in_vars[0] for variable in expression.get_vars())


def test_dfig_dc_link_initial_condition_targets_its_executable_integrator() -> None:
    """Keep the exported DC-link state condition attached after nested assembly.

    :return: None.
    """
    path: Path = Path(__file__).resolve().parents[4] / 'trunk/dynamics/DFIG_RMS_v5_Export.dgs'
    if not path.is_file():
        pytest.skip('Local PowerFactory DFIG export is unavailable')
    else:
        pass
    source: DgsCircuit = DgsCircuit()
    source.parse_dgs(str(path))
    root: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        source, parse_dgs_block_definitions_from_circuit(source), root_name='RMS', root_dgs_id='947')
    model: Block = build_direct_root_elmcomp_block(source, root).root_block
    dc_link: Block = next(block for block in model.get_all_blocks() if block.name == 'Vdc_Calc')
    integrator: Block = next(block for block in dc_link.get_all_blocks() if block.name == '1/s')
    state: Var = integrator.state_vars[0]
    assert next(variable for variable in dc_link.init_eqs if variable.uid == state.uid) is state
    assert dc_link.init_eqs[state].eval_uid(dict()) == pytest.approx(1150.0)
    owned_uids: set[int] = set(variable.uid for block in model.get_all_blocks()
                                for variable in block.state_vars)
    assert all(variable.uid in owned_uids for block in model.get_all_blocks()
               for variable in block.init_eqs if variable.name.endswith('__x'))
