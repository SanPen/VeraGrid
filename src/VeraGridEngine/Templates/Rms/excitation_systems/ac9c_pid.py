# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""AC9C proportional-integral-derivative voltage regulator core."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Ac9cPidSettings:
    """Store the AC9C regulator gains, output limits and initialization point."""

    __slots__ = ('kpr', 'kir', 'kdr', 'tdr', 'vpidmax', 'vpidmin', 'error0', 'vpid0')

    def __init__(self, kpr: float = 10.0, kir: float = 10.0,
                 kdr: float = 0.0, tdr: float = 0.01,
                 vpidmax: float = 1.6, vpidmin: float = 0.0,
                 error0: float = 0.0, vpid0: float = 0.0) -> None:
        """Store parameters in per-unit and seconds.

        :param kpr: Proportional regulator gain.
        :param kir: Integral regulator gain per second.
        :param kdr: Derivative regulator gain in pu-seconds.
        :param tdr: Derivative-channel lag time in seconds.
        :param vpidmax: Upper regulator output capability.
        :param vpidmin: Lower regulator output capability.
        :param error0: Initial input error at the solved operating point.
        :param vpid0: Initial bounded regulator output.
        """
        self.kpr: float = kpr
        self.kir: float = kir
        self.kdr: float = kdr
        self.tdr: float = tdr
        self.vpidmax: float = vpidmax
        self.vpidmin: float = vpidmin
        self.error0: float = error0
        self.vpid0: float = vpid0


def build_ac9c_pid_template(
        vf: VarFactory,
        name: str = 'AC9C PID regulator',
        settings: Ac9cPidSettings | None = None,
) -> RmsModelTemplate:
    """Build the two-state PID core after the AC9C voltage-error summing point.

    The integral memory follows ``KIR*error``. A positive ``TDR`` filters the
    derivative input and produces ``KDR/TDR*(error-memory)``; zero ``TDR`` is
    accepted only when derivative gain is zero. The P/I/D sum is statically
    bounded by ``VPIDMIN`` and ``VPIDMAX``. Error routing, terminal transducer,
    limiter gates and excitation source remain owned by the surrounding AC9C
    composition.

    :param vf: Symbol factory owning the PID state and equations.
    :param name: Unique component label.
    :param settings: Regulator gains, limits and solved initial values.
    :return: Native PID component with output ``VPIDPu``.
    :raises ValueError: Gains, time or output limits are invalid.
    """
    selected: Ac9cPidSettings = Ac9cPidSettings() if settings is None else settings
    values: tuple[float, ...] = (
        selected.kpr, selected.kir, selected.kdr, selected.tdr,
        selected.vpidmax, selected.vpidmin, selected.error0, selected.vpid0,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('AC9C PID settings must be finite')
    elif selected.kpr < 0.0 or selected.kir < 0.0 or selected.kdr < 0.0:
        raise ValueError('AC9C PID gains must be nonnegative')
    elif selected.tdr < 0.0 or (selected.tdr == 0.0 and selected.kdr != 0.0):
        raise ValueError('AC9C derivative gain requires a positive TDR')
    elif selected.vpidmin >= selected.vpidmax:
        raise ValueError('AC9C PID output limits must be ordered')
    elif not selected.vpidmin <= selected.vpid0 <= selected.vpidmax:
        raise ValueError('AC9C initial PID output must lie within its limits')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, name)
    kpr: Var = control.parameter('KPR', selected.kpr)
    kir: Var = control.parameter('KIR', selected.kir)
    kdr: Var = control.parameter('KDR', selected.kdr)
    tdr: Var = control.parameter('TDR', selected.tdr)
    maximum: Var = control.parameter('VPIDMAX', selected.vpidmax)
    minimum: Var = control.parameter('VPIDMIN', selected.vpidmin)
    error: Var = control.input('VoltageErrorPu', Const(selected.error0))
    integral_initial: float = selected.vpid0 - selected.kpr * selected.error0
    integral: Var = vf.add_var('PIDIntegratorPu_' + name)
    control.differential(integral, kir * error, Const(integral_initial))
    if selected.tdr > 0.0:
        derivative_memory: Var = control.lag(
            'PIDDerivativeMemoryPu', error, tdr, selected.tdr, Const(selected.error0),
        )
        derivative: Expr = kdr / tdr * (error - derivative_memory)
    else:
        derivative = Const(0.0)
    raw_output: Expr = kpr * error + integral + derivative
    output_expression: Expr = sym.hard_sat(raw_output, minimum, maximum)
    output: Var = control.algebraic('VPIDPu', output_expression, Const(selected.vpid0))
    return control.finish((output,), 'AC9C bounded proportional-integral-derivative regulator core')
