# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""REECA1 QFLAG=0 reactive-current path after the PFFLAG selector."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Reeca1ConstantQSettings:
    """Store the local constant-Q path's reactive limits and lag time."""

    __slots__ = ('tiq', 'qmin', 'qmax')

    def __init__(self, tiq: float = .02, qmin: float = -999., qmax: float = 999.) -> None:
        """Store Q-path parameters on the generator MVA base.

        :param tiq: Reactive-current lag time in seconds.
        :param qmin: Lower Qext limit in per unit.
        :param qmax: Upper Qext limit in per unit.
        :return: None.
        """
        self.tiq: float = tiq
        self.qmin: float = qmin
        self.qmax: float = qmax


def build_reeca1_constant_q_template(
        vf: VarFactory,
        name: str = 'REECA1 local constant Q',
        settings: Reeca1ConstantQSettings | None = None,
) -> RmsModelTemplate:
    """Build the QFLAG=0 branch after Qext or pf-reference selection.

    The selected Q reference is limited, converted to current with filtered
    voltage, then passed through the source Tiq lag. VFLAG does not select this branch. The output
    is the base Iq command; voltage-fault injection is added downstream.

    :param vf: Shared symbolic variable factory.
    :param name: Unique controller instance name.
    :param settings: Tiq and reactive-power reference bounds.
    :return: Controller with Qext and filtered-voltage inputs, and base Iq output.
    :raises ValueError: Invalid lag time or Q bounds.
    """
    selected: Reeca1ConstantQSettings = Reeca1ConstantQSettings() if settings is None else settings
    if not all(math.isfinite(value) for value in (selected.tiq, selected.qmin, selected.qmax)):
        raise ValueError('REECA1 constant-Q settings must be finite')
    elif selected.tiq < 0 or selected.qmax <= selected.qmin:
        raise ValueError('REECA1 constant-Q time or limits are invalid')
    else:
        pass
    control: ControlRealization = ControlRealization(vf, name)
    qext: Var = control.input('QextPu', Const(0.))
    filtered: Var = control.input('FilteredVoltagePu', Const(1.))
    tiq: Var = control.parameter('TIQ', selected.tiq)
    qmin: Var = control.parameter('QMIN', selected.qmin)
    qmax: Var = control.parameter('QMAX', selected.qmax)
    # Apply the source's Q-reference bounds before conversion to current;
    # Tiq then delays that current demand, not the reactive power itself.
    target: Expr = sym.hard_sat(qext, qmin, qmax) / sym.max(filtered, Const(.01))
    base_current: Var = control.lag('BaseReactiveCurrentPu', target, tiq,
                                    selected.tiq, Const(0.))
    return control.finish((base_current,), 'REECA1 local constant-Q current-order path')
