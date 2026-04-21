# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
import pandas as pd
from VeraGridEngine.Simulations.results_table import ResultsTable
from VeraGridEngine.Simulations.results_template import ResultsTemplate, ResultsProperty
from VeraGridEngine.basic_structures import DateVec, IntVec, Vec
from VeraGridEngine.enumerations import StudyResultsType, ResultTypes, DeviceType


class ReliabilityResults(ResultsTemplate):

    LOCAL_RESULTS_DECLARATIONS = (
        ResultsProperty(name='LOLE_evolution', tpe=Vec, old_names=list()),
        ResultsProperty(name='ENS_evolution', tpe=Vec, old_names=list()),
        ResultsProperty(name='LOLF_evolution', tpe=Vec, old_names=list()),
        ResultsProperty(name='LOLET_evolution', tpe=Vec, old_names=list()),
        ResultsProperty(name='LOLFT_evolution', tpe=Vec, old_names=list()),
        ResultsProperty(name='SAIDI_evolution', tpe=Vec, old_names=list()),
        ResultsProperty(name='SAIFI_evolution', tpe=Vec, old_names=list()),
        ResultsProperty(name='CAIDI_evolution', tpe=Vec, old_names=list()),
    )

    __slots__ = (
        "LOLE_evolution",
        "ENS_evolution",
        "LOLF_evolution",
        "LOLET_evolution",
        "LOLFT_evolution",
        "SAIDI_evolution",
        "SAIFI_evolution",
        "CAIDI_evolution",
    )

    def __init__(self, nsim: int):
        """
        Clustering Results constructor
        """
        ResultsTemplate.__init__(
            self,
            name='Reliability Analysis',
            available_results=[
                ResultTypes.ReliabilityLOLEResults,
                ResultTypes.ReliabilityENSResults,
                ResultTypes.ReliabilityLOLFResults,
                ResultTypes.ReliabilityLOLETResults,
                ResultTypes.ReliabilityLOLFTResults,
                ResultTypes.ReliabilitySAIDIResults,
                ResultTypes.ReliabilitySAIFIResults,
                ResultTypes.ReliabilityCAIDIResults,
            ],
            clustering_results=None,
            time_array=None,
            study_results_type=StudyResultsType.Clustering
        )

        self.LOLE_evolution = np.zeros(nsim)
        self.ENS_evolution = np.zeros(nsim)
        self.LOLF_evolution = np.zeros(nsim)
        self.LOLET_evolution = np.zeros(nsim)
        self.LOLFT_evolution = np.zeros(nsim)
        self.SAIDI_evolution = np.zeros(nsim)
        self.SAIFI_evolution = np.zeros(nsim)
        self.CAIDI_evolution = np.zeros(nsim)


    def mdl(self, result_type: ResultTypes) -> ResultsTable:
        """
        Plot the results.
        :param result_type: ResultTypes
        :return: ResultsModel
        """

        if result_type == ResultTypes.ReliabilityLOLEResults:
            return ResultsTable(data=self.LOLE_evolution,
                                index=np.arange(len(self.LOLE_evolution), dtype=int),
                                columns=np.array(['LOLE']),
                                title=result_type.value,
                                units="hours",
                                idx_device_type=DeviceType.NoDevice,
                                cols_device_type=DeviceType.NoDevice,
                                ylabel='incident_hours/year')

        elif result_type == ResultTypes.ReliabilityENSResults:
            return ResultsTable(data=self.ENS_evolution,
                                index=np.arange(len(self.ENS_evolution), dtype=int),
                                columns=np.array(['ENS']),
                                title=result_type.value,
                                units="MWh",
                                idx_device_type=DeviceType.NoDevice,
                                cols_device_type=DeviceType.NoDevice,
                                ylabel='MWh/year')

        elif result_type == ResultTypes.ReliabilityLOLFResults:
            return ResultsTable(data=self.LOLF_evolution,
                                index=np.arange(len(self.LOLF_evolution), dtype=int),
                                columns=np.array(['LOLF']),
                                title=result_type.value,
                                units="nº of incidences",
                                idx_device_type=DeviceType.NoDevice,
                                cols_device_type=DeviceType.NoDevice,
                                ylabel='nº of incidences/year')

        elif result_type == ResultTypes.ReliabilityLOLETResults:
            return ResultsTable(data=self.LOLET_evolution,
                                index=np.arange(len(self.LOLET_evolution), dtype=int),
                                columns=np.array(['LOLET_total']),
                                title=result_type.value,
                                units="nº of hours",
                                idx_device_type=DeviceType.NoDevice,
                                cols_device_type=DeviceType.NoDevice,
                                ylabel='failure_hours/year')

        elif result_type == ResultTypes.ReliabilityLOLFTResults:
            return ResultsTable(data=self.LOLFT_evolution,
                                index=np.arange(len(self.LOLFT_evolution), dtype=int),
                                columns=np.array(['LOLFT_total']),
                                title=result_type.value,
                                units="nº of failures",
                                idx_device_type=DeviceType.NoDevice,
                                cols_device_type=DeviceType.NoDevice,
                                ylabel='nº of failures/year')

        elif result_type == ResultTypes.ReliabilitySAIDIResults:
            return ResultsTable(data=self.SAIDI_evolution,
                                index=np.arange(len(self.SAIDI_evolution), dtype=int),
                                columns=np.array(['SAIDI']),
                                title=result_type.value,
                                units="hours/customer",
                                idx_device_type=DeviceType.NoDevice,
                                cols_device_type=DeviceType.NoDevice,
                                ylabel='customer_interruption_hours/customer')

        elif result_type == ResultTypes.ReliabilitySAIFIResults:
            return ResultsTable(data=self.SAIFI_evolution,
                                index=np.arange(len(self.SAIFI_evolution), dtype=int),
                                columns=np.array(['SAIFI']),
                                title=result_type.value,
                                units="interruptions/customer",
                                idx_device_type=DeviceType.NoDevice,
                                cols_device_type=DeviceType.NoDevice,
                                ylabel='customer_interruptions/customer')

        elif result_type == ResultTypes.ReliabilityCAIDIResults:
            return ResultsTable(data=self.CAIDI_evolution,
                                index=np.arange(len(self.CAIDI_evolution), dtype=int),
                                columns=np.array(['CAIDI']),
                                title=result_type.value,
                                units="hours/interruption",
                                idx_device_type=DeviceType.NoDevice,
                                cols_device_type=DeviceType.NoDevice,
                                ylabel='customer_interruption_hours/interruption')

        else:
            raise Exception('Result type not understood:' + str(result_type))
