# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Continuous-time equations for the CGMES PssPTIST3 stabilizer."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss_pti_tap_selection import (
    build_pti_tap_selection_expression,
)
from VeraGridEngine.Templates.Rms.power_system_stabilizers.ieeest import (
    polynomial_measurement_filter,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.Utils.procedural_logic import PeriodicSampleLogic, PssPTIST3SampledOutputLogic
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class PssPTIST3Parameters:
    """CGMES PssPTIST3 fields used by its continuous and sampled stages."""

    __slots__ = (
        'm', 'tf', 'tp', 't1', 't2', 't3', 't4', 'k', 'dtf', 'dtc', 'dtp',
        't5', 't6', 'a0', 'a1', 'a2', 'b0', 'b1', 'b2', 'a3', 'a4', 'a5',
        'b3', 'b4', 'b5', 'athres', 'dl', 'al', 'lthres', 'pmin', 'isw',
        'nav', 'ncl', 'ncr',
    )

    def __init__(
            self,
            m: float = 0.0,
            tf: float = 0.0,
            tp: float = 0.0,
            t1: float = 0.0,
            t2: float = 0.0,
            t3: float = 0.0,
            t4: float = 0.0,
            k: float = 0.0,
            dtf: float = 0.0,
            dtc: float = 0.0,
            dtp: float = 0.0,
            t5: float = 0.0,
            t6: float = 0.0,
            a0: float = 1.0,
            a1: float = 0.0,
            a2: float = 0.0,
            b0: float = 1.0,
            b1: float = 0.0,
            b2: float = 0.0,
            a3: float = 1.0,
            a4: float = 0.0,
            a5: float = 0.0,
            b3: float = 1.0,
            b4: float = 0.0,
            b5: float = 0.0,
            athres: float = 0.0,
            dl: float = 0.0,
            al: float = 0.0,
            lthres: float = 0.0,
            pmin: float = 0.0,
            isw: bool = False,
            nav: float = 0.0,
            ncl: float = 0.0,
            ncr: float = 0.0,
    ) -> None:
        """Store all imported parameters without changing their RDF values.

        :param m: Speed-washout gain.
        :param tf: Speed-washout time constant.
        :param tp: Electrical-power measurement time constant.
        :param t1: First phase lead time.
        :param t2: First phase lag time.
        :param t3: Second phase lead time.
        :param t4: Second phase lag time.
        :param k: Stabilizer gain.
        :param dtf: Speed-filter sampling period.
        :param dtc: Controller sampling period.
        :param dtp: Power-filter sampling period.
        :param t5: Final filter numerator time constant.
        :param t6: Final filter denominator time constant.
        :param a0: First measurement-filter numerator constant.
        :param a1: First measurement-filter numerator linear coefficient.
        :param a2: First measurement-filter numerator quadratic coefficient.
        :param b0: First measurement-filter denominator constant.
        :param b1: First measurement-filter denominator linear coefficient.
        :param b2: First measurement-filter denominator quadratic coefficient.
        :param a3: Second measurement-filter numerator constant.
        :param a4: Second measurement-filter numerator linear coefficient.
        :param a5: Second measurement-filter numerator quadratic coefficient.
        :param b3: Second measurement-filter denominator constant.
        :param b4: Second measurement-filter denominator linear coefficient.
        :param b5: Second measurement-filter denominator quadratic coefficient.
        :param athres: Averaging-function threshold.
        :param dl: Digital limiter decrement.
        :param al: Analog output limit.
        :param lthres: Limiter threshold.
        :param pmin: Minimum active-power gate.
        :param isw: Selects the analog output path when true.
        :param nav: Number of averaging samples.
        :param ncl: Negative tap-count limit.
        :param ncr: Positive tap-count limit.
        """
        self.m: float = m
        self.tf: float = tf
        self.tp: float = tp
        self.t1: float = t1
        self.t2: float = t2
        self.t3: float = t3
        self.t4: float = t4
        self.k: float = k
        self.dtf: float = dtf
        self.dtc: float = dtc
        self.dtp: float = dtp
        self.t5: float = t5
        self.t6: float = t6
        self.a0: float = a0
        self.a1: float = a1
        self.a2: float = a2
        self.b0: float = b0
        self.b1: float = b1
        self.b2: float = b2
        self.a3: float = a3
        self.a4: float = a4
        self.a5: float = a5
        self.b3: float = b3
        self.b4: float = b4
        self.b5: float = b5
        self.athres: float = athres
        self.dl: float = dl
        self.al: float = al
        self.lthres: float = lthres
        self.pmin: float = pmin
        self.isw: bool = isw
        self.nav: float = nav
        self.ncl: float = ncl
        self.ncr: float = ncr


def build_pss_p_t_i_s_t3_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: PssPTIST3Parameters | None = None,
) -> RmsModelTemplate:
    """Build the continuous PssPTIST3 chain and expose sampled stages.

    :param vfactory: Factory allocating equation and parameter symbols.
    :param name: Optional unique runtime model name.
    :param parameters: Parsed canonical PssPTIST3 fields.
    :return: Continuous stabilizer graph with explicit averaging and tap inputs.
    :raises ValueError: Invalid coefficient constants, times, or phase stages.
    """
    settings: PssPTIST3Parameters = PssPTIST3Parameters() if parameters is None else parameters
    numeric_values: tuple[float, ...] = (
        settings.m, settings.tf, settings.tp, settings.t1, settings.t2, settings.t3,
        settings.t4, settings.k, settings.dtf, settings.dtc, settings.dtp, settings.t5,
        settings.t6, settings.a0, settings.a1, settings.a2, settings.b0, settings.b1,
        settings.b2, settings.a3, settings.a4, settings.a5, settings.b3, settings.b4,
        settings.b5, settings.athres, settings.dl, settings.al, settings.lthres,
        settings.pmin, settings.nav, settings.ncl, settings.ncr,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('PssPTIST3 numeric parameters must be finite')
    elif min(settings.tf, settings.tp, settings.t1, settings.t2, settings.t3,
             settings.t4, settings.dtf, settings.dtc, settings.dtp, settings.t5,
             settings.t6) < 0.0:
        raise ValueError('PssPTIST3 filter times must be nonnegative')
    elif settings.b0 == 0.0 or settings.b3 == 0.0:
        raise ValueError('PssPTIST3 measurement filter denominator constants must be nonzero')
    elif settings.a0 == 0.0 or settings.a3 == 0.0:
        raise ValueError('PssPTIST3 measurement filter numerator constants must be nonzero')
    elif settings.pmin < 0.0:
        raise ValueError('PssPTIST3 minimum active power must be nonnegative')
    elif settings.nav < 0.0 or settings.nav > 16.0 or not settings.nav.is_integer():
        raise ValueError('PssPTIST3 nav must be an integer from one to sixteen, or zero when omitted')
    elif (
            settings.ncl < 0.0 or settings.ncr < 0.0
            or not settings.ncl.is_integer() or not settings.ncr.is_integer()
    ):
        raise ValueError('PssPTIST3 ncl and ncr must be nonnegative integer counts')
    elif settings.athres < 0.0 or settings.lthres < 0.0:
        raise ValueError('PssPTIST3 thresholds must be nonnegative')
    elif settings.dl < 0.0 or settings.al < 0.0:
        raise ValueError('PssPTIST3 digital and analog limits must be nonnegative')
    elif ((settings.t2 == 0.0 and settings.t1 > 0.0)
          or (settings.t4 == 0.0 and settings.t3 > 0.0)
          or (settings.t6 == 0.0 and settings.t5 > 0.0)):
        raise ValueError('PssPTIST3 lead times require nonzero corresponding lag times')
    else:
        pass

    template_name: str = 'PssPTIST3' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    isw_mode: Var = vfactory.add_var(f'PssPTIST3.isw_{template_name}')
    model.block.event_dict[isw_mode] = vfactory.add_const(value=settings.isw)
    a0: Var = model.parameter('PssPTIST3.a0', settings.a0)
    a1: Var = model.parameter('PssPTIST3.a1', settings.a1)
    a2: Var = model.parameter('PssPTIST3.a2', settings.a2)
    b0: Var = model.parameter('PssPTIST3.b0', settings.b0)
    b1: Var = model.parameter('PssPTIST3.b1', settings.b1)
    b2: Var = model.parameter('PssPTIST3.b2', settings.b2)
    a3: Var = model.parameter('PssPTIST3.a3', settings.a3)
    a4: Var = model.parameter('PssPTIST3.a4', settings.a4)
    a5: Var = model.parameter('PssPTIST3.a5', settings.a5)
    b3: Var = model.parameter('PssPTIST3.b3', settings.b3)
    b4: Var = model.parameter('PssPTIST3.b4', settings.b4)
    b5: Var = model.parameter('PssPTIST3.b5', settings.b5)
    speed_deviation: Var = model.input('OmegaPu', Const(0.0))
    electrical_power: Var = model.input('PePu', Const(0.0))
    terminal_voltage: Var = model.input('VtPu', Const(1.0))
    sampled_speed: Var = speed_deviation
    if settings.dtf > 0.0:
        sampled_speed = vfactory.add_var(f'SampledOmegaPu_{template_name}')
        model.block.mode_dict[sampled_speed] = Const(0.0)
        model.block.procedural_logic.append(PeriodicSampleLogic(
            output_var_name=sampled_speed.name,
            output_var_uid=sampled_speed.uid,
            source_expr=speed_deviation,
            sample_period=settings.dtf,
            name=f'PssPTIST3.SpeedSample_{template_name}',
        ))
    else:
        pass
    sampled_power: Var = electrical_power
    if settings.dtp > 0.0:
        sampled_power = vfactory.add_var(f'SampledPePu_{template_name}')
        model.block.mode_dict[sampled_power] = Const(0.0)
        model.block.procedural_logic.append(PeriodicSampleLogic(
            output_var_name=sampled_power.name,
            output_var_uid=sampled_power.uid,
            source_expr=electrical_power,
            sample_period=settings.dtp,
            name=f'PssPTIST3.PowerSample_{template_name}',
        ))
    else:
        pass
    sampled_limiter_output: Var = vfactory.add_var(f'SampledLimitedSignalPu_{template_name}')
    model.block.mode_dict[sampled_limiter_output] = Const(0.0)
    minimum_power: Var = model.parameter('PssPTIST3.pmin', settings.pmin)
    power_enable_initial: float = 1.0 if settings.pmin == 0.0 else 0.0
    power_enable: Var = model.algebraic(
        'PowerEnablePu',
        Const(1.0) - sym.heaviside(minimum_power - electrical_power),
        Const(power_enable_initial),
    )
    enabled_limiter_output: Var = model.algebraic(
        'EnabledLimitedSignalPu', power_enable * sampled_limiter_output,
        Const(0.0),
    )
    tap_selection: Var = model.algebraic(
        'TapSelectionPu',
        build_pti_tap_selection_expression(
            sym.hard_sat(enabled_limiter_output, Const(-settings.dl), Const(settings.dl))
            if settings.dl > 0.0 else enabled_limiter_output
        ),
        Const(0.0),
    )

    if settings.tf > 0.0:
        speed_path: Var = model.washout(
            'SpeedWashoutPu', sampled_speed,
            model.parameter('PssPTIST3.tf', settings.tf), settings.tf,
            model.parameter('PssPTIST3.m', settings.m), Const(0.0),
        )
    else:
        speed_path = model.algebraic('SpeedWashoutPu', Const(0.0), Const(0.0))
    measured_power: Var = model.lag(
        'MeasuredPowerPu', sampled_power,
        model.parameter('PssPTIST3.tp', settings.tp), settings.tp, sampled_power,
    )
    combined_signal: Var = model.algebraic(
        'CombinedSignalPu', speed_path + measured_power - electrical_power, Const(0.0),
    )
    first_phase: Var = model.lead_lag(
        'FirstPhasePu', combined_signal * model.parameter('PssPTIST3.k', settings.k),
        model.parameter('PssPTIST3.t1', settings.t1),
        model.parameter('PssPTIST3.t2', settings.t2), settings.t1, settings.t2, Const(0.0),
    )
    second_phase: Var = model.lead_lag(
        'SecondPhasePu', first_phase,
        model.parameter('PssPTIST3.t3', settings.t3),
        model.parameter('PssPTIST3.t4', settings.t4), settings.t3, settings.t4, Const(0.0),
    )
    normalized_first: Var = polynomial_measurement_filter(
        builder=model,
        signal=second_phase,
        coefficients=(settings.b1 / settings.b0, settings.b2 / settings.b0, 0.0, 0.0,
                      settings.a1 / settings.a0, settings.a2 / settings.a0),
        prefix='FirstMeasurement',
    )
    first_filter_coefficients: tuple[tuple[str, Expr], ...] = (
        ('FirstMeasurementA1', b1 / b0), ('FirstMeasurementA2', b2 / b0),
        ('FirstMeasurementA3', Const(0.0)), ('FirstMeasurementA4', Const(0.0)),
        ('FirstMeasurementA5', a1 / a0), ('FirstMeasurementA6', a2 / a0),
    )
    for coefficient_name, coefficient_expression in first_filter_coefficients:
        coefficient_variable: Var | None = None
        coefficient_variable_name: str = f'{coefficient_name}_{template_name}'
        for event_variable in model.block.event_dict:
            if event_variable.name == coefficient_variable_name:
                coefficient_variable = event_variable
            else:
                pass
        if coefficient_variable is not None:
            model.block.event_dict[coefficient_variable] = coefficient_expression
        else:
            raise ValueError('PssPTIST3 first measurement coefficient is missing: ' + coefficient_name)
    first_measurement: Var = model.algebraic(
        'FirstMeasurementGainPu', normalized_first * (a0 / b0),
        Const(0.0),
    )
    normalized_second: Var = polynomial_measurement_filter(
        builder=model,
        signal=first_measurement,
        coefficients=(settings.b4 / settings.b3, settings.b5 / settings.b3, 0.0, 0.0,
                      settings.a4 / settings.a3, settings.a5 / settings.a3),
        prefix='SecondMeasurement',
    )
    second_filter_coefficients: tuple[tuple[str, Expr], ...] = (
        ('SecondMeasurementA1', b4 / b3), ('SecondMeasurementA2', b5 / b3),
        ('SecondMeasurementA3', Const(0.0)), ('SecondMeasurementA4', Const(0.0)),
        ('SecondMeasurementA5', a4 / a3), ('SecondMeasurementA6', a5 / a3),
    )
    for coefficient_name, coefficient_expression in second_filter_coefficients:
        coefficient_variable = None
        coefficient_variable_name = f'{coefficient_name}_{template_name}'
        for event_variable in model.block.event_dict:
            if event_variable.name == coefficient_variable_name:
                coefficient_variable = event_variable
            else:
                pass
        if coefficient_variable is not None:
            model.block.event_dict[coefficient_variable] = coefficient_expression
        else:
            raise ValueError('PssPTIST3 second measurement coefficient is missing: ' + coefficient_name)
    controller_signal: Var = model.algebraic(
        'ControllerSignalPu', normalized_second * (a3 / b3), Const(0.0),
    )
    filtered_output: Var = model.lead_lag(
        'OutputFilterPu', controller_signal,
        model.parameter('PssPTIST3.t5', settings.t5),
        model.parameter('PssPTIST3.t6', settings.t6), settings.t5, settings.t6, Const(0.0),
    )
    analog_output: Var = model.algebraic(
        'AnalogOutputPu',
        sym.hard_sat(enabled_limiter_output, Const(-settings.al), Const(settings.al))
        if settings.al > 0.0 else enabled_limiter_output,
        Const(0.0),
    )
    digital_output: Var = model.algebraic(
        'DigitalOutputPu', terminal_voltage * (Const(1.0) + tap_selection), terminal_voltage,
    )
    output_initial: float = 0.0 if settings.isw else 1.0
    output: Var = model.algebraic(
        'VsPu', isw_mode * analog_output + (Const(1.0) - isw_mode) * digital_output,
        Const(output_initial),
    )
    average_count: int = 1 if settings.nav == 0.0 else int(settings.nav)
    sample_period: float | None = settings.dtc if settings.dtc > 0.0 else None
    model.block.procedural_logic.append(PssPTIST3SampledOutputLogic(
        output_var_name=sampled_limiter_output.name,
        output_var_uid=sampled_limiter_output.uid,
        source_expr=filtered_output * power_enable,
        sample_period=sample_period,
        average_count=average_count,
        average_threshold=settings.athres,
        limit_threshold=settings.lthres,
        limit_count=int(settings.ncl),
        reset_count=int(settings.ncr),
        name=f'PssPTIST3.SampledAverageAndLimit_{template_name}',
    ))
    template: RmsModelTemplate = model.finish(
        (output, filtered_output), 'CGMES PssPTIST3 continuous stabilizer',
    )
    template.comment = (
        'Continuous speed/power filters, phase compensation, measurement filters and output filter '
        'follow EA1321. Isw selects the limited analogue output or terminal voltage multiplied by '
        'the tap ratio from IEC 61970-302 Figure 151. Its 13-bin tap-selection table is evaluated '
        'from the internally sampled output after NAV averaging and NCL/NCR limit handling. Pmin disables '
        'stabilizer action below electrical power on the generator MBASE, matching the PTIST3 '
        'model-library behavior. Positive dtf and dtp sample frequency and active power, while '
        'dtc samples the discrete controller/limiter output. The 2023 draft describes dtp as a '
        'moving-average window, whereas the 2.4.15 Dynamics profile defines all three as time '
        'steps; this builder follows the 2.4.15 parameter semantics. The '
        'The controller-click logic follows the PSS/E 35.2 PTIST3 tap averaging and '
        'time-at-limit description: ATHRES bypasses and clears the NAV ring; NCL consecutive '
        'over-limit clicks trigger a ramp to neutral over NCR clicks.'
    )
    parameter_values: tuple[tuple[str, float | bool | None], ...] = (
        ('enabled', None),
        ('m', settings.m), ('tf', settings.tf), ('tp', settings.tp),
        ('t1', settings.t1), ('t2', settings.t2), ('t3', settings.t3),
        ('t4', settings.t4), ('k', settings.k), ('dtf', settings.dtf),
        ('dtc', settings.dtc), ('dtp', settings.dtp), ('t5', settings.t5),
        ('t6', settings.t6), ('a0', settings.a0), ('a1', settings.a1),
        ('a2', settings.a2), ('b0', settings.b0), ('b1', settings.b1),
        ('b2', settings.b2), ('a3', settings.a3), ('a4', settings.a4),
        ('a5', settings.a5), ('b3', settings.b3), ('b4', settings.b4),
        ('b5', settings.b5), ('athres', settings.athres), ('dl', settings.dl),
        ('al', settings.al), ('lthres', settings.lthres), ('pmin', settings.pmin),
        ('nav', settings.nav), ('ncl', settings.ncl), ('ncr', settings.ncr),
    )
    for parameter_name, parameter_value in parameter_values:
        parameter_variable_name: str = f'PssPTIST3.{parameter_name}_{template_name}'
        parameter_exists: bool = any(
            event_variable.name == parameter_variable_name
            for event_variable in template.block.event_dict
        )
        if not parameter_exists:
            parameter_variable: Var = vfactory.add_var(parameter_variable_name)
            template.block.event_dict[parameter_variable] = vfactory.add_const(value=parameter_value)
        else:
            pass
    return template
