# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES IEEE UEL1 circular-characteristic limiter."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class UnderexcLimIEEE1Parameters:
    """Canonical IEEE UEL1 RDF parameters."""

    __slots__ = (
        'kur', 'kuc', 'kuf', 'vurmax', 'vucmax', 'kui', 'kul', 'vuimax',
        'vuimin', 'tu1', 'tu2', 'tu3', 'tu4', 'vulmax', 'vulmin',
    )

    def __init__(self, kur: float = 1.95, kuc: float = 1.38, kuf: float = 0.0,
                 vurmax: float = 5.8, vucmax: float = 5.8, kui: float = 0.0,
                 kul: float = 100.0, vuimax: float = 18.0, vuimin: float = -18.0,
                 tu1: float = 0.0, tu2: float = 0.05, tu3: float = 0.0,
                 tu4: float = 0.0, vulmax: float = 18.0, vulmin: float = -18.0) -> None:
        """Store the complete IEEE UEL1 parameter surface.

        :param kur: Circular limiting-characteristic radius gain.
        :param kuc: Circular limiting-characteristic center gain.
        :param kuf: Stabilizing input gain.
        :param vurmax: Maximum radius-phasor magnitude.
        :param vucmax: Maximum center/operating-point phasor magnitude.
        :param kui: Integral gain.
        :param kul: Proportional gain.
        :param vuimax: PI output upper limit.
        :param vuimin: PI output lower limit.
        :param tu1: First lead time constant.
        :param tu2: First lag time constant.
        :param tu3: Second lead time constant.
        :param tu4: Second lag time constant.
        :param vulmax: Final UEL output upper limit.
        :param vulmin: Final UEL output lower limit.
        """
        self.kur: float = kur
        self.kuc: float = kuc
        self.kuf: float = kuf
        self.vurmax: float = vurmax
        self.vucmax: float = vucmax
        self.kui: float = kui
        self.kul: float = kul
        self.vuimax: float = vuimax
        self.vuimin: float = vuimin
        self.tu1: float = tu1
        self.tu2: float = tu2
        self.tu3: float = tu3
        self.tu4: float = tu4
        self.vulmax: float = vulmax
        self.vulmin: float = vulmin


def build_underexc_lim_i_e_e_e1_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: UnderexcLimIEEE1Parameters | None = None,
) -> RmsModelTemplate:
    """Build the IEEE UEL1 phasor, bounded-PI and lead-lag graph.

    :param vfactory: Factory allocating graph variables.
    :param name: Optional runtime model name.
    :param parameters: Canonical UnderexcLimIEEE1 settings.
    :return: Limiter with terminal phasor and stabilizing-signal inputs.
    :raises ValueError: Parameters are nonfinite, limits are unordered, or a stage is improper.
    """
    settings: UnderexcLimIEEE1Parameters = (
        UnderexcLimIEEE1Parameters() if parameters is None else parameters
    )
    numeric_values: tuple[float, ...] = (
        settings.kur, settings.kuc, settings.kuf, settings.vurmax, settings.vucmax,
        settings.kui, settings.kul, settings.vuimax, settings.vuimin,
        settings.tu1, settings.tu2, settings.tu3, settings.tu4,
        settings.vulmax, settings.vulmin,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('UnderexcLimIEEE1 parameters must be finite')
    elif min(settings.vurmax, settings.vucmax, settings.tu1, settings.tu2,
             settings.tu3, settings.tu4) < 0.0:
        raise ValueError('UnderexcLimIEEE1 bounds and time constants must be nonnegative')
    elif settings.vuimin >= settings.vuimax or settings.vulmin >= settings.vulmax:
        raise ValueError('UnderexcLimIEEE1 lower limits must be below upper limits')
    elif (settings.tu2 == 0.0 and settings.tu1 > 0.0) or (
            settings.tu4 == 0.0 and settings.tu3 > 0.0):
        raise ValueError('UnderexcLimIEEE1 zero lag requires a zero lead')
    else:
        pass

    template_name: str = 'UnderexcLimIEEE1' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    parameter_symbols: tuple[Var, ...] = tuple(
        model.parameter('UnderexcLimIEEE1.' + parameter_name, parameter_value)
        for parameter_name, parameter_value in (
            ('kur', settings.kur), ('kuc', settings.kuc), ('kuf', settings.kuf),
            ('vurmax', settings.vurmax), ('vucmax', settings.vucmax),
            ('kui', settings.kui), ('kul', settings.kul),
            ('vuimax', settings.vuimax), ('vuimin', settings.vuimin),
            ('tu1', settings.tu1), ('tu2', settings.tu2),
            ('tu3', settings.tu3), ('tu4', settings.tu4),
            ('vulmax', settings.vulmax), ('vulmin', settings.vulmin),
        )
    )
    radius_gain: Var = parameter_symbols[0]
    center_gain: Var = parameter_symbols[1]
    stabilizer_gain: Var = parameter_symbols[2]
    radius_limit: Var = parameter_symbols[3]
    center_limit: Var = parameter_symbols[4]
    integral_gain: Var = parameter_symbols[5]
    proportional_gain: Var = parameter_symbols[6]
    pi_upper: Var = parameter_symbols[7]
    pi_lower: Var = parameter_symbols[8]
    lead_one: Var = parameter_symbols[9]
    lag_one: Var = parameter_symbols[10]
    lead_two: Var = parameter_symbols[11]
    lag_two: Var = parameter_symbols[12]
    output_upper: Var = parameter_symbols[13]
    output_lower: Var = parameter_symbols[14]

    # Inputs retain complex terminal phasors because the circular characteristic depends on angle.
    voltage_real: Var = model.input('VtRePu', Const(1.0))
    voltage_imaginary: Var = model.input('VtImPu', Const(0.0))
    current_real: Var = model.input('ItRePu', Const(0.0))
    current_imaginary: Var = model.input('ItImPu', Const(0.0))
    stabilizer: Var = model.input('VfPu', Const(0.0))
    radius_magnitude: Expr = radius_gain * sym.sqrt(
        voltage_real * voltage_real + voltage_imaginary * voltage_imaginary,
    )
    center_real: Expr = center_gain * voltage_real + current_imaginary
    center_imaginary: Expr = center_gain * voltage_imaginary - current_real
    center_magnitude: Expr = sym.sqrt(
        center_real * center_real + center_imaginary * center_imaginary,
    )
    radius_signal: Var = model.algebraic(
        'VurPu', sym.hard_sat(radius_magnitude, Const(0.0), radius_limit), Const(0.0),
    )
    center_signal: Var = model.algebraic(
        'VucPu', sym.hard_sat(center_magnitude, Const(0.0), center_limit), Const(0.0),
    )
    control_error: Expr = center_signal - radius_signal + stabilizer_gain * stabilizer
    proportional_signal: Expr = proportional_gain * control_error
    if settings.kui > 0.0:
        integral_state: Var = vfactory.add_var(f'PiIntegralPu_{template_name}')
        model.differential(
            integral_state,
            integral_gain * control_error,
            Const(0.0),
            pi_lower - proportional_signal,
            pi_upper - proportional_signal,
        )
        pi_unbounded: Expr = proportional_signal + integral_state
    else:
        pi_unbounded = proportional_signal
    pi_output: Var = model.algebraic(
        'PiOutputPu', sym.hard_sat(pi_unbounded, pi_lower, pi_upper), Const(0.0),
    )
    first_compensation: Var = model.lead_lag(
        'LeadLag1Pu', pi_output, lead_one, lag_one, settings.tu1, settings.tu2, Const(0.0),
    )
    second_compensation: Var = model.lead_lag(
        'LeadLag2Pu', first_compensation, lead_two, lag_two,
        settings.tu3, settings.tu4, Const(0.0),
    )
    output: Var = model.algebraic(
        'VuelPu', sym.hard_sat(second_compensation, output_lower, output_upper), Const(0.0),
    )
    template: RmsModelTemplate = model.finish(
        (output,), 'CGMES IEEE UEL1 circular characteristic limiter',
    )
    template.comment = (
        'IEEE 421.5 Type UEL1: VUR=clip(|KUR*Vt|), VUC=clip(|KUC*Vt−j*It|), '
        'VUerr=VUC−VUR+KUF*Vf, followed by bounded KUL+KUI/s and TU1/TU2, TU3/TU4 '
        'lead-lags with VUL bounds. Vf remains an explicit input because this RDF class '
        'does not identify the source AVR stabilizing signal.'
    )
    enabled_name: str = f'UnderexcLimIEEE1.enabled_{template_name}'
    enabled_variable: Var = vfactory.add_var(enabled_name)
    model.block.event_dict[enabled_variable] = vfactory.add_const(value=None, name=enabled_name)
    return template
