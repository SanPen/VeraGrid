# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Static voltage/frequency load branch of the PSS/E CMLD model."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.enumerations import DeviceType, VarPowerFlowReferenceType


class CmldStaticLoadParameters:
    """Store the source static-load fraction and voltage/frequency coefficients."""

    __slots__ = (
        'active_power_pu', 'static_power_factor', 'motor_a_fraction',
        'motor_b_fraction', 'motor_c_fraction', 'motor_d_fraction',
        'electronic_fraction', 'p1_exponent', 'p1_coefficient',
        'p2_exponent', 'p2_coefficient', 'p_frequency_coefficient',
        'q1_exponent', 'q1_coefficient', 'q2_exponent', 'q2_coefficient',
        'q_frequency_coefficient', 'initial_voltage_pu',
    )

    def __init__(
            self,
            active_power_pu: float,
            static_power_factor: float,
            motor_a_fraction: float,
            motor_b_fraction: float,
            motor_c_fraction: float,
            motor_d_fraction: float,
            electronic_fraction: float,
            p1_exponent: float,
            p1_coefficient: float,
            p2_exponent: float,
            p2_coefficient: float,
            p_frequency_coefficient: float,
            q1_exponent: float,
            q1_coefficient: float,
            q2_exponent: float,
            q2_coefficient: float,
            q_frequency_coefficient: float,
            initial_voltage_pu: float = 1.0,
    ) -> None:
        """Store the constants needed by the source static branch.

        :param active_power_pu: Total solved active load on system base.
        :param static_power_factor: CMLD static-load power factor, lagging positive.
        :param motor_a_fraction: Source motor A fraction.
        :param motor_b_fraction: Source motor B fraction.
        :param motor_c_fraction: Source motor C fraction.
        :param motor_d_fraction: Source single-phase motor D fraction.
        :param electronic_fraction: Source electronic-load fraction.
        :param p1_exponent: Static active-power voltage exponent P1e.
        :param p1_coefficient: Static active-power voltage coefficient P1c.
        :param p2_exponent: Static active-power voltage exponent P2e.
        :param p2_coefficient: Static active-power voltage coefficient P2c.
        :param p_frequency_coefficient: Active-power frequency coefficient Pfrq.
        :param q1_exponent: Static reactive-power voltage exponent Q1e.
        :param q1_coefficient: Static reactive-power voltage coefficient Q1c.
        :param q2_exponent: Static reactive-power voltage exponent Q2e.
        :param q2_coefficient: Static reactive-power voltage coefficient Q2c.
        :param q_frequency_coefficient: Reactive-power frequency coefficient Qfrq.
        :param initial_voltage_pu: Solved voltage used by the source V/V0 law.
        """
        self.active_power_pu: float = active_power_pu
        self.static_power_factor: float = static_power_factor
        self.motor_a_fraction: float = motor_a_fraction
        self.motor_b_fraction: float = motor_b_fraction
        self.motor_c_fraction: float = motor_c_fraction
        self.motor_d_fraction: float = motor_d_fraction
        self.electronic_fraction: float = electronic_fraction
        self.p1_exponent: float = p1_exponent
        self.p1_coefficient: float = p1_coefficient
        self.p2_exponent: float = p2_exponent
        self.p2_coefficient: float = p2_coefficient
        self.p_frequency_coefficient: float = p_frequency_coefficient
        self.q1_exponent: float = q1_exponent
        self.q1_coefficient: float = q1_coefficient
        self.q2_exponent: float = q2_exponent
        self.q2_coefficient: float = q2_coefficient
        self.q_frequency_coefficient: float = q_frequency_coefficient
        self.initial_voltage_pu: float = initial_voltage_pu


def build_cmld_static_load_component(
        vf: VarFactory,
        name: str,
        parameters: CmldStaticLoadParameters,
) -> RmsModelTemplate:
    """Build CMLD's static load power law with live voltage and frequency inputs.

    PSS/E assigns the static branch the remainder of the five source fractions.
    If those fractions exceed one, the model normalizes the dynamic fractions
    and has no static branch.

    :param vf: Variable factory owning the component equations.
    :param name: Unique instance name.
    :param parameters: Solved load point and source static-load constants.
    :return: Generic component with inputs (Vm, frequency deviation) and outputs (P, Q).
    :raises ValueError: The source coefficients or solved operating point are invalid.
    """
    fractions: tuple[float, ...] = (
        parameters.motor_a_fraction, parameters.motor_b_fraction,
        parameters.motor_c_fraction, parameters.motor_d_fraction,
        parameters.electronic_fraction,
    )
    coefficients: tuple[float, ...] = (
        parameters.active_power_pu, parameters.static_power_factor,
        parameters.p1_exponent, parameters.p1_coefficient,
        parameters.p2_exponent, parameters.p2_coefficient,
        parameters.p_frequency_coefficient, parameters.q1_exponent,
        parameters.q1_coefficient, parameters.q2_exponent,
        parameters.q2_coefficient, parameters.q_frequency_coefficient,
        parameters.initial_voltage_pu,
    )
    if not all(math.isfinite(value) for value in fractions + coefficients):
        raise ValueError('CMLD static-load parameters must be finite')
    elif not all(fraction >= 0.0 for fraction in fractions):
        raise ValueError('CMLD component fractions must be nonnegative')
    elif parameters.active_power_pu < 0.0 or parameters.initial_voltage_pu <= 0.0:
        raise ValueError('CMLD active load must be nonnegative and initial voltage positive')
    elif not 0.0 < parameters.static_power_factor <= 1.0:
        raise ValueError('CMLD static power factor must lie in (0, 1]')
    else:
        pass

    component_fraction: float = sum(fractions)
    static_fraction: float = max(1.0 - component_fraction, 0.0)
    initial_active_power: float = parameters.active_power_pu * static_fraction
    initial_reactive_power: float = (
        initial_active_power
        * math.sqrt(1.0 - parameters.static_power_factor ** 2)
        / parameters.static_power_factor
    )

    control: ControlRealization = ControlRealization(vf, name)
    voltage: Var = control.input('VoltageMagnitudePu', Const(parameters.initial_voltage_pu))
    frequency_deviation: Expr
    if parameters.p_frequency_coefficient != 0.0 or parameters.q_frequency_coefficient != 0.0:
        frequency_deviation = control.input('FrequencyDeviationPu', Const(0.0))
    else:
        frequency_deviation = Const(0.0)
    normalized_voltage: Expr = voltage / Const(parameters.initial_voltage_pu)
    p3: float = 1.0 - parameters.p1_coefficient - parameters.p2_coefficient
    q3: float = 1.0 - parameters.q1_coefficient - parameters.q2_coefficient
    active_power: Expr = (
        Const(initial_active_power)
        * (Const(parameters.p1_coefficient) * normalized_voltage ** parameters.p1_exponent
           + Const(parameters.p2_coefficient) * normalized_voltage ** parameters.p2_exponent
           + Const(p3))
        * (Const(1.0) + Const(parameters.p_frequency_coefficient) * frequency_deviation)
    )
    reactive_power: Expr = (
        Const(initial_reactive_power)
        * (Const(parameters.q1_coefficient) * normalized_voltage ** parameters.q1_exponent
           + Const(parameters.q2_coefficient) * normalized_voltage ** parameters.q2_exponent
           + Const(q3))
        * (Const(1.0) + Const(parameters.q_frequency_coefficient) * frequency_deviation)
    )
    active_output: Var = control.algebraic(
        'StaticActivePowerPu', active_power, Const(initial_active_power),
    )
    reactive_output: Var = control.algebraic(
        'StaticReactivePowerPu', reactive_power, Const(initial_reactive_power),
    )
    template: RmsModelTemplate = control.finish(
        (active_output, reactive_output),
        'PSS/E CMLD static voltage- and frequency-dependent load branch.',
    )
    template.tpe = DeviceType.LoadDevice
    template.block.external_mapping = dict((
        (VarPowerFlowReferenceType.Vm, voltage),
        (VarPowerFlowReferenceType.P, active_output),
        (VarPowerFlowReferenceType.Q, reactive_output),
    ))
    return template
