# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES mechanical load model type 1."""

from math import isfinite

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Expr, Var
from VeraGridEngine.enumerations import DeviceType


def build_mech_load1_template(
        vfactory: VarFactory,
        name: str | None = None,
        initial_power: float = 0.0,
) -> RmsModelTemplate:
    """Build the speed-dependent mechanical shaft-load characteristic.

    The torque curve is ``T=T0*(a*w**2+b*w+c+d*w**e)`` with
    ``c=1-a-b-d``; shaft power is ``P=T*w``. The selected coefficients
    remain mutable RDF events, and ``initial_power`` seeds the operating point
    at the standard initial speed ``w=1``.

    :param vfactory: Factory that owns the model symbols.
    :param name: Optional runtime model name.
    :param initial_power: Initial shaft power in the machine's per-unit base.
    :return: RMS template with a speed input and mechanical-power output.
    :raises ValueError: Initial power is non-finite or negative.
    """
    if isfinite(initial_power) and initial_power >= 0.0:
        pass
    else:
        raise ValueError("MechLoad1 initial power must be finite and nonnegative")

    template_name: str = "MechLoad1" if name is None else name
    template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    template.tpe = DeviceType.GeneratorDevice
    block: Block = Block(name=template_name)

    # Keep the curve coefficients as their RDF properties so the importer
    # populates precisely the values used by the torque equation.
    a: Var = vfactory.add_var(f"MechLoad1.a_{template_name}")
    b: Var = vfactory.add_var(f"MechLoad1.b_{template_name}")
    d: Var = vfactory.add_var(f"MechLoad1.d_{template_name}")
    e: Var = vfactory.add_var(f"MechLoad1.e_{template_name}")
    block.event_dict[a] = vfactory.add_const(value=None, name=a.name)
    block.event_dict[b] = vfactory.add_const(value=None, name=b.name)
    block.event_dict[d] = vfactory.add_const(value=None, name=d.name)
    block.event_dict[e] = vfactory.add_const(value=None, name=e.name)
    for parameter_name in ("enabled",):
        parameter: Var = vfactory.add_var(f"MechLoad1.{parameter_name}_{template_name}")
        block.event_dict[parameter] = vfactory.add_const(value=None, name=parameter.name)

    # At nominal speed the normalized torque curve equals one, so its seed is
    # the imported machine's initial mechanical power.
    speed: Var = vfactory.add_var("OmegaPu")
    nominal_power: Var = vfactory.add_var(f"MechLoad1.Pmech0Pu_{template_name}")
    mechanical_power: Var = vfactory.add_var("PmechPu")
    curve_constant: Expr = vfactory.add_const(value=1.0) - a - b - d
    torque_curve: Expr = (
        a * (speed ** vfactory.add_const(value=2.0))
        + b * speed
        + curve_constant
        + d * (speed ** e)
    )
    block.in_vars = list((speed,))
    block.event_dict[nominal_power] = vfactory.add_const(value=initial_power, name=nominal_power.name)
    block.algebraic_vars = list((mechanical_power,))
    block.algebraic_eqs = list((mechanical_power - nominal_power * speed * torque_curve,))
    block.out_vars = list((mechanical_power,))
    block.init_eqs[speed] = vfactory.add_const(value=1.0)
    block.init_eqs[mechanical_power] = vfactory.add_const(value=initial_power)

    template.block.children.append(block)
    template.block.in_vars = list((speed,))
    template.block.out_vars = list((mechanical_power,))
    template.block.name = template_name
    template.comment = "CGMES MechLoad1 speed-dependent shaft torque and power equations."
    return template
