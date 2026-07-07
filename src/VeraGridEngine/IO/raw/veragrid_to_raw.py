# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import math

import numpy as np
from typing import Dict, List, Set
from itertools import groupby
from scipy.sparse import lil_matrix

from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.IO.raw.versioned.v29.area import RawAreaV29
from VeraGridEngine.IO.raw.versioned.v29.zone import RawZoneV29
from VeraGridEngine.IO.raw.versioned.v29.bus import RawBusV29
from VeraGridEngine.IO.raw.versioned.v29.load import RawLoadV29
from VeraGridEngine.IO.raw.versioned.v29.generator import RawGeneratorV29
from VeraGridEngine.IO.raw.versioned.v29.fixed_shunt import RawFixedShuntV29
from VeraGridEngine.IO.raw.versioned.v29.switched_shunt import RawSwitchedShuntV29
from VeraGridEngine.IO.raw.versioned.v29.branch import RawBranchV29
from VeraGridEngine.IO.raw.versioned.v29.system_switching_device import RawSystemSwitchingDeviceV29
from VeraGridEngine.IO.raw.versioned.v29.transformer import RawTransformerV29
from VeraGridEngine.IO.raw.versioned.v29.vsc_dc_line import RawVscDCLineV29
from VeraGridEngine.IO.raw.versioned.v29.two_terminal_dc_line import RawTwoTerminalDCLineV29
from VeraGridEngine.IO.raw.versioned.v29.facts import RawFACTSV29
from VeraGridEngine.IO.raw.versioned.v30.area import RawAreaV30
from VeraGridEngine.IO.raw.versioned.v30.zone import RawZoneV30
from VeraGridEngine.IO.raw.versioned.v30.bus import RawBusV30
from VeraGridEngine.IO.raw.versioned.v30.load import RawLoadV30
from VeraGridEngine.IO.raw.versioned.v30.generator import RawGeneratorV30
from VeraGridEngine.IO.raw.versioned.v30.fixed_shunt import RawFixedShuntV30
from VeraGridEngine.IO.raw.versioned.v30.switched_shunt import RawSwitchedShuntV30
from VeraGridEngine.IO.raw.versioned.v30.branch import RawBranchV30
from VeraGridEngine.IO.raw.versioned.v30.system_switching_device import RawSystemSwitchingDeviceV30
from VeraGridEngine.IO.raw.versioned.v30.transformer import RawTransformerV30
from VeraGridEngine.IO.raw.versioned.v30.vsc_dc_line import RawVscDCLineV30
from VeraGridEngine.IO.raw.versioned.v30.two_terminal_dc_line import RawTwoTerminalDCLineV30
from VeraGridEngine.IO.raw.versioned.v30.facts import RawFACTSV30
from VeraGridEngine.IO.raw.versioned.v31.area import RawAreaV31
from VeraGridEngine.IO.raw.versioned.v31.zone import RawZoneV31
from VeraGridEngine.IO.raw.versioned.v31.bus import RawBusV31
from VeraGridEngine.IO.raw.versioned.v31.load import RawLoadV31
from VeraGridEngine.IO.raw.versioned.v31.generator import RawGeneratorV31
from VeraGridEngine.IO.raw.versioned.v31.fixed_shunt import RawFixedShuntV31
from VeraGridEngine.IO.raw.versioned.v31.switched_shunt import RawSwitchedShuntV31
from VeraGridEngine.IO.raw.versioned.v31.branch import RawBranchV31
from VeraGridEngine.IO.raw.versioned.v31.system_switching_device import RawSystemSwitchingDeviceV31
from VeraGridEngine.IO.raw.versioned.v31.transformer import RawTransformerV31
from VeraGridEngine.IO.raw.versioned.v31.vsc_dc_line import RawVscDCLineV31
from VeraGridEngine.IO.raw.versioned.v31.two_terminal_dc_line import RawTwoTerminalDCLineV31
from VeraGridEngine.IO.raw.versioned.v31.facts import RawFACTSV31
from VeraGridEngine.IO.raw.versioned.v32.area import RawAreaV32
from VeraGridEngine.IO.raw.versioned.v32.zone import RawZoneV32
from VeraGridEngine.IO.raw.versioned.v32.bus import RawBusV32
from VeraGridEngine.IO.raw.versioned.v32.load import RawLoadV32
from VeraGridEngine.IO.raw.versioned.v32.generator import RawGeneratorV32
from VeraGridEngine.IO.raw.versioned.v32.fixed_shunt import RawFixedShuntV32
from VeraGridEngine.IO.raw.versioned.v32.switched_shunt import RawSwitchedShuntV32
from VeraGridEngine.IO.raw.versioned.v32.branch import RawBranchV32
from VeraGridEngine.IO.raw.versioned.v32.system_switching_device import RawSystemSwitchingDeviceV32
from VeraGridEngine.IO.raw.versioned.v32.transformer import RawTransformerV32
from VeraGridEngine.IO.raw.versioned.v32.vsc_dc_line import RawVscDCLineV32
from VeraGridEngine.IO.raw.versioned.v32.two_terminal_dc_line import RawTwoTerminalDCLineV32
from VeraGridEngine.IO.raw.versioned.v32.facts import RawFACTSV32
from VeraGridEngine.IO.raw.versioned.v33.area import RawAreaV33
from VeraGridEngine.IO.raw.versioned.v33.zone import RawZoneV33
from VeraGridEngine.IO.raw.versioned.v33.bus import RawBusV33
from VeraGridEngine.IO.raw.versioned.v33.load import RawLoadV33
from VeraGridEngine.IO.raw.versioned.v33.generator import RawGeneratorV33
from VeraGridEngine.IO.raw.versioned.v33.fixed_shunt import RawFixedShuntV33
from VeraGridEngine.IO.raw.versioned.v33.switched_shunt import RawSwitchedShuntV33
from VeraGridEngine.IO.raw.versioned.v33.branch import RawBranchV33
from VeraGridEngine.IO.raw.versioned.v33.system_switching_device import RawSystemSwitchingDeviceV33
from VeraGridEngine.IO.raw.versioned.v33.transformer import RawTransformerV33
from VeraGridEngine.IO.raw.versioned.v33.vsc_dc_line import RawVscDCLineV33
from VeraGridEngine.IO.raw.versioned.v33.two_terminal_dc_line import RawTwoTerminalDCLineV33
from VeraGridEngine.IO.raw.versioned.v33.facts import RawFACTSV33
from VeraGridEngine.IO.raw.versioned.v34.area import RawAreaV34
from VeraGridEngine.IO.raw.versioned.v34.zone import RawZoneV34
from VeraGridEngine.IO.raw.versioned.v34.bus import RawBusV34
from VeraGridEngine.IO.raw.versioned.v34.load import RawLoadV34
from VeraGridEngine.IO.raw.versioned.v34.generator import RawGeneratorV34
from VeraGridEngine.IO.raw.versioned.v34.fixed_shunt import RawFixedShuntV34
from VeraGridEngine.IO.raw.versioned.v34.switched_shunt import RawSwitchedShuntV34
from VeraGridEngine.IO.raw.versioned.v34.branch import RawBranchV34
from VeraGridEngine.IO.raw.versioned.v34.system_switching_device import RawSystemSwitchingDeviceV34
from VeraGridEngine.IO.raw.versioned.v34.transformer import RawTransformerV34
from VeraGridEngine.IO.raw.versioned.v34.vsc_dc_line import RawVscDCLineV34
from VeraGridEngine.IO.raw.versioned.v34.two_terminal_dc_line import RawTwoTerminalDCLineV34
from VeraGridEngine.IO.raw.versioned.v34.facts import RawFACTSV34
from VeraGridEngine.IO.raw.versioned.v34.substation import RawSubstationV34
from VeraGridEngine.IO.raw.versioned.v34.node import RawNodeV34
from VeraGridEngine.IO.raw.versioned.v34.substation_switching_device import RawSubstationSwitchingDeviceV34
from VeraGridEngine.IO.raw.versioned.v34.equipment_terminal import RawEquipmentTerminalV34
from VeraGridEngine.IO.raw.versioned.v35.area import RawAreaV35
from VeraGridEngine.IO.raw.versioned.v35.zone import RawZoneV35
from VeraGridEngine.IO.raw.versioned.v35.bus import RawBusV35
from VeraGridEngine.IO.raw.versioned.v35.load import RawLoadV35
from VeraGridEngine.IO.raw.versioned.v35.generator import RawGeneratorV35
from VeraGridEngine.IO.raw.versioned.v35.fixed_shunt import RawFixedShuntV35
from VeraGridEngine.IO.raw.versioned.v35.switched_shunt import RawSwitchedShuntV35
from VeraGridEngine.IO.raw.versioned.v35.branch import RawBranchV35
from VeraGridEngine.IO.raw.versioned.v35.system_switching_device import RawSystemSwitchingDeviceV35
from VeraGridEngine.IO.raw.versioned.v35.transformer import RawTransformerV35
from VeraGridEngine.IO.raw.versioned.v35.vsc_dc_line import RawVscDCLineV35
from VeraGridEngine.IO.raw.versioned.v35.two_terminal_dc_line import RawTwoTerminalDCLineV35
from VeraGridEngine.IO.raw.versioned.v35.facts import RawFACTSV35
from VeraGridEngine.IO.raw.versioned.v35.substation import RawSubstationV35
from VeraGridEngine.IO.raw.versioned.v35.node import RawNodeV35
from VeraGridEngine.IO.raw.versioned.v35.substation_switching_device import RawSubstationSwitchingDeviceV35
from VeraGridEngine.IO.raw.versioned.v35.equipment_terminal import RawEquipmentTerminalV35
from VeraGridEngine.IO.raw.versioned.v36.area import RawAreaV36
from VeraGridEngine.IO.raw.versioned.v36.zone import RawZoneV36
from VeraGridEngine.IO.raw.versioned.v36.bus import RawBusV36
from VeraGridEngine.IO.raw.versioned.v36.load import RawLoadV36
from VeraGridEngine.IO.raw.versioned.v36.generator import RawGeneratorV36
from VeraGridEngine.IO.raw.versioned.v36.fixed_shunt import RawFixedShuntV36
from VeraGridEngine.IO.raw.versioned.v36.switched_shunt import RawSwitchedShuntV36
from VeraGridEngine.IO.raw.versioned.v36.branch import RawBranchV36
from VeraGridEngine.IO.raw.versioned.v36.system_switching_device import RawSystemSwitchingDeviceV36
from VeraGridEngine.IO.raw.versioned.v36.transformer import RawTransformerV36
from VeraGridEngine.IO.raw.versioned.v36.vsc_dc_line import RawVscDCLineV36
from VeraGridEngine.IO.raw.versioned.v36.two_terminal_dc_line import RawTwoTerminalDCLineV36
from VeraGridEngine.IO.raw.versioned.v36.facts import RawFACTSV36
from VeraGridEngine.IO.raw.versioned.v36.substation import RawSubstationV36
from VeraGridEngine.IO.raw.versioned.v36.node import RawNodeV36
from VeraGridEngine.IO.raw.versioned.v36.substation_switching_device import RawSubstationSwitchingDeviceV36
from VeraGridEngine.IO.raw.versioned.v36.equipment_terminal import RawEquipmentTerminalV36
from VeraGridEngine.IO.raw.psse_circuit import PsseCircuit
from VeraGridEngine.IO.raw.psse_object import RawObject
from VeraGridEngine.IO.raw.raw_types import (RawAreaLike, RawBranchLike, RawBusLike, RawEquipmentTerminalLike,
                                             RawFACTSLike, RawFixedShuntLike, RawGeneratorLike, RawLoadLike,
                                             RawNodeLike, RawSubstationLike,
                                             RawSubstationSwitchingDeviceLike, RawSwitchedShuntLike,
                                             RawSystemSwitchingDeviceLike, RawTransformerLike,
                                             RawTwoTerminalDCLineLike, RawVscDCLineLike, RawZoneLike)
import VeraGridEngine.Devices as dev
from VeraGridEngine.Devices.types import BRANCH_TYPES
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import (TapChangerTypes,
                                         TapPhaseControl,
                                         TapModuleControl,
                                         SwitchGraphicType,
                                         PsseTopologyExportMode)


def _set_if_registered(raw_obj: RawObject, property_name: str, value) -> None:
    """

    :param raw_obj:
    :param property_name:
    :param value:
    :return:
    """
    raw_obj.set_registered_property_value(property_name, value)


def _set_branch_ratings(raw_branch: RawObject,
                        version: int,
                        rate: float,
                        contingency_factor: float,
                        protection_factor: float) -> None:
    """

    :param raw_branch:
    :param version:
    :param rate:
    :param contingency_factor:
    :param protection_factor:
    :return:
    """
    rate2 = rate * contingency_factor
    rate3 = rate * protection_factor
    if version <= 33:
        raw_branch.RATEA = rate
        raw_branch.RATEB = rate2
        raw_branch.RATEC = rate3
    else:
        raw_branch.RATE1 = rate
        raw_branch.RATE2 = rate2
        raw_branch.RATE3 = rate3


def _set_transformer_winding_ratings(raw_transformer: RawTransformerLike,
                                     version: int,
                                     winding_index: int,
                                     rate: float,
                                     contingency_factor: float,
                                     protection_factor: float) -> None:
    """

    :param raw_transformer:
    :param version:
    :param winding_index:
    :param rate:
    :param contingency_factor:
    :param protection_factor:
    :return:
    """
    rate2 = rate * contingency_factor
    rate3 = rate * protection_factor
    raw_transformer.set_winding_rating_triplet(winding_index=winding_index,
                                               version=version,
                                               rate_1=rate,
                                               rate_2=rate2,
                                               rate_3=rate3)


def _normalize_psse_version(version: int) -> int:
    """
    Clamp the requested PSSE RAW version to the supported VeraGrid range.

    :param version: Requested PSSE RAW version.
    :return: Supported PSSE RAW version.
    """
    if version > 36:
        return 36
    elif version < 29:
        return 33
    else:
        return version


class RawNodeBreakerExportData:
    """
    Typed storage for the optional PSSE 34+ node-breaker projection.
    """

    __slots__ = (
        "bus_number_by_bus",
        "node_number_by_bus",
        "substation_number_by_substation",
        "substations",
        "nodes",
        "substation_switching_devices",
        "equipment_terminals",
    )

    def __init__(self) -> None:
        """
        Initialize the export storage.

        :return: None
        """
        self.bus_number_by_bus: Dict[dev.Bus, int] = dict()
        self.node_number_by_bus: Dict[dev.Bus, int] = dict()
        self.substation_number_by_substation: Dict[dev.Substation, int] = dict()
        self.substations: List[RawSubstationLike] = list()
        self.nodes: List[RawNodeLike] = list()
        self.substation_switching_devices: List[RawSubstationSwitchingDeviceLike] = list()
        self.equipment_terminals: List[RawEquipmentTerminalLike] = list()


def get_export_substations(grid: MultiCircuit) -> List[dev.Substation]:
    """
    Collect the substations that are actually referenced by buses.

    :param grid: VeraGrid circuit.
    :return: Ordered list of substations to export.
    """
    substations: List[dev.Substation] = list()
    seen_substations: Set[dev.Substation] = set()

    for substation in grid.substations:
        buses = grid.get_substation_buses(substation=substation)
        if len(buses) > 0:
            substations.append(substation)
            seen_substations.add(substation)
        else:
            pass

    for bus in grid.buses:
        if bus.substation is not None and bus.substation not in seen_substations:
            substations.append(bus.substation)
            seen_substations.add(bus.substation)
        else:
            pass

    return substations


def get_psse_substation(substation: dev.Substation,
                        psse_number: int,
                        version: int,
                        t_idx: int | None = None) -> RawSubstationLike:
    """
    Convert a VeraGrid substation into a PSSE substation record.

    :param substation: VeraGrid substation.
    :param psse_number: PSSE substation number.
    :param version: Target PSSE RAW version.
    :return: RAW substation record.
    """
    version = _normalize_psse_version(version=version)
    if version <= 34:
        psse_substation: RawSubstationLike = RawSubstationV34()
    elif version == 35:
        psse_substation = RawSubstationV35()
    else:
        psse_substation = RawSubstationV36()
    psse_substation.IS = psse_number
    psse_substation.NAME = str(substation.name)
    psse_substation.LATI = float(substation.latitude)
    psse_substation.LONG = float(substation.longitude)
    psse_substation.SGR = 0.0
    return psse_substation


def get_psse_node(bus: dev.Bus,
                  node_number: int,
                  electrical_bus_number: int,
                  version: int,
                  t_idx: int | None = None) -> RawNodeLike:
    """
    Convert a VeraGrid bus into a PSSE node record.

    :param bus: VeraGrid bus.
    :param node_number: Node number within the substation.
    :param electrical_bus_number: Derived PSSE electrical bus number.
    :param version: Target PSSE RAW version.
    :return: RAW node record.
    """
    version = _normalize_psse_version(version=version)
    if version <= 34:
        psse_node: RawNodeLike = RawNodeV34()
    elif version == 35:
        psse_node = RawNodeV35()
    else:
        psse_node = RawNodeV36()
    psse_node.NI = node_number
    psse_node.NAME = str(bus.name)
    psse_node.I = electrical_bus_number
    psse_node.STATUS = 1 if bus.get_active_at(t=t_idx) else 0
    psse_node.VM = float(bus.Vm0)
    psse_node.VA = float(np.rad2deg(bus.Va0))
    return psse_node


def get_psse_substation_switch(switch: dev.Switch,
                               node_breaker_data: RawNodeBreakerExportData,
                               ckt: int,
                               version: int,
                               t_idx: int | None = None) -> RawSubstationSwitchingDeviceLike:
    """
    Convert an internal VeraGrid switch into a PSSE substation switching device.

    :param switch: VeraGrid switch.
    :param node_breaker_data: Node-breaker export context.
    :param ckt: Switch identifier.
    :param version: PSSE RAW version.
    :return: RAW substation switching device record.
    """
    version = _normalize_psse_version(version=version)
    if version <= 34:
        psse_switch: RawSubstationSwitchingDeviceLike = RawSubstationSwitchingDeviceV34()
    elif version == 35:
        psse_switch = RawSubstationSwitchingDeviceV35()
    else:
        psse_switch = RawSubstationSwitchingDeviceV36()

    substation: dev.Substation | None = None
    if switch.bus_from is not None and switch.bus_from.substation is not None:
        substation = switch.bus_from.substation
    elif switch.bus_to is not None and switch.bus_to.substation is not None:
        substation = switch.bus_to.substation
    else:
        pass

    substation_number: int = 0
    if substation is not None:
        registered_substation_number = node_breaker_data.substation_number_by_substation.get(substation, None)
        if registered_substation_number is not None:
            substation_number = registered_substation_number
        else:
            pass
    else:
        pass

    from_node_number: int = 0
    if switch.bus_from is not None:
        registered_from_node_number = node_breaker_data.node_number_by_bus.get(switch.bus_from, None)
        if registered_from_node_number is not None:
            from_node_number = registered_from_node_number
        else:
            pass
    else:
        pass

    to_node_number: int = 0
    if switch.bus_to is not None:
        registered_to_node_number = node_breaker_data.node_number_by_bus.get(switch.bus_to, None)
        if registered_to_node_number is not None:
            to_node_number = registered_to_node_number
        else:
            pass
    else:
        pass

    psse_switch.ISUB = substation_number
    psse_switch.NI = from_node_number
    psse_switch.NJ = to_node_number
    psse_switch.NAME = str(switch.name)
    psse_switch.TYPE = 3 if switch.graphic_type == SwitchGraphicType.Disconnector else 2
    psse_switch.STATUS = 1 if switch.get_active_at(t=t_idx) else 0
    psse_switch.NSTAT = 0 if switch.normal_open else 1
    psse_switch.X = float(switch.X)
    if version == 34:
        psse_switch.CKTID = str(ckt)
        psse_switch.RATE1 = float(switch.get_rate_at(t=t_idx))
        psse_switch.RATE2 = float(switch.get_rate_at(t=t_idx) * switch.get_contingency_factor_at(t=t_idx))
        psse_switch.RATE3 = float(switch.get_rate_at(t=t_idx) * switch.get_protection_rating_factor_at(t=t_idx))
    elif version == 35:
        psse_switch.CKT = str(ckt)
        psse_switch.RATE1 = float(switch.get_rate_at(t=t_idx))
        psse_switch.RATE2 = float(switch.get_rate_at(t=t_idx) * switch.get_contingency_factor_at(t=t_idx))
        psse_switch.RATE3 = float(switch.get_rate_at(t=t_idx) * switch.get_protection_rating_factor_at(t=t_idx))
    else:
        psse_switch.CKT = str(ckt)
        psse_switch.RSETNAM = ""

    return psse_switch


def append_psse_terminal(node_breaker_data: RawNodeBreakerExportData,
                         bus: dev.Bus,
                         type_code: str,
                         eqid: int | str,
                         version: int,
                         ibus: int,
                         jbus: int = 0,
                         kbus: int = 0,
                         t_idx: int | None = None) -> None:
    """
    Append one PSSE equipment terminal when the endpoint bus is exported as a node.

    :param node_breaker_data: Node-breaker export context.
    :param bus: VeraGrid bus that owns the node.
    :param type_code: PSSE terminal type code.
    :param eqid: Equipment identifier.
    :param version: Target PSSE RAW version.
    :param ibus: Electrical bus number of the local terminal side.
    :param jbus: Secondary bus number.
    :param kbus: Tertiary bus number.
    :return: None
    """
    if bus not in node_breaker_data.node_number_by_bus:
        return
    else:
        pass

    version = _normalize_psse_version(version=version)
    if version <= 34:
        terminal: RawEquipmentTerminalLike = RawEquipmentTerminalV34()
    elif version == 35:
        terminal = RawEquipmentTerminalV35()
    else:
        terminal = RawEquipmentTerminalV36()

    substation_number: int = 0
    if bus.substation is not None:
        registered_substation_number = node_breaker_data.substation_number_by_substation.get(bus.substation, None)
        if registered_substation_number is not None:
            substation_number = registered_substation_number
        else:
            pass
    else:
        pass

    terminal.ISUB = substation_number
    terminal.IBUS = ibus
    terminal.NI = node_breaker_data.node_number_by_bus[bus]
    terminal.TYPE = type_code
    terminal.JBUS = jbus
    terminal.KBUS = kbus
    terminal.EQID = str(eqid)
    node_breaker_data.equipment_terminals.append(terminal)


def get_area(area: dev.Area, i: int, version: int) -> RawAreaLike:
    """

    :param area:
    :param i:
    :param version:
    :return:
    """
    version = _normalize_psse_version(version=version)
    if version == 29:
        result: RawAreaLike = RawAreaV29()
    elif version == 30:
        result = RawAreaV30()
    elif version == 31:
        result = RawAreaV31()
    elif version == 32:
        result = RawAreaV32()
    elif version == 33:
        result = RawAreaV33()
    elif version == 34:
        result = RawAreaV34()
    elif version == 35:
        result = RawAreaV35()
    else:
        result = RawAreaV36()
    result.ARNAME = area.name
    result.I = i
    return result


def get_zone(zone: dev.Zone, i: int, version: int) -> RawZoneLike:
    """

    :param zone:
    :param i:
    :param version:
    :return:
    """
    version = _normalize_psse_version(version=version)
    if version == 29:
        result: RawZoneLike = RawZoneV29()
    elif version == 30:
        result = RawZoneV30()
    elif version == 31:
        result = RawZoneV31()
    elif version == 32:
        result = RawZoneV32()
    elif version == 33:
        result = RawZoneV33()
    elif version == 34:
        result = RawZoneV34()
    elif version == 35:
        result = RawZoneV35()
    else:
        result = RawZoneV36()
    result.ZONAME = zone.name
    result.I = i
    return result


def get_psse_bus(bus: dev.Bus,
                 area_dict: Dict[dev.Area, int],
                 zones_dict: Dict[dev.Zone, int],
                 suggested_psse_number: int,
                 version: int,
                 t_idx: int | None = None) -> RawBusLike:
    """

    :param bus:
    :param area_dict: 
    :param zones_dict:
    :param suggested_psse_number:
    :param version:
    :return:
    """
    version = _normalize_psse_version(version=version)
    if version == 29:
        psse_bus: RawBusLike = RawBusV29()
    elif version == 30:
        psse_bus = RawBusV30()
    elif version == 31:
        psse_bus = RawBusV31()
    elif version == 32:
        psse_bus = RawBusV32()
    elif version == 33:
        psse_bus = RawBusV33()
    elif version == 34:
        psse_bus = RawBusV34()
    elif version == 35:
        psse_bus = RawBusV35()
    else:
        psse_bus = RawBusV36()
    psse_bus.NAME = str(bus.name)
    psse_bus.BASKV = bus.Vnom

    psse_bus.I = suggested_psse_number

    psse_bus.EVLO = bus.get_Vmin_at(t=t_idx)
    psse_bus.EVHI = bus.get_Vmax_at(t=t_idx)

    psse_bus.AREA = area_dict.get(bus.area, 0)
    psse_bus.ZONE = zones_dict.get(bus.zone, 0)
    psse_bus.VM = bus.Vm0
    psse_bus.VA = np.rad2deg(bus.Va0)

    psse_bus.IDE = bus._bus_type.value

    return psse_bus


def get_psse_load(load: dev.Load,
                  bus_dict: Dict[dev.Bus, int],
                  id_number: int,
                  version: int,
                  t_idx: int | None = None) -> RawLoadLike:
    """

    :param load:
    :param bus_dict:
    :param id_number:
    :return:
    """
    version = _normalize_psse_version(version=version)
    if version == 29:
        psse_load: RawLoadLike = RawLoadV29()
    elif version == 30:
        psse_load = RawLoadV30()
    elif version == 31:
        psse_load = RawLoadV31()
    elif version == 32:
        psse_load = RawLoadV32()
    elif version == 33:
        psse_load = RawLoadV33()
    elif version == 34:
        psse_load = RawLoadV34()
    elif version == 35:
        psse_load = RawLoadV35()
    else:
        psse_load = RawLoadV36()

    psse_load.I = bus_dict[load.bus]
    psse_load.ID = id_number

    psse_load.YP = load.get_G_at(t=t_idx)
    psse_load.YQ = load.get_B_at(t=t_idx)
    psse_load.IP = load.get_Ir_at(t=t_idx)
    psse_load.IQ = -load.get_Ii_at(t=t_idx)
    psse_load.PL = load.get_P_at(t=t_idx)
    psse_load.QL = load.get_Q_at(t=t_idx)
    psse_load.STATUS = 1 if load.get_active_at(t=t_idx) else 0
    psse_load.SCALE = 1.0 if load.scalable else 0.0
    if version >= 36:
        _set_if_registered(psse_load, "NAME", str(load.name))

    return psse_load


def get_psse_load_from_external_grid(load: dev.ExternalGrid,
                                     bus_dict: Dict[dev.Bus, int],
                                     id_number: int,
                                     version: int,
                                     t_idx: int | None = None) -> RawLoadLike:
    """

    :param load:
    :param bus_dict:
    :param id_number:
    :return:
    """
    version = _normalize_psse_version(version=version)
    if version == 29:
        psse_load: RawLoadLike = RawLoadV29()
    elif version == 30:
        psse_load = RawLoadV30()
    elif version == 31:
        psse_load = RawLoadV31()
    elif version == 32:
        psse_load = RawLoadV32()
    elif version == 33:
        psse_load = RawLoadV33()
    elif version == 34:
        psse_load = RawLoadV34()
    elif version == 35:
        psse_load = RawLoadV35()
    else:
        psse_load = RawLoadV36()

    psse_load.I = bus_dict[load.bus]
    psse_load.ID = id_number

    psse_load.PL = load.get_P_at(t=t_idx)
    psse_load.QL = load.get_Q_at(t=t_idx)
    psse_load.STATUS = 1 if load.get_active_at(t=t_idx) else 0
    if version >= 36:
        _set_if_registered(psse_load, "NAME", str(load.name))

    return psse_load


def get_psse_fixed_shunt(shunt: dev.Shunt,
                         bus_dict: Dict[dev.Bus, int],
                         id_number: int,
                         version: int,
                         t_idx: int | None = None) -> RawFixedShuntLike:
    """

    :param shunt:
    :param bus_dict:
    :param id_number:
    :return:
    """
    version = _normalize_psse_version(version=version)
    if version == 29:
        psse_shunt: RawFixedShuntLike = RawFixedShuntV29()
    elif version == 30:
        psse_shunt = RawFixedShuntV30()
    elif version == 31:
        psse_shunt = RawFixedShuntV31()
    elif version == 32:
        psse_shunt = RawFixedShuntV32()
    elif version == 33:
        psse_shunt = RawFixedShuntV33()
    elif version == 34:
        psse_shunt = RawFixedShuntV34()
    elif version == 35:
        psse_shunt = RawFixedShuntV35()
    else:
        psse_shunt = RawFixedShuntV36()

    psse_shunt.I = bus_dict[shunt.bus]
    psse_shunt.ID = id_number

    psse_shunt.GL = shunt.get_G_at(t=t_idx)
    psse_shunt.BL = shunt.get_B_at(t=t_idx)

    psse_shunt.STATUS = 1 if shunt.get_active_at(t=t_idx) else 0
    if version >= 36:
        _set_if_registered(psse_shunt, "NAME", str(shunt.name))

    return psse_shunt


def get_psse_switched_shunt(shunt: dev.ControllableShunt,
                            bus_dict: Dict[dev.Bus, int],
                            version: int,
                            t_idx: int | None = None) -> RawSwitchedShuntLike:
    """

    :param shunt:
    :param bus_dict:
    :return:
    """
    version = _normalize_psse_version(version=version)
    if version == 29:
        psse_switched_shunt: RawSwitchedShuntLike = RawSwitchedShuntV29()
    elif version == 30:
        psse_switched_shunt = RawSwitchedShuntV30()
    elif version == 31:
        psse_switched_shunt = RawSwitchedShuntV31()
    elif version == 32:
        psse_switched_shunt = RawSwitchedShuntV32()
    elif version == 33:
        psse_switched_shunt = RawSwitchedShuntV33()
    elif version == 34:
        psse_switched_shunt = RawSwitchedShuntV34()
    elif version == 35:
        psse_switched_shunt = RawSwitchedShuntV35()
    else:
        psse_switched_shunt = RawSwitchedShuntV36()

    psse_switched_shunt.I = bus_dict[shunt.bus]

    psse_switched_shunt.BINIT = shunt.get_B_at(t=t_idx)
    psse_switched_shunt.STAT = int(shunt.get_active_at(t=t_idx))
    if version >= 36:
        _set_if_registered(psse_switched_shunt, "NAME", str(shunt.name))

    if shunt.control_bus is not None and shunt.control_bus != shunt.bus:
        psse_switched_shunt.SWREG = bus_dict.get(shunt.control_bus, 0)

    if len(shunt.b_steps) > 0:
        diff_list = np.insert(np.diff(shunt.b_steps), 0, shunt.b_steps[0])
        aggregated_steps = [(sum(1 for _ in group), key) for key, group in groupby(diff_list)]

        for index, aggregated_step in enumerate(aggregated_steps):
            if index < 8:
                psse_switched_shunt.set_block(index + 1, 1, aggregated_step[0], aggregated_step[1])

    return psse_switched_shunt


def get_psse_generator(generator: dev.Generator,
                       bus_dict: Dict[dev.Bus, int],
                       id_number: int,
                       version: int,
                       t_idx: int | None = None) -> RawGeneratorLike:
    """

    :param generator:
    :param bus_dict:
    :param id_number:
    :return:
    """
    version = _normalize_psse_version(version=version)
    if version == 29:
        psse_generator: RawGeneratorLike = RawGeneratorV29()
    elif version == 30:
        psse_generator = RawGeneratorV30()
    elif version == 31:
        psse_generator = RawGeneratorV31()
    elif version == 32:
        psse_generator = RawGeneratorV32()
    elif version == 33:
        psse_generator = RawGeneratorV33()
    elif version == 34:
        psse_generator = RawGeneratorV34()
    elif version == 35:
        psse_generator = RawGeneratorV35()
    else:
        psse_generator = RawGeneratorV36()

    psse_generator.I = bus_dict[generator.bus]
    psse_generator.ID = id_number

    if generator.control_bus is not None and generator.control_bus != generator.bus:
        psse_generator.IREG = bus_dict.get(generator.control_bus, 0)

    psse_generator.PG = generator.get_P_at(t=t_idx)
    psse_generator.VS = generator.get_Vset_at(t=t_idx)
    psse_generator.QB = generator.get_Qmin_at(t=t_idx)
    psse_generator.QT = generator.get_Qmax_at(t=t_idx)
    psse_generator.MBASE = generator.Snom
    psse_generator.PT = generator.get_Pmax_at(t=t_idx)
    psse_generator.PB = generator.get_Pmin_at(t=t_idx)
    psse_generator.STAT = 1 if generator.get_active_at(t=t_idx) else 0
    psse_generator.WPF = generator.get_Pf_at(t=t_idx)
    psse_generator.QG = generator.get_Q_at(t=t_idx)
    if version >= 36:
        _set_if_registered(psse_generator, "DROOPNAME", "")
        _set_if_registered(psse_generator, "NAME", str(generator.name))

    return psse_generator


def get_psse_transformer2w(transformer: dev.Transformer2W,
                           bus_dict: Dict[dev.Bus, int],
                           ckt: int,
                           version: int,
                           t_idx: int | None = None) -> RawTransformerLike:
    """

    :param transformer:
    :param bus_dict:
    :param ckt:
    :return:
    """
    version = _normalize_psse_version(version=version)
    if version == 29:
        psse_transformer: RawTransformerLike = RawTransformerV29()
    elif version == 30:
        psse_transformer = RawTransformerV30()
    elif version == 31:
        psse_transformer = RawTransformerV31()
    elif version == 32:
        psse_transformer = RawTransformerV32()
    elif version == 33:
        psse_transformer = RawTransformerV33()
    elif version == 34:
        psse_transformer = RawTransformerV34()
    elif version == 35:
        psse_transformer = RawTransformerV35()
    else:
        psse_transformer = RawTransformerV36()
    psse_transformer.windings = 2

    psse_transformer.idtag = transformer.idtag
    psse_transformer.STAT = 1 if transformer.get_active_at(t=t_idx) else 0

    psse_transformer.SBASE1_2 = transformer.Sn
    _set_transformer_winding_ratings(psse_transformer, version, 1,
                                     transformer.get_rate_at(t=t_idx),
                                     transformer.get_contingency_factor_at(t=t_idx),
                                     transformer.get_protection_rating_factor_at(t=t_idx))

    # i, j, ckt = transformer.code.split("_", 2)
    psse_transformer.I = bus_dict[transformer.bus_from]
    psse_transformer.J = bus_dict[transformer.bus_to]
    psse_transformer.CKT = ckt

    psse_transformer.CW = 1
    # WINDV1 is the Winding 1 off-nominal turns ratio in pu of Winding1 bus base voltage
    mf, mt = transformer.get_virtual_taps()
    psse_transformer.WINDV1 = transformer.get_tap_module_at(t=t_idx) * mf / mt
    psse_transformer.WINDV2 = 1.0

    V1, V2, _ = transformer.get_from_to_nominal_voltages()
    psse_transformer.NOMV1 = V1
    psse_transformer.NOMV2 = V2 if V2 != V1 else 0.0

    psse_transformer.CZ = 1
    # 1 for resistance and reactance in pu on system MVA base and winding voltage base
    # translating: impedances in the system base, do noting
    psse_transformer.R1_2 = transformer.R
    psse_transformer.X1_2 = transformer.X

    psse_transformer.CM = 1
    # 1 for complex  admittance  in pu  on  system  MVA  base  and Winding 1 bus voltage base
    psse_transformer.MAG1 = transformer.G
    psse_transformer.MAG2 = transformer.B

    # tap changer values
    psse_transformer.NTP1 = transformer.tap_changer.total_positions
    psse_transformer.VMA1 = transformer.tap_changer.get_tap_module_max()
    psse_transformer.VMI1 = transformer.tap_changer.get_tap_module_min()

    psse_transformer.ANG1 = np.rad2deg(transformer.get_tap_phase_at(t=t_idx))

    # Control types
    tap_changer_type = transformer.tap_changer.tc_type
    tap_module_control_mode = transformer.get_tap_module_control_mode_at(t=t_idx)
    tap_phase_control_mode = transformer.get_tap_phase_control_mode_at(t=t_idx)

    if tap_changer_type == TapChangerTypes.NoRegulation:

        psse_transformer.COD1 = 0

    elif tap_changer_type == TapChangerTypes.VoltageRegulation:

        if tap_module_control_mode == TapModuleControl.fixed:
            psse_transformer.COD1 = -1
        else:
            psse_transformer.COD1 = 1

    elif tap_changer_type == TapChangerTypes.Symmetrical:

        if tap_phase_control_mode == TapPhaseControl.fixed:
            psse_transformer.COD1 = -3
        else:
            psse_transformer.COD1 = 3

        # RMA - Phase shift angle in degrees when |COD1| is 3 or 5. No default is allowed
        number_of_symmetrical_step = (transformer.tap_changer.total_positions - 1) / 2
        psse_transformer.RMA1 = 2 * math.degrees(math.atan(
             number_of_symmetrical_step * transformer.tap_changer.dV / 2
        ))

    elif tap_changer_type == TapChangerTypes.Asymmetrical:

        if (tap_module_control_mode == TapModuleControl.fixed or
                tap_phase_control_mode == TapPhaseControl.fixed):
            psse_transformer.COD1 = -5
        else:
            psse_transformer.COD1 = 5
        psse_transformer.CNXA1 = transformer.tap_changer.asymmetry_angle

    else:
        pass

    return psse_transformer


def get_psse_transformer3w(transformer: dev.Transformer3W,
                           bus_dict: Dict[dev.Bus, int],
                           version: int,
                           t_idx: int | None = None) -> RawTransformerLike:
    """

    :param transformer:
    :param bus_dict:
    :return:
    """
    version = _normalize_psse_version(version=version)
    if version == 29:
        psse_transformer: RawTransformerLike = RawTransformerV29()
    elif version == 30:
        psse_transformer = RawTransformerV30()
    elif version == 31:
        psse_transformer = RawTransformerV31()
    elif version == 32:
        psse_transformer = RawTransformerV32()
    elif version == 33:
        psse_transformer = RawTransformerV33()
    elif version == 34:
        psse_transformer = RawTransformerV34()
    elif version == 35:
        psse_transformer = RawTransformerV35()
    else:
        psse_transformer = RawTransformerV36()
    psse_transformer.windings = 3

    psse_transformer.NOMV1 = transformer.V1
    psse_transformer.NOMV2 = transformer.V2
    psse_transformer.NOMV3 = transformer.V3

    psse_transformer.idtag = transformer.idtag
    psse_transformer.STAT = 1 if transformer.get_active_at(t=t_idx) else 0

    psse_transformer.NAME = transformer.name
    _set_transformer_winding_ratings(psse_transformer, version, 1,
                                     transformer.rate1,
                                     transformer.winding1.contingency_factor,
                                     transformer.winding1.protection_rating_factor)
    _set_transformer_winding_ratings(psse_transformer, version, 2,
                                     transformer.rate2,
                                     transformer.winding2.contingency_factor,
                                     transformer.winding2.protection_rating_factor)
    _set_transformer_winding_ratings(psse_transformer, version, 3,
                                     transformer.rate3,
                                     transformer.winding3.contingency_factor,
                                     transformer.winding3.protection_rating_factor)

    # The winding tap is stored on the winding-bus (bus_from) side, matching PSSe's
    # winding-bus-side WINDVn / ANGn, so write the values directly (see raw_to_veragrid).
    psse_transformer.CW = 1
    psse_transformer.WINDV1 = transformer.winding1.tap_module
    psse_transformer.WINDV2 = transformer.winding2.tap_module
    psse_transformer.WINDV3 = transformer.winding3.tap_module

    psse_transformer.ANG1 = np.rad2deg(transformer.winding1.tap_phase)
    psse_transformer.ANG2 = np.rad2deg(transformer.winding2.tap_phase)
    psse_transformer.ANG3 = np.rad2deg(transformer.winding3.tap_phase)

    # Winding tap regulation (mirror of the winding_controls parsing in raw_to_veragrid).
    # Without writing these fields the COD/CONT/RMA/RMI/VMA/VMI/NTP default to "no control",
    # so the regulation parsed from the input RAW is lost on round-trip and the regulated bus
    # loses its voltage lock (shifting its initial voltage).
    winding1 = transformer.winding1
    if winding1.tap_module_control_mode == TapModuleControl.Vm and winding1.regulation_bus is not None:
        psse_transformer.COD1 = 1
        psse_transformer.CONT1 = bus_dict.get(winding1.regulation_bus, 0)
        psse_transformer.RMA1 = winding1.tap_module_max
        psse_transformer.RMI1 = winding1.tap_module_min
        # the controlled-voltage band collapses to its midpoint (vset) on read, so write
        # vset on both ends to reproduce it exactly.
        psse_transformer.VMA1 = winding1.vset
        psse_transformer.VMI1 = winding1.vset
        psse_transformer.NTP1 = int(winding1.tap_changer.total_positions)
    else:
        psse_transformer.COD1 = 0

    winding2 = transformer.winding2
    if winding2.tap_module_control_mode == TapModuleControl.Vm and winding2.regulation_bus is not None:
        psse_transformer.COD2 = 1
        psse_transformer.CONT2 = bus_dict.get(winding2.regulation_bus, 0)
        psse_transformer.RMA2 = winding2.tap_module_max
        psse_transformer.RMI2 = winding2.tap_module_min
        # the controlled-voltage band collapses to its midpoint (vset) on read, so write
        # vset on both ends to reproduce it exactly.
        psse_transformer.VMA2 = winding2.vset
        psse_transformer.VMI2 = winding2.vset
        psse_transformer.NTP2 = int(winding2.tap_changer.total_positions)
    else:
        psse_transformer.COD2 = 0

    winding3 = transformer.winding3
    if winding3.tap_module_control_mode == TapModuleControl.Vm and winding3.regulation_bus is not None:
        psse_transformer.COD3 = 1
        psse_transformer.CONT3 = bus_dict.get(winding3.regulation_bus, 0)
        psse_transformer.RMA3 = winding3.tap_module_max
        psse_transformer.RMI3 = winding3.tap_module_min
        # the controlled-voltage band collapses to its midpoint (vset) on read, so write
        # vset on both ends to reproduce it exactly.
        psse_transformer.VMA3 = winding3.vset
        psse_transformer.VMI3 = winding3.vset
        psse_transformer.NTP3 = int(winding3.tap_changer.total_positions)
    else:
        psse_transformer.COD3 = 0

    i, j, k, ckt = transformer.code.split("_", 3)

    psse_transformer.I = bus_dict[transformer.bus1]
    psse_transformer.J = bus_dict[transformer.bus2]
    psse_transformer.K = bus_dict[transformer.bus3]
    psse_transformer.CKT = ckt

    psse_transformer.R1_2 = transformer.r12
    psse_transformer.X1_2 = transformer.x12
    psse_transformer.R2_3 = transformer.r23
    psse_transformer.X2_3 = transformer.x23
    psse_transformer.R3_1 = transformer.r31
    psse_transformer.X3_1 = transformer.x31
    psse_transformer.VMSTAR = transformer.bus0.Vm0
    psse_transformer.ANSTAR = np.rad2deg(transformer.bus0.Va0)

    return psse_transformer


def get_psse_branch(branch: dev.Line,
                    bus_dict: Dict[dev.Bus, int],
                    ckt: int,
                    version: int,
                    t_idx: int | None = None) -> RawBranchLike:
    """

    :param branch:
    :param bus_dict:
    :param ckt:
    :return:
    """
    version = _normalize_psse_version(version=version)
    if version == 29:
        psse_branch: RawBranchLike = RawBranchV29()
    elif version == 30:
        psse_branch = RawBranchV30()
    elif version == 31:
        psse_branch = RawBranchV31()
    elif version == 32:
        psse_branch = RawBranchV32()
    elif version == 33:
        psse_branch = RawBranchV33()
    elif version == 34:
        psse_branch = RawBranchV34()
    elif version == 35:
        psse_branch = RawBranchV35()
    else:
        psse_branch = RawBranchV36()

    # i, j, ckt = line.code.split("_", 2)

    psse_branch.I = bus_dict[branch.bus_from]
    psse_branch.J = bus_dict[branch.bus_to]

    psse_branch.CKT = ckt

    psse_branch.NAME = branch.name
    psse_branch.R = branch.R
    psse_branch.X = branch.X
    psse_branch.B = branch.B
    psse_branch.ST = 1 if branch.get_active_at(t=t_idx) else 0
    psse_branch.idtag = branch.idtag
    psse_branch.LEN = branch.length
    _set_branch_ratings(psse_branch, version,
                        branch.get_rate_at(t=t_idx),
                        branch.get_contingency_factor_at(t=t_idx),
                        branch.get_protection_rating_factor_at(t=t_idx))

    return psse_branch


def get_vsc_dc_line(hvdc_line: dev.HvdcLine,
                    bus_dict: Dict[dev.Bus, int],
                    version: int,
                    t_idx: int | None = None) -> RawVscDCLineLike:
    """

    :param hvdc_line:
    :param bus_dict:
    :return:
    """
    version = _normalize_psse_version(version=version)
    if version == 29:
        psse_vsc_dc_line: RawVscDCLineLike = RawVscDCLineV29()
    elif version == 30:
        psse_vsc_dc_line = RawVscDCLineV30()
    elif version == 31:
        psse_vsc_dc_line = RawVscDCLineV31()
    elif version == 32:
        psse_vsc_dc_line = RawVscDCLineV32()
    elif version == 33:
        psse_vsc_dc_line = RawVscDCLineV33()
    elif version == 34:
        psse_vsc_dc_line = RawVscDCLineV34()
    elif version == 35:
        psse_vsc_dc_line = RawVscDCLineV35()
    else:
        psse_vsc_dc_line = RawVscDCLineV36()
    psse_vsc_dc_line.NAME = hvdc_line.name
    psse_vsc_dc_line.MDC = 1
    psse_vsc_dc_line.IBUS1 = bus_dict[hvdc_line.bus_from]
    psse_vsc_dc_line.IBUS2 = bus_dict[hvdc_line.bus_to]
    psse_vsc_dc_line.TYPE1 = 1
    psse_vsc_dc_line.TYPE2 = 2
    psse_vsc_dc_line.MODE1 = 1
    psse_vsc_dc_line.MODE2 = 1
    psse_vsc_dc_line.ACSET1 = hvdc_line.get_Vset_f_at(t=t_idx)
    psse_vsc_dc_line.ACSET2 = hvdc_line.get_Vset_t_at(t=t_idx)
    psse_vsc_dc_line.DCSET1 = hvdc_line.get_Pset_at(t=t_idx)
    psse_vsc_dc_line.DCSET2 = -hvdc_line.get_Pset_at(t=t_idx)
    psse_vsc_dc_line.SMAX1 = hvdc_line.get_rate_at(t=t_idx)
    psse_vsc_dc_line.SMAX2 = hvdc_line.get_rate_at(t=t_idx)
    if version >= 35:
        psse_vsc_dc_line.VSREG1 = psse_vsc_dc_line.IBUS1
        psse_vsc_dc_line.VSREG2 = psse_vsc_dc_line.IBUS2
    else:
        _set_if_registered(psse_vsc_dc_line, "REMOT1", psse_vsc_dc_line.IBUS1)
        _set_if_registered(psse_vsc_dc_line, "REMOT2", psse_vsc_dc_line.IBUS2)
    psse_vsc_dc_line.RMPCT1 = 100.0
    psse_vsc_dc_line.RMPCT2 = 100.0

    V1 = hvdc_line.bus_from.Vnom * psse_vsc_dc_line.ACSET1
    V2 = hvdc_line.bus_to.Vnom * psse_vsc_dc_line.ACSET2
    dV = (V1 - V2) * 1000.0
    P = hvdc_line.Pset / 1e-6
    psse_vsc_dc_line.RDC = dV * dV / P if P != 0 else 0

    return psse_vsc_dc_line


def get_psse_two_terminal_dc_line(hvdc_line: dev.HvdcLine,
                                  bus_dict: Dict[dev.Bus, int],
                                  version: int,
                                  t_idx: int | None = None) -> RawTwoTerminalDCLineLike:
    """

    :param hvdc_line:
    :param bus_dict:
    :return:
    """
    version = _normalize_psse_version(version=version)
    if version == 29:
        psse_two_terminal_dc_line: RawTwoTerminalDCLineLike = RawTwoTerminalDCLineV29()
    elif version == 30:
        psse_two_terminal_dc_line = RawTwoTerminalDCLineV30()
    elif version == 31:
        psse_two_terminal_dc_line = RawTwoTerminalDCLineV31()
    elif version == 32:
        psse_two_terminal_dc_line = RawTwoTerminalDCLineV32()
    elif version == 33:
        psse_two_terminal_dc_line = RawTwoTerminalDCLineV33()
    elif version == 34:
        psse_two_terminal_dc_line = RawTwoTerminalDCLineV34()
    elif version == 35:
        psse_two_terminal_dc_line = RawTwoTerminalDCLineV35()
    else:
        psse_two_terminal_dc_line = RawTwoTerminalDCLineV36()
    psse_two_terminal_dc_line.NAME = hvdc_line.name

    psse_two_terminal_dc_line.IPR = bus_dict[hvdc_line.bus_from]
    psse_two_terminal_dc_line.IPI = bus_dict[hvdc_line.bus_to]

    psse_two_terminal_dc_line.RDC = hvdc_line.r
    psse_two_terminal_dc_line.ANMNR = np.rad2deg(hvdc_line.min_firing_angle_f)
    psse_two_terminal_dc_line.ANMXR = np.rad2deg(hvdc_line.max_firing_angle_f)
    psse_two_terminal_dc_line.ANMNI = np.rad2deg(hvdc_line.min_firing_angle_t)
    psse_two_terminal_dc_line.ANMXI = np.rad2deg(hvdc_line.max_firing_angle_t)

    return psse_two_terminal_dc_line


def get_psse_facts(upfc: dev.UPFC,
                   bus_dict: Dict[dev.Bus, int],
                   version: int,
                   t_idx: int | None = None) -> RawFACTSLike:
    """

    :param upfc:
    :param bus_dict:
    :return:
    """
    version = _normalize_psse_version(version=version)
    if version == 29:
        psse_facts: RawFACTSLike = RawFACTSV29()
    elif version == 30:
        psse_facts = RawFACTSV30()
    elif version == 31:
        psse_facts = RawFACTSV31()
    elif version == 32:
        psse_facts = RawFACTSV32()
    elif version == 33:
        psse_facts = RawFACTSV33()
    elif version == 34:
        psse_facts = RawFACTSV34()
    elif version == 35:
        psse_facts = RawFACTSV35()
    else:
        psse_facts = RawFACTSV36()
    psse_facts.NAME = upfc.name

    id_tag = upfc.idtag[:-2] if upfc.idtag.endswith("_1") else upfc.idtag
    # i, j = id_tag.split("_", 2)

    psse_facts.I = bus_dict[upfc.bus_from]
    psse_facts.J = bus_dict[upfc.bus_to]
    psse_facts.SET1 = upfc.R
    psse_facts.SHMX = 1 / upfc.Xsh if upfc.Xsh > 0 else 0.0
    psse_facts.VSET = upfc.Vsh
    psse_facts.PDES = upfc.Pfset
    psse_facts.QDES = upfc.Qfset
    psse_facts.IMX = upfc.get_rate_at(t=t_idx) - 1e-20
    if version <= 34:
        _set_if_registered(psse_facts, "REMOT", psse_facts.I)
    else:
        _set_if_registered(psse_facts, "FCREG", psse_facts.I)
        _set_if_registered(psse_facts, "NREG", 0)

    return psse_facts


def get_psse_switch(switch: dev.Switch,
                    bus_dict: Dict[dev.Bus, int],
                    ckt: int,
                    version: int,
                    t_idx: int | None = None) -> RawSystemSwitchingDeviceLike:
    """
    Convert VeraGrid Switch to PSSE system switching device.
    """
    version = _normalize_psse_version(version=version)
    if version == 29:
        psse_switch: RawSystemSwitchingDeviceLike = RawSystemSwitchingDeviceV29()
    elif version == 30:
        psse_switch = RawSystemSwitchingDeviceV30()
    elif version == 31:
        psse_switch = RawSystemSwitchingDeviceV31()
    elif version == 32:
        psse_switch = RawSystemSwitchingDeviceV32()
    elif version == 33:
        psse_switch = RawSystemSwitchingDeviceV33()
    elif version == 34:
        psse_switch = RawSystemSwitchingDeviceV34()
    elif version == 35:
        psse_switch = RawSystemSwitchingDeviceV35()
    else:
        psse_switch = RawSystemSwitchingDeviceV36()

    psse_switch.I = bus_dict[switch.bus_from]
    psse_switch.J = bus_dict[switch.bus_to]
    psse_switch.CKT = str(ckt)
    psse_switch.X = switch.X
    if version <= 35:
        psse_switch.RATE1 = switch.get_rate_at(t=t_idx)
    psse_switch.STATUS = 1 if switch.get_active_at(t=t_idx) else 0
    psse_switch.NSTATUS = 0 if switch.normal_open else 1
    psse_switch.METERED = 1
    psse_switch.STYPE = 3 if switch.graphic_type == SwitchGraphicType.Disconnector else 2
    psse_switch.NAME = str(switch.name)
    if version >= 36:
        _set_if_registered(psse_switch, "RSETNAM", "")

    return psse_switch


class RawCounter:
    """
    Items to count stuff for the raw files
    """

    def __init__(self, grid: MultiCircuit):
        """
        Constructor
        :param grid: MultiCircuit
        """
        n = grid.get_bus_number()
        self._bus_int_dict = {bus: i + 1 for i, bus in enumerate(grid.get_buses())}
        self._bus_2_psseI_dict = dict()
        self._bus_dev_count_dict = {bus: 0 for bus in grid.get_buses()}
        self._ckt_counter = lil_matrix((n + 1, n + 1), dtype=int)
        self._used_psse_numbers: Dict[int, dev.Bus] = dict()

        self._max_bus_number = 1

    @property
    def psse_numbers_dict(self) -> Dict[dev.Bus, int]:
        """

        :return:
        """
        return self._bus_2_psseI_dict

    def register_psse_number(self, bus: dev.Bus, psse_I: int):
        """

        :param bus:
        :param psse_I:
        :return:
        """
        self._max_bus_number = max(self._max_bus_number, psse_I)
        self._bus_2_psseI_dict[bus] = psse_I
        if psse_I not in self._used_psse_numbers:
            self._used_psse_numbers[psse_I] = bus
        else:
            pass

    def get_next_psse_number(self):
        """

        :return:
        """
        return self._max_bus_number + 1

    def get_suggested_psse_number(self, bus: dev.Bus, logger: Logger) -> int:
        """

        :param bus:
        :param logger:
        :return:
        """
        try:
            psse_I = int(bus.code)

            if psse_I in self._used_psse_numbers:
                psse_I_pre = psse_I
                # repeated number, get a new one
                psse_I = self.get_next_psse_number()
                logger.add_error("Repeated PSSe number",
                                 device=bus.name,
                                 value=psse_I_pre,
                                 expected_value=psse_I)

        except ValueError:
            psse_I = self.get_next_psse_number()
            logger.add_warning("Invalid PSSe number stored in bus.code",
                               device=bus.name,
                               value=str(bus.code),
                               expected_value=psse_I)

        self.register_psse_number(bus, psse_I)

        return psse_I

    def get_id(self, bus: dev.Bus) -> int:
        """
        Query the dictionary for the internal number and increase that number for the next time
        :param bus: Bus
        :return: integer
        """
        id_number = self._bus_dev_count_dict[bus] + 1
        self._bus_dev_count_dict[bus] = id_number
        return id_number

    def get_ckt(self, branch: BRANCH_TYPES) -> int:
        """
        Count the circuit number in the PSSe sense
        :param branch: some branch
        :return: CKT
        """
        i = self._bus_int_dict[branch.bus_from]
        j = self._bus_int_dict[branch.bus_to]
        ckt = self._ckt_counter[i, j]
        ckt2 = ckt + 1
        self._ckt_counter[i, j] = ckt2
        self._ckt_counter[j, i] = ckt2
        return ckt2


def veragrid_to_raw(grid: MultiCircuit,
                    version: int,
                    logger: Logger,
                    topology_mode: PsseTopologyExportMode = PsseTopologyExportMode.BusBranch,
                    t_idx: int | None = None) -> PsseCircuit:
    """
    Convert a VeraGrid circuit into a PSSE RAW circuit.

    :param grid: VeraGrid circuit.
    :param version: Target PSSE RAW version.
    :param logger: Logger.
    :param topology_mode: Export topology strategy.
    :param t_idx: Snapshot selector. ``None`` exports snapshot values, otherwise exports the selected profile step.
    :return: PSSE RAW circuit.
    """
    version = _normalize_psse_version(version=version)

    node_breaker_requested: bool = topology_mode == PsseTopologyExportMode.NodeBreaker and version >= 34
    if topology_mode == PsseTopologyExportMode.NodeBreaker and version < 34:
        logger.add_info(msg="PSSE node-breaker export ignored because the target RAW version is below 34")
    else:
        pass

    psse_circuit = PsseCircuit()
    psse_circuit.REV = version

    area_dict: Dict[dev.Area, int] = dict()
    zones_dict: Dict[dev.Zone, int] = dict()
    counter = RawCounter(grid=grid)

    for i, area in enumerate(grid.areas):
        psse_circuit.areas.append(get_area(area=area, i=i + 1, version=version))
        area_dict[area] = i + 1

    for i, zone in enumerate(grid.zones):
        psse_circuit.zones.append(get_zone(zone=zone, i=i + 1, version=version))
        zones_dict[zone] = i + 1

    node_breaker_data: RawNodeBreakerExportData | None = None
    if node_breaker_requested:
        node_breaker_data = RawNodeBreakerExportData()
        export_substations = get_export_substations(grid=grid)

        for substation_index, substation in enumerate(export_substations):
            substation_number = substation_index + 1
            node_breaker_data.substation_number_by_substation[substation] = substation_number
            node_breaker_data.substations.append(
                get_psse_substation(substation=substation,
                                    psse_number=substation_number,
                                    version=version,
                                    t_idx=t_idx)
            )

            substation_buses = grid.get_substation_buses(substation=substation)
            for node_index, bus in enumerate(substation_buses):
                # Each VeraGrid bus that belongs to a substation becomes one PSS/E
                # node. We keep the electrical bus mapping one-to-one as well,
                # because this export mode is only about exposing node ownership.
                node_breaker_data.node_number_by_bus[bus] = node_index + 1
                psse_circuit.buses.append(
                    get_psse_bus(bus=bus,
                                 area_dict=area_dict,
                                 zones_dict=zones_dict,
                                 suggested_psse_number=counter.get_suggested_psse_number(bus=bus, logger=logger),
                                 version=version,
                                 t_idx=t_idx)
                )
                node_breaker_data.bus_number_by_bus[bus] = counter.psse_numbers_dict[bus]

            for bus in substation_buses:
                if bus in node_breaker_data.bus_number_by_bus:
                    raw_node = get_psse_node(bus=bus,
                                             node_number=node_breaker_data.node_number_by_bus[bus],
                                             electrical_bus_number=node_breaker_data.bus_number_by_bus[bus],
                                             version=version,
                                             t_idx=t_idx)
                    raw_node.ISUB = substation_number
                    node_breaker_data.nodes.append(raw_node)
                else:
                    logger.add_error(msg="Substation bus missing from node-breaker grouping",
                                     device=bus.name)
    else:
        pass

    for bus in grid.buses:
        if bus.internal:
            logger.add_info(msg="Internal bus skipped at RAW export", device=bus.name)
        elif node_breaker_requested and bus.substation is not None:
            pass
        else:
            psse_circuit.buses.append(
                get_psse_bus(bus=bus,
                             area_dict=area_dict,
                             zones_dict=zones_dict,
                             suggested_psse_number=counter.get_suggested_psse_number(bus=bus, logger=logger),
                             version=version,
                             t_idx=t_idx)
            )

    if node_breaker_requested and node_breaker_data is not None:
        psse_circuit.substations.extend(node_breaker_data.substations)
        psse_circuit.nodes.extend(node_breaker_data.nodes)
    else:
        pass

    for load in grid.loads:
        psse_load = get_psse_load(load=load,
                                  bus_dict=counter.psse_numbers_dict,
                                  id_number=counter.get_id(load.bus),
                                  version=version,
                                  t_idx=t_idx)
        psse_circuit.loads.append(psse_load)
        if node_breaker_requested and node_breaker_data is not None:
            append_psse_terminal(node_breaker_data=node_breaker_data,
                                 bus=load.bus,
                                 type_code='L',
                                 eqid=psse_load.ID,
                                 version=version,
                                 ibus=psse_load.I,
                                 t_idx=t_idx)
        else:
            pass

    for external_grid in grid.external_grids:
        psse_load = get_psse_load_from_external_grid(load=external_grid,
                                                     bus_dict=counter.psse_numbers_dict,
                                                     id_number=counter.get_id(external_grid.bus),
                                                     version=version,
                                                     t_idx=t_idx)
        psse_circuit.loads.append(psse_load)
        if node_breaker_requested and node_breaker_data is not None:
            append_psse_terminal(node_breaker_data=node_breaker_data,
                                 bus=external_grid.bus,
                                 type_code='L',
                                 eqid=psse_load.ID,
                                 version=version,
                                 ibus=psse_load.I,
                                 t_idx=t_idx)
        else:
            pass

    for generator in grid.generators:
        psse_generator = get_psse_generator(generator=generator,
                                            bus_dict=counter.psse_numbers_dict,
                                            id_number=counter.get_id(generator.bus),
                                            version=version,
                                            t_idx=t_idx)
        if node_breaker_requested and node_breaker_data is not None and version >= 35:
            if generator.control_bus is not None and generator.control_bus in node_breaker_data.node_number_by_bus:
                psse_generator.NREG = node_breaker_data.node_number_by_bus[generator.control_bus]
            else:
                pass
        else:
            pass

        psse_circuit.generators.append(psse_generator)
        if node_breaker_requested and node_breaker_data is not None:
            append_psse_terminal(node_breaker_data=node_breaker_data,
                                 bus=generator.bus,
                                 type_code='M',
                                 eqid=psse_generator.ID,
                                 version=version,
                                 ibus=psse_generator.I,
                                 t_idx=t_idx)
        else:
            pass

    for shunt in grid.shunts:
        psse_shunt = get_psse_fixed_shunt(shunt=shunt,
                                          bus_dict=counter.psse_numbers_dict,
                                          id_number=counter.get_id(shunt.bus),
                                          version=version,
                                          t_idx=t_idx)
        psse_circuit.fixed_shunts.append(psse_shunt)
        if node_breaker_requested and node_breaker_data is not None:
            append_psse_terminal(node_breaker_data=node_breaker_data,
                                 bus=shunt.bus,
                                 type_code='F',
                                 eqid=psse_shunt.ID,
                                 version=version,
                                 ibus=psse_shunt.I,
                                 t_idx=t_idx)
        else:
            pass

    for controllable_shunt in grid.controllable_shunts:
        psse_shunt = get_psse_switched_shunt(shunt=controllable_shunt,
                                             bus_dict=counter.psse_numbers_dict,
                                             version=version,
                                             t_idx=t_idx)
        if node_breaker_requested and node_breaker_data is not None and version >= 35:
            if controllable_shunt.control_bus is not None and controllable_shunt.control_bus in node_breaker_data.node_number_by_bus:
                psse_shunt.NREG = node_breaker_data.node_number_by_bus[controllable_shunt.control_bus]
            else:
                pass
        else:
            pass

        psse_circuit.switched_shunts.append(psse_shunt)
        if node_breaker_requested and node_breaker_data is not None:
            switched_shunt_eqid = psse_shunt.ID if version >= 35 else "1"
            append_psse_terminal(node_breaker_data=node_breaker_data,
                                 bus=controllable_shunt.bus,
                                 type_code='S',
                                 eqid=switched_shunt_eqid,
                                 version=version,
                                 ibus=psse_shunt.I,
                                 t_idx=t_idx)
        else:
            pass

    for line in grid.lines:
        raw_branch = get_psse_branch(branch=line,
                                     bus_dict=counter.psse_numbers_dict,
                                     ckt=counter.get_ckt(branch=line),
                                     version=version,
                                     t_idx=t_idx)
        psse_circuit.branches.append(raw_branch)
        if node_breaker_requested and node_breaker_data is not None:
            append_psse_terminal(node_breaker_data=node_breaker_data,
                                 bus=line.bus_from,
                                 type_code='B',
                                 eqid=raw_branch.CKT,
                                 version=version,
                                 ibus=raw_branch.I,
                                 jbus=raw_branch.J,
                                 t_idx=t_idx)
            append_psse_terminal(node_breaker_data=node_breaker_data,
                                 bus=line.bus_to,
                                 type_code='B',
                                 eqid=raw_branch.CKT,
                                 version=version,
                                 ibus=raw_branch.J,
                                 jbus=raw_branch.I,
                                 t_idx=t_idx)
        else:
            pass

    for switch in grid.get_switches():
        if (node_breaker_requested and node_breaker_data is not None and switch.bus_from is not None and
                switch.bus_to is not None and switch.bus_from.substation is not None and
                switch.bus_from.substation == switch.bus_to.substation):
            psse_circuit.substation_switching_devices.append(
                get_psse_substation_switch(switch=switch,
                                           node_breaker_data=node_breaker_data,
                                           ckt=counter.get_ckt(branch=switch),
                                           version=version,
                                           t_idx=t_idx)
            )
        else:
            psse_circuit.switches.append(get_psse_switch(switch=switch,
                                                         bus_dict=counter.psse_numbers_dict,
                                                         ckt=counter.get_ckt(branch=switch),
                                                         version=version,
                                                         t_idx=t_idx))

    for transformer in grid.transformers2w:
        psse_transformer = get_psse_transformer2w(transformer=transformer,
                                                  bus_dict=counter.psse_numbers_dict,
                                                  ckt=counter.get_ckt(branch=transformer),
                                                  version=version,
                                                  t_idx=t_idx)
        if node_breaker_requested and node_breaker_data is not None and version >= 35:
            if transformer.regulation_bus is not None and transformer.regulation_bus in node_breaker_data.node_number_by_bus:
                psse_transformer.CONT1 = counter.psse_numbers_dict[transformer.regulation_bus]
                psse_transformer.NODE1 = node_breaker_data.node_number_by_bus[transformer.regulation_bus]
            else:
                pass
        else:
            pass

        psse_circuit.transformers.append(psse_transformer)
        if node_breaker_requested and node_breaker_data is not None:
            append_psse_terminal(node_breaker_data=node_breaker_data,
                                 bus=transformer.bus_from,
                                 type_code='2',
                                 eqid=psse_transformer.CKT,
                                 version=version,
                                 ibus=psse_transformer.I,
                                 jbus=psse_transformer.J,
                                 t_idx=t_idx)
            append_psse_terminal(node_breaker_data=node_breaker_data,
                                 bus=transformer.bus_to,
                                 type_code='2',
                                 eqid=psse_transformer.CKT,
                                 version=version,
                                 ibus=psse_transformer.J,
                                 jbus=psse_transformer.I,
                                 t_idx=t_idx)
        else:
            pass

    for transformer in grid.transformers3w:
        psse_transformer = get_psse_transformer3w(transformer=transformer,
                                                  bus_dict=counter.psse_numbers_dict,
                                                  version=version,
                                                  t_idx=t_idx)
        psse_circuit.transformers.append(psse_transformer)
        if node_breaker_requested and node_breaker_data is not None:
            append_psse_terminal(node_breaker_data=node_breaker_data,
                                 bus=transformer.bus1,
                                 type_code='3',
                                 eqid=psse_transformer.CKT,
                                 version=version,
                                 ibus=psse_transformer.I,
                                 jbus=psse_transformer.J,
                                 kbus=psse_transformer.K,
                                 t_idx=t_idx)
            append_psse_terminal(node_breaker_data=node_breaker_data,
                                 bus=transformer.bus2,
                                 type_code='3',
                                 eqid=psse_transformer.CKT,
                                 version=version,
                                 ibus=psse_transformer.J,
                                 jbus=psse_transformer.I,
                                 kbus=psse_transformer.K,
                                 t_idx=t_idx)
            append_psse_terminal(node_breaker_data=node_breaker_data,
                                 bus=transformer.bus3,
                                 type_code='3',
                                 eqid=psse_transformer.CKT,
                                 version=version,
                                 ibus=psse_transformer.K,
                                 jbus=psse_transformer.I,
                                 kbus=psse_transformer.J,
                                 t_idx=t_idx)
        else:
            pass

    for hvdc_line in grid.hvdc_lines:
        if abs(hvdc_line.get_Vset_f_at(t=t_idx) - 1.0) > 1e-9 or abs(hvdc_line.get_Vset_t_at(t=t_idx) - 1.0) > 1e-9:
            raw_vsc = get_vsc_dc_line(hvdc_line,
                                      bus_dict=counter.psse_numbers_dict,
                                      version=version,
                                      t_idx=t_idx)
            psse_circuit.vsc_dc_lines.append(raw_vsc)
            if node_breaker_requested and node_breaker_data is not None:
                append_psse_terminal(node_breaker_data=node_breaker_data,
                                     bus=hvdc_line.bus_from,
                                     type_code='V',
                                     eqid=raw_vsc.NAME,
                                     version=version,
                                     ibus=raw_vsc.IBUS1,
                                     t_idx=t_idx)
                append_psse_terminal(node_breaker_data=node_breaker_data,
                                     bus=hvdc_line.bus_to,
                                     type_code='V',
                                     eqid=raw_vsc.NAME,
                                     version=version,
                                     ibus=raw_vsc.IBUS2,
                                     t_idx=t_idx)
            else:
                pass
        else:
            raw_dc = get_psse_two_terminal_dc_line(hvdc_line,
                                                   bus_dict=counter.psse_numbers_dict,
                                                   version=version,
                                                   t_idx=t_idx)
            psse_circuit.two_terminal_dc_lines.append(raw_dc)
            if node_breaker_requested and node_breaker_data is not None:
                append_psse_terminal(node_breaker_data=node_breaker_data,
                                     bus=hvdc_line.bus_from,
                                     type_code='D',
                                     eqid=raw_dc.NAME,
                                     version=version,
                                     ibus=raw_dc.IPR,
                                     t_idx=t_idx)
                append_psse_terminal(node_breaker_data=node_breaker_data,
                                     bus=hvdc_line.bus_to,
                                     type_code='D',
                                     eqid=raw_dc.NAME,
                                     version=version,
                                     ibus=raw_dc.IPI,
                                     t_idx=t_idx)
            else:
                pass

    for upfc_device in grid.upfc_devices:
        psse_circuit.facts.append(get_psse_facts(upfc_device,
                                                 bus_dict=counter.psse_numbers_dict,
                                                 version=version,
                                                 t_idx=t_idx))

    if node_breaker_requested and node_breaker_data is not None:
        psse_circuit.equipment_terminals.extend(node_breaker_data.equipment_terminals)
    else:
        pass

    return psse_circuit
