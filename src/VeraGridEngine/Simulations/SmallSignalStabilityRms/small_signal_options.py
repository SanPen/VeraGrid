# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Tuple

from VeraGridEngine.enumerations import DynamicIntegrationMethod
from VeraGridEngine.Simulations.options_template import OptionsTemplate
from VeraGridEngine.Devices.Parents.editable_device import GCProp



class RmsSmallSignalStabilityOptions(OptionsTemplate):
    """
    Small Signal Stability RMS simulation options.
    """
    __slots__ = ['ss_assessment_time', 'k', 'verbose']

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(key="ss_assessment_time", tpe=float),
        GCProp(key="k", tpe=int),
        GCProp(key="verbose", tpe=int),
    )

    def __init__(self,
                 k: int | None = None,
                 ss_assessment_time: float = 5.0,
                 verbose: int = 0):

        """
        SmallSignalStabilityRmsOptions constructor.

        :param k: number of eigenvalues that must be calculated
        :type k: int | None
        :param ss_assessment_time: stability assessment time (s)
        :type ss_assessment_time: float
        :param verbose: verbosity level
        :type verbose: int
        """
        OptionsTemplate.__init__(self, name='RmsSimulationOptions')

        self.ss_assessment_time: float = ss_assessment_time
        self.k: int | None = k
        self.verbose: int = verbose

