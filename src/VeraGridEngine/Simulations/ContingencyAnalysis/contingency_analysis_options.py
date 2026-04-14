# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import List, Union, Tuple
from VeraGridEngine.enumerations import ContingencyMethod, SubObjectType, DeviceType
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions, SolverType
from VeraGridEngine.Simulations.LinearFactors.linear_analysis_options import LinearAnalysisOptions
from VeraGridEngine.Devices.Events.contingency_group import ContingencyGroup
from VeraGridEngine.Simulations.options_template import OptionsTemplate
from VeraGridEngine.Devices.Parents.editable_device import GCProp



class ContingencyAnalysisOptions(OptionsTemplate):
    """
    Contingency analysis options
    """

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(key="use_provided_flows", tpe=bool),
        GCProp(key="Pf", tpe=SubObjectType.Array),
        GCProp(key="contingency_method", tpe=ContingencyMethod),
        GCProp(key="pf_options", tpe=DeviceType.SimulationOptionsDevice),
        GCProp(key="lin_options", tpe=DeviceType.SimulationOptionsDevice),
        GCProp(key="use_srap", tpe=bool),
        GCProp(key="srap_max_power", tpe=float),
        GCProp(key="srap_top_n", tpe=int),
        GCProp(key="srap_deadband", tpe=float),
        GCProp(key="srap_rever_to_nominal_rating", tpe=bool),
        GCProp(key="detailed_massive_report", tpe=bool),
        GCProp(key="contingency_deadband", tpe=float),
        GCProp(key="contingency_groups", tpe=SubObjectType.ObjectsList),
    )

    def __init__(self,
                 pf_options:PowerFlowOptions | None = None,
                 lin_options:LinearAnalysisOptions|None = None,
                 use_srap: bool = False,
                 srap_max_power: float = 1400.0,
                 srap_top_n: int = 5,
                 srap_deadband: float = 10,
                 srap_rever_to_nominal_rating: bool = False,
                 detailed_massive_report: bool = False,
                 contingency_deadband: float = 0.0,
                 contingency_method=ContingencyMethod.PowerFlow,
                 contingency_groups: Union[List[ContingencyGroup], None] = None):
        """
        ContingencyAnalysisOptions
        :param pf_options: PowerFlowOptions
        :param lin_options: LinearAnalysisOptions
        :param use_srap: use the SRAP check?
        :param srap_max_power: maximum SRAP usage (limit) in MW
        :param srap_top_n: Maximum number of nodes to use with SRAP
        :param srap_deadband: Dead band over the SRAP rating. If greater than zero,
                              the SRAP is investigated for values over the branch
                              protections rating until the specified value. (in %)
        :param srap_rever_to_nominal_rating: If checked, the SRAP objective solution is the branch nominal rate.
                                             Otherwise, the objective rating is the contingency rating.
        :param detailed_massive_report: If checked, a massive possibly intractable report is generated.
        :param contingency_deadband: Deadband to report contingencies
        :param contingency_method: ContingencyEngine to use (PowerFlow, PTDF, ...)
        :param contingency_groups: List of contingencies to use, if None all will be used
        """
        OptionsTemplate.__init__(self, name="ContingencyAnalysisOptions")

        self.contingency_method = contingency_method

        self.pf_options = PowerFlowOptions(SolverType.Linear) if pf_options is None else pf_options

        self.lin_options = LinearAnalysisOptions() if lin_options is None else lin_options

        self.use_srap: bool = use_srap

        self.srap_max_power: float = srap_max_power

        self.srap_top_n = srap_top_n

        self.srap_deadband: float = srap_deadband

        self.srap_revert_to_nominal_rating: bool = srap_rever_to_nominal_rating

        self.detailed_massive_report = detailed_massive_report

        self.contingency_deadband = contingency_deadband

        self.contingency_groups: Union[List[ContingencyGroup], None] = contingency_groups

