# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Import an OpenDSS feeder using the optional OpenDSSDirect.py package.

The importer creates a balanced positive-sequence VeraGrid model. OpenDSSDirect
solves/compiles the source circuit; this module maps supported elements into a
VeraGrid ``MultiCircuit`` and sends import diagnostics to a VeraGrid ``Logger``.
"""
from __future__ import annotations

import math
import json
from typing import Any

import numpy as np

import VeraGridEngine.Devices as dev
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import CableResistanceInput, ExternalGridMode, GeneratorControlMode
from VeraGridEngine.Utils.optional_dependencies import optional_dependency_failure

try:
    import opendssdirect as _opendssdirect
    OPENDSSDIRECT_AVAILABLE = True
    OPENDSSDIRECT_UNAVAILABLE_REASON = ""
except (ImportError, AttributeError, OSError, RuntimeError, ValueError, TypeError) as error:
    _opendssdirect = None
    OPENDSSDIRECT_AVAILABLE = False
    OPENDSSDIRECT_UNAVAILABLE_REASON = optional_dependency_failure("OpenDSSDirect.py", error)

_SQRT3 = math.sqrt(3.0)
_LINE_UNITS_TO_KM = {0: 1.0, 1: 1.609344, 2: 0.3048, 3: 1.0, 4: 1e-3, 5: 3.048e-4, 6: 2.54e-5, 7: 1e-5}


def _bus_name(token: str) -> str:
    """Return a normalized bus name from an OpenDSS terminal token.

    :param token: OpenDSS bus token, optionally followed by node numbers.
    :return: Lowercase bus name without node suffixes.
    """
    return token.split(".", 1)[0].strip().lower()


def _active_bus(dss_api: Any, buses: dict[str, dev.Bus], element_name: str, class_name: str) -> dev.Bus | None:
    """Resolve the first terminal of an active OpenDSS element to a VeraGrid bus.

    :param dss_api: OpenDSSDirect API module.
    :param buses: Imported buses indexed by normalized name.
    :param element_name: Name of the element to activate.
    :param class_name: OpenDSS class containing the element.
    :return: Matching VeraGrid bus, or ``None`` when it is not imported.
    """
    dss_api.Circuit.SetActiveElement(f"{class_name}.{element_name}")
    terminals = list(dss_api.CktElement.BusNames())
    return buses.get(_bus_name(token=terminals[0])) if terminals else None


def _convert_sources(dss_api: Any, grid: dev.MultiCircuit, buses: dict[str, dev.Bus], logger: Logger) -> int:
    """Convert every OpenDSS Vsource into an external-grid device.

    :param dss_api: OpenDSSDirect API module.
    :param grid: VeraGrid circuit receiving the sources.
    :param buses: Imported buses indexed by normalized name.
    :param logger: Logger receiving conversion warnings.
    :return: Number of sources imported.
    """
    count = 0
    idx = dss_api.Vsources.First()
    while idx:
        name = dss_api.Vsources.Name()
        bus = _active_bus(dss_api=dss_api, buses=buses, element_name=name, class_name="Vsource")
        if bus is None:
            logger.add_warning(msg=f"Vsource {name!r} references an unknown bus", device_class="OpenDSS import")
        else:
            bus.is_slack = count == 0
            grid.add_external_grid(
                bus=bus,
                api_obj=dev.ExternalGrid(
                    name=name,
                    Vm=float(dss_api.Vsources.PU()),
                    mode=ExternalGridMode.VD if count == 0 else ExternalGridMode.PQ,
                ),
            )
            count += 1
        idx = dss_api.Vsources.Next()
    return count


def _convert_dispatchable(dss_api: Any, grid: dev.MultiCircuit, buses: dict[str, dev.Bus], logger: Logger,
                          interface_name: str, class_name: str) -> int:
    """Convert an OpenDSS inverter collection to VeraGrid static generators.

    :param dss_api: OpenDSSDirect API module.
    :param grid: VeraGrid circuit receiving the static generators.
    :param buses: Imported buses indexed by normalized name.
    :param logger: Logger receiving conversion warnings.
    :param interface_name: OpenDSSDirect collection attribute name.
    :param class_name: OpenDSS element class name used for terminal lookup.
    :return: Number of static generators imported.
    """
    interface = getattr(dss_api, interface_name, None)
    if interface is None:
        return 0
    count = 0
    idx = interface.First()
    while idx:
        name = interface.Name()
        bus = _active_bus(dss_api=dss_api, buses=buses, element_name=name, class_name=class_name)
        if bus is None:
            logger.add_warning(msg=f"{class_name} {name!r} references an unknown bus", device_class="OpenDSS import")
        else:
            p_mw = float(interface.kW()) / 1000.0
            q_mvar = float(interface.kvar()) / 1000.0
            snom = float(interface.kVA()) / 1000.0 if hasattr(interface, "kVA") else math.hypot(p_mw, q_mvar)
            grid.add_static_generator(
                bus=bus,
                api_obj=dev.StaticGenerator(name=name, P=p_mw, Q=q_mvar, Snom=max(snom, 0.001)),
            )
            count += 1
        idx = interface.Next()
    return count


def _convert_generators(dss_api: Any, grid: dev.MultiCircuit, buses: dict[str, dev.Bus],
                        logger: Logger) -> int:
    """Convert OpenDSS Generator objects, retaining PQ/PV control selection.

    :param dss_api: OpenDSSDirect API module.
    :param grid: VeraGrid circuit receiving the generators.
    :param buses: Imported buses indexed by normalized name.
    :param logger: Logger receiving conversion warnings.
    :return: Number of generators imported.
    """
    interface = getattr(dss_api, "Generators", None)
    if interface is None:
        return 0
    count = 0
    idx = interface.First()
    while idx:
        name = interface.Name()
        bus = _active_bus(dss_api=dss_api, buses=buses, element_name=name, class_name="Generator")
        if bus is None:
            logger.add_warning(msg=f"Generator {name!r} references an unknown bus", device_class="OpenDSS import")
        else:
            model = int(interface.Model())
            p_mw = float(interface.kW()) / 1000.0
            q_mvar = float(interface.kvar()) / 1000.0
            snom_kva = float(interface.kVARated()) if hasattr(interface, "kVARated") else math.hypot(p_mw, q_mvar) * 1000
            is_voltage_controlled = model == 3
            generator = dev.Generator(
                name=name,
                P=p_mw,
                Q=q_mvar,
                Snom=max(snom_kva / 1000.0, 0.001),
                control_mode=GeneratorControlMode.V if is_voltage_controlled else GeneratorControlMode.Q,
            )
            grid.add_generator(bus=bus, api_obj=generator)
            count += 1
            if model in (2, 5, 6):
                logger.add_warning(msg=f"Generator {name!r} OpenDSS model {model} imported as its operating-point P/Q equivalent", device_class="OpenDSS import")
            elif is_voltage_controlled:
                logger.add_warning(msg=f"Generator {name!r} model 3 imported as voltage-controlled at 1.0 pu; OpenDSS Vpu and reactive limits are not transferred", device_class="OpenDSS import")
        idx = interface.Next()
    return count


def _convert_storage(dss_api: Any, grid: dev.MultiCircuit, buses: dict[str, dev.Bus], logger: Logger) -> int:
    """Convert OpenDSS Storage objects to VeraGrid Battery devices.

    :param dss_api: OpenDSSDirect API module.
    :param grid: VeraGrid circuit receiving the batteries.
    :param buses: Imported buses indexed by normalized name.
    :param logger: Logger receiving conversion warnings.
    :return: Number of batteries imported.
    """
    interface = getattr(dss_api, "Storages", None)
    if interface is None:
        return 0
    count = 0
    idx = interface.First()
    while idx:
        name = interface.Name()
        bus = _active_bus(dss_api=dss_api, buses=buses, element_name=name, class_name="Storage")
        if bus is None:
            logger.add_warning(msg=f"Storage {name!r} references an unknown bus", device_class="OpenDSS import")
        else:
            p_mw = float(interface.kW()) / 1000.0
            q_mvar = float(interface.kvar()) / 1000.0
            energy = max(float(interface.kWhRated()) / 1000.0, 0.001)
            snom = max(float(interface.kVA()) / 1000.0, math.hypot(p_mw, q_mvar), 0.001)
            soc = min(max(float(interface.kWhStored()) / (energy * 1000.0), 0.0), 1.0)
            grid.add_battery(
                bus=bus,
                api_obj=dev.Battery(name=name, P=p_mw, Q=q_mvar, Snom=snom, Enom=energy, soc=soc),
            )
            count += 1
        idx = interface.Next()
    return count


def _convert_current_sources(dss_api: Any, grid: dev.MultiCircuit, buses: dict[str, dev.Bus], logger: Logger) -> int:
    """Convert OpenDSS Isource elements to operating-point current injections.

    :param dss_api: OpenDSSDirect API module.
    :param grid: VeraGrid circuit receiving the current injections.
    :param buses: Imported buses indexed by normalized name.
    :param logger: Logger receiving conversion warnings.
    :return: Number of current injections imported.
    """
    interface = getattr(dss_api, "Isource", None)
    if interface is None:
        return 0
    count = 0
    idx = interface.First()
    while idx:
        name = interface.Name()
        bus = _active_bus(dss_api=dss_api, buses=buses, element_name=name, class_name="Isource")
        if bus is None:
            logger.add_warning(msg=f"Isource {name!r} references an unknown bus", device_class="OpenDSS import")
        else:
            powers = np.asarray(dss_api.CktElement.Powers(), dtype=float)
            conductors = int(dss_api.CktElement.NumConductors())
            p_load_kw = float(np.sum(powers[:2 * conductors:2]))
            q_load_kvar = float(np.sum(powers[1:2 * conductors:2]))
            grid.add_current_injection(
                bus=bus,
                api_obj=dev.CurrentInjection(name=name, Ir=-p_load_kw / 1000.0, Ii=-q_load_kvar / 1000.0),
            )
            count += 1
            logger.add_warning(msg=f"Isource {name!r} converted as constant equivalent P/Q at the solved point", device_class="OpenDSS import")
        idx = interface.Next()
    return count


def _convert_sensors(dss_api: Any, grid: dev.MultiCircuit, buses: dict[str, dev.Bus],
                     branches: dict[str, Any], logger: Logger) -> int:
    """Map OpenDSS Sensor readings to VeraGrid state-estimation measurements.

    :param dss_api: OpenDSSDirect API module.
    :param grid: VeraGrid circuit receiving the measurements.
    :param buses: Imported buses indexed by normalized name.
    :param branches: Imported branches indexed by OpenDSS element name.
    :param logger: Logger receiving conversion warnings.
    :return: Number of measurements imported.
    """
    interface = getattr(dss_api, "Sensors", None)
    if interface is None:
        return 0
    count = 0
    idx = interface.First()
    while idx:
        sensor_count = 0
        name = interface.Name()
        element_name = str(interface.MeteredElement()).lower()
        terminal = max(int(interface.MeteredTerminal()), 1)
        error_fraction = max(abs(float(interface.PctError())) / 100.0, 1e-6)
        branch = branches.get(element_name)
        bus = None
        try:
            dss_api.Circuit.SetActiveElement(str(interface.MeteredElement()))
            terminals = list(dss_api.CktElement.BusNames())
            if terminals:
                bus = buses.get(_bus_name(token=terminals[min(terminal - 1, len(terminals) - 1)]))
        except (AttributeError, TypeError, ValueError):
            terminals = []

        values_p = np.asarray(interface.kW(), dtype=float).reshape(-1) if hasattr(interface, "kW") else np.zeros(0)
        values_q = np.asarray(interface.kvar(), dtype=float).reshape(-1) if hasattr(interface, "kvar") else np.zeros(0)
        if branch is not None and values_p.size and values_q.size:
            p_mw = float(np.sum(values_p)) / 1000.0
            q_mvar = float(np.sum(values_q)) / 1000.0
            side = "f" if terminal == 1 else "t"
            p_type = dev.PfMeasurement if side == "f" else dev.PtMeasurement
            q_type = dev.QfMeasurement if side == "f" else dev.QtMeasurement
            add_p_measurement = grid.add_pf_measurement if side == "f" else grid.add_pt_measurement
            add_q_measurement = grid.add_qf_measurement if side == "f" else grid.add_qt_measurement
            add_p_measurement(obj=p_type(value=p_mw, uncertainty=max(abs(p_mw) * error_fraction, 1e-6),
                                          api_obj=branch, name=f"{name} P"))
            add_q_measurement(obj=q_type(value=q_mvar, uncertainty=max(abs(q_mvar) * error_fraction, 1e-6),
                                          api_obj=branch, name=f"{name} Q"))
            count += 2
            sensor_count += 2

        voltage_values = np.asarray(interface.kVS(), dtype=float).reshape(-1) if hasattr(interface, "kVS") else np.zeros(0)
        voltage_base = float(interface.kVBase()) if hasattr(interface, "kVBase") else 0.0
        if bus is not None and voltage_values.size and voltage_base > 0:
            voltage_pu = float(np.mean(np.abs(voltage_values))) / voltage_base
            grid.add_vm_measurement(obj=dev.VmMeasurement(
                value=voltage_pu,
                uncertainty=max(abs(voltage_pu) * error_fraction, 1e-6),
                api_obj=bus,
                name=f"{name} V",
            ))
            count += 1
            sensor_count += 1

        # OpenDSS treats the current and kW/kvar registers as alternate sensor
        # modes; reading P/Q can synthesize and overwrite the current registers.
        current_values = (
            np.asarray(interface.Currents(), dtype=float).reshape(-1)
            if not (values_p.size and values_q.size) and hasattr(interface, "Currents")
            else np.zeros(0)
        )
        if branch is not None and current_values.size:
            # Sensor current registers are phase-wise amperes; reduce to the
            # average magnitude in kA for VeraGrid's positive-sequence estimator.
            current_ka = float(np.mean(np.abs(current_values))) / 1000.0
            current_type = dev.IfMeasurement if terminal == 1 else dev.ItMeasurement
            add_measurement = grid.add_if_measurement if terminal == 1 else grid.add_it_measurement
            add_measurement(obj=current_type(value=current_ka,
                                             uncertainty=max(current_ka * error_fraction, 1e-6),
                                             api_obj=branch, name=f"{name} I"))
            count += 1
            sensor_count += 1

        if sensor_count == 0:
            logger.add_warning(msg=f"Sensor {name!r} has no measurement that could be linked to an imported bus or branch", device_class="OpenDSS import")
        idx = interface.Next()
    return count


def _log_unmapped_elements(dss_api: Any, logger: Logger, mapped: set[str]) -> None:
    """Warn about circuit elements without a native VeraGrid mapping.

    :param dss_api: OpenDSSDirect API module.
    :param logger: Logger receiving warnings.
    :param mapped: Lowercase OpenDSS element-name prefixes handled by this importer.
    :return: None.
    """
    try:
        names = list(dss_api.Circuit.AllElementNames())
    except (AttributeError, TypeError):
        return
    for element_name in names:
        if not any(element_name.lower().startswith(prefix) for prefix in mapped):
            logger.add_warning(
                msg=f"OpenDSS element {element_name!r} has no VeraGrid mapping and was skipped",
                device_class="OpenDSS import",
            )


def _kron_neutral(matrix: np.ndarray, n: int) -> np.ndarray:
    """Kron-reduce conductors after ABC, following OpenDSS conductor ordering.

    :param matrix: Complex or real conductor impedance/admittance matrix.
    :param n: Number of conductors represented by the matrix.
    :return: Reduced phase matrix.
    """
    phase_count = min(n, 3)
    phase = matrix[:phase_count, :phase_count].copy()
    if n > phase_count:
        phase_neutral = matrix[:phase_count, phase_count:]
        neutral_phase = matrix[phase_count:, :phase_count]
        neutral = matrix[phase_count:, phase_count:]
        try:
            phase = phase - phase_neutral @ np.linalg.solve(neutral, neutral_phase)
        except np.linalg.LinAlgError:
            pass
    return phase


def _positive_sequence(matrix: Any, n: int) -> complex:
    """Reduce a conductor matrix to positive sequence.

    :param matrix: Conductor matrix in row-major form.
    :param n: Number of conductors represented by the matrix.
    :return: Positive-sequence matrix value.
    """
    values = np.asarray(matrix, dtype=complex).reshape(n, n)
    phase_count = min(n, 3)
    phase = _kron_neutral(matrix=values, n=n)
    self_avg = np.trace(phase) / phase_count
    mutual_avg = ((phase.sum() - np.trace(phase)) / (phase_count * (phase_count - 1))
                  if phase_count > 1 else 0j)
    return complex(self_avg - mutual_avg)


def _zero_sequence(matrix: Any, n: int) -> complex:
    """Reduce a conductor matrix to its zero-sequence value.

    :param matrix: Conductor matrix in row-major form.
    :param n: Number of conductors represented by the matrix.
    :return: Zero-sequence matrix value.
    """
    values = np.asarray(matrix, dtype=complex).reshape(n, n)
    phase = _kron_neutral(matrix=values, n=n)
    return complex(phase.sum() / phase.shape[0])


def _record_matrix(line: dev.Line, zabc_pu: np.ndarray, yabc_pu: np.ndarray) -> None:
    """Store complete imported ABC series and shunt matrices in VeraGrid NABC form.

    :param line: VeraGrid line receiving the matrices.
    :param zabc_pu: ABC series impedance matrix in per-unit.
    :param yabc_pu: ABC shunt admittance matrix in per-unit.
    :return: None.
    """
    line.disable_auto_updates()
    ys = dev.AdmittanceMatrix(size=4)
    ys.values[1:4, 1:4] = np.linalg.pinv(zabc_pu, rcond=1e-12)
    ys.phA = ys.phB = ys.phC = True
    ysh = dev.AdmittanceMatrix(size=4)
    # VeraGrid stores line shunt matrices at 1e6 scale; the compiler converts
    # them back to per-unit when assembling the branch stamps.
    ysh.values[1:4, 1:4] = yabc_pu * 1e6
    ysh.phA = ysh.phB = ysh.phC = True
    line.ys = ys
    line.ysh = ysh


def _length_unit_to_km(units: int) -> float:
    """Convert an OpenDSS length-unit enum to kilometres per unit.

    :param units: OpenDSS distance-units enum value.
    :return: Kilometres represented by one source unit.
    """
    return _LINE_UNITS_TO_KM.get(units, 1.0)


def _read_float(interface: Any, property_name: str, default: float = 0.0) -> float:
    """Read an optional numeric property from an OpenDSSDirect interface.

    :param interface: OpenDSSDirect class interface.
    :param property_name: Zero-argument getter name.
    :param default: Value returned when the getter is absent or invalid.
    :return: Property value converted to float, or ``default``.
    """
    getter = getattr(interface, property_name, None)
    if getter is None:
        return default
    try:
        return float(getter())
    except (AttributeError, TypeError, ValueError, RuntimeError):
        return default


def _convert_wire_data(dss_api: Any, grid: dev.MultiCircuit) -> dict[str, dev.Wire]:
    """Import OpenDSS WireData definitions as VeraGrid physical wires.

    :param dss_api: OpenDSSDirect API module.
    :param grid: VeraGrid circuit receiving wire definitions.
    :return: Imported wires indexed by normalized name.
    """
    wires: dict[str, dev.Wire] = {}
    interface = getattr(dss_api, "WireData", None)
    if interface is None:
        return wires
    idx = interface.First()
    while idx:
        name = str(interface.Name())
        resistance_units = int(_read_float(interface, "ResistanceUnits", 0.0))
        gmr_units = int(_read_float(interface, "GMRUnits", resistance_units))
        radius_units = int(_read_float(interface, "RadiusUnits", resistance_units))
        resistance_per_km = _read_float(interface, "Rac", _read_float(interface, "Rdc"))
        resistance_per_km /= _length_unit_to_km(units=resistance_units)
        gmr_mm = _read_float(interface, "GMRac") * _length_unit_to_km(units=gmr_units) * 1e6
        diameter_mm = _read_float(interface, "Diameter") * _length_unit_to_km(units=radius_units) * 1e6
        if diameter_mm <= 0.0:
            diameter_mm = 2.0 * _read_float(interface, "Radius") * _length_unit_to_km(units=radius_units) * 1e6
        wire = dev.Wire(
            name=name,
            r=max(resistance_per_km, 0.0),
            max_current=max(_read_float(interface, "NormAmps") / 1000.0, 0.0),
            diameter=max(diameter_mm, 0.01),
            gmr=max(gmr_mm, 0.0),
        )
        grid.add_wire(obj=wire)
        wires[name.lower()] = wire
        idx = interface.Next()
    return wires


def _convert_line_codes(dss_api: Any, grid: dev.MultiCircuit,
                        logger: Logger) -> dict[str, dev.SequenceLineType]:
    """Import reusable OpenDSS LineCode definitions as sequence line types.

    :param dss_api: OpenDSSDirect API module.
    :param grid: VeraGrid circuit receiving sequence line types.
    :param logger: Logger receiving conversion warnings.
    :return: Imported templates indexed by normalized LineCode name.
    """
    templates: dict[str, dev.SequenceLineType] = {}
    interface = getattr(dss_api, "LineCodes", None)
    if interface is None:
        return templates
    idx = interface.First()
    while idx:
        name = str(interface.Name())
        units = int(_read_float(interface, "Units", 0.0))
        km_per_unit = _length_unit_to_km(units=units)
        phases = max(int(_read_float(interface, "Phases", 3.0)), 1)
        try:
            is_sequence = bool(interface.IsZ1Z0())
            if is_sequence:
                r1 = float(interface.R1()) / km_per_unit
                x1 = float(interface.X1()) / km_per_unit
                r0 = float(interface.R0()) / km_per_unit
                x0 = float(interface.X0()) / km_per_unit
                c1 = _read_float(interface, "C1") / km_per_unit
                c0 = _read_float(interface, "C0") / km_per_unit
            else:
                r_matrix = np.asarray(interface.Rmatrix(), dtype=float).reshape(phases, phases)
                x_matrix = np.asarray(interface.Xmatrix(), dtype=float).reshape(phases, phases)
                c_matrix = np.asarray(interface.Cmatrix(), dtype=float).reshape(phases, phases)
                z1 = _positive_sequence(matrix=r_matrix + 1j * x_matrix, n=phases) / km_per_unit
                z0 = _zero_sequence(matrix=r_matrix + 1j * x_matrix, n=phases) / km_per_unit
                r1, x1, r0, x0 = z1.real, z1.imag, z0.real, z0.imag
                c1 = _positive_sequence(matrix=c_matrix.astype(complex), n=phases).real / km_per_unit
                c0 = _zero_sequence(matrix=c_matrix.astype(complex), n=phases).real / km_per_unit
        except (AttributeError, TypeError, ValueError, RuntimeError) as error:
            logger.add_warning(
                msg=f"LineCode {name!r} could not be imported: {error}",
                device_class="OpenDSS import",
            )
            idx = interface.Next()
            continue
        template = dev.SequenceLineType(
            name=name,
            Imax=max(_read_float(interface, "NormAmps") / 1000.0, 0.001),
            R=float(r1),
            X=float(x1),
            R0=float(r0),
            X0=float(x0),
            B=max(float(c1), 0.0) * 2.0 * math.pi * 50.0 * 1e-3,
            B0=max(float(c0), 0.0) * 2.0 * math.pi * 50.0 * 1e-3,
            use_conductance=False,
        )
        grid.add_sequence_line(obj=template)
        templates[name.lower()] = template
        idx = interface.Next()
    return templates


def _read_active_class_properties(dss_api: Any, class_name: str) -> dict[str, dict[str, Any]]:
    """Read OpenDSS properties for every object in a class using its JSON API.

    :param dss_api: OpenDSSDirect API module.
    :param class_name: OpenDSS object class to activate and serialize.
    :return: Object properties indexed by lowercase full object name.
    """
    active_class = getattr(dss_api, "ActiveClass", None)
    if active_class is None or not hasattr(active_class, "ToJSON"):
        return {}
    try:
        dss_api.Text.Command(f"Set ActiveClass={class_name}")
        payload = json.loads(active_class.ToJSON())
    except (AttributeError, TypeError, ValueError, RuntimeError):
        return {}
    if isinstance(payload, dict):
        elements = payload.get("DSSObject", payload.get("objects", []))
    else:
        elements = payload
    if isinstance(elements, dict):
        if "DSSObject" in elements or "objects" in elements:
            elements = elements.get("DSSObject", elements.get("objects", []))
        else:
            elements = [elements]
    if isinstance(elements, dict):
        elements = [elements]
    properties: dict[str, dict[str, Any]] = {}
    for element in elements if isinstance(elements, list) else []:
        if not isinstance(element, dict):
            continue
        full_name = str(element.get("Name", element.get("name", ""))).lower()
        if not full_name:
            obj_class = str(element.get("DSSClass", "")).lower()
            obj_name = str(element.get("DSSObj", "")).lower()
            if obj_class and obj_name:
                full_name = f"{obj_class}.{obj_name}"
        if not full_name and isinstance(element.get("DSSObject"), dict):
            nested_element = element["DSSObject"]
            full_name = str(nested_element.get("Name", nested_element.get("name", ""))).lower()
            element = nested_element
        if full_name:
            properties[full_name] = element
    return properties


def _convert_direct_line_spacings(dss_api: Any, grid: dev.MultiCircuit,
                                  wires: dict[str, dev.Wire],
                                  logger: Logger) -> dict[str, Any]:
    """Create physical overhead templates for lines using Spacing and Wires directly.

    :param dss_api: OpenDSSDirect API module.
    :param grid: VeraGrid circuit receiving physical line templates.
    :param wires: Imported wires indexed by normalized name.
    :param logger: Logger receiving conversion warnings.
    :return: Imported templates indexed by lowercase line name.
    """
    templates: dict[str, Any] = {}
    line_properties = _read_active_class_properties(dss_api=dss_api, class_name="Line")
    spacing_properties = _read_active_class_properties(dss_api=dss_api, class_name="LineSpacing")
    for line_name, properties in line_properties.items():
        spacing_name = str(properties.get("Spacing", "")).strip().lower()
        if not spacing_name:
            continue
        conductor_names = properties.get("Wires", [])
        if isinstance(conductor_names, str):
            conductor_names = conductor_names.strip("[](){}").replace(",", " ").split()
        conductor_names = [str(value).strip("'\" ").lower() for value in conductor_names]
        spacing = spacing_properties.get(f"linespacing.{spacing_name}",
                                         spacing_properties.get(spacing_name, {}))
        spacing_name_from_json = str(spacing.get("Name", spacing.get("name", ""))).lower()
        if not spacing and spacing_name_from_json == f"linespacing.{spacing_name}":
            spacing = spacing_properties.get(spacing_name_from_json, {})
        x_values = np.asarray(spacing.get("X", spacing.get("Xcoords", [])), dtype=float).reshape(-1)
        y_values = np.asarray(spacing.get("H", spacing.get("Y", spacing.get("Ycoords", []))), dtype=float).reshape(-1)
        if not conductor_names or len(conductor_names) != len(x_values) or len(x_values) != len(y_values):
            logger.add_warning(
                msg=f"Line {line_name!r} uses LineSpacing {spacing_name!r}, but OpenDSSDirect did not expose matching wires and positions",
                device_class="OpenDSS import",
            )
            continue
        count = len(conductor_names)
        template = dev.OverheadLineType(
            name=f"{line_name} (LineSpacing)",
            earth_resistivity=max(float(spacing.get("Rho", properties.get("Rho", 100.0))), 1e-6),
            frequency=max(_read_float(dss_api.Solution, "Frequency", 50.0), 1e-6),
        )
        units_value = spacing.get("Units", properties.get("Units", 0))
        try:
            units = int(units_value)
        except (TypeError, ValueError):
            units_by_name = {"none": 0, "mi": 1, "kft": 2, "km": 3,
                             "m": 4, "ft": 5, "in": 6, "cm": 7}
            units = units_by_name.get(str(units_value).strip().lower(), 0)
        coordinate_scale = _length_unit_to_km(units=units) * 1000.0
        phases = max(int(properties.get("Phases", 3)), 1)
        missing_wire = False
        for conductor_idx in range(count):
            wire = wires.get(conductor_names[conductor_idx])
            if wire is None:
                logger.add_warning(
                    msg=f"Line {line_name!r} LineSpacing references unavailable WireData {conductor_names[conductor_idx]!r}",
                    device_class="OpenDSS import",
                )
                missing_wire = True
                break
            template.add_wire_relationship(
                wire=wire,
                xpos=float(x_values[conductor_idx]) * coordinate_scale,
                ypos=float(y_values[conductor_idx]) * coordinate_scale,
                phase=conductor_idx + 1 if conductor_idx < phases else 0,
            )
        if missing_wire:
            continue
        grid.add_overhead_line(obj=template)
        templates[line_name.removeprefix("line.")] = template
    return templates


def _convert_cable_data(dss_api: Any, grid: dev.MultiCircuit, logger: Logger) -> dict[str, dev.UndergroundCableType]:
    """Import OpenDSS CNData and TSData as VeraGrid single-core cable assets.

    :param dss_api: OpenDSSDirect API module.
    :param grid: VeraGrid circuit receiving cable definitions.
    :param logger: Logger receiving warnings about source properties that cannot
        be represented exactly by the VeraGrid cable model.
    :return: Imported cable definitions indexed by normalized name.
    """
    cables: dict[str, dev.UndergroundCableType] = {}
    for class_name in ("CNData", "TSData"):
        interface = getattr(dss_api, class_name, None)
        if interface is None:
            continue
        idx = interface.First()
        while idx:
            name = str(interface.Name())
            resistance_units = int(_read_float(interface, "ResistanceUnits", 0.0))
            radius_units = int(_read_float(interface, "RadiusUnits", resistance_units))
            distance_factor_mm = _length_unit_to_km(units=radius_units) * 1e6
            core_diameter = _read_float(interface, "Diameter") * distance_factor_mm
            insulation_diameter = _read_float(interface, "DiaIns", core_diameter + 10.0) * distance_factor_mm
            cable_diameter = _read_float(interface, "DiaCable", insulation_diameter + 2.0) * distance_factor_mm
            core_resistance = _read_float(interface, "Rdc", _read_float(interface, "Rac"))
            core_resistance /= _length_unit_to_km(units=resistance_units)
            insulation_thickness = max((insulation_diameter - core_diameter) / 2.0, 0.1)
            sheath_thickness = max((cable_diameter - insulation_diameter) / 2.0, 0.1)
            if class_name == "CNData":
                strand_count = max(_read_float(interface, "k", 1.0), 1.0)
                strand_diameter_mm = _read_float(interface, "DiaStrand") * distance_factor_mm
                strand_resistance = _read_float(interface, "RStrand", core_resistance)
                strand_resistance /= _length_unit_to_km(units=resistance_units)
                sheath_resistance = strand_resistance / strand_count
                if strand_diameter_mm > 0.0:
                    sheath_thickness = max(
                        sheath_thickness,
                        strand_count * strand_diameter_mm ** 2 / max(4.0 * insulation_diameter, 1e-9),
                    )
            else:
                sheath_resistance = core_resistance
                logger.add_warning(
                    msg=f"TSData cable {name!r} imported as a two-layer cable; tape shield construction is approximated",
                    device_class="OpenDSS import",
                )
            cable = dev.UndergroundCableType(
                name=name,
                core_resistance_input=CableResistanceInput.DcResistance,
                core_dc_resistance=max(core_resistance, 1e-12),
                sheath_dc_resistance=max(sheath_resistance, 1e-12),
                core_diameter=max(core_diameter, 0.1),
                cable_diameter=max(cable_diameter, core_diameter + 2.0),
                main_insulation_thickness=insulation_thickness,
                sheath_thickness=sheath_thickness,
                main_insulation_permittivity=max(_read_float(interface, "EpsR", 2.3), 1.0),
            )
            grid.add_underground_cable(obj=cable)
            cables[name.lower()] = cable
            logger.add_warning(
                msg=f"{class_name} cable {name!r} imported with approximated construction details",
                device_class="OpenDSS import",
            )
            idx = interface.Next()
    return cables


def _convert_line_geometries(dss_api: Any, grid: dev.MultiCircuit,
                             wires: dict[str, dev.Wire],
                             cables: dict[str, dev.UndergroundCableType],
                             logger: Logger) -> dict[str, Any]:
    """Import LineGeometry definitions as VeraGrid overhead or cable systems.

    :param dss_api: OpenDSSDirect API module.
    :param grid: VeraGrid circuit receiving physical line templates.
    :param wires: Imported overhead conductors indexed by normalized name.
    :param cables: Imported underground cables indexed by normalized name.
    :param logger: Logger receiving warnings for unsupported geometry details.
    :return: Imported line templates indexed by geometry name.
    """
    templates: dict[str, Any] = {}
    interface = getattr(dss_api, "LineGeometries", None)
    if interface is None:
        return templates
    idx = interface.First()
    while idx:
        name = str(interface.Name())
        try:
            conductor_names = [str(value).lower() for value in interface.Conductors()]
            x_values = np.asarray(interface.Xcoords(), dtype=float).reshape(-1)
            y_values = np.asarray(interface.Ycoords(), dtype=float).reshape(-1)
        except (AttributeError, TypeError, ValueError, RuntimeError) as error:
            logger.add_warning(
                msg=f"LineGeometry {name!r} could not be imported: {error}",
                device_class="OpenDSS import",
            )
            idx = interface.Next()
            continue
        units = int(_read_float(interface, "Units", 0.0))
        coordinate_scale = _length_unit_to_km(units=units) * 1000.0
        phases = max(int(_read_float(interface, "Phases", 3.0)), 1)
        conductor_count = min(len(conductor_names), len(x_values), len(y_values))
        geometry_wires = [wires.get(conductor_name) for conductor_name in conductor_names[:conductor_count]]
        geometry_cables = [cables.get(conductor_name) for conductor_name in conductor_names[:conductor_count]]
        use_cables = any(cable is not None for cable in geometry_cables)
        if use_cables:
            template = dev.UndergroundLineType(
                name=name,
                Imax=max(_read_float(interface, "NormAmps") / 1000.0, 0.001),
                freq=max(_read_float(dss_api.Solution, "Frequency", 50.0), 1e-6),
                earth_resistivity=max(_read_float(interface, "RhoEarth", 100.0), 1e-6),
            )
            for conductor_idx in range(conductor_count):
                cable = geometry_cables[conductor_idx]
                if cable is None:
                    logger.add_warning(
                        msg=f"LineGeometry {name!r} contains a non-cable conductor that is not represented in its cable template",
                        device_class="OpenDSS import",
                    )
                    continue
                if conductor_idx >= phases:
                    logger.add_warning(
                        msg=f"LineGeometry {name!r} neutral cable {conductor_names[conductor_idx]!r} is omitted from the VeraGrid cable system",
                        device_class="OpenDSS import",
                    )
                    continue
                template.add_cable_relationship(
                    cable=cable,
                    xpos=float(x_values[conductor_idx]) * coordinate_scale,
                    ypos=abs(float(y_values[conductor_idx])) * coordinate_scale,
                    phase=conductor_idx + 1,
                )
            grid.add_underground_line(obj=template)
        else:
            template = dev.OverheadLineType(
                name=name,
                earth_resistivity=max(_read_float(interface, "RhoEarth", 100.0), 1e-6),
                frequency=max(_read_float(dss_api.Solution, "Frequency", 50.0), 1e-6),
            )
            for conductor_idx in range(conductor_count):
                wire = geometry_wires[conductor_idx]
                if wire is None:
                    logger.add_warning(
                        msg=f"LineGeometry {name!r} references an unavailable WireData definition {conductor_names[conductor_idx]!r}",
                        device_class="OpenDSS import",
                    )
                    continue
                template.add_wire_relationship(
                    wire=wire,
                    xpos=float(x_values[conductor_idx]) * coordinate_scale,
                    ypos=float(y_values[conductor_idx]) * coordinate_scale,
                    phase=conductor_idx + 1 if conductor_idx < phases else 0,
                )
            grid.add_overhead_line(obj=template)
        templates[name.lower()] = template
        idx = interface.Next()
    return templates


def _convert_buses(dss_api: Any, grid: dev.MultiCircuit,
                   logger: Logger) -> dict[str, dev.Bus]:
    """Create VeraGrid buses from OpenDSS circuit buses.

    :param dss_api: OpenDSSDirect API module.
    :param grid: VeraGrid circuit receiving the buses.
    :param logger: Logger receiving conversion warnings.
    :return: Imported buses indexed by normalized name.
    """
    buses: dict[str, dev.Bus] = {}
    for bus_name in dss_api.Circuit.AllBusNames():
        dss_api.Circuit.SetActiveBus(bus_name)
        kv_ln = float(dss_api.Bus.kVBase())
        if kv_ln <= 0:
            logger.add_warning(msg=f"Bus {bus_name!r} has no voltage base; imported with 0 kV", device_class="OpenDSS import")
        bus = dev.Bus(name=bus_name, Vnom=kv_ln * _SQRT3 if kv_ln > 0 else 0.0)
        grid.add_bus(obj=bus)
        buses[bus_name.lower()] = bus
    return buses


def _convert_lines(dss_api: Any, grid: dev.MultiCircuit, buses: dict[str, dev.Bus],
                   logger: Logger, branches: dict[str, Any],
                   line_templates: dict[str, Any],
                   line_code_templates: dict[str, dev.SequenceLineType],
                   direct_spacing_templates: dict[str, Any]) -> None:
    """Convert OpenDSS Lines to VeraGrid Lines or switches.

    :param dss_api: OpenDSSDirect API module.
    :param grid: VeraGrid circuit receiving the lines and switches.
    :param buses: Imported buses indexed by normalized name.
    :param logger: Logger receiving conversion warnings.
    :param branches: Mutable branch lookup populated for sensor linking.
    :param line_templates: Imported physical templates indexed by LineGeometry name.
    :param line_code_templates: Imported sequence templates indexed by LineCode name.
    :param direct_spacing_templates: Physical templates indexed by line name.
    :return: None.
    """
    template_vnom: dict[str, float] = {}
    idx = dss_api.Lines.First()
    while idx:
        line_name = dss_api.Lines.Name()
        bus_from = buses.get(_bus_name(token=dss_api.Lines.Bus1()))
        bus_to = buses.get(_bus_name(token=dss_api.Lines.Bus2()))
        if bus_from is None or bus_to is None:
            logger.add_warning(msg=f"Line {line_name!r} references an unknown bus; skipped", device_class="OpenDSS import")
            idx = dss_api.Lines.Next()
            continue
        km = _LINE_UNITS_TO_KM.get(int(dss_api.Lines.Units()), 1.0)
        length = float(dss_api.Lines.Length()) * km
        if dss_api.Lines.IsSwitch() or length <= 0:
            closed = not dss_api.CktElement.IsOpen(1, 0)
            grid.add_switch(obj=dev.Switch(bus_from=bus_from, bus_to=bus_to, name=line_name, active=closed))
            idx = dss_api.Lines.Next()
            continue
        n = int(dss_api.Lines.Phases())
        if n < 1:
            logger.add_warning(msg=f"Line {line_name!r} has invalid phase count; skipped", device_class="OpenDSS import")
            idx = dss_api.Lines.Next()
            continue
        r_matrix = np.asarray(dss_api.Lines.RMatrix(), dtype=float).reshape(n, n)
        x_matrix = np.asarray(dss_api.Lines.XMatrix(), dtype=float).reshape(n, n)
        c_matrix = np.asarray(dss_api.Lines.CMatrix(), dtype=float).reshape(n, n)
        z_matrix = _kron_neutral(matrix=r_matrix + 1j * x_matrix, n=n)
        c_phase = _kron_neutral(matrix=c_matrix.astype(complex), n=n).real
        if z_matrix.shape != (3, 3):
            z1 = _positive_sequence(matrix=r_matrix + 1j * x_matrix, n=n)
            z_matrix = np.eye(3, dtype=complex) * z1
            c1 = _positive_sequence(matrix=c_matrix.astype(complex), n=n).real
            c_phase = np.eye(3, dtype=float) * c1
            if n < 3:
                logger.add_warning(msg=f"Line {line_name!r} has {n} phase(s); represented as a balanced equivalent", device_class="OpenDSS import")
        vbase = max(bus_from.Vnom, 1e-9)
        zbase = vbase * vbase / grid.Sbase
        length_source = float(dss_api.Lines.Length())
        series_matrix_pu = z_matrix * length_source / zbase
        z1 = _positive_sequence(matrix=r_matrix + 1j * x_matrix, n=n)
        series_pu = z1 * length_source / zbase
        ysh_matrix_pu = (1j * 2 * math.pi * grid.fBase * c_phase * 1e-9
                         * length_source * zbase)
        b_total_pu = float(np.trace(ysh_matrix_pu).imag / 3)
        branch = dev.Line(
            bus_from=bus_from,
            bus_to=bus_to,
            name=line_name,
            r=series_pu.real,
            x=series_pu.imag,
            b=b_total_pu,
            length=length,
            rate=max(float(dss_api.Lines.NormAmps()) * vbase * _SQRT3 / 1000, 0.001),
        )
        branch.R0 = float(dss_api.Lines.R0()) * length_source / zbase
        branch.X0 = float(dss_api.Lines.X0()) * length_source / zbase
        branch.R2, branch.X2 = branch.R, branch.X
        _record_matrix(line=branch, zabc_pu=series_matrix_pu, yabc_pu=ysh_matrix_pu)
        geometry_getter = getattr(dss_api.Lines, "Geometry", None)
        geometry_name = str(geometry_getter()).strip().lower() if geometry_getter is not None else ""
        template = line_templates.get(geometry_name)
        if template is not None:
            if geometry_name not in template_vnom:
                template.Vnom = max(bus_from.Vnom, bus_to.Vnom)
                template_vnom[geometry_name] = template.Vnom
            elif not math.isclose(template_vnom[geometry_name], max(bus_from.Vnom, bus_to.Vnom), rel_tol=1e-6):
                logger.add_warning(
                    msg=f"LineGeometry {geometry_name!r} is used at multiple voltage levels; its template retains the first line voltage",
                    device_class="OpenDSS import",
                )
            branch.template = template
        else:
            line_code_getter = getattr(dss_api.Lines, "LineCode", None)
            line_code_name = str(line_code_getter()).strip().lower() if line_code_getter is not None else ""
            template = line_code_templates.get(line_code_name)
            if template is not None:
                if template.Vnom <= 1e-9:
                    template.Vnom = max(bus_from.Vnom, bus_to.Vnom)
                elif not math.isclose(template.Vnom, max(bus_from.Vnom, bus_to.Vnom), rel_tol=1e-6):
                    logger.add_warning(
                        msg=f"LineCode {line_code_name!r} is used at multiple voltage levels; its template retains the first line voltage",
                        device_class="OpenDSS import",
                    )
                branch.template = template
            else:
                template = direct_spacing_templates.get(line_name.lower())
                if template is not None:
                    template.Vnom = max(bus_from.Vnom, bus_to.Vnom)
                    branch.template = template
        if (template is None and getattr(dss_api.Lines, "Spacing", None) is not None
                and str(dss_api.Lines.Spacing()).strip()):
            logger.add_warning(
                msg=f"Line {line_name!r} uses LineSpacing directly, but its physical template could not be reconstructed",
                device_class="OpenDSS import",
            )
        grid.add_line(obj=branch)
        branches[f"line.{line_name.lower()}"] = branch
        idx = dss_api.Lines.Next()


def _convert_reactors(dss_api: Any, grid: dev.MultiCircuit, buses: dict[str, dev.Bus],
                      logger: Logger, branches: dict[str, Any]) -> None:
    """Convert OpenDSS Reactor elements to series reactances or fixed shunts.

    :param dss_api: OpenDSSDirect API module.
    :param grid: VeraGrid circuit receiving the reactors.
    :param buses: Imported buses indexed by normalized name.
    :param logger: Logger receiving conversion warnings.
    :param branches: Mutable branch lookup populated for sensor linking.
    :return: None.
    """
    idx = dss_api.Reactors.First()
    while idx:
        name = dss_api.Reactors.Name()
        dss_api.Circuit.SetActiveElement("Reactor." + name)
        endpoints = list(dss_api.CktElement.BusNames())
        if len(endpoints) < 2 or _bus_name(token=endpoints[0]) == _bus_name(token=endpoints[1]):
            bus = buses.get(_bus_name(token=endpoints[0])) if endpoints else None
            reactance = float(dss_api.Reactors.X())
            if bus is not None and abs(reactance) > 1e-12:
                q_mvar = bus.Vnom ** 2 / reactance
                grid.add_shunt(bus=bus, api_obj=dev.Shunt(name=name, B=-q_mvar))
                logger.add_warning(msg=f"Shunt reactor {name!r} imported as fixed susceptance; losses and phase detail are omitted", device_class="OpenDSS import")
            else:
                logger.add_warning(msg=f"Shunt reactor {name!r} has no bus or usable reactance; skipped", device_class="OpenDSS import")
            idx = dss_api.Reactors.Next()
            continue
        bus_from = buses.get(_bus_name(token=endpoints[0]))
        bus_to = buses.get(_bus_name(token=endpoints[1]))
        if bus_from is None or bus_to is None:
            logger.add_warning(msg=f"Reactor {name!r} references an unknown bus; skipped", device_class="OpenDSS import")
            idx = dss_api.Reactors.Next()
            continue
        vbase = max(bus_from.Vnom, 1e-9)
        zbase = vbase * vbase / grid.Sbase
        z = complex(float(dss_api.Reactors.R()), float(dss_api.Reactors.X())) / zbase
        branch = dev.SeriesReactance(bus_from=bus_from, bus_to=bus_to, name=name, r=z.real, x=z.imag)
        grid.add_series_reactance(obj=branch)
        branches[f"reactor.{name.lower()}"] = branch
        idx = dss_api.Reactors.Next()


def _convert_transformers(dss_api: Any, grid: dev.MultiCircuit, buses: dict[str, dev.Bus],
                          logger: Logger, branches: dict[str, Any]) -> None:
    """Convert two- and three-winding OpenDSS transformers.

    :param dss_api: OpenDSSDirect API module.
    :param grid: VeraGrid circuit receiving the transformers.
    :param buses: Imported buses indexed by normalized name.
    :param logger: Logger receiving conversion warnings.
    :param branches: Mutable branch lookup populated for sensor linking.
    :return: None.
    """
    idx = dss_api.Transformers.First()
    while idx:
        name = dss_api.Transformers.Name()
        dss_api.Circuit.SetActiveElement("Transformer." + name)
        winding_buses = [_bus_name(token=bus) for bus in dss_api.CktElement.BusNames()]
        winding_count = int(dss_api.Transformers.NumWindings())
        kva: list[float] = []
        pct_r: list[float] = []
        taps: list[float] = []
        for winding in range(1, winding_count + 1):
            dss_api.Transformers.Wdg(winding)
            kva.append(float(dss_api.Transformers.kVA()))
            pct_r.append(float(dss_api.Transformers.R()))
            taps.append(float(dss_api.Transformers.Tap()))
        if winding_count == 3 and len(winding_buses) >= 3:
            winding_grid_buses = [buses.get(winding_buses[j]) for j in range(3)]
            if any(bus is None for bus in winding_grid_buses):
                logger.add_warning(msg=f"Three-winding transformer {name!r} references an unknown bus; skipped", device_class="OpenDSS import")
                idx = dss_api.Transformers.Next()
                continue
            bus1, bus2, bus3 = winding_grid_buses
            sn = [max(value / 1000.0, 0.001) for value in kva[:3]]
            scale = grid.Sbase / max(sn)
            r12, r23, r31 = pct_r[0] + pct_r[1], pct_r[1] + pct_r[2], pct_r[2] + pct_r[0]
            x12 = float(dss_api.Transformers.Xhl())
            x23 = float(dss_api.Transformers.Xlt())
            x31 = float(dss_api.Transformers.Xht())
            transformer = dev.Transformer3W(
                name=name, bus1=bus1, bus2=bus2, bus3=bus3,
                V1=bus1.Vnom, V2=bus2.Vnom, V3=bus3.Vnom,
                r12=max(r12 / 100.0 * scale, 1e-12),
                r23=max(r23 / 100.0 * scale, 1e-12),
                r31=max(r31 / 100.0 * scale, 1e-12),
                x12=max(x12 / 100.0 * scale, 1e-12),
                x23=max(x23 / 100.0 * scale, 1e-12),
                x31=max(x31 / 100.0 * scale, 1e-12),
                rate12=min(sn[0], sn[1]), rate23=min(sn[1], sn[2]), rate31=min(sn[2], sn[0]),
            )
            grid.add_transformer3w(obj=transformer)
            idx = dss_api.Transformers.Next()
            continue
        if winding_count != 2 or len(winding_buses) < 2:
            logger.add_warning(msg=f"Transformer {name!r} has unsupported {winding_count}-winding topology; skipped", device_class="OpenDSS import")
            idx = dss_api.Transformers.Next()
            continue
        bus_from, bus_to = buses.get(winding_buses[0]), buses.get(winding_buses[1])
        if bus_from is None or bus_to is None:
            logger.add_warning(msg=f"Transformer {name!r} references an unknown bus; skipped", device_class="OpenDSS import")
            idx = dss_api.Transformers.Next()
            continue
        hv, lv = (bus_from, bus_to) if bus_from.Vnom >= bus_to.Vnom else (bus_to, bus_from)
        wdg_hv, wdg_lv = (0, 1) if hv is bus_from else (1, 0)
        sn = max(kva) / 1000.0
        xhl = float(dss_api.Transformers.Xhl())
        vkr = pct_r[wdg_hv] + pct_r[wdg_lv]
        vk = math.hypot(vkr, xhl)
        tap_ratio = taps[wdg_hv] / max(taps[wdg_lv], 1e-12)
        transformer = dev.Transformer2W(
            bus_from=hv, bus_to=lv, name=name, HV=hv.Vnom, LV=lv.Vnom,
            nominal_power=sn,
            r=max(vkr / 100.0 * grid.Sbase / sn, 1e-12),
            x=max(math.sqrt(max(vk * vk - vkr * vkr, 0.0)) / 100.0 * grid.Sbase / sn, 1e-12),
            tap_module=tap_ratio, rate=sn,
        )
        grid.add_transformer2w(obj=transformer)
        branches[f"transformer.{name.lower()}"] = transformer
        if any(abs(tap - 1.0) > 1e-6 for tap in taps):
            logger.add_warning(msg=f"Transformer {name!r} imported with solved tap ratio; regulator controls are not recreated", device_class="OpenDSS import")
        idx = dss_api.Transformers.Next()


def _convert_loads(dss_api: Any, grid: dev.MultiCircuit, buses: dict[str, dev.Bus],
                   logger: Logger) -> None:
    """Convert OpenDSS Loads to VeraGrid constant P/Q loads.

    :param dss_api: OpenDSSDirect API module.
    :param grid: VeraGrid circuit receiving the loads.
    :param buses: Imported buses indexed by normalized name.
    :param logger: Logger receiving conversion warnings.
    :return: None.
    """
    idx = dss_api.Loads.First()
    while idx:
        name = dss_api.Loads.Name()
        dss_api.Circuit.SetActiveElement("Load." + name)
        terminals = list(dss_api.CktElement.BusNames())
        bus = buses.get(_bus_name(token=terminals[0])) if terminals else None
        if bus is not None:
            phase_count = sum(node not in ("", "0") for node in terminals[0].split(".")[1:])
            if phase_count in (1, 2):
                logger.add_warning(msg=f"Load {name!r} is {phase_count}-phase; imported as balanced total P/Q", device_class="OpenDSS import")
            grid.add_load(
                bus=bus,
                api_obj=dev.Load(name=name, P=float(dss_api.Loads.kW()) / 1000.0,
                                 Q=float(dss_api.Loads.kvar()) / 1000.0),
            )
        else:
            logger.add_warning(msg=f"Load {name!r} references an unknown bus; skipped", device_class="OpenDSS import")
        idx = dss_api.Loads.Next()


def _convert_capacitors(dss_api: Any, grid: dev.MultiCircuit, buses: dict[str, dev.Bus],
                        logger: Logger) -> None:
    """Convert OpenDSS Capacitors to fixed VeraGrid shunts.

    :param dss_api: OpenDSSDirect API module.
    :param grid: VeraGrid circuit receiving the shunts.
    :param buses: Imported buses indexed by normalized name.
    :param logger: Logger receiving conversion warnings.
    :return: None.
    """
    idx = dss_api.Capacitors.First()
    while idx:
        name = dss_api.Capacitors.Name()
        dss_api.Circuit.SetActiveElement("Capacitor." + name)
        terminals = list(dss_api.CktElement.BusNames())
        bus = buses.get(_bus_name(token=terminals[0])) if terminals else None
        if bus is not None:
            grid.add_shunt(bus=bus, api_obj=dev.Shunt(name=name, B=float(dss_api.Capacitors.kvar()) / 1000.0))
        else:
            logger.add_warning(msg=f"Capacitor {name!r} references an unknown bus; skipped", device_class="OpenDSS import")
        idx = dss_api.Capacitors.Next()


def opendss_to_veragrid(path: str, solve: bool = True, name: str | None = None,
                        logger: Logger | None = None) -> dev.MultiCircuit:
    """Import a ``.dss`` master file into a balanced positive-sequence grid.

    OpenDSSDirect.py is optional. Install it with ``pip install OpenDSSDirect.py``.
    Unsupported or approximated source features are logged as warnings.
    Unbalanced phase topology and OpenDSS control objects are not fully modeled;
    inspect the supplied logger for approximations and circuit elements without
    a native VeraGrid mapping.

    :param path: Path to the OpenDSS master file.
    :param solve: Whether to solve the compiled OpenDSS circuit before import.
    :param name: Optional VeraGrid circuit name override.
    :param logger: Optional VeraGrid logger to receive import information and
        warnings. A new logger is used when omitted.
    :return: Imported VeraGrid circuit.
    """
    import_logger = logger if logger is not None else Logger()
    if not OPENDSSDIRECT_AVAILABLE:
        message = (
            "OpenDSSDirect.py is required to import OpenDSS files. Install it with "
            "'pip install OpenDSSDirect.py'. Details: " + OPENDSSDIRECT_UNAVAILABLE_REASON
        )
        import_logger.add_warning(msg=message, device_class="OpenDSS import")
        raise ImportError(message)

    dss_api = _opendssdirect
    dss_api.Command("Clear")
    dss_api.Command(f'Redirect "{path}"')
    if solve:
        dss_api.Solution.Solve()

    circuit_name = name or dss_api.Circuit.Name()
    grid = dev.MultiCircuit(name=circuit_name)
    wires = _convert_wire_data(dss_api=dss_api, grid=grid)
    cables = _convert_cable_data(dss_api=dss_api, grid=grid, logger=import_logger)
    line_code_templates = _convert_line_codes(dss_api=dss_api, grid=grid, logger=import_logger)
    line_templates = _convert_line_geometries(
        dss_api=dss_api,
        grid=grid,
        wires=wires,
        cables=cables,
        logger=import_logger,
    )
    direct_spacing_templates = _convert_direct_line_spacings(
        dss_api=dss_api,
        grid=grid,
        wires=wires,
        logger=import_logger,
    )
    buses = _convert_buses(dss_api=dss_api, grid=grid, logger=import_logger)
    branches: dict[str, Any] = {}
    _convert_sources(dss_api=dss_api, grid=grid, buses=buses, logger=import_logger)
    _convert_lines(
        dss_api=dss_api,
        grid=grid,
        buses=buses,
        logger=import_logger,
        branches=branches,
        line_templates=line_templates,
        line_code_templates=line_code_templates,
        direct_spacing_templates=direct_spacing_templates,
    )
    _convert_reactors(dss_api=dss_api, grid=grid, buses=buses, logger=import_logger, branches=branches)
    _convert_transformers(dss_api=dss_api, grid=grid, buses=buses, logger=import_logger, branches=branches)
    _convert_loads(dss_api=dss_api, grid=grid, buses=buses, logger=import_logger)
    _convert_capacitors(dss_api=dss_api, grid=grid, buses=buses, logger=import_logger)
    _convert_generators(dss_api=dss_api, grid=grid, buses=buses, logger=import_logger)
    _convert_dispatchable(dss_api=dss_api, grid=grid, buses=buses, logger=import_logger,
                          interface_name="PVsystems", class_name="PVSystem")
    _convert_storage(dss_api=dss_api, grid=grid, buses=buses, logger=import_logger)
    _convert_current_sources(dss_api=dss_api, grid=grid, buses=buses, logger=import_logger)
    _convert_sensors(dss_api=dss_api, grid=grid, buses=buses, branches=branches, logger=import_logger)
    _log_unmapped_elements(
        dss_api=dss_api,
        logger=import_logger,
        mapped={"vsource.", "line.", "reactor.", "transformer.", "load.", "capacitor.",
                "generator.", "pvsystem.", "storage.", "isource.", "sensor."},
    )

    import_logger.add_info(
        f"Imported {len(wires)} OpenDSS WireData definitions, {len(cables)} cable definitions, "
        f"{len(line_code_templates)} LineCodes, {len(line_templates)} physical line geometries "
        f"and {len(direct_spacing_templates)} direct LineSpacing templates",
        device_class="OpenDSS import",
    )
    import_logger.add_info(
        f"Imported OpenDSS circuit {path!r} with {len(buses)} buses",
        device_class="OpenDSS import",
    )
    return grid


from_opendss = opendss_to_veragrid

__all__ = [
    "OPENDSSDIRECT_AVAILABLE",
    "OPENDSSDIRECT_UNAVAILABLE_REASON",
    "opendss_to_veragrid",
    "from_opendss",
]
