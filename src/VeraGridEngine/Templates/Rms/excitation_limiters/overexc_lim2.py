# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES OverexcLim2 field-current limiter."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var


class OverexcLim2Parameters:
    """Canonical OverexcLim2 current threshold and bounded-integrator fields."""

    __slots__ = ('koi', 'voimax', 'voimin', 'ifdlim')

    def __init__(
            self,
            koi: float = 0.0,
            voimax: float = 1.0,
            voimin: float = -1.0,
            ifdlim: float = 1.0,
    ) -> None:
        """Store the exact RDF parameters.

        :param koi: Integral gain.
        :param voimax: Upper limiter-output bound.
        :param voimin: Lower limiter-output bound.
        :param ifdlim: Field-current threshold in per unit.
        """
        self.koi: float = koi
        self.voimax: float = voimax
        self.voimin: float = voimin
        self.ifdlim: float = ifdlim


def build_overexc_lim2_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: OverexcLim2Parameters | None = None,
) -> RmsModelTemplate:
    """Build the bounded integral OEL shown in the local EA diagram.

    :param vfactory: Factory allocating the equation and parameter symbols.
    :param name: Optional unique runtime model label.
    :param parameters: Parsed canonical OverexcLim2 fields.
    :return: OEL graph with field-current input and limiter output.
    :raises ValueError: Nonfinite fields, negative gain, or reversed output bounds.
    """
    settings: OverexcLim2Parameters = OverexcLim2Parameters() if parameters is None else parameters
    numeric_values: tuple[float, ...] = (
        settings.koi, settings.voimax, settings.voimin, settings.ifdlim,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('OverexcLim2 parameters must be finite')
    elif settings.koi < 0.0 or settings.voimin >= settings.voimax:
        raise ValueError('OverexcLim2 gain and output bounds are invalid')
    else:
        pass

    template_name: str = 'OverexcLim2' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    integral_gain: Var = model.parameter('OverexcLim2.koi', settings.koi)
    current_limit: Var = model.parameter('OverexcLim2.ifdlim', settings.ifdlim)
    output_lower: Var = model.parameter('OverexcLim2.voimin', settings.voimin)
    output_upper: Var = model.parameter('OverexcLim2.voimax', settings.voimax)
    field_current: Var = model.input('IfdPu', Const(settings.ifdlim))
    current_error: Var = model.algebraic(
        'CurrentErrorPu', current_limit - field_current, Const(0.0),
    )
    limiter_output: Var = vfactory.add_var(f'OelPu_{template_name}')
    model.differential(
        state=limiter_output,
        derivative=integral_gain * current_error,
        initial=Const(0.0),
        lower=output_lower,
        upper=output_upper,
    )
    template: RmsModelTemplate = model.finish(
        (limiter_output,), 'CGMES OverexcLim2 bounded field-current integral limiter',
    )
    template.comment = (
        'Equations follow the local CGMES 2.4.15 EA1265/EA1266 diagram: '
        'Koi/s integral of Ifdlim−Ifd/Irated with Voimin/Voimax bounds; IfdPu and Irated=1 '
        'represent the canonical per-unit current convention.'
    )
    enabled_name: str = f'OverexcLim2.enabled_{template_name}'
    enabled_variable: Var = vfactory.add_var(enabled_name)
    template.block.event_dict[enabled_variable] = vfactory.add_const(value=None, name=enabled_name)
    return template
