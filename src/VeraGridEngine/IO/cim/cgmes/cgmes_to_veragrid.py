# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Dict, List, Tuple, Union
import numpy as np
import VeraGridEngine.IO.cim.cgmes.cgmes_enums as cgmes_enums
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.enumerations import CGMESVersions, CgmesTopologyMode, ConverterControlType, ExternalGridMode
import VeraGridEngine.Devices as gcdev
import VeraGridEngine.IO.cim.cgmes.cgmes_assets.cgmes_2_4_15_assets as cgmes24
import VeraGridEngine.IO.cim.cgmes.cgmes_assets.cgmes_3_0_0_assets as cgmes30
from VeraGridEngine.IO.cim.cgmes.cgmes_circuit import CgmesCircuit
from VeraGridEngine.IO.cim.cgmes.cgmes_typing import (CGMES_TERMINAL, CGMES_TOPOLOGICAL_NODE,
                                                      CGMES_CONNECTIVITY_NODE, CGMES_DC_TERMINAL, CGMES_ASSETS,
                                                      CGMES_POWER_TRANSFORMER_END)

from VeraGridEngine.IO.cim.cgmes.cgmes_utils import (get_nominal_voltage,
                                                     get_nominal_voltage_for_cn,
                                                     get_pu_values_ac_line_segment,
                                                     get_values_shunt,
                                                     get_pu_values_power_transformer,
                                                     get_pu_values_power_transformer3w,
                                                     get_regulating_control_params,
                                                     sanitize_voltage_setpoint,
                                                     get_pu_values_power_transformer_end,
                                                     get_slack_id,
                                                     find_object_by_idtag,
                                                     find_terminal_bus,
                                                     find_terminal_bus_connectivity_priority,
                                                     normalize_cgmes_reference_uuid,
                                                     is_reference_priority_one,
                                                     build_cgmes_limit_dicts,
                                                     get_voltage_shunt,
                                                     get_power_transformer_ends,
                                                     extract_base_voltage_value,
                                                     recover_base_voltage_from_container,
                                                     recover_base_voltage_from_topological_node)

from VeraGridEngine.data_logger import DataLogger
from VeraGridEngine.enumerations import TapChangerTypes, TapPhaseControl, TapModuleControl, ShuntControlMode


class Cn2BusBarLookup:
    """
    Class to properly match the ConnectivityNodes to the BusBars
    """

    def __init__(self, cgmes_model: CgmesCircuit):
        """

        :param cgmes_model:
        """
        self.cn_dict: Dict[str, gcdev.Bus] = dict()
        self.bus_dict: Dict[str, gcdev.Bus] = dict()

        # fill information from CGMES terminals
        self.bb_to_cn_dict: Dict[str, CGMES_CONNECTIVITY_NODE] = dict()
        self.bb_to_tn_dict: Dict[str, CGMES_TOPOLOGICAL_NODE] = dict()

        self.fill(cgmes_model=cgmes_model)

    def fill(self, cgmes_model: CgmesCircuit):
        """

        :param cgmes_model:
        :return:
        """
        bb_tpe = cgmes_model.cgmes_assets.class_dict.get("BusbarSection", None)

        if bb_tpe is not None:

            # find the terminal -> CN links
            for terminal in cgmes_model.cgmes_assets.Terminal_list:
                if isinstance(terminal.ConductingEquipment, bb_tpe):

                    if terminal.ConnectivityNode is not None:
                        self.bb_to_cn_dict[terminal.ConductingEquipment.uuid] = terminal.ConnectivityNode

                    if terminal.TopologicalNode is not None:
                        self.bb_to_tn_dict[terminal.ConductingEquipment.uuid] = terminal.TopologicalNode

    def add_cn(self, bus: gcdev.Bus):
        """

        :param bus:
        :return:
        """
        self.cn_dict[bus.idtag] = bus

    def add_bus(self, bus: gcdev.Bus):
        """

        :param bus:
        :return:
        """
        self.bus_dict[bus.idtag] = bus

    def get_busbar_cn(self, bb_id: str) -> Union[None, gcdev.Bus]:
        """
        Get the associated ConnectivityNode object
        :param bb_id: BusBarSection uuid
        :return: Bus or None
        """
        cgmes_cn = self.bb_to_cn_dict.get(bb_id, None)

        if cgmes_cn is not None:
            return self.cn_dict[cgmes_cn.uuid]
        else:
            return None

    def get_busbar_bus(self, bb_id: str) -> Union[None, gcdev.Bus]:
        """
        Get the associated Bus object
        :param bb_id: BusBarSection uuid
        :return: Bus or None
        """
        cgmes_tn = self.bb_to_tn_dict.get(bb_id, None)

        if cgmes_tn is not None:
            return self.bus_dict[cgmes_tn.uuid]
        else:
            return None


def assign_bus_nominal_voltage_if_missing(bus: gcdev.Bus | None,
                                          nominal_voltage: float,
                                          logger: DataLogger,
                                          source: str,
                                          source_idtag: str) -> bool:
    """
    Assign bus nominal voltage if it is missing.

    :param bus: Bus object to update.
    :param nominal_voltage: Candidate nominal voltage.
    :param logger: Logger.
    :param source: Source element type.
    :param source_idtag: Source element idtag.
    :return: True if bus nominal voltage was updated.
    """
    if bus is None:
        return False
    else:
        pass

    if nominal_voltage <= 0.0:
        return False
    else:
        pass

    if bus.Vnom > 0.0:
        return False
    else:
        pass

    bus.Vnom = float(nominal_voltage)
    logger.add_warning(
        msg='Recovered bus nominal voltage from connected element',
        device=bus.idtag,
        device_class='Bus',
        device_property='Vnom',
        value=0.0,
        expected_value=bus.Vnom,
        comment=f'{source}:{source_idtag}'
    )
    return True


def recover_bus_nominal_voltages(gc_model: MultiCircuit, logger: DataLogger) -> None:
    """
    Recover missing bus nominal voltages from connected network elements.

    Recovery order:
    1. Seed voltages from transformer nominal side voltages.
    2. Propagate voltages through line/switch links.

    :param gc_model: Converted VeraGrid model.
    :param logger: Logger.
    :return: Nothing.
    """
    # Step 1: seed from transformer nominal sides.
    for transformer in gc_model.transformers2w:
        assign_bus_nominal_voltage_if_missing(
            bus=transformer.bus_from,
            nominal_voltage=float(transformer.HV),
            logger=logger,
            source='Transformer2W',
            source_idtag=transformer.idtag
        )
        assign_bus_nominal_voltage_if_missing(
            bus=transformer.bus_to,
            nominal_voltage=float(transformer.LV),
            logger=logger,
            source='Transformer2W',
            source_idtag=transformer.idtag
        )

    for transformer in gc_model.transformers3w:
        assign_bus_nominal_voltage_if_missing(
            bus=transformer.bus1,
            nominal_voltage=float(transformer.V1),
            logger=logger,
            source='Transformer3W',
            source_idtag=transformer.idtag
        )
        assign_bus_nominal_voltage_if_missing(
            bus=transformer.bus2,
            nominal_voltage=float(transformer.V2),
            logger=logger,
            source='Transformer3W',
            source_idtag=transformer.idtag
        )
        assign_bus_nominal_voltage_if_missing(
            bus=transformer.bus3,
            nominal_voltage=float(transformer.V3),
            logger=logger,
            source='Transformer3W',
            source_idtag=transformer.idtag
        )

    # Step 2: propagate through line/switch links.
    max_iterations: int = max(1, len(gc_model.buses))
    iteration_index: int = 0
    changed: bool = True
    while changed and iteration_index < max_iterations:
        changed = False
        iteration_index += 1

        for line in gc_model.lines:
            bus_from = line.bus_from
            bus_to = line.bus_to
            if bus_from is None or bus_to is None:
                pass
            elif bus_from.Vnom > 0.0 and bus_to.Vnom <= 0.0:
                if assign_bus_nominal_voltage_if_missing(
                        bus=bus_to,
                        nominal_voltage=float(bus_from.Vnom),
                        logger=logger,
                        source='Line',
                        source_idtag=line.idtag):
                    changed = True
                else:
                    pass
            elif bus_to.Vnom > 0.0 and bus_from.Vnom <= 0.0:
                if assign_bus_nominal_voltage_if_missing(
                        bus=bus_from,
                        nominal_voltage=float(bus_to.Vnom),
                        logger=logger,
                        source='Line',
                        source_idtag=line.idtag):
                    changed = True
                else:
                    pass
            else:
                pass

        for switch in gc_model.switch_devices:
            bus_from = switch.bus_from
            bus_to = switch.bus_to
            if bus_from is None or bus_to is None:
                pass
            elif bus_from.Vnom > 0.0 and bus_to.Vnom <= 0.0:
                if assign_bus_nominal_voltage_if_missing(
                        bus=bus_to,
                        nominal_voltage=float(bus_from.Vnom),
                        logger=logger,
                        source='Switch',
                        source_idtag=switch.idtag):
                    changed = True
                else:
                    pass
            elif bus_to.Vnom > 0.0 and bus_from.Vnom <= 0.0:
                if assign_bus_nominal_voltage_if_missing(
                        bus=bus_from,
                        nominal_voltage=float(bus_to.Vnom),
                        logger=logger,
                        source='Switch',
                        source_idtag=switch.idtag):
                    changed = True
                else:
                    pass
            else:
                pass


def enforce_ac_line_voltage_consistency(gc_model: MultiCircuit,
                                        logger: DataLogger,
                                        branch_connection_voltage_tolerance: float = 0.1) -> None:
    """
    Convert cross-voltage AC lines into transformers when both bus voltages are known.

    This enforces the same line/transformer consistency criterion after CGMES-specific
    voltage recovery has completed.

    :param gc_model: Converted VeraGrid model.
    :param logger: Logger.
    :param branch_connection_voltage_tolerance: Tolerance used by line->transformer criterion.
    :return: Nothing.
    """
    kept_lines: List[gcdev.Line] = list()

    for line in gc_model.lines:
        bus_from = line.bus_from
        bus_to = line.bus_to

        if bus_from is None or bus_to is None:
            kept_lines.append(line)
        elif bus_from.Vnom > 0.0 and bus_to.Vnom > 0.0:
            should_convert = line.should_this_be_a_transformer(
                branch_connection_voltage_tolerance=branch_connection_voltage_tolerance,
                logger=None
            )
            if should_convert:
                transformer = line.get_equivalent_transformer(index=gc_model.time_profile)
                gc_model.add_transformer2w(transformer)
                logger.add_warning(
                    msg='Converted cross-voltage ACLineSegment to Transformer2W after CGMES nominal-voltage recovery',
                    device=line.idtag,
                    device_class='ACLineSegment',
                    value=min(bus_from.Vnom, bus_to.Vnom),
                    expected_value=max(bus_from.Vnom, bus_to.Vnom)
                )
            else:
                kept_lines.append(line)
        else:
            kept_lines.append(line)

    gc_model.lines = kept_lines


def build_terminal_voltage_hints(cgmes_model: CgmesCircuit) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    Build voltage hints from terminal associations for CN and TN buses.

    The hints are used when direct BaseVoltage references are missing.

    :param cgmes_model: CGMES model.
    :return: Tuple with:
             - ConnectivityNode UUID -> nominal voltage hint (kV)
             - TopologicalNode UUID -> nominal voltage hint (kV)
    """
    cn_voltage_hints: Dict[str, float] = dict()
    tn_voltage_hints: Dict[str, float] = dict()

    for terminal in cgmes_model.cgmes_assets.Terminal_list:
        voltage_hint: float | None = None

        equipment = terminal.ConductingEquipment
        if equipment is not None and not isinstance(equipment, str):
            if equipment.BaseVoltage is not None:
                voltage_hint = extract_base_voltage_value(equipment.BaseVoltage)

            if voltage_hint is None:
                voltage_hint = recover_base_voltage_from_container(equipment.EquipmentContainer)

        if voltage_hint is None:
            voltage_hint = recover_base_voltage_from_topological_node(terminal.TopologicalNode)

        if voltage_hint is not None and voltage_hint > 0.0:
            if terminal.ConnectivityNode is not None and not isinstance(terminal.ConnectivityNode, str):
                cn_uuid: str = terminal.ConnectivityNode.uuid
                if cn_uuid not in cn_voltage_hints:
                    cn_voltage_hints[cn_uuid] = voltage_hint
                else:
                    pass
            else:
                pass

            if terminal.TopologicalNode is not None and not isinstance(terminal.TopologicalNode, str):
                tn_uuid: str = terminal.TopologicalNode.uuid
                if tn_uuid not in tn_voltage_hints:
                    tn_voltage_hints[tn_uuid] = voltage_hint
                else:
                    pass
            else:
                pass
        else:
            pass

    return cn_voltage_hints, tn_voltage_hints


def get_gcdev_voltage_dict(cgmes_model: CgmesCircuit,
                           logger: DataLogger) -> Dict[str, Tuple[float, float]]:
    """
    Builds up voltage dictionary.

    :param cgmes_model: The CGMES circuit model.
    :param logger: The data logger for error handling.
    :return: A dictionary mapping TopologicalNode UUIDs
        to voltage (v) and angle. Dict[str, Tuple[float, float]]
    """

    # build the voltages dictionary
    v_dict: Dict[str, Tuple[float, float]] = dict()

    for e in cgmes_model.cgmes_assets.SvVoltage_list:
        if e.TopologicalNode and not isinstance(e.TopologicalNode, str):
            v_dict[e.TopologicalNode.uuid] = (e.v, e.angle)
        else:
            logger.add_error(msg='Missing reference',
                             device=e.rdfid,
                             device_class=e.tpe,
                             device_property="TopologicalNode",
                             value=e.TopologicalNode,
                             expected_value='object')
    return v_dict


def get_gcdev_device_to_terminal_dict(cgmes_model: CgmesCircuit,
                                      logger: DataLogger) -> Dict[str, List[CGMES_TERMINAL]]:
    """
    Dictionary relating the conducting equipment to the terminal object(s)
    """
    # dictionary relating the conducting equipment to the terminal object
    device_to_terminal_dict: Dict[str, List[CGMES_TERMINAL]] = dict()

    if cgmes_model.cgmes_version == CGMESVersions.v2_4_15:
        con_eq_type = cgmes24.ConductingEquipment
    elif cgmes_model.cgmes_version == CGMESVersions.v3_0_0:
        con_eq_type = cgmes30.ConductingEquipment
    else:
        raise NotImplementedError()

    for term in cgmes_model.cgmes_assets.Terminal_list:
        if isinstance(term.ConductingEquipment, con_eq_type):
            lst = device_to_terminal_dict.get(term.ConductingEquipment.uuid, None)
            if lst is None:
                device_to_terminal_dict[term.ConductingEquipment.uuid] = [term]
            else:
                lst.append(term)
        else:
            logger.add_error(msg='The object is not a ConductingEquipment',
                             device=term.rdfid,
                             device_class=term.tpe,
                             device_property="ConductingEquipment",
                             value=term.ConductingEquipment,
                             expected_value='object')
    return device_to_terminal_dict


def get_gcdev_dc_device_to_terminal_dict(
        cgmes_model: CgmesCircuit,
        logger: DataLogger) -> tuple[
    dict[str, list[CGMES_DC_TERMINAL]],
    list[CGMES_TOPOLOGICAL_NODE],
    list[CGMES_DC_TERMINAL]]:
    """
    Dictionary relating the DC conducting equipment to the DC terminal object(s)
    :param cgmes_model:
    :param logger:
    :return:
    """

    dc_device_to_terminal_dict: Dict[str, List[CGMES_TERMINAL]] = dict()

    if cgmes_model.cgmes_version == CGMESVersions.v2_4_15:
        dc_ground_type = cgmes24.DCGround
        dc_terminal_type = cgmes24.DCTerminal

    elif cgmes_model.cgmes_version == CGMESVersions.v3_0_0:
        dc_ground_type = cgmes30.DCGround
        dc_terminal_type = cgmes30.DCTerminal
    else:
        raise NotImplementedError()

    for dc_term in cgmes_model.cgmes_assets.DCTerminal_list:

        if isinstance(dc_term.DCConductingEquipment, dc_ground_type):
            logger.add_info(msg='DCGround DCTerminals are not imported',
                            device=dc_term.rdfid,
                            device_class=dc_term.tpe,
                            device_property="DCGround",
                            value=dc_term.DCConductingEquipment,
                            comment="get_gcdev_dc_device_to_terminal_dict")
            continue
        else:  # DCTerminals for DCLineSegments
            if dc_term.DCConductingEquipment is not None:
                lst = dc_device_to_terminal_dict.get(dc_term.DCConductingEquipment.uuid, None)
                if lst is None:
                    dc_device_to_terminal_dict[dc_term.DCConductingEquipment.uuid] = [dc_term]
                else:
                    lst.append(dc_term)
            else:
                logger.add_error(msg='No DCConductingEquipment',
                                 device=dc_term.rdfid,
                                 device_class=dc_term.tpe,
                                 device_property="DCConductingEquipment")

    ground_tp_list = list()
    ground_node_list = list()

    # relating the converter terminals to DCTerminals to if DCNode is common
    for conv_dc_term in cgmes_model.cgmes_assets.ACDCConverterDCTerminal_list:

        dc_term_n = None  # DCTerminal inside the same DCNode
        dc_node = conv_dc_term.DCNode

        if dc_node is not None:
            dc_tp = conv_dc_term.DCTopologicalNode

            dc_node_terminals = getattr(dc_node, "DCTerminals", None)
            if dc_node_terminals is None or len(dc_node_terminals) == 0:
                logger.add_error(
                    msg='No DCTerminals in DCNode',
                    device=conv_dc_term.rdfid,
                    device_class=conv_dc_term.tpe,
                    device_property="DCNode.DCTerminals",
                    value=dc_node_terminals,
                    comment="get_gcdev_dc_device_to_terminal_dict"
                )
                continue

            if isinstance(dc_node_terminals[0], dc_terminal_type):
                dc_term_n = dc_node_terminals[0]
            elif len(dc_node_terminals) > 1 and isinstance(dc_node_terminals[1], dc_terminal_type):
                dc_term_n = dc_node_terminals[1]
            else:
                logger.add_error(
                    msg='No DCTerminal in DCNode Terminals [0:1]',
                    device=conv_dc_term.rdfid,
                    device_class=conv_dc_term.tpe,
                    device_property="DCNode",
                    value=conv_dc_term.DCNode,
                    comment="get_gcdev_dc_device_to_terminal_dict"
                )
                continue

            dc_term_n_cond_eq = getattr(dc_term_n, "DCConductingEquipment", None)
            if dc_term_n_cond_eq is None:
                logger.add_error(
                    msg='No DCConductingEquipment in DCTerminal',
                    device=conv_dc_term.rdfid,
                    device_class=conv_dc_term.tpe,
                    device_property="DCTerminal.DCConductingEquipment",
                    value=dc_term_n,
                    comment="get_gcdev_dc_device_to_terminal_dict"
                )
                continue

            if isinstance(dc_term_n_cond_eq, dc_ground_type):
                logger.add_info(msg='DCGround ACDC converter DC terminals are not imported',
                                device=conv_dc_term.rdfid,
                                device_class=conv_dc_term.tpe,
                                device_property="DCGround",
                                value=conv_dc_term.DCConductingEquipment,
                                comment="get_gcdev_dc_device_to_terminal_dict")
                ground_tp_list.append(dc_tp)
                ground_node_list.append(dc_node)
                continue
            else:  # DCTerminals for ACDCConverter DC side
                dc_cond_eq = conv_dc_term.DCConductingEquipment  # the VSC
                if dc_cond_eq is None:
                    logger.add_error(msg='No DCConductingEquipment',
                                     device=conv_dc_term.rdfid,
                                     device_class=conv_dc_term.tpe,
                                     device_property="DCConductingEquipment",
                                     comment="get_gcdev_dc_device_to_terminal_dict")
                    continue
                lst = dc_device_to_terminal_dict.get(dc_cond_eq.uuid, None)
                if lst is None:
                    dc_device_to_terminal_dict[dc_cond_eq.uuid] = [dc_term_n]
                else:
                    lst.append(dc_term_n)
        else:
            logger.add_error("DCNode is None",
                             device_class=conv_dc_term.tpe,
                             device=conv_dc_term.rdfid,
                             device_property="DCNode")

    return dc_device_to_terminal_dict, ground_tp_list, ground_node_list


def find_associated_buses(cgmes_elm: CGMES_ASSETS,
                          device_to_terminal_dict: Dict[str, List[CGMES_TERMINAL | CGMES_DC_TERMINAL]],
                          bus_dict: Dict[str, gcdev.Bus],
                          TopologicalNode_tpe,
                          DCTopologicalNode_tpe,
                          logger: DataLogger,
                          cgmes_version: CGMESVersions | None = None,
                          prefer_connectivity_node: bool = False) -> List[gcdev.Bus]:
    """
    This function finds the buses connected to a device
    :param cgmes_elm: some CGMES element
    :param device_to_terminal_dict: dictionary that related the CGMES device to all the terminals it may have
    :param bus_dict: dictionary of VeraGrid buses
    :param TopologicalNode_tpe: TopologicalNode type
                                (might come from different cgmes versions, hence we need to pass the type)
    :param DCTopologicalNode_tpe: DCTopologicalNode type
                                  (might come from different cgmes versions, hence we need to pass the type)
    :param logger: DataLogger
    :param cgmes_version: CGMES version to select the terminal-to-bus strategy.
    :return: list of associated buses
    """
    # get the cgmes terminal of this device
    cgmes_terminals = device_to_terminal_dict.get(cgmes_elm.uuid, None)

    if cgmes_terminals is not None:
        buses = list()
        for cgmes_terminal in cgmes_terminals:
            if prefer_connectivity_node or cgmes_version == CGMESVersions.v3_0_0:
                bus = find_terminal_bus_connectivity_priority(
                    cgmes_terminal=cgmes_terminal,
                    bus_dict=bus_dict,
                    TopologicalNode_tpe=TopologicalNode_tpe,
                    DCTopologicalNode_tpe=DCTopologicalNode_tpe
                )
            else:
                bus = find_terminal_bus(cgmes_terminal=cgmes_terminal,
                                        bus_dict=bus_dict,
                                        TopologicalNode_tpe=TopologicalNode_tpe,
                                        DCTopologicalNode_tpe=DCTopologicalNode_tpe)
            if bus is not None:
                buses.append(bus)
    else:
        buses = []
        logger.add_error("No terminal for the device",
                         device=cgmes_elm.rdfid,
                         device_class=cgmes_elm.tpe)

    return buses


def deduplicate_buses_preserve_order(buses: List[gcdev.Bus]) -> List[gcdev.Bus]:
    """
    Deduplicate a bus list preserving order by bus idtag.

    This is useful when CGMES profile merges produce repeated terminals that map
    to the same electrical pair.
    """
    unique_buses: List[gcdev.Bus] = list()
    seen: set[str] = set()
    for bus in buses:
        if bus.idtag not in seen:
            unique_buses.append(bus)
            seen.add(bus.idtag)
    return unique_buses


def normalize_terminal_bus_mappings(calc_nodes: List[gcdev.Bus],
                                    expected_count: int) -> Tuple[List[gcdev.Bus], List[gcdev.Bus], bool]:
    """
    Normalize terminal-to-bus mappings for devices with a known connection count.

    Some CGMES imports can produce repeated terminal mappings that still resolve to
    the expected number of electrically distinct buses. In that case, collapse the
    repeated references instead of dropping the device.
    """
    unique_calc_nodes = deduplicate_buses_preserve_order(calc_nodes)

    if len(calc_nodes) == expected_count:
        return calc_nodes, unique_calc_nodes, False

    if len(calc_nodes) > expected_count and len(unique_calc_nodes) == expected_count:
        return unique_calc_nodes, unique_calc_nodes, True

    return calc_nodes, unique_calc_nodes, False


def log_collapsed_terminal_mapping_warning(logger: DataLogger,
                                           cgmes_elm: CGMES_ASSETS,
                                           raw_count: int,
                                           expected_count: int) -> None:
    logger.add_warning(
        msg='Collapsed repeated terminal-to-bus mappings',
        device=cgmes_elm.rdfid,
        device_class=cgmes_elm.tpe,
        device_property="number of associated terminals",
        value=raw_count,
        expected_value=expected_count
    )


def get_cgmes_equipment_active_state(cgmes_elm: CGMES_ASSETS,
                                     use_switch_open: bool = False) -> bool:
    """
    Determine whether a CGMES equipment item should be active in VeraGrid.

    For switches, an element is active only when it is in service and closed.
    For all other equipment, the inService flag is used when available.
    """
    in_service = getattr(cgmes_elm, "inService", None)
    active = True if in_service is None else bool(in_service)

    if use_switch_open:
        active = active and not bool(getattr(cgmes_elm, "open", False))

    return active


def derive_switch_bus_pair(calc_nodes: List[gcdev.Bus],
                           allow_terminal_pair_merge: bool) -> Tuple[gcdev.Bus | None, gcdev.Bus | None]:
    """
    Derive a two-bus switch pair from terminal-mapped buses.

    :param calc_nodes: Buses mapped from all switch terminals.
    :param allow_terminal_pair_merge: Allow collapsing repeated terminal mappings.
    :return: Pair of buses or (None, None) when no valid pair is available.
    """
    if len(calc_nodes) == 2:
        # Keep legacy behavior for canonical two-terminal switches.
        return calc_nodes[0], calc_nodes[1]
    else:
        pass

    if allow_terminal_pair_merge:
        unique_calc_nodes: List[gcdev.Bus] = deduplicate_buses_preserve_order(calc_nodes)
        if len(calc_nodes) > 2 and len(unique_calc_nodes) == 2:
            return unique_calc_nodes[0], unique_calc_nodes[1]
        elif len(calc_nodes) > 2 and len(unique_calc_nodes) == 1:
            # Preserve historical permissive handling for repeated same-bus references.
            return calc_nodes[0], calc_nodes[1]
        else:
            return None, None
    else:
        return None, None


def has_v2_4_15_terminal_pathology_for_switch_merge(
        cgmes_model: CgmesCircuit,
        device_to_terminal_dict: Dict[str, List[CGMES_TERMINAL]]) -> bool:
    """
    Detect known terminal-pathology patterns that justify switch pair merging.

    :param cgmes_model: CGMES model.
    :param device_to_terminal_dict: Device-to-terminal mapping.
    :return: True when known pathological signatures are detected.
    """
    malformed_equivalent_injections: int = 0
    for equivalent_injection in cgmes_model.cgmes_assets.EquivalentInjection_list:
        terminals: List[CGMES_TERMINAL] | None = device_to_terminal_dict.get(equivalent_injection.uuid, None)
        terminal_count: int = 0 if terminals is None else len(terminals)
        if terminal_count == 0:
            malformed_equivalent_injections += 1
        else:
            pass

    malformed_ac_lines: int = 0
    for ac_line_segment in cgmes_model.cgmes_assets.ACLineSegment_list:
        terminals = device_to_terminal_dict.get(ac_line_segment.uuid, None)
        terminal_count = 0 if terminals is None else len(terminals)
        if terminal_count == 1:
            malformed_ac_lines += 1
        else:
            pass

    if malformed_equivalent_injections > 0 or malformed_ac_lines > 0:
        return True
    else:
        return False


def detect_switch_terminal_pairing_preference(cgmes_model: CgmesCircuit,
                                              cgmes_topology_mode: CgmesTopologyMode,
                                              device_to_terminal_dict: Dict[str, List[CGMES_TERMINAL]],
                                              bus_dict: Dict[str, gcdev.Bus]) -> bool:
    """
    Decide if switch terminal pairing should prioritize ConnectivityNode.
    """
    # This detection is only intended for CGMES 2.4.15.
    if cgmes_model.cgmes_version != CGMESVersions.v2_4_15:
        return False
    else:
        pass
    if not has_v2_4_15_terminal_pathology_for_switch_merge(
            cgmes_model=cgmes_model,
            device_to_terminal_dict=device_to_terminal_dict):
        return False
    else:
        pass

    TopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("TopologicalNode")
    DCTopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("DCTopologicalNode")

    switch_elements = (
            cgmes_model.cgmes_assets.Switch_list
            + cgmes_model.cgmes_assets.Breaker_list
            + cgmes_model.cgmes_assets.Disconnector_list
            + cgmes_model.cgmes_assets.LoadBreakSwitch_list
    )

    if len(switch_elements) == 0:
        return False
    else:
        pass

    cn_valid, cn_invalid = score_switch_pairing_mode(
        switch_elements=switch_elements,
        prefer_connectivity=True,
        device_to_terminal_dict=device_to_terminal_dict,
        bus_dict=bus_dict,
        TopologicalNode_tpe=TopologicalNode_tpe,
        DCTopologicalNode_tpe=DCTopologicalNode_tpe,
        cgmes_version=cgmes_model.cgmes_version
    )
    tn_valid, tn_invalid = score_switch_pairing_mode(
        switch_elements=switch_elements,
        prefer_connectivity=False,
        device_to_terminal_dict=device_to_terminal_dict,
        bus_dict=bus_dict,
        TopologicalNode_tpe=TopologicalNode_tpe,
        DCTopologicalNode_tpe=DCTopologicalNode_tpe,
        cgmes_version=cgmes_model.cgmes_version
    )

    if cn_valid > tn_valid:
        return True
    if cn_valid < tn_valid:
        return False
    # tie-breaker: fewer invalid elements wins; final tie keeps legacy behavior
    if cn_invalid < tn_invalid:
        return True
    return False


def score_switch_pairing_mode(switch_elements: List[CGMES_ASSETS],
                              prefer_connectivity: bool,
                              device_to_terminal_dict: Dict[str, List[CGMES_TERMINAL]],
                              bus_dict: Dict[str, gcdev.Bus],
                              TopologicalNode_tpe,
                              DCTopologicalNode_tpe,
                              cgmes_version: CGMESVersions) -> Tuple[int, int]:
    """
    Score a switch pairing mode by counting valid two-bus matches.

    :param switch_elements: Switch-like CGMES elements to evaluate.
    :param prefer_connectivity: Whether to prioritize ConnectivityNode.
    :param device_to_terminal_dict: Device-to-terminal mapping.
    :param bus_dict: Imported bus lookup.
    :param TopologicalNode_tpe: TopologicalNode class type.
    :param DCTopologicalNode_tpe: DCTopologicalNode class type.
    :param cgmes_version: CGMES version.
    :return: Tuple(valid_two_bus_count, invalid_count).
    """
    valid_two_bus: int = 0
    invalid: int = 0
    silent_logger: DataLogger = DataLogger()
    for switch_element in switch_elements:
        nodes: List[gcdev.Bus] = find_associated_buses(
            cgmes_elm=switch_element,
            device_to_terminal_dict=device_to_terminal_dict,
            bus_dict=bus_dict,
            TopologicalNode_tpe=TopologicalNode_tpe,
            DCTopologicalNode_tpe=DCTopologicalNode_tpe,
            logger=silent_logger,
            cgmes_version=cgmes_version,
            prefer_connectivity_node=prefer_connectivity
        )
        unique_nodes: List[gcdev.Bus] = deduplicate_buses_preserve_order(nodes)
        if len(unique_nodes) == 2:
            valid_two_bus += 1
        else:
            invalid += 1
    return valid_two_bus, invalid


def get_gcdev_buses(cgmes_model: CgmesCircuit,
                    gc_model: MultiCircuit,
                    v_dict: Dict[str, Tuple[float, float]],
                    cn_look_up: Cn2BusBarLookup,
                    cgmes_topology_mode: CgmesTopologyMode,
                    skip_dc_import: bool,
                    buses_to_skip: List,
                    default_nominal_voltage: float,
                    logger: DataLogger) -> Tuple[Dict[str, gcdev.Bus], bool]:
    """
    Convert the TopologicalNodes to Buses (CalculationNodes)

    :param cgmes_model: CgmesCircuit
    :param gc_model: gcdevCircuit
    :param v_dict: Dict[str, Terminal]
    :param cn_look_up: CnLookup
    :param cgmes_topology_mode: Bus creation strategy.
    :param default_nominal_voltage:
    :param buses_to_skip:
    :param skip_dc_import:
    :param logger: DataLogger

    :return: dictionary relating the TopologicalNode uuid to the gcdev CalculationNode
             Dict[str, gcdev.Bus], fatal error?
    """

    slack_tp_uuid_set = set()

    slack_tp_uuid = get_slack_id(cgmes_model.cgmes_assets.SynchronousMachine_list)
    if slack_tp_uuid is not None:
        slack_tp_uuid_set.add(slack_tp_uuid)

    for machine in cgmes_model.cgmes_assets.SynchronousMachine_list:
        reference_priority = getattr(machine, "referencePriority", None)
        if is_reference_priority_one(reference_priority):
            machine_terminals = getattr(machine, "Terminals", None)
            if isinstance(machine_terminals, list):
                for machine_terminal in machine_terminals:
                    if hasattr(machine_terminal, "TopologicalNode"):
                        machine_tp_uuid = normalize_cgmes_reference_uuid(machine_terminal.TopologicalNode)
                        if machine_tp_uuid is not None:
                            slack_tp_uuid_set.add(machine_tp_uuid)
            elif machine_terminals is not None:
                if hasattr(machine_terminals, "TopologicalNode"):
                    machine_tp_uuid = normalize_cgmes_reference_uuid(machine_terminals.TopologicalNode)
                    if machine_tp_uuid is not None:
                        slack_tp_uuid_set.add(machine_tp_uuid)

    for island in cgmes_model.cgmes_assets.TopologicalIsland_list:
        angle_ref = getattr(island, "AngleRefTopologicalNode", None)
        island_tp_uuid = normalize_cgmes_reference_uuid(angle_ref)
        if island_tp_uuid is not None:
            slack_tp_uuid_set.add(island_tp_uuid)

    if len(slack_tp_uuid_set) == 0:
        logger.add_error(msg="Couldn't find slack reference from SynchronousMachines or TopologicalIslands.",
                         device_class="SynchronousMachine",
                         device_property="referencePriority")

    # dictionary relating the TopologicalNode uuid to the gcdev CalculationNode
    calc_node_dict: Dict[str, gcdev.Bus] = dict()

    tp_with_cn = set()
    TopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("TopologicalNode")
    DCTopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("DCTopologicalNode")
    line_tpe = cgmes_model.cgmes_assets.class_dict.get("Line")
    cn_voltage_hints, tn_voltage_hints = build_terminal_voltage_hints(cgmes_model=cgmes_model)

    if cgmes_topology_mode == CgmesTopologyMode.Auto:
        use_connectivity_nodes = len(cgmes_model.cgmes_assets.ConnectivityNode_list) > 0
    elif cgmes_topology_mode == CgmesTopologyMode.ConnectivityNode:
        use_connectivity_nodes = True
    else:
        use_connectivity_nodes = False

    # First convert every CN to a bus when working in node-breaker mode.
    if use_connectivity_nodes:
        for cn_elm in cgmes_model.cgmes_assets.ConnectivityNode_list:

            voltage = v_dict.get(cn_elm.uuid, None)
            nominal_voltage = get_nominal_voltage_for_cn(cn=cn_elm, logger=logger)
            if nominal_voltage == 0:
                cn_hint_voltage = cn_voltage_hints.get(cn_elm.uuid, None)
                if cn_hint_voltage is not None:
                    nominal_voltage = cn_hint_voltage
                    logger.add_warning(msg='Recovered ConnectivityNode nominal voltage from terminal associations',
                                       device=cn_elm.rdfid,
                                       device_class=cn_elm.tpe,
                                       device_property="nominalVoltage",
                                       value=0.0,
                                       expected_value=cn_hint_voltage)
                else:
                    logger.add_error(msg='Nominal voltage is 0. :(',
                                     device=cn_elm.rdfid,
                                     device_class=cn_elm.tpe,
                                     device_property="nominalVoltage")
            elif nominal_voltage is None:
                recovered_voltage = None
                if hasattr(cn_elm, "TopologicalNode"):
                    cn_tp_uuid = normalize_cgmes_reference_uuid(cn_elm.TopologicalNode)
                    if cn_tp_uuid is not None:
                        recovered_voltage = tn_voltage_hints.get(cn_tp_uuid, None)

                if recovered_voltage is None:
                    recovered_voltage = float(default_nominal_voltage)
                    logger.add_warning(
                        msg='Nominal voltage is None. Falling back to default nominal voltage',
                        device=cn_elm.rdfid,
                        device_class=cn_elm.tpe,
                        device_property="nominalVoltage",
                        value=None,
                        expected_value=recovered_voltage
                    )
                else:
                    logger.add_warning(
                        msg='Recovered ConnectivityNode nominal voltage from related TopologicalNode hints',
                        device=cn_elm.rdfid,
                        device_class=cn_elm.tpe,
                        device_property="nominalVoltage",
                        value=None,
                        expected_value=recovered_voltage
                    )
                nominal_voltage = recovered_voltage

            if voltage is not None and nominal_voltage is not None:
                if nominal_voltage != 0.0:
                    vm = voltage[0] / nominal_voltage
                    va = np.deg2rad(voltage[1])
                else:
                    logger.add_error("Nominal voltage is exactly zero",
                                     device=cn_elm.rdfid,
                                     device_class=cn_elm.tpe,
                                     device_property="nominalVoltage")
                    vm = 1.0
                    va = 0.0
            else:
                vm = 1.0
                va = 0.0

            cn_uuid = normalize_cgmes_reference_uuid(cn_elm.uuid)
            cn_rdfid_uuid = normalize_cgmes_reference_uuid(cn_elm.rdfid)
            cn_tp_uuid = normalize_cgmes_reference_uuid(
                cn_elm.TopologicalNode if hasattr(cn_elm, "TopologicalNode") else None
            )

            is_slack = False
            if cn_uuid is not None and cn_uuid in slack_tp_uuid_set:
                is_slack = True
            elif cn_rdfid_uuid is not None and cn_rdfid_uuid in slack_tp_uuid_set:
                is_slack = True
            elif cn_tp_uuid is not None and cn_tp_uuid in slack_tp_uuid_set:
                is_slack = True
            else:
                is_slack = False

            gcdev_elm = gcdev.Bus(
                idtag=cn_elm.uuid,
                code=cn_elm.description,
                name=cn_elm.name,
                Vnom=nominal_voltage,
                is_slack=is_slack,
                Va0=va,
                Vm0=vm,
            )

            gc_model.add_bus(gcdev_elm)
            cn_look_up.add_cn(gcdev_elm)
            calc_node_dict[gcdev_elm.idtag] = gcdev_elm

            # Record the associated TopologicalNode
            if hasattr(cn_elm, "TopologicalNode"):
                if isinstance(cn_elm.TopologicalNode, (TopologicalNode_tpe, DCTopologicalNode_tpe)):
                    tp_uid = cn_elm.TopologicalNode.uuid
                    tp_with_cn.add(tp_uid)
                    # we double-record such that the TP is considered later
                    calc_node_dict[tp_uid] = gcdev_elm

    # A TopologicalNode is only converted if there is no ConnectivityNode associated
    for tp_node in cgmes_model.cgmes_assets.TopologicalNode_list:

        if (not use_connectivity_nodes) or (tp_node.uuid not in tp_with_cn):

            voltage = v_dict.get(tp_node.uuid, None)
            nominal_voltage = get_nominal_voltage(topological_node=tp_node, logger=logger)
            if nominal_voltage == 0:
                tp_hint_voltage = tn_voltage_hints.get(tp_node.uuid, None)
                if tp_hint_voltage is not None:
                    nominal_voltage = tp_hint_voltage
                    logger.add_warning(msg='Recovered TopologicalNode nominal voltage from terminal associations',
                                       device=tp_node.rdfid,
                                       device_class=tp_node.tpe,
                                       device_property="nominalVoltage",
                                       value=0.0,
                                       expected_value=tp_hint_voltage)
                else:
                    logger.add_error(msg='Nominal voltage is 0. :(',
                                     device=tp_node.rdfid,
                                     device_class=tp_node.tpe,
                                     device_property="nominalVoltage")
            elif nominal_voltage is None:
                tp_hint_voltage = tn_voltage_hints.get(tp_node.uuid, None)
                if tp_hint_voltage is not None:
                    nominal_voltage = tp_hint_voltage
                    logger.add_warning(
                        msg='Recovered TopologicalNode nominal voltage from terminal associations after missing base reference',
                        device=tp_node.rdfid,
                        device_class=tp_node.tpe,
                        device_property="nominalVoltage",
                        value=None,
                        expected_value=tp_hint_voltage
                    )
                else:
                    nominal_voltage = float(default_nominal_voltage)
                    logger.add_warning(
                        msg='Nominal voltage is None. Falling back to default nominal voltage',
                        device=tp_node.rdfid,
                        device_class=tp_node.tpe,
                        device_property="nominalVoltage",
                        value=None,
                        expected_value=nominal_voltage
                    )

            if voltage is not None and nominal_voltage is not None:
                if nominal_voltage != 0.0:
                    vm = voltage[0] / nominal_voltage
                    va = np.deg2rad(voltage[1])
                else:
                    logger.add_error("Nominal voltage is exactly zero",
                                     device=tp_node.rdfid,
                                     device_class=tp_node.tpe,
                                     device_property="nominalVoltage")
                    vm = 1.0
                    va = 0.0
            else:
                vm = 1.0
                va = 0.0

            tp_uuid = normalize_cgmes_reference_uuid(tp_node.uuid)
            tp_rdfid_uuid = normalize_cgmes_reference_uuid(tp_node.rdfid)
            is_slack = False
            if tp_uuid is not None and tp_uuid in slack_tp_uuid_set:
                is_slack = True
            elif tp_rdfid_uuid is not None and tp_rdfid_uuid in slack_tp_uuid_set:
                is_slack = True

            volt_lev = None
            substation = None
            country = None
            area = None
            zone = None
            longitude = 0.0
            latitude = 0.0
            if tp_node.ConnectivityNodeContainer is not None:

                if isinstance(tp_node.ConnectivityNodeContainer, str):
                    volt_lev: gcdev.VoltageLevel | None = find_object_by_idtag(
                        object_list=gc_model.voltage_levels,
                        target_idtag=tp_node.ConnectivityNodeContainer
                    )
                else:
                    volt_lev: gcdev.VoltageLevel | None = find_object_by_idtag(
                        object_list=gc_model.voltage_levels,
                        target_idtag=tp_node.ConnectivityNodeContainer.uuid
                    )

                if volt_lev is None:
                    if not isinstance(tp_node.ConnectivityNodeContainer, line_tpe):
                        logger.add_warning(msg='No voltage level found for the bus',
                                           device=tp_node.rdfid,
                                           device_class=tp_node.tpe,
                                           device_property="ConnectivityNodeContainer")
                else:
                    if volt_lev.substation is not None:
                        substation: gcdev.Substation | None = find_object_by_idtag(
                            object_list=gc_model.substations,
                            target_idtag=volt_lev.substation.idtag
                        )
                    else:
                        substation = None

                    if substation is None:
                        logger.add_warning(msg='No substation found for bus.',
                                           device=volt_lev.rdfid,
                                           device_class=str(volt_lev),
                                           device_property="substation")
                        print(f'No substation found for BUS {tp_node.name}')
                    else:
                        if cgmes_model.cgmes_map_areas_like_raw:
                            area = substation.area
                            zone = substation.zone
                        else:
                            country = substation.country
                        longitude = substation.longitude
                        latitude = substation.latitude
            else:
                logger.add_warning(msg='Missing voltage level.',
                                   device=tp_node.rdfid,
                                   device_class=tp_node.tpe,
                                   device_property="ConnectivityNodeContainer")
                # else form here get SubRegion and Region for Country...

            gcdev_elm = gcdev.Bus(name=tp_node.name,
                                  idtag=tp_node.uuid,
                                  code=tp_node.description,
                                  Vnom=nominal_voltage,
                                  vmin=0.9,
                                  vmax=1.1,
                                  active=True,
                                  is_slack=is_slack,
                                  is_dc=False,
                                  # is_internal=False,
                                  area=area,
                                  zone=zone,
                                  substation=substation,
                                  voltage_level=volt_lev,
                                  country=country,
                                  latitude=latitude,
                                  longitude=longitude,
                                  Vm0=vm,
                                  Va0=va)

            gc_model.add_bus(gcdev_elm)
            cn_look_up.add_bus(bus=gcdev_elm)
            calc_node_dict[gcdev_elm.idtag] = gcdev_elm
        else:
            logger.add_info(
                "TopologicalNode skipped because a ConnectivityNode exists",
                device_class="TopologicalNode",
                device=tp_node.uuid)

    # We try to add the DC nodes
    for cn_elm in cgmes_model.cgmes_assets.DCTopologicalNode_list:

        if not (cn_elm.uuid in tp_with_cn):
            if cn_elm not in buses_to_skip:
                gcdev_elm = gcdev.Bus(
                    name=cn_elm.name,
                    idtag=cn_elm.uuid,
                    code=cn_elm.description,
                    Vnom=default_nominal_voltage,
                    active=True,
                    is_slack=False,
                    is_dc=True,
                    area=None,  # areas and zones are not created from cgmes models
                    zone=None,
                    # substation=substat,
                    # voltage_level=volt_lev,
                    # country=country,
                    # latitude=latitude,
                    # longitude=longitude,
                    # Vm0=vm,
                    # Va0=va
                )

                if not skip_dc_import:
                    gc_model.add_bus(gcdev_elm)

                calc_node_dict[gcdev_elm.idtag] = gcdev_elm

    has_slack = any(bus.is_slack for bus in gc_model.buses)
    if not has_slack:
        matched_slack_uuid_set = set()
        for slack_tp_uuid in slack_tp_uuid_set:
            slack_bus = calc_node_dict.get(slack_tp_uuid, None)
            if slack_bus is not None:
                slack_bus.is_slack = True
                matched_slack_uuid_set.add(slack_tp_uuid)

        if len(slack_tp_uuid_set) > 0 and len(matched_slack_uuid_set) == 0:
            logger.add_warning(msg='Slack node reference not matched to imported buses',
                               device_class='TopologicalNode',
                               device_property='AngleRefTopologicalNode',
                               value=str(slack_tp_uuid_set))

    return calc_node_dict, False


# def get_gcdev_dc_buses(cgmes_model: CgmesCircuit,
#                        gc_model: MultiCircuit,
#                        skip_dc_import: bool,
#                        buses_to_skip: List,
#                        logger: DataLogger,
#                        default_nominal_voltage=500.0) -> Dict[str, gcdev.Bus]:
#     """
#     Convert the DCTopologicalNodes to DC Buses (CalculationNodes)
#
#     :param cgmes_model: CgmesCircuit
#     :param gc_model: gcdevCircuit
#     :param buses_to_skip:
#     :param skip_dc_import: If simplified HVDC modelling applied,
#                            DC buses are not imported into MultiCircuit model,
#                            but they are added to dc_bus_dict.
#     :param buses_to_skip: DCGround buses
#     :param logger: DataLogger
#     :param default_nominal_voltage: default nominal voltage for DC nodes since CGMES does not have any...
#     :return:
#     """
#
#     # dictionary relating the DCTopologicalNode uuid to the gcdev Bus (CalculationNode)
#     dc_bus_dict: Dict[str, gcdev.Bus] = dict()
#
#     for cgmes_elm in cgmes_model.cgmes_assets.DCTopologicalNode_list:
#
#         if cgmes_elm not in buses_to_skip:
#             gcdev_elm = gcdev.Bus(
#                 name=cgmes_elm.name,
#                 idtag=cgmes_elm.uuid,
#                 code=cgmes_elm.description,
#                 Vnom=default_nominal_voltage,
#                 active=True,
#                 is_slack=False,
#                 is_dc=True,
#                 area=None,  # areas and zones are not created from cgmes models
#                 zone=None,
#                 # substation=substat,
#                 # voltage_level=volt_lev,
#                 # country=country,
#                 # latitude=latitude,
#                 # longitude=longitude,
#                 # Vm0=vm,
#                 # Va0=va
#             )
#
#             if not skip_dc_import:
#                 gc_model.add_bus(gcdev_elm)
#
#             dc_bus_dict[gcdev_elm.idtag] = gcdev_elm
#
#     return dc_bus_dict


def get_gcdev_dc_connectivity_nodes(cgmes_model: CgmesCircuit,
                                    gc_model: MultiCircuit,
                                    skip_dc_import: bool,
                                    dc_bus_dict: Dict[str, gcdev.Bus],
                                    logger: DataLogger) -> Dict[str, gcdev.Bus]:
    """
    Convert the DC Nodes to DC Connectivity nodes

    :param cgmes_model: CgmesCircuit
    :param gc_model: gcdevCircuit
    :param skip_dc_import: If simplified HVDC modelling applied,
                           DCNodes are not imported into MultiCircuit model,
                           but they are added to dc_cn_node_dict.
    :param dc_bus_dict:
    :param logger: DataLogger
    :return:
    """
    # dictionary relating the ConnectivityNode uuid to the gcdev ConnectivityNode (DC)
    dc_cn_node_dict: Dict[str, gcdev.Bus] = dict()
    used_buses = set()
    for cgmes_elm in cgmes_model.cgmes_assets.DCNode_list:
        if cgmes_elm.DCTopologicalNode is not None:
            bus = dc_bus_dict.get(cgmes_elm.DCTopologicalNode.uuid, None)
        else:
            bus = None

        if bus is None:
            logger.add_warning(msg='No DC Bus found for DC Node.',
                               device=cgmes_elm.rdfid,
                               device_class=cgmes_elm.tpe,
                               comment="Maybe it belongs to a DCGround, that is not imported.")

        else:
            if bus not in used_buses:
                used_buses.add(bus)
                dc_cn_node_dict[bus.idtag] = bus

    return dc_cn_node_dict


def get_gcdev_dc_lines(cgmes_model: CgmesCircuit,
                       gcdev_model: MultiCircuit,
                       dc_bus_dict: Dict[str, gcdev.Bus],
                       device_to_terminal_dict: Dict[str, List[CGMES_TERMINAL]],
                       logger: DataLogger) -> None:
    """
    Convert the CGMES DCLineSegment to gcdev DC Line

    :param cgmes_model: CgmesCircuit
    :param gcdev_model: gcdevCircuit
    :param dc_bus_dict: Dict[str, gcdev.Bus]
    :param device_to_terminal_dict: Dict[str, Terminal]
    :param logger: DataLogger
    :return: None
    """
    TopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("TopologicalNode")
    DCTopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("DCTopologicalNode")

    # convert DC lines
    for cgmes_elm in cgmes_model.cgmes_assets.DCLineSegment_list:

        calc_nodes = find_associated_buses(cgmes_elm=cgmes_elm,
                                           device_to_terminal_dict=device_to_terminal_dict,
                                           bus_dict=dc_bus_dict,
                                           TopologicalNode_tpe=TopologicalNode_tpe,
                                           DCTopologicalNode_tpe=DCTopologicalNode_tpe,
                                           logger=logger,
                                           cgmes_version=cgmes_model.cgmes_version)

        resolved_calc_nodes, unique_calc_nodes, collapsed_terminals = normalize_terminal_bus_mappings(
            calc_nodes=calc_nodes,
            expected_count=2
        )
        if collapsed_terminals:
            log_collapsed_terminal_mapping_warning(logger=logger,
                                                   cgmes_elm=cgmes_elm,
                                                   raw_count=len(calc_nodes),
                                                   expected_count=2)

        if len(resolved_calc_nodes) == 2:
            bus_f = resolved_calc_nodes[0]
            bus_t = resolved_calc_nodes[1]

            if cgmes_elm.length is None:
                length = 1.0
                logger.add_error(msg='DCLineSegment length is missing.', device=cgmes_elm.rdfid,
                                 device_class=str(cgmes_elm.tpe))
            else:
                length = float(cgmes_elm.length)

            gcdev_elm = gcdev.DcLine(
                bus_from=bus_f,
                bus_to=bus_t,
                name=cgmes_elm.name,
                idtag=cgmes_elm.uuid,
                code=cgmes_elm.description,
                r=cgmes_elm.resistance,
                # rate=rate,
                active=get_cgmes_equipment_active_state(cgmes_elm),
                # r_fault = 0.0,
                # fault_pos = 0.5,
                length=length,
                # temp_base = 20,
                # temp_oper = 20,
                # alpha = 0.00330,
                # template = None,
                # contingency_factor = 1.0,
            )

            gcdev_model.add_dc_line(gcdev_elm)
        else:
            logger.add_error(msg='Not exactly two terminals',
                             device=cgmes_elm.rdfid,
                             device_class=cgmes_elm.tpe,
                             device_property="number of associated terminals",
                             value=f"raw={len(calc_nodes)}, unique={len(unique_calc_nodes)}",
                             expected_value=2)

    return


def get_gcdev_vsc_converters(cgmes_model: CgmesCircuit,
                             gcdev_model: MultiCircuit,
                             dc_bus_dict: Dict[str, gcdev.Bus],
                             dc_device_to_terminal_dict: Dict[str, List[CGMES_DC_TERMINAL]],
                             bus_dict: Dict[str, gcdev.Bus],
                             device_to_terminal_dict: Dict[str, List[CGMES_TERMINAL]],
                             logger: DataLogger) -> None:
    """
    Convert the CGMES VcConverter to gcdev VSConverter

    :param cgmes_model: CgmesCircuit
    :param gcdev_model: gcdevCircuit
    :param dc_bus_dict:
    :param dc_device_to_terminal_dict:
    :param bus_dict: Dict[str, gcdev.Bus]
    :param device_to_terminal_dict: Dict[str, Terminal]
    :param logger: DataLogger
    :return: None
    """
    TopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("TopologicalNode")
    DCTopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("DCTopologicalNode")

    for cgmes_elm in cgmes_model.cgmes_assets.VsConverter_list:

        bus_dc = find_associated_buses(cgmes_elm=cgmes_elm,
                                       device_to_terminal_dict=dc_device_to_terminal_dict,
                                       bus_dict=dc_bus_dict,
                                       TopologicalNode_tpe=TopologicalNode_tpe,
                                       DCTopologicalNode_tpe=DCTopologicalNode_tpe,
                                       logger=logger,
                                       cgmes_version=cgmes_model.cgmes_version)

        bus_ac = find_associated_buses(cgmes_elm=cgmes_elm,
                                       device_to_terminal_dict=device_to_terminal_dict,
                                       bus_dict=bus_dict,
                                       TopologicalNode_tpe=TopologicalNode_tpe,
                                       DCTopologicalNode_tpe=DCTopologicalNode_tpe,
                                       logger=logger,
                                       cgmes_version=cgmes_model.cgmes_version)

        bus_dc_resolved, bus_dc_unique, bus_dc_collapsed = normalize_terminal_bus_mappings(
            calc_nodes=bus_dc,
            expected_count=1
        )
        bus_ac_resolved, bus_ac_unique, bus_ac_collapsed = normalize_terminal_bus_mappings(
            calc_nodes=bus_ac,
            expected_count=1
        )
        if bus_dc_collapsed or bus_ac_collapsed:
            log_collapsed_terminal_mapping_warning(logger=logger,
                                                   cgmes_elm=cgmes_elm,
                                                   raw_count=max(len(bus_dc), len(bus_ac)),
                                                   expected_count=1)

        if len(bus_dc_resolved) == 1 and len(bus_ac_resolved) == 1:

            gcdev_elm = gcdev.VSC(
                bus_from=bus_dc_resolved[0],
                bus_to=bus_ac_resolved[0],
                name=cgmes_elm.name,
                idtag=cgmes_elm.uuid,
                code=cgmes_elm.description,
                active=get_cgmes_equipment_active_state(cgmes_elm),
                # alpha1 = 0.0001,
                # alpha2 = 0.015,
                # alpha3 = 0.2,
                control1=ConverterControlType.Pdc,
                control1_val=cgmes_elm.p,
                control2=ConverterControlType.Vm_dc,
                control2_val=1.0,
            )

            gcdev_model.add_vsc(gcdev_elm)

        else:
            logger.add_error(msg='VSC has to have one AC and one DC terminal',
                             device=cgmes_elm.rdfid,
                             device_class=cgmes_elm.tpe,
                             device_property="number of associated terminals",
                             value=(f"dc_raw={len(bus_dc)}, dc_unique={len(bus_dc_unique)}, "
                                    f"ac_raw={len(bus_ac)}, ac_unique={len(bus_ac_unique)}"),
                             expected_value=1,
                             comment="Import VSC from CGMES")

    return


def get_gcdev_hvdc_from_dcline_and_vscs(
        cgmes_model: CgmesCircuit,
        gcdev_model: MultiCircuit,
        dc_bus_dict: Dict[str, gcdev.Bus],
        dc_device_to_terminal_dict: Dict[str, List[CGMES_DC_TERMINAL]],
        bus_dict: Dict[str, gcdev.Bus],
        device_to_terminal_dict: Dict[str, List[CGMES_TERMINAL]],
        logger: DataLogger) -> None:
    """
    Convert the CGMES VcConverter to gcdev simplified HVDC lines
    (if required attributes for converting from VSC to VSC not given)

    :param cgmes_model: CgmesCircuit
    :param gcdev_model: gcdevCircuit
    :param dc_bus_dict:
    :param dc_device_to_terminal_dict:
    :param bus_dict: Dict[str, gcdev.Bus]
    :param device_to_terminal_dict: Dict[str, Terminal]
    :param logger: DataLogger
    :return: None
    """
    TopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("TopologicalNode")
    DCTopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("DCTopologicalNode")

    for dc_line_sgm in cgmes_model.cgmes_assets.DCLineSegment_list:
        # or in more general it is DCLine_list

        dc_buses = find_associated_buses(cgmes_elm=dc_line_sgm,
                                         device_to_terminal_dict=dc_device_to_terminal_dict,
                                         bus_dict=dc_bus_dict,
                                         TopologicalNode_tpe=TopologicalNode_tpe,
                                         DCTopologicalNode_tpe=DCTopologicalNode_tpe,
                                         logger=logger,
                                         cgmes_version=cgmes_model.cgmes_version)

        # get the cgmes terminal of this device
        dc_terminals = dc_device_to_terminal_dict.get(dc_line_sgm.uuid, None)

        # get the VSC-s connected to this dc_buses
        device_list = [device
                       for device, term in dc_device_to_terminal_dict.items()
                       if term[0] in dc_terminals]

        vsc_list = [vsc
                    for vsc in cgmes_model.cgmes_assets.VsConverter_list
                    if vsc.uuid in device_list]

        # ONLY one line + two converters structure can be simplified
        if len(vsc_list) != 2:
            logger.add_info(msg='Not exactly two VSCs for DCLine(Segment)! cannot be simplified',
                            device=dc_line_sgm.rdfid,
                            device_class=dc_line_sgm.tpe,
                            device_property="number of connected VSConverters",
                            value=len(vsc_list),
                            expected_value=2,
                            comment="get_gcdev_hvdc_from_dcline_and_vscs")

        else:
            # bus_from: AC side of VSC 1
            bus_from = find_associated_buses(cgmes_elm=vsc_list[0],
                                             device_to_terminal_dict=device_to_terminal_dict,
                                             bus_dict=bus_dict,
                                             TopologicalNode_tpe=TopologicalNode_tpe,
                                             DCTopologicalNode_tpe=DCTopologicalNode_tpe,
                                             logger=logger,
                                             cgmes_version=cgmes_model.cgmes_version)

            # bus_to: AC side of VSC 2
            bus_to = find_associated_buses(cgmes_elm=vsc_list[1],
                                           device_to_terminal_dict=device_to_terminal_dict,
                                           bus_dict=bus_dict,
                                           TopologicalNode_tpe=TopologicalNode_tpe,
                                           DCTopologicalNode_tpe=DCTopologicalNode_tpe,
                                           logger=logger,
                                           cgmes_version=cgmes_model.cgmes_version)

            bus_from_resolved, bus_from_unique, bus_from_collapsed = normalize_terminal_bus_mappings(
                calc_nodes=bus_from,
                expected_count=1
            )
            bus_to_resolved, bus_to_unique, bus_to_collapsed = normalize_terminal_bus_mappings(
                calc_nodes=bus_to,
                expected_count=1
            )

            if bus_from_collapsed:
                log_collapsed_terminal_mapping_warning(logger=logger,
                                                       cgmes_elm=vsc_list[0],
                                                       raw_count=len(bus_from),
                                                       expected_count=1)
            if bus_to_collapsed:
                log_collapsed_terminal_mapping_warning(logger=logger,
                                                       cgmes_elm=vsc_list[1],
                                                       raw_count=len(bus_to),
                                                       expected_count=1)

            if len(bus_from_resolved) != 1 or len(bus_to_resolved) != 1:
                logger.add_error(
                    msg='HVDC simplified import requires one AC terminal per VSC',
                    device=dc_line_sgm.rdfid,
                    device_class=dc_line_sgm.tpe,
                    device_property="number of associated terminals",
                    value=(f"from_raw={len(bus_from)}, from_unique={len(bus_from_unique)}, "
                           f"to_raw={len(bus_to)}, to_unique={len(bus_to_unique)}"),
                    expected_value=1,
                    comment="get_gcdev_hvdc_from_dcline_and_vscs"
                )
                continue

            rated_udc = getattr(vsc_list[0], 'ratedUdc', None)
            if rated_udc is None:
                rated_udc = 200.0

            Vset_f = vsc_list[0].targetUpcc / bus_from_resolved[0].Vnom  # if not found, 1.0 p.u.
            if Vset_f > 1.1:
                Vset_f = 1.1
            elif Vset_f < 0.9:
                Vset_f = 0.9

            Vset_t = vsc_list[1].targetUpcc / bus_to_resolved[0].Vnom
            if Vset_t > 1.1:
                Vset_t = 1.1
            elif Vset_t < 0.9:
                Vset_t = 0.9

            gcdev_elm = gcdev.HvdcLine(
                bus_from=bus_from_resolved[0],
                bus_to=bus_to_resolved[0],
                name=dc_line_sgm.name,
                idtag=dc_line_sgm.uuid,
                code=dc_line_sgm.description,
                active=get_cgmes_equipment_active_state(dc_line_sgm),
                Pset=abs(vsc_list[0].p),  # power of the VS converter
                # rate=rate,
                # rate of DCLine? or ratedP of Converter?
                # no Limit for DC terminal in XML
                Vset_f=Vset_f,  # if not found, 1.0 p.u.
                Vset_t=Vset_t,
                r=dc_line_sgm.resistance,
                dc_link_voltage=rated_udc,
            )

            gcdev_model.add_hvdc(gcdev_elm)

    return


def get_gcdev_branch_groups(cgmes_model: CgmesCircuit,
                            gcdev_model: MultiCircuit) -> None:
    """
    Convert to gcdev BranchGroups from CGMES
        Line, DCLIne, DCConverterUnit

    :param cgmes_model: CgmesCircuit
    :param gcdev_model: gcdevCircuit
    """
    # convert branch aggregations
    for cgmes_elm in cgmes_model.cgmes_assets.DCLine_list:
        gcdev_elm = gcdev.BranchGroup(
            name=cgmes_elm.name,
            idtag=cgmes_elm.uuid,
            code=cgmes_elm.description,
        )

        gcdev_model.add_branch_group(gcdev_elm)


# def get_gcdev_connectivity_nodes(cgmes_model: CgmesCircuit,
#                                  gcdev_model: MultiCircuit,
#                                  calc_node_dict: Dict[str, gcdev.Bus],
#                                  cn_look_up: Cn2BusBarLookup,
#                                  logger: DataLogger) -> Dict[str, gcdev.Bus]:
#     """
#     Convert the ConnectivityNodes to VeraGrid Buses
#
#     :param calc_node_dict: dictionary relating the TopologicalNode uuid to the gcdev CalculationNode
#              Dict[str, gcdev.Bus]
#     :param cgmes_model: CgmesCircuit
#     :param gcdev_model: gcdevCircuit
#     :param cn_look_up: CnLookUp
#     :param logger: DataLogger
#     :return: dictionary relating the ConnectivityNode uuid to the gcdev CalculationNode
#              Dict[str, gcdev.Bus]
#     """
#     # dictionary relating the ConnectivityNode uuid to the gcdev ConnectivityNode
#     cn_node_dict: Dict[str, gcdev.Bus] = dict()
#     used_buses = set()
#     for cgmes_elm in cgmes_model.cgmes_assets.ConnectivityNode_list:
#         bus: gcdev.Bus = calc_node_dict.get(cgmes_elm.TopologicalNode.uuid, None)
#         # vnom, vl = 10, None
#         # if bus is None:
#         #     logger.add_error(msg='No Bus found',
#         #                      device=cgmes_elm.rdfid,
#         #                      device_class=cgmes_elm.tpe)
#         #     default_bus = None
#         # else:
#         #     if bus not in used_buses:
#         #         default_bus = bus
#         #         used_buses.add(bus)
#         #     else:
#         #         default_bus = bus
#         #         # for the new TP processor, a CN always has to have a TP(/Bus)
#         #     vnom = bus.Vnom
#         #     vl = bus.voltage_level
#
#         gcdev_elm = gcdev.Bus(
#             idtag=cgmes_elm.uuid,
#             code=cgmes_elm.description,
#             name=cgmes_elm.name,
#         )
#
#         gcdev_model.add_bus(gcdev_elm)
#         cn_look_up.add_cn(gcdev_elm)
#         cn_node_dict[gcdev_elm.idtag] = gcdev_elm
#
#     return cn_node_dict


def get_gcdev_loads(cgmes_model: CgmesCircuit,
                    gcdev_model: MultiCircuit,
                    bus_dict: Dict[str, gcdev.Bus],
                    device_to_terminal_dict: Dict[str, List[CGMES_TERMINAL]],
                    logger: DataLogger) -> None:
    """
    Convert the CGMES loads to gcdev
    :param cgmes_model: CgmesCircuit
    :param gcdev_model: gcdevCircuit
    :param bus_dict: Dict[str, gcdev.Bus]
    :param device_to_terminal_dict: Dict[str, Terminal]
    :param logger:
    """
    TopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("TopologicalNode")
    DCTopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("DCTopologicalNode")

    # convert loads
    for device_list in [cgmes_model.cgmes_assets.EnergyConsumer_list,
                        cgmes_model.cgmes_assets.ConformLoad_list,
                        cgmes_model.cgmes_assets.NonConformLoad_list]:

        for cgmes_elm in device_list:
            calc_nodes = find_associated_buses(cgmes_elm=cgmes_elm,
                                               device_to_terminal_dict=device_to_terminal_dict,
                                               bus_dict=bus_dict,
                                               TopologicalNode_tpe=TopologicalNode_tpe,
                                               DCTopologicalNode_tpe=DCTopologicalNode_tpe,
                                               logger=logger,
                                               cgmes_version=cgmes_model.cgmes_version,
                                               prefer_connectivity_node=True)

            if len(calc_nodes) == 1:
                calc_node = calc_nodes[0]

                p, q, i_i, i_r, g, b = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
                if cgmes_elm.LoadResponse is not None:

                    if cgmes_elm.LoadResponse.exponentModel:
                        # Convert CGMES exponent model (P = P0·V^α) to ZIP via
                        # linear interpolation between the bracketing integer exponents:
                        #   α=0 → constant power, α=1 → constant current, α=2 → constant impedance.
                        # Exponents outside [0, 2] are clamped to the nearest endpoint.
                        lr = cgmes_elm.LoadResponse
                        p_exp = lr.pVoltageExponent if lr.pVoltageExponent is not None else 0.0
                        q_exp = lr.qVoltageExponent if lr.qVoltageExponent is not None else 0.0

                        def _exponent_to_zip(exp: float):
                            exp = max(0.0, min(2.0, exp))
                            if exp <= 1.0:
                                return 1.0 - exp, exp, 0.0  # (P, I, Z) weights
                            else:
                                return 0.0, 2.0 - exp, exp - 1.0

                        pp, pi, pz = _exponent_to_zip(p_exp)
                        qp, qi, qz = _exponent_to_zip(q_exp)

                        p = cgmes_elm.p * pp
                        q = cgmes_elm.q * qp
                        i_r = cgmes_elm.p * pi
                        i_i = cgmes_elm.q * qi
                        g = cgmes_elm.p * pz
                        b = cgmes_elm.q * qz

                        if p_exp != 0.0 or q_exp != 0.0:
                            logger.add_warning(
                                msg='Exponent load model approximated as ZIP',
                                device=cgmes_elm.rdfid,
                                device_class=cgmes_elm.tpe,
                                device_property="LoadResponse",
                                comment=f"pVoltageExponent={p_exp}, qVoltageExponent={q_exp}")
                    else:  # ZIP model
                        # :param P: Active power in MW
                        p = cgmes_elm.p * cgmes_elm.LoadResponse.pConstantPower
                        # :param Q: Reactive power in MVAr
                        q = cgmes_elm.q * cgmes_elm.LoadResponse.qConstantPower
                        # :param Ir: Real current in equivalent MW
                        i_r = cgmes_elm.p * cgmes_elm.LoadResponse.pConstantCurrent
                        # :param Ii: Imaginary current in equivalent MVAr
                        i_i = cgmes_elm.q * cgmes_elm.LoadResponse.qConstantCurrent
                        # :param G: Conductance in equivalent MW
                        g = cgmes_elm.p * cgmes_elm.LoadResponse.pConstantImpedance
                        # :param B: Susceptance in equivalent MVAr
                        b = cgmes_elm.q * cgmes_elm.LoadResponse.qConstantImpedance
                else:
                    p = cgmes_elm.p
                    q = cgmes_elm.q

                gcdev_elm = gcdev.Load(idtag=cgmes_elm.uuid,
                                       code=cgmes_elm.description,
                                       name=cgmes_elm.name,
                                       active=get_cgmes_equipment_active_state(cgmes_elm),
                                       P=p,
                                       Q=q,
                                       Ir=i_r,
                                       Ii=i_i,
                                       G=g,
                                       B=b)

                if isinstance(cgmes_elm, cgmes_model.assets.ConformLoad):
                    gcdev_elm.scalable = True
                else:
                    gcdev_elm.scalable = False

                gcdev_model.add_load(bus=calc_node, api_obj=gcdev_elm)

            else:
                logger.add_error(msg='Not exactly one terminal',
                                 device=cgmes_elm.rdfid,
                                 device_class=cgmes_elm.tpe,
                                 device_property="number of associated terminals",
                                 value=len(calc_nodes),
                                 expected_value=1)


def get_gcdev_generators(cgmes_model: CgmesCircuit,
                         gcdev_model: MultiCircuit,
                         bus_dict: Dict[str, gcdev.Bus],
                         device_to_terminal_dict: Dict[str, List[CGMES_TERMINAL]],
                         logger: DataLogger) -> None:
    """
    Convert the CGMES generators to gcdev
    :param cgmes_model: CgmesCircuit
    :param gcdev_model: gcdevCircuit
    :param bus_dict: Dict[str, gcdev.Bus]
    :param device_to_terminal_dict: Dict[str, Terminal]
    :param logger: Logger object
    """
    TopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("TopologicalNode")
    DCTopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("DCTopologicalNode")

    # add generation technologies
    general_tech = gcdev.Technology(idtag='', code='', name='General')
    thermal_tech = gcdev.Technology(idtag='', code='', name='Thermal')
    hydro_tech = gcdev.Technology(idtag='', code='', name='Hydro')
    solar_tech = gcdev.Technology(idtag='', code='', name='Solar')
    wind_tech_on = gcdev.Technology(idtag='', code='', name='Wind Onshore')
    wind_tech_off = gcdev.Technology(idtag='', code='', name='Wind Offshore')
    nuclear_tech = gcdev.Technology(idtag='', code='', name='Nuclear')

    gcdev_model.add_technology(general_tech)
    gcdev_model.add_technology(thermal_tech)
    gcdev_model.add_technology(hydro_tech)
    gcdev_model.add_technology(solar_tech)
    gcdev_model.add_technology(wind_tech_on)
    gcdev_model.add_technology(wind_tech_off)
    gcdev_model.add_technology(nuclear_tech)

    tech_dict = {
        "GeneratingUnit": general_tech,
        "ThermalGeneratingUnit": thermal_tech,
        "HydroGeneratingUnit": hydro_tech,
        "SolarGeneratingUnit": solar_tech,
        "WindGeneratingUnit": [wind_tech_on, wind_tech_off],
        "NuclearGeneratingUnit": nuclear_tech,
    }

    # plants_dict: Dict[str, gcdev.aggregation.Plant] = dict()

    # convert generators
    for device_list in [cgmes_model.cgmes_assets.SynchronousMachine_list]:
        for cgmes_elm in device_list:
            calc_nodes = find_associated_buses(cgmes_elm=cgmes_elm,
                                               device_to_terminal_dict=device_to_terminal_dict,
                                               bus_dict=bus_dict,
                                               TopologicalNode_tpe=TopologicalNode_tpe,
                                               DCTopologicalNode_tpe=DCTopologicalNode_tpe,
                                               logger=logger,
                                               cgmes_version=cgmes_model.cgmes_version)

            if len(calc_nodes) == 1:
                calc_node = calc_nodes[0]

                if cgmes_elm.GeneratingUnit is not None:

                    v_set, is_controlled, controlled_bus, controlled_cn = (
                        get_regulating_control_params(
                            cgmes_elm=cgmes_elm,
                            cgmes_enums=cgmes_enums,
                            bus_dict=bus_dict,
                            TopologicalNode_tpe=TopologicalNode_tpe,
                            DCTopologicalNode_tpe=DCTopologicalNode_tpe,
                            logger=logger,
                            prefer_connectivity_node=(cgmes_model.cgmes_version == CGMESVersions.v3_0_0)
                        ))

                    if cgmes_elm.p != 0.0:
                        pf = np.cos(np.arctan(cgmes_elm.q / cgmes_elm.p))
                    else:
                        pf = 1.0  # default is 0.8 in gc
                        logger.add_warning(msg='GeneratingUnit p is 0.',
                                           device=cgmes_elm.rdfid,
                                           device_class=cgmes_elm.tpe,
                                           device_property="p",
                                           value='0')

                    technology = tech_dict.get(cgmes_elm.GeneratingUnit.tpe, None)
                    if cgmes_elm.GeneratingUnit.tpe == "WindGeneratingUnit":
                        if cgmes_elm.GeneratingUnit.windGenUnitType == cgmes_enums.WindGenUnitKind.onshore:
                            technology = technology[0]
                        else:
                            technology = technology[1]

                    gcdev_elm = gcdev.Generator(idtag=cgmes_elm.uuid,
                                                code=cgmes_elm.description,
                                                name=cgmes_elm.name,
                                                active=get_cgmes_equipment_active_state(cgmes_elm),
                                                Snom=cgmes_elm.ratedS,
                                                P=-cgmes_elm.p,
                                                Pmin=cgmes_elm.GeneratingUnit.minOperatingP,
                                                Pmax=cgmes_elm.GeneratingUnit.maxOperatingP,
                                                power_factor=pf,
                                                Qmax=cgmes_elm.maxQ if cgmes_elm.maxQ is not None else 9999.0,
                                                Qmin=cgmes_elm.minQ if cgmes_elm.minQ is not None else -9999.0,
                                                vset=v_set,
                                                is_controlled=is_controlled,
                                                )
                    gcdev_elm.control_bus = controlled_bus

                    gcdev_model.add_generator(bus=calc_node, api_obj=gcdev_elm)

                    if technology:
                        gcdev_elm.technologies.append(gcdev.Association(api_object=technology, value=1.0))
                else:
                    logger.add_error(msg='SynchronousMachine has no generating unit',
                                     device=cgmes_elm.rdfid,
                                     device_class=cgmes_elm.tpe,
                                     device_property="GeneratingUnit",
                                     value='None')
            else:
                logger.add_error(msg='Not exactly one terminal',
                                 device=cgmes_elm.rdfid,
                                 device_class=cgmes_elm.tpe,
                                 device_property="number of associated terminals",
                                 value=len(calc_nodes),
                                 expected_value=1)


def get_gcdev_external_grids(cgmes_model: CgmesCircuit,
                             gcdev_model: MultiCircuit,
                             calc_node_dict: Dict[str, gcdev.Bus],
                             device_to_terminal_dict: Dict[str, List[CGMES_TERMINAL]],
                             logger: DataLogger) -> None:
    """
    Convert the CGMES loads to gcdev
    :param cgmes_model: CgmesCircuit
    :param gcdev_model: gcdevCircuit
    :param calc_node_dict: Dict[str, gcdev.Bus]
    :param device_to_terminal_dict: Dict[str, Terminal]
    :param logger:
    """
    TopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("TopologicalNode")
    DCTopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("DCTopologicalNode")

    # Import both equivalent and explicit external-network boundary devices.
    external_device_lists = [cgmes_model.cgmes_assets.EquivalentInjection_list]
    external_network_injection_list = getattr(cgmes_model.cgmes_assets, "ExternalNetworkInjection_list", None)
    if external_network_injection_list is not None:
        external_device_lists.append(external_network_injection_list)

    for device_list in external_device_lists:
        for cgmes_elm in device_list:
            calc_nodes = find_associated_buses(cgmes_elm=cgmes_elm,
                                               device_to_terminal_dict=device_to_terminal_dict,
                                               bus_dict=calc_node_dict,
                                               TopologicalNode_tpe=TopologicalNode_tpe,
                                               DCTopologicalNode_tpe=DCTopologicalNode_tpe,
                                               logger=logger,
                                               cgmes_version=cgmes_model.cgmes_version)

            if len(calc_nodes) == 1:
                calc_node = calc_nodes[0]

                mode = ExternalGridMode.PQ
                vm = 1.0

                if hasattr(cgmes_elm, "regulationCapability") and getattr(cgmes_elm, "regulationCapability", False):
                    regulation_target = getattr(cgmes_elm, "regulationTarget", None)
                    if regulation_target is not None and calc_node.Vnom > 0.0:
                        vm = float(regulation_target) / float(calc_node.Vnom)
                        vm = sanitize_voltage_setpoint(v_set=vm,
                                                       cgmes_elm=cgmes_elm,
                                                       logger=logger)
                        mode = ExternalGridMode.VD
                    else:
                        logger.add_warning(
                            msg='EquivalentInjection voltage regulation ignored due to missing target or nominal voltage',
                            device=cgmes_elm.rdfid,
                            device_class=cgmes_elm.tpe,
                            device_property="regulationTarget",
                            value=regulation_target,
                            expected_value="finite target and Bus.Vnom > 0")
                elif getattr(cgmes_elm, "controlEnabled", False):
                    regulating_control = getattr(cgmes_elm, "RegulatingControl", None)
                    if regulating_control is not None:
                        target_value = getattr(regulating_control, "targetValue", None)
                        if target_value is not None and calc_node.Vnom > 0.0:
                            vm = float(target_value) / float(calc_node.Vnom)
                            vm = sanitize_voltage_setpoint(v_set=vm,
                                                           cgmes_elm=cgmes_elm,
                                                           logger=logger)
                            mode = ExternalGridMode.VD
                        else:
                            logger.add_warning(
                                msg='ExternalNetworkInjection voltage regulation ignored due to missing target or nominal voltage',
                                device=cgmes_elm.rdfid,
                                device_class=cgmes_elm.tpe,
                                device_property="RegulatingControl.targetValue",
                                value=target_value,
                                expected_value="finite target and Bus.Vnom > 0")
                    else:
                        logger.add_warning(
                            msg='ExternalNetworkInjection controlEnabled but RegulatingControl is missing',
                            device=cgmes_elm.rdfid,
                            device_class=cgmes_elm.tpe,
                            device_property="RegulatingControl",
                            value='None')
                elif getattr(cgmes_elm, "referencePriority", 0) == 1:
                    mode = ExternalGridMode.VD

                gcdev_elm = gcdev.ExternalGrid(idtag=cgmes_elm.uuid,
                                               code=cgmes_elm.description,
                                               name=cgmes_elm.name,
                                               active=get_cgmes_equipment_active_state(cgmes_elm),
                                               mode=mode,
                                               Vm=vm,
                                               P=cgmes_elm.p,
                                               Q=cgmes_elm.q)

                gcdev_model.add_external_grid(bus=calc_node, api_obj=gcdev_elm)
            else:
                logger.add_error(msg='Not exactly one terminal',
                                 device=cgmes_elm.rdfid,
                                 device_class=cgmes_elm.tpe,
                                 device_property="number of associated terminals",
                                 value=len(calc_nodes),
                                 expected_value=1)


def get_gcdev_ac_lines(cgmes_model: CgmesCircuit,
                       gcdev_model: MultiCircuit,
                       bus_dict: Dict[str, gcdev.Bus],
                       device_to_terminal_dict: Dict[str, List[CGMES_TERMINAL]],
                       logger: DataLogger,
                       Sbase: float) -> None:
    """
    Convert the CGMES ac lines to gcdev
    :param cgmes_model: CgmesCircuit
    :param gcdev_model: gcdevCircuit
    :param bus_dict: Dict[str, gcdev.Bus]
    :param device_to_terminal_dict: Dict[str, Terminal]
    :param logger: DataLogger
    :param Sbase: system base power in MVA
    :return: None
    """

    # build the ratings dictionary
    (patl_dict, tatl_900_dict, tatl_60_dict) = build_cgmes_limit_dicts(
        cgmes_model=cgmes_model,
        device_type=cgmes_model.assets.ACLineSegment,
        logger=logger
    )
    # # build the ratings dictionary
    # rates_dict = dict()
    # acline_type = cgmes_model.get_class_type("ACLineSegment")
    # for e in cgmes_model.cgmes_assets.CurrentLimit_list:
    #     if e.OperationalLimitSet is None:
    #         logger.add_error(msg='OperationalLimitSet missing.',
    #                          device=e.rdfid,
    #                          device_class=e.tpe,
    #                          device_property="OperationalLimitSet",
    #                          value="None")
    #         continue
    #     if not isinstance(e.OperationalLimitSet, str):
    #         if isinstance(e.OperationalLimitSet, list):
    #             for ols in e.OperationalLimitSet:
    #                 if isinstance(ols.Terminal.ConductingEquipment, acline_type):
    #                     branch_id = ols.Terminal.ConductingEquipment.uuid
    #                     rates_dict[branch_id] = e.value
    #         else:
    #             if isinstance(e.OperationalLimitSet.Terminal.ConductingEquipment, acline_type):
    #                 branch_id = e.OperationalLimitSet.Terminal.ConductingEquipment.uuid
    #                 rates_dict[branch_id] = e.value

    TopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("TopologicalNode")
    DCTopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("DCTopologicalNode")

    # convert ac lines
    for device_list in [cgmes_model.cgmes_assets.ACLineSegment_list]:
        for cgmes_elm in device_list:
            calc_nodes = find_associated_buses(cgmes_elm=cgmes_elm,
                                               device_to_terminal_dict=device_to_terminal_dict,
                                               bus_dict=bus_dict,
                                               TopologicalNode_tpe=TopologicalNode_tpe,
                                               DCTopologicalNode_tpe=DCTopologicalNode_tpe,
                                               logger=logger,
                                               cgmes_version=cgmes_model.cgmes_version)

            resolved_calc_nodes, unique_calc_nodes, collapsed_terminals = normalize_terminal_bus_mappings(
                calc_nodes=calc_nodes,
                expected_count=2
            )
            if collapsed_terminals:
                log_collapsed_terminal_mapping_warning(logger=logger,
                                                       cgmes_elm=cgmes_elm,
                                                       raw_count=len(calc_nodes),
                                                       expected_count=2)

            if len(resolved_calc_nodes) == 2:
                calc_node_f = resolved_calc_nodes[0]
                calc_node_t = resolved_calc_nodes[1]

                # get per unit values
                r, x, g, b, r0, x0, g0, b0 = get_pu_values_ac_line_segment(ac_line_segment=cgmes_elm, logger=logger,
                                                                           Sbase=Sbase)

                normal_rate_mva = patl_dict.get(cgmes_elm.uuid, 9999.0)
                # min PATL rate in MW/MVA
                cont_rate_mva = tatl_900_dict.get(cgmes_elm.uuid, 9999.0)
                # min TATL900 rate in MW/MVA

                if cont_rate_mva != 9999.0:
                    cont_factor = cont_rate_mva / normal_rate_mva if normal_rate_mva != 0.0 else 1.0
                else:
                    cont_factor = 1.0

                prot_rate_mva = tatl_60_dict.get(cgmes_elm.uuid, 9999.0)
                # min TATL60 rate in MW/MVA
                if prot_rate_mva != 9999.0:
                    prot_factor = prot_rate_mva / normal_rate_mva if normal_rate_mva != 0.0 else 1.4
                else:
                    prot_factor = 1.4

                if cgmes_elm.length is None:
                    length = 1.0
                    logger.add_error(msg='Length missing.', device=cgmes_elm.rdfid, device_class=str(cgmes_elm.tpe))
                else:
                    length = float(cgmes_elm.length)

                gcdev_elm = gcdev.Line(
                    idtag=cgmes_elm.uuid,
                    code=cgmes_elm.description,
                    name=cgmes_elm.name,
                    active=get_cgmes_equipment_active_state(cgmes_elm),
                    bus_from=calc_node_f,
                    bus_to=calc_node_t,
                    r=r,
                    x=x,
                    b=b,
                    r0=r0,
                    x0=x0,
                    b0=b0,
                    rate=normal_rate_mva,
                    contingency_factor=cont_factor,
                    protection_rating_factor=prot_factor,
                    length=length,
                )

                has_unknown_bus_voltage: bool = calc_node_f.Vnom <= 0.0 or calc_node_t.Vnom <= 0.0
                if has_unknown_bus_voltage:
                    logger.add_warning(
                        msg='ACLineSegment kept as line because one associated bus has unknown nominal voltage',
                        device=cgmes_elm.rdfid,
                        device_class=cgmes_elm.tpe,
                        value=min(calc_node_f.Vnom, calc_node_t.Vnom),
                        expected_value=max(calc_node_f.Vnom, calc_node_t.Vnom),
                    )

                    if gcdev_model.time_profile is not None:
                        gcdev_elm.ensure_profiles_exist(gcdev_model.time_profile)
                    else:
                        pass

                    gcdev_model.lines.append(gcdev_elm)
                    gcdev_elm.set_var_factory(gcdev_model.var_factory)
                else:
                    gcdev_model.add_line(gcdev_elm, logger=logger)
            else:
                logger.add_error(msg='Not exactly two terminals',
                                 device=cgmes_elm.rdfid,
                                 device_class=cgmes_elm.tpe,
                                 device_property="number of associated terminals",
                                 value=f"raw={len(calc_nodes)}, unique={len(unique_calc_nodes)}",
                                 expected_value=2)


def get_gcdev_series_compensators(cgmes_model: CgmesCircuit,
                                  gcdev_model: MultiCircuit,
                                  bus_dict: Dict[str, gcdev.Bus],
                                  device_to_terminal_dict: Dict[str, List[CGMES_TERMINAL]],
                                  logger: DataLogger,
                                  Sbase: float) -> None:
    """
    Convert CGMES SeriesCompensator devices to VeraGrid SeriesReactance branches.

    :param cgmes_model: CgmesCircuit
    :param gcdev_model: gcdevCircuit
    :param bus_dict: Dict[str, gcdev.Bus]
    :param device_to_terminal_dict: Dict[str, Terminal]
    :param logger: DataLogger
    :param Sbase: system base power in MVA
    :return: None
    """
    TopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("TopologicalNode")
    DCTopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("DCTopologicalNode")

    (patl_dict, tatl_900_dict, tatl_60_dict) = build_cgmes_limit_dicts(
        cgmes_model=cgmes_model,
        device_type=cgmes_model.assets.SeriesCompensator,
        logger=logger
    )

    for cgmes_elm in cgmes_model.cgmes_assets.SeriesCompensator_list:
        calc_nodes = find_associated_buses(cgmes_elm=cgmes_elm,
                                           device_to_terminal_dict=device_to_terminal_dict,
                                           bus_dict=bus_dict,
                                           TopologicalNode_tpe=TopologicalNode_tpe,
                                           DCTopologicalNode_tpe=DCTopologicalNode_tpe,
                                           logger=logger,
                                           cgmes_version=cgmes_model.cgmes_version)

        resolved_calc_nodes, unique_calc_nodes, collapsed_terminals = normalize_terminal_bus_mappings(
            calc_nodes=calc_nodes,
            expected_count=2
        )
        if collapsed_terminals:
            log_collapsed_terminal_mapping_warning(logger=logger,
                                                   cgmes_elm=cgmes_elm,
                                                   raw_count=len(calc_nodes),
                                                   expected_count=2)

        if len(resolved_calc_nodes) == 2:
            calc_node_f = resolved_calc_nodes[0]
            calc_node_t = resolved_calc_nodes[1]

            if cgmes_elm.BaseVoltage is not None and cgmes_elm.BaseVoltage.nominalVoltage is not None:
                v_nom = float(cgmes_elm.BaseVoltage.nominalVoltage)
            elif calc_node_f.Vnom > 0.0:
                v_nom = float(calc_node_f.Vnom)
            elif calc_node_t.Vnom > 0.0:
                v_nom = float(calc_node_t.Vnom)
            else:
                v_nom = 0.0

            if v_nom > 0.0:
                z_base = (v_nom * v_nom) / Sbase
                r = float(cgmes_elm.r) / z_base if cgmes_elm.r is not None else 1e-20
                x = float(cgmes_elm.x) / z_base if cgmes_elm.x is not None else 1e-20
                r0 = float(cgmes_elm.r0) / z_base if cgmes_elm.r0 is not None else 1e-20
                x0 = float(cgmes_elm.x0) / z_base if cgmes_elm.x0 is not None else 1e-20
            else:
                logger.add_warning(
                    msg='SeriesCompensator nominal voltage is missing or invalid; default p.u. values used',
                    device=cgmes_elm.rdfid,
                    device_class=cgmes_elm.tpe,
                    device_property="BaseVoltage.nominalVoltage",
                    value=v_nom,
                    expected_value='> 0.0')
                r = 1e-20
                x = 1e-20
                r0 = 1e-20
                x0 = 1e-20

            rates = [patl_dict.get(cgmes_elm.uuid, 9999.0),
                     tatl_900_dict.get(cgmes_elm.uuid, 9999.0),
                     tatl_60_dict.get(cgmes_elm.uuid, 9999.0)]
            rates_pos = [val for val in rates if val > 0.0]
            if len(rates_pos) > 0:
                rate = min(rates_pos)
            else:
                rate = 9999.0

            gcdev_elm = gcdev.SeriesReactance(bus_from=calc_node_f,
                                              bus_to=calc_node_t,
                                              idtag=cgmes_elm.uuid,
                                              code=cgmes_elm.description,
                                              name=cgmes_elm.name,
                                              active=get_cgmes_equipment_active_state(cgmes_elm),
                                              rate=rate,
                                              r=r,
                                              x=x,
                                              r0=r0,
                                              x0=x0)

            gcdev_model.add_series_reactance(obj=gcdev_elm)
        else:
            logger.add_error(msg='Not exactly two terminals',
                             device=cgmes_elm.rdfid,
                             device_class=cgmes_elm.tpe,
                             device_property="number of associated terminals",
                             value=f"raw={len(calc_nodes)}, unique={len(unique_calc_nodes)}",
                             expected_value=2)


# def get_tap_changer_values(windings):
#     """
#     Get Tap Changer values from one of the given windings (that is not None).
#
#     :param windings: List of transformer windings.
#     :return:
#     """
#     tap_module: float = 1.0
#     total_positions, neutral_pos, normal, tap_step, dV = 0, 0, 0, 0, 0.0
#     tc_type = TapChangerTypes.NoRegulation
#
#     for winding in windings:
#         rtc = winding.RatioTapChanger
#         if rtc is not None:
#             total_positions = rtc.highStep - rtc.lowStep + 1    # lowStep generally negative
#             neutral_pos = rtc.neutralStep - rtc.lowStep
#             normal = rtc.normalStep - rtc.lowStep
#             dV = round(rtc.stepVoltageIncrement / 100, 6)
#             # tc._tap_position = neutral_position  # index with respect to the neutral position = Step from SSH
#             # set after initialisation
#             tap_step = rtc.step
#             tap_module = round(1 + (rtc.step - rtc.neutralStep) * dV, 6)
#
#             # Control from Control object
#             if (getattr(rtc, 'TapChangerControl', None) and
#                     rtc.TapChangerControl.mode == cgmes_enums.RegulatingControlModeKind.voltage):
#                 tc_type = TapChangerTypes.VoltageRegulation
#
#             # tculControlMode is not relevant
#             # if (hasattr(rtc, 'tculControlMode') and
#             #         rtc.tculControlMode == cgmes_enums.TransformerControlMode.volt):
#             #     tc_type = TapChangerTypes.VoltageRegulation
#
#         else:
#             continue
#     return tap_module, total_positions, neutral_pos, normal, dV, tc_type, tap_step

#
# def set_tap_changer_values(windings,
#                            gcdev_trafo: gcdev.Transformer2W) -> None:
#     """
#     Get Tap Changer values from one of the given windings (that is not None).
#
#     :param gcdev_trafo: VeraGrid transformer
#     :param windings: List of transformer windings.
#     :return:
#     """
#     total_positions, neutral_pos, normal, tap_step, dV = 0, 0, 0, 0, 0.0
#     tc_type = TapChangerTypes.NoRegulation
#
#     for winding in windings:
#         rtc = winding.RatioTapChanger
#         if rtc is not None:
#             # Control from Control object
#             if (getattr(rtc, 'TapChangerControl', None) and
#                     rtc.TapChangerControl.mode == cgmes_enums.RegulatingControlModeKind.voltage):
#                 tc_type = TapChangerTypes.VoltageRegulation
#
#             gcdev_trafo.tap_changer.init_from_cgmes(
#                 low=rtc.lowStep,
#                 high=rtc.highStep,
#                 normal=rtc.normalStep,
#                 neutral=rtc.neutralStep,
#                 stepVoltageIncrement=rtc.stepVoltageIncrement,
#                 step=rtc.step,
#                 asymmetry_angle=90,
#                 tc_type=tc_type)
#
#         ptc = winding.PhaseTapChanger
#         # if isinstance(ptc, cgmes_model.get_class_type("PhaseTapChangerSymmetrical")):
#         if ptc is not None:
#             # Control from Control object
#             if (getattr(ptc, 'TapChangerControl', None) and
#                     ptc.TapChangerControl.mode == cgmes_enums.RegulatingControlModeKind.voltage):
#                 tc_type = TapChangerTypes.VoltageRegulation
#
#             gcdev_trafo.tap_changer.init_from_cgmes(
#                 low=ptc.lowStep,
#                 high=ptc.highStep,
#                 normal=ptc.normalStep,
#                 neutral=ptc.neutralStep,
#                 stepVoltageIncrement=ptc.voltageStepIncrement,
#                 step=ptc.step,
#                 asymmetry_angle=90,
#                 tc_type=tc_type)
#
#     return


def get_gcdev_ac_transformers(cgmes_model: CgmesCircuit,
                              gcdev_model: MultiCircuit,
                              bus_dict: Dict[str, gcdev.Bus],
                              device_to_terminal_dict: Dict[str, List[CGMES_TERMINAL]],
                              logger: DataLogger,
                              Sbase: float) -> None:
    """
    Convert the CGMES ac lines to gcdev
    :param cgmes_model: CgmesCircuit
    :param gcdev_model: gcdevCircuit
    :param bus_dict: Dict[str, gcdev.Bus]
    :param device_to_terminal_dict: Dict[str, Terminal]
    :param logger: DataLogger
    :param Sbase: system base power in MVA
    :return: None
    """

    TopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("TopologicalNode")
    DCTopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("DCTopologicalNode")

    # build the ratings dictionary
    trafo_type = cgmes_model.assets.PowerTransformer
    (patl_dict, tatl_900_dict, tatl_60_dict) = build_cgmes_limit_dicts(cgmes_model, trafo_type, logger)

    # convert transformers
    for device_list in [cgmes_model.cgmes_assets.PowerTransformer_list]:

        for cgmes_elm in device_list:

            windings: List[CGMES_POWER_TRANSFORMER_END | None] = [None, None, None]
            for pte in get_power_transformer_ends(power_transformer=cgmes_elm, cgmes_model=cgmes_model):
                if hasattr(pte, "endNumber"):
                    i = getattr(pte, "endNumber")
                    if i is not None:
                        windings[i - 1] = pte
            windings: List[CGMES_POWER_TRANSFORMER_END | None] = [x for x in windings if x is not None]

            normal_rate_mva = patl_dict.get(cgmes_elm.uuid, 9999.0)  # min PATL rate in MW/MVA
            cont_rate_mva = tatl_900_dict.get(cgmes_elm.uuid, 9999.0)  # min TATL900 rate in MW/MVA
            if cont_rate_mva != 9999.0:
                cont_factor = cont_rate_mva / normal_rate_mva if normal_rate_mva != 0 else 1.4
            else:
                cont_factor = 1.0
            prot_rate_mva = tatl_60_dict.get(cgmes_elm.uuid, 9999.0)  # min TATL60 rate in MW/MVA
            if prot_rate_mva != 9999.0:
                prot_factor = prot_rate_mva / normal_rate_mva if normal_rate_mva != 0 else 1.4
            else:
                prot_factor = 1.4

            calc_nodes = find_associated_buses(cgmes_elm=cgmes_elm,
                                               device_to_terminal_dict=device_to_terminal_dict,
                                               bus_dict=bus_dict,
                                               TopologicalNode_tpe=TopologicalNode_tpe,
                                               DCTopologicalNode_tpe=DCTopologicalNode_tpe,
                                               logger=logger,
                                               cgmes_version=cgmes_model.cgmes_version)

            if len(windings) == 2:
                resolved_calc_nodes, unique_calc_nodes, collapsed_terminals = normalize_terminal_bus_mappings(
                    calc_nodes=calc_nodes,
                    expected_count=2
                )
                if collapsed_terminals:
                    log_collapsed_terminal_mapping_warning(logger=logger,
                                                           cgmes_elm=cgmes_elm,
                                                           raw_count=len(calc_nodes),
                                                           expected_count=2)

                if len(resolved_calc_nodes) == 2:
                    calc_node_f = resolved_calc_nodes[0]
                    calc_node_t = resolved_calc_nodes[1]

                    HV = windings[0].ratedU
                    LV = windings[1].ratedU

                    # get per unit values
                    r, x, g, b, r0, x0, g0, b0 = get_pu_values_power_transformer(cgmes_elm,
                                                                                 Sbase,
                                                                                 cgmes_model=cgmes_model)
                    rated_s = windings[0].ratedS

                    gcdev_elm = gcdev.Transformer2W(
                        idtag=cgmes_elm.uuid,
                        code=cgmes_elm.description,
                        name=cgmes_elm.name,
                        active=get_cgmes_equipment_active_state(cgmes_elm),
                        bus_from=calc_node_f,
                        bus_to=calc_node_t,
                        nominal_power=rated_s,
                        HV=HV,
                        LV=LV,
                        r=r,
                        x=x,
                        g=g,
                        b=b,
                        r0=r0,
                        x0=x0,
                        g0=g0,
                        b0=b0,
                        # tap_module=tap_m,
                        # # tap_phase=0.0,
                        # # tap_module_control_mode=,  # leave fixed
                        # # tap_angle_control_mode=,
                        # tc_total_positions=total_pos,
                        # tc_neutral_position=neutral_pos,
                        # tc_normal_position=normal_pos,
                        # tc_dV=dV,
                        # # tc_asymmetry_angle = 90,
                        # tc_type=tc_type,
                        rate=normal_rate_mva,
                        contingency_factor=cont_factor,
                        protection_rating_factor=prot_factor,
                    )

                    # # get Tap data from CGMES
                    # tap_m, total_pos, neutral_pos, normal_pos, dV, tc_type, tap_pos = get_tap_changer_values(windings)

                    # # TAP Changer INIT from CGMES
                    # set_tap_changer_values(windings=windings,
                    #                        gcdev_trafo=gcdev_elm)

                    gcdev_model.add_transformer2w(gcdev_elm)
                else:
                    logger.add_error(msg='Not exactly two terminals',
                                     device=cgmes_elm.rdfid,
                                     device_class=cgmes_elm.tpe,
                                     device_property="number of associated terminals",
                                     value=f"raw={len(calc_nodes)}, unique={len(unique_calc_nodes)}",
                                     expected_value="2")

            elif len(windings) == 3:
                resolved_calc_nodes, unique_calc_nodes, collapsed_terminals = normalize_terminal_bus_mappings(
                    calc_nodes=calc_nodes,
                    expected_count=3
                )
                if collapsed_terminals:
                    log_collapsed_terminal_mapping_warning(logger=logger,
                                                           cgmes_elm=cgmes_elm,
                                                           raw_count=len(calc_nodes),
                                                           expected_count=3)

                if len(resolved_calc_nodes) == 3:

                    # sort the windings to match the nominal buses voltage...
                    # The problem is that the windings order might not be the same as the buses order
                    # hence, there might be large virtual taps
                    windings2 = [None, None, None]
                    winding_used = [False, False, False]
                    for i in range(3):
                        v_bus = resolved_calc_nodes[i].Vnom
                        d_min = 1e20
                        j_min = -1
                        for j in range(3):
                            if not winding_used[j]:
                                v_winding = windings[j].ratedU
                                d = abs(v_bus - v_winding)
                                if d < d_min:
                                    d_min = d
                                    j_min = j
                            else:
                                pass

                        if j_min == -1:
                            j_min = i
                        else:
                            pass

                        windings2[i] = windings[j_min]
                        winding_used[j_min] = True

                        if i != j_min:
                            logger.add_error(
                                msg='The winding is not in the right order with respect to the transformer TopologicalNodes',
                                device=windings[j_min].uuid, device_class=windings[j_min].tpe
                            )

                    windings = windings2

                    # assign values
                    r12, r23, r31, x12, x23, x31 = get_pu_values_power_transformer3w(cgmes_elm,
                                                                                     Sbase,
                                                                                     cgmes_model=cgmes_model)

                    gcdev_elm = gcdev.Transformer3W(idtag=cgmes_elm.uuid,
                                                    code=cgmes_elm.description,
                                                    name=cgmes_elm.name,
                                                    active=get_cgmes_equipment_active_state(cgmes_elm),
                                                    bus1=resolved_calc_nodes[0],
                                                    bus2=resolved_calc_nodes[1],
                                                    bus3=resolved_calc_nodes[2],
                                                    w1_idtag=windings[0].uuid,
                                                    w2_idtag=windings[1].uuid,
                                                    w3_idtag=windings[2].uuid,
                                                    V1=windings[0].ratedU,
                                                    V2=windings[1].ratedU,
                                                    V3=windings[2].ratedU,
                                                    # r12=r12, r23=r23, r31=r31,
                                                    # x12=x12, x23=x23, x31=x31,
                                                    rate12=windings[0].ratedS,
                                                    rate23=windings[1].ratedS,
                                                    rate31=windings[2].ratedS, )

                    r1, x1, g1, b1, r01, x01, g01, b01 = get_pu_values_power_transformer_end(windings[0], Sbase)
                    gcdev_elm.winding1.R = r1
                    gcdev_elm.winding1.X = x1
                    gcdev_elm.winding1.G = g1
                    gcdev_elm.winding1.B = b1
                    gcdev_elm.winding1.R0 = r01
                    gcdev_elm.winding1.X0 = x01
                    gcdev_elm.winding1.G0 = g01
                    gcdev_elm.winding1.B0 = b01
                    gcdev_elm.winding1.rate = float(windings[0].ratedS)

                    r2, x2, g2, b2, r02, x02, g02, b02 = get_pu_values_power_transformer_end(windings[1], Sbase)
                    gcdev_elm.winding2.R = r2
                    gcdev_elm.winding2.X = x2
                    gcdev_elm.winding2.G = g2
                    gcdev_elm.winding2.B = b2
                    gcdev_elm.winding2.R0 = r02
                    gcdev_elm.winding2.X0 = x02
                    gcdev_elm.winding2.G0 = g02
                    gcdev_elm.winding2.B0 = b02
                    gcdev_elm.winding2.rate = float(windings[1].ratedS)

                    r3, x3, g3, b3, r03, x03, g03, b03 = get_pu_values_power_transformer_end(windings[2], Sbase)
                    gcdev_elm.winding3.R = r3
                    gcdev_elm.winding3.X = x3
                    gcdev_elm.winding3.G = g3
                    gcdev_elm.winding3.B = b3
                    gcdev_elm.winding3.R0 = r03
                    gcdev_elm.winding3.X0 = x03
                    gcdev_elm.winding3.G0 = g03
                    gcdev_elm.winding3.B0 = b03
                    gcdev_elm.winding3.rate = float(windings[2].ratedS)

                    try:
                        gcdev_elm.fill_from_star(r1=r1, r2=r2, r3=r3, x1=x1, x2=x2, x3=x3)
                    except ZeroDivisionError:
                        logger.add_error(msg='Zero division when trying to create a 3W transformer',
                                         device=cgmes_elm.rdfid,
                                         device_class=cgmes_elm.tpe,
                                         device_property="",
                                         value=f"r1:{r1}, r2:{r2}, r3:{r3}, x1:{x1}, x2:{x2}, x3:{x3}",
                                         expected_value="")

                    gcdev_model.add_transformer3w(gcdev_elm, add_middle_bus=True)

                else:
                    logger.add_error(msg='Not exactly three terminals',
                                     device=cgmes_elm.rdfid,
                                     device_class=cgmes_elm.tpe,
                                     device_property="number of associated terminals",
                                     value=f"raw={len(calc_nodes)}, unique={len(unique_calc_nodes)}",
                                     expected_value="3")

            else:
                logger.add_error(msg=f'Transformers with {len(windings)} windings not supported yet',
                                 device=cgmes_elm.rdfid,
                                 device_class=cgmes_elm.tpe,
                                 device_property="windings",
                                 value=len(windings),
                                 expected_value="2 or 3")


def get_tap_step_voltage_increment(tap_changer: CGMES_ASSETS) -> float | None:
    """
    Read the tap step-voltage increment without mutating the imported CGMES object.

    CGMES tap changer classes are inconsistent here. Some expose
    ``stepVoltageIncrement`` directly, while phase tap changers expose
    ``voltageStepIncrement`` instead. The previous implementation normalized this
    by creating a synthetic ``stepVoltageIncrement`` attribute on the CGMES
    instance. That is incompatible with slotted CGMES classes because imported
    objects must keep a fixed attribute layout.

    This helper preserves the compatibility behavior by reading the supported
    attribute names explicitly and returning one normalized value to the caller.

    :param tap_changer: Imported CGMES tap changer instance.
    :return: Normalized step-voltage increment.
    :rtype: float | None
    """
    step_voltage_increment: float | None

    step_voltage_increment = getattr(tap_changer, "stepVoltageIncrement", None)

    if step_voltage_increment is not None:
        return step_voltage_increment
    else:
        return getattr(tap_changer, "voltageStepIncrement", None)


def apply_ratio_tap_changer_table_points(tap_changer: CGMES_ASSETS,
                                         gcdev_tap_changer: gcdev.TapChanger,
                                         cgmes_model: CgmesCircuit) -> bool:
    """
    Normalize imported CGMES tap positions and, when available, override the
    linear tap-module approximation with the exact RatioTapChangerTable ratios.

    CGMES step numbering is relative to ``lowStep`` while VeraGrid stores tap
    positions as zero-based array indices. The imported tap changers currently
    keep the raw CGMES step value, which shifts positive-low tap changers by one
    position. Table-based ratio tap changers also carry exact per-step ratios
    that should replace the synthetic linear module array.

    :return: ``True`` when table ratios were applied, else ``False``.
    """
    low_step = int(getattr(tap_changer, "lowStep", 0) or 0)
    normal_step = int(getattr(tap_changer, "normalStep", low_step) or low_step)
    neutral_step = int(getattr(tap_changer, "neutralStep", low_step) or low_step)
    current_step = int(getattr(tap_changer, "step", low_step) or low_step)

    total_positions = gcdev_tap_changer.total_positions
    if total_positions > 0:
        gcdev_tap_changer._normal_position = min(max(normal_step - low_step, 0), total_positions - 1)
        gcdev_tap_changer._neutral_position = min(max(neutral_step - low_step, 0), total_positions - 1)
        gcdev_tap_changer._tap_position = min(max(current_step - low_step, 0), total_positions - 1)
        gcdev_tap_changer.recalc()

    ratio_table = getattr(tap_changer, "RatioTapChangerTable", None)
    if ratio_table is None:
        return False

    modules = np.array(gcdev_tap_changer.tap_modules_array, dtype=float, copy=True)
    k_re = np.array(gcdev_tap_changer._k_re_array, dtype=float, copy=True)
    k_im = np.array(gcdev_tap_changer._k_im_array, dtype=float, copy=True)

    applied = False
    for point in cgmes_model.cgmes_assets.RatioTapChangerTablePoint_list:
        if getattr(point, "RatioTapChangerTable", None) != ratio_table:
            continue

        point_step = getattr(point, "step", None)
        point_ratio = getattr(point, "ratio", None)
        if point_step is None or point_ratio is None:
            continue

        idx = int(point_step) - low_step
        if 0 <= idx < len(modules):
            modules[idx] = float(point_ratio)
            if getattr(point, "r", None) is not None:
                k_re[idx] = float(point.r)
            if getattr(point, "x", None) is not None:
                k_im[idx] = float(point.x)
            applied = True

    if applied:
        gcdev_tap_changer._m_array = modules
        gcdev_tap_changer._k_re_array = k_re
        gcdev_tap_changer._k_im_array = k_im

    return applied


def get_transformer_tap_changers(cgmes_model: CgmesCircuit,
                                 gcdev_model: MultiCircuit,
                                 bus_dict: Dict[str, gcdev.Bus],
                                 logger: DataLogger) -> None:
    """
    Process Tap Changer Classes from CGMES and put them into VeraGrid transformers.

    :param cgmes_model: CgmesModel
    :param gcdev_model: MultiCircuit
    :param bus_dict: Dict[str, gcdev.Bus]
    :param logger:
    :return:
    """

    TopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("TopologicalNode")
    DCTopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("DCTopologicalNode")

    ratio_tc_class = cgmes_model.assets.RatioTapChanger
    phase_sy_class = cgmes_model.assets.PhaseTapChangerSymmetrical
    phase_as_class = cgmes_model.assets.PhaseTapChangerAsymmetrical

    # convert ac lines
    for device_list in [cgmes_model.cgmes_assets.RatioTapChanger_list,
                        cgmes_model.cgmes_assets.PhaseTapChangerSymmetrical_list,
                        cgmes_model.cgmes_assets.PhaseTapChangerAsymmetrical_list]:

        for tap_changer in device_list:

            # Transformer attributes
            tap_module_control_mode: TapModuleControl = TapModuleControl.fixed
            tap_phase_control_mode: TapPhaseControl = TapPhaseControl.fixed
            # TapChanger attributes
            asymmetry_angle = 90
            tc_type = TapChangerTypes.NoRegulation
            reg_bus = None
            reg_cn = None

            if isinstance(tap_changer, ratio_tc_class):
                # Control from Control object
                if getattr(tap_changer, 'TapChangerControl', None):
                    tap_changer_control_enabled = bool(tap_changer.TapChangerControl.enabled)
                    if tap_changer.controlEnabled is not None:
                        tap_changer_control_enabled = tap_changer_control_enabled and bool(tap_changer.controlEnabled)

                    if (tap_changer.TapChangerControl.mode == cgmes_enums.RegulatingControlModeKind.voltage
                            and tap_changer_control_enabled):

                        if cgmes_model.cgmes_version == CGMESVersions.v3_0_0:
                            reg_bus = find_terminal_bus_connectivity_priority(
                                cgmes_terminal=tap_changer.TapChangerControl.Terminal,
                                bus_dict=bus_dict,
                                TopologicalNode_tpe=TopologicalNode_tpe,
                                DCTopologicalNode_tpe=DCTopologicalNode_tpe
                            )
                        else:
                            reg_bus = find_terminal_bus(
                                cgmes_terminal=tap_changer.TapChangerControl.Terminal,
                                bus_dict=bus_dict,
                                TopologicalNode_tpe=TopologicalNode_tpe,
                                DCTopologicalNode_tpe=DCTopologicalNode_tpe
                            )

                        if reg_bus is not None:
                            tc_type = TapChangerTypes.VoltageRegulation
                            tap_module_control_mode = TapModuleControl.Vm
                        else:
                            logger.add_warning(
                                msg="TapChangerControl voltage mode ignored: regulation terminal not mapped to bus",
                                device=tap_changer.rdfid,
                                device_class=tap_changer.tpe,
                                device_property="TapChangerControl.Terminal",
                                value='None',
                                expected_value='Bus')
                else:
                    logger.add_warning(msg="No TapChangerControl found for RatioTapChanger",
                                       device=tap_changer.rdfid,
                                       device_class=tap_changer.tpe,
                                       device_property="control for TapChanger",
                                       value=type(tap_changer))

            elif isinstance(tap_changer, phase_sy_class):
                tc_type = TapChangerTypes.Symmetrical

                if getattr(tap_changer, 'TapChangerControl', None):
                    if (tap_changer.TapChangerControl.mode == cgmes_enums.RegulatingControlModeKind.activePower
                            and tap_changer.TapChangerControl.enabled):
                        tap_phase_control_mode = TapPhaseControl.Pf  # from bus
                else:
                    logger.add_warning(msg="No TapChangerControl found for PhaseTapChangerSymmetrical",
                                       device=tap_changer.rdfid,
                                       device_class=tap_changer.tpe,
                                       device_property="control for TapChanger",
                                       value=type(tap_changer))

            elif isinstance(tap_changer, phase_as_class):
                tc_type = TapChangerTypes.Asymmetrical
                # windingConnectionAngle def in CGMES:
                # The phase angle between the in-phase winding and the out-of -phase winding
                # used for creating phase shift. The out-of-phase winding produces
                # what is known as the difference voltage.
                # Setting this angle to 90 degrees is not the same as a symmemtrical transformer.
                asymmetry_angle = tap_changer.windingConnectionAngle

                if getattr(tap_changer, 'TapChangerControl', None):
                    if (tap_changer.TapChangerControl.mode == cgmes_enums.RegulatingControlModeKind.activePower
                            and tap_changer.TapChangerControl.enabled):
                        tap_phase_control_mode = TapPhaseControl.Pf  # from bus
                else:
                    logger.add_warning(msg="No TapChangerControl found for PhaseTapChangerAsymmetrical",
                                       device=tap_changer.rdfid,
                                       device_class=tap_changer.tpe,
                                       device_property="control for TapChanger",
                                       value=type(tap_changer))

            else:
                logger.add_warning(msg="TapChanger Class not recognized.",
                                   device=tap_changer.rdfid,
                                   device_class=tap_changer.tpe,
                                   device_property="control for TapChanger",
                                   value=type(tap_changer))

            step_voltage_increment: float | None
            step_voltage_increment = get_tap_step_voltage_increment(tap_changer=tap_changer)

            if tap_changer.TransformerEnd is not None:
                if tap_changer.TransformerEnd.PowerTransformer is not None:
                    trafo_id = tap_changer.TransformerEnd.PowerTransformer.uuid

                    # Search in Transformer 2W
                    gcdev_trafo = find_object_by_idtag(
                        object_list=gcdev_model.transformers2w,
                        target_idtag=trafo_id
                    )

                    if gcdev_trafo is None:
                        # Search in Transformer 3W
                        gcdev_trafo = find_object_by_idtag(
                            object_list=gcdev_model.transformers3w,
                            target_idtag=trafo_id
                        )
                    else:
                        pass
                else:
                    trafo_id = None
                    gcdev_trafo = None

                if isinstance(gcdev_trafo, gcdev.Transformer2W):

                    gcdev_trafo.tap_module_control_mode = tap_module_control_mode
                    gcdev_trafo.tap_phase_control_mode = tap_phase_control_mode
                    gcdev_trafo.regulation_bus = reg_bus
                    gcdev_trafo.regulation_cn = reg_cn

                    gcdev_trafo.tap_changer.init_from_cgmes(
                        low=tap_changer.lowStep,
                        high=tap_changer.highStep,
                        normal=tap_changer.normalStep,
                        neutral=tap_changer.neutralStep,
                        stepVoltageIncrement=step_voltage_increment,
                        step=int(tap_changer.step),
                        asymmetry_angle=asymmetry_angle,
                        tc_type=tc_type
                    )
                    apply_ratio_tap_changer_table_points(
                        tap_changer=tap_changer,
                        gcdev_tap_changer=gcdev_trafo.tap_changer,
                        cgmes_model=cgmes_model
                    )

                    if gcdev_trafo.tap_changer.tc_type == TapChangerTypes.NoRegulation:
                        gcdev_trafo.tap_module = gcdev_trafo.tap_changer.get_tap_module()
                        # print(f"Tap module: {gcdev_trafo.tap_module} <--- before recalc")
                        # SET tap_module asif it was VoltageRegulation
                        gcdev_trafo.tap_changer.tc_type = TapChangerTypes.VoltageRegulation
                        gcdev_trafo.tap_changer.recalc()
                        gcdev_trafo.tap_module = gcdev_trafo.tap_changer.get_tap_module()
                        # print(f"Tap module: {gcdev_trafo.tap_module} <--- after recalc")
                        # Set it back to NoRegulation
                        gcdev_trafo.tap_changer.tc_type = TapChangerTypes.NoRegulation
                        # # SET tap_module from dV
                        # print(f"Tap module: {1 - gcdev_trafo.tap_changer.dV} <-- from dV")
                        # gcdev_trafo.tap_module = 1 - gcdev_trafo.tap_changer.dV
                        # gcdev_trafo.tap_phase = 0

                    elif gcdev_trafo.tap_changer.tc_type == TapChangerTypes.VoltageRegulation:
                        # SET tap_module from its own TapChanger object
                        gcdev_trafo.tap_module = gcdev_trafo.tap_changer.get_tap_module()
                        logger.add_info(msg="CGMES import: tap module calculated",
                                        device=gcdev_trafo.device_type,
                                        value=gcdev_trafo.tap_module)
                        # print("Tap module calculated:", gcdev_trafo.tap_module)

                    elif gcdev_trafo.tap_changer.tc_type == TapChangerTypes.Symmetrical:
                        gcdev_trafo.tap_phase = gcdev_trafo.tap_changer.get_tap_phase()
                        logger.add_info(msg="CGMES import: tap module calculated",
                                        device=gcdev_trafo.device_type,
                                        value=gcdev_trafo.tap_module)
                        # print("Tap phase calculated:", gcdev_trafo.tap_phase)

                    elif gcdev_trafo.tap_changer.tc_type == TapChangerTypes.Asymmetrical:
                        # SET tap_module from its own TapChanger object
                        gcdev_trafo.tap_module = gcdev_trafo.tap_changer.get_tap_module()
                        logger.add_info(msg="CGMES import: tap module calculated",
                                        device=gcdev_trafo.device_type,
                                        value=gcdev_trafo.tap_module)
                        # print("Tap module calculated:", gcdev_trafo.tap_module)
                        gcdev_trafo.tap_phase = gcdev_trafo.tap_changer.get_tap_phase()
                        logger.add_info(msg="CGMES import: tap module calculated",
                                        device=gcdev_trafo.device_type,
                                        value=gcdev_trafo.tap_module)
                        # print("Tap phase calculated:", gcdev_trafo.tap_phase)

                    else:
                        logger.add_error(msg="CGMES import: TapChanger has no Type",
                                         device=gcdev_trafo.device_type,
                                         value=gcdev_trafo.tap_changer.tc_type)

                elif isinstance(gcdev_trafo, gcdev.Transformer3W):
                    winding_id = tap_changer.TransformerEnd.uuid
                    # get the winding with the TapChanger
                    winding_w_tc = find_object_by_idtag(
                        object_list=[gcdev_trafo.winding1,
                                     gcdev_trafo.winding2,
                                     gcdev_trafo.winding3],
                        target_idtag=winding_id
                    )

                    if winding_w_tc is not None:
                        winding_w_tc.tap_module_control_mode = tap_module_control_mode
                        winding_w_tc.tap_phase_control_mode = tap_phase_control_mode
                        winding_w_tc.regulation_bus = reg_bus
                        winding_w_tc.regulation_cn = reg_cn

                        winding_w_tc.tap_changer.init_from_cgmes(
                            low=tap_changer.lowStep,
                            high=tap_changer.highStep,
                            normal=tap_changer.normalStep,
                            neutral=tap_changer.neutralStep,
                            stepVoltageIncrement=step_voltage_increment,
                            step=int(tap_changer.step),
                            # asymmetry_angle=90,
                            tc_type=tc_type
                        )
                        apply_ratio_tap_changer_table_points(
                            tap_changer=tap_changer,
                            gcdev_tap_changer=winding_w_tc.tap_changer,
                            cgmes_model=cgmes_model
                        )

                        if winding_w_tc.tap_changer.tc_type == TapChangerTypes.NoRegulation:
                            winding_w_tc.tap_module = winding_w_tc.tap_changer.get_tap_module()
                            winding_w_tc.tap_changer.tc_type = TapChangerTypes.VoltageRegulation
                            winding_w_tc.tap_changer.recalc()
                            winding_w_tc.tap_module = winding_w_tc.tap_changer.get_tap_module()
                            winding_w_tc.tap_changer.tc_type = TapChangerTypes.NoRegulation
                            winding_w_tc.tap_phase = winding_w_tc.tap_changer.get_tap_phase()
                        elif winding_w_tc.tap_changer.tc_type == TapChangerTypes.VoltageRegulation:
                            winding_w_tc.tap_module = winding_w_tc.tap_changer.get_tap_module()
                            winding_w_tc.tap_phase = winding_w_tc.tap_changer.get_tap_phase()
                        elif winding_w_tc.tap_changer.tc_type == TapChangerTypes.Symmetrical:
                            winding_w_tc.tap_module = winding_w_tc.tap_changer.get_tap_module()
                            winding_w_tc.tap_phase = winding_w_tc.tap_changer.get_tap_phase()
                        elif winding_w_tc.tap_changer.tc_type == TapChangerTypes.Asymmetrical:
                            winding_w_tc.tap_module = winding_w_tc.tap_changer.get_tap_module()
                            winding_w_tc.tap_phase = winding_w_tc.tap_changer.get_tap_phase()
                        else:
                            logger.add_error(msg="CGMES import: Winding TapChanger has no Type",
                                             device=winding_w_tc.device_type,
                                             value=winding_w_tc.tap_changer.tc_type)
                    else:
                        logger.add_error("Winding of the tap changer not found",
                                         device_class="TransformerEnd",
                                         device=winding_id)

                else:
                    logger.add_error(msg='Transformer not found for TapChanger',
                                     device=tap_changer.rdfid,
                                     device_class=tap_changer.tpe,
                                     device_property="transformer for powertransformerend",
                                     value=None,
                                     expected_value=trafo_id)

            else:
                logger.add_error("tap_changer.TransformerEnd is None",
                                 device_class=tap_changer.tpe,
                                 device=tap_changer.rdfid,
                                 device_property="TransformerEnd")


def get_gcdev_shunts(cgmes_model: CgmesCircuit,
                     gcdev_model: MultiCircuit,
                     calc_node_dict: Dict[str, gcdev.Bus],
                     device_to_terminal_dict: Dict[str, List[CGMES_TERMINAL]],
                     logger: DataLogger) -> None:
    """
    Convert the CGMES equivalent shunts to gcdev shunts,
    simple shunts without control

    :param cgmes_model: CgmesCircuit
    :param gcdev_model: GcdevCircuit
    :param calc_node_dict: Dict[str, gcdev.Bus]
    :param device_to_terminal_dict: Dict[str, Terminal]
    :param logger:
    """
    TopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("TopologicalNode")
    DCTopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("DCTopologicalNode")

    # convert shunts
    for device_list in [cgmes_model.cgmes_assets.EquivalentShunt_list]:

        for cgmes_elm in device_list:

            calc_nodes = find_associated_buses(cgmes_elm=cgmes_elm,
                                               device_to_terminal_dict=device_to_terminal_dict,
                                               bus_dict=calc_node_dict,
                                               TopologicalNode_tpe=TopologicalNode_tpe,
                                               DCTopologicalNode_tpe=DCTopologicalNode_tpe,
                                               logger=logger,
                                               cgmes_version=cgmes_model.cgmes_version)

            if len(calc_nodes) == 1:
                calc_node = calc_nodes[0]

                Vnom = get_voltage_shunt(shunt=cgmes_elm, logger=logger)

                G = cgmes_elm.g * (Vnom * Vnom)
                B = cgmes_elm.b * (Vnom * Vnom)

                gcdev_elm = gcdev.Shunt(
                    idtag=cgmes_elm.uuid,
                    name=cgmes_elm.name,
                    code=cgmes_elm.description,
                    G=round(G, 4),
                    B=round(B, 4),
                    active=get_cgmes_equipment_active_state(cgmes_elm),
                )
                gcdev_model.add_shunt(bus=calc_node, api_obj=gcdev_elm)

            else:
                logger.add_error(msg='Not exactly one terminal',
                                 device=cgmes_elm.rdfid,
                                 device_class=cgmes_elm.tpe,
                                 device_property="number of associated terminals",
                                 value=len(calc_nodes),
                                 expected_value=1)


def get_gcdev_controllable_shunts(
        cgmes_model: CgmesCircuit,
        gcdev_model: MultiCircuit,
        bus_dict: Dict[str, gcdev.Bus],
        device_to_terminal_dict: Dict[str, List[CGMES_TERMINAL]],
        logger: DataLogger,
        Sbase: float) -> None:
    """
    Convert the CGMES linear and non-linear shunt compensators
    to gcdev Controllable shunts.

    :param cgmes_model: CgmesCircuit
    :param gcdev_model: gcdevCircuit
    :param bus_dict: Dict[str, gcdev.Bus]
    :param device_to_terminal_dict: Dict[str, Terminal]
    :param Sbase: base power (100 MVA)
    :param logger:
    """
    TopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("TopologicalNode")
    DCTopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("DCTopologicalNode")

    # LINEAR
    for cgmes_elm in cgmes_model.cgmes_assets.LinearShuntCompensator_list:

        calc_nodes = find_associated_buses(cgmes_elm=cgmes_elm,
                                           device_to_terminal_dict=device_to_terminal_dict,
                                           bus_dict=bus_dict,
                                           TopologicalNode_tpe=TopologicalNode_tpe,
                                           DCTopologicalNode_tpe=DCTopologicalNode_tpe,
                                           logger=logger,
                                           cgmes_version=cgmes_model.cgmes_version)

        if len(calc_nodes) == 1:
            calc_node = calc_nodes[0]

            # conversion
            g, b, g0, b0 = get_values_shunt(shunt=cgmes_elm,
                                            logger=logger,
                                            Sbase=Sbase)

            v_set, is_controlled, controlled_bus, controlled_cn = (
                get_regulating_control_params(
                    cgmes_elm=cgmes_elm,
                    cgmes_enums=cgmes_enums,
                    bus_dict=bus_dict,
                    TopologicalNode_tpe=TopologicalNode_tpe,
                    DCTopologicalNode_tpe=DCTopologicalNode_tpe,
                    logger=logger,
                    prefer_connectivity_node=(cgmes_model.cgmes_version == CGMESVersions.v3_0_0)
                ))

            gcdev_elm = gcdev.ControllableShunt(
                idtag=cgmes_elm.uuid,
                name=cgmes_elm.name,
                code=cgmes_elm.description,
                active=get_cgmes_equipment_active_state(cgmes_elm),
                number_of_steps=cgmes_elm.maximumSections,
                g_per_step=g,
                b_per_step=b,
                G0=g0,
                B0=b0,
                vset=v_set,
                control_mode=ShuntControlMode.Continuous if is_controlled else ShuntControlMode.Locked,
                control_bus=controlled_bus,
            )
            # B, G is calculated when step is set: only if .sections >= 1
            gcdev_elm.step = cgmes_elm.sections - 1

            gcdev_model.add_controllable_shunt(bus=calc_node, api_obj=gcdev_elm)

        else:
            logger.add_error(msg='Not exactly one terminal',
                             device=cgmes_elm.rdfid,
                             device_class=cgmes_elm.tpe,
                             device_property="number of associated terminals",
                             value=len(calc_nodes),
                             expected_value=1)

    # NON - LINEAR
    for cgmes_elm in cgmes_model.cgmes_assets.NonlinearShuntCompensator_list:

        calc_nodes = find_associated_buses(cgmes_elm=cgmes_elm,
                                           device_to_terminal_dict=device_to_terminal_dict,
                                           bus_dict=bus_dict,
                                           TopologicalNode_tpe=TopologicalNode_tpe,
                                           DCTopologicalNode_tpe=DCTopologicalNode_tpe,
                                           logger=logger,
                                           cgmes_version=cgmes_model.cgmes_version)

        if len(calc_nodes) == 1:
            calc_node = calc_nodes[0]

            # # conversion
            # G, B, G0, B0 = get_values_shunt(shunt=cgmes_elm,
            #                                 logger=logger,
            #                                 Sbase=Sbase)

            v_set, is_controlled, controlled_bus, controlled_cn = (
                get_regulating_control_params(
                    cgmes_elm=cgmes_elm,
                    cgmes_enums=cgmes_enums,
                    bus_dict=bus_dict,
                    TopologicalNode_tpe=TopologicalNode_tpe,
                    DCTopologicalNode_tpe=DCTopologicalNode_tpe,
                    logger=logger,
                    prefer_connectivity_node=(cgmes_model.cgmes_version == CGMESVersions.v3_0_0)
                ))

            gcdev_elm = gcdev.ControllableShunt(
                idtag=cgmes_elm.uuid,
                name=cgmes_elm.name,
                code=cgmes_elm.description,
                active=get_cgmes_equipment_active_state(cgmes_elm),
                number_of_steps=cgmes_elm.maximumSections,
                step=cgmes_elm.sections,
                # g_per_step=G,
                # b_per_step=B,
                # G=G,
                # B=B,
                vset=v_set,
                control_mode=ShuntControlMode.Continuous if is_controlled else ShuntControlMode.Locked,
                control_bus=controlled_bus,
            )

            point_list = []
            for nl_sc_p in cgmes_model.cgmes_assets.NonlinearShuntCompensatorPoint_list:
                if nl_sc_p.NonlinearShuntCompensator == cgmes_elm:
                    point_list.append(nl_sc_p)
            point_list.sort(key=lambda obj: obj.sectionNumber)

            Vnom = get_voltage_shunt(shunt=cgmes_elm, logger=logger)

            cumulative_b_list = [point.b * (Vnom * Vnom) for point in point_list]
            cumulative_g_list = [point.g * (Vnom * Vnom) for point in point_list]
            b_list: list[float] = list()
            g_list: list[float] = list()
            previous_b: float = 0.0
            previous_g: float = 0.0

            for cumulative_b, cumulative_g in zip(cumulative_b_list, cumulative_g_list):
                b_list.append(cumulative_b - previous_b)
                g_list.append(cumulative_g - previous_g)
                previous_b = cumulative_b
                previous_g = cumulative_g

            n_list = [1] * len(b_list)

            gcdev_elm.set_blocks(n_list, b_list)
            gcdev_elm.g_steps = np.array(g_list, dtype=float)

            # Re-apply the active section count so the setter rebuilds the
            # cumulative susceptance and conductance from the imported curve.
            if cgmes_elm.sections is not None and cgmes_elm.sections > 0:
                gcdev_elm.step = cgmes_elm.sections - 1
            else:
                gcdev_elm.step = 0
                gcdev_elm.B = 0.0
                gcdev_elm.G = 0.0
                gcdev_elm.active = False

            gcdev_model.add_controllable_shunt(bus=calc_node, api_obj=gcdev_elm)

        else:
            logger.add_error(msg='Not exactly one terminal',
                             device=cgmes_elm.rdfid,
                             device_class=cgmes_elm.tpe,
                             device_property="number of associated terminals",
                             value=len(calc_nodes),
                             expected_value=1)


def get_gcdev_static_var_compensators(cgmes_model: CgmesCircuit,
                                      gcdev_model: MultiCircuit,
                                      bus_dict: Dict[str, gcdev.Bus],
                                      device_to_terminal_dict: Dict[str, List[CGMES_TERMINAL]],
                                      logger: DataLogger) -> None:
    """
    Convert CGMES StaticVarCompensator devices to VeraGrid ControllableShunt devices.

    :param cgmes_model: CgmesCircuit
    :param gcdev_model: gcdevCircuit
    :param bus_dict: Dict[str, gcdev.Bus]
    :param device_to_terminal_dict: Dict[str, Terminal]
    :param logger: DataLogger
    :return: None
    """
    TopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("TopologicalNode")
    DCTopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("DCTopologicalNode")

    for cgmes_elm in cgmes_model.cgmes_assets.StaticVarCompensator_list:
        calc_nodes = find_associated_buses(cgmes_elm=cgmes_elm,
                                           device_to_terminal_dict=device_to_terminal_dict,
                                           bus_dict=bus_dict,
                                           TopologicalNode_tpe=TopologicalNode_tpe,
                                           DCTopologicalNode_tpe=DCTopologicalNode_tpe,
                                           logger=logger,
                                           cgmes_version=cgmes_model.cgmes_version)

        if len(calc_nodes) == 1:
            calc_node = calc_nodes[0]

            b_value = float(cgmes_elm.q) if cgmes_elm.q is not None else 0.0
            b_max = abs(b_value) if b_value != 0.0 else 9999.0
            b_min = -b_max

            control_mode = ShuntControlMode.Locked
            v_set = 1.0

            if cgmes_elm.RegulatingControl is not None:
                (v_set, is_controlled, _, _) = get_regulating_control_params(
                    cgmes_elm=cgmes_elm,
                    cgmes_enums=cgmes_enums,
                    bus_dict=bus_dict,
                    TopologicalNode_tpe=TopologicalNode_tpe,
                    DCTopologicalNode_tpe=DCTopologicalNode_tpe,
                    logger=logger,
                    prefer_connectivity_node=(cgmes_model.cgmes_version == CGMESVersions.v3_0_0)
                )
                if is_controlled:
                    control_mode = ShuntControlMode.Continuous

            if cgmes_elm.voltageSetPoint is not None and calc_node.Vnom > 0.0:
                v_set = float(cgmes_elm.voltageSetPoint) / float(calc_node.Vnom)
                v_set = sanitize_voltage_setpoint(v_set=v_set,
                                                  cgmes_elm=cgmes_elm,
                                                  logger=logger)
                if cgmes_elm.sVCControlMode == cgmes_enums.SVCControlMode.voltage:
                    control_mode = ShuntControlMode.Continuous
            elif cgmes_elm.sVCControlMode == cgmes_enums.SVCControlMode.reactivePower:
                control_mode = ShuntControlMode.Locked

            gcdev_elm = gcdev.ControllableShunt(idtag=cgmes_elm.uuid,
                                                code=cgmes_elm.description,
                                                name=cgmes_elm.name,
                                                active=get_cgmes_equipment_active_state(cgmes_elm),
                                                B=b_value,
                                                G=0.0,
                                                Bmax=b_max,
                                                Bmin=b_min,
                                                Gmax=0.0,
                                                Gmin=0.0,
                                                vset=v_set,
                                                control_mode=control_mode,
                                                number_of_steps=1,
                                                step=0,
                                                b_per_step=b_value,
                                                g_per_step=0.0)
            gcdev_model.add_controllable_shunt(bus=calc_node, api_obj=gcdev_elm)

        else:
            logger.add_error(msg='Not exactly one terminal',
                             device=cgmes_elm.rdfid,
                             device_class=cgmes_elm.tpe,
                             device_property="number of associated terminals",
                             value=len(calc_nodes),
                             expected_value=1)


def get_gcdev_switches(cgmes_model: CgmesCircuit,
                       gcdev_model: MultiCircuit,
                       bus_dict: Dict[str, gcdev.Bus],
                       device_to_terminal_dict: Dict[str, List[CGMES_TERMINAL]],
                       logger: DataLogger,
                       prefer_connectivity_node_for_terminal_pairing: bool = False,
                       allow_terminal_pair_merge: bool = False) -> None:
    """
    Convert the CGMES switching devices to gcdev

    :param cgmes_model: CgmesCircuit
    :param gcdev_model: gcdevCircuit
    :param bus_dict: Dict[str, gcdev.Bus]
    :param device_to_terminal_dict: Dict[str, Terminal]
    :param logger: DataLogger
    :return: None
    """
    TopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("TopologicalNode")
    DCTopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("DCTopologicalNode")

    # Build the ratings dictionary
    rates_dict = {}

    sw_type = cgmes_model.assets.Switch
    br_type = cgmes_model.assets.Breaker
    ds_type = cgmes_model.assets.Disconnector
    lbs_type = cgmes_model.assets.LoadBreakSwitch
    for e in cgmes_model.cgmes_assets.CurrentLimit_list:

        if e.OperationalLimitSet is not None:

            if not isinstance(e.OperationalLimitSet, str):

                if e.OperationalLimitSet.Terminal is not None:
                    if hasattr(e.OperationalLimitSet.Terminal, "ConductingEquipment"):
                        conducting_equipment = e.OperationalLimitSet.Terminal.ConductingEquipment
                        if isinstance(conducting_equipment, (sw_type, br_type, ds_type, lbs_type)):
                            branch_id = conducting_equipment.uuid
                            rates_dict[branch_id] = e.value
                    else:
                        logger.add_error("No ConductingEquipment",
                                         device_class=e.OperationalLimitSet.Terminal.tpe,
                                         device_property="ConductingEquipment",
                                         device=e.OperationalLimitSet.Terminal.rdfid, )
                else:
                    pass
            else:
                logger.add_error("OperationalLimitSet reference not found",
                                 device_class=e.tpe,
                                 device_property="OperationalLimitSet",
                                 device=e.OperationalLimitSet, )
        else:
            logger.add_error("No OperationalLimitSet",
                             device_class=e.tpe,
                             device_property="OperationalLimitSet",
                             device=e.rdfid, )

    # convert switch
    for device_list in [cgmes_model.cgmes_assets.Switch_list,
                        cgmes_model.cgmes_assets.Breaker_list,
                        cgmes_model.cgmes_assets.Disconnector_list,
                        cgmes_model.cgmes_assets.LoadBreakSwitch_list,
                        # cgmes_model.GroundDisconnector_list
                        ]:

        for cgmes_elm in device_list:
            calc_nodes = find_associated_buses(cgmes_elm=cgmes_elm,
                                               device_to_terminal_dict=device_to_terminal_dict,
                                               bus_dict=bus_dict,
                                               TopologicalNode_tpe=TopologicalNode_tpe,
                                               DCTopologicalNode_tpe=DCTopologicalNode_tpe,
                                               logger=logger,
                                               cgmes_version=cgmes_model.cgmes_version,
                                               prefer_connectivity_node=(
                                                   prefer_connectivity_node_for_terminal_pairing
                                               ))
            calc_node_f, calc_node_t = derive_switch_bus_pair(
                calc_nodes=calc_nodes,
                allow_terminal_pair_merge=allow_terminal_pair_merge
            )
            if allow_terminal_pair_merge and (calc_node_f is None or calc_node_t is None):
                # Fallback: try the opposite pairing mode before dropping.
                alt_calc_nodes = find_associated_buses(
                    cgmes_elm=cgmes_elm,
                    device_to_terminal_dict=device_to_terminal_dict,
                    bus_dict=bus_dict,
                    TopologicalNode_tpe=TopologicalNode_tpe,
                    DCTopologicalNode_tpe=DCTopologicalNode_tpe,
                    logger=logger,
                    cgmes_version=cgmes_model.cgmes_version,
                    prefer_connectivity_node=(
                        not prefer_connectivity_node_for_terminal_pairing
                    )
                )
                calc_node_f, calc_node_t = derive_switch_bus_pair(
                    calc_nodes=alt_calc_nodes,
                    allow_terminal_pair_merge=allow_terminal_pair_merge
                )
                if calc_node_f is not None and calc_node_t is not None:
                    calc_nodes = alt_calc_nodes

            unique_calc_nodes = deduplicate_buses_preserve_order(calc_nodes)
            if allow_terminal_pair_merge and len(calc_nodes) > 2 and len(unique_calc_nodes) == 2:
                logger.add_warning(
                    msg='Collapsed repeated switch terminals to one bus pair',
                    device=cgmes_elm.rdfid,
                    device_class=cgmes_elm.tpe,
                    device_property="number of associated terminals",
                    value=len(calc_nodes),
                    expected_value=2
                )

            if calc_node_f is not None and calc_node_t is not None:
                operational_current_rate = rates_dict.get(cgmes_elm.uuid, None)  # A
                if operational_current_rate and cgmes_elm.BaseVoltage is not None:
                    # rate in MVA = A / 1000 * kV * sqrt(3)    CORRECTED!
                    op_rate = np.round((operational_current_rate / 1000.0) *
                                       cgmes_elm.BaseVoltage.nominalVoltage * 1.73205080756888,
                                       4)
                else:
                    op_rate = 9999  # Corrected

                if (cgmes_elm.ratedCurrent is not None
                        and cgmes_elm.ratedCurrent != 0.0
                        and cgmes_elm.BaseVoltage is not None):
                    rated_current = np.round(
                        (cgmes_elm.ratedCurrent / 1000.0) * cgmes_elm.BaseVoltage.nominalVoltage * 1.73205080756888,
                        4)
                else:
                    rated_current = op_rate

                active = get_cgmes_equipment_active_state(cgmes_elm, use_switch_open=True)

                gcdev_elm = gcdev.Switch(
                    idtag=cgmes_elm.uuid,
                    code=cgmes_elm.description,
                    name=cgmes_elm.name,
                    active=active,
                    bus_from=calc_node_f,
                    bus_to=calc_node_t,
                    rate=op_rate,
                    rated_current=rated_current,
                    retained=cgmes_elm.retained,
                    normal_open=cgmes_elm.normalOpen
                )

                gcdev_model.add_switch(gcdev_elm)
            else:
                logger.add_error(msg='Not exactly two terminals',
                                 device=cgmes_elm.rdfid,
                                 device_class=cgmes_elm.tpe,
                                 device_property="number of associated terminals",
                                 value=f"raw={len(calc_nodes)}, unique={len(unique_calc_nodes)}",
                                 expected_value=2)


def get_gcdev_substations(cgmes_model: CgmesCircuit,
                          gcdev_model: MultiCircuit,
                          logger: DataLogger) -> None:
    """
    Convert the CGMES substations to gcdev substations

    :param cgmes_model: CgmesCircuit
    :param gcdev_model: gcdevCircuit
    """
    # convert substations
    for device_list in [cgmes_model.cgmes_assets.Substation_list]:

        for cgmes_elm in device_list:

            community, area, zone = None, None, None

            if cgmes_model.cgmes_map_areas_like_raw:
                if cgmes_elm.Region is not None:
                    zone = find_object_by_idtag(
                        object_list=gcdev_model.zones,
                        target_idtag=cgmes_elm.Region.uuid
                    )
                else:
                    zone = None

                if cgmes_elm.Region is not None:
                    if cgmes_elm.Region.Region is not None:
                        area = find_object_by_idtag(
                            object_list=gcdev_model.areas,
                            target_idtag=cgmes_elm.Region.Region.uuid
                        )
                    else:
                        area = None
                else:
                    area = None
            else:
                if cgmes_elm.Region is not None:
                    community = find_object_by_idtag(
                        object_list=gcdev_model.communities,
                        target_idtag=cgmes_elm.Region.uuid
                    )
                else:
                    community = None

            if cgmes_elm.Location:
                try:
                    longitude = float(cgmes_elm.Location.PositionPoints.xPosition)
                    latitude = float(cgmes_elm.Location.PositionPoints.yPosition)
                except ValueError:
                    longitude = 0.0
                    latitude = 0.0
                    logger.add_error(msg="Cannot extract longitude or latitude value.")
            else:
                latitude = 0.0
                longitude = 0.0

            gcdev_elm = gcdev.Substation(
                name=cgmes_elm.name,
                idtag=cgmes_elm.uuid,
                code=cgmes_elm.description,
                latitude=latitude,  # later from GL profile/Location class
                longitude=longitude
            )

            if community is not None:
                gcdev_elm.community = community
            if area is not None:
                gcdev_elm.area = area
            if zone is not None:
                gcdev_elm.zone = zone

            gcdev_model.add_substation(gcdev_elm)


def get_gcdev_voltage_levels(cgmes_model: CgmesCircuit,
                             gcdev_model: MultiCircuit,
                             logger: DataLogger) -> Dict[str, gcdev.VoltageLevel]:
    """
    Convert the CGMES voltage levels to gcdev voltage levels

    :param cgmes_model: CgmesCircuit
    :param gcdev_model: gcdevCircuit
    :param logger:
    """
    # dictionary relating the VoltageLevel idtag to the gcdev VoltageLevel
    volt_lev_dict: Dict[str, gcdev.VoltageLevel] = dict()

    for cgmes_elm in cgmes_model.cgmes_assets.VoltageLevel_list:

        if not isinstance(cgmes_elm.BaseVoltage, str):  # if it is a string it was not substituted...

            if cgmes_elm.BaseVoltage is not None:
                gcdev_elm = gcdev.VoltageLevel(
                    idtag=cgmes_elm.uuid,
                    name=cgmes_elm.name,
                    Vnom=cgmes_elm.BaseVoltage.nominalVoltage
                )

                if cgmes_elm.Substation is not None:
                    subs = find_object_by_idtag(
                        object_list=gcdev_model.substations,
                        target_idtag=cgmes_elm.Substation.uuid  # gcdev_elm.idtag
                    )

                    if subs:
                        gcdev_elm.substation = subs

                gcdev_model.add_voltage_level(gcdev_elm)
                volt_lev_dict[gcdev_elm.idtag] = gcdev_elm
            else:
                logger.add_error(msg='Base voltage not found for VoltageLevel',
                                 device=cgmes_elm.parsed_properties.get("BaseVoltage", "not provided"),
                                 comment="get_gcdev_voltage_levels")
        else:
            logger.add_error(msg='Base voltage not found for VoltageLevel',
                             device=str(cgmes_elm.BaseVoltage),
                             comment="get_gcdev_voltage_levels")

    return volt_lev_dict


def get_gcdev_busbars(cgmes_model: CgmesCircuit,
                      gcdev_model: MultiCircuit,
                      calc_node_dict: Dict[str, gcdev.Bus],
                      device_to_terminal_dict: Dict[str, List[CGMES_TERMINAL]],
                      create_busbar_section_for_every_connectivity_node: bool,
                      logger: DataLogger) -> None:
    """
    Convert the CGMES busbars to gcdev busbars

    :param cgmes_model: CgmesCircuit
    :param gcdev_model: gcdevCircuit
    :param calc_node_dict: Dict[str, gcdev.Bus]
    :param device_to_terminal_dict: Dict[str, Terminal]
    :param create_busbar_section_for_every_connectivity_node:
    :param logger: DataLogger
    """
    vl_dict = {elm.idtag: elm for elm in gcdev_model.voltage_levels}
    created_bus_bar_ids: set[str] = set()

    TopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("TopologicalNode")
    DCTopologicalNode_tpe = cgmes_model.cgmes_assets.class_dict.get("DCTopologicalNode")

    # convert busbars
    for device_list in [cgmes_model.cgmes_assets.BusbarSection_list]:

        for cgmes_elm in device_list:

            calc_nodes = find_associated_buses(cgmes_elm=cgmes_elm,
                                               device_to_terminal_dict=device_to_terminal_dict,
                                               bus_dict=calc_node_dict,
                                               TopologicalNode_tpe=TopologicalNode_tpe,
                                               DCTopologicalNode_tpe=DCTopologicalNode_tpe,
                                               logger=logger,
                                               cgmes_version=cgmes_model.cgmes_version)

            if len(calc_nodes) == 1:

                container = cgmes_elm.EquipmentContainer

                if isinstance(container, cgmes_model.assets.VoltageLevel):
                    vl_cgmes = container
                    vl_gc = vl_dict.get(vl_cgmes.uuid, None)
                else:
                    vl_gc = None

                gcdev_elm = gcdev.BusBar(
                    name=cgmes_elm.name,
                    idtag=cgmes_elm.uuid,
                    code=cgmes_elm.description,
                    voltage_level=vl_gc,
                )
                gcdev_model.add_bus_bar(gcdev_elm)
                created_bus_bar_ids.add(cgmes_elm.uuid)

            else:
                logger.add_error(msg='Not exactly one terminal',
                                 device=cgmes_elm.rdfid,
                                 device_class=cgmes_elm.tpe,
                                 device_property="number of associated terminals",
                                 value=len(calc_nodes),
                                 expected_value=1)

    if create_busbar_section_for_every_connectivity_node:
        for cn_elm in cgmes_model.cgmes_assets.ConnectivityNode_list:
            if cn_elm.uuid in created_bus_bar_ids:
                continue

            tp_uid = None
            if isinstance(cn_elm.TopologicalNode, (TopologicalNode_tpe, DCTopologicalNode_tpe)):
                tp_uid = cn_elm.TopologicalNode.uuid

            if cn_elm.uuid in calc_node_dict:
                has_mapped_bus = True
            elif tp_uid is not None and tp_uid in calc_node_dict:
                has_mapped_bus = True
            else:
                has_mapped_bus = False

            if has_mapped_bus:
                if tp_uid is not None and isinstance(cn_elm.TopologicalNode.ConnectivityNodeContainer, str):
                    vl_gc = vl_dict.get(cn_elm.TopologicalNode.ConnectivityNodeContainer, None)
                elif tp_uid is not None and cn_elm.TopologicalNode.ConnectivityNodeContainer is not None:
                    vl_gc = vl_dict.get(cn_elm.TopologicalNode.ConnectivityNodeContainer.uuid, None)
                else:
                    vl_gc = None

                bus_bar_name = cn_elm.name if cn_elm.name else f"Busbar_{cn_elm.uuid}"
                gcdev_elm = gcdev.BusBar(
                    name=bus_bar_name,
                    idtag=cn_elm.uuid,
                    code=cn_elm.description,
                    voltage_level=vl_gc,
                )
                gcdev_model.add_bus_bar(gcdev_elm)
                created_bus_bar_ids.add(cn_elm.uuid)
            else:
                logger.add_info(
                    msg="ConnectivityNode busbar was not created because no mapped bus exists",
                    device=cn_elm.rdfid,
                    device_class=cn_elm.tpe,
                    device_property="ConnectivityNode"
                )


def get_gcdev_countries(cgmes_model: CgmesCircuit,
                        gcdev_model: MultiCircuit) -> None:
    """
    Convert the CGMES GeoGraphicalRegions to gcdev Country

    :param cgmes_model: CgmesCircuit
    :param gcdev_model: gcdevCircuit
    """
    for device_list in [cgmes_model.cgmes_assets.GeographicalRegion_list]:

        for cgmes_elm in device_list:
            if cgmes_model.cgmes_map_areas_like_raw:
                gcdev_elm = gcdev.Area(
                    name=cgmes_elm.name,
                    idtag=cgmes_elm.uuid,
                    code=cgmes_elm.description,
                    # latitude=0.0,     # later from GL profile/Location class
                    # longitude=0.0
                )

                gcdev_model.add_area(gcdev_elm)

            else:
                gcdev_elm = gcdev.Country(
                    name=cgmes_elm.name,
                    idtag=cgmes_elm.uuid,
                    code=cgmes_elm.description,
                    # latitude=0.0,     # later from GL profile/Location class
                    # longitude=0.0
                )

                gcdev_model.add_country(gcdev_elm)


def get_gcdev_community(cgmes_model: CgmesCircuit,
                        gcdev_model: MultiCircuit) -> None:
    """
    Convert the CGMES SubGeographicalRegions to gcdev Community

    :param cgmes_model: CgmesCircuit
    :param gcdev_model: gcdevCircuit
    """
    for device_list in [cgmes_model.cgmes_assets.SubGeographicalRegion_list]:

        for cgmes_elm in device_list:
            if cgmes_model.cgmes_map_areas_like_raw:
                gcdev_elm = gcdev.Zone(
                    name=cgmes_elm.name,
                    idtag=cgmes_elm.uuid,
                    code=cgmes_elm.description,
                    # latitude=0.0,     # later from GL profile/Location class
                    # longitude=0.0
                )

                if cgmes_elm.Region is not None:
                    a = find_object_by_idtag(
                        object_list=gcdev_model.areas,
                        target_idtag=cgmes_elm.Region.uuid
                    )
                else:
                    a = None

                if a is not None:
                    gcdev_elm.area = a
                else:
                    pass

                gcdev_model.add_zone(gcdev_elm)

            else:
                gcdev_elm = gcdev.Community(
                    name=cgmes_elm.name,
                    idtag=cgmes_elm.uuid,
                    code=cgmes_elm.description,
                    # latitude=0.0,     # later from GL profile/Location class
                    # longitude=0.0
                )

                if cgmes_elm.Region is not None:
                    c = find_object_by_idtag(
                        object_list=gcdev_model.countries,
                        target_idtag=cgmes_elm.Region.uuid
                    )

                    if c is not None:
                        gcdev_elm.country = c

                gcdev_model.add_community(gcdev_elm)


def get_header_mas(cgmes_model: CgmesCircuit,
                   gcdev_model: MultiCircuit,
                   logger: DataLogger) -> None:
    """

    :param cgmes_model:
    :param gcdev_model:
    :param logger:
    :return:
    """
    mas_set = set()
    for full_model in cgmes_model.cgmes_assets.FullModel_list:
        if full_model.modelingAuthoritySet is None:
            logger.add_warning(msg="Missing MAS in header!",
                               device=full_model.rdfid,
                               device_property="modelingAuthoritySet")
            continue
        if isinstance(full_model.modelingAuthoritySet, list):
            for mas in full_model.modelingAuthoritySet:
                mas_set.add(mas)
        else:
            mas_set.add(full_model.modelingAuthoritySet)
    for mas in mas_set:
        gcdev_elm = gcdev.ModellingAuthority(name=mas)
        gcdev_model.add_modelling_authority(gcdev_elm)


def cgmes_to_veragrid(cgmes_model: CgmesCircuit,
                      map_dc_to_hvdc_line: bool,
                      logger: DataLogger,
                      cgmes_topology_mode: CgmesTopologyMode = CgmesTopologyMode.Auto,
                      create_busbar_section_for_every_connectivity_node: bool = False) -> MultiCircuit:
    """
    Convert CGMES model to gcdev

    :param cgmes_model: CgmesCircuit
    :param map_dc_to_hvdc_line: Converters and DC lines from CGMES are converted
                                to the simplified HvdcLine objects in VeraGrid
    :param cgmes_topology_mode: Strategy to create buses from CGMES topology.
    :param create_busbar_section_for_every_connectivity_node: Optional node-breaker busbar expansion.
    :param logger: Logger object
    :return: MultiCircuit
    """
    gc_model = MultiCircuit()  # roseta
    gc_model.comments = 'Converted from a CGMES file'
    Sbase = gc_model.Sbase
    cgmes_model.emit_progress(70)
    cgmes_model.emit_text("Converting CGMES to VeraGrid")

    get_header_mas(cgmes_model, gc_model, logger)

    get_gcdev_countries(cgmes_model, gc_model)

    get_gcdev_community(cgmes_model, gc_model)

    get_gcdev_substations(cgmes_model, gc_model, logger)

    vl_dict = get_gcdev_voltage_levels(cgmes_model=cgmes_model,
                                       gcdev_model=gc_model,
                                       logger=logger)

    cn_look_up = Cn2BusBarLookup(cgmes_model)

    sv_volt_dict = get_gcdev_voltage_dict(cgmes_model=cgmes_model,
                                          logger=logger)

    device_to_terminal_dict = get_gcdev_device_to_terminal_dict(cgmes_model=cgmes_model,
                                                                logger=logger)

    dc_device_to_terminal_dict, ground_buses, ground_nodes = get_gcdev_dc_device_to_terminal_dict(
        cgmes_model=cgmes_model,
        logger=logger
    )

    # NOTE: In VeraGrid there are only buses (as it should be)
    # hence, the ConnectivityNodes and TopologicalNodes are
    # converted to buses giving priority to the ConnectivityNodes
    bus_dict, fatal_error = get_gcdev_buses(cgmes_model=cgmes_model,
                                            gc_model=gc_model,
                                            v_dict=sv_volt_dict,
                                            cn_look_up=cn_look_up,
                                            cgmes_topology_mode=cgmes_topology_mode,
                                            skip_dc_import=map_dc_to_hvdc_line,
                                            buses_to_skip=ground_buses,
                                            default_nominal_voltage=500.0,
                                            logger=logger)

    if fatal_error:
        return gc_model

    # cn_dict = get_gcdev_connectivity_nodes(cgmes_model=cgmes_model,
    #                                        gcdev_model=gc_model,
    #                                        calc_node_dict=bus_dict,
    #                                        cn_look_up=cn_look_up,
    #                                        logger=logger)

    cgmes_model.emit_progress(78)
    get_gcdev_busbars(cgmes_model=cgmes_model,
                      gcdev_model=gc_model,
                      calc_node_dict=bus_dict,
                      device_to_terminal_dict=device_to_terminal_dict,
                      create_busbar_section_for_every_connectivity_node=(
                          create_busbar_section_for_every_connectivity_node
                      ),
                      logger=logger)

    get_gcdev_loads(cgmes_model=cgmes_model,
                    gcdev_model=gc_model,
                    bus_dict=bus_dict,
                    device_to_terminal_dict=device_to_terminal_dict,
                    logger=logger)

    get_gcdev_external_grids(cgmes_model=cgmes_model,
                             gcdev_model=gc_model,
                             calc_node_dict=bus_dict,
                             device_to_terminal_dict=device_to_terminal_dict,
                             logger=logger)

    get_gcdev_generators(cgmes_model=cgmes_model,
                         gcdev_model=gc_model,
                         bus_dict=bus_dict,
                         device_to_terminal_dict=device_to_terminal_dict,
                         logger=logger)

    cgmes_model.emit_progress(86)

    get_gcdev_ac_lines(cgmes_model=cgmes_model,
                       gcdev_model=gc_model,
                       bus_dict=bus_dict,
                       device_to_terminal_dict=device_to_terminal_dict,
                       logger=logger,
                       Sbase=Sbase)

    get_gcdev_series_compensators(cgmes_model=cgmes_model,
                                  gcdev_model=gc_model,
                                  bus_dict=bus_dict,
                                  device_to_terminal_dict=device_to_terminal_dict,
                                  logger=logger,
                                  Sbase=Sbase)

    get_gcdev_ac_transformers(cgmes_model=cgmes_model,
                              gcdev_model=gc_model,
                              bus_dict=bus_dict,
                              device_to_terminal_dict=device_to_terminal_dict,
                              logger=logger,
                              Sbase=Sbase)

    get_transformer_tap_changers(cgmes_model=cgmes_model,
                                 gcdev_model=gc_model,
                                 bus_dict=bus_dict,
                                 logger=logger)

    get_gcdev_shunts(cgmes_model=cgmes_model,
                     gcdev_model=gc_model,
                     calc_node_dict=bus_dict,
                     device_to_terminal_dict=device_to_terminal_dict,
                     logger=logger)

    get_gcdev_controllable_shunts(
        cgmes_model=cgmes_model,
        gcdev_model=gc_model,
        bus_dict=bus_dict,
        device_to_terminal_dict=device_to_terminal_dict,
        logger=logger,
        Sbase=Sbase
    )

    get_gcdev_static_var_compensators(cgmes_model=cgmes_model,
                                      gcdev_model=gc_model,
                                      bus_dict=bus_dict,
                                      device_to_terminal_dict=device_to_terminal_dict,
                                      logger=logger)

    prefer_connectivity_for_switch_pairing = detect_switch_terminal_pairing_preference(
        cgmes_model=cgmes_model,
        cgmes_topology_mode=cgmes_topology_mode,
        device_to_terminal_dict=device_to_terminal_dict,
        bus_dict=bus_dict
    )

    get_gcdev_switches(cgmes_model=cgmes_model,
                       gcdev_model=gc_model,
                       bus_dict=bus_dict,
                       device_to_terminal_dict=device_to_terminal_dict,
                       logger=logger,
                       prefer_connectivity_node_for_terminal_pairing=(
                           prefer_connectivity_for_switch_pairing
                       ),
                       allow_terminal_pair_merge=prefer_connectivity_for_switch_pairing)

    cgmes_model.emit_progress(91)
    cgmes_model.emit_text("Converting CGMES to VeraGrid - HVDC")

    # DC elements  ---------------------------------------------------------

    dc_device_to_terminal_dict, ground_buses, ground_nodes = get_gcdev_dc_device_to_terminal_dict(
        cgmes_model=cgmes_model,
        logger=logger
    )

    # dc_bus_dict = get_gcdev_dc_buses(
    #     cgmes_model=cgmes_model,
    #     gc_model=gc_model,
    #     skip_dc_import=map_dc_to_hvdc_line,
    #     buses_to_skip=ground_buses,
    #     logger=logger
    # )

    dc_cn_dict = get_gcdev_dc_connectivity_nodes(
        cgmes_model=cgmes_model,
        gc_model=gc_model,
        skip_dc_import=map_dc_to_hvdc_line,
        dc_bus_dict=bus_dict,
        logger=logger
    )

    if map_dc_to_hvdc_line:

        logger.add_info(
            msg="Simplified HVDC modelling",
            comment="DC buses are not imported!")

        get_gcdev_hvdc_from_dcline_and_vscs(
            cgmes_model=cgmes_model,
            gcdev_model=gc_model,
            dc_bus_dict=bus_dict,
            dc_device_to_terminal_dict=dc_device_to_terminal_dict,
            bus_dict=bus_dict,
            device_to_terminal_dict=device_to_terminal_dict,
            logger=logger,
        )

    else:

        logger.add_info(
            msg="Detailed HVDC modelling with VsConverters and DC Lines",
            comment="DC buses are imported!")

        get_gcdev_dc_lines(
            cgmes_model=cgmes_model,
            gcdev_model=gc_model,
            dc_bus_dict=bus_dict,
            device_to_terminal_dict=dc_device_to_terminal_dict,
            logger=logger,
        )

        get_gcdev_vsc_converters(
            cgmes_model=cgmes_model,
            gcdev_model=gc_model,
            dc_bus_dict=bus_dict,
            dc_device_to_terminal_dict=dc_device_to_terminal_dict,
            bus_dict=bus_dict,
            device_to_terminal_dict=device_to_terminal_dict,
            logger=logger,
        )

    cgmes_model.emit_progress(100)
    cgmes_model.emit_text("Cgmes import done!")

    recover_bus_nominal_voltages(gc_model=gc_model, logger=logger)
    enforce_ac_line_voltage_consistency(gc_model=gc_model, logger=logger)

    return gc_model
