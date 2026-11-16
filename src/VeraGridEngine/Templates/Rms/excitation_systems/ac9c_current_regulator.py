# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""AC9C field-current proportional-integral regulator stage."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Ac9cCurrentRegulatorSettings:
    """Store AC9C field-current PI gains and regulator limits."""

    __slots__ = ('kpa', 'kia', 'vamax', 'vamin', 'error0', 'vavr0')

    def __init__(self, kpa: float = 1.0, kia: float = 1.0, vamax: float = 1.0,
                 vamin: float = -1.0, error0: float = 0.0, vavr0: float = 0.0) -> None:
        """Store gains, bounds and equilibrium values.

        :param kpa: Proportional field-current regulator gain.
        :param kia: Integral field-current regulator gain per second.
        :param vamax: Maximum regulator output.
        :param vamin: Minimum regulator output.
        :param error0: Initial routed field-current error.
        :param vavr0: Initial bounded regulator output.
        """
        self.kpa: float = kpa
        self.kia: float = kia
        self.vamax: float = vamax
        self.vamin: float = vamin
        self.error0: float = error0
        self.vavr0: float = vavr0


def build_ac9c_current_regulator_template(
        vf: VarFactory,
        name: str = 'AC9C field-current regulator',
        settings: Ac9cCurrentRegulatorSettings | None = None,
) -> RmsModelTemplate:
    """Build the source PI stage after AC9C's limiter gates.

    The integrator follows ``KIA*error`` and the proportional-integral sum is
    bounded by ``VAMIN`` and ``VAMAX``. The error port is the output of the
    source HV/LV limiter gates, whose ICON-dependent routing remains external.

    :param vf: Symbol factory owning controller symbols.
    :param name: Unique component label.
    :param settings: Gains, bounds and solved initial values.
    :return: Native component exposing ``VAVRPu``.
    :raises ValueError: Nonfinite values, negative gains or invalid bounds.
    """
    selected: Ac9cCurrentRegulatorSettings = (
        Ac9cCurrentRegulatorSettings() if settings is None else settings
    )
    values: tuple[float, ...] = (
        selected.kpa, selected.kia, selected.vamax, selected.vamin,
        selected.error0, selected.vavr0,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('AC9C current-regulator settings must be finite')
    elif selected.kpa < 0.0 or selected.kia < 0.0:
        raise ValueError('AC9C current-regulator gains must be nonnegative')
    elif selected.vamin >= selected.vamax:
        raise ValueError('AC9C current-regulator output limits must be ordered')
    elif not selected.vamin <= selected.vavr0 <= selected.vamax:
        raise ValueError('AC9C initial regulator output must lie within its limits')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, name)
    kpa: Var = control.parameter('KPA', selected.kpa)
    kia: Var = control.parameter('KIA', selected.kia)
    maximum: Var = control.parameter('VAMAX', selected.vamax)
    minimum: Var = control.parameter('VAMIN', selected.vamin)
    error: Var = control.input('GatedCurrentErrorPu', Const(selected.error0))
    integral_initial: float = selected.vavr0 - selected.kpa * selected.error0
    integral: Var = vf.add_var('CurrentRegulatorIntegratorPu_' + name)
    control.differential(integral, kia * error, Const(integral_initial))
    raw_output = kpa * error + integral
    output_expression = sym.hard_sat(raw_output, minimum, maximum)
    output: Var = control.algebraic('VAVRPu', output_expression, Const(selected.vavr0))
    return control.finish((output,), 'AC9C bounded field-current PI regulator')
