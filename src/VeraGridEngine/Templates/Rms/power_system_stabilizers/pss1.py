# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed template for the canonical CGMES Pss1 model."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Pss1Parameters:
    """Canonical Pss1 gains, filter times, limits, and adaptive switch."""

    __slots__ = (
        'kw', 'kf', 'kpe', 'pmin', 'ks', 'vsmn', 'vsmx', 'tpe',
        't5', 't6', 't7', 't8', 't9', 't10', 'vadat',
    )

    def __init__(
            self,
            kw: float = 0.0,
            kf: float = 5.0,
            kpe: float = 0.3,
            pmin: float = 0.25,
            ks: float = 1.0,
            vsmn: float = -0.06,
            vsmx: float = 0.06,
            tpe: float = 0.05,
            t5: float = 3.5,
            t6: float = 0.0,
            t7: float = 0.0,
            t8: float = 0.0,
            t9: float = 0.0,
            t10: float = 0.0,
            vadat: bool = True,
    ) -> None:
        """Store imported Pss1 values in their CGMES units.

        :param kw: Shaft-speed input gain.
        :param kf: Frequency input gain.
        :param kpe: Electrical-power input gain.
        :param pmin: Minimum power enabling adaptive output scaling.
        :param ks: Stabilizer gain.
        :param vsmn: Lower output limit.
        :param vsmx: Upper output limit.
        :param tpe: Active-power adaptive-path lag in seconds.
        :param t5: Main washout time in seconds.
        :param t6: Post-washout lag time in seconds.
        :param t7: First lead-lag denominator time in seconds.
        :param t8: First lead-lag numerator time in seconds.
        :param t9: Second lead-lag denominator time in seconds.
        :param t10: Second lead-lag numerator time in seconds.
        :param vadat: Enable the power-threshold adaptive output branch.
        """
        self.kw: float = kw
        self.kf: float = kf
        self.kpe: float = kpe
        self.pmin: float = pmin
        self.ks: float = ks
        self.vsmn: float = vsmn
        self.vsmx: float = vsmx
        self.tpe: float = tpe
        self.t5: float = t5
        self.t6: float = t6
        self.t7: float = t7
        self.t8: float = t8
        self.t9: float = t9
        self.t10: float = t10
        self.vadat: bool = vadat


def build_pss1_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: Pss1Parameters | None = None,
) -> RmsModelTemplate:
    """Build the EA1307 three-input Italian stabilizer and adaptive output path.

    :param vfactory: Factory allocating the equation and parameter symbols.
    :param name: Optional unique runtime instance name.
    :param parameters: Imported CGMES Pss1 settings.
    :return: Equation-backed stabilizer with speed, frequency, and Pe inputs.
    :raises ValueError: Invalid times, limits, or nonfinite field values.
    """
    settings: Pss1Parameters = Pss1Parameters() if parameters is None else parameters
    values: tuple[float, ...] = (
        settings.kw, settings.kf, settings.kpe, settings.pmin, settings.ks,
        settings.vsmn, settings.vsmx, settings.tpe, settings.t5, settings.t6,
        settings.t7, settings.t8, settings.t9, settings.t10,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('CGMES Pss1 parameters must be finite')
    elif min(settings.tpe, settings.t5, settings.t6, settings.t7,
             settings.t8, settings.t9, settings.t10) < 0.0:
        raise ValueError('CGMES Pss1 times must be nonnegative')
    elif settings.vsmn >= settings.vsmx:
        raise ValueError('CGMES Pss1 output limits must be ordered')
    elif (settings.t7 == 0.0 and settings.t8 != 0.0) or (settings.t9 == 0.0 and settings.t10 != 0.0):
        raise ValueError('CGMES Pss1 lead time requires a nonzero lag time')
    else:
        pass

    template_name: str = 'Pss1' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    shaft_speed: Var = model.input('OmegaPu', Const(1.0))
    frequency_deviation: Var = model.input('FrequencyDeviationPu', Const(0.0))
    electrical_power: Var = model.input('PePu', Const(0.0))
    measured_power: Var = model.lag(
        'MeasuredPowerPu', electrical_power,
        model.parameter('Pss1.tpe', settings.tpe), settings.tpe, electrical_power,
    )
    input_sum: Expr = (
        model.parameter('Pss1.kw', settings.kw) * (shaft_speed - Const(1.0))
        + model.parameter('Pss1.kf', settings.kf) * frequency_deviation
        - model.parameter('Pss1.kpe', settings.kpe) * electrical_power
    )
    if settings.t5 > 0.0:
        washed_signal: Var = model.washout(
            'MainWashoutPu', input_sum,
            model.parameter('Pss1.t5', settings.t5), settings.t5,
            Const(1.0), input_sum,
        )
    else:
        washed_signal = model.algebraic('MainWashoutPu', Const(0.0), Const(0.0))
    filtered_signal: Var = model.lag(
        'PostWashoutFilterPu', washed_signal,
        model.parameter('Pss1.t6', settings.t6), settings.t6, Const(0.0),
    )
    gained_signal: Expr = model.parameter('Pss1.ks', settings.ks) * filtered_signal
    first_phase: Var = model.lead_lag(
        'FirstPhasePu', gained_signal,
        model.parameter('Pss1.t8', settings.t8),
        model.parameter('Pss1.t7', settings.t7),
        settings.t8, settings.t7, Const(0.0),
    )
    second_phase: Var = model.lead_lag(
        'SecondPhasePu', first_phase,
        model.parameter('Pss1.t10', settings.t10),
        model.parameter('Pss1.t9', settings.t9),
        settings.t10, settings.t9, Const(0.0),
    )
    bounded_signal: Expr = sym.hard_sat(
        second_phase,
        model.parameter('Pss1.vsmn', settings.vsmn),
        model.parameter('Pss1.vsmx', settings.vsmx),
    )
    power_threshold: Var = model.parameter('Pss1.pmin', settings.pmin)
    power_gate: Expr = sym.heaviside(measured_power - power_threshold)
    power_sign: Expr = sym.safe_divide(
        measured_power, sym.abs(measured_power), Const(1.0),
    )
    if settings.vadat:
        adapted_signal: Expr = bounded_signal * (
            Const(1.0) + Const(0.05) * power_gate * power_sign
        )
    else:
        adapted_signal = bounded_signal
    output: Var = model.algebraic('VsPu', adapted_signal, Const(0.0))
    template: RmsModelTemplate = model.finish((output,), 'CGMES Pss1 three-input stabilizer')
    template.comment = 'CGMES Pss1 EA1307 speed/frequency/power path, phase stages, output limits, and VADAT.'
    vadat: Var = vfactory.add_var(f'Pss1.vadat_{template_name}')
    template.block.event_dict[vadat] = vfactory.add_const(value=settings.vadat)
    return template
