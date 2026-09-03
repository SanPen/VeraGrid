from __future__ import annotations

from typing import Dict

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.rms_meter_templates import RMS_CURRENT_METER_OUTPUT_NAMES
from VeraGridEngine.Templates.Rms.rms_meter_templates import RMS_PLL_METER_OUTPUT_NAMES
from VeraGridEngine.Templates.Rms.rms_meter_templates import RMS_POWER_METER_OUTPUT_NAMES
from VeraGridEngine.Templates.Rms.rms_meter_templates import RMS_VOLTAGE_METER_OUTPUT_NAMES
from VeraGridEngine.Templates.Rms.rms_meter_templates import build_rms_current_meter_outputs_from_pq
from VeraGridEngine.Templates.Rms.rms_meter_templates import build_rms_pll_meter_outputs
from VeraGridEngine.Templates.Rms.rms_meter_templates import build_rms_power_meter_outputs_from_pq
from VeraGridEngine.Templates.Rms.rms_meter_templates import build_signal_meter_block
from VeraGridEngine.Templates.Rms.rms_meter_templates import build_rms_station_meter_bundle
from VeraGridEngine.Templates.Rms.rms_meter_templates import build_rms_voltage_meter_outputs_from_dc
from VeraGridEngine.Templates.Rms.rms_meter_templates import build_rms_voltage_meter_outputs_from_polar
from VeraGridEngine.Templates.Rms.rms_meter_templates import connect_meter_signal_outputs_to_block_inputs
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Expr, Var


RMS_STAVMEA_OUTPUT_NAMES: tuple[str, ...] = RMS_VOLTAGE_METER_OUTPUT_NAMES
RMS_STAPQMEA_OUTPUT_NAMES: tuple[str, ...] = RMS_POWER_METER_OUTPUT_NAMES
RMS_STAIMEA_OUTPUT_NAMES: tuple[str, ...] = RMS_CURRENT_METER_OUTPUT_NAMES
RMS_ELMPHI_PLL_OUTPUT_NAMES: tuple[str, ...] = RMS_PLL_METER_OUTPUT_NAMES


def build_powerfactory_rms_stavmea_outputs_from_polar(vm: Expr,
                                                      va: Expr,
                                                      measured_frequency_hz: Expr,
                                                      nominal_frequency_hz: Expr) -> Dict[str, Expr]:
    """
    Compatibility wrapper mapping the DGS importer voltage-meter request to VeraGrid RMS meters.

    :param vm: Voltage magnitude.
    :param va: Voltage angle in radians.
    :param measured_frequency_hz: Measured frequency in Hz.
    :param nominal_frequency_hz: Nominal frequency in Hz.
    :return: Signal-name to expression mapping.
    """
    return build_rms_voltage_meter_outputs_from_polar(vm, va, measured_frequency_hz, nominal_frequency_hz)


def build_powerfactory_rms_stavmea_outputs_from_dc(vdc: Expr,
                                                   nominal_frequency_hz: Expr) -> Dict[str, Expr]:
    """
    Compatibility wrapper mapping the DGS importer DC-voltage-meter request to VeraGrid RMS meters.

    :param vdc: DC voltage magnitude.
    :param nominal_frequency_hz: Nominal frequency in Hz.
    :return: Signal-name to expression mapping.
    """
    return build_rms_voltage_meter_outputs_from_dc(vdc, nominal_frequency_hz)


def build_powerfactory_rms_staimea_outputs_from_pq(vm: Expr,
                                                   va: Expr,
                                                   p: Expr,
                                                   q: Expr) -> Dict[str, Expr]:
    """
    Compatibility wrapper mapping the DGS importer current-meter request to VeraGrid RMS meters.

    :param vm: Voltage magnitude.
    :param va: Voltage angle in radians.
    :param p: Active power.
    :param q: Reactive power.
    :return: Signal-name to expression mapping.
    """
    return build_rms_current_meter_outputs_from_pq(vm, va, p, q)


def build_powerfactory_rms_stapqmea_outputs_from_pq(p: Expr, q: Expr) -> Dict[str, Expr]:
    """
    Compatibility wrapper mapping the DGS importer power-meter request to VeraGrid RMS meters.

    :param p: Active power.
    :param q: Reactive power.
    :return: Signal-name to expression mapping.
    """
    return build_rms_power_meter_outputs_from_pq(p, q)


def build_powerfactory_rms_elmphi_pll_outputs(va: Expr,
                                              measured_frequency_hz: Expr,
                                              nominal_frequency_hz: Expr) -> Dict[str, Expr]:
    """
    Compatibility wrapper mapping the DGS importer PLL request to VeraGrid RMS meters.

    :param va: Local phase angle in radians.
    :param measured_frequency_hz: Measured frequency in Hz.
    :param nominal_frequency_hz: Nominal frequency in Hz.
    :return: Signal-name to expression mapping.
    """
    return build_rms_pll_meter_outputs(va, measured_frequency_hz, nominal_frequency_hz)


def build_powerfactory_measurement_signal_block(vf: VarFactory,
                                                signal_expressions: Dict[str, Expr],
                                                name: str) -> tuple[Block, Dict[str, Var]]:
    """
    Compatibility wrapper mapping one named-signal meter block to VeraGrid RMS meter templates.

    :param vf: Shared variable factory.
    :param signal_expressions: Signal-name to expression mapping.
    :param name: Block name suffix.
    :return: Pair ``(block, output_var_by_signal_name)``.
    """
    return build_signal_meter_block(vf, signal_expressions, name)


def connect_powerfactory_signal_outputs_to_block_inputs(block: Block,
                                                        signal_output_by_name: Dict[str, Var],
                                                        var_factory: VarFactory) -> None:
    """
    Compatibility wrapper connecting imported DGS signal names to VeraGrid RMS meter outputs.

    :param block: Target block receiving the signals.
    :param signal_output_by_name: Signal-name to source-variable mapping.
    :param var_factory: Shared variable factory.
    :return: None.
    """
    connect_meter_signal_outputs_to_block_inputs(block, signal_output_by_name, var_factory)


def build_powerfactory_rms_station_measurement_bundle(vf: VarFactory,
                                                      label: str,
                                                      dc_plus_v: Expr,
                                                      dc_minus_v: Expr,
                                                      dc_current: Expr,
                                                      nominal_frequency_hz: Expr,
                                                      local_vm: Expr,
                                                      local_va: Expr,
                                                      local_p: Expr,
                                                      local_q: Expr,
                                                      poc1_vm: Expr,
                                                      poc1_va: Expr,
                                                      poc1_p: Expr,
                                                      poc1_q: Expr,
                                                      poc2_vm: Expr,
                                                      poc2_va: Expr,
                                                      poc2_p: Expr,
                                                      poc2_q: Expr,
                                                      ucap: Expr | None = None,
                                                      measured_frequency_hz: Expr | None = None) -> tuple[list[Block], Dict[str, Var]]:
    """
    Compatibility wrapper mapping the DGS importer station bundle request to VeraGrid RMS meters.

    :param vf: Shared variable factory.
    :param label: Stable suffix appended to generated block names.
    :param dc_plus_v: Positive DC terminal voltage.
    :param dc_minus_v: Negative DC terminal voltage.
    :param dc_current: DC current seen by the control.
    :param nominal_frequency_hz: Nominal frequency in Hz.
    :param local_vm: Local AC voltage magnitude.
    :param local_va: Local AC voltage angle.
    :param local_p: Local active power.
    :param local_q: Local reactive power.
    :param poc1_vm: PoC1 voltage magnitude.
    :param poc1_va: PoC1 voltage angle.
    :param poc1_p: PoC1 active power.
    :param poc1_q: PoC1 reactive power.
    :param poc2_vm: PoC2 voltage magnitude.
    :param poc2_va: PoC2 voltage angle.
    :param poc2_p: PoC2 active power.
    :param poc2_q: PoC2 reactive power.
    :param ucap: Optional capacitor-voltage proxy.
    :param measured_frequency_hz: Optional measured frequency override.
    :return: Pair ``(measurement_blocks, signal_output_by_name)``.
    """
    return build_rms_station_meter_bundle(
        vf=vf,
        label=label,
        dc_plus_v=dc_plus_v,
        dc_minus_v=dc_minus_v,
        dc_current=dc_current,
        nominal_frequency_hz=nominal_frequency_hz,
        local_vm=local_vm,
        local_va=local_va,
        local_p=local_p,
        local_q=local_q,
        poc1_vm=poc1_vm,
        poc1_va=poc1_va,
        poc1_p=poc1_p,
        poc1_q=poc1_q,
        poc2_vm=poc2_vm,
        poc2_va=poc2_va,
        poc2_p=poc2_p,
        poc2_q=poc2_q,
        ucap=ucap,
        measured_frequency_hz=measured_frequency_hz,
    )
