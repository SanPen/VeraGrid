# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import List, Set
from PySide6 import QtWidgets
from PySide6.QtGui import QClipboard
import numpy as np
from VeraGrid.Gui.GridReduce.grid_reduce_gui import Ui_ReduceDialog
from VeraGrid.Gui.messages import yes_no_question, warning_msg
from VeraGrid.Gui.gui_functions import ComboModel, get_list_model
from VeraGrid.Session.session import SimulationSession
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Topology.GridReduction.di_shi_grid_reduction import di_shi_reduction
from VeraGridEngine.Topology.GridReduction.ptdf_grid_reduction import ptdf_reduction, ptdf_reduction_projected
from VeraGridEngine.Topology.GridReduction.ward_equivalents import ward_standard_reduction
from VeraGridEngine.basic_structures import IntVec, Logger
from VeraGridEngine.enumerations import GridReductionMethod, BusReductionMethod


class GridReduceDialogue(QtWidgets.QDialog):
    """
    GridMergeDialogue
    """

    def __init__(self, grid: MultiCircuit, session: SimulationSession, selected_buses_set: Set[Bus]) -> None:
        """
        GridMergeDialogue
        :param grid: MultiCircuit instance
        :param session: SimulationSession instance to query the power flow
        :param selected_buses_set: Set of buses (Bus objects) to reduce
        """
        QtWidgets.QDialog.__init__(self)
        self.ui = Ui_ReduceDialog()
        self.ui.setupUi(self)
        self.setWindowTitle(self.tr('Grid reduction'))
        self.setModal(True)

        self.logger = Logger()
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

        selected_bus_idtags: Set[str] = {bus.idtag for bus in selected_buses_set}
        self._grid: MultiCircuit = grid.copy()
        self._session: SimulationSession = session
        self._selected_buses_set: Set[Bus] = {bus for bus in self._grid.buses if bus.idtag in selected_bus_idtags}

        self.did_reduce: bool = False
        self.deleted_buses: List[Bus] = list()
        self.deleted_bus_idtags: List[str] = list()
        self.reduced_grid: MultiCircuit | None = None

        self.ui.reduceButton.clicked.connect(self.reduce_grid)
        self.ui.copyIndicesButton.clicked.connect(self.copy_indices)

    def reduce_grid(self) -> None:
        """
        The elements of the grid will be added with new idtags.
        This is useful in the case you want to compose a new grid from grids that are the same.
        :return:
        """
        self.did_reduce = False
        self.deleted_buses = list()
        self.deleted_bus_idtags = list()
        self.reduced_grid = None
        dialog_result: int = int(QtWidgets.QDialog.DialogCode.Rejected)

        try:
            if len(self._selected_buses_set):

                reduction_method: GridReductionMethod = self.ui.methodComboBox.currentData()
                bus_mode: BusReductionMethod = self.ui.busModeComboBox.currentData()

                if bus_mode == BusReductionMethod.Reduce:
                    text = f"This will delete the selected buses and reintroduce their influence."
                else:
                    text = "This will keep the selected buses and delete all others, reintroducing their influence."

                text += f"using the {reduction_method.value} equivalent. "
                text += "This cannot be undone and it is dangerous if you don't know "
                text += "what you are doing \nAre you sure?"

                ok = yes_no_question(
                    text=text,
                    title=self.tr("Grid reduction?"))

                if ok:
                    can_reduce: bool = True
                    reduction_bus_indices: IntVec

                    if bus_mode == BusReductionMethod.Reduce:
                        # convert the set of buses to bus indices
                        reduction_bus_indices = np.array([self._grid.buses.index(b)
                                                          for b in self._selected_buses_set],
                                                         dtype=int)

                    elif bus_mode == BusReductionMethod.Keep:
                        # the other buses that are not in the set
                        reduction_bus_indices = np.array([i for i in range(self._grid.get_bus_number())
                                                          if self._grid.buses[i] not in self._selected_buses_set],
                                                         dtype=int)
                    else:
                        raise NotImplementedError(f"BusReductionMethod not implemented: {bus_mode.value}")

                    before_reduction_buses: List[Bus] = list(self._grid.buses)
                    logger: Logger = Logger()

                    if reduction_method == GridReductionMethod.DiShi:

                        # get the previous power flow
                        _, pf_res = self._session.power_flow

                        if pf_res is None:
                            warning_msg(self.tr("Run a power flow first! or select another method"),
                                        self.tr("Grid reduction"))
                            can_reduce = False
                        else:
                            # NOTE: self._grid gets reduced in-place
                            _, logger = di_shi_reduction(
                                grid=self._grid,
                                reduction_bus_indices=reduction_bus_indices,
                                V0=pf_res.voltage
                            )


                    elif reduction_method == GridReductionMethod.Ward:

                        # get the previous power flow
                        _, pf_res = self._session.power_flow

                        if pf_res is None:
                            warning_msg(self.tr("Run a power flow first! or select another method"),
                                        self.tr("Grid reduction"))
                            can_reduce = False
                        else:
                            # NOTE: self._grid gets reduced in-place
                            _, logger = ward_standard_reduction(
                                grid=self._grid,
                                reduction_bus_indices=reduction_bus_indices,
                                V0=pf_res.voltage,
                            )


                    elif reduction_method == GridReductionMethod.PTDF:

                        # NOTE: self._grid gets reduced in-place
                        _, logger = ptdf_reduction(
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
                            distribute_slack = True

                        _, logger = ptdf_reduction_projected(
                            grid=self._grid,
                            reduction_bus_indices=reduction_bus_indices,
                            distribute_slack=distribute_slack
                        )

                    else:
                        raise NotImplementedError("Reduction method not supported")

                    if can_reduce:
                        # The engine mutates the grid in-place. Keep only buses that truly disappeared.
                        self.logger = logger
                        remaining_bus_idtags: Set[str] = {bus.idtag for bus in self._grid.buses}
                        self.deleted_buses = [bus for bus in before_reduction_buses
                                              if bus.idtag not in remaining_bus_idtags]
                        self.deleted_bus_idtags = [bus.idtag for bus in self.deleted_buses]
                        self.did_reduce = len(self.deleted_buses) > 0

                        if self.did_reduce:
                            self.reduced_grid = self._grid
                            dialog_result = int(QtWidgets.QDialog.DialogCode.Accepted)
                        else:
                            dialog_result = int(QtWidgets.QDialog.DialogCode.Rejected)
                    else:
                        dialog_result = int(QtWidgets.QDialog.DialogCode.Rejected)
                else:
                    dialog_result = int(QtWidgets.QDialog.DialogCode.Rejected)
            else:
                warning_msg(self.tr("No reduction happened"), self.tr("Grid reduction"))
                dialog_result = int(QtWidgets.QDialog.DialogCode.Rejected)
        except Exception as exc:
            self.logger.add_error(msg="Grid reduction failed", value=str(exc))
            self.did_reduce = False
            dialog_result = int(QtWidgets.QDialog.DialogCode.Rejected)
        else:
            pass

        self.done(dialog_result)

    def copy_indices(self) -> None:
        """
        Copy the bus indices to the clipboard
        """
        tsv_text: str = ", ".join([bus.name for bus in self._selected_buses_set])

        QtWidgets.QApplication.clipboard().setText(tsv_text, QClipboard.Mode.Clipboard)
