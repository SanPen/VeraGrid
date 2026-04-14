# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import List
from VeraGridEngine.IO.iidm.devices.rtesubstation import IidmSubstation
from VeraGridEngine.IO.iidm.devices.voltage_level import IidmVoltageLevel
from VeraGridEngine.IO.iidm.devices.rte_area import IidmArea
from VeraGridEngine.IO.iidm.devices.rte_bus import IidmBus
from VeraGridEngine.IO.iidm.devices.generator import IidmGenerator
from VeraGridEngine.IO.iidm.devices.load import Load
from VeraGridEngine.IO.iidm.devices.line import IidmLine
from VeraGridEngine.IO.iidm.devices.two_winding_transformer import TwoWindingsTransformer
from VeraGridEngine.IO.iidm.devices.rte_dangling_line import IidmDanglingLine
from VeraGridEngine.IO.iidm.devices.shunt import Shunt
from VeraGridEngine.IO.iidm.devices.switch import Switch
from VeraGridEngine.IO.iidm.devices.rte_busbar_section import IidmBusbarSection
from VeraGridEngine.IO.iidm.devices.static_var_compensator import StaticVarCompensator

class IidmCircuit:
    def __init__(self):
        self.substations: List[IidmSubstation] = []
        self.voltage_levels: List[IidmVoltageLevel] = []
        self.areas: List[IidmArea] = []
        self.buses: List[IidmBus] = []
        self.generators: List[IidmGenerator] = []
        self.loads: List[Load] = []
        self.lines: List[IidmLine] = []
        self.transformers: List[TwoWindingsTransformer] = []
        self.dangling_lines: List[IidmDanglingLine] = []
        self.shunts: List[Shunt] = []
        self.switches: List[Switch] = []
        self.busbar_sections: List[IidmBusbarSection] = []
        self.svcs: List[StaticVarCompensator] = []