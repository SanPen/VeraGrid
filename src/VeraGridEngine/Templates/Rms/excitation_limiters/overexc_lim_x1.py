# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES OverexcLimX1 field-voltage limiter."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var, hard_sat
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class OverexcLimX1Parameters:
    """Canonical OverexcLimX1 fields for timed voltage-limit action."""

    __slots__ = ('efdrated', 'efd1', 't1', 'efd2', 't2', 'efd3', 't3', 'efddes', 'kmx', 'vlow')

    def __init__(
            self,
            efdrated: float = 1.05,
            efd1: float = 1.1,
            t1: float = 120.0,
            efd2: float = 1.2,
            t2: float = 40.0,
            efd3: float = 1.5,
            t3: float = 15.0,
            efddes: float = 0.9,
            kmx: float = 0.01,
            vlow: float = 0.0,
    ) -> None:
        """Store the canonical parameters.

        :param efdrated: Rated field voltage.
        :param efd1: First field-voltage point of the time curve.
        :param t1: Trip time at ``efd1``.
        :param efd2: Second field-voltage point of the time curve.
        :param t2: Trip time at ``efd2``.
        :param efd3: Third field-voltage point of the time curve.
        :param t3: Trip time at ``efd3``.
        :param efddes: Desired field-voltage reference after limiter action.
        :param kmx: Output gain.
        :param vlow: Low-voltage dead zone threshold.
        """
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


def build_overexc_lim_x1_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: OverexcLimX1Parameters | None = None,
) -> RmsModelTemplate:
    """Build the voltage-error output shown in the CGMES EA diagram.

    :param vfactory: Factory used to allocate equation and parameter symbols.
    :param name: Optional runtime model name.
    :param parameters: Canonical OverexcLimX1 settings.
    :return: Model with field voltage input, OEL correction, and inverse-time curve signals.
    """
    settings: OverexcLimX1Parameters = OverexcLimX1Parameters() if parameters is None else parameters
    numeric_values: tuple[float, ...] = (
        settings.efdrated, settings.efd1, settings.t1, settings.efd2, settings.t2,
        settings.efd3, settings.t3, settings.efddes, settings.kmx, settings.vlow,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('OverexcLimX1 parameters must be finite')
    elif settings.efdrated <= 0.0:
        raise ValueError('OverexcLimX1 rated field voltage must be positive')
    elif settings.efd1 >= settings.efd2 or settings.efd2 >= settings.efd3:
        raise ValueError('OverexcLimX1 field-voltage curve points must be strictly increasing')
    elif settings.t1 <= 0.0 or settings.t2 <= 0.0 or settings.t3 <= 0.0:
        raise ValueError('OverexcLimX1 inverse-time points require positive trip times')
    elif settings.kmx < 0.0 or settings.vlow < 0.0:
        raise ValueError('OverexcLimX1 gain and low-voltage threshold must be nonnegative')
    else:
        pass

    template_name: str = 'OverexcLimX1' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    desired_voltage: Var = model.parameter('OverexcLimX1.efddes', settings.efddes)
    output_gain: Var = model.parameter('OverexcLimX1.kmx', settings.kmx)
    low_voltage: Var = model.parameter('OverexcLimX1.vlow', settings.vlow)
    rated_voltage: Var = model.parameter('OverexcLimX1.efdrated', settings.efdrated)
    field_voltage: Var = model.input('EfdPu', Const(settings.efddes))
    field_voltage_1: Var = model.parameter('OverexcLimX1.efd1', settings.efd1)
    trip_time_1: Var = model.parameter('OverexcLimX1.t1', settings.t1)
    field_voltage_2: Var = model.parameter('OverexcLimX1.efd2', settings.efd2)
    trip_time_2: Var = model.parameter('OverexcLimX1.t2', settings.t2)
    field_voltage_3: Var = model.parameter('OverexcLimX1.efd3', settings.efd3)
    trip_time_3: Var = model.parameter('OverexcLimX1.t3', settings.t3)

    # The curve x-axis is EFD in per unit of rated field voltage, unlike VOEL's machine input.
    rated_field_voltage_pu: Expr = field_voltage / rated_voltage
    curve_field_voltage_pu: Expr = sym.max(rated_field_voltage_pu, field_voltage_1)
    first_curve_segment: Expr = (
        trip_time_1
        + (trip_time_2 - trip_time_1)
        * (curve_field_voltage_pu - field_voltage_1)
        / (field_voltage_2 - field_voltage_1)
    )
    second_curve_segment: Expr = (
        trip_time_2
        + (trip_time_3 - trip_time_2)
        * (curve_field_voltage_pu - field_voltage_2)
        / (field_voltage_3 - field_voltage_2)
    )
    curve_after_efd2: Expr = first_curve_segment + sym.heaviside(
        curve_field_voltage_pu - field_voltage_2,
    ) * (second_curve_segment - first_curve_segment)
    trip_time: Var = model.algebraic(
        'TripTimeSec',
        curve_after_efd2 + sym.heaviside(
            curve_field_voltage_pu - field_voltage_3,
        ) * (trip_time_3 - curve_after_efd2),
        trip_time_1,
    )
    trip_curve_active: Var = model.algebraic(
        'TripCurveActive',
        Const(1.0) - sym.heaviside(field_voltage_1 - rated_field_voltage_pu),
        Const(0.0),
    )
    oel_error: Var = model.algebraic(
        'OelErrorPu', rated_voltage * desired_voltage - field_voltage, Const(0.0),
    )
    output: Var = vfactory.add_var(f'OelPu_{template_name}')
    model.block.algebraic_vars.append(output)
    model.block.algebraic_eqs.append(
        output - hard_sat(output_gain * oel_error, -low_voltage, Const(0.0)),
    )
    template: RmsModelTemplate = model.finish(
        (output, trip_time, trip_curve_active),
        'CGMES OverexcLimX1 desired field-voltage limiter and inverse-time curve',
    )
    template.comment = (
        'EA1270 defines VOEL=KMX*(EFD_DES*EFD_RATED−EFD), limited between −VLOW and zero; '
        'the canonical RDF defines VLOW as a positive magnitude. '
        'EA1274 is implemented as the piecewise-linear EFD pu-of-rated to trip-time output '
        'through EFD1/T1, EFD2/T2, and EFD3/T3, with T3 held above EFD3. TripCurveActive '
        'marks the defined curve domain; TripTimeSec is meaningful only when it is active. '
        'The RDF has no trip/reset port, so this curve does not trip equipment.'
    )
    enabled_name: str = f'OverexcLimX1.enabled_{template_name}'
    enabled_variable: Var = vfactory.add_var(enabled_name)
    template.block.event_dict[enabled_variable] = vfactory.add_const(value=None, name=enabled_name)
    return template
