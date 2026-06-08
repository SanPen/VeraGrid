# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import math
from collections import defaultdict
from typing import Dict

import numpy as np

import VeraGridEngine.Devices as dev
from VeraGridEngine.Devices.Branches.sequence_line_type import get_line_impedances_with_b
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.IO.ucte.devices.ucte_base import coalesce_number, is_defined_number
from VeraGridEngine.IO.ucte.devices.ucte_circuit import UcteCircuit
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import TapChangerTypes, TapModuleControl, TapPhaseControl, GeneratorControlMode


def is_xnode_code(node_code: str) -> bool:
    return len(node_code) > 0 and node_code[0] == "X"


def is_fictitious_shunt_code(node_code: str) -> bool:
    return node_code.strip().endswith("Q")


def is_fictitious_shunt_node(ucte_node) -> bool:
    geo_name = (ucte_node.geo_name or "").strip().lower()
    return geo_name == "fict. shunt" or is_fictitious_shunt_code(ucte_node.node_code)


def is_canonical_ucte_node_code(node_code: str) -> bool:
    code = (node_code or "")
    if len(code) != 8:
        return False
    if any(ch.isspace() for ch in code):
        return False
    return True


def is_standard_ucte_country_code(country_code: str) -> bool:
    code = (country_code or "").strip()
    return len(code) == 2 and code.isalpha() and code.upper() == code and code != "XX"


def get_default_power_limit() -> float:
    return 9999.0


def get_current_limit_a(current_limit: float | None) -> float:
    return float(coalesce_number(current_limit, 9999.0))


def get_current_limit_ka(current_limit: float | None) -> float:
    return get_current_limit_a(current_limit) / 1000.0


def same_nominal_voltage(bus_f: dev.Bus, bus_t: dev.Bus, tol: float = 1e-6) -> bool:
    return abs(bus_f.Vnom - bus_t.Vnom) <= tol


def compute_switch_rate(bus_f: dev.Bus, bus_t: dev.Bus, current_limit: float | None) -> float:
    return max(bus_f.Vnom, bus_t.Vnom) * get_current_limit_ka(current_limit) * np.sqrt(3.0)


def build_xnode_active_line_counts(ucte_grid: UcteCircuit, logger: Logger) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)

    for ucte_line in ucte_grid.lines:
        active, _ = ucte_line.is_active_and_reducible(logger=logger)
        if not active:
            continue

        if is_xnode_code(ucte_line.node1) and not is_xnode_code(ucte_line.node2):
            counts[ucte_line.node1] += 1
        elif is_xnode_code(ucte_line.node2) and not is_xnode_code(ucte_line.node1):
            counts[ucte_line.node2] += 1

    return counts


def build_technologies(grid: MultiCircuit) -> dict[str, dev.Technology]:
    tech_dict = {
        "H": dev.Technology(name="Hydro"),
        "N": dev.Technology(name="Nuclear"),
        "L": dev.Technology(name="lignite"),
        "C": dev.Technology(name="hard coal"),
        "G": dev.Technology(name="Gas"),
        "O": dev.Technology(name="Oil"),
        "W": dev.Technology(name="Wind"),
        "F": dev.Technology(name="further"),
    }

    for elm in tech_dict.values():
        grid.add_technology(obj=elm)

    return tech_dict


def discover_nominal_voltages(ucte_grid: UcteCircuit) -> Dict[str, float]:
    """
    Attempt to discover the nominal voltage for each level character.
    """
    node_vref_by_level: Dict[str, list[float]] = defaultdict(list)
    trafo_rated_by_level: Dict[str, list[float]] = defaultdict(list)

    for node in ucte_grid.nodes:
        if is_fictitious_shunt_node(node):
            continue
        if len(node.node_code) >= 7 and is_defined_number(node.voltage_reference) and node.voltage_reference > 0:
            node_vref_by_level[node.node_code[6]].append(float(node.voltage_reference))

    for trafo in ucte_grid.transformers:
        if len(trafo.node1) >= 7 and trafo.rated_voltage1 > 0:
            trafo_rated_by_level[trafo.node1[6]].append(float(trafo.rated_voltage1))
        if len(trafo.node2) >= 7 and trafo.rated_voltage2 > 0:
            trafo_rated_by_level[trafo.node2[6]].append(float(trafo.rated_voltage2))

    candidate_nominal_levels = np.array(
        [1.0, 11.0, 15.0, 20.0, 22.0, 27.0, 33.0, 66.0, 70.0, 110.0, 120.0, 132.0,
         138.0, 150.0, 220.0, 330.0, 380.0, 500.0, 750.0]
    )

    vnom_map: Dict[str, float] = {}
    for level, vrefs in node_vref_by_level.items():
        vrefs_arr = np.array(vrefs, dtype=float)
        rated_arr = np.array(trafo_rated_by_level.get(level, []), dtype=float)

        best_score = float("inf")
        best_level = None
        for nominal in candidate_nominal_levels:
            # Keep operating voltages around 1.0 p.u.
            vm_penalty = float(np.median(np.abs(vrefs_arr / nominal - 1.0)))

            # Prefer nominal levels that keep transformer fixed taps in a plausible range.
            tap_penalty = 0.0
            if rated_arr.size > 0:
                tap = rated_arr / nominal
                tap_penalty = float(
                    np.mean(np.maximum(0.0, 0.9 - tap) + np.maximum(0.0, tap - 1.1))
                )

            score = vm_penalty + 4.0 * tap_penalty
            if score < best_score:
                best_score = score
                best_level = float(nominal)

        if best_level is not None:
            vnom_map[level] = best_level

    return vnom_map


def snap_nominal_voltage_from_reference(voltage_reference: float) -> float:
    # Conservative set of practical nominal levels used in UCTE/ENTSO-E style grids.
    nominal_levels = np.array([1.0, 11.0, 15.0, 20.0, 22.0, 33.0, 66.0, 70.0, 110.0, 120.0,
                               132.0, 138.0, 150.0, 220.0, 330.0, 380.0, 400.0, 500.0, 750.0])
    idx = int(np.argmin(np.abs(nominal_levels - float(voltage_reference))))
    return float(nominal_levels[idx])


def repair_nominal_voltages_from_references(ucte_grid: UcteCircuit, logger: Logger):
    """
    Fix clearly inconsistent nominal voltages in non-canonical UCTE variants.

    If Vref/Vnom is outside a realistic range for steady-state operation,
    infer Vnom from Vref directly using a conservative nominal-level palette.
    """
    for node in ucte_grid.nodes:
        # Keep strict semantics for canonical UCTE IDs in standard country blocks.
        # Rescue malformed/non-canonical variants (e.g., synthetic IEEE fixtures).
        if is_canonical_ucte_node_code(node.node_code) and is_standard_ucte_country_code(node.current_country):
            continue

        if not (is_defined_number(node.voltage_reference) and node.voltage_reference > 0 and node.voltage > 0):
            continue

        vm0 = float(node.voltage_reference) / float(node.voltage)
        if 0.8 <= vm0 <= 1.2:
            continue

        snapped_vnom = snap_nominal_voltage_from_reference(node.voltage_reference)
        snapped_vm0 = float(node.voltage_reference) / float(snapped_vnom)

        # Apply only when the repaired value becomes plausible.
        if 0.8 <= snapped_vm0 <= 1.2:
            logger.add_warning("Adjusted UCTE node nominal voltage from voltage reference",
                               device=node.node_code,
                               value=f"{node.voltage} kV -> {snapped_vnom} kV (Vref={node.voltage_reference} kV)")
            node.voltage = snapped_vnom
            node.normalize(logger)


def parse_nodes(ucte_grid: UcteCircuit, grid: MultiCircuit, logger: Logger) -> Dict[str, dev.Bus]:
    """
    Create buses and their injections.
    """
    bus_dict: Dict[str, dev.Bus] = dict()
    tech_dict = build_technologies(grid)
    country_dict: dict[str, dev.Country] = dict()

    for ucte_elm in ucte_grid.nodes:
        if is_fictitious_shunt_node(ucte_elm):
            continue

        if ucte_elm.current_country not in ("", "XX"):
            country = country_dict.get(ucte_elm.current_country, None)

            if country is None:
                country = dev.Country(name=ucte_elm.current_country)
                country_dict[ucte_elm.current_country] = country
                grid.add_country(country)
        else:
            country = None

        name = ucte_elm.geo_name or ucte_elm.node_code

        if ucte_elm.voltage <= 0:
            logger.add_error("Bus nominal voltage is invalid",
                             device_class="Bus",
                             device=ucte_elm.node_code,
                             value=ucte_elm.voltage,
                             expected_value=">0")

        vm0 = 1.0
        if is_defined_number(ucte_elm.voltage_reference) and ucte_elm.voltage_reference > 0 and ucte_elm.voltage > 0:
            vm0 = float(ucte_elm.voltage_reference) / float(ucte_elm.voltage)

        elm = dev.Bus(
            name=name,
            code=ucte_elm.node_code,
            active=True,
            is_slack=ucte_elm.node_type == 3,
            is_internal=is_xnode_code(ucte_elm.node_code),
            Vnom=ucte_elm.voltage,
            Vm0=vm0,
            country=country,
        )

        bus_role = "equivalent" if ucte_elm.status != 0 else "real"
        if is_xnode_code(ucte_elm.node_code):
            bus_role += " xnode"
        elm.comment = bus_role

        grid.add_bus(obj=elm)
        bus_dict[elm.code] = elm

        if ucte_elm.has_load():
            ld = dev.Load(
                name=elm.code,
                P=ucte_elm.active_load,
                Q=ucte_elm.reactive_load,
            )
            grid.add_load(bus=elm, api_obj=ld)

        if ucte_elm.has_gen():
            if ucte_elm.is_regulating_voltage() and is_defined_number(ucte_elm.voltage_reference):
                control_mode = GeneratorControlMode.V
            else:
                control_mode = GeneratorControlMode.Q
            pmin = -coalesce_number(ucte_elm.max_gen_mw, get_default_power_limit())
            pmax = -coalesce_number(ucte_elm.min_gen_mw, -get_default_power_limit())

            qmin_ucte = ucte_elm.min_gen_mvar
            qmax_ucte = ucte_elm.max_gen_mvar

            # Handle potentially missing reactive limits in non-standard UCTE files
            if ((control_mode == GeneratorControlMode.V)
                    and (not is_defined_number(qmin_ucte) or qmin_ucte == 0.0)
                    and (not is_defined_number(qmax_ucte) or qmax_ucte == 0.0)):
                qmin = -get_default_power_limit()
                qmax = get_default_power_limit()
            else:
                qmin = -coalesce_number(ucte_elm.max_gen_mvar, get_default_power_limit())
                qmax = -coalesce_number(ucte_elm.min_gen_mvar, -get_default_power_limit())

            gen = dev.Generator(
                name=elm.code,
                code=elm.code,
                P=-coalesce_number(ucte_elm.active_gen, 0.0),
                Q=-coalesce_number(ucte_elm.reactive_gen, 0.0),
                Pmin=pmin,
                Pmax=pmax,
                Qmin=qmin,
                Qmax=qmax,
                vset=vm0 if (control_mode == GeneratorControlMode.V) else 1.0,
                control_mode=control_mode,
            )

            tech = tech_dict.get(ucte_elm.plant_type, None)
            if tech is not None:
                gen.associate_technology(tech, 1.0)

            grid.add_generator(bus=elm, api_obj=gen)

    return bus_dict


def add_switch(grid: MultiCircuit,
               code: str,
               name: str,
               current_limit: float | None,
               bus_f: dev.Bus,
               bus_t: dev.Bus,
               active: bool,
               reducible: bool):
    switch = dev.Switch(
        bus_from=bus_f,
        bus_to=bus_t,
        code=code,
        active=active,
        retained=not reducible,
        normal_open=not active,
        rated_current=get_current_limit_ka(current_limit),
        rate=compute_switch_rate(bus_f, bus_t, current_limit),
        name=name,
    )
    grid.add_switch(obj=switch)


def add_switch_from_line(grid: MultiCircuit, ucte_elm, bus_f: dev.Bus, bus_t: dev.Bus, active: bool, reducible: bool):
    add_switch(
        grid=grid,
        code=ucte_elm.order_code,
        name=ucte_elm.name or f"{ucte_elm.node1} {ucte_elm.node2}",
        current_limit=ucte_elm.current_limit,
        bus_f=bus_f,
        bus_t=bus_t,
        active=active,
        reducible=reducible,
    )


def add_switch_from_transformer(grid: MultiCircuit,
                                ucte_elm,
                                bus_f: dev.Bus,
                                bus_t: dev.Bus,
                                active: bool,
                                reducible: bool):
    add_switch(
        grid=grid,
        code=ucte_elm.order_code,
        name=ucte_elm.name or f"{ucte_elm.node1} {ucte_elm.node2}",
        current_limit=ucte_elm.current_limit,
        bus_f=bus_f,
        bus_t=bus_t,
        active=active,
        reducible=reducible,
    )


def add_standard_line(grid: MultiCircuit, ucte_elm, bus_f: dev.Bus, bus_t: dev.Bus, active: bool, reducible: bool,
                      logger: Logger):
    elm = dev.Line(
        bus_from=bus_f,
        bus_to=bus_t,
        code=ucte_elm.order_code,
        active=active,
        name=ucte_elm.name,
    )
    elm.reducible = reducible

    b_siemens_total = ucte_elm.susceptance * 1e-6  # uS to S
    c_nf = b_siemens_total / (2 * np.pi * grid.fBase * 1e-9)

    elm.fill_design_properties(
        r_ohm=ucte_elm.resistance,
        x_ohm=ucte_elm.reactance,
        c_nf=c_nf,
        length=1.0,
        Imax=get_current_limit_ka(ucte_elm.current_limit),
        freq=grid.fBase,
        Sbase=grid.Sbase,
        logger=logger
    )

    grid.add_line(obj=elm, logger=logger)


def is_fictitious_shunt_line(ucte_elm, tol: float = 1e-9) -> bool:
    return (
            (is_fictitious_shunt_code(ucte_elm.node1) or is_fictitious_shunt_code(ucte_elm.node2))
            and abs(ucte_elm.resistance) <= tol
            and abs(ucte_elm.reactance - 0.05) <= 1e-6
            and abs(ucte_elm.susceptance) > tol
    )


def add_fixed_shunt_from_ucte_line(grid: MultiCircuit, ucte_elm, bus: dev.Bus):
    # UCTE branch susceptance is in uS; convert to MVAr at V=1.0 p.u.
    b_mvar = ucte_elm.susceptance * 1e-6 * (bus.Vnom ** 2)
    shunt = dev.Shunt(
        name=ucte_elm.name or f"{bus.code}_shunt",
        code=ucte_elm.order_code,
        G=0.0,
        B=b_mvar,
        active=True,
    )
    grid.add_shunt(bus=bus, api_obj=shunt)


def should_import_mismatch_line_as_transformer(ucte_elm, bus_f: dev.Bus, bus_t: dev.Bus) -> bool:
    node1_is_canonical = is_canonical_ucte_node_code(ucte_elm.node1)
    node2_is_canonical = is_canonical_ucte_node_code(ucte_elm.node2)
    country_f = bus_f.country.name if bus_f.country is not None else ""
    country_t = bus_t.country.name if bus_t.country is not None else ""
    countries_are_standard = is_standard_ucte_country_code(country_f) and is_standard_ucte_country_code(country_t)
    return not (node1_is_canonical and node2_is_canonical and countries_are_standard)


def use_legacy_ucte_transformer_orientation(ucte_elm, bus_node1: dev.Bus, bus_node2: dev.Bus) -> bool:
    country_1 = bus_node1.country.name if bus_node1.country is not None else ""
    country_2 = bus_node2.country.name if bus_node2.country is not None else ""
    countries_are_standard = is_standard_ucte_country_code(country_1) and is_standard_ucte_country_code(country_2)
    return countries_are_standard


def add_transformer_from_mismatch_line(grid: MultiCircuit, ucte_elm, bus_f: dev.Bus, bus_t: dev.Bus):
    vbase = bus_f.Vnom if bus_f.Vnom > 0 else max(bus_f.Vnom, bus_t.Vnom)
    R, X, B, rate = get_line_impedances_with_b(
        r_ohm=ucte_elm.resistance,
        x_ohm=ucte_elm.reactance,
        b_us=ucte_elm.susceptance,
        length=1.0,
        Imax=get_current_limit_a(ucte_elm.current_limit),
        Sbase=grid.Sbase,
        Vnom=vbase,
    )

    tr = dev.Transformer2W(
        bus_from=bus_f,
        bus_to=bus_t,
        code=ucte_elm.order_code,
        active=True,
        name=ucte_elm.name or f"{ucte_elm.node1} {ucte_elm.node2}",
        HV=max(bus_f.Vnom, bus_t.Vnom),
        LV=min(bus_f.Vnom, bus_t.Vnom),
        nominal_power=100.0,
        r=R,
        x=X,
        b=B,
        rate=rate,
    )
    grid.add_transformer2w(obj=tr)


def parse_lines(ucte_grid: UcteCircuit, grid: MultiCircuit, bus_dict: Dict[str, dev.Bus], logger: Logger):
    """
    Parse UCTE lines and couplers.
    """
    xnode_active_line_counts = build_xnode_active_line_counts(ucte_grid, logger)
    unsupported_xnodes: set[str] = set()

    for ucte_elm in ucte_grid.lines:
        bus_f = bus_dict.get(ucte_elm.node1, None)
        bus_t = bus_dict.get(ucte_elm.node2, None)

        if is_fictitious_shunt_line(ucte_elm):
            if bus_f is not None and not is_fictitious_shunt_code(ucte_elm.node1):
                add_fixed_shunt_from_ucte_line(grid=grid, ucte_elm=ucte_elm, bus=bus_f)
                continue
            if bus_t is not None and not is_fictitious_shunt_code(ucte_elm.node2):
                add_fixed_shunt_from_ucte_line(grid=grid, ucte_elm=ucte_elm, bus=bus_t)
                continue

        if bus_f is None or bus_t is None:
            if bus_f is None:
                logger.add_error("Line from bus not found",
                                 device=ucte_elm.name,
                                 device_property="node1",
                                 value=ucte_elm.node1)
            if bus_t is None:
                logger.add_error("Line to bus not found",
                                 device=ucte_elm.name,
                                 device_property="node2",
                                 value=ucte_elm.node2)
            continue

        active, reducible = ucte_elm.is_active_and_reducible(logger=logger)
        node1_is_xnode = is_xnode_code(ucte_elm.node1)
        node2_is_xnode = is_xnode_code(ucte_elm.node2)

        if node1_is_xnode and node2_is_xnode:
            logger.add_error("Line between 2 X-nodes is not supported",
                             device=ucte_elm.name or f"{ucte_elm.node1} {ucte_elm.node2}",
                             value=f"{ucte_elm.node1} {ucte_elm.node2}")
            continue

        xnode_code = ucte_elm.node1 if node1_is_xnode else (ucte_elm.node2 if node2_is_xnode else "")
        if xnode_code != "" and xnode_active_line_counts.get(xnode_code, 0) > 2:
            if xnode_code not in unsupported_xnodes:
                unsupported_xnodes.add(xnode_code)
                logger.add_error("X-node connected to more than two active lines is not supported",
                                 device=xnode_code,
                                 value=xnode_active_line_counts.get(xnode_code, 0),
                                 expected_value="<=2")
            continue

        if bus_f.code == bus_t.code:
            logger.add_warning("Ignoring self-connected UCTE line/coupler",
                               device=ucte_elm.name or bus_f.code,
                               value=bus_f.code)
            continue

        if not same_nominal_voltage(bus_f, bus_t):
            if should_import_mismatch_line_as_transformer(ucte_elm=ucte_elm, bus_f=bus_f, bus_t=bus_t):
                logger.add_warning("Importing cross-voltage UCTE line as transformer in non-canonical data",
                                   device=ucte_elm.name or f"{ucte_elm.node1} {ucte_elm.node2}",
                                   value=f"{bus_f.Vnom} != {bus_t.Vnom}")
                add_transformer_from_mismatch_line(grid=grid, ucte_elm=ucte_elm, bus_f=bus_f, bus_t=bus_t)
                continue
            else:
                logger.add_error("UCTE line/coupler endpoints have different nominal voltages",
                                 device=ucte_elm.name or f"{ucte_elm.node1} {ucte_elm.node2}",
                                 value=f"{bus_f.Vnom} != {bus_t.Vnom}")
                continue

        is_switch = reducible

        if is_switch:
            add_switch_from_line(grid, ucte_elm, bus_f, bus_t, active, reducible)
        else:
            add_standard_line(grid, ucte_elm, bus_f, bus_t, active, reducible, logger)


def has_zero_transformer_impedance(ucte_elm, tol: float = 1e-9) -> bool:
    conductance = ucte_elm.conductance if is_defined_number(ucte_elm.conductance) else 0.0
    return (
            abs(ucte_elm.resistance) <= tol
            and abs(ucte_elm.reactance) <= tol
            and abs(ucte_elm.susceptance) <= tol
            and abs(conductance) <= tol
    )


def compute_tap_span(regulator, tap_tables) -> tuple[int, int]:
    tap_positions: list[int] = [0]

    if regulator is not None:
        if regulator.n1 is not None:
            tap_positions.extend([-regulator.n1, regulator.n1])
        if regulator.n1_prime is not None:
            tap_positions.append(regulator.n1_prime)
        if regulator.n2 is not None:
            tap_positions.extend([-regulator.n2, regulator.n2])
        if regulator.n2_prime is not None:
            tap_positions.append(regulator.n2_prime)

    for tap_table in tap_tables:
        tap_positions.append(tap_table.tap_position)

    return min(tap_positions), max(tap_positions)


def choose_tap_number(regulator) -> int:
    if regulator is None:
        return 0

    if regulator.has_angle_regulation() and regulator.n2_prime is not None:
        return regulator.n2_prime

    if regulator.has_phase_regulation() and regulator.n1_prime is not None:
        return regulator.n1_prime

    return 0


def build_tap_changer_type(regulator) -> TapChangerTypes:
    if regulator is None:
        return TapChangerTypes.NoRegulation

    if regulator.has_angle_regulation():
        if regulator.regulation_type == "SYMM":
            return TapChangerTypes.Symmetrical
        return TapChangerTypes.Asymmetrical

    if regulator.has_phase_regulation():
        return TapChangerTypes.VoltageRegulation

    return TapChangerTypes.NoRegulation


def build_current_tap_state(regulator, tap_type: TapChangerTypes) -> tuple[float, float]:
    tap_module = 1.0
    tap_phase = 0.0

    if regulator is not None and regulator.has_phase_regulation() and regulator.n1_prime is not None:
        tap_module = 1.0 / (1.0 + regulator.n1_prime * regulator.delta_u1 / 100.0)

    if regulator is not None and regulator.has_angle_regulation():
        tmp_tap_changer = dev.TapChanger(
            total_positions=max(2 * abs(regulator.n2 or 0) + 1, 1),
            neutral_position=abs(regulator.n2 or 0),
            normal_position=abs(regulator.n2 or 0) + (regulator.n2_prime or 0),
            dV=coalesce_number(regulator.delta_u2, 0.0) / 100.0,
            asymmetry_angle=coalesce_number(regulator.theta, 90.0),
            tc_type=tap_type,
        )
        tmp_tap_changer.tap_position = abs(regulator.n2 or 0) + (regulator.n2_prime or 0)
        tap_phase = tmp_tap_changer.get_tap_phase()

        if not regulator.has_phase_regulation():
            tap_module = tmp_tap_changer.get_tap_module()

    return tap_module, tap_phase


def apply_tap_table(elm: dev.Transformer2W,
                    ucte_elm,
                    tap_tables,
                    low_tap_position: int,
                    current_tap_number: int,
                    logger: Logger):
    if not tap_tables:
        return

    tap_data = elm.tap_changer.to_dict()
    re_corr = np.ones(elm.tap_changer.total_positions)
    im_corr = np.ones(elm.tap_changer.total_positions)

    for tap_table in tap_tables:
        idx = tap_table.tap_position - low_tap_position
        if not 0 <= idx < elm.tap_changer.total_positions:
            continue

        if abs(ucte_elm.resistance) > 1e-12:
            re_corr[idx] = tap_table.resistance / ucte_elm.resistance

        if abs(ucte_elm.reactance) > 1e-12:
            im_corr[idx] = tap_table.reactance / ucte_elm.reactance

    tap_data["impedance_correction_real"] = re_corr.tolist()
    tap_data["impedance_correction_imag"] = im_corr.tolist()
    tap_data["tap_position"] = current_tap_number - low_tap_position
    elm.tap_changer.parse(tap_data, logger=logger)

    current_row = next((row for row in tap_tables if row.tap_position == current_tap_number), None)
    if current_row is not None:
        elm.tap_module = 1.0 / (1.0 + current_row.delta_u / 100.0)
        elm.tap_phase = np.deg2rad(current_row.phase_shift)


def build_transformer_tap_data(ucte_elm,
                               regulator,
                               tap_tables,
                               bus_f: dev.Bus,
                               bus_t: dev.Bus,
                               invert_fixed_tap: bool,
                               logger: Logger):
    low_tap_position, high_tap_position = compute_tap_span(regulator, tap_tables)
    total_positions = max(high_tap_position - low_tap_position + 1, 1)
    neutral_position = -low_tap_position
    current_tap_number = choose_tap_number(regulator)
    current_tap_index = current_tap_number - low_tap_position
    tap_type = build_tap_changer_type(regulator)

    tc_dv = 0.01
    tc_asymmetry_angle = 90.0
    tap_module_control_mode = TapModuleControl.fixed
    tap_phase_control_mode = TapPhaseControl.fixed
    vset = 1.0
    pset = 0.0

    if regulator is not None:
        if regulator.has_angle_regulation():
            tc_dv = coalesce_number(regulator.delta_u2, 0.0) / 100.0
            tc_asymmetry_angle = coalesce_number(regulator.theta, 90.0)

            if is_defined_number(regulator.p):
                tap_phase_control_mode = TapPhaseControl.Pf
                pset = -float(regulator.p)

        elif regulator.has_phase_regulation():
            tc_dv = -coalesce_number(regulator.delta_u1, 0.0) / 100.0

        if regulator.has_phase_regulation() and is_defined_number(regulator.u1) and bus_f.Vnom > 0:
            tap_module_control_mode = TapModuleControl.Vm
            vset = float(regulator.u1) / float(bus_f.Vnom)

    tap_module, tap_phase = build_current_tap_state(regulator, tap_type)

    # In many practical UCTE files, fixed off-nominal taps are represented only via rated_voltage1.
    if regulator is None and len(tap_tables) == 0 and ucte_elm.rated_voltage1 > 0:
        if invert_fixed_tap and bus_t.Vnom > 0:
            # Legacy orientation places node2 as branch "from" side.
            # Fixed UCTE taps are encoded from node1 rated voltage, so use the inverse ratio.
            tap_module = float(bus_t.Vnom) / float(ucte_elm.rated_voltage1)
        elif (not invert_fixed_tap) and bus_f.Vnom > 0:
            # Non-canonical IEEE-like datasets map node1->node2 and fixed taps directly.
            tap_module = float(ucte_elm.rated_voltage1) / float(bus_f.Vnom)

    return {
        "tc_total_positions": total_positions,
        "tc_neutral_position": neutral_position,
        "tc_normal_position": current_tap_index,
        "tc_dV": tc_dv,
        "tc_asymmetry_angle": tc_asymmetry_angle,
        "tc_type": tap_type,
        "tap_position_index": current_tap_index,
        "tap_number": current_tap_number,
        "low_tap_position": low_tap_position,
        "tap_module": tap_module,
        "tap_phase": tap_phase,
        "tap_module_control_mode": tap_module_control_mode,
        "tap_phase_control_mode": tap_phase_control_mode,
        "vset": vset,
        "Pset": pset,
    }


def parse_transformer(ucte_grid: UcteCircuit, grid: MultiCircuit, bus_dict: Dict[str, dev.Bus], logger: Logger):
    """
    Parse UCTE transformers.
    """
    for ucte_elm in ucte_grid.transformers:
        bus_node1 = bus_dict.get(ucte_elm.node1, None)
        bus_node2 = bus_dict.get(ucte_elm.node2, None)

        if bus_node1 is None or bus_node2 is None:
            logger.add_error("Disconnected transformer", value=ucte_elm.name)
            continue

        legacy_orientation = use_legacy_ucte_transformer_orientation(
            ucte_elm=ucte_elm,
            bus_node1=bus_node1,
            bus_node2=bus_node2,
        )
        if legacy_orientation:
            bus_f = bus_node2  # regulated winding
            bus_t = bus_node1  # non-regulated winding
        else:
            bus_f = bus_node1
            bus_t = bus_node2

        active, reducible = ucte_elm.is_active_and_reducible(logger=logger)

        if reducible:
            if bus_f.code == bus_t.code:
                logger.add_warning("Ignoring self-connected UCTE transformer coupler",
                                   device=ucte_elm.name or bus_f.code,
                                   value=bus_f.code)
                continue

            if not same_nominal_voltage(bus_f, bus_t):
                logger.add_error("UCTE transformer coupler endpoints have different nominal voltages",
                                 device=ucte_elm.name or ucte_elm.get_primary_key(),
                                 value=f"{bus_f.Vnom} != {bus_t.Vnom}")
                continue

            regulator = ucte_grid.get_transformer_regulation(elm=ucte_elm)
            tap_tables = ucte_grid.get_transformers_tap_table(elm=ucte_elm)

            if regulator is not None or tap_tables:
                logger.add_warning("Ignoring tap data on UCTE transformer coupler",
                                   device=ucte_elm.name or ucte_elm.get_primary_key())

            if not has_zero_transformer_impedance(ucte_elm):
                logger.add_warning(
                    "UCTE transformer coupler has non-zero impedance/admittance, importing it as a switch",
                    device=ucte_elm.name or ucte_elm.get_primary_key())

            add_switch_from_transformer(grid, ucte_elm, bus_f, bus_t, active, reducible)
            continue

        R, X, B, rate = get_line_impedances_with_b(
            r_ohm=ucte_elm.resistance,
            x_ohm=ucte_elm.reactance,
            b_us=ucte_elm.susceptance,
            length=1.0,
            Imax=get_current_limit_a(ucte_elm.current_limit),
            Sbase=grid.Sbase,
            Vnom=ucte_elm.rated_voltage1
        )

        regulator = ucte_grid.get_transformer_regulation(elm=ucte_elm)
        tap_tables = ucte_grid.get_transformers_tap_table(elm=ucte_elm)
        tap_data = build_transformer_tap_data(
            ucte_elm=ucte_elm,
            regulator=regulator,
            tap_tables=tap_tables,
            bus_f=bus_f,
            bus_t=bus_t,
            invert_fixed_tap=legacy_orientation,
            logger=logger,
        )

        elm = dev.Transformer2W(
            bus_from=bus_f,
            bus_to=bus_t,
            code=ucte_elm.order_code,
            active=active,
            name=ucte_elm.name,
            HV=max(ucte_elm.rated_voltage1, ucte_elm.rated_voltage2),
            LV=min(ucte_elm.rated_voltage1, ucte_elm.rated_voltage2),
            nominal_power=ucte_elm.nominal_power,
            r=R,
            x=X,
            b=B,
            rate=rate,
            vset=tap_data["vset"],
            Pset=tap_data["Pset"],
            tap_module_control_mode=tap_data["tap_module_control_mode"],
            tap_phase_control_mode=tap_data["tap_phase_control_mode"],
            tc_total_positions=tap_data["tc_total_positions"],
            tc_neutral_position=tap_data["tc_neutral_position"],
            tc_normal_position=tap_data["tc_normal_position"],
            tc_dV=tap_data["tc_dV"],
            tc_asymmetry_angle=tap_data["tc_asymmetry_angle"],
            tc_type=tap_data["tc_type"],
        )
        elm.reducible = reducible

        elm.tap_changer.tap_position = tap_data["tap_position_index"]
        elm.tap_module = tap_data["tap_module"]
        elm.tap_phase = tap_data["tap_phase"]

        apply_tap_table(elm, ucte_elm, tap_tables, tap_data["low_tap_position"], tap_data["tap_number"], logger)

        grid.add_transformer2w(obj=elm)


def parse_exchange_power(ucte_grid: UcteCircuit, grid: MultiCircuit, bus_dict: Dict[str, dev.Bus], logger: Logger):
    """
    Exchange powers are currently ignored by the VeraGrid UCTE importer.
    """
    pass


def convert_ucte_to_veragrid(ucte_grid: UcteCircuit, logger: Logger) -> MultiCircuit:
    """
    Convert UCTE grid to VeraGrid.
    """
    # Attempt to discover more accurate nominal voltages for level characters
    vnom_map = discover_nominal_voltages(ucte_grid)
    if vnom_map:
        for node in ucte_grid.nodes:
            if len(node.node_code) >= 7 and (not is_standard_ucte_country_code(node.current_country)):
                level = node.node_code[6]
                if level in vnom_map:
                    node.voltage = vnom_map[level]
                    node.normalize(logger)

    # Guard against malformed/non-canonical IDs that break the level-character heuristic.
    repair_nominal_voltages_from_references(ucte_grid, logger)

    grid = MultiCircuit()
    grid.fBase = 50.0
    grid.Sbase = 100.0
    grid.comments = ucte_grid.fuse_comments()

    bus_dict: Dict[str, dev.Bus] = parse_nodes(ucte_grid=ucte_grid, grid=grid, logger=logger)
    parse_lines(ucte_grid=ucte_grid, grid=grid, bus_dict=bus_dict, logger=logger)
    parse_transformer(ucte_grid=ucte_grid, grid=grid, bus_dict=bus_dict, logger=logger)
    parse_exchange_power(ucte_grid=ucte_grid, grid=grid, bus_dict=bus_dict, logger=logger)

    return grid
