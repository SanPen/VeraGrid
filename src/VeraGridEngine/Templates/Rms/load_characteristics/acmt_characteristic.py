# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Run and stall power characteristic for the PSS/E ACMT motor."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import CmpOp, Comparison, Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.enumerations import DeviceType, VarPowerFlowReferenceType


class AcmtCharacteristicParameters:
    """Hold the ACMT running curve and stalled-motor impedance."""

    __slots__ = (
        'power_factor', 'stall_resistance_pu', 'stall_reactance_pu',
        'kp1', 'np1', 'kq1', 'nq1', 'kp2',
        'np2', 'kq2', 'nq2', 'breakdown_voltage_pu',
        'active_frequency_coefficient', 'reactive_frequency_coefficient',
    )

    def __init__(
            self,
            power_factor: float,
            stall_resistance_pu: float,
            stall_reactance_pu: float,
            kp1: float,
            np1: float,
            kq1: float,
            nq1: float,
            kp2: float,
            np2: float,
            kq2: float,
            nq2: float,
            breakdown_voltage_pu: float,
            active_frequency_coefficient: float = 0.0,
            reactive_frequency_coefficient: float = 0.0,
    ) -> None:
        """Store the ACMT equations' required constants.

        :param power_factor: Running compressor power factor at nominal voltage.
        :param stall_resistance_pu: Stall resistance on motor MVA base.
        :param stall_reactance_pu: Unsaturated stall reactance on motor MVA base.
        :param kp1: Active-power coefficient above breakdown voltage.
        :param np1: Active-power exponent above breakdown voltage.
        :param kq1: Reactive-power coefficient above breakdown voltage.
        :param nq1: Reactive-power exponent above breakdown voltage.
        :param kp2: Active-power coefficient below breakdown voltage while running.
        :param np2: Active-power exponent below breakdown voltage while running.
        :param kq2: Reactive-power coefficient below breakdown voltage while running.
        :param nq2: Reactive-power exponent below breakdown voltage while running.
        :param breakdown_voltage_pu: Load-adjusted running-curve breakpoint.
        :param active_frequency_coefficient: Active-power frequency slope.
        :param reactive_frequency_coefficient: Reactive-power frequency slope.
        """
        self.power_factor: float = power_factor
        self.stall_resistance_pu: float = stall_resistance_pu
        self.stall_reactance_pu: float = stall_reactance_pu
        self.kp1: float = kp1
        self.np1: float = np1
        self.kq1: float = kq1
        self.nq1: float = nq1
        self.kp2: float = kp2
        self.np2: float = np2
        self.kq2: float = kq2
        self.nq2: float = nq2
        self.breakdown_voltage_pu: float = breakdown_voltage_pu
        self.active_frequency_coefficient: float = active_frequency_coefficient
        self.reactive_frequency_coefficient: float = reactive_frequency_coefficient


def build_acmt_power_characteristic(
        vf: VarFactory,
        name: str,
        parameters: AcmtCharacteristicParameters,
) -> RmsModelTemplate:
    """Build ACMT P/Q curves for host-provided voltage, frequency and run state.

    The input ``Running`` selects the published compressor curve or its
    ``Rstall + j Xstall`` impedance. Timers, protection logic and state changes
    belong to the composite host and are deliberately not inferred here.

    :param vf: Variable factory owning this component's symbolic variables.
    :param name: Unique component instance name.
    :param parameters: Source coefficients with load-factor voltage adjustment applied.
    :return: Load component with P/Q in motor-MVA-base per-unit.
    :raises ValueError: If a source coefficient is nonfinite or inconsistent.
    """
    coefficients: tuple[float, ...] = (
        parameters.power_factor, parameters.stall_resistance_pu,
        parameters.stall_reactance_pu,
        parameters.kp1, parameters.np1, parameters.kq1, parameters.nq1,
        parameters.kp2, parameters.np2, parameters.kq2, parameters.nq2,
        parameters.breakdown_voltage_pu,
        parameters.active_frequency_coefficient,
        parameters.reactive_frequency_coefficient,
    )
    if not all(math.isfinite(value) for value in coefficients):
        raise ValueError('ACMT characteristic parameters must be finite')
    elif not 0.0 < parameters.power_factor <= 1.0:
        raise ValueError('ACMT running power factor must lie in (0, 1]')
    elif parameters.breakdown_voltage_pu <= 0.0:
        raise ValueError('ACMT breakdown voltage must be positive')
    elif parameters.stall_resistance_pu <= 0.0 or parameters.stall_reactance_pu < 0.0:
        raise ValueError('ACMT stall impedance must have positive resistance and nonnegative reactance')
    elif min(parameters.np1, parameters.nq1, parameters.np2, parameters.nq2) <= 0.0:
        raise ValueError('ACMT voltage exponents must be positive')
    elif parameters.power_factor == 1.0 and parameters.reactive_frequency_coefficient != 0.0:
        raise ValueError('ACMT reactive frequency response is singular at unity power factor')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, name)
    voltage: Var = control.input('VoltageMagnitudePu', Const(1.0))
    frequency_deviation: Var = control.input('FrequencyDeviationPu', Const(0.0))
    running: Var = control.input('Running', Const(1.0))
    breakdown: Const = Const(parameters.breakdown_voltage_pu)
    above_breakdown: Expr = Comparison(
        voltage, CmpOp.GE, breakdown,
    ).to_expression()
    below_breakdown: Expr = Const(1.0) - above_breakdown

    # The two exponential sections meet at breakdown voltage by construction.
    p_at_breakdown: float = 1.0 - parameters.kp1 * (
        1.0 - parameters.breakdown_voltage_pu
    ) ** parameters.np1
    q_at_breakdown: float = (
        math.sqrt(1.0 - parameters.power_factor ** 2) / parameters.power_factor
        - parameters.kq1 * (1.0 - parameters.breakdown_voltage_pu) ** parameters.nq1
    )
    p_running: Expr = (
        Const(p_at_breakdown)
        + Const(parameters.kp1)
        * sym.max(voltage - breakdown, Const(0.0)) ** parameters.np1
    ) * above_breakdown + (
        Const(p_at_breakdown)
        + Const(parameters.kp2)
        * sym.max(breakdown - voltage, Const(0.0)) ** parameters.np2
    ) * below_breakdown
    q_running: Expr = (
        Const(q_at_breakdown)
        + Const(parameters.kq1)
        * sym.max(voltage - breakdown, Const(0.0)) ** parameters.nq1
    ) * above_breakdown + (
        Const(q_at_breakdown)
        + Const(parameters.kq2)
        * sym.max(breakdown - voltage, Const(0.0)) ** parameters.nq2
    ) * below_breakdown

    impedance_denominator: float = (
        parameters.stall_resistance_pu ** 2 + parameters.stall_reactance_pu ** 2
    )
    voltage_squared: Expr = voltage ** 2
    p_stalled: Expr = (
        voltage_squared * Const(parameters.stall_resistance_pu / impedance_denominator)
    )
    q_stalled: Expr = (
        voltage_squared * Const(parameters.stall_reactance_pu / impedance_denominator)
    )
    running_power: Expr = (
        running * p_running + (Const(1.0) - running) * p_stalled
    )
    running_reactive: Expr = (
        running * q_running + (Const(1.0) - running) * q_stalled
    )
    active_power: Expr = running_power * (
        Const(1.0)
        + Const(parameters.active_frequency_coefficient) * frequency_deviation
    )
    if parameters.reactive_frequency_coefficient == 0.0:
        reactive_frequency_factor: Expr = Const(1.0)
    else:
        reactive_frequency_factor = Const(1.0) + (
            Const(parameters.reactive_frequency_coefficient)
            * frequency_deviation
            / Const(math.sqrt(1.0 - parameters.power_factor ** 2))
        )
    active_output: Var = control.algebraic(
        'ActivePowerPu', active_power, Const(1.0),
    )
    reactive_output: Var = control.algebraic(
        'ReactivePowerPu', running_reactive * reactive_frequency_factor,
        Const(math.sqrt(1.0 - parameters.power_factor ** 2) / parameters.power_factor),
    )
    template: RmsModelTemplate = control.finish(
        (active_output, reactive_output),
        'PSS/E ACMT running power curve and stalled-motor impedance characteristic.',
    )
    template.tpe = DeviceType.LoadDevice
    template.block.external_mapping = dict((
        (VarPowerFlowReferenceType.Vm, voltage),
        (VarPowerFlowReferenceType.P, active_output),
        (VarPowerFlowReferenceType.Q, reactive_output),
    ))
    return template
