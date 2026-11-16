# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Executable CGMES GovGAST turbine-governor model."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Templates.Rms.governors.gast import GasGovernorParameters
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def build_gov_g_a_s_t_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: GasGovernorParameters | None = None,
) -> RmsModelTemplate:
    """Build the CGMES GAST equations with exact zero-time stage bypasses.

    :param vfactory: Factory used to allocate the template parameters.
    :param name: Optional runtime model name.
    :param parameters: Parsed CGMES values used to select the zero-time topology.
    :return: Equation-backed template retaining the CGMES scalar parameter surface.
    :raises ValueError: Invalid droop, time constants, or turbine limits.
    """
    settings: GasGovernorParameters = GasGovernorParameters() if parameters is None else parameters
    template_name: str = "GovGAST" if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.r, settings.t1, settings.t2, settings.t3, settings.ambient_limit,
        settings.temperature_gain, settings.valve_max, settings.valve_min, settings.damping,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError("CGMES GovGAST parameters must be finite")
    elif settings.r <= 0.0 or min(settings.t1, settings.t2, settings.t3) < 0.0:
        raise ValueError("CGMES GovGAST droop must be positive and times nonnegative")
    elif settings.valve_min >= settings.valve_max or settings.temperature_gain < 0.0 or settings.damping < 0.0:
        raise ValueError("CGMES GovGAST limits and gains are invalid")
    else:
        pass

    template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    builder: ControlRealization = ControlRealization(vfactory, template_name)
    droop: Var = builder.parameter("R", settings.r)
    t1: Var = builder.parameter("T1", settings.t1)
    t2: Var = builder.parameter("T2", settings.t2)
    t3: Var = builder.parameter("T3", settings.t3)
    ambient: Var = builder.parameter("AT", settings.ambient_limit)
    temperature_gain: Var = builder.parameter("KT", settings.temperature_gain)
    valve_max: Var = builder.parameter("VMAX", settings.valve_max)
    valve_min: Var = builder.parameter("VMIN", settings.valve_min)
    damping: Var = builder.parameter("Dturb", settings.damping)
    speed: Var = builder.input("OmegaPu", Const(1.0))
    power_reference: Var = builder.input("PRefPu", Const(0.5))
    speed_error: Expr = (speed - Const(1.0)) / droop

    # Predeclare temperature so its zero-time algebraic bypass closes the
    # thermal feedback loop without allocating a fictitious fast state.
    temperature: Var = vfactory.add_var(name=f"ExhaustTemperaturePu_{template_name}")
    equilibrium: Expr = sym.hard_sat(
        sym.min(power_reference - speed_error, ambient),
        valve_min,
        valve_max,
    )
    thermal_demand: Expr = ambient + temperature_gain * (ambient - temperature)
    command_initial: Expr = sym.min(
        power_reference - speed_error,
        ambient + temperature_gain * (ambient - equilibrium),
    )
    demand: Var = builder.algebraic(
        "FuelDemandPu",
        sym.min(power_reference - speed_error, thermal_demand),
        command_initial,
    )
    valve: Var = builder.lag(
        "ValvePu", demand, t1, settings.t1, equilibrium, valve_min, valve_max,
    )
    fuel: Var = builder.lag("FuelFlowPu", valve, t2, settings.t2, equilibrium)

    if settings.t3 > 0.0:
        builder.differential(
            temperature,
            (fuel - temperature) / t3,
            equilibrium,
        )
    else:
        builder.block.algebraic_vars.append(temperature)
        builder.block.algebraic_eqs.append(temperature - fuel)
        builder.block.init_eqs[temperature] = equilibrium

    mechanical_power_initial: Expr = equilibrium - damping * (speed - Const(1.0))
    mechanical_power: Var = builder.algebraic(
        "PmPu",
        fuel - damping * (speed - Const(1.0)),
        mechanical_power_initial,
    )
    runtime_template: RmsModelTemplate = builder.finish(
        (mechanical_power, valve),
        "Gas-turbine governor with exhaust-temperature load limiting",
    )
    template.block.children.append(runtime_template.block)
    template.block.name = template_name
    template.comment = "CGMES GovGAST equations with exact zero-time valve, turbine, and temperature stages."

    # Preserve every RDF scalar independently from the equation symbols.
    parameter_names: tuple[str, ...] = (
        "enabled", "mwbase", "r", "t1", "t2", "t3", "at", "kt", "vmax", "vmin", "dturb",
    )
    for parameter_name in parameter_names:
        variable_name: str = f"GovGAST.{parameter_name}_{template_name}"
        parameter_variable = vfactory.add_var(variable_name)
        template.block.event_dict[parameter_variable] = vfactory.add_const(
            value=None,
            name=variable_name,
        )
    return template
