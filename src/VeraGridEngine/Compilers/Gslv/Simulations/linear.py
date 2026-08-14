# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from VeraGridEngine.Compilers.Gslv.activation import pg
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Compilers.Gslv.conversion import to_gslv


def gslv_linear_matrices(circuit: MultiCircuit,
                         distributed_slack=False,
                         correctValues=False,
                         override_branch_controls=False) -> "pg.LinearAnalysis":
    """
    Newton linear analysis
    :param circuit: MultiCircuit instance
    :param distributed_slack: distribute the PTDF slack
    :param correctValues: Correct nonsense values (outsie -1, 1) interval
    :param override_branch_controls: Override branch controls
    :return: Newton LinearAnalysisMatrices object
    """
    gslv_circuit, _ = to_gslv(circuit=circuit,
                              use_time_series=False,
                              override_branch_controls=override_branch_controls)

    options = pg.LinearAnalysisOptions(distributeSlack=distributed_slack,
                                       correctValues=correctValues,
                                       ptdfThreshold=0.001,
                                       lodfThreshold=0.001)

    logger = pg.Logger()
    nc = pg.compile(grid=gslv_circuit, logger=logger, t_idx=0)

    results = pg.LinearAnalysis(nc=nc,
                                distributed_slack_=distributed_slack,
                                correct_values_=correctValues, )

    return results
