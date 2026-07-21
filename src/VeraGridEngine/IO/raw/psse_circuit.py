# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import datetime
from typing import List, Dict, Tuple

from VeraGridEngine.IO.raw.psse_object import RawObject
from VeraGridEngine.IO.raw.psse_property import PsseProperty
from VeraGridEngine.IO.raw.raw_types import RawAreaLike, RawBranchLike, RawBusLike, RawEquipmentTerminalLike, \
    RawFACTSLike, RawFixedShuntLike, RawGeneratorLike, RawGneDeviceLike, RawImpedanceCorrectionTableLike, \
    RawInductionMachineLike, RawInterAreaLike, RawLoadLike, RawMultiLineSectionLike, RawNodeLike, RawOwnerLike, \
    RawSubstationLike, RawSubstationSwitchingDeviceLike, RawSwitchedShuntLike, RawSystemSwitchingDeviceLike, \
    RawTransformerLike, RawTwoTerminalDCLineLike, RawVscDCLineLike, RawZoneLike
from VeraGridEngine.IO.raw.versioned.base.multi_section_line import RawMultiLineSection
from VeraGridEngine.IO.raw.versioned.base.area import RawArea
from VeraGridEngine.IO.raw.versioned.base.branch import RawBranch
from VeraGridEngine.IO.raw.versioned.base.bus import RawBus
from VeraGridEngine.IO.raw.versioned.base.facts import RawFACTS
from VeraGridEngine.IO.raw.versioned.base.generator import RawGenerator
from VeraGridEngine.IO.raw.versioned.base.induction_machine import RawInductionMachine
from VeraGridEngine.IO.raw.versioned.base.inter_area import RawInterArea
from VeraGridEngine.IO.raw.versioned.base.load import RawLoad
from VeraGridEngine.IO.raw.versioned.base.fixed_shunt import RawFixedShunt
from VeraGridEngine.IO.raw.versioned.base.switched_shunt import RawSwitchedShunt
from VeraGridEngine.IO.raw.versioned.base.transformer import RawTransformer
from VeraGridEngine.IO.raw.versioned.base.two_terminal_dc_line import RawTwoTerminalDCLine
from VeraGridEngine.IO.raw.versioned.base.vsc_dc_line import RawVscDCLine
from VeraGridEngine.IO.raw.versioned.base.zone import RawZone
from VeraGridEngine.IO.raw.versioned.base.owner import RawOwner
from VeraGridEngine.IO.raw.versioned.base.substation import RawSubstation
from VeraGridEngine.IO.raw.versioned.base.node import RawNode
from VeraGridEngine.IO.raw.versioned.base.substation_switching_device import RawSubstationSwitchingDevice
from VeraGridEngine.IO.raw.versioned.base.equipment_terminal import RawEquipmentTerminal
from VeraGridEngine.IO.raw.versioned.base.gne_device import RawGneDevice
from VeraGridEngine.IO.raw.versioned.base.impedance_correction_table import RawImpedanceCorrectionTable
from VeraGridEngine.IO.raw.versioned.base.system_switching_device import RawSystemSwitchingDevice
from VeraGridEngine.IO.base.base_circuit import BaseCircuit
from VeraGridEngine.basic_structures import Logger


class PsseCircuit(RawObject, BaseCircuit):
    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name='areas', rawx_key='area', class_type=RawArea),
        PsseProperty(property_name='inter_areas', rawx_key='iatrans', class_type=RawInterArea),
        PsseProperty(property_name='zones', rawx_key='zone', class_type=RawZone),
        PsseProperty(property_name='owners', rawx_key='owner', class_type=RawOwner),
        PsseProperty(property_name='buses', rawx_key='bus', class_type=RawBus),
        PsseProperty(property_name='branches', rawx_key='acline', class_type=RawBranch),
        PsseProperty(property_name='transformers', rawx_key='transformer', class_type=RawTransformer),
        PsseProperty(property_name='two_terminal_dc_lines', rawx_key='twotermdc', class_type=RawTwoTerminalDCLine),
        PsseProperty(property_name='vsc_dc_lines', rawx_key='vscdc', class_type=RawVscDCLine),
        PsseProperty(property_name='facts', rawx_key='facts', class_type=RawFACTS),
        PsseProperty(property_name='loads', rawx_key='load', class_type=RawLoad),
        PsseProperty(property_name='generators', rawx_key='generator', class_type=RawGenerator),
        PsseProperty(property_name='induction_machines', rawx_key='indmach', class_type=RawInductionMachine),
        PsseProperty(property_name='fixed_shunts', rawx_key='fixshunt', class_type=RawFixedShunt),
        PsseProperty(property_name='switched_shunts', rawx_key='swshunt', class_type=RawSwitchedShunt),
        PsseProperty(property_name='substations', rawx_key='sub', class_type=RawSubstation),
        PsseProperty(property_name='nodes', rawx_key='subnode', class_type=RawNode),
        PsseProperty(property_name='substation_switching_devices', rawx_key='subswd',
                     class_type=RawSubstationSwitchingDevice),
        PsseProperty(property_name='equipment_terminals', rawx_key='subterm', class_type=RawEquipmentTerminal),
        PsseProperty(property_name='switches', rawx_key='sysswd', class_type=RawSystemSwitchingDevice),
        PsseProperty(property_name='gne', rawx_key='gne', class_type=RawGneDevice),
        PsseProperty(property_name='indiction_tables', rawx_key='impcor', class_type=RawImpedanceCorrectionTable),
        PsseProperty(property_name='multi_line_sections', rawx_key='msline', class_type=RawMultiLineSection),
    )

    def __init__(self):
        RawObject.__init__(self, "Circuit")
        BaseCircuit.__init__(self)

        self.IC = ''
        self.SBASE = 100.0
        self.REV = 35
        self.XFRRAT = 0
        self.NXFRAT = 0
        self.BASFRQ = 50

        self.date_time: datetime.datetime | None = None

        self.areas: List[RawAreaLike] = list()

        self.inter_areas: List[RawInterAreaLike] = list()

        self.zones: List[RawZoneLike] = list()

        self.owners: List[RawOwnerLike] = list()

        self.buses: List[RawBusLike] = list()

        self.branches: List[RawBranchLike] = list()

        self.transformers: List[RawTransformerLike] = list()

        self.two_terminal_dc_lines: List[RawTwoTerminalDCLineLike] = list()

        self.vsc_dc_lines: List[RawVscDCLineLike] = list()

        self.facts: List[RawFACTSLike] = list()

        self.loads: List[RawLoadLike] = list()

        self.generators: List[RawGeneratorLike] = list()

        self.induction_machines: List[RawInductionMachineLike] = list()

        self.fixed_shunts: List[RawFixedShuntLike] = list()

        self.switched_shunts: List[RawSwitchedShuntLike] = list()

        self.substations: List[RawSubstationLike] = list()

        self.nodes: List[RawNodeLike] = list()

        self.substation_switching_devices: List[RawSubstationSwitchingDeviceLike] = list()

        self.equipment_terminals: List[RawEquipmentTerminalLike] = list()

        self.switches: List[RawSystemSwitchingDeviceLike] = list()

        self.gne: List[RawGneDeviceLike] = list()

        self.indiction_tables: List[RawImpedanceCorrectionTableLike] = list()

        self.multi_line_sections: List[RawMultiLineSectionLike] = list()

    def parse(self, data: List[int | float], logger: Logger) -> None:
        """
        Parse the basic data
        :param data: line with information
        :param logger: logger object
        :return:
        """
        if len(data) == 6:
            self.IC, self.SBASE, self.REV, self.XFRRAT, self.NXFRAT, self.BASFRQ = data
        elif len(data) == 3:
            self.IC, self.SBASE, self.REV = data
            logger.add_warning("RAW header contains 3 elements instead of the expected 6")
        else:
            logger.add_warning(f"RAW header contains {len(data)} elements instead of the expected 6")

    def get_class_properties(self) -> List[PsseProperty]:
        """

        :return:
        """
        return [p for p in self.get_properties() if p.class_type not in [str, bool, int, float]]

    def check_primary_keys(self, logger: Logger = Logger()):
        """
        Check all primary keys locally and globally
        :param logger:
        :return:
        """

        global_index = dict()

        for prop in self.get_class_properties():

            local_index = dict()
            lst = self.__dict__[prop.property_name]

            for elm in lst:
                id_ = elm.get_id()
                uuid_ = elm.get_uuid5()

                if id_ in local_index:
                    found_elm = local_index[id_]
                    logger.add_error(msg="Local ID duplicate", device=id_,
                                     device_class=prop.rawx_key,
                                     comment="Found {}:{}".format(found_elm.class_name, found_elm.get_id()))
                else:
                    local_index[id_] = elm

                if uuid_ in global_index:
                    found_elm = global_index[uuid_]
                    logger.add_info(msg="Global UUID5 duplicate", device=id_,
                                    device_class=prop.rawx_key, value=uuid_,
                                    comment="Found {}:{}".format(found_elm.class_name, found_elm.get_id()))
                else:
                    global_index[uuid_] = elm
