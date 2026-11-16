# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""MAXEX2 inverse-time excitation limiter."""
from __future__ import annotations

import math
from enum import Enum

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.Utils.procedural_logic import TimeDelayLogic
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Maxex2Measurement(Enum):
    """Select the MAXEX2 field-voltage or field-current measurement."""

    FIELD_VOLTAGE = 0
    FIELD_CURRENT = 1


class Maxex2Parameters:
    """Store rated measurement, inverse-time curve, and reset-integrator values."""

    __slots__ = (
        'measurement', 'rated', 'level1', 'time1', 'level2', 'time2',
        'level3', 'time3', 'desired_level', 'kmx', 'vlow',
    )

    def __init__(self, measurement: Maxex2Measurement = Maxex2Measurement.FIELD_VOLTAGE,
                 rated: float = 1.0, level1: float = 1.1, time1: float = 60.0,
                 level2: float = 1.2, time2: float = 30.0, level3: float = 1.5,
                 time3: float = 15.0, desired_level: float = 1.0,
                 kmx: float = 0.2, vlow: float = -0.5) -> None:
        """Store the ten ordered PSS/E constants and the mode ICON.

        :param measurement: EFD or IFD mode selected by ICON M.
        :param rated: EFD or IFD rated value in the connected signal's units.
        :param level1: Lowest overexcitation point, pu of rated.
        :param time1: Longest allowed exposure at level1, seconds.
        :param level2: Middle overexcitation point, pu of rated.
        :param time2: Allowed exposure at level2, seconds.
        :param level3: Highest overexcitation point, pu of rated.
        :param time3: Shortest allowed exposure at level3, seconds.
        :param desired_level: Post-limiting target, pu of rated.
        :param kmx: Reset-integrator gain.
        :param vlow: Lower reset-integrator output limit; must be negative.
        """
        self.measurement: Maxex2Measurement = measurement
        self.rated: float = rated
        self.level1: float = level1
        self.time1: float = time1
        self.level2: float = level2
        self.time2: float = time2
        self.level3: float = level3
        self.time3: float = time3
        self.desired_level: float = desired_level
        self.kmx: float = kmx
        self.vlow: float = vlow


def build_maxex2_template(vf: VarFactory, name: str | None = None,
                          parameters: Maxex2Parameters | None = None) -> RmsModelTemplate:
    """Build the MAXEX2 inverse-time contact and bounded reset integrator.

    The three source points define allowed exposure time as a piecewise-linear
    function of measured EFD/IFD divided by its rating. A delayed binary
    overload signal drives the source reset integrator after the allowed time;
    the integrator then moves ``VOEL`` toward ``VLOW`` until the measurement
    returns to its desired level.

    :param vf: Symbol factory owning the native equation graph.
    :param name: Optional instance name.
    :param parameters: Exact MAXEX2 DYR values and selected measurement mode.
    :return: One-input, one-output MAXEX2 limiter with its reset state.
    :raises ValueError: Source settings are nonfinite or do not define an
        ordered inverse-time characteristic.
    """
    selected: Maxex2Parameters = Maxex2Parameters() if parameters is None else parameters
    values: tuple[float, ...] = (
        selected.rated, selected.level1, selected.time1, selected.level2,
        selected.time2, selected.level3, selected.time3, selected.desired_level,
        selected.kmx, selected.vlow,
    )
    if not isinstance(selected.measurement, Maxex2Measurement):
        raise ValueError('MAXEX2 measurement mode must be EFD or IFD')
    elif not all(math.isfinite(value) for value in values):
        raise ValueError('MAXEX2 constants must be finite')
    elif selected.rated <= 0.0 or selected.kmx <= 0.0:
        raise ValueError('MAXEX2 rated measurement and KMX must be positive')
    elif not (0.0 < selected.desired_level < selected.level1 < selected.level2 < selected.level3):
        raise ValueError('MAXEX2 desired and curve levels must increase strictly')
    elif not (selected.time1 > selected.time2 > selected.time3 > 0.0):
        raise ValueError('MAXEX2 exposure times must decrease strictly with level')
    elif selected.vlow >= 0.0:
        raise ValueError('MAXEX2 VLOW must be negative')
    else:
        pass

    template_name: str = 'MAXEX2' if name is None else name
    control: ControlRealization = ControlRealization(vf, template_name)
    rated: Var = control.parameter('RatedMeasurement', selected.rated)
    level1: Var = control.parameter('Level1PuRated', selected.level1)
    time1: Var = control.parameter('Time1Sec', selected.time1)
    level2: Var = control.parameter('Level2PuRated', selected.level2)
    time2: Var = control.parameter('Time2Sec', selected.time2)
    level3: Var = control.parameter('Level3PuRated', selected.level3)
    time3: Var = control.parameter('Time3Sec', selected.time3)
    desired: Var = control.parameter('DesiredLevelPuRated', selected.desired_level)
    gain: Var = control.parameter('KMX', selected.kmx)
    lower: Var = control.parameter('VLOW', selected.vlow)

    measurement: Var = control.input('ExcitationMeasurementPu', Const(selected.rated))
    normalized_measurement: Expr = measurement / rated
    first_segment: Expr = time1 + (
        (time2 - time1) / (level2 - level1)
    ) * (normalized_measurement - level1)
    second_segment: Expr = time2 + (
        (time3 - time2) / (level3 - level2)
    ) * (normalized_measurement - level2)
    second_segment_selected: Expr = sym.heaviside(normalized_measurement - level2)
    allowed_time: Expr = sym.max(
        first_segment * (Const(1.0) - second_segment_selected)
        + second_segment * second_segment_selected,
        Const(0.0),
    )

    contact: Var = vf.add_var(f'MAXEX2ContactPosition_{template_name}')
    control.block.event_dict[contact] = Const(0.0)
    overload: Expr = sym.heaviside(measurement - desired * rated)
    control.block.procedural_logic.append(
        TimeDelayLogic(
            output_var_name=contact.name,
            source_expr=overload,
            delay_expr=allowed_time,
            name='MAXEX2 inverse-time overexcitation contact',
        )
    )

    output: Var = vf.add_var(f'MAXEX2VoltageOffsetPu_{template_name}')
    derivative: Expr = contact * gain * (desired * rated - measurement)
    control.differential(output, derivative, Const(0.0), lower, Const(0.0))
    return control.finish((output,), 'MAXEX2 inverse-time maximum excitation limiter')
