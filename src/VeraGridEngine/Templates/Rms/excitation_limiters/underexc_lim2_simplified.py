# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES UnderexcLim2Simplified limiter."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var


class UnderexcLim2SimplifiedParameters:
    """Canonical Q/P curve, integral gain, and output bounds."""

    __slots__ = ('q0', 'q1', 'p0', 'p1', 'kui', 'vuimin', 'vuimax')

    def __init__(
            self,
            q0: float = 0.0,
            q1: float = 0.0,
            p0: float = 0.0,
            p1: float = 1.0,
            kui: float = 0.0,
            vuimin: float = -1.0,
            vuimax: float = 1.0,
    ) -> None:
        """Store the exact RDF parameter values.

        :param q0: Reactive-power curve value at ``p0``.
        :param q1: Reactive-power curve value at ``p1``.
        :param p0: Lower active-power curve point.
        :param p1: Upper active-power curve point.
        :param kui: Integral gain in per unit.
        :param vuimin: Lower UEL output bound.
        :param vuimax: Upper UEL output bound.
        """
        self.q0: float = q0
        self.q1: float = q1
        self.p0: float = p0
        self.p1: float = p1
        self.kui: float = kui
        self.vuimin: float = vuimin
        self.vuimax: float = vuimax


def build_underexc_lim2_simplified_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: UnderexcLim2SimplifiedParameters | None = None,
) -> RmsModelTemplate:
    """Build the two-point UEL lookup curve and bounded integrator.

    :param vfactory: Factory allocating all equation and parameter symbols.
    :param name: Optional unique runtime model label.
    :param parameters: Canonical CGMES parameter values.
    :return: UEL graph with P/V and Q/V measurement ports.
    :raises ValueError: Nonfinite data, a vertical curve, or reversed limits.
    """
    settings: UnderexcLim2SimplifiedParameters = (
        UnderexcLim2SimplifiedParameters() if parameters is None else parameters
    )
    numeric_values: tuple[float, ...] = (
        settings.q0, settings.q1, settings.p0, settings.p1,
        settings.kui, settings.vuimin, settings.vuimax,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('UnderexcLim2Simplified parameters must be finite')
    elif settings.p0 == settings.p1:
        raise ValueError('UnderexcLim2Simplified active-power curve points must differ')
    elif settings.kui < 0.0 or settings.vuimin >= settings.vuimax:
        raise ValueError('UnderexcLim2Simplified gain and output bounds are invalid')
    else:
        pass

    template_name: str = 'UnderexcLim2Simplified' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    q0: Var = model.parameter('UnderexcLim2Simplified.q0', settings.q0)
    q1: Var = model.parameter('UnderexcLim2Simplified.q1', settings.q1)
    p0: Var = model.parameter('UnderexcLim2Simplified.p0', settings.p0)
    p1: Var = model.parameter('UnderexcLim2Simplified.p1', settings.p1)
    kui: Var = model.parameter('UnderexcLim2Simplified.kui', settings.kui)
    lower: Var = model.parameter('UnderexcLim2Simplified.vuimin', settings.vuimin)
    upper: Var = model.parameter('UnderexcLim2Simplified.vuimax', settings.vuimax)
    active_power_over_voltage: Var = model.input('PPuOverVPu', Const(settings.p0))
    reactive_power_over_voltage: Var = model.input('QPuOverVPu', Const(settings.q0))

    # The EA1291 lookup line is the exact affine segment through (P0,Q0) and (P1,Q1).
    reactive_reference: Var = model.algebraic(
        'ReactiveReferencePu', q0 + (q1 - q0) * (active_power_over_voltage - p0) / (p1 - p0),
        q0,
    )
    limiter_error: Var = model.algebraic(
        'LimiterErrorPu', reactive_reference - reactive_power_over_voltage, Const(0.0),
    )
    output_state: Var = vfactory.add_var(f'VuelPu_{template_name}')
    model.differential(
        state=output_state,
        derivative=kui * limiter_error,
        initial=Const(0.0),
        lower=lower,
        upper=upper,
    )
    template: RmsModelTemplate = model.finish(
        (output_state,), 'CGMES UnderexcLim2Simplified Q/P curve and bounded integral UEL',
    )
    template.comment = (
        'Equations follow the local CGMES 2.4.15 EA1290/EA1291 diagram: linear QREF(P/V), '
        'Q/V subtraction, and KUI/s with VUIMIN/VUIMAX bounds.'
    )
    enabled_name: str = f'UnderexcLim2Simplified.enabled_{template_name}'
    enabled_variable: Var = vfactory.add_var(enabled_name)
    template.block.event_dict[enabled_variable] = vfactory.add_const(value=None, name=enabled_name)
    return template
