# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Battery energy state and SOC-dependent active-power limits for REEC_C."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Reecc1BatterySettings:
    """Store the battery energy and operating bounds in per unit."""

    __slots__ = ('time_seconds', 'soc_initial', 'soc_maximum', 'soc_minimum')

    def __init__(self, time_seconds: float = 14400.0, soc_initial: float = 0.5,
                 soc_maximum: float = 1.0, soc_minimum: float = 0.0) -> None:
        """Set discharge time and initial/allowed state of charge.

        :param time_seconds: Discharge time corresponding to unit power, seconds.
        :param soc_initial: Initial state of charge in per unit.
        :param soc_maximum: Maximum allowed state of charge.
        :param soc_minimum: Minimum allowed state of charge.
        :return: None.
        """
        self.time_seconds: float = time_seconds
        self.soc_initial: float = soc_initial
        self.soc_maximum: float = soc_maximum
        self.soc_minimum: float = soc_minimum


def build_reecc1_battery_template(
        vf: VarFactory,
        name: str = 'REECC1 battery',
        settings: Reecc1BatterySettings | None = None,
) -> RmsModelTemplate:
    """Build the WECC REEC_C battery-energy state and active-power gates.

    The SOC state integrates positive generated power as discharge. At the
    upper SOC boundary charging is disabled; at the lower boundary discharge
    is disabled. The surrounding REEC_A control chain remains a separate
    assembly responsibility.

    :param vf: Shared symbolic variable factory.
    :param name: Unique battery-template name.
    :param settings: Discharge time and state-of-charge limits.
    :return: Battery block with Pgen input and SOC/current-bound outputs.
    :raises ValueError: Invalid discharge time or SOC interval.
    """
    selected: Reecc1BatterySettings = Reecc1BatterySettings() if settings is None else settings
    values: tuple[float, ...] = (
        selected.time_seconds, selected.soc_initial,
        selected.soc_maximum, selected.soc_minimum,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('REECC1 battery settings must be finite')
    elif (selected.time_seconds <= 0.0 or selected.soc_minimum < 0.0
          or selected.soc_minimum > selected.soc_initial
          or selected.soc_initial > selected.soc_maximum
          or selected.soc_maximum > 1.0):
        raise ValueError('REECC1 battery time or SOC limits are invalid')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, name)
    generated_power: Var = control.input('GeneratedPowerPu', Const(0.0))
    active_current_order: Var = control.input('ActiveCurrentOrderPu', Const(0.0))
    auxiliary_current: Var = control.input('AuxiliaryCurrentPu', Const(0.0))
    requested_pmin: Var = control.input('RequestedPminPu', Const(-1.0))
    requested_pmax: Var = control.input('RequestedPmaxPu', Const(1.0))
    time_seconds: Var = control.parameter('T', selected.time_seconds)
    soc_initial: Var = control.parameter('SOCINI', selected.soc_initial)
    soc_maximum: Var = control.parameter('SOCMAX', selected.soc_maximum)
    soc_minimum: Var = control.parameter('SOCMIN', selected.soc_minimum)
    energy_output: Var = vf.add_var('BatteryEnergyOutputPu_' + name)
    control.differential(energy_output, generated_power / time_seconds, Const(0.0))
    soc: Var = control.algebraic(
        'StateOfChargePu', soc_initial - energy_output, Const(selected.soc_initial),
    )
    at_maximum_charge: Expr = (soc >= soc_maximum).to_expression()
    at_minimum_charge: Expr = (soc <= soc_minimum).to_expression()
    initial_pmin: float = (
        0.0 if selected.soc_initial >= selected.soc_maximum else -1.0
    )
    initial_pmax: float = (
        0.0 if selected.soc_initial <= selected.soc_minimum else 1.0
    )
    lower_power_limit: Var = control.algebraic(
        'BatteryIpminPu',
        requested_pmin * (Const(1.0) - at_maximum_charge),
        Const(initial_pmin),
    )
    upper_power_limit: Var = control.algebraic(
        'BatteryIpmaxPu',
        requested_pmax * (Const(1.0) - at_minimum_charge),
        Const(initial_pmax),
    )
    active_current_command: Var = control.algebraic(
        'ActiveCurrentCommandPu',
        sym.hard_sat(active_current_order + auxiliary_current,
                     lower_power_limit, upper_power_limit),
        Const(0.0),
    )
    return control.finish(
        (soc, lower_power_limit, upper_power_limit, active_current_command),
        'WECC REEC_C battery SOC state and SOC boundary current gates',
    )
