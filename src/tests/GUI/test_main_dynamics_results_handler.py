from typing import Dict, List, Tuple

from PySide6 import QtCore, QtGui

from VeraGrid.Gui.Main.SubClasses.Results.dynamics_results_handler import (
    DynamicResultSeriesKey,
    DynamicPlotCandidate,
    DynamicsDeviceTreeModel,
    DynamicsPlotGroup,
    DynamicsPlotGroups,
    DynamicsPlotsTreeModel,
    build_dynamics_tree_model,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import DeviceType, PlotSimulationType


class NamedDevice:
    """
    Minimal device-like object used to label dynamics tree rows.
    """

    __slots__ = ("_name",)

    def __init__(self, name: str) -> None:
        """
        Build the named device.

        :param name: Name shown by the dynamics tree.
        :return: Nothing.
        """
        self._name: str = name

    def __str__(self) -> str:
        """
        Get the user-facing device name.

        :return: Device name.
        """
        return self._name


class FakeDropHandler:
    """
    Minimal handler used to test ``DynamicsPlotsTreeModel`` drop routing.
    """

    __slots__ = ("_group_name_role", "_drag_mime_type", "_group_name", "_accepted_var_uid", "_calls")

    def __init__(self, group_name_role: int, drag_mime_type: str, group_name: str, accepted_var_uid: int) -> None:
        """
        Build the fake drop handler.

        :param group_name_role: Qt role that stores plot-group names.
        :param drag_mime_type: Mime type accepted by the plots tree.
        :param group_name: Group name returned for drop targets.
        :param accepted_var_uid: Variable UID accepted by ``add_var_to_group``.
        :return: Nothing.
        """
        self._group_name_role: int = group_name_role
        self._drag_mime_type: str = drag_mime_type
        self._group_name: str = group_name
        self._accepted_var_uid: int = accepted_var_uid
        self._calls: List[Tuple[str, int]] = list()

    def get_group_name_role(self) -> int:
        """
        Get the Qt role used by plot-group items.

        :return: Group-name role.
        """
        return self._group_name_role

    def get_drag_mime_type(self) -> str:
        """
        Get the dynamics drag mime type.

        :return: Drag mime type.
        """
        return self._drag_mime_type

    def get_group_name_from_drop_index(self, index: QtCore.QModelIndex) -> str | None:
        """
        Resolve a group name for a drop index.

        :param index: Drop target index.
        :return: Configured group name or ``None``.
        """
        if index.isValid():
            return self._group_name
        else:
            return None

    def add_var_to_group(self, group_name: str, var_uid: int) -> bool:
        """
        Record accepted drop calls.

        :param group_name: Target plot group.
        :param var_uid: Dropped variable UID.
        :return: ``True`` when the call matches the configured target.
        """
        accepted: bool = group_name == self._group_name and var_uid == self._accepted_var_uid
        if accepted:
            self._calls.append((group_name, var_uid))
            return True
        else:
            return False

    def add_series_to_group(self, group_name: str, series_key: DynamicResultSeriesKey) -> bool:
        """
        Compatibility shim for current drop handler API.

        :param group_name: Target plot group.
        :param series_key: Dropped series key.
        :return: ``True`` when accepted.
        """
        return self.add_var_to_group(group_name=group_name, var_uid=series_key.get_component_index())

    def get_candidate_from_payload(self, payload: str) -> DynamicPlotCandidate | None:
        """
        Parse one drop payload into a candidate object.

        :param payload: Serialized candidate payload.
        :return: Parsed candidate or ``None``.
        """
        if payload == "":
            return None
        else:
            return DynamicPlotCandidate(
                simulation_type=PlotSimulationType.RMS,
                event_group_idtag="group-id",
                event_group_name="Group 1",
                device_type=DeviceType.GeneratorDevice,
                device_idtag="device-id",
                device_label="Generator 1",
                bus_label="",
                variable_name="omega",
                result_path_kind="values",
                variable_custom_name="Generator 1 - omega",
                var=Var(name="omega", uid=self._accepted_var_uid),
            )

    def add_candidate_to_group(self, group_name: str, candidate: DynamicPlotCandidate) -> bool:
        """
        Compatibility shim for current candidate-drop path.

        :param group_name: Target plot group.
        :param candidate: Candidate dropped into the group.
        :return: ``True`` when accepted.
        """
        return self.add_var_to_group(group_name=group_name, var_uid=candidate.get_var().uid)

    def get_calls(self) -> List[Tuple[str, int]]:
        """
        Get recorded accepted drop calls.

        :return: Accepted calls.
        """
        return list(self._calls)


def test_dynamics_plot_group_rejects_duplicate_variables_by_uid() -> None:
    """
    Check that plot groups treat variable UID as the identity key.

    :return: Nothing.
    """
    group: DynamicsPlotGroup = DynamicsPlotGroup(name="Plot A")
    first_var: Var = Var(name="x", uid=10)
    duplicate_uid_var: Var = Var(name="x-copy", uid=10)

    assert group.add_var(variable=first_var) is True
    assert group.add_var(variable=duplicate_uid_var) is False
    assert group.contains_var(variable=duplicate_uid_var) is True
    assert group.remove_var(variable=duplicate_uid_var) is True
    assert group.get_vars() == list()


def test_dynamics_plot_groups_create_rename_and_delete_groups() -> None:
    """
    Check plot-group collection CRUD rules used by the dynamic-results GUI.

    :return: Nothing.
    """
    groups: DynamicsPlotGroups = DynamicsPlotGroups()

    assert groups.create_group(name="  Plot A  ") is True
    assert groups.create_group(name="Plot A") is False
    assert groups.create_group(name="") is False
    assert groups.create_group(name="Plot B") is True
    assert groups.rename_group(old_name="Plot A", new_name="Plot B") is False
    assert groups.rename_group(old_name="Plot A", new_name="Plot C") is True
    assert groups.get_group(name="Plot A") is None
    assert groups.get_group(name="Plot C") is not None
    assert groups.delete_group(name="Plot C") is True
    assert groups.delete_group(name="Plot C") is False


def test_dynamics_tree_model_exports_only_variable_leaf_mime_data(qt_app: object) -> None:
    """
    Check that the dynamics source tree marks only variable leaves as draggable.

    :param qt_app: Shared Qt application fixture.
    :return: Nothing.
    """
    del qt_app

    var_role: int = int(QtCore.Qt.ItemDataRole.UserRole) + 300
    mime_type: str = "application/x-veragrid-test-dynamics-var"
    variable: Var = Var(name="omega", uid=500)
    variables: List[Var] = list()
    variables.append(variable)

    device: NamedDevice = NamedDevice(name="Generator 1")
    devices_data: Dict[NamedDevice, List[Var]] = dict()
    devices_data[device] = variables

    tree_data: Dict[DeviceType, Dict[NamedDevice, List[Var]]] = dict()
    tree_data[DeviceType.GeneratorDevice] = devices_data
    series_by_var_uid: Dict[int, List[DynamicPlotCandidate]] = dict()
    series_by_var_uid[variable.uid] = list([
        DynamicPlotCandidate(
            simulation_type=PlotSimulationType.RMS,
            event_group_idtag="group-id",
            event_group_name="Group 1",
            device_type=DeviceType.GeneratorDevice,
            device_idtag="device-id",
            device_label="Generator 1",
            bus_label="",
            variable_name=variable.name,
            result_path_kind="values",
            variable_custom_name="Generator 1 - omega",
            var=variable,
        )
    ])

    model: DynamicsDeviceTreeModel = build_dynamics_tree_model(
        tree_data=tree_data,
        var_role=var_role,
        mime_type=mime_type,
        series_by_var_uid=series_by_var_uid,
        has_multiple_sources=False,
    )
    device_type_item: QtGui.QStandardItem = model.item(0, 0)
    device_item: QtGui.QStandardItem = device_type_item.child(0, 0)
    variable_item: QtGui.QStandardItem = device_item.child(0, 0)

    device_flags: QtCore.Qt.ItemFlag = model.flags(device_item.index())
    variable_flags: QtCore.Qt.ItemFlag = model.flags(variable_item.index())
    mime_data: QtCore.QMimeData = model.mimeData(indexes=[variable_item.index()])
    device_mime_data: QtCore.QMimeData = model.mimeData(indexes=[device_item.index()])

    assert model.horizontalHeaderItem(0).text() == "Dynamics results"
    assert device_type_item.text() == str(DeviceType.GeneratorDevice.value)
    assert device_item.text() == "Generator 1"
    assert variable_item.text() == "omega"
    assert bool(device_flags & QtCore.Qt.ItemFlag.ItemIsDragEnabled) is False
    assert bool(variable_flags & QtCore.Qt.ItemFlag.ItemIsDragEnabled) is True
    assert mime_data.hasFormat(mime_type) is True
    assert bytes(mime_data.data(mime_type)).decode("utf-8") == series_by_var_uid[variable.uid][0].to_payload()
    assert device_mime_data.hasFormat(mime_type) is False


def test_dynamics_plots_tree_accepts_valid_variable_drop(qt_app: object) -> None:
    """
    Check that the dynamics plots tree routes valid drops to the handler.

    :param qt_app: Shared Qt application fixture.
    :return: Nothing.
    """
    del qt_app

    group_name_role: int = int(QtCore.Qt.ItemDataRole.UserRole) + 301
    mime_type: str = "application/x-veragrid-test-dynamics-var"
    variable_uid: int = 777
    handler: FakeDropHandler = FakeDropHandler(
        group_name_role=group_name_role,
        drag_mime_type=mime_type,
        group_name="Plot 1",
        accepted_var_uid=variable_uid,
    )
    model: DynamicsPlotsTreeModel = DynamicsPlotsTreeModel(handler=handler)
    group_item: QtGui.QStandardItem = QtGui.QStandardItem("Plot 1")
    child_item: QtGui.QStandardItem = QtGui.QStandardItem("omega")
    group_item.setData("Plot 1", group_name_role)
    model.invisibleRootItem().appendRow(group_item)
    group_item.appendRow(child_item)

    candidate: DynamicPlotCandidate = DynamicPlotCandidate(
        simulation_type=PlotSimulationType.RMS,
        event_group_idtag="group-id",
        event_group_name="Group 1",
        device_type=DeviceType.GeneratorDevice,
        device_idtag="device-id",
        device_label="Generator 1",
        bus_label="",
        variable_name="omega",
        result_path_kind="values",
        variable_custom_name="Generator 1 - omega",
        var=Var(name="omega", uid=variable_uid),
    )
    mime_data: QtCore.QMimeData = QtCore.QMimeData()
    mime_data.setData(mime_type, QtCore.QByteArray(candidate.to_payload().encode("utf-8")))

    group_flags: QtCore.Qt.ItemFlag = model.flags(group_item.index())
    child_flags: QtCore.Qt.ItemFlag = model.flags(child_item.index())
    accepted: bool = model.dropMimeData(
        data=mime_data,
        action=QtCore.Qt.DropAction.CopyAction,
        row=-1,
        column=-1,
        parent=group_item.index(),
    )

    assert bool(group_flags & QtCore.Qt.ItemFlag.ItemIsDropEnabled) is True
    assert bool(child_flags & QtCore.Qt.ItemFlag.ItemIsDropEnabled) is False
    assert accepted is True
    assert handler.get_calls() == [("Plot 1", variable_uid)]
