# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES UnderexcLimX2 minimum-excitation limiter."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class UnderexcLimX2Parameters:
    """Canonical UnderexcLimX2 parameters."""

    __slots__ = ('kf2', 'tf2', 'km', 'tm', 'melmax', 'qo', 'r')

    def __init__(self, kf2: float = 0.0, tf2: float = 1.0, km: float = 1.0,
                 tm: float = 1.0, melmax: float = 1.0, qo: float = 0.0,
                 r: float = 1.0) -> None:
        """Store the seven RDF fields.

        :param kf2: Field-voltage feedback washout gain.
        :param tf2: Field-voltage feedback washout time.
        :param km: UEL output gain.
        :param tm: UEL output lag time.
        :param melmax: Maximum UEL output.
        :param qo: Center reactive-power setting.
        :param r: P-Q capability radius.
        """
        self.kf2: float = kf2
        self.tf2: float = tf2
        self.km: float = km
        self.tm: float = tm
        self.melmax: float = melmax
        self.qo: float = qo
        self.r: float = r


def build_underexc_lim_x2_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: UnderexcLimX2Parameters | None = None,
) -> RmsModelTemplate:
    """Build the EA1295 P-Q radius and field-feedback limiter graph.

    :param vfactory: Factory for equation and parameter symbols.
    :param name: Optional runtime model name.
    :param parameters: Canonical UnderexcLimX2 settings.
    :return: UEL graph with P, Q, terminal-voltage inputs and VUEL output.
    """
    settings: UnderexcLimX2Parameters = (
        UnderexcLimX2Parameters() if parameters is None else parameters
    )
    numeric_values: tuple[float, ...] = (
        settings.kf2, settings.tf2, settings.km, settings.tm,
        settings.melmax, settings.qo, settings.r,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('UnderexcLimX2 parameters must be finite')
    elif settings.tf2 < 0.0 or settings.tm < 0.0 or settings.km < 0.0 or settings.melmax < 0.0:
        raise ValueError('UnderexcLimX2 times, gain, and MELMAX must be nonnegative')
    else:
        pass

    template_name: str = 'UnderexcLimX2' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    differential_gain: Var = model.parameter('UnderexcLimX2.kf2', settings.kf2)
    differential_time: Var = model.parameter('UnderexcLimX2.tf2', settings.tf2)
    output_gain: Var = model.parameter('UnderexcLimX2.km', settings.km)
    output_time: Var = model.parameter('UnderexcLimX2.tm', settings.tm)
    output_limit: Var = model.parameter('UnderexcLimX2.melmax', settings.melmax)
    center_q: Var = model.parameter('UnderexcLimX2.qo', settings.qo)
    capability_radius: Var = model.parameter('UnderexcLimX2.r', settings.r)
    active_power: Var = model.input('PPu', Const(0.0))
    reactive_power: Var = model.input('QPu', Const(0.0))
    terminal_voltage: Var = model.input('EtPu', Const(1.0))
    output: Var = vfactory.add_var(f'VuelPu_{template_name}')

    # The EA diagram builds the squared P-Q radius error, avoiding a square-root stage.
    voltage_squared: Expr = terminal_voltage * terminal_voltage
    reactive_offset: Expr = reactive_power - center_q * voltage_squared
    radius_error: Expr = (
        reactive_offset * reactive_offset
        + active_power * active_power
        - (capability_radius * voltage_squared) * (capability_radius * voltage_squared)
    )
    if settings.tf2 > 0.0:
        feedback_washout: Var = model.washout(
            'FieldFeedbackWashoutPu', output, differential_time, settings.tf2,
            differential_gain, Const(0.0),
        )
    else:
        feedback_washout = model.algebraic('FieldFeedbackWashoutPu', Const(0.0), Const(0.0))
    limiter_input: Expr = radius_error - feedback_washout
    model.lag(
        'VuelPu', output_gain * limiter_input, output_time, settings.tm,
        Const(0.0), Const(0.0), output_limit, output,
    )
    template: RmsModelTemplate = model.finish(
        (output,), 'CGMES UnderexcLimX2 P-Q capability limiter with field feedback',
    )
    template.comment = (
        'EA1295: PQSIG=(Q−Qo*Et²)²+P²−(R*Et²)²; feedback subtracts '
        'Kf2*s/(1+s*Tf2)*VUEL; output is Km/(1+s*Tm), limited from zero to MELMAX. '
        'Zero-time feedback and output stages reduce algebraically.'
    )
    enabled_name: str = f'UnderexcLimX2.enabled_{template_name}'
    enabled_variable: Var = vfactory.add_var(enabled_name)
    model.block.event_dict[enabled_variable] = vfactory.add_const(value=None, name=enabled_name)
    return template
