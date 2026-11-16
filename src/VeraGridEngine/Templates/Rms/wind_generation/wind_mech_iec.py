# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES IEC two-mass wind drivetrain component."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class WindMechIECParameters:
    """Store the four canonical IEC drivetrain parameters."""

    __slots__ = ('cdrt', 'hgen', 'hwtr', 'kdrt')

    def __init__(
            self,
            cdrt: float = 0.0,
            hgen: float = 1.0,
            hwtr: float = 1.0,
            kdrt: float = 1.0,
    ) -> None:
        """Set drivetrain damping, inertias, and stiffness.

        :param cdrt: Shaft damping in pu torque per pu speed deviation.
        :param hgen: Generator inertia constant in seconds.
        :param hwtr: Wind-turbine-rotor inertia constant in seconds.
        :param kdrt: Shaft stiffness in pu torque per relative rotor angle.
        """
        self.cdrt: float = cdrt
        self.hgen: float = hgen
        self.hwtr: float = hwtr
        self.kdrt: float = kdrt


def build_wind_mech_i_e_c_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: WindMechIECParameters | None = None,
        initial_power: float = 0.0,
) -> RmsModelTemplate:
    """Build the IEC two-mass turbine and generator shaft equations.

    The model converts aerodynamic and air-gap power to torque at each shaft
    speed, couples the two inertias through the spring-damper shaft, and exposes
    the resulting mechanical torque and both speeds for parent-block wiring.

    :param vfactory: Factory allocating the model symbols.
    :param name: Optional unique runtime template name.
    :param parameters: Canonical CGMES drivetrain coefficients.
    :param initial_power: Solved per-unit air-gap/mechanical power.
    :return: Equation-backed drivetrain with explicit power inputs and torque output.
    :raises ValueError: Invalid inertia, shaft coefficients, or initial power.
    """
    settings: WindMechIECParameters = (
        WindMechIECParameters() if parameters is None else parameters
    )
    parameter_values: tuple[float, ...] = (
        settings.cdrt, settings.hgen, settings.hwtr, settings.kdrt, initial_power,
    )
    if not all(math.isfinite(value) for value in parameter_values):
        raise ValueError('CGMES WindMechIEC values must be finite')
    elif settings.cdrt < 0.0 or settings.kdrt <= 0.0:
        raise ValueError('CGMES WindMechIEC requires nonnegative damping and positive stiffness')
    elif settings.hgen <= 0.0 or settings.hwtr <= 0.0:
        raise ValueError('CGMES WindMechIEC requires positive generator and turbine inertia')
    elif initial_power < 0.0:
        raise ValueError('CGMES WindMechIEC initial generating power must be nonnegative')
    else:
        pass

    template_name: str = 'WindMechIEC' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    cdrt: Var = model.parameter('WindMechIEC.cdrt', settings.cdrt)
    hgen: Var = model.parameter('WindMechIEC.hgen', settings.hgen)
    hwtr: Var = model.parameter('WindMechIEC.hwtr', settings.hwtr)
    kdrt: Var = model.parameter('WindMechIEC.kdrt', settings.kdrt)
    aerodynamic_power: Var = model.input('PaeroPu', Const(initial_power))
    air_gap_power: Var = model.input('PagPu', Const(initial_power))
    turbine_speed: Var = vfactory.add_var(f'OmegaWtrPu_{template_name}')
    generator_speed: Var = vfactory.add_var(f'OmegaGenPu_{template_name}')
    shaft_twist: Var = vfactory.add_var(f'ShaftTwistPu_{template_name}')
    initial_speed: Const = Const(1.0)
    initial_twist: Expr = Const(initial_power / settings.kdrt)
    relative_speed: Expr = turbine_speed - generator_speed
    shaft_torque: Var = model.algebraic(
        'TshaftPu',
        kdrt * shaft_twist + cdrt * relative_speed,
        Const(initial_power),
    )
    turbine_torque: Expr = sym.safe_divide(
        aerodynamic_power,
        turbine_speed,
        Const(1.0),
    )
    generator_torque: Expr = sym.safe_divide(
        air_gap_power,
        generator_speed,
        Const(1.0),
    )
    model.differential(
        turbine_speed,
        (turbine_torque - shaft_torque) / (Const(2.0) * hwtr),
        initial_speed,
    )
    model.differential(
        generator_speed,
        (shaft_torque - generator_torque) / (Const(2.0) * hgen),
        initial_speed,
    )
    model.differential(shaft_twist, relative_speed, initial_twist)
    template: RmsModelTemplate = model.finish(
        (shaft_torque, turbine_speed, generator_speed),
        'IEC 61400-27-1 two-mass wind drivetrain: aerodynamic torque, shaft spring/damping, and generator torque.',
    )
    template.comment += (
        ' Signal association to the converter/machine host remains an importer composition step.'
    )
    return template
