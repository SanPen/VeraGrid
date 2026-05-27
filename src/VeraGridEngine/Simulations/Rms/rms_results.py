# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
from typing import List, Dict, Optional

from matplotlib import pyplot as plt

from VeraGridEngine.Simulations.results_template import ResultsTemplate, ResultsProperty
from VeraGridEngine.basic_structures import Vec, DateVec, StrVec, Mat
from VeraGridEngine.enumerations import StudyResultsType, DeviceType
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.Devices.types import ALL_DEV_TYPES


class RmsResults(ResultsTemplate):
    LOCAL_RESULTS_DECLARATIONS = (
        ResultsProperty(name='values', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='rms_events_group_idtags', tpe=StrVec, old_names=list(), expandable=False),
    )

    __slots__ = (
        "nt",
        "nv",
        "ng",
        "rms_events_group_names",
        "rms_events_group_idtags",
        "has_event_group_results",
        "well_initialized",
        "converged",
        "variables",
        "uid2vars_glob_name",
        "devices_vars_info",
        "parameter_value_maps",
        "uid2idx",
        "vars_glob_name2uid",
        "variable_array",
        "values",
    )

    def __init__(self,
                 time_array: DateVec,
                 rms_events_group_names: StrVec,
                 rms_events_group_idtags: StrVec,
                  variables: List[Var],
                  uid2idx: Dict[int, int],
                  vars_glob_name2uid: Dict[str, int],
                  devices_vars_info: Dict[ALL_DEV_TYPES, List[Var]],
                  parameter_value_maps: Optional[List[Dict[str, float]]] = None,
                  has_event_group_results: Optional[StrVec] = None):
        """
        Build the RMS dynamic results container.

        :param time_array: Ordered simulation time samples.
        :param rms_events_group_names: Ordered declared RMS event-group names.
        :param rms_events_group_idtags: Ordered declared RMS event-group idtags.
        :param variables: Exported RMS variables stored in ``values``.
        :param uid2idx: Mapping from variable uid to the ``values`` column index.
        :param vars_glob_name2uid: Mapping from global variable label to variable uid.
        :param devices_vars_info: Device-to-variable mapping used to rebuild the results tree.
        :param parameter_value_maps: Per-event-group parameter scalar maps exported for GUI plotting.
        :param has_event_group_results: Boolean mask telling which event-group columns contain actual simulation data.
        :return: None.

        The results arrays are still allocated for every declared event group so
        the storage layout remains stable across the simulation stack. The extra
        availability mask is therefore needed to distinguish declared groups
        from groups that actually produced runtime samples in the current run.
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
        self.rms_events_group_idtags = rms_events_group_idtags

        # The results arrays are allocated for every declared event group, but
        # only a subset may have been simulated in the current run. The dynamic
        # plotting layer must inspect this mask before binding a curve so
        # placeholder zero columns stay unresolved instead of being plotted.
        if has_event_group_results is None:
            self.has_event_group_results = np.ones(self.ng, dtype=bool)
        else:
            self.has_event_group_results = np.array(has_event_group_results, dtype=bool)

        self.well_initialized = np.zeros(self.ng, dtype=bool)
        self.converged = np.zeros(self.ng, dtype=bool)

        self.variables = variables
        self.uid2vars_glob_name = {uid: name for name, uid in vars_glob_name2uid.items()}
        self.devices_vars_info: Dict[ALL_DEV_TYPES, List[Var]] = devices_vars_info
        if parameter_value_maps is None:
            self.parameter_value_maps: List[Dict[str, float]] = list()
            group_index: int
            for group_index in range(self.ng):
                self.parameter_value_maps.append(dict())
        else:
            self.parameter_value_maps = list(parameter_value_maps)
        self.uid2idx: Dict[int, int] = uid2idx
        self.vars_glob_name2uid = vars_glob_name2uid
        self.variable_array = np.array([self.uid2vars_glob_name[var.uid] for var in variables], dtype=str)
        self.values = np.zeros((self.nt, self.nv, self.ng), dtype=float)

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

    def get_parameter_value(self, group_idx: int, device_idtag: str, parameter_name: str) -> float | None:
        """
        Get one exported parameter value for one event group.

        :param group_idx: Event-group index.
        :param device_idtag: Stable device identifier.
        :param parameter_name: Canonical symbolic parameter name.
        :return: Parameter scalar value, or ``None``.
        """
        if group_idx >= 0 and group_idx < len(self.parameter_value_maps):
            parameter_key: str = str(device_idtag) + ":" + str(parameter_name)
            return self.parameter_value_maps[group_idx].get(parameter_key, None)
        else:
            return None

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
