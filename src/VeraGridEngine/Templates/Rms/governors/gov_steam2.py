# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed IEC GovSteam2 governor template."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def build_gov_steam2_template(
        vfactory: VarFactory,
        name: str | None = None,
        t1_value: float = 0.45,
        t2_value: float = 0.0,
) -> RmsModelTemplate:
    """Build the GovSteam2 deadband, limiter, lag and turbine lead-lag equations.

    :param vfactory: Factory owning all symbolic variables.
    :param name: Optional instance name.
    :param t1_value: Construction-time branch selector for the governor lag.
    :param t2_value: Construction-time branch selector for the turbine lead.
    :return: Equation-backed model retaining the canonical GovSteam2 parameters.
    """
    template_name: str = "GovSteam2" if name is None else name
    control: ControlRealization = ControlRealization(vfactory, template_name)
    gain: Var = control.parameter("K", 20.0)
    deadband: Var = control.parameter("DBF", 0.0)
    governor_time: Var = control.parameter("T1", t1_value)
    turbine_lead: Var = control.parameter("T2", t2_value)
    maximum_power: Var = control.parameter("PMaxPu", 1.0)
    minimum_power: Var = control.parameter("PMinPu", 0.0)
    maximum_error: Var = control.parameter("MXEF", 1.0)
    minimum_error: Var = control.parameter("MNEF", -1.0)
    speed: Var = control.input("gov.omegaPu", Const(1.0))
    reference: Var = control.input("gov.PRefPu", Const(0.5))

    # IEEE/CIM speed is absolute pu; positive underspeed raises the fuel request.
    speed_error: Expr = Const(1.0) - speed
    half_deadband: Expr = deadband / Const(2.0)
    deadband_output: Expr = (
        sym.max(speed_error - half_deadband, Const(0.0))
        + sym.min(speed_error + half_deadband, Const(0.0))
    )
    speed_correction: Expr = sym.hard_sat(
        gain * deadband_output,
        minimum_error,
        maximum_error,
    )
    fuel_demand: Expr = sym.hard_sat(
        reference + speed_correction,
        minimum_power,
        maximum_power,
    )
    governor_output: Var = control.lag(
        "GovSteam2GovernorOutputPu",
        fuel_demand,
        governor_time,
        t1_value,
        reference,
        minimum_power,
        maximum_power,
    )
    if t1_value > 0.0 and t2_value > 0.0:
        turbine_lag: Var = control.lag(
            "GovSteam2TurbineLagPu",
            governor_output,
            governor_time,
            t1_value,
            reference,
        )
        lead_fraction: Expr = turbine_lead / governor_time
        turbine_output: Expr = (
            lead_fraction * governor_output
            + (Const(1.0) - lead_fraction) * turbine_lag
        )
    else:
        turbine_output = governor_output
    mechanical_power: Var = control.algebraic(
        "gov.PmPu",
        turbine_output,
        reference,
    )
    runtime_template: RmsModelTemplate = control.finish(
        (mechanical_power,),
        "CGMES GovSteam2 frequency governor and turbine lead-lag",
    )
    template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    template.tpe = runtime_template.tpe
    template.block = runtime_template.block
    template.comment = "IEC GovSteam2 equations with explicit T1 zero-time topology."

    # Keep the source RDF class parameter surface available on the standalone template.
    parameter_names: tuple[str, ...] = (
        "enabled", "k", "dbf", "t1", "t2", "pmax", "pmin", "mxef", "mnef",
    )
    for parameter_name in parameter_names:
        parameter_variable: Var = vfactory.add_var(
            f"GovSteam2.{parameter_name}_{template_name}"
        )
        template.block.event_dict[parameter_variable] = vfactory.add_const(
            value=None,
            name=parameter_variable.name,
        )
    return template
