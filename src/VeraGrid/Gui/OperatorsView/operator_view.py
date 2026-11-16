# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Interactive controller for the Operator View window."""

from __future__ import annotations

from typing import TYPE_CHECKING, List
from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import QAbstractItemView, QMainWindow, QWidget

import VeraGrid.Gui.gui_functions as gf
from VeraGrid.Gui.gui_functions import ComboModel
from VeraGrid.Gui.Icons.icon_associations import device_type_icons
from VeraGrid.Gui.OperatorsView.operator_schematic import OperatorSchematic, get_operator_focal_buses
from VeraGrid.Gui.OperatorsView.operator_view_ui import Ui_OperatorView
from VeraGrid.Gui.object_model import ObjectsModel
from VeraGrid.Session.session import SimulationSession
import VeraGridEngine.Devices as dev
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.enumerations import DeviceType

if TYPE_CHECKING:
    from VeraGrid.Gui.Main.VeraGridMain import VeraGridMainGUI


class OperatorView(QMainWindow):
    """Show searchable grid devices and the properties of one selection."""

    __slots__ = (
        'ui', '_circuit', '_devices_model', '_devices_proxy_model',
        '_selection_model', '_device_types', '_main_gui', '_session', '_schematic_widget',
    )

    def __init__(self,
                 main_gui: VeraGridMainGUI,
                 device_types: List[DeviceType],
                 parent: QWidget | None = None) -> None:
        """
        Build an Operator View bound to one circuit.
        :param main_gui: Main GUI providing the circuit, session and simulation actions.
        :param device_types: Device categories available from the type combo box.
        :param parent: Optional Qt owner of this window.
        :return: None.
        """
        QMainWindow.__init__(self, parent)
        self.ui: Ui_OperatorView = Ui_OperatorView()
        self.ui.setupUi(self)
        self._circuit: MultiCircuit = main_gui.circuit
        self._devices_model: ObjectsModel | None = None
        self._devices_proxy_model: QtCore.QSortFilterProxyModel | None = None
        self._selection_model: QtGui.QStandardItemModel | None = None
        self._device_types: list[DeviceType] = list(device_types)
        self._main_gui: VeraGridMainGUI = main_gui
        self._session: SimulationSession = main_gui.session
        self._schematic_widget: OperatorSchematic | None = None

        # The table is a read-only navigation surface; device editing remains in its editor windows.
        self.ui.devicesTableView.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.ui.devicesTableView.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.ui.selectionInformationTableView.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # ComboModel preserves DeviceType runtime data while translating only the displayed labels.
        device_icons: list[tuple[DeviceType, str]] = list()
        device_type: DeviceType
        for device_type in self._device_types:
            icon_path: str | None = device_type_icons.get(device_type.value, None)
            if icon_path is not None:
                device_icons.append((device_type, icon_path))
            else:
                device_icons.append((device_type, ""))
        device_types_model: ComboModel = ComboModel(icon_enum_values=device_icons, translate=self.tr)
        self.ui.deviceTypeComboBox.setModel(device_types_model)
        self._connect_main_gui_actions()
        self.refresh_simulation_results()

        # Device types own the contents of the main table, while text only reduces its visible rows.
        self.ui.deviceTypeComboBox.currentIndexChanged.connect(self._set_device_type)
        self.ui.deviceSearchLineEdit.textChanged.connect(self._filter_devices)
        self.ui.simulationResultsComboBox.currentIndexChanged.connect(self._show_selected_results)

        if self.ui.deviceTypeComboBox.count() > 0:
            self._set_device_type(combo_index=0)
        else:
            self._clear_device_models()

    def _connect_main_gui_actions(self) -> None:
        """Connect the Designer-owned toolbar actions to Main GUI simulations.

        :return: None.
        """
        self.ui.actionPower_flow.triggered.connect(self._main_gui.ui.actionPower_flow.trigger)
        self.ui.actionShort_Circuit.triggered.connect(self._main_gui.ui.actionShort_Circuit.trigger)
        self.ui.actionRun_Dynamic_RMS_Simulation.triggered.connect(
            self._main_gui.ui.actionRun_Dynamic_RMS_Simulation.trigger,
        )
        self.ui.actionOPF.triggered.connect(self._main_gui.ui.actionOPF.trigger)

    def get_session(self) -> SimulationSession:
        """Return the simulation session exposed by the Main GUI owner.

        :return: Main GUI session.
        """
        return self._session

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        """Mark the Main GUI toggle action checked when the window becomes visible.

        :param event: Qt visibility event.
        :return: None.
        """
        self._main_gui.set_operator_view_action_checked(is_checked=True)
        self.refresh_simulation_results()
        QMainWindow.showEvent(self, event)

    def hideEvent(self, event: QtGui.QHideEvent) -> None:
        """Mark the Main GUI toggle action unchecked when the window is hidden.

        :param event: Qt visibility event.
        :return: None.
        """
        self._main_gui.set_operator_view_action_checked(is_checked=False)
        QMainWindow.hideEvent(self, event)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Hide the reusable Operator View when its title-bar close button is used.

        :param event: Qt close event.
        :return: None.
        """
        event.ignore()
        self.hide()

    @QtCore.Slot(int)
    def _set_device_type(self, combo_index: int) -> None:
        """
        Replace the device table with the collection selected by the type combo box.

        :param combo_index: Current combo-box row supplied by Qt.
        :return: None.
        """
        selected_type: object = self.ui.deviceTypeComboBox.itemData(combo_index)
        if isinstance(selected_type, DeviceType):
            devices: list[ALL_DEV_TYPES] = list(self._circuit.get_elements_by_type(device_type=selected_type))
            if len(devices) > 0:
                self._devices_model = ObjectsModel(
                    objects=devices,
                    property_list=list(devices[0].property_list),
                    time_index=None,
                    parent=self.ui.devicesTableView,
                    editable=False,
                )
                self._devices_proxy_model = QtCore.QSortFilterProxyModel(self.ui.devicesTableView)
                self._devices_proxy_model.setSourceModel(self._devices_model)
                self._devices_proxy_model.setFilterCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
                self._devices_proxy_model.setFilterKeyColumn(-1)
                self.ui.devicesTableView.setModel(self._devices_proxy_model)
                self.ui.devicesTableView.selectionModel().currentChanged.connect(self._show_selection_information)
                self._filter_devices(text=self.ui.deviceSearchLineEdit.text())
            else:
                self._clear_device_models()
        else:
            self._clear_device_models()

    @QtCore.Slot(str)
    def _filter_devices(self, text: str) -> None:
        """Filter the visible device rows by plain, case-insensitive text.

        :param text: Search text provided by the right-panel line edit.
        :return: None.
        """
        if self._devices_proxy_model is not None:
            self._devices_proxy_model.setFilterFixedString(text)
        else:
            pass

    @QtCore.Slot(QtCore.QModelIndex, QtCore.QModelIndex)
    def _show_selection_information(self,
                                    current_index: QtCore.QModelIndex,
                                    previous_index: QtCore.QModelIndex) -> None:
        """Display the selected device's properties in the lower-left table.

        :param current_index: Current row in the filtered device table.
        :param previous_index: Previously selected row, unused after the change.
        :return: None.
        """
        _ = previous_index
        if self._devices_model is not None and self._devices_proxy_model is not None and current_index.isValid():
            source_index: QtCore.QModelIndex = self._devices_proxy_model.mapToSource(current_index)
            source_row: int = source_index.row()
            if 0 <= source_row < len(self._devices_model.objects):
                selected_device: ALL_DEV_TYPES = self._devices_model.objects[source_row]
                self._show_vicinity_diagram(device=selected_device)
            else:
                self._clear_selection_information()
                self._clear_schematic_diagram()
        else:
            self._clear_selection_information()
            self._clear_schematic_diagram()

    def _show_vicinity_diagram(self, device: ALL_DEV_TYPES) -> None:
        """Show the reduced level-one operator context for one selected device.

        :param device: Device selected from the right-side device table.
        :return: None.
        """
        focal_buses = get_operator_focal_buses(circuit=self._circuit, device=device)
        if len(focal_buses) > 0:
            self._clear_schematic_diagram()
            self.ui.operatorDiagramLabel.setText(self.tr("Operator diagram: {0}").format(device.name))
            diagram_widget: OperatorSchematic = OperatorSchematic(
                circuit=self._circuit,
                focal_buses=focal_buses,
                gui=self._main_gui,
            )
            diagram_widget.bus_navigation_requested.connect(self._show_operator_bus_context)
            self.ui.operatorDiagramContentLayout.addWidget(diagram_widget)
            self._schematic_widget = diagram_widget
            self._show_selected_results(self.ui.simulationResultsComboBox.currentIndex())
        else:
            self.ui.operatorDiagramLabel.setText(self.tr("Operator diagrams"))
            self._clear_schematic_diagram()

    @QtCore.Slot(object)
    def _show_operator_bus_context(self, bus: object) -> None:
        """Center the existing diagram on the Ctrl-clicked context bus.

        :param bus: Adjacent bus emitted by the reduced schematic.
        :return: None.
        """
        if isinstance(bus, dev.Bus):
            self._show_vicinity_diagram(device=bus)
        else:
            pass

    def refresh_simulation_results(self) -> None:
        """Populate the Designer-owned combo with completed session simulations.

        :return: None.
        """
        current_type: object = self.ui.simulationResultsComboBox.currentData()
        self.ui.simulationResultsComboBox.blockSignals(True)
        result_items: list[tuple[str, object, str]] = list()
        simulation_icons: dict = gf.get_simulation_tree_icons()
        if isinstance(self._session, SimulationSession):
            driver: object
            for driver in self._session.get_available_drivers():
                if driver.results is not None:
                    icon_path: str | None = simulation_icons.get(driver.tpe, None)
                    if icon_path is not None:
                        result_items.append((str(driver.tpe.value), driver.tpe, icon_path))
                    else:
                        result_items.append((str(driver.tpe.value), driver.tpe, ""))
                else:
                    pass
        else:
            pass
        result_model: ComboModel = ComboModel(
            text_items=[(self.tr("No results"), None)],
            icon_text_items=result_items,
            translate=self.tr,
        )
        self.ui.simulationResultsComboBox.setModel(result_model)
        result_index: int = self.ui.simulationResultsComboBox.findData(current_type)
        if result_index >= 0:
            self.ui.simulationResultsComboBox.setCurrentIndex(result_index)
        else:
            self.ui.simulationResultsComboBox.setCurrentIndex(0)
        self.ui.simulationResultsComboBox.blockSignals(False)
        self._show_selected_results(self.ui.simulationResultsComboBox.currentIndex())

    @QtCore.Slot(int)
    def _show_selected_results(self, combo_index: int) -> None:
        """Apply the selected completed study to the active operator canvas.

        :param combo_index: Current result-combo row supplied by Qt.
        :return: None.
        """
        simulation_type: object = self.ui.simulationResultsComboBox.itemData(combo_index)
        if self._schematic_widget is not None:
            if isinstance(self._session, SimulationSession):
                results: object | None = self._session.get_results(driver_type=simulation_type)
                if results is not None:
                    self._schematic_widget.set_results(results=results)
                    self._set_diagram_summary(results=results)
                else:
                    self._schematic_widget.clear_results()
                    self._set_diagram_summary(results=None)
            else:
                self._schematic_widget.clear_results()
                self._set_diagram_summary(results=None)
        else:
            pass

    def _set_diagram_summary(self, results: object | None) -> None:
        """Show flow and voltage values for every element in the active diagram.

        :param results: Selected completed simulation result object, if any.
        :return: None.
        """
        if self._schematic_widget is not None:
            rows: list[list[str]] = self._schematic_widget.get_summary_rows(results=results)
            model: QtGui.QStandardItemModel = QtGui.QStandardItemModel(self.ui.selectionInformationTableView)
            model.setHorizontalHeaderLabels([
                self.tr("Element"), self.tr("Name"), self.tr("Voltage"), self.tr("Angle"), self.tr("P"),
                self.tr("Q"), self.tr("Loading"),
            ])
            row: list[str]
            for row in rows:
                model.appendRow([QtGui.QStandardItem(value) for value in row])
            self._selection_model = model
            self.ui.selectionInformationTableView.setModel(model)
        else:
            self._clear_selection_information()

    def _clear_schematic_diagram(self) -> None:
        """Dispose the current schematic before replacing it or closing the window.

        :return: None.
        """
        schematic_widget: OperatorSchematic | None = self._schematic_widget
        self._schematic_widget = None
        if schematic_widget is not None:
            # Match the Main GUI disposal sequence to avoid retaining scene-owned graphics wrappers.
            schematic_widget.prepare_to_delete()
            self.ui.operatorDiagramContentLayout.removeWidget(schematic_widget)
            schematic_widget.setParent(None)
            schematic_widget.deleteLater()
        else:
            pass

    def _clear_device_models(self) -> None:
        """Clear dependent tables when the selected type has no usable devices.

        :return: None.
        """
        self._devices_model = None
        self._devices_proxy_model = None
        self.ui.devicesTableView.setModel(None)
        self._clear_selection_information()
        self._clear_schematic_diagram()

    def _clear_selection_information(self) -> None:
        """Clear stale properties when no device is selected.

        :return: None.
        """
        self._selection_model = None
        self.ui.selectionInformationTableView.setModel(None)
