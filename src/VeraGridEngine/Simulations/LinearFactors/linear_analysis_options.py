# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.Simulations.options_template import OptionsTemplate
from VeraGridEngine.Devices.Parents.editable_device import GCProp



class LinearAnalysisOptions(OptionsTemplate):
    """
    LinearAnalysisOptions
    """

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(key="distribute_slack", tpe=bool),
        GCProp(key="correct_values", tpe=bool),
        GCProp(key="ptdf_threshold", tpe=float),
        GCProp(key="lodf_threshold", tpe=float),
    )

    def __init__(self,
                 distribute_slack=False,
                 correct_values=True,
                 ptdf_threshold: float = 1e-3,
                 lodf_threshold: float = 1e-3):
        """
        Power Transfer Distribution Factors' options
        :param distribute_slack: Distribute the slack effect?
        :param correct_values: correct out of bounds values?
        :param ptdf_threshold: threshold for PTDF's to be converted to sparse
        :param lodf_threshold: threshold for LODF's to be converted to sparse
        """
        OptionsTemplate.__init__(self, name="LinearAnalysisOptions")

        self.distribute_slack = distribute_slack

        self.correct_values = correct_values

        self.ptdf_threshold = ptdf_threshold

        self.lodf_threshold = lodf_threshold

