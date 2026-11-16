# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""IEC 61400-27-1 wind-plant frequency and active-power control."""

import math
from typing import Sequence

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.template_catalogue import (
    _build_clipped_lookup_expression,
)
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.Utils.procedural_logic import gradlim_const
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def build_wind_plant_freq_pcontrol_i_e_c_template(
        vfactory: VarFactory,
        name: str | None = None,
        dprefmax: float = 999.0,
        dprefmin: float = -999.0,
        dpwprefmax: float = 999.0,
        dpwprefmin: float = -999.0,
        prefmax: float = 999.0,
        prefmin: float = -999.0,
        kiwpp: float = 0.0,
        kiwppmax: float = 999.0,
        kiwppmin: float = -999.0,
        kpwpp: float = 0.0,
        kwppref: float = 1.0,
        tpft: float = 0.0,
        tpfv: float = 0.0,
        twpffiltp: float = 0.0,
        twppfiltp: float = 0.0,
        frequency_power_curve: Sequence[tuple[float, float]] = (),
        initial_power: float = 0.0,
) -> RmsModelTemplate:
    """Build the Figure 40 frequency and active-power plant controller.

    :param vfactory: Factory allocating symbolic variables.
    :param name: Optional unique runtime model name.
    :param dprefmax: Maximum turbine-reference ramp in pu/s.
    :param dprefmin: Minimum turbine-reference ramp in pu/s.
    :param dpwprefmax: Maximum plant-reference ramp in pu/s.
    :param dpwprefmin: Minimum plant-reference ramp in pu/s.
    :param prefmax: Maximum turbine reference in pu.
    :param prefmin: Minimum turbine reference in pu.
    :param kiwpp: Plant active-power PI integral gain.
    :param kiwppmax: Maximum PI integral state in pu.
    :param kiwppmin: Minimum PI integral state in pu.
    :param kpwpp: Plant active-power PI proportional gain.
    :param kwppref: Plant reference feed-forward gain.
    :param tpft: Lead time of the reference transfer function in seconds.
    :param tpfv: Lag time of the reference transfer function in seconds.
    :param twpffiltp: Frequency measurement filter time in seconds.
    :param twppfiltp: Active-power measurement filter time in seconds.
    :param frequency_power_curve: Ordered frequency deviation/power-bias points.
    :param initial_power: Solved initial plant active power in pu.
    :return: Equation-backed model with plant and turbine active-power references.
    :raises ValueError: Invalid limits, times, or frequency lookup data.
    """
    values: tuple[float, ...] = (
        dprefmax, dprefmin, dpwprefmax, dpwprefmin, prefmax, prefmin,
        kiwpp, kiwppmax, kiwppmin, kpwpp, kwppref, tpft, tpfv,
        twpffiltp, twppfiltp, initial_power,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('CGMES wind plant frequency-control parameters must be finite')
    elif min(tpft, tpfv, twpffiltp, twppfiltp) < 0.0:
        raise ValueError('CGMES wind plant frequency-control times must be nonnegative')
    elif tpft > tpfv:
        raise ValueError('CGMES wind plant reference transfer function must be proper')
    elif prefmin > prefmax or kiwppmin > kiwppmax:
        raise ValueError('CGMES wind plant frequency-control limits are reversed')
    elif dprefmin > 0.0 or dpwprefmin > 0.0:
        raise ValueError('CGMES wind plant downward ramp rates must be nonpositive')
    elif len(frequency_power_curve) < 2:
        raise ValueError('CGMES wind plant frequency controller requires its bias curve')
    else:
        pass

    for point_index in range(len(frequency_power_curve)):
        frequency_value: float = float(frequency_power_curve[point_index][0])
        power_bias: float = float(frequency_power_curve[point_index][1])
        if not math.isfinite(frequency_value) or not math.isfinite(power_bias):
            raise ValueError('CGMES wind plant frequency lookup values must be finite')
        elif point_index > 0 and frequency_value <= float(frequency_power_curve[point_index - 1][0]):
            raise ValueError('CGMES wind plant frequency lookup inputs must increase')
        else:
            pass

    template_name: str = 'WindPlantFreqPcontrolIEC' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    plant_reference_ramp_up: Var = model.parameter('WindPlantFreqPcontrolIEC.dpwprefmax', dpwprefmax)
    plant_reference_ramp_down: Var = model.parameter('WindPlantFreqPcontrolIEC.dpwprefmin', dpwprefmin)
    turbine_reference_ramp_up: Var = model.parameter('WindPlantFreqPcontrolIEC.dprefmax', dprefmax)
    turbine_reference_ramp_down: Var = model.parameter('WindPlantFreqPcontrolIEC.dprefmin', dprefmin)
    reference_maximum: Var = model.parameter('WindPlantFreqPcontrolIEC.prefmax', prefmax)
    reference_minimum: Var = model.parameter('WindPlantFreqPcontrolIEC.prefmin', prefmin)
    integral_gain: Var = model.parameter('WindPlantFreqPcontrolIEC.kiwpp', kiwpp)
    integral_maximum: Var = model.parameter('WindPlantFreqPcontrolIEC.kiwppmax', kiwppmax)
    integral_minimum: Var = model.parameter('WindPlantFreqPcontrolIEC.kiwppmin', kiwppmin)
    proportional_gain: Var = model.parameter('WindPlantFreqPcontrolIEC.kpwpp', kpwpp)
    reference_gain: Var = model.parameter('WindPlantFreqPcontrolIEC.kwppref', kwppref)
    lead_time: Var = model.parameter('WindPlantFreqPcontrolIEC.tpft', tpft)
    lag_time: Var = model.parameter('WindPlantFreqPcontrolIEC.tpfv', tpfv)
    frequency_filter_time: Var = model.parameter('WindPlantFreqPcontrolIEC.twpffiltp', twpffiltp)
    power_filter_time: Var = model.parameter('WindPlantFreqPcontrolIEC.twppfiltp', twppfiltp)

    frequency_deviation: Var = model.input('FrequencyDeviationPu', Const(0.0))
    plant_power_measurement: Var = model.input('PlantActivePowerPu', Const(initial_power))
    plant_power_reference: Var = model.input('PlantActivePowerReferencePu', Const(initial_power))
    filtered_frequency: Var = model.lag(
        'FilteredFrequencyDeviationPu', frequency_deviation, frequency_filter_time,
        twpffiltp, Const(0.0),
    )
    filtered_power: Var = model.lag(
        'FilteredPlantActivePowerPu', plant_power_measurement, power_filter_time,
        twppfiltp, Const(initial_power),
    )

    lookup_input_variables: list[Var] = list()
    lookup_output_variables: list[Var] = list()
    for point_index in range(len(frequency_power_curve)):
        lookup_input_variables.append(model.parameter(
            f'WindPlantFreqPcontrolIEC.pwp_frequency_{point_index}',
            float(frequency_power_curve[point_index][0]),
        ))
        lookup_output_variables.append(model.parameter(
            f'WindPlantFreqPcontrolIEC.pwp_power_bias_{point_index}',
            float(frequency_power_curve[point_index][1]),
        ))
    else:
        pass
    frequency_bias: Expr = _build_clipped_lookup_expression(
        filtered_frequency,
        lookup_input_variables,
        lookup_output_variables,
    )
    plant_reference_state: Var = vfactory.add_var(f'PlantActivePowerReferenceLimitedPu_{template_name}')
    model.block.event_dict[plant_reference_state] = vfactory.add_const(value=initial_power)
    model.block.procedural_logic.append(gradlim_const(
        plant_power_reference,
        plant_reference_ramp_down,
        plant_reference_ramp_up,
        plant_reference_state,
        name=f'WindPlantFreqPcontrolIEC.PlantReferenceRamp_{template_name}',
    ))
    plant_reference_bias: Expr = reference_gain * plant_reference_state + frequency_bias
    transferred_reference: Var = model.lead_lag(
        'PlantReferenceTransfer',
        plant_reference_bias,
        lead_time,
        lag_time,
        tpft,
        tpfv,
        Const(initial_power),
    )
    reference_error: Expr = transferred_reference - filtered_power
    proportional_correction: Expr = proportional_gain * reference_error
    integral_state: Var = vfactory.add_var(f'FrequencyPIIntegralPu_{template_name}')
    pi_correction: Expr = proportional_correction + integral_state
    plant_order_unlimited: Expr = transferred_reference + pi_correction
    plant_order_limited: Var = model.algebraic(
        'PlantActivePowerOrderPu',
        sym.hard_sat(plant_order_unlimited, reference_minimum, reference_maximum),
        Const(initial_power),
    )
    turbine_reference: Var = vfactory.add_var(f'TurbineActivePowerReferencePu_{template_name}')
    model.block.event_dict[turbine_reference] = vfactory.add_const(value=initial_power)
    model.block.procedural_logic.append(gradlim_const(
        plant_order_limited,
        turbine_reference_ramp_down,
        turbine_reference_ramp_up,
        turbine_reference,
        name=f'WindPlantFreqPcontrolIEC.TurbineReferenceRamp_{template_name}',
    ))

    # Figure 40 freezes the PI integrator while the reference is held by an
    # absolute or ramp limit and its error would push farther into that limit.
    positive_pi_drive: Expr = integral_gain * reference_error
    absolute_upper_freeze: Expr = sym.heaviside(
        plant_order_unlimited - reference_maximum,
    ) * sym.heaviside(positive_pi_drive)
    absolute_lower_freeze: Expr = sym.heaviside(
        reference_minimum - plant_order_unlimited,
    ) * sym.heaviside(-positive_pi_drive)
    ramp_up_freeze: Expr = sym.heaviside(
        plant_order_limited - turbine_reference,
    ) * sym.heaviside(positive_pi_drive)
    ramp_down_freeze: Expr = sym.heaviside(
        turbine_reference - plant_order_limited,
    ) * sym.heaviside(-positive_pi_drive)
    freeze_signal: Expr = sym.max(
        sym.max(absolute_upper_freeze, absolute_lower_freeze),
        sym.max(ramp_up_freeze, ramp_down_freeze),
    )
    model.differential(
        integral_state,
        positive_pi_drive * (Const(1.0) - freeze_signal),
        Const(0.0),
        integral_minimum,
        integral_maximum,
    )

    return model.finish(
        (plant_order_limited, turbine_reference),
        'IEC 61400-27-1 WP power/frequency controller; frequency bias, PI and reference ramps',
    )
