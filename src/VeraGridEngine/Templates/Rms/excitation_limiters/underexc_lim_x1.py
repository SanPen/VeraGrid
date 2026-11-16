# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES UnderexcLimX1 minimum-excitation limiter."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class UnderexcLimX1Parameters:
    """Canonical Allis-Chalmers UEL parameters."""

    __slots__ = ('kf2', 'tf2', 'km', 'tm', 'melmax', 'k')

    def __init__(
            self,
            kf2: float = 0.0,
            tf2: float = 1.0,
            km: float = 1.0,
            tm: float = 1.0,
            melmax: float = 1.0,
            k: float = 1.0,
    ) -> None:
        """Store the exact RDF parameters.

        :param kf2: Differential gain for the Efd path.
        :param tf2: Differential filter time constant.
        :param km: Minimum-excitation gain.
        :param tm: Minimum-excitation lag time constant.
        :param melmax: Maximum minimum-excitation signal.
        :param k: Reactive-power slope coefficient.
        """
        self.kf2: float = kf2
        self.tf2: float = tf2
        self.km: float = km
        self.tm: float = tm
        self.melmax: float = melmax
        self.k: float = k


def build_underexc_lim_x1_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: UnderexcLimX1Parameters | None = None,
) -> RmsModelTemplate:
    """Build the EA1293 differentiated-field and Q/P limiting graph.

    :param vfactory: Factory used to allocate equation and parameter symbols.
    :param name: Optional runtime model name.
    :param parameters: Canonical UnderexcLimX1 settings.
    :return: UEL graph exposing machine reactive power, Efd, and VUEL.
    :raises ValueError: Invalid time constants, gains, or curve limits.
    """
    settings: UnderexcLimX1Parameters = (
        UnderexcLimX1Parameters() if parameters is None else parameters
    )
    numeric_values: tuple[float, ...] = (
        settings.kf2, settings.tf2, settings.km, settings.tm, settings.melmax, settings.k,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('UnderexcLimX1 parameters must be finite')
    elif settings.tf2 < 0.0 or settings.tm < 0.0 or settings.k <= 0.0:
        raise ValueError('UnderexcLimX1 time constants must be nonnegative and K positive')
    elif settings.km < 0.0 or settings.melmax < 0.0:
        raise ValueError('UnderexcLimX1 gains and MELMAX must be nonnegative')
    else:
        pass

    template_name: str = 'UnderexcLimX1' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    differential_gain: Var = model.parameter('UnderexcLimX1.kf2', settings.kf2)
    differential_time: Var = model.parameter('UnderexcLimX1.tf2', settings.tf2)
    minimum_gain: Var = model.parameter('UnderexcLimX1.km', settings.km)
    minimum_time: Var = model.parameter('UnderexcLimX1.tm', settings.tm)
    minimum_limit: Var = model.parameter('UnderexcLimX1.melmax', settings.melmax)
    slope: Var = model.parameter('UnderexcLimX1.k', settings.k)
    reactive_power: Var = model.input('QPu', Const(0.0))
    field_current: Var = model.input('IfdPu', Const(0.0))
    field_voltage: Var = model.input('EfdPu', Const(1.0))

    # The documented high-pass differentiator is represented without a zero-time state.
    if settings.tf2 > 0.0:
        field_filter_state: Var = model.lag(
            'FieldLowPassPu', field_voltage, differential_time, settings.tf2, field_voltage,
        )
        field_high_pass: Expr = differential_gain * (field_voltage - field_filter_state)
    else:
        field_high_pass = Const(0.0)
    excitation_margin: Var = model.algebraic(
        'ExcitationMarginPu', reactive_power - field_current / slope, Const(0.0),
    )
    limited_signal: Expr = minimum_gain * excitation_margin
    limited_output: Var
    if settings.tm > 0.0:
        limited_output = model.lag(
            'LimitedExcitationPu', limited_signal, minimum_time, settings.tm,
            Const(0.0), Const(0.0), minimum_limit,
        )
    else:
        limited_output = model.algebraic(
            'LimitedExcitationPu',
            sym.hard_sat(limited_signal, Const(0.0), minimum_limit),
            Const(0.0),
        )
    output_state: Var = model.algebraic(
        'VuelPu', limited_output - field_high_pass, Const(0.0),
    )
    template: RmsModelTemplate = model.finish(
        (output_state,), 'CGMES UnderexcLimX1 differentiated-field and limited reactive UEL',
    )
    template.comment = (
        'Equations follow local EA1292/EA1293: Q−IFD/K passes through the bounded '
        'Km/(1+s*Tm) stage, then subtracts Kf2*s/(1+s*Tf2)*EFD to produce VUEL.'
    )
    enabled_name: str = f'UnderexcLimX1.enabled_{template_name}'
    enabled_variable: Var = vfactory.add_var(enabled_name)
    template.block.event_dict[enabled_variable] = vfactory.add_const(value=None, name=enabled_name)
    return template
