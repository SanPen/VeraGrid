# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import base64
import html
import io
import math
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
from PySide6 import QtCore, QtGui, QtWidgets

from VeraGrid.Gui.Analysis.analysis_gui import Ui_MainWindow
from VeraGrid.Gui.Analysis.object_plot_analysis import (FIXABLE_ERROR_TYPES, FixableErrorNegative,
                                                        FixableErrorOutOfRange, FixableErrorRangeFlip,
                                                        FixableErrorValueCorrection, FixableTransformerVtaps,
                                                        GridErrorLog, grid_analysis)
from VeraGrid.Gui.Icons import icons_rc
from VeraGrid.Gui.Widgets.matplotlibwidget import MatplotlibWidget
from VeraGrid.Gui.general_dialogues import Logger, LogsDialogue
from VeraGrid.Gui.results_model import ResultsModel
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Simulations.InputsAnalysis.inputs_analysis_driver import InputsAnalysisDriver, InputsAnalysisResults
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions
from VeraGridEngine.Simulations.SigmaAnalysis.sigma_analysis_driver import SigmaAnalysisDriver, SigmaAnalysisResults
from VeraGridEngine.enumerations import LogSeverity, ResultTypes


def translate_analysis_dialog(source_text: str, disambiguation: str | None = None, n: int = -1) -> str:
    """
    Translate one runtime dashboard string through the generated UI context.

    :param source_text: Source string to translate.
    :param disambiguation: Optional Qt disambiguation text.
    :param n: Optional plural parameter.
    :return: Translated text.
    """
    return QtCore.QCoreApplication.translate("MainWindow", source_text, disambiguation, n)


class IssueEntry:
    """
    Lightweight record containing one normalized dashboard issue row.
    """

    __slots__ = (
        "message",
        "object_type",
        "element_name",
        "element_index",
        "severity",
        "property_name",
        "lower",
        "value",
        "upper",
        "fixable",
    )

    def __init__(self,
                 message: str,
                 object_type: str,
                 element_name: str,
                 element_index: int,
                 severity: LogSeverity,
                 property_name: str,
                 lower: str,
                 value: str,
                 upper: str,
                 fixable: bool) -> None:
        """
        Build one normalized issue entry.

        :param message: Human readable message
        :param object_type: Device type or logical object type
        :param element_name: Element display name
        :param element_index: Element or time index
        :param severity: Log severity
        :param property_name: Property under analysis
        :param lower: Lower limit text
        :param value: Current value text
        :param upper: Upper limit text
        :param fixable: Whether the dashboard can auto-fix the issue
        """
        self.message = message
        self.object_type = object_type
        self.element_name = element_name
        self.element_index = element_index
        self.severity = severity
        self.property_name = property_name
        self.lower = lower
        self.value = value
        self.upper = upper
        self.fixable = fixable

    def matches_filters(self,
                        search_text: str,
                        severity_filter_text: str,
                        object_type_filter_text: str,
                        fixable_only: bool) -> bool:
        """
        Check whether the issue passes the active dashboard filters.

        :param search_text: Lower-cased free text search
        :param severity_filter_text: Selected severity label
        :param object_type_filter_text: Selected object-type label
        :param fixable_only: Only keep auto-fixable rows
        :return: True when the row should remain visible
        """
        severity_matches: bool = False
        if severity_filter_text == translate_analysis_dialog("All severities"):
            severity_matches = True
        else:
            if severity_filter_text == severity_to_text(self.severity):
                severity_matches = True
            else:
                severity_matches = False

        object_type_matches: bool = False
        if object_type_filter_text == translate_analysis_dialog("All object types"):
            object_type_matches = True
        else:
            if object_type_filter_text == self.object_type:
                object_type_matches = True
            else:
                object_type_matches = False

        if fixable_only:
            fixable_matches: bool = self.fixable
        else:
            fixable_matches = True

        if search_text == "":
            search_matches: bool = True
        else:
            haystack: str = (
                f"{self.message} {self.object_type} {self.element_name} "
                f"{self.property_name} {self.lower} {self.value} {self.upper}"
            ).lower()
            if search_text in haystack:
                search_matches = True
            else:
                search_matches = False

        if severity_matches and object_type_matches and fixable_matches and search_matches:
            return True
        else:
            return False


class DashboardSummary:
    """
    Lightweight record containing the synthesized dashboard health summary.
    """

    __slots__ = (
        "issue_count",
        "critical_count",
        "error_count",
        "warning_count",
        "information_count",
        "divergence_count",
        "fixable_count",
        "asset_count",
        "issue_score",
        "sigma_score",
        "overall_score",
        "grade",
        "sigma_available",
        "sigma_status_text",
        "min_sigma_distance",
        "mean_sigma_distance",
        "top_message",
        "top_message_count",
    )

    def __init__(self,
                 issue_count: int,
                 critical_count: int,
                 error_count: int,
                 warning_count: int,
                 information_count: int,
                 divergence_count: int,
                 fixable_count: int,
                 asset_count: int,
                 issue_score: float,
                 sigma_score: float,
                 overall_score: int,
                 grade: str,
                 sigma_available: bool,
                 sigma_status_text: str,
                 min_sigma_distance: float,
                 mean_sigma_distance: float,
                 top_message: str,
                 top_message_count: int) -> None:
        """
        Build one normalized dashboard summary.

        :param issue_count: Total visible issues before filtering
        :param critical_count: Count of critical issues
        :param error_count: Count of errors
        :param warning_count: Count of warnings
        :param information_count: Count of informational messages
        :param divergence_count: Count of divergence messages
        :param fixable_count: Count of auto-fixable items
        :param asset_count: Number of analyzed grid assets
        :param issue_score: Score driven by diagnostics
        :param sigma_score: Score driven by sigma margin
        :param overall_score: Final blended score
        :param grade: Grade label
        :param sigma_available: Whether sigma analysis is available
        :param sigma_status_text: Human-readable sigma execution status
        :param min_sigma_distance: Minimum sigma distance
        :param mean_sigma_distance: Mean sigma distance
        :param top_message: Most common message
        :param top_message_count: Occurrences of top_message
        """
        self.issue_count = issue_count
        self.critical_count = critical_count
        self.error_count = error_count
        self.warning_count = warning_count
        self.information_count = information_count
        self.divergence_count = divergence_count
        self.fixable_count = fixable_count
        self.asset_count = asset_count
        self.issue_score = issue_score
        self.sigma_score = sigma_score
        self.overall_score = overall_score
        self.grade = grade
        self.sigma_available = sigma_available
        self.sigma_status_text = sigma_status_text
        self.min_sigma_distance = min_sigma_distance
        self.mean_sigma_distance = mean_sigma_distance
        self.top_message = top_message
        self.top_message_count = top_message_count


def clamp_value(value: float, lower: float, upper: float) -> float:
    """
    Clamp a float value to the provided interval.

    :param value: Value to clamp
    :param lower: Lower bound
    :param upper: Upper bound
    :return: Clamped value
    """
    if value < lower:
        return lower
    else:
        if value > upper:
            return upper
        else:
            return value


def severity_to_text(severity: LogSeverity) -> str:
    """
    Convert the log severity enum to the dashboard label.

    :param severity: Log severity
    :return: Display label
    """
    if severity == LogSeverity.Error:
        return translate_analysis_dialog("Error")
    else:
        if severity == LogSeverity.Warning:
            return translate_analysis_dialog("Warning")
        else:
            if severity == LogSeverity.Information:
                return translate_analysis_dialog("Information")
            else:
                return translate_analysis_dialog("Divergence")


def severity_sort_weight(severity: LogSeverity) -> int:
    """
    Return an explicit sorting weight for dashboard issues.

    :param severity: Log severity
    :return: Integer weight, lower means more severe
    """
    if severity == LogSeverity.Error:
        return 0
    else:
        if severity == LogSeverity.Divergence:
            return 1
        else:
            if severity == LogSeverity.Warning:
                return 2
            else:
                return 3


def display_text(value: object) -> str:
    """
    Normalize a value into a dashboard-safe display string.

    :param value: Value to convert
    :return: Display string
    """
    if value is None:
        return ""
    else:
        return str(value)


def grade_from_score(score: int) -> str:
    """
    Map a numeric dashboard score to a simple grade.

    :param score: Score in the interval [0, 100]
    :return: Grade string
    """
    if score >= 90:
        return "A"
    else:
        if score >= 80:
            return "B"
        else:
            if score >= 70:
                return "C"
            else:
                if score >= 60:
                    return "D"
                else:
                    return "F"


def sigma_point_is_outside_curve(sigma_real: float, sigma_imag: float, tolerance: float = 1e-9) -> bool:
    """
    Check whether one sigma point lies outside the sigma stability boundary.

    The sigma boundary used by the plot is:
    ``sigma_im = ±sqrt(0.25 + sigma_real)``, valid for ``sigma_real >= -0.25``.

    :param sigma_real: Sigma real coordinate
    :param sigma_imag: Sigma imaginary coordinate
    :param tolerance: Small tolerance to avoid false positives near the boundary
    :return: True when the point lies outside the stability region
    """
    if np.isnan(sigma_real) or np.isnan(sigma_imag):
        return False

    if sigma_real < (-0.25 - tolerance):
        return True

    boundary_argument: float = 0.25 + sigma_real
    if boundary_argument < 0.0:
        boundary_argument = 0.0

    boundary: float = math.sqrt(boundary_argument)
    return abs(sigma_imag) > (boundary + tolerance)


def build_fixable_identifiers(fixable_error: FIXABLE_ERROR_TYPES) -> List[str]:
    """
    Extract a small family of identifiers that can be matched against log rows.

    :param fixable_error: Fixable error record
    :return: List of candidate identifiers
    """
    identifiers: List[str] = list()
    element: object
    if isinstance(fixable_error, FixableTransformerVtaps):
        element = fixable_error.grid_element
    else:
        if isinstance(fixable_error, FixableErrorOutOfRange):
            element = fixable_error.grid_element
        else:
            if isinstance(fixable_error, FixableErrorRangeFlip):
                element = fixable_error.grid_element
            else:
                if isinstance(fixable_error, FixableErrorNegative):
                    element = fixable_error.grid_element
                else:
                    if isinstance(fixable_error, FixableErrorValueCorrection):
                        element = fixable_error.grid_element
                    else:
                        element = None

    if element is not None:
        identifiers.append(str(element))
        identifiers.append(str(element.name))
        identifiers.append(str(element.idtag))
    else:
        pass

    return identifiers


def build_fixable_properties(fixable_error: FIXABLE_ERROR_TYPES) -> List[str]:
    """
    Extract the property names affected by one fixable error.

    :param fixable_error: Fixable error record
    :return: Property names that may appear in the log
    """
    properties: List[str] = list()

    if isinstance(fixable_error, FixableTransformerVtaps):
        properties.append("HV or LV")
    else:
        if isinstance(fixable_error, FixableErrorOutOfRange):
            properties.append(fixable_error.property_name)
        else:
            if isinstance(fixable_error, FixableErrorRangeFlip):
                properties.append(fixable_error.property_name_low)
                properties.append(fixable_error.property_name_high)
            else:
                if isinstance(fixable_error, FixableErrorNegative):
                    properties.append(fixable_error.property_name)
                else:
                    if isinstance(fixable_error, FixableErrorValueCorrection):
                        properties.append(fixable_error.property_name_low)
                        properties.append(fixable_error.property_name_high)
                    else:
                        pass

    return properties


class GridAnalysisGUI(QtWidgets.QMainWindow):
    """
    Modern dashboard window merging grid analysis and sigma analysis.
    """

    __slots__ = (
        "ui",
        "circuit",
        "power_flow_options",
        "log",
        "fixable_errors",
        "issue_entries",
        "issue_model",
        "inputs_results",
        "sigma_results",
        "sigma_model",
        "summary",
        "theme_is_dark",
        "theme_refresh_in_progress",
        "theme_updates_enabled",
        "balance_page",
        "balanceAggregationComboBox",
        "balanceTopNSpinBox",
        "balanceSummaryLabel",
        "balancePlotWidget",
    )

    def __init__(self,
                 circuit: MultiCircuit,
                 power_flow_options: Optional[PowerFlowOptions] = None,
                 parent: Optional[QtWidgets.QWidget] = None) -> None:
        """
        Initialize the combined scoring dashboard.

        :param circuit: Active grid model
        :param power_flow_options: Power-flow options used by sigma analysis
        :param parent: Parent window when available
        """
        QtWidgets.QMainWindow.__init__(self, parent)

        # Keep theme refreshes disabled until the window state is fully initialized.
        self.theme_is_dark = False
        self.theme_refresh_in_progress = False
        self.theme_updates_enabled = False

        # Build the generated UI first because every later step depends on the widgets.
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setup_balance_tab()

        # Store the circuit and the power-flow options used to compute sigma data.
        self.circuit = circuit
        if power_flow_options is None:
            self.power_flow_options = PowerFlowOptions()
        else:
            self.power_flow_options = power_flow_options

        # Initialize mutable dashboard state before wiring events.
        self.log = GridErrorLog()
        self.fixable_errors = list()
        self.issue_entries = list()
        self.issue_model = QtGui.QStandardItemModel(self)
        self.inputs_results = None
        self.sigma_results = None
        self.sigma_model = None
        self.summary = DashboardSummary(
            issue_count=0,
            critical_count=0,
            error_count=0,
            warning_count=0,
            information_count=0,
            divergence_count=0,
            fixable_count=0,
            asset_count=0,
            issue_score=0.0,
            sigma_score=0.0,
            overall_score=0,
            grade="F",
            sigma_available=False,
            sigma_status_text=self.tr("Sigma analysis pending."),
            min_sigma_distance=0.0,
            mean_sigma_distance=0.0,
            top_message="",
            top_message_count=0,
        )
        self.theme_updates_enabled = True

        # Apply one-time widget configuration before any analysis is executed.
        self.configure_window()
        self.configure_tables()
        self.populate_static_controls()
        self.connect_signals()

        # Run the first analysis immediately so the dashboard opens populated.
        self.analyze_all()

    def tr(self, source_text: str, disambiguation: str | None = None, n: int = -1) -> str:
        """
        Translate runtime strings through the ``MainWindow`` catalog context.

        :param source_text: Source string to translate.
        :param disambiguation: Optional Qt disambiguation text.
        :param n: Optional plural parameter.
        :return: Translated text.
        """
        return translate_analysis_dialog(source_text, disambiguation, n)

    def configure_window(self) -> None:
        """
        Apply one-time dashboard-level window configuration.
        """
        # Set the window title and icons so the dashboard feels like a first-class tool.
        self.setWindowTitle(self.tr("Grid Health Dashboard"))
        self.setWindowIcon(QtGui.QIcon(":/icons/icons/inputs_analysis 2.png"))
        self.ui.actionAnalyze.setIcon(QtGui.QIcon(":/Icons/icons/inputs_analysis 2.png"))
        self.ui.actionFixIssues.setIcon(QtGui.QIcon(":/Icons/icons/fix.png"))
        self.ui.actionSaveDiagnostic.setIcon(QtGui.QIcon(":/Icons/icons/savec.png"))
        self.ui.actionExportReport.setIcon(QtGui.QIcon(":/Icons/icons/import_profiles.png"))
        self.ui.actionCopySigmaTable.setIcon(QtGui.QIcon(":/Icons/icons/copy.png"))
        self.ui.mainTabWidget.setCurrentIndex(0)

        # Surface basic context immediately in the hero panel.
        circuit_name: str = self.circuit.name.strip()
        if circuit_name == "":
            circuit_name = self.tr("Unnamed grid")
        else:
            pass

        bus_count: int = len(self.circuit.get_buses())
        line_count: int = len(self.circuit.get_lines())
        transformer_count: int = len(self.circuit.get_transformers2w()) + len(self.circuit.get_windings())
        self.ui.gridNameLabel.setText(
            self.tr("{grid_name}  •  {bus_count} buses  •  {line_count} lines  •  {transformer_count} transformers").format(
                grid_name=circuit_name,
                bus_count=bus_count,
                line_count=line_count,
                transformer_count=transformer_count,
            )
        )

        # Sync the auxiliary dashboard visuals with the current application theme.
        self.apply_theme()

    def configure_tables(self) -> None:
        """
        Apply one-time configuration to the findings tree.
        """
        # Configure the findings tree for grouped browsing by severity, message and object.
        self.issue_model.setHorizontalHeaderLabels(
            [self.tr("Item"),
             self.tr("Property"),
             self.tr("Lower"),
             self.tr("Value"),
             self.tr("Upper"),
             self.tr("Index"),
             self.tr("Auto-fix")]
        )
        self.ui.issuesTreeView.setModel(self.issue_model)
        self.ui.issuesTreeView.setAlternatingRowColors(True)
        self.ui.issuesTreeView.setUniformRowHeights(True)
        self.ui.issuesTreeView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.ui.issuesTreeView.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.ui.issuesTreeView.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.ui.issuesTreeView.setRootIsDecorated(True)
        self.ui.issuesTreeView.setItemsExpandable(True)
        self.ui.issuesTreeView.setAllColumnsShowFocus(True)
        self.ui.issuesTreeView.header().setStretchLastSection(False)
        self.ui.issuesTreeView.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.ui.issuesTreeView.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)

        # Configure the sigma table once and let the model be swapped after each analysis.
        self.ui.mainTabWidget.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                                            QtWidgets.QSizePolicy.Policy.Expanding)

    def setup_balance_tab(self) -> None:
        """
        Create the runtime inputs-analysis tab used to explore the strongest balances.
        """
        self.balance_page = QtWidgets.QWidget()
        self.balance_page.setObjectName("balancePage")

        page_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self.balance_page)
        page_layout.setSpacing(12)
        page_layout.setContentsMargins(10, 10, 10, 10)

        panel_frame: QtWidgets.QFrame = QtWidgets.QFrame(self.balance_page)
        panel_frame.setObjectName("balancePanelFrame")
        panel_frame.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        panel_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(panel_frame)
        panel_layout.setSpacing(12)
        panel_layout.setContentsMargins(22, 18, 22, 18)

        header_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        header_layout.setSpacing(10)

        title_label: QtWidgets.QLabel = QtWidgets.QLabel(self.tr("Balance Explorer"), panel_frame)
        title_label.setObjectName("balanceTitleLabel")
        title_label.setProperty("cssClass", "sectionTitle")
        header_layout.addWidget(title_label)

        header_layout.addStretch(1)

        aggregation_label: QtWidgets.QLabel = QtWidgets.QLabel(self.tr("Aggregation"), panel_frame)
        aggregation_label.setObjectName("balanceAggregationLabel")
        header_layout.addWidget(aggregation_label)

        self.balanceAggregationComboBox = QtWidgets.QComboBox(panel_frame)
        self.balanceAggregationComboBox.setObjectName("balanceAggregationComboBox")
        header_layout.addWidget(self.balanceAggregationComboBox)

        top_n_label: QtWidgets.QLabel = QtWidgets.QLabel(self.tr("Top N"), panel_frame)
        top_n_label.setObjectName("balanceTopNLabel")
        header_layout.addWidget(top_n_label)

        self.balanceTopNSpinBox = QtWidgets.QSpinBox(panel_frame)
        self.balanceTopNSpinBox.setObjectName("balanceTopNSpinBox")
        self.balanceTopNSpinBox.setMinimum(1)
        self.balanceTopNSpinBox.setMaximum(20)
        self.balanceTopNSpinBox.setValue(8)
        header_layout.addWidget(self.balanceTopNSpinBox)

        panel_layout.addLayout(header_layout)

        self.balanceSummaryLabel = QtWidgets.QLabel(self.tr("Inputs analysis pending."), panel_frame)
        self.balanceSummaryLabel.setObjectName("balanceSummaryLabel")
        self.balanceSummaryLabel.setWordWrap(True)
        panel_layout.addWidget(self.balanceSummaryLabel)

        self.balancePlotWidget = MatplotlibWidget(panel_frame)
        self.balancePlotWidget.setObjectName("balancePlotWidget")
        panel_layout.addWidget(self.balancePlotWidget)

        page_layout.addWidget(panel_frame)

        controls_index: int = self.ui.mainTabWidget.indexOf(self.ui.controlsPage)
        if controls_index >= 0:
            self.ui.mainTabWidget.insertTab(controls_index, self.balance_page, self.tr("Balance Explorer"))
        else:
            self.ui.mainTabWidget.addTab(self.balance_page, self.tr("Balance Explorer"))

    def populate_static_controls(self) -> None:
        """
        Fill dashboard controls whose contents do not depend on a simulation.
        """
        # Populate the filter combo once because the dashboard reuses the same labels repeatedly.
        self.ui.severityFilterComboBox.clear()
        self.ui.severityFilterComboBox.addItem(self.tr("All severities"))
        self.ui.severityFilterComboBox.addItem(self.tr("Error"))
        self.ui.severityFilterComboBox.addItem(self.tr("Warning"))
        self.ui.severityFilterComboBox.addItem(self.tr("Information"))
        self.ui.severityFilterComboBox.addItem(self.tr("Divergence"))

        self.ui.objectTypeFilterComboBox.clear()
        self.ui.objectTypeFilterComboBox.addItem(self.tr("All object types"))

        self.balanceAggregationComboBox.clear()
        self.balanceAggregationComboBox.addItem(self.tr("Area"))
        self.balanceAggregationComboBox.addItem(self.tr("Zone"))
        self.balanceAggregationComboBox.addItem(self.tr("Substation"))
        self.balanceAggregationComboBox.addItem(self.tr("VoltageLevel"))
        self.balanceAggregationComboBox.addItem(self.tr("Country"))
        self.balanceAggregationComboBox.addItem(self.tr("Community"))
        self.balanceAggregationComboBox.addItem(self.tr("Region"))
        self.balanceAggregationComboBox.addItem(self.tr("Municipality"))

    def populate_object_type_filter(self) -> None:
        """
        Refresh the object-type filter options from the current issue set.
        """
        current_text: str = self.ui.objectTypeFilterComboBox.currentText()
        object_types: List[str] = sorted({issue.object_type for issue in self.issue_entries if issue.object_type != ""})

        self.ui.objectTypeFilterComboBox.blockSignals(True)
        self.ui.objectTypeFilterComboBox.clear()
        self.ui.objectTypeFilterComboBox.addItem(self.tr("All object types"))
        for object_type in object_types:
            self.ui.objectTypeFilterComboBox.addItem(object_type)

        if self.ui.objectTypeFilterComboBox.findText(current_text) >= 0:
            self.ui.objectTypeFilterComboBox.setCurrentText(current_text)
        else:
            self.ui.objectTypeFilterComboBox.setCurrentIndex(0)
        self.ui.objectTypeFilterComboBox.blockSignals(False)

    def connect_signals(self) -> None:
        """
        Connect the dashboard actions and live filters.
        """
        # Route toolbar and hero actions to the same controller methods to keep behavior consistent.
        self.ui.actionAnalyze.triggered.connect(self.analyze_all)
        self.ui.actionFixIssues.triggered.connect(self.fix_all)
        self.ui.actionSaveDiagnostic.triggered.connect(self.save_diagnostic)
        self.ui.actionExportReport.triggered.connect(self.export_report)
        self.ui.actionCopySigmaTable.triggered.connect(self.copy_sigma_to_clipboard)
        self.ui.analyzeButton.clicked.connect(self.analyze_all)
        self.ui.fixIssuesButton.clicked.connect(self.fix_all)
        self.ui.exportReportButton.clicked.connect(self.export_report)

        # Make the findings table react live to dashboard filters.
        self.ui.severityFilterComboBox.currentTextChanged.connect(self.refresh_issue_table)
        self.ui.objectTypeFilterComboBox.currentTextChanged.connect(self.refresh_issue_table)
        self.ui.fixableOnlyCheckBox.toggled.connect(self.refresh_issue_table)
        self.ui.issueSearchLineEdit.textChanged.connect(self.refresh_issue_table)
        self.ui.expandAllIssuesButton.clicked.connect(self.expand_all_issues)
        self.ui.collapseAllIssuesButton.clicked.connect(self.collapse_all_issues)
        self.balanceAggregationComboBox.currentTextChanged.connect(self.update_balance_panel)
        self.balanceTopNSpinBox.valueChanged.connect(self.update_balance_panel)

    def expand_all_issues(self) -> None:
        """
        Expand the full findings tree.
        """
        self.ui.issuesTreeView.expandAll()

    def collapse_all_issues(self) -> None:
        """
        Collapse the findings tree back to top-level severity groups.
        """
        self.ui.issuesTreeView.collapseAll()

    def changeEvent(self, event: QtCore.QEvent) -> None:
        """
        Refresh the dashboard theme when the application palette or style changes.

        :param event: Qt change event
        """
        QtWidgets.QMainWindow.changeEvent(self, event)

        event_tpe: QtCore.QEvent.Type = event.type()
        if event_tpe in (
            QtCore.QEvent.Type.PaletteChange,
            QtCore.QEvent.Type.ApplicationPaletteChange,
            QtCore.QEvent.Type.StyleChange,
        ):
            if self.theme_updates_enabled and (not self.theme_refresh_in_progress):
                self.apply_theme()
            else:
                pass
        else:
            pass

    def is_dashboard_dark_mode(self) -> bool:
        """
        Determine whether the dashboard should render in dark mode.

        :return: True when the main application is in dark mode
        """
        # Follow the live main-window palette first so the dashboard actually tracks the host theme.
        parent_widget: Optional[QtWidgets.QWidget] = self.parentWidget()
        if parent_widget is not None:
            palette: QtGui.QPalette = parent_widget.palette()
        else:
            palette = QtWidgets.QApplication.palette()

        window_color: QtGui.QColor = palette.color(QtGui.QPalette.ColorGroup.Active,
                                                   QtGui.QPalette.ColorRole.Window)
        if window_color.lightness() < 128:
            return True
        else:
            return False

    def apply_theme(self) -> None:
        """
        Sync the dashboard helper visuals with the current main-window theme.
        """
        if not self.theme_updates_enabled:
            return
        else:
            pass

        if self.theme_refresh_in_progress:
            return
        else:
            pass

        # Recompute the mode each time because the main application can switch live between light and dark.
        new_theme_is_dark: bool = self.is_dashboard_dark_mode()
        theme_changed: bool = (new_theme_is_dark != self.theme_is_dark)
        overview_stylesheet: str = self.build_overview_stylesheet(dark_mode=new_theme_is_dark)
        self.ui.overviewPage.setStyleSheet(overview_stylesheet)

        if not theme_changed:
            return
        else:
            pass

        self.theme_refresh_in_progress = True
        try:
            self.theme_is_dark = new_theme_is_dark
            self.refresh_issue_table()
            self.update_balance_panel()
            self.update_sigma_panel()
            self.update_narrative()
        finally:
            self.theme_refresh_in_progress = False

    def build_overview_stylesheet(self, dark_mode: bool) -> str:
        """
        Build the dashboard stylesheet for the overview tab only.

        :param dark_mode: Whether the overview should use dark-mode colors
        :return: Overview-page stylesheet
        """
        if dark_mode:
            window_background: str = "#161b22"
            panel_background: str = "#1f2630"
            border_color: str = "#344051"
            text_color: str = "#e7edf5"
            input_border: str = "#46556a"
            progress_background: str = "#304053"
            hero_gradient_start: str = "#0a2a43"
            hero_gradient_mid: str = "#0f4d69"
            hero_gradient_end: str = "#19614d"
            chip_background: str = "rgba(255, 255, 255, 42)"
            chip_border: str = "rgba(255, 255, 255, 80)"
            grade_text_color: str = "#a6f4d0"
            grade_background: str = "#153e35"
            grade_border: str = "#2a6d5d"
            primary_button_background: str = "#00aa88"
            primary_button_hover: str = "#0ab596"
            primary_button_text: str = "#ffffff"
            secondary_button_background: str = "#203547"
            secondary_button_text: str = "#d9ecff"
            accent_button_background: str = "#173c35"
            accent_button_text: str = "#bff2e1"
            sigma_status_color: str = "#bfd0e3"
            card_caption_color: str = "#8fa3b9"
            card_value_color: str = "#f2f7fb"
            muted_line_color: str = "#425164"
        else:
            window_background = "#f3f7fb"
            panel_background = "#ffffff"
            border_color = "#dce7f2"
            text_color = "#102235"
            input_border = "#d4e1ee"
            progress_background = "#e5eef6"
            hero_gradient_start = "#0d344f"
            hero_gradient_mid = "#135a7c"
            hero_gradient_end = "#1f8a70"
            chip_background = "rgba(255, 255, 255, 38)"
            chip_border = "rgba(255, 255, 255, 60)"
            grade_text_color = "#0b6b4b"
            grade_background = "#def7ea"
            grade_border = "#c4ebd8"
            primary_button_background = "#00aa88"
            primary_button_hover = "#0ab596"
            primary_button_text = "#ffffff"
            secondary_button_background = "#e9f5ff"
            secondary_button_text = "#10415f"
            accent_button_background = "#e3fbf2"
            accent_button_text = "#0f473e"
            sigma_status_color = "#375166"
            card_caption_color = "#5e7388"
            card_value_color = "#0d2236"
            muted_line_color = "#90abc6"

        return f"""
QWidget#overviewPage {{
    background-color: {window_background};
    color: {text_color};
    font-family: "DejaVu Sans";
}}

QWidget#overviewPage QFrame#heroFrame {{
    border-radius: 28px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 {hero_gradient_start}, stop:0.55 {hero_gradient_mid}, stop:1 {hero_gradient_end});
}}

QWidget#overviewPage QFrame#scoreCardFrame,
QWidget#overviewPage QFrame#issueCardFrame,
QWidget#overviewPage QFrame#criticalCardFrame,
QWidget#overviewPage QFrame#fixableCardFrame,
QWidget#overviewPage QFrame#sigmaCardFrame,
QWidget#overviewPage QFrame#overviewHintFrame {{
    background-color: {panel_background};
    border: 1px solid {border_color};
    border-radius: 24px;
}}

QWidget#overviewPage QLabel#titleLabel {{
    color: #f7fbff;
    font-size: 30px;
    font-weight: 700;
}}

QWidget#overviewPage QLabel#subtitleLabel,
QWidget#overviewPage QLabel#gridNameLabel {{
    color: rgba(247, 251, 255, 215);
    font-size: 13px;
}}

QWidget#overviewPage QLabel#statusChipLabel {{
    color: #ffffff;
    background-color: {chip_background};
    border: 1px solid {chip_border};
    border-radius: 14px;
    padding: 6px 12px;
    font-size: 11px;
    font-weight: 600;
}}

QWidget#overviewPage QLabel[cssClass="cardCaption"] {{
    color: {card_caption_color};
    font-size: 11px;
    font-weight: 600;
}}

QWidget#overviewPage QLabel[cssClass="cardValue"] {{
    color: {card_value_color};
    font-size: 28px;
    font-weight: 700;
}}

QWidget#overviewPage QLabel#scoreGradeLabel {{
    color: {grade_text_color};
    background-color: {grade_background};
    border: 1px solid {grade_border};
    border-radius: 12px;
    padding: 6px 12px;
    font-size: 12px;
    font-weight: 700;
}}

QWidget#overviewPage QLabel#scoreExplainerLabel {{
    color: {sigma_status_color};
    font-size: 12px;
}}

QWidget#overviewPage QPushButton {{
    min-height: 38px;
    border-radius: 18px;
    padding-left: 16px;
    padding-right: 16px;
    font-weight: 600;
    border: 1px solid {input_border};
    background-color: {panel_background};
    color: {text_color};
}}

QWidget#overviewPage QPushButton#analyzeButton {{
    color: {primary_button_text};
    border: 0px;
    background-color: {primary_button_background};
}}

QWidget#overviewPage QPushButton#fixIssuesButton {{
    color: {secondary_button_text};
    background-color: {secondary_button_background};
    border: 1px solid {border_color};
}}

QWidget#overviewPage QPushButton#exportReportButton {{
    color: {accent_button_text};
    background-color: {accent_button_background};
    border: 1px solid {border_color};
}}

QWidget#overviewPage QPushButton:hover {{
    border-color: {muted_line_color};
}}

QWidget#overviewPage QPushButton#analyzeButton:hover {{
    background-color: {primary_button_hover};
}}

QWidget#overviewPage QProgressBar {{
    border: 0px;
    border-radius: 10px;
    background-color: {progress_background};
    min-height: 10px;
    max-height: 10px;
}}

QWidget#overviewPage QProgressBar::chunk {{
    border-radius: 10px;
    background-color: {primary_button_background};
}}
"""

    def analyze_all(self) -> None:
        """
        Run the structural analysis, sigma analysis and dashboard scoring workflow.
        """
        # Start from a clean state because the dashboard score must reflect only the latest configuration.
        self.log = GridErrorLog()

        # Reuse the existing backend grid analysis so the dashboard stays consistent with current checks.
        self.fixable_errors = grid_analysis(
            circuit=self.circuit,
            analyze_ts=self.ui.fixTimeSeriesCheckBox.isChecked(),
            imbalance_threshold=self.ui.activePowerImbalanceSpinBox.value() / 100.0,
            v_low=self.ui.genVsetMinSpinBox.value(),
            v_high=self.ui.genVsetMaxSpinBox.value(),
            tap_min=self.ui.transformerTapModuleMinSpinBox.value(),
            tap_max=self.ui.transformerTapModuleMaxSpinBox.value(),
            transformer_virtual_tap_tolerance=self.ui.virtualTapToleranceSpinBox.value() / 100.0,
            branch_connection_voltage_tolerance=self.ui.lineNominalVoltageToleranceSpinBox.value() / 100.0,
            min_vcc=self.ui.transformerVccMinSpinBox.value(),
            max_vcc=self.ui.transformerVccMaxSpinBox.value(),
            branch_x_threshold=1e-4,
            power_flow_options=self.power_flow_options,
            logger=self.log,
        )

        # Run sigma analysis separately so the dashboard can still open even when sigma is not available.
        sigma_status_text: str
        self.inputs_results = self.run_inputs_analysis()
        self.sigma_results, sigma_status_text = self.run_sigma_analysis()

        # Normalize the log into table rows before score computation and filtering.
        self.issue_entries = self.collect_issue_entries()
        self.issue_entries.extend(self.collect_sigma_issue_entries(results=self.sigma_results,
                                                                  sigma_status_text=sigma_status_text))
        self.issue_entries.sort(key=self.sort_issue_entries)
        self.populate_object_type_filter()

        self.summary = self.build_summary(sigma_status_text=sigma_status_text)

        # Refresh every visual section after the new state has been fully computed.
        self.update_score_cards()
        self.refresh_issue_table()
        self.update_balance_panel()
        self.update_sigma_panel()
        self.update_narrative()
        self.statusBar().showMessage(
            self.tr("Dashboard refreshed: {issue_count} findings, score {overall_score}/100.").format(
                issue_count=self.summary.issue_count,
                overall_score=self.summary.overall_score,
            ),
            8000,
        )

    def run_inputs_analysis(self) -> Optional[InputsAnalysisResults]:
        """
        Build the inputs-analysis results used by the balance explorer tab.

        :return: Inputs-analysis results when available
        """
        inputs_driver: InputsAnalysisDriver

        # Reuse the existing backend so the balance explorer stays aligned with the main application logic.
        try:
            inputs_driver = InputsAnalysisDriver(grid=self.circuit)
        except Exception:
            return None
        else:
            return inputs_driver.results

    def get_balance_result_type(self, aggregation: str) -> ResultTypes:
        """
        Map one balance aggregation label to the matching inputs-analysis result type.

        :param aggregation: Aggregation label selected in the balance explorer
        :return: Matching balance result type
        """
        if aggregation == self.tr("Area"):
            return ResultTypes.AreaBalanceAnalysis
        else:
            if aggregation == self.tr("Zone"):
                return ResultTypes.ZoneBalanceAnalysis
            else:
                if aggregation == self.tr("Substation"):
                    return ResultTypes.SubstationBalanceAnalysis
                else:
                    if aggregation == self.tr("VoltageLevel"):
                        return ResultTypes.VoltageLevelBalanceAnalysis
                    else:
                        if aggregation == self.tr("Country"):
                            return ResultTypes.CountryBalanceAnalysis
                        else:
                            if aggregation == self.tr("Community"):
                                return ResultTypes.CommunityBalanceAnalysis
                            else:
                                if aggregation == self.tr("Region"):
                                    return ResultTypes.RegionBalanceAnalysis
                                else:
                                    return ResultTypes.MunicipalityBalanceAnalysis

    def update_balance_panel(self) -> None:
        """
        Refresh the balance explorer chart from the latest inputs-analysis results.
        """
        axis = self.balancePlotWidget.get_axis()
        figure = self.balancePlotWidget.get_figure()
        self.balancePlotWidget.clear(force=True)
        axis = self.balancePlotWidget.get_axis()
        figure = self.balancePlotWidget.get_figure()

        if self.theme_is_dark:
            figure_facecolor: str = "#1f2630"
            axis_facecolor: str = "#171c24"
            grid_color: str = "#455365"
            label_color: str = "#e7edf5"
            positive_color: str = "#00aa88"
            negative_color: str = "#c96f5d"
        else:
            figure_facecolor = "#ffffff"
            axis_facecolor = "#f7fbff"
            grid_color = "#dce7f2"
            label_color = "#17324a"
            positive_color = "#00aa88"
            negative_color = "#c96f5d"

        figure.set_facecolor(figure_facecolor)
        axis.set_facecolor(axis_facecolor)

        if self.inputs_results is None:
            self.balanceSummaryLabel.setText(self.tr("Inputs analysis is unavailable for the current grid."))
            axis.text(0.5,
                      0.5,
                      self.tr("Inputs analysis unavailable"),
                      ha="center",
                      va="center",
                      fontsize=12,
                      color=label_color,
                      transform=axis.transAxes)
            axis.set_xticks(list())
            axis.set_yticks(list())
            axis.set_frame_on(False)
            figure.tight_layout()
            self.balancePlotWidget.redraw()
            return
        else:
            pass

        aggregation: str = self.balanceAggregationComboBox.currentText()
        top_n: int = self.balanceTopNSpinBox.value()

        if self.circuit.get_time_number() > 0:
            self.plot_time_series_balances(aggregation=aggregation,
                                           top_n=top_n,
                                           axis=axis,
                                           label_color=label_color,
                                           grid_color=grid_color,
                                           positive_color=positive_color,
                                           negative_color=negative_color)
        else:
            self.plot_snapshot_balances(aggregation=aggregation,
                                        top_n=top_n,
                                        axis=axis,
                                        label_color=label_color,
                                        grid_color=grid_color,
                                        positive_color=positive_color,
                                        negative_color=negative_color)

        figure.tight_layout()
        self.balancePlotWidget.redraw()
        self.ui.mainTabWidget.setTabText(self.ui.mainTabWidget.indexOf(self.balance_page),
                                         self.tr("Balance Explorer"))

    def plot_time_series_balances(self,
                                  aggregation: str,
                                  top_n: int,
                                  axis,
                                  label_color: str,
                                  grid_color: str,
                                  positive_color: str,
                                  negative_color: str) -> None:
        """
        Plot the strongest time-series balances for the selected aggregation.

        :param aggregation: Aggregation label
        :param top_n: Maximum number of traces to show
        :param axis: Matplotlib axis
        :param label_color: Theme text color
        :param grid_color: Theme grid color
        :param positive_color: Positive accent color
        :param negative_color: Negative accent color
        """
        result_type: ResultTypes = self.get_balance_result_type(aggregation)
        result_table = self.inputs_results.mdl(result_type)
        magnitude: np.ndarray = np.max(np.abs(result_table.data_c), axis=0)
        ranking: np.ndarray = np.argsort(magnitude)[::-1]
        selected_indices: np.ndarray = ranking[:min(top_n, len(ranking))]

        if len(selected_indices) == 0:
            self.balanceSummaryLabel.setText(
                self.tr("No {aggregation} balances are available to plot.").format(
                    aggregation=aggregation.lower(),
                )
            )
            axis.text(0.5,
                      0.5,
                      self.tr("No balance series available"),
                      ha="center",
                      va="center",
                      fontsize=12,
                      color=label_color,
                      transform=axis.transAxes)
            axis.set_xticks(list())
            axis.set_yticks(list())
            axis.set_frame_on(False)
            return
        else:
            pass

        time_index = pd.to_datetime(result_table.index_c)
        for position, column_index in enumerate(selected_indices):
            series_values: np.ndarray = result_table.data_c[:, column_index]
            column_name: str = str(result_table.cols_c[column_index])

            if position == 0:
                line_color: str = positive_color
            else:
                if position == 1:
                    line_color = negative_color
                else:
                    line_color = "#4f7cac"

            axis.plot(time_index, series_values, linewidth=1.8, label=column_name, color=line_color)

        axis.axhline(0.0, color=grid_color, linewidth=1.0, linestyle="--")
        axis.grid(True, color=grid_color, linewidth=0.7)
        axis.tick_params(axis="x", colors=label_color)
        axis.tick_params(axis="y", colors=label_color)
        axis.title.set_color(label_color)
        axis.xaxis.label.set_color(label_color)
        axis.yaxis.label.set_color(label_color)
        axis.set_title(
            self.tr("Top {count} {aggregation} balances over time").format(
                count=len(selected_indices),
                aggregation=aggregation,
            )
        )
        axis.set_xlabel(self.tr("Time"))
        axis.set_ylabel(self.tr("Net balance (MW)"))
        axis.legend(loc="best")

        top_column_name: str = str(result_table.cols_c[selected_indices[0]])
        top_column_value: float = float(magnitude[selected_indices[0]])
        self.balanceSummaryLabel.setText(
            self.tr("Showing the {count} strongest {aggregation} balance traces. "
                    "Largest absolute balance: {column_name} at {column_value:.3f} MW.").format(
                count=len(selected_indices),
                aggregation=aggregation.lower(),
                column_name=top_column_name,
                column_value=top_column_value,
            )
        )

    def plot_snapshot_balances(self,
                               aggregation: str,
                               top_n: int,
                               axis,
                               label_color: str,
                               grid_color: str,
                               positive_color: str,
                               negative_color: str) -> None:
        """
        Plot the strongest snapshot balances for the selected aggregation.

        :param aggregation: Aggregation label
        :param top_n: Maximum number of bars to show
        :param axis: Matplotlib axis
        :param label_color: Theme text color
        :param grid_color: Theme grid color
        :param positive_color: Positive accent color
        :param negative_color: Negative accent color
        """
        grouped_frame: pd.DataFrame = self.inputs_results.group_by(aggregation)
        balance_series: pd.Series = grouped_frame["P"].astype(float)
        ordered_series: pd.Series = balance_series.reindex(balance_series.abs().sort_values(ascending=False).index)
        selected_series: pd.Series = ordered_series.head(top_n)

        if selected_series.empty:
            self.balanceSummaryLabel.setText(
                self.tr("No {aggregation} balances are available to plot.").format(
                    aggregation=aggregation.lower(),
                )
            )
            axis.text(0.5,
                      0.5,
                      self.tr("No snapshot balances available"),
                      ha="center",
                      va="center",
                      fontsize=12,
                      color=label_color,
                      transform=axis.transAxes)
            axis.set_xticks(list())
            axis.set_yticks(list())
            axis.set_frame_on(False)
            return
        else:
            pass

        labels: List[str] = list(selected_series.index.astype(str))
        values: np.ndarray = selected_series.to_numpy(dtype=float)
        colors: List[str] = list()
        value_index: int = 0
        while value_index < len(values):
            if values[value_index] >= 0.0:
                colors.append(positive_color)
            else:
                colors.append(negative_color)
            value_index += 1

        axis.barh(labels[::-1], values[::-1], color=colors[::-1])
        axis.axvline(0.0, color=grid_color, linewidth=1.0, linestyle="--")
        axis.grid(True, color=grid_color, linewidth=0.7, axis="x")
        axis.tick_params(axis="x", colors=label_color)
        axis.tick_params(axis="y", colors=label_color)
        axis.title.set_color(label_color)
        axis.xaxis.label.set_color(label_color)
        axis.yaxis.label.set_color(label_color)
        axis.set_title(
            self.tr("Top {count} {aggregation} snapshot balances").format(
                count=len(values),
                aggregation=aggregation,
            )
        )
        axis.set_xlabel(self.tr("Net balance (MW)"))
        axis.set_ylabel(aggregation)

        exporter_name: str = str(selected_series.idxmax())
        exporter_value: float = float(selected_series.max())
        importer_name: str = str(selected_series.idxmin())
        importer_value: float = float(selected_series.min())
        self.balanceSummaryLabel.setText(
            self.tr("Snapshot net balances by {aggregation}. "
                    "Largest exporter: {exporter_name} ({exporter_value:.3f} MW). "
                    "Largest importer: {importer_name} ({importer_value:.3f} MW).").format(
                aggregation=aggregation.lower(),
                exporter_name=exporter_name,
                exporter_value=exporter_value,
                importer_name=importer_name,
                importer_value=importer_value,
            )
        )

    def sort_issue_entries(self, issue: IssueEntry) -> Tuple[int, str, str]:
        """
        Provide an explicit, deterministic dashboard sorting key.

        :param issue: Issue entry to sort
        :return: Sorting key
        """
        return severity_sort_weight(issue.severity), issue.message, issue.element_name

    def collect_issue_entries(self) -> List[IssueEntry]:
        """
        Convert the grouped backend log into flat dashboard rows.

        :return: Flat issue list
        """
        # Build a small lookup set so the dashboard can tag rows that are safe to auto-fix.
        fixable_keys: set[str] = self.build_fixable_keys()
        entries: List[IssueEntry] = list()

        # Flatten the grouped logger structure because the dashboard table is row-oriented.
        for message, grouped_entries in self.log.logs.items():
            for raw_entry in grouped_entries:
                object_type: str = display_text(raw_entry[0])
                element_name: str = display_text(raw_entry[1])
                element_index: int = int(raw_entry[2])
                severity: LogSeverity = raw_entry[3]
                property_name: str = display_text(raw_entry[4])
                lower: str = display_text(raw_entry[5])
                value: str = display_text(raw_entry[6])
                upper: str = display_text(raw_entry[7])
                fixable: bool = self.is_fixable_issue(element_name=element_name,
                                                      property_name=property_name,
                                                      fixable_keys=fixable_keys)

                issue_entry: IssueEntry = IssueEntry(
                    message=message,
                    object_type=object_type,
                    element_name=element_name,
                    element_index=element_index,
                    severity=severity,
                    property_name=property_name,
                    lower=lower,
                    value=value,
                    upper=upper,
                    fixable=fixable,
                )
                entries.append(issue_entry)

        return entries

    def collect_sigma_issue_entries(self,
                                    results: Optional[SigmaAnalysisResults],
                                    sigma_status_text: str) -> List[IssueEntry]:
        """
        Convert sigma-analysis outcomes into dashboard findings.

        :param results: Sigma-analysis results when available
        :param sigma_status_text: Human-readable sigma status
        :return: Sigma-derived issue entries
        """
        entries: List[IssueEntry] = list()

        if results is None:
            return entries
        else:
            pass

        if not results.converged:
            entries.append(
                IssueEntry(
                    message=self.tr("Sigma analysis did not converge"),
                    object_type=self.tr("Sigma analysis"),
                    element_name=self.tr("Global"),
                    element_index=-1,
                    severity=LogSeverity.Error,
                    property_name=self.tr("Status"),
                    lower=self.tr("Converged"),
                    value=sigma_status_text,
                    upper="",
                    fixable=False,
                )
            )
        else:
            pass

        bus_names: np.ndarray = results.bus_names
        distances: np.ndarray = results.distances
        sigma_real_values: np.ndarray = results.sigma_re
        sigma_imag_values: np.ndarray = results.sigma_im
        for index, distance in enumerate(distances):
            if np.isnan(distance):
                entries.append(
                    IssueEntry(
                        message=self.tr("Sigma distance is not available"),
                        object_type=self.tr("Bus"),
                        element_name=display_text(bus_names[index]),
                        element_index=index,
                        severity=LogSeverity.Error,
                        property_name=self.tr("Sigma distance"),
                        lower="0.0",
                        value="nan",
                        upper="inf",
                        fixable=False,
                    )
                )
            else:
                sigma_real: float = float(sigma_real_values[index])
                sigma_imag: float = float(sigma_imag_values[index])

                if sigma_point_is_outside_curve(sigma_real=sigma_real, sigma_imag=sigma_imag):
                    entries.append(
                        IssueEntry(
                            message=self.tr("Sigma point is outside the stability curve"),
                            object_type=self.tr("Bus"),
                            element_name=display_text(bus_names[index]),
                            element_index=index,
                            severity=LogSeverity.Error,
                            property_name=self.tr("Sigma distance"),
                            lower="0.0",
                            value=f"{abs(float(distance)):.6f}",
                            upper="inf",
                            fixable=False,
                        )
                    )
                else:
                    pass

        return entries

    def build_fixable_keys(self) -> set[str]:
        """
        Build a small lookup set linking auto-fix records with dashboard rows.

        :return: Set of compound identifier keys
        """
        keys: set[str] = set()

        # Store a couple of identifier variants because logs use names while fixers hold full objects.
        for fixable_error in self.fixable_errors:
            identifiers: List[str] = build_fixable_identifiers(fixable_error)
            properties: List[str] = build_fixable_properties(fixable_error)
            for identifier in identifiers:
                for property_name in properties:
                    keys.add(f"{identifier}|{property_name}")

        return keys

    def is_fixable_issue(self, element_name: str, property_name: str, fixable_keys: set[str]) -> bool:
        """
        Match one dashboard row against the auto-fix lookup set.

        :param element_name: Element display name in the dashboard row
        :param property_name: Property name in the dashboard row
        :param fixable_keys: Lookup set built from fixable errors
        :return: True when the row is fixable
        """
        compound_key: str = f"{element_name}|{property_name}"
        if compound_key in fixable_keys:
            return True
        else:
            return False

    def run_sigma_analysis(self) -> Tuple[Optional[SigmaAnalysisResults], str]:
        """
        Execute sigma analysis with the current power-flow options.

        :return: Results object and execution status text
        """
        results: Optional[SigmaAnalysisResults] = None
        status_text: str

        # Refuse to execute sigma when the backend already knows the circuit is not simulation-ready.
        if self.circuit.valid_for_simulation():
            try:
                sigma_driver: SigmaAnalysisDriver = SigmaAnalysisDriver(grid=self.circuit,
                                                                       options=self.power_flow_options)
                sigma_driver.run()
                results = sigma_driver.results

                if results is not None:
                    bus_names: np.ndarray = np.array([bus.name for bus in self.circuit.buses], dtype=object)
                    if len(bus_names) == len(results.bus_names):
                        results.bus_names = bus_names
                    else:
                        pass

                    if results.converged:
                        status_text = self.tr("Sigma analysis converged.")
                    else:
                        status_text = self.tr("Sigma coefficients did not fully converge.")
                else:
                    status_text = self.tr("Sigma analysis returned no results.")
            except Exception as exception:
                results = None
                status_text = self.tr("Sigma analysis failed: {exception}").format(exception=exception)
        else:
            status_text = self.tr("Sigma analysis unavailable because the grid is not valid for simulation.")

        return results, status_text

    def build_summary(self, sigma_status_text: str) -> DashboardSummary:
        """
        Synthesize the dashboard score and the main summary metrics.

        :param sigma_status_text: Human-readable sigma status
        :return: Dashboard summary record
        """
        # Count severities explicitly because the dashboard exposes them directly in the cards and report.
        error_count: int = 0
        warning_count: int = 0
        information_count: int = 0
        divergence_count: int = 0

        for issue in self.issue_entries:
            if issue.severity == LogSeverity.Error:
                error_count += 1
            else:
                if issue.severity == LogSeverity.Warning:
                    warning_count += 1
                else:
                    if issue.severity == LogSeverity.Information:
                        information_count += 1
                    else:
                        divergence_count += 1

        critical_count: int = error_count + divergence_count
        fixable_count: int = len(self.fixable_errors)
        asset_count: int = self.compute_asset_count()
        issue_score: float = self.compute_issue_score(error_count=error_count,
                                                      warning_count=warning_count,
                                                      information_count=information_count,
                                                      divergence_count=divergence_count,
                                                      asset_count=asset_count)

        # Blend sigma health only when the backend produced sigma data successfully.
        sigma_available: bool = False
        sigma_score: float = 0.0
        min_sigma_distance: float = 0.0
        mean_sigma_distance: float = 0.0
        if self.sigma_results is not None:
            sigma_available = True
            sigma_score, min_sigma_distance, mean_sigma_distance = self.compute_sigma_score(self.sigma_results)
        else:
            sigma_available = False

        overall_score: int
        if sigma_available:
            weighted_score: float = (0.75 * issue_score) + (0.25 * sigma_score)
            overall_score = int(round(clamp_value(weighted_score, 0.0, 100.0)))
        else:
            overall_score = int(round(clamp_value(issue_score, 0.0, 100.0)))

        grade: str = grade_from_score(overall_score)
        top_message: str
        top_message_count: int
        top_message, top_message_count = self.get_top_message()

        return DashboardSummary(
            issue_count=len(self.issue_entries),
            critical_count=critical_count,
            error_count=error_count,
            warning_count=warning_count,
            information_count=information_count,
            divergence_count=divergence_count,
            fixable_count=fixable_count,
            asset_count=asset_count,
            issue_score=issue_score,
            sigma_score=sigma_score,
            overall_score=overall_score,
            grade=grade,
            sigma_available=sigma_available,
            sigma_status_text=sigma_status_text,
            min_sigma_distance=min_sigma_distance,
            mean_sigma_distance=mean_sigma_distance,
            top_message=top_message,
            top_message_count=top_message_count,
        )

    def compute_asset_count(self) -> int:
        """
        Count the main assets inspected by the dashboard.

        :return: Asset count
        """
        # Use an explicit count so the score scaling grows with the modeled system size.
        count: int = 0
        count += len(self.circuit.get_buses())
        count += len(self.circuit.get_lines())
        count += len(self.circuit.get_transformers2w())
        count += len(self.circuit.get_windings())
        count += len(self.circuit.get_loads())
        count += len(self.circuit.get_generators())
        count += len(self.circuit.get_batteries())
        count += len(self.circuit.get_static_generators())
        count += len(self.circuit.get_shunts())
        return count

    def compute_issue_score(self,
                            error_count: int,
                            warning_count: int,
                            information_count: int,
                            divergence_count: int,
                            asset_count: int) -> float:
        """
        Compute the score component driven by grid diagnostics.

        :param error_count: Number of errors
        :param warning_count: Number of warnings
        :param information_count: Number of informational messages
        :param divergence_count: Number of divergences
        :param asset_count: Number of analyzed assets
        :return: Score in the interval [0, 100]
        """
        # Weight severe problems more strongly while still scaling by system size.
        penalty: float = (
            (12.0 * float(error_count))
            + (4.0 * float(warning_count))
            + (0.1 * float(information_count))
            + (16.0 * float(divergence_count))
        )

        # Use a square-root scale so large models are not punished only for being large.
        asset_scale: float = max(3.0, math.sqrt(float(max(asset_count, 1))) * 1.8)
        score: float = 100.0 - ((penalty / asset_scale) * 10.0)
        return clamp_value(score, 0.0, 100.0)

    def compute_sigma_score(self, results: SigmaAnalysisResults) -> Tuple[float, float, float]:
        """
        Compute the sigma-driven score component and key summary statistics.

        :param results: Sigma analysis results
        :return: Sigma score, minimum distance and mean distance
        """
        # Sigma distances are already a margin-like metric, so the score comes from normalized distances.
        distances: np.ndarray = np.abs(np.nan_to_num(results.distances, nan=0.0, posinf=0.0, neginf=0.0))
        if distances.size > 0:
            min_distance: float = float(np.min(distances))
            mean_distance: float = float(np.mean(distances))
        else:
            min_distance = 0.0
            mean_distance = 0.0

        normalized_margin: float = ((0.65 * min_distance) + (0.35 * mean_distance)) / 0.25
        sigma_score: float = clamp_value(normalized_margin * 100.0, 0.0, 100.0)
        if results.converged:
            return sigma_score, min_distance, mean_distance
        else:
            sigma_score = clamp_value(sigma_score - 20.0, 0.0, 100.0)
            return sigma_score, min_distance, mean_distance

    def get_top_message(self) -> Tuple[str, int]:
        """
        Extract the most repeated dashboard message.

        :return: Message text and occurrence count
        """
        # Count messages because repeated issue families are usually the best next-action clue.
        counts: dict[str, int] = dict()
        for issue in self.issue_entries:
            current_count: Optional[int] = counts.get(issue.message, None)
            if current_count is None:
                counts[issue.message] = 1
            else:
                counts[issue.message] = current_count + 1

        best_message: str = ""
        best_count: int = 0
        for message, count in counts.items():
            if count > best_count:
                best_message = message
                best_count = count
            else:
                pass

        return best_message, best_count

    def update_score_cards(self) -> None:
        """
        Push the synthesized summary metrics into the dashboard cards.
        """
        # Update the hero cards first because they provide the user-facing summary at a glance.
        self.ui.scoreValueLabel.setText(str(self.summary.overall_score))
        self.ui.scoreGradeLabel.setText(self.tr("Grade {grade}").format(grade=self.summary.grade))
        self.ui.scoreProgressBar.setValue(self.summary.overall_score)
        self.ui.issueCountValueLabel.setText(str(self.summary.issue_count))
        self.ui.criticalCountValueLabel.setText(str(self.summary.critical_count))
        self.ui.fixableCountValueLabel.setText(str(self.summary.fixable_count))

        # Surface the most useful sigma metric directly on the top row when available.
        if self.summary.sigma_available:
            self.ui.sigmaHealthValueLabel.setText(f"{self.summary.min_sigma_distance:.3f}")
            self.ui.sigmaFootnoteLabel.setText(
                self.tr("Minimum distance {min_distance:.3f} p.u. • "
                        "mean distance {mean_distance:.3f} p.u.").format(
                    min_distance=self.summary.min_sigma_distance,
                    mean_distance=self.summary.mean_sigma_distance,
                )
            )
        else:
            self.ui.sigmaHealthValueLabel.setText(self.tr("N/A"))
            self.ui.sigmaFootnoteLabel.setText(
                self.tr("Sigma analysis could not be produced for the current grid state.")
            )

        # Keep the score explanation explicit so users understand what the dashboard is scoring.
        if self.summary.sigma_available:
            self.ui.scoreExplainerLabel.setText(
                self.tr("Issue score {issue_score:.1f}/100 • sigma score {sigma_score:.1f}/100.").format(
                    issue_score=self.summary.issue_score,
                    sigma_score=self.summary.sigma_score,
                )
            )
        else:
            self.ui.scoreExplainerLabel.setText(
                self.tr("Issue score {issue_score:.1f}/100 • sigma score unavailable.").format(
                    issue_score=self.summary.issue_score,
                )
            )

    def refresh_issue_table(self) -> None:
        """
        Rebuild the findings tree according to the live dashboard filters.
        """
        # Read filters once so the same criteria are applied to every row consistently.
        search_text: str = self.ui.issueSearchLineEdit.text().strip().lower()
        severity_filter_text: str = self.ui.severityFilterComboBox.currentText()
        object_type_filter_text: str = self.ui.objectTypeFilterComboBox.currentText()
        fixable_only: bool = self.ui.fixableOnlyCheckBox.isChecked()

        filtered_issues: List[IssueEntry] = list()
        for issue in self.issue_entries:
            if issue.matches_filters(search_text=search_text,
                                     severity_filter_text=severity_filter_text,
                                     object_type_filter_text=object_type_filter_text,
                                     fixable_only=fixable_only):
                filtered_issues.append(issue)
            else:
                pass

        # Rebuild the model from scratch because the dashboard issue set is usually small-to-medium.
        self.issue_model.removeRows(0, self.issue_model.rowCount())

        current_severity_text: str = ""
        current_message_text: str = ""
        current_object_text: str = ""
        severity_item: Optional[QtGui.QStandardItem] = None
        message_item: Optional[QtGui.QStandardItem] = None
        object_item: Optional[QtGui.QStandardItem] = None

        for issue in filtered_issues:
            severity_text: str = severity_to_text(issue.severity)
            if issue.object_type != "":
                object_text: str = issue.object_type
            else:
                object_text = issue.element_name

            if severity_text != current_severity_text:
                severity_item = self.build_group_item(severity_text, issue.severity)
                self.issue_model.appendRow([severity_item] + self.build_empty_issue_columns())
                current_severity_text = severity_text
                current_message_text = ""
                current_object_text = ""
                message_item = None
                object_item = None
            else:
                pass

            if message_item is None:
                pass
            else:
                if issue.message == current_message_text:
                    pass
                else:
                    message_item = None
                    current_object_text = ""
                    object_item = None

            if message_item is None:
                message_item = self.build_group_item(issue.message, issue.severity)
                severity_item.appendRow([message_item] + self.build_empty_issue_columns())
                current_message_text = issue.message
            else:
                pass

            if object_item is None:
                pass
            else:
                if object_text == current_object_text:
                    pass
                else:
                    object_item = None

            if object_item is None:
                object_item = self.build_group_item(object_text, issue.severity)
                message_item.appendRow([object_item] + self.build_empty_issue_columns())
                current_object_text = object_text
            else:
                pass

            row_items: List[QtGui.QStandardItem] = self.build_issue_row_items(issue)
            object_item.appendRow(row_items)

        # Keep the current findings count visible in the section title after filtering.
        filtered_count: int = len(filtered_issues)
        self.ui.findingsTitleLabel.setText(self.tr("Findings ({count})").format(count=filtered_count))
        self.ui.mainTabWidget.setTabText(self.ui.mainTabWidget.indexOf(self.ui.findingsPage),
                                         self.tr("Findings Explorer ({count})").format(count=filtered_count))
        self.ui.mainTabWidget.setTabText(self.ui.mainTabWidget.indexOf(self.ui.narrativePage),
                                         self.tr("Action Narrative"))
        self.ui.issuesTreeView.expandToDepth(1)

    def build_empty_issue_columns(self) -> List[QtGui.QStandardItem]:
        """
        Build the empty trailing columns used by one group row in the findings tree.

        :return: Empty item list for the non-label columns
        """
        items: List[QtGui.QStandardItem] = list()
        for _ in range(6):
            item: QtGui.QStandardItem = QtGui.QStandardItem("")
            item.setEditable(False)
            items.append(item)
        return items

    def build_group_item(self, text: str, severity: LogSeverity) -> QtGui.QStandardItem:
        """
        Build one group-row item for the findings tree.

        :param text: Group label text
        :param severity: Severity associated with the group
        :return: Styled tree item
        """
        item: QtGui.QStandardItem = QtGui.QStandardItem(text)
        item.setEditable(False)
        font: QtGui.QFont = item.font()
        font.setBold(True)
        item.setFont(font)

        if severity == LogSeverity.Error:
            if self.theme_is_dark:
                item.setForeground(QtGui.QBrush(QtGui.QColor("#ffd2c8")))
            else:
                item.setForeground(QtGui.QBrush(QtGui.QColor("#8b2c13")))
        else:
            if severity == LogSeverity.Warning:
                if self.theme_is_dark:
                    item.setForeground(QtGui.QBrush(QtGui.QColor("#ffe7a6")))
                else:
                    item.setForeground(QtGui.QBrush(QtGui.QColor("#885500")))
            else:
                if severity == LogSeverity.Information:
                    if self.theme_is_dark:
                        item.setForeground(QtGui.QBrush(QtGui.QColor("#c7e5ff")))
                    else:
                        item.setForeground(QtGui.QBrush(QtGui.QColor("#1f5278")))
                else:
                    if self.theme_is_dark:
                        item.setForeground(QtGui.QBrush(QtGui.QColor("#ffd6e3")))
                    else:
                        item.setForeground(QtGui.QBrush(QtGui.QColor("#8a2243")))

        return item

    def build_issue_row_items(self, issue: IssueEntry) -> List[QtGui.QStandardItem]:
        """
        Convert one normalized issue into tree-leaf items with dashboard styling.

        :param issue: Issue entry
        :return: Row items
        """
        # Put the detailed issue data on one leaf row under its severity, message and object groups.
        values: List[str] = [
            issue.element_name,
            issue.property_name,
            issue.lower,
            issue.value,
            issue.upper,
            str(issue.element_index),
            self.tr("Yes") if issue.fixable else self.tr("No"),
        ]
        items: List[QtGui.QStandardItem] = list()
        for value in values:
            item: QtGui.QStandardItem = QtGui.QStandardItem(value)
            item.setEditable(False)
            items.append(item)

        # Color the leading leaf label so high-priority rows are still obvious inside the grouped tree.
        if issue.severity == LogSeverity.Error:
            if self.theme_is_dark:
                brush: QtGui.QBrush = QtGui.QBrush(QtGui.QColor("#5a2d24"))
                foreground: QtGui.QBrush = QtGui.QBrush(QtGui.QColor("#ffd2c8"))
            else:
                brush = QtGui.QBrush(QtGui.QColor("#ffe5df"))
                foreground = QtGui.QBrush(QtGui.QColor("#8b2c13"))
        else:
            if issue.severity == LogSeverity.Warning:
                if self.theme_is_dark:
                    brush = QtGui.QBrush(QtGui.QColor("#564723"))
                    foreground = QtGui.QBrush(QtGui.QColor("#ffe7a6"))
                else:
                    brush = QtGui.QBrush(QtGui.QColor("#fff3da"))
                    foreground = QtGui.QBrush(QtGui.QColor("#885500"))
            else:
                if issue.severity == LogSeverity.Information:
                    if self.theme_is_dark:
                        brush = QtGui.QBrush(QtGui.QColor("#24384f"))
                        foreground = QtGui.QBrush(QtGui.QColor("#c7e5ff"))
                    else:
                        brush = QtGui.QBrush(QtGui.QColor("#e8f2fb"))
                        foreground = QtGui.QBrush(QtGui.QColor("#1f5278"))
                else:
                    if self.theme_is_dark:
                        brush = QtGui.QBrush(QtGui.QColor("#522b3f"))
                        foreground = QtGui.QBrush(QtGui.QColor("#ffd6e3"))
                    else:
                        brush = QtGui.QBrush(QtGui.QColor("#fde7ef"))
                        foreground = QtGui.QBrush(QtGui.QColor("#8a2243"))

        items[0].setBackground(brush)
        items[0].setForeground(foreground)

        if issue.fixable:
            if self.theme_is_dark:
                items[6].setBackground(QtGui.QBrush(QtGui.QColor("#173e36")))
                items[6].setForeground(QtGui.QBrush(QtGui.QColor("#bff2e1")))
            else:
                items[6].setBackground(QtGui.QBrush(QtGui.QColor("#def7ea")))
                items[6].setForeground(QtGui.QBrush(QtGui.QColor("#0b6b4b")))
        else:
            pass

        return items

    def update_sigma_panel(self) -> None:
        """
        Refresh the sigma plot and sigma status copy.
        """
        # Always clear the plot first because sigma availability may change between runs.
        self.ui.sigmaPlotWidget.clear(force=True)
        axis = self.ui.sigmaPlotWidget.get_axis()
        figure = self.ui.sigmaPlotWidget.get_figure()
        if self.theme_is_dark:
            figure_facecolor: str = "#1f2630"
            axis_facecolor: str = "#171c24"
            grid_color: str = "#455365"
            label_color: str = "#e7edf5"
            boundary_line_color: str = "#d8e3ee"
        else:
            figure_facecolor = "#ffffff"
            axis_facecolor = "#f7fbff"
            grid_color = "#dce7f2"
            label_color = "#17324a"
            boundary_line_color = "#102235"

        figure.set_facecolor(figure_facecolor)
        axis.set_facecolor(axis_facecolor)

        if self.sigma_results is not None:
            self.sigma_results.plot(figure, axis)
            self.apply_sigma_plot_theme(axis=axis,
                                        label_color=label_color,
                                        grid_color=grid_color,
                                        boundary_line_color=boundary_line_color)
            figure.tight_layout()
            self.ui.sigmaPlotWidget.redraw()
            self.populate_sigma_table()

            sigma_status_text: str = (
                self.tr("{status_text} Min distance {min_distance:.3f} p.u. • "
                        "mean distance {mean_distance:.3f} p.u.").format(
                    status_text=self.summary.sigma_status_text,
                    min_distance=self.summary.min_sigma_distance,
                    mean_distance=self.summary.mean_sigma_distance,
                )
            )
            self.ui.sigmaStatusLabel.setText(sigma_status_text)
        else:
            self.sigma_model = None
            axis.text(
                0.5,
                0.5,
                self.summary.sigma_status_text,
                ha="center",
                va="center",
                fontsize=12,
                color=label_color,
                transform=axis.transAxes,
            )
            axis.set_xticks(list())
            axis.set_yticks(list())
            axis.set_frame_on(False)
            figure.tight_layout()
            self.ui.sigmaPlotWidget.redraw()
            self.ui.sigmaStatusLabel.setText(self.summary.sigma_status_text)
        self.ui.mainTabWidget.setTabText(self.ui.mainTabWidget.indexOf(self.ui.sigmaPage),
                                         self.tr("Sigma Stability"))
        self.ui.mainTabWidget.setTabText(self.ui.mainTabWidget.indexOf(self.ui.controlsPage),
                                         self.tr("Assessment Controls"))

    def apply_sigma_plot_theme(self,
                               axis,
                               label_color: str,
                               grid_color: str,
                               boundary_line_color: str) -> None:
        """
        Restyle the sigma plot after the sigma backend populates it.

        :param axis: Matplotlib axis to retheme
        :param label_color: Theme text color
        :param grid_color: Theme grid color
        :param boundary_line_color: Theme color for the sigma boundary curves
        """
        # Update axes and grid colors because the sigma backend draws with Matplotlib defaults.
        axis.grid(True, color=grid_color, linewidth=0.7)
        axis.tick_params(axis="x", colors=label_color)
        axis.tick_params(axis="y", colors=label_color)
        axis.title.set_color(label_color)
        axis.xaxis.label.set_color(label_color)
        axis.yaxis.label.set_color(label_color)

        for spine in axis.spines.values():
            spine.set_color(grid_color)

        for index, line in enumerate(axis.lines):
            if index < 2:
                line.set_color(boundary_line_color)
            else:
                pass

    def populate_sigma_table(self) -> None:
        """
        Build the sigma data model from the current sigma results.
        """
        # Keep the sigma data model for export and clipboard actions even though the visible table was removed.
        if self.sigma_results is not None:
            bus_names: np.ndarray = np.array([bus.name for bus in self.circuit.buses], dtype=object)
            n_rows: int = len(bus_names)
            sigma_results_table = self.sigma_results.mdl(
                result_type=ResultTypes.SigmaPlusDistances,
                indices=np.arange(n_rows),
                names=bus_names,
            )

            if sigma_results_table is not None:
                self.sigma_model = ResultsModel(sigma_results_table)
            else:
                self.sigma_model = None
        else:
            self.sigma_model = None

    def update_narrative(self) -> None:
        """
        Rebuild the dashboard recommendation and score explanation panel.
        """
        # The narrative panel translates the raw findings into a concise action list.
        report_html: str = self.build_narrative_html()
        self.ui.narrativeBrowser.setHtml(report_html)

    def build_narrative_html(self) -> str:
        """
        Build the narrative HTML shown inside the dashboard recommendation panel.

        :return: HTML fragment
        """
        # Start with the score rationale because that is the dashboard's main promise.
        if self.theme_is_dark:
            body_text_color: str = "#e7edf5"
            heading_text_color: str = "#f4f8fb"
        else:
            body_text_color = "#17324a"
            heading_text_color = "#102235"

        parts: List[str] = list()
        parts.append(f"<div style='font-family: DejaVu Sans; color: {body_text_color};'>")
        parts.append(
            f"<h3 style='margin-top: 0px; color: {heading_text_color};'>{self.tr('Score Rationale')}</h3>"
        )
        parts.append(
            "<p>"
            + self.tr("The grid scores <b>{overall_score}/100</b> "
                      "(<b>grade {grade}</b>) across <b>{asset_count}</b> analyzed assets.").format(
                overall_score=self.summary.overall_score,
                grade=html.escape(self.summary.grade),
                asset_count=self.summary.asset_count,
            )
            + "</p>"
        )

        # Explain what is driving the score numerically.
        parts.append("<ul>")
        parts.append(
            "<li>"
            + self.tr("<b>{error_count}</b> errors and <b>{divergence_count}</b> divergences are blocking the score most strongly.").format(
                error_count=self.summary.error_count,
                divergence_count=self.summary.divergence_count,
            )
            + "</li>"
        )
        parts.append(
            "<li>"
            + self.tr("<b>{warning_count}</b> warnings and <b>{information_count}</b> informational findings still reduce confidence.").format(
                warning_count=self.summary.warning_count,
                information_count=self.summary.information_count,
            )
            + "</li>"
        )
        parts.append(
            "<li>"
            + self.tr("<b>{fixable_count}</b> findings can be auto-corrected safely from this dashboard.").format(
                fixable_count=self.summary.fixable_count,
            )
            + "</li>"
        )
        if self.summary.sigma_available:
            parts.append(
                "<li>"
                + self.tr("Sigma stability margin is available with minimum distance <b>{min_distance:.3f} p.u.</b> "
                          "and mean distance <b>{mean_distance:.3f} p.u.</b>.").format(
                    min_distance=self.summary.min_sigma_distance,
                    mean_distance=self.summary.mean_sigma_distance,
                )
                + "</li>"
            )
        else:
            parts.append(
                "<li>"
                + self.tr("Sigma stability could not be included in the score because the simulation could not be produced.")
                + "</li>"
            )
        parts.append("</ul>")

        # Show the most repeated issue family because repeated patterns often define the best first move.
        if self.summary.top_message_count > 0:
            parts.append(
                f"<h3 style='color: {heading_text_color};'>{self.tr('Most Repeated Finding')}</h3>"
            )
            parts.append(
                f"<p><b>{self.summary.top_message_count}×</b> "
                f"{html.escape(self.summary.top_message)}</p>"
            )
        else:
            parts.append(
                f"<h3 style='color: {heading_text_color};'>{self.tr('Most Repeated Finding')}</h3>"
            )
            parts.append(f"<p>{self.tr('No findings were produced by the current analysis settings.')}</p>")

        # Finish with explicit next actions so the dashboard is operational rather than decorative.
        parts.append(
            f"<h3 style='color: {heading_text_color};'>{self.tr('Recommended Next Actions')}</h3>"
        )
        parts.append("<ol>")
        if self.summary.fixable_count > 0:
            parts.append(
                "<li>"
                + self.tr("Use <b>Fix Safe Issues</b> to correct the problems already covered by automatic repairs, then refresh the score.")
                + "</li>"
            )
        else:
            parts.append(
                "<li>"
                + self.tr("No safe automatic fixes were detected, so the next step is a manual review of the highest-severity findings.")
                + "</li>"
            )
        if self.summary.critical_count > 0:
            parts.append(
                "<li>"
                + self.tr("Prioritize errors and divergences before warnings, especially the rows tagged with severe numerical or connectivity issues.")
                + "</li>"
            )
        else:
            parts.append(
                "<li>"
                + self.tr("There are no critical findings, so the remaining work is mainly quality hardening and model cleanup.")
                + "</li>"
            )
        if self.summary.sigma_available:
            if self.summary.min_sigma_distance < 0.10:
                parts.append(
                    "<li>"
                    + self.tr("Investigate buses with the smallest sigma distances because the current stability margin is tight.")
                    + "</li>"
                )
            else:
                parts.append(
                    "<li>"
                    + self.tr("Sigma margin is acceptable, so focus on structural cleanup before attempting aggressive operational studies.")
                    + "</li>"
                )
        else:
            parts.append(
                "<li>"
                + self.tr("Make the grid simulation-ready and rerun the dashboard so sigma margin can join the report.")
                + "</li>"
            )
        parts.append(
            "<li>"
            + self.tr("Export the full report once the score and findings reflect the scenario you want to share.")
            + "</li>"
        )
        parts.append("</ol>")
        parts.append("</div>")
        return "".join(parts)

    def copy_sigma_to_clipboard(self) -> None:
        """
        Copy the sigma table to the clipboard.
        """
        # Reuse the existing results model capability when sigma data is available.
        if self.sigma_model is not None:
            self.sigma_model.copy_to_clipboard()
            self.statusBar().showMessage(self.tr("Sigma table copied to clipboard."), 5000)
        else:
            self.show_information_message(self.tr("There is no sigma table available to copy."),
                                          self.tr("Sigma table"))

    def fix_all(self) -> None:
        """
        Execute all safe automatic fixes and refresh the dashboard.
        """
        # Refuse to execute a fix pass when the current analysis did not detect supported fixes.
        if len(self.fixable_errors) > 0:
            logger: Logger = Logger()
            for fixable_error in self.fixable_errors:
                fixable_error.fix(logger=logger, fix_ts=self.ui.fixTimeSeriesCheckBox.isChecked())

            if logger.has_logs():
                dialogue: LogsDialogue = LogsDialogue(self.tr("Fixed issues"), logger)
                dialogue.setModal(True)
                dialogue.exec()
            else:
                pass

            self.analyze_all()
        else:
            self.show_information_message(
                self.tr("The current dashboard state does not expose any safe automatic fixes."),
                self.tr("Fix safe issues"),
            )

    def save_diagnostic(self) -> None:
        """
        Export only the diagnostic issue list and summary as an Excel workbook.
        """
        # Keep the legacy behavior available, but augment it with the current score summary.
        file_types: str = self.tr("Excel (*.xlsx)")
        default_name: str = "grid_diagnostics_dashboard.xlsx"
        file_name: str
        selected_filter: str
        file_name, selected_filter = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                           self.tr("Export issues only"),
                                                                           default_name,
                                                                           file_types)

        if file_name != "":
            if file_name.endswith(".xlsx"):
                final_name: str = file_name
            else:
                final_name = f"{file_name}.xlsx"

            with pd.ExcelWriter(final_name) as excel_writer:
                self.build_summary_data_frame().to_excel(excel_writer, sheet_name=self.tr("Summary"), index=False)
                self.build_issue_data_frame().to_excel(excel_writer, sheet_name=self.tr("Issues"), index=False)
            self.statusBar().showMessage(self.tr("Issues exported to {file_name}.").format(file_name=final_name), 8000)
        else:
            pass

    def export_report(self) -> None:
        """
        Export the dashboard report as Excel, HTML or PDF.
        """
        # Offer portable report formats because the dashboard is meant to be shared outside the GUI.
        file_types: str = self.tr("Excel (*.xlsx);;HTML (*.html);;PDF (*.pdf)")
        default_name: str = "grid_health_dashboard_report.pdf"
        file_name: str
        selected_filter: str
        file_name, selected_filter = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                           self.tr("Export full report"),
                                                                           default_name,
                                                                           file_types)

        if file_name != "":
            if "html" in selected_filter.lower():
                final_name: str
                if file_name.endswith(".html"):
                    final_name = file_name
                else:
                    final_name = f"{file_name}.html"
                self.export_report_to_html(final_name)
            else:
                if "pdf" in selected_filter.lower():
                    if file_name.endswith(".pdf"):
                        final_name = file_name
                    else:
                        final_name = f"{file_name}.pdf"
                    self.export_report_to_pdf(final_name)
                else:
                    if file_name.endswith(".xlsx"):
                        final_name = file_name
                    else:
                        final_name = f"{file_name}.xlsx"
                    self.export_report_to_excel(final_name)
        else:
            pass

    def export_report_to_excel(self, file_name: str) -> None:
        """
        Export the full dashboard report to Excel.

        :param file_name: Destination file name
        """
        # Write separate sheets so the report is useful both for reading and for follow-up analysis.
        with pd.ExcelWriter(file_name) as excel_writer:
            self.build_summary_data_frame().to_excel(excel_writer, sheet_name=self.tr("Summary"), index=False)
            self.build_thresholds_data_frame().to_excel(excel_writer, sheet_name=self.tr("Thresholds"), index=False)
            self.build_issue_data_frame().to_excel(excel_writer, sheet_name=self.tr("Issues"), index=False)
            self.build_sigma_data_frame().to_excel(excel_writer, sheet_name=self.tr("Sigma"), index=False)

        self.statusBar().showMessage(
            self.tr("Full dashboard report exported to {file_name}.").format(file_name=file_name),
            8000,
        )

    def export_report_to_html(self, file_name: str) -> None:
        """
        Export the full dashboard report to HTML.

        :param file_name: Destination file name
        """
        # Build the HTML report in memory so the export stays deterministic and easy to test.
        html_report: str = self.build_html_report()
        with open(file_name, "w", encoding="utf-8") as file_handle:
            file_handle.write(html_report)

        self.statusBar().showMessage(
            self.tr("Full dashboard report exported to {file_name}.").format(file_name=file_name),
            8000,
        )

    def export_report_to_pdf(self, file_name: str) -> None:
        """
        Export the full dashboard report to PDF.

        :param file_name: Destination file name
        """
        # Reuse the HTML report so PDF stays aligned with the shareable dashboard layout.
        html_report: str = self.build_html_report()
        document: QtGui.QTextDocument = QtGui.QTextDocument()
        document.setHtml(html_report)

        pdf_writer: QtGui.QPdfWriter = QtGui.QPdfWriter(file_name)
        pdf_writer.setPageSize(QtGui.QPageSize(QtGui.QPageSize.PageSizeId.A4))
        pdf_writer.setPageOrientation(QtGui.QPageLayout.Orientation.Portrait)
        pdf_writer.setResolution(96)
        pdf_writer.setPageMargins(QtCore.QMarginsF(16.0, 16.0, 16.0, 16.0),
                                  QtGui.QPageLayout.Unit.Millimeter)

        paint_rect: QtCore.QRect = pdf_writer.pageLayout().paintRectPixels(pdf_writer.resolution())
        document.setPageSize(QtCore.QSizeF(float(paint_rect.width()), float(paint_rect.height())))
        document.print_(pdf_writer)

        self.statusBar().showMessage(
            self.tr("Full dashboard report exported to {file_name}.").format(file_name=file_name),
            8000,
        )

    def build_summary_data_frame(self) -> pd.DataFrame:
        """
        Convert the current summary into a simple report table.

        :return: Summary data frame
        """
        # Represent the summary as key-value rows because that layout exports cleanly to both Excel and HTML.
        rows: List[List[object]] = list()
        rows.append([self.tr("Overall score"), self.summary.overall_score])
        rows.append([self.tr("Grade"), self.summary.grade])
        rows.append([self.tr("Issue score"), round(self.summary.issue_score, 3)])
        rows.append([self.tr("Sigma score"), round(self.summary.sigma_score, 3)])
        rows.append([self.tr("Total findings"), self.summary.issue_count])
        rows.append([self.tr("Critical findings"), self.summary.critical_count])
        rows.append([self.tr("Errors"), self.summary.error_count])
        rows.append([self.tr("Warnings"), self.summary.warning_count])
        rows.append([self.tr("Information"), self.summary.information_count])
        rows.append([self.tr("Divergences"), self.summary.divergence_count])
        rows.append([self.tr("Auto-fix ready"), self.summary.fixable_count])
        rows.append([self.tr("Analyzed assets"), self.summary.asset_count])
        rows.append([self.tr("Sigma available"), self.summary.sigma_available])
        rows.append([self.tr("Sigma status"), self.summary.sigma_status_text])
        rows.append([self.tr("Minimum sigma distance"), round(self.summary.min_sigma_distance, 6)])
        rows.append([self.tr("Mean sigma distance"), round(self.summary.mean_sigma_distance, 6)])
        rows.append([self.tr("Most repeated finding"), self.summary.top_message])
        rows.append([self.tr("Most repeated finding count"), self.summary.top_message_count])
        return pd.DataFrame(rows, columns=[self.tr("Metric"), self.tr("Value")])

    def build_thresholds_data_frame(self) -> pd.DataFrame:
        """
        Convert the current dashboard thresholds into a report table.

        :return: Threshold data frame
        """
        # Report the exact thresholds used so exported scores remain auditable.
        rows: List[List[object]] = list()
        rows.append([self.tr("Active power imbalance (%)"), self.ui.activePowerImbalanceSpinBox.value()])
        rows.append([self.tr("Generator Vset min"), self.ui.genVsetMinSpinBox.value()])
        rows.append([self.tr("Generator Vset max"), self.ui.genVsetMaxSpinBox.value()])
        rows.append([self.tr("Transformer tap module min"), self.ui.transformerTapModuleMinSpinBox.value()])
        rows.append([self.tr("Transformer tap module max"), self.ui.transformerTapModuleMaxSpinBox.value()])
        rows.append([self.tr("Virtual tap tolerance (%)"), self.ui.virtualTapToleranceSpinBox.value()])
        rows.append([self.tr("Line voltage mismatch tolerance (%)"), self.ui.lineNominalVoltageToleranceSpinBox.value()])
        rows.append([self.tr("Transformer Vcc min (%)"), self.ui.transformerVccMinSpinBox.value()])
        rows.append([self.tr("Transformer Vcc max (%)"), self.ui.transformerVccMaxSpinBox.value()])
        rows.append([self.tr("Apply fixes to time series"), self.ui.fixTimeSeriesCheckBox.isChecked()])
        return pd.DataFrame(rows, columns=[self.tr("Threshold"), self.tr("Value")])

    def build_issue_data_frame(self) -> pd.DataFrame:
        """
        Convert the current dashboard issue list into a report table.

        :return: Issue data frame
        """
        # Preserve every visible issue column because the report must be enough to act on offline.
        rows: List[List[object]] = list()
        for issue in self.issue_entries:
            rows.append([
                severity_to_text(issue.severity),
                issue.message,
                issue.object_type,
                issue.element_name,
                issue.property_name,
                issue.lower,
                issue.value,
                issue.upper,
                issue.element_index,
                issue.fixable,
            ])
        return pd.DataFrame(rows,
                            columns=[self.tr("Severity"),
                                     self.tr("Message"),
                                     self.tr("Object"),
                                     self.tr("Name"),
                                     self.tr("Property"),
                                     self.tr("Lower"),
                                     self.tr("Value"),
                                     self.tr("Upper"),
                                     self.tr("Index"),
                                     self.tr("Auto-fix")])

    def build_sigma_data_frame(self) -> pd.DataFrame:
        """
        Convert the current sigma results into a report table.

        :return: Sigma data frame
        """
        # Export the old sigma table verbatim when possible because users already know that layout.
        if self.sigma_model is not None:
            return self.sigma_model.to_df().reset_index()
        else:
            rows: List[List[object]] = list()
            rows.append([self.tr("Status"), self.summary.sigma_status_text])
            return pd.DataFrame(rows, columns=[self.tr("Field"), self.tr("Value")])

    def build_html_report(self) -> str:
        """
        Build a shareable HTML report reflecting the current dashboard state.

        :return: Full HTML report
        """
        # Convert each report section independently so the final document is easy to inspect and maintain.
        summary_table_html: str = self.build_summary_data_frame().to_html(index=False, border=0)
        thresholds_table_html: str = self.build_thresholds_data_frame().to_html(index=False, border=0)
        issues_table_html: str = self.build_issue_data_frame().to_html(index=False, border=0)
        sigma_table_html: str = self.build_sigma_data_frame().to_html(index=False, border=0)
        sigma_plot_html: str = self.build_sigma_plot_html()
        narrative_html: str = self.build_narrative_html()

        # Compose a lightweight website-like report so exported results match the dashboard spirit.
        parts: List[str] = list()
        parts.append("<html><head><meta charset='utf-8'>")
        parts.append(f"<title>{self.tr('Grid Health Dashboard Report')}</title>")
        parts.append("<style>")
        parts.append("body { background:#f3f7fb; color:#17324a; font-family:'DejaVu Sans'; margin:0; }")
        parts.append(".page { max-width:1360px; margin:0 auto; padding:24px; }")
        parts.append(".hero { background:linear-gradient(135deg,#0d344f,#135a7c,#1f8a70); color:#ffffff; padding:28px; border-radius:28px; }")
        parts.append(".grid { display:grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap:14px; margin-top:18px; }")
        parts.append(".card, .panel { background:#ffffff; border:1px solid #dce7f2; border-radius:24px; padding:20px; }")
        parts.append(".cardsmall { color:#5e7388; font-size:12px; font-weight:700; text-transform:uppercase; }")
        parts.append(".cardvalue { color:#0d2236; font-size:32px; font-weight:700; margin-top:8px; }")
        parts.append(".panelgrid { display:grid; grid-template-columns: 1.2fr 0.8fr; gap:16px; margin-top:18px; }")
        parts.append(".section { margin-top:18px; }")
        parts.append("table { width:100%; border-collapse:collapse; background:#ffffff; }")
        parts.append("th { background:#eef4f9; color:#23415a; padding:10px; text-align:left; }")
        parts.append("td { border-top:1px solid #edf3f8; padding:10px; vertical-align:top; }")
        parts.append("h1, h2, h3 { margin-top:0px; }")
        parts.append(".plot { margin-top:16px; }")
        parts.append("</style></head><body><div class='page'>")
        parts.append("<div class='hero'>")
        parts.append(
            f"<div style='font-size:12px;font-weight:700;letter-spacing:0.08em;'>{self.tr('SCORING DASHBOARD')}</div>"
        )
        parts.append(f"<h1 style='margin-bottom:8px;'>{self.tr('Grid Health Dashboard Report')}</h1>")
        parts.append(f"<p style='max-width:920px;'>{html.escape(self.summary.sigma_status_text)}</p>")
        parts.append("</div>")
        parts.append("<div class='grid'>")
        parts.append(
            f"<div class='card'><div class='cardsmall'>{self.tr('Overall Score')}</div>"
            f"<div class='cardvalue'>{self.summary.overall_score}</div>"
            f"<div>{self.tr('Grade {grade}').format(grade=html.escape(self.summary.grade))}</div></div>"
        )
        parts.append(
            f"<div class='card'><div class='cardsmall'>{self.tr('Total Findings')}</div>"
            f"<div class='cardvalue'>{self.summary.issue_count}</div>"
            f"<div>{self.tr('{critical_count} critical findings').format(critical_count=self.summary.critical_count)}</div></div>"
        )
        parts.append(
            f"<div class='card'><div class='cardsmall'>{self.tr('Auto-Fix Ready')}</div>"
            f"<div class='cardvalue'>{self.summary.fixable_count}</div>"
            f"<div>{self.tr('Safe corrections available')}</div></div>"
        )
        if self.summary.sigma_available:
            parts.append(
                f"<div class='card'><div class='cardsmall'>{self.tr('Sigma Margin')}</div>"
                f"<div class='cardvalue'>{self.summary.min_sigma_distance:.3f}</div>"
                f"<div>{self.tr('Mean {mean_distance:.3f} p.u.').format(mean_distance=self.summary.mean_sigma_distance)}</div></div>"
            )
        else:
            parts.append(
                f"<div class='card'><div class='cardsmall'>{self.tr('Sigma Margin')}</div>"
                f"<div class='cardvalue'>{self.tr('N/A')}</div>"
                f"<div>{self.tr('Sigma data unavailable')}</div></div>"
            )
        parts.append("</div>")
        parts.append("<div class='panelgrid'>")
        parts.append(
            f"<div class='panel section'><h2>{self.tr('What Needs Attention')}</h2>{narrative_html}</div>"
        )
        parts.append(
            f"<div class='panel section'><h2>{self.tr('Summary')}</h2>{summary_table_html}<div class='plot'>{sigma_plot_html}</div></div>"
        )
        parts.append("</div>")
        parts.append(f"<div class='panel section'><h2>{self.tr('Thresholds')}</h2>{thresholds_table_html}</div>")
        parts.append(f"<div class='panel section'><h2>{self.tr('Findings')}</h2>{issues_table_html}</div>")
        parts.append(f"<div class='panel section'><h2>{self.tr('Sigma Table')}</h2>{sigma_table_html}</div>")
        parts.append("</div></body></html>")
        return "".join(parts)

    def build_sigma_plot_html(self) -> str:
        """
        Export the current sigma plot as an embeddable HTML image.

        :return: HTML fragment containing the plot or a fallback message
        """
        # Reuse the live dashboard plot so the report matches what the user saw before exporting.
        if self.sigma_results is not None:
            image_base64: str = self.get_sigma_plot_base64()
            return (
                f"<h3>{self.tr('Sigma Plot')}</h3>"
                f"<img alt='{self.tr('Sigma plot')}' style='max-width:100%; border-radius:18px; border:1px solid #dce7f2;' "
                f"src='data:image/png;base64,{image_base64}' />"
            )
        else:
            return f"<h3>{self.tr('Sigma Plot')}</h3><p>{self.tr('Sigma plot is unavailable for the current grid state.')}</p>"

    def get_sigma_plot_base64(self) -> str:
        """
        Convert the current sigma figure into a base64-encoded PNG string.

        :return: Base64 image string
        """
        # Write the live figure into an in-memory PNG so HTML export remains self-contained.
        image_buffer: io.BytesIO = io.BytesIO()
        self.ui.sigmaPlotWidget.get_figure().savefig(image_buffer, format="png", dpi=160, bbox_inches="tight")
        image_buffer.seek(0)
        encoded_image: str = base64.b64encode(image_buffer.getvalue()).decode("ascii")
        image_buffer.close()
        return encoded_image

    def show_information_message(self, text: str, title: str) -> None:
        """
        Display a simple informational message box.

        :param text: Message text
        :param title: Message-box title
        """
        # Keep message creation centralized so non-critical UX feedback stays consistent.
        message_box: QtWidgets.QMessageBox = QtWidgets.QMessageBox(self)
        message_box.setIcon(QtWidgets.QMessageBox.Icon.Information)
        message_box.setWindowTitle(title)
        message_box.setText(text)
        message_box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
        message_box.exec()
