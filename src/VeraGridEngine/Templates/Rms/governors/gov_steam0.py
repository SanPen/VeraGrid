# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES GovSteam0 steam-turbine governor model."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class GovSteam0Parameters:
    """Physical settings for the CGMES GovSteam0 valve and turbine stages."""

    __slots__ = ("r", "t1", "vmax", "vmin", "t2", "t3", "dt")

    def __init__(
            self,
            r: float = 0.05,
            t1: float = 0.1,
            vmax: float = 1.2,
            vmin: float = 0.0,
            t2: float = 0.2,
            t3: float = 10.0,
            dt: float = 0.0,
    ) -> None:
        """Store droop, stage times, valve limits, and turbine damping.

        :param r: Positive permanent speed droop.
        :param t1: Nonnegative steam-bowl valve time constant, in seconds.
        :param vmax: Maximum valve position, in per unit.
        :param vmin: Minimum valve position, in per unit.
        :param t2: Numerator time constant of the turbine transfer, in seconds.
        :param t3: Nonnegative reheater time constant, in seconds.
        :param dt: Turbine damping coefficient, in per unit.
        """
        self.r: float = r
        self.t1: float = t1
        self.vmax: float = vmax
        self.vmin: float = vmin
        self.t2: float = t2
        self.t3: float = t3
        self.dt: float = dt


def build_gov_steam0_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: GovSteam0Parameters | None = None,
) -> RmsModelTemplate:
    """Build TGOV1 equations with exact zero-time limits for CGMES GovSteam0.

    :param vfactory: Factory used to allocate the template symbols.
    :param name: Optional runtime model name.
    :param parameters: Parsed CGMES values used to select exact stage topology.
    :return: Equation-backed template retaining all GovSteam0 scalar fields.
    :raises ValueError: Invalid droop, time, valve limits, or improper transfer.
    """
    settings: GovSteam0Parameters = GovSteam0Parameters() if parameters is None else parameters
    template_name: str = "GovSteam0" if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.r, settings.t1, settings.vmax, settings.vmin,
        settings.t2, settings.t3, settings.dt,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError("CGMES GovSteam0 parameters must be finite")
    elif settings.r <= 0.0 or min(settings.t1, settings.t2, settings.t3) < 0.0:
        raise ValueError("CGMES GovSteam0 droop must be positive and times nonnegative")
    elif settings.vmin >= settings.vmax:
        raise ValueError("CGMES GovSteam0 minimum valve limit must be below its maximum")
    elif settings.t3 == 0.0 and settings.t2 != 0.0:
        raise ValueError("CGMES GovSteam0 T3=0 requires T2=0 for a proper transfer")
    else:
        pass

    # Keep the equation variables in this CGMES template so construction can
    # remove zero-time states before the simulator sees the model.
    template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    builder: ControlRealization = ControlRealization(vfactory, template_name)
    droop: Var = builder.parameter("R", settings.r)
    t1: Var = builder.parameter("T1", settings.t1)
    valve_max: Var = builder.parameter("Vmax", settings.vmax)
    valve_min: Var = builder.parameter("Vmin", settings.vmin)
    t2: Var = builder.parameter("T2", settings.t2)
    t3: Var = builder.parameter("T3", settings.t3)
    damping: Var = builder.parameter("Dt", settings.dt)
    speed: Var = builder.input("OmegaPu", Const(1.0))
    power_reference: Var = builder.input("PRefPu", Const(0.5))

    # The droop controller requests valve power; the bounded lag realizes
    # steam-bowl dynamics or becomes an algebraic limiter when T1 is zero.
    speed_error: Expr = speed - Const(1.0)
    equilibrium: Expr = sym.hard_sat(power_reference, valve_min, valve_max)
    valve_command: Expr = sym.hard_sat(
        power_reference - speed_error / droop,
        valve_min,
        valve_max,
    )
    valve: Var = builder.lag(
        "ValvePu",
        valve_command,
        t1,
        settings.t1,
        equilibrium,
        valve_min,
        valve_max,
    )

    # TGOV1's (1+s*T2)/(1+s*T3) turbine path is represented by one reheater
    # state. Its zero-time limit is the identity only when T2 is also zero.
    if settings.t3 > 0.0:
        turbine_lag: Var = builder.lag("TurbineLagPu", valve, t3, settings.t3, equilibrium)
        turbine_power: Expr = (t2 / t3) * valve + (Const(1.0) - t2 / t3) * turbine_lag
    else:
        turbine_power = valve

    mechanical_power: Var = builder.algebraic(
        "PmPu",
        turbine_power - damping * speed_error,
        equilibrium,
    )
    runtime_template: RmsModelTemplate = builder.finish(
        (mechanical_power, valve),
        "CGMES GovSteam0 valve and reheater turbine governor",
    )
    template.block.children.append(runtime_template.block)
    template.block.name = template_name
    template.comment = "CGMES GovSteam0 equations with exact T1 and T2/T3 zero-time topology."

    # Preserve MWBASE even though it is used by the importer to establish the
    # governor reference and by the machine-chain composer for base conversion.
    parameter_names: tuple[str, ...] = (
        "enabled", "mwbase", "r", "t1", "vmax", "vmin", "t2", "t3", "dt",
    )
    for parameter_name in parameter_names:
        variable_name: str = f"GovSteam0.{parameter_name}_{template_name}"
        parameter_variable: Var = vfactory.add_var(variable_name)
        template.block.event_dict[parameter_variable] = vfactory.add_const(
            value=None,
            name=variable_name,
        )
    return template
