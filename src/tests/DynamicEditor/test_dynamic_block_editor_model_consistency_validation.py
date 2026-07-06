# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.001--.0-
from __future__ import annotations

import sys

import pytest
from PySide6 import QtWidgets

import VeraGrid.Gui.DynamicModelEditor.dynamic_block_editor as dynamic_block_editor_module
from VeraGrid.Gui.DynamicModelEditor.dynamic_block_editor import DynamicBlockEditorGUI
from VeraGrid.Gui.DynamicModelEditor.dynamic_block_editor import ValidationSection
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.enumerations import DynamicSimulationMode
from VeraGridEngine.enumerations import VarPowerFlowReferenceType

pytestmark = pytest.mark.filterwarnings("error")


class _BusStub:
    """
    Minimal bus object used by the validation tests.
    """

    __slots__ = ("name", "is_dc", "emt_model")

    def __init__(self, name: str, is_dc: bool, emt_model: Block) -> None:
        """
        Build one bus stub.

        :param name: Bus name.
        :param is_dc: Whether the bus is DC.
        :param emt_model: Existing EMT model shell.
        :return: None.
        """
        self.name: str = name
        self.is_dc: bool = is_dc
        self.emt_model: Block = emt_model


class _InjectionStub:
    """
    Minimal injection API object accepted by the dynamic editor.
    """

    __slots__ = ("name", "bus", "rms_template", "emt_template", "emt_model", "device_type")

    def __init__(self, name: str, bus: _BusStub, emt_template: EmtModelTemplate, device_type: DeviceType) -> None:
        """
        Build one injection stub.

        :param name: Device name.
        :param bus: Connected bus.
        :param emt_template: EMT template.
        :param device_type: Device type enum.
        :return: None.
        """
        self.name: str = name
        self.bus: _BusStub = bus
        self.rms_template = None
        self.emt_template: EmtModelTemplate = emt_template
        self.emt_model: Block = emt_template.block
        self.device_type: DeviceType = device_type


class _BranchStub:
    """
    Minimal branch API object accepted by the dynamic editor.
    """

    __slots__ = ("name", "bus_from", "bus_to", "rms_template", "emt_template", "emt_model", "device_type")

    def __init__(self,
                 name: str,
                 bus_from: _BusStub,
                 bus_to: _BusStub,
                 emt_template: EmtModelTemplate,
                 device_type: DeviceType) -> None:
        """
        Build one branch stub.

        :param name: Device name.
        :param bus_from: From-side bus.
        :param bus_to: To-side bus.
        :param emt_template: EMT template.
        :param device_type: Device type enum.
        :return: None.
        """
        self.name: str = name
        self.bus_from: _BusStub = bus_from
        self.bus_to: _BusStub = bus_to
        self.rms_template = None
        self.emt_template: EmtModelTemplate = emt_template
        self.emt_model: Block = emt_template.block
        self.device_type: DeviceType = device_type


@pytest.fixture(scope="module", autouse=True)
def _override_branch_parent_type() -> None:
    """
    Replace the branch-type check with the lightweight branch stub for this module.

    :return: None.
    """
    original_branch_parent = dynamic_block_editor_module.BranchParent
    dynamic_block_editor_module.BranchParent = _BranchStub
    try:
        yield
    finally:
        dynamic_block_editor_module.BranchParent = original_branch_parent


def _get_app() -> QtWidgets.QApplication:
    """
    Return the shared Qt application for validation tests.

    :return: Qt application.
    """
    application: QtWidgets.QApplication | None = QtWidgets.QApplication.instance()
    if application is None:
        return QtWidgets.QApplication(sys.argv)
    else:
        return application


def _make_var(name: str, reference: VarPowerFlowReferenceType) -> Var:
    """
    Build one symbolic variable with an EMT reference.

    :param name: Variable name.
    :param reference: Power-flow reference.
    :return: Symbolic variable.
    """
    return Var(name=name, reference=reference)


def _make_ac_bus(name: str) -> _BusStub:
    """
    Build one AC bus stub.

    :param name: Bus name.
    :return: AC bus stub.
    """
    bus_shell: Block = Block(external_mapping=dict({
        VarPowerFlowReferenceType.v_N: _make_var(f"v_N_{name}", VarPowerFlowReferenceType.v_N),
        VarPowerFlowReferenceType.v_A: _make_var(f"v_A_{name}", VarPowerFlowReferenceType.v_A),
        VarPowerFlowReferenceType.v_B: _make_var(f"v_B_{name}", VarPowerFlowReferenceType.v_B),
        VarPowerFlowReferenceType.v_C: _make_var(f"v_C_{name}", VarPowerFlowReferenceType.v_C),
    }))
    return _BusStub(name=name, is_dc=False, emt_model=bus_shell)


def _make_dc_bus(name: str) -> _BusStub:
    """
    Build one DC bus stub.

    :param name: Bus name.
    :return: DC bus stub.
    """
    bus_shell: Block = Block(external_mapping=dict({
        VarPowerFlowReferenceType.Vdc: _make_var(f"Vdc_{name}", VarPowerFlowReferenceType.Vdc),
    }))
    return _BusStub(name=name, is_dc=True, emt_model=bus_shell)


def _make_template(mapping_refs: list[VarPowerFlowReferenceType]) -> EmtModelTemplate:
    """
    Build one EMT template exposing the requested external references.

    :param mapping_refs: External references to expose.
    :return: EMT template.
    """
    external_mapping: dict[VarPowerFlowReferenceType, Var] = dict()
    reference: VarPowerFlowReferenceType

    for reference in mapping_refs:
        external_mapping[reference] = _make_var(f"templ_{reference.value}", reference)

    template: EmtModelTemplate = EmtModelTemplate(name="stub_template")
    template.block = Block(external_mapping=external_mapping)
    return template


def _set_editor_root_interface_refs(editor: DynamicBlockEditorGUI, refs: list[VarPowerFlowReferenceType]) -> None:
    """
    Materialize the requested EMT references into the editor root interface.

    :param editor: Editor instance.
    :param refs: Interface references to expose on the root block.
    :return: None.
    """
    # The real editor populates the root interface with connection variables. The
    # validation tests must mirror that state so the phase-consistency section is
    # evaluated against the same data structures as the running application.
    root_external_mapping: dict[VarPowerFlowReferenceType, Var] = dict()
    root_in_vars: list[Var] = list()
    root_out_vars: list[Var] = list()
    reference: VarPowerFlowReferenceType

    for reference in refs:
        var: Var = _make_var(name=f"root_{reference.value}", reference=reference)
        root_external_mapping[reference] = var

        if reference in {
            VarPowerFlowReferenceType.v_N,
            VarPowerFlowReferenceType.v_A,
            VarPowerFlowReferenceType.v_B,
            VarPowerFlowReferenceType.v_C,
            VarPowerFlowReferenceType.vf_N,
            VarPowerFlowReferenceType.vf_A,
            VarPowerFlowReferenceType.vf_B,
            VarPowerFlowReferenceType.vf_C,
            VarPowerFlowReferenceType.vt_N,
            VarPowerFlowReferenceType.vt_A,
            VarPowerFlowReferenceType.vt_B,
            VarPowerFlowReferenceType.vt_C,
            VarPowerFlowReferenceType.Vdc,
            VarPowerFlowReferenceType.Vf_dc,
            VarPowerFlowReferenceType.Vt_dc,
        }:
            root_in_vars.append(var)
        else:
            root_out_vars.append(var)

    editor.main_block.external_mapping = root_external_mapping
    editor.main_block.in_vars = root_in_vars
    editor.main_block.out_vars = root_out_vars

    # Rebuild the editor connection blocks so the scene and the saved diagram are
    # synchronized with the synthetic root interface used by the test.
    editor.diagram.node_data = dict()
    editor.diagram.con_data = dict()
    editor.add_connection_items()
    editor.rebuild_scene_from_diagram()


def _build_editor(api_object: ALL_DEV_TYPES) -> DynamicBlockEditorGUI:
    """
    Build one EMT dynamic block editor for validation tests.

    :param api_object: Stub API object.
    :return: Editor instance.
    """
    _get_app()
    editor: DynamicBlockEditorGUI = DynamicBlockEditorGUI(
        var_factory=VarFactory(),
        block=Block(),
        api_object=api_object,
        circuit=MultiCircuit(),
        mode=DynamicSimulationMode.EMT,
        templates_list=list(),
        main_editor=False,
        modal=False,
    )
    return editor


def _get_section_by_title(sections: list[ValidationSection], title: str) -> ValidationSection | None:
    """
    Return one validation section by title.

    :param sections: Validation section list.
    :param title: Section title.
    :return: Matching section or ``None``.
    """
    section: ValidationSection
    for section in sections:
        if section.get_title() == title:
            return section
        else:
            pass

    return None


def _get_row_detail_map(section: ValidationSection) -> dict[str, list[str]]:
    """
    Build one lookup from row label to detail lines.

    :param section: Validation section.
    :return: Detail lookup map.
    """
    detail_map: dict[str, list[str]] = dict()
    row = None

    for row in section.get_rows():
        detail_map[row.get_block_label()] = list(row.get_details())

    return detail_map


def _get_section_row_labels(section: ValidationSection) -> list[str]:
    """
    Return one ordered list of row labels from the section.

    :param section: Validation section.
    :return: Row labels.
    """
    row_labels: list[str] = list()
    row = None

    for row in section.get_rows():
        row_labels.append(row.get_block_label())

    return row_labels


def _connect_root_interface_ref(editor: DynamicBlockEditorGUI, reference: VarPowerFlowReferenceType) -> None:
    """
    Mark one protected EMT interface block as connected for validation tests.

    :param editor: Editor instance.
    :param reference: Interface reference to connect.
    :return: None.
    """
    scene_item: object
    protected_item: dynamic_block_editor_module.ProtectedConnectionBlockItem
    reference_var: Var | None = None
    connection_stub: object = object()

    for scene_item in editor.scene.items():
        if isinstance(scene_item, dynamic_block_editor_module.ProtectedConnectionBlockItem):
            protected_item = scene_item
            if protected_item.subsys is not None:
                if len(protected_item.subsys.out_vars) > 0:
                    reference_var = protected_item.subsys.out_vars[0]
                else:
                    if len(protected_item.subsys.in_vars) > 0:
                        reference_var = protected_item.subsys.in_vars[0]
                    else:
                        reference_var = None
            else:
                reference_var = None

            if reference_var is not None:
                if reference_var.ref == reference:
                    if len(protected_item.outputs) > 0:
                        protected_item.outputs[0].connections = list([connection_stub])
                    else:
                        if len(protected_item.inputs) > 0:
                            protected_item.inputs[0].connections = list([connection_stub])
                        else:
                            pass
                else:
                    pass
            else:
                pass
        else:
            pass


def test_validation_sections_skip_phase_consistency_for_pure_dc_injection() -> None:
    """
    Ensure pure DC EMT interfaces do not show the phase-consistency section.

    :return: None.
    """
    bus: _BusStub = _make_dc_bus("DC Bus")
    template: EmtModelTemplate = _make_template(list([
        VarPowerFlowReferenceType.Vdc,
        VarPowerFlowReferenceType.Idc,
    ]))
    injection: _InjectionStub = _InjectionStub("DC Load", bus, template, DeviceType.LoadDevice)
    editor: DynamicBlockEditorGUI = _build_editor(injection)

    sections: list[ValidationSection] = editor.collect_model_consistency_sections()
    phase_section: ValidationSection | None = _get_section_by_title(sections, "Phases Consistency")

    assert phase_section is None
    editor.close()


def test_validation_sections_show_phase_consistency_for_mixed_ac_dc_branch() -> None:
    """
    Ensure mixed AC/DC branch EMT interfaces still expose phase consistency.

    :return: None.
    """
    bus_from: _BusStub = _make_ac_bus("AC Bus")
    bus_to: _BusStub = _make_dc_bus("DC Bus")
    template: EmtModelTemplate = _make_template(list([
        VarPowerFlowReferenceType.v_A,
        VarPowerFlowReferenceType.v_B,
        VarPowerFlowReferenceType.v_C,
        VarPowerFlowReferenceType.Vdc,
        VarPowerFlowReferenceType.i_A,
        VarPowerFlowReferenceType.i_B,
        VarPowerFlowReferenceType.i_C,
        VarPowerFlowReferenceType.Idc,
    ]))
    branch: _BranchStub = _BranchStub("VSC 1", bus_from, bus_to, template, DeviceType.LineDevice)
    editor: DynamicBlockEditorGUI = _build_editor(branch)
    _set_editor_root_interface_refs(editor, list([
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
    ]))

    sections: list[ValidationSection] = editor.collect_model_consistency_sections()
    phase_section: ValidationSection | None = _get_section_by_title(sections, "Phases Consistency")

    assert phase_section is not None
    assert phase_section.get_first_column_title() == "Phase"
    editor.close()


def test_validation_phase_consistency_matches_injection_mask_logic() -> None:
    """
    Ensure the validator phase section matches the EMT ``Do it!`` mask logic.

    :return: None.
    """
    bus: _BusStub = _make_ac_bus("Load Bus")
    template: EmtModelTemplate = _make_template(list([
        VarPowerFlowReferenceType.v_N,
        VarPowerFlowReferenceType.v_A,
        VarPowerFlowReferenceType.v_B,
        VarPowerFlowReferenceType.v_C,
        VarPowerFlowReferenceType.i_N,
        VarPowerFlowReferenceType.i_A,
        VarPowerFlowReferenceType.i_B,
        VarPowerFlowReferenceType.i_C,
    ]))
    injection: _InjectionStub = _InjectionStub("Load 1", bus, template, DeviceType.LoadDevice)
    editor: DynamicBlockEditorGUI = _build_editor(injection)
    _set_editor_root_interface_refs(editor, list([
        VarPowerFlowReferenceType.v_N,
        VarPowerFlowReferenceType.v_A,
        VarPowerFlowReferenceType.v_B,
        VarPowerFlowReferenceType.v_C,
        VarPowerFlowReferenceType.i_N,
        VarPowerFlowReferenceType.i_A,
        VarPowerFlowReferenceType.i_B,
        VarPowerFlowReferenceType.i_C,
    ]))

    _connect_root_interface_ref(editor, VarPowerFlowReferenceType.v_N)
    _connect_root_interface_ref(editor, VarPowerFlowReferenceType.i_N)
    _connect_root_interface_ref(editor, VarPowerFlowReferenceType.v_A)
    _connect_root_interface_ref(editor, VarPowerFlowReferenceType.i_A)
    _connect_root_interface_ref(editor, VarPowerFlowReferenceType.v_B)

    sections: list[ValidationSection] = editor.collect_model_consistency_sections()
    phase_section: ValidationSection | None = _get_section_by_title(sections, "Phases Consistency")
    assert phase_section is not None

    detail_map: dict[str, list[str]] = _get_row_detail_map(phase_section)
    assert detail_map["Neutral"] == ["the model has this neutral wire"]
    assert detail_map["A"] == ["the model has this phase A"]
    assert detail_map["B"] == ["inconsistent connection of phase B, only V ports are connected"]
    assert detail_map["C"] == ["the model has no phase C"]
    editor.close()


def test_validation_phase_consistency_shows_only_ac_side_for_mixed_branch() -> None:
    """
    Ensure mixed AC/DC branch devices show only the AC side rows.

    :return: None.
    """
    bus_from: _BusStub = _make_ac_bus("AC Bus")
    bus_to: _BusStub = _make_dc_bus("DC Bus")
    template: EmtModelTemplate = _make_template(list([
        VarPowerFlowReferenceType.v_A,
        VarPowerFlowReferenceType.v_B,
        VarPowerFlowReferenceType.v_C,
        VarPowerFlowReferenceType.Vdc,
        VarPowerFlowReferenceType.i_A,
        VarPowerFlowReferenceType.i_B,
        VarPowerFlowReferenceType.i_C,
        VarPowerFlowReferenceType.Idc,
    ]))
    branch: _BranchStub = _BranchStub("VSC 1", bus_from, bus_to, template, DeviceType.LineDevice)
    editor: DynamicBlockEditorGUI = _build_editor(branch)
    _set_editor_root_interface_refs(editor, list([
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
    ]))

    sections: list[ValidationSection] = editor.collect_model_consistency_sections()
    phase_section: ValidationSection | None = _get_section_by_title(sections, "Phases Consistency")
    assert phase_section is not None

    row_labels: list[str] = list(row.get_block_label() for row in phase_section.get_rows())
    assert row_labels == [
        "N bus from",
        "A bus from",
        "B bus from",
        "C bus from",
    ]
    editor.close()


def test_validation_port_connectivity_skips_absent_protected_emt_phase_pair() -> None:
    """
    Ensure absent protected EMT phase pairs do not appear as port errors.

    :return: None.
    """
    bus: _BusStub = _make_ac_bus("Load Bus")
    template: EmtModelTemplate = _make_template(list([
        VarPowerFlowReferenceType.v_N,
        VarPowerFlowReferenceType.v_A,
        VarPowerFlowReferenceType.v_B,
        VarPowerFlowReferenceType.v_C,
        VarPowerFlowReferenceType.i_N,
        VarPowerFlowReferenceType.i_A,
        VarPowerFlowReferenceType.i_B,
        VarPowerFlowReferenceType.i_C,
    ]))
    injection: _InjectionStub = _InjectionStub("Load 1", bus, template, DeviceType.LoadDevice)
    editor: DynamicBlockEditorGUI = _build_editor(injection)

    _connect_root_interface_ref(editor, VarPowerFlowReferenceType.v_A)
    _connect_root_interface_ref(editor, VarPowerFlowReferenceType.i_A)
    _connect_root_interface_ref(editor, VarPowerFlowReferenceType.v_B)

    sections: list[ValidationSection] = editor.collect_model_consistency_sections()
    port_section: ValidationSection | None = _get_section_by_title(sections, "Port Connectivity")
    assert port_section is not None

    row_labels: list[str] = _get_section_row_labels(port_section)
    assert "v_N_Load Bus" not in row_labels
    assert "net_conn_i_N_Load 1" not in row_labels
    editor.close()
