# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Colib system-frequency-response and underfrequency-load-shedding template."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def get_sfrm_ufls_rms_template(
        vf: VarFactory,
        name: str = 'SFRM_UFLS',
) -> RmsModelTemplate:
    """Build Colib's aggregated frequency response with staged UFLS.

    The governor realization is algebraically equivalent to Colib's
    ``Km * (1 + Fh * Tr * s) / (R * (1 + Tr * s))`` transfer function.
    Two independently sized frequency stages provide the conventional UFLS
    feedback path; additional stages can be composed by placing this block in
    parallel with relay templates.

    :param vf: Variable factory used to allocate symbolic variables.
    :param name: Unique template instance name.
    :return: Generic RMS system-frequency-response template.
    """
    template: RmsModelTemplate = RmsModelTemplate(name=name)
    template.tpe = DeviceType.NoDevice

    imbalance: Var = vf.add_var('DeltaPPu_' + name)
    frequency: Var = vf.add_var('FrequencyPu_' + name)
    governor_memory: Var = vf.add_var('GovernorMemoryPu_' + name)
    mechanical_power: Var = vf.add_var('MechanicalPowerPu_' + name)
    shed_power: Var = vf.add_var('UflsPowerPu_' + name)

    inertia: Var = vf.add_var('H_' + name)
    damping: Var = vf.add_var('D_' + name)
    mechanical_gain: Var = vf.add_var('Km_' + name)
    droop: Var = vf.add_var('R_' + name)
    reheater_fraction: Var = vf.add_var('Fh_' + name)
    reheater_time: Var = vf.add_var('Tr_' + name)
    threshold_one: Var = vf.add_var('F1_' + name)
    threshold_two: Var = vf.add_var('F2_' + name)
    stage_one: Var = vf.add_var('Pufls1_' + name)
    stage_two: Var = vf.add_var('Pufls2_' + name)

    speed_deviation = frequency - Const(1.0)
    governor_target = -mechanical_gain * (
        reheater_fraction * speed_deviation
        + (Const(1.0) - reheater_fraction) * governor_memory
    ) / droop
    stage_one_output = stage_one * sym.heaviside(threshold_one - frequency)
    stage_two_output = stage_two * sym.heaviside(threshold_two - frequency)

    template.block = Block(
        algebraic_eqs=[
            mechanical_power - governor_target,
            shed_power - stage_one_output - stage_two_output,
        ],
        algebraic_vars=[mechanical_power, shed_power],
        state_eqs=[
            (mechanical_power - imbalance + shed_power - damping * speed_deviation)
            / (Const(2.0) * inertia),
            (speed_deviation - governor_memory) / reheater_time,
        ],
        state_vars=[frequency, governor_memory],
        in_vars=[imbalance],
        init_eqs={frequency: Const(1.0), governor_memory: Const(0.0)},
        event_dict={
            inertia: Const(5.0),
            damping: Const(1.0),
            mechanical_gain: Const(1.0),
            droop: Const(0.05),
            reheater_fraction: Const(0.3),
            reheater_time: Const(5.0),
            threshold_one: Const(0.98),
            threshold_two: Const(0.96),
            stage_one: Const(0.1),
            stage_two: Const(0.1),
        },
    )
    template.comment = 'Colib system-frequency response with two-stage conventional UFLS'
    return template
