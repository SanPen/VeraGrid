from __future__ import annotations

import sys

import pytest
from PySide6 import QtWidgets

from VeraGrid.Gui.DynamicModelEditor.dynamic_block_editor import BlockItem, DynamicBlockEditorGUI
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import DeviceType, DynamicSimulationMode, VarPowerFlowReferenceType

pytestmark = pytest.mark.filterwarnings("error")


class _BusStub:
    __slots__ = ("name", "is_dc", "emt_model")

    def __init__(self, name: str, is_dc: bool, emt_model: Block) -> None:
        self.name = name
        self.is_dc = is_dc
        self.emt_model = emt_model


class _InjectionStub:
    __slots__ = ("name", "bus", "rms_template", "emt_template", "emt_model", "device_type")

    def __init__(self, name: str, bus: _BusStub, emt_template: EmtModelTemplate, device_type: DeviceType) -> None:
        self.name = name
        self.bus = bus
        self.rms_template = None
        self.emt_template = emt_template
        self.emt_model = emt_template.block
        self.device_type = device_type


class _BranchStub:
    __slots__ = ("name", "bus_from", "bus_to", "rms_template", "emt_template", "emt_model", "device_type")

    def __init__(self,
                 name: str,
                 bus_from: _BusStub,
                 bus_to: _BusStub,
                 emt_template: EmtModelTemplate,
                 device_type: DeviceType) -> None:
        self.name = name
        self.bus_from = bus_from
        self.bus_to = bus_to
        self.rms_template = None
        self.emt_template = emt_template
        self.emt_model = emt_template.block
        self.device_type = device_type


def _get_app() -> QtWidgets.QApplication:
    app = QtWidgets.QApplication.instance()
    if app is None:
        return QtWidgets.QApplication(sys.argv)
    else:
        return app


def _make_var(name: str, reference: VarPowerFlowReferenceType) -> Var:
    return Var(name=name, reference=reference)


def _make_ac_bus(name: str) -> _BusStub:
    return _BusStub(
        name=name,
        is_dc=False,
        emt_model=Block(external_mapping={
            VarPowerFlowReferenceType.v_N: _make_var(f"v_N_{name}", VarPowerFlowReferenceType.v_N),
            VarPowerFlowReferenceType.v_A: _make_var(f"v_A_{name}", VarPowerFlowReferenceType.v_A),
            VarPowerFlowReferenceType.v_B: _make_var(f"v_B_{name}", VarPowerFlowReferenceType.v_B),
            VarPowerFlowReferenceType.v_C: _make_var(f"v_C_{name}", VarPowerFlowReferenceType.v_C),
        }),
    )


def _make_dc_bus(name: str) -> _BusStub:
    return _BusStub(
        name=name,
        is_dc=True,
        emt_model=Block(external_mapping={
            VarPowerFlowReferenceType.Vdc: _make_var(f"Vdc_{name}", VarPowerFlowReferenceType.Vdc),
        }),
    )


def _make_template(mapping_refs: list[VarPowerFlowReferenceType]) -> EmtModelTemplate:
    template = EmtModelTemplate(name="stub_template")
    template.block = Block(external_mapping={
        reference: _make_var(f"templ_{reference.value}", reference)
        for reference in mapping_refs
    })
    return template


def _build_editor(api_object: object) -> DynamicBlockEditorGUI:
    _get_app()
    editor = DynamicBlockEditorGUI(
        var_factory=VarFactory(),
        block=Block(),
        api_object=api_object,
        mode=DynamicSimulationMode.EMT,
        templates_list=list(),
        main_editor=False,
        modal=False,
    )
    return editor


def _find_connection_block_item(editor: DynamicBlockEditorGUI, block_name: str) -> BlockItem:
    """Return the scene block item wrapping one top-level connection variable."""
    item: object
    wrapped_var_name: str | None

    for item in editor.scene.items():
        if isinstance(item, BlockItem):
            if item.subsys is not None:
                wrapped_var_name = None

                if len(item.subsys.out_vars) > 0:
                    wrapped_var_name = item.subsys.out_vars[0].name
                elif len(item.subsys.in_vars) > 0:
                    wrapped_var_name = item.subsys.in_vars[0].name
                else:
                    pass

                if wrapped_var_name == block_name:
                    return item
                else:
                    pass
            else:
                pass
        else:
            pass

    raise AssertionError(f"Connection block '{block_name}' not found")


def test_emt_branch_connection_specs_expose_bus_domain_interface_for_ac_branch() -> None:
    bus_from = _make_ac_bus("Bus From")
    bus_to = _make_ac_bus("Bus To")
    template = _make_template([
        VarPowerFlowReferenceType.vf_N,
        VarPowerFlowReferenceType.vf_A,
        VarPowerFlowReferenceType.vf_B,
        VarPowerFlowReferenceType.vf_C,
        VarPowerFlowReferenceType.vt_N,
        VarPowerFlowReferenceType.vt_A,
        VarPowerFlowReferenceType.vt_B,
        VarPowerFlowReferenceType.vt_C,
        VarPowerFlowReferenceType.if_N,
        VarPowerFlowReferenceType.if_A,
        VarPowerFlowReferenceType.if_B,
        VarPowerFlowReferenceType.if_C,
        VarPowerFlowReferenceType.it_N,
        VarPowerFlowReferenceType.it_A,
        VarPowerFlowReferenceType.it_B,
        VarPowerFlowReferenceType.it_C,
    ])
    branch = _BranchStub("Line 1", bus_from, bus_to, template, DeviceType.LineDevice)
    editor = _build_editor(branch)

    specs = editor._build_emt_branch_connection_specs()

    assert [spec.reference for spec in specs] == [
        VarPowerFlowReferenceType.vf_N,
        VarPowerFlowReferenceType.vf_A,
        VarPowerFlowReferenceType.vf_B,
        VarPowerFlowReferenceType.vf_C,
        VarPowerFlowReferenceType.if_N,
        VarPowerFlowReferenceType.if_A,
        VarPowerFlowReferenceType.if_B,
        VarPowerFlowReferenceType.if_C,
        VarPowerFlowReferenceType.vt_N,
        VarPowerFlowReferenceType.vt_A,
        VarPowerFlowReferenceType.vt_B,
        VarPowerFlowReferenceType.vt_C,
        VarPowerFlowReferenceType.it_N,
        VarPowerFlowReferenceType.it_A,
        VarPowerFlowReferenceType.it_B,
        VarPowerFlowReferenceType.it_C,
    ]
    assert [spec.visible_name for spec in specs] == [
        "vf_N_Bus_From",
        "vf_A_Bus_From",
        "vf_B_Bus_From",
        "vf_C_Bus_From",
        "net_conn_if_N_Bus_From_Line 1",
        "net_conn_if_A_Bus_From_Line 1",
        "net_conn_if_B_Bus_From_Line 1",
        "net_conn_if_C_Bus_From_Line 1",
        "vt_N_Bus_To",
        "vt_A_Bus_To",
        "vt_B_Bus_To",
        "vt_C_Bus_To",
        "net_conn_it_N_Bus_To_Line 1",
        "net_conn_it_A_Bus_To_Line 1",
        "net_conn_it_B_Bus_To_Line 1",
        "net_conn_it_C_Bus_To_Line 1",
    ]

    editor.close()


def test_emt_branch_connection_specs_expose_bus_domain_interface_for_ac_dc_branch() -> None:
    bus_from = _make_ac_bus("AC Bus")
    bus_to = _make_dc_bus("DC Bus")
    template = _make_template([
        VarPowerFlowReferenceType.v_A,
        VarPowerFlowReferenceType.v_B,
        VarPowerFlowReferenceType.v_C,
        VarPowerFlowReferenceType.Vdc,
        VarPowerFlowReferenceType.i_A,
        VarPowerFlowReferenceType.i_B,
        VarPowerFlowReferenceType.i_C,
        VarPowerFlowReferenceType.Idc,
    ])
    branch = _BranchStub("VSC 1", bus_from, bus_to, template, DeviceType.VscDevice)
    editor = _build_editor(branch)

    specs = editor._build_emt_branch_connection_specs()

    assert [spec.reference for spec in specs] == [
        VarPowerFlowReferenceType.vf_N,
        VarPowerFlowReferenceType.vf_A,
        VarPowerFlowReferenceType.vf_B,
        VarPowerFlowReferenceType.vf_C,
        VarPowerFlowReferenceType.if_N,
        VarPowerFlowReferenceType.if_A,
        VarPowerFlowReferenceType.if_B,
        VarPowerFlowReferenceType.if_C,
        VarPowerFlowReferenceType.Vt_dc,
        VarPowerFlowReferenceType.It_dc,
    ]
    assert [spec.visible_name for spec in specs] == [
        "vf_N_AC_Bus",
        "vf_A_AC_Bus",
        "vf_B_AC_Bus",
        "vf_C_AC_Bus",
        "net_conn_if_N_AC_Bus_VSC 1",
        "net_conn_if_A_AC_Bus_VSC 1",
        "net_conn_if_B_AC_Bus_VSC 1",
        "net_conn_if_C_AC_Bus_VSC 1",
        "Vt_dc_DC_Bus",
        "net_conn_It_dc_DC_Bus_VSC 1",
    ]

    editor.close()


def test_emt_injection_connection_specs_expose_bus_domain_interface_for_ac_injection() -> None:
    bus = _make_ac_bus("Gen Bus")
    template = _make_template([
        VarPowerFlowReferenceType.v_A,
        VarPowerFlowReferenceType.v_B,
        VarPowerFlowReferenceType.v_C,
        VarPowerFlowReferenceType.i_A,
        VarPowerFlowReferenceType.i_B,
        VarPowerFlowReferenceType.i_C,
    ])
    injection = _InjectionStub("Gen 1", bus, template, DeviceType.GeneratorDevice)
    editor = _build_editor(injection)

    specs = editor._build_emt_injection_connection_specs()

    assert [spec.reference for spec in specs] == [
        VarPowerFlowReferenceType.v_N,
        VarPowerFlowReferenceType.v_A,
        VarPowerFlowReferenceType.v_B,
        VarPowerFlowReferenceType.v_C,
        VarPowerFlowReferenceType.i_N,
        VarPowerFlowReferenceType.i_A,
        VarPowerFlowReferenceType.i_B,
        VarPowerFlowReferenceType.i_C,
    ]
    assert [spec.visible_name for spec in specs] == [
        "v_N_Gen_Bus",
        "v_A_Gen_Bus",
        "v_B_Gen_Bus",
        "v_C_Gen_Bus",
        "net_conn_i_N_Gen 1",
        "net_conn_i_A_Gen 1",
        "net_conn_i_B_Gen 1",
        "net_conn_i_C_Gen 1",
    ]

    editor.close()


def test_emt_injection_connection_specs_expose_bus_domain_interface_for_dc_injection() -> None:
    bus = _make_dc_bus("DC Load Bus")
    template = _make_template([
        VarPowerFlowReferenceType.Vdc,
        VarPowerFlowReferenceType.Idc,
    ])
    injection = _InjectionStub("DC Load 1", bus, template, DeviceType.LoadDevice)
    editor = _build_editor(injection)

    specs = editor._build_emt_injection_connection_specs()

    assert [spec.reference for spec in specs] == [
        VarPowerFlowReferenceType.Vdc,
        VarPowerFlowReferenceType.Idc,
    ]
    assert [spec.visible_name for spec in specs] == [
        "Vdc_DC_Load_Bus",
        "net_conn_Idc_DC Load 1",
    ]

    editor.close()


def test_removing_connection_block_removes_saved_root_interface_variable() -> None:
    bus = _make_ac_bus("Removal Bus")
    template = _make_template(list())
    injection = _InjectionStub("Load 1", bus, template, DeviceType.LoadDevice)
    editor = _build_editor(injection)

    editor._materialize_connection_specs(editor._build_emt_injection_connection_specs())
    editor.add_connection_items()

    assert VarPowerFlowReferenceType.v_N in editor.main_block.external_mapping
    assert any(var.name == "v_N_Removal_Bus" for var in editor.main_block.in_vars)

    neutral_item = _find_connection_block_item(editor, "v_N_Removal_Bus")
    editor.remove_item(neutral_item)

    assert VarPowerFlowReferenceType.v_N not in editor.main_block.external_mapping
    assert all(var.name != "v_N_Removal_Bus" for var in editor.main_block.in_vars)
    assert editor.get_block_from_main_block(neutral_item.subsys.uid) is None

    editor.has_unapplied_changes = False
    editor.close()
