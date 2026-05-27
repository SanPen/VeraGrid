from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

import numpy as np
from PySide6 import QtCore

from VeraGrid.Gui.Main.SubClasses.Results.dynamics_results_handler import DynamicsResultsHandler
from VeraGridEngine.Devices.Events.dynamic_plot import DynamicPlot
from VeraGridEngine.Devices.Events.dynamic_plot_entry import DynamicPlotEntry
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Simulations.EMT.emt_results import EmtResults
from VeraGridEngine.Simulations.Rms.rms_results import RmsResults
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import DeviceType, PlotSimulationType


class FakeDynamicDevice:
    """
    Minimal device object used to exercise dynamic-results tree matching.
    """

    def __init__(self, name: str, idtag: str, device_type: DeviceType) -> None:
        """
        Build one fake dynamics device.

        :param name: Device name exposed in the GUI tree.
        :param idtag: Stable device identifier used across repeated simulations.
        :param device_type: Device type used by the results tree.
        :return: None.
        """
        self.name: str = name
        self.idtag: str = idtag
        self.device_type: DeviceType = device_type

    def __str__(self) -> str:
        """
        Return the GUI label for this fake device.

        :return: Device name.
        """
        return self.name

    def __hash__(self) -> int:
        """
        Hash the fake device by its stable identity.

        :return: Hash value.
        """
        return hash((self.idtag, self.name, self.device_type))

    def __eq__(self, other: object) -> bool:
        """
        Compare fake devices by stable identity.

        :param other: Object to compare.
        :return: ``True`` when both fake devices match.
        """
        if isinstance(other, FakeDynamicDevice):
            return ((self.idtag, self.name, self.device_type)
                    == (other.idtag, other.name, other.device_type))
        else:
            return False


def ensure_qt_application() -> QtCore.QCoreApplication:
    """
    Ensure a Qt core application exists for Qt model creation.

    :return: Existing or newly created Qt core application.
    """
    application: QtCore.QCoreApplication | None = QtCore.QCoreApplication.instance()
    if application is None:
        application = QtCore.QCoreApplication(list())
    else:
        pass
    return application


def make_device(name: str, idtag: str) -> FakeDynamicDevice:
    """
    Build one fake device with a consistent dynamic device type.

    :param name: Device name.
    :param idtag: Stable device identifier.
    :return: Fake device.
    """
    return FakeDynamicDevice(name=name, idtag=idtag, device_type=DeviceType.NoDevice)


def make_var(name: str, uid: int) -> Var:
    """
    Build one symbolic variable with an explicit uid.

    :param name: Variable name.
    :param uid: Variable uid.
    :return: Variable object.
    """
    return Var(name=name, uid=uid)


def build_rms_results(device_entries: Sequence[Tuple[FakeDynamicDevice, Sequence[Var]]]) -> RmsResults:
    """
    Build a minimal RMS results object for handler tests.

    :param device_entries: Devices and their plotted variables.
    :return: RMS results object.
    """
    time_array: np.ndarray = np.array([0.0, 1.0], dtype=float)
    group_names: np.ndarray = np.array(["Group 1"], dtype=str)
    group_idtags: np.ndarray = np.array(["rms-group-1"], dtype=str)
    has_event_group_results: np.ndarray = np.ones(len(group_names), dtype=bool)
    variables: List[Var] = list()
    uid2idx: Dict[int, int] = dict()
    vars_glob_name2uid: Dict[str, int] = dict()
    devices_vars_info: Dict[FakeDynamicDevice, List[Var]] = dict()

    device: FakeDynamicDevice
    device_variables: Sequence[Var]
    for device, device_variables in device_entries:
        device_var_list: List[Var] = list(device_variables)
        devices_vars_info[device] = device_var_list

        variable: Var
        for variable in device_var_list:
            uid2idx[variable.uid] = len(variables)
            vars_glob_name2uid[device.idtag + ":" + variable.name + ":" + str(variable.uid)] = variable.uid
            variables.append(variable)

    results: RmsResults = RmsResults(
        time_array=time_array,
        rms_events_group_names=group_names,
        rms_events_group_idtags=group_idtags,
        variables=variables,
        uid2idx=uid2idx,
        vars_glob_name2uid=vars_glob_name2uid,
        devices_vars_info=devices_vars_info,
        has_event_group_results=has_event_group_results,
    )

    if len(variables) > 0:
        results.values[:, :, 0] = np.arange(results.nt * results.nv, dtype=float).reshape(results.nt, results.nv)
    else:
        pass

    return results


def build_emt_results(device_entries: Sequence[Tuple[FakeDynamicDevice, Sequence[Var]]]) -> EmtResults:
    """
    Build a minimal EMT results object for handler tests.

    :param device_entries: Devices and their plotted variables.
    :return: EMT results object.
    """
    time_array: np.ndarray = np.array([0.0, 1.0], dtype=float)
    group_names: np.ndarray = np.array(["Group 1"], dtype=str)
    group_idtags: np.ndarray = np.array(["emt-group-1"], dtype=str)
    has_event_group_results: np.ndarray = np.ones(len(group_names), dtype=bool)
    variables: List[Var] = list()
    uid2idx_vars: Dict[int, int] = dict()
    uid2idx_diff: Dict[int, int] = dict()
    vars_glob_name2uid: Dict[str, int] = dict()
    devices_vars_info: Dict[FakeDynamicDevice, List[Var]] = dict()

    device: FakeDynamicDevice
    device_variables: Sequence[Var]
    for device, device_variables in device_entries:
        device_var_list: List[Var] = list(device_variables)
        devices_vars_info[device] = device_var_list

        variable: Var
        for variable in device_var_list:
            uid2idx_vars[variable.uid] = len(variables)
            vars_glob_name2uid[device.idtag + ":" + variable.name + ":" + str(variable.uid)] = variable.uid
            variables.append(variable)

    results: EmtResults = EmtResults(
        time_array=time_array,
        emt_events_group_names=group_names,
        emt_events_group_idtags=group_idtags,
        variables=variables,
        diff_variables=list(),
        uid2idx_vars=uid2idx_vars,
        uid2idx_diff=uid2idx_diff,
        vars_glob_name2uid=vars_glob_name2uid,
        devices_vars_info=devices_vars_info,
        has_event_group_results=has_event_group_results,
    )

    if len(variables) > 0:
        results.values[:, :, 0] = np.arange(results.nt * results.nv, dtype=float).reshape(results.nt, results.nv)
    else:
        pass

    return results


def build_rms_results_with_unexported_device_var(device: FakeDynamicDevice,
                                                 exported_var: Var,
                                                 unexported_var: Var) -> RmsResults:
    """
    Build one RMS results object whose device tree contains one unexported variable.

    :param device: Device referenced by the results tree.
    :param exported_var: Variable present in ``results.values``.
    :param unexported_var: Variable present only in ``devices_vars_info``.
    :return: RMS results object.
    """
    results: RmsResults = RmsResults(
        time_array=np.array([0.0, 1.0], dtype=float),
        rms_events_group_names=np.array(["Group 1"], dtype=str),
        rms_events_group_idtags=np.array(["rms-group-1"], dtype=str),
        variables=[exported_var],
        uid2idx={exported_var.uid: 0},
        vars_glob_name2uid={device.idtag + ":" + exported_var.name + ":" + str(exported_var.uid): exported_var.uid},
        devices_vars_info={device: [exported_var, unexported_var]},
        has_event_group_results=np.ones(1, dtype=bool),
    )
    results.values[:, :, 0] = np.array([[0.0], [1.0]], dtype=float)
    return results


def build_rms_results_with_groups(device_entries: Sequence[Tuple[FakeDynamicDevice, Sequence[Var]]],
                                  group_names: Sequence[str]) -> RmsResults:
    """
    Build RMS results with an explicit set of event-group labels.

    :param device_entries: Devices and their plotted variables.
    :param group_names: Ordered RMS event-group names.
    :return: RMS results object.
    """
    # The helper intentionally reshapes the single-group fixture into a
    # multi-group fixture so the binding tests can exercise event-group
    # restoration logic without running full simulations.
    results: RmsResults = build_rms_results(device_entries=device_entries)
    results.rms_events_group_names = np.array(group_names, dtype=str)
    results.rms_events_group_idtags = np.array(
        ["rms-group-" + str(group_name).replace(" ", "-").lower() for group_name in group_names],
        dtype=str,
    )
    results.ng = len(group_names)
    results.has_event_group_results = np.ones(results.ng, dtype=bool)
    results.well_initialized = np.zeros(results.ng, dtype=bool)
    results.converged = np.zeros(results.ng, dtype=bool)
    results.values = np.zeros((results.nt, results.nv, results.ng), dtype=float)
    if results.nv > 0:
        results.values[:, :, :] = np.arange(results.nt * results.nv * results.ng, dtype=float).reshape(
            results.nt,
            results.nv,
            results.ng,
        )
    else:
        pass
    return results


def get_group_var_uids(handler: DynamicsResultsHandler, group_name: str) -> List[int]:
    """
    Get the restored variable uids stored in one plot group.

    :param handler: Dynamics results handler under test.
    :param group_name: Plot-group name.
    :return: Variable uids in insertion order.
    """
    group = handler.plot_groups.get_group(name=group_name)
    if group is not None:
        return [variable.uid for variable in group.get_vars()]
    else:
        return list()


def get_group_series_group_indexes(handler: DynamicsResultsHandler, group_name: str) -> List[int]:
    """
    Get the restored event-group indexes stored in one plot group.

    :param handler: Dynamics results handler under test.
    :param group_name: Plot-group name.
    :return: Event-group indexes in insertion order.
    """
    group = handler.plot_groups.get_group(name=group_name)
    if group is not None:
        return [series.get_group_idx() for series in group.get_series()]
    else:
        return list()


def build_handler_with_group(results: RmsResults | EmtResults,
                             group_name: str,
                             variable_uids: Sequence[int]) -> DynamicsResultsHandler:
    """
    Build a handler and populate one plot group through the public CRUD API.

    :param results: Initial RMS or EMT results object.
    :param group_name: Plot-group name to create.
    :param variable_uids: Variable uids to add to the group.
    :return: Populated handler.
    """
    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=results)
    created: bool = handler.create_plot_group(name=group_name)
    assert created is True

    variable_uid: int
    for variable_uid in variable_uids:
        inserted: bool = handler.add_var_to_group(group_name=group_name, var_uid=variable_uid)
        assert inserted is True

    return handler


def test_dynamic_plot_restores_same_var_when_uid_changes() -> None:
    """
    Restore one variable when only its uid changes across RMS runs.
    """
    ensure_qt_application()

    old_results: RmsResults = build_rms_results([
        (make_device(name="DeviceA", idtag="dev-a"), [make_var(name="v_A", uid=1)]),
    ])
    new_results: RmsResults = build_rms_results([
        (make_device(name="DeviceA", idtag="dev-a"), [make_var(name="v_A", uid=101)]),
    ])

    handler: DynamicsResultsHandler = build_handler_with_group(results=old_results,
                                                               group_name="Plot 1",
                                                               variable_uids=[1])
    handler.update_results(results=new_results)

    assert get_group_var_uids(handler=handler, group_name="Plot 1") == [101]


def test_dynamic_plot_restores_remaining_vars_only() -> None:
    """
    Restore only the variables that still exist after an RMS rerun.
    """
    ensure_qt_application()

    old_results: RmsResults = build_rms_results([
        (make_device(name="DeviceA", idtag="dev-a"), [make_var(name="v_A", uid=1), make_var(name="i_A", uid=2)]),
    ])
    new_results: RmsResults = build_rms_results([
        (make_device(name="DeviceA", idtag="dev-a"), [make_var(name="v_A", uid=101)]),
    ])

    handler: DynamicsResultsHandler = build_handler_with_group(results=old_results,
                                                               group_name="Plot 1",
                                                               variable_uids=[1, 2])
    handler.update_results(results=new_results)

    assert get_group_var_uids(handler=handler, group_name="Plot 1") == [101]


def test_dynamic_plot_keeps_group_empty_when_device_name_changes() -> None:
    """
    Restore a variable when the stable device idtag still matches.
    """
    ensure_qt_application()

    old_results: RmsResults = build_rms_results([
        (make_device(name="DeviceA", idtag="dev-a"), [make_var(name="v_A", uid=1)]),
    ])
    new_results: RmsResults = build_rms_results([
        (make_device(name="DeviceB", idtag="dev-a"), [make_var(name="v_A", uid=101)]),
    ])

    handler: DynamicsResultsHandler = build_handler_with_group(results=old_results,
                                                               group_name="Plot 1",
                                                               variable_uids=[1])
    handler.update_results(results=new_results)

    assert get_group_var_uids(handler=handler, group_name="Plot 1") == [101]


def test_dynamic_plot_keeps_group_empty_when_var_name_changes() -> None:
    """
    Do not restore a variable when its variable name changes.
    """
    ensure_qt_application()

    old_results: RmsResults = build_rms_results([
        (make_device(name="DeviceA", idtag="dev-a"), [make_var(name="v_A", uid=1)]),
    ])
    new_results: RmsResults = build_rms_results([
        (make_device(name="DeviceA", idtag="dev-a"), [make_var(name="v_B", uid=101)]),
    ])

    handler: DynamicsResultsHandler = build_handler_with_group(results=old_results,
                                                               group_name="Plot 1",
                                                               variable_uids=[1])
    handler.update_results(results=new_results)

    assert get_group_var_uids(handler=handler, group_name="Plot 1") == list()


def test_dynamic_plot_skips_ambiguous_visible_signature() -> None:
    """
    Restore the exact matching series even if another visible signature also exists.
    """
    ensure_qt_application()

    old_results: RmsResults = build_rms_results([
        (make_device(name="DeviceA", idtag="dev-a-1"), [make_var(name="v_A", uid=1)]),
    ])
    new_results: RmsResults = build_rms_results([
        (make_device(name="DeviceA", idtag="dev-a-1"), [make_var(name="v_A", uid=101)]),
        (make_device(name="DeviceA", idtag="dev-a-2"), [make_var(name="v_A", uid=102)]),
    ])

    handler: DynamicsResultsHandler = build_handler_with_group(results=old_results,
                                                               group_name="Plot 1",
                                                               variable_uids=[1])
    handler.update_results(results=new_results)

    assert get_group_var_uids(handler=handler, group_name="Plot 1") == [101]


def test_dynamic_plot_restores_multiple_groups() -> None:
    """
    Preserve separate plot groups and their variable assignments.
    """
    ensure_qt_application()

    old_results: RmsResults = build_rms_results([
        (make_device(name="DeviceA", idtag="dev-a"), [make_var(name="v_A", uid=1), make_var(name="i_A", uid=2)]),
    ])
    new_results: RmsResults = build_rms_results([
        (make_device(name="DeviceA", idtag="dev-a"), [make_var(name="v_A", uid=101), make_var(name="i_A", uid=102)]),
    ])

    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=old_results)
    assert handler.create_plot_group(name="Plot 1") is True
    assert handler.create_plot_group(name="Plot 2") is True
    assert handler.add_var_to_group(group_name="Plot 1", var_uid=1) is True
    assert handler.add_var_to_group(group_name="Plot 2", var_uid=2) is True

    handler.update_results(results=new_results)

    assert get_group_var_uids(handler=handler, group_name="Plot 1") == [101]
    assert get_group_var_uids(handler=handler, group_name="Plot 2") == [102]


def test_dynamic_results_handler_type_reuse_protection() -> None:
    """
    Reuse only handlers that stay within the same dynamics results family.
    """
    ensure_qt_application()

    emt_results: EmtResults = build_emt_results([
        (make_device(name="DeviceA", idtag="dev-a"), [make_var(name="v_A", uid=1)]),
    ])
    rms_results: RmsResults = build_rms_results([
        (make_device(name="DeviceA", idtag="dev-a"), [make_var(name="v_A", uid=101)]),
    ])
    new_rms_results: RmsResults = build_rms_results([
        (make_device(name="DeviceA", idtag="dev-a"), [make_var(name="v_A", uid=201)]),
    ])

    emt_handler: DynamicsResultsHandler = DynamicsResultsHandler(results=emt_results)
    rms_handler: DynamicsResultsHandler = DynamicsResultsHandler(results=rms_results)

    assert not type(emt_handler.results) == type(rms_results)
    assert type(rms_handler.results) == type(new_rms_results)


def test_dynamic_plot_can_store_same_var_from_multiple_rms_groups() -> None:
    """
    Allow the same device variable from multiple RMS event groups in one plot.
    """
    ensure_qt_application()

    results: RmsResults = build_rms_results_with_groups([
        (make_device(name="DeviceA", idtag="dev-a"), [make_var(name="v_A", uid=1)]),
    ], group_names=["With event", "Without event"])

    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=results)
    assert handler.create_plot_group(name="Plot 1") is True

    series_list = handler.series_by_var_uid[1]
    assert len(series_list) == 2
    assert handler.add_series_to_group(group_name="Plot 1", series_key=series_list[0].get_key()) is True
    assert handler.add_series_to_group(group_name="Plot 1", series_key=series_list[1].get_key()) is True

    group = handler.plot_groups.get_group(name="Plot 1")
    assert group is not None
    restored_series = group.get_series()
    assert len(restored_series) == 2
    assert restored_series[0].get_key() != restored_series[1].get_key()


def test_dynamic_plot_restores_event_groups_by_label_after_reorder() -> None:
    """
    Restore the same semantic event groups even when a rerun changes their order.
    """
    ensure_qt_application()

    old_results: RmsResults = build_rms_results_with_groups([
        (make_device(name="DeviceA", idtag="dev-a"), [make_var(name="v_A", uid=1)]),
    ], group_names=["With event", "Without event"])
    new_results: RmsResults = build_rms_results_with_groups([
        (make_device(name="DeviceA", idtag="dev-a"), [make_var(name="v_A", uid=101)]),
    ], group_names=["Without event", "With event"])

    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=old_results)
    assert handler.create_plot_group(name="Plot 1") is True

    old_series_list = handler.series_by_var_uid[1]
    assert len(old_series_list) == 2
    assert handler.add_series_to_group(group_name="Plot 1", series_key=old_series_list[0].get_key()) is True
    assert handler.add_series_to_group(group_name="Plot 1", series_key=old_series_list[1].get_key()) is True

    handler.update_results(results=new_results)

    assert get_group_var_uids(handler=handler, group_name="Plot 1") == [101, 101]
    assert get_group_series_group_indexes(handler=handler, group_name="Plot 1") == [1, 0]


def test_dynamic_plot_prunes_missing_event_group_when_only_subset_is_rerun() -> None:
    """
    Keep only the plot entries whose semantic event group still exists.
    """
    ensure_qt_application()

    old_results: RmsResults = build_rms_results_with_groups([
        (make_device(name="DeviceA", idtag="dev-a"), [make_var(name="v_A", uid=1)]),
    ], group_names=["With event", "Without event"])
    new_results: RmsResults = build_rms_results_with_groups([
        (make_device(name="DeviceA", idtag="dev-a"), [make_var(name="v_A", uid=101)]),
    ], group_names=["Without event"])

    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=old_results)
    assert handler.create_plot_group(name="Plot 1") is True

    old_series_list = handler.series_by_var_uid[1]
    assert len(old_series_list) == 2
    assert handler.add_series_to_group(group_name="Plot 1", series_key=old_series_list[0].get_key()) is True
    assert handler.add_series_to_group(group_name="Plot 1", series_key=old_series_list[1].get_key()) is True

    handler.update_results(results=new_results)

    assert get_group_var_uids(handler=handler, group_name="Plot 1") == [101]
    assert get_group_series_group_indexes(handler=handler, group_name="Plot 1") == [0]


def test_dynamic_plot_keeps_unsimulated_rms_event_group_unresolved() -> None:
    """
    Keep the missing RMS event-group curve unresolved when its result column was not simulated.
    """
    ensure_qt_application()

    old_results: RmsResults = build_rms_results_with_groups([
        (make_device(name="DeviceA", idtag="dev-a"), [make_var(name="v_A", uid=1)]),
    ], group_names=["With event", "Without event"])
    old_results.has_event_group_results = np.ones(2, dtype=bool)

    new_results: RmsResults = build_rms_results_with_groups([
        (make_device(name="DeviceA", idtag="dev-a"), [make_var(name="v_A", uid=101)]),
    ], group_names=["With event", "Without event"])
    new_results.has_event_group_results = np.array([True, False], dtype=bool)
    new_results.values[:, :, 1] = 0.0

    circuit: MultiCircuit = MultiCircuit(name="rms-unsimulated-group")
    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=old_results, circuit=circuit)
    assert handler.create_plot_group(name="Plot 1") is True

    old_series_list = handler.series_by_var_uid[1]
    assert len(old_series_list) == 2
    assert handler.add_series_to_group(group_name="Plot 1", series_key=old_series_list[0].get_key()) is True
    assert handler.add_series_to_group(group_name="Plot 1", series_key=old_series_list[1].get_key()) is True

    handler.update_results(results=new_results)

    group: object = handler.plot_groups.get_group(name="Plot 1")
    assert group is not None
    group_entries: List[object] = group.get_series()
    assert len(group_entries) == 2
    assert isinstance(group_entries[0], DynamicPlotEntry) is False
    assert isinstance(group_entries[1], DynamicPlotEntry) is True
    assert group_entries[0].get_var().uid == 101
    assert group_entries[1].variable is not None
    assert group_entries[1].variable.uid == 1


def test_dynamic_plot_keeps_unsimulated_emt_event_group_unresolved() -> None:
    """
    Keep the missing EMT event-group curve unresolved when its result column was not simulated.
    """
    ensure_qt_application()

    old_results: EmtResults = build_emt_results([
        (make_device(name="DeviceA", idtag="dev-a"), [make_var(name="v_A", uid=1)]),
    ])
    old_results.emt_events_group_names = np.array(["With event", "Without event"], dtype=str)
    old_results.emt_events_group_idtags = np.array(["emt-group-with-event", "emt-group-without-event"], dtype=str)
    old_results.ng = 2
    old_results.has_event_group_results = np.ones(2, dtype=bool)
    old_results.well_initialized = np.zeros(2, dtype=bool)
    old_results.converged = np.zeros(2, dtype=bool)
    old_results.values = np.repeat(old_results.values, 2, axis=2)
    old_results.diff_values = np.zeros((old_results.nt, old_results.ndv, old_results.ng), dtype=float)

    new_results: EmtResults = build_emt_results([
        (make_device(name="DeviceA", idtag="dev-a"), [make_var(name="v_A", uid=101)]),
    ])
    new_results.emt_events_group_names = np.array(["With event", "Without event"], dtype=str)
    new_results.emt_events_group_idtags = np.array(["emt-group-with-event", "emt-group-without-event"], dtype=str)
    new_results.ng = 2
    new_results.has_event_group_results = np.array([True, False], dtype=bool)
    new_results.well_initialized = np.zeros(2, dtype=bool)
    new_results.converged = np.zeros(2, dtype=bool)
    new_results.values = np.repeat(new_results.values, 2, axis=2)
    new_results.values[:, :, 1] = 0.0
    new_results.diff_values = np.zeros((new_results.nt, new_results.ndv, new_results.ng), dtype=float)

    circuit: MultiCircuit = MultiCircuit(name="emt-unsimulated-group")
    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=old_results, circuit=circuit)
    assert handler.create_plot_group(name="Plot 1") is True

    old_series_list = handler.series_by_var_uid[1]
    assert len(old_series_list) == 2
    assert handler.add_series_to_group(group_name="Plot 1", series_key=old_series_list[0].get_key()) is True
    assert handler.add_series_to_group(group_name="Plot 1", series_key=old_series_list[1].get_key()) is True

    handler.update_results(results=new_results)

    group: object = handler.plot_groups.get_group(name="Plot 1")
    assert group is not None
    group_entries: List[object] = group.get_series()
    assert len(group_entries) == 2
    assert isinstance(group_entries[0], DynamicPlotEntry) is False
    assert isinstance(group_entries[1], DynamicPlotEntry) is True
    assert group_entries[0].get_var().uid == 101
    assert group_entries[1].variable is not None
    assert group_entries[1].variable.uid == 1


def test_dynamic_plot_prunes_event_group_when_label_becomes_ambiguous() -> None:
    """
    Drop a plot entry when the rerun exposes multiple matching event groups.
    """
    ensure_qt_application()

    old_results: RmsResults = build_rms_results_with_groups([
        (make_device(name="DeviceA", idtag="dev-a"), [make_var(name="v_A", uid=1)]),
    ], group_names=["With event"])
    new_results: RmsResults = build_rms_results_with_groups([
        (make_device(name="DeviceA", idtag="dev-a"), [make_var(name="v_A", uid=101)]),
    ], group_names=["With event", "With event"])

    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=old_results)
    assert handler.create_plot_group(name="Plot 1") is True

    old_series_list = handler.series_by_var_uid[1]
    assert len(old_series_list) == 1
    assert handler.add_series_to_group(group_name="Plot 1", series_key=old_series_list[0].get_key()) is True

    handler.update_results(results=new_results)

    assert get_group_var_uids(handler=handler, group_name="Plot 1") == list()


def test_dynamic_plot_keeps_unaffected_emt_device_vars_after_model_change() -> None:
    """
    Keep unaffected EMT device variables when another device changes model.
    """
    ensure_qt_application()

    old_results: EmtResults = build_emt_results([
        (make_device(name="GeneratorA", idtag="gen-a"), [make_var(name="efd", uid=1), make_var(name="omega", uid=2)]),
        (make_device(name="LoadA", idtag="load-a"), [make_var(name="p", uid=3)]),
    ])
    new_results: EmtResults = build_emt_results([
        (make_device(name="GeneratorA", idtag="gen-a"), [make_var(name="eq1", uid=101)]),
        (make_device(name="LoadA", idtag="load-a"), [make_var(name="p", uid=102)]),
    ])

    handler: DynamicsResultsHandler = build_handler_with_group(results=old_results,
                                                               group_name="Plot 1",
                                                               variable_uids=[1, 3])
    handler.update_results(results=new_results)

    assert get_group_var_uids(handler=handler, group_name="Plot 1") == [102]


def test_asset_backed_dynamic_plot_entry_uses_device_idtag_binding() -> None:
    """
    Restore only the asset entry that matches the stable device idtag.
    """
    ensure_qt_application()

    old_results: RmsResults = build_rms_results([
        (make_device(name="DeviceA", idtag="dev-a-1"), [make_var(name="v_A", uid=1)]),
        (make_device(name="DeviceA", idtag="dev-a-2"), [make_var(name="v_A", uid=2)]),
    ])
    new_results: RmsResults = build_rms_results([
        (make_device(name="DeviceA", idtag="dev-a-1"), [make_var(name="v_A", uid=101)]),
        (make_device(name="DeviceA", idtag="dev-a-2"), [make_var(name="v_A", uid=102)]),
    ])

    circuit: MultiCircuit = MultiCircuit(name="binding")
    plot_asset: DynamicPlot = DynamicPlot(name="Plot 1", simulation_type=PlotSimulationType.RMS)
    circuit.add_dynamic_plot(obj=plot_asset)
    circuit.add_dynamic_plot_entry(obj=DynamicPlotEntry(
        variable=None,
        plot=plot_asset,
        group=None,
        device=None,
        simulation_type=PlotSimulationType.RMS,
        event_group_idtag="rms-group-1",
        event_group_name="Group 1",
        curve_device_type=DeviceType.NoDevice,
        device_idtag="dev-a-2",
        device_name_hint="DeviceA",
        variable_name="v_A",
        result_path_kind="values",
        enabled=True,
        runtime_series_key_payload="",
    ))

    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=old_results, circuit=circuit)
    handler.update_results(results=new_results)

    assert get_group_var_uids(handler=handler, group_name="Plot 1") == [102]


def test_unresolved_asset_entry_remains_persistent_in_circuit() -> None:
    """
    Keep unresolved persistent plot entries in the circuit assets.
    """
    ensure_qt_application()

    results: RmsResults = build_rms_results([
        (make_device(name="DeviceA", idtag="dev-a"), [make_var(name="v_A", uid=1)]),
    ])

    circuit: MultiCircuit = MultiCircuit(name="unresolved")
    plot_asset: DynamicPlot = DynamicPlot(name="Plot 1", simulation_type=PlotSimulationType.RMS)
    circuit.add_dynamic_plot(obj=plot_asset)
    unresolved_entry: DynamicPlotEntry = DynamicPlotEntry(
        variable=None,
        plot=plot_asset,
        group=None,
        device=None,
        simulation_type=PlotSimulationType.RMS,
        event_group_idtag="rms-group-1",
        event_group_name="Group 1",
        curve_device_type=DeviceType.NoDevice,
        device_idtag="missing-device",
        device_name_hint="Missing",
        variable_name="missing_var",
        result_path_kind="values",
        enabled=True,
        runtime_series_key_payload="",
    )
    circuit.add_dynamic_plot_entry(obj=unresolved_entry)

    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=results, circuit=circuit)

    assert len(circuit.dynamic_plot_entries) == 1
    assert circuit.dynamic_plot_entries[0] is unresolved_entry
    assert get_group_var_uids(handler=handler, group_name="Plot 1") == list()


def test_dynamic_plot_restores_duplicate_var_names_by_exact_key() -> None:
    """
    Preserve both duplicate variable names on the same device using exact series keys.
    """
    ensure_qt_application()

    old_results: RmsResults = build_rms_results([
        (make_device(name="DeviceA", idtag="dev-a"), [make_var(name="v_A", uid=1), make_var(name="v_A", uid=2)]),
    ])
    new_results: RmsResults = build_rms_results([
        (make_device(name="DeviceA", idtag="dev-a"), [make_var(name="v_A", uid=101), make_var(name="v_A", uid=102)]),
    ])

    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=old_results)
    assert handler.create_plot_group(name="Plot 1") is True
    assert handler.add_var_to_group(group_name="Plot 1", var_uid=1) is True
    assert handler.add_var_to_group(group_name="Plot 1", var_uid=2) is True

    handler.update_results(results=new_results)

    assert get_group_var_uids(handler=handler, group_name="Plot 1") == [101, 102]


def test_dynamic_results_handler_skips_unexported_rms_device_vars() -> None:
    """
    Ignore RMS device variables that are not exported in the runtime results arrays.
    """
    ensure_qt_application()

    device: FakeDynamicDevice = make_device(name="DeviceA", idtag="dev-a")
    results: RmsResults = build_rms_results_with_unexported_device_var(
        device=device,
        exported_var=make_var(name="omega", uid=1),
        unexported_var=make_var(name="domega", uid=2),
    )

    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=results)

    assert 1 in handler.series_by_var_uid
    assert 2 not in handler.series_by_var_uid
    assert handler.tree_data[device.device_type][device].get_variables()[0].name == "omega"
