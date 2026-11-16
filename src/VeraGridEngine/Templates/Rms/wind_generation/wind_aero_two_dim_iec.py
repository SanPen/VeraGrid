# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES IEC two-dimensional wind aerodynamic model."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def build_wind_aero_two_dim_i_e_c_template(
        vfactory: VarFactory,
        name: str | None = None,
        dpomega: float = 0.0,
        dptheta: float = 0.0,
        dpv1: float = 0.0,
        omegazero: float = 1.0,
        pavail: float = 0.0,
        thetav2: float = 1.0,
        thetazero: float = 0.0,
) -> RmsModelTemplate:
    """Build the IEC 61400-27-1 two-dimensional aerodynamic equations.

    The standard linearizes aerodynamic power about the available-power
    operating point. Its type dependent pitch adjustment modifies the rotor
    speed derivative during derated operation.

    :param vfactory: Factory allocating the model symbols.
    :param name: Optional unique runtime template name.
    :param dpomega: Power derivative with respect to turbine rotor speed.
    :param dptheta: Power derivative with respect to blade pitch angle.
    :param dpv1: Rated-wind-speed rotor-speed derivative correction.
    :param omegazero: Turbine rotor speed at the reference operating point.
    :param pavail: Available aerodynamic power at the reference operating point.
    :param thetav2: Blade angle at twice rated wind speed; must be positive.
    :param thetazero: Blade angle at the reference operating point.
    :return: Equation-backed model with pitch and rotor-speed inputs.
    :raises ValueError: Nonfinite values or a nonpositive ``thetav2``.
    """
    values: tuple[float, ...] = (
        dpomega, dptheta, dpv1, omegazero, pavail, thetav2, thetazero,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('CGMES WindAeroTwoDimIEC values must be finite')
    elif thetav2 <= 0.0 or pavail < 0.0:
        raise ValueError('CGMES WindAeroTwoDimIEC requires positive thetav2 and nonnegative pavail')
    else:
        pass

    template_name: str = 'WindAeroTwoDimIEC' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    rotor_speed_derivative: Var = model.parameter('WindAeroTwoDimIEC.dpomega', dpomega)
    pitch_power_derivative: Var = model.parameter('WindAeroTwoDimIEC.dptheta', dptheta)
    rated_speed_derivative: Var = model.parameter('WindAeroTwoDimIEC.dpv1', dpv1)
    reference_speed: Var = model.parameter('WindAeroTwoDimIEC.omegazero', omegazero)
    available_power: Var = model.parameter('WindAeroTwoDimIEC.pavail', pavail)
    twice_rated_pitch: Var = model.parameter('WindAeroTwoDimIEC.thetav2', thetav2)
    reference_pitch: Var = model.parameter('WindAeroTwoDimIEC.thetazero', thetazero)
    pitch_angle: Var = model.input('ThetaDeg', Const(thetazero))
    turbine_speed: Var = model.input('OmegaWtrPu', Const(omegazero))

    # IEC 61400-27-1:2015 E.7 adjusts dpomega linearly with pitch angle.
    pitch_derivative_adjustment: Expr = (
        rated_speed_derivative * (twice_rated_pitch - pitch_angle)
        / (Const(2.0) * twice_rated_pitch)
    )
    effective_speed_derivative: Expr = rotor_speed_derivative + pitch_derivative_adjustment
    aerodynamic_power: Var = model.algebraic(
        'PaeroPu',
        available_power
        + pitch_power_derivative * (pitch_angle - reference_pitch)
        + effective_speed_derivative * (turbine_speed - reference_speed),
        Const(pavail),
    )
    return model.finish(
        (aerodynamic_power,),
        'IEC 61400-27-1 two-dimensional aerodynamic power linearization with derating pitch correction.',
    )
