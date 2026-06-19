from __future__ import annotations

import math

import VeraGridEngine.Devices as dev
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.IO.Eurostag.Devices.eurostag_base import is_closed
from VeraGridEngine.IO.Eurostag.Devices.eurostag_circuit import EurostagCircuit
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import GeneratorControlMode, TapModuleControl


def _get_bus(bus_dict: dict[str, dev.Bus],
             code: str | None,
             logger: Logger,
             device_class: str,
             device: str) -> dev.Bus | None:
    if not code:
        logger.add_error("Missing bus code", device_class=device_class, device=device)
        return None

    bus = bus_dict.get(code)
    if bus is None:
        logger.add_error("Bus not found", device_class=device_class, device=device, value=code)
    return bus


def _add_lines(circuit: MultiCircuit,
               eurostag_grid: EurostagCircuit,
               bus_dict: dict[str, dev.Bus],
               logger: Logger) -> None:
    for row in eurostag_grid.lines:
        bus_from = _get_bus(bus_dict, row.sending_node, logger, "Line", row.name)
        bus_to = _get_bus(bus_dict, row.receiving_node, logger, "Line", row.name)
        if bus_from is None or bus_to is None:
            continue

        code = f"{bus_from.code}_{bus_to.code}_{row.parallel_index}"
        line = dev.Line(
            bus_from=bus_from,
            bus_to=bus_to,
            name=code,
            code=code,
            active=is_closed(row.opening_code),
            r=row.resistance,
            x=row.reactance,
            b=2.0 * row.semi_shunt_susceptance,
            rate=row.rated_apparent_power,
        )
        circuit.add_line(line, logger=logger)


def _add_switches(circuit: MultiCircuit,
                  eurostag_grid: EurostagCircuit,
                  bus_dict: dict[str, dev.Bus],
                  logger: Logger) -> None:
    for row in eurostag_grid.coupling_devices:
        bus_from = _get_bus(bus_dict, row.sending_node, logger, "Switch", row.name)
        bus_to = _get_bus(bus_dict, row.receiving_node, logger, "Switch", row.name)
        if bus_from is None or bus_to is None:
            continue

        code = f"{bus_from.code}_{bus_to.code}_{row.parallel_index}"
        active = is_closed(row.opening_code)
        circuit.add_switch(
            dev.Switch(
                bus_from=bus_from,
                bus_to=bus_to,
                name=code,
                code=code,
                active=active,
                normal_open=not active,
            )
        )


def _add_type1_transformers(circuit: MultiCircuit,
                            eurostag_grid: EurostagCircuit,
                            bus_dict: dict[str, dev.Bus],
                            logger: Logger) -> None:
    for row in eurostag_grid.type1_transformers:
        bus_from = _get_bus(bus_dict, row.sending_node, logger, "Transformer", row.name)
        bus_to = _get_bus(bus_dict, row.receiving_node, logger, "Transformer", row.name)
        if bus_from is None or bus_to is None:
            continue

        circuit.add_transformer2w(
            dev.Transformer2W(
                bus_from=bus_from,
                bus_to=bus_to,
                name=row.name,
                code=row.code,
                active=is_closed(row.opening_code),
                HV=max(bus_from.Vnom, bus_to.Vnom),
                LV=min(bus_from.Vnom, bus_to.Vnom),
                nominal_power=row.rated_apparent_power,
                rate=row.rated_apparent_power,
                r=row.resistance,
                x=row.reactance,
                tap_module=row.transformation_ratio if row.transformation_ratio > 0.0 else 1.0,
            )
        )


def _add_type8_transformers(circuit: MultiCircuit,
                            eurostag_grid: EurostagCircuit,
                            bus_dict: dict[str, dev.Bus],
                            logger: Logger) -> None:
    for row in eurostag_grid.type8_transformers:
        bus_from = _get_bus(bus_dict, row.sending_node, logger, "Transformer", row.name)
        bus_to = _get_bus(bus_dict, row.receiving_node, logger, "Transformer", row.name)
        if bus_from is None or bus_to is None:
            continue

        raw_tap_module = 1.0
        tap_phase = 0.0
        current_tap = row.get_current_tap()
        if current_tap is not None:
            nominal_tap = row.get_nominal_tap()
            if (nominal_tap is not None
                    and current_tap.sending_side_voltage > 0.0
                    and current_tap.receiving_side_voltage > 0.0
                    and nominal_tap.sending_side_voltage > 0.0
                    and nominal_tap.receiving_side_voltage > 0.0):
                current_ratio = current_tap.sending_side_voltage / current_tap.receiving_side_voltage
                nominal_ratio = nominal_tap.sending_side_voltage / nominal_tap.receiving_side_voltage
                if nominal_ratio > 0.0:
                    raw_tap_module = current_ratio / nominal_ratio
            tap_phase = math.radians(current_tap.phase_shift_angle)

        regulated_bus = None
        if row.regulated_node_name:
            regulated_bus = bus_dict.get(row.regulated_node_name)

        transformer = dev.Transformer2W(
            bus_from=bus_from,
            bus_to=bus_to,
            name=row.name,
            code=row.code,
            active=is_closed(row.opening_code),
            HV=max(bus_from.Vnom, bus_to.Vnom),
            LV=min(bus_from.Vnom, bus_to.Vnom),
            nominal_power=row.rated_apparent_power,
            rate=row.rated_apparent_power,
            tap_module=raw_tap_module,
            tap_phase=tap_phase,
        )
        transformer.fill_design_properties(
            Pcu=1000.0 * row.copper_losses,
            Pfe=1000.0 * row.iron_losses,
            I0=row.no_load_current,
            Vsc=row.get_current_leakage_impedance(),
            Sbase=circuit.Sbase,
        )
        if row.regulating_mode == "V" and regulated_bus is not None:
            transformer.tap_module_control_mode = TapModuleControl.Vm
            transformer.regulation_bus = regulated_bus
            if row.voltage_target > 0.0 and regulated_bus.Vnom > 0.0:
                transformer.vset = row.voltage_target / regulated_bus.Vnom
        circuit.add_transformer2w(transformer)


def eurostag_to_veragrid(eurostag_grid: EurostagCircuit, logger: Logger = Logger()) -> MultiCircuit:
    circuit = MultiCircuit(name=eurostag_grid.name, Sbase=eurostag_grid.Sbase)
    circuit.comments = f"Eurostag import from {eurostag_grid.ech_file_name} and {eurostag_grid.dta_file_name}"

    slack_angles = {row.name: row.phase_angle for row in eurostag_grid.slack_buses}
    dynamic_sn = {row.name: row.rated_apparent_power for row in eurostag_grid.dynamic_generators}

    bus_dict: dict[str, dev.Bus] = {}
    for row in eurostag_grid.nodes:
        bus = dev.Bus(
            name=row.name,
            code=row.name,
            Vnom=row.base_voltage,
            is_slack=row.is_slack or row.name in slack_angles,
            Vm0=row.initial_voltage if row.initial_voltage > 0.0 else 1.0,
            Va0=math.radians(row.initial_angle),
        )
        circuit.add_bus(bus)
        bus_dict[row.name] = bus

    for row in eurostag_grid.loads:
        bus = _get_bus(bus_dict, row.bus_name, logger, "Load", row.name)
        if bus is None:
            continue
        circuit.add_load(
            bus=bus,
            api_obj=dev.Load(
                name=row.name or bus.code,
                P=row.active_power,
                Q=row.reactive_power,
                active=row.state == "Y",
            ),
        )

    for row in eurostag_grid.capacitor_banks:
        bus = _get_bus(bus_dict, row.bus_name, logger, "Shunt", row.name)
        if bus is None:
            continue
        circuit.add_shunt(
            bus=bus,
            api_obj=dev.Shunt(
                name=row.name or f"{bus.code}_bank",
                code=row.name,
                G=row.number_active_steps * row.active_loss_on_step,
                B=row.number_active_steps * row.reactive_power_on_step,
                active=row.number_active_steps > 0,
            ),
        )

    for row in eurostag_grid.generators:
        bus = _get_bus(bus_dict, row.bus_name, logger, "Generator", row.name)
        if bus is None:
            continue

        regulated_bus = bus
        if row.regulated_node_name and row.regulated_node_name != row.bus_name:
            remote_bus = _get_bus(bus_dict, row.regulated_node_name, logger, "Generator", row.name)
            if remote_bus is not None:
                regulated_bus = remote_bus

        vset = 1.0
        if row.target_voltage > 0.0 and regulated_bus.Vnom > 0.0:
            vset = row.target_voltage / regulated_bus.Vnom

        control_mode = GeneratorControlMode.V if row.regulating_mode == "V" else GeneratorControlMode.Q
        if control_mode == GeneratorControlMode.V:
            regulated_bus.Vm0 = vset

        generator = dev.Generator(
            name=row.name,
            code=row.name,
            P=row.active_power,
            Q=row.reactive_power,
            vset=vset,
            control_mode=control_mode,
            Qmin=row.min_reactive_power,
            Qmax=row.max_reactive_power,
            Snom=dynamic_sn.get(row.name, row.max_active_power),
            active=row.state == "Y",
            Pmin=row.min_active_power,
            Pmax=row.max_active_power,
        )
        if control_mode == GeneratorControlMode.V:
            generator.control_bus = regulated_bus

        circuit.add_generator(
            bus=bus,
            api_obj=generator,
        )

    _add_switches(circuit=circuit, eurostag_grid=eurostag_grid, bus_dict=bus_dict, logger=logger)
    _add_lines(circuit=circuit, eurostag_grid=eurostag_grid, bus_dict=bus_dict, logger=logger)
    _add_type1_transformers(circuit=circuit, eurostag_grid=eurostag_grid, bus_dict=bus_dict, logger=logger)
    _add_type8_transformers(circuit=circuit, eurostag_grid=eurostag_grid, bus_dict=bus_dict, logger=logger)

    return circuit
