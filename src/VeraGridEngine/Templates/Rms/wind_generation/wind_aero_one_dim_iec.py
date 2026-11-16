# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES IEC one-dimensional wind aerodynamic model."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def build_wind_aero_one_dim_i_e_c_template(
        vfactory: VarFactory,
        name: str | None = None,
        ka: float = 0.0,
        initial_pitch_angle: float = 0.0,
        initial_power: float = 0.0,
) -> RmsModelTemplate:
    """Build the IEC 61400-27-1 one-dimensional aerodynamic model.

    :param vfactory: Factory allocating the model symbols.
    :param name: Optional unique runtime template name.
    :param ka: Canonical CGMES aerodynamic gain in pu power per degree squared.
    :param initial_pitch_angle: Load-flow pitch angle in degrees.
    :param initial_power: Load-flow aerodynamic power in pu on the generator base.
    :return: Equation-backed aerodynamic model with pitch input and power output.
    :raises ValueError: Nonfinite or negative model values.
    """
    values: tuple[float, ...] = (ka, initial_pitch_angle, initial_power)
    if not all(math.isfinite(value) for value in values):
        raise ValueError('CGMES WindAeroOneDimIEC values must be finite')
    elif ka < 0.0 or initial_power < 0.0:
        raise ValueError('CGMES WindAeroOneDimIEC gain and initial power must be nonnegative')
    else:
        pass

    template_name: str = 'WindAeroOneDimIEC' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    aerodynamic_gain: Var = model.parameter('WindAeroOneDimIEC.ka', ka)
    reference_pitch: Var = model.parameter('WindAeroOneDimIEC.thetaomega', initial_pitch_angle)
    pitch_angle: Var = model.input('ThetaDeg', Const(initial_pitch_angle))
    initial_aerodynamic_power: Const = Const(initial_power)
    pitch_error: Expr = pitch_angle - reference_pitch
    aerodynamic_power: Var = model.algebraic(
        'PaeroPu',
        initial_aerodynamic_power - aerodynamic_gain * pitch_error ** 2,
        initial_aerodynamic_power,
    )
    return model.finish(
        (aerodynamic_power,),
        'IEC 61400-27-1 one-dimensional pitch-dependent aerodynamic power model.',
    )
