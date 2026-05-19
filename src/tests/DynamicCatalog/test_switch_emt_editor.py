from __future__ import annotations

import sys

from PySide6 import QtWidgets

import VeraGrid.Gui.DynamicModelEditor.dynamic_block_editor as dynamic_block_editor_module
from VeraGrid.Gui.DynamicModelEditor.dynamic_block_editor import DynamicBlockEditorGUI
from VeraGrid.Gui.DynamicModelEditor.dynamic_block_editor import get_modal_template_metadata
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.enumerations import BlockType, DynamicSimulationMode, DeviceType

class _ApiStub:
    __slots__ = ("name", "rms_template", "emt_template", "device_type")

    def __init__(self) -> None:
        self.name = "Stub"
        self.rms_template = None
        self.emt_template = None
        self.device_type = DeviceType.NoDevice


def _get_app() -> QtWidgets.QApplication:
    app = QtWidgets.QApplication.instance()
    if app is None:
        return QtWidgets.QApplication(sys.argv)
    return app


def _build_editor() -> DynamicBlockEditorGUI:
    _get_app()
    editor = DynamicBlockEditorGUI(
        var_factory=VarFactory(),
        block=Block(),
        api_object=_ApiStub(),
        mode=DynamicSimulationMode.EMT,
        templates_list=list(),
        main_editor=False,
        modal=False,
    )
    editor.show()
    editor.activateWindow()
    return editor


def test_switch_emt_block_item_is_created_from_modal(override_attrs) -> None:
    editor = _build_editor()

    class _SwitchDialogStub:
        def __init__(self, parent=None) -> None:
            _unused = parent

        def exec(self) -> int:
            return int(QtWidgets.QDialog.DialogCode.Accepted)

        def get_switch_configuration(self) -> dict[str, object]:
            return dict({
                "phA": True,
                "phB": True,
                "phC": True,
                "signal_controlled": True,
                "seed_from_pf_active": True,
                "initial_closed": True,
                "use_device_conductance": True,
                "manual_closed_conductance": 1.0e4,
                "open_conductance": 1.0e-8,
                "switch_time_constant": 1.0e-4,
                "command_threshold": 0.5,
            })

    override_attrs.setattr(dynamic_block_editor_module, "SwitchEmtDialog", _SwitchDialogStub)
    block_item = editor.create_library_payload_item(BlockType.SWITCH_EMT, 10.0, 20.0)

    assert block_item is not None
    assert any(var.name.startswith("switch_closed_mode_") for var in block_item.subsys.mode_dict.keys())
    assert any(var.name.startswith("switch_cmd_") for var in block_item.subsys.in_vars)

    editor.has_unapplied_changes = False
    editor.close()


def test_modal_created_block_supports_nested_editor_open(override_attrs) -> None:
    editor = _build_editor()
    block = Block(name="nested_test_block")
    block_item = editor.create_template_block_item(type("_Template", (), {"name": "nested_test_block", "block": block})(), 10.0, 20.0)

    assert block_item is not None

    override_attrs.setattr(dynamic_block_editor_module.DynamicBlockEditorGUI, "show", lambda self: None)
    override_attrs.setattr(dynamic_block_editor_module.DynamicBlockEditorGUI, "raise_", lambda self: None)
    override_attrs.setattr(dynamic_block_editor_module.DynamicBlockEditorGUI, "activateWindow", lambda self: None)
    editor.open_block_subeditor(block_item)
    assert getattr(block_item, "editor_window", None) is not None

    editor.has_unapplied_changes = False
    editor.close()


def test_scene_edit_dispatch_opens_editor_for_modal_created_block(override_attrs) -> None:
    editor = _build_editor()
    block = Block(name="dispatch_edit_block")
    block_item = editor.create_template_block_item(type("_Template", (), {"name": "dispatch_edit_block", "block": block})(), 10.0, 20.0)

    assert block_item is not None

    override_attrs.setattr(dynamic_block_editor_module.DynamicBlockEditorGUI, "show", lambda self: None)
    override_attrs.setattr(dynamic_block_editor_module.DynamicBlockEditorGUI, "raise_", lambda self: None)
    override_attrs.setattr(dynamic_block_editor_module.DynamicBlockEditorGUI, "activateWindow", lambda self: None)
    editor.edit_scene_item(block_item)
    assert getattr(block_item, "editor_window", None) is not None

    editor.has_unapplied_changes = False
    editor.close()


def test_modify_template_updates_switch_block_in_place(override_attrs) -> None:
    editor = _build_editor()

    class _CreateDialogStub:
        def __init__(self, parent=None, initial_config=None) -> None:
            _unused = (parent, initial_config)

        def exec(self) -> int:
            return int(QtWidgets.QDialog.DialogCode.Accepted)

        def get_switch_configuration(self) -> dict[str, object]:
            return dict({
                "phA": True,
                "phB": False,
                "phC": False,
                "signal_controlled": False,
                "seed_from_pf_active": True,
                "initial_closed": True,
                "use_device_conductance": True,
                "manual_closed_conductance": 1.0e4,
                "open_conductance": 1.0e-8,
                "switch_time_constant": 1.0e-4,
                "command_threshold": 0.5,
            })

    class _ModifyDialogStub:
        def __init__(self, parent=None, initial_config=None) -> None:
            _unused = (parent, initial_config)

        def exec(self) -> int:
            return int(QtWidgets.QDialog.DialogCode.Accepted)

        def get_switch_configuration(self) -> dict[str, object]:
            return dict({
                "phA": True,
                "phB": True,
                "phC": True,
                "signal_controlled": True,
                "seed_from_pf_active": False,
                "initial_closed": False,
                "use_device_conductance": False,
                "manual_closed_conductance": 25.0,
                "open_conductance": 1.0e-6,
                "switch_time_constant": 2.0e-4,
                "command_threshold": 0.25,
            })

    override_attrs.setattr(dynamic_block_editor_module, "SwitchEmtDialog", _CreateDialogStub)
    block_item = editor.create_library_payload_item(BlockType.SWITCH_EMT, 10.0, 20.0)
    assert block_item is not None

    override_attrs.setattr(dynamic_block_editor_module, "SwitchEmtDialog", _ModifyDialogStub)
    editor.modify_scene_item_template(block_item)

    modal_kind, modal_config = get_modal_template_metadata(block_item.subsys)
    assert modal_kind == "switch_emt"
    assert modal_config is not None
    assert bool(modal_config["signal_controlled"])
    assert not bool(modal_config["seed_from_pf_active"])
    assert float(modal_config["manual_closed_conductance"]) == 25.0
    assert any(var.name.startswith("switch_cmd_") for var in block_item.subsys.in_vars)

    editor.has_unapplied_changes = False
    editor.close()
