# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.001--.0-

"""
Static EMT API-object parameter mapping.

This module contains the static-device to EMT-parameter assignment layer used
by ``EmtProblemDae``. The contract is intentionally narrow:

* ``Block.api_obj_mapping`` maps ``ParamPowerFlowRefferenceType`` keys to
  constant symbolic EMT parameters.
* Only values that come from the static grid device, or from static network
  bases such as ``Sbase`` and ``fBase``, are assigned here.
* ``Block.event_dict`` is never written by this module. Runtime/event
  parameters belong to explicit/native initialization and runtime event logic.

The EMT problem parser should call ``assign_static_api_object_mapping_for_device``
after processing each device block. The EMT model template chooses which static
values it consumes by exposing only the desired enum keys in ``api_obj_mapping``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np

from VeraGridEngine.Devices.Branches.overhead_line_type import OverheadLineType
from VeraGridEngine.Devices import MultiCircuit
from VeraGridEngine.Devices.Branches.dc_line import DcLine
from VeraGridEngine.Devices.Branches.transformer import Transformer2W
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import (
    ConverterControlType,
    DeviceType,
    ExternalGridMode,
    ParamPowerFlowRefferenceType,
    ShuntConnectionType,
    ShuntControlMode,
    WindingType,
)

devices_static_params_mapping: Dict[DeviceType, List[ParamPowerFlowRefferenceType]] = {
    DeviceType.LoadDevice: [
        ParamPowerFlowRefferenceType.device_active,
        ParamPowerFlowRefferenceType.injection_connection_type,
        ParamPowerFlowRefferenceType.load_p_pu,
        ParamPowerFlowRefferenceType.load_q_pu,
        ParamPowerFlowRefferenceType.load_pa_pu,
        ParamPowerFlowRefferenceType.load_pb_pu,
        ParamPowerFlowRefferenceType.load_pc_pu,
        ParamPowerFlowRefferenceType.load_qa_pu,
        ParamPowerFlowRefferenceType.load_qb_pu,
        ParamPowerFlowRefferenceType.load_qc_pu,
        ParamPowerFlowRefferenceType.load_g_pu,
        ParamPowerFlowRefferenceType.load_b_pu,
        ParamPowerFlowRefferenceType.load_ga_pu,
        ParamPowerFlowRefferenceType.load_gb_pu,
        ParamPowerFlowRefferenceType.load_gc_pu,
        ParamPowerFlowRefferenceType.load_ba_pu,
        ParamPowerFlowRefferenceType.load_bb_pu,
        ParamPowerFlowRefferenceType.load_bc_pu,
        ParamPowerFlowRefferenceType.load_ir_pu,
        ParamPowerFlowRefferenceType.load_ii_pu,
        ParamPowerFlowRefferenceType.load_ira_pu,
        ParamPowerFlowRefferenceType.load_irb_pu,
        ParamPowerFlowRefferenceType.load_irc_pu,
        ParamPowerFlowRefferenceType.load_iia_pu,
        ParamPowerFlowRefferenceType.load_iib_pu,
        ParamPowerFlowRefferenceType.load_iic_pu,
        ParamPowerFlowRefferenceType.load_contract_power_pu,
        ParamPowerFlowRefferenceType.Pl0,
        ParamPowerFlowRefferenceType.g,
        ParamPowerFlowRefferenceType.Pl0_A,
        ParamPowerFlowRefferenceType.Pl0_B,
        ParamPowerFlowRefferenceType.Pl0_C,
        ParamPowerFlowRefferenceType.Ql0_A,
        ParamPowerFlowRefferenceType.Ql0_B,
        ParamPowerFlowRefferenceType.Ql0_C,
        ParamPowerFlowRefferenceType.omega_base,
    ],
    DeviceType.StaticGeneratorDevice: [
        ParamPowerFlowRefferenceType.device_active,
        ParamPowerFlowRefferenceType.injection_connection_type,
        ParamPowerFlowRefferenceType.load_p_pu,
        ParamPowerFlowRefferenceType.load_q_pu,
        ParamPowerFlowRefferenceType.load_pa_pu,
        ParamPowerFlowRefferenceType.load_pb_pu,
        ParamPowerFlowRefferenceType.load_pc_pu,
        ParamPowerFlowRefferenceType.load_qa_pu,
        ParamPowerFlowRefferenceType.load_qb_pu,
        ParamPowerFlowRefferenceType.load_qc_pu,
        ParamPowerFlowRefferenceType.Pl0_A,
        ParamPowerFlowRefferenceType.Pl0_B,
        ParamPowerFlowRefferenceType.Pl0_C,
        ParamPowerFlowRefferenceType.Ql0_A,
        ParamPowerFlowRefferenceType.Ql0_B,
        ParamPowerFlowRefferenceType.Ql0_C,
        ParamPowerFlowRefferenceType.omega_base,
        ParamPowerFlowRefferenceType.static_generator_snom_mva,
    ],
    DeviceType.ExternalGridDevice: [
        ParamPowerFlowRefferenceType.device_active,
        ParamPowerFlowRefferenceType.injection_connection_type,
        ParamPowerFlowRefferenceType.load_p_pu,
        ParamPowerFlowRefferenceType.load_pa_pu,
        ParamPowerFlowRefferenceType.load_pb_pu,
        ParamPowerFlowRefferenceType.load_pc_pu,
        ParamPowerFlowRefferenceType.load_qa_pu,
        ParamPowerFlowRefferenceType.load_qb_pu,
        ParamPowerFlowRefferenceType.load_qc_pu,
        ParamPowerFlowRefferenceType.omega_base,
        ParamPowerFlowRefferenceType.load_q_pu,
        ParamPowerFlowRefferenceType.external_grid_vm_pu,
        ParamPowerFlowRefferenceType.external_grid_va_rad,
        ParamPowerFlowRefferenceType.external_grid_mode_code,
    ],
    DeviceType.ShuntDevice: [
        ParamPowerFlowRefferenceType.device_active,
        ParamPowerFlowRefferenceType.injection_connection_type,
        ParamPowerFlowRefferenceType.shunt_g_pu,
        ParamPowerFlowRefferenceType.shunt_b_pu,
        ParamPowerFlowRefferenceType.shunt_g0_pu,
        ParamPowerFlowRefferenceType.shunt_b0_pu,
        ParamPowerFlowRefferenceType.shunt_ga_pu,
        ParamPowerFlowRefferenceType.shunt_gb_pu,
        ParamPowerFlowRefferenceType.shunt_gc_pu,
        ParamPowerFlowRefferenceType.shunt_ba_pu,
        ParamPowerFlowRefferenceType.shunt_bb_pu,
        ParamPowerFlowRefferenceType.shunt_bc_pu,
    ],
    DeviceType.ControllableShuntDevice: [
        ParamPowerFlowRefferenceType.device_active,
        ParamPowerFlowRefferenceType.injection_connection_type,
        ParamPowerFlowRefferenceType.shunt_g_pu,
        ParamPowerFlowRefferenceType.shunt_b_pu,
        ParamPowerFlowRefferenceType.shunt_g0_pu,
        ParamPowerFlowRefferenceType.shunt_b0_pu,
        ParamPowerFlowRefferenceType.shunt_ga_pu,
        ParamPowerFlowRefferenceType.shunt_gb_pu,
        ParamPowerFlowRefferenceType.shunt_gc_pu,
        ParamPowerFlowRefferenceType.shunt_ba_pu,
        ParamPowerFlowRefferenceType.shunt_bb_pu,
        ParamPowerFlowRefferenceType.shunt_bc_pu,
        ParamPowerFlowRefferenceType.controllable_shunt_step,
        ParamPowerFlowRefferenceType.controllable_shunt_vset_pu,
        ParamPowerFlowRefferenceType.controllable_shunt_vmin_pu,
        ParamPowerFlowRefferenceType.controllable_shunt_vmax_pu,
        ParamPowerFlowRefferenceType.controllable_shunt_gmin_pu,
        ParamPowerFlowRefferenceType.controllable_shunt_gmax_pu,
        ParamPowerFlowRefferenceType.controllable_shunt_bmin_pu,
        ParamPowerFlowRefferenceType.controllable_shunt_bmax_pu,
        ParamPowerFlowRefferenceType.controllable_shunt_control_mode_code,
    ],
    DeviceType.CurrentInjectionDevice: [
        ParamPowerFlowRefferenceType.device_active,
        ParamPowerFlowRefferenceType.injection_connection_type,
        ParamPowerFlowRefferenceType.current_injection_ir_pu,
        ParamPowerFlowRefferenceType.current_injection_ii_pu,
        ParamPowerFlowRefferenceType.current_injection_ira_pu,
        ParamPowerFlowRefferenceType.current_injection_irb_pu,
        ParamPowerFlowRefferenceType.current_injection_irc_pu,
        ParamPowerFlowRefferenceType.current_injection_iia_pu,
        ParamPowerFlowRefferenceType.current_injection_iib_pu,
        ParamPowerFlowRefferenceType.current_injection_iic_pu,
    ],
    DeviceType.GeneratorDevice: [
        ParamPowerFlowRefferenceType.device_active,
        ParamPowerFlowRefferenceType.injection_connection_type,
        ParamPowerFlowRefferenceType.omega_base,
        ParamPowerFlowRefferenceType.fn,
        ParamPowerFlowRefferenceType.ws,
        ParamPowerFlowRefferenceType.R1,
        ParamPowerFlowRefferenceType.X1,
        ParamPowerFlowRefferenceType.X0,
        ParamPowerFlowRefferenceType.generator_p_pu,
        ParamPowerFlowRefferenceType.generator_q_pu,
        ParamPowerFlowRefferenceType.generator_pmin_pu,
        ParamPowerFlowRefferenceType.generator_pmax_pu,
        ParamPowerFlowRefferenceType.generator_qmin_pu,
        ParamPowerFlowRefferenceType.generator_qmax_pu,
        ParamPowerFlowRefferenceType.generator_power_factor,
        ParamPowerFlowRefferenceType.generator_vset_pu,
        ParamPowerFlowRefferenceType.generator_snom_mva,
        ParamPowerFlowRefferenceType.generator_r0_pu,
        ParamPowerFlowRefferenceType.generator_r2_pu,
        ParamPowerFlowRefferenceType.generator_x2_pu,
        ParamPowerFlowRefferenceType.generator_is_controlled,
        ParamPowerFlowRefferenceType.generator_enabled_dispatch,
        ParamPowerFlowRefferenceType.generator_must_run,
        ParamPowerFlowRefferenceType.generator_use_reactive_power_curve,
        ParamPowerFlowRefferenceType.generator_device_sbase_mva,
        ParamPowerFlowRefferenceType.freq,
    ],
    DeviceType.BatteryDevice: [
        ParamPowerFlowRefferenceType.device_active,
        ParamPowerFlowRefferenceType.injection_connection_type,
        ParamPowerFlowRefferenceType.omega_base,
        ParamPowerFlowRefferenceType.fn,
        ParamPowerFlowRefferenceType.ws,
        ParamPowerFlowRefferenceType.R1,
        ParamPowerFlowRefferenceType.X1,
        ParamPowerFlowRefferenceType.X0,
        ParamPowerFlowRefferenceType.generator_p_pu,
        ParamPowerFlowRefferenceType.generator_q_pu,
        ParamPowerFlowRefferenceType.generator_pmin_pu,
        ParamPowerFlowRefferenceType.generator_pmax_pu,
        ParamPowerFlowRefferenceType.generator_qmin_pu,
        ParamPowerFlowRefferenceType.generator_qmax_pu,
        ParamPowerFlowRefferenceType.generator_power_factor,
        ParamPowerFlowRefferenceType.generator_vset_pu,
        ParamPowerFlowRefferenceType.generator_snom_mva,
        ParamPowerFlowRefferenceType.generator_r0_pu,
        ParamPowerFlowRefferenceType.generator_r2_pu,
        ParamPowerFlowRefferenceType.generator_x2_pu,
        ParamPowerFlowRefferenceType.generator_is_controlled,
        ParamPowerFlowRefferenceType.generator_enabled_dispatch,
        ParamPowerFlowRefferenceType.generator_must_run,
        ParamPowerFlowRefferenceType.generator_use_reactive_power_curve,
        ParamPowerFlowRefferenceType.generator_device_sbase_mva,
        ParamPowerFlowRefferenceType.freq,
        ParamPowerFlowRefferenceType.battery_enom_mwh,
        ParamPowerFlowRefferenceType.battery_soc_0_pu,
        ParamPowerFlowRefferenceType.battery_max_soc_pu,
        ParamPowerFlowRefferenceType.battery_min_soc_pu,
        ParamPowerFlowRefferenceType.battery_charge_efficiency_pu,
        ParamPowerFlowRefferenceType.battery_discharge_efficiency_pu,
        ParamPowerFlowRefferenceType.battery_charge_per_cycle_pu,
        ParamPowerFlowRefferenceType.battery_discharge_per_cycle_pu,
    ],
    DeviceType.VscDevice: [
        ParamPowerFlowRefferenceType.device_active,
        ParamPowerFlowRefferenceType.branch_rate_mva,
        ParamPowerFlowRefferenceType.branch_temp_base_deg_c,
        ParamPowerFlowRefferenceType.branch_temp_oper_deg_c,
        ParamPowerFlowRefferenceType.branch_alpha_per_deg_c,
        ParamPowerFlowRefferenceType.Sbase,
        ParamPowerFlowRefferenceType.omega_base,
        ParamPowerFlowRefferenceType.converter_control_mode_1,
        ParamPowerFlowRefferenceType.converter_control_mode_2,
        ParamPowerFlowRefferenceType.converter_control_target_1,
        ParamPowerFlowRefferenceType.converter_control_target_2,
        ParamPowerFlowRefferenceType.alpha1,
        ParamPowerFlowRefferenceType.alpha2,
        ParamPowerFlowRefferenceType.alpha3,
        ParamPowerFlowRefferenceType.vsc_kdp_pu,
        ParamPowerFlowRefferenceType.vsc_min_ac_voltage_pu,
    ],
    DeviceType.DCLineDevice: [
        ParamPowerFlowRefferenceType.device_active,
        ParamPowerFlowRefferenceType.branch_rate_mva,
        ParamPowerFlowRefferenceType.branch_temp_base_deg_c,
        ParamPowerFlowRefferenceType.branch_temp_oper_deg_c,
        ParamPowerFlowRefferenceType.branch_alpha_per_deg_c,
        ParamPowerFlowRefferenceType.g,
        ParamPowerFlowRefferenceType.b,
        ParamPowerFlowRefferenceType.bsh,
        ParamPowerFlowRefferenceType.dc_line_r_pu,
        ParamPowerFlowRefferenceType.dc_line_length_km,
    ],
    DeviceType.Transformer2WDevice: [
        ParamPowerFlowRefferenceType.device_active,
        ParamPowerFlowRefferenceType.branch_rate_mva,
        ParamPowerFlowRefferenceType.branch_temp_base_deg_c,
        ParamPowerFlowRefferenceType.branch_temp_oper_deg_c,
        ParamPowerFlowRefferenceType.branch_alpha_per_deg_c,
        ParamPowerFlowRefferenceType.omega_base,
        ParamPowerFlowRefferenceType.transformer_rated_power_mva,
        ParamPowerFlowRefferenceType.transformer_winding1_rated_voltage_ll_kv,
        ParamPowerFlowRefferenceType.transformer_winding2_rated_voltage_ll_kv,
        ParamPowerFlowRefferenceType.transformer_connection_clock,
        ParamPowerFlowRefferenceType.transformer_open_circuit_current_pct,
        ParamPowerFlowRefferenceType.transformer_open_circuit_loss_kw,
        ParamPowerFlowRefferenceType.transformer_short_circuit_voltage_pct,
        ParamPowerFlowRefferenceType.transformer_short_circuit_resistance_pct,
        ParamPowerFlowRefferenceType.transformer_short_circuit_loss_kw,
        ParamPowerFlowRefferenceType.transformer_tap_module,
        ParamPowerFlowRefferenceType.transformer_nominal_voltage_ratio,
        ParamPowerFlowRefferenceType.transformer_total_voltage_ratio,
        ParamPowerFlowRefferenceType.transformer_tap_ratio,
        ParamPowerFlowRefferenceType.transformer_winding1_resistance_pu,
        ParamPowerFlowRefferenceType.transformer_winding2_resistance_pu,
        ParamPowerFlowRefferenceType.transformer_winding1_inductance_pu_s,
        ParamPowerFlowRefferenceType.transformer_winding2_inductance_pu_s,
        ParamPowerFlowRefferenceType.transformer_mutual_inductance_pu_s,
        ParamPowerFlowRefferenceType.transformer_magnetizing_conductance_pu,
    ],
    DeviceType.WindingDevice: [
        ParamPowerFlowRefferenceType.device_active,
        ParamPowerFlowRefferenceType.branch_rate_mva,
        ParamPowerFlowRefferenceType.branch_temp_base_deg_c,
        ParamPowerFlowRefferenceType.branch_temp_oper_deg_c,
        ParamPowerFlowRefferenceType.branch_alpha_per_deg_c,
        ParamPowerFlowRefferenceType.omega_base,
        ParamPowerFlowRefferenceType.transformer_rated_power_mva,
        ParamPowerFlowRefferenceType.transformer_winding1_rated_voltage_ll_kv,
        ParamPowerFlowRefferenceType.transformer_winding2_rated_voltage_ll_kv,
        ParamPowerFlowRefferenceType.transformer_connection_clock,
        ParamPowerFlowRefferenceType.transformer_open_circuit_current_pct,
        ParamPowerFlowRefferenceType.transformer_open_circuit_loss_kw,
        ParamPowerFlowRefferenceType.transformer_short_circuit_voltage_pct,
        ParamPowerFlowRefferenceType.transformer_short_circuit_resistance_pct,
        ParamPowerFlowRefferenceType.transformer_short_circuit_loss_kw,
        ParamPowerFlowRefferenceType.transformer_tap_module,
        ParamPowerFlowRefferenceType.transformer_nominal_voltage_ratio,
        ParamPowerFlowRefferenceType.transformer_total_voltage_ratio,
        ParamPowerFlowRefferenceType.transformer_tap_ratio,
        ParamPowerFlowRefferenceType.transformer_winding1_resistance_pu,
        ParamPowerFlowRefferenceType.transformer_winding2_resistance_pu,
        ParamPowerFlowRefferenceType.transformer_winding1_inductance_pu_s,
        ParamPowerFlowRefferenceType.transformer_winding2_inductance_pu_s,
        ParamPowerFlowRefferenceType.transformer_mutual_inductance_pu_s,
        ParamPowerFlowRefferenceType.transformer_magnetizing_conductance_pu,
    ],
    DeviceType.LineDevice: [
        ParamPowerFlowRefferenceType.device_active,
        ParamPowerFlowRefferenceType.branch_rate_mva,
        ParamPowerFlowRefferenceType.branch_temp_base_deg_c,
        ParamPowerFlowRefferenceType.branch_temp_oper_deg_c,
        ParamPowerFlowRefferenceType.branch_alpha_per_deg_c,
        ParamPowerFlowRefferenceType.line_length_km,
    ],
    DeviceType.HVDCLineDevice: [],
    DeviceType.SeriesReactanceDevice: [],
    DeviceType.SwitchDevice: [],
    DeviceType.UpfcDevice: [],
}


def to_static_mapping_const(value: Any) -> Const:
    """
    Convert a static numerical mapping value into a symbolic constant.

    :param value: Numerical value or an already-created ``Const``.
    :return: Constant symbolic expression used by EMT parameters.
    """
    out: Const

    if isinstance(value, Const):
        # Existing constants are preserved so callers can pre-build symbolic
        # constants without being wrapped a second time.
        out = value
    else:
        # Static API-object values are scalar real constants. The explicit float
        # conversion keeps parameter values homogeneous in the EMT parameter map.
        out = Const(float(value))

    return out


def add_static_mapping_warning(
        logger: Logger | None,
        device_name: str,
        message: str,
        value: str,
        expected_value: str,
        device_property: str,
) -> None:
    """
    Add one diagnostic warning for a static mapping issue.

    :param logger: Optional EMT logger.
    :param device_name: Device name used in diagnostics.
    :param message: Warning message.
    :param value: Actual problematic value.
    :param expected_value: Expected value or condition.
    :param device_property: Device property involved in the warning.
    :return: None.
    """
    if logger is None:
        # The mapper can be used in small unit tests without a full EMT logger.
        # In that case, invalid optional mappings are skipped silently.
        pass
    else:
        logger.add_warning(
            msg=message,
            device=device_name,
            value=value,
            expected_value=expected_value,
            device_class="EMT",
            device_property=device_property,
        )


def assign_api_mapping_value_if_present(
        mdl: Block,
        key: ParamPowerFlowRefferenceType,
        value: Any,
        logger: Logger | None,
        device_name: str,
) -> bool:
    """
    Assign one static API-object value to ``mdl.parameters`` if exposed.

    This function is the only low-level writer used by this module. It never
    writes into ``mdl.event_dict`` because event parameters are model-dynamic
    or runtime parameters initialized by the explicit/native initialization path.

    :param mdl: EMT symbolic block receiving the static parameter.
    :param key: Static API-object reference key.
    :param value: Static numerical value to assign.
    :param logger: Optional logger used to report invalid mapping contracts.
    :param device_name: Device name used in diagnostics.
    :return: ``True`` if the value was assigned, ``False`` otherwise.
    """
    assigned: bool = False
    api_obj_mapping: Any = mdl.api_obj_mapping


    # The mapping is optional: a model receives only the static parameters it
    # explicitly requests by exposing the enum key.
    target: Any | None = api_obj_mapping.get(key, None)

    if target is None:
        assigned = False
    else:
        event_dict: Any = mdl.event_dict

        if target in event_dict:

            # A target present in event_dict means the model declared a
            # runtime parameter as a static API-object parameter. That is
            # a contract error unless the caller explicitly opted into
            # seeding runtime parameters from static device data.
            add_static_mapping_warning(
                logger=logger,
                device_name=device_name,
                message="Static api_obj_mapping points to an event_dict parameter.",
                value=str(key),
                expected_value="api_obj_mapping target must be a constant parameter",
                device_property="api_obj_mapping",
            )
            assigned = False
        else:
            # The static mapping declares the symbolic parameter target.
            # The target does not need to pre-exist in mdl.parameters.
            mdl.parameters[target] = to_static_mapping_const(value)
            assigned = True



    return assigned


def api_mapping_has_any_key(
        mdl: Block,
        keys: List[ParamPowerFlowRefferenceType],
) -> bool:
    """
    Return whether the block exposes at least one of the provided static keys.

    :param mdl: EMT symbolic block.
    :param keys: API-object enum keys to test.
    :return: ``True`` if any key is present in ``mdl.api_obj_mapping``.
    """
    has_key: bool = False
    api_obj_mapping: Any = mdl.api_obj_mapping

    if isinstance(api_obj_mapping, dict):
        key_index: int = 0

        while key_index < len(keys):
            key: ParamPowerFlowRefferenceType = keys[key_index]

            if key in api_obj_mapping:
                # Do not break the loop: keeping the loop explicit avoids control
                # flow surprises and follows the local style constraints.
                has_key = True
            else:
                pass

            key_index += 1
    else:
        has_key = False

    return has_key


def boolean_to_float(value: bool) -> float:
    """
    Convert a static boolean into the EMT scalar convention.

    :param value: Static boolean value.
    :return: ``1.0`` when ``True``, ``0.0`` when ``False``.
    """
    out: float

    if value:
        out = 1.0
    else:
        out = 0.0

    return out


def omega_base_from_grid(grid: MultiCircuit) -> float:
    """
    Return the angular base frequency of the network.

    :param grid: Static network model.
    :return: Angular base frequency in rad/s.
    """
    return 2.0 * np.pi * float(grid.fBase)


def frequency_base_hz_from_grid(grid: MultiCircuit) -> float:
    """
    Return the nominal frequency base of the network.

    :param grid: Static network model.
    :return: Nominal frequency in Hz.
    """
    return float(grid.fBase)


def mw_to_pu_on_grid_base(value_mw: float, grid: MultiCircuit) -> float:
    """
    Convert MW-like static power to p.u. on ``grid.Sbase``.

    :param value_mw: Static active-power-like quantity in MW.
    :param grid: Static network model.
    :return: Per-unit value on ``grid.Sbase``.
    """
    return float(value_mw) / float(grid.Sbase)


def mvar_to_pu_on_grid_base(value_mvar: float, grid: MultiCircuit) -> float:
    """
    Convert MVAr-like static power to p.u. on ``grid.Sbase``.

    :param value_mvar: Static reactive-power-like quantity in MVAr.
    :param grid: Static network model.
    :return: Per-unit value on ``grid.Sbase``.
    """
    return float(value_mvar) / float(grid.Sbase)


def _float_or_zero(value: float | None) -> float:
    """
    Return one scalar value, replacing ``None`` with zero.

    :param value: Optional scalar value.
    :return: Float scalar with ``None`` mapped to ``0.0``.
    """
    out: float

    if value is None:
        out = 0.0
    else:
        out = float(value)

    return out


def _abc_values_are_meaningful(
        phase_a: float | None,
        phase_b: float | None,
        phase_c: float | None,
) -> bool:
    """
    Return whether explicit ABC values should override balanced fallback.

    The static-device classes do not expose a dedicated "phase values are
    provided" flag. The practical contract used here is therefore explicit and
    conservative: if any phase value is numerically non-zero, the phase triplet is
    treated as meaningful and is preserved.

    :param phase_a: Phase-A scalar.
    :param phase_b: Phase-B scalar.
    :param phase_c: Phase-C scalar.
    :return: ``True`` when explicit phase values should be used.
    """
    value_a: float = _float_or_zero(phase_a)
    value_b: float = _float_or_zero(phase_b)
    value_c: float = _float_or_zero(phase_c)
    meaningful: bool

    if abs(value_a) > 0.0:
        meaningful = True
    else:
        if abs(value_b) > 0.0:
            meaningful = True
        else:
            if abs(value_c) > 0.0:
                meaningful = True
            else:
                meaningful = False

    return meaningful


def balanced_to_abc_power(total_value: float | None) -> np.ndarray:
    """
    Split one balanced total scalar equally into explicit ABC values.

    :param total_value: Balanced total scalar.
    :return: ABC array with one third of the total in each phase.
    """
    total_scalar: float = _float_or_zero(total_value)
    phase_scalar: float = total_scalar / 3.0
    phase_values: np.ndarray = np.zeros(3, dtype=np.float64)

    phase_values[0] = phase_scalar
    phase_values[1] = phase_scalar
    phase_values[2] = phase_scalar

    return phase_values


def _resolve_explicit_or_balanced_abc_values(
        phase_a: float | None,
        phase_b: float | None,
        phase_c: float | None,
        total_value: float | None,
) -> np.ndarray:
    """
    Resolve one ABC quantity from explicit phase values or from a balanced total.

    :param phase_a: Phase-A scalar.
    :param phase_b: Phase-B scalar.
    :param phase_c: Phase-C scalar.
    :param total_value: Balanced total scalar used as fallback.
    :return: Explicit ABC array.
    """
    phase_values: np.ndarray = np.zeros(3, dtype=np.float64)

    if _abc_values_are_meaningful(phase_a=phase_a, phase_b=phase_b, phase_c=phase_c):
        phase_values[0] = _float_or_zero(phase_a)
        phase_values[1] = _float_or_zero(phase_b)
        phase_values[2] = _float_or_zero(phase_c)
    else:
        phase_values = balanced_to_abc_power(total_value=total_value)

    return phase_values


def abc_to_nabc(phase_values_abc: np.ndarray) -> np.ndarray:
    """
    Expand an ABC phase array into fixed NABC order.

    :param phase_values_abc: Explicit ABC array.
    :return: NABC array with a zero neutral entry.
    """
    phase_values_nabc: np.ndarray = np.zeros(4, dtype=np.float64)

    phase_values_nabc[0] = 0.0
    phase_values_nabc[1] = float(phase_values_abc[0])
    phase_values_nabc[2] = float(phase_values_abc[1])
    phase_values_nabc[3] = float(phase_values_abc[2])

    return phase_values_nabc


def get_load_power_phase_values_pu_abc(load: Any, grid: MultiCircuit) -> Tuple[np.ndarray, np.ndarray]:
    """
    Return explicit ABC active/reactive load powers in p.u. on ``grid.Sbase``.

    Explicit phase values are used when they are meaningfully populated.
    Otherwise the balanced total values are split equally among phases.

    :param load: Load-like static device.
    :param grid: Static network model.
    :return: Pair ``(p_abc_pu, q_abc_pu)``.
    """
    p_mw_abc: np.ndarray = _resolve_explicit_or_balanced_abc_values(
        phase_a=load.Pa,
        phase_b=load.Pb,
        phase_c=load.Pc,
        total_value=load.P,
    )
    q_mvar_abc: np.ndarray = _resolve_explicit_or_balanced_abc_values(
        phase_a=load.Qa,
        phase_b=load.Qb,
        phase_c=load.Qc,
        total_value=load.Q,
    )
    p_pu_abc: np.ndarray = p_mw_abc / float(grid.Sbase)
    q_pu_abc: np.ndarray = q_mvar_abc / float(grid.Sbase)

    return p_pu_abc, q_pu_abc


def get_load_impedance_phase_values_pu_abc(load: Any, grid: MultiCircuit) -> Tuple[np.ndarray, np.ndarray]:
    """
    Return explicit ABC ZIP-impedance powers in p.u. on ``grid.Sbase``.

    :param load: Load-like static device exposing ``G``/``B`` totals and
        ``G1``/``G2``/``G3`` plus ``B1``/``B2``/``B3`` phase values.
    :param grid: Static network model.
    :return: Pair ``(g_abc_pu, b_abc_pu)``.
    """
    g_mw_abc: np.ndarray = _resolve_explicit_or_balanced_abc_values(
        phase_a=load.G1,
        phase_b=load.G2,
        phase_c=load.G3,
        total_value=load.G,
    )
    b_mvar_abc: np.ndarray = _resolve_explicit_or_balanced_abc_values(
        phase_a=load.B1,
        phase_b=load.B2,
        phase_c=load.B3,
        total_value=load.B,
    )
    g_pu_abc: np.ndarray = g_mw_abc / float(grid.Sbase)
    b_pu_abc: np.ndarray = b_mvar_abc / float(grid.Sbase)

    return g_pu_abc, b_pu_abc


def get_load_current_phase_values_pu_abc(load: Any, grid: MultiCircuit) -> Tuple[np.ndarray, np.ndarray]:
    """
    Return explicit ABC ZIP-current powers in p.u. on ``grid.Sbase``.

    :param load: Load-like static device exposing ``Ir``/``Ii`` totals and
        ``Ir1``/``Ir2``/``Ir3`` plus ``Ii1``/``Ii2``/``Ii3`` phase values.
    :param grid: Static network model.
    :return: Pair ``(ir_abc_pu, ii_abc_pu)``.
    """
    ir_mw_abc: np.ndarray = _resolve_explicit_or_balanced_abc_values(
        phase_a=load.Ir1,
        phase_b=load.Ir2,
        phase_c=load.Ir3,
        total_value=load.Ir,
    )
    ii_mvar_abc: np.ndarray = _resolve_explicit_or_balanced_abc_values(
        phase_a=load.Ii1,
        phase_b=load.Ii2,
        phase_c=load.Ii3,
        total_value=load.Ii,
    )
    ir_pu_abc: np.ndarray = ir_mw_abc / float(grid.Sbase)
    ii_pu_abc: np.ndarray = ii_mvar_abc / float(grid.Sbase)

    return ir_pu_abc, ii_pu_abc


def get_shunt_phase_values_pu_abc(shunt: Any, grid: MultiCircuit) -> Tuple[np.ndarray, np.ndarray]:
    """
    Return explicit ABC shunt conductance/susceptance powers in p.u.

    Explicit phase values are used when meaningfully populated. Otherwise the
    balanced totals are split equally among phases.

    :param shunt: Shunt-like static device.
    :param grid: Static network model.
    :return: Pair ``(g_abc_pu, b_abc_pu)``.
    """
    g_mw_abc: np.ndarray = _resolve_explicit_or_balanced_abc_values(
        phase_a=shunt.Ga,
        phase_b=shunt.Gb,
        phase_c=shunt.Gc,
        total_value=shunt.G,
    )
    b_mvar_abc: np.ndarray = _resolve_explicit_or_balanced_abc_values(
        phase_a=shunt.Ba,
        phase_b=shunt.Bb,
        phase_c=shunt.Bc,
        total_value=shunt.B,
    )
    g_pu_abc: np.ndarray = g_mw_abc / float(grid.Sbase)
    b_pu_abc: np.ndarray = b_mvar_abc / float(grid.Sbase)

    return g_pu_abc, b_pu_abc


def get_current_injection_phase_values_pu_abc(
        current_injection: Any,
        grid: MultiCircuit,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Return explicit ABC current-injection powers in p.u. on ``grid.Sbase``.

    :param current_injection: Current-injection static device.
    :param grid: Static network model.
    :return: Pair ``(ir_abc_pu, ii_abc_pu)``.
    """
    ir_mw_abc: np.ndarray = _resolve_explicit_or_balanced_abc_values(
        phase_a=current_injection.Ir1,
        phase_b=current_injection.Ir2,
        phase_c=current_injection.Ir3,
        total_value=current_injection.Ir,
    )
    ii_mvar_abc: np.ndarray = _resolve_explicit_or_balanced_abc_values(
        phase_a=current_injection.Ii1,
        phase_b=current_injection.Ii2,
        phase_c=current_injection.Ii3,
        total_value=current_injection.Ii,
    )
    ir_pu_abc: np.ndarray = ir_mw_abc / float(grid.Sbase)
    ii_pu_abc: np.ndarray = ii_mvar_abc / float(grid.Sbase)

    return ir_pu_abc, ii_pu_abc


def shunt_connection_code(connection_type: ShuntConnectionType) -> float:
    """
    Convert a static shunt connection enum into a stable EMT code.

    :param connection_type: Static connection enum.
    :return: Numerical code used by static EMT parameters.
    """
    code: float

    if connection_type == ShuntConnectionType.GroundedStar:
        code = 1.0
    elif connection_type == ShuntConnectionType.FloatingStar:
        code = 2.0
    elif connection_type == ShuntConnectionType.NeutralStar:
        code = 3.0
    elif connection_type == ShuntConnectionType.Delta:
        code = 4.0
    else:
        code = 0.0

    return code


def external_grid_mode_code(mode: ExternalGridMode) -> float:
    """
    Convert a static external-grid mode enum into a stable EMT code.

    :param mode: External-grid mode.
    :return: Numerical code used by static EMT parameters.
    """
    code: float

    if mode == ExternalGridMode.PQ:
        code = 1.0
    elif mode == ExternalGridMode.PV:
        code = 2.0
    elif mode == ExternalGridMode.VD:
        code = 3.0
    else:
        code = 0.0

    return code


def controllable_shunt_mode_code(mode: ShuntControlMode) -> float:
    """
    Convert a controllable-shunt control mode into a stable EMT code.

    :param mode: Static shunt control mode.
    :return: Numerical code used by static EMT parameters.
    """
    code: float

    if mode == ShuntControlMode.Locked:
        code = 1.0
    elif mode == ShuntControlMode.Continuous:
        code = 2.0
    elif mode == ShuntControlMode.Discrete:
        code = 3.0
    else:
        code = 0.0

    return code



def assign_static_api_object_mapping_for_device(
        grid: MultiCircuit,
        device: Any,
        mdl: Block,
        logger: Logger | None,
) -> None:
    """
    Assign static API-object parameters for one EMT device block.

    The dispatcher is generic with respect to RMS/EMT templates. A template receives
    values only for the ``ParamPowerFlowRefferenceType`` keys it exposes in
    ``mdl.api_obj_mapping``. Adding a new EMT model for an already-supported
    ``DeviceType`` should not require modifying ``EmtProblemDae``.

    :param grid: Static network model containing base values.
    :param device: Static grid device owning the EMT model.
    :param mdl: EMT block receiving static parameter constants.
    :param logger: Optional logger used for diagnostics.
    :return: None.
    """
    api_obj_mapping: Any = mdl.api_obj_mapping

    if isinstance(api_obj_mapping, dict):
        if len(api_obj_mapping) == 0:
            pass
        else:
            # The dispatch is based on the static device type, not on the EMT
            # template name. The template only selects a subset of keys.
            device_type: DeviceType = device.device_type

            if device_type == DeviceType.LoadDevice:
                assign_load_static_api_mapping(
                    grid=grid,
                    load=device,
                    mdl=mdl,
                    logger=logger,
                )
            elif device_type == DeviceType.StaticGeneratorDevice:
                assign_static_generator_static_api_mapping(
                    grid=grid,
                    static_generator=device,
                    mdl=mdl,
                    logger=logger,
                )
            elif device_type == DeviceType.ExternalGridDevice:
                assign_external_grid_static_api_mapping(
                    grid=grid,
                    external_grid=device,
                    mdl=mdl,
                    logger=logger,
                )
            elif device_type == DeviceType.ShuntDevice:
                assign_shunt_static_api_mapping(
                    grid=grid,
                    shunt=device,
                    mdl=mdl,
                    logger=logger,
                )
            elif device_type == DeviceType.ControllableShuntDevice:
                assign_controllable_shunt_static_api_mapping(
                    grid=grid,
                    controllable_shunt=device,
                    mdl=mdl,
                    logger=logger,
                )
            elif device_type == DeviceType.CurrentInjectionDevice:
                assign_current_injection_static_api_mapping(
                    grid=grid,
                    current_injection=device,
                    mdl=mdl,
                    logger=logger,
                )
            elif device_type == DeviceType.GeneratorDevice:
                assign_generator_static_api_mapping(
                    grid=grid,
                    generator=device,
                    mdl=mdl,
                    logger=logger,
                )
            elif device_type == DeviceType.BatteryDevice:
                assign_battery_static_api_mapping(
                    grid=grid,
                    battery=device,
                    mdl=mdl,
                    logger=logger,
                )
            elif device_type == DeviceType.VscDevice:
                assign_vsc_static_api_mapping(
                    grid=grid,
                    vsc=device,
                    mdl=mdl,
                    logger=logger,
                )
            elif device_type == DeviceType.DCLineDevice:
                if isinstance(device, DcLine):
                    assign_dc_line_static_api_mapping(
                        dc_line=device,
                        mdl=mdl,
                        logger=logger,
                    )
                else:
                    add_static_mapping_warning(
                        logger=logger,
                        device_name=str(device.name),
                        message="DCLineDevice static mapping skipped because the object type is not DcLine.",
                        value=str(device_type),
                        expected_value="DcLine instance",
                        device_property="device_type",
                    )
            elif device_type == DeviceType.Transformer2WDevice:
                if isinstance(device, Transformer2W):
                    assign_transformer2w_static_api_mapping(
                        grid=grid,
                        transformer=device,
                        mdl=mdl,
                        logger=logger,
                    )
                else:
                    add_static_mapping_warning(
                        logger=logger,
                        device_name=str(device.name),
                        message="Transformer2WDevice static mapping skipped because the object type is not Transformer2W.",
                        value=str(device_type),
                        expected_value="Transformer2W instance",
                        device_property="device_type",
                    )
            elif device_type == DeviceType.WindingDevice:
                if isinstance(device, Transformer2W):
                    assign_transformer2w_static_api_mapping(
                        grid=grid,
                        transformer=device,
                        mdl=mdl,
                        logger=logger,
                    )
                else:
                    add_static_mapping_warning(
                        logger=logger,
                        device_name=str(device.name),
                        message="WindingDevice static mapping skipped because the object type is not Transformer2W-compatible.",
                        value=str(device_type),
                        expected_value="Transformer2W-compatible instance",
                        device_property="device_type",
                    )
            elif device_type == DeviceType.LineDevice:
                assign_line_static_api_mapping(
                    grid=grid,
                    line=device,
                    mdl=mdl,
                    logger=logger,
                )
            elif device_type == DeviceType.HVDCLineDevice:
                assign_hvdc_line_static_api_mapping(
                    hvdc_line=device,
                    mdl=mdl,
                    logger=logger,
                )
            elif device_type == DeviceType.SeriesReactanceDevice:
                assign_series_reactance_static_api_mapping(
                    series_reactance=device,
                    mdl=mdl,
                    logger=logger,
                )
            elif device_type == DeviceType.SwitchDevice:
                assign_switch_static_api_mapping(
                    switch=device,
                    mdl=mdl,
                    logger=logger,
                )
            elif device_type == DeviceType.UpfcDevice:
                assign_upfc_static_api_mapping(
                    upfc=device,
                    mdl=mdl,
                    logger=logger,
                )
            else:
                # Compatibility fallback: older branch-like models may expose
                # line matrix keys even if their device_type is more generic.
                # The fallback activates only when the EMT template explicitly
                # requests line-matrix keys.
                if api_mapping_has_any_key(mdl=mdl, keys=get_all_line_matrix_keys()):
                    assign_line_static_api_mapping(
                        grid=grid,
                        line=device,
                        mdl=mdl,
                        logger=logger,
                    )
                else:
                    pass
    else:
        pass



def converter_control_code(control_tpe: ConverterControlType | None) -> float:
    """
    Convert a static VSC control enum to the EMT template numerical code.

    :param control_tpe: Converter control enum or ``None``.
    :return: Numerical control code used by existing EMT templates.
    """
    code: float

    if control_tpe is None:
        code = 0.0
    elif control_tpe == ConverterControlType.Vm_dc:
        code = 1.0
    elif control_tpe == ConverterControlType.Vm_ac:
        code = 2.0
    elif control_tpe == ConverterControlType.Va_ac:
        code = 3.0
    elif control_tpe == ConverterControlType.Qac:
        code = 4.0
    elif control_tpe == ConverterControlType.Pdc:
        code = 5.0
    elif control_tpe == ConverterControlType.Pac:
        code = 6.0
    elif control_tpe == ConverterControlType.Pdc_angle_droop:
        code = 7.0
    elif control_tpe == ConverterControlType.Imax:
        code = 8.0
    else:
        code = 0.0

    return code



def xfmr_connection_matrix(winding_tpe: WindingType) -> np.ndarray:
    """
    Return the 3x3 transformer winding connection matrix.

    :param winding_tpe: Transformer winding connection type.
    :return: 3x3 winding connection matrix.
    """
    matrix: np.ndarray

    if winding_tpe in (
            WindingType.GroundedStar,
            WindingType.NeutralStar,
            WindingType.FloatingStar,
    ):
        matrix = np.eye(3, dtype=float)
    else:
        if winding_tpe == WindingType.Delta:
            matrix = np.array(
                [
                    [1.0, 0.0, -1.0],
                    [-1.0, 1.0, 0.0],
                    [0.0, -1.0, 1.0],
                ],
                dtype=float,
            ) / np.sqrt(3.0)
        else:
            matrix = np.eye(3, dtype=float)

    return matrix


def xfmr_phase_permutation_matrix(clock: int) -> np.ndarray:
    """
    Return the transformer phase permutation matrix from vector-group clock.

    :param clock: Transformer vector-group clock number.
    :return: 3x3 phase permutation matrix.
    """
    matrix: np.ndarray
    shift: int = (int(clock) // 4) % 3

    if shift == 0:
        matrix = np.eye(3, dtype=float)
    else:
        if shift == 1:
            matrix = np.array(
                [
                    [0.0, 1.0, 0.0],
                    [0.0, 0.0, 1.0],
                    [1.0, 0.0, 0.0],
                ],
                dtype=float,
            )
        else:
            matrix = np.array(
                [
                    [0.0, 0.0, 1.0],
                    [1.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0],
                ],
                dtype=float,
            )

    return matrix




def get_transformer_from_connection_keys() -> List[List[ParamPowerFlowRefferenceType]]:
    """
    Return 3x3 from-side transformer connection mapping keys.

    :return: Matrix of from-side API-object keys.
    """
    keys: List[List[ParamPowerFlowRefferenceType]] = list([
        list([
            ParamPowerFlowRefferenceType.transformer_from_connection_aa,
            ParamPowerFlowRefferenceType.transformer_from_connection_ab,
            ParamPowerFlowRefferenceType.transformer_from_connection_ac,
        ]),
        list([
            ParamPowerFlowRefferenceType.transformer_from_connection_ba,
            ParamPowerFlowRefferenceType.transformer_from_connection_bb,
            ParamPowerFlowRefferenceType.transformer_from_connection_bc,
        ]),
        list([
            ParamPowerFlowRefferenceType.transformer_from_connection_ca,
            ParamPowerFlowRefferenceType.transformer_from_connection_cb,
            ParamPowerFlowRefferenceType.transformer_from_connection_cc,
        ]),
    ])

    return keys


def get_transformer_to_connection_keys() -> List[List[ParamPowerFlowRefferenceType]]:
    """
    Return 3x3 to-side transformer connection mapping keys.

    :return: Matrix of to-side API-object keys.
    """
    keys: List[List[ParamPowerFlowRefferenceType]] = list([
        list([
            ParamPowerFlowRefferenceType.transformer_to_connection_aa,
            ParamPowerFlowRefferenceType.transformer_to_connection_ab,
            ParamPowerFlowRefferenceType.transformer_to_connection_ac,
        ]),
        list([
            ParamPowerFlowRefferenceType.transformer_to_connection_ba,
            ParamPowerFlowRefferenceType.transformer_to_connection_bb,
            ParamPowerFlowRefferenceType.transformer_to_connection_bc,
        ]),
        list([
            ParamPowerFlowRefferenceType.transformer_to_connection_ca,
            ParamPowerFlowRefferenceType.transformer_to_connection_cb,
            ParamPowerFlowRefferenceType.transformer_to_connection_cc,
        ]),
    ])

    return keys


def assign_3x3_static_matrix(
        mdl: Block,
        matrix: np.ndarray,
        keys: List[List[ParamPowerFlowRefferenceType]],
        logger: Logger | None,
        device_name: str,
) -> None:
    """
    Assign a 3x3 static matrix through a 3x3 API-object key matrix.

    :param mdl: EMT block.
    :param matrix: Numerical 3x3 matrix.
    :param keys: API-object key matrix.
    :param logger: Optional logger.
    :param device_name: Device name used in diagnostics.
    :return: None.
    """
    row_index: int = 0

    while row_index < 3:
        col_index: int = 0

        while col_index < 3:
            assign_api_mapping_value_if_present(
                mdl=mdl,
                key=keys[row_index][col_index],
                value=float(matrix[row_index, col_index]),
                logger=logger,
                device_name=device_name,
            )
            col_index += 1

        row_index += 1


def get_transformer_equivalent_circuit_derived_keys() -> List[ParamPowerFlowRefferenceType]:
    """
    Return transformer equivalent-circuit derived-value keys.

    :return: Derived equivalent-circuit API-object keys.
    """
    keys: List[ParamPowerFlowRefferenceType] = list([
        ParamPowerFlowRefferenceType.transformer_winding1_resistance_pu,
        ParamPowerFlowRefferenceType.transformer_winding2_resistance_pu,
        ParamPowerFlowRefferenceType.transformer_winding1_inductance_pu_s,
        ParamPowerFlowRefferenceType.transformer_winding2_inductance_pu_s,
        ParamPowerFlowRefferenceType.transformer_mutual_inductance_pu_s,
        ParamPowerFlowRefferenceType.transformer_magnetizing_conductance_pu,
    ])

    return keys


def transformer_equivalent_circuit_values_are_requested(mdl: Block) -> bool:
    """
    Return whether any transformer equivalent-circuit derived value is requested.

    This helper is only a computation guard. It is not a template-family or
    model-family detector.

    :param mdl: EMT block.
    :return: ``True`` if any derived transformer key is exposed.
    """
    return api_mapping_has_any_key(mdl=mdl, keys=get_transformer_equivalent_circuit_derived_keys())


def compute_transformer_equivalent_circuit_values(
        omega_base: float,
        transformer_r_pu: float,
        transformer_x_pu: float,
        transformer_g_pu: float,
        transformer_b_pu: float,
        total_voltage_ratio: float,
        total_voltage_ratio_square: float,
        eps_value: float,
) -> Tuple[float, float, float, float, float, float]:
    """
    Compute derived transformer equivalent-circuit values from static data.

    :param omega_base: Angular base frequency in rad/s.
    :param transformer_r_pu: Total series resistance in p.u.
    :param transformer_x_pu: Total series reactance in p.u.
    :param transformer_g_pu: Magnetizing conductance in p.u.
    :param transformer_b_pu: Magnetizing susceptance in p.u.
    :param total_voltage_ratio: Total nominal-times-tap voltage ratio.
    :param total_voltage_ratio_square: Square of the total voltage ratio.
    :param eps_value: Numerical guard constant.
    :return: Tuple ``(r1, r2, l1, l2, mutual_inductance, g_core)``.
    """
    r1_value: float = 0.5 * transformer_r_pu
    r2_value: float = 0.5 * transformer_r_pu / (total_voltage_ratio_square + eps_value)
    leakage_l_primary: float = 0.5 * transformer_x_pu / (omega_base + eps_value)
    leakage_l_secondary: float = leakage_l_primary / (total_voltage_ratio_square + eps_value)
    x_magnetizing: float

    if abs(transformer_b_pu) > eps_value:
        x_magnetizing = 1.0 / abs(transformer_b_pu)
    else:
        x_magnetizing = max(1000.0, 100.0 * max(abs(transformer_x_pu), 1.0))

    magnetizing_l_primary: float = x_magnetizing / (omega_base + eps_value)
    magnetizing_l_secondary: float = magnetizing_l_primary / (total_voltage_ratio_square + eps_value)
    mutual_inductance: float = magnetizing_l_primary / (total_voltage_ratio + eps_value)
    l1_value: float = leakage_l_primary + magnetizing_l_primary
    l2_value: float = leakage_l_secondary + magnetizing_l_secondary
    g_core: float = transformer_g_pu

    return r1_value, r2_value, l1_value, l2_value, mutual_inductance, g_core


def get_line_r_keys() -> List[List[ParamPowerFlowRefferenceType]]:
    """
    Return the fixed 4x4 NABC resistance mapping keys.

    :return: Matrix of resistance API-object keys.
    """
    keys: List[List[ParamPowerFlowRefferenceType]] = list([
        list([
            ParamPowerFlowRefferenceType.Rnn,
            ParamPowerFlowRefferenceType.Rna,
            ParamPowerFlowRefferenceType.Rnb,
            ParamPowerFlowRefferenceType.Rnc,
        ]),
        list([
            ParamPowerFlowRefferenceType.Ran,
            ParamPowerFlowRefferenceType.Raa,
            ParamPowerFlowRefferenceType.Rab,
            ParamPowerFlowRefferenceType.Rac,
        ]),
        list([
            ParamPowerFlowRefferenceType.Rbn,
            ParamPowerFlowRefferenceType.Rba,
            ParamPowerFlowRefferenceType.Rbb,
            ParamPowerFlowRefferenceType.Rbc,
        ]),
        list([
            ParamPowerFlowRefferenceType.Rcn,
            ParamPowerFlowRefferenceType.Rca,
            ParamPowerFlowRefferenceType.Rcb,
            ParamPowerFlowRefferenceType.Rcc,
        ]),
    ])

    return keys


def get_line_linv_keys() -> List[List[ParamPowerFlowRefferenceType]]:
    """
    Return the fixed 4x4 NABC inverse-inductance mapping keys.

    :return: Matrix of inverse-inductance API-object keys.
    """
    keys: List[List[ParamPowerFlowRefferenceType]] = list([
        list([
            ParamPowerFlowRefferenceType.Linv_nn,
            ParamPowerFlowRefferenceType.Linv_na,
            ParamPowerFlowRefferenceType.Linv_nb,
            ParamPowerFlowRefferenceType.Linv_nc,
        ]),
        list([
            ParamPowerFlowRefferenceType.Linv_an,
            ParamPowerFlowRefferenceType.Linv_aa,
            ParamPowerFlowRefferenceType.Linv_ab,
            ParamPowerFlowRefferenceType.Linv_ac,
        ]),
        list([
            ParamPowerFlowRefferenceType.Linv_bn,
            ParamPowerFlowRefferenceType.Linv_ba,
            ParamPowerFlowRefferenceType.Linv_bb,
            ParamPowerFlowRefferenceType.Linv_bc,
        ]),
        list([
            ParamPowerFlowRefferenceType.Linv_cn,
            ParamPowerFlowRefferenceType.Linv_ca,
            ParamPowerFlowRefferenceType.Linv_cb,
            ParamPowerFlowRefferenceType.Linv_cc,
        ]),
    ])

    return keys


def get_line_c_keys() -> List[List[ParamPowerFlowRefferenceType]]:
    """
    Return the fixed 4x4 NABC capacitance mapping keys.

    :return: Matrix of capacitance API-object keys.
    """
    keys: List[List[ParamPowerFlowRefferenceType]] = list([
        list([
            ParamPowerFlowRefferenceType.Cnn,
            ParamPowerFlowRefferenceType.Cna,
            ParamPowerFlowRefferenceType.Cnb,
            ParamPowerFlowRefferenceType.Cnc,
        ]),
        list([
            ParamPowerFlowRefferenceType.Can,
            ParamPowerFlowRefferenceType.Caa,
            ParamPowerFlowRefferenceType.Cab,
            ParamPowerFlowRefferenceType.Cac,
        ]),
        list([
            ParamPowerFlowRefferenceType.Cbn,
            ParamPowerFlowRefferenceType.Cba,
            ParamPowerFlowRefferenceType.Cbb,
            ParamPowerFlowRefferenceType.Cbc,
        ]),
        list([
            ParamPowerFlowRefferenceType.Ccn,
            ParamPowerFlowRefferenceType.Cca,
            ParamPowerFlowRefferenceType.Ccb,
            ParamPowerFlowRefferenceType.Ccc,
        ]),
    ])

    return keys


def flatten_matrix_keys(
        matrix_keys: List[List[ParamPowerFlowRefferenceType]],
) -> List[ParamPowerFlowRefferenceType]:
    """
    Flatten a matrix of API-object enum keys.

    :param matrix_keys: Matrix of API-object keys.
    :return: Flat list of keys.
    """
    flat_keys: List[ParamPowerFlowRefferenceType] = list()
    row_index: int = 0

    while row_index < len(matrix_keys):
        col_index: int = 0

        while col_index < len(matrix_keys[row_index]):
            flat_keys.append(matrix_keys[row_index][col_index])
            col_index += 1

        row_index += 1

    return flat_keys


def get_all_line_matrix_keys() -> List[ParamPowerFlowRefferenceType]:
    """
    Return every line R, Linv and C API-object key.

    :return: Flat list of all line matrix mapping keys.
    """
    all_keys: List[ParamPowerFlowRefferenceType] = list()
    key_matrices: List[List[List[ParamPowerFlowRefferenceType]]] = list([
        get_line_r_keys(),
        get_line_linv_keys(),
        get_line_c_keys(),
    ])
    matrix_index: int = 0

    while matrix_index < len(key_matrices):
        flat_keys: List[ParamPowerFlowRefferenceType] = flatten_matrix_keys(key_matrices[matrix_index])
        key_index: int = 0

        while key_index < len(flat_keys):
            all_keys.append(flat_keys[key_index])
            key_index += 1

        matrix_index += 1

    return all_keys


def get_line_active_global_indices(line: Any) -> List[int]:
    """
    Return active NABC phase indices for a line-like device.

    :param line: Line-like branch device.
    :return: Active indices in fixed NABC order.
    """
    phase_mask: List[bool] = list([
        bool(line.ys.phN),
        bool(line.ys.phA),
        bool(line.ys.phB),
        bool(line.ys.phC),
    ])
    active_indices: List[int] = list()
    phase_index: int = 0

    while phase_index < len(phase_mask):
        if phase_mask[phase_index]:
            active_indices.append(phase_index)
        else:
            pass

        phase_index += 1

    return active_indices


def build_uncoupled_line_static_matrices(
        line: Any,
        omega_base: float,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Build uncoupled fallback line matrices.

    This preserves the historical fallback used when no tower/template matrix is
    available. The historical code uses ``X = line.B`` and ``B = line.X`` in
    this fallback; that convention is preserved here to avoid a hidden numerical
    behavior change in the mapping refactor.

    :param line: Line-like branch device.
    :param omega_base: Base angular frequency.
    :return: Tuple ``(R, L, C)`` in EMT per-unit form.
    """
    r_value: float = float(line.R)

    # Historical fallback naming intentionally preserved for the common case.
    # Some saved grids still rely on ``line.B`` feeding the series-reactance slot.
    # However, when that historical slot is zero while the direct line reactance is
    # non-zero, the EMT pi-line becomes singular and loses all series dynamics.
    # In that narrow case we prefer the physical direct interpretation.
    x_value: float = float(line.B)
    b_value: float = float(line.X)

    if abs(x_value) <= 1.0e-15 and abs(float(line.X)) > 1.0e-15:
        x_value = float(line.X)
        b_value = float(line.B)
    else:
        pass

    r_full: np.ndarray = np.zeros((3, 3), dtype=np.float64)
    x_full: np.ndarray = np.zeros((3, 3), dtype=np.float64)
    bsh_full: np.ndarray = np.zeros((3, 3), dtype=np.float64)
    phase_index: int = 0

    while phase_index < 3:
        r_full[phase_index, phase_index] = r_value
        x_full[phase_index, phase_index] = x_value
        bsh_full[phase_index, phase_index] = b_value
        phase_index += 1

    l_full: np.ndarray = x_full / (omega_base + 1.0e-20)
    c_full: np.ndarray = (bsh_full / (omega_base + 1.0e-20)) / 2.0

    return r_full, l_full, c_full


def build_line_static_matrices(
        grid: MultiCircuit,
        line: Any,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Build line R, L and C matrices in EMT per-unit form.

    :param grid: Static network model.
    :param line: Line-like branch device.
    :return: Tuple ``(R, L, C)`` in reduced active-phase coordinates.
    """
    frequency_base: float = float(grid.fBase)
    omega_base: float = 2.0 * np.pi * frequency_base
    voltage_base: float = float(line.bus_from.Vnom) * 1.0e3
    sbase_va: float = float(grid.Sbase) * 1.0e6
    zbase: float = (voltage_base * voltage_base) / sbase_va
    ybase: float = 1.0 / zbase
    line_template: Any = line.template

    if type(line_template)== OverheadLineType:
        r_full: np.ndarray
        l_full: np.ndarray
        c_full: np.ndarray
        r_full, l_full, c_full = build_uncoupled_line_static_matrices(
            line=line,
            omega_base=omega_base,
        )
        # Tower/template matrices are physical line matrices. They are first
        # length-scaled and then converted to the system EMT per-unit base.
        z_phys: np.ndarray = line_template.z_nabc * float(line.length)
        y_phys: np.ndarray = line_template.y_nabc * float(line.length)

        z_pu: np.ndarray = z_phys / zbase
        y_pu: np.ndarray = y_phys / ybase

        r_full = np.real(z_pu)
        x_full: np.ndarray = np.imag(z_pu)
        l_full = x_full / (omega_base + 1.0e-20)

        bsh_full: np.ndarray = np.imag(y_pu)
        c_full = (bsh_full / (omega_base + 1.0e-20)) / 2.0
    else:
        r_full: np.ndarray
        l_full: np.ndarray
        c_full: np.ndarray
        r_full, l_full, c_full = build_uncoupled_line_static_matrices(
            line=line,
            omega_base=omega_base,
        )

    return r_full, l_full, c_full


def validate_line_static_matrices(
        line: Any,
        r_full: np.ndarray,
        l_full: np.ndarray,
        c_full: np.ndarray,
        n_active: int,
        logger: Logger | None,
) -> bool:
    """
    Validate reduced line matrix dimensions before assignment.

    :param line: Line-like branch device.
    :param r_full: Reduced resistance matrix.
    :param l_full: Reduced inductance matrix.
    :param c_full: Reduced capacitance matrix.
    :param n_active: Number of active physical phases.
    :param logger: Optional logger.
    :return: ``True`` if all matrices match the active-phase shape.
    """
    valid: bool = True
    expected_shape: Tuple[int, int] = (n_active, n_active)
    device_name: str = str(line.name)

    if r_full.shape != expected_shape:
        add_static_mapping_warning(
            logger=logger,
            device_name=device_name,
            message="Line static mapping skipped because R matrix shape is inconsistent.",
            value=str(r_full.shape),
            expected_value=str(expected_shape),
            device_property="line_static_matrix_shape",
        )
        valid = False
    else:
        pass

    if l_full.shape != expected_shape:
        add_static_mapping_warning(
            logger=logger,
            device_name=device_name,
            message="Line static mapping skipped because L matrix shape is inconsistent.",
            value=str(l_full.shape),
            expected_value=str(expected_shape),
            device_property="line_static_matrix_shape",
        )
        valid = False
    else:
        pass

    if c_full.shape != expected_shape:
        add_static_mapping_warning(
            logger=logger,
            device_name=device_name,
            message="Line static mapping skipped because C matrix shape is inconsistent.",
            value=str(c_full.shape),
            expected_value=str(expected_shape),
            device_property="line_static_matrix_shape",
        )
        valid = False
    else:
        pass

    return valid


def assign_common_injection_static_api_mapping(
        grid: MultiCircuit,
        device: Any,
        mdl: Block,
        logger: Logger | None,
) -> None:
    """
    Assign static parameters inherited from ``InjectionParent``.

    ``injection_use_kw`` is a static boolean flag and
    ``injection_connection_type`` is a stable numeric encoding of the static
    connection enum.

    :param grid: Static network model.
    :param device: Injection-like static device.
    :param mdl: EMT block receiving constants.
    :param logger: Optional logger.
    :return: None.
    """
    device_name: str = str(device.name)

    # if the device is active or not
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.device_active,
        value=boolean_to_float(bool(device.active)),
        logger=logger,
        device_name=device_name,
    )

    # connection type
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.injection_connection_type,
        value=shunt_connection_code(device.conn),
        logger=logger,
        device_name=device_name,
    )


def assign_common_branch_static_api_mapping(
        device: Any,
        mdl: Block,
        logger: Logger | None,
) -> None:
    """
    Assign static parameters inherited from ``BranchParent``.

    :param device: Branch-like static device.
    :param mdl: EMT block receiving constants.
    :param logger: Optional logger.
    :return: None.
    """
    device_name: str = str(device.name)

    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.device_active,
        value=boolean_to_float(bool(device.active)),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.branch_rate_mva,
        value=float(device.rate),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.branch_temp_base_deg_c,
        value=float(device.temp_base),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.branch_temp_oper_deg_c,
        value=float(device.temp_oper),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.branch_alpha_per_deg_c,
        value=float(device.alpha),
        logger=logger,
        device_name=device_name,
    )


def assign_load_static_api_mapping(
        grid: MultiCircuit,
        load: Any,
        mdl: Block,
        logger: Logger | None,
) -> None:
    """
    Assign static load parameters exposed by ``mdl.api_obj_mapping``.

    :param grid: Static network model.
    :param load: Load device.
    :param mdl: Load EMT block.
    :param logger: Optional logger.
    :return: None.
    """
    device_name: str = str(load.name)
    sbase: float = float(grid.Sbase)
    phase_p_pu_abc: np.ndarray
    phase_q_pu_abc: np.ndarray
    phase_g_pu_abc: np.ndarray
    phase_b_pu_abc: np.ndarray
    phase_ir_pu_abc: np.ndarray
    phase_ii_pu_abc: np.ndarray

    phase_p_pu_abc, phase_q_pu_abc = get_load_power_phase_values_pu_abc(load=load, grid=grid)
    phase_g_pu_abc, phase_b_pu_abc = get_load_impedance_phase_values_pu_abc(load=load, grid=grid)
    phase_ir_pu_abc, phase_ii_pu_abc = get_load_current_phase_values_pu_abc(load=load, grid=grid)

    assign_common_injection_static_api_mapping(
        grid=grid,
        device=load,
        mdl=mdl,
        logger=logger,
    )

    # Load ZIP quantities are static power-like data expressed in MW/MVAr at
    # 1.0 p.u. voltage on the network base. They are exported in p.u. on
    # ``grid.Sbase``.
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_p_pu,
        value=mw_to_pu_on_grid_base(float(load.P), grid),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_q_pu,
        value=mvar_to_pu_on_grid_base(float(load.Q), grid),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_pa_pu,
        value=float(phase_p_pu_abc[0]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_pb_pu,
        value=float(phase_p_pu_abc[1]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_pc_pu,
        value=float(phase_p_pu_abc[2]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_qa_pu,
        value=float(phase_q_pu_abc[0]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_qb_pu,
        value=float(phase_q_pu_abc[1]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_qc_pu,
        value=float(phase_q_pu_abc[2]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_g_pu,
        value=mw_to_pu_on_grid_base(float(load.G), grid),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_b_pu,
        value=mvar_to_pu_on_grid_base(float(load.B), grid),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_ga_pu,
        value=float(phase_g_pu_abc[0]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_gb_pu,
        value=float(phase_g_pu_abc[1]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_gc_pu,
        value=float(phase_g_pu_abc[2]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_ba_pu,
        value=float(phase_b_pu_abc[0]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_bb_pu,
        value=float(phase_b_pu_abc[1]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_bc_pu,
        value=float(phase_b_pu_abc[2]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_ir_pu,
        value=mw_to_pu_on_grid_base(float(load.Ir), grid),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_ii_pu,
        value=mvar_to_pu_on_grid_base(float(load.Ii), grid),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_ira_pu,
        value=float(phase_ir_pu_abc[0]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_irb_pu,
        value=float(phase_ir_pu_abc[1]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_irc_pu,
        value=float(phase_ir_pu_abc[2]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_iia_pu,
        value=float(phase_ii_pu_abc[0]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_iib_pu,
        value=float(phase_ii_pu_abc[1]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_iic_pu,
        value=float(phase_ii_pu_abc[2]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_contract_power_pu,
        value=mw_to_pu_on_grid_base(float(load._contract_power), grid),
        logger=logger,
        device_name=device_name,
    )

    if load.bus.is_dc:
        # DC loads use the historical EMT convention: explicit conductance is
        # used when available; otherwise active power is represented as an
        # equivalent conductance on the DC base.
        dc_p_value: float = float(load.P) / sbase
        dc_g_value: float = float(load.G) / sbase

        if dc_g_value == 0.0:
            dc_p_value = 0.0
            dc_g_value = float(load.P) / sbase
        else:
            pass

        assign_api_mapping_value_if_present(
            mdl=mdl,
            key=ParamPowerFlowRefferenceType.Pl0,
            value=dc_p_value,
            logger=logger,
            device_name=device_name,
        )
        assign_api_mapping_value_if_present(
            mdl=mdl,
            key=ParamPowerFlowRefferenceType.g,
            value=dc_g_value,
            logger=logger,
            device_name=device_name,
        )
    else:
        omega_base: float = omega_base_from_grid(grid)
        p_values: np.ndarray = phase_p_pu_abc
        q_values: np.ndarray = phase_q_pu_abc

        p_keys: List[ParamPowerFlowRefferenceType] = list([
            ParamPowerFlowRefferenceType.Pl0_A,
            ParamPowerFlowRefferenceType.Pl0_B,
            ParamPowerFlowRefferenceType.Pl0_C,
        ])
        q_keys: List[ParamPowerFlowRefferenceType] = list([
            ParamPowerFlowRefferenceType.Ql0_A,
            ParamPowerFlowRefferenceType.Ql0_B,
            ParamPowerFlowRefferenceType.Ql0_C,
        ])

        # TODO: static mapping should not put anything in event_dict! allow_event_parameters_target should not exist (ALWAYS FALSE)
        phase_index: int = 0
        while phase_index < 3:
            assign_api_mapping_value_if_present(
                mdl=mdl,
                key=p_keys[phase_index],
                value=float(p_values[phase_index]),
                logger=logger,
                device_name=device_name,
                # allow_event_parameter_target=True,
            )
            assign_api_mapping_value_if_present(
                mdl=mdl,
                key=q_keys[phase_index],
                value=float(q_values[phase_index]),
                logger=logger,
                device_name=device_name,
                # allow_event_parameter_target=True,
            )
            phase_index += 1

        assign_api_mapping_value_if_present(
            mdl=mdl,
            key=ParamPowerFlowRefferenceType.omega_base,
            value=omega_base,
            logger=logger,
            device_name=device_name,
            # allow_event_parameter_target=True,
        )


def assign_static_generator_static_api_mapping(
        grid: MultiCircuit,
        static_generator: Any,
        mdl: Block,
        logger: Logger | None,
) -> None:
    """
    Assign static StaticGenerator parameters exposed by ``mdl.api_obj_mapping``.

    :param grid: Static network model.
    :param static_generator: Static-generator device.
    :param mdl: EMT block.
    :param logger: Optional logger.
    :return: None.
    """
    device_name: str = str(static_generator.name)
    omega_base: float = omega_base_from_grid(grid)
    phase_p_pu_abc: np.ndarray
    phase_q_pu_abc: np.ndarray

    phase_p_pu_abc, phase_q_pu_abc = get_load_power_phase_values_pu_abc(load=static_generator, grid=grid)

    assign_common_injection_static_api_mapping(
        grid=grid,
        device=static_generator,
        mdl=mdl,
        logger=logger,
    )

    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_p_pu,
        value=mw_to_pu_on_grid_base(float(static_generator.P), grid),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_q_pu,
        value=mvar_to_pu_on_grid_base(float(static_generator.Q), grid),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_pa_pu,
        value=float(phase_p_pu_abc[0]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_pb_pu,
        value=float(phase_p_pu_abc[1]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_pc_pu,
        value=float(phase_p_pu_abc[2]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_qa_pu,
        value=float(phase_q_pu_abc[0]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_qb_pu,
        value=float(phase_q_pu_abc[1]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_qc_pu,
        value=float(phase_q_pu_abc[2]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.Pl0_A,
        value=float(phase_p_pu_abc[0]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.Pl0_B,
        value=float(phase_p_pu_abc[1]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.Pl0_C,
        value=float(phase_p_pu_abc[2]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.Ql0_A,
        value=float(phase_q_pu_abc[0]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.Ql0_B,
        value=float(phase_q_pu_abc[1]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.Ql0_C,
        value=float(phase_q_pu_abc[2]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.omega_base,
        value=omega_base,
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.static_generator_snom_mva,
        value=float(static_generator.Snom),
        logger=logger,
        device_name=device_name,
    )


def assign_external_grid_static_api_mapping(
        grid: MultiCircuit,
        external_grid: Any,
        mdl: Block,
        logger: Logger | None,
) -> None:
    """
    Assign static ExternalGrid parameters exposed by ``mdl.api_obj_mapping``.

    :param grid: Static network model.
    :param external_grid: External-grid device.
    :param mdl: EMT block.
    :param logger: Optional logger.
    :return: None.
    """
    device_name: str = str(external_grid.name)
    omega_base: float = omega_base_from_grid(grid)
    phase_p_pu_abc: np.ndarray
    phase_q_pu_abc: np.ndarray

    phase_p_pu_abc, phase_q_pu_abc = get_load_power_phase_values_pu_abc(load=external_grid, grid=grid)

    assign_common_injection_static_api_mapping(
        grid=grid,
        device=external_grid,
        mdl=mdl,
        logger=logger,
    )

    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_p_pu,
        value=mw_to_pu_on_grid_base(float(external_grid.P), grid),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_pa_pu,
        value=float(phase_p_pu_abc[0]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_pb_pu,
        value=float(phase_p_pu_abc[1]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_pc_pu,
        value=float(phase_p_pu_abc[2]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_qa_pu,
        value=float(phase_q_pu_abc[0]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_qb_pu,
        value=float(phase_q_pu_abc[1]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_qc_pu,
        value=float(phase_q_pu_abc[2]),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.omega_base,
        value=omega_base,
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.load_q_pu,
        value=mvar_to_pu_on_grid_base(float(external_grid.Q), grid),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.external_grid_vm_pu,
        value=float(external_grid.Vm),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.external_grid_va_rad,
        value=float(external_grid.Va),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.external_grid_mode_code,
        value=external_grid_mode_code(external_grid.mode),
        logger=logger,
        device_name=device_name,
    )


def assign_shunt_static_api_mapping(
        grid: MultiCircuit,
        shunt: Any,
        mdl: Block,
        logger: Logger | None,
) -> None:
    """
    Assign static Shunt parameters exposed by ``mdl.api_obj_mapping``.

    :param grid: Static network model.
    :param shunt: Shunt device.
    :param mdl: EMT block.
    :param logger: Optional logger.
    :return: None.
    """
    device_name: str = str(shunt.name)
    phase_g_pu_abc: np.ndarray
    phase_b_pu_abc: np.ndarray

    phase_g_pu_abc, phase_b_pu_abc = get_shunt_phase_values_pu_abc(shunt=shunt, grid=grid)

    assign_common_injection_static_api_mapping(
        grid=grid,
        device=shunt,
        mdl=mdl,
        logger=logger,
    )

    assign_api_mapping_value_if_present(mdl=mdl,
                                        key=ParamPowerFlowRefferenceType.shunt_g_pu,
                                        value=mw_to_pu_on_grid_base(float(shunt.G), grid),
                                        logger=logger,
                                        device_name=device_name
                                        )
    assign_api_mapping_value_if_present(mdl=mdl,
                                        key=ParamPowerFlowRefferenceType.shunt_b_pu,
                                        value=mvar_to_pu_on_grid_base(float(shunt.B), grid),
                                        logger=logger,
                                        device_name=device_name
                                        )
    assign_api_mapping_value_if_present(mdl=mdl,
                                        key=ParamPowerFlowRefferenceType.shunt_g0_pu,
                                        value=mw_to_pu_on_grid_base(float(shunt.G0), grid),
                                        logger=logger,
                                        device_name=device_name
                                        )
    assign_api_mapping_value_if_present(mdl=mdl,
                                        key=ParamPowerFlowRefferenceType.shunt_b0_pu,
                                        value=mvar_to_pu_on_grid_base(float(shunt.B0), grid),
                                        logger=logger,
                                        device_name=device_name
                                        )
    assign_api_mapping_value_if_present(mdl=mdl,
                                        key=ParamPowerFlowRefferenceType.shunt_ga_pu,
                                        value=float(phase_g_pu_abc[0]),
                                        logger=logger,
                                        device_name=device_name
                                        )
    assign_api_mapping_value_if_present(mdl=mdl,
                                        key=ParamPowerFlowRefferenceType.shunt_gb_pu,
                                        value=float(phase_g_pu_abc[1]),
                                        logger=logger,
                                        device_name=device_name
                                        )
    assign_api_mapping_value_if_present(mdl=mdl,
                                        key=ParamPowerFlowRefferenceType.shunt_gc_pu,
                                        value=float(phase_g_pu_abc[2]),
                                        logger=logger,
                                        device_name=device_name
                                        )
    assign_api_mapping_value_if_present(mdl=mdl,
                                        key=ParamPowerFlowRefferenceType.shunt_ba_pu,
                                        value=float(phase_b_pu_abc[0]),
                                        logger=logger,
                                        device_name=device_name
                                        )
    assign_api_mapping_value_if_present(mdl=mdl,
                                        key=ParamPowerFlowRefferenceType.shunt_bb_pu,
                                        value=float(phase_b_pu_abc[1]),
                                        logger=logger,
                                        device_name=device_name
                                        )
    assign_api_mapping_value_if_present(mdl=mdl,
                                        key=ParamPowerFlowRefferenceType.shunt_bc_pu,
                                        value=float(phase_b_pu_abc[2]),
                                        logger=logger,
                                        device_name=device_name
                                        )

def assign_controllable_shunt_static_api_mapping(
        grid: MultiCircuit,
        controllable_shunt: Any,
        mdl: Block,
        logger: Logger | None,
) -> None:
    """
    Assign static ControllableShunt parameters exposed by ``mdl.api_obj_mapping``.

    :param grid: Static network model.
    :param controllable_shunt: Controllable shunt device.
    :param mdl: EMT block.
    :param logger: Optional logger.
    :return: None.
    """
    device_name: str = str(controllable_shunt.name)
    assign_shunt_static_api_mapping(
        grid=grid,
        shunt=controllable_shunt,
        mdl=mdl,
        logger=logger,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.controllable_shunt_step,
        value=float(controllable_shunt.step),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.controllable_shunt_vset_pu,
        value=float(controllable_shunt.Vset),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.controllable_shunt_vmin_pu,
        value=float(controllable_shunt.Vmin),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.controllable_shunt_vmax_pu,
        value=float(controllable_shunt.Vmax),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.controllable_shunt_gmin_pu,
        value=mw_to_pu_on_grid_base(float(controllable_shunt.Gmin), grid),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.controllable_shunt_gmax_pu,
        value=mw_to_pu_on_grid_base(float(controllable_shunt.Gmax), grid),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.controllable_shunt_bmin_pu,
        value=mvar_to_pu_on_grid_base(float(controllable_shunt.Bmin), grid),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.controllable_shunt_bmax_pu,
        value=mvar_to_pu_on_grid_base(float(controllable_shunt.Bmax), grid),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.controllable_shunt_control_mode_code,
        value=controllable_shunt_mode_code(controllable_shunt.control_mode),
        logger=logger,
        device_name=device_name,
    )


def assign_current_injection_static_api_mapping(
        grid: MultiCircuit,
        current_injection: Any,
        mdl: Block,
        logger: Logger | None,
) -> None:
    """
    Assign static CurrentInjection parameters exposed by ``mdl.api_obj_mapping``.

    :param grid: Static network model.
    :param current_injection: Current-injection device.
    :param mdl: EMT block.
    :param logger: Optional logger.
    :return: None.
    """
    device_name: str = str(current_injection.name)
    phase_ir_pu_abc: np.ndarray
    phase_ii_pu_abc: np.ndarray

    phase_ir_pu_abc, phase_ii_pu_abc = get_current_injection_phase_values_pu_abc(
        current_injection=current_injection,
        grid=grid,
    )

    assign_common_injection_static_api_mapping(
        grid=grid,
        device=current_injection,
        mdl=mdl,
        logger=logger,
    )

    assign_api_mapping_value_if_present(mdl=mdl,
                                        key=ParamPowerFlowRefferenceType.current_injection_ir_pu,
                                        value=mw_to_pu_on_grid_base(float(current_injection.Ir), grid),
                                        logger=logger,
                                        device_name=device_name
                                        )
    assign_api_mapping_value_if_present(mdl=mdl,
                                        key=ParamPowerFlowRefferenceType.current_injection_ii_pu,
                                        value=mvar_to_pu_on_grid_base(float(current_injection.Ii), grid),
                                        logger=logger,
                                        device_name=device_name
                                        )
    assign_api_mapping_value_if_present(mdl=mdl,
                                        key=ParamPowerFlowRefferenceType.current_injection_ira_pu,
                                        value=float(phase_ir_pu_abc[0]),
                                        logger=logger,
                                        device_name=device_name
                                        )
    assign_api_mapping_value_if_present(mdl=mdl,
                                        key=ParamPowerFlowRefferenceType.current_injection_irb_pu,
                                        value=float(phase_ir_pu_abc[1]),
                                        logger=logger,
                                        device_name=device_name
                                        )
    assign_api_mapping_value_if_present(mdl=mdl,
                                        key=ParamPowerFlowRefferenceType.current_injection_irc_pu,
                                        value=float(phase_ir_pu_abc[2]),
                                        logger=logger,
                                        device_name=device_name
                                        )
    assign_api_mapping_value_if_present(mdl=mdl,
                                        key=ParamPowerFlowRefferenceType.current_injection_iia_pu,
                                        value=float(phase_ii_pu_abc[0]),
                                        logger=logger,
                                        device_name=device_name
                                        )
    assign_api_mapping_value_if_present(mdl=mdl,
                                        key=ParamPowerFlowRefferenceType.current_injection_iib_pu,
                                        value=float(phase_ii_pu_abc[1]),
                                        logger=logger,
                                        device_name=device_name
                                        )
    assign_api_mapping_value_if_present(mdl=mdl,
                                        key=ParamPowerFlowRefferenceType.current_injection_iic_pu,
                                        value=float(phase_ii_pu_abc[2]),
                                        logger=logger,
                                        device_name=device_name
                                        )

def assign_generator_static_api_mapping(
        grid: MultiCircuit,
        generator: Any,
        mdl: Block,
        logger: Logger | None,
) -> None:
    """
    Assign static generator parameters exposed by ``mdl.api_obj_mapping``.

    :param grid: Static network model.
    :param generator: Generator device.
    :param mdl: Generator EMT block.
    :param logger: Optional logger.
    :return: None.
    """
    device_name: str = str(generator.name)
    omega_base: float = omega_base_from_grid(grid)

    assign_common_injection_static_api_mapping(
        grid=grid,
        device=generator,
        mdl=mdl,
        logger=logger,
    )

    # These quantities are static generator object data or system base data.
    # PF-derived sharing targets are intentionally handled outside this module.
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.omega_base,
        value=omega_base,
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.fn,
        value=frequency_base_hz_from_grid(grid),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.ws,
        value=omega_base,
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.R1,
        value=float(generator.R1),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.X1,
        value=float(generator.X1),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.X0,
        value=float(generator.X0),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.generator_p_pu,
        value=mw_to_pu_on_grid_base(float(generator.P), grid),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.generator_q_pu,
        value=mvar_to_pu_on_grid_base(float(generator.Q), grid),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.generator_pmin_pu,
        value=mw_to_pu_on_grid_base(float(generator.Pmin), grid),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.generator_pmax_pu,
        value=mw_to_pu_on_grid_base(float(generator.Pmax), grid),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.generator_qmin_pu,
        value=mvar_to_pu_on_grid_base(float(generator.Qmin), grid),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.generator_qmax_pu,
        value=mvar_to_pu_on_grid_base(float(generator.Qmax), grid),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.generator_power_factor,
        value=float(generator.Pf),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.generator_vset_pu,
        value=float(generator.Vset),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.generator_snom_mva,
        value=float(generator.Snom),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.generator_r0_pu,
        value=float(generator.R0),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.generator_r2_pu,
        value=float(generator.R2),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.generator_x2_pu,
        value=float(generator.X2),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.generator_is_controlled,
        value=boolean_to_float(bool(generator.is_controlled)),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.generator_enabled_dispatch,
        value=boolean_to_float(bool(generator.enabled_dispatch)),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.generator_must_run,
        value=boolean_to_float(bool(generator.must_run)),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.generator_use_reactive_power_curve,
        value=boolean_to_float(bool(generator.use_reactive_power_curve)),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.generator_device_sbase_mva,
        value=float(generator.Sbase),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.freq,
        value=float(generator.freq),
        logger=logger,
        device_name=device_name,
    )


def assign_battery_static_api_mapping(
        grid: MultiCircuit,
        battery: Any,
        mdl: Block,
        logger: Logger | None,
) -> None:
    """
    Assign static Battery parameters exposed by ``mdl.api_obj_mapping``.

    :param grid: Static network model.
    :param battery: Battery device.
    :param mdl: EMT block.
    :param logger: Optional logger.
    :return: None.
    """
    device_name: str = str(battery.name)
    assign_generator_static_api_mapping(
        grid=grid,
        generator=battery,
        mdl=mdl,
        logger=logger,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.battery_enom_mwh,
        value=float(battery.Enom),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.battery_soc_0_pu,
        value=float(battery.soc_0),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.battery_max_soc_pu,
        value=float(battery.max_soc),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.battery_min_soc_pu,
        value=float(battery.min_soc),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.battery_charge_efficiency_pu,
        value=float(battery.charge_efficiency),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.battery_discharge_efficiency_pu,
        value=float(battery.discharge_efficiency),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.battery_charge_per_cycle_pu,
        value=float(battery.charge_per_cycle),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.battery_discharge_per_cycle_pu,
        value=float(battery.discharge_per_cycle),
        logger=logger,
        device_name=device_name,
    )


def assign_vsc_static_api_mapping(
        grid: MultiCircuit,
        vsc: Any,
        mdl: Block,
        logger: Logger | None,
) -> None:
    """
    Assign static VSC parameters exposed by ``mdl.api_obj_mapping``.

    PF-derived quantities such as converter initial active power or converter
    losses are intentionally not assigned here. They are initialization data, not
    static API-object data.

    :param grid: Static network model.
    :param vsc: VSC device.
    :param mdl: VSC EMT block.
    :param logger: Optional logger.
    :return: None.
    """
    device_name: str = str(vsc.name)
    omega_base: float = omega_base_from_grid(grid)

    assign_common_branch_static_api_mapping(
        device=vsc,
        mdl=mdl,
        logger=logger,
    )

    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.Sbase,
        value=float(grid.Sbase),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.omega_base,
        value=omega_base,
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.converter_control_mode_1,
        value=converter_control_code(vsc.control1),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.converter_control_mode_2,
        value=converter_control_code(vsc.control2),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.converter_control_target_1,
        value=float(vsc.control1_val),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.converter_control_target_2,
        value=float(vsc.control2_val),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.alpha1,
        value=float(vsc.alpha1),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.alpha2,
        value=float(vsc.alpha2),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.alpha3,
        value=float(vsc.alpha3),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.vsc_kdp_pu,
        value=float(vsc.control1_val_droop),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.vsc_min_ac_voltage_pu,
        value=float(vsc.min_ac_voltage),
        logger=logger,
        device_name=device_name,
    )


def assign_dc_line_static_api_mapping(
        dc_line: DcLine,
        mdl: Block,
        logger: Logger | None,
) -> None:
    """
    Assign static DC-line parameters exposed by ``mdl.api_obj_mapping``.

    :param dc_line: DC line device.
    :param mdl: DC line EMT block.
    :param logger: Optional logger.
    :return: None.
    """
    device_name: str = str(dc_line.name)
    eps_value: float = 1.0e-12
    resistance_value: float = float(dc_line.R_corrected)
    conductance_value: float = 1.0 / max(abs(resistance_value), eps_value)

    assign_common_branch_static_api_mapping(
        device=dc_line,
        mdl=mdl,
        logger=logger,
    )

    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.g,
        value=conductance_value,
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.b,
        value=0.0,
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.bsh,
        value=0.0,
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.dc_line_r_pu,
        value=resistance_value,
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.dc_line_length_km,
        value=float(dc_line.length),
        logger=logger,
        device_name=device_name,
    )


def assign_transformer2w_static_api_mapping(
        grid: MultiCircuit,
        transformer: Transformer2W,
        mdl: Block,
        logger: Logger | None,
) -> None:
    """
    Assign static Transformer2W parameters exposed by ``mdl.api_obj_mapping``.

    :param grid: Static network model.
    :param transformer: Two-winding transformer device.
    :param mdl: Transformer EMT block.
    :param logger: Optional logger.
    :return: None.
    """
    assign_common_branch_static_api_mapping(
        device=transformer,
        mdl=mdl,
        logger=logger,
    )
    device_name: str = str(transformer.name)
    eps_value: float = 1.0e-12
    omega_base: float = omega_base_from_grid(grid)
    sn_value: float = max(float(transformer.Sn), 1.0e-9)
    pcu_kw_value: float = max(float(transformer.Pcu), 0.0)
    pfe_kw_value: float = max(float(transformer.Pfe), 0.0)
    i0_pct_value: float = max(float(transformer.I0), 0.0)
    hv_nominal_kv: float
    lv_nominal_kv: float

    if transformer.HV is not None and float(transformer.HV) > eps_value:
        hv_nominal_kv = float(transformer.HV)
    else:
        hv_nominal_kv = float(transformer.bus_from.Vnom)

    if transformer.LV is not None and float(transformer.LV) > eps_value:
        lv_nominal_kv = float(transformer.LV)
    else:
        lv_nominal_kv = float(transformer.bus_to.Vnom)

    tap_module_value: float = float(transformer.tap_module)
    if abs(tap_module_value) <= eps_value:
        tap_module_value = 1.0
    else:
        pass

    tap_phase_value: float = float(transformer.tap_phase)

    if abs(lv_nominal_kv) > eps_value:
        nominal_voltage_ratio: float = hv_nominal_kv / lv_nominal_kv
    else:
        nominal_voltage_ratio = 1.0

    total_voltage_ratio: float = nominal_voltage_ratio * tap_module_value
    total_voltage_ratio_square: float = total_voltage_ratio * total_voltage_ratio
    transformer_r_pu: float = float(transformer.R)
    transformer_x_pu: float = float(transformer.X)
    transformer_g_pu: float = float(transformer.G)
    transformer_b_pu: float = float(transformer.B)

    if float(transformer.Vsc) > 0.0:
        vsc_pct_value: float = float(transformer.Vsc)
    else:
        vsc_pct_value = 100.0 * np.sqrt(
            max(
                transformer_r_pu * transformer_r_pu + transformer_x_pu * transformer_x_pu,
                0.0,
            )
        )

    if pcu_kw_value > 0.0 and sn_value > eps_value:
        short_circuit_resistance_pct: float = pcu_kw_value / (10.0 * sn_value)
    else:
        short_circuit_resistance_pct = 100.0 * transformer_r_pu

    from_connection_matrix: np.ndarray = xfmr_connection_matrix(transformer.conn_f)
    to_connection_matrix: np.ndarray = xfmr_connection_matrix(transformer.conn_t)
    permutation_matrix: np.ndarray = xfmr_phase_permutation_matrix(int(transformer.vector_group_number))
    to_effective_connection_matrix: np.ndarray = permutation_matrix @ to_connection_matrix

    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.omega_base,
        value=omega_base,
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.transformer_rated_power_mva,
        value=sn_value,
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.transformer_winding1_rated_voltage_ll_kv,
        value=hv_nominal_kv,
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.transformer_winding2_rated_voltage_ll_kv,
        value=lv_nominal_kv,
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.transformer_connection_clock,
        value=float(transformer.vector_group_number),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.transformer_open_circuit_current_pct,
        value=i0_pct_value,
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.transformer_open_circuit_loss_kw,
        value=pfe_kw_value,
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.transformer_short_circuit_voltage_pct,
        value=vsc_pct_value,
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.transformer_short_circuit_resistance_pct,
        value=short_circuit_resistance_pct,
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.transformer_short_circuit_loss_kw,
        value=pcu_kw_value,
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.transformer_tap_module,
        value=tap_module_value,
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.transformer_nominal_voltage_ratio,
        value=nominal_voltage_ratio,
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.transformer_total_voltage_ratio,
        value=total_voltage_ratio,
        logger=logger,
        device_name=device_name,
    )

    # ``transformer_tap_ratio`` is preserved as a legacy alias for the plain tap
    # module so that existing direct EMT templates keep their historical meaning.
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.transformer_tap_ratio,
        value=tap_module_value,
        logger=logger,
        device_name=device_name,
    )

    if transformer_equivalent_circuit_values_are_requested(mdl=mdl):
        if abs(tap_phase_value) > eps_value:
            add_static_mapping_warning(
                logger=logger,
                device_name=device_name,
                message="Transformer equivalent-circuit derived values skipped because tap_phase is non-zero.",
                value=str(tap_phase_value),
                expected_value="tap_phase close to zero",
                device_property="tap_phase",
            )
        else:
            r1_value: float
            r2_value: float
            l1_value: float
            l2_value: float
            mutual_inductance: float
            g_core: float
            determinant_value: float

            r1_value, r2_value, l1_value, l2_value, mutual_inductance, g_core = compute_transformer_equivalent_circuit_values(
                omega_base=omega_base,
                transformer_r_pu=transformer_r_pu,
                transformer_x_pu=transformer_x_pu,
                transformer_g_pu=transformer_g_pu,
                transformer_b_pu=transformer_b_pu,
                total_voltage_ratio=total_voltage_ratio,
                total_voltage_ratio_square=total_voltage_ratio_square,
                eps_value=eps_value,
            )
            determinant_value = l1_value * l2_value - mutual_inductance * mutual_inductance

            if determinant_value <= eps_value:
                add_static_mapping_warning(
                    logger=logger,
                    device_name=device_name,
                    message="Transformer equivalent-circuit derived inductance values skipped because the inductance matrix is non-physical.",
                    value=str(determinant_value),
                    expected_value="positive inductance matrix determinant",
                    device_property="transformer_equivalent_circuit",
                )
            else:
                assign_api_mapping_value_if_present(
                    mdl=mdl,
                    key=ParamPowerFlowRefferenceType.transformer_winding1_resistance_pu,
                    value=r1_value,
                    logger=logger,
                    device_name=device_name,
                )
                assign_api_mapping_value_if_present(
                    mdl=mdl,
                    key=ParamPowerFlowRefferenceType.transformer_winding2_resistance_pu,
                    value=r2_value,
                    logger=logger,
                    device_name=device_name,
                )
                assign_api_mapping_value_if_present(
                    mdl=mdl,
                    key=ParamPowerFlowRefferenceType.transformer_winding1_inductance_pu_s,
                    value=l1_value,
                    logger=logger,
                    device_name=device_name,
                )
                assign_api_mapping_value_if_present(
                    mdl=mdl,
                    key=ParamPowerFlowRefferenceType.transformer_winding2_inductance_pu_s,
                    value=l2_value,
                    logger=logger,
                    device_name=device_name,
                )
                assign_api_mapping_value_if_present(
                    mdl=mdl,
                    key=ParamPowerFlowRefferenceType.transformer_mutual_inductance_pu_s,
                    value=mutual_inductance,
                    logger=logger,
                    device_name=device_name,
                )
                assign_api_mapping_value_if_present(
                    mdl=mdl,
                    key=ParamPowerFlowRefferenceType.transformer_magnetizing_conductance_pu,
                    value=g_core,
                    logger=logger,
                    device_name=device_name,
                )
    else:
        pass

    assign_3x3_static_matrix(
        mdl=mdl,
        matrix=from_connection_matrix,
        keys=get_transformer_from_connection_keys(),
        logger=logger,
        device_name=device_name,
    )
    assign_3x3_static_matrix(
        mdl=mdl,
        matrix=to_effective_connection_matrix,
        keys=get_transformer_to_connection_keys(),
        logger=logger,
        device_name=device_name,
    )


def assign_line_static_api_mapping(
        grid: MultiCircuit,
        line: Any,
        mdl: Block,
        logger: Logger | None,
) -> None:
    """
    Assign static line R, Linv and C parameters exposed by ``api_obj_mapping``.

    The physical reduced matrix is projected into the fixed 4x4 NABC API-object
    contract. Exposed inactive-phase entries are explicitly zeroed, preserving the
    previous template semantics while allowing partial key subsets.

    :param grid: Static network model.
    :param line: Line-like branch device.
    :param mdl: Line EMT block.
    :param logger: Optional logger.
    :return: None.
    """
    # todo: make sure it also works for rms
    device_name: str = str(line.name)
    assign_common_branch_static_api_mapping(
        device=line,
        mdl=mdl,
        logger=logger,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.line_length_km,
        value=float(line.length),
        logger=logger,
        device_name=device_name,
    )

    active_indices: List[int] = get_line_active_global_indices(line)
    n_active: int = len(active_indices)

    if n_active == 0:
        add_static_mapping_warning(
            logger=logger,
            device_name=device_name,
            message="Line static mapping skipped because no physical phases are active.",
            value="0 active phases",
            expected_value="at least one active phase",
            device_property="line_phases",
        )
    else:
        r_full: np.ndarray
        l_full: np.ndarray
        c_full: np.ndarray
        r_full, l_full, c_full = build_line_static_matrices(
            grid=grid,
            line=line,
        )

        matrices_are_valid: bool = validate_line_static_matrices(
            line=line,
            r_full=r_full,
            l_full=l_full,
            c_full=c_full,
            n_active=n_active,
            logger=logger,
        )

        if matrices_are_valid:
            linv_full: np.ndarray

            try:
                # The physically meaningful criterion is invertibility, not the
                # absolute determinant magnitude. Small but diagonal inductance
                # matrices are valid after per-unit scaling and should not be
                # rejected only because their determinant is numerically tiny.
                linv_full = np.linalg.inv(l_full)
            except np.linalg.LinAlgError:
                determinant_value: float = float(np.linalg.det(l_full))
                add_static_mapping_warning(
                    logger=logger,
                    device_name=device_name,
                    message="Line static mapping skipped because inductance matrix is singular.",
                    value=str(determinant_value),
                    expected_value="invertible inductance matrix",
                    device_property="line_inductance_matrix",
                )
            else:
                r_keys: List[List[ParamPowerFlowRefferenceType]] = get_line_r_keys()
                linv_keys: List[List[ParamPowerFlowRefferenceType]] = get_line_linv_keys()
                c_keys: List[List[ParamPowerFlowRefferenceType]] = get_line_c_keys()

                # First zero every exposed slot of the fixed NABC map. This is
                # important for templates that expose inactive neutral/phase keys.
                global_row: int = 0
                while global_row < 4:
                    global_col: int = 0

                    while global_col < 4:
                        assign_api_mapping_value_if_present(
                            mdl=mdl,
                            key=r_keys[global_row][global_col],
                            value=0.0,
                            logger=logger,
                            device_name=device_name,
                        )
                        assign_api_mapping_value_if_present(
                            mdl=mdl,
                            key=linv_keys[global_row][global_col],
                            value=0.0,
                            logger=logger,
                            device_name=device_name,
                        )
                        assign_api_mapping_value_if_present(
                            mdl=mdl,
                            key=c_keys[global_row][global_col],
                            value=0.0,
                            logger=logger,
                            device_name=device_name,
                        )
                        global_col += 1

                    global_row += 1

                # Then project reduced active-phase values into the fixed NABC
                # contract. Only keys requested by the EMT model are written.
                reduced_row: int = 0
                while reduced_row < n_active:
                    mapped_global_row: int = active_indices[reduced_row]
                    reduced_col: int = 0

                    while reduced_col < n_active:
                        mapped_global_col: int = active_indices[reduced_col]

                        assign_api_mapping_value_if_present(
                            mdl=mdl,
                            key=r_keys[mapped_global_row][mapped_global_col],
                            value=float(r_full[reduced_row, reduced_col]),
                            logger=logger,
                            device_name=device_name,
                        )
                        assign_api_mapping_value_if_present(
                            mdl=mdl,
                            key=linv_keys[mapped_global_row][mapped_global_col],
                            value=float(linv_full[reduced_row, reduced_col]),
                            logger=logger,
                            device_name=device_name,
                        )
                        assign_api_mapping_value_if_present(
                            mdl=mdl,
                            key=c_keys[mapped_global_row][mapped_global_col],
                            value=float(c_full[reduced_row, reduced_col]),
                            logger=logger,
                            device_name=device_name,
                        )
                        reduced_col += 1

                    reduced_row += 1
        else:
            pass





def assign_hvdc_line_static_api_mapping(
        hvdc_line: Any,
        mdl: Block,
        logger: Logger | None,
) -> None:
    """
    Intentionally leave HVDC-line static mapping as a no-op.

    Reachability exists in the EMT builder, but there is no established EMT
    template/static-key contract for ``HvdcLine`` yet.

    :param hvdc_line: HVDC-line device.
    :param mdl: EMT block.
    :param logger: Optional logger.
    :return: None.
    """
    if logger is None:
        pass
    else:
        pass


def assign_series_reactance_static_api_mapping(
        series_reactance: Any,
        mdl: Block,
        logger: Logger | None,
) -> None:
    """
    Intentionally leave series-reactance static mapping as a no-op.

    Reachability exists in the EMT builder, but there is no established EMT
    template/static-key contract for ``SeriesReactance`` yet.

    :param series_reactance: Series-reactance device.
    :param mdl: EMT block.
    :param logger: Optional logger.
    :return: None.
    """
    if logger is None:
        pass
    else:
        pass


def assign_switch_static_api_mapping(
        switch: Any,
        mdl: Block,
        logger: Logger | None,
) -> None:
    """
    Intentionally leave switch static mapping as a no-op.

    Reachability exists in the EMT builder, but there is no established EMT
    template/static-key contract for ``Switch`` yet.

    :param switch: Switch device.
    :param mdl: EMT block.
    :param logger: Optional logger.
    :return: None.
    """
    if logger is None:
        pass
    else:
        pass


def assign_upfc_static_api_mapping(
        upfc: Any,
        mdl: Block,
        logger: Logger | None,
) -> None:
    """
    Intentionally leave UPFC static mapping as a no-op.

    Reachability exists in the EMT builder, but there is no established EMT
    template/static-key contract for ``Upfc`` yet.

    :param upfc: UPFC device.
    :param mdl: EMT block.
    :param logger: Optional logger.
    :return: None.
    """
    if logger is None:
        pass
    else:
        pass
