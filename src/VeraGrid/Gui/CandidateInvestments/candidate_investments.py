# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING

from PySide6 import QtCore, QtGui, QtWidgets

import VeraGridEngine.Devices as dev
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.Simulations.InvestmentsEvaluation.CandidateGeneration.candidate_generation_driver import (
    CandidateGenerationDriver,
)
from VeraGridEngine.Simulations.InvestmentsEvaluation.CandidateGeneration.candidate_generation_options import (
    CandidateGenerationOptions,
)
from VeraGridEngine.Simulations.InvestmentsEvaluation.CandidateGeneration.candidate_generation_results import (
    ReinforcementCandidate,
)
from VeraGrid.Gui.Diagrams.SchematicWidget.schematic_widget import SchematicWidget
from VeraGrid.Gui.Diagrams.MapWidget.grid_map_widget import GridMapWidget
from VeraGrid.Gui.general_dialogues import LogsDialogue
from VeraGrid.Gui.messages import warning_msg

if TYPE_CHECKING:
    from VeraGrid.Gui.Main.SubClasses.simulations import SimulationsMain


class CandidateInvestmentsWindow(QtWidgets.QDialog):
    """
    Candidate-investment generator window.

    Runs the transmission-expansion candidate-generation pipeline (AC power flow base case ->
    LODF N-1 + voltage screening -> PTDF-ranked reinforcements (new line, upgrade, static
    generator, battery) and voltage-relief reinforcements (shunt reactor) -> shortlist -> AC
    power-flow verification) and lets the user pick which of the ranked candidates to materialise
    as investments, mirroring the ``ProceduralGridWindow`` accept flow.
    """

    def __init__(self, app: SimulationsMain, parent=None):
        """
        :param app: The main application (SimulationsMain).
        :param parent: Optional Qt parent.
        """
        QtWidgets.QDialog.__init__(self, parent)
        self.setWindowTitle('Candidate investment generator')
        self.app = app

        # State of the last successful run. "Add investments" can only run once these are populated.
        self._driver: Optional[CandidateGenerationDriver] = None
        self._candidates: List[ReinforcementCandidate] = list()

        # ------------------------------------------------------------------------------------------
        # Widgets
        # ------------------------------------------------------------------------------------------
        main_layout = QtWidgets.QVBoxLayout(self)

        # --- options row: number of new-line corridors enumerated per violation ---
        options_layout = QtWidgets.QHBoxLayout()
        options_layout.addWidget(QtWidgets.QLabel("Corridors per violation"))
        self.top_n_spin = QtWidgets.QSpinBox()
        self.top_n_spin.setMinimum(1)
        self.top_n_spin.setMaximum(50)
        self.top_n_spin.setValue(5)
        self.top_n_spin.setToolTip("Number of nearby substation corridors enumerated as new-line "
                                   "candidates for each flagged violation.")
        options_layout.addWidget(self.top_n_spin)

        options_layout.addWidget(QtWidgets.QLabel("Candidates to verify"))
        self.verify_top_k_spin = QtWidgets.QSpinBox()
        self.verify_top_k_spin.setMinimum(1)
        self.verify_top_k_spin.setMaximum(50)
        self.verify_top_k_spin.setValue(1)
        self.verify_top_k_spin.setToolTip("Number of top-ranked candidates (by score) verified with "
                                          "a full AC power flow plus N-1 screening. Only verified "
                                          "candidates that introduce no new violations are listed.")
        options_layout.addWidget(self.verify_top_k_spin)
        options_layout.addStretch(1)
        self.run_button = QtWidgets.QPushButton("Run")
        self.run_button.setToolTip("Run the candidate-generation pipeline.")
        self.run_button.clicked.connect(self.run)
        options_layout.addWidget(self.run_button)
        main_layout.addLayout(options_layout)

        # --- base case / N-1 report ---
        main_layout.addWidget(QtWidgets.QLabel("Base case and N-1 screening"))
        self.report_text = QtWidgets.QPlainTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setMaximumHeight(160)
        main_layout.addWidget(self.report_text)

        # --- ranked candidates (checkable) ---
        main_layout.addWidget(QtWidgets.QLabel("Ranked candidate reinforcements"))
        self.candidate_list = QtWidgets.QListWidget()
        main_layout.addWidget(self.candidate_list)

        # --- accept row ---
        accept_layout = QtWidgets.QHBoxLayout()
        accept_layout.addStretch(1)
        self.add_button = QtWidgets.QPushButton("Add investments")
        self.add_button.setToolTip("Add every listed candidate as an investment, each in its own "
                                   "investments group named after the asset.")
        self.add_button.setEnabled(False)
        self.add_button.clicked.connect(self.add_investments)
        accept_layout.addWidget(self.add_button)
        main_layout.addLayout(accept_layout)

        self.setLayout(main_layout)
        self.resize(560, 520)

    # ----------------------------------------------------------------------------------------------
    # Run the pipeline
    # ----------------------------------------------------------------------------------------------
    def run(self) -> None:
        """
        Run the candidate-generation pipeline synchronously and populate the report and the
        ranked candidate list. "Add investments" is enabled only when candidates result.
        """
        self.add_button.setEnabled(False)
        self.candidate_list.clear()
        self._candidates.clear()

        grid = self.app.circuit
        if grid.has_time_series and not self.app.ts_flag():
            warning_msg("This grid model has a time series, activate time series mode to run the "
                       "candidate investments generator feature.")
            self.report_text.setPlainText("")
            return

        self.report_text.setPlainText("Running...")
        QtGui.QGuiApplication.processEvents()

        if grid.has_time_series:
            options = CandidateGenerationOptions(top_n_corridors=self.top_n_spin.value(),
                                                 verify_top_k=self.verify_top_k_spin.value(),
                                                 use_time_series=True,
                                                 time_indices=self.app.get_time_indices())
        else:
            options = CandidateGenerationOptions(top_n_corridors=self.top_n_spin.value(),
                                                 verify_top_k=self.verify_top_k_spin.value())
        pf_options = self.app.get_selected_power_flow_options()

        driver = CandidateGenerationDriver(grid=self.app.circuit,
                                           options=options,
                                           pf_options=pf_options)

        QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.CursorShape.WaitCursor))
        try:
            driver.run()
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

        self._driver = driver
        results = driver.results

        # Fill the base-case / N-1 report
        self.report_text.setPlainText(results.summary_text())

        # Fill the ranked candidate list. Only verified candidates that introduce no new violations
        # are listed, so everything shown is confirmed by a full AC power flow + N-1/voltage
        # re-check. Line/upgrade, injection (static gen/battery) and voltage-relief (shunt reactor)
        # candidates are three independently ranked/verified tracks (see CandidateGenerationResults
        # docstring); each candidate's label() already names its own kind, so a simple concatenation
        # is enough here.
        self._candidates = (results.verified_candidates + results.verified_injection_candidates
                            + results.verified_voltage_candidates)
        for candidate in self._candidates:
            self.candidate_list.addItem(QtWidgets.QListWidgetItem(candidate.label()))

        self.add_button.setEnabled(len(self._candidates) > 0)

    # ----------------------------------------------------------------------------------------------
    # Materialise the selected candidates as investments
    # ----------------------------------------------------------------------------------------------
    def add_investments(self) -> None:
        """
        Add every listed candidate as an investment. Each candidate gets its own
        ``InvestmentsGroup``, named after the asset it represents, so they can be combined freely
        by the downstream investment evaluation. Any newly created device (line, shunt reactor,
        static generator or battery) is added to the circuit and drawn on the currently selected
        diagram.
        """
        if self._driver is None or len(self._candidates) == 0:
            return

        logger = Logger()
        new_devices: List[dev.EditableDevice] = list()

        for candidate in self._candidates:
            group = dev.InvestmentsGroup(idtag=None,
                                         name=candidate.group_name(),
                                         category="single")
            self.app.circuit.add_investments_group(group)

            # Each candidate creates its Investment(s) (and any new device) against the circuit.
            # A new-line candidate returns a Line to draw; an upgrade returns its uprated branch
            # copy, which overlaps the original geometrically — draw it only when it is a Line so
            # the corridor still shows solid once applied (transformer copies are left undrawn);
            # shunt reactor / static generator / battery candidates return an injection device.
            created = candidate.apply(circuit=self.app.circuit, group=group, logger=logger)
            if isinstance(created, dev.Line):
                new_devices.append(created)
            elif isinstance(created, (dev.ControllableShunt, dev.StaticGenerator, dev.Battery)):
                new_devices.append(created)
            else:
                pass

        # Draw any newly created devices on the currently selected diagram. New-line, static-gen,
        # battery and shunt-reactor candidates all connect to/attach at existing buses, so their
        # host bus(es) already exist on the diagram.
        self._draw_new_devices(new_devices)

        if logger.has_logs():
            LogsDialogue('Candidate investment generator log', logger).exec()

        self.close()

    def _draw_new_devices(self, new_devices: List[dev.EditableDevice]) -> None:
        """
        Draw newly created devices on the currently selected diagram widget, if any. A new line
        connects two existing buses and uses the line-drawing path; an injection device (shunt
        reactor / static generator / battery) attaches to its host bus's existing graphic item.

        :param new_devices: Devices created by ``candidate.apply()`` across all accepted candidates.
        """
        if len(new_devices) == 0:
            return
        else:
            pass

        diagram = self.app.get_selected_diagram_widget()
        if diagram is None:
            return
        else:
            pass

        if isinstance(diagram, SchematicWidget):
            for device in new_devices:
                if diagram.graphics_manager.query(elm=device) is not None:
                    pass  # already drawn
                elif isinstance(device, dev.Line):
                    diagram.add_api_line(branch=device)
                else:
                    # Injection device: attach to its host bus's existing graphic item, if drawn.
                    bus_graphic = diagram.graphics_manager.query(elm=device.bus)
                    if bus_graphic is not None:
                        bus_graphic.add_object(api_obj=device)
                    else:
                        pass  # host bus not on this diagram; nothing to attach to
        elif isinstance(diagram, GridMapWidget):
            for device in new_devices:
                if diagram.graphics_manager.query(elm=device) is not None:
                    pass
                elif isinstance(device, dev.Line):
                    diagram.add_api_line(api_object=device)
                else:
                    # The map widget has no drawing method for ControllableShunt today; battery
                    # and static-generator investments still exist correctly in the circuit, just
                    # won't render on the map diagram specifically (known, pre-existing gap).
                    pass
        else:
            pass
