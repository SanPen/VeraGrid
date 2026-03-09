# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Union, Tuple
import numpy as np
from VeraGridEngine.enumerations import AvailableTransferMode, SubObjectType
from VeraGridEngine.basic_structures import Vec, IntVec
from VeraGridEngine.Simulations.options_template import OptionsTemplate
from VeraGridEngine.Devices.Parents.editable_device import GCProp



class AvailableTransferCapacityOptions(OptionsTemplate):
    """
    Available Transfer Capacity Options
    """

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(key="distributed_slack", tpe=bool),
        GCProp(key="correct_values", tpe=bool),
        GCProp(key="use_provided_flows", tpe=bool),
        GCProp(key="bus_idx_from", tpe=SubObjectType.Array),
        GCProp(key="bus_idx_to", tpe=SubObjectType.Array),
        GCProp(key="inter_area_branch_idx", tpe=SubObjectType.Array),
        GCProp(key="inter_area_branch_sense", tpe=SubObjectType.Array),
        GCProp(key="Pf", tpe=SubObjectType.Array),
        GCProp(key="idx_hvdc_br", tpe=SubObjectType.Array),
        GCProp(key="inter_area_hvdc_branch_sense", tpe=SubObjectType.Array),
        GCProp(key="Pf_hvdc", tpe=SubObjectType.Array),
        GCProp(key="dT", tpe=float),
        GCProp(key="threshold", tpe=float),
        GCProp(key="mode", tpe=AvailableTransferMode),
        GCProp(key="max_report_elements", tpe=int),
        GCProp(key="use_clustering", tpe=bool),
        GCProp(key="cluster_number", tpe=int),
    )

    def __init__(self,
                 distributed_slack: bool = True,
                 correct_values: bool = True,
                 use_provided_flows: bool = False,
                 bus_idx_from: Union[None, IntVec] = None,
                 bus_idx_to: Union[None, IntVec] = None,
                 idx_br: Union[None, IntVec] = None,
                 sense_br: Union[None, Vec] = None,
                 Pf: Union[None, Vec] = None,
                 idx_hvdc_br: Union[None, IntVec] = None,
                 sense_hvdc_br: Union[None, Vec] = None,
                 Pf_hvdc: Union[None, Vec] = None,
                 dT: float = 100.0,
                 threshold: float = 0.02,
                 mode: AvailableTransferMode = AvailableTransferMode.Generation,
                 max_report_elements: int = -1,
                 use_clustering: bool = False,
                 cluster_number: int = 200):
        """
        Available Transfer Capacity Options
        :param distributed_slack: Distribute the slack effect?
        :param correct_values: Correct the theoretical glitch values to [-1, 1] ?
        :param use_provided_flows: Use the provided flows?
        :param bus_idx_from: array of bus from idx for every branch
        :param bus_idx_to: array of bus to idx for every branch
        :param idx_br: array of selected branches idx
        :param sense_br: array of sense sign of the branches.
                        1 if the branch connection goes in the same sense as the transfer, -1 otherwise
        :param Pf: Array of base real power flow values for all the branches
        :param idx_hvdc_br: Array of HVDC slected indices
        :param sense_hvdc_br: array of sense sign of the HVDC branches.
                             1 if the branch connection goes in the same sense as the transfer, -1 otherwise
        :param Pf_hvdc: Array of base real power flow values for all the HVDC
        :param dT: increment o transfer in MW
        :param threshold: Sentitivity threeshold to the transfer
        :param mode: AvailableTransferMode
        :param max_report_elements: maximum number of elements to show in the report (-1 for all)
        :param use_clustering: Use clustering?
        """
        OptionsTemplate.__init__(self, name="AvailableTransferCapacityOptions")

        self.distributed_slack = distributed_slack
        self.correct_values = correct_values
        self.use_provided_flows = use_provided_flows

        empty_idx = np.zeros(0, dtype=int)

        self.bus_idx_from: IntVec = bus_idx_from if bus_idx_from is not None else empty_idx
        self.bus_idx_to: IntVec = bus_idx_to if bus_idx_to is not None else empty_idx
        self.inter_area_branch_idx: IntVec = idx_br if idx_br is not None else empty_idx
        self.inter_area_branch_sense: IntVec = sense_br if sense_br is not None else empty_idx

        self.Pf: Union[None, Vec] = Pf

        self.idx_hvdc_br: IntVec = idx_hvdc_br if idx_hvdc_br is not None else empty_idx
        self.inter_area_hvdc_branch_sense: IntVec = sense_hvdc_br if sense_hvdc_br is not None else empty_idx

        self.Pf_hvdc: Union[None, Vec] = Pf_hvdc

        self.dT = dT
        self.threshold = threshold
        self.mode = mode
        self.max_report_elements = max_report_elements
        self.use_clustering = use_clustering
        self.cluster_number = cluster_number



