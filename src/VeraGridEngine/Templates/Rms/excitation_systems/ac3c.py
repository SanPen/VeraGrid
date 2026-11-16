# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""PID brushless excitation with independent OEL and UEL routing."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.excitation_systems.dc_exciter import RotatingLimiterLocation
from VeraGridEngine.Templates.Rms.excitation_systems.esac3a import build_esac3a_template
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Ac3cParameters:
    """Store all 28 constants from the PSS/E 35.2 AC3C parameter table."""

    __slots__ = (
        'tr', 'tb', 'tc', 'ka', 'ta', 'vamax', 'vamin', 'te', 'vemin', 'kr',
        'kf', 'tf', 'kn', 'efdn', 'kc', 'kd', 'ke', 'vfemax', 'e1', 'se1',
        'e2', 'se2', 'kpa', 'kia', 'kda', 'tda', 'vpidmax', 'vpidmin',
    )

    def __init__(
            self,
            tr: float = 0.02, tb: float = 1.0, tc: float = 1.0,
            ka: float = 200.0, ta: float = 0.02, vamax: float = 5.0,
            vamin: float = -5.0, te: float = 0.5, vemin: float = 0.0,
            kr: float = 1.0, kf: float = 0.05, tf: float = 1.0,
            kn: float = 0.2, efdn: float = 2.0, kc: float = 0.0,
            kd: float = 0.0, ke: float = 1.0, vfemax: float = 5.0,
            e1: float = 2.3, se1: float = 0.1, e2: float = 3.1,
            se2: float = 0.33, kpa: float = 1.0, kia: float = 0.1,
            kda: float = 0.05, tda: float = 0.1, vpidmax: float = 5.0,
            vpidmin: float = -5.0,
    ) -> None:
        """Store source-order AC3C winding, regulator, saturation and PID data.

        :param tr: Terminal-voltage transducer time in seconds.
        :param tb: Lead-lag denominator time in seconds.
        :param tc: Lead-lag numerator time in seconds.
        :param ka: Voltage-regulator gain.
        :param ta: Regulator-output time in seconds.
        :param vamax: Upper regulator-output limit.
        :param vamin: Lower regulator-output limit.
        :param te: Exciter field time in seconds.
        :param vemin: Minimum exciter field voltage.
        :param kr: Self-excited regulator and alternator power gain.
        :param kf: Field-rate feedback gain.
        :param tf: Feedback time in seconds.
        :param kn: Upper-slope rate-feedback gain.
        :param efdn: Field-voltage knee for the feedback slope.
        :param kc: Rectifier commutating reactance coefficient.
        :param kd: Exciter demagnetizing coefficient.
        :param ke: Exciter field proportional coefficient.
        :param vfemax: Maximum current-equivalent exciter field.
        :param e1: First saturation sample voltage.
        :param se1: Saturation factor at E1.
        :param e2: Second saturation sample voltage.
        :param se2: Saturation factor at E2.
        :param kpa: PID proportional gain.
        :param kia: PID integral gain.
        :param kda: PID derivative gain.
        :param tda: PID derivative-filter time in seconds.
        :param vpidmax: PID output upper limit.
        :param vpidmin: PID output lower limit.
        """
        self.tr: float = tr
        self.tb: float = tb
        self.tc: float = tc
        self.ka: float = ka
        self.ta: float = ta
        self.vamax: float = vamax
        self.vamin: float = vamin
        self.te: float = te
        self.vemin: float = vemin
        self.kr: float = kr
        self.kf: float = kf
        self.tf: float = tf
        self.kn: float = kn
        self.efdn: float = efdn
        self.kc: float = kc
        self.kd: float = kd
        self.ke: float = ke
        self.vfemax: float = vfemax
        self.e1: float = e1
        self.se1: float = se1
        self.e2: float = e2
        self.se2: float = se2
        self.kpa: float = kpa
        self.kia: float = kia
        self.kda: float = kda
        self.tda: float = tda
        self.vpidmax: float = vpidmax
        self.vpidmin: float = vpidmin


def build_ac3c_template(
        vf: VarFactory,
        name: str | None = None,
        parameters: Ac3cParameters | None = None,
        oel_location: RotatingLimiterLocation = RotatingLimiterLocation.SUMMATION,
        uel_location: RotatingLimiterLocation = RotatingLimiterLocation.SUMMATION,
) -> RmsModelTemplate:
    """Build AC3C's PID, limiter gates and rotating-field excitation.

    The diagram places the PID before the lead-lag compensator, the field-rate
    feedback after phase compensation, and separate low/high OEL/UEL takeover
    gates after the PID path. The base rotating-field equations and initial
    magnetic/rectifier values are shared with ESAC3A. Two PID memories are
    included when derivative action is enabled; this follows the plotted
    integrator and filtered derivative even though the PSS/E state table lists
    only five states. Therefore this native template is not enabled for DYR
    conversion until that source state-count conflict is resolved.

    :param vf: Symbol factory owning the model equations.
    :param name: Optional unique controller label.
    :param parameters: All 28 source-order constants.
    :param oel_location: Summing-point or low-value takeover insertion.
    :param uel_location: Summing-point or high-value takeover insertion.
    :return: AC3C template with six host inputs and three diagnostic outputs.
    :raises ValueError: Invalid settings or limiter selections.
    """
    label: str = 'AC3C' if name is None else name
    selected: Ac3cParameters = Ac3cParameters() if parameters is None else parameters
    values: tuple[float, ...] = (
        selected.tr, selected.tb, selected.tc, selected.ka, selected.ta,
        selected.vamax, selected.vamin, selected.te, selected.vemin, selected.kr,
        selected.kf, selected.tf, selected.kn, selected.efdn, selected.kc,
        selected.kd, selected.ke, selected.vfemax, selected.e1, selected.se1,
        selected.e2, selected.se2, selected.kpa, selected.kia, selected.kda,
        selected.tda, selected.vpidmax, selected.vpidmin,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('AC3C settings must be finite')
    elif min(selected.tr, selected.tb, selected.ta, selected.te, selected.tf) <= 0.0:
        raise ValueError('AC3C transducer, lead, regulator, field and feedback times must be positive')
    elif selected.ka <= 0.0 or selected.kr <= 0.0 or selected.ke <= 0.0:
        raise ValueError('AC3C regulator, power and exciter-field gains must be positive')
    elif selected.kc < 0.0 or selected.kd < 0.0 or selected.kf < 0.0 or selected.kn < 0.0:
        raise ValueError('AC3C loading, demagnetizing and feedback gains must be nonnegative')
    elif selected.kpa < 0.0 or selected.kia <= 0.0 or selected.kda < 0.0:
        raise ValueError('AC3C requires nonnegative proportional/derivative and positive integral gains')
    elif selected.kda > 0.0 and selected.tda <= 0.0:
        raise ValueError('AC3C derivative action requires a positive filter time')
    elif selected.vpidmin >= selected.vpidmax:
        raise ValueError('AC3C PID output limits must be ordered')
    elif selected.vamin >= selected.vamax or selected.vemin < 0.0 or selected.vfemax <= 0.0:
        raise ValueError('AC3C regulator and exciter field limits are invalid')
    elif selected.se1 < 0.0 or selected.se2 < 0.0:
        raise ValueError('AC3C saturation factors must be nonnegative')
    elif (selected.se1 == 0.0) != (selected.se2 == 0.0):
        raise ValueError('AC3C saturation requires two enabled samples or two disabled samples')
    elif selected.se1 > 0.0 and (
            selected.e1 <= 0.0 or selected.e2 <= selected.e1
            or selected.e2 * selected.se2 <= selected.e1 * selected.se1):
        raise ValueError('AC3C saturation samples must increase in voltage and excess field')
    elif (not isinstance(oel_location, RotatingLimiterLocation)
            or not isinstance(uel_location, RotatingLimiterLocation)):
        raise ValueError('AC3C limiter selections must use supported locations')
    else:
        pass

    template: RmsModelTemplate = build_esac3a_template(vf, label)
    block: Block = template.block
    variables: dict[str, Var] = dict(
        (variable.name, variable) for variable in block.get_all_vars()
    )
    variables.update((variable.name, variable) for variable in block.event_dict)
    source_parameters: tuple[tuple[str, float], ...] = (
        ('avr.tR_', selected.tr), ('avr.tB_', selected.tb),
        ('avr.tC_', selected.tc), ('avr.Ka_', selected.ka),
        ('avr.tA_', selected.ta), ('avr.VrMaxPu_', selected.vamax),
        ('avr.VrMinPu_', selected.vamin), ('avr.tE_', selected.te),
        ('VEMIN_', selected.vemin), ('KR_', selected.kr),
        ('avr.Kf_', selected.kf), ('avr.tF_', selected.tf),
        ('KN_', selected.kn), ('EFDN_', selected.efdn),
        ('avr.Kc_', selected.kc), ('avr.Kd_', selected.kd),
        ('avr.Ke_', selected.ke), ('VFEMAX_', selected.vfemax),
        ('avr.VExcLowPu_', selected.e1), ('avr.VExcSatLowPu_', selected.se1),
        ('avr.VExcHighPu_', selected.e2), ('avr.VExcSatHighPu_', selected.se2),
    )
    for parameter_name, parameter_value in source_parameters:
        block.event_dict[variables[parameter_name + label]] = Const(parameter_value)
    block.event_dict[variables['avr.UsRef0Pu_' + label]] = variables['avr.Us0Pu_' + label]
    kpa: Var = vf.add_var('KPA_' + label)
    kia: Var = vf.add_var('KIA_' + label)
    kda: Var = vf.add_var('KDA_' + label)
    tda: Var = vf.add_var('TDA_' + label)
    pidmax: Var = vf.add_var('VPIDMAX_' + label)
    pidmin: Var = vf.add_var('VPIDMIN_' + label)
    block.event_dict[kpa] = Const(selected.kpa)
    block.event_dict[kia] = Const(selected.kia)
    block.event_dict[kda] = Const(selected.kda)
    block.event_dict[tda] = Const(selected.tda)
    block.event_dict[pidmax] = Const(selected.vpidmax)
    block.event_dict[pidmin] = Const(selected.vpidmin)

    # Rebuild the error sum so ICON choices control additive and takeover paths independently.
    sensed: Var = variables['avr.firstOrder.y_' + label]
    error_sum: Var = variables['avr.sum1.y_' + label]
    overexcitation: Var = block.in_vars[1]
    supplementary: Var = block.in_vars[2]
    reference: Var = block.in_vars[4]
    underexcitation: Var = block.in_vars[5]
    error: Expr = reference + supplementary - sensed
    if oel_location is RotatingLimiterLocation.SUMMATION:
        error += overexcitation
    else:
        pass
    if uel_location is RotatingLimiterLocation.SUMMATION:
        error += underexcitation
    else:
        pass

    # The PSS/E diagram uses KIA/s and KDA*s/(1+s*TDA); retain those memories explicitly.
    integral: Var = vf.add_var('PidIntegratorPu_' + label)
    block.state_vars.append(integral)
    block.diff_vars.append(vf.add_diff_var(name='d_' + integral.name, base_var=integral))
    block.state_eqs.append(kia * error)
    integral_output: Expr = integral
    derivative_output: Expr = Const(0.0)
    derivative_memory: Var | None = None
    if selected.kda > 0.0:
        derivative_memory = vf.add_var('PidDerivativeMemoryPu_' + label)
        block.state_vars.append(derivative_memory)
        block.diff_vars.append(
            vf.add_diff_var(name='d_' + derivative_memory.name, base_var=derivative_memory)
        )
        block.state_eqs.append((error - derivative_memory) / tda)
        derivative_output = kda * (error - derivative_memory) / tda
    else:
        pass

    pid_output: Var = vf.add_var('PidOutputPu_' + label)
    pid_expression: Expr = sym.hard_sat(
        kpa * error + integral_output + derivative_output, pidmin, pidmax,
    )
    block.algebraic_vars.append(pid_output)
    block.algebraic_eqs.append(pid_output - pid_expression)
    block.init_eqs[pid_output] = variables['avr.leadLag.y_start_' + label]

    # Seed the PID memories to preserve the base exciter's solved regulator demand.
    initial_error: Expr = error
    initial_phase: Expr = variables['avr.leadLag.y_start_' + label]
    block.init_eqs[integral] = initial_phase - kpa * initial_error
    if derivative_memory is not None:
        block.init_eqs[derivative_memory] = initial_error
    else:
        pass

    # Feed PID demand into phase compensation and apply the field-rate feedback after it.
    lead_input: Var = variables['avr.feedback.y_' + label]
    lead_output: Var = variables['avr.leadLag.y_' + label]
    feedback: Var = variables['avr.derivative.y_' + label]
    amplifier_drive: Var = variables['avr.limitedFirstOrder.Gk.y_' + label]
    regulated: Expr = lead_output - feedback
    if uel_location is RotatingLimiterLocation.TAKEOVER_GATE:
        regulated = sym.max(regulated, underexcitation)
    else:
        pass
    if oel_location is RotatingLimiterLocation.TAKEOVER_GATE:
        regulated = sym.min(regulated, overexcitation)
    else:
        pass
    amplifier_gain: Var = variables['avr.Ka_' + label]
    for index, variable in enumerate(block.algebraic_vars):
        if variable == error_sum:
            block.algebraic_eqs[index] = error_sum - error
        elif variable == lead_input:
            block.algebraic_eqs[index] = lead_input - pid_output
        elif variable == amplifier_drive:
            block.algebraic_eqs[index] = amplifier_drive - amplifier_gain * regulated
        else:
            pass
    block.init_eqs[error_sum] = error
    block.init_eqs[lead_input] = pid_output
    block.init_eqs[amplifier_drive] = amplifier_gain * regulated

    # Each absent gate receives its preceding live demand as an exact bypass.
    gate_initial: Expr = initial_phase
    if uel_location is RotatingLimiterLocation.TAKEOVER_GATE:
        block.init_eqs[underexcitation] = gate_initial
    else:
        block.init_eqs[underexcitation] = Const(0.0)
    if oel_location is RotatingLimiterLocation.TAKEOVER_GATE:
        block.init_eqs[overexcitation] = gate_initial
    else:
        block.init_eqs[overexcitation] = Const(0.0)
    block.out_vars = list((block.out_vars[0], pid_output, lead_output))
    template.comment = 'PID brushless exciter with independent over/under-excitation gates'
    return template
