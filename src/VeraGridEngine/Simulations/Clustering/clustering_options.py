# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.Simulations.options_template import OptionsTemplate
from VeraGridEngine.Devices.Parents.editable_device import GCProp



class ClusteringAnalysisOptions(OptionsTemplate):

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(key="n_points", tpe=int),
    )

    def __init__(self, n_points: int):
        """
        Clustering options
        :param n_points: number of points
        """
        OptionsTemplate.__init__(self, name='Clustering analysis options')

        self.n_points = n_points

