# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcANS amplifier and exciter model."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcANSParameters:
    """Numeric and integer selectors declared by the CGMES ExcANS class."""

    __slots__ = (
        'k3', 'k2', 'kce', 't3', 't2', 't1', 'blint', 'kvfif', 'ifmn', 'ifmx',
        'vrmn', 'vrmx', 'krvecc', 'tb',
    )

    def __init__(
            self,
            k3: float = 1000.0,
            k2: float = 20.0,
            kce: float = 1.0,
            t3: float = 1.6,
            t2: float = 0.05,
            t1: float = 20.0,
            blint: int = 0,
            kvfif: int = 0,
            ifmn: float = -5.2,
            ifmx: float = 6.5,
            vrmn: float = -5.2,
            vrmx: float = 6.5,
            krvecc: int = 1,
            tb: float = 0.04,
    ) -> None:
        """Store canonical ExcANS values and EA typical defaults.

        :param k3: AVR gain.
        :param k2: Exciter gain.
        :param kce: Ceiling factor.
        :param t3: Lead or proportional time constant.
        :param t2: Exciter control time constant.
        :param t1: Regulator lag time constant.
        :param blint: Zero selects lead-lag; one selects proportional-integral.
        :param kvfif: Zero selects exciter-voltage rate feedback; one selects field-current feedback.
        :param ifmn: Lower field-current limit for the AVR characteristic.
        :param ifmx: Upper field-current limit for the AVR characteristic.
        :param vrmn: Lower AVR output bound.
        :param vrmx: Upper AVR output bound.
        :param krvecc: Select closed-loop exciter feedback when nonzero.
        :param tb: Exciter output-filter time constant.
        """
        self.k3: float = k3
        self.k2: float = k2
        self.kce: float = kce
        self.t3: float = t3
        self.t2: float = t2
        self.t1: float = t1
        self.blint: int = blint
        self.kvfif: int = kvfif
        self.ifmn: float = ifmn
        self.ifmx: float = ifmx
        self.vrmn: float = vrmn
        self.vrmx: float = vrmx
        self.krvecc: int = krvecc
        self.tb: float = tb


def build_exc_a_n_s_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcANSParameters | None = None,
) -> RmsModelTemplate:
    """Build ExcANS regulator, exciter, rate feedback, and ceiling equations.

    :param vfactory: Factory that owns the symbolic graph.
    :param name: Optional runtime instance name.
    :param parameters: Parsed CGMES ExcANS settings.
    :return: Equation-backed model with voltage, field-current, speed, and Efd ports.
    :raises ValueError: Invalid selector, time, or limit settings.
    """
    settings: ExcANSParameters = ExcANSParameters() if parameters is None else parameters
    template_name: str = 'ExcANS' if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.k3, settings.k2, settings.kce, settings.t3, settings.t2,
        settings.t1, settings.ifmn, settings.ifmx, settings.vrmn, settings.vrmx, settings.tb,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcANS parameters must be finite')
    elif min(settings.t1, settings.t2, settings.t3, settings.tb) < 0.0:
        raise ValueError('ExcANS times must be nonnegative')
    elif settings.t2 <= 0.0 or settings.tb <= 0.0:
        raise ValueError('ExcANS T2 and TB must be positive')
    elif settings.blint not in (0, 1) or settings.kvfif not in (0, 1) or settings.krvecc not in (0, 1):
        raise ValueError('ExcANS BLINT, KVFIF, and KRVECC selectors must be zero or one')
    elif settings.ifmn >= settings.ifmx or settings.vrmn >= settings.vrmx:
        raise ValueError('ExcANS current and voltage bounds must be ordered')
    elif settings.blint == 0 and settings.t1 == 0.0 and settings.t3 != 0.0:
        raise ValueError('ExcANS lead-lag branch requires zero T3 when T1 is zero')
    else:
        pass

    builder: ControlRealization = ControlRealization(vfactory, template_name)
    k3: Var = builder.parameter('K3', settings.k3)
    k2: Var = builder.parameter('K2', settings.k2)
    kce: Var = builder.parameter('KCE', settings.kce)
    t3: Var = builder.parameter('T3', settings.t3)
    t2: Var = builder.parameter('T2', settings.t2)
    t1: Var = builder.parameter('T1', settings.t1)
    ifmn: Var = builder.parameter('IFMN', settings.ifmn)
    ifmx: Var = builder.parameter('IFMX', settings.ifmx)
    vrmn: Var = builder.parameter('VRMN', settings.vrmn)
    vrmx: Var = builder.parameter('VRMX', settings.vrmx)
    tb: Var = builder.parameter('TB', settings.tb)
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    stabilizer: Var = builder.input('UpssPu', Const(0.0))
    field_current: Var = builder.input('IfdPu', Const(0.0))

    voltage_error: Expr = reference - terminal_voltage + stabilizer
    avr_input: Var = builder.algebraic('AvrInputPu', k3 * voltage_error, Const(0.0))
    if settings.blint == 1:
        regulator_integral: Var = vfactory.add_var(f'RegulatorIntegralPu_{template_name}')
        regulator_integral_derivative: Expr = avr_input
        regulator_output_unlimited: Expr = regulator_integral + t3 * avr_input
        builder.differential(regulator_integral, regulator_integral_derivative, Const(0.0))
    else:
        lead_lag_output: Var = builder.lead_lag(
            'RegulatorLeadLagPu', avr_input, t3, t1, settings.t3, settings.t1, Const(0.0),
        )
        regulator_output_unlimited = lead_lag_output
    regulator_output: Var = builder.algebraic(
        'RegulatorOutputPu', sym.hard_sat(regulator_output_unlimited, vrmn, vrmx), Const(0.0),
    )
    field_voltage: Var = vfactory.add_var(f'EfdPu_{template_name}')
    limited_field_current: Expr = sym.hard_sat(field_current, ifmn, ifmx)
    current_feedback: Expr = Const(float(settings.kvfif)) * limited_field_current
    voltage_feedback: Expr = Const(1.0 - float(settings.kvfif)) * field_voltage
    feedback: Expr = voltage_feedback + current_feedback
    exciter_error: Expr = regulator_output
    if settings.krvecc == 1:
        exciter_error = regulator_output - feedback
    else:
        pass
    exciter_integral: Var = vfactory.add_var(f'ExciterIntegralPu_{template_name}')
    exciter_integral_derivative: Expr = k2 * exciter_error
    builder.differential(exciter_integral, exciter_integral_derivative, Const(1.0))
    exciter_voltage: Var = builder.algebraic(
        'ExciterVoltagePu', exciter_integral + t2 * exciter_integral_derivative, Const(1.0),
    )
    rate_memory: Var = builder.lag(
        'FieldVoltageMemoryPu', (Const(1.0) - Const(float(settings.kvfif))) * exciter_voltage,
        tb, settings.tb, Const(1.0), vrmn, vrmx,
    )
    ceiling_branch: Expr = sym.hard_sat(kce * current_feedback, vrmn, vrmx)
    field_voltage_output: Expr = rate_memory + ceiling_branch
    builder.block.algebraic_vars.append(field_voltage)
    builder.block.algebraic_eqs.append(field_voltage - field_voltage_output)
    builder.block.init_eqs[field_voltage] = Const(1.0)
    return builder.finish((field_voltage,), 'CGMES ExcANS excitation system')
