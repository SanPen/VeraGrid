# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
from typing import List, Dict

from matplotlib import pyplot as plt

from VeraGridEngine.Simulations.results_template import ResultsTemplate
from VeraGridEngine.basic_structures import Vec, DateVec, StrVec, Mat
from VeraGridEngine.enumerations import StudyResultsType, DeviceType
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.Devices.types import ALL_DEV_TYPES


class RmsResults(ResultsTemplate):
    __slots__ = (
        "nt",
        "nv",
        "ng",
        "rms_events_group_names",
        "well_initialized",
        "converged",
        "variables",
        "uid2vars_glob_name",
        "devices_vars_info",
        "uid2idx",
        "vars_glob_name2uid",
        "variable_array",
        "values",
    )

    def __init__(self,
                 time_array: DateVec,
                 rms_events_group_names: StrVec,
                 variables: List[Var],

                 uid2idx: Dict[int, int],
                 vars_glob_name2uid: Dict[str, int],
                 devices_vars_info: Dict[ALL_DEV_TYPES, List[Var]]):
        """

        :param rms_events_group_names: names of the RMS groups simulated
        :param time_array: Array of time steps
        :param variables: List of all variables (Redundant?)
        :param uid2idx: Var uid to var index in values
        :param vars_glob_name2uid: dictionary relating var names to uid (WTF?)
        :param devices_vars_info: dictionary relating the devices with a list of their simulation vars
        """
        ResultsTemplate.__init__(
            self,
            name='RMS simulation',
            available_results=[],
            time_array=time_array,
            clustering_results=None,
            study_results_type=StudyResultsType.RmsSimulation
        )

        self.nt = len(time_array)
        self.nv = len(variables)
        self.ng = len(rms_events_group_names)

        self.rms_events_group_names = rms_events_group_names

        self.well_initialized = np.zeros(self.ng, dtype=bool)
        self.converged = np.zeros(self.ng, dtype=bool)
        
        self.variables = variables
        self.uid2vars_glob_name = {uid: name for name, uid in vars_glob_name2uid.items()}
        self.devices_vars_info: Dict[ALL_DEV_TYPES, List[Var]] = devices_vars_info
        self.uid2idx: Dict[int, int] = uid2idx
        self.vars_glob_name2uid = vars_glob_name2uid
        not_found_vars= list()
        for var in variables:
            if var.uid not in self.uid2vars_glob_name:
                not_found_vars.append(var)
        self.variable_array = np.array([self.uid2vars_glob_name[var.uid] for var in variables], dtype=str)
        self.values = np.zeros((self.nt, self.nv, self.ng), dtype=float)

        self.register(name='values', tpe=Vec)
        
    def get_var(self, uid: int) -> Var:
        """
        
        :param uid: 
        :return: 
        """
        idx = self.uid2idx[uid]
        return self.variables[idx]

    def get_devices_dict_tree(self) -> Dict[DeviceType, Dict[ALL_DEV_TYPES, List[Var]]]:
        """

        :return:
        """
        tree: Dict[DeviceType, Dict[ALL_DEV_TYPES, List[Var]]] = dict()

        for elm, var_list in self.devices_vars_info.items():

            elm_by_type_dict = tree.get(elm.device_type, None)

            if elm_by_type_dict is None:
                tree[elm.device_type] = {elm: var_list}
            else:
                elm_by_type_dict[elm] = var_list

        return tree

    def plot_var(self, var: Var, group_idx: int = 0):
        """

        :param var:
        :param group_idx:
        :return:
        """
        idx = self.uid2idx[var.uid]

        y = self.values[:, idx, group_idx]

        plt.plot(self.time_array, y, label=var.name)
        plt.legend()
        plt.show()

    def get_vars_data(self, var_list: List[Var], group_idx: int = 0) -> Mat:
        """
        Get time, vars data matrix for the vars selection
        :param var_list: List of vars
        :param group_idx: group index
        :return: data (time, vars)
        """
        data = np.empty((self.nt, len(var_list)), dtype=float)

        for i, var in enumerate(var_list):
            idx = self.uid2idx[var.uid]
            data[:, i] = self.values[:, idx, group_idx]

        return data

    # def mdl(self, result_type: ResultTypes) -> ResultsTable:
    #     """
    #     Export the results as a ResultsTable for plotting.
    #     """
    #     if result_type == ResultTypes.RmsSimulationReport:
    #         return ResultsTable(
    #             data=np.array(self.values),
    #             index=np.array(pd.to_datetime(self.time_array).astype(str), dtype=np.str_),
    #             columns=self.variable_array,
    #             title="Rms Simulation Results",
    #             units=self.units,
    #             idx_device_type=DeviceType.TimeDevice,
    #             cols_device_type=DeviceType.NoDevice
    #         )
    #
    #     else:
    #         raise Exception(f"Result type not understood: {result_type}")
