from __future__ import annotations

import sys
from typing import Dict, List

from PySide6 import QtCore, QtWidgets

from VeraGrid.Gui.DynamicModelEditor.Editor.ElementDialogues.MeasurementsDialog.measurements_dialog import MeasurementsDialog
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.enumerations import BlockType, VarPowerFlowReferenceType


def get_qt_application() -> QtWidgets.QApplication:
    """Return the shared Qt application used by the dialog tests.

    :return: Existing or newly created Qt application.
    """
    application: QtWidgets.QApplication | None = QtWidgets.QApplication.instance()
    if application is None:
        return QtWidgets.QApplication(sys.argv)
    else:
        return application


def test_measurements_dialog_uses_selected_bus_from_clickable_label() -> None:
    """A selected bus must update the label and measurement configuration.

    :return: None.
    """
    _unused_application: QtWidgets.QApplication = get_qt_application()
    bus: Bus = Bus(name="Selected bus")
    ac_measurements: Dict[BlockType, List[VarPowerFlowReferenceType]] = dict()
    ac_measurements[BlockType.MEASUREMENTS_VOLTAGE_ANGLE] = list((
        VarPowerFlowReferenceType.Vm,
    ))
    measurements: Dict[str, Dict[BlockType, List[VarPowerFlowReferenceType]]] = dict()
    measurements["a_c_bus"] = ac_measurements
    dialog: MeasurementsDialog = MeasurementsDialog(
        buses=list((bus,)),
        measurement_vars_dict=measurements,
    )

    assert dialog._selected_bus is None
    assert dialog.ui.bus_label.text() == "Select bus..."
    assert not dialog.ui.measurement_tree.isEnabled()

    dialog.set_selected_bus(bus)

    assert dialog._selected_bus is bus
    assert dialog.ui.bus_label.text() == "Selected bus"
    assert dialog.ui.measurement_tree.isEnabled()
    assert dialog.ui.measurement_tree.topLevelItemCount() == 1
    measurement_item: QtWidgets.QTreeWidgetItem = dialog.ui.measurement_tree.topLevelItem(0)
    measurement_item.setCheckState(0, QtCore.Qt.CheckState.Checked)
    selected_bus: Bus
    selected_type: BlockType
    inputs: List[VarPowerFlowReferenceType]
    outputs: List[VarPowerFlowReferenceType]
    selected_bus, selected_type, inputs, outputs = dialog.get_user_info()
    assert selected_bus is bus
    assert selected_type == BlockType.MEASUREMENTS_VOLTAGE_ANGLE
    assert inputs == list()
    assert outputs == list((VarPowerFlowReferenceType.Vm,))
    dialog.close()
