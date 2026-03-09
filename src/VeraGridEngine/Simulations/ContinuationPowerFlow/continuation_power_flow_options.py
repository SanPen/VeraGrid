# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

from typing import Tuple

from VeraGridEngine.Simulations.ContinuationPowerFlow.continuation_power_flow import (CpfStopAt,
                                                                                      CpfParametrization)
from VeraGridEngine.Simulations.options_template import OptionsTemplate
from VeraGridEngine.Devices.Parents.editable_device import GCProp



class ContinuationPowerFlowOptions(OptionsTemplate):
    """
    ContinuationPowerFlowOptions
    """

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(key="step", tpe=float),
        GCProp(key="approximation_order", tpe=CpfParametrization),
        GCProp(key="adapt_step", tpe=bool),
        GCProp(key="step_min", tpe=float),
        GCProp(key="step_max", tpe=float),
        GCProp(key="step_tol", tpe=float),
        GCProp(key="solution_tol", tpe=float),
        GCProp(key="max_it", tpe=int),
        GCProp(key="stop_at", tpe=CpfStopAt),
        GCProp(key="verbose", tpe=int),
    )

    def __init__(self,
                 step=0.01,
                 approximation_order=CpfParametrization.Natural,
                 adapt_step=True,
                 step_min=0.0001,
                 step_max=0.2,
                 error_tol=1e-3,
                 tol=1e-6,
                 max_it=20,
                 stop_at=CpfStopAt.Nose,
                 verbose: int = 0):
        """
        Voltage collapse options
        @param step: Step length
        @param approximation_order: Order of the approximation: 1, 2, 3, etc...
        @param adapt_step: Use adaptive step length?
        @param step_min: Minimum step length
        @param step_max: Maximum step length
        @param error_tol: Error tolerance
        @param tol: tolerance
        @param max_it: Maximum number of iterations
        @param stop_at: Value of lambda to stop at, it can be specified by a concept namely NOSE to sto at the edge or
        FULL tp draw the full curve
        """
        OptionsTemplate.__init__(self, name='ContinuationPowerFlowOptions')

        self.step = step

        self.approximation_order = approximation_order

        self.adapt_step = adapt_step

        self.step_min = step_min

        self.step_max = step_max

        self.step_tol = error_tol

        self.solution_tol = tol

        self.max_it = max_it

        self.stop_at = stop_at

        self.verbose = verbose

