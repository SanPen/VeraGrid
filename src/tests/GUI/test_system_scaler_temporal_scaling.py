import numpy as np
import pandas as pd
from PySide6 import QtCore
from PySide6 import QtWidgets

import VeraGridEngine.Devices as dev
from VeraGrid.Gui.SystemScaler.system_scaler import (
    SystemScalingCheckpoint,
    SystemScalingModel,
    SystemScaler,
    apply_time_series_scaling_from_checkpoints,
    interpolate_time_series_scaling,
)
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.enumerations import DeviceType


def build_temporal_scaling_grid() -> MultiCircuit:
    """
    Build a two-area grid with load and generator profiles.

    :return: Test grid.
    """
    grid: MultiCircuit = MultiCircuit()
    area_1: dev.Area = dev.Area(name="Area 1")
    area_2: dev.Area = dev.Area(name="Area 2")
    zone_1: dev.Zone = dev.Zone(name="Zone 1", area=area_1)
    zone_2: dev.Zone = dev.Zone(name="Zone 2", area=area_2)
    time_profile: pd.DatetimeIndex = pd.date_range("2026-01-01 00:00:00", periods=5, freq="h")

    grid.add_area(obj=area_1)
    grid.add_area(obj=area_2)
    grid.add_zone(obj=zone_1)
    grid.add_zone(obj=zone_2)
    grid.format_profiles(index=time_profile)

    bus_1: dev.Bus = dev.Bus(name="Bus 1", area=area_1, zone=zone_1)
    bus_2: dev.Bus = dev.Bus(name="Bus 2", area=area_2, zone=zone_2)
    grid.add_bus(obj=bus_1)
    grid.add_bus(obj=bus_2)

    load_1: dev.Load = dev.Load(name="Load 1", P=10.0, Q=2.0)
    load_2: dev.Load = dev.Load(name="Load 2", P=20.0, Q=4.0)
    gen_1: dev.Generator = dev.Generator(name="Gen 1", P=30.0)
    gen_2: dev.Generator = dev.Generator(name="Gen 2", P=40.0)

    grid.add_load(bus=bus_1, api_obj=load_1)
    grid.add_load(bus=bus_2, api_obj=load_2)
    grid.add_generator(bus=bus_1, api_obj=gen_1)
    grid.add_generator(bus=bus_2, api_obj=gen_2)

    load_1.P_prof.set(np.ones(5, dtype=float) * 10.0)
    load_1.Q_prof.set(np.ones(5, dtype=float) * 2.0)
    load_2.P_prof.set(np.ones(5, dtype=float) * 20.0)
    load_2.Q_prof.set(np.ones(5, dtype=float) * 4.0)
    gen_1.P_prof.set(np.ones(5, dtype=float) * 30.0)
    gen_2.P_prof.set(np.ones(5, dtype=float) * 40.0)

    return grid


def build_scaling_model(
        grid: MultiCircuit,
        table_view: QtWidgets.QTableView,
        factors: np.ndarray,
) -> SystemScalingModel:
    """
    Build an area scaling model with explicit load and generation factors.

    :param grid: Test grid.
    :param table_view: Parent table view required by the Qt model.
    :param factors: Load/generation factors by area row.
    :return: Configured scaling model.
    """
    model: SystemScalingModel = SystemScalingModel(
        device_tpe=DeviceType.AreaDevice,
        grid=grid,
        parent=table_view,
    )
    model.set_load_generation_scaling_factors(factors=factors)
    return model


def test_interpolate_time_series_scaling_uses_checkpoints(qt_app: object) -> None:
    """
    Check that checkpoint models produce a temporal scaling cube.

    :param qt_app: Shared Qt application fixture.
    :return: Nothing.
    """
    del qt_app

    grid: MultiCircuit = build_temporal_scaling_grid()
    table_view: QtWidgets.QTableView = QtWidgets.QTableView()
    first_model: SystemScalingModel = build_scaling_model(
        grid=grid,
        table_view=table_view,
        factors=np.array([[1.0, 1.0], [2.0, 3.0]], dtype=float),
    )
    last_model: SystemScalingModel = build_scaling_model(
        grid=grid,
        table_view=table_view,
        factors=np.array([[3.0, 5.0], [4.0, 7.0]], dtype=float),
    )
    checkpoints: list[SystemScalingCheckpoint] = list()
    checkpoints.append(SystemScalingCheckpoint(time_key=0, model=first_model))
    checkpoints.append(SystemScalingCheckpoint(time_key=4, model=last_model))

    temporal_scaling: np.ndarray = interpolate_time_series_scaling(
        time_profile=grid.time_profile,
        checkpoints=checkpoints,
    )

    assert temporal_scaling.shape == (5, 2, 2)
    np.testing.assert_allclose(temporal_scaling[:, 0, 0], np.array([1.0, 1.5, 2.0, 2.5, 3.0]))
    np.testing.assert_allclose(temporal_scaling[:, 0, 1], np.array([1.0, 2.0, 3.0, 4.0, 5.0]))
    np.testing.assert_allclose(temporal_scaling[:, 1, 0], np.array([2.0, 3.5, 5.0, 6.5, 8.0]))
    np.testing.assert_allclose(temporal_scaling[:, 1, 1], np.array([3.0, 7.5, 12.0, 16.5, 21.0]))

    table_view.close()
    table_view.deleteLater()


def test_apply_time_series_scaling_from_checkpoints_scales_profiles(qt_app: object) -> None:
    """
    Check that temporal factors are applied to load and generator profiles.

    :param qt_app: Shared Qt application fixture.
    :return: Nothing.
    """
    del qt_app

    grid: MultiCircuit = build_temporal_scaling_grid()
    table_view: QtWidgets.QTableView = QtWidgets.QTableView()
    first_model: SystemScalingModel = build_scaling_model(
        grid=grid,
        table_view=table_view,
        factors=np.array([[1.0, 1.0], [2.0, 3.0]], dtype=float),
    )
    last_model: SystemScalingModel = build_scaling_model(
        grid=grid,
        table_view=table_view,
        factors=np.array([[3.0, 5.0], [4.0, 7.0]], dtype=float),
    )
    checkpoints: list[SystemScalingCheckpoint] = list()
    checkpoints.append(SystemScalingCheckpoint(time_key=0, model=first_model))
    checkpoints.append(SystemScalingCheckpoint(time_key=4, model=last_model))

    apply_time_series_scaling_from_checkpoints(model=first_model, checkpoints=checkpoints)

    load_1: dev.Load = grid.get_loads()[0]
    load_2: dev.Load = grid.get_loads()[1]
    gen_1: dev.Generator = grid.get_generators()[0]
    gen_2: dev.Generator = grid.get_generators()[1]

    np.testing.assert_allclose(load_1.P_prof.toarray(), np.array([10.0, 15.0, 20.0, 25.0, 30.0]))
    np.testing.assert_allclose(load_1.Q_prof.toarray(), np.array([2.0, 3.0, 4.0, 5.0, 6.0]))
    np.testing.assert_allclose(load_2.P_prof.toarray(), np.array([40.0, 70.0, 100.0, 130.0, 160.0]))
    np.testing.assert_allclose(load_2.Q_prof.toarray(), np.array([8.0, 14.0, 20.0, 26.0, 32.0]))
    np.testing.assert_allclose(gen_1.P_prof.toarray(), np.array([30.0, 60.0, 90.0, 120.0, 150.0]))
    np.testing.assert_allclose(gen_2.P_prof.toarray(), np.array([120.0, 300.0, 480.0, 660.0, 840.0]))

    table_view.close()
    table_view.deleteLater()


def test_system_scaler_add_checkpoint_copies_previous_grouping_values(qt_app: object) -> None:
    """
    Check that the dialog creates a default snapshot checkpoint and seeds new matching groups.

    :param qt_app: Shared Qt application fixture.
    :return: Nothing.
    """
    del qt_app

    grid: MultiCircuit = build_temporal_scaling_grid()
    window: SystemScaler = SystemScaler(grid=grid)
    factors: np.ndarray = np.array([[1.25, 2.25], [3.25, 4.25]], dtype=float)

    assert len(window.checkpoints) == 1
    assert window.checkpoints[0].time_key is None

    window.checkpoints[0].model.set_load_generation_scaling_factors(factors=factors)
    window.add_checkpoint()

    assert len(window.checkpoints) == 2
    assert window.checkpoints[1].time_key == 0
    np.testing.assert_allclose(window.checkpoints[1].model._data[:, 0:2], factors)

    first_inserted_row: int = 1

    assert window.checkpoints_model.data(window.checkpoints_model.index(first_inserted_row, 2)) == "226.88"

    window.close()
    window.deleteLater()


def test_system_scaler_add_checkpoint_advances_timed_checkpoint(qt_app: object) -> None:
    """
    Check that adding after a timed checkpoint advances one time index.

    :param qt_app: Shared Qt application fixture.
    :return: Nothing.
    """
    del qt_app

    grid: MultiCircuit = build_temporal_scaling_grid()
    window: SystemScaler = SystemScaler(grid=grid)
    time_index: QtCore.QModelIndex = window.checkpoints_model.index(0, 0)

    window.checkpoints_model.setData(time_index, grid.time_profile[2])
    window.add_checkpoint()

    assert len(window.checkpoints) == 2
    assert window.checkpoints[1].time_key == 3

    window.close()
    window.deleteLater()


def test_system_scaler_remove_selected_checkpoints(qt_app: object) -> None:
    """
    Check that remove deletes all selected checkpoint rows.

    :param qt_app: Shared Qt application fixture.
    :return: Nothing.
    """
    del qt_app

    grid: MultiCircuit = build_temporal_scaling_grid()
    window: SystemScaler = SystemScaler(grid=grid)
    time_index: QtCore.QModelIndex = window.checkpoints_model.index(0, 0)

    window.checkpoints_model.setData(time_index, grid.time_profile[0])
    window.add_checkpoint()
    window.add_checkpoint()
    window.add_checkpoint()

    assert len(window.checkpoints) == 4

    selection_model: QtCore.QItemSelectionModel = window.ui.checkpointsTableView.selectionModel()
    selection_model.clearSelection()
    checkpoint_1_row: int = 1
    checkpoint_2_row: int = 2
    selection_model.select(window.checkpoints_model.index(checkpoint_1_row, 0),
                           QtCore.QItemSelectionModel.SelectionFlag.Select |
                           QtCore.QItemSelectionModel.SelectionFlag.Rows)
    selection_model.select(window.checkpoints_model.index(checkpoint_2_row, 0),
                           QtCore.QItemSelectionModel.SelectionFlag.Select |
                           QtCore.QItemSelectionModel.SelectionFlag.Rows)

    window.remove_checkpoint()

    assert len(window.checkpoints) == 2
    assert window.checkpoints[0].time_key == 0
    assert window.checkpoints[1].time_key == 3

    window.close()
    window.deleteLater()


def test_system_scaler_checkpoint_table_edits_grouping_and_time(qt_app: object) -> None:
    """
    Check that checkpoint table edits update grouping models and time keys.

    :param qt_app: Shared Qt application fixture.
    :return: Nothing.
    """
    del qt_app

    grid: MultiCircuit = build_temporal_scaling_grid()
    window: SystemScaler = SystemScaler(grid=grid)
    time_index: QtCore.QModelIndex = window.checkpoints_model.index(0, 0)
    grouping_index: QtCore.QModelIndex = window.checkpoints_model.index(0, 1)

    assert window.ui.checkpointsTableView.itemDelegateForColumn(0) is not None
    assert window.ui.checkpointsTableView.itemDelegateForColumn(1) is not None
    assert window.checkpoints_model.headerData(0, QtCore.Qt.Orientation.Horizontal) == "Time"
    assert window.checkpoints_model.headerData(1, QtCore.Qt.Orientation.Horizontal) == "Grouping"
    assert window.checkpoints_model.headerData(2, QtCore.Qt.Orientation.Horizontal) == "Total load (MW)"

    window.checkpoints_model.setData(grouping_index, DeviceType.ZoneDevice)

    assert window.checkpoints[0].model.device_tpe == DeviceType.ZoneDevice
    assert window.ui.checkpointDataTableView.model() is window.checkpoints[0].model
    assert window.checkpoints[0].model.columnCount() == 2
    assert window.checkpoints[0].model.headerData(0, QtCore.Qt.Orientation.Horizontal) == "Load factor"
    assert window.checkpoints[0].model.headerData(1, QtCore.Qt.Orientation.Horizontal) == "Generation factor"
    assert window.checkpoints[0].model.headerData(0, QtCore.Qt.Orientation.Vertical) == "Zone 1"

    window.checkpoints_model.setData(time_index, grid.time_profile[2])

    assert window.checkpoints[0].time_key == 2
    assert window.checkpoints_model.data(time_index) == str(grid.time_profile[2])

    load_factor_index: QtCore.QModelIndex = window.checkpoints[0].model.index(0, 0)
    window.checkpoints[0].model.setData(load_factor_index, 2.0)

    assert window.checkpoints_model.data(window.checkpoints_model.index(0, 2)) == "40.00"

    window.close()
    window.deleteLater()


def test_system_scaler_checkpoint_totals_are_cumulative(qt_app: object) -> None:
    """
    Check that editing a previous checkpoint updates later checkpoint totals.

    :param qt_app: Shared Qt application fixture.
    :return: Nothing.
    """
    del qt_app

    grid: MultiCircuit = build_temporal_scaling_grid()
    window: SystemScaler = SystemScaler(grid=grid)
    time_index: QtCore.QModelIndex = window.checkpoints_model.index(0, 0)

    window.checkpoints_model.setData(time_index, grid.time_profile[0])
    window.checkpoints[0].model.setData(window.checkpoints[0].model.index(0, 0), 2.0)
    window.add_checkpoint()
    window.checkpoints[1].model.setData(window.checkpoints[1].model.index(0, 0), 3.0)

    assert window.checkpoints[1].time_key == 1
    assert window.checkpoints_model.data(window.checkpoints_model.index(1, 2)) == "80.00"

    window.ui.checkpointsTableView.selectRow(0)
    window.set_current_checkpoint_data_model(checkpoint_idx=0)
    window.checkpoints[0].model.setData(window.checkpoints[0].model.index(0, 0), 4.0)

    assert window.checkpoints_model.data(window.checkpoints_model.index(0, 2)) == "60.00"
    assert window.checkpoints_model.data(window.checkpoints_model.index(1, 2)) == "140.00"

    invalid_time_index: QtCore.QModelIndex = window.checkpoints_model.index(1, 0)
    accepted: bool = window.checkpoints_model.setData(invalid_time_index, grid.time_profile[0])

    assert not accepted
    assert window.checkpoints[1].time_key == 1

    window.close()
    window.deleteLater()


def test_system_scaler_preview_arrays_do_not_mutate_profiles(qt_app: object) -> None:
    """
    Check that scaling preview aggregates scaled arrays without changing device profiles.

    :param qt_app: Shared Qt application fixture.
    :return: Nothing.
    """
    del qt_app

    grid: MultiCircuit = build_temporal_scaling_grid()
    window: SystemScaler = SystemScaler(grid=grid)
    first_load: dev.Load = grid.get_loads()[0]
    original_profile: np.ndarray = first_load.P_prof.toarray().copy()
    factors: np.ndarray = np.array([[2.0, 1.0], [1.0, 1.0]], dtype=float)

    window.checkpoints[0].model.set_load_generation_scaling_factors(factors=factors)

    time_profile: pd.DatetimeIndex
    original_load: np.ndarray
    scaled_load: np.ndarray
    original_generation: np.ndarray
    scaled_generation: np.ndarray
    time_profile, original_load, scaled_load, original_generation, scaled_generation = window.get_scaling_preview_arrays()

    assert len(time_profile) == 5
    np.testing.assert_allclose(first_load.P_prof.toarray(), original_profile)
    np.testing.assert_allclose(original_load, np.ones(5, dtype=float) * 30.0)
    np.testing.assert_allclose(scaled_load, np.ones(5, dtype=float) * 40.0)
    np.testing.assert_allclose(original_generation, scaled_generation)

    window.close()
    window.deleteLater()


def test_system_scaler_preview_arrays_use_cumulative_checkpoints(qt_app: object) -> None:
    """
    Check that plot preview arrays use cumulative checkpoint factors.

    :param qt_app: Shared Qt application fixture.
    :return: Nothing.
    """
    del qt_app

    grid: MultiCircuit = build_temporal_scaling_grid()
    window: SystemScaler = SystemScaler(grid=grid)
    factors: np.ndarray = np.array([[2.0, 1.0], [1.0, 1.0]], dtype=float)

    window.checkpoints[0].model.set_load_generation_scaling_factors(factors=factors)
    window.add_checkpoint()

    time_profile: pd.DatetimeIndex
    original_load: np.ndarray
    scaled_load: np.ndarray
    original_generation: np.ndarray
    scaled_generation: np.ndarray
    time_profile, original_load, scaled_load, original_generation, scaled_generation = window.get_scaling_preview_arrays()

    assert len(time_profile) == 5
    np.testing.assert_allclose(original_load, np.ones(5, dtype=float) * 30.0)
    np.testing.assert_allclose(scaled_load, np.ones(5, dtype=float) * 60.0)
    np.testing.assert_allclose(original_generation, scaled_generation)

    window.close()
    window.deleteLater()


def test_system_scaler_plot_is_embedded_in_plot_frame(qt_app: object) -> None:
    """
    Check that the scaling preview plot is embedded in the plot frame.

    :param qt_app: Shared Qt application fixture.
    :return: Nothing.
    """
    del qt_app

    grid: MultiCircuit = build_temporal_scaling_grid()
    window: SystemScaler = SystemScaler(grid=grid)

    assert window.ui.verticalLayout_2.indexOf(window.plot_canvas) >= 0
    assert window.ui.verticalLayout_2.indexOf(window.plot_toolbar) >= 0

    window.plot_scaling()

    assert len(window.plot_figure.axes) == 2

    window.close()
    window.deleteLater()
