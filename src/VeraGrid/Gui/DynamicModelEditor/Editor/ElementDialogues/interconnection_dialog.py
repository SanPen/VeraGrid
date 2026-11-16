"""Select source devices and variables for an RMS interconnection item."""
from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from VeraGrid.Gui.dialog_lifecycle import exec_dialog_safely
from VeraGrid.Gui.general_dialogues import DeviceSelectorDialogue
from VeraGridEngine.Devices.Dynamic.model_interconnections import get_interconnection_variables
from VeraGridEngine.Devices.Parents.dynamic_parent import DynamicDevice
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.enumerations import DeviceType


class InterconnectionDialog(QtWidgets.QDialog):
    """Configure read-only output ports referencing another device's RMS model."""

    __slots__ = ("_devices", "_selected_device", "_choices", "_device_button", "_tree", "_initial_variables")

    def __init__(self, devices: list[DynamicDevice], initial_device_id: str = "",
                 initial_variables: list[Var] | None = None,
                 parent: QtWidgets.QWidget | None = None) -> None:
        """Build the source selector and checkable variable tree.

        :param devices: Available source devices, excluding the receiving device.
        :param initial_device_id: Device identifier persisted in the diagram.
        :param initial_variables: Previously selected output variables.
        :param parent: Dialog parent.
        :return: None.
        """
        super().__init__(parent)
        self.setWindowTitle("Interconnection")
        self.resize(650, 500)
        self._devices: list[DynamicDevice] = devices
        self._selected_device: DynamicDevice | None = None
        self._choices: list[Var] = list()
        self._initial_variables: list[Var] = list() if initial_variables is None else initial_variables
        layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        self._device_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Select source device…", self)
        self._device_button.clicked.connect(self.select_device)
        layout.addWidget(self._device_button)
        self._tree: QtWidgets.QTreeWidget = QtWidgets.QTreeWidget(self)
        self._tree.setHeaderLabels(list(("Source variable",)))
        layout.addWidget(self._tree)
        buttons: QtWidgets.QDialogButtonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        # Recover configuration using persistent device identity, never a label.
        device: DynamicDevice
        for device in devices:
            if device.idtag == initial_device_id:
                self.set_selected_device(device)
            else:
                pass

    def select_device(self) -> None:
        """Open the same grouped searchable device selector used by measurements.

        :return: None.
        """
        grouped: dict[DeviceType, list] = dict()
        device: DynamicDevice
        for device in self._devices:
            if device.device_type not in grouped:
                grouped[device.device_type] = list()
            else:
                pass
            grouped[device.device_type].append(device)
        selector: DeviceSelectorDialogue = DeviceSelectorDialogue(devices_by_type=grouped, allow_none=False, parent=self)
        if exec_dialog_safely(selector) == QtWidgets.QDialog.DialogCode.Accepted:
            selected: object = selector.get_selected_device()
            if isinstance(selected, DynamicDevice):
                self.set_selected_device(selected)
            else:
                pass
        else:
            pass

    def set_selected_device(self, device: DynamicDevice) -> None:
        """Display source variables and restore surviving selections.

        :param device: Authoritative circuit device.
        :return: None.
        """
        choices: list[Var] = get_interconnection_variables(device)
        self._selected_device = device
        self._choices = choices
        self._device_button.setText(f"{device.name} ({device.device_type.value})")
        self._tree.clear()
        selected: set[int] = set(variable.uid for variable in self._initial_variables)
        # Group labels by their symbolic owner so repeated variable names remain
        # distinguishable without displaying implementation identifiers.
        labels: dict[int, str] = dict()
        block: Block
        for block in device.rms_model.get_all_blocks():
            collection: list[Var]
            for collection in (block.state_vars, block.algebraic_vars, block.diff_vars,
                               list(block.parameters), list(block.event_dict), list(block.mode_dict),
                               block.in_vars, block.out_vars):
                variable: Var
                for variable in collection:
                    labels[variable.non_mutable_uid] = f"{block.name}/{variable.name}"
        choice: Var
        index: int
        for index, choice in enumerate(choices):
            row: QtWidgets.QTreeWidgetItem = QtWidgets.QTreeWidgetItem(self._tree, list((labels[choice.non_mutable_uid],)))
            row.setData(0, QtCore.Qt.ItemDataRole.UserRole, index)
            row.setFlags(row.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            row.setCheckState(0, QtCore.Qt.CheckState.Checked if choice.uid in selected else QtCore.Qt.CheckState.Unchecked)

    def get_variables(self) -> list[Var]:
        """Collect selected source variables in their visible port order.

        :return: Selected source variables.
        """
        result: list[Var] = list()
        index: int
        for index in range(self._tree.topLevelItemCount()):
            row: QtWidgets.QTreeWidgetItem = self._tree.topLevelItem(index)
            if row.checkState(0) == QtCore.Qt.CheckState.Checked:
                choice_index: int = row.data(0, QtCore.Qt.ItemDataRole.UserRole)
                result.append(self._choices[choice_index])
            else:
                pass
        return result

    def get_selected_device(self) -> DynamicDevice | None:
        """Return the selected circuit device.

        :return: Selected device, or None before configuration.
        """
        return self._selected_device

    def accept(self) -> None:
        """Require a concrete device and at least one selected variable.

        :return: None.
        """
        if self._selected_device is None or len(self.get_variables()) == 0:
            QtWidgets.QMessageBox.warning(self, "Interconnection", "Select a source device and at least one variable.")
        else:
            super().accept()
