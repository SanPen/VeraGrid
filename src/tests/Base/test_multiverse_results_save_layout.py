from __future__ import annotations

from pathlib import Path
import zipfile

import numpy as np

import VeraGridEngine.api as vg
from VeraGridEngine.IO.file_save import FileSavingOptions
from VeraGridEngine.IO.file_save import save_veragrid_multiverse
from VeraGridEngine.IO.veragrid.zip_interface import get_session_tree
from VeraGridEngine.IO.veragrid.zip_interface import load_session_driver_objects
from VeraGridEngine.Simulations.InvestmentsEvaluation.investments_evaluation_driver import (
    InvestmentsEvaluationDriver,
)
from VeraGridEngine.Simulations.InvestmentsEvaluation.investments_evaluation_options import (
    InvestmentsEvaluationOptions,
)
from VeraGridEngine.Simulations.InvestmentsEvaluation.investments_evaluation_results import (
    InvestmentsEvaluationResults,
)
from tests.Base.test_dynamic_results_save_load import _build_rms_driver


GRID_FOLDER = Path(__file__).resolve().parents[1] / "data" / "grids"


def test_multiverse_scenario_results_are_saved_under_scenario_sessions_folder(tmp_path: Path) -> None:
    """
    Scenario results must be stored directly under ``multiverse/<idtag>/sessions``.

    The previous layout wrote scenario sessions under ``model_data/sessions`` or
    ``symbolic_data/sessions``, which made the saved scenario look as if it had
    no results folder at all.

    :param tmp_path: Temporary pytest path.
    :return: None.
    """
    base_grid = vg.open_file(str(GRID_FOLDER / "lynn5node.gridcal"))
    multiverse = vg.MultiVerse(base_grid)
    root = multiverse.root_nodes[0]
    child = multiverse.create_node(
        data=vg.MultiCircuit(name="child"),
        parent_id=root.node_id,
        position=root.child_count(),
    )

    driver = InvestmentsEvaluationDriver(
        grid=child.circuit,
        options=InvestmentsEvaluationOptions(max_eval=2),
        problem=None,
    )
    driver.results = InvestmentsEvaluationResults(
        f_names=np.array(["capex"], dtype=str),
        x_names=np.array(["group_0"], dtype=str),
        max_eval=2,
        plot_x_idx=0,
        plot_y_idx=0,
    )
    driver.results.x = np.array([[0.0], [1.0]], dtype=float)
    driver.results.f = np.array([[1.0], [2.0]], dtype=float)
    driver.results.f_best = np.array([1.0], dtype=float)
    driver.results.sorting_indices = np.array([0, 1], dtype=int)
    child.drivers[driver.tpe] = driver

    file_name = tmp_path / "multiverse_results_layout.veragrid"
    vg.save_multiverse(mv=multiverse, filename=str(file_name))

    with zipfile.ZipFile(file_name) as zip_file:
        names = zip_file.namelist()

    child_prefix = f"multiverse/{child.circuit.idtag}/sessions/{driver.name}/{driver.tpe.value}/"
    assert any(name.startswith(child_prefix) for name in names)
    assert f"{child_prefix}x.parquet" in names
    assert f"{child_prefix}f.parquet" in names
    assert f"{child_prefix}logger.parquet" in names

    bad_model_data_prefix = f"multiverse/{child.circuit.idtag}/model_data/sessions/"
    bad_symbolic_prefix = f"multiverse/{child.circuit.idtag}/model_data/symbolic_data/sessions/"
    assert not any(name.startswith(bad_model_data_prefix) for name in names)
    assert not any(name.startswith(bad_symbolic_prefix) for name in names)


def test_multiverse_save_uses_active_sessions_payload_for_rms_results(tmp_path: Path) -> None:
    """
    The multiverse save path must persist the active GUI session payload even when
    the active scenario node has no registered driver objects.

    This reproduces the user-facing failure mode where saving a multiverse with the
    "save results" option enabled produced no ``sessions`` folder at all.

    :param tmp_path: Temporary pytest path.
    :return: None.
    """
    driver = _build_rms_driver()
    multiverse = vg.MultiVerse(driver.grid)

    assert multiverse.current_node is not None
    assert multiverse.current_node.child_count() == 0
    assert len(multiverse.current_node.drivers) == 0

    file_name = tmp_path / "multiverse_rms_results.veragrid"
    options = FileSavingOptions(sessions_data=[driver.get_save_data()])

    save_veragrid_multiverse(
        file_name=str(file_name),
        multiverse=multiverse,
        options=options,
    )

    with zipfile.ZipFile(file_name) as zip_file:
        names = zip_file.namelist()

    scenario_prefix = (
        f"multiverse/{multiverse.current_node.circuit.idtag}/sessions/"
        f"{driver.name}/{driver.tpe.value}/"
    )

    assert any(name.startswith(scenario_prefix) for name in names)
    assert f"{scenario_prefix}time_array.parquet" in names
    assert f"{scenario_prefix}values.npy" in names
    assert f"{scenario_prefix}logger.parquet" in names

    tree_data = get_session_tree(str(file_name))
    assert driver.name in tree_data
    assert driver.tpe.value in tree_data[driver.name]

    loaded_data = load_session_driver_objects(
        file_name_zip=str(file_name),
        session_name=driver.name,
        study_name=driver.tpe.value,
    )
    assert "time_array" in loaded_data
    assert "values" in loaded_data
