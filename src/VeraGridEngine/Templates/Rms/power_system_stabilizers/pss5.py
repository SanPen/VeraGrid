# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed template for the CGMES Pss5 stabilizer."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def build_pss5_template(
        vfactory: VarFactory,
        name: str | None = None,
        kpe: float = 0.3,
        kf: float = 5.0,
        isfreq: bool = True,
        kpss: float = 1.0,
        ctw2: bool = True,
        tw1: float = 3.5,
        tw2: float = 0.0,
        tl1: float = 0.0,
        tl2: float = 0.0,
        tl3: float = 0.0,
        tl4: float = 0.0,
        vsmn: float = -0.1,
        vsmx: float = 0.1,
        tpe: float = 0.05,
        pmm: float = 0.25,
        deadband: float = 0.0,
        vadat: bool = True,
) -> RmsModelTemplate:
    """Build the Italian PSS from its CGMES EA block diagram.

    :param vfactory: Factory that allocates equation variables.
    :param name: Optional unique runtime model name.
    :param kpe: Electrical-power input gain.
    :param kf: Selected frequency/speed input gain.
    :param isfreq: Select shaft speed when true and bus frequency when false.
    :param kpss: Common stabilizer gain.
    :param ctw2: Select the second power washout branch.
    :param tw1: First power washout time.
    :param tw2: Optional second power washout time.
    :param tl1: First phase lead time.
    :param tl2: First phase lag time.
    :param tl3: Second phase lead time.
    :param tl4: Second phase lag time.
    :param vsmn: Lower speed-dependent output limit.
    :param vsmx: Upper speed-dependent output limit.
    :param tpe: Electrical-power measurement lag.
    :param pmm: Minimum power for PSS enablement.
    :param deadband: Speed deadband threshold.
    :param vadat: Enable power-derived adaptive deadband.
    :return: Standalone equation-backed PSS template with selected signal ports.
    """
    values: tuple[float, ...] = (
        kpe, kf, kpss, tw1, tw2, tl1, tl2, tl3, tl4, vsmn, vsmx,
        tpe, pmm, deadband,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('Pss5 parameters must be finite')
    elif min(tw1, tw2, tl1, tl2, tl3, tl4, tpe, deadband) < 0.0:
        raise ValueError('Pss5 times and deadband must be nonnegative')
    elif vsmn >= vsmx:
        raise ValueError('Pss5 output limits must be ordered')
    else:
        pass

    template_name: str = 'Pss5' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    electrical_power: Var = model.input('PePu', Const(0.0))
    if isfreq:
        selected_speed: Var = model.input('OmegaPu', Const(1.0))
        selected_frequency: Expr = selected_speed - Const(1.0)
    else:
        selected_bus_frequency: Var = model.input('FrequencyPu', Const(1.0))
        selected_frequency = selected_bus_frequency - Const(1.0)
    frequency_term: Expr = model.parameter('Pss5.kf', kf) * selected_frequency
    measured_power: Var = model.lag(
        'MeasuredPowerPu', electrical_power,
        model.parameter('Pss5.tpe', tpe), tpe, electrical_power,
    )
    input_sum: Expr = frequency_term + model.parameter('Pss5.kpe', kpe) * measured_power
    first_washout_time: Var = model.parameter('Pss5.tw1', tw1)
    second_washout_time: Var = model.parameter('Pss5.tw2', tw2)
    first_washout: Var
    if tw1 > 0.0:
        first_washout = model.washout(
            'Washout1Pu', input_sum, first_washout_time,
            tw1, Const(1.0), input_sum,
        )
    else:
        first_washout = model.algebraic('Washout1Pu', Const(0.0), Const(0.0))
    if not ctw2 and tw2 > 0.0:
        selected_input: Expr = model.washout(
            'Washout2Pu', first_washout, second_washout_time,
            tw2, Const(1.0), Const(0.0),
        )
    elif not ctw2:
        selected_input = Const(0.0)
    else:
        selected_input = first_washout
    phase1: Var = model.lead_lag(
        'Phase1Pu', selected_input,
        model.parameter('Pss5.tl1', tl1), model.parameter('Pss5.tl2', tl2),
        tl1, tl2, Const(0.0),
    )
    phase2: Var = model.lead_lag(
        'Phase2Pu', phase1,
        model.parameter('Pss5.tl3', tl3), model.parameter('Pss5.tl4', tl4),
        tl3, tl4, Const(0.0),
    )
    output_limit: Expr = sym.hard_sat(
        model.parameter('Pss5.kpss', kpss) * phase2,
        model.parameter('Pss5.vsmn', vsmn),
        model.parameter('Pss5.vsmx', vsmx),
    )
    power_threshold: Var = model.parameter('Pss5.pmm', pmm)
    power_gate: Expr = sym.heaviside(measured_power - power_threshold)
    power_sign: Expr = sym.safe_divide(
        measured_power, sym.abs(measured_power), Const(1.0),
    )
    adaptive_deadband: Expr = Const(0.05) * power_gate * power_sign if vadat else Const(0.0)
    adapted_output: Expr = output_limit + adaptive_deadband
    deadband_parameter: Var = model.parameter('Pss5.deadband', deadband)
    deadband_output: Expr = (
        sym.max(adapted_output - deadband_parameter, Const(0.0))
        + sym.min(adapted_output + deadband_parameter, Const(0.0))
    )
    output: Var = model.algebraic('VsPu', deadband_output, Const(0.0))
    template: RmsModelTemplate = model.finish((output,), 'CGMES Pss5 Italian stabilizer')
    template.comment = (
        'CGMES Pss5 EA1315 signal path, VADAT/Pmin power adaptation, output limits, '
        'and output deadband are represented. The EA diagram does not define a '
        'frequency-input source for installations without a connected bus-frequency signal.'
    )
    for parameter_name in ('enabled', 'isfreq', 'ctw2', 'vadat'):
        parameter_variable: Var = vfactory.add_var(f'Pss5.{parameter_name}_{template_name}')
        template.block.event_dict[parameter_variable] = vfactory.add_const(value=None)
    return template
