from __future__ import annotations

from PySide6 import QtWidgets

from VeraGrid.Gui.DeviceEditors.DcLineEditor.dc_line_device_editor import DcLineDeviceEditorDialog
from VeraGrid.Gui.DeviceEditors.LineEditor.line_device_editor import LineDeviceEditorDialog
from VeraGrid.Gui.DeviceEditors.TemplateDeviceEditor.template_device_editor import TemplateDeviceEditor
from VeraGridEngine.Devices.Parents.editable_device import EditableDevice
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.enumerations import DeviceType


def build_device_editor_dialog(api_object: EditableDevice,
                               circuit: MultiCircuit | None = None) -> QtWidgets.QDialog:
    """
    Build the best editor dialog for one editable device.

    :param api_object: Device to edit.
    :param circuit: Optional circuit context used by the editor.
    :return: Configured dialog instance.
    """
    # Route branch devices through their wrapper dialogs so shared tabs such as
    # admittance and locations stay available alongside the legacy design tabs.
    if api_object.device_type == DeviceType.LineDevice:
        return LineDeviceEditorDialog(api_object=api_object, circuit=circuit)
    elif api_object.device_type == DeviceType.DCLineDevice:
        return DcLineDeviceEditorDialog(api_object=api_object, circuit=circuit)
    else:
        return TemplateDeviceEditor(api_object=api_object, circuit=circuit)
