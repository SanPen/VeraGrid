# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Set
from PySide6 import QtWidgets
from PySide6.QtGui import QClipboard
import numpy as np
from VeraGrid.Gui.GridReduce.grid_reduce_gui import Ui_ReduceDialog
from VeraGrid.Gui.general_dialogues import LogsDialogue
from VeraGrid.Gui.messages import yes_no_question, warning_msg
from VeraGrid.Gui.gui_functions import ComboModel, get_list_model
from VeraGrid.Session.session import SimulationSession
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Topology.GridReduction.di_shi_grid_reduction import di_shi_reduction
from VeraGridEngine.Topology.GridReduction.ptdf_grid_reduction import ptdf_reduction, ptdf_reduction_projected
from VeraGridEngine.Topology.GridReduction.ward_equivalents import ward_standard_reduction
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import GridReductionMethod, BusReductionMethod


class GridReduceDialogue(QtWidgets.QDialog):
    """
    GridMergeDialogue
    """

    def __init__(self, grid: MultiCircuit, session: SimulationSession, selected_buses_set: Set[Bus]):
        """
        GridMergeDialogue
        :param grid: MultiCircuit instance
        :param session: SimulationSession instance to query the power flow
        :param selected_buses_set: Set of buses (Bus objects) to reduce
        """
        QtWidgets.QDialog.__init__(self)
        self.ui = Ui_ReduceDialog()
        self.ui.setupUi(self)
        self.setWindowTitle('Grid reduction')
        self.setModal(True)

        self.logger = Logger()
        self.logs_dialogue: LogsDialogue | None = None

        self.ui.listView.setModel(get_list_model(list(selected_buses_set)))

        methods_mdl = ComboModel(
            enum_values=[GridReductionMethod.PTDF,
                         GridReductionMethod.PTDFProjected,
                         GridReductionMethod.DiShi,
                         GridReductionMethod.Ward],
            translate=self.tr
        )
        self.ui.methodComboBox.setModel(methods_mdl)

        bus_methods_mdl = ComboModel(
            enum_values=[BusReductionMethod.Reduce, BusReductionMethod.Keep],
            translate=self.tr
        )
        self.ui.busModeComboBox.setModel(bus_methods_mdl)

        self._grid: MultiCircuit = grid
        self._session: SimulationSession = session
        self._selected_buses_set: Set[Bus] = selected_buses_set

        self.did_reduce = False

        self.ui.reduceButton.clicked.connect(self.reduce_grid)
        self.ui.copyIndicesButton.clicked.connect(self.copy_indices)

    def reduce_grid(self) -> None:
        """
        The elements of the grid will be added with new idtags.
        This is useful in the case you want to compose a new grid from grids that are the same.
        :return:
        """
        if len(self._selected_buses_set):

            reduction_method: GridReductionMethod = self.ui.methodComboBox.currentData()
            bus_mode: BusReductionMethod = self.ui.busModeComboBox.currentData()

            if bus_mode == BusReductionMethod.Reduce:
                text = f"This will delete the selected buses and reintroduce their influence."
            else:
                text = "This will keep the selected buses and delete all others, reintroducing their influence."

            text += f"using the {reduction_method.value} equivalent. "
            "This cannot be undone and it is dangerous if you don't know"
            "what you are doing \nAre you sure?"

            ok = yes_no_question(
                text=text,
                title="Grid reduction?")

            if ok:

                if bus_mode == BusReductionMethod.Reduce:
                    # convert the set of buses to bus indices
                    reduction_bus_indices = np.array([self._grid.buses.index(b)
                                                      for b in self._selected_buses_set],
                                                     dtype=int)

                elif bus_mode == BusReductionMethod.Keep:
                    # the the other buses that are not in the set
                    reduction_bus_indices = np.array([i for i in range(self._grid.get_bus_number())
                                                      if self._grid.buses[i] not in self._selected_buses_set],
                                                     dtype=int)
                else:
                    raise NotImplementedError(f"BusReductionMethod not implemented: {bus_mode.value}")

                if reduction_method == GridReductionMethod.DiShi:

                    # get the previous power flow
                    _, pf_res = self._session.power_flow

                    if pf_res is None:
                        warning_msg("Run a power flow first! or select another method", "Grid reduction")
                        return

                    # NOTE: self._grid gets reduced in-place
                    grid_reduced, logger = di_shi_reduction(
                        grid=self._grid,
                        reduction_bus_indices=reduction_bus_indices,
                        V0=pf_res.voltage
                    )

                elif reduction_method == GridReductionMethod.Ward:

                    # get the previous power flow
                    _, pf_res = self._session.power_flow

                    if pf_res is None:
                        warning_msg("Run a power flow first! or select another method", "Grid reduction")
                        return

                    # NOTE: self._grid gets reduced in-place
                    grid_reduced, logger = ward_standard_reduction(
                        grid=self._grid,
                        reduction_bus_indices=reduction_bus_indices,
                        V0=pf_res.voltage,
                    )

                elif reduction_method == GridReductionMethod.PTDF:

                    # NOTE: self._grid gets reduced in-place
                    grid_reduced, logger = ptdf_reduction(
                        grid=self._grid,
                        reduction_bus_indices=reduction_bus_indices,
                    )

                elif reduction_method == GridReductionMethod.PTDFProjected:

                    # NOTE: self._grid gets reduced in-place

                    # get the options from the linear analysis drivers (prefer TS if available)
                    distribute_slack = True
                    lin_drv_ts, _ = self._session.linear_power_flow_ts
                    lin_drv, _ = self._session.linear_power_flow

                    if lin_drv_ts is not None:
                        distribute_slack = lin_drv_ts.options.distribute_slack

                    elif lin_drv is not None:
                        distribute_slack = lin_drv.options.distribute_slack

                    else:
                        pass

                    grid_reduced, logger = ptdf_reduction_projected(
                        grid=self._grid,
                        reduction_bus_indices=reduction_bus_indices,
                        distribute_slack=distribute_slack
                    )

                    # grid_reduced, logger = ptdf_reduction_ree_bad(
                    #     grid=self._grid,
                    #     reduction_bus_indices=reduction_bus_indices,
                    # )

                    # grid_reduced, logger = ptdf_reduction_ree_less_bad(
                    #     grid=self._grid,
                    #     reduction_bus_indices=reduction_bus_indices,
                    # )

                else:
                    raise NotImplementedError("Reduction method not supported")

                if logger.has_logs():
                    self.logs_dialogue = LogsDialogue(name="Import profiles", logger=logger)
                    self.logs_dialogue.exec()

                self.did_reduce = True
            else:
                pass  # not ok
        else:
            warning_msg("No reduction happened", "Grid reduction")

        # exit
        self.close()

    def copy_indices(self):
        """
        Copy the bus indices to the clipboard
        """
        tsv_text = ", ".join(list(self._selected_buses_set))

        QtWidgets.QApplication.clipboard().setText(tsv_text, QClipboard.Mode.Clipboard)
