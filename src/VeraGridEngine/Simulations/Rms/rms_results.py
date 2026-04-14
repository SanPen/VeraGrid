# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
import pandas as pd
from typing import List, Dict, Union

from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.Parents.branch_parent import BranchParent
from VeraGridEngine.Devices.Parents.injection_parent import InjectionParent

from VeraGridEngine.Simulations.results_table import ResultsTable
from VeraGridEngine.Simulations.results_template import ResultsTemplate
from VeraGridEngine.basic_structures import Vec, DateVec
from VeraGridEngine.enumerations import StudyResultsType, ResultTypes, DeviceType
from VeraGridEngine.Utils.Symbolic.symbolic import Var


class RmsResults(ResultsTemplate):

    def __init__(self,
                 values: np.ndarray,
                 time_array: DateVec,
                 stat_vars: List[Var],
                 algeb_vars: List[Var],
                 uid2idx: Dict[int, int],
                 vars_glob_name2uid: Dict[str, int],
                 devices: List[Union[Bus, BranchParent, InjectionParent]],
                 units: str = ""):
        """

        :param values:
        :param time_array:
        :param stat_vars:
        :param algeb_vars:
        :param uid2idx:
        :param vars_glob_name2uid:
        :param devices:
        :param units:
        """
        ResultsTemplate.__init__(
            self,
            name='RMS simulation',
            available_results=[
                ResultTypes.RmsSimulationReport,
                # ResultTypes.RmsPlotResults
            ],
            time_array=time_array,
            clustering_results=None,
            study_results_type=StudyResultsType.RmsSimulation
        )
        self.uid2vars_glob_name = {uid: name for name, uid in vars_glob_name2uid.items()}
        variables = stat_vars + algeb_vars
        variable_names = [self.uid2vars_glob_name[var.uid] for var in variables]
        self.devices = devices
        self.uid2idx = uid2idx
        self.vars_glob_name2uid = vars_glob_name2uid
        self.variable_array = np.array(variable_names, dtype=np.str_)

        self.values = values
        self.units = units
        self.register(name='values', tpe=Vec)

    def mdl(self, result_type: ResultTypes) -> ResultsTable:
        """
        Export the results as a ResultsTable for plotting.
        """
        if result_type == ResultTypes.RmsSimulationReport:
            return ResultsTable(
                data=np.array(self.values),
                index=np.array(pd.to_datetime(self.time_array).astype(str), dtype=np.str_),
                columns=self.variable_array,
                title="Rms Simulation Results",
                units=self.units,
                idx_device_type=DeviceType.TimeDevice,
                cols_device_type=DeviceType.NoDevice
            )
        # elif result_type == ResultTypes.RmsPlotResults:
        #
        #     results_table = ResultsTable(
        #         data=np.array(self.values),
        #         index=np.array(pd.to_datetime(self.time_array).astype(str), dtype=np.str_),
        #         columns=self.variable_array,
        #         title="Rms Simulation Results",
        #         units=self.units,
        #         idx_device_type=DeviceType.TimeDevice,
        #         cols_device_type=DeviceType.NoDevice,
        #         xlabel=" time (s)",
        #         ylabel="",
        #     )

        else:
            raise Exception(f"Result type not understood: {result_type}")
