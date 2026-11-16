# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation block for the CGMES 2.4.15 linear aerodynamic wind model."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var


def build_wind_aero_linear_i_e_c_template(
        vfactory: VarFactory,
        name: str | None = None,
        dpomega: float = 0.0,
        dptheta: float = 0.0,
        omegazero: float = 1.0,
        pavail: float = 0.0,
        thetazero: float = 0.0,
) -> RmsModelTemplate:
    """Build IEC 61400-27-1:2015 §6.6.1.2 linear aerodynamic equations.

    The linear model evaluates the first-order power expansion around its
    case-dependent reference point using the RDF's speed and pitch derivatives.

    :param vfactory: Factory allocating the model symbols.
    :param name: Optional unique runtime template name.
    :param dpomega: Aerodynamic power derivative with respect to rotor speed.
    :param dptheta: Aerodynamic power derivative with respect to pitch angle.
    :param omegazero: Rotor speed at the reference operating point.
    :param pavail: Available aerodynamic power at the reference operating point.
    :param thetazero: Pitch angle at the reference operating point, in degrees.
    :return: Algebraic model exposing ``PaeroPu`` from pitch and rotor speed.
    :raises ValueError: If any parameter is nonfinite.
    """
    parameter_values: tuple[float, ...] = (
        dpomega, dptheta, omegazero, pavail, thetazero,
    )
    if not all(math.isfinite(value) for value in parameter_values):
        raise ValueError('CGMES WindAeroLinearIEC values must be finite')
    else:
        pass

    template_name: str = 'WindAeroLinearIEC' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    speed_gain: Var = model.parameter('WindAeroLinearIEC.dpomega', dpomega)
    pitch_gain: Var = model.parameter('WindAeroLinearIEC.dptheta', dptheta)
    reference_speed: Var = model.parameter('WindAeroLinearIEC.omegazero', omegazero)
    available_power: Var = model.parameter('WindAeroLinearIEC.pavail', pavail)
    reference_pitch: Var = model.parameter('WindAeroLinearIEC.thetazero', thetazero)
    pitch_angle: Var = model.input('ThetaDeg', Const(thetazero))
    turbine_speed: Var = model.input('OmegaWtrPu', Const(omegazero))
    aerodynamic_power: Var = model.algebraic(
        'PaeroPu',
        available_power
        + pitch_gain * (pitch_angle - reference_pitch)
        + speed_gain * (turbine_speed - reference_speed),
        Const(pavail),
    )
    return model.finish(
        (aerodynamic_power,),
        'IEC 61400-27-1:2015 linear aerodynamic power expansion about the case reference point.',
    )
