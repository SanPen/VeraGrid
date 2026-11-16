# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""DERA1 active/reactive current-priority circle from PSS/E 35.2 §17.1."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def build_dera1_current_limit_template(
        vf: VarFactory,
        name: str = 'DERA1 current limit',
        imax: float = 1.0,
        active_current_priority: bool = False,
        generator: bool = True,
) -> RmsModelTemplate:
    """Limit DERA1 current commands using its selected P/Q priority.

    PSS/E defines the unused current capability as the circle remaining after
    the priority command. Generator mode clips active injection at zero;
    storage mode permits active charging down to the circle limit.

    :param vf: Shared symbolic variable factory.
    :param name: Unique component name.
    :param imax: Maximum converter current in per unit.
    :param active_current_priority: True selects P priority; false selects Q.
    :param generator: True restricts active current to nonnegative injection.
    :return: Algebraic component with limited active/reactive current outputs.
    :raises ValueError: Invalid current limit or selector values.
    """
    if not math.isfinite(imax) or imax <= 0.0:
        raise ValueError('DERA1 Imax must be finite and positive')
    elif not isinstance(active_current_priority, bool) or not isinstance(generator, bool):
        raise ValueError('DERA1 priority and generator selectors must be Boolean')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, name)
    active_command: Var = control.input('ActiveCurrentCommandPu', Const(0.0))
    reactive_command: Var = control.input('ReactiveCurrentCommandPu', Const(0.0))
    limit: Var = control.parameter('IMAX', imax)
    if active_current_priority:
        active_limit: Var = control.algebraic(
            'ActiveCurrentCapabilityPu', limit, Const(imax),
        )
        reactive_limit: Var = control.algebraic(
            'ReactiveCurrentCapabilityPu',
            sym.sqrt(sym.max(limit * limit - active_command * active_command, Const(0.0))),
            Const(imax),
        )
    else:
        reactive_limit = control.algebraic(
            'ReactiveCurrentCapabilityPu', limit, Const(imax),
        )
        active_limit = control.algebraic(
            'ActiveCurrentCapabilityPu',
            sym.sqrt(sym.max(limit * limit - reactive_command * reactive_command, Const(0.0))),
            Const(imax),
        )

    active_minimum: Const | Var = Const(0.0) if generator else -active_limit
    limited_active: Var = control.algebraic(
        'LimitedActiveCurrentPu',
        sym.hard_sat(active_command, active_minimum, active_limit), Const(0.0),
    )
    limited_reactive: Var = control.algebraic(
        'LimitedReactiveCurrentPu',
        sym.hard_sat(reactive_command, -reactive_limit, reactive_limit), Const(0.0),
    )
    return control.finish((limited_active, limited_reactive),
                          'DERA1 P/Q-priority current circle')
