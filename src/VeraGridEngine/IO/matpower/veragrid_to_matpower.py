# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import math
import os
import re
from typing import Dict, List

import numpy as np

import VeraGridEngine.Devices as dev
from VeraGridEngine.Devices.Aggregation.area import Area
from VeraGridEngine.Devices.Aggregation.zone import Zone
from VeraGridEngine.Devices.Injections.external_grid import ExternalGrid
from VeraGridEngine.Devices.Parents.injection_parent import InjectionParent
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import BusMode, ExternalGridMode, GeneratorControlMode

MatpowerScalar = int | float
MATPOWER_EXTERNAL_GRID_LIMIT: float = 1.0e6


class MatpowerCaseExport:
    """
    Store one MATPOWER case export in an explicit container.
    """

    __slots__ = (
        "base_mva",
        "bus_table",
        "gen_table",
        "branch_table",
        "gencost_table",
        "bus_names",
    )

    def __init__(self, base_mva: float) -> None:
        """
        Build one empty MATPOWER case container.

        :param base_mva: Case base power in MVA.
        :return: None.
        """
        self.base_mva: float = float(base_mva)
        self.bus_table: List[List[MatpowerScalar]] = list()
        self.gen_table: List[List[MatpowerScalar]] = list()
        self.branch_table: List[List[MatpowerScalar]] = list()
        self.gencost_table: List[List[MatpowerScalar]] = list()
        self.bus_names: List[str] = list()


def _sanitize_case_name(case_name: str) -> str:
    """
    Convert one arbitrary file stem into a valid MATLAB function name.

    :param case_name: Raw case name candidate.
    :return: Sanitized MATLAB identifier.
    """
    normalized_name: str = re.sub(r"[^0-9A-Za-z_]+", "_", case_name).strip("_")

    if normalized_name == "":
        normalized_name = "veragrid_case"
    else:
        pass

    if normalized_name[0].isdigit():
        normalized_name = "veragrid_" + normalized_name
    else:
        pass

    return normalized_name


def _escape_matlab_string(value: str) -> str:
    """
    Escape one string for a MATLAB single-quoted literal.

    :param value: Raw text.
    :return: Escaped text.
    """
    return value.replace("'", "''")


def _format_numeric_value(value: MatpowerScalar) -> str:
    """
    Format one MATPOWER numeric field.

    :param value: Numeric value to serialize.
    :return: String ready to write to the MATPOWER file.
    """
    if isinstance(value, int):
        return str(value)
    else:
        pass

    numeric_value: float = float(value)

    if math.isfinite(numeric_value):
        rounded_value: float = float(np.round(numeric_value))
        if abs(numeric_value - rounded_value) <= 1e-12:
            return str(int(rounded_value))
        else:
            return f"{numeric_value:.12g}"
    else:
        return "0"


def _scale_power_value(device: InjectionParent, value: float) -> float:
    """
    Convert one device power-like value into MATPOWER MW/MVAr units.

    :param device: VeraGrid injection device.
    :param value: Raw device value.
    :return: Value in MATPOWER units.
    """
    if device.use_kw:
        return float(value) / 1000.0
    else:
        return float(value)


def _get_group_number_map(group_list: List[Area] | List[Zone]) -> Dict[Area | Zone, int]:
    """
    Build one deterministic positive-integer map for areas or zones.

    :param group_list: Ordered list of VeraGrid groups.
    :return: Object-to-positive-integer mapping.
    """
    group_number_map: Dict[Area | Zone, int] = dict()

    for index, group in enumerate(group_list):
        group_number_map[group] = index + 1

    return group_number_map


def _append_missing_group_number(group_number_map: Dict[Area | Zone, int], group: Area | Zone | None) -> int:
    """
    Return the positive integer associated with one optional area or zone.

    :param group_number_map: Existing numbering map.
    :param group: Area or zone object.
    :return: Positive MATPOWER area/zone number.
    """
    if group is None:
        return 1
    else:
        pass

    group_number: int | None = group_number_map.get(group, None)

    if group_number is None:
        group_number = len(group_number_map) + 1
        group_number_map[group] = group_number
    else:
        pass

    return int(group_number)


def _collect_bus_controller_data(
        circuit: MultiCircuit,
        t_idx: int | None
) -> tuple[Dict[dev.Bus, ExternalGrid], Dict[dev.Bus, ExternalGrid], Dict[dev.Bus, dev.Generator | dev.Battery]]:
    """
    Gather the bus-level control devices that affect MATPOWER bus typing.

    :param circuit: Circuit to export.
    :param t_idx: Optional time index.
    :return: Tuple with slack external grids, PV external grids and controlled generators.
    """
    slack_external_grid_by_bus: Dict[dev.Bus, ExternalGrid] = dict()
    pv_external_grid_by_bus: Dict[dev.Bus, ExternalGrid] = dict()
    controlled_generation_by_bus: Dict[dev.Bus, dev.Generator | dev.Battery] = dict()

    external_grid: ExternalGrid
    for external_grid in circuit.get_external_grids():
        if external_grid.bus is None:
            pass
        elif not external_grid.get_active_at(t_idx):
            pass
        elif external_grid.mode == ExternalGridMode.VD:
            if external_grid.bus not in slack_external_grid_by_bus:
                slack_external_grid_by_bus[external_grid.bus] = external_grid
            else:
                pass
        elif external_grid.mode == ExternalGridMode.PV:
            if external_grid.bus not in pv_external_grid_by_bus:
                pv_external_grid_by_bus[external_grid.bus] = external_grid
            else:
                pass
        else:
            pass

    generator: dev.Generator
    for generator in circuit.get_generators():
        if generator.bus is None:
            pass
        elif not generator.get_active_at(t_idx):
            pass
        elif generator.control_mode == GeneratorControlMode.V:
            if generator.bus not in controlled_generation_by_bus:
                controlled_generation_by_bus[generator.bus] = generator
            else:
                pass
        else:
            pass

    battery: dev.Battery
    for battery in circuit.get_batteries():
        if battery.bus is None:
            pass
        elif not battery.get_active_at(t_idx):
            pass
        elif battery.control_mode == GeneratorControlMode.V:
            if battery.bus not in controlled_generation_by_bus:
                controlled_generation_by_bus[battery.bus] = battery
            else:
                pass
        else:
            pass

    return slack_external_grid_by_bus, pv_external_grid_by_bus, controlled_generation_by_bus


def _get_bus_type(
        bus: dev.Bus,
        t_idx: int | None,
        slack_external_grid_by_bus: Dict[dev.Bus, ExternalGrid],
        pv_external_grid_by_bus: Dict[dev.Bus, ExternalGrid],
        controlled_generation_by_bus: Dict[dev.Bus, dev.Generator | dev.Battery]
) -> int:
    """
    Compute the MATPOWER bus type for one VeraGrid bus.

    :param bus: Bus to classify.
    :param t_idx: Optional time index.
    :param slack_external_grid_by_bus: Slack external-grid lookup.
    :param pv_external_grid_by_bus: PV external-grid lookup.
    :param controlled_generation_by_bus: Controlled generation lookup.
    :return: MATPOWER bus type code.
    """
    if not bus.get_active_at(t_idx):
        return 4
    elif bus.is_slack or bus in slack_external_grid_by_bus:
        return int(BusMode.Slack_tpe.value)
    elif bus in pv_external_grid_by_bus or bus in controlled_generation_by_bus:
        return int(BusMode.PV_tpe.value)
    else:
        return int(BusMode.PQ_tpe.value)


def _get_bus_vm_value(
        bus: dev.Bus,
        slack_external_grid_by_bus: Dict[dev.Bus, ExternalGrid],
        pv_external_grid_by_bus: Dict[dev.Bus, ExternalGrid],
        controlled_generation_by_bus: Dict[dev.Bus, dev.Generator | dev.Battery],
        t_idx: int | None
) -> float:
    """
    Compute the MATPOWER bus voltage magnitude seed.

    :param bus: Bus to export.
    :param slack_external_grid_by_bus: Slack external-grid lookup.
    :param pv_external_grid_by_bus: PV external-grid lookup.
    :param controlled_generation_by_bus: Controlled generation lookup.
    :param t_idx: Optional time index.
    :return: Voltage magnitude in p.u.
    """
    if bus in slack_external_grid_by_bus:
        return float(slack_external_grid_by_bus[bus].get_Vm_at(t_idx))
    elif bus in pv_external_grid_by_bus:
        return float(pv_external_grid_by_bus[bus].get_Vm_at(t_idx))
    elif bus in controlled_generation_by_bus:
        return float(controlled_generation_by_bus[bus].get_Vset_at(t_idx))
    else:
        return float(bus.Vm0)


def _get_bus_va_value(bus: dev.Bus, slack_external_grid_by_bus: Dict[dev.Bus, ExternalGrid], t_idx: int | None) -> float:
    """
    Compute the MATPOWER bus voltage angle seed in degrees.

    :param bus: Bus to export.
    :param slack_external_grid_by_bus: Slack external-grid lookup.
    :param t_idx: Optional time index.
    :return: Voltage angle in degrees.
    """
    if bus in slack_external_grid_by_bus:
        return float(np.rad2deg(slack_external_grid_by_bus[bus].get_Va_at(t_idx)))
    else:
        return float(np.rad2deg(bus.Va0))


def _append_bus_rows(
        circuit: MultiCircuit,
        case_export: MatpowerCaseExport,
        bus_number_by_bus: Dict[dev.Bus, int],
        t_idx: int | None,
        logger: Logger
) -> None:
    """
    Fill the MATPOWER bus table and bus-name list.

    :param circuit: Circuit to export.
    :param case_export: Target case container.
    :param bus_number_by_bus: VeraGrid-to-MATPOWER bus-number map.
    :param t_idx: Optional time index.
    :param logger: Export logger.
    :return: None.
    """
    del logger

    injection_devices_by_bus: Dict[dev.Bus, Dict[object, List[InjectionParent]]] = circuit.get_injection_devices_grouped_by_bus()
    area_number_by_area: Dict[Area | Zone, int] = _get_group_number_map(circuit.areas)
    zone_number_by_zone: Dict[Area | Zone, int] = _get_group_number_map(circuit.zones)
    slack_external_grid_by_bus: Dict[dev.Bus, ExternalGrid]
    pv_external_grid_by_bus: Dict[dev.Bus, ExternalGrid]
    controlled_generation_by_bus: Dict[dev.Bus, dev.Generator | dev.Battery]
    slack_external_grid_by_bus, pv_external_grid_by_bus, controlled_generation_by_bus = _collect_bus_controller_data(
        circuit=circuit,
        t_idx=t_idx,
    )

    bus: dev.Bus
    for bus in circuit.buses:
        pd_value: float = 0.0
        qd_value: float = 0.0
        gs_value: float = 0.0
        bs_value: float = 0.0

        injection_devices_by_type: Dict[object, List[InjectionParent]] | None = injection_devices_by_bus.get(bus, None)
        if injection_devices_by_type is None:
            injection_device_list: List[InjectionParent] = list()
        else:
            injection_device_list = list()

            grouped_device_list: List[InjectionParent]
            for grouped_device_list in injection_devices_by_type.values():
                injection_device_list.extend(grouped_device_list)

        injection_device: InjectionParent
        for injection_device in injection_device_list:
            if not injection_device.get_active_at(t_idx):
                pass
            elif isinstance(injection_device, dev.Load):
                pd_value += _scale_power_value(injection_device, injection_device.get_P_at(t_idx))
                qd_value += _scale_power_value(injection_device, injection_device.get_Q_at(t_idx))
                gs_value += _scale_power_value(injection_device, injection_device.get_G_at(t_idx))
                bs_value += _scale_power_value(injection_device, injection_device.get_B_at(t_idx))
            elif isinstance(injection_device, dev.StaticGenerator):
                pd_value -= _scale_power_value(injection_device, injection_device.get_P_at(t_idx))
                qd_value -= _scale_power_value(injection_device, injection_device.get_Q_at(t_idx))
            elif isinstance(injection_device, dev.Shunt):
                gs_value += _scale_power_value(injection_device, injection_device.get_G_at(t_idx))
                bs_value += _scale_power_value(injection_device, injection_device.get_B_at(t_idx))
            elif isinstance(injection_device, dev.ExternalGrid):
                if injection_device.mode == ExternalGridMode.PQ:
                    pd_value += _scale_power_value(injection_device, injection_device.get_P_at(t_idx))
                    qd_value += _scale_power_value(injection_device, injection_device.get_Q_at(t_idx))
                else:
                    pass
            else:
                pass

        area_number: int = _append_missing_group_number(area_number_by_area, bus.area)
        zone_number: int = _append_missing_group_number(zone_number_by_zone, bus.zone)
        bus_type: int = _get_bus_type(bus=bus,
                                      t_idx=t_idx,
                                      slack_external_grid_by_bus=slack_external_grid_by_bus,
                                      pv_external_grid_by_bus=pv_external_grid_by_bus,
                                      controlled_generation_by_bus=controlled_generation_by_bus)
        vm_value: float = _get_bus_vm_value(bus=bus,
                                            slack_external_grid_by_bus=slack_external_grid_by_bus,
                                            pv_external_grid_by_bus=pv_external_grid_by_bus,
                                            controlled_generation_by_bus=controlled_generation_by_bus,
                                            t_idx=t_idx)
        va_value: float = _get_bus_va_value(bus=bus,
                                            slack_external_grid_by_bus=slack_external_grid_by_bus,
                                            t_idx=t_idx)

        case_export.bus_table.append([
            int(bus_number_by_bus[bus]),
            int(bus_type),
            float(pd_value),
            float(qd_value),
            float(gs_value),
            float(bs_value),
            int(area_number),
            float(vm_value),
            float(va_value),
            float(bus.Vnom),
            int(zone_number),
            float(bus.get_Vmax_at(t_idx)),
            float(bus.get_Vmin_at(t_idx)),
        ])
        case_export.bus_names.append(str(bus.name))


def _append_generator_row(
        case_export: MatpowerCaseExport,
        bus_number: int,
        pg_value: float,
        qg_value: float,
        qmax_value: float,
        qmin_value: float,
        vg_value: float,
        mbase_value: float,
        status_value: int,
        pmax_value: float,
        pmin_value: float,
        startup_cost: float,
        shutdown_cost: float,
        cost_2: float,
        cost_1: float,
        cost_0: float
) -> None:
    """
    Append one generator and one gencost row.

    :param case_export: Target case container.
    :param bus_number: MATPOWER bus number.
    :param pg_value: Active power in MW.
    :param qg_value: Reactive power in MVAr.
    :param qmax_value: Maximum reactive power in MVAr.
    :param qmin_value: Minimum reactive power in MVAr.
    :param vg_value: Voltage setpoint in p.u.
    :param mbase_value: Generator MVA base.
    :param status_value: MATPOWER generator status.
    :param pmax_value: Maximum active power in MW.
    :param pmin_value: Minimum active power in MW.
    :param startup_cost: Startup cost.
    :param shutdown_cost: Shutdown cost.
    :param cost_2: Quadratic cost coefficient.
    :param cost_1: Linear cost coefficient.
    :param cost_0: Constant cost coefficient.
    :return: None.
    """
    case_export.gen_table.append([
        int(bus_number),
        float(pg_value),
        float(qg_value),
        float(qmax_value),
        float(qmin_value),
        float(vg_value),
        float(mbase_value),
        int(status_value),
        float(pmax_value),
        float(pmin_value),
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
    ])
    case_export.gencost_table.append([
        2,
        float(startup_cost),
        float(shutdown_cost),
        3,
        float(cost_2),
        float(cost_1),
        float(cost_0),
    ])


def _append_generator_rows(
        circuit: MultiCircuit,
        case_export: MatpowerCaseExport,
        bus_number_by_bus: Dict[dev.Bus, int],
        t_idx: int | None
) -> None:
    """
    Fill the MATPOWER generator and gencost tables.

    :param circuit: Circuit to export.
    :param case_export: Target case container.
    :param bus_number_by_bus: VeraGrid-to-MATPOWER bus-number map.
    :param t_idx: Optional time index.
    :return: None.
    """
    generator: dev.Generator
    for generator in circuit.get_generators():
        if generator.bus is None:
            pass
        else:
            bus_number: int = int(bus_number_by_bus[generator.bus])
            mbase_value: float = _scale_power_value(generator, generator.Snom)

            if mbase_value <= 0.0:
                mbase_value = float(circuit.Sbase)
            else:
                pass

            _append_generator_row(
                case_export=case_export,
                bus_number=bus_number,
                pg_value=_scale_power_value(generator, generator.get_P_at(t_idx)),
                qg_value=_scale_power_value(generator, generator.get_Q_at(t_idx)),
                qmax_value=_scale_power_value(generator, generator.get_Qmax_at(t_idx)),
                qmin_value=_scale_power_value(generator, generator.get_Qmin_at(t_idx)),
                vg_value=float(generator.get_Vset_at(t_idx)),
                mbase_value=mbase_value,
                status_value=1 if generator.get_active_at(t_idx) else 0,
                pmax_value=_scale_power_value(generator, generator.get_Pmax_at(t_idx)),
                pmin_value=_scale_power_value(generator, generator.get_Pmin_at(t_idx)),
                startup_cost=float(generator.startup_cost),
                shutdown_cost=float(generator.shutdown_cost),
                cost_2=float(generator.get_Cost2_at(t_idx)),
                cost_1=float(generator.get_Cost_at(t_idx)),
                cost_0=float(generator.get_Cost0_at(t_idx)),
            )

    battery: dev.Battery
    for battery in circuit.get_batteries():
        if battery.bus is None:
            pass
        else:
            bus_number = int(bus_number_by_bus[battery.bus])
            mbase_value = _scale_power_value(battery, battery.Snom)

            if mbase_value <= 0.0:
                mbase_value = float(circuit.Sbase)
            else:
                pass

            _append_generator_row(
                case_export=case_export,
                bus_number=bus_number,
                pg_value=_scale_power_value(battery, battery.get_P_at(t_idx)),
                qg_value=_scale_power_value(battery, battery.get_Q_at(t_idx)),
                qmax_value=_scale_power_value(battery, battery.get_Qmax_at(t_idx)),
                qmin_value=_scale_power_value(battery, battery.get_Qmin_at(t_idx)),
                vg_value=float(battery.get_Vset_at(t_idx)),
                mbase_value=mbase_value,
                status_value=1 if battery.get_active_at(t_idx) else 0,
                pmax_value=_scale_power_value(battery, battery.get_Pmax_at(t_idx)),
                pmin_value=_scale_power_value(battery, battery.get_Pmin_at(t_idx)),
                startup_cost=float(battery.startup_cost),
                shutdown_cost=float(battery.shutdown_cost),
                cost_2=float(battery.get_Cost2_at(t_idx)),
                cost_1=float(battery.get_Cost_at(t_idx)),
                cost_0=float(battery.get_Cost0_at(t_idx)),
            )

    external_grid: ExternalGrid
    for external_grid in circuit.get_external_grids():
        if external_grid.bus is None:
            pass
        elif not external_grid.get_active_at(t_idx):
            pass
        elif external_grid.mode == ExternalGridMode.VD or external_grid.mode == ExternalGridMode.PV:
            bus_number = int(bus_number_by_bus[external_grid.bus])
            _append_generator_row(
                case_export=case_export,
                bus_number=bus_number,
                pg_value=-_scale_power_value(external_grid, external_grid.get_P_at(t_idx)),
                qg_value=-_scale_power_value(external_grid, external_grid.get_Q_at(t_idx)),
                qmax_value=MATPOWER_EXTERNAL_GRID_LIMIT,
                qmin_value=-MATPOWER_EXTERNAL_GRID_LIMIT,
                vg_value=float(external_grid.get_Vm_at(t_idx)),
                mbase_value=float(circuit.Sbase),
                status_value=1,
                pmax_value=MATPOWER_EXTERNAL_GRID_LIMIT,
                pmin_value=-MATPOWER_EXTERNAL_GRID_LIMIT,
                startup_cost=0.0,
                shutdown_cost=0.0,
                cost_2=0.0,
                cost_1=0.0,
                cost_0=0.0,
            )
        else:
            pass


def _append_branch_rows(
        circuit: MultiCircuit,
        case_export: MatpowerCaseExport,
        bus_number_by_bus: Dict[dev.Bus, int],
        t_idx: int | None
) -> None:
    """
    Fill the MATPOWER branch table.

    :param circuit: Circuit to export.
    :param case_export: Target case container.
    :param bus_number_by_bus: VeraGrid-to-MATPOWER bus-number map.
    :param t_idx: Optional time index.
    :return: None.
    """
    branch_list: List[dev.Branch] = circuit.get_branches(add_vsc=False, add_hvdc=False, add_switch=True)

    branch: dev.Branch
    for branch in branch_list:
        rate_a_value: float = float(branch.get_rate_at(t_idx))
        contingency_factor_value: float = float(branch.get_contingency_factor_at(t_idx))
        protection_factor_value: float = float(branch.get_protection_rating_factor_at(t_idx))

        if rate_a_value <= 0.0:
            rate_b_value: float = 0.0
            rate_c_value: float = 0.0
        else:
            rate_b_value = rate_a_value * contingency_factor_value
            rate_c_value = rate_a_value * protection_factor_value

        if isinstance(branch, dev.Transformer2W):
            tap_ratio_value: float = float(branch.get_tap_module_at(t_idx))
            phase_shift_value: float = float(np.rad2deg(branch.get_tap_phase_at(t_idx)))
        else:
            tap_ratio_value = 0.0
            phase_shift_value = 0.0

        case_export.branch_table.append([
            int(bus_number_by_bus[branch.bus_from]),
            int(bus_number_by_bus[branch.bus_to]),
            float(branch.R),
            float(branch.X),
            float(branch.B),
            float(rate_a_value) if rate_a_value > 0.0 else 0.0,
            float(rate_b_value),
            float(rate_c_value),
            float(tap_ratio_value),
            float(phase_shift_value),
            1 if branch.get_active_at(t_idx) else 0,
            0.0,
            0.0,
        ])


def build_matpower_case(circuit: MultiCircuit,
                        t_idx: int | None = None,
                        logger: Logger | None = None) -> MatpowerCaseExport:
    """
    Convert one VeraGrid circuit into a MATPOWER case container.

    :param circuit: Circuit to export.
    :param t_idx: Optional time index. ``None`` exports the snapshot state.
    :param logger: Optional export logger.
    :return: MATPOWER case container.
    """
    export_logger: Logger = Logger() if logger is None else logger
    case_export: MatpowerCaseExport = MatpowerCaseExport(base_mva=float(circuit.Sbase))
    bus_number_by_bus: Dict[dev.Bus, int] = dict()

    bus: dev.Bus
    for bus_index, bus in enumerate(circuit.buses):
        bus_number_by_bus[bus] = bus_index + 1

    if circuit.get_hvdc_number() > 0:
        export_logger.add_warning(msg="MATPOWER export skips HVDC lines.", value=circuit.get_hvdc_number())
    else:
        pass

    if circuit.get_vsc_number() > 0:
        export_logger.add_warning(msg="MATPOWER export skips VSC devices.", value=circuit.get_vsc_number())
    else:
        pass

    _append_bus_rows(circuit=circuit,
                     case_export=case_export,
                     bus_number_by_bus=bus_number_by_bus,
                     t_idx=t_idx,
                     logger=export_logger)
    _append_generator_rows(circuit=circuit,
                           case_export=case_export,
                           bus_number_by_bus=bus_number_by_bus,
                           t_idx=t_idx)
    _append_branch_rows(circuit=circuit,
                        case_export=case_export,
                        bus_number_by_bus=bus_number_by_bus,
                        t_idx=t_idx)

    return case_export


def build_matpower_case_dict(circuit: MultiCircuit,
                             t_idx: int | None = None,
                             logger: Logger | None = None) -> dict[str, float | List[List[MatpowerScalar]] | List[str]]:
    """
    Convert one VeraGrid circuit into a plain MATPOWER dictionary structure.

    :param circuit: Circuit to export.
    :param t_idx: Optional time index. ``None`` exports the snapshot state.
    :param logger: Optional export logger.
    :return: Dictionary with MATPOWER case data.
    """
    case_export: MatpowerCaseExport = build_matpower_case(circuit=circuit, t_idx=t_idx, logger=logger)
    case_dict: dict[str, float | List[List[MatpowerScalar]] | List[str]] = dict()
    case_dict["baseMVA"] = case_export.base_mva
    case_dict["bus"] = case_export.bus_table
    case_dict["gen"] = case_export.gen_table
    case_dict["branch"] = case_export.branch_table
    case_dict["gencost"] = case_export.gencost_table
    case_dict["bus_name"] = case_export.bus_names
    return case_dict


def _serialize_numeric_matrix(matrix: List[List[MatpowerScalar]], indent: str = "\t") -> List[str]:
    """
    Serialize one numeric MATPOWER matrix body.

    :param matrix: Numeric rows to serialize.
    :param indent: Line indentation.
    :return: Serialized lines without surrounding assignment text.
    """
    serialized_lines: List[str] = list()

    row: List[MatpowerScalar]
    for row in matrix:
        value_strings: List[str] = list()

        value: MatpowerScalar
        for value in row:
            value_strings.append(_format_numeric_value(value))

        serialized_lines.append(indent + "\t".join(value_strings) + ";")

    return serialized_lines


def _serialize_bus_name_table(bus_names: List[str], indent: str = "\t") -> List[str]:
    """
    Serialize the optional MATPOWER bus-name table.

    :param bus_names: Ordered bus-name list.
    :param indent: Line indentation.
    :return: Serialized lines without surrounding assignment text.
    """
    serialized_lines: List[str] = list()

    bus_name: str
    for bus_name in bus_names:
        escaped_name: str = _escape_matlab_string(str(bus_name))
        serialized_lines.append(indent + "'" + escaped_name + "';")

    return serialized_lines


def compose_matpower_case_lines(case_export: MatpowerCaseExport, case_name: str) -> List[str]:
    """
    Compose the full MATPOWER case-file contents.

    :param case_export: Case container to serialize.
    :param case_name: Requested MATLAB function name.
    :return: Output text split into lines.
    """
    sanitized_case_name: str = _sanitize_case_name(case_name)
    lines: List[str] = list()

    lines.append(f"function mpc = {sanitized_case_name}")
    lines.append(f"%{sanitized_case_name.upper()}  VeraGrid export.")
    lines.append("%")
    lines.append("%   MATPOWER case generated by VeraGrid.")
    lines.append("")
    lines.append("%% MATPOWER Case Format : Version 2")
    lines.append("mpc.version = '2';")
    lines.append("")
    lines.append("%%-----  Power Flow Data  -----%%")
    lines.append("%% system MVA base")
    lines.append(f"mpc.baseMVA = {_format_numeric_value(case_export.base_mva)};")
    lines.append("")
    lines.append("%% bus data")
    lines.append("%\tbus_i\ttype\tPd\tQd\tGs\tBs\tarea\tVm\tVa\tbaseKV\tzone\tVmax\tVmin")
    lines.append("mpc.bus = [")
    lines.extend(_serialize_numeric_matrix(case_export.bus_table))
    lines.append("];")
    lines.append("")
    lines.append("%% generator data")
    lines.append("%\tbus\tPg\tQg\tQmax\tQmin\tVg\tmBase\tstatus\tPmax\tPmin\tPc1\tPc2\tQc1min\tQc1max\tQc2min\tQc2max\tramp_agc\tramp_10\tramp_30\tramp_q\tapf")
    lines.append("mpc.gen = [")
    lines.extend(_serialize_numeric_matrix(case_export.gen_table))
    lines.append("];")
    lines.append("")
    lines.append("%% branch data")
    lines.append("%\tfbus\ttbus\tr\tx\tb\trateA\trateB\trateC\tratio\tangle\tstatus\tangmin\tangmax")
    lines.append("mpc.branch = [")
    lines.extend(_serialize_numeric_matrix(case_export.branch_table))
    lines.append("];")
    lines.append("")
    lines.append("%% generator cost data")
    lines.append("%\tmodel\tstartup\tshutdown\tn\tc(n-1)\t...\tc0")
    lines.append("mpc.gencost = [")
    lines.extend(_serialize_numeric_matrix(case_export.gencost_table))
    lines.append("];")

    if len(case_export.bus_names) > 0:
        lines.append("")
        lines.append("%% bus names")
        lines.append("mpc.bus_name = {")
        lines.extend(_serialize_bus_name_table(case_export.bus_names))
        lines.append("};")
    else:
        pass

    return lines


def write_matpower_case_file(file_name: str,
                             circuit: MultiCircuit,
                             t_idx: int | None = None,
                             logger: Logger | None = None,
                             case_name: str | None = None) -> Logger:
    """
    Export one VeraGrid circuit into one MATPOWER case file.

    :param file_name: Target MATPOWER file path.
    :param circuit: Circuit to export.
    :param t_idx: Optional time index. ``None`` exports the snapshot state.
    :param logger: Optional export logger.
    :param case_name: Optional explicit MATLAB function name.
    :return: Export logger.
    """
    export_logger: Logger = Logger() if logger is None else logger
    file_root_name: str
    file_extension: str
    file_root_name, file_extension = os.path.splitext(file_name)

    if case_name is None:
        selected_case_name: str = os.path.basename(file_root_name)
    else:
        selected_case_name = case_name

    if file_extension.lower() not in [".m", ".matpower"]:
        normalized_file_name: str = file_name + ".m"
    else:
        normalized_file_name = file_name

    case_export: MatpowerCaseExport = build_matpower_case(circuit=circuit, t_idx=t_idx, logger=export_logger)
    output_lines: List[str] = compose_matpower_case_lines(case_export=case_export, case_name=selected_case_name)
    output_text: str = "\n".join(output_lines) + "\n"

    with open(normalized_file_name, "w", encoding="utf-8") as file_ptr:
        file_ptr.write(output_text)

    return export_logger
