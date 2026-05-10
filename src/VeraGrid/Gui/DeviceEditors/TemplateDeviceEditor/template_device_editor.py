# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import sys
import re
from enum import EnumMeta
from typing import Any, Sequence
import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets
from VeraGrid.Gui.associations_model import AssociationsModel
from VeraGrid.Gui.DeviceEditors.TemplateDeviceEditor.template_device_editor_gui import Ui_TemplateDeviceEditorDialog
from VeraGrid.Gui.gui_functions import ComboDelegate, FloatDelegate, IntDelegate, TextDelegate, ComplexDelegate
from VeraGrid.Gui.Widgets.matplotlibwidget import MatplotlibWidget
from VeraGrid.Gui.messages import warning_msg
from VeraGrid.Gui.object_model import ObjectsModel
from VeraGrid.Gui.table_view_header_wrap import HeaderViewWithWordWrap
import VeraGrid.Gui.gui_functions as gf
from VeraGridEngine.Devices.Associations.association import Associations
from VeraGridEngine.Devices.Parents.editable_device import EditableDevice, GCProp
from VeraGridEngine.Devices.Profiles import AnyProfile
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.enumerations import DeviceType, PrpCat



def parse_profile_cell_value(value: Any, tpe: type) -> tuple[bool, object]:
    """
    Parse an edited profile cell value according to the profile data type.

    :param value: Raw value received from the Qt delegate.
    :param tpe: Declared property type.
    :return: ``(ok, parsed_value)``.
    """
    if tpe is bool:
        if isinstance(value, bool):
            return True, value
        else:
            value_text: str = str(value).strip().lower()
            if value_text in ["1", "true", "yes", "y", "t"]:
                return True, True
            elif value_text in ["0", "false", "no", "n", "f"]:
                return True, False
            else:
                return False, value
    elif tpe is float:
        try:
            return True, float(value)
        except (TypeError, ValueError):
            return False, value
    elif tpe is int:
        try:
            return True, int(value)
        except (TypeError, ValueError):
            return False, value
    elif tpe is str:
        return True, str(value)
    elif isinstance(tpe, EnumMeta):
        if isinstance(value, tpe):
            return True, value
        else:
            value_text = str(value)
            try:
                return True, tpe(value_text)
            except (ValueError, TypeError):
                try:
                    return True, tpe[value_text]
                except (KeyError, TypeError):
                    return False, value
    else:
        return True, value


class MultiFormatProfilesTableModel(QtCore.QAbstractTableModel):
    """
    Profile table model for a single device with mixed column data formats.
    """

    def __init__(self,
                 device: EditableDevice,
                 profile_properties: list[GCProp],
                 time_labels: list[str],
                 parent: QtCore.QObject | None = None) -> None:
        """
        Build the profile table model.

        :param device: Edited device object.
        :param profile_properties: Properties that have an associated profile.
        :param time_labels: Row labels shown as profile time axis.
        :param parent: Qt parent object.
        """
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.device: EditableDevice = device
        self.profile_properties: list[GCProp] = profile_properties
        self.time_labels: list[str] = time_labels
        self._profiles: list[AnyProfile] = [self.device.get_profile_by_prop(prop=prop) for prop in self.profile_properties]

        # Keep all profile columns aligned to the same number of time rows.
        self._normalize_profile_lengths()

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        """
        Return profile row count.

        :param parent: Unused parent index.
        :return: Number of rows.
        """
        _ = parent
        return len(self.time_labels)

    def columnCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        """
        Return profile column count.

        :param parent: Unused parent index.
        :return: Number of columns.
        """
        _ = parent
        return len(self.profile_properties)

    def data(self,
             index: QtCore.QModelIndex,
             role: int = int(QtCore.Qt.ItemDataRole.DisplayRole)) -> str | None:
        """
        Return profile cell text for display and edition.

        :param index: Cell index.
        :param role: Qt data role.
        :return: Cell string or ``None``.
        """
        if index.isValid():
            if role == int(QtCore.Qt.ItemDataRole.DisplayRole) or role == int(QtCore.Qt.ItemDataRole.EditRole):
                profile: AnyProfile = self._profiles[index.column()]
                row_index: int = index.row()
                if row_index < profile.size():
                    value: object = profile[row_index]
                    return str(value)
                else:
                    return ""
            else:
                return None
        else:
            return None

    def setData(self,
                index: QtCore.QModelIndex,
                value: object,
                role: int = int(QtCore.Qt.ItemDataRole.EditRole)) -> bool:
        """
        Set profile cell value with per-column type parsing.

        :param index: Cell index.
        :param value: New value.
        :param role: Qt data role.
        :return: True when the assignment succeeds.
        """
        if index.isValid():
            if role == int(QtCore.Qt.ItemDataRole.EditRole):
                prop: GCProp = self.profile_properties[index.column()]
                profile: AnyProfile = self._profiles[index.column()]
                row_index: int = index.row()
                if row_index < profile.size():
                    ok: bool
                    parsed_value: object
                    ok, parsed_value = parse_profile_cell_value(value=value, tpe=prop.tpe)
                    if ok:
                        profile[row_index] = parsed_value
                        self.dataChanged.emit(index, index, [int(QtCore.Qt.ItemDataRole.DisplayRole)])
                        return True
                    else:
                        return False
                else:
                    return False
            else:
                return False
        else:
            return False

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlag:
        """
        Return item flags for editable profile cells.

        :param index: Cell index.
        :return: Qt item flags.
        """
        if index.isValid():
            return (QtCore.Qt.ItemFlag.ItemIsEnabled
                    | QtCore.Qt.ItemFlag.ItemIsEditable
                    | QtCore.Qt.ItemFlag.ItemIsSelectable)
        else:
            return QtCore.Qt.ItemFlag.NoItemFlags

    def headerData(self,
                   section: int,
                   orientation: QtCore.Qt.Orientation,
                   role: int = int(QtCore.Qt.ItemDataRole.DisplayRole)) -> str | None:
        """
        Return horizontal and vertical header labels.

        :param section: Header section.
        :param orientation: Header orientation.
        :param role: Qt data role.
        :return: Header text or ``None``.
        """
        if role == int(QtCore.Qt.ItemDataRole.DisplayRole):
            if orientation == QtCore.Qt.Orientation.Horizontal:
                if section < len(self.profile_properties):
                    prop: GCProp = self.profile_properties[section]
                    if prop.units != "":
                        return f"{prop.name} [{prop.units}]"
                    else:
                        return prop.name
                else:
                    return ""
            else:
                if section < len(self.time_labels):
                    return self.time_labels[section]
                else:
                    return ""
        else:
            return None

    def get_column_type(self, column_index: int) -> type:
        """
        Get the declared property type of one profile column.

        :param column_index: Profile column index.
        :return: Declared python type.
        """
        return self.profile_properties[column_index].tpe

    def get_profile_properties(self) -> list[GCProp]:
        """
        Get the profile property definitions shown by this model.

        :return: Profile property list.
        """
        return self.profile_properties

    def _normalize_profile_lengths(self) -> None:
        """
        Enforce equal profile length for all displayed profile properties.
        """
        target_rows: int = len(self.time_labels)
        if target_rows > 0:
            for profile in self._profiles:
                current_rows: int = profile.size()
                if current_rows != target_rows:
                    profile.resize(target_rows)
        else:
            pass


class TemplateDeviceEditor(QtWidgets.QDialog):
    """
    Base editor dialog with common snapshot/profile and full profile-table tabs.
    """

    def __init__(self, api_object: EditableDevice, circuit: MultiCircuit | None = None) -> None:
        """
        Build the base template editor.

        :param api_object: Device edited in place.
        :param circuit: Optional circuit for delegates and time axis labels.
        """
        QtWidgets.QDialog.__init__(self)
        self.api_object: EditableDevice = api_object
        self.circuit: MultiCircuit | None = circuit
        self.delegate_dictionary: dict[object, list[object]] = self._build_delegate_dictionary()

        # Load UI from Qt Designer definition.
        self.ui = Ui_TemplateDeviceEditorDialog()
        self.ui.setupUi(self)
        self.setWindowTitle("Device editor")

        self.prop_filter_dict, prop_filter_mdl = gf.enums_to_icons_model(
            [
                (PrpCat.All,":/Icons/icons/edit.png"),
                (PrpCat.TP,":/Icons/icons/automatic_layout.png"),
                (PrpCat.PF,":/Icons/icons/pf.png"),
                (PrpCat.PF3,":/Icons/icons/pf3.png"),
                (PrpCat.SC,":/Icons/icons/short_circuit.png"),
                (PrpCat.OPF,":/Icons/icons/dcopf.png"),
                (PrpCat.CON,":/Icons/icons/otdf.png"),
                (PrpCat.REL,":/Icons/icons/reliability.png"),
                (PrpCat.NTC,":/Icons/icons/ntc_opf.png"),
                (PrpCat.INV,":/Icons/icons/expansion_planning.png"),
                (PrpCat.RMS,":/Icons/icons/dyn.png"),
                (PrpCat.EMT,":/Icons/icons/dyn_emt.png"),
            ]
        )
        self.ui.filterComboBox.setModel(prop_filter_mdl)

        # Keep explicit references to the relevant widgets used by the controller.
        self.tab_widget: QtWidgets.QTabWidget = self.ui.tab_widget

        self.properties_tab: QtWidgets.QWidget = self.ui.properties_tab
        self.properties_layout: QtWidgets.QVBoxLayout = self.ui.properties_layout
        self.time_controls_frame: QtWidgets.QFrame = self.ui.time_controls_frame
        self.time_controls_layout: QtWidgets.QHBoxLayout = self.ui.time_controls_layout
        self.time_step_title_label: QtWidgets.QLabel = self.ui.time_step_title_label
        self.time_step_slider: QtWidgets.QSlider = self.ui.time_step_slider
        self.time_step_label: QtWidgets.QLabel = self.ui.time_step_label
        self.properties_table_view: QtWidgets.QTableView = self.ui.properties_table_view

        self.profiles_tab: QtWidgets.QWidget = self.ui.profiles_tab
        self.profiles_layout: QtWidgets.QVBoxLayout = self.ui.profiles_layout
        self.profiles_tools_frame: QtWidgets.QFrame = self.ui.profiles_tools_frame
        self.profiles_tools_layout: QtWidgets.QHBoxLayout = self.ui.profiles_tools_layout
        self.profiles_copy_button: QtWidgets.QPushButton = self.ui.profiles_copy_button
        self.profiles_paste_button: QtWidgets.QPushButton = self.ui.profiles_paste_button
        self.profiles_plot_selected_button: QtWidgets.QPushButton = self.ui.profiles_plot_selected_button
        self.profiles_table_view: QtWidgets.QTableView = self.ui.profiles_table_view

        self.associations_tab: QtWidgets.QWidget = self.ui.associations_tab
        self.associations_layout: QtWidgets.QVBoxLayout = self.ui.associations_layout
        self.associations_controls_frame: QtWidgets.QFrame = self.ui.associations_controls_frame
        self.associations_controls_layout: QtWidgets.QHBoxLayout = self.ui.associations_controls_layout
        self.associations_property_label: QtWidgets.QLabel = self.ui.associations_property_label
        self.associations_combo_box: QtWidgets.QComboBox = self.ui.associations_combo_box
        self.associations_units_title_label: QtWidgets.QLabel = self.ui.associations_units_title_label
        self.associations_units_value_label: QtWidgets.QLabel = self.ui.associations_units_value_label
        self.associations_table_view: QtWidgets.QTableView = self.ui.associations_table_view

        # UI post-configuration.
        self.properties_table_view.setAlternatingRowColors(True)
        self.profiles_table_view.setAlternatingRowColors(True)
        self.profiles_table_view.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectItems)
        self.profiles_table_view.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.associations_table_view.setAlternatingRowColors(True)
        self.associations_table_view.setHorizontalHeader(HeaderViewWithWordWrap(self.associations_table_view))

        self.profiles_copy_button.setIcon(QtGui.QIcon(":/Icons/icons/copy.png"))
        self.profiles_paste_button.setIcon(QtGui.QIcon(":/Icons/icons/paste.png"))
        self.profiles_plot_selected_button.setIcon(QtGui.QIcon(":/Icons/icons/plot.png"))
        self.profiles_copy_button.setToolTip("Copy selected profile cells (Ctrl+C)")
        self.profiles_paste_button.setToolTip("Paste tabular clipboard data at selection anchor (Ctrl+V)")
        self.profiles_plot_selected_button.setToolTip("Plot selected profile columns grouped by units")
        self.profiles_copy_button.setText("")
        self.profiles_paste_button.setText("")
        self.profiles_plot_selected_button.setText("")

        # Build and bind the snapshot/time-step table model.
        self.properties_model: ObjectsModel = self.build_properties_model()
        self.properties_table_view.setModel(self.properties_model)
        self.properties_table_view.horizontalHeader().setStretchLastSection(True)
        self.properties_table_view.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.properties_table_view.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        # Build and bind the multi-format profile editor table model.
        self.profile_properties: list[GCProp] = self._get_profile_properties()
        self.time_labels: list[str] = self._build_time_labels()
        self.profiles_model: MultiFormatProfilesTableModel = MultiFormatProfilesTableModel(
            device=self.api_object,
            profile_properties=self.profile_properties,
            time_labels=self.time_labels,
            parent=self.profiles_table_view,
        )
        self.profiles_table_view.setModel(self.profiles_model)
        self.profiles_table_view.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
        self.profiles_table_view.horizontalHeader().setStretchLastSection(True)
        self.profiles_table_view.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.profiles_table_view.verticalHeader().setDefaultSectionSize(self.fontMetrics().height() + 8)
        self._configure_profiles_table_delegates()

        # Build associations controls and model.
        self.association_properties: list[GCProp] = self._get_association_properties()
        self.associations_model: AssociationsModel | None = None
        self._populate_associations_combo_box()

        # Configure and connect the slider and dialog actions.
        n_time_steps: int = self._get_available_time_steps()
        if n_time_steps > 0:
            self.time_step_slider.setRange(-1, n_time_steps - 1)
        else:
            self.time_step_slider.setRange(-1, -1)
        self.time_step_slider.setValue(-1)

        self.time_step_slider.valueChanged.connect(self.on_time_step_changed)
        self.profiles_copy_button.clicked.connect(self.copy_profiles_selection_to_clipboard)
        self.profiles_paste_button.clicked.connect(self.paste_profiles_from_clipboard)
        self.profiles_plot_selected_button.clicked.connect(self.plot_selected_profiles_grouped_by_units)
        self.associations_combo_box.currentTextChanged.connect(self.on_association_property_changed)

        self.ui.filterComboBox.currentIndexChanged.connect(self.refresh_model)

        self.profiles_shortcuts: list[QtGui.QShortcut] = list()
        self._install_profiles_shortcuts()

        self._update_time_label(slider_index=self.time_step_slider.value())
        self.refresh_associations_table()

    def _build_delegate_dictionary(self) -> dict[DeviceType, list[object]]:
        """
        Build the dictionary used by foreign-key delegates in ``ObjectsModel``.

        :return: Delegate dictionary.
        """
        if self.circuit is not None:
            _, dictionary_of_lists = self.circuit.get_dictionary_of_lists(elm_type=self.api_object.device_type)
            return dictionary_of_lists
        else:
            return dict()

    def build_properties_model(self) -> ObjectsModel:
        """
        Build the snapshot/time-step properties model.

        :return: Configured ``ObjectsModel``.
        """
        property_list: list[GCProp] = list(self.api_object.property_list)
        filter_prop = self.prop_filter_dict[self.ui.filterComboBox.currentText()]
        model: ObjectsModel = ObjectsModel(
            objects=[self.api_object],
            property_list=property_list,
            time_index=None,
            parent=self.properties_table_view,
            editable=True,
            transposed=True,
            dictionary_of_lists=self.delegate_dictionary,
            properties_filter=filter_prop
        )

        return model

    def refresh_model(self):
        """
        Function to call when the filter changes
        """
        self.properties_model: ObjectsModel = self.build_properties_model()
        self.properties_table_view.setModel(self.properties_model)
        self.properties_table_view.horizontalHeader().setStretchLastSection(True)
        self.properties_table_view.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.properties_table_view.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

    def _get_profile_properties(self) -> list[GCProp]:
        """
        Get ordered property list that has profile backing values.

        :return: Profile-enabled property list.
        """
        profile_properties: list[GCProp] = list()
        for prop in self.api_object.property_list:
            if prop.has_profile():
                profile_properties.append(prop)
            else:
                pass
        return profile_properties

    def _get_association_properties(self) -> list[GCProp]:
        """
        Get ordered property list that stores associations.

        :return: Association property list.
        """
        assoc_props: list[GCProp]
        assoc_indices: list[int]
        assoc_props, assoc_indices = self.api_object.get_association_properties()
        _ = assoc_indices
        return list(assoc_props)

    def _populate_associations_combo_box(self) -> None:
        """
        Fill the associations property selector combo-box.
        """
        self.associations_combo_box.blockSignals(True)
        self.associations_combo_box.clear()

        if len(self.association_properties) > 0:
            association_prop: GCProp
            for association_prop in self.association_properties:
                self.associations_combo_box.addItem(association_prop.name)
        else:
            pass

        self.associations_combo_box.blockSignals(False)

    def _get_selected_association_property(self) -> GCProp | None:
        """
        Get the currently selected association property.

        :return: Selected property or ``None``.
        """
        selected_name: str = self.associations_combo_box.currentText()
        if selected_name != "":
            return self.api_object.get_property_by_name(prop_name=selected_name)
        else:
            return None

    def _get_associated_objects_for_property(self, prop: GCProp) -> list[object]:
        """
        Resolve the available associated objects for one association property.

        :param prop: Association property.
        :return: Compatible associated objects.
        """
        if self.circuit is not None:
            associations_obj: object = self.api_object.get_snapshot_value(prop=prop)
            if isinstance(associations_obj, Associations):
                return list(self.circuit.get_elements_by_type(device_type=associations_obj.device_type))
            else:
                return list()
        else:
            return list()

    def on_association_property_changed(self, association_property_name: str) -> None:
        """
        Handle association-property selection changes.

        :param association_property_name: Selected association property name.
        """
        _ = association_property_name
        self.refresh_associations_table()

    def refresh_associations_table(self) -> None:
        """
        Rebuild the associations model for the selected association property.
        """
        selected_prop: GCProp | None = self._get_selected_association_property()

        if selected_prop is not None:
            self.associations_units_value_label.setText(selected_prop.units)
            associated_objects: list[object] = self._get_associated_objects_for_property(prop=selected_prop)
            if len(associated_objects) > 0:
                self.associations_model = AssociationsModel(
                    objects=[self.api_object],
                    associated_objects=associated_objects,
                    gc_prop=selected_prop,
                    table_view=self.associations_table_view,
                )
                self.associations_table_view.setModel(self.associations_model)
                self.associations_model.set_delegates()
                self.associations_table_view.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
                self.associations_table_view.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
            else:
                self.associations_model = None
                self.associations_table_view.setModel(None)
        else:
            self.associations_units_value_label.setText("")
            self.associations_model = None
            self.associations_table_view.setModel(None)

        if self.circuit is not None and len(self.association_properties) > 0:
            self.associations_combo_box.setEnabled(True)
        else:
            self.associations_combo_box.setEnabled(False)

    def _get_available_time_steps(self) -> int:
        """
        Compute the available time-step count for profile-aware editing.

        :return: Number of time steps.
        """
        if self.circuit is not None and self.circuit.time_profile is not None:
            return len(self.circuit.time_profile)
        else:
            max_profile_size: int = 0
            for prop in self.profile_properties:
                profile: AnyProfile = self.api_object.get_profile_by_prop(prop=prop)
                profile_size: int = profile.size()
                if profile_size > max_profile_size:
                    max_profile_size = profile_size
                else:
                    pass
            return max_profile_size

    def _build_time_labels(self) -> list[str]:
        """
        Build profile row labels.

        :return: Time labels.
        """
        if self.circuit is not None and self.circuit.time_profile is not None:
            labels: list[str] = [str(value) for value in self.circuit.time_profile]
            return labels
        else:
            count: int = self._get_available_time_steps()
            labels = [str(i) for i in range(count)]
            return labels

    def _get_current_time_index(self) -> int | None:
        """
        Convert slider value into the profile index convention.

        :return: ``None`` for snapshot, integer for one profile row.
        """
        slider_index: int = int(self.time_step_slider.value())
        if slider_index < 0:
            return None
        else:
            return slider_index

    def _update_time_label(self, slider_index: int) -> None:
        """
        Update slider label text.

        :param slider_index: Current slider value.
        """
        if slider_index < 0:
            if self.circuit is not None:
                snapshot_label: str = f"Snapshot [{self.circuit.get_snapshot_time_str()}]"
            else:
                snapshot_label = "Snapshot"
            self.time_step_label.setText(snapshot_label)
        else:
            if self.circuit is not None and self.circuit.time_profile is not None and slider_index < len(self.circuit.time_profile):
                label_text: str = f"[{slider_index}] {self.circuit.time_profile[slider_index]}"
            else:
                label_text = f"[{slider_index}]"
            self.time_step_label.setText(label_text)

    def _configure_profiles_table_delegates(self) -> None:
        """
        Configure per-column delegates on the profile table.
        """
        column_index: int
        for column_index, prop in enumerate(self.profiles_model.get_profile_properties()):
            if prop.tpe is bool:
                delegate: ComboDelegate = ComboDelegate(self.profiles_table_view, [True, False], ["True", "False"])
                self.profiles_table_view.setItemDelegateForColumn(column_index, delegate)
            elif prop.tpe is float:
                float_delegate: FloatDelegate = FloatDelegate(self.profiles_table_view)
                self.profiles_table_view.setItemDelegateForColumn(column_index, float_delegate)
            elif prop.tpe is int:
                int_delegate: IntDelegate = IntDelegate(self.profiles_table_view)
                self.profiles_table_view.setItemDelegateForColumn(column_index, int_delegate)
            elif prop.tpe is str:
                text_delegate: TextDelegate = TextDelegate(self.profiles_table_view)
                self.profiles_table_view.setItemDelegateForColumn(column_index, text_delegate)
            elif prop.tpe is complex:
                complex_delegate: ComplexDelegate = ComplexDelegate(self.profiles_table_view)
                self.profiles_table_view.setItemDelegateForColumn(column_index, complex_delegate)
            elif isinstance(prop.tpe, EnumMeta):
                enum_objects: list[object] = list(prop.tpe)
                enum_names: list[str] = [enum_obj.value for enum_obj in enum_objects]
                enum_delegate: ComboDelegate = ComboDelegate(self.profiles_table_view, enum_objects, enum_names)
                self.profiles_table_view.setItemDelegateForColumn(column_index, enum_delegate)
            else:
                delegate_objects: list[object] | None = self._get_profile_delegate_objects(prop=prop)
                if delegate_objects is not None:
                    names: list[str] = ["None"] + [obj.name for obj in delegate_objects]
                    objects: list[object | None] = [None] + delegate_objects
                    fk_delegate: ComboDelegate = ComboDelegate(
                        parent=self.profiles_table_view,
                        objects=objects,
                        object_names=names,
                    )
                    self.profiles_table_view.setItemDelegateForColumn(column_index, fk_delegate)
                else:
                    self.profiles_table_view.setItemDelegateForColumn(column_index, None)

    def _get_profile_delegate_objects(self, prop: GCProp) -> list[object] | None:
        """
        Return the object list used by one profile foreign-key delegate.

        Resolution order mirrors ``ObjectsModel``:
        ``(prop.name, prop.tpe)`` -> ``prop.name`` -> ``prop.tpe``.
        """
        specific_key: tuple[str, type] = (prop.name, prop.tpe)
        if specific_key in self.delegate_dictionary:
            return self.delegate_dictionary[specific_key]
        elif prop.name in self.delegate_dictionary:
            return self.delegate_dictionary[prop.name]
        elif prop.tpe in self.delegate_dictionary:
            return self.delegate_dictionary[prop.tpe]
        else:
            return None

    def _install_profiles_shortcuts(self) -> None:
        """
        Install profile-tab shortcuts for spreadsheet-style edition.
        """
        copy_shortcut: QtGui.QShortcut = QtGui.QShortcut(QtGui.QKeySequence.StandardKey.Copy, self.profiles_tab)
        copy_shortcut.setContext(QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        copy_shortcut.activated.connect(self.copy_profiles_selection_to_clipboard)
        self.profiles_shortcuts.append(copy_shortcut)

        paste_shortcut: QtGui.QShortcut = QtGui.QShortcut(QtGui.QKeySequence.StandardKey.Paste, self.profiles_tab)
        paste_shortcut.setContext(QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        paste_shortcut.activated.connect(self.paste_profiles_from_clipboard)
        self.profiles_shortcuts.append(paste_shortcut)

    @staticmethod
    def _parse_clipboard_grid(clipboard_text: str) -> list[list[str]]:
        """
        Parse clipboard text into a two-dimensional grid.

        :param clipboard_text: Raw clipboard text.
        :return: Parsed string grid.
        """
        parsed_rows: list[list[str]] = list()
        line_text: str
        split_values: list[str]

        for line_text in clipboard_text.splitlines():
            if len(line_text.strip()) > 0:
                if "\t" in line_text:
                    split_values = [value.rstrip("\r") for value in line_text.split("\t")]
                    parsed_rows.append(split_values)
                else:
                    split_values = [value.strip() for value in re.split(r"[;,]+", line_text.strip())]
                    parsed_rows.append(split_values)
            else:
                pass

        return parsed_rows

    def _get_profiles_paste_anchor(self) -> tuple[int, int]:
        """
        Determine the anchor cell where clipboard data starts to paste.

        :return: `(row, column)` anchor.
        """
        selection_model: QtCore.QItemSelectionModel | None = self.profiles_table_view.selectionModel()
        selected_indexes: list[QtCore.QModelIndex] = list()

        if selection_model is not None:
            selected_indexes = list(selection_model.selectedIndexes())
        else:
            pass

        if len(selected_indexes) > 0:
            row_values: list[int] = [index.row() for index in selected_indexes]
            col_values: list[int] = [index.column() for index in selected_indexes]
            return min(row_values), min(col_values)
        else:
            current_index: QtCore.QModelIndex = self.profiles_table_view.currentIndex()
            if current_index.isValid():
                return current_index.row(), current_index.column()
            else:
                return 0, 0

    def copy_profiles_selection_to_clipboard(self) -> None:
        """
        Copy the selected profile range to the clipboard.
        """
        selection_model: QtCore.QItemSelectionModel | None = self.profiles_table_view.selectionModel()
        selected_indexes: list[QtCore.QModelIndex] = list()

        if selection_model is not None:
            selected_indexes = list(selection_model.selectedIndexes())
        else:
            pass

        if len(selected_indexes) > 0:
            min_row: int = min(index.row() for index in selected_indexes)
            max_row: int = max(index.row() for index in selected_indexes)
            min_col: int = min(index.column() for index in selected_indexes)
            max_col: int = max(index.column() for index in selected_indexes)
            row_lines: list[str] = list()
            row_index: int
            col_index: int

            # Copy one rectangular range so it can be pasted directly in spreadsheets.
            for row_index in range(min_row, max_row + 1):
                row_cells: list[str] = list()
                for col_index in range(min_col, max_col + 1):
                    model_index: QtCore.QModelIndex = self.profiles_model.index(row_index, col_index)
                    model_value: str | None = self.profiles_model.data(
                        model_index, int(QtCore.Qt.ItemDataRole.DisplayRole)
                    )
                    if model_value is not None:
                        row_cells.append(model_value)
                    else:
                        row_cells.append("")
                row_lines.append("\t".join(row_cells))

            QtWidgets.QApplication.clipboard().setText("\n".join(row_lines))
        else:
            warning_msg("Select profile cells before copying", "Profile editor")

    def paste_profiles_from_clipboard(self) -> None:
        """
        Paste tabular clipboard data into profile cells.
        """
        clipboard_text: str = QtWidgets.QApplication.clipboard().text()
        parsed_rows: list[list[str]] = self._parse_clipboard_grid(clipboard_text=clipboard_text)

        if len(parsed_rows) > 0:
            anchor_row: int
            anchor_col: int
            anchor_row, anchor_col = self._get_profiles_paste_anchor()

            row_count: int = self.profiles_model.rowCount()
            col_count: int = self.profiles_model.columnCount()
            row_offset: int
            col_offset: int
            target_row: int
            target_col: int
            failed_cells: int = 0
            pasted_cells: int = 0

            # Paste each source cell in the matching target offset cell.
            for row_offset, row_values in enumerate(parsed_rows):
                for col_offset, cell_text in enumerate(row_values):
                    target_row = anchor_row + row_offset
                    target_col = anchor_col + col_offset
                    if target_row < row_count and target_col < col_count:
                        model_index: QtCore.QModelIndex = self.profiles_model.index(target_row, target_col)
                        ok: bool = self.profiles_model.setData(
                            model_index,
                            cell_text,
                            int(QtCore.Qt.ItemDataRole.EditRole),
                        )
                        if ok:
                            pasted_cells += 1
                        else:
                            failed_cells += 1
                    else:
                        pass

            if failed_cells > 0:
                warning_msg(f"{failed_cells} cell values could not be parsed for their column type", "Profile editor")
            else:
                pass

            if pasted_cells == 0:
                warning_msg("No profile cells were updated", "Profile editor")
            else:
                pass
        else:
            warning_msg("Clipboard does not contain tabular data", "Profile editor")

    def _collect_profile_series_by_unit(self, columns: Sequence[int]) -> dict[str, list[tuple[str, np.ndarray]]]:
        """
        Collect numeric profile series grouped by their engineering units.

        :param columns: Table columns to gather.
        :return: Mapping `unit -> list[(series_name, series_values)]`.
        """
        grouped_series: dict[str, list[tuple[str, np.ndarray]]] = dict()
        skipped_columns: list[str] = list()
        column_index: int

        for column_index in columns:
            if column_index < len(self.profile_properties):
                prop: GCProp = self.profile_properties[column_index]
                if prop.tpe is bool or prop.tpe is int or prop.tpe is float:
                    profile: AnyProfile = self.api_object.get_profile_by_prop(prop=prop)
                    profile_values: np.ndarray = np.asarray(profile.toarray(), dtype=float)
                    unit_label: str = prop.units if prop.units != "" else "(unitless)"
                    if unit_label in grouped_series:
                        grouped_series[unit_label].append((prop.name, profile_values))
                    else:
                        grouped_series[unit_label] = [(prop.name, profile_values)]
                else:
                    skipped_columns.append(prop.name)
            else:
                pass

        if len(skipped_columns) > 0:
            warning_msg(
                "Skipped non numeric profiles: " + ", ".join(skipped_columns),
                "Profile plotting",
            )
        else:
            pass

        return grouped_series

    def _open_profiles_plot_dialog(self, grouped_series: dict[str, list[tuple[str, np.ndarray]]], title: str) -> None:
        """
        Open a modal chart dialog with one subplot per units group.

        :param grouped_series: Mapping `unit -> list[(series_name, values)]`.
        :param title: Dialog title.
        """
        if len(grouped_series) > 0:
            dialog: QtWidgets.QDialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle(title)
            dialog.resize(1200, 760)

            dialog_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(dialog)
            plot_widget: MatplotlibWidget = MatplotlibWidget(dialog)
            dialog_layout.addWidget(plot_widget)

            close_buttons: QtWidgets.QDialogButtonBox = QtWidgets.QDialogButtonBox(
                QtWidgets.QDialogButtonBox.StandardButton.Close,
                dialog,
            )
            dialog_layout.addWidget(close_buttons)
            close_buttons.rejected.connect(dialog.close)

            unit_labels: list[str] = sorted(list(grouped_series.keys()))
            figure = plot_widget.canvas.fig
            figure.clear()

            # Build one axis per engineering unit to avoid mixing scales.
            axes_object = figure.subplots(len(unit_labels), 1, sharex=True)
            if len(unit_labels) == 1:
                axes = [axes_object]
            else:
                axes = list(np.ravel(np.asarray(axes_object)))

            axis_index: int
            for axis_index, unit_label in enumerate(unit_labels):
                axis = axes[axis_index]
                series_items: list[tuple[str, np.ndarray]] = grouped_series[unit_label]
                series_name: str
                series_values: np.ndarray
                for series_name, series_values in series_items:
                    x_values: np.ndarray = np.arange(len(series_values), dtype=float)
                    axis.plot(x_values, series_values, label=series_name, linewidth=1.5)

                axis.set_ylabel(unit_label)
                axis.grid(True, linestyle="--", alpha=0.4)
                axis.legend(loc="best")

            axes[len(axes) - 1].set_xlabel("Time index")
            figure.tight_layout()
            plot_widget.redraw()
            dialog.exec()
        else:
            warning_msg("No numeric profile columns available for plotting", "Profile plotting")

    def plot_selected_profiles_grouped_by_units(self) -> None:
        """
        Plot currently selected profile columns grouped by units.
        """
        selection_model: QtCore.QItemSelectionModel | None = self.profiles_table_view.selectionModel()
        selected_indexes: list[QtCore.QModelIndex] = list()

        if selection_model is not None:
            selected_indexes = list(selection_model.selectedIndexes())
        else:
            pass

        if len(selected_indexes) > 0:
            selected_columns_set: set[int] = set()
            index: QtCore.QModelIndex
            for index in selected_indexes:
                selected_columns_set.add(index.column())

            selected_columns: list[int] = sorted(list(selected_columns_set))
            grouped_series: dict[str, list[tuple[str, np.ndarray]]] = self._collect_profile_series_by_unit(
                columns=selected_columns
            )
            self._open_profiles_plot_dialog(grouped_series=grouped_series, title="Selected Profile Plots")
        else:
            warning_msg("Select one or more profile cells before plotting", "Profile plotting")

    def on_time_step_changed(self) -> None:
        """
        Handle slider changes by moving the editable time index.
        """
        slider_index: int = int(self.time_step_slider.value())
        time_index: int | None = self._get_current_time_index()
        self.properties_model.set_time_index(time_index=time_index)
        self._update_time_label(slider_index=slider_index)

    def refresh_profile_table(self) -> None:
        """
        Rebuild the profile table model after external profile changes.
        """
        self.time_labels = self._build_time_labels()
        self.profiles_model = MultiFormatProfilesTableModel(
            device=self.api_object,
            profile_properties=self.profile_properties,
            time_labels=self.time_labels,
            parent=self.profiles_table_view,
        )
        self.profiles_table_view.setModel(self.profiles_model)
        self._configure_profiles_table_delegates()

        n_time_steps: int = self._get_available_time_steps()
        old_value: int = int(self.time_step_slider.value())
        if n_time_steps > 0:
            self.time_step_slider.setRange(-1, n_time_steps - 1)
            if old_value <= (n_time_steps - 1):
                self.time_step_slider.setValue(old_value)
            else:
                self.time_step_slider.setValue(-1)
        else:
            self.time_step_slider.setRange(-1, -1)
            self.time_step_slider.setValue(-1)

        self.properties_model.set_time_index(time_index=self._get_current_time_index())
        self._update_time_label(slider_index=int(self.time_step_slider.value()))


if __name__ == "__main__":
    from VeraGridEngine.Devices.Injections.generator import Generator
    from VeraGridEngine.Devices.Substation.bus import Bus

    qt_app: QtWidgets.QApplication = QtWidgets.QApplication(sys.argv)

    # Build one minimal circuit context to inspect base tabs (properties/profiles/associations).
    circuit_demo: MultiCircuit = MultiCircuit(name="Template device editor demo", Sbase=100.0, fbase=50.0)
    circuit_demo.create_profiles(steps=24, step_length=1, step_unit="h")

    bus_demo: Bus = Bus(name="Bus demo", Vnom=132.0)
    circuit_demo.add_bus(obj=bus_demo)

    generator_demo: Generator = Generator(
        name="Generator demo",
        P=55.0,
        Q=5.0,
        Qmin=-50.0,
        Qmax=60.0,
        Pmin=15.0,
        Pmax=90.0,
        Snom=100.0,
        is_controlled=True,
        power_factor=0.95,
    )
    circuit_demo.add_generator(bus=bus_demo, api_obj=generator_demo)

    dialog_demo: TemplateDeviceEditor = TemplateDeviceEditor(api_object=generator_demo, circuit=circuit_demo)
    dialog_demo.show()
    sys.exit(qt_app.exec())
