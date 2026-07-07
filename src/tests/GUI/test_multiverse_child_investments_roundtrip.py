from __future__ import annotations

from pathlib import Path

import VeraGridEngine.api as vge


GRID_FOLDER = Path(__file__).resolve().parents[1] / "data" / "grids"


def _assert_circuits_equal(grid1: vge.MultiCircuit, grid2: vge.MultiCircuit) -> None:
    """
    Assert semantic circuit equality and print the engine logger on mismatch.
    """
    equal, logger = grid1.compare_circuits(
        grid2,
        detailed_profile_comparison=True,
        skip_internals=True,
    )

    if not equal:
        logger.print()

    assert equal


def test_multiverse_child_investments_survive_save_load_roundtrip(tmp_path: Path) -> None:
    """
    Verify child-only investments persist through multiverse save/load and rebind to the loaded child circuit.
    """
    base_grid = vge.open_file(str(GRID_FOLDER / "lynn5node.gridcal"))
    mv = vge.MultiVerse(base_grid)

    root = mv.root_nodes[0]
    child = mv.create_node(
        data=vge.MultiCircuit(name="child"),
        parent_id=root.node_id,
        position=root.child_count(),
    )

    mv.activate_scenario(child.node_id)
    target_line = mv.current_model.lines[0]
    target_line_idtag = target_line.idtag

    group = vge.InvestmentsGroup(name="child-investment-group", category="single")
    mv.current_model.add_investments_group(group)
    mv.current_model.add_investment(
        vge.Investment(
            device=target_line,
            name="child-line-investment",
            CAPEX=12.5,
            status=True,
            group=group,
        )
    )
    mv.commit_current()

    root_before_save = mv.checkout(root)
    child_before_save = mv.checkout(child)

    assert len(root_before_save.investments_groups) == 0
    assert len(root_before_save.investments) == 0
    assert len(child_before_save.investments_groups) == 1
    assert len(child_before_save.investments) == 1
    child_before_save_line = next(line for line in child_before_save.lines if line.idtag == target_line_idtag)
    assert child_before_save.investments[0].device is child_before_save_line
    assert child_before_save.investments[0].group is child_before_save.investments_groups[0]

    file_name = tmp_path / "multiverse_child_investments.veragrid"
    vge.save_multiverse(mv=mv, filename=str(file_name))

    loader = vge.FileOpen(str(file_name))
    loader.open()

    assert loader.multiverse is not None

    loaded_mv = loader.multiverse
    loaded_root = loaded_mv.get_node(root.node_id)
    loaded_child = loaded_mv.get_node(child.node_id)

    loaded_root_grid = loaded_mv.checkout(loaded_root)
    loaded_child_grid = loaded_mv.activate_scenario(loaded_child.node_id)

    _assert_circuits_equal(root_before_save, loaded_root_grid)

    expected_child_network = child_before_save.copy()
    expected_child_network.investments_groups = list()
    expected_child_network.investments = list()

    loaded_child_network = loaded_child_grid.copy()
    loaded_child_network.investments_groups = list()
    loaded_child_network.investments = list()

    _assert_circuits_equal(expected_child_network, loaded_child_network)

    assert len(loaded_root_grid.investments_groups) == 0
    assert len(loaded_root_grid.investments) == 0
    assert len(loaded_child_grid.investments_groups) == 1
    assert len(loaded_child_grid.investments) == 1

    loaded_group = loaded_child_grid.investments_groups[0]
    loaded_investment = loaded_child_grid.investments[0]
    loaded_line = next(line for line in loaded_child_grid.lines if line.idtag == target_line_idtag)

    assert loaded_group.name == "child-investment-group"
    assert loaded_group.category == "single"
    assert loaded_investment.group is loaded_group
    assert loaded_investment.device is loaded_line
    assert loaded_investment.device.idtag == target_line_idtag
    assert loaded_investment.name == "child-line-investment"
    assert loaded_investment.CAPEX == 12.5
