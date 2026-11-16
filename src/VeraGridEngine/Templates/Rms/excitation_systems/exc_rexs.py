# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""CGMES ExcREXS rotating-exciter regulator and field equations."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcREXSParameters:
    """Canonical ExcREXS scalar values controlling the block realization."""

    __slots__ = (
        'e1', 'e2', 'fbf_code', 'flimf', 'kc', 'kd', 'ke', 'kefd', 'kf', 'kh',
        'kii', 'kip', 'ks', 'kvi', 'kvp', 'kvphz', 'nvphz', 'se1', 'se2',
        'ta', 'tb1', 'tb2', 'tc1', 'tc2', 'te', 'tf', 'tf1', 'tf2', 'tp',
        'vcmax', 'vfmax', 'vfmin', 'vimax', 'vrmax', 'vrmin', 'xc',
    )

    def __init__(
            self,
            e1: float = 0.0,
            e2: float = 0.0,
            fbf_code: int = 0,
            flimf: float = 0.0,
            kc: float = 0.0,
            kd: float = 0.0,
            ke: float = 0.0,
            kefd: float = 0.0,
            kf: float = 0.0,
            kh: float = 0.0,
            kii: float = 0.0,
            kip: float = 1.0,
            ks: float = 0.0,
            kvi: float = 0.0,
            kvp: float = 1.0,
            kvphz: float = 0.0,
            nvphz: float = 0.0,
            se1: float = 0.0,
            se2: float = 0.0,
            ta: float = 0.0,
            tb1: float = 0.0,
            tb2: float = 0.0,
            tc1: float = 0.0,
            tc2: float = 0.0,
            te: float = 1.0,
            tf: float = 0.0,
            tf1: float = 0.0,
            tf2: float = 0.0,
            tp: float = 0.0,
            vcmax: float = 0.0,
            vfmax: float = 0.0,
            vfmin: float = 0.0,
            vimax: float = 0.0,
            vrmax: float = 0.0,
            vrmin: float = 0.0,
            xc: float = 0.0,
    ) -> None:
        """Store the 35 numeric RDF properties and enum code.

        :param e1: First saturation voltage point.
        :param e2: Second saturation voltage point.
        :param fbf_code: RDF feedback selector code, 0 through 2.
        :param flimf: Flag selecting fixed or terminal-voltage scaled limits.
        :param kc: Rotating-rectifier commutation coefficient.
        :param kd: Exciter armature-reaction coefficient.
        :param ke: Exciter field-loss coefficient.
        :param kefd: Exciter field-current feedback gain.
        :param kf: Rate-feedback gain.
        :param kh: Inner field-current feedback gain.
        :param kii: Field-current regulator integral gain.
        :param kip: Field-current regulator proportional gain.
        :param ks: Excitation output speed multiplier gain.
        :param kvi: Voltage-regulator integral gain.
        :param kvp: Voltage-regulator proportional gain.
        :param kvphz: Volts-per-hertz reduction gain.
        :param nvphz: Volts-per-hertz speed threshold.
        :param se1: Saturation at e1.
        :param se2: Saturation at e2.
        :param ta: Voltage-regulator output time constant.
        :param tb1: First voltage-regulator lag time.
        :param tb2: Second voltage-regulator lag time.
        :param tc1: First voltage-regulator lead time.
        :param tc2: Second voltage-regulator lead time.
        :param te: Exciter field time constant.
        :param tf: Rate-feedback washout time constant.
        :param tf1: Feedback lead time.
        :param tf2: Feedback lag time.
        :param tp: Field-current regulator output time constant.
        :param vcmax: Upper bound on terminal-current compounding voltage.
        :param vfmax: Upper field-current regulator output limit.
        :param vfmin: Lower field-current regulator output limit.
        :param vimax: Symmetric voltage-regulator input limit.
        :param vrmax: Upper voltage-regulator output limit.
        :param vrmin: Lower voltage-regulator output limit.
        :param xc: Terminal-current compounding reactance.
        """
        self.e1: float = e1
        self.e2: float = e2
        self.fbf_code: int = fbf_code
        self.flimf: float = flimf
        self.kc: float = kc
        self.kd: float = kd
        self.ke: float = ke
        self.kefd: float = kefd
        self.kf: float = kf
        self.kh: float = kh
        self.kii: float = kii
        self.kip: float = kip
        self.ks: float = ks
        self.kvi: float = kvi
        self.kvp: float = kvp
        self.kvphz: float = kvphz
        self.nvphz: float = nvphz
        self.se1: float = se1
        self.se2: float = se2
        self.ta: float = ta
        self.tb1: float = tb1
        self.tb2: float = tb2
        self.tc1: float = tc1
        self.tc2: float = tc2
        self.te: float = te
        self.tf: float = tf
        self.tf1: float = tf1
        self.tf2: float = tf2
        self.tp: float = tp
        self.vcmax: float = vcmax
        self.vfmax: float = vfmax
        self.vfmin: float = vfmin
        self.vimax: float = vimax
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin
        self.xc: float = xc


def build_exc_r_e_x_s_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcREXSParameters | None = None,
) -> RmsModelTemplate:
    """Build the ExcREXS regulator, feedback, rotating field, and rectifier.

    :param vfactory: Factory allocating symbolic variables.
    :param name: Optional runtime model name.
    :param parameters: Canonical parsed RDF properties.
    :return: Equation-backed standalone CGMES ExcREXS model.
    :raises ValueError: An invalid selector, time constant, or limit ordering.
    """
    settings: ExcREXSParameters = ExcREXSParameters() if parameters is None else parameters
    template_name: str = 'ExcREXS' if name is None else name
    parameter_names: tuple[str, ...] = (
        'e1', 'e2', 'flimf', 'kc', 'kd', 'ke', 'kefd', 'kf', 'kh', 'kii', 'kip',
        'ks', 'kvi', 'kvp', 'kvphz', 'nvphz', 'se1', 'se2', 'ta', 'tb1', 'tb2',
        'tc1', 'tc2', 'te', 'tf', 'tf1', 'tf2', 'tp', 'vcmax', 'vfmax', 'vfmin',
        'vimax', 'vrmax', 'vrmin', 'xc',
    )
    parameter_values: tuple[float, ...] = (
        settings.e1, settings.e2, settings.flimf, settings.kc, settings.kd,
        settings.ke, settings.kefd, settings.kf, settings.kh, settings.kii,
        settings.kip, settings.ks, settings.kvi, settings.kvp, settings.kvphz,
        settings.nvphz, settings.se1, settings.se2, settings.ta, settings.tb1,
        settings.tb2, settings.tc1, settings.tc2, settings.te, settings.tf,
        settings.tf1, settings.tf2, settings.tp, settings.vcmax, settings.vfmax,
        settings.vfmin, settings.vimax, settings.vrmax, settings.vrmin, settings.xc,
    )
    if not all(math.isfinite(value) for value in parameter_values):
        raise ValueError('ExcREXS numeric parameters must be finite')
    elif settings.fbf_code not in (0, 1, 2):
        raise ValueError('ExcREXS fbf must select fieldVoltage, fieldCurrent, or outputVoltage')
    elif settings.flimf not in (0.0, 1.0):
        raise ValueError('ExcREXS flimf must be zero or one')
    elif min(settings.ta, settings.tb1, settings.tb2, settings.te, settings.tf,
             settings.tf1, settings.tf2, settings.tp) < 0.0:
        raise ValueError('ExcREXS time constants must be nonnegative')
    elif settings.te <= 0.0:
        raise ValueError('ExcREXS requires a positive exciter field time constant Te')
    elif (settings.tb1 == 0.0 and settings.tc1 > 0.0) or (settings.tb2 == 0.0 and settings.tc2 > 0.0):
        raise ValueError('ExcREXS lead times require positive corresponding lag times')
    elif settings.tf2 == 0.0 and settings.tf1 > 0.0:
        raise ValueError('ExcREXS feedback lead Tf1 requires a positive lag Tf2')
    elif settings.vrmin > settings.vrmax or settings.vfmin > settings.vfmax:
        raise ValueError('ExcREXS lower limits must not exceed their upper limits')
    elif settings.kvp == 0.0 and settings.kvi == 0.0:
        raise ValueError('ExcREXS voltage regulator requires Kvp or Kvi')
    elif settings.kip == 0.0 and settings.kii == 0.0:
        raise ValueError('ExcREXS field-current regulator requires Kip or Kii')
    else:
        pass

    template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    block: Block = Block(name=template_name)
    parameter_variables: list[Var] = list()
    for parameter_index in range(len(parameter_names)):
        parameter_name: str = parameter_names[parameter_index]
        parameter_variable: Var = vfactory.add_var(f'ExcREXS.{parameter_name}_{template_name}')
        block.event_dict[parameter_variable] = vfactory.add_const(
            value=parameter_values[parameter_index],
            name=parameter_variable.name,
        )
        parameter_variables.append(parameter_variable)
    parameter_by_name: dict[str, Var] = dict()
    for parameter_index in range(len(parameter_names)):
        parameter_by_name[parameter_names[parameter_index]] = parameter_variables[parameter_index]
    feedback_selector: Var = vfactory.add_var(f'ExcREXS.fbf_{template_name}')
    block.event_dict[feedback_selector] = vfactory.add_const(
        value=float(settings.fbf_code), name=feedback_selector.name,
    )
    e1: Var = parameter_by_name['e1']
    e2: Var = parameter_by_name['e2']
    flimf: Var = parameter_by_name['flimf']
    kc: Var = parameter_by_name['kc']
    kd: Var = parameter_by_name['kd']
    ke: Var = parameter_by_name['ke']
    kefd: Var = parameter_by_name['kefd']
    kf: Var = parameter_by_name['kf']
    kh: Var = parameter_by_name['kh']
    kii: Var = parameter_by_name['kii']
    kip: Var = parameter_by_name['kip']
    ks: Var = parameter_by_name['ks']
    kvi: Var = parameter_by_name['kvi']
    kvp: Var = parameter_by_name['kvp']
    kvphz: Var = parameter_by_name['kvphz']
    nvphz: Var = parameter_by_name['nvphz']
    se1: Var = parameter_by_name['se1']
    se2: Var = parameter_by_name['se2']
    ta: Var = parameter_by_name['ta']
    tb1: Var = parameter_by_name['tb1']
    tb2: Var = parameter_by_name['tb2']
    tc1: Var = parameter_by_name['tc1']
    tc2: Var = parameter_by_name['tc2']
    te: Var = parameter_by_name['te']
    tf: Var = parameter_by_name['tf']
    tf1: Var = parameter_by_name['tf1']
    tf2: Var = parameter_by_name['tf2']
    tp: Var = parameter_by_name['tp']
    vcmax: Var = parameter_by_name['vcmax']
    vfmax: Var = parameter_by_name['vfmax']
    vfmin: Var = parameter_by_name['vfmin']
    vimax: Var = parameter_by_name['vimax']
    vrmax: Var = parameter_by_name['vrmax']
    vrmin: Var = parameter_by_name['vrmin']
    xc: Var = parameter_by_name['xc']

    # Explicit ports keep converter associations independent from internal equation symbols.
    reference: Var = vfactory.add_var(f'VRefPu_ExcREXS_{template_name}')
    terminal_voltage: Var = vfactory.add_var(f'VcPu_ExcREXS_{template_name}')
    terminal_voltage_magnitude: Var = vfactory.add_var(f'VtermPu_ExcREXS_{template_name}')
    terminal_current_real: Var = vfactory.add_var(f'ItermRePu_ExcREXS_{template_name}')
    terminal_current_imaginary: Var = vfactory.add_var(f'ItermImPu_ExcREXS_{template_name}')
    stabilizer: Var = vfactory.add_var(f'VsPu_ExcREXS_{template_name}')
    underexcitation_limiter: Var = vfactory.add_var(f'VuelPu_ExcREXS_{template_name}')
    overexcitation_limiter: Var = vfactory.add_var(f'VoelPu_ExcREXS_{template_name}')
    field_current: Var = vfactory.add_var(f'IfdPu_ExcREXS_{template_name}')
    speed: Var = vfactory.add_var(f'SpeedPu_ExcREXS_{template_name}')
    block.in_vars = [
        reference, terminal_voltage, terminal_voltage_magnitude, terminal_current_real,
        terminal_current_imaginary, stabilizer, underexcitation_limiter,
        overexcitation_limiter, field_current, speed,
    ]
    block.init_eqs[reference] = Const(1.0)
    block.init_eqs[terminal_voltage] = Const(1.0)
    block.init_eqs[terminal_voltage_magnitude] = Const(1.0)
    block.init_eqs[terminal_current_real] = Const(0.0)
    block.init_eqs[terminal_current_imaginary] = Const(0.0)
    block.init_eqs[stabilizer] = Const(0.0)
    block.init_eqs[underexcitation_limiter] = Const(0.0)
    block.init_eqs[overexcitation_limiter] = Const(0.0)
    block.init_eqs[field_current] = Const(1.0)
    block.init_eqs[speed] = Const(1.0)

    # The local EA diagram sums auxiliary signals before the symmetric Vimax clip.
    effective_reference: Expr = reference
    if settings.kvphz != 0.0 and settings.nvphz != 0.0:
        effective_reference = reference * (
            Const(1.0) - kvphz * (speed - nvphz) * sym.heaviside(nvphz - speed)
        )
    else:
        pass
    feedback_signal: Var = vfactory.add_var(f'RateFeedbackPu_ExcREXS_{template_name}')
    regulator_error: Expr = sym.hard_sat(
        effective_reference - terminal_voltage + stabilizer
        + underexcitation_limiter + overexcitation_limiter - feedback_signal,
        -vimax,
        vimax,
    )

    # The PI regulator is followed by two independently bypassable lead-lag stages.
    voltage_regulator_output: Expr = kvp * regulator_error
    if settings.kvi != 0.0:
        voltage_integrator: Var = vfactory.add_var(f'VoltageRegulatorIntegral_ExcREXS_{template_name}')
        block.state_vars.append(voltage_integrator)
        block.state_eqs.append(kvi * regulator_error)
        block.diff_vars.append(vfactory.add_diff_var(
            f'd_VoltageRegulatorIntegral_ExcREXS_{template_name}', base_var=voltage_integrator,
        ))
        block.init_eqs[voltage_integrator] = Const(0.0)
        voltage_regulator_output = voltage_regulator_output + voltage_integrator
    else:
        pass
    for stage_index in range(2):
        if stage_index == 0:
            lag_time: float = settings.tb1
            lag_parameter: Var = tb1
            lead_parameter: Var = tc1
        else:
            lag_time = settings.tb2
            lag_parameter = tb2
            lead_parameter = tc2
        if lag_time > 0.0:
            lead_lag_state: Var = vfactory.add_var(
                f'VoltageRegulatorLeadLag{stage_index + 1}_ExcREXS_{template_name}',
            )
            block.state_vars.append(lead_lag_state)
            block.state_eqs.append((voltage_regulator_output - lead_lag_state) / lag_parameter)
            block.diff_vars.append(vfactory.add_diff_var(
                f'd_VoltageRegulatorLeadLag{stage_index + 1}_ExcREXS_{template_name}',
                base_var=lead_lag_state,
            ))
            block.init_eqs[lead_lag_state] = Const(0.0)
            voltage_regulator_output = lead_lag_state + (lead_parameter / lag_parameter) * (
                voltage_regulator_output - lead_lag_state
            )
        else:
            voltage_regulator_output = voltage_regulator_output
    vr_limit_scale: Expr = Const(1.0) + flimf * (terminal_voltage_magnitude - Const(1.0))
    regulator_output_limit_low: Expr = vrmin * vr_limit_scale
    regulator_output_limit_high: Expr = vrmax * vr_limit_scale
    regulator_output: Var = vfactory.add_var(f'VrPu_ExcREXS_{template_name}')
    if settings.ta > 0.0:
        regulator_lag: Var = vfactory.add_var(f'VoltageRegulatorLag_ExcREXS_{template_name}')
        block.state_vars.append(regulator_lag)
        block.state_eqs.append((voltage_regulator_output - regulator_lag) / ta)
        block.diff_vars.append(vfactory.add_diff_var(
            f'd_VoltageRegulatorLag_ExcREXS_{template_name}', base_var=regulator_lag,
        ))
        block.init_eqs[regulator_lag] = Const(0.0)
        block.algebraic_vars.append(regulator_output)
        block.algebraic_eqs.append(regulator_output - sym.hard_sat(
            regulator_lag, regulator_output_limit_low, regulator_output_limit_high,
        ))
    else:
        block.algebraic_vars.append(regulator_output)
        block.algebraic_eqs.append(regulator_output - sym.hard_sat(
            voltage_regulator_output, regulator_output_limit_low, regulator_output_limit_high,
        ))
    block.init_eqs[regulator_output] = Const(0.0)

    # Selector 0 uses AVR output, 1 uses Kefd*Efd, and 2 uses exciter output voltage.
    field_voltage_state: Var = vfactory.add_var(f'FieldVoltage_ExcREXS_{template_name}')
    field_voltage_output: Var = vfactory.add_var(f'EfdPu_ExcREXS_{template_name}')
    selected_field_voltage: Expr = sym.heaviside(Const(0.5) - feedback_selector)
    selected_field_current: Expr = (
        sym.heaviside(feedback_selector - Const(0.5))
        - sym.heaviside(feedback_selector - Const(1.5))
    )
    selected_output_voltage: Expr = sym.heaviside(feedback_selector - Const(1.5))
    selected_feedback: Expr = (
        regulator_output * selected_field_voltage
        + kefd * field_voltage_output * selected_field_current
        + field_voltage_output * selected_output_voltage
    )
    feedback_filtered: Expr = selected_feedback
    if settings.tf2 > 0.0:
        feedback_filter_state: Var = vfactory.add_var(f'FeedbackFilter_ExcREXS_{template_name}')
        block.state_vars.append(feedback_filter_state)
        block.state_eqs.append((selected_feedback - feedback_filter_state) / tf2)
        block.diff_vars.append(vfactory.add_diff_var(
            f'd_FeedbackFilter_ExcREXS_{template_name}', base_var=feedback_filter_state,
        ))
        block.init_eqs[feedback_filter_state] = Const(0.0)
        feedback_filtered = feedback_filter_state + (tf1 / tf2) * (
            selected_feedback - feedback_filter_state
        )
    else:
        pass
    feedback_output: Expr = Const(0.0)
    if settings.tf > 0.0:
        feedback_washout_state: Var = vfactory.add_var(f'FeedbackWashout_ExcREXS_{template_name}')
        block.state_vars.append(feedback_washout_state)
        block.state_eqs.append((feedback_filtered - feedback_washout_state) / tf)
        block.diff_vars.append(vfactory.add_diff_var(
            f'd_FeedbackWashout_ExcREXS_{template_name}', base_var=feedback_washout_state,
        ))
        block.init_eqs[feedback_washout_state] = Const(0.0)
        feedback_output = kf * (feedback_filtered - feedback_washout_state)
    else:
        pass

    # The inner current loop, compounding reactance, and exciter field balance follow EA1145.
    inner_current_error: Expr = regulator_output - kh * selected_feedback
    current_regulator_output: Expr = kip * inner_current_error
    if settings.kii != 0.0:
        current_integrator: Var = vfactory.add_var(f'FieldCurrentRegulatorIntegral_ExcREXS_{template_name}')
        block.state_vars.append(current_integrator)
        block.state_eqs.append(kii * inner_current_error)
        block.diff_vars.append(vfactory.add_diff_var(
            f'd_FieldCurrentRegulatorIntegral_ExcREXS_{template_name}', base_var=current_integrator,
        ))
        block.init_eqs[current_integrator] = Const(0.0)
        current_regulator_output = current_regulator_output + current_integrator
    else:
        pass
    vf_limit_scale: Expr = Const(1.0) + flimf * (terminal_voltage_magnitude - Const(1.0))
    current_output_limit_low: Expr = vfmin * vf_limit_scale
    current_output_limit_high: Expr = vfmax * vf_limit_scale
    field_current_regulator_output: Expr = sym.hard_sat(
        current_regulator_output, current_output_limit_low, current_output_limit_high,
    )
    if settings.tp > 0.0:
        current_regulator_lag: Var = vfactory.add_var(f'FieldCurrentRegulatorLag_ExcREXS_{template_name}')
        block.state_vars.append(current_regulator_lag)
        block.state_eqs.append((current_regulator_output - current_regulator_lag) / tp)
        block.diff_vars.append(vfactory.add_diff_var(
            f'd_FieldCurrentRegulatorLag_ExcREXS_{template_name}', base_var=current_regulator_lag,
        ))
        block.init_eqs[current_regulator_lag] = Const(0.0)
        field_current_regulator_output = sym.hard_sat(
            current_regulator_lag, current_output_limit_low, current_output_limit_high,
        )
    else:
        pass
    terminal_current_magnitude: Expr = sym.sqrt(
        terminal_current_real ** Const(2.0) + terminal_current_imaginary ** Const(2.0),
    )
    compounding_voltage: Expr = sym.hard_sat(
        xc * terminal_current_magnitude, 0.0, vcmax,
    )
    exciter_field_input: Expr = field_current_regulator_output + compounding_voltage
    saturation: Expr = Const(0.0)
    first_saturation_product: float = settings.e1 * settings.se1
    second_saturation_product: float = settings.e2 * settings.se2
    if first_saturation_product > 0.0 and second_saturation_product > 0.0 and settings.e1 != settings.e2:
        saturation_slope: Expr = sym.log((e2 * se2) / (e1 * se1)) / (e2 - e1)
        saturation_intercept: Expr = e1 * se1 * sym.exp(-saturation_slope * e1)
        saturation = saturation_intercept * sym.exp(saturation_slope * field_voltage_state) / sym.max(
            field_voltage_state, Const(1e-9),
        )
    else:
        pass
    field_balance: Expr = (
        exciter_field_input + kd * field_current
        - (ke + saturation) * field_voltage_state
    ) / te
    block.state_vars.append(field_voltage_state)
    block.state_eqs.append(field_balance)
    block.diff_vars.append(vfactory.add_diff_var(
        f'd_FieldVoltage_ExcREXS_{template_name}', base_var=field_voltage_state,
    ))
    block.init_eqs[field_voltage_state] = Const(0.0)
    rectifier_input: Expr = kc * field_current / sym.max(field_voltage_state, Const(1e-9))
    rectifier_factor: Expr = (
        (Const(1.0) - Const(0.58) * rectifier_input) * sym.heaviside(Const(0.433) - rectifier_input)
        + sym.sqrt(sym.max(Const(0.75) - rectifier_input ** Const(2.0), Const(0.0)))
        * (sym.heaviside(Const(0.75) - rectifier_input) - sym.heaviside(Const(0.433) - rectifier_input))
        + Const(1.732) * (Const(1.0) - rectifier_input)
        * (Const(1.0) - sym.heaviside(Const(0.75) - rectifier_input))
    )
    speed_gain: Expr = Const(1.0) + ks * (speed - Const(1.0))
    block.algebraic_vars.append(field_voltage_output)
    block.algebraic_eqs.append(
        field_voltage_output - speed_gain * speed * field_voltage_state * rectifier_factor,
    )
    block.init_eqs[field_voltage_output] = Const(0.0)
    block.algebraic_vars.append(feedback_signal)
    block.algebraic_eqs.append(feedback_signal - feedback_output)
    block.init_eqs[feedback_signal] = Const(0.0)
    block.out_vars.append(field_voltage_output)
    template.block = block
    template.comment = 'CGMES ExcREXS regulator, feedback, field-current loop, rotating exciter, and rectifier.'
    return template
