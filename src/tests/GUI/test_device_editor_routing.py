from __future__ import annotations

from PySide6 import QtWidgets

from VeraGrid.Gui.DeviceEditors.DcLineEditor.dc_line_device_editor import DcLineDeviceEditor
from VeraGrid.Gui.DeviceEditors.LineEditor.line_device_editor import LineDeviceEditor
from VeraGrid.Gui.DeviceEditors.TemplateDeviceEditor.template_device_editor import TemplateDeviceEditor
from VeraGrid.Gui.DeviceEditors.device_editor_factory import build_device_editor_dialog
from VeraGridEngine.Devices.Branches.dc_line import DcLine
from VeraGridEngine.Devices.Branches.hvdc_line import HvdcLine
from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit


def _build_branch_demo_circuit() -> tuple[MultiCircuit, Bus, Bus]:
    """
    Build one minimal circuit shared by the editor-routing checks.

    :return: Circuit and its endpoint buses.
    """
    circuit: MultiCircuit = MultiCircuit(name="device editor routing demo", Sbase=100.0, fbase=50.0)
    bus_from: Bus = Bus(name="Bus from", Vnom=110.0)
    bus_to: Bus = Bus(name="Bus to", Vnom=110.0)
    circuit.add_bus(obj=bus_from)
    circuit.add_bus(obj=bus_to)
    return circuit, bus_from, bus_to


def _get_tab_titles(dialog: TemplateDeviceEditor) -> list[str]:
    """
    Collect the visible tab titles from one device editor dialog.

    :param dialog: Editor dialog to inspect.
    :return: Tab title list in display order.
    """
    tab_titles: list[str] = list()
    tab_index: int
    for tab_index in range(dialog.tab_widget.count()):
        tab_titles.append(dialog.tab_widget.tabText(tab_index))
    return tab_titles


def test_branch_editor_factory_routes_line_and_dc_wrappers(qt_app: QtWidgets.QApplication) -> None:
    """
    Check that branch editors use the wrapper dialogs that embed the shared tabs.

    :param qt_app: Qt application fixture.
    """
    _qt_app: QtWidgets.QApplication = qt_app
    circuit: MultiCircuit
    bus_from: Bus
    bus_to: Bus
    circuit, bus_from, bus_to = _build_branch_demo_circuit()

    line: Line = Line(bus_from=bus_from, bus_to=bus_to, name="Line under test")
    dc_line: DcLine = DcLine(bus_from=bus_from, bus_to=bus_to, name="DC line under test")
    hvdc_line: HvdcLine = HvdcLine(bus_from=bus_from, bus_to=bus_to, name="HVDC line under test")

    line_dialog = build_device_editor_dialog(api_object=line, circuit=circuit)
    dc_line_dialog = build_device_editor_dialog(api_object=dc_line, circuit=circuit)
    hvdc_line_dialog = build_device_editor_dialog(api_object=hvdc_line, circuit=circuit)

    assert isinstance(line_dialog, LineDeviceEditor)
    assert isinstance(dc_line_dialog, DcLineDeviceEditor)
    assert isinstance(hvdc_line_dialog, TemplateDeviceEditor)

    line_dialog.close()
    dc_line_dialog.close()
    hvdc_line_dialog.close()


def test_branch_editors_expose_admittance_and_locations_tabs(qt_app: QtWidgets.QApplication) -> None:
    """
    Check that the routed branch editors keep the shared admittance and locations tabs.

    :param qt_app: Qt application fixture.
    """
    _qt_app: QtWidgets.QApplication = qt_app
    circuit: MultiCircuit
    bus_from: Bus
    bus_to: Bus
    circuit, bus_from, bus_to = _build_branch_demo_circuit()

    line: Line = Line(bus_from=bus_from, bus_to=bus_to, name="Line under test")
    dc_line: DcLine = DcLine(bus_from=bus_from, bus_to=bus_to, name="DC line under test")
    hvdc_line: HvdcLine = HvdcLine(bus_from=bus_from, bus_to=bus_to, name="HVDC line under test")

    line_dialog: LineDeviceEditor = LineDeviceEditor(api_object=line, circuit=circuit)
    dc_line_dialog: DcLineDeviceEditor = DcLineDeviceEditor(api_object=dc_line, circuit=circuit)
    hvdc_line_dialog: TemplateDeviceEditor = TemplateDeviceEditor(api_object=hvdc_line, circuit=circuit)

    line_tabs: list[str] = _get_tab_titles(dialog=line_dialog)
    dc_line_tabs: list[str] = _get_tab_titles(dialog=dc_line_dialog)
    hvdc_line_tabs: list[str] = _get_tab_titles(dialog=hvdc_line_dialog)

    assert "Admittance" in line_tabs
    assert "Locations" in line_tabs
    assert "Locations" in dc_line_tabs
    assert "Locations" in hvdc_line_tabs

    line_dialog.close()
    dc_line_dialog.close()
    hvdc_line_dialog.close()
