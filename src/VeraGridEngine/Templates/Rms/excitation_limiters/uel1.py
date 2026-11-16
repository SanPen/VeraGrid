# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""IEEE 421.5 UEL1 under-excitation limiter."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Uel1Settings:
    """Hold UEL1 source constants and solved signal values."""

    __slots__ = ('kur', 'kuc', 'kuf', 'vurmax', 'vucmax', 'kui', 'kul',
                 'vuimax', 'vuimin', 'tu1', 'tu2', 'tu3', 'tu4',
                 'vulmax', 'vulmin', 'vt_re0', 'vt_im0', 'it_re0',
                 'it_im0', 'vf0', 'reference0')

    def __init__(self, kur: float = 1.0, kuc: float = 0.0, kuf: float = 1.0,
                 vurmax: float = 5.0, vucmax: float = 5.0, kui: float = 1.0,
                 kul: float = 1.0, vuimax: float = 1.0, vuimin: float = -1.0,
                 tu1: float = 1.0, tu2: float = 1.0, tu3: float = 1.0,
                 tu4: float = 1.0, vulmax: float = 1.0, vulmin: float = -1.0,
                 vt_re0: float = 1.0, vt_im0: float = 0.0, it_re0: float = 0.8,
                 it_im0: float = 0.0, vf0: float = 0.0,
                 reference0: float = 0.0) -> None:
        """Store source constants and one operating-point seed.

        :param kur: Radius multiplier for terminal-current magnitude.
        :param kuc: Center multiplier for the terminal-voltage/current phasor.
        :param kuf: Excitation-system feedback gain.
        :param vurmax: Upper radius-magnitude limit.
        :param vucmax: Upper operating-point-magnitude limit.
        :param kui: Integral gain.
        :param kul: Proportional gain.
        :param vuimax: Upper PI output limit.
        :param vuimin: Lower PI output limit.
        :param tu1: First lead time constant in seconds.
        :param tu2: First lag time constant in seconds.
        :param tu3: Second lead time constant in seconds.
        :param tu4: Second lag time constant in seconds.
        :param vulmax: Upper final-output limit.
        :param vulmin: Lower final-output limit.
        :param vt_re0: Initial terminal-voltage real component.
        :param vt_im0: Initial terminal-voltage imaginary component.
        :param it_re0: Initial terminal-current real component.
        :param it_im0: Initial terminal-current imaginary component.
        :param vf0: Initial field-voltage feedback.
        :param reference0: Initial additive UEL reference.
        """
        self.kur: float = kur
        self.kuc: float = kuc
        self.kuf: float = kuf
        self.vurmax: float = vurmax
        self.vucmax: float = vucmax
        self.kui: float = kui
        self.kul: float = kul
        self.vuimax: float = vuimax
        self.vuimin: float = vuimin
        self.tu1: float = tu1
        self.tu2: float = tu2
        self.tu3: float = tu3
        self.tu4: float = tu4
        self.vulmax: float = vulmax
        self.vulmin: float = vulmin
        self.vt_re0: float = vt_re0
        self.vt_im0: float = vt_im0
        self.it_re0: float = it_re0
        self.it_im0: float = it_im0
        self.vf0: float = vf0
        self.reference0: float = reference0


def build_uel1_template(
        vf: VarFactory,
        name: str | None = None,
        settings: Uel1Settings | None = None,
) -> RmsModelTemplate:
    """Build UEL1's phasor capability error, PI, lead-lags and output limit.

    :param vf: Symbol factory owning all UEL1 symbols.
    :param name: Optional unique component name.
    :param settings: Source constants and standalone operating-point seed.
    :return: Native UEL1 block exposing the additive VUEL signal.
    :raises ValueError: A source constant, limit or lead-lag structure is invalid.
    """
    template_name: str = 'UEL1' if name is None else name
    selected: Uel1Settings = Uel1Settings() if settings is None else settings
    values: tuple[float, ...] = (
        selected.kur, selected.kuc, selected.kuf, selected.vurmax,
        selected.vucmax, selected.kui, selected.kul, selected.vuimax,
        selected.vuimin, selected.tu1, selected.tu2, selected.tu3,
        selected.tu4, selected.vulmax, selected.vulmin, selected.vt_re0,
        selected.vt_im0, selected.it_re0, selected.it_im0, selected.vf0,
        selected.reference0,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('UEL1 settings must be finite')
    elif min(selected.kur, selected.kuc, selected.kuf, selected.kui,
             selected.kul) < 0.0:
        raise ValueError('UEL1 source gains must be nonnegative')
    elif min(selected.vurmax, selected.vucmax) <= 0.0:
        raise ValueError('UEL1 magnitude limits must be positive')
    elif selected.vuimin >= selected.vuimax or selected.vulmin >= selected.vulmax:
        raise ValueError('UEL1 output limits must be ordered')
    elif min(selected.tu1, selected.tu2, selected.tu3, selected.tu4) < 0.0:
        raise ValueError('UEL1 lead-lag times must be nonnegative')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, template_name)
    kur: Var = control.parameter('KUR', selected.kur)
    kuc: Var = control.parameter('KUC', selected.kuc)
    kuf: Var = control.parameter('KUF', selected.kuf)
    vurmax: Var = control.parameter('VURMAX', selected.vurmax)
    vucmax: Var = control.parameter('VUCMAX', selected.vucmax)
    kui: Var = control.parameter('KUI', selected.kui)
    kul: Var = control.parameter('KUL', selected.kul)
    vuimax: Var = control.parameter('VUIMAX', selected.vuimax)
    vuimin: Var = control.parameter('VUIMIN', selected.vuimin)
    tu1: Var = control.parameter('TU1', selected.tu1)
    tu2: Var = control.parameter('TU2', selected.tu2)
    tu3: Var = control.parameter('TU3', selected.tu3)
    tu4: Var = control.parameter('TU4', selected.tu4)
    vulmax: Var = control.parameter('VULMAX', selected.vulmax)
    vulmin: Var = control.parameter('VULMIN', selected.vulmin)

    terminal_voltage_re: Var = control.input('TerminalVoltageRePu', Const(selected.vt_re0))
    terminal_voltage_im: Var = control.input('TerminalVoltageImPu', Const(selected.vt_im0))
    terminal_current_re: Var = control.input('TerminalCurrentRePu', Const(selected.it_re0))
    terminal_current_im: Var = control.input('TerminalCurrentImPu', Const(selected.it_im0))
    field_voltage: Var = control.input('FieldVoltagePu', Const(selected.vf0))
    reference: Var = control.input('ReferencePu', Const(selected.reference0))

    # The phasor magnitudes are the two sides of UEL1's capability boundary.
    radius: Expr = kur * sym.sqrt(
        terminal_current_re * terminal_current_re
        + terminal_current_im * terminal_current_im
    )
    radius_limited: Var = control.algebraic(
        'RadiusMagnitudePu', sym.hard_sat(radius, Const(0.0), vurmax), radius,
    )
    center_re: Expr = kuc * terminal_voltage_re + terminal_current_im
    center_im: Expr = kuc * terminal_voltage_im - terminal_current_re
    center: Expr = sym.sqrt(center_re * center_re + center_im * center_im)
    center_limited: Var = control.algebraic(
        'CenterMagnitudePu', sym.hard_sat(center, Const(0.0), vucmax), center,
    )
    initial_error: float = (
        math.hypot(
            selected.kuc * selected.vt_re0 + selected.it_im0,
            selected.kuc * selected.vt_im0 - selected.it_re0,
        )
        - selected.kur * math.hypot(selected.it_re0, selected.it_im0)
        - selected.kuf * selected.vf0
    )
    error: Var = control.algebraic(
        'UnderexcitationErrorPu',
        center_limited - radius_limited - kuf * field_voltage,
        Const(initial_error),
    )

    # Start at zero so the directional PI stop can hold an inactive UEL output.
    integrator_initial: float = max(selected.vuimin,min(selected.vuimax,0.0))
    integrator: Var = vf.add_var('PIIntegratorPu_' + template_name)
    control.differential(
        integrator, kui * error, Const(integrator_initial), vuimin, vuimax,
    )
    pi_output: Expr = sym.hard_sat(kul * error + integrator, vuimin, vuimax)

    # The two source lead-lags precede the reference sum and final output limit.
    first: Var = control.lead_lag(
        'FirstLeadLagPu', pi_output, tu1, tu2, selected.tu1, selected.tu2,
        Const(0.0),
    )
    second: Var = control.lead_lag(
        'SecondLeadLagPu', first, tu3, tu4, selected.tu3, selected.tu4,
        Const(0.0),
    )
    output: Var = control.algebraic(
        'VUELPu', sym.hard_sat(reference + second, vulmin, vulmax),
        Const(max(selected.vulmin, min(selected.vulmax, selected.reference0))),
    )
    template: RmsModelTemplate = control.finish(
        (output,), 'IEEE 421.5 UEL1 under-excitation limiter',
    )
    return template
