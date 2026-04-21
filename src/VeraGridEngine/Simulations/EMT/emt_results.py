# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
from matplotlib import pyplot as plt
from typing import List, Dict

from VeraGridEngine.Simulations.results_template import ResultsTemplate, ResultsProperty
from VeraGridEngine.basic_structures import Vec, StrVec,  DateVec, Mat
from VeraGridEngine.enumerations import StudyResultsType,  DeviceType
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.Devices.types import ALL_DEV_TYPES


class EmtResults(ResultsTemplate):

    LOCAL_RESULTS_DECLARATIONS = (
        ResultsProperty(name='values', tpe=Vec, old_names=list()),
    )

    __slots__ = (
        "nt",
        "nv",
        "ndv",
        "ng",
        "emt_events_group_names",
        "well_initialized",
        "converged",
        "variables",
        "diff_variables",
        "uid2vars_glob_name",
        "devices_vars_info",
        "uid2idx_vars",
        "uid2idx_diff",
        "uid2idx",
        "vars_glob_name2uid",
        "variable_array",
        "values",
        "diff_values",
    )

    def __init__(self,
                 time_array: DateVec,
                 emt_events_group_names: StrVec,
                 variables: List[Var],
                 diff_variables: List[Var],
                 uid2idx_vars: Dict[int, int],
                 uid2idx_diff: Dict[int, int],
                 vars_glob_name2uid: Dict[str, int],
                 devices_vars_info: Dict[ALL_DEV_TYPES, List[Var]]):
        """

        :param emt_events_group_names: names of the EMT groups simulated
        :param time_array: Array of time steps
        :param variables: List of all variables (Redundant?)
        :param diff_variables: List of all derivatives of variables (Redundant?)
        :param uid2idx_vars: Var uid to var index in values variables
        :param uid2idx_diff: Var uid to var index in values diff vars
        :param vars_glob_name2uid: dictionary relating var names to uid (WTF?)
        :param devices_vars_info: dictionary relating the devices with a list of their simulation vars and diffvars
        """
        ResultsTemplate.__init__(
            self,
            name='EMT simulation',
            available_results=[],
            time_array=time_array,
            clustering_results=None,
            study_results_type=StudyResultsType.EmtSimulation
        )

        self.nt = len(time_array)
        self.nv = len(variables)
        self.ndv = len(diff_variables)
        self.ng = len(emt_events_group_names)

        self.emt_events_group_names = emt_events_group_names

        self.well_initialized = np.zeros(self.ng, dtype=bool)
        self.converged = np.zeros(self.ng, dtype=bool)

        self.variables = variables
        self.diff_variables = diff_variables
        self.uid2vars_glob_name = {uid: name for name, uid in vars_glob_name2uid.items()}
        self.devices_vars_info: Dict[ALL_DEV_TYPES, List[Var]] = devices_vars_info
        self.uid2idx_vars: Dict[int, int] = uid2idx_vars
        self.uid2idx_diff: Dict[int, int] = uid2idx_diff
        self.uid2idx: Dict[int, int] = dict()
        self.uid2idx.update(self.uid2idx_vars)
        self.uid2idx.update(self.uid2idx_diff)
        self.vars_glob_name2uid = vars_glob_name2uid
        not_found_vars = list()
        not_found_diff_vars = list()
        for var in variables:
            if var.uid not in self.uid2vars_glob_name:
                not_found_vars.append(var)
        for diff in diff_variables:
            if diff.uid not in self.uid2vars_glob_name:
                not_found_diff_vars.append(diff)

        self.variable_array = np.array([self.uid2vars_glob_name[var.uid] for var in variables], dtype=str)
        self.values = np.zeros((self.nt, self.nv, self.ng), dtype=float)
        self.diff_values = np.zeros((self.nt, self.ndv, self.ng), dtype=float)


    def get_var(self, uid: int) -> Var:
        """
        Get a var or a diff var from its uid
        :param uid:
        :return:
        """

        if uid in self.uid2idx_vars:
            idx = self.uid2idx_vars[uid]
            return self.variables[idx]

        elif uid in self.uid2idx_diff:
            idx = self.uid2idx_diff[uid]
            return self.diff_variables[idx]

        else:
            raise ValueError(f"Variable with uid {uid} not found in vars either diff_vars list.")


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
        Plot a variable or a derivative
        :param var:
        :param group_idx:
        :return:
        """
        if var.uid in self.uid2idx_vars:
            idx = self.uid2idx_vars[var.uid]
            y = self.values[:, idx, group_idx]
            plt.plot(self.time_array, y, label=var.name)
            plt.legend()
            plt.show()

        elif var.uid in self.uid2idx_diff:
            idx = self.uid2idx_diff[var.uid]
            y = self.diff_values[:, idx, group_idx]
            plt.plot(self.time_array, y, label=var.name)
            plt.legend()
            plt.show()
        else:
            raise ValueError(f"Variable {var} not found in vars either diff_vars.")


    def get_vars_data(self, var_list: List[Var], group_idx: int = 0) -> Mat:
        """
        Get time, vars data matrix for the vars selection
        :param var_list: List of vars
        :param group_idx: group index
        :return: data (time, vars)
        """
        data = np.empty((self.nt, len(var_list)), dtype=float)

        for i, var in enumerate(var_list):
            # idx = self.uid2idx_vars[var.uid]
            if var.uid in self.uid2idx_vars:
                idx = self.uid2idx_vars[var.uid]
                data[:, i] = self.values[:, idx, group_idx]
            elif var.uid in self.uid2idx_diff:
                idx = self.uid2idx_diff[var.uid]
                data[:, i] = self.diff_values[:, idx, group_idx]

        return data


