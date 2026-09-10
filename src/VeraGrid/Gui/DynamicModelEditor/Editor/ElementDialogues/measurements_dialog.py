# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.001--.0-
from __future__ import annotations

from typing import Dict, List, Tuple

from PySide6 import QtCore, QtGui, QtWidgets

from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.enumerations import BlockType, VarPowerFlowReferenceType


class MeasurementReferenceList(QtWidgets.QListWidget):
    """One direction list that accepts dragged measurement references."""

    __slots__ = ("_target_direction",)

    moveRequested = QtCore.Signal(object, int)

    def __init__(self,
                 target_direction: int,
                 parent: QtWidgets.QWidget | None = None) -> None:
        """Create one input or output reference list.

        :param target_direction: Zero for inputs or one for outputs.
        :param parent: Optional owning widget.
        :return: None.
        """
        super().__init__(parent)
        self._target_direction: int = target_direction
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(QtCore.Qt.DropAction.MoveAction)
        self.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

    def startDrag(self, supported_actions: QtCore.Qt.DropAction) -> None:
        """Start a drag carrying one typed measurement reference.

        :param supported_actions: Actions accepted by the initiating view.
        :return: None.
        """
        selected_items: List[QtWidgets.QListWidgetItem] = self.selectedItems()
        if len(selected_items) == 1:
            selected_item: QtWidgets.QListWidgetItem = selected_items[0]
            reference_data: object = selected_item.data(QtCore.Qt.ItemDataRole.UserRole)
            if isinstance(reference_data, VarPowerFlowReferenceType):
                mime_data: QtCore.QMimeData = QtCore.QMimeData()
                mime_data.setText(reference_data.name)
                drag: QtGui.QDrag = QtGui.QDrag(self)
                drag.setMimeData(mime_data)
                drag.exec(QtCore.Qt.DropAction.MoveAction)
            else:
                pass
        else:
            pass

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        """Accept drags containing one measurement-reference name.

        :param event: Incoming drag event.
        :return: None.
        """
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
        """Keep a valid measurement drag active over this direction list.

        :param event: Incoming drag-move event.
        :return: None.
        """
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        """Request moving the dropped reference into this list's direction.

        :param event: Incoming drop event.
        :return: None.
        """
        reference_name: str = event.mimeData().text()
        if reference_name in VarPowerFlowReferenceType.__members__:
            reference: VarPowerFlowReferenceType = VarPowerFlowReferenceType[reference_name]
            self.moveRequested.emit(reference, self._target_direction)
            event.acceptProposedAction()
        else:
            event.ignore()


class MeasurementsDialog(QtWidgets.QDialog):
    """Select one bus and configure the interface of one RMS measurement block."""

    __slots__ = (
        "_buses",
        "_measurement_vars_dict",
        "_active_measurement_vars_dict",
        "_bus_combo",
        "_measurement_tree",
        "_input_list",
        "_output_list",
        "_selected_block_type",
        "_input_references",
        "_output_references",
        "_updating_tree",
    )

    def __init__(self,
                 buses: List[Bus],
                 measurement_vars_dict: Dict[str, Dict[BlockType, List[VarPowerFlowReferenceType]]],
                 parent: QtWidgets.QWidget | None = None) -> None:
        """Build the measurement configuration dialog.

        :param buses: Buses available to the measurement block.
        :param measurement_vars_dict: Measurement types and references grouped by bus domain.
        :param parent: Optional owning widget.
        :return: None.
        """
        super().__init__(parent)
        self.setWindowTitle("Configure measurement block")
        self.resize(900, 560)

        self._buses: List[Bus] = list(buses)
        self._measurement_vars_dict: Dict[
            str,
            Dict[BlockType, List[VarPowerFlowReferenceType]],
        ] = dict()
        bus_domain: str
        domain_measurements: Dict[BlockType, List[VarPowerFlowReferenceType]]
        block_type: BlockType
        references: List[VarPowerFlowReferenceType]
        for bus_domain, domain_measurements in measurement_vars_dict.items():
            copied_domain_measurements: Dict[BlockType, List[VarPowerFlowReferenceType]] = dict()
            for block_type, references in domain_measurements.items():
                copied_domain_measurements[block_type] = list(references)
            self._measurement_vars_dict[bus_domain] = copied_domain_measurements
        self._active_measurement_vars_dict: Dict[
            BlockType,
            List[VarPowerFlowReferenceType],
        ] = dict()

        self._bus_combo: QtWidgets.QComboBox = QtWidgets.QComboBox(self)
        self._measurement_tree: QtWidgets.QTreeWidget = QtWidgets.QTreeWidget(self)
        self._input_list: MeasurementReferenceList = MeasurementReferenceList(0, self)
        self._output_list: MeasurementReferenceList = MeasurementReferenceList(1, self)
        self._selected_block_type: BlockType | None = None
        self._input_references: List[VarPowerFlowReferenceType] = list()
        self._output_references: List[VarPowerFlowReferenceType] = list()
        self._updating_tree: bool = False

        self._build_ui()
        self._populate_buses()
        self._connect_signals()
        self._refresh_direction_lists()
        self._set_measurement_configuration_enabled(False)

    def _build_ui(self) -> None:
        """Build the bus selector, measurement tree, direction lists, and buttons.

        :return: None.
        """
        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        bus_layout: QtWidgets.QFormLayout = QtWidgets.QFormLayout()
        # Keep the selector compact while leaving enough room for " BUS 0" and
        # the platform-specific drop-down indicator.
        self._bus_combo.setFixedWidth(140)
        self._bus_combo.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        bus_layout.addRow("Bus", self._bus_combo)
        main_layout.addLayout(bus_layout)

        content_widget: QtWidgets.QWidget = QtWidgets.QWidget(self)
        content_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout(content_widget)
        # Divide the available width equally and leave an actual blank gap
        # between the measurement tree and the combined direction area.
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(20)
        self._measurement_tree.setHeaderLabels(list(("Measurement variables",)))
        self._measurement_tree.setAlternatingRowColors(True)
        self._measurement_tree.setRootIsDecorated(True)
        self._measurement_tree.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
        )
        content_layout.addWidget(self._measurement_tree, 1)

        direction_widget: QtWidgets.QWidget = QtWidgets.QWidget(content_widget)
        direction_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout(direction_widget)
        # Remove only the container margin so the two direction groups start at
        # the same vertical position as the measurement-variable tree.
        direction_layout.setContentsMargins(0, 0, 0, 0)
        input_group: QtWidgets.QGroupBox = QtWidgets.QGroupBox("Inputs", direction_widget)
        input_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(input_group)
        input_layout.addWidget(self._input_list)
        output_group: QtWidgets.QGroupBox = QtWidgets.QGroupBox("Outputs", direction_widget)
        output_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(output_group)
        output_layout.addWidget(self._output_list)
        direction_layout.addWidget(input_group)
        direction_layout.addWidget(output_group)
        content_layout.addWidget(direction_widget, 1)
        main_layout.addWidget(content_widget, 1)

        explanation_label: QtWidgets.QLabel = QtWidgets.QLabel(
            "Check one measurement type, choose its variables, and drag variables between Outputs and Inputs.",
            self,
        )
        explanation_label.setWordWrap(True)
        main_layout.addWidget(explanation_label)

        buttons: QtWidgets.QDialogButtonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        buttons.accepted.connect(self.accept_dialog)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    def _populate_buses(self) -> None:
        """Populate the bus selector while retaining each concrete Bus object.

        :return: None.
        """
        # A data-less first entry forces an explicit user choice before the
        # bus-dependent measurement configuration can be created.
        self._bus_combo.addItem("Select bus...", None)
        bus: Bus
        for bus in self._buses:
            self._bus_combo.addItem(bus.name, bus)

    def _set_measurement_configuration_enabled(self, enabled: bool) -> None:
        """Enable or shade all controls that depend on the selected bus.

        :param enabled: Whether a concrete bus has been selected.
        :return: None.
        """
        self._measurement_tree.setEnabled(enabled)
        self._input_list.setEnabled(enabled)
        self._output_list.setEnabled(enabled)

    def _populate_measurement_tree(self) -> None:
        """Populate collapsed measurement keys and their checkable references.

        :return: None.
        """
        block_type: BlockType
        references: List[VarPowerFlowReferenceType]
        for block_type, references in self._active_measurement_vars_dict.items():
            parent_item: QtWidgets.QTreeWidgetItem = QtWidgets.QTreeWidgetItem(
                self._measurement_tree,
                list((block_type.name,)),
            )
            parent_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, block_type)
            parent_item.setFlags(
                parent_item.flags()
                | QtCore.Qt.ItemFlag.ItemIsUserCheckable
                | QtCore.Qt.ItemFlag.ItemIsSelectable
            )
            parent_item.setCheckState(0, QtCore.Qt.CheckState.Unchecked)

            reference: VarPowerFlowReferenceType
            for reference in references:
                child_item: QtWidgets.QTreeWidgetItem = QtWidgets.QTreeWidgetItem(
                    parent_item,
                    list((reference.name,)),
                )
                child_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, reference)
                child_item.setFlags(
                    child_item.flags()
                    | QtCore.Qt.ItemFlag.ItemIsUserCheckable
                    | QtCore.Qt.ItemFlag.ItemIsSelectable
                )
                child_item.setCheckState(0, QtCore.Qt.CheckState.Unchecked)
            parent_item.setExpanded(False)

    def _connect_signals(self) -> None:
        """Connect tree and drag-and-drop changes to the detached selection state.

        :return: None.
        """
        self._measurement_tree.itemChanged.connect(self.on_tree_item_changed)
        self._measurement_tree.itemClicked.connect(self.on_tree_item_clicked)
        self._input_list.moveRequested.connect(self.move_reference)
        self._output_list.moveRequested.connect(self.move_reference)
        self._bus_combo.currentIndexChanged.connect(self.on_bus_changed)

    @QtCore.Slot(int)
    def on_bus_changed(self, index: int) -> None:
        """Rebuild the available measurement types for the selected bus domain.

        :param index: Current bus-combo index.
        :return: None.
        """
        selected_bus: object = self._bus_combo.itemData(index)

        # Changing the physical bus invalidates every selection made for the
        # previous domain, even when both buses happen to share that domain.
        self._updating_tree = True
        self._measurement_tree.clear()
        self._selected_block_type = None
        self._input_references = list()
        self._output_references = list()
        self._active_measurement_vars_dict = dict()

        if isinstance(selected_bus, Bus):
            bus_domain: str
            if selected_bus.is_dc:
                bus_domain = "dc_bus"
            else:
                bus_domain = "a_c_bus"
            domain_measurements: Dict[BlockType, List[VarPowerFlowReferenceType]] | None = (
                self._measurement_vars_dict.get(bus_domain, None)
            )
            if domain_measurements is not None:
                block_type: BlockType
                references: List[VarPowerFlowReferenceType]
                for block_type, references in domain_measurements.items():
                    self._active_measurement_vars_dict[block_type] = list(references)
                self._populate_measurement_tree()
            else:
                pass
            self._set_measurement_configuration_enabled(True)
        else:
            self._set_measurement_configuration_enabled(False)

        self._updating_tree = False
        self._refresh_direction_lists()

    @QtCore.Slot(QtWidgets.QTreeWidgetItem, int)
    def on_tree_item_changed(self,
                             item: QtWidgets.QTreeWidgetItem,
                             column: int) -> None:
        """Apply exclusive key selection and individual reference selection.

        :param item: Tree item whose check state changed.
        :param column: Changed tree column.
        :return: None.
        """
        if self._updating_tree or column != 0:
            pass
        elif item.parent() is None:
            self._apply_key_check_change(item)
        else:
            self._apply_reference_check_change(item)

    def _apply_key_check_change(self, item: QtWidgets.QTreeWidgetItem) -> None:
        """Select at most one key and select all of its references by default.

        :param item: Changed top-level key item.
        :return: None.
        """
        block_type_data: object = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if not isinstance(block_type_data, BlockType):
            pass
        elif item.checkState(0) == QtCore.Qt.CheckState.Checked:
            self._updating_tree = True
            top_index: int
            for top_index in range(self._measurement_tree.topLevelItemCount()):
                candidate_item: QtWidgets.QTreeWidgetItem = self._measurement_tree.topLevelItem(top_index)
                if candidate_item is item:
                    pass
                else:
                    candidate_item.setCheckState(0, QtCore.Qt.CheckState.Unchecked)
                    candidate_child_index: int
                    for candidate_child_index in range(candidate_item.childCount()):
                        candidate_item.child(candidate_child_index).setCheckState(
                            0,
                            QtCore.Qt.CheckState.Unchecked,
                        )
            child_index: int
            for child_index in range(item.childCount()):
                item.child(child_index).setCheckState(0, QtCore.Qt.CheckState.Checked)
            self._updating_tree = False

            self._selected_block_type = block_type_data
            self._input_references = list()
            selected_references: List[VarPowerFlowReferenceType] | None = (
                self._active_measurement_vars_dict.get(block_type_data, None)
            )
            if selected_references is not None:
                self._output_references = list(selected_references)
            else:
                self._output_references = list()
            item.setExpanded(True)
            self._refresh_direction_lists()
        elif self._selected_block_type is block_type_data:
            # Keep the visual tree consistent with the inactive key by clearing
            # every child without processing each generated itemChanged signal.
            self._updating_tree = True
            child_index: int
            for child_index in range(item.childCount()):
                item.child(child_index).setCheckState(
                    0,
                    QtCore.Qt.CheckState.Unchecked,
                )
            self._updating_tree = False

            # Removing the active key invalidates both direction collections.
            self._selected_block_type = None
            self._input_references = list()
            self._output_references = list()
            self._refresh_direction_lists()
        else:
            pass

    def _apply_reference_check_change(self, item: QtWidgets.QTreeWidgetItem) -> None:
        """Add checked references to outputs and remove unchecked references.

        :param item: Changed child reference item.
        :return: None.
        """
        parent_item: QtWidgets.QTreeWidgetItem | None = item.parent()
        reference_data: object = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if parent_item is None or not isinstance(reference_data, VarPowerFlowReferenceType):
            pass
        else:
            parent_type_data: object = parent_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if parent_type_data is not self._selected_block_type:
                pass
            elif item.checkState(0) == QtCore.Qt.CheckState.Checked:
                if (reference_data not in self._input_references
                        and reference_data not in self._output_references):
                    self._output_references.append(reference_data)
                else:
                    pass
                self._refresh_direction_lists()
            else:
                if reference_data in self._input_references:
                    self._input_references.remove(reference_data)
                else:
                    pass
                if reference_data in self._output_references:
                    self._output_references.remove(reference_data)
                else:
                    pass
                self._refresh_direction_lists()

    @QtCore.Slot(QtWidgets.QTreeWidgetItem, int)
    def on_tree_item_clicked(self,
                             item: QtWidgets.QTreeWidgetItem,
                             column: int) -> None:
        """Expand a clicked measurement key so its references become visible.

        :param item: Clicked tree item.
        :param column: Clicked column.
        :return: None.
        """
        if item.parent() is None and column == 0:
            item.setExpanded(True)
        else:
            pass

    @QtCore.Slot(object, int)
    def move_reference(self,
                       reference_data: object,
                       target_direction: int) -> None:
        """Move one selected reference between the input and output collections.

        :param reference_data: Dragged measurement reference.
        :param target_direction: Zero for inputs or one for outputs.
        :return: None.
        """
        if not isinstance(reference_data, VarPowerFlowReferenceType):
            pass
        elif (reference_data not in self._input_references
              and reference_data not in self._output_references):
            pass
        elif target_direction == 0:
            if reference_data in self._output_references:
                self._output_references.remove(reference_data)
            else:
                pass
            if reference_data not in self._input_references:
                self._input_references.append(reference_data)
            else:
                pass
            self._refresh_direction_lists()
        elif target_direction == 1:
            if reference_data in self._input_references:
                self._input_references.remove(reference_data)
            else:
                pass
            if reference_data not in self._output_references:
                self._output_references.append(reference_data)
            else:
                pass
            self._refresh_direction_lists()
        else:
            pass

    def _refresh_direction_lists(self) -> None:
        """Render selected references in the input and output list widgets.

        :return: None.
        """
        self._input_list.clear()
        self._output_list.clear()
        reference: VarPowerFlowReferenceType
        for reference in self._input_references:
            self._add_direction_item(self._input_list, reference)
        for reference in self._output_references:
            self._add_direction_item(self._output_list, reference)

    def _add_direction_item(self,
                            destination_list: MeasurementReferenceList,
                            reference: VarPowerFlowReferenceType) -> None:
        """Insert one draggable typed reference in a direction list.

        :param destination_list: Input or output list receiving the item.
        :param reference: Measurement reference represented by the item.
        :return: None.
        """
        list_item: QtWidgets.QListWidgetItem = QtWidgets.QListWidgetItem(reference.name)
        list_item.setData(QtCore.Qt.ItemDataRole.UserRole, reference)
        list_item.setFlags(
            QtCore.Qt.ItemFlag.ItemIsEnabled
            | QtCore.Qt.ItemFlag.ItemIsSelectable
            | QtCore.Qt.ItemFlag.ItemIsDragEnabled
        )
        destination_list.addItem(list_item)

    def accept_dialog(self) -> None:
        """Accept the dialog only when a bus and one measurement key are selected.

        :return: None.
        """
        selected_bus: object = self._bus_combo.currentData()
        if not isinstance(selected_bus, Bus):
            QtWidgets.QMessageBox.warning(self, "Measurement block", "Select one bus.")
        elif self._selected_block_type is None:
            QtWidgets.QMessageBox.warning(self, "Measurement block", "Select one measurement type.")
        else:
            self.accept()

    def get_user_info(
            self,
    ) -> Tuple[
        Bus,
        BlockType,
        List[VarPowerFlowReferenceType],
        List[VarPowerFlowReferenceType],
    ]:
        """Return the selected bus, block type, and detached reference lists.

        :return: Selected bus, block type, input references, and output references.
        :raises RuntimeError: If queried before a complete selection exists.
        """
        selected_bus: object = self._bus_combo.currentData()
        if isinstance(selected_bus, Bus) and self._selected_block_type is not None:
            return (
                selected_bus,
                self._selected_block_type,
                list(self._input_references),
                list(self._output_references),
            )
        else:
            raise RuntimeError("Measurement dialog has no complete selection")
