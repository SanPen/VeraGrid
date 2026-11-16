# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Exercise static bus synchronization before editor document creation."""
from __future__ import annotations

import numpy as np
import pytest
from PySide6 import QtCore, QtWidgets

from VeraGrid.Gui.DynamicModelEditor.Editor import dynamic_editor_graphics as graph
from VeraGrid.Gui.DynamicModelEditor.Editor.dynamic_block_editor import DynamicBlockEditorGUI
from VeraGrid.Gui.DynamicModelEditor.Workspace.Tabs.dynamic_editor_tab import DynamicEditorTab
from VeraGrid.Gui.DynamicModelEditor.Workspace.dynamic_editor_entries import DynamicEditorEntry, build_dynamic_editor_entry
from VeraGrid.Gui.DynamicModelEditor.Workspace.dynamic_editor_workspace_session import DynamicEditorWorkspaceSession
from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Parents.dynamic_bus_parent import EmtBusConnectionSide
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Templates.Emt.buses.bus_emt_template import get_bus_emt_template
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.Utils.Symbolic.templates_common_functions import (
    EmtBusShellSyncResult,
    connect_models_by_reference,
    synchronize_emt_bus_shell_with_grid,
)
from VeraGridEngine.Devices.Branches.overhead_line_type import OverheadLineType, create_known_abc_overhead_template
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import BlockType, DynamicSimulationMode, VarPowerFlowReferenceType


def _set_phases(grid: MultiCircuit, line: Line, phases: tuple[int, ...]) -> None:
    """Replace a static line phase layout.

    :param grid: Owning grid.
    :param line: Static line providing the bus phase mask.
    :param phases: Enabled NABC phase indices.
    :return: None.
    """
    # Use the same physical template API as ordinary static phase edits.
    impedance: np.ndarray = np.eye(len(phases), dtype=complex) * (0.3 + 1j)
    admittance: np.ndarray = np.eye(len(phases), dtype=complex) * 1e-6j
    template: OverheadLineType = create_known_abc_overhead_template(
        name="phase layout", z_nabc=impedance, ysh_nabc=admittance,
        phases=np.array(phases), Vnom=10.0,
    )
    line.apply_template(template, grid.Sbase, grid.fBase, Logger())


def _build_grid(phases: tuple[int, ...] = (1, 2, 3)) -> tuple[MultiCircuit, Bus, Line, Load]:
    """Create a connected ABC load with a registered symbolic bus interface.

    :param phases: Initial static phase layout.
    :return: Grid, local bus, static line and load.
    """
    grid: MultiCircuit = MultiCircuit()
    bus: Bus = Bus(name="local", Vnom=10.0)
    remote: Bus = Bus(name="remote", Vnom=10.0)
    grid.add_bus(bus)
    grid.add_bus(remote)
    line: Line = Line(bus_from=bus, bus_to=remote)
    _set_phases(grid, line, phases)
    grid.add_line(line)
    get_bus_emt_template(grid=grid, bus=bus)
    load: Load = Load(name="load")
    grid.add_load(bus=bus, api_obj=load)
    inputs: list[Var] = list()
    outputs: list[Var] = list()
    source: Var
    current_ref: VarPowerFlowReferenceType
    current_refs: dict[VarPowerFlowReferenceType, VarPowerFlowReferenceType] = dict((
        (VarPowerFlowReferenceType.v_N, VarPowerFlowReferenceType.i_N),
        (VarPowerFlowReferenceType.v_A, VarPowerFlowReferenceType.i_A),
        (VarPowerFlowReferenceType.v_B, VarPowerFlowReferenceType.i_B),
        (VarPowerFlowReferenceType.v_C, VarPowerFlowReferenceType.i_C),
    ))
    for source in bus.emt_model.out_vars:
        assert source.ref is not None
        current_ref = current_refs[source.ref]
        target: Var = grid.var_factory.add_var(name=source.ref.name, reference=source.ref)
        current: Var = grid.var_factory.add_var(name=current_ref.name, reference=current_ref, network_conn=True)
        inputs.append(target)
        outputs.append(current)
        grid.var_factory.add_connection(var_to_subs=target, incoming_var=source)
    load.emt_model = Block(name="load model", in_vars=inputs, out_vars=outputs)
    for source in inputs:
        load.emt_model.external_mapping[source.ref] = source
    for source in outputs:
        load.emt_model.external_mapping[source.ref] = source
    return grid, bus, line, load


@pytest.mark.parametrize(("initial_phases", "final_phases"), (
    ((1, 2, 3), (1, 2)), ((1, 2, 3), (1, 3)), ((1, 2, 3), (2, 3)),
    ((1, 2, 3), (1,)), ((1, 2, 3), (2,)), ((1, 2, 3), (3,)),
    ((1, 2), (1, 2, 3)), ((1, 3), (1, 2, 3)),
    ((1, 2), (2, 3)), ((1, 3), (1, 2)),
    ((1, 2, 3), (0, 1, 2, 3)), ((0, 1, 2, 3), (1, 2, 3)),
))
def test_sync_reconnects_grid_devices_and_keeps_unused_vars(initial_phases: tuple[int, ...],
                                                           final_phases: tuple[int, ...]) -> None:
    """Adapt every phase permutation without deleting unused factory variables.

    :param initial_phases: Original static phase layout.
    :param final_phases: New static phase layout.
    :return: None.
    """
    grid: MultiCircuit
    bus: Bus
    line: Line
    load: Load
    grid, bus, line, load = _build_grid(initial_phases)
    old_sources: list[Var] = list(bus.emt_model.out_vars)
    old_inputs: list[Var] = list(load.emt_model.in_vars)
    _set_phases(grid, line, final_phases)
    result: EmtBusShellSyncResult = synchronize_emt_bus_shell_with_grid(bus=bus, grid=grid, var_factory=grid.var_factory)
    assert result.changed
    assert len(load.emt_model.in_vars) == len(final_phases)
    assert len(load.emt_model.out_vars) == len(final_phases)
    source: Var
    target: Var
    for source in old_sources:
        assert source.non_mutable_uid in grid.var_factory.get_vars_dict()
        assert source.non_mutable_uid not in grid.var_factory.get_connections_dict()
    for target in load.emt_model.in_vars:
        source = bus.emt_model.external_mapping[target.ref]
        assert source is not None
        assert target.uid == source.uid
        assert target.name == source.name
        assert any(connection.non_mutable_uid == target.non_mutable_uid
                   for connection in grid.var_factory.get_connections_dict()[source.non_mutable_uid])
    live_refs: set[VarPowerFlowReferenceType] = set(var.ref for var in load.emt_model.in_vars)
    for target in old_inputs:
        if target.ref not in live_refs:
            assert target.uid == target.non_mutable_uid
            assert target.name == target.ref.name
        else:
            pass
    unchanged: EmtBusShellSyncResult = synchronize_emt_bus_shell_with_grid(bus=bus, grid=grid, var_factory=grid.var_factory)
    assert not unchanged.changed


def test_reference_connection_ignores_shared_reference() -> None:
    """Connect matching power-flow refs and leave unreferenced inputs alone.

    :return: None.
    """
    factory: VarFactory = VarFactory()
    source: Var = factory.add_var(name="source", reference=VarPowerFlowReferenceType.v_A)
    target: Var = factory.add_var(name="target", reference=VarPowerFlowReferenceType.v_A)
    unrelated: Var = factory.add_var(name="unreferenced")
    connect_models_by_reference(Block(out_vars=list((source,))),
                                Block(in_vars=list((target, unrelated))), factory)
    assert target.uid == source.uid
    assert unrelated.uid != source.uid
    factory.remove_connection(var_to_disconnect=target, outgoing_var=source)
    assert target.name == "target"
    assert target.uid == target.non_mutable_uid


@pytest.mark.parametrize("phases", ((1, 2), (0, 1, 2, 3)))
def test_workspace_repairs_stale_measurements_after_copy(phases: tuple[int, ...]) -> None:
    """Open through production page creation and repair only an existing stale interface.

    :param phases: Static layout requested before opening.
    :return: None.
    """
    application: QtWidgets.QApplication | None = QtWidgets.QApplication.instance()
    if application is None:
        application = QtWidgets.QApplication(list())
    else:
        pass
    grid: MultiCircuit
    bus: Bus
    line: Line
    load: Load
    grid, bus, line, load = _build_grid()
    # Persist grouped measurements so the new phase layout differs from their old lists.
    input_block: Block = Block(name=BlockType.INPUT_CONN.name, out_vars=list(load.emt_model.in_vars))
    output_block: Block = Block(name=BlockType.OUTPUT_CONN.name, in_vars=list(load.emt_model.out_vars))
    load.emt_model.add(input_block)
    load.emt_model.add(output_block)
    load.emt_model.diagram.add_node(name=input_block.name, x=0.0, y=0.0,
                                    tpe=BlockType.INPUT_CONN.name, device_uid=input_block.uid)
    load.emt_model.diagram.add_node(name=output_block.name, x=600.0, y=0.0,
                                    tpe=BlockType.OUTPUT_CONN.name, device_uid=output_block.uid)
    # A user block is connected semantically by reference, independently of shared_ref.
    user_input: Var = grid.var_factory.add_var(name="user voltage", reference=VarPowerFlowReferenceType.v_A)
    user_output: Var = grid.var_factory.add_var(name="user current", reference=VarPowerFlowReferenceType.i_A)
    user_block: Block = Block(name="user block", in_vars=list((user_input,)), out_vars=list((user_output,)))
    load.emt_model.add(user_block)
    load.emt_model.diagram.add_node(name=user_block.name, x=300.0, y=100.0,
                                    tpe=BlockType.GENERIC.name, device_uid=user_block.uid)
    _set_phases(grid, line, phases)
    entry: DynamicEditorEntry | None = build_dynamic_editor_entry(load, grid)
    assert entry is not None
    session: DynamicEditorWorkspaceSession = DynamicEditorWorkspaceSession()
    page: DynamicEditorTab = session.create_page(entry, DynamicSimulationMode.EMT)
    try:
        editor: DynamicBlockEditorGUI | None = page.editor
        assert editor is not None
        assert len(load.emt_model.in_vars) == len(phases)
        assert len(editor.main_block.in_vars) == len(phases)
        assert editor.main_block is not load.emt_model
        items: list[graph.MeasurementsItem] = list(item for item in editor.scene.items()
                                                  if isinstance(item, graph.MeasurementsItem))
        assert len(items) == 2
        assert editor._emt_measurements_match_root_interface(items)
        assert input_block.uid not in editor.diagram.node_data
        assert output_block.uid not in editor.diagram.node_data
        assert editor.has_unapplied_changes
        assert user_block.uid in editor.diagram.node_data
        assert editor.diagram.node_data[user_block.uid].x == 300.0
        assert editor.diagram.node_data[user_block.uid].y == 100.0
        assert len(editor.diagram.con_data) == 2
        # An already coherent interface must keep its exact item and node identities.
        identities: set[int] = set(item.subsys.uid for item in items)
        editor._repair_stale_emt_measurements()
        assert identities == set(item.subsys.uid for item in editor.scene.items()
                                  if isinstance(item, graph.MeasurementsItem))
        synchronized_bus: Block = bus.emt_model
        editor.persist_changes_only()
        assert bus.emt_model is synchronized_bus
        reopened_page: DynamicEditorTab = session.create_page(entry, DynamicSimulationMode.EMT)
        try:
            reopened_editor: DynamicBlockEditorGUI | None = reopened_page.editor
            assert reopened_editor is not None
            reopened_items: list[graph.MeasurementsItem] = list(
                item for item in reopened_editor.scene.items() if isinstance(item, graph.MeasurementsItem))
            assert reopened_editor._emt_measurements_match_root_interface(reopened_items)
            assert len(reopened_editor.diagram.con_data) == 2
            assert identities == set(item.subsys.uid for item in reopened_items)
        finally:
            reopened_page.prepare_to_delete()
            reopened_page.close()
            reopened_page.deleteLater()
    finally:
        page.prepare_to_delete()
        page.close()
        page.deleteLater()
        QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
        application.processEvents()


@pytest.mark.parametrize("side", (EmtBusConnectionSide.FROM, EmtBusConnectionSide.TO))
@pytest.mark.parametrize("is_dc", (False, True))
def test_bus_rebuild_changes_only_the_connected_branch_terminal(side: EmtBusConnectionSide, is_dc: bool) -> None:
    """Discover branches from the circuit and preserve the opposite terminal.

    :param side: Branch terminal whose bus changes.
    :param is_dc: Whether that terminal changes from AC to DC instead of shrinking.
    :return: None.
    """
    grid: MultiCircuit
    bus: Bus
    line: Line
    load: Load
    grid, bus, line, load = _build_grid()
    get_bus_emt_template(grid=grid, bus=line.bus_to)
    inputs: list[Var] = list()
    outputs: list[Var] = list()
    side_bus: Bus
    voltage_ref: VarPowerFlowReferenceType
    current_ref: VarPowerFlowReferenceType
    source: Var
    target: Var
    current: Var
    voltage_refs: tuple[VarPowerFlowReferenceType, ...]
    current_refs: tuple[VarPowerFlowReferenceType, ...]
    refs: tuple[tuple[Bus, tuple[VarPowerFlowReferenceType, ...], tuple[VarPowerFlowReferenceType, ...]], ...] = (
        (bus, (VarPowerFlowReferenceType.vf_A, VarPowerFlowReferenceType.vf_B, VarPowerFlowReferenceType.vf_C),
         (VarPowerFlowReferenceType.if_A, VarPowerFlowReferenceType.if_B, VarPowerFlowReferenceType.if_C)),
        (line.bus_to, (VarPowerFlowReferenceType.vt_A, VarPowerFlowReferenceType.vt_B, VarPowerFlowReferenceType.vt_C),
         (VarPowerFlowReferenceType.it_A, VarPowerFlowReferenceType.it_B, VarPowerFlowReferenceType.it_C)),
    )
    for side_bus, voltage_refs, current_refs in refs:
        for source, voltage_ref, current_ref in zip(side_bus.emt_model.out_vars, voltage_refs, current_refs):
            target = grid.var_factory.add_var(name=voltage_ref.name, reference=voltage_ref)
            current = grid.var_factory.add_var(name=current_ref.name, reference=current_ref, network_conn=True)
            inputs.append(target)
            outputs.append(current)
            grid.var_factory.add_connection(var_to_subs=target, incoming_var=source)
    line.emt_model = Block(name="line model", in_vars=inputs, out_vars=outputs)
    for target in inputs:
        line.emt_model.external_mapping[target.ref] = target
    for current in outputs:
        line.emt_model.external_mapping[current.ref] = current
    if side == EmtBusConnectionSide.FROM:
        selected_bus: Bus = bus
        opposite_inputs: list[Var] = inputs[3:]
        voltage_refs = refs[0][1]
        current_refs = refs[0][2]
    else:
        selected_bus = line.bus_to
        opposite_inputs = inputs[:3]
        voltage_refs = refs[1][1]
        current_refs = refs[1][2]
    opposite: tuple[tuple[int, int, str], ...] = tuple((var.non_mutable_uid, var.uid, var.name) for var in opposite_inputs)
    empty_load: Load = Load(name="empty")
    grid.add_load(bus=selected_bus, api_obj=empty_load)
    if is_dc:
        selected_bus.is_dc = True
    else:
        _set_phases(grid, line, (1, 2))
    synchronize_emt_bus_shell_with_grid(bus=selected_bus, grid=grid, var_factory=grid.var_factory)
    assert len(line.emt_model.in_vars) == (4 if is_dc else 5)
    assert len(line.emt_model.out_vars) == (4 if is_dc else 5)
    assert voltage_refs[2] not in line.emt_model.external_mapping
    assert current_refs[2] not in line.emt_model.external_mapping
    if not is_dc:
        assert line.emt_model.external_mapping[voltage_refs[0]].uid == selected_bus.emt_model.external_mapping[VarPowerFlowReferenceType.v_A].uid
    else:
        pass
    assert opposite == tuple((var.non_mutable_uid, var.uid, var.name) for var in opposite_inputs)
    if side == EmtBusConnectionSide.FROM:
        assert len(load.emt_model.in_vars) == (1 if is_dc else 2)
    else:
        assert len(load.emt_model.in_vars) == 3
    assert empty_load.emt_model.empty()


def test_bus_domain_transition_replaces_ac_terminal_with_dc() -> None:
    """Adapt voltage and current interfaces together when a bus changes domain.

    :return: None.
    """
    grid: MultiCircuit
    bus: Bus
    line: Line
    load: Load
    grid, bus, line, load = _build_grid()
    bus.is_dc = True
    synchronize_emt_bus_shell_with_grid(bus=bus, grid=grid, var_factory=grid.var_factory)
    assert tuple(var.ref for var in load.emt_model.in_vars) == (VarPowerFlowReferenceType.Vdc,)
    assert tuple(var.ref for var in load.emt_model.out_vars) == (VarPowerFlowReferenceType.Idc,)
    assert load.emt_model.in_vars[0].uid == bus.emt_model.out_vars[0].uid
