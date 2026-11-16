# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Resolve routed wires by exact producer ports and exported diagram scope."""

from pathlib import Path

import pytest

from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.IO.dgs.dgs_graphical_routing import DgsGraphicalRoutingResolver, build_graphical_node_scopes, build_graphical_reference_owners, build_graphical_reference_owner_candidates
from VeraGridEngine.IO.dgs.dgs_objects import BlkDef, BlkFrom, BlkGoto, BlkRef, BlkSig, IntGrf, IntGrfgroup, IntGrfnet
from VeraGridEngine.IO.dgs.dgs_to_blocks import (
    DgsGraphicTreeResult, DgsRootBlockResult, build_dgs_root_block_from_circuit,
    extract_root_slot_graphical_tree_from_circuit, parse_dgs_block_definitions_from_circuit,
)


def _cable(identifier: str, source: str, target: str, label: str,
           source_port: int = 0, target_port: int = 0) -> BlkSig:
    """Declare a wire independently of the source port's symbolic name.

    :param identifier: Cable FID.
    :param source: Exact source-node FID.
    :param target: Exact destination-node FID.
    :param label: Descriptive cable label.
    :param source_port: Raw source port ordinal.
    :param target_port: Raw destination port ordinal.
    :return: Source wire declaration.
    """
    cable: BlkSig = BlkSig()
    cable.ID = identifier
    cable.pnodfrom = source
    cable.pnodto = target
    cable.loc_name = label
    cable.inodfrom = source_port
    cable.inodto = target_port
    return cable


def _route_source() -> tuple[DgsCircuit, BlkFrom, BlkGoto, BlkSig]:
    """Create the same topology as the Vdc_out0 route in the reported model.

    :return: Source graph, reader, writer and wire to the macro output.
    """
    source: DgsCircuit = DgsCircuit()
    root: BlkDef = BlkDef()
    root.ID = 'macro'
    source.blkdefs.append(root)
    producer: BlkRef = BlkRef()
    producer.ID = 'producer'
    source.blkrefs.append(producer)
    reader: BlkFrom = BlkFrom()
    reader.ID = 'from'
    reader.signals = list(('Vdc_out0',))
    source.blkfroms.append(reader)
    writer: BlkGoto = BlkGoto()
    writer.ID = 'goto'
    source.blkgotos.append(writer)
    output: BlkSig = _cable('out', 'from', 'macro', 'Vdc_unfiltered', target_port=1)
    source.blksigs.extend((_cable('in', 'producer', 'goto', 'Vdc_out0', source_port=2), output))
    return source, reader, writer, output


def test_route_preserves_exact_producer_port_without_mutating_source() -> None:
    """A renamed output cable still resolves to the actual block output.

    :return: None.
    """
    source: DgsCircuit
    reader: BlkFrom
    writer: BlkGoto
    output: BlkSig
    source, reader, writer, output = _route_source()
    resolver: DgsGraphicalRoutingResolver = DgsGraphicalRoutingResolver(source, 'macro', list(), set(('macro', reader.ID)))
    nodes: set[str] = resolver.expand_selected_nodes()
    assert 'producer' in nodes
    assert writer.ID in nodes
    resolved: BlkSig = resolver.resolve(output)
    assert resolved.pnodfrom == 'producer'
    assert resolved.inodfrom == 2
    assert resolved.pnodto == 'macro'
    assert resolved.inodto == 1
    assert resolved.ID == 'out'
    assert resolved.loc_name == 'Vdc_unfiltered'
    assert output.pnodfrom == 'from'


def test_unscoped_homonymous_gotos_are_rejected() -> None:
    """Do not pick by ordering or graphical distance when scope is missing.

    :return: None.
    """
    source: DgsCircuit
    reader: BlkFrom
    writer: BlkGoto
    output: BlkSig
    source, reader, writer, output = _route_source()
    other: BlkGoto = BlkGoto()
    other.ID = 'other_goto'
    source.blkgotos.append(other)
    source.blksigs.append(_cable('other_in', 'other_producer', other.ID, 'Vdc_out0'))
    resolver: DgsGraphicalRoutingResolver = DgsGraphicalRoutingResolver(source, 'macro', list(), set(('macro', reader.ID)))
    with pytest.raises(ValueError, match='has 2 producers'):
        resolver.resolve(output)


def test_exported_diagram_scope_disambiguates_nested_graphics() -> None:
    """Follow IntGrfgroup parents to the owning IntGrfnet data folder.

    :return: None.
    """
    source: DgsCircuit
    reader: BlkFrom
    writer: BlkGoto
    output: BlkSig
    source, reader, writer, output = _route_source()
    other: BlkGoto = BlkGoto()
    other.ID = 'other_goto'
    source.blkgotos.append(other)
    source.blksigs.append(_cable('other_in', 'other_producer', other.ID, 'Vdc_out0'))
    diagram: IntGrfnet = IntGrfnet()
    diagram.ID = 'diagram'
    diagram.pDataFolder = 'macro'
    foreign: IntGrfnet = IntGrfnet()
    foreign.ID = 'foreign'
    foreign.pDataFolder = 'other_macro'
    source.intgrfnets.extend((diagram, foreign))
    group: IntGrfgroup = IntGrfgroup()
    group.ID = 'group'
    group.fold_id = 'diagram'
    source.intgrfgroups.append(group)
    identifier: str
    folder: str
    for identifier, folder in ((reader.ID, group.ID), (writer.ID, group.ID), (other.ID, foreign.ID)):
        graphic: IntGrf = IntGrf()
        graphic.ID = f'view_{identifier}'
        graphic.fold_id = folder
        graphic.pDataObj = identifier
        source.intgrfs.append(graphic)
    scopes: dict[str, set[str]] = build_graphical_node_scopes(source)
    assert scopes[writer.ID] == set(('macro',))
    resolver: DgsGraphicalRoutingResolver = DgsGraphicalRoutingResolver(source, 'macro', list(), set(('macro', reader.ID)))
    assert resolver.resolve(output).pnodfrom == 'producer'


def test_routing_cycle_and_missing_producer_are_diagnosed() -> None:
    """Report a broken path instead of assigning a zero or using name aliases.

    :return: None.
    """
    source: DgsCircuit
    reader: BlkFrom
    writer: BlkGoto
    output: BlkSig
    source, reader, writer, output = _route_source()
    source.blksigs[0].pnodfrom = reader.ID
    source.blksigs[0].inodfrom = 0
    resolver: DgsGraphicalRoutingResolver = DgsGraphicalRoutingResolver(source, 'macro', list(), set(('macro', reader.ID)))
    with pytest.raises(ValueError, match='routing cycle'):
        resolver.resolve(output)
    source.blksigs.pop(0)
    resolver = DgsGraphicalRoutingResolver(source, 'macro', list(), set(('macro', reader.ID)))
    with pytest.raises(ValueError, match='has 0 producers'):
        resolver.resolve(output)


def test_route_can_read_an_exact_macro_input() -> None:
    """Resolve a boundary input by its declared ordinal without alias guessing.

    :return: None.
    """
    source: DgsCircuit
    reader: BlkFrom
    writer: BlkGoto
    output: BlkSig
    source, reader, writer, output = _route_source()
    source.blksigs.pop(0)
    resolver: DgsGraphicalRoutingResolver = DgsGraphicalRoutingResolver(source, 'macro', list(('unused', 'Vdc_out0')), set(('macro', reader.ID)))
    resolved: BlkSig = resolver.resolve(output)
    assert resolved.pnodfrom == 'macro'
    assert resolved.inodfrom == 1
    assert resolved.iconfrom == 1


@pytest.mark.parametrize("boundary_source", (False, True))
def test_macro_outputs_and_internal_inputs_use_the_same_routed_producer(boundary_source: bool) -> None:
    """Keep filtered and unfiltered signals distinct through full materialization.

    :param boundary_source: Route a macro input instead of a child output.
    :return: None.
    """
    path: Path = Path(__file__).resolve().parents[2] / 'data' / 'grids' / 'DGS' / 'graphical_from_goto_routes.dgs'
    source: DgsCircuit = DgsCircuit()
    source.parse_dgs(str(path))
    if boundary_source:
        incoming: BlkSig = next(cable for cable in source.blksigs if cable.ID == 'route_in')
        incoming.pnodfrom = 'MACRO'
        incoming.iconfrom = 1
    else:
        pass
    root: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        source, parse_dgs_block_definitions_from_circuit(source), 'Routing example')
    tree: DgsGraphicTreeResult | None = extract_root_slot_graphical_tree_from_circuit(source, root, 'Measure')
    assert tree is not None
    block: Block = tree.view_block
    calculation: Block = next(child for child in block.children if child.name == 'Calc')
    filtering: Block = next(child for child in block.children if child.name == 'Filter')
    assert block.out_vars[0] is filtering.out_vars[0]
    if boundary_source:
        assert block.out_vars[1] is block.in_vars[0]
        assert filtering.in_vars[0] is block.in_vars[0]
        assert block.in_vars[0].name == 'u'
    else:
        assert block.out_vars[1] is calculation.out_vars[0]
        assert filtering.in_vars[0] is calculation.out_vars[0]
    assert filtering.out_vars[0].uid != calculation.out_vars[0].uid
    bindings: dict[int, float] = dict(((block.in_vars[0].uid, 3.0),))
    for child in (calculation, filtering):
        output: Var = child.out_vars[0]
        bindings[output.uid] = 0.0
        bindings[output.uid] = -child.algebraic_eqs[0].eval_uid(bindings)
    assert bindings[block.out_vars[1].uid] == pytest.approx(3.0 if boundary_source else 6.0)
    assert bindings[block.out_vars[0].uid] == pytest.approx(9.0 if boundary_source else 18.0)


@pytest.mark.parametrize("shared_reader", (False, True))
def test_chained_from_goto_routes_preserve_the_final_producer_port(shared_reader: bool) -> None:
    """Follow multiple routing stages rather than equating all their labels.

    :param shared_reader: Follow a different signal port on the same From object.
    :return: None.
    """
    source: DgsCircuit
    reader: BlkFrom
    writer: BlkGoto
    output: BlkSig
    source, reader, writer, output = _route_source()
    intermediate: BlkFrom
    if shared_reader:
        intermediate = reader
        intermediate.signals.append('inner_route')
    else:
        intermediate = BlkFrom()
        intermediate.ID = 'intermediate'
        intermediate.signals = list(('inner_route',))
        source.blkfroms.append(intermediate)
    upstream: BlkGoto = BlkGoto()
    upstream.ID = 'upstream'
    source.blkgotos.append(upstream)
    source.blksigs[0].pnodfrom = intermediate.ID
    source.blksigs[0].inodfrom = 1 if shared_reader else 0
    source.blksigs.append(_cable('inner', 'producer', upstream.ID, 'inner_route', source_port=2))
    resolver: DgsGraphicalRoutingResolver = DgsGraphicalRoutingResolver(source, 'macro', list(), set(('macro', reader.ID)))
    resolved: BlkSig = resolver.resolve(output)
    assert resolved.pnodfrom == 'producer'
    assert resolved.inodfrom == 2


def test_invalid_routed_source_port_is_not_replaced_by_a_name_alias() -> None:
    """Carry the original port through to the executable connector validator.

    :return: None.
    """
    path: Path = Path(__file__).resolve().parents[2] / 'data' / 'grids' / 'DGS' / 'graphical_from_goto_routes.dgs'
    source: DgsCircuit = DgsCircuit()
    source.parse_dgs(str(path))
    incoming: BlkSig = next(cable for cable in source.blksigs if cable.ID == 'route_in')
    incoming.inodfrom = 99
    root: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        source, parse_dgs_block_definitions_from_circuit(source), 'Routing example')
    with pytest.raises(ValueError, match='invalid source output'):
        extract_root_slot_graphical_tree_from_circuit(source, root, 'Measure')


def _add_lexical_owner_evidence(source: DgsCircuit) -> tuple[BlkRef, BlkRef]:
    """Add the two disconnected components found in the reported Id ambiguity.

    :param source: Routing fixture with a macro, reader and primary writer.
    :return: Primary reference and a bound peer of the foreign producer.
    """
    parent: BlkDef = source.blkdefs[0]
    parent.params = list(('direction_I', 'T_dq_I'))
    parent.states = list(('x6', 'x7'))
    parent.internals = list(('d1', 'alpha2'))
    primary: BlkRef = source.blkrefs[0]
    primary.typ_id = 'transform_definition'
    primary.params = list(('direction_I', 'T_dq_I'))
    primary.states = list(('x6', 'x7'))
    primary.internals = list(('d1', 'alpha2'))
    foreign_parent: BlkDef = BlkDef()
    foreign_parent.ID = 'foreign_macro'
    foreign_parent.params = list(('Tdel', 'Tlength', 'Avg_Init'))
    foreign_parent.internals = list(('avg_o', 'avg_y'))
    source.blkdefs.append(foreign_parent)
    maximum: BlkRef = BlkRef()
    maximum.ID = 'maximum'
    source.blkrefs.append(maximum)
    average: BlkRef = BlkRef()
    average.ID = 'average'
    average.typ_id = 'average_definition'
    average.params = list(('Tdel', 'Tlength', 'Avg_Init'))
    average.internals = list(('avg_o', 'avg_y'))
    source.blkrefs.append(average)
    foreign_writer: BlkGoto = BlkGoto()
    foreign_writer.ID = 'foreign_writer'
    source.blkgotos.append(foreign_writer)
    source.blksigs.extend((
        _cable('foreign_tag', maximum.ID, foreign_writer.ID, 'Vdc_out0'),
        _cable('foreign_peer', average.ID, maximum.ID, 'Mean_Id'),
    ))
    return primary, average


def test_typed_bindings_disambiguate_homonymous_gotos_without_diagram_metadata() -> None:
    """Propagate lexical ownership through the raw physical component only.

    :return: None.
    """
    source: DgsCircuit
    reader: BlkFrom
    writer: BlkGoto
    output: BlkSig
    source, reader, writer, output = _route_source()
    primary: BlkRef
    average: BlkRef
    primary, average = _add_lexical_owner_evidence(source)
    owners: dict[str, str] = build_graphical_reference_owners(source)
    assert owners[primary.ID] == 'macro'
    assert owners[average.ID] == 'foreign_macro'
    assert 'maximum' not in owners
    resolver: DgsGraphicalRoutingResolver = DgsGraphicalRoutingResolver(source, 'macro', list(), set(('macro', reader.ID)))
    resolved: BlkSig = resolver.resolve(output)
    assert resolved.pnodfrom == primary.ID
    assert resolver.component_owners[writer.ID] == set(('macro',))
    assert resolver.component_owners['foreign_writer'] == set(('foreign_macro',))
    assert resolver.component_owners['maximum'] == set(('foreign_macro',))
    # A second instance of the foreign macro must select its own route instead.
    other_reader: BlkFrom = BlkFrom()
    other_reader.ID = 'foreign_reader'
    other_reader.signals = list(('Vdc_out0',))
    source.blkfroms.append(other_reader)
    other_output: BlkSig = _cable('foreign_out', other_reader.ID, 'foreign_macro', 'result')
    source.blksigs.append(other_output)
    foreign: DgsGraphicalRoutingResolver = DgsGraphicalRoutingResolver(source, 'foreign_macro', list(), set(('foreign_macro', other_reader.ID)))
    assert foreign.resolve(other_output).pnodfrom == 'maximum'


@pytest.mark.parametrize('invalid_case', ('duplicate_owner', 'wrong_category', 'missing_binding', 'missing_upper_binding'))
def test_incomplete_or_ambiguous_binding_evidence_never_guesses_an_owner(invalid_case: str) -> None:
    """Require a unique complete match in the corresponding declaration categories.

    :param invalid_case: Why the reference cannot establish a lexical owner.
    :return: None.
    """
    source: DgsCircuit
    reader: BlkFrom
    writer: BlkGoto
    output: BlkSig
    source, reader, writer, output = _route_source()
    primary: BlkRef
    average: BlkRef
    primary, average = _add_lexical_owner_evidence(source)
    if invalid_case == 'duplicate_owner':
        duplicate: BlkDef = BlkDef()
        duplicate.ID = 'another_compatible_macro'
        duplicate.params = list(source.blkdefs[0].params)
        duplicate.states = list(source.blkdefs[0].states)
        duplicate.internals = list(source.blkdefs[0].internals)
        source.blkdefs.append(duplicate)
    elif invalid_case == 'wrong_category':
        source.blkdefs[0].states.remove('x6')
        source.blkdefs[0].params.append('x6')
    elif invalid_case == 'missing_upper_binding':
        primary.upper_limit_params = list(('unresolved_limit',))
    else:
        primary.internals.append('unresolved_binding')
    assert primary.ID not in build_graphical_reference_owners(source)


def test_parameter_expression_bindings_exclude_called_function_names() -> None:
    """Extract lexical dependencies without evaluating or mistaking max for a parameter.

    :return: None.
    """
    source: DgsCircuit
    reader: BlkFrom
    writer: BlkGoto
    output: BlkSig
    source, reader, writer, output = _route_source()
    primary: BlkRef
    average: BlkRef
    primary, average = _add_lexical_owner_evidence(source)
    primary.params = list(('2*direction_I + max(T_dq_I,0.1)',))
    primary.upper_limit_params = list(('1.1*upper_limit',))
    source.blkdefs[0].upper_limit_params = list(('upper_limit',))
    assert build_graphical_reference_owners(source)[primary.ID] == 'macro'


def test_conflicting_owners_on_one_component_are_reported() -> None:
    """Reject incompatible lexical evidence instead of merging macro scopes.

    :return: None.
    """
    source: DgsCircuit
    reader: BlkFrom
    writer: BlkGoto
    output: BlkSig
    source, reader, writer, output = _route_source()
    primary: BlkRef
    average: BlkRef
    primary, average = _add_lexical_owner_evidence(source)
    source.blksigs.append(_cable('invalid_cross_macro_wire', primary.ID, average.ID, 'cross'))
    resolver: DgsGraphicalRoutingResolver = DgsGraphicalRoutingResolver(source, 'macro', list(), set(('macro', reader.ID)))
    with pytest.raises(ValueError, match='conflicting macro owners'):
        resolver.resolve(output)


def test_ambiguous_foreign_owners_exclude_the_current_macro() -> None:
    """Retain exclusion evidence instead of treating several owners as unknown.

    :return: None.
    """
    source: DgsCircuit
    reader: BlkFrom
    writer: BlkGoto
    output: BlkSig
    source, reader, writer, output = _route_source()
    primary: BlkRef
    average: BlkRef
    primary, average = _add_lexical_owner_evidence(source)
    foreign_copy: BlkDef = BlkDef()
    foreign_copy.ID = 'foreign_alternative'
    foreign_copy.params = list(source.blkdefs[1].params)
    foreign_copy.internals = list(source.blkdefs[1].internals)
    source.blkdefs.append(foreign_copy)
    candidates: dict[str, set[str]] = build_graphical_reference_owner_candidates(source)
    assert candidates[average.ID] == set(('foreign_macro', 'foreign_alternative'))
    # Mirror cable 1187: the local writer is driven by a declared macro input.
    source.blkdefs[0].inputs = list(('Vlv',))
    source.blksigs[0].pnodfrom = 'macro'
    source.blksigs[0].inodfrom = 0
    source.blksigs[0].iconfrom = 1
    resolver: DgsGraphicalRoutingResolver = DgsGraphicalRoutingResolver(source, 'macro', list(('Vlv',)), set(('macro', reader.ID)))
    assert resolver.resolve(output).pnodfrom == 'macro'
    assert resolver.component_owners['foreign_writer'] == set(('foreign_macro', 'foreign_alternative'))


def test_a_compatible_ambiguous_owner_remains_a_real_candidate() -> None:
    """Do not prefer a unique owner when another compatible source still exists.

    :return: None.
    """
    source: DgsCircuit
    reader: BlkFrom
    writer: BlkGoto
    output: BlkSig
    source, reader, writer, output = _route_source()
    primary: BlkRef
    average: BlkRef
    primary, average = _add_lexical_owner_evidence(source)
    source.blkdefs[0].params.extend(source.blkdefs[1].params)
    source.blkdefs[0].internals.extend(source.blkdefs[1].internals)
    candidates: dict[str, set[str]] = build_graphical_reference_owner_candidates(source)
    assert candidates[average.ID] == set(('macro', 'foreign_macro'))
    resolver: DgsGraphicalRoutingResolver = DgsGraphicalRoutingResolver(source, 'macro', list(), set(('macro', reader.ID)))
    with pytest.raises(ValueError, match='has 2 producers'):
        resolver.resolve(output)


def test_intersection_of_partial_component_evidence_proves_one_owner() -> None:
    """Combine all connected references without guessing from their separate sets.

    :return: None.
    """
    source: DgsCircuit
    reader: BlkFrom
    writer: BlkGoto
    output: BlkSig
    source, reader, writer, output = _route_source()
    source.blkdefs[0].params = list(('alpha', 'beta'))
    first_parent: BlkDef = BlkDef()
    first_parent.ID = 'first_parent'
    first_parent.params = list(('alpha',))
    second_parent: BlkDef = BlkDef()
    second_parent.ID = 'second_parent'
    second_parent.params = list(('beta',))
    source.blkdefs.extend((first_parent, second_parent))
    source.blkrefs[0].params = list(('alpha',))
    peer: BlkRef = BlkRef()
    peer.ID = 'peer'
    peer.params = list(('beta',))
    source.blkrefs.append(peer)
    source.blksigs.append(_cable('peer_input', peer.ID, 'producer', 'input'))
    candidates: dict[str, set[str]] = build_graphical_reference_owner_candidates(source)
    assert candidates['producer'] == set(('macro', 'first_parent'))
    assert candidates[peer.ID] == set(('macro', 'second_parent'))
    resolver: DgsGraphicalRoutingResolver = DgsGraphicalRoutingResolver(source, 'macro', list(), set(('macro', reader.ID)))
    assert resolver.resolve(output).pnodfrom == 'producer'
    assert resolver.component_owners[writer.ID] == set(('macro',))


def test_missing_binding_evidence_differs_from_no_compatible_owner() -> None:
    """An unconstrained component stays possible; an incompatible one is excluded.

    :return: None.
    """
    source: DgsCircuit
    reader: BlkFrom
    writer: BlkGoto
    output: BlkSig
    source, reader, writer, output = _route_source()
    resolver: DgsGraphicalRoutingResolver = DgsGraphicalRoutingResolver(source, 'macro', list(), set(('macro', reader.ID)))
    assert resolver.resolve(output).pnodfrom == 'producer'
    assert resolver.component_owners[writer.ID] is None
    source.blkrefs[0].params = list(('missing_parent_parameter',))
    resolver = DgsGraphicalRoutingResolver(source, 'macro', list(), set(('macro', reader.ID)))
    with pytest.raises(ValueError, match='has 0 producers'):
        resolver.resolve(output)
    assert resolver.component_owners[writer.ID] == set()
