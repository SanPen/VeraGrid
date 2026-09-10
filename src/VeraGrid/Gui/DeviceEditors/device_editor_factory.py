from __future__ import annotations

from PySide6 import QtWidgets

from VeraGrid.Gui.DeviceEditors.ControllableShuntEditor.controllable_shunt_device_editor import (
    ControllableShuntDeviceEditorDialog,
)
from VeraGrid.Gui.DeviceEditors.DcLineEditor.dc_line_device_editor import DcLineDeviceEditorDialog
from VeraGrid.Gui.DeviceEditors.GeneratorEditor.generator_editor import GeneratorEditorDialog
from VeraGrid.Gui.DeviceEditors.LineEditor.line_device_editor import LineDeviceEditorDialog
from VeraGrid.Gui.DeviceEditors.LoadDesigner.load_device_editor import LoadDeviceEditorDialog
from VeraGrid.Gui.DeviceEditors.TemplateDeviceEditor.template_device_editor import TemplateDeviceEditor
from VeraGrid.Gui.DeviceEditors.Transformer3wEditor.transformer3w_device_editor import Transformer3WDeviceEditorDialog
from VeraGrid.Gui.DeviceEditors.TransformerEditor.transformer_device_editor import TransformerDeviceEditorDialog
from VeraGrid.Gui.DeviceEditors.VscEditor.vsc_device_editor import VscDeviceEditorDialog
from VeraGridEngine.Devices.Parents.editable_device import EditableDevice
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.enumerations import DeviceType


def build_device_editor_dialog(api_object: EditableDevice,
                               circuit: MultiCircuit | None = None,
                               main_gui: object | None = None) -> QtWidgets.QDialog:
    """
    Build the best editor dialog for one editable device.

    :param api_object: Device to edit.
    :param circuit: Optional circuit context used by the editor.
    :param main_gui: Optional main GUI context used by specialized editors.
    :return: Configured dialog instance.
    """
    # Route devices through their wrapper dialogs so specialized tabs stay available.
    if api_object.device_type == DeviceType.ControllableShuntDevice:
        return ControllableShuntDeviceEditorDialog(api_object=api_object, circuit=circuit)
    elif api_object.device_type == DeviceType.DCLineDevice:
        return DcLineDeviceEditorDialog(api_object=api_object, circuit=circuit)
    elif api_object.device_type == DeviceType.GeneratorDevice:
        return GeneratorEditorDialog(api_object=api_object, circuit=circuit)
    elif api_object.device_type == DeviceType.BatteryDevice:
        return GeneratorEditorDialog(api_object=api_object, circuit=circuit)
    elif api_object.device_type == DeviceType.LineDevice:
        return LineDeviceEditorDialog(api_object=api_object, circuit=circuit)
    elif api_object.device_type == DeviceType.LoadDevice:
        return LoadDeviceEditorDialog(api_object=api_object, circuit=circuit)
    elif api_object.device_type == DeviceType.Transformer2WDevice:
        return TransformerDeviceEditorDialog(api_object=api_object, circuit=circuit)
    elif api_object.device_type == DeviceType.Transformer3WDevice:
        return Transformer3WDeviceEditorDialog(api_object=api_object, circuit=circuit)
    elif api_object.device_type == DeviceType.VscDevice:
        return VscDeviceEditorDialog(api_object=api_object, circuit=circuit, main_gui=main_gui)
    else:
        return TemplateDeviceEditor(api_object=api_object, circuit=circuit)
