# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Regression coverage for the Operator View device navigation workflow."""

from PySide6 import QtCore, QtTest, QtWidgets
from PySide6.QtGui import QAction
import shiboken6

import VeraGridEngine.Devices as dev
from VeraGrid.Gui.OperatorsView.operator_view import OperatorView
from VeraGrid.Gui.OperatorsView.operator_schematic import (
    OperatorSchematic,
    get_operator_focal_buses,
    make_operator_diagram,
)
from VeraGrid.Gui.Main.SubClasses.base_gui import BaseMainGui
from VeraGrid.Gui.Main.SubClasses.window_manager import WindowManager
from VeraGridEngine.enumerations import DeviceType


class OperatorViewUiStub:
    """Provide the Main GUI actions consumed by the Operator View test.

    :return: None.
    """

    __slots__ = (
        'actionPower_flow', 'actionShort_Circuit',
        'actionRun_Dynamic_RMS_Simulation', 'actionOPF',
        'power_flow_count', 'short_circuit_count', 'rms_count', 'opf_count',
    )

    def __init__(self) -> None:
        """Create the snapshot simulation actions used by the test owner.

        :return: None.
        """
        self.actionPower_flow: QAction = QAction()
        self.actionShort_Circuit: QAction = QAction()
        self.actionRun_Dynamic_RMS_Simulation: QAction = QAction()
        self.actionOPF: QAction = QAction()
        self.power_flow_count: int = 0
        self.short_circuit_count: int = 0
        self.rms_count: int = 0
        self.opf_count: int = 0
        self.actionPower_flow.triggered.connect(self.record_power_flow)
        self.actionShort_Circuit.triggered.connect(self.record_short_circuit)
        self.actionRun_Dynamic_RMS_Simulation.triggered.connect(self.record_rms)
        self.actionOPF.triggered.connect(self.record_opf)

    @QtCore.Slot()
    def record_power_flow(self) -> None:
        """Record one forwarded power-flow action.

        :return: None.
        """
        self.power_flow_count += 1

    @QtCore.Slot()
    def record_short_circuit(self) -> None:
        """Record one forwarded short-circuit action.

        :return: None.
        """
        self.short_circuit_count += 1

    @QtCore.Slot()
    def record_rms(self) -> None:
        """Record one forwarded RMS action.

        :return: None.
        """
        self.rms_count += 1

    @QtCore.Slot()
    def record_opf(self) -> None:
        """Record one forwarded OPF action.

        :return: None.
        """
        self.opf_count += 1


class OperatorViewMainGuiStub:
    """Supply the circuit, session and actions required from the Main GUI.

    :return: None.
    """

    __slots__ = ('circuit', 'session', 'ui', 'operator_view_visible')

    def __init__(self, circuit: dev.MultiCircuit) -> None:
        """Build a Main GUI test double for one circuit.

        :param circuit: Circuit exposed through the Main GUI contract.
        :return: None.
        """
        self.circuit: dev.MultiCircuit = circuit
        self.session: object = object()
        self.ui: OperatorViewUiStub = OperatorViewUiStub()
        self.operator_view_visible: bool = False

    def set_operator_view_action_checked(self, is_checked: bool) -> None:
        """Record the view visibility reported by the managed window.

        :param is_checked: Whether the view is visible.
        :return: None.
        """
        self.operator_view_visible = is_checked


class OperatorViewLockUiStub:
    """Expose the widgets touched by the Main GUI lock routine.

    :return: None.
    """

    __slots__ = ('mainTabWidget', 'menuBar', 'toolBar')

    def __init__(self, parent: QtWidgets.QMainWindow) -> None:
        """Create widgets required by ``BaseMainGui.LOCK_UI``.

        :param parent: Parent main window for the lock-state widgets.
        :return: None.
        """
        self.mainTabWidget: QtWidgets.QTabWidget = QtWidgets.QTabWidget(parent)
        self.menuBar: QtWidgets.QMenuBar = QtWidgets.QMenuBar(parent)
        self.toolBar: QtWidgets.QToolBar = QtWidgets.QToolBar(parent)


class OperatorViewLockOwner:
    """Supply the lock routine with the Main GUI state it consumes.

    :return: None.
    """

    __slots__ = ('ui', 'window_manager')

    def __init__(self, main_window: QtWidgets.QMainWindow, window_manager: WindowManager) -> None:
        """Build a narrow Main GUI test double for UI locking.

        :param main_window: Parent window for the lock-state widgets.
        :param window_manager: Managed-window registry used by the lock routine.
        :return: None.
        """
        self.ui: OperatorViewLockUiStub = OperatorViewLockUiStub(parent=main_window)
        self.window_manager: WindowManager = window_manager


def test_operator_view_filters_devices_and_shows_selected_properties(
        qt_app: QtWidgets.QApplication) -> None:
    """Show only matching devices and expose the selected device properties.

    :param qt_app: Shared Qt application.
    :return: None.
    """
    application: QtWidgets.QApplication = qt_app
    circuit: dev.MultiCircuit = dev.MultiCircuit()
    circuit.add_bus(obj=dev.Bus(name='North bus', Vnom=110.0))
    circuit.add_bus(obj=dev.Bus(name='South bus', Vnom=110.0))
    device_types: list[DeviceType] = [DeviceType.GeneratorDevice, DeviceType.BusDevice]
    main_gui: OperatorViewMainGuiStub = OperatorViewMainGuiStub(circuit=circuit)
    window: OperatorView = OperatorView(device_types=device_types, main_gui=main_gui)
    bus_index: int = window.ui.deviceTypeComboBox.findData(DeviceType.BusDevice)

    assert window.ui.deviceTypeComboBox.count() == len(device_types)
    assert window.get_session() is main_gui.session
    assert window.ui.toolBar.actions()[-4:] == [
        window.ui.actionPower_flow,
        window.ui.actionShort_Circuit,
        window.ui.actionRun_Dynamic_RMS_Simulation,
        window.ui.actionOPF,
    ]
    assert window.ui.simulationResultsComboBox.count() == 1
    window.ui.actionPower_flow.trigger()
    window.ui.actionShort_Circuit.trigger()
    window.ui.actionRun_Dynamic_RMS_Simulation.trigger()
    window.ui.actionOPF.trigger()
    assert main_gui.ui.power_flow_count == 1
    assert main_gui.ui.short_circuit_count == 1
    assert main_gui.ui.rms_count == 1
    assert main_gui.ui.opf_count == 1
    assert bus_index >= 0
    window.ui.deviceTypeComboBox.setCurrentIndex(bus_index)
    window.ui.deviceSearchLineEdit.setText('south')
    application.processEvents()
    assert window.ui.devicesTableView.model().rowCount() == 1

    device_index: QtCore.QModelIndex = window.ui.devicesTableView.model().index(0, 0)
    window.ui.devicesTableView.setCurrentIndex(device_index)
    application.processEvents()

    selection_model: QtCore.QAbstractItemModel | None = window.ui.selectionInformationTableView.model()
    assert selection_model is not None
    assert selection_model.rowCount() > 0
    first_schematic: object = window._schematic_widget
    assert first_schematic is not None
    assert window._schematic_widget.parent() is window.ui.operatorDiagramFrame
    assert window.ui.operatorDiagramLabel.text() == 'Operator diagram: South bus'

    window.ui.deviceSearchLineEdit.setText('north')
    application.processEvents()
    north_index: QtCore.QModelIndex = window.ui.devicesTableView.model().index(0, 0)
    window.ui.devicesTableView.setCurrentIndex(north_index)
    application.processEvents()
    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
    application.processEvents()

    assert window._schematic_widget is not None
    assert window._schematic_widget is not first_schematic
    assert not shiboken6.isValid(first_schematic)


def test_operator_view_is_reused_then_pruned_after_qt_destruction(
        qt_app: QtWidgets.QApplication) -> None:
    """Retain one view by key and remove its pointer only after Qt destruction.

    :param qt_app: Shared Qt application.
    :return: None.
    """
    application: QtWidgets.QApplication = qt_app
    main_window: QtWidgets.QMainWindow = QtWidgets.QMainWindow()
    window_manager: WindowManager = WindowManager(main_window=main_window)
    circuit: dev.MultiCircuit = dev.MultiCircuit()
    device_types: list[DeviceType] = [DeviceType.BusDevice]
    main_gui: OperatorViewMainGuiStub = OperatorViewMainGuiStub(circuit=circuit)
    first_window: OperatorView = OperatorView(
        device_types=device_types,
        main_gui=main_gui,
        parent=main_window,
    )

    shown_window: QtWidgets.QMainWindow | QtWidgets.QDialog = window_manager.show(
        win=first_window,
        key='operator_view',
        delete_on_close=True,
    )
    reused_window: QtWidgets.QMainWindow | QtWidgets.QDialog = window_manager.show(
        win=first_window,
        key='operator_view',
        delete_on_close=True,
    )

    assert shown_window is first_window
    assert reused_window is first_window
    assert window_manager.get(key='operator_view') is first_window
    assert main_gui.operator_view_visible
    lock_owner: OperatorViewLockOwner = OperatorViewLockOwner(
        main_window=main_window,
        window_manager=window_manager,
    )
    BaseMainGui.LOCK_UI(lock_owner, True)
    assert not first_window.isEnabled()
    BaseMainGui.LOCK_UI(lock_owner, False)
    assert first_window.isEnabled()
    assert not first_window.close()
    application.processEvents()
    assert window_manager.get(key='operator_view') is first_window
    assert not first_window.isVisible()
    assert not main_gui.operator_view_visible


def test_operator_schematic_stops_at_context_nodes_and_navigates(
        qt_app: QtWidgets.QApplication) -> None:
    """Keep only direct context and emit navigation from a context node.

    :param qt_app: Shared Qt application.
    :return: None.
    """
    _ = qt_app
    circuit: dev.MultiCircuit = dev.MultiCircuit()
    north_bus: dev.Bus = circuit.add_bus(dev.Bus(name='North', Vnom=110.0))
    central_bus: dev.Bus = circuit.add_bus(dev.Bus(name='Central', Vnom=110.0))
    south_bus: dev.Bus = circuit.add_bus(dev.Bus(name='South', Vnom=110.0))
    circuit.add_load(bus=central_bus, api_obj=dev.Load(name='Central load', P=10.0, Q=2.0))
    circuit.add_line(dev.Line(name='North-Central', bus_from=north_bus, bus_to=central_bus))
    circuit.add_line(dev.Line(name='Central-South', bus_from=central_bus, bus_to=south_bus))
    focal_buses: list[dev.Bus] = get_operator_focal_buses(circuit=circuit, device=central_bus)
    diagram = make_operator_diagram(circuit=circuit, focal_buses=focal_buses)
    schematic: OperatorSchematic = OperatorSchematic(circuit=circuit, focal_buses=focal_buses)
    navigated_buses: list[dev.Bus] = list()
    schematic.bus_navigation_requested.connect(navigated_buses.append)

    assert diagram is not None
    assert diagram.query_point(device=central_bus) is not None
    assert diagram.query_point(device=north_bus) is not None
    assert diagram.query_point(device=south_bus) is not None
    context_nodes: list[QtWidgets.QGraphicsEllipseItem] = [
        item for item in schematic.scene().items()
        if (isinstance(item, QtWidgets.QGraphicsEllipseItem)
            and item.parentItem() is None
            and isinstance(item.data(0), dev.Bus))
    ]
    assert len(context_nodes) == 2
    assert len(schematic._bus_graphics[central_bus]._child_graphics) == 1
    north_graphic = schematic._node_graphics[north_bus]
    branch_graphic = schematic._branch_graphics[circuit.lines[0]]
    initial_endpoint_x: float = branch_graphic.pos1.x()
    initial_other_endpoint_x: float = branch_graphic.pos2.x()
    north_graphic.setPos(north_graphic.pos() + QtCore.QPointF(100.0, 0.0))
    qt_app.processEvents()
    assert (branch_graphic.pos1.x() != initial_endpoint_x
            or branch_graphic.pos2.x() != initial_other_endpoint_x)

    schematic.show()
    qt_app.processEvents()
    north_node: QtWidgets.QGraphicsEllipseItem = next(
        item for item in context_nodes if item.data(0) is north_bus
    )
    node_position = schematic.mapFromScene(north_node.sceneBoundingRect().center())
    QtTest.QTest.mouseClick(
        schematic.viewport(),
        QtCore.Qt.MouseButton.LeftButton,
        QtCore.Qt.KeyboardModifier.ControlModifier,
        node_position,
    )
    assert navigated_buses == [north_bus]
    schematic.prepare_to_delete()
