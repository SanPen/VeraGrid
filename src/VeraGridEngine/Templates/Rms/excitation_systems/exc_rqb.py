# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed template for the canonical CGMES ExcRQB model."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcRQBParameters:
    """Canonical ExcRQB scalar parameters."""

    __slots__ = (
        'ki0', 'ki1', 'te', 'tc', 'klir', 'ucmin', 'ucmax', 'lus', 'klus',
        'mesu', 't4m', 'lsat', 'tf',
    )

    def __init__(
            self,
            ki0: float = 12.7,
            ki1: float = -16.8,
            te: float = 0.22,
            tc: float = 0.02,
            klir: float = 12.13,
            ucmin: float = 0.9,
            ucmax: float = 1.1,
            lus: float = 0.12,
            klus: float = 50.0,
            mesu: float = 0.02,
            t4m: float = 5.0,
            lsat: float = 5.73,
            tf: float = 0.01,
    ) -> None:
        """Store the IEC typical values without changing RDF field names.

        :param ki0: Voltage-reference channel gain.
        :param ki1: Voltage channel gain.
        :param te: Lead-lag numerator time constant in seconds.
        :param tc: Lead-lag denominator time constant in seconds.
        :param klir: OEL channel gain.
        :param ucmin: Lower voltage-reference limit.
        :param ucmax: Upper voltage-reference limit.
        :param lus: Voltage-dependent limiter setpoint.
        :param klus: Voltage-dependent limiter gain.
        :param mesu: Voltage measurement time constant in seconds.
        :param t4m: Input filter and regulator integration time in seconds.
        :param lsat: Symmetric regulator-integrator state limit.
        :param tf: Exciter output time constant in seconds.
        """
        self.ki0: float = ki0
        self.ki1: float = ki1
        self.te: float = te
        self.tc: float = tc
        self.klir: float = klir
        self.ucmin: float = ucmin
        self.ucmax: float = ucmax
        self.lus: float = lus
        self.klus: float = klus
        self.mesu: float = mesu
        self.t4m: float = t4m
        self.lsat: float = lsat
        self.tf: float = tf


def build_exc_r_q_b_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcRQBParameters | None = None,
) -> RmsModelTemplate:
    """Build the IEC 61970-302 ExcRQB regulator and exciter graph.

    :param vfactory: Factory allocating equation and parameter symbols.
    :param name: Optional unique runtime model name.
    :param parameters: Imported canonical CGMES values.
    :return: Exciter with sensed-voltage, reference, PSS and OEL ports.
    :raises ValueError: Invalid limits or non-realizable time constants.
    """
    settings: ExcRQBParameters = ExcRQBParameters() if parameters is None else parameters
    values: tuple[float, ...] = (
        settings.ki0, settings.ki1, settings.te, settings.tc, settings.klir,
        settings.ucmin, settings.ucmax, settings.lus, settings.klus, settings.mesu,
        settings.t4m, settings.lsat, settings.tf,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('CGMES ExcRQB parameters must be finite')
    elif min(settings.te, settings.tc, settings.mesu, settings.tf) < 0.0:
        raise ValueError('CGMES ExcRQB time constants must be nonnegative')
    elif settings.t4m <= 0.0:
        raise ValueError('CGMES ExcRQB T4M must be positive for its regulator integrator')
    elif settings.ucmin >= settings.ucmax:
        raise ValueError('CGMES ExcRQB UCMIN must be below UCMAX')
    elif settings.lus < 0.0 or settings.klus < 0.0 or settings.lsat < 0.0:
        raise ValueError('CGMES ExcRQB LUS, KLUS, and LSAT must be nonnegative')
    elif settings.tc == 0.0 and settings.te != 0.0:
        raise ValueError('CGMES ExcRQB TC must be positive when TE is nonzero')
    else:
        pass

    template_name: str = 'ExcRQB' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    sensed_voltage: Var = model.input('UsPu', Const(1.0))
    voltage_reference: Var = model.input('UsRefPu', Const(1.0))
    stabilizer_signal: Var = model.input('VsPu', Const(0.0))
    overexcitation_signal: Var = model.input('OelPu', Const(0.0))

    # MESU measures the compensated terminal voltage before the complementary T4M channels.
    measurement: Var = model.lag(
        'MeasuredVoltagePu', sensed_voltage,
        model.parameter('ExcRQB.mesu', settings.mesu), settings.mesu, sensed_voltage,
    )
    input_time: Var = model.parameter('ExcRQB.t4m', settings.t4m)
    voltage_lowpass: Var = model.lag(
        'VoltageLowpassPu', measurement, input_time, settings.t4m, measurement,
    )
    voltage_highpass: Var = model.algebraic(
        'VoltageHighpassPu', measurement - voltage_lowpass,
        measurement - voltage_lowpass,
    )

    # UCMIN/UCMAX bound Vref; Ki0 receives Vref minus the filtered Vc channel.
    reference_minimum: Var = model.parameter('ExcRQB.ucmin', settings.ucmin)
    reference_maximum: Var = model.parameter('ExcRQB.ucmax', settings.ucmax)
    bounded_reference: Var = model.algebraic(
        'BoundedVoltageReferencePu',
        sym.hard_sat(voltage_reference, reference_minimum, reference_maximum),
        sym.hard_sat(voltage_reference, reference_minimum, reference_maximum),
    )
    reference_error: Var = model.algebraic(
        'VoltageReferenceErrorPu', bounded_reference - voltage_lowpass,
        bounded_reference - voltage_lowpass,
    )
    voltage_reference_gain: Var = model.parameter('ExcRQB.ki0', settings.ki0)
    reference_channel: Var = model.algebraic(
        'VoltageReferenceChannelPu',
        voltage_reference_gain * reference_error,
        voltage_reference_gain * reference_error,
    )
    voltage_gain: Var = model.parameter('ExcRQB.ki1', settings.ki1)
    voltage_channel: Var = model.algebraic(
        'VoltageChannelPu', voltage_gain * voltage_highpass,
        voltage_gain * voltage_highpass,
    )

    # The two KLUS loops form the voltage-dependent upper and lower regulator limits.
    limiter_setpoint: Var = model.parameter('ExcRQB.lus', settings.lus)
    limiter_gain: Var = model.parameter('ExcRQB.klus', settings.klus)
    upper_regulator_limit: Var = model.algebraic(
        'UpperRegulatorLimitPu',
        limiter_gain * (Const(1.0) + limiter_setpoint - sensed_voltage),
        limiter_gain * (Const(1.0) + limiter_setpoint - sensed_voltage),
    )
    lower_regulator_limit: Var = model.algebraic(
        'LowerRegulatorLimitPu',
        limiter_gain * (Const(1.0) - limiter_setpoint - sensed_voltage),
        limiter_gain * (Const(1.0) - limiter_setpoint - sensed_voltage),
    )
    regulator_equation: Expr = reference_channel + voltage_channel + stabilizer_signal
    regulator_initial: Expr = reference_channel + voltage_channel + stabilizer_signal
    regulator_sum: Var = model.algebraic(
        'RegulatorInputPu', regulator_equation, regulator_initial,
    )
    voltage_limit_initial: Var = sym.hard_sat(
        regulator_sum, lower_regulator_limit, upper_regulator_limit,
    )
    voltage_dependent_limit: Var = model.algebraic(
        'VoltageDependentLimitedPu',
        sym.hard_sat(regulator_sum, lower_regulator_limit, upper_regulator_limit),
        voltage_limit_initial,
    )
    fixed_limit_initial: Var = sym.hard_sat(
        voltage_dependent_limit, Const(-4.0), Const(4.0),
    )
    fixed_limit: Var = model.algebraic(
        'FixedRegulatorLimitedPu',
        sym.hard_sat(voltage_dependent_limit, Const(-4.0), Const(4.0)),
        fixed_limit_initial,
    )
    compensated_regulator: Var = model.lead_lag(
        'LeadLagRegulatorPu', fixed_limit,
        model.parameter('ExcRQB.te', settings.te),
        model.parameter('ExcRQB.tc', settings.tc),
        settings.te, settings.tc, Const(0.0),
    )

    # OEL acts with negative KLIR gain before the LSAT-bounded T4M integrator.
    overexcitation_gain: Var = model.parameter('ExcRQB.klir', settings.klir)
    integrator_demand: Var = compensated_regulator - overexcitation_gain * overexcitation_signal
    integrator_input: Var = model.algebraic(
        'RegulatorIntegratorInputPu', integrator_demand, integrator_demand,
    )
    integral_state: Var = vfactory.add_var(f'RegulatorIntegralPu_{template_name}')
    integral_limit: Var = model.parameter('ExcRQB.lsat', settings.lsat)
    field_initial: Const = Const(1.0)
    integral_initial: Var = field_initial + integrator_input
    model.differential(
        integral_state,
        integrator_input / input_time,
        integral_initial,
        -integral_limit,
        integral_limit,
    )
    integrator_output: Var = model.algebraic(
        'RegulatorIntegralOutputPu', integral_state - integrator_input, field_initial,
    )
    field_voltage: Var = model.lag(
        'EfdPu', integrator_output,
        model.parameter('ExcRQB.tf', settings.tf), settings.tf, field_initial,
    )

    template: RmsModelTemplate = model.finish((field_voltage,), 'CGMES ExcRQB excitation system')
    template.comment = (
        'CGMES ExcRQB IEC 61970-302:2023-06 Figure 120: voltage measurement, '
        'complementary T4M channels, voltage-dependent limits, OEL summation, '
        'bounded integration and final exciter lag.'
    )
    enabled: Var = vfactory.add_var(f'ExcRQB.enabled_{template_name}')
    template.block.event_dict[enabled] = vfactory.add_const(value=None)
    return template
