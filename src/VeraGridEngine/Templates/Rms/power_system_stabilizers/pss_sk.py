# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed template for the CGMES PssSK stabilizer."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def build_pss_s_k_template(
        vfactory: VarFactory,
        name: str | None = None,
        k1: float = -0.3,
        k2: float = -0.15,
        k3: float = 10.0,
        t1: float = 0.3,
        t2: float = 0.35,
        t3: float = 0.22,
        t4: float = 0.02,
        t5: float = 0.02,
        t6: float = 0.02,
        vsmax: float = 0.4,
        vsmin: float = -0.4,
) -> RmsModelTemplate:
    """Build the three-channel Slovakian PSS shown in EA1327.

    :param vfactory: Factory that allocates equation variables.
    :param name: Optional unique runtime model name.
    :param k1: Generator active-power channel gain.
    :param k2: Electrical-frequency channel gain.
    :param k3: Field-current channel gain.
    :param t1: Active-power measurement lag time.
    :param t2: Active-power washout time.
    :param t3: Frequency measurement lag time.
    :param t4: Frequency washout time.
    :param t5: Field-current measurement lag time.
    :param t6: Field-current washout time.
    :param vsmax: Upper stabilizer output limit.
    :param vsmin: Lower stabilizer output limit.
    :return: Equation-backed template with active power, frequency, and field-current ports.
    """
    values: tuple[float, ...] = (k1, k2, k3, t1, t2, t3, t4, t5, t6, vsmax, vsmin)
    if not all(math.isfinite(value) for value in values):
        raise ValueError('PssSK parameters must be finite')
    elif min(t1, t2, t3, t4, t5, t6) <= 0.005:
        raise ValueError('PssSK T1 through T6 must be greater than 0.005 seconds')
    elif vsmin >= vsmax:
        raise ValueError('PssSK output limits must be ordered')
    else:
        pass

    template_name: str = 'PssSK' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    power_input: Var = model.input('PePu', Const(0.0))
    frequency_input: Var = model.input('FrequencyDeviationPu', Const(0.0))
    field_current_input: Var = model.input('IfdPu', Const(0.0))
    power_measurement: Var = model.lag(
        'PowerMeasurementPu', power_input,
        model.parameter('PssSK.t1', t1), t1, power_input,
    )
    frequency_measurement: Var = model.lag(
        'FrequencyMeasurementPu', frequency_input,
        model.parameter('PssSK.t3', t3), t3, frequency_input,
    )
    field_current_measurement: Var = model.lag(
        'FieldCurrentMeasurementPu', field_current_input,
        model.parameter('PssSK.t5', t5), t5, field_current_input,
    )
    power_washout_time: Var = model.parameter('PssSK.t2', t2)
    frequency_washout_time: Var = model.parameter('PssSK.t4', t4)
    field_current_washout_time: Var = model.parameter('PssSK.t6', t6)
    power_washout: Var = model.washout(
        'PowerWashoutPu', power_measurement,
        power_washout_time, t2, Const(1.0), power_measurement,
    )
    frequency_washout: Var = model.washout(
        'FrequencyWashoutPu', frequency_measurement,
        frequency_washout_time, t4, Const(1.0), frequency_measurement,
    )
    field_current_washout: Var = model.washout(
        'FieldCurrentWashoutPu', field_current_measurement,
        field_current_washout_time, t6, Const(1.0), field_current_measurement,
    )
    output_sum: Expr = (
        model.parameter('PssSK.k1', k1) * power_washout
        + model.parameter('PssSK.k2', k2) * frequency_washout
        + model.parameter('PssSK.k3', k3) * field_current_washout
    )
    output: Var = model.algebraic(
        'VsPu',
        sym.hard_sat(
            output_sum,
            model.parameter('PssSK.vsmin', vsmin),
            model.parameter('PssSK.vsmax', vsmax),
        ),
        Const(0.0),
    )
    template: RmsModelTemplate = model.finish((output,), 'CGMES PssSK three-input stabilizer')
    template.comment = 'CGMES PssSK EA1327 three-channel measurement, washout, gain, and limit graph.'
    for parameter_name in ('enabled',):
        parameter_variable: Var = vfactory.add_var(f'PssSK.{parameter_name}_{template_name}')
        template.block.event_dict[parameter_variable] = vfactory.add_const(value=None)
    return template
