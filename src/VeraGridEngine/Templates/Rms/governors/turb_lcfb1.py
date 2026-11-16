# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES TurbLCFB1 supervisory load controller."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class TurbLCFB1Parameters:
    """Canonical TurbLCFB1 scalar and selector properties."""

    __slots__ = (
        'mwbase', 'speed_reference_governor', 'db', 'emax', 'fb', 'kp', 'ki',
        'fbf', 'pbf', 'tpelec', 'irmax', 'pmwset',
    )

    def __init__(
            self, mwbase: float = 100.0, speed_reference_governor: bool = True,
            db: float = 0.0, emax: float = 0.02, fb: float = 0.0,
            kp: float = 0.0, ki: float = 0.0, fbf: bool = False,
            pbf: bool = False, tpelec: float = 0.0, irmax: float = 0.0,
            pmwset: float = 0.0,
    ) -> None:
        """Store the complete TurbLCFB1 RDF parameter surface.

        :param mwbase: Controller power base in MW.
        :param speed_reference_governor: True for a speed-reference governor, false for load reference.
        :param db: Symmetric power-error deadband in per unit.
        :param emax: Symmetric maximum control-error magnitude in per unit.
        :param fb: Frequency-bias gain.
        :param kp: Proportional gain.
        :param ki: Integral gain.
        :param fbf: Enables frequency bias when true.
        :param pbf: Enables load control when true.
        :param tpelec: Electrical-power transducer lag time in seconds.
        :param irmax: Symmetric governor-reference correction bound.
        :param pmwset: Active-power setpoint in MW.
        """
        self.mwbase: float = mwbase
        self.speed_reference_governor: bool = speed_reference_governor
        self.db: float = db
        self.emax: float = emax
        self.fb: float = fb
        self.kp: float = kp
        self.ki: float = ki
        self.fbf: bool = fbf
        self.pbf: bool = pbf
        self.tpelec: float = tpelec
        self.irmax: float = irmax
        self.pmwset: float = pmwset


def build_turb_l_c_f_b1_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: TurbLCFB1Parameters | None = None,
) -> RmsModelTemplate:
    """Build filtered power, deadband, frequency-bias and bounded PI equations.

    :param vfactory: Factory allocating the graph variables.
    :param name: Optional runtime model name.
    :param parameters: Canonical TurbLCFB1 settings.
    :return: Load controller with Pe/frequency/base-reference inputs and Pref output.
    :raises ValueError: A parameter is nonfinite, a base is invalid, or limits are unordered.
    """
    settings: TurbLCFB1Parameters = TurbLCFB1Parameters() if parameters is None else parameters
    numeric_values: tuple[float, ...] = (
        settings.mwbase, settings.db, settings.emax, settings.fb, settings.kp,
        settings.ki, settings.tpelec, settings.irmax, settings.pmwset,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('TurbLCFB1 parameters must be finite')
    elif settings.mwbase <= 0.0:
        raise ValueError('TurbLCFB1 MWBASE must be positive')
    elif min(settings.db, settings.emax, settings.kp, settings.ki,
             settings.tpelec, settings.irmax) < 0.0:
        raise ValueError('TurbLCFB1 deadband, gains, time and limit must be nonnegative')
    else:
        pass

    template_name: str = 'TurbLCFB1' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    parameter_values: tuple[tuple[str, float], ...] = (
        ('mwbase', settings.mwbase), ('db', settings.db), ('emax', settings.emax),
        ('fb', settings.fb), ('kp', settings.kp), ('ki', settings.ki),
        ('tpelec', settings.tpelec), ('irmax', settings.irmax),
        ('pmwset', settings.pmwset),
        ('fbf', float(settings.fbf)), ('pbf', float(settings.pbf)),
        ('speedReferenceGovernor', float(settings.speed_reference_governor)),
    )
    parameter_symbols: tuple[Var, ...] = tuple(
        model.parameter('TurbLCFB1.' + property_name, property_value)
        for property_name, property_value in parameter_values
    )
    electrical_base: Var = parameter_symbols[0]
    deadband: Var = parameter_symbols[1]
    error_limit: Var = parameter_symbols[2]
    frequency_gain: Var = parameter_symbols[3]
    proportional_gain: Var = parameter_symbols[4]
    integral_gain: Var = parameter_symbols[5]
    power_filter_time: Var = parameter_symbols[6]
    reference_limit: Var = parameter_symbols[7]
    power_setpoint: Var = parameter_symbols[8]
    frequency_bias_enabled: Var = parameter_symbols[9]
    controller_enabled: Var = parameter_symbols[10]

    # The NERC LCFB1 diagram compares setpoint and filtered Pe, with frequency bias optional.
    electrical_power: Var = model.input('PePu', Const(settings.pmwset / settings.mwbase))
    frequency_deviation: Var = model.input('FrequencyDeviationPu', Const(0.0))
    reference_base: Var = model.input('Pref0Pu', Const(0.0))
    filtered_power: Var = model.lag(
        'PeFilteredPu', electrical_power, power_filter_time, settings.tpelec,
        Const(settings.pmwset / settings.mwbase),
    )
    power_error: Expr = power_setpoint / electrical_base - filtered_power
    frequency_correction: Expr = (
        frequency_bias_enabled * frequency_gain * frequency_deviation
    )
    error_before_deadband: Expr = power_error - frequency_correction
    deadbanded_error: Expr = (
        sym.max(error_before_deadband - deadband, Const(0.0))
        - sym.max(-error_before_deadband - deadband, Const(0.0))
    )
    limited_error: Var = model.algebraic(
        'LimitedErrorPu', sym.hard_sat(deadbanded_error, -error_limit, error_limit), Const(0.0),
    )
    proportional_output: Expr = sym.hard_sat(
        proportional_gain * limited_error, -reference_limit, reference_limit,
    )
    if settings.ki > 0.0 and settings.irmax > 0.0:
        integral_state: Var = vfactory.add_var(f'LoadControlIntegralPu_{template_name}')
        model.differential(
            integral_state, integral_gain * limited_error, Const(0.0),
            -reference_limit, reference_limit,
        )
        integral_output: Expr = integral_state
    else:
        integral_output = Const(0.0)
    correction: Expr = controller_enabled * sym.hard_sat(
        proportional_output + integral_output, -reference_limit, reference_limit,
    )
    governor_reference: Var = model.algebraic(
        'PrefPu', reference_base + correction, Const(0.0),
    )
    template: RmsModelTemplate = model.finish(
        (governor_reference,), 'CGMES TurbLCFB1 filtered-power supervisory PI controller',
    )
    template.comment = (
        'NERC 2019 LCFB1 Figure 1.5 / IEC 61970-302 Figure 85: '
        'Pref0 + clip(Kp*e + integral(Ki*e), ±Irmax), where e is the '
        'deadbanded and Emax-limited Pmwset/MWBASE − PeFiltered − FBF*FB*Δf. '
        'The RDF speedReferenceGovernor selector determines the connected governor-reference port.'
    )
    enabled_name: str = f'TurbLCFB1.enabled_{template_name}'
    enabled_variable: Var = vfactory.add_var(enabled_name)
    model.block.event_dict[enabled_variable] = vfactory.add_const(value=None, name=enabled_name)
    return template
