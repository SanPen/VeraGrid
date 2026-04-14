# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Tuple, List

from VeraGridEngine.enumerations import DynamicIntegrationMethod, RmsInitializationMethod, SubObjectType, RmsProblemTypes
from VeraGridEngine.Simulations.options_template import OptionsTemplate
from VeraGridEngine.Devices.Parents.editable_device import GCProp
from VeraGridEngine.Utils.Symbolic.symbolic import Var



class RmsOptions(OptionsTemplate):
    """
    Rms simulation options
    """

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(key="integration_method", tpe=DynamicIntegrationMethod),
        GCProp(key="initialization_method", tpe=RmsInitializationMethod),
        GCProp(key="problem_type", tpe=RmsProblemTypes),
        GCProp(key="time_step", tpe=float),
        GCProp(key="simulation_time", tpe=float),
        GCProp(key="tolerance", tpe=float),
        GCProp(key="use_init_values", tpe=bool),
        GCProp(key="max_iter", tpe=int),
        GCProp(key="rms_event_groups", tpe=SubObjectType.ObjectsList),
    )

    def __init__(self,
                 time_step: float = 0.001,
                 simulation_time: float = 5,
                 tolerance: float = 1e-6,
                 integration_method: DynamicIntegrationMethod = DynamicIntegrationMethod.DaeBackEuler,
                 initialization_method: RmsInitializationMethod = RmsInitializationMethod.Explicit,
                 problem_type: RmsProblemTypes = RmsProblemTypes.PowerBalance,
                 vars_to_save: List[Var] | None = None,
                 use_init_values: bool = False,
                 max_iter: int = 1000,
                 verbose: int = 0):
        """
        RmsOptions
        :param time_step: time step of the simulations (s)
        :param simulation_time: simulation time (s)
        :param max_iter: max number of iterations
        :param tolerance: Integration tolerance
        :param integration_method: Integration method (default Trapezoid)
        """

        OptionsTemplate.__init__(self, name='RmsSimulationOptions')

        self.integration_method: DynamicIntegrationMethod = integration_method
        self.initialization_method: RmsInitializationMethod = initialization_method
        self.problem_type: RmsProblemTypes = problem_type
        self.time_step: float = time_step
        self.simulation_time: float = simulation_time
        self.tolerance: float = tolerance
        self.use_init_values: bool = use_init_values
        self.max_iter: int = max_iter
        self.verbose = verbose

