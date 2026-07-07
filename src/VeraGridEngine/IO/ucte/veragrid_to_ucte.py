# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import math
from datetime import datetime
from typing import Dict, List, TextIO

import VeraGridEngine.Devices as dev
from VeraGridEngine.Devices.Injections.external_grid import ExternalGrid
from VeraGridEngine.Devices.Injections.static_generator import StaticGenerator
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import ExternalGridMode, TapModuleControl, TapPhaseControl, GeneratorControlMode


class UcteBusAggregate:
    """
    Store the bus-level values required by one exported UCTE node.
    """

    __slots__ = (
        "status",
        "node_type",
        "voltage_reference_kv",
        "active_load_mw",
        "reactive_load_mvar",
        "has_generation_record",
        "active_gen_mw",
        "reactive_gen_mvar",
        "has_generation_limits",
        "min_gen_mw",
        "max_gen_mw",
        "min_gen_mvar",
        "max_gen_mvar",
        "plant_type",
        "shunt_b_mvar",
    )

    def __init__(self) -> None:
        """
        Build one empty node aggregate.

        :return: None.
        """
        self.status: int = 0
        self.node_type: int = 0
        self.voltage_reference_kv: float = math.nan
        self.active_load_mw: float = 0.0
        self.reactive_load_mvar: float = 0.0
        self.has_generation_record: bool = False
        self.active_gen_mw: float = 0.0
        self.reactive_gen_mvar: float = 0.0
        self.has_generation_limits: bool = False
        self.min_gen_mw: float = 0.0
        self.max_gen_mw: float = 0.0
        self.min_gen_mvar: float = 0.0
        self.max_gen_mvar: float = 0.0
        self.plant_type: str = ""
        self.shunt_b_mvar: float = 0.0


class UcteBranchCounter:
    """
    Assign one-character UCTE order codes per branch endpoint pair.
    """

    __slots__ = ("_count_by_pair",)

    def __init__(self) -> None:
        """
        Build one empty counter.

        :return: None.
        """
        self._count_by_pair: Dict[tuple[str, str], int] = dict()

    def get_next_code(self, node_1: str, node_2: str, logger: Logger) -> str:
        """
        Get the next order code for one endpoint pair.

        :param node_1: First node code.
        :param node_2: Second node code.
        :param logger: Export logger.
        :return: One-character UCTE order code.
        """
        alphabet: str = "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0"
        pair_key: tuple[str, str] = tuple(sorted((node_1, node_2)))
        current_count: int = self._count_by_pair.get(pair_key, 0)
        self._count_by_pair[pair_key] = current_count + 1

        if current_count < len(alphabet):
            return alphabet[current_count]
        else:
            logger.add_warning("Too many parallel UCTE branches for one endpoint pair, reusing the last order code",
                               device=f"{node_1}-{node_2}",
                               value=current_count + 1,
                               expected_value=f"<= {len(alphabet)}")
            return alphabet[len(alphabet) - 1]


def get_ucte_voltage_code(voltage_kv: float) -> str:
    """
    Map one nominal voltage value to the closest standard UCTE voltage code.

    :param voltage_kv: Nominal voltage in kV.
    :return: One-character voltage code.
    """
    voltage_map: Dict[str, float] = {
        "0": 750.0,
        "1": 380.0,
        "2": 220.0,
        "3": 150.0,
        "4": 120.0,
        "5": 110.0,
        "6": 70.0,
        "7": 27.0,
        "8": 330.0,
        "9": 500.0,
        "A": 26.0,
        "B": 25.0,
        "C": 24.0,
        "D": 23.0,
        "E": 22.0,
        "F": 21.0,
        "G": 20.0,
        "H": 19.0,
        "I": 18.0,
        "J": 17.0,
        "K": 15.7,
        "L": 15.0,
        "M": 13.7,
        "N": 13.0,
        "O": 12.0,
        "P": 11.0,
        "Q": 9.8,
        "R": 9.0,
        "S": 8.0,
        "T": 7.0,
        "U": 6.0,
        "V": 5.0,
        "W": 4.0,
        "X": 3.0,
        "Y": 2.0,
        "Z": 1.0,
    }
    best_code: str = "Z"
    best_distance: float = float("inf")
    code_value: float
    code_key: str
    for code_key, code_value in voltage_map.items():
        distance: float = abs(code_value - float(voltage_kv))
        if distance < best_distance:
            best_distance = distance
            best_code = code_key
        else:
            pass

    return best_code


def is_usable_ucte_bus_code(node_code: str, bus: dev.Bus) -> bool:
    """
    Check if one bus code can be reused directly as a canonical UCTE node code.

    :param node_code: Candidate node code.
    :param bus: VeraGrid bus.
    :return: ``True`` when the code is already UCTE-safe.
    """
    if len(node_code) != 8:
        return False
    else:
        pass

    if any(character.isspace() for character in node_code):
        return False
    else:
        pass

    if node_code.endswith("Q"):
        return False
    else:
        pass

    voltage_code: str = get_ucte_voltage_code(bus.Vnom)
    if node_code[6] != voltage_code:
        return False
    else:
        pass

    return True


def normalize_reusable_noncanonical_ucte_bus_code(node_code: str) -> str | None:
    """
    Normalize one existing non-canonical node code for roundtrip preservation.

    This keeps non-canonical UCTE identifiers from imported synthetic datasets
    so that the importer can continue applying its nominal-voltage repair
    heuristics on roundtrip.

    :param node_code: Candidate node code.
    :return: Normalized 8-character code or ``None``.
    """
    normalized_code: str = str(node_code)

    if len(normalized_code) < 8 and any(character.isspace() for character in normalized_code):
        normalized_code = normalized_code.ljust(8)
    else:
        pass

    if len(normalized_code) != 8:
        return None
    else:
        pass

    if normalized_code.strip() == "":
        return None
    else:
        pass

    if normalized_code.endswith("Q"):
        return None
    else:
        pass

    if any(character.isspace() for character in normalized_code):
        return normalized_code
    else:
        return None


def get_country_code(bus: dev.Bus) -> str:
    """
    Get the UCTE country code to use for one bus block.

    :param bus: VeraGrid bus.
    :return: Two-letter country code or ``XX``.
    """
    if bus.country is None:
        return "XX"
    else:
        pass

    country_name: str = str(bus.country.name).strip().upper()
    if len(country_name) == 2 and country_name.isalpha():
        return country_name
    else:
        return "XX"


def is_standard_ucte_country_code(country_code: str) -> bool:
    """
    Check if one country code matches the standard UCTE two-letter form.

    :param country_code: Country code to inspect.
    :return: ``True`` when the code is standard.
    """
    normalized_code: str = str(country_code).strip()
    return (
        len(normalized_code) == 2
        and normalized_code.isalpha()
        and normalized_code.upper() == normalized_code
        and normalized_code != "XX"
    )


def use_legacy_transformer_orientation(bus_from: dev.Bus, bus_to: dev.Bus) -> bool:
    """
    Select the transformer orientation expected by the UCTE importer.

    Standard country-coded UCTE data uses the legacy regulated/non-regulated
    winding convention, while IEEE-like synthetic files use the direct
    ``node1 -> node2`` orientation.

    :param bus_from: VeraGrid transformer ``bus_from`` side.
    :param bus_to: VeraGrid transformer ``bus_to`` side.
    :return: ``True`` when the legacy UCTE orientation must be exported.
    """
    country_code_from: str = get_country_code(bus_from)
    country_code_to: str = get_country_code(bus_to)
    return is_standard_ucte_country_code(country_code_from) and is_standard_ucte_country_code(country_code_to)


def build_bus_node_code_map(circuit: MultiCircuit, logger: Logger) -> Dict[dev.Bus, str]:
    """
    Build one deterministic UCTE node-code map for every exported bus.

    :param circuit: Circuit to export.
    :param logger: Export logger.
    :return: Bus-to-node-code mapping.
    """
    code_map: Dict[dev.Bus, str] = dict()
    used_codes: set[str] = set()
    bus_index: int = 0
    bus: dev.Bus
    for bus in circuit.get_buses():
        candidate_code: str = str(bus.code)
        candidate_code_display: str = candidate_code.strip()
        reusable_noncanonical_code: str | None = normalize_reusable_noncanonical_ucte_bus_code(candidate_code)

        if is_usable_ucte_bus_code(candidate_code, bus) and candidate_code not in used_codes:
            code_map[bus] = candidate_code
            used_codes.add(candidate_code)
        elif reusable_noncanonical_code is not None and reusable_noncanonical_code not in used_codes:
            code_map[bus] = reusable_noncanonical_code
            used_codes.add(reusable_noncanonical_code)
        else:
            voltage_code: str = get_ucte_voltage_code(bus.Vnom)
            prefix: str
            if bus.internal:
                prefix = "X"
            else:
                prefix = "N"

            generated_code: str = ""
            found_code: bool = False
            while not found_code:
                generated_code = f"{prefix}{bus_index:05d}{voltage_code}A"
                bus_index += 1
                if generated_code not in used_codes:
                    found_code = True
                else:
                    found_code = False

            code_map[bus] = generated_code
            used_codes.add(generated_code)

            if candidate_code_display != "":
                logger.add_warning("Generated canonical UCTE node code for bus",
                                   device=bus.name,
                                   value=candidate_code_display,
                                   expected_value=generated_code)
            else:
                logger.add_info("Generated canonical UCTE node code for bus",
                                device=bus.name,
                                value=generated_code)

    return code_map


def build_shunt_node_code(bus_code: str) -> str:
    """
    Build the fictitious-shunt node code paired to one exported bus code.

    :param bus_code: Main bus node code.
    :return: Fictitious-shunt node code.
    """
    return f"{bus_code[:7]}Q"


def get_snapshot_datetime(circuit: MultiCircuit, t_idx: int | None) -> datetime:
    """
    Get the export timestamp represented by one UCTE file.

    :param circuit: Circuit to export.
    :param t_idx: Optional profile index.
    :return: Snapshot datetime.
    """
    if t_idx is None:
        return circuit.snapshot_time
    else:
        if circuit.has_time_series:
            return circuit.time_profile[t_idx].to_pydatetime()
        else:
            return circuit.snapshot_time


def get_bus_voltage_reference(bus: dev.Bus) -> float:
    """
    Convert the VeraGrid bus voltage seed to the UCTE ``Uref`` value.

    :param bus: VeraGrid bus.
    :return: Voltage reference in kV.
    """
    if bus.Vnom > 0.0:
        return float(bus.Vm0) * float(bus.Vnom)
    else:
        return math.nan


def update_generation_limits_from_generator(aggregate: UcteBusAggregate,
                                            generator: dev.Generator | dev.Battery) -> None:
    """
    Accumulate UCTE generation limits from one VeraGrid generator-like device.

    :param aggregate: Target bus aggregate.
    :param generator: Generator or battery device.
    :return: None.
    """
    min_gen_mw: float = -float(generator.Pmax)
    max_gen_mw: float = -float(generator.Pmin)
    min_gen_mvar: float = -float(generator.Qmax)
    max_gen_mvar: float = -float(generator.Qmin)

    if aggregate.has_generation_limits:
        aggregate.min_gen_mw += min_gen_mw
        aggregate.max_gen_mw += max_gen_mw
        aggregate.min_gen_mvar += min_gen_mvar
        aggregate.max_gen_mvar += max_gen_mvar
    else:
        aggregate.min_gen_mw = min_gen_mw
        aggregate.max_gen_mw = max_gen_mw
        aggregate.min_gen_mvar = min_gen_mvar
        aggregate.max_gen_mvar = max_gen_mvar
        aggregate.has_generation_limits = True


def add_generator_like_device(aggregate: UcteBusAggregate,
                              device: dev.Generator | dev.Battery | StaticGenerator,
                              t_idx: int | None) -> None:
    """
    Add one generator-like device to the bus aggregate using UCTE sign semantics.

    :param aggregate: Target bus aggregate.
    :param device: Generator-like device.
    :param t_idx: Optional profile index.
    :return: None.
    """
    active_power_mw: float = float(device.get_P_at(t_idx))
    reactive_power_mvar: float = float(device.get_Q_at(t_idx))

    # UCTE generation is imported with the opposite sign, so the exporter must
    # invert VeraGrid generator injections to preserve the same numerical state.
    aggregate.active_gen_mw += -active_power_mw
    aggregate.reactive_gen_mvar += -reactive_power_mvar
    aggregate.has_generation_record = True


def add_load_like_device(aggregate: UcteBusAggregate,
                         device: dev.Load | ExternalGrid,
                         t_idx: int | None,
                         logger: Logger) -> None:
    """
    Add one load-like device to the bus aggregate.

    :param aggregate: Target bus aggregate.
    :param device: Load or load-mode external grid.
    :param t_idx: Optional profile index.
    :param logger: Export logger.
    :return: None.
    """
    aggregate.active_load_mw += float(device.get_P_at(t_idx))
    aggregate.reactive_load_mvar += float(device.get_Q_at(t_idx))

    if abs(float(device.get_G_at(t_idx))) > 1e-9 or abs(float(device.get_B_at(t_idx))) > 1e-9:
        logger.add_warning("UCTE node export ignores admittance terms on load-like devices",
                           device=device.name,
                           value=f"G={device.get_G_at(t_idx)}, B={device.get_B_at(t_idx)}")
    else:
        pass


def update_aggregate_voltage_control_from_generator(aggregate: UcteBusAggregate,
                                                    bus: dev.Bus,
                                                    generator: dev.Generator | dev.Battery,
                                                    t_idx: int | None) -> None:
    """
    Apply one generator voltage-control mode to the aggregate node state.

    :param aggregate: Target bus aggregate.
    :param bus: Parent bus.
    :param generator: Generator or battery.
    :param t_idx: Optional profile index.
    :return: None.
    """
    if generator.control_mode == GeneratorControlMode.V:
        if aggregate.node_type != 3:
            aggregate.node_type = 2
        else:
            pass
        aggregate.voltage_reference_kv = float(generator.get_Vset_at(t_idx)) * float(bus.Vnom)
    else:
        pass


def update_aggregate_from_external_grid(aggregate: UcteBusAggregate,
                                        bus: dev.Bus,
                                        external_grid: ExternalGrid,
                                        t_idx: int | None,
                                        logger: Logger) -> None:
    """
    Apply one external-grid device to the UCTE node aggregate.

    :param aggregate: Target bus aggregate.
    :param bus: Parent bus.
    :param external_grid: External-grid device.
    :param t_idx: Optional profile index.
    :param logger: Export logger.
    :return: None.
    """
    if external_grid.mode == ExternalGridMode.PQ:
        add_load_like_device(aggregate=aggregate,
                             device=external_grid,
                             t_idx=t_idx,
                             logger=logger)
    elif external_grid.mode == ExternalGridMode.PV:
        if aggregate.node_type != 3:
            aggregate.node_type = 2
        else:
            pass
        aggregate.voltage_reference_kv = float(external_grid.get_Vm_at(t_idx)) * float(bus.Vnom)

        # Power values remain important in PQ/PV steady-state exchanges. The
        # load-parent sign convention is preserved exactly on the UCTE node.
        aggregate.active_load_mw += float(external_grid.get_P_at(t_idx))
        aggregate.reactive_load_mvar += float(external_grid.get_Q_at(t_idx))
    elif external_grid.mode == ExternalGridMode.VD:
        aggregate.node_type = 3
        aggregate.voltage_reference_kv = float(external_grid.get_Vm_at(t_idx)) * float(bus.Vnom)
        aggregate.active_load_mw += float(external_grid.get_P_at(t_idx))
        aggregate.reactive_load_mvar += float(external_grid.get_Q_at(t_idx))
    else:
        logger.add_warning("Unsupported external-grid mode for UCTE export",
                           device=external_grid.name,
                           value=str(external_grid.mode))


def build_bus_aggregate(circuit: MultiCircuit,
                        bus: dev.Bus,
                        bus_injections: Dict[dev.Bus, Dict[object, List[object]]],
                        t_idx: int | None,
                        logger: Logger) -> UcteBusAggregate:
    """
    Aggregate all supported VeraGrid injections attached to one bus.

    :param circuit: Circuit to export.
    :param bus: Bus to aggregate.
    :param bus_injections: Bus-grouped injection lookup.
    :param t_idx: Optional profile index.
    :param logger: Export logger.
    :return: Filled node aggregate.
    """
    del circuit

    aggregate: UcteBusAggregate = UcteBusAggregate()

    if bus.get_active_at(t_idx):
        aggregate.status = 0
    else:
        aggregate.status = 1

    if bus.is_slack:
        aggregate.node_type = 3
    else:
        aggregate.node_type = 0

    aggregate.voltage_reference_kv = get_bus_voltage_reference(bus)

    injection_lists_by_type: Dict[object, List[object]] | None = bus_injections.get(bus, None)
    if injection_lists_by_type is None:
        return aggregate
    else:
        pass

    device_list: List[object]
    for device_list in injection_lists_by_type.values():
        device_obj: object
        for device_obj in device_list:
            if isinstance(device_obj, dev.Load):
                if device_obj.get_active_at(t_idx):
                    add_load_like_device(aggregate=aggregate,
                                         device=device_obj,
                                         t_idx=t_idx,
                                         logger=logger)
                else:
                    pass
            elif isinstance(device_obj, StaticGenerator):
                if device_obj.get_active_at(t_idx):
                    add_generator_like_device(aggregate=aggregate,
                                              device=device_obj,
                                              t_idx=t_idx)
                else:
                    pass
            elif isinstance(device_obj, dev.Generator):
                if device_obj.get_active_at(t_idx):
                    add_generator_like_device(aggregate=aggregate,
                                              device=device_obj,
                                              t_idx=t_idx)
                    update_generation_limits_from_generator(aggregate=aggregate, generator=device_obj)
                    update_aggregate_voltage_control_from_generator(aggregate=aggregate,
                                                                    bus=bus,
                                                                    generator=device_obj,
                                                                    t_idx=t_idx)
                else:
                    pass
            elif isinstance(device_obj, dev.Battery):
                if device_obj.get_active_at(t_idx):
                    add_generator_like_device(aggregate=aggregate,
                                              device=device_obj,
                                              t_idx=t_idx)
                    update_generation_limits_from_generator(aggregate=aggregate, generator=device_obj)
                    update_aggregate_voltage_control_from_generator(aggregate=aggregate,
                                                                    bus=bus,
                                                                    generator=device_obj,
                                                                    t_idx=t_idx)
                else:
                    pass
            elif isinstance(device_obj, dev.Shunt):
                if device_obj.get_active_at(t_idx):
                    aggregate.shunt_b_mvar += float(device_obj.get_B_at(t_idx))
                    if abs(float(device_obj.get_G_at(t_idx))) > 1e-9:
                        logger.add_warning("UCTE shunt export ignores conductance terms",
                                           device=device_obj.name,
                                           value=device_obj.get_G_at(t_idx))
                    else:
                        pass
                else:
                    pass
            elif isinstance(device_obj, ExternalGrid):
                if device_obj.get_active_at(t_idx):
                    update_aggregate_from_external_grid(aggregate=aggregate,
                                                        bus=bus,
                                                        external_grid=device_obj,
                                                        t_idx=t_idx,
                                                        logger=logger)
                else:
                    pass
            else:
                logger.add_warning("Unsupported injection device skipped by UCTE export",
                                   device_class=str(type(device_obj)),
                                   device=str(device_obj))

    return aggregate


def format_optional_float(value: float, decimals: int) -> str:
    """
    Format one optional float for tolerant UCTE text output.

    :param value: Numeric value.
    :param decimals: Number of decimal places.
    :return: Formatted text or an empty string.
    """
    if math.isfinite(value):
        return f"{value:.{decimals}f}"
    else:
        return ""


def format_optional_float_width(value: float, width: int, decimals: int) -> str:
    """
    Format one optional float using one strict fixed-width UCTE field.

    :param value: Numeric value.
    :param width: Field width.
    :param decimals: Number of decimal places.
    :return: Fixed-width text or blanks.
    """
    if math.isfinite(value):
        return f"{value:>{width}.{decimals}f}"
    else:
        return " " * width


def format_node_row(node_code: str,
                    bus: dev.Bus,
                    aggregate: UcteBusAggregate) -> str:
    """
    Format one UCTE node record.

    :param node_code: Exported node code.
    :param bus: Source bus.
    :param aggregate: Aggregated node state.
    :return: Node row text.
    """
    geo_name: str = str(bus.name).strip()[:12]
    active_gen_text: str
    reactive_gen_text: str
    min_gen_mw_text: str
    max_gen_mw_text: str
    min_gen_mvar_text: str
    max_gen_mvar_text: str

    if aggregate.has_generation_record:
        active_gen_text = format_optional_float_width(aggregate.active_gen_mw, 7, 2)
        reactive_gen_text = format_optional_float_width(aggregate.reactive_gen_mvar, 7, 2)
    else:
        active_gen_text = " " * 7
        reactive_gen_text = " " * 7

    if aggregate.has_generation_limits:
        min_gen_mw_text = format_optional_float_width(aggregate.min_gen_mw, 7, 2)
        max_gen_mw_text = format_optional_float_width(aggregate.max_gen_mw, 7, 2)
        min_gen_mvar_text = format_optional_float_width(aggregate.min_gen_mvar, 7, 2)
        max_gen_mvar_text = format_optional_float_width(aggregate.max_gen_mvar, 7, 2)
    else:
        min_gen_mw_text = " " * 7
        max_gen_mw_text = " " * 7
        min_gen_mvar_text = " " * 7
        max_gen_mvar_text = " " * 7

    # The node parser first tries a strict fixed-width layout. The exporter
    # therefore writes the canonical field positions explicitly so all numeric
    # columns survive a round-trip without being shifted by whitespace.
    row_text: str = (
        f"{node_code:<8} "
        f"{geo_name:<12} "
        f"{aggregate.status:d} "
        f"{aggregate.node_type:d} "
        f"{format_optional_float_width(aggregate.voltage_reference_kv, 6, 2)} "
        f"{aggregate.active_load_mw:>7.2f} "
        f"{aggregate.reactive_load_mvar:>7.2f} "
        f"{active_gen_text} "
        f"{reactive_gen_text} "
        f"{min_gen_mw_text} "
        f"{max_gen_mw_text} "
        f"{min_gen_mvar_text} "
        f"{max_gen_mvar_text} "
        f"{'':>5} "
        f"{'':>7} "
        f"{'':>7} "
        f"{'':>7} "
        f"{aggregate.plant_type[:1]}"
    )
    return row_text.rstrip()


def get_line_current_limit_a(line: dev.Line, vnom_kv: float, t_idx: int | None) -> float:
    """
    Convert one VeraGrid line rate to a UCTE current limit.

    :param line: VeraGrid line.
    :param vnom_kv: Nominal voltage in kV.
    :param t_idx: Optional profile index.
    :return: Current limit in A or ``nan``.
    """
    rate_mva: float = float(line.get_rate_at(t_idx))
    if rate_mva > 0.0 and vnom_kv > 0.0:
        return (rate_mva / (math.sqrt(3.0) * vnom_kv)) * 1000.0
    else:
        return math.nan


def get_transformer_current_limit_a(transformer: dev.Transformer2W, t_idx: int | None) -> float:
    """
    Convert one VeraGrid transformer rate to a UCTE current limit.

    :param transformer: VeraGrid transformer.
    :param t_idx: Optional profile index.
    :return: Current limit in A or ``nan``.
    """
    rated_voltage_kv: float = max(float(transformer.HV), float(transformer.LV))
    rate_mva: float = float(transformer.get_rate_at(t_idx))
    if rate_mva > 0.0 and rated_voltage_kv > 0.0:
        return (rate_mva / (math.sqrt(3.0) * rated_voltage_kv)) * 1000.0
    else:
        return math.nan


def get_line_ucte_impedance(line: dev.Line, circuit: MultiCircuit) -> tuple[float, float, float]:
    """
    Convert one VeraGrid line impedance to UCTE units.

    :param line: VeraGrid line.
    :param circuit: Circuit base values.
    :return: Resistance in ohm, reactance in ohm, susceptance in uS.
    """
    base_voltage_kv: float = float(line.bus_from.Vnom)
    base_impedance_ohm: float = (base_voltage_kv * base_voltage_kv) / float(circuit.Sbase)
    resistance_ohm: float = float(line.R) * base_impedance_ohm
    reactance_ohm: float = float(line.X) * base_impedance_ohm
    susceptance_us: float = (float(line.B) / base_impedance_ohm) * 1e6
    return resistance_ohm, reactance_ohm, susceptance_us


def get_transformer_ucte_impedance(transformer: dev.Transformer2W,
                                   circuit: MultiCircuit,
                                   rated_voltage_1_kv: float) -> tuple[float, float, float, float]:
    """
    Convert one VeraGrid transformer impedance to UCTE units.

    :param transformer: VeraGrid transformer.
    :param circuit: Circuit base values.
    :param rated_voltage_1_kv: UCTE rated voltage on node1 side.
    :return: Resistance in ohm, reactance in ohm, susceptance in uS, conductance in uS.
    """
    base_impedance_ohm: float = (rated_voltage_1_kv * rated_voltage_1_kv) / float(circuit.Sbase)
    resistance_ohm: float = float(transformer.R) * base_impedance_ohm
    reactance_ohm: float = float(transformer.X) * base_impedance_ohm
    susceptance_us: float = (float(transformer.B) / base_impedance_ohm) * 1e6
    conductance_us: float = (float(transformer.G) / base_impedance_ohm) * 1e6
    return resistance_ohm, reactance_ohm, susceptance_us, conductance_us


def format_line_row(node_1: str,
                    node_2: str,
                    order_code: str,
                    status: int,
                    resistance_ohm: float,
                    reactance_ohm: float,
                    susceptance_us: float,
                    current_limit_a: float,
                    name: str) -> str:
    """
    Format one UCTE line record.

    :param node_1: First node code.
    :param node_2: Second node code.
    :param order_code: One-character order code.
    :param status: UCTE status code.
    :param resistance_ohm: Series resistance in ohm.
    :param reactance_ohm: Series reactance in ohm.
    :param susceptance_us: Total shunt susceptance in uS.
    :param current_limit_a: Current limit in A.
    :param name: Device name.
    :return: Line row text.
    """
    return (
        f"{node_1:<8} "
        f"{node_2:<8} "
        f"{order_code[:1]} "
        f"{status:d} "
        f"{format_optional_float_width(resistance_ohm, 6, 4)} "
        f"{format_optional_float_width(reactance_ohm, 6, 4)} "
        f"{format_optional_float_width(susceptance_us, 8, 4)} "
        f"{format_optional_float_width(current_limit_a, 6, 0)}  "
        f"{str(name).strip()}"
    ).rstrip()


def format_transformer_row(node_1: str,
                           node_2: str,
                           order_code: str,
                           status: int,
                           rated_voltage_1_kv: float,
                           rated_voltage_2_kv: float,
                           nominal_power_mva: float,
                           resistance_ohm: float,
                           reactance_ohm: float,
                           susceptance_us: float,
                           conductance_us: float,
                           current_limit_a: float,
                           name: str) -> str:
    """
    Format one UCTE transformer record.

    :param node_1: Non-regulated winding node code.
    :param node_2: Regulated winding node code.
    :param order_code: One-character order code.
    :param status: UCTE status code.
    :param rated_voltage_1_kv: Rated voltage on node1 side.
    :param rated_voltage_2_kv: Rated voltage on node2 side.
    :param nominal_power_mva: Nominal power in MVA.
    :param resistance_ohm: Series resistance in ohm.
    :param reactance_ohm: Series reactance in ohm.
    :param susceptance_us: Total shunt susceptance in uS.
    :param conductance_us: Total shunt conductance in uS.
    :param current_limit_a: Current limit in A.
    :param name: Device name.
    :return: Transformer row text.
    """
    return (
        f"{node_1:<8} {node_2:<8} {order_code} {status} "
        f"{rated_voltage_1_kv:.1f} {rated_voltage_2_kv:.1f} {nominal_power_mva:.1f} "
        f"{resistance_ohm:.6f} {reactance_ohm:.6f} {susceptance_us:.5f} "
        f"{format_optional_float(conductance_us, 4)} {format_optional_float(current_limit_a, 0)} "
        f"{str(name).strip()}"
    ).rstrip()


def write_comment_block(circuit: MultiCircuit,
                        t_idx: int | None,
                        file_pointer: TextIO) -> None:
    """
    Write the UCTE comment block.

    :param circuit: Circuit to export.
    :param t_idx: Optional profile index.
    :param file_pointer: Open output file.
    :return: None.
    """
    snapshot_datetime: datetime = get_snapshot_datetime(circuit=circuit, t_idx=t_idx)
    file_pointer.write(f"##C {snapshot_datetime.strftime('%Y.%m.%d')}\n")
    file_pointer.write(f"{str(circuit.name).strip()}\n")


def write_node_blocks_from_aggregates(circuit: MultiCircuit,
                                      bus_code_map: Dict[dev.Bus, str],
                                      aggregate_by_bus: Dict[dev.Bus, UcteBusAggregate],
                                      file_pointer: TextIO) -> None:
    """
    Write the UCTE node sections grouped by country block.

    :param circuit: Circuit to export.
    :param bus_code_map: Bus-to-node-code mapping.
    :param aggregate_by_bus: Precomputed bus aggregates.
    :param file_pointer: Open output file.
    :return: None.
    """
    buses_by_country: Dict[str, List[dev.Bus]] = dict()
    bus: dev.Bus
    for bus in circuit.get_buses():
        country_code: str = get_country_code(bus)
        bucket: List[dev.Bus] | None = buses_by_country.get(country_code, None)
        if bucket is None:
            buses_by_country[country_code] = [bus]
        else:
            bucket.append(bus)

    country_code: str
    for country_code in sorted(buses_by_country.keys()):
        file_pointer.write(f"##Z{country_code}\n")
        for bus in buses_by_country[country_code]:
            aggregate: UcteBusAggregate = aggregate_by_bus[bus]
            node_row: str = format_node_row(node_code=bus_code_map[bus],
                                            bus=bus,
                                            aggregate=aggregate)
            file_pointer.write(node_row + "\n")


def write_line_block(circuit: MultiCircuit,
                     bus_code_map: Dict[dev.Bus, str],
                     aggregate_by_bus: Dict[dev.Bus, UcteBusAggregate],
                     t_idx: int | None,
                     logger: Logger,
                     file_pointer: TextIO) -> None:
    """
    Write the UCTE line block, including switch couplers and fictitious shunts.

    :param circuit: Circuit to export.
    :param bus_code_map: Bus-to-node-code mapping.
    :param aggregate_by_bus: Precomputed bus aggregates.
    :param t_idx: Optional profile index.
    :param logger: Export logger.
    :param file_pointer: Open output file.
    :return: None.
    """
    file_pointer.write("##L\n")
    pair_counter: UcteBranchCounter = UcteBranchCounter()

    line: dev.Line
    for line in circuit.get_lines():
        if line.bus_from is None or line.bus_to is None:
            logger.add_warning("Skipping disconnected line in UCTE export", device=line.name)
        else:
            if line.bus_from.is_dc or line.bus_to.is_dc:
                logger.add_warning("Skipping DC line in UCTE export", device=line.name)
            else:
                if abs(float(line.bus_from.Vnom) - float(line.bus_to.Vnom)) <= 1e-6:
                    node_1: str = bus_code_map[line.bus_from]
                    node_2: str = bus_code_map[line.bus_to]
                    order_code: str = pair_counter.get_next_code(node_1=node_1, node_2=node_2, logger=logger)
                    status: int
                    if line.get_active_at(t_idx):
                        status = 0
                    else:
                        status = 8
                    resistance_ohm: float
                    reactance_ohm: float
                    susceptance_us: float
                    resistance_ohm, reactance_ohm, susceptance_us = get_line_ucte_impedance(line=line,
                                                                                             circuit=circuit)
                    current_limit_a: float = get_line_current_limit_a(line=line,
                                                                      vnom_kv=float(line.bus_from.Vnom),
                                                                      t_idx=t_idx)
                    line_row: str = format_line_row(node_1=node_1,
                                                    node_2=node_2,
                                                    order_code=order_code,
                                                    status=status,
                                                    resistance_ohm=resistance_ohm,
                                                    reactance_ohm=reactance_ohm,
                                                    susceptance_us=susceptance_us,
                                                    current_limit_a=current_limit_a,
                                                    name=line.name)
                    file_pointer.write(line_row + "\n")
                else:
                    logger.add_warning("Skipping cross-voltage line in UCTE export",
                                       device=line.name,
                                       value=f"{line.bus_from.Vnom} != {line.bus_to.Vnom}")

    switch_obj: dev.Switch
    for switch_obj in circuit.get_switches():
        if switch_obj.bus_from is None or switch_obj.bus_to is None:
            logger.add_warning("Skipping disconnected switch in UCTE export", device=switch_obj.name)
        else:
            if switch_obj.bus_from.is_dc or switch_obj.bus_to.is_dc:
                logger.add_warning("Skipping DC switch in UCTE export", device=switch_obj.name)
            else:
                if abs(float(switch_obj.bus_from.Vnom) - float(switch_obj.bus_to.Vnom)) <= 1e-6:
                    node_1 = bus_code_map[switch_obj.bus_from]
                    node_2 = bus_code_map[switch_obj.bus_to]
                    order_code = pair_counter.get_next_code(node_1=node_1, node_2=node_2, logger=logger)
                    if switch_obj.get_active_at(t_idx):
                        status = 2
                    else:
                        status = 7
                    current_limit_a: float
                    if float(switch_obj.rated_current) > 0.0:
                        current_limit_a = float(switch_obj.rated_current) * 1000.0
                    else:
                        current_limit_a = math.nan
                    switch_row: str = format_line_row(node_1=node_1,
                                                      node_2=node_2,
                                                      order_code=order_code,
                                                      status=status,
                                                      resistance_ohm=0.0,
                                                      reactance_ohm=0.0,
                                                      susceptance_us=0.0,
                                                      current_limit_a=current_limit_a,
                                                      name=switch_obj.name)
                    file_pointer.write(switch_row + "\n")
                else:
                    logger.add_warning("Skipping cross-voltage switch in UCTE export",
                                       device=switch_obj.name,
                                       value=f"{switch_obj.bus_from.Vnom} != {switch_obj.bus_to.Vnom}")

    bus: dev.Bus
    for bus in circuit.get_buses():
        aggregate: UcteBusAggregate = aggregate_by_bus[bus]
        if abs(aggregate.shunt_b_mvar) > 1e-9:
            if bus.Vnom > 0.0:
                shunt_node_code: str = build_shunt_node_code(bus_code_map[bus])
                order_code = pair_counter.get_next_code(node_1=bus_code_map[bus], node_2=shunt_node_code, logger=logger)
                susceptance_us = (aggregate.shunt_b_mvar / (float(bus.Vnom) * float(bus.Vnom))) * 1e6
                shunt_row: str = format_line_row(node_1=bus_code_map[bus],
                                                 node_2=shunt_node_code,
                                                 order_code=order_code,
                                                 status=0,
                                                 resistance_ohm=0.0,
                                                 reactance_ohm=0.05,
                                                 susceptance_us=susceptance_us,
                                                 current_limit_a=math.nan,
                                                 name=f"{bus.name} fict. shunt")
                file_pointer.write(shunt_row + "\n")
            else:
                logger.add_warning("Skipping bus shunt in UCTE export because the bus nominal voltage is invalid",
                                   device=bus.name,
                                   value=bus.Vnom)
        else:
            pass


def write_transformer_block(circuit: MultiCircuit,
                            bus_code_map: Dict[dev.Bus, str],
                            t_idx: int | None,
                            logger: Logger,
                            file_pointer: TextIO) -> None:
    """
    Write the UCTE transformer block.

    :param circuit: Circuit to export.
    :param bus_code_map: Bus-to-node-code mapping.
    :param t_idx: Optional profile index.
    :param logger: Export logger.
    :param file_pointer: Open output file.
    :return: None.
    """
    file_pointer.write("##T\n")
    pair_counter: UcteBranchCounter = UcteBranchCounter()

    transformer: dev.Transformer2W
    for transformer in circuit.get_transformers2w():
        if transformer.bus_from is None or transformer.bus_to is None:
            logger.add_warning("Skipping disconnected transformer in UCTE export", device=transformer.name)
        else:
            if transformer.bus_from.is_dc or transformer.bus_to.is_dc:
                logger.add_warning("Skipping DC transformer in UCTE export", device=transformer.name)
            else:
                legacy_orientation: bool = use_legacy_transformer_orientation(bus_from=transformer.bus_from,
                                                                              bus_to=transformer.bus_to)
                node_1: str
                node_2: str
                if legacy_orientation:
                    # Standard country-coded UCTE files map node1 to the
                    # non-regulated winding and node2 to the regulated one.
                    node_1 = bus_code_map[transformer.bus_to]
                    node_2 = bus_code_map[transformer.bus_from]
                else:
                    # IEEE-like synthetic UCTE data is interpreted directly as
                    # node1 -> node2 by the importer, so preserve that order.
                    node_1 = bus_code_map[transformer.bus_from]
                    node_2 = bus_code_map[transformer.bus_to]

                order_code: str = pair_counter.get_next_code(node_1=node_1, node_2=node_2, logger=logger)
                status: int
                if transformer.get_active_at(t_idx):
                    status = 0
                else:
                    status = 8

                # Without explicit UCTE regulation rows, fixed taps are carried
                # by rated_voltage1 in the same way the importer already
                # expects.
                tap_module: float = float(transformer.get_tap_module_at(t_idx))
                rated_voltage_1_kv: float
                if legacy_orientation:
                    if abs(tap_module) > 1e-9:
                        rated_voltage_1_kv = float(transformer.bus_to.Vnom) / tap_module
                    else:
                        rated_voltage_1_kv = float(transformer.bus_to.Vnom)
                else:
                    rated_voltage_1_kv = float(transformer.bus_from.Vnom) * tap_module
                rated_voltage_2_kv: float
                if legacy_orientation:
                    rated_voltage_2_kv = float(transformer.bus_from.Vnom)
                else:
                    rated_voltage_2_kv = float(transformer.bus_to.Vnom)

                if abs(float(transformer.get_tap_phase_at(t_idx))) > 1e-9:
                    logger.add_warning("UCTE export is ignoring transformer phase shifting because no regulation rows are emitted yet",
                                       device=transformer.name,
                                       value=transformer.get_tap_phase_at(t_idx))
                else:
                    pass

                if transformer.tap_module_control_mode != TapModuleControl.fixed:
                    logger.add_warning("UCTE export is flattening transformer tap control to a fixed rated-voltage ratio",
                                       device=transformer.name,
                                       value=str(transformer.tap_module_control_mode))
                else:
                    pass

                if transformer.tap_phase_control_mode != TapPhaseControl.fixed:
                    logger.add_warning("UCTE export is flattening transformer phase control to the fixed transformer state",
                                       device=transformer.name,
                                       value=str(transformer.tap_phase_control_mode))
                else:
                    pass

                resistance_ohm: float
                reactance_ohm: float
                susceptance_us: float
                conductance_us: float
                resistance_ohm, reactance_ohm, susceptance_us, conductance_us = get_transformer_ucte_impedance(
                    transformer=transformer,
                    circuit=circuit,
                    rated_voltage_1_kv=rated_voltage_1_kv,
                )
                nominal_power_mva: float
                if float(transformer.Sn) > 0.0:
                    nominal_power_mva = float(transformer.Sn)
                elif float(transformer.get_rate_at(t_idx)) > 0.0:
                    nominal_power_mva = float(transformer.get_rate_at(t_idx))
                else:
                    nominal_power_mva = 100.0
                current_limit_a: float = get_transformer_current_limit_a(transformer=transformer, t_idx=t_idx)
                transformer_row: str = format_transformer_row(node_1=node_1,
                                                              node_2=node_2,
                                                              order_code=order_code,
                                                              status=status,
                                                              rated_voltage_1_kv=rated_voltage_1_kv,
                                                              rated_voltage_2_kv=rated_voltage_2_kv,
                                                              nominal_power_mva=nominal_power_mva,
                                                              resistance_ohm=resistance_ohm,
                                                              reactance_ohm=reactance_ohm,
                                                              susceptance_us=susceptance_us,
                                                              conductance_us=conductance_us,
                                                              current_limit_a=current_limit_a,
                                                              name=transformer.name)
                file_pointer.write(transformer_row + "\n")


def write_empty_regulation_blocks(file_pointer: TextIO) -> None:
    """
    Write the optional UCTE blocks that are not populated yet.

    :param file_pointer: Open output file.
    :return: None.
    """
    file_pointer.write("##R\n")
    file_pointer.write("##TT\n")
    file_pointer.write("##E\n")


def write_ucte(file_name: str,
               circuit: MultiCircuit,
               t_idx: int | None = None,
               logger: Logger | None = None) -> Logger:
    """
    Write one VeraGrid circuit as one UCTE text file.

    :param file_name: Target file path.
    :param circuit: Circuit to export.
    :param t_idx: Optional profile index. ``None`` means snapshot export.
    :param logger: Optional logger.
    :return: Logger with export messages.
    """
    export_logger: Logger
    if logger is None:
        export_logger = Logger()
    else:
        export_logger = logger

    bus_code_map: Dict[dev.Bus, str] = build_bus_node_code_map(circuit=circuit, logger=export_logger)
    bus_injections: Dict[dev.Bus, Dict[object, List[object]]] = circuit.get_injection_devices_grouped_by_bus()
    aggregate_by_bus: Dict[dev.Bus, UcteBusAggregate] = dict()
    bus: dev.Bus
    for bus in circuit.get_buses():
        aggregate_by_bus[bus] = build_bus_aggregate(circuit=circuit,
                                                    bus=bus,
                                                    bus_injections=bus_injections,
                                                    t_idx=t_idx,
                                                    logger=export_logger)

    with open(file_name, "w", encoding="utf-8") as file_pointer:
        write_comment_block(circuit=circuit, t_idx=t_idx, file_pointer=file_pointer)
        write_node_blocks_from_aggregates(circuit=circuit,
                                          bus_code_map=bus_code_map,
                                          aggregate_by_bus=aggregate_by_bus,
                                          file_pointer=file_pointer)
        write_line_block(circuit=circuit,
                         bus_code_map=bus_code_map,
                         aggregate_by_bus=aggregate_by_bus,
                         t_idx=t_idx,
                         logger=export_logger,
                         file_pointer=file_pointer)
        write_transformer_block(circuit=circuit,
                                bus_code_map=bus_code_map,
                                t_idx=t_idx,
                                logger=export_logger,
                                file_pointer=file_pointer)
        write_empty_regulation_blocks(file_pointer=file_pointer)

    return export_logger
