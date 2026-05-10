# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os
from pathlib import Path
import pytest

import VeraGridEngine.api as vge
from VeraGridEngine.Devices.Diagrams.graphic_location import GraphicLocation
from VeraGridEngine.Devices.Diagrams.map_location import MapLocation
from VeraGridEngine.Devices.Dynamic.fmu_template import FmuTemplate
from VeraGridEngine.enumerations import DeviceType, FmuTemplateDomain
from VeraGridEngine.IO.file_open import FileOpen
from VeraGridEngine.Utils.Symbolic.block import Block


GRID_FOLDER = Path(__file__).resolve().parents[1] / "data" / "grids"


def _load_grid(name: str):
    """
    Load a test grid from the shared test data folder.

    Every multiverse test uses real `.gridcal` fixtures so that serialization, diagram
    handling, and circuit diffs exercise the same code paths used by the application.
    """
    return vge.open_file(str(GRID_FOLDER / name))


def _get_bus_by_name(grid, bus_name: str):
    """
    Find a bus by name in a grid.

    The tests use names as stable intent-revealing identifiers when asserting that a
    scenario gained or did not gain a specific object.
    """
    for bus in grid.buses:
        if bus.name == bus_name:
            return bus
    return None


def _build_grid_with_schematic_diagram():
    """
    Build a minimal grid whose schematic locations point to its API objects.
    """
    grid = vge.MultiCircuit(name="diagram-pointer-grid")
    bus_from = grid.add_bus(vge.Bus(name="B1", Vnom=10.0, is_slack=True))
    bus_to = grid.add_bus(vge.Bus(name="B2", Vnom=10.0))
    line = grid.add_line(vge.Line(name="L12", bus_from=bus_from, bus_to=bus_to, r=0.1, x=0.2, rate=100.0))

    diagram = vge.SchematicDiagram(name="diagram-pointer-schematic")
    diagram.set_point(bus_from, GraphicLocation(x=0.0, y=0.0, w=80.0, h=40.0, api_object=bus_from))
    diagram.set_point(bus_to, GraphicLocation(x=200.0, y=0.0, w=80.0, h=40.0, api_object=bus_to))
    diagram.set_point(line, GraphicLocation(x=0.0, y=0.0, w=0.0, h=0.0, api_object=line))
    grid.add_diagram(diagram)

    return grid


def _build_grid_with_schematic_and_map_diagrams():
    """
    Build a minimal grid with both schematic and map locations.
    """
    grid = _build_grid_with_schematic_diagram()
    line = grid.lines[0]

    map_diagram = vge.MapDiagram(name="diagram-pointer-map")
    map_diagram.set_point(
        line,
        MapLocation(latitude=28.1, longitude=-15.4, altitude=12.0, draw_labels=False, api_object=line),
    )
    grid.add_diagram(map_diagram)

    return grid


def _build_grid_with_internal_references():
    """
    Build a grid containing direct, association, and profile device references.
    """
    grid = vge.MultiCircuit(name="internal-pointer-grid")
    bus_from = grid.add_bus(vge.Bus(name="B1", Vnom=10.0, is_slack=True))
    bus_to = grid.add_bus(vge.Bus(name="B2", Vnom=10.0))
    dc_bus = grid.add_bus(vge.Bus(name="DC", Vnom=10.0, is_dc=True))

    line = grid.add_line(vge.Line(name="L12", bus_from=bus_from, bus_to=bus_to, r=0.1, x=0.2, rate=100.0))
    grid.add_load(bus=bus_to, api_obj=vge.Load(name="LD"))

    technology = vge.Technology(name="Solar")
    grid.add_technology(technology)

    generator = grid.add_generator(bus=bus_from, api_obj=vge.Generator(name="G"))
    generator.technologies.add_object(api_object=technology, val=1.0)

    vsc = vge.VSC(
        name="VSC",
        bus_from=dc_bus,
        bus_to=bus_from,
        control1_dev=line,
        control2_dev=bus_to,
    )
    vsc.control1_dev_prof.create_sparse(size=3, default_value=line, map_data={1: bus_to})
    vsc.control2_dev_prof.create_dense(size=2, default_value=bus_to)
    vsc.control2_dev_prof[1] = line
    grid.add_vsc(vsc)

    return grid


def _build_grid_with_dynamic_templates():
    """
    Build a grid with native RMS/EMT templates and one RMS FMU template.
    """
    grid = vge.MultiCircuit(name="dynamic-template-pointer-grid")
    bus_from = grid.add_bus(vge.Bus(name="B1", Vnom=10.0, is_slack=True))
    bus_to = grid.add_bus(vge.Bus(name="B2", Vnom=10.0))
    line = grid.add_line(vge.Line(name="L12", bus_from=bus_from, bus_to=bus_to, r=0.1, x=0.2, rate=100.0))
    load = grid.add_load(bus=bus_to, api_obj=vge.Load(name="LD"))

    grid.add_rms_model_catalogue()
    grid.add_emt_model_catalogue()

    rms_template = next(t for t in grid.rms_models if t.tpe == DeviceType.LineDevice)
    emt_template = next(t for t in grid.emt_models if t.tpe == DeviceType.LineDevice)
    line.rms_template = rms_template
    line.emt_template = emt_template

    fmu_template = FmuTemplate(name="load-rms-fmu")
    fmu_template.tpe = DeviceType.LoadDevice
    fmu_template.domain = FmuTemplateDomain.RMS
    fmu_template.block = Block(name="load-rms-fmu-block")
    grid.add_fmu_template(fmu_template)
    load.rms_fmu_template = fmu_template

    return grid, rms_template, emt_template, fmu_template


def _assert_diagram_locations_point_to_circuit_objects(grid) -> None:
    """
    Assert every diagram location points to the canonical object in the circuit.
    """
    obj_dict = grid.get_all_elements_dict_by_type(add_locations=True)

    for diagram in grid.diagrams:
        for category, points_group in diagram.data.items():
            category_obj_dict = obj_dict.get(category, dict())

            for idtag, location in points_group.locations.items():
                assert idtag in category_obj_dict
                assert location.api_object is category_obj_dict[idtag]


def _assert_circuits_equal(grid1, grid2) -> None:
    """
    Assert semantic circuit equality using the engine's comparison helper.

    When a comparison fails, the logger is printed so the failing structural difference is
    visible immediately from the pytest output.
    """
    equal, logger = grid1.compare_circuits(
        grid2,
        detailed_profile_comparison=True,
        skip_internals=True,
    )

    if not equal:
        logger.print()

    assert equal


def _assert_same_multiverse(expected, loaded) -> None:
    """
    Assert that two multiverse objects represent the same scenario tree and scenario content.

    The comparison checks:
    - node traversal order and node ids
    - parent relationships
    - active scenario identity
    - scenario names
    - per-node diagrams
    - fully composed scenario circuits for every node
    """
    # Compare the traversal shape first so later node-by-node comparisons are aligned.
    expected_ids = [node.node_id for node in expected.iter_nodes_depth_first()]
    loaded_ids = [node.node_id for node in loaded.iter_nodes_depth_first()]

    assert loaded_ids == expected_ids
    assert len(loaded.root_nodes) == len(expected.root_nodes)
    assert loaded.current_node is not None
    assert expected.current_node is not None
    assert loaded.current_node.node_id == expected.current_node.node_id

    for node_id in expected_ids:
        # Resolve the corresponding nodes in both trees.
        expected_node = expected.get_node(node_id)
        loaded_node = loaded.get_node(node_id)

        # Parent ids must match exactly so the restored tree shape is identical.
        expected_parent_id = None if expected_node.parent is None else expected_node.parent.node_id
        loaded_parent_id = None if loaded_node.parent is None else loaded_node.parent.node_id

        assert loaded_parent_id == expected_parent_id
        assert loaded_node.circuit.name == expected_node.circuit.name
        assert len(loaded_node.diagrams) == len(expected_node.diagrams)

        # Diagrams are scenario-owned, so content must match but object identity must not.
        for expected_diagram, loaded_diagram in zip(expected_node.diagrams, loaded_node.diagrams):
            assert loaded_diagram is not expected_diagram
            assert loaded_diagram.name == expected_diagram.name

        # The fully composed scenario represented by each node must round-trip exactly.
        _assert_circuits_equal(
            expected.checkout(expected_node),
            loaded.checkout(loaded_node),
        )


def _build_sample_multiverse():
    """
    Build a small but non-trivial multiverse used by multiple tests.

    The fixture shape is:
    - one root
    - two direct children
    - one grandchild under the first child

    Each non-root scenario receives its own bus so checkout, save/load, and active-node logic
    can verify inherited versus local changes clearly.
    """
    # Start from a real base grid so the scenarios contain realistic objects and diagrams.
    base_grid = _load_grid("lynn5node.gridcal")
    mv = vge.MultiVerse(base_grid)

    # Build a two-level scenario tree with siblings and a grandchild.
    root = mv.root_nodes[0]
    child = mv.create_node(
        data=vge.MultiCircuit(name="child"),
        parent_id=root.node_id,
        position=root.child_count(),
    )
    sibling = mv.create_node(
        data=vge.MultiCircuit(name="sibling"),
        parent_id=root.node_id,
        position=root.child_count(),
    )
    grandchild = mv.create_node(
        data=vge.MultiCircuit(name="grandchild"),
        parent_id=child.node_id,
        position=child.child_count(),
    )

    # Add one child-only change.
    mv.activate_scenario(child.node_id)
    mv.current_model.add_bus(vge.Bus(Vnom=10.0, name="child_only_bus"))

    # Add one grandchild-only change on top of the child state.
    mv.activate_scenario(grandchild.node_id)
    mv.current_model.add_bus(vge.Bus(Vnom=11.0, name="grandchild_only_bus"))

    # Add one sibling-only change and commit so the tree is in a saved-like state.
    mv.activate_scenario(sibling.node_id)
    mv.current_model.add_bus(vge.Bus(Vnom=12.0, name="sibling_only_bus"))
    mv.commit_current()

    return mv, root, child, sibling, grandchild


def test_multiverse_child_edits_do_not_touch_root() -> None:
    """
    Verify that edits made in a child scenario are isolated from the root scenario.

    The child should keep its added bus after switching away and back, while the root
    should remain equal to the pristine base grid.
    """
    # Load a real base grid and snapshot its pristine state before building the multiverse.
    base_grid = _load_grid("lynn5node.gridcal")
    pristine_root = base_grid.copy()

    # Build a root plus one child scenario.
    mv = vge.MultiVerse(base_grid)
    root = mv.root_nodes[0]
    child = mv.create_node(
        data=vge.MultiCircuit(name="child"),
        parent_id=root.node_id,
        position=root.child_count(),
    )

    # Edit only the child scenario.
    mv.activate_scenario(child.node_id)
    mv.current_model.add_bus(vge.Bus(Vnom=10.0, name="child_only_bus"))

    # Switching away from the child must persist the delta automatically.
    mv.activate_scenario(root.node_id)

    # Compose both scenarios and verify isolation.
    root_grid = mv.checkout(root)
    child_grid = mv.checkout(child)

    assert _get_bus_by_name(root_grid, "child_only_bus") is None
    assert _get_bus_by_name(child_grid, "child_only_bus") is not None
    _assert_circuits_equal(root_grid, pristine_root)
    _assert_circuits_equal(root.circuit, pristine_root)

    # Re-activating the child must restore the child-only change.
    reloaded_child_grid = mv.activate_scenario(child.node_id)
    assert _get_bus_by_name(reloaded_child_grid, "child_only_bus") is not None


def test_multiverse_nested_checkout_replays_parent_deltas() -> None:
    """
    Verify that checkout() composes ancestor deltas in order for nested scenarios.

    A grandchild should inherit the child's changes plus its own changes, while the
    child should not include changes introduced only at the grandchild level.
    """
    # Create a root -> child -> grandchild chain.
    base_grid = _load_grid("lynn5node.gridcal")
    mv = vge.MultiVerse(base_grid)

    root = mv.root_nodes[0]
    child = mv.create_node(
        data=vge.MultiCircuit(name="child"),
        parent_id=root.node_id,
        position=root.child_count(),
    )
    grandchild = mv.create_node(
        data=vge.MultiCircuit(name="grandchild"),
        parent_id=child.node_id,
        position=child.child_count(),
    )

    # Add a child-level change first.
    mv.activate_scenario(child.node_id)
    mv.current_model.add_bus(vge.Bus(Vnom=10.0, name="child_only_bus"))

    # Activating the grandchild commits the child and composes the child changes into the new model.
    mv.activate_scenario(grandchild.node_id)
    mv.current_model.add_bus(vge.Bus(Vnom=11.0, name="grandchild_only_bus"))
    mv.commit_current()

    # Reconstruct each scenario and verify inheritance boundaries.
    root_grid = mv.checkout(root)
    child_grid = mv.checkout(child)
    grandchild_grid = mv.checkout(grandchild)

    assert _get_bus_by_name(root_grid, "child_only_bus") is None
    assert _get_bus_by_name(root_grid, "grandchild_only_bus") is None
    assert _get_bus_by_name(child_grid, "child_only_bus") is not None
    assert _get_bus_by_name(child_grid, "grandchild_only_bus") is None
    assert _get_bus_by_name(grandchild_grid, "child_only_bus") is not None
    assert _get_bus_by_name(grandchild_grid, "grandchild_only_bus") is not None


def test_multiverse_parse_json_roundtrip() -> None:
    """
    Verify that get_save_data() and parse_json() rebuild the same multiverse in memory.

    This covers tree structure, parent relationships, scenario names, and composed
    circuit equality for every node.
    """
    # Build an in-memory sample multiverse and serialize it to metadata + model payloads.
    mv, _, _, _, _ = _build_sample_multiverse()

    metadata, model_data, drivers_data = mv.get_save_data()

    # Parse the serialized payloads into a fresh multiverse instance.
    loaded_mv = vge.MultiVerse(current_model=None)
    loaded_mv.parse_json(model_data, metadata)

    # The reconstructed tree and scenario content must match the original.
    _assert_same_multiverse(mv, loaded_mv)


def test_multiverse_save_load_roundtrip(tmp_path: Path) -> None:
    """
    Verify full multiverse persistence through save/load of a .veragrid archive.

    The loaded multiverse should match the original one node-for-node and scenario-for-scenario.
    """
    # Build a non-trivial multiverse and make a non-root node active before saving.
    mv, _, _, sibling, _ = _build_sample_multiverse()
    mv.activate_scenario(sibling.node_id)

    # Save to a real .veragrid file and load it back through the file API.
    file_name = tmp_path / "multiverse_roundtrip.veragrid"
    vge.save_multiverse(mv=mv, filename=str(file_name))

    loader = FileOpen(str(file_name))
    loader.open()

    # The loaded multiverse must match node structure, active node, diagrams, and circuits.
    assert loader.multiverse is not None
    _assert_same_multiverse(mv, loader.multiverse)


def test_multiverse_move_node_is_disabled_until_rebasing_exists() -> None:
    """
    Verify that move_node() is disabled until scenario delta rebasing is implemented.

    Reparenting a node without recomputing its delta relative to the new parent corrupts the
    scenario semantics, so the operation must fail loudly for now.
    """
    # Build a small tree where a move would require delta rebasing.
    mv = vge.MultiVerse(vge.MultiCircuit(name="base"))
    root = mv.root_nodes[0]

    child_a = mv.create_node(
        data=vge.MultiCircuit(name="child_a"),
        parent_id=root.node_id,
        position=root.child_count(),
    )
    child_b = mv.create_node(
        data=vge.MultiCircuit(name="child_b"),
        parent_id=root.node_id,
        position=root.child_count(),
    )
    grandchild = mv.create_node(
        data=vge.MultiCircuit(name="grandchild"),
        parent_id=child_a.node_id,
        position=child_a.child_count(),
    )

    # The API must reject the move explicitly until rebasing semantics are implemented.
    with pytest.raises(NotImplementedError):
        mv.move_node(grandchild.node_id, child_b.node_id, position=0)


def test_multiverse_delete_active_node_falls_back_to_parent() -> None:
    """
    Verify that deleting the active scenario switches the active state to a valid fallback node.

    Removing the current node must not leave current_node/current_model pointing at detached data.
    """
    # Build a root -> child -> grandchild tree and make the grandchild active.
    mv = vge.MultiVerse(_load_grid("lynn5node.gridcal"))
    root = mv.root_nodes[0]
    child = mv.create_node(
        data=vge.MultiCircuit(name="child"),
        parent_id=root.node_id,
        position=root.child_count(),
    )
    grandchild = mv.create_node(
        data=vge.MultiCircuit(name="grandchild"),
        parent_id=child.node_id,
        position=child.child_count(),
    )

    # Add a grandchild-only edit so the active scenario has meaningful state.
    mv.activate_scenario(grandchild.node_id)
    mv.current_model.add_bus(vge.Bus(Vnom=10.0, name="grandchild_bus"))
    mv.commit_current()

    # Delete the parent subtree and verify that active state falls back safely.
    mv.delete_node(child.node_id)

    assert not mv.exists(child.node_id)
    assert not mv.exists(grandchild.node_id)
    assert mv.current_node is root
    assert mv.current_model is root.circuit
    assert root.child_count() == 0


def test_multiverse_merge_children_into_parent_rebases_grandchildren() -> None:
    """
    Verify that merging direct children into a parent preserves rebased descendants.

    Direct children should be removed after their changes are absorbed by the parent,
    while grandchildren should move under the parent and keep the same composed scenario.
    """
    # Create a parent with two children and one grandchild to exercise merge + rebase logic.
    base_grid = _load_grid("lynn5node.gridcal")
    mv = vge.MultiVerse(base_grid)

    root = mv.root_nodes[0]
    child_a = mv.create_node(
        data=vge.MultiCircuit(name="child_a"),
        parent_id=root.node_id,
        position=root.child_count(),
    )
    child_b = mv.create_node(
        data=vge.MultiCircuit(name="child_b"),
        parent_id=root.node_id,
        position=root.child_count(),
    )
    grandchild = mv.create_node(
        data=vge.MultiCircuit(name="grandchild"),
        parent_id=child_a.node_id,
        position=child_a.child_count(),
    )

    # Child A contributes both network and diagram changes.
    mv.activate_scenario(child_a.node_id)
    mv.current_model.add_bus(vge.Bus(Vnom=10.0, name="child_a_bus"))
    mv.current_model.diagrams[0].name = "child_a_diagram"

    # Child B contributes later network and diagram changes that should win on conflicts.
    mv.activate_scenario(child_b.node_id)
    mv.current_model.add_bus(vge.Bus(Vnom=11.0, name="child_b_bus"))
    mv.current_model.diagrams[0].name = "child_b_diagram"

    # The grandchild keeps its own extra state and must be rebased under the parent after merge.
    mv.activate_scenario(grandchild.node_id)
    mv.current_model.add_bus(vge.Bus(Vnom=12.0, name="grandchild_bus"))
    mv.commit_current()

    # Compute the expected merged parent and preserved grandchild scenarios before mutating the tree.
    expected_parent = mv.checkout(root)
    expected_parent.merge_circuit(child_a.circuit)
    expected_parent.merge_circuit(child_b.circuit)
    expected_grandchild = mv.checkout(grandchild)

    # Merge the direct children into the root.
    mv.merge_children_into_parent(root.node_id)

    # Verify structure, inherited buses, and diagram override semantics.
    assert root.child_count() == 1
    assert root.child(0) is grandchild
    assert grandchild.parent is root
    assert not mv.exists(child_a.node_id)
    assert not mv.exists(child_b.node_id)

    merged_root = mv.checkout(root)
    merged_grandchild = mv.checkout(grandchild)

    assert _get_bus_by_name(merged_root, "child_a_bus") is not None
    assert _get_bus_by_name(merged_root, "child_b_bus") is not None
    assert _get_bus_by_name(merged_root, "grandchild_bus") is None
    assert _get_bus_by_name(merged_grandchild, "grandchild_bus") is not None
    assert root.diagrams[0].name == "child_b_diagram"
    assert merged_root.diagrams[0].name == "child_b_diagram"

    _assert_circuits_equal(merged_root, expected_parent)
    _assert_circuits_equal(merged_grandchild, expected_grandchild)


def test_multiverse_root_edits_are_persisted_in_place() -> None:
    """
    Verify that edits performed on the root scenario stay in the authoritative root model.

    Root scenarios are not stored as deltas, so switching away and back must not lose
    the changes or require a separate diff commit step.
    """
    # Create a root and one child so switching away and back exercises root persistence.
    base_grid = _load_grid("lynn5node.gridcal")
    mv = vge.MultiVerse(base_grid)

    root = mv.root_nodes[0]
    child = mv.create_node(
        data=vge.MultiCircuit(name="child"),
        parent_id=root.node_id,
        position=root.child_count(),
    )

    # Edit the root directly.
    root_bus = vge.Bus(Vnom=13.0, name="root_only_bus")
    mv.current_model.add_bus(root_bus)

    # Switch away and back to force the normal activation flow.
    mv.activate_scenario(child.node_id)
    mv.activate_scenario(root.node_id)

    # Root changes must still be present everywhere the authoritative root is observed.
    root_grid = mv.checkout(root)

    assert _get_bus_by_name(root.circuit, "root_only_bus") is not None
    assert _get_bus_by_name(root_grid, "root_only_bus") is not None
    assert _get_bus_by_name(mv.current_model, "root_only_bus") is not None


def test_multicircuit_copy_deep_copies_diagrams() -> None:
    """
    Verify that MultiCircuit.copy() duplicates stored diagrams instead of sharing them.

    Child scenario activation relies on checkout(), which uses circuit copies. If diagrams are
    shared by reference, edits in one scenario can leak visually into other scenarios.
    """
    # Load a grid with existing diagrams and append two extra diagrams to make the check explicit.
    original = _load_grid("lynn5node.gridcal")
    original.add_diagram(vge.SchematicDiagram(name="Schematic Copy Test"))
    original.add_diagram(vge.MapDiagram(name="Map Copy Test"))
    original_schematic_index = len(original.diagrams) - 2

    # Copy the grid through the engine helper under test.
    copied = original.copy()

    assert len(copied.diagrams) == len(original.diagrams)

    for original_diagram, copied_diagram in zip(original.diagrams, copied.diagrams):
        assert copied_diagram is not original_diagram
        assert copied_diagram.name == original_diagram.name

    # Mutate the copied diagram and verify the source diagram is untouched.
    copied.diagrams[original_schematic_index].name = "Modified Diagram Name"
    assert original.diagrams[original_schematic_index].name == "Schematic Copy Test"


def test_multicircuit_copy_rebinds_diagram_objects_to_copied_circuit() -> None:
    """
    Verify copied circuit diagrams point to copied API objects, not stale source objects.
    """
    original = _build_grid_with_schematic_and_map_diagrams()

    copied = original.copy()
    _assert_diagram_locations_point_to_circuit_objects(copied)

    copied_line = copied.lines[0]
    copied_diagram_line = copied.diagrams[0].query_point(copied_line).api_object
    copied_map_line_location = copied.diagrams[1].query_point(copied_line)

    assert copied_diagram_line is copied_line
    assert copied_diagram_line is not original.lines[0]
    assert copied_map_line_location.api_object is copied_line
    assert copied_map_line_location.draw_labels is False

    copied_diagram_line.rate = 1234.0
    assert copied_line.rate == 1234.0
    assert original.lines[0].rate == 100.0


def test_multicircuit_copy_rebinds_internal_device_references_to_copied_circuit() -> None:
    """
    Verify copied device pointers refer to canonical objects inside the copied circuit.
    """
    original = _build_grid_with_internal_references()

    copied = original.copy()

    copied_bus_from = copied.buses[0]
    copied_bus_to = copied.buses[1]
    copied_dc_bus = copied.buses[2]
    copied_line = copied.lines[0]
    copied_load = copied.loads[0]
    copied_generator = copied.generators[0]
    copied_technology = copied.technologies[0]
    copied_vsc = copied.vsc_devices[0]
    copied_generator_technology = next(iter(copied_generator.technologies)).api_object

    assert copied_line.bus_from is copied_bus_from
    assert copied_line.bus_to is copied_bus_to
    assert copied_load.bus is copied_bus_to
    assert copied_generator.bus is copied_bus_from
    assert copied_generator_technology is copied_technology
    assert copied_generator_technology is not original.technologies[0]
    assert copied_bus_from._var_factory is copied.var_factory
    assert copied_line._var_factory is copied.var_factory
    assert copied_load._var_factory is copied.var_factory
    assert copied_generator._var_factory is copied.var_factory

    assert copied_vsc.bus_from is copied_dc_bus
    assert copied_vsc.bus_to is copied_bus_from
    assert copied_vsc.control1_dev is copied_line
    assert copied_vsc.control2_dev is copied_bus_to
    assert copied_vsc._var_factory is copied.var_factory
    assert copied_vsc.control1_dev_prof.default_value is copied_line
    assert copied_vsc.control1_dev_prof[0] is copied_line
    assert copied_vsc.control1_dev_prof[1] is copied_bus_to
    assert copied_vsc.control2_dev_prof.default_value is copied_bus_to
    assert copied_vsc.control2_dev_prof[0] is copied_bus_to
    assert copied_vsc.control2_dev_prof[1] is copied_line

    copied_line.rate = 2468.0
    assert copied_vsc.control1_dev.rate == 2468.0
    assert original.lines[0].rate == 100.0


def test_multicircuit_copy_deep_copies_dynamic_template_blocks() -> None:
    """
    Verify copied RMS/EMT catalogue templates do not share symbolic blocks.
    """
    original, rms_template, emt_template, _ = _build_grid_with_dynamic_templates()

    copied = original.copy()
    copied_line = copied.lines[0]
    copied_rms_template = next(t for t in copied.rms_models if t.idtag == rms_template.idtag)
    copied_emt_template = next(t for t in copied.emt_models if t.idtag == emt_template.idtag)

    assert copied_rms_template is not rms_template
    assert copied_emt_template is not emt_template
    assert copied_rms_template.block is not rms_template.block
    assert copied_emt_template.block is not emt_template.block
    assert copied_line.rms_template is copied_rms_template
    assert copied_line.emt_template is copied_emt_template
    assert copied_line.rms_model is not original.lines[0].rms_model
    assert copied_line.emt_model is not original.lines[0].emt_model

    copied_rms_template.block.name = "copied-rms-template-block"
    copied_emt_template.block.name = "copied-emt-template-block"
    copied_line.rms_model.name = "copied-rms-concrete-block"
    copied_line.emt_model.name = "copied-emt-concrete-block"

    assert rms_template.block.name != "copied-rms-template-block"
    assert emt_template.block.name != "copied-emt-template-block"
    assert original.lines[0].rms_model.name != "copied-rms-concrete-block"
    assert original.lines[0].emt_model.name != "copied-emt-concrete-block"


def test_multicircuit_copy_copies_fmu_templates_and_rebinds_devices() -> None:
    """
    Verify copied RMS FMU template references point to the copied catalogue entry.
    """
    original, _, _, fmu_template = _build_grid_with_dynamic_templates()

    copied = original.copy()
    copied_load = copied.loads[0]
    copied_fmu_template = next(t for t in copied.fmu_templates if t.idtag == fmu_template.idtag)

    assert len(copied.fmu_templates) == len(original.fmu_templates)
    assert copied_fmu_template is not fmu_template
    assert copied_fmu_template.block is not fmu_template.block
    assert copied_fmu_template.name == fmu_template.name
    assert copied_fmu_template.device_type == fmu_template.device_type
    assert copied_fmu_template.tpe == fmu_template.tpe
    assert copied_fmu_template.domain == fmu_template.domain
    assert copied_load.rms_fmu_template is copied_fmu_template

    copied_fmu_template.block.name = "copied-fmu-template-block"
    assert fmu_template.block.name != "copied-fmu-template-block"


def test_multiverse_child_starts_with_copies_of_parent_diagrams() -> None:
    """
    Verify that a newly created child scenario inherits deep-copied diagrams from its parent.

    The child should start with the same diagram content as the parent, but diagram objects
    must not be shared by reference between the two scenarios.
    """
    # Create a parent and child without any edits so the child starts from inherited diagrams.
    mv = vge.MultiVerse(_load_grid("lynn5node.gridcal"))
    root = mv.root_nodes[0]
    child = mv.create_node(
        data=vge.MultiCircuit(name="child"),
        parent_id=root.node_id,
        position=root.child_count(),
    )

    # The child should inherit the same diagram content but as different Python objects.
    assert len(child.diagrams) == len(root.diagrams)

    for root_diagram, child_diagram in zip(root.diagrams, child.diagrams):
        assert child_diagram is not root_diagram
        assert child_diagram.name == root_diagram.name


def test_multiverse_root_commit_syncs_diagrams_for_new_child() -> None:
    """
    Verify root commit keeps root-owned diagram snapshots in sync for child inheritance.
    """
    mv = vge.MultiVerse(_load_grid("lynn5node.gridcal"))
    root = mv.root_nodes[0]

    edited_name = "Root Diagram Edited"
    mv.current_model.diagrams[0].name = edited_name
    mv.commit_current()

    child = mv.create_node(
        data=vge.MultiCircuit(name="child"),
        parent_id=root.node_id,
        position=root.child_count(),
    )

    assert root.diagrams[0].name == edited_name
    assert child.diagrams[0].name == edited_name
    assert child.diagrams[0] is not root.diagrams[0]


def test_multiverse_save_load_rebinds_active_diagram_objects_to_current_model(tmp_path: Path) -> None:
    """
    Verify loaded diagrams edit the same objects used by the active simulation circuit.
    """
    mv = vge.MultiVerse(_build_grid_with_schematic_and_map_diagrams())
    file_name = tmp_path / "diagram_pointer_multiverse.veragrid"

    vge.save_multiverse(mv=mv, filename=str(file_name))

    loader = FileOpen(str(file_name))
    loader.open()

    loaded_grid = loader.multiverse.current_model
    _assert_diagram_locations_point_to_circuit_objects(loaded_grid)

    loaded_line = loaded_grid.lines[0]
    loaded_diagram_line = loaded_grid.diagrams[0].query_point(loaded_line).api_object
    loaded_map_line_location = loaded_grid.diagrams[1].query_point(loaded_line)

    assert loaded_diagram_line is loaded_line
    assert loaded_map_line_location.api_object is loaded_line
    assert loaded_map_line_location.draw_labels is False

    loaded_diagram_line.rate = 4321.0
    assert loaded_line.rate == 4321.0


def test_multiverse_child_diagram_edits_persist_across_switches() -> None:
    """
    Verify that child-specific diagram edits survive commit and scenario switching.

    This covers the workflow where the user activates a child, edits its diagrams, commits,
    switches to the parent, and later comes back to the child.
    """
    # Create a root and child and activate the child for diagram editing.
    mv = vge.MultiVerse(_load_grid("lynn5node.gridcal"))
    root = mv.root_nodes[0]
    child = mv.create_node(
        data=vge.MultiCircuit(name="child"),
        parent_id=root.node_id,
        position=root.child_count(),
    )

    # Rename the first child diagram and commit that scenario.
    mv.activate_scenario(child.node_id)
    original_root_diagram_name = root.diagrams[0].name
    child_diagram_name = "Child Diagram Edited"
    mv.current_model.diagrams[0].name = child_diagram_name
    mv.commit_current()

    # Root and child must now diverge in diagram state.
    assert child.diagrams[0].name == child_diagram_name
    assert root.diagrams[0].name == original_root_diagram_name

    # Switching to root must restore root diagrams.
    mv.activate_scenario(root.node_id)
    assert mv.current_model.diagrams[0].name == original_root_diagram_name

    # Switching back to child must restore the child-specific diagram edits.
    mv.activate_scenario(child.node_id)
    assert mv.current_model.diagrams[0].name == child_diagram_name
    assert child.diagrams[0].name == child_diagram_name


def test_multiverse_reactivated_child_rebinds_branch_bus_references() -> None:
    """
    Verify that reactivating a child scenario rebinds branch endpoint references to the
    buses of the newly composed current model.

    This protects the root -> child -> root -> child workflow used before running a simulation.
    """
    # Create a root and child, then add a line while the child is active.
    mv = vge.MultiVerse(_load_grid("lynn5node.gridcal"))
    root = mv.root_nodes[0]
    child = mv.create_node(
        data=vge.MultiCircuit(name="child"),
        parent_id=root.node_id,
        position=root.child_count(),
    )

    # Activate the child and create a branch between buses from the composed child grid.
    mv.activate_scenario(child.node_id)

    bus_from = mv.current_model.buses[0]
    bus_to = mv.current_model.buses[1]
    new_line = vge.Line(name="child_line", bus_from=bus_from, bus_to=bus_to)
    mv.current_model.add_line(new_line)
    mv.commit_current()

    # Force a full root -> child reactivation cycle.
    mv.activate_scenario(root.node_id)
    child_grid = mv.activate_scenario(child.node_id)

    # The restored line endpoints must belong to the newly composed child grid.
    child_bus_set = set(child_grid.buses)
    restored_line = next(line for line in child_grid.lines if line.name == "child_line")

    assert restored_line.bus_from in child_bus_set
    assert restored_line.bus_to in child_bus_set


def test_multiverse_activation_rebinds_diagram_locations_to_active_circuit_objects() -> None:
    """
    Verify scenario activation leaves diagram locations bound to the active model objects.
    """
    mv = vge.MultiVerse(_build_grid_with_schematic_and_map_diagrams())
    root = mv.root_nodes[0]
    child = mv.create_node(
        data=vge.MultiCircuit(name="child"),
        parent_id=root.node_id,
        position=root.child_count(),
    )

    child_grid = mv.activate_scenario(child.node_id)
    _assert_diagram_locations_point_to_circuit_objects(child_grid)

    root_grid = mv.activate_scenario(root.node_id)
    _assert_diagram_locations_point_to_circuit_objects(root_grid)


def test_multiverse_get_save_data_contains_consistent_metadata() -> None:
    """
    Verify that get_save_data() emits parent/child metadata consistent with the in-memory tree.

    This guards the serialization contract consumed later by parse_json() and the zip loader.
    """
    # Build a sample multiverse and make the sibling the active scenario before serialization.
    mv, root, child, sibling, grandchild = _build_sample_multiverse()
    mv.activate_scenario(sibling.node_id)

    # Serialize metadata and split out the node records from the metadata envelope.
    metadata, model_data, driver_data = mv.get_save_data()
    nodes = metadata["nodes"]

    # Verify both top-level and per-node metadata fields.
    assert metadata["active_node_id"] == sibling.node_id
    assert set(nodes.keys()) == {root.node_id, child.node_id, sibling.node_id, grandchild.node_id}
    assert set(model_data.keys()) == {node.circuit.idtag for node in mv.iter_nodes_depth_first()}

    assert nodes[root.node_id]["parent_id"] is None
    assert nodes[root.node_id]["children"] == [child.node_id, sibling.node_id]
    assert nodes[child.node_id]["parent_id"] == root.node_id
    assert nodes[child.node_id]["children"] == [grandchild.node_id]
    assert nodes[sibling.node_id]["parent_id"] == root.node_id
    assert nodes[sibling.node_id]["children"] == []
    assert nodes[grandchild.node_id]["parent_id"] == child.node_id
    assert nodes[grandchild.node_id]["children"] == []


def test_multiverse_parse_json_initializes_active_state() -> None:
    """
    Verify that parse_json() leaves the loaded multiverse in a usable active state.

    After parsing, the saved active node should be restored, while base_model should still
    point to the authoritative root circuit.
    """
    # Build and serialize a multiverse with a non-root active node.
    mv, root, child, _, _ = _build_sample_multiverse()
    mv.activate_scenario(child.node_id)

    metadata, model_data, driver_data = mv.get_save_data()

    # Parse the payload into a fresh instance.
    loaded_mv = vge.MultiVerse(current_model=None)
    loaded_mv.parse_json(model_data, metadata)

    # The active node must be restored while the base model remains the root.
    assert loaded_mv.current_node.node_id == child.node_id
    assert loaded_mv.current_model is not loaded_mv.current_node.circuit
    _assert_circuits_equal(loaded_mv.current_model, loaded_mv.checkout(loaded_mv.current_node))
    assert loaded_mv.base_model is loaded_mv.root_nodes[0].circuit
    assert loaded_mv.base_model is loaded_mv.get_node(root.node_id).circuit


def test_multiverse_merge_children_into_parent_updates_current_when_child_was_active() -> None:
    """
    Verify that merging children reassigns the active scenario to the parent when needed.

    If the currently active node is one of the removed children, the multiverse should
    keep a valid active node/model pair by switching to the merge target parent.
    """
    # Build a parent with two children and make one child active before merging.
    mv = vge.MultiVerse(_load_grid("lynn5node.gridcal"))
    root = mv.root_nodes[0]
    child = mv.create_node(
        data=vge.MultiCircuit(name="child"),
        parent_id=root.node_id,
        position=root.child_count(),
    )
    sibling = mv.create_node(
        data=vge.MultiCircuit(name="sibling"),
        parent_id=root.node_id,
        position=root.child_count(),
    )

    # Give each child a distinct edit so both should appear in the merged parent.
    mv.activate_scenario(child.node_id)
    mv.current_model.add_bus(vge.Bus(Vnom=10.0, name="child_bus"))

    mv.activate_scenario(sibling.node_id)
    mv.current_model.add_bus(vge.Bus(Vnom=11.0, name="sibling_bus"))
    mv.commit_current()

    # Merge while the soon-to-be-removed child is active.
    mv.activate_scenario(child.node_id)
    mv.merge_children_into_parent(root.node_id)

    # The active scenario must fall back to the merge target parent with both edits applied.
    assert mv.current_node is root
    assert mv.current_model is root.circuit
    assert _get_bus_by_name(mv.current_model, "child_bus") is not None
    assert _get_bus_by_name(mv.current_model, "sibling_bus") is not None


def test_multiverse_merge_children_into_parent_noop_without_children() -> None:
    """
    Verify that merging a leaf scenario is a no-op and does not corrupt active state.

    This covers the degenerate path where the selected node has no direct children to merge.
    """
    # Build a simple root + leaf tree so the merge target has no direct children.
    mv = vge.MultiVerse(_load_grid("lynn5node.gridcal"))
    root = mv.root_nodes[0]
    leaf = mv.create_node(
        data=vge.MultiCircuit(name="leaf"),
        parent_id=root.node_id,
        position=root.child_count(),
    )

    # Activate the leaf and capture its current composed state.
    leaf_model = mv.activate_scenario(leaf.node_id)
    before_leaf = mv.checkout(leaf)

    # Merging a leaf should do nothing but still keep active state valid.
    result = mv.merge_children_into_parent(leaf.node_id)

    assert result is leaf
    assert mv.current_node is leaf
    _assert_circuits_equal(mv.current_model, leaf_model)
    _assert_circuits_equal(mv.checkout(leaf), before_leaf)
