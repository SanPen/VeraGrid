from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

import numpy as np
from PySide6 import QtCore

from VeraGrid.Gui.Main.SubClasses.Results.dynamics_results_handler import DynamicsResultsHandler
from VeraGridEngine.Simulations.EMT.emt_results import EmtResults
from VeraGridEngine.Simulations.Rms.rms_results import RmsResults
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import DeviceType


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
        variables=variables,
        uid2idx=uid2idx,
        vars_glob_name2uid=vars_glob_name2uid,
        devices_vars_info=devices_vars_info,
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
        variables=variables,
        diff_variables=list(),
        uid2idx_vars=uid2idx_vars,
        uid2idx_diff=uid2idx_diff,
        vars_glob_name2uid=vars_glob_name2uid,
        devices_vars_info=devices_vars_info,
    )

    if len(variables) > 0:
        results.values[:, :, 0] = np.arange(results.nt * results.nv, dtype=float).reshape(results.nt, results.nv)
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
    Do not restore a variable when the owning device name changes.
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

    assert get_group_var_uids(handler=handler, group_name="Plot 1") == list()


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
    Skip restoration when duplicate ``device.name`` and ``var.name`` pairs exist.
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

    assert get_group_var_uids(handler=handler, group_name="Plot 1") == list()


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
