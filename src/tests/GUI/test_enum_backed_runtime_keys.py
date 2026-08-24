from __future__ import annotations

from PySide6 import QtCore, QtGui

import VeraGrid.Gui.gui_functions as gf
from VeraGrid.Gui.Main.SubClasses.io import get_session_tree_icon_map
from VeraGrid.Session.session import SimulationSession
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Simulations.driver_template import DriverTemplate
from VeraGridEngine.Simulations.results_template import ResultsTemplate
from VeraGridEngine.enumerations import DeviceType, ResultTypes, SimulationTypes, StudyResultsType


class RuntimeKeysDriver(DriverTemplate):
    """
    Minimal driver used to verify typed session lookup.
    """

    __slots__ = tuple()

    name = "Runtime keys driver"
    tpe = SimulationTypes.PowerFlow_run

    def __init__(self, grid: MultiCircuit) -> None:
        """
        Initialize the test driver.

        :param grid: Test circuit.
        :return: None.
        """
        DriverTemplate.__init__(self, grid=grid)

    def run(self) -> None:
        """
        Run no simulation because only session lookup is under test.

        :return: None.
        """
        return None


def test_multicircuit_runtime_device_keys_are_enums() -> None:
    """
    Verify runtime device metadata is keyed by DeviceType instead of display strings.

    :return: None.
    """
    circuit: MultiCircuit = MultiCircuit()

    assert DeviceType.BusDevice in circuit.device_type_name_dict
    assert DeviceType.BusDevice in circuit.device_associations
    assert DeviceType.BusDevice in circuit.profile_magnitudes
    assert DeviceType.BusDevice.value not in circuit.device_type_name_dict


def test_results_template_runtime_result_keys_are_enums() -> None:
    """
    Verify result metadata can be consumed without display strings.

    :return: None.
    """
    results: ResultsTemplate = ResultsTemplate(
        name="runtime result keys",
        available_results={ResultTypes.BusResults: [ResultTypes.BusVoltageModule]},
        time_array=None,
        clustering_results=None,
        study_results_type=StudyResultsType.PowerFlow,
    )

    results_tree: object = results.get_results_type_tree()
    results_dict: dict[ResultTypes, ResultTypes] = results.get_results_type_dict()

    assert results_tree == {ResultTypes.BusResults: [ResultTypes.BusVoltageModule]}
    assert results_dict[ResultTypes.BusVoltageModule] == ResultTypes.BusVoltageModule
    assert ResultTypes.BusVoltageModule.value not in results_dict


def test_session_keeps_typed_driver_lookup_and_legacy_name_lookup() -> None:
    """
    Verify typed session lookup works while legacy name lookup remains available.

    :return: None.
    """
    session: SimulationSession = SimulationSession()
    driver: RuntimeKeysDriver = RuntimeKeysDriver(grid=MultiCircuit())
    session.drivers[driver.tpe] = driver

    assert session.get_driver(driver_type=SimulationTypes.PowerFlow_run) is driver
    assert session.get_driver_by_name(study_name=SimulationTypes.PowerFlow_run.value) is driver


def test_tree_items_can_translate_labels_without_losing_enum_payloads() -> None:
    """
    Verify tree labels are independent from runtime enum payloads.

    :return: None.
    """
    device_item: QtGui.QStandardItem = QtGui.QStandardItem("translated bus label")
    result_item: QtGui.QStandardItem = QtGui.QStandardItem("translated voltage label")
    study_item: QtGui.QStandardItem = QtGui.QStandardItem("translated power-flow label")

    device_item.setData(DeviceType.BusDevice, QtCore.Qt.ItemDataRole.UserRole)
    result_item.setData(ResultTypes.BusVoltageModule, QtCore.Qt.ItemDataRole.UserRole)
    study_item.setData(SimulationTypes.PowerFlow_run, QtCore.Qt.ItemDataRole.UserRole)

    assert device_item.text() != DeviceType.BusDevice.value
    assert result_item.text() != ResultTypes.BusVoltageModule.value
    assert study_item.text() != SimulationTypes.PowerFlow_run.value
    assert device_item.data(QtCore.Qt.ItemDataRole.UserRole) is DeviceType.BusDevice
    assert result_item.data(QtCore.Qt.ItemDataRole.UserRole) is ResultTypes.BusVoltageModule
    assert study_item.data(QtCore.Qt.ItemDataRole.UserRole) is SimulationTypes.PowerFlow_run


def test_simulation_tree_icons_support_enum_keys_for_translated_result_tree() -> None:
    """
    Verify live results tree icon lookup does not require display strings.

    :return: None.
    """
    icons: dict[SimulationTypes, str] = gf.get_simulation_tree_icons()

    assert icons.get(SimulationTypes.PowerFlow_run, None) == ':/Icons/icons/pf'
    assert SimulationTypes.PowerFlow_run.value not in icons


def test_persisted_session_tree_icon_map_converts_string_study_names() -> None:
    """
    Verify disk session strings are converted at the GUI boundary for icon lookup.

    :return: None.
    """
    session_data_dict: dict[str, dict[str, list[str]]] = {
        "Session": {
            SimulationTypes.PowerFlow_run.value: ["Bus voltage"],
            "unknown study": ["ignored"],
        }
    }

    icon_map: dict[str, str] = get_session_tree_icon_map(session_data_dict=session_data_dict)

    assert icon_map[SimulationTypes.PowerFlow_run.value] == ':/Icons/icons/pf'
    assert "unknown study" not in icon_map
