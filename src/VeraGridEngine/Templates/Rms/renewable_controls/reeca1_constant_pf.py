# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""REECA1 constant power-factor reference for PFFLAG=1 and QFLAG=0."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Reeca1ConstantPfSettings:
    """Store the electrical-power measurement lag for local pf control."""

    __slots__ = ('tp',)

    def __init__(self, tp: float = .02) -> None:
        """Store the source electrical-power filter time.

        :param tp: Pe filter time constant in seconds.
        :return: None.
        """
        self.tp: float = tp


def build_reeca1_constant_pf_template(
        vf: VarFactory,
        name: str = 'REECA1 local constant pf',
        settings: Reeca1ConstantPfSettings | None = None,
) -> RmsModelTemplate:
    """Filter measured Pe and multiply by the fixed initial pf-angle tangent.

    The output replaces Qext ahead of the shared Qmin/Qmax and Tiq path.
    The angle must come from the connected generator's solved P and Q.

    :param vf: Shared symbolic variable factory.
    :param name: Unique controller instance name.
    :param settings: Electrical-power filter time.
    :return: Controller with Pe and pf-angle inputs, and reactive-power reference.
    :raises ValueError: Negative or nonfinite filter time.
    """
    selected: Reeca1ConstantPfSettings = Reeca1ConstantPfSettings() if settings is None else settings
    if not math.isfinite(selected.tp) or selected.tp < 0:
        raise ValueError('REECA1 electrical-power filter time is invalid')
    else:
        pass
    control: ControlRealization = ControlRealization(vf, name)
    pe: Var = control.input('ElectricalPowerPu', Const(0.))
    pf_angle: Var = control.input('PfAngleRad', Const(0.))
    tp: Var = control.parameter('TP', selected.tp)
    filtered_pe: Var = control.lag('FilteredElectricalPowerPu', pe, tp,
                                   selected.tp, Const(0.))
    q_reference: Var = control.algebraic(
        'PfReactiveReferencePu', filtered_pe * sym.tan(pf_angle), Const(0.),
    )
    return control.finish((q_reference,), 'REECA1 local power-factor reactive reference')
