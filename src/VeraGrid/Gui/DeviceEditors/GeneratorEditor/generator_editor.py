# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import sys
from typing import Callable, Sequence

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from VeraGrid.Gui.DeviceEditors.GeneratorEditor.generator_editor_gui import Ui_GeneratorQCurveEditorDialog
from VeraGrid.Gui.DeviceEditors.GeneratorEditor.SolarPowerWizard.solar_power_wizzard import SolarPvWizard
from VeraGrid.Gui.DeviceEditors.TemplateDeviceEditor.template_device_editor import TemplateDeviceEditor
from VeraGrid.Gui.DeviceEditors.GeneratorEditor.WindPowerWizard.wind_power_wizzard import WindFarmWizard
from VeraGrid.Gui.Widgets.matplotlibwidget import MatplotlibWidget
from VeraGrid.Gui.messages import info_msg, warning_msg
from VeraGrid.Gui.profile_wizard_utils import fill_substation_weather_profiles
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Injections.generator_q_curve import GeneratorQCurve
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.basic_structures import Mat, Vec
from VeraGridEngine.enumerations import GeneratorControlMode


def build_safe_single_point_curve(qmin: float, qmax: float) -> Mat:
    """
    Build a one-point capability curve used as safe fallback.

    :param qmin: Reactive lower limit in MVAr.
    :param qmax: Reactive upper limit in MVAr.
    :return: Matrix with one row ``[P, Qmin, Qmax]``.
    """
    curve_data: Mat = np.zeros((1, 3), dtype=float)
    curve_data[0, 0] = 0.0
    curve_data[0, 1] = float(qmin)
    curve_data[0, 2] = float(qmax)
    return curve_data


def draw_styled_qcurve_plot(plotter: MatplotlibWidget, q_curve: GeneratorQCurve, chart_title: str) -> None:
    """
    Draw a styled generator capability chart.

    :param plotter: Plot widget where the chart is rendered.
    :param q_curve: Generator reactive capability curve object.
    :param chart_title: Plot title text.
    """
    plotter.clear()
    figure = plotter.canvas.fig
    axis = plotter.canvas.ax
    figure.set_tight_layout(True)

    # Configure a clean background that improves contrast for overlays.
    figure.patch.set_facecolor("#FFFFFF")
    axis.set_facecolor("#F8FAFC")

    # Draw the apparent-power circle to show the global capability envelope.
    radius: float = float(q_curve.get_Snom())
    theta: Vec = np.linspace(0.0, 2.0 * np.pi, 360)
    circle_x: Vec = radius * np.cos(theta)
    circle_y: Vec = radius * np.sin(theta)
    axis.fill(circle_x, circle_y, color="#3B82F6", alpha=0.08, label="Snom envelope")
    axis.plot(circle_x, circle_y, color="#2563EB", linewidth=1.8, linestyle="--")

    # Draw q-curve limits and the feasible band between Qmin/Qmax.
    curve_data: Mat = q_curve.get_data()
    max_abs_value: float = abs(radius)
    if curve_data.shape[0] > 0:
        sorted_indices: Vec = np.argsort(curve_data[:, 0], kind="stable")
        sorted_curve_data: Mat = curve_data[sorted_indices, :]
        p_values: np.ndarray = np.asarray(sorted_curve_data[:, 0], dtype=float)
        qmin_values: np.ndarray = np.asarray(sorted_curve_data[:, 1], dtype=float)
        qmax_values: np.ndarray = np.asarray(sorted_curve_data[:, 2], dtype=float)

        axis.fill_between(p_values, qmin_values, qmax_values, color="#10B981", alpha=0.16, label="Feasible band")
        axis.plot(p_values, qmax_values, color="#0F766E", linewidth=2.2, marker="o", markersize=4, label="Qmax(P)")
        axis.plot(p_values, qmin_values, color="#F97316", linewidth=2.2, marker="o", markersize=4, label="Qmin(P)")
        axis.scatter(p_values, qmax_values, color="#0F766E", s=28, alpha=0.95, zorder=3)
        axis.scatter(p_values, qmin_values, color="#F97316", s=28, alpha=0.95, zorder=3)

        p_abs: float = float(np.max(np.abs(p_values)))
        qmin_abs: float = float(np.max(np.abs(qmin_values)))
        qmax_abs: float = float(np.max(np.abs(qmax_values)))
        max_abs_value = max(max_abs_value, p_abs, qmin_abs, qmax_abs)
    else:
        pass

    # Add coordinate axes and readable limits around the largest value shown.
    axis.axhline(0.0, color="#94A3B8", linewidth=1.0)
    axis.axvline(0.0, color="#94A3B8", linewidth=1.0)
    if max_abs_value > 0.0:
        span_value: float = max_abs_value * 1.15
    else:
        span_value = 1.0
    axis.set_xlim(-span_value, span_value)
    axis.set_ylim(-span_value, span_value)

    # Configure labels, grid and styling for better visual tracking.
    axis.set_title(chart_title)
    axis.set_xlabel("P [MW]")
    axis.set_ylabel("Q [MVAr]")
    axis.set_aspect("equal", adjustable="box")
    axis.minorticks_on()
    axis.grid(True, which="major", linestyle="--", linewidth=0.8, color="#CBD5E1", alpha=0.75)
    axis.grid(True, which="minor", linestyle=":", linewidth=0.6, color="#E2E8F0", alpha=0.65)
    axis.text(
        0.02,
        0.98,
        f"Snom = {radius:.2f} MVA",
        transform=axis.transAxes,
        ha="left",
        va="top",
        fontsize=9,
        bbox=dict(boxstyle="round,pad=0.28", facecolor="#FFFFFF", edgecolor="#D1D5DB", alpha=0.95),
    )

    # Keep the legend outside the axes so it never hides q-curve points.
    legend_font_size: float = float(axis.xaxis.label.get_size()) / 3.0 + 4.0
    axis.legend(
        loc="upper left",
        bbox_to_anchor=(1.01, 1.0),
        borderaxespad=0.0,
        frameon=True,
        framealpha=0.95,
        fancybox=True,
        fontsize=legend_font_size,
    )
    for spine_key in axis.spines.keys():
        axis.spines[spine_key].set_color("#94A3B8")
        axis.spines[spine_key].set_linewidth(0.9)

    figure.tight_layout(rect=(0.0, 0.0, 0.82, 1.0))
    plotter.redraw()


class GeneratorQCurveEditorTableModel(QtCore.QAbstractTableModel):
    """
    Table model for reactive power capability points.
    """

    def __init__(self,
                 data: Mat,
                 headers: list[str],
                 callback: Callable[[], None] | None = None,
                 parent: QtCore.QObject | None = None) -> None:
        """
        Build table model.

        :param data: Initial point matrix.
        :param headers: Column labels.
        :param callback: Optional callback on data changes.
        :param parent: Qt parent object.
        """
        QtCore.QAbstractTableModel.__init__(self, parent)
        self._data: Mat = data
        self._headers: list[str] = headers
        self.callback: Callable[[], None] | None = callback

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        """
        Return number of rows.

        :param parent: Unused parent index.
        :return: Row count.
        """
        _ = parent
        return len(self._data)

    def columnCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        """
        Return number of columns.

        :param parent: Unused parent index.
        :return: Column count.
        """
        _ = parent
        return len(self._headers)

    def data(self, index: QtCore.QModelIndex, role: int = int(QtCore.Qt.ItemDataRole.DisplayRole)) -> str | None:
        """
        Return displayed and edited value.

        :param index: Target table index.
        :param role: Qt data role.
        :return: Formatted cell value or ``None``.
        """
        if role == int(QtCore.Qt.ItemDataRole.DisplayRole) or role == int(QtCore.Qt.ItemDataRole.EditRole):
            return str(self._data[index.row(), index.column()])
        else:
            return None

    def setData(self, index: QtCore.QModelIndex, value: object, role: int = int(QtCore.Qt.ItemDataRole.EditRole)) -> bool:
        """
        Set one numeric cell.

        :param index: Target table index.
        :param value: New value.
        :param role: Qt data role.
        :return: Success flag.
        """
        if role == int(QtCore.Qt.ItemDataRole.EditRole):
            try:
                numeric_value: float = float(value)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                return False

            self._data[index.row(), index.column()] = numeric_value
            self.dataChanged.emit(index, index)

            if self.callback is not None:
                self.callback()
            else:
                pass

            if index.column() == 0:
                self.sort_data()
            else:
                pass
            return True
        else:
            return False

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlag:
        """
        Return editable item flags.

        :param index: Target table index.
        :return: Item flags.
        """
        _ = index
        return QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsEditable | QtCore.Qt.ItemFlag.ItemIsSelectable

    def headerData(self,
                   section: int,
                   orientation: QtCore.Qt.Orientation,
                   role: int = int(QtCore.Qt.ItemDataRole.DisplayRole)) -> str | None:
        """
        Return column headers.

        :param section: Header section.
        :param orientation: Header orientation.
        :param role: Qt role.
        :return: Header text or ``None``.
        """
        if role == int(QtCore.Qt.ItemDataRole.DisplayRole) and orientation == QtCore.Qt.Orientation.Horizontal:
            return self._headers[section]
        else:
            return QtCore.QAbstractTableModel.headerData(self, section, orientation, role)

    def add_row(self, row_data: Vec) -> None:
        """
        Append one row.

        :param row_data: Row data with three values.
        """
        self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount())
        self._data = np.vstack([self._data, row_data])
        self.endInsertRows()

    def del_row(self, row_index: int) -> None:
        """
        Remove row at index.

        :param row_index: Row index to remove.
        """
        if self._data.shape[0] > 0:
            self.beginRemoveRows(QtCore.QModelIndex(), row_index, row_index)
            self._data = np.delete(self._data, row_index, axis=0)
            self.endRemoveRows()
        else:
            pass

    def del_last_row(self) -> None:
        """
        Remove last row if any.
        """
        if self._data.shape[0] > 0:
            row_index: int = int(self._data.shape[0] - 1)
            self.beginRemoveRows(QtCore.QModelIndex(), row_index, row_index)
            self._data = np.delete(self._data, row_index, axis=0)
            self.endRemoveRows()
        else:
            pass

    def sort_data(self) -> None:
        """
        Sort rows by active power column.
        """
        if self._data.shape[0] > 0:
            sorted_indices: Vec = np.argsort(self._data[:, 0], kind="stable")
            self._data = self._data[sorted_indices]
            self.layoutChanged.emit()
        else:
            pass

    def get_data(self) -> Mat:
        """
        Get table matrix.

        :return: Data matrix.
        """
        return self._data


class GeneratorQCurveEditorWidget(QtWidgets.QWidget):
    """
    Reactive power capability curve editor widget backed by a Qt Designer `.ui`.
    """

    curve_changed = QtCore.Signal()

    def __init__(self, q_curve: GeneratorQCurve, Qmin: float, Qmax: float, Pmin: float, Pmax: float, Snom: float) -> None:
        """
        Build the curve editor widget.

        :param q_curve: Generator reactive capability object.
        :param Qmin: Initial minimum reactive power.
        :param Qmax: Initial maximum reactive power.
        :param Pmin: Initial minimum active power.
        :param Pmax: Initial maximum active power.
        :param Snom: Initial apparent power nominal value.
        """
        QtWidgets.QWidget.__init__(self)
        self.ui = Ui_GeneratorQCurveEditorDialog()
        self.ui.setupUi(self)
        self.setWindowTitle("")

        self.q_curve: GeneratorQCurve = q_curve
        self.Qmin: float = Qmin
        self.Qmax: float = Qmax
        self.Pmin: float = Pmin
        self.Pmax: float = Pmax
        self.Snom: float = Snom
        self.headers: list[str] = ["P", "Qmin", "Qmax"]

        self.table_model: GeneratorQCurveEditorTableModel = GeneratorQCurveEditorTableModel(
            data=self.q_curve.get_data(),
            headers=self.headers,
            callback=self._on_table_model_changed,
            parent=self,
        )

        self.ui.tableView.setSelectionBehavior(QtWidgets.QTableView.SelectionBehavior.SelectRows)
        self.ui.tableView.setSelectionMode(QtWidgets.QTableView.SelectionMode.SingleSelection)
        self.ui.tableView.setModel(self.table_model)
        self.ui.addRowButton.clicked.connect(self.add_row)
        self.ui.delRowButton.clicked.connect(self.remove_selected_row)

        self.plot()

    def add_row(self) -> None:
        """
        Add one empty row.
        """
        self.table_model.add_row(np.zeros(3))
        self._on_table_model_changed()

    def remove_selected_row(self) -> None:
        """
        Remove selected row or the last row when no selection exists.
        """
        selected_indexes: list[QtCore.QModelIndex] = self.ui.tableView.selectionModel().selectedRows()
        if len(selected_indexes) > 0:
            selected_row: int = selected_indexes[0].row()
            self.table_model.del_row(selected_row)
        else:
            self.table_model.del_last_row()
        self._on_table_model_changed()

    def collect_data(self) -> None:
        """
        Collect values from the table model and update scalar limits.
        """
        curve_data: Mat = self.table_model.get_data()
        if curve_data.shape[0] > 0:
            safe_curve_data: Mat = curve_data
        else:
            safe_curve_data = build_safe_single_point_curve(qmin=self.Qmin, qmax=self.Qmax)

        self.q_curve.set(safe_curve_data)
        self.Snom = float(self.q_curve.get_Snom())
        self.Qmax = float(self.q_curve.get_Qmax())
        self.Qmin = float(self.q_curve.get_Qmin())
        self.Pmax = float(self.q_curve.get_Pmax())
        self.Pmin = float(self.q_curve.get_Pmin())

    def closeEvent(self, event: QtCore.QEvent) -> None:
        """
        Save edited data when closing.

        :param event: Qt close event.
        """
        _ = event
        self.collect_data()
        self.ui.plotter.dispose()

    def plot(self) -> None:
        """
        Plot capability envelope and q-curve limits.
        """
        self.collect_data()
        draw_styled_qcurve_plot(plotter=self.ui.plotter, q_curve=self.q_curve, chart_title="Reactive capability curve")

    def _on_table_model_changed(self) -> None:
        """
        React to table edits by redrawing and notifying listeners.
        """
        self.plot()
        self.curve_changed.emit()


class GeneratorQCurveEditor(QtWidgets.QDialog):
    """
    Standalone reactive power capability curve editor.
    """

    def __init__(self, q_curve: GeneratorQCurve, Qmin: float, Qmax: float, Pmin: float, Pmax: float, Snom: float) -> None:
        """
        Build the curve editor.

        :param q_curve: Generator reactive capability object.
        :param Qmin: Initial minimum reactive power.
        :param Qmax: Initial maximum reactive power.
        :param Pmin: Initial minimum active power.
        :param Pmax: Initial maximum active power.
        :param Snom: Initial apparent power nominal value.
        """
        QtWidgets.QDialog.__init__(self)
        self.q_curve_widget: GeneratorQCurveEditorWidget = GeneratorQCurveEditorWidget(
            q_curve=q_curve,
            Qmin=Qmin,
            Qmax=Qmax,
            Pmin=Pmin,
            Pmax=Pmax,
            Snom=Snom,
        )
        self.q_curve_widget.curve_changed.connect(self._sync_from_widget)
        self.setWindowTitle(self.tr("Reactive power curve editor"))

        self.q_curve: GeneratorQCurve = q_curve
        self.Qmin: float = Qmin
        self.Qmax: float = Qmax
        self.Pmin: float = Pmin
        self.Pmax: float = Pmax
        self.Snom: float = Snom

        self.main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addWidget(self.q_curve_widget)
        self.resize(980, 620)

    def _sync_from_widget(self) -> None:
        """
        Synchronize the scalar fields from the embedded q-curve widget.
        """
        self.q_curve_widget.collect_data()
        self.q_curve = self.q_curve_widget.q_curve
        self.Snom = float(self.q_curve_widget.Snom)
        self.Qmax = float(self.q_curve_widget.Qmax)
        self.Qmin = float(self.q_curve_widget.Qmin)
        self.Pmax = float(self.q_curve_widget.Pmax)
        self.Pmin = float(self.q_curve_widget.Pmin)

    def closeEvent(self, event: QtCore.QEvent) -> None:
        """
        Save edited data when closing.

        :param event: Qt close event.
        """
        _ = event
        self._sync_from_widget()


class EmbeddedSolarPvEditorWidget(SolarPvWizard):
    """
    Solar editor embedded as a child widget inside the generator editor tab.
    """

    generation_finished = QtCore.Signal(bool)

    def __init__(self,
                 time_array: Sequence[object],
                 peak_power: float,
                 latitude: float,
                 longitude: float,
                 gen_name: str,
                 bus_name: str,
                 parent: QtWidgets.QWidget | None = None) -> None:
        """
        Build embedded solar editor widget.

        :param time_array: Time profile sequence.
        :param peak_power: Generator peak power.
        :param latitude: Bus latitude.
        :param longitude: Bus longitude.
        :param gen_name: Generator name.
        :param bus_name: Bus name.
        :param parent: Qt parent widget.
        """
        SolarPvWizard.__init__(
            self,
            time_array=time_array,
            peak_power=peak_power,
            latitude=latitude,
            longitude=longitude,
            gen_name=gen_name,
            bus_name=bus_name,
            title="Solar profile editor",
        )
        if parent is not None:
            self.setParent(parent)
        else:
            pass

        self.setWindowFlags(QtCore.Qt.WindowType.Widget)
        self.ui.acceptButton.hide()
        self.setWindowTitle("")

    def generate_click(self) -> None:
        """
        Generate the solar profile and notify parent listeners.
        """
        SolarPvWizard.generate_click(self)
        self.generation_finished.emit(bool(self.ok))

    def accept_click(self) -> None:
        """
        Notify parent listeners without closing embedded widget.
        """
        self.is_accepted = bool(self.ok)
        self.generation_finished.emit(self.is_accepted)


class EmbeddedWindFarmEditorWidget(WindFarmWizard):
    """
    Wind farm editor embedded as a child widget inside the generator editor tab.
    """

    generation_finished = QtCore.Signal(bool)

    def __init__(self,
                 time_array: Sequence[object],
                 peak_power: float,
                 latitude: float,
                 longitude: float,
                 gen_name: str,
                 bus_name: str,
                 parent: QtWidgets.QWidget | None = None) -> None:
        """
        Build embedded wind farm editor widget.

        :param time_array: Time profile sequence.
        :param peak_power: Generator peak power.
        :param latitude: Bus latitude.
        :param longitude: Bus longitude.
        :param gen_name: Generator name.
        :param bus_name: Bus name.
        :param parent: Qt parent widget.
        """
        WindFarmWizard.__init__(
            self,
            time_array=time_array,
            peak_power=peak_power,
            latitude=latitude,
            longitude=longitude,
            gen_name=gen_name,
            bus_name=bus_name,
            title="Wind profile editor",
        )
        if parent is not None:
            self.setParent(parent)
        else:
            pass

        self.setWindowFlags(QtCore.Qt.WindowType.Widget)
        self.ui.acceptButton.hide()
        self.setWindowTitle("")

    def generate_click(self) -> None:
        """
        Generate the wind profile and notify parent listeners.
        """
        WindFarmWizard.generate_click(self)
        self.generation_finished.emit(bool(self.ok))

    def accept_click(self) -> None:
        """
        Notify parent listeners without closing embedded widget.
        """
        self.is_accepted = bool(self.ok)
        self.generation_finished.emit(self.is_accepted)


class GeneratorEditor(TemplateDeviceEditor):
    """
    Generator editor that extends ``TemplateDeviceEditor`` with specialized tabs.
    """

    def __init__(self, api_object: Generator, circuit: MultiCircuit | None = None) -> None:
        """
        Build the generator editor.

        :param api_object: Generator edited in place.
        :param circuit: Optional circuit context.
        """
        TemplateDeviceEditor.__init__(self, api_object=api_object, circuit=circuit)
        self.api_object: Generator = api_object
        self.setWindowTitle(self.tr("Generator editor"))

        self.solar_editor_widget: EmbeddedSolarPvEditorWidget | None = None
        self.wind_editor_widget: EmbeddedWindFarmEditorWidget | None = None

        self._build_qcurve_tab()
        self._build_solar_tab()
        self._build_wind_tab()

    def _build_qcurve_tab(self) -> None:
        """
        Build and configure the capability curve tab widget.
        """
        self.qcurve_tab: QtWidgets.QWidget = QtWidgets.QWidget(self.tab_widget)
        self.qcurve_tab_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self.qcurve_tab)
        self.qcurve_editor_widget: GeneratorQCurveEditorWidget = GeneratorQCurveEditorWidget(
            q_curve=self.api_object.q_curve,
            Qmin=self.api_object.Qmin,
            Qmax=self.api_object.Qmax,
            Pmin=self.api_object.Pmin,
            Pmax=self.api_object.Pmax,
            Snom=self.api_object.Snom,
        )
        self.qcurve_tab_layout.addWidget(self.qcurve_editor_widget)
        qcurve_tab_index: int = self.tab_widget.addTab(self.qcurve_tab, "Q curve editor")
        self.tab_widget.setTabIcon(qcurve_tab_index, QtGui.QIcon(":/Icons/icons/plot.png"))
        self.qcurve_editor_widget.curve_changed.connect(self._on_qcurve_data_changed)

    def _build_solar_tab(self) -> None:
        """
        Build and configure the embedded solar profile editor tab.
        """
        self.solar_tab: QtWidgets.QWidget = QtWidgets.QWidget(self.tab_widget)
        self.solar_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self.solar_tab)
        self.solar_button_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        self.solar_apply_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Accept", self.solar_tab)
        self.solar_apply_button.setIcon(QtGui.QIcon(":/Icons/icons/accept.png"))
        self.solar_apply_button.setEnabled(False)

        bus: Bus | None = self._get_generator_bus()
        if self.circuit is not None and self.circuit.has_time_series and bus is not None:
            self.solar_editor_widget: EmbeddedSolarPvEditorWidget = EmbeddedSolarPvEditorWidget(
                time_array=self.circuit.time_profile,
                peak_power=self.api_object.Pmax,
                latitude=bus.latitude,
                longitude=bus.longitude,
                gen_name=self.api_object.name,
                bus_name=bus.name,
                parent=self.solar_tab,
            )
            self.solar_editor_widget.generation_finished.connect(self._on_embedded_solar_generation_finished)
            self.solar_layout.addWidget(self.solar_editor_widget)
            self.solar_apply_button.clicked.connect(self._apply_solar_profile)
        else:
            self.solar_editor_widget = None
            self.solar_apply_button.setEnabled(False)
            missing_msg: QtWidgets.QLabel = QtWidgets.QLabel(
                "Solar editor requires an assigned bus and circuit time profiles.",
                self.solar_tab,
            )
            self.solar_layout.addWidget(missing_msg)

        self.solar_button_layout.addStretch()
        self.solar_button_layout.addWidget(self.solar_apply_button)
        self.solar_layout.addLayout(self.solar_button_layout)

        solar_tab_index: int = self.tab_widget.addTab(self.solar_tab, "Solar editor")
        self.tab_widget.setTabIcon(solar_tab_index, QtGui.QIcon(":/Icons/icons/solar_power.png"))

    def _build_wind_tab(self) -> None:
        """
        Build and configure the embedded wind profile editor tab.
        """
        self.wind_tab: QtWidgets.QWidget = QtWidgets.QWidget(self.tab_widget)
        self.wind_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self.wind_tab)
        self.wind_button_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        self.wind_apply_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Accept", self.wind_tab)
        self.wind_apply_button.setIcon(QtGui.QIcon(":/Icons/icons/accept.png"))
        self.wind_apply_button.setEnabled(False)

        bus: Bus | None = self._get_generator_bus()
        if self.circuit is not None and self.circuit.has_time_series and bus is not None:
            self.wind_editor_widget: EmbeddedWindFarmEditorWidget = EmbeddedWindFarmEditorWidget(
                time_array=self.circuit.time_profile,
                peak_power=self.api_object.Pmax,
                latitude=bus.latitude,
                longitude=bus.longitude,
                gen_name=self.api_object.name,
                bus_name=bus.name,
                parent=self.wind_tab,
            )
            self.wind_editor_widget.generation_finished.connect(self._on_embedded_wind_generation_finished)
            self.wind_layout.addWidget(self.wind_editor_widget)
            self.wind_apply_button.clicked.connect(self._apply_wind_profile)
        else:
            self.wind_editor_widget = None
            self.wind_apply_button.setEnabled(False)
            missing_msg: QtWidgets.QLabel = QtWidgets.QLabel(
                "Wind editor requires an assigned bus and circuit time profiles.",
                self.wind_tab,
            )
            self.wind_layout.addWidget(missing_msg)

        self.wind_button_layout.addStretch()
        self.wind_button_layout.addWidget(self.wind_apply_button)
        self.wind_layout.addLayout(self.wind_button_layout)

        wind_tab_index: int = self.tab_widget.addTab(self.wind_tab, "Wind farm editor")
        self.tab_widget.setTabIcon(wind_tab_index, QtGui.QIcon(":/Icons/icons/wind_power.png"))

    def _plot_qcurve(self) -> None:
        """
        Plot capability envelope and edited q-curve.
        """
        self.qcurve_editor_widget.plot()

    def _sync_qcurve_to_generator(self) -> None:
        """
        Synchronize q-curve widget data into the generator object.
        """
        self.qcurve_editor_widget.collect_data()
        self.api_object.q_curve = self.qcurve_editor_widget.q_curve
        self.api_object.Snom = float(self.api_object.q_curve.get_Snom())
        self.api_object.Qmax = float(self.api_object.q_curve.get_Qmax())
        self.api_object.Qmin = float(self.api_object.q_curve.get_Qmin())
        self.api_object.Pmax = float(self.api_object.q_curve.get_Pmax())
        self.api_object.Pmin = float(self.api_object.q_curve.get_Pmin())

        # Keep property and profile tabs coherent with scalar updates.
        self.properties_model.set_time_index(time_index=self._get_current_time_index())
        self.refresh_profile_table()

    def _on_qcurve_data_changed(self) -> None:
        """
        React to q-curve table changes.
        """
        self._sync_qcurve_to_generator()
        self._plot_qcurve()

    def _get_generator_bus(self) -> Bus | None:
        """
        Get generator bus if available.

        :return: Bus object or ``None``.
        """
        bus: Bus | None = self.api_object.bus
        return bus

    def _on_embedded_solar_generation_finished(self, ok: bool) -> None:
        """
        Enable or disable solar profile application according to generation status.

        :param ok: Generation status.
        """
        self.solar_apply_button.setEnabled(ok)

    def _on_embedded_wind_generation_finished(self, ok: bool) -> None:
        """
        Enable or disable wind profile application according to generation status.

        :param ok: Generation status.
        """
        self.wind_apply_button.setEnabled(ok)

    def _apply_solar_profile(self) -> None:
        """
        Apply previously generated solar profile values to generator profiles.
        """
        if self.solar_editor_widget is None:
            warning_msg(self.tr("Solar editor is not available"), self.tr("Generator editor"))
        elif not bool(self.solar_editor_widget.ok):
            warning_msg(self.tr("Generate a solar profile first"), self.tr("Generator editor"))
        else:
            solar_profile_values: np.ndarray = np.asarray(self.solar_editor_widget.P, dtype=float)
            solar_temperature: np.ndarray | None = (
                None if self.solar_editor_widget.temperature is None else np.asarray(self.solar_editor_widget.temperature, dtype=float)
            )
            solar_wind_speed: np.ndarray | None = (
                None if self.solar_editor_widget.wind_speed is None else np.asarray(self.solar_editor_widget.wind_speed, dtype=float)
            )
            solar_irradiation: np.ndarray | None = (
                None if self.solar_editor_widget.irradiation is None else np.asarray(self.solar_editor_widget.irradiation, dtype=float)
            )

            expected_size: int = self.api_object.P_prof.size()
            if len(solar_profile_values) == expected_size:
                self.api_object.P_prof.set(solar_profile_values)

                bus: Bus | None = self._get_generator_bus()
                if bus is not None:
                    fill_substation_weather_profiles(
                        bus=bus,
                        temperature=solar_temperature,
                        wind_speed=solar_wind_speed,
                        irradiation=solar_irradiation,
                        expected_size=expected_size,
                    )
                else:
                    pass

                self.refresh_profile_table()
                info_msg(self.tr("Solar profile applied to generator"), self.tr("Generator editor"))
            else:
                warning_msg(self.tr("Wrong solar profile length"), self.tr("Generator editor"))

    def _apply_wind_profile(self) -> None:
        """
        Apply previously generated wind profile values to generator profiles.
        """
        if self.wind_editor_widget is None:
            warning_msg(self.tr("Wind editor is not available"), self.tr("Generator editor"))
        elif not bool(self.wind_editor_widget.ok):
            warning_msg(self.tr("Generate a wind profile first"), self.tr("Generator editor"))
        else:
            wind_profile_values: np.ndarray = np.asarray(self.wind_editor_widget.P, dtype=float)
            wind_temperature: np.ndarray | None = (
                None if self.wind_editor_widget.temperature is None else np.asarray(self.wind_editor_widget.temperature, dtype=float)
            )
            wind_speed: np.ndarray | None = (
                None if self.wind_editor_widget.wind_speed is None else np.asarray(self.wind_editor_widget.wind_speed, dtype=float)
            )

            expected_size: int = self.api_object.P_prof.size()
            if len(wind_profile_values) == expected_size:
                self.api_object.P_prof.set(wind_profile_values)

                bus: Bus | None = self._get_generator_bus()
                if bus is not None:
                    fill_substation_weather_profiles(
                        bus=bus,
                        temperature=wind_temperature,
                        wind_speed=wind_speed,
                        irradiation=None,
                        expected_size=expected_size,
                    )
                else:
                    pass

                self.refresh_profile_table()
                info_msg(self.tr("Wind profile applied to generator"), self.tr("Generator editor"))
            else:
                warning_msg(self.tr("Wrong wind profile length"), self.tr("Generator editor"))

    def closeEvent(self, event: QtCore.QEvent) -> None:
        """
        Synchronize q-curve table edits before dialog closes.

        :param event: Qt close event.
        """
        _ = event
        self._sync_qcurve_to_generator()
        self.qcurve_editor_widget.ui.plotter.dispose()


# Backward-compatible alias used by existing call sites in diagrams.
GeneratorEditorDialog = GeneratorEditor


if __name__ == "__main__":
    qt_app: QtWidgets.QApplication = QtWidgets.QApplication(sys.argv)

    circuit_demo: MultiCircuit = MultiCircuit(name="Generator editor demo", Sbase=100.0, fbase=50.0)
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
        control_mode=GeneratorControlMode.V,
        power_factor=0.95,
    )
    circuit_demo.add_generator(bus=bus_demo, api_obj=generator_demo)

    generator_demo.P_prof[0] = 52.0
    generator_demo.P_prof[1] = 58.0
    generator_demo.Vset_prof[0] = 1.01
    generator_demo.Vset_prof[1] = 1.02

    dialog_demo: GeneratorEditor = GeneratorEditor(api_object=generator_demo, circuit=circuit_demo)
    dialog_demo.show()
    sys.exit(qt_app.exec())
