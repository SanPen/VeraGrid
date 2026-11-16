# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Exercise interconnection configuration and persisted graphics reconstruction."""
from __future__ import annotations

import sys

from PySide6 import QtCore, QtWidgets

from VeraGrid.Gui.DynamicModelEditor.Editor import dynamic_editor_graphics as graph
from VeraGrid.Gui.DynamicModelEditor.Editor.dynamic_block_editor import DynamicBlockEditorGUI
from VeraGrid.Gui.DynamicModelEditor.Editor.ElementDialogues.interconnection_dialog import InterconnectionDialog
from VeraGridEngine.Devices.Dynamic.model_interconnections import add_interconnection_block
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
from VeraGridEngine.enumerations import BlockType, DynamicSimulationMode


def get_qt_application() -> QtWidgets.QApplication:
    """Retain one QApplication for graphical tests.

    :return: Existing or newly created application.
    """
    application: QtWidgets.QApplication | None = QtWidgets.QApplication.instance()
    if application is None:
        return QtWidgets.QApplication(sys.argv)
    else:
        return application


def test_interconnection_dialog_selects_source_variables_and_restores_selection() -> None:
    """Restore selections by source device and effective variable UID.

    :return: None.
    """
    application: QtWidgets.QApplication = get_qt_application()
    source: Generator = Generator(name="Source")
    state: Var = Var("shared_state")
    source.rms_model = Block(state_vars=list((state,)), state_eqs=list((Const(1.0),)))
    dialog: InterconnectionDialog = InterconnectionDialog(list((source,)))
    dialog.set_selected_device(source)
    assert dialog._device_button.text().startswith("Source")
    assert dialog._tree.topLevelItemCount() == 1
    dialog._tree.topLevelItem(0).setCheckState(0, QtCore.Qt.CheckState.Checked)
    assert dialog.get_selected_device() is source
    assert dialog.get_variables() == list((state,))
    dialog.accept()
    assert dialog.result() == QtWidgets.QDialog.DialogCode.Accepted
    restored: InterconnectionDialog = InterconnectionDialog(list((source,)), source.idtag, list((state,)))
    assert restored.get_variables() == list((state,))
    restored.close()
    dialog.close()
    application.processEvents()


def test_library_item_and_imported_diagram_rebuild_as_interconnection_items() -> None:
    """Rebuild the same graphical class from nodes created without Qt.

    :return: None.
    """
    application: QtWidgets.QApplication = get_qt_application()
    circuit: MultiCircuit = MultiCircuit()
    bus: Bus = Bus(name="Bus")
    circuit.add_bus(bus)
    source: Generator = Generator(name="Source")
    receiver: Generator = Generator(name="Receiver")
    circuit.add_generator(bus, source)
    circuit.add_generator(bus, receiver)
    state: Var = circuit.var_factory.add_var(name="shared_state")
    source.rms_model = Block(state_vars=list((state,)), state_eqs=list((Const(1.0),)))
    working: VarFactory = VarFactory()
    root: Block = Block(name="Receiver")
    # This is the parser-facing path: no graphics object is needed to create it.
    link: Block = add_interconnection_block(root, working, source, list((state,)), 50.0, 60.0)
    editor: DynamicBlockEditorGUI = DynamicBlockEditorGUI(
        var_factory=working, current_block=root, api_object=receiver, current_theme="Light",
        mode=DynamicSimulationMode.RMS, templates_list=list(), circuit=circuit,
        is_root_editor=False, modal=False)
    editor.rebuild_scene_from_diagram()
    items: list[graph.InterconnectionItem] = list(item for item in editor.scene.items()
                                                 if isinstance(item, graph.InterconnectionItem))
    assert len(items) == 1
    assert items[0].subsys is link
    assert len(items[0].outputs) == 1
    assert items[0].outputs[0].base_var.uid == state.uid
    assert items[0].scenePos().x() == 50.0
    # Copy/paste keeps the external UID while assigning a fresh block identity.
    items[0].setSelected(True)
    editor.copy_selected_blocks()
    editor.paste_copied_blocks()
    copied: list[graph.InterconnectionItem] = list(item for item in editor.scene.items()
                                                  if isinstance(item, graph.InterconnectionItem))
    assert len(copied) == 2
    assert all(item.outputs[0].base_var.uid == state.uid for item in copied)
    # The drag/drop dispatch also creates the specialized class and diagram type.
    provisional: object = editor.create_library_payload_item(BlockType.INTERCONNECTION, 200.0, 300.0)
    assert isinstance(provisional, graph.InterconnectionItem)
    assert provisional.subsys is not None
    assert editor.diagram.node_data[provisional.subsys.uid].tpe == BlockType.INTERCONNECTION.name
    editor.has_unapplied_changes = False
    editor.close()
    application.processEvents()
