# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Contracts for catalogue actions derived from the dynamic Library."""

from __future__ import annotations


import copy
from pathlib import Path

from PySide6 import QtWidgets

import VeraGridEngine.api as vg
from VeraGrid.Gui.CatalogueElementsDialogue.catalogue_actions import CatalogueAction
from VeraGrid.Gui.DynamicModelEditor.Editor.dynamic_block_editor import DynamicBlockEditorGUI
from VeraGridEngine.Templates.device_template_materialization import (
    create_default_template_builder,
    initialize_template_builder_from_block,
)
from VeraGrid.Gui.CatalogueElementsDialogue.catalogue_elements_dialogue import (
    CatalogueElementsSelectionDialogue,
)
from VeraGrid.Gui.DynamicModelEditor.Editor.DynamicLibrary.dynamic_editor_library import (
    LibraryDeviceTemplateSpec,
    get_dynamic_library_device_specs,
)
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Templates.Rms.converters.hvdc_vsc_gfl_rms_template_v2 import HvdcVscGflRmsTemplate
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic_io import BlockSaver
from VeraGridEngine.enumerations import BlockType, ConverterControlType, DeviceType, DynamicSimulationMode

from tests.symbolic_block_roundtrip import parse_saved_block, roundtrip_block, save_block_fixture


def test_rms_catalogue_matches_library_devices(qt_app: QtWidgets.QApplication) -> None:
    """Require a one-to-one mapping between RMS Devices and catalogue actions.

    :param qt_app: Shared Qt application required to construct the dialog.
    :return: None.
    """
    application: QtWidgets.QApplication = qt_app
    circuit: MultiCircuit = MultiCircuit()
    dialog: CatalogueElementsSelectionDialogue = CatalogueElementsSelectionDialogue(
        parent=None,
        circuit=circuit,
    )
    actions: list[CatalogueAction] = dialog.build_rms_actions()
    specs: list[LibraryDeviceTemplateSpec] = get_dynamic_library_device_specs(
        mode=DynamicSimulationMode.RMS,
    )

    assert list(action.name for action in actions) == list(spec.label for spec in specs)
    assert all(action.voltage_text == "" for action in actions)
    assert list(action.description_text for action in actions) == list(
        spec.description for spec in specs
    )
    assert len(set(action.unique_key for action in actions)) == len(actions)
    assert "GENROE" in list(spec.label for spec in specs)

    line_action: CatalogueAction | None = None
    action: CatalogueAction
    for action in actions:
        if action.name == "Line":
            line_action = action
        else:
            pass
    assert line_action is not None
    line_action.execute(circuit=circuit)
    assert circuit.rms_models[-1].code == ""

    dialog.close()
    application.processEvents()


def test_catalogue_hvdc_controls_survive_save_reload_and_insertion(
        qt_app: QtWidgets.QApplication,
        tmp_path: Path,
) -> None:
    """Keep selected HVDC control modes visible through file and editor copies."""
    circuit = MultiCircuit()
    spec = next(
        item for item in get_dynamic_library_device_specs(DynamicSimulationMode.RMS)
        if item.source == BlockType.GFL_VSC_HVDC_RMS
    )
    builder = HvdcVscGflRmsTemplate(circuit.var_factory)
    builder.params_dict["control1"].value = ConverterControlType.Pdc
    builder.params_dict["control2"].value = ConverterControlType.Vm_ac
    builder.params_dict["cdc"].value = 0.73
    template = builder.eval()
    circuit.add_rms_model(template)
    expected_config = {"control1": "Pdc", "control2": "Vm_ac", "cdc": 0.73}

    copied_block = copy.deepcopy(template.block)
    assert copied_block.modal_template_config == expected_config
    assert copied_block.modal_template_config is not template.block.modal_template_config
    assert roundtrip_block(template.block).modal_template_config == expected_config
    # A real version-6 record has no modal metadata anywhere, so the controls
    # must be recovered from the block structure.
    legacy_records: dict[int, dict[str, object]]
    legacy_data: dict[str, object]
    legacy_saver: BlockSaver
    legacy_records, legacy_saver = save_block_fixture(template.block)
    legacy_data = legacy_records[template.block.uid]
    legacy_contract: object = legacy_data["dynamic_model_contract"]
    assert isinstance(legacy_contract, dict)
    legacy_contract["version"] = 6
    legacy_contract.pop("modal_template_kind")
    legacy_contract.pop("modal_template_config")
    legacy_contract.pop("emt_finite_reciprocal_source_mode_var_uid", None)
    assert "modal_template_kind" not in legacy_data
    assert "modal_template_config" not in legacy_data
    legacy_block = parse_saved_block(legacy_records, legacy_saver)
    legacy_builder = create_default_template_builder(
        circuit.var_factory,
        BlockType.GFL_VSC_HVDC_RMS,
        legacy_block.name,
    )
    assert legacy_builder is not None
    initialize_template_builder_from_block(
        legacy_builder,
        legacy_block,
        BlockType.GFL_VSC_HVDC_RMS,
    )
    assert legacy_builder.get_value("control1") is ConverterControlType.Pdc
    assert legacy_builder.get_value("control2") is ConverterControlType.Vm_ac

    path = tmp_path / "catalogue_hvdc.veragrid"
    vg.save_file(circuit, str(path))
    reopened = vg.open_file(str(path))
    saved_template = reopened.rms_models[0]
    assert saved_template.code == ""
    assert saved_template.block.modal_template_kind == template.block.modal_template_kind
    assert saved_template.block.modal_template_config == expected_config
    assert template.block.compare(saved_template.block)

def test_emt_catalogue_matches_library_devices(qt_app: QtWidgets.QApplication) -> None:
    """Require a one-to-one mapping between EMT Devices and catalogue actions.

    :param qt_app: Shared Qt application required to construct the dialog.
    :return: None.
    """
    application: QtWidgets.QApplication = qt_app
    circuit: MultiCircuit = MultiCircuit()
    dialog: CatalogueElementsSelectionDialogue = CatalogueElementsSelectionDialogue(
        parent=None,
        circuit=circuit,
    )
    actions: list[CatalogueAction] = dialog.build_emt_actions()
    specs: list[LibraryDeviceTemplateSpec] = get_dynamic_library_device_specs(
        mode=DynamicSimulationMode.EMT,
    )

    assert list(action.name for action in actions) == list(spec.label for spec in specs)
    assert all(action.voltage_text == "" for action in actions)
    assert list(action.description_text for action in actions) == list(
        spec.description for spec in specs
    )
    assert len(set(action.unique_key for action in actions)) == len(actions)

    load_action: CatalogueAction | None = None
    action: CatalogueAction
    for action in actions:
        if action.name == "DC load":
            load_action = action
        else:
            pass
    assert load_action is not None
    load_action.execute(circuit=circuit)
    assert circuit.emt_models[-1].code == ""

    dialog.close()
    application.processEvents()


def test_catalogue_retains_dynamic_library_category_paths(
        qt_app: QtWidgets.QApplication,
) -> None:
    """Keep RMS and EMT catalogue entries grouped like the Dynamic Library.

    :param qt_app: Shared Qt application required to construct the dialog.
    :return: None.
    """
    application: QtWidgets.QApplication = qt_app
    circuit: MultiCircuit = MultiCircuit()
    dialog: CatalogueElementsSelectionDialogue = CatalogueElementsSelectionDialogue(
        parent=None,
        circuit=circuit,
    )
    root = dialog._model.invisibleRootItem()
    rms_item = None
    emt_item = None
    root_index: int
    for root_index in range(root.rowCount()):
        candidate_item = root.child(root_index, 0)
        if candidate_item is None:
            pass
        elif candidate_item.text() == "RMS model templates":
            rms_item = candidate_item
        elif candidate_item.text() == "EMT model templates":
            emt_item = candidate_item
        else:
            pass

    assert rms_item is not None
    assert emt_item is not None
    rms_categories: set[str] = set()
    emt_categories: set[str] = set()
    category_index: int
    for category_index in range(rms_item.rowCount()):
        category_item = rms_item.child(category_index, 0)
        if category_item is None:
            pass
        else:
            rms_categories.add(category_item.text())
    for category_index in range(emt_item.rowCount()):
        category_item = emt_item.child(category_index, 0)
        if category_item is None:
            pass
        else:
            emt_categories.add(category_item.text())

    assert "Native" not in rms_categories
    assert "International standards" not in rms_categories
    assert "PV generators" in rms_categories
    assert "Wind turbines" in rms_categories
    assert "Synchronous and other generators" in rms_categories
    assert "Additional templates" not in rms_categories
    assert rms_categories.isdisjoint(set(("Controls", "Basic", "Procedural logic")))
    assert "Native" not in emt_categories
    assert "Sources" in emt_categories

    dialog.select_all()
    selected: dict[str, list[CatalogueAction]] = dialog.get_selected_elements()
    assert len(selected["RMS model templates"]) == (
        len(get_dynamic_library_device_specs(DynamicSimulationMode.RMS))
    )
    assert len(selected["EMT model templates"]) == (
        len(get_dynamic_library_device_specs(DynamicSimulationMode.EMT))
    )

    dialog.close()
    application.processEvents()
