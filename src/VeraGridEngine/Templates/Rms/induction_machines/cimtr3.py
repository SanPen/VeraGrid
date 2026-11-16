# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""CIMTR3 induction generator with rotor-angle deviation."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import DeviceType, InductionMachineRole
from VeraGridEngine.Templates.Rms.common.auxiliary_functions import (
    build_induction_machine,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var


class Cimtr3Parameters:
    """Store PSS/E CIMTR3 source constants for post-start dynamics."""

    __slots__ = (
        't_prime', 't_double_prime', 'inertia', 'x', 'x_prime',
        'x_double_prime', 'x_leakage', 'e1', 'se1', 'e2', 'se2',
        'switch', 'synchronous_power', 'ra',
    )

    def __init__(
            self, t_prime: float = 0.6, t_double_prime: float = 0.05,
            inertia: float = 0.8, x: float = 3.0, x_prime: float = 0.3,
            x_double_prime: float = 0.2, x_leakage: float = 0.2,
            e1: float = 0.0, se1: float = 0.0, e2: float = 0.0,
            se2: float = 0.0, switch: int = 0,
            synchronous_power: float = 1.0, ra: float = 0.015,
    ) -> None:
        """Store source data and stator resistance supplied by RAW.

        :param t_prime: Transient rotor time constant in seconds.
        :param t_double_prime: Subtransient rotor time constant in seconds.
        :param inertia: Inertia constant on the machine base.
        :param x: Synchronous reactance in per unit.
        :param x_prime: Transient reactance in per unit.
        :param x_double_prime: Subtransient reactance in per unit.
        :param x_leakage: Leakage reactance retained for validation.
        :param e1: First saturation voltage point.
        :param se1: Saturation factor at ``e1``.
        :param e2: Second saturation voltage point.
        :param se2: Saturation factor at ``e2``.
        :param switch: Source switch; PAGV2 states it does not affect the model.
        :param synchronous_power: Positive starting-only mechanical power.
        :param ra: Stator resistance supplied by the associated RAW machine.
        """
        self.t_prime: float = t_prime
        self.t_double_prime: float = t_double_prime
        self.inertia: float = inertia
        self.x: float = x
        self.x_prime: float = x_prime
        self.x_double_prime: float = x_double_prime
        self.x_leakage: float = x_leakage
        self.e1: float = e1
        self.se1: float = se1
        self.e2: float = e2
        self.se2: float = se2
        self.switch: int = switch
        self.synchronous_power: float = synchronous_power
        self.ra: float = ra


def build_cimtr3_template(
        vf: VarFactory,
        name: str | None = None,
        parameters: Cimtr3Parameters | None = None,
) -> RmsModelTemplate:
    """Build CIMTR3's unsaturated two-cage generator component.

    The model adds the rotor-angle deviation kinematic state to the CIMTR1
    generator equations. ``SYNPOW`` applies only to starting and therefore
    does not alter post-start dynamics; startup sequencing is not modeled here.

    :param vf: Variable factory that owns the model symbols.
    :param name: Optional unique model name.
    :param parameters: PSS/E source constants and RAW stator resistance.
    :return: Six-state induction-generator template.
    :raises ValueError: Unsupported source modes or invalid two-cage constants.
    """
    label: str = 'CIMTR3' if name is None else name
    selected: Cimtr3Parameters = Cimtr3Parameters() if parameters is None else parameters
    values: tuple[float, ...] = (
        selected.t_prime, selected.t_double_prime, selected.inertia,
        selected.x, selected.x_prime, selected.x_double_prime,
        selected.x_leakage, selected.e1, selected.se1, selected.e2,
        selected.se2, selected.synchronous_power, selected.ra,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('CIMTR3 parameters must be finite')
    elif (
            selected.t_prime <= 0.0 or selected.t_double_prime <= 0.0
            or selected.inertia <= 0.0 or selected.x <= selected.x_prime
            or selected.x_prime <= selected.x_double_prime
            or selected.x_double_prime <= 0.0 or selected.x_leakage < 0.0
            or selected.synchronous_power <= 0.0 or selected.ra < 0.0):
        raise ValueError('CIMTR3 requires ordered two-cage parameters and positive SYNPOW')
    elif selected.se1 != 0.0 or selected.se2 != 0.0:
        raise ValueError('CIMTR3 saturation is not represented by this native reduction')
    elif selected.switch not in (0, 1):
        raise ValueError('CIMTR3 switch must be 0 or 1')
    else:
        pass

    # The generator role preserves injected-power signs; the extra state tracks rotor angle.
    template: RmsModelTemplate = build_induction_machine(
        vf=vf, name=label, role=InductionMachineRole.GENERATOR,
        angle_deviation=True,
    )
    parameter_values: tuple[tuple[str, float], ...] = (
        ('RaPu_', selected.ra), ('XsPu_', selected.x),
        ('XpPu_', selected.x_prime), ('XppPu_', selected.x_double_prime),
        ('Tp0_', selected.t_prime), ('Tpp0_', selected.t_double_prime),
        ('H_', selected.inertia),
    )
    parameter: Var
    suffix: str
    value: float
    for parameter in template.block.event_dict:
        for suffix, value in parameter_values:
            if parameter.name == suffix + label:
                template.block.event_dict[parameter] = Const(value)
            else:
                pass
    template.tpe = DeviceType.GeneratorDevice
    template.comment = 'PSS/E CIMTR3 post-start induction generator component'
    return template
