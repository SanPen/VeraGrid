# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed IEC grid-protection relays for CGMES wind turbines."""

import math
from typing import Sequence

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.template_catalogue import (
    _build_clipped_lookup_expression,
)
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.procedural_logic import (
    flipflop,
    gradlim_const,
    movingavg,
    pickup_dropoff,
    wrapped_derivative,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Comparison, Const, Expr, Var
from VeraGridEngine.enumerations import VarPowerFlowReferenceType


def _protection_delay_expression(
        model: ControlRealization,
        curve: Sequence[tuple[float, float]],
        curve_name: str,
        measured_value: Var,
) -> Expr:
    """Build a clipped IEC trip-time curve, including definite-time points.

    :param model: Runtime equation builder owning curve parameter symbols.
    :param curve: Ordered measurement/trip-time coordinates.
    :param curve_name: Stable name prefix for parameter symbols.
    :param measured_value: Measured voltage or frequency input.
    :return: Piecewise-linear delay expression in seconds.
    """
    x_variables: list[Var] = list()
    y_variables: list[Var] = list()
    point_index: int
    for point_index in range(len(curve)):
        x_variables.append(model.parameter(
            f'WindProtectionIEC.{curve_name}_input_{point_index}',
            float(curve[point_index][0]),
        ))
        y_variables.append(model.parameter(
            f'WindProtectionIEC.{curve_name}_time_{point_index}',
            float(curve[point_index][1]),
        ))
    else:
        pass
    if len(curve) == 1:
        return y_variables[0]
    else:
        return _build_clipped_lookup_expression(
            yi_var=measured_value,
            x_vars=x_variables,
            y_vars=y_variables,
        )


def build_wind_protection_i_e_c_template(
        vfactory: VarFactory,
        name: str | None = None,
        dfimax: float | None = None,
        fover: float = 1.0,
        funder: float = 1.0,
        mzc: bool = False,
        tfma: float = 0.0,
        nominal_frequency_hz: float = 50.0,
        uover: float = 1.2,
        uunder: float = 0.8,
        tuover_curve: Sequence[tuple[float, float]] = (),
        tuunder_curve: Sequence[tuple[float, float]] = (),
        tfover_curve: Sequence[tuple[float, float]] = (),
        tfunder_curve: Sequence[tuple[float, float]] = (),
) -> RmsModelTemplate:
    """Build IEC 61400-27-1:2015 Figure 39 trip relays.

    Figure 40 supplies the one-cycle voltage magnitude measurement and, when
    zero-crossing mode is disabled, the filtered phase-angle frequency estimate.

    :param vfactory: Factory allocating symbolic runtime variables.
    :param name: Optional unique runtime model name.
    :param dfimax: Maximum rate of change of frequency parameter.
    :param fover: Overfrequency pickup threshold in nominal-frequency pu.
    :param funder: Underfrequency pickup threshold in nominal-frequency pu.
    :param mzc: Selects the type-specific zero-crossing frequency method.
    :param tfma: Frequency measurement moving-average window in seconds.
    :param nominal_frequency_hz: Nominal grid frequency used by the phase estimator.
    :param uover: Overvoltage pickup threshold in pu.
    :param uunder: Undervoltage pickup threshold in pu.
    :param tuover_curve: Voltage/trip-time coordinates for overvoltage.
    :param tuunder_curve: Voltage/trip-time coordinates for undervoltage.
    :param tfover_curve: Frequency/trip-time coordinates for overfrequency.
    :param tfunder_curve: Frequency/trip-time coordinates for underfrequency.
    :return: Relay component with four trip signals and a latched breaker-open output.
    :raises ValueError: If thresholds or relay curves are invalid or missing.
    """
    if not math.isfinite(nominal_frequency_hz):
        raise ValueError('CGMES WindProtectionIEC nominal frequency must be finite')
    elif nominal_frequency_hz <= 0.0:
        raise ValueError('CGMES WindProtectionIEC nominal frequency must be positive')
    else:
        pass
    if dfimax is None:
        # The IEC recommendation is 5 Hz/s, expressed on the fn/s parameter base.
        dfimax_value: float = 5.0 / nominal_frequency_hz
    else:
        dfimax_value = dfimax

    scalar_values: tuple[float, ...] = (
        dfimax_value, fover, funder, tfma, nominal_frequency_hz, uover, uunder,
    )
    if not all(math.isfinite(value) for value in scalar_values):
        raise ValueError('CGMES WindProtectionIEC values must be finite')
    elif min(dfimax_value, tfma, uover, uunder) < 0.0 or nominal_frequency_hz <= 0.0:
        raise ValueError('CGMES WindProtectionIEC rate/time and voltage settings are invalid')
    elif funder > fover or uunder > uover:
        raise ValueError('CGMES WindProtectionIEC lower thresholds must not exceed upper thresholds')
    elif min(len(tuover_curve), len(tuunder_curve), len(tfover_curve), len(tfunder_curve)) < 1:
        raise ValueError('CGMES WindProtectionIEC requires all four trip-time curves')
    else:
        pass

    curve_groups: tuple[Sequence[tuple[float, float]], ...] = (
        tuover_curve, tuunder_curve, tfover_curve, tfunder_curve,
    )
    curve_index: int
    for curve_index in range(len(curve_groups)):
        previous_input: float | None = None
        point_index: int
        for point_index in range(len(curve_groups[curve_index])):
            input_value: float = float(curve_groups[curve_index][point_index][0])
            delay_value: float = float(curve_groups[curve_index][point_index][1])
            if not math.isfinite(input_value) or not math.isfinite(delay_value):
                raise ValueError('CGMES WindProtectionIEC curve values must be finite')
            elif delay_value < 0.0:
                raise ValueError('CGMES WindProtectionIEC trip delays must be nonnegative')
            elif previous_input is not None and input_value <= previous_input:
                raise ValueError('CGMES WindProtectionIEC curve inputs must increase')
            else:
                pass
            previous_input = input_value
        else:
            pass
    else:
        pass

    template_name: str = 'WindProtectionIEC' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    model.parameter('WindProtectionIEC.dfimax', dfimax_value)
    frequency_maximum: Var = model.parameter('WindProtectionIEC.fover', fover)
    frequency_minimum: Var = model.parameter('WindProtectionIEC.funder', funder)
    model.parameter('WindProtectionIEC.mzc', 1.0 if mzc else 0.0)
    frequency_average_window: Var = model.parameter('WindProtectionIEC.tfma', tfma)
    voltage_maximum: Var = model.parameter('WindProtectionIEC.uover', uover)
    voltage_minimum: Var = model.parameter('WindProtectionIEC.uunder', uunder)

    voltage_input: Var = model.input('UwtPu', Const(1.0))
    voltage: Var = model.parameter('WindProtectionIEC.VoltageMA', 1.0)
    model.block.procedural_logic.append(movingavg(
        input_expr=voltage_input,
        Tdel=Const(0.0),
        Tlength=Const(1.0 / nominal_frequency_hz),
        output=voltage,
        name=f'WindProtectionIEC.VoltageMA_{template_name}',
    ))
    frequency: Var
    if mzc:
        # This mode needs instantaneous voltage waveform samples, absent from the phasor RMS bus.
        frequency = model.input('FwtPu', Const(1.0))
    else:
        # The phasor mode estimates frequency from the accepted, cycle-averaged bus angle.
        phase_angle: Var = vfactory.add_var(
            name=f'Va_{template_name}',
            reference=VarPowerFlowReferenceType.Va,
        )
        model.block.in_vars.append(phase_angle)
        model.block.init_eqs[phase_angle] = Const(0.0)
        phase_angle_average: Var = model.parameter(
            'WindProtectionIEC.AngleMA', 0.0,
        )
        phase_rate: Var = model.parameter('WindProtectionIEC.PhaseRate', 0.0)
        frequency_deviation: Var = model.parameter(
            'WindProtectionIEC.FrequencyDeviationMA', 0.0,
        )
        frequency_deviation_limited: Var = model.parameter(
            'WindProtectionIEC.FrequencyDeviationLimited', 0.0,
        )
        model.block.procedural_logic.append(movingavg(
            input_expr=phase_angle,
            Tdel=Const(0.0),
            Tlength=Const(1.0 / nominal_frequency_hz),
            output=phase_angle_average,
            name=f'WindProtectionIEC.AngleMA_{template_name}',
        ))
        model.block.procedural_logic.append(wrapped_derivative(
            input_expr=phase_angle_average,
            maximum_rate_expr=None,
            output=phase_rate,
            name=f'WindProtectionIEC.PhaseRate_{template_name}',
        ))
        model.block.procedural_logic.append(gradlim_const(
            input_expr=phase_rate / Const(2.0 * math.pi * nominal_frequency_hz),
            gradmin=Const(-dfimax_value),
            gradmax=Const(dfimax_value),
            output=frequency_deviation_limited,
            name=f'WindProtectionIEC.ROCOFLimit_{template_name}',
        ))
        model.block.procedural_logic.append(movingavg(
            input_expr=frequency_deviation_limited,
            Tdel=Const(0.0),
            Tlength=frequency_average_window,
            output=frequency_deviation,
            name=f'WindProtectionIEC.FrequencyMA_{template_name}',
        ))
        frequency = model.algebraic(
            'FwtPu', Const(1.0) + frequency_deviation, Const(1.0),
        )
    delay_curves: tuple[Sequence[tuple[float, float]], ...] = (
        tuover_curve, tuunder_curve, tfover_curve, tfunder_curve,
    )
    delay_curve_names: tuple[str, ...] = ('tuover', 'tuunder', 'tfover', 'tfunder')
    measured_values: tuple[Var, ...] = (voltage, voltage, frequency, frequency)
    threshold_expressions: tuple[Expr | Comparison, ...] = (
        voltage > voltage_maximum,
        voltage < voltage_minimum,
        frequency > frequency_maximum,
        frequency < frequency_minimum,
    )
    relay_outputs: list[Var] = list()
    curve_index = 0
    for curve_index in range(len(delay_curves)):
        delay_expression: Expr = _protection_delay_expression(
            model=model,
            curve=delay_curves[curve_index],
            curve_name=delay_curve_names[curve_index],
            measured_value=measured_values[curve_index],
        )
        relay_output: Var = vfactory.add_var(
            f'{delay_curve_names[curve_index]}_trip_{template_name}',
        )
        model.block.event_dict[relay_output] = vfactory.add_const(value=0.0)
        model.block.procedural_logic.append(pickup_dropoff(
            output=relay_output,
            boolexpr=threshold_expressions[curve_index],
            Tpick=delay_expression,
            Tdrop=Const(0.0),
            name=f'WindProtectionIEC.{delay_curve_names[curve_index]}_{template_name}',
        ))
        relay_outputs.append(relay_output)
    else:
        pass

    breaker_open: Var = vfactory.add_var(f'FOCB_{template_name}')
    model.block.event_dict[breaker_open] = vfactory.add_const(value=0.0)
    model.block.procedural_logic.append(flipflop(
        boolset=relay_outputs[0] + relay_outputs[1] + relay_outputs[2] + relay_outputs[3] > Const(0.0),
        boolreset=Const(0.0),
        output=breaker_open,
        name=f'WindProtectionIEC.TripLatch_{template_name}',
    ))
    template: RmsModelTemplate = model.finish(
        (breaker_open, *relay_outputs),
        'IEC 61400-27-1:2015 Figure 39 over/undervoltage and over/underfrequency trips.',
    )
    template.comment = (
        'IEC Figure 39 relay timers and latched breaker-open output. Figure 40 '
        'cycle-averages voltage and estimates FwtPu from Va when mzc is false; '
        'zero-crossing FwtPu remains an open waveform-measurement input when mzc is true.'
    )
    return template
