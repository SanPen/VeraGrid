# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES OverexcLimX2 excitation limiter."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class OverexcLimX2Parameters:
    """Canonical OverexcLimX2 parameters."""

    __slots__ = ('m', 'efdrated', 'efd1', 't1', 'efd2', 't2', 'efd3', 't3', 'efddes', 'kmx', 'vlow')

    def __init__(self, m: bool = False, efdrated: float = 1.05, efd1: float = 1.1,
                 t1: float = 120.0, efd2: float = 1.2, t2: float = 40.0,
                 efd3: float = 1.5, t3: float = 15.0, efddes: float = 1.0,
                 kmx: float = 0.01, vlow: float = 0.0) -> None:
        """Store the RDF parameters.

        :param m: Select field current when true, otherwise field voltage.
        :param efdrated: Rated field current or voltage.
        :param efd1: First inverse-time threshold.
        :param t1: Trip time at the first threshold.
        :param efd2: Second inverse-time threshold.
        :param t2: Trip time at the second threshold.
        :param efd3: Third inverse-time threshold.
        :param t3: Trip time at the third threshold.
        :param efddes: Desired field current or voltage.
        :param kmx: Bounded-integrator gain.
        :param vlow: Positive magnitude of the negative output bound.
        """
        self.m: bool = m
        self.efdrated: float = efdrated
        self.efd1: float = efd1
        self.t1: float = t1
        self.efd2: float = efd2
        self.t2: float = t2
        self.efd3: float = efd3
        self.t3: float = t3
        self.efddes: float = efddes
        self.kmx: float = kmx
        self.vlow: float = vlow


def build_overexc_lim_x2_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: OverexcLimX2Parameters | None = None,
) -> RmsModelTemplate:
    """Build the bounded-integrator OverexcLimX2 equation graph.

    :param vfactory: Factory for model symbols.
    :param name: Optional model instance name.
    :param parameters: Canonical model fields and selector.
    :return: Limiter template with the selected machine measurement and VOEL output.
    """
    settings: OverexcLimX2Parameters = OverexcLimX2Parameters() if parameters is None else parameters
    numeric_values: tuple[float, ...] = (
        settings.efdrated, settings.efd1, settings.t1, settings.efd2, settings.t2,
        settings.efd3, settings.t3, settings.efddes, settings.kmx, settings.vlow,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('OverexcLimX2 parameters must be finite')
    elif settings.efdrated <= 0.0:
        raise ValueError('OverexcLimX2 rated field quantity must be positive')
    elif settings.efd1 >= settings.efd2 or settings.efd2 >= settings.efd3:
        raise ValueError('OverexcLimX2 curve thresholds must be strictly increasing')
    elif min(settings.t1, settings.t2, settings.t3) <= 0.0:
        raise ValueError('OverexcLimX2 inverse-time points require positive trip times')
    elif settings.kmx < 0.0 or settings.vlow < 0.0:
        raise ValueError('OverexcLimX2 gain must be nonnegative and VLOW must be nonnegative')
    else:
        pass

    template_name: str = 'OverexcLimX2' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    rated_quantity: Var = model.parameter('OverexcLimX2.efdrated', settings.efdrated)
    threshold_1: Var = model.parameter('OverexcLimX2.efd1', settings.efd1)
    trip_time_1: Var = model.parameter('OverexcLimX2.t1', settings.t1)
    threshold_2: Var = model.parameter('OverexcLimX2.efd2', settings.efd2)
    trip_time_2: Var = model.parameter('OverexcLimX2.t2', settings.t2)
    threshold_3: Var = model.parameter('OverexcLimX2.efd3', settings.efd3)
    trip_time_3: Var = model.parameter('OverexcLimX2.t3', settings.t3)
    desired_field: Var = model.parameter('OverexcLimX2.efddes', settings.efddes)
    output_gain: Var = model.parameter('OverexcLimX2.kmx', settings.kmx)
    lower_limit: Var = model.parameter('OverexcLimX2.vlow', settings.vlow)
    if settings.m:
        measurement: Var = model.input('IfdPu', Const(settings.efddes))
    else:
        measurement = model.input('EfdPu', Const(settings.efddes))
    rated_measurement: Expr = measurement / rated_quantity
    curve_measurement: Expr = sym.max(rated_measurement, threshold_1)
    first_curve_segment: Expr = (
        trip_time_1
        + (trip_time_2 - trip_time_1)
        * (curve_measurement - threshold_1)
        / (threshold_2 - threshold_1)
    )
    second_curve_segment: Expr = (
        trip_time_2
        + (trip_time_3 - trip_time_2)
        * (curve_measurement - threshold_2)
        / (threshold_3 - threshold_2)
    )
    curve_after_threshold_2: Expr = first_curve_segment + sym.heaviside(
        curve_measurement - threshold_2,
    ) * (second_curve_segment - first_curve_segment)
    trip_time: Var = model.algebraic(
        'TripTimeSec',
        curve_after_threshold_2 + sym.heaviside(
            curve_measurement - threshold_3,
        ) * (trip_time_3 - curve_after_threshold_2),
        trip_time_1,
    )
    trip_curve_active: Var = model.algebraic(
        'TripCurveActive',
        Const(1.0) - sym.heaviside(threshold_1 - rated_measurement),
        Const(0.0),
    )
    output: Var = vfactory.add_var(f'OelPu_{template_name}')
    model.differential(output, output_gain * (desired_field - measurement), Const(0.0),
                       -lower_limit, Const(0.0))
    template: RmsModelTemplate = model.finish(
        (output, trip_time, trip_curve_active),
        'CGMES OverexcLimX2 bounded excitation-error integrator and inverse-time curve',
    )
    template.comment = (
        'EA1272: d(VOEL)/dt=KMX*(EFD_DES−EFD) for m=F or '
        'KMX*(IFD_DES−IFD) for m=T, with −VLOW≤VOEL≤0; the canonical RDF defines VLOW '
        'as a positive magnitude. EA1276 is implemented as the '
        'piecewise-linear EFD/IFD pu-of-rated to trip-time curve using the same m-selected '
        'measurement; TripCurveActive marks its threshold domain. No trip/reset port is '
        'defined by the RDF, so this curve does not trip equipment.'
    )
    enabled_name: str = f'OverexcLimX2.enabled_{template_name}'
    enabled_variable: Var = vfactory.add_var(enabled_name)
    model.block.event_dict[enabled_variable] = vfactory.add_const(value=None, name=enabled_name)
    mode_name: str = f'OverexcLimX2.m_{template_name}'
    mode_variable: Var = vfactory.add_var(mode_name)
    model.block.event_dict[mode_variable] = vfactory.add_const(value=settings.m, name=mode_name)
    return template
