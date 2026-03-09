# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import matplotlib.colors as plt_colors
from typing import List, Tuple, Dict, Union

# from VeraGrid.Gui.rms_plot_variables_dialog import RmsPlotDialog
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.Parents.branch_parent import BranchParent
from VeraGridEngine.Devices.Parents.injection_parent import InjectionParent

from VeraGridEngine.Devices.Parents.physical_device import PhysicalDevice
from VeraGridEngine.Simulations.results_table import ResultsTable
from VeraGridEngine.Simulations.results_template import ResultsTemplate
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.basic_structures import IntVec, Vec, StrVec, CxVec, ConvergenceReport, Logger, DateVec
from VeraGridEngine.enumerations import StudyResultsType, ResultTypes, DeviceType
from VeraGridEngine.Utils.Symbolic.symbolic import Var


class EmtResults(ResultsTemplate):

    def __init__(self,
                 values: np.ndarray,
                 time_array: DateVec,
                 uid2idx: Dict[int, int],
                 vars_glob_name2uid: Dict[str, int],
                 devices: List[Union[Bus, BranchParent, InjectionParent]],
                 units: str = ""):
        """

        :param values:
        :param time_array:
        :param uid2idx:
        :param vars_glob_name2uid:
        :param devices:
        :param units:
        """
        ResultsTemplate.__init__(
            self,
            name='RMS simulation',
            available_results=[],
            time_array=time_array,
            clustering_results=None,
            study_results_type=StudyResultsType.RmsSimulation
        )

        # variables = stat_vars + algeb_vars
        # variable_names = [str(var) for var in variables]
        self.devices = devices
        self.uid2idx = uid2idx
        self.vars_glob_name2uid = vars_glob_name2uid
        # self.variable_array = np.array(variable_names, dtype=np.str_)

        self.values = values
        self.units = units
        self.register(name='values', tpe=Vec)
