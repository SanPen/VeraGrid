# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""CIMTR4 induction motor with load torque law and rotor-angle deviation."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import DeviceType, InductionMachineRole
from VeraGridEngine.Templates.Rms.common.auxiliary_functions import (
    build_induction_machine,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var


class Cimtr4Parameters:
    """Store PSS/E CIMTR4 source constants for post-start dynamics."""

    __slots__ = (
        't_prime', 't_double_prime', 'inertia', 'x', 'x_prime',
        'x_double_prime', 'x_leakage', 'e1', 'se1', 'e2', 'se2',
        'load_torque_exponent', 'synchronous_torque', 'ra',
    )

    def __init__(
            self, t_prime: float = 0.6, t_double_prime: float = 0.05,
            inertia: float = 0.8, x: float = 3.0, x_prime: float = 0.3,
            x_double_prime: float = 0.2, x_leakage: float = 0.2,
            e1: float = 0.0, se1: float = 0.0, e2: float = 0.0,
            se2: float = 0.0, load_torque_exponent: float = 1.0,
            synchronous_torque: float = -1.0, ra: float = 0.015,
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
        :param load_torque_exponent: PSS/E exponent in ``Tnom * speed**D``.
        :param synchronous_torque: Negative starting-only synchronous torque.
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
        self.load_torque_exponent: float = load_torque_exponent
        self.synchronous_torque: float = synchronous_torque
        self.ra: float = ra


def build_cimtr4_template(
        vf: VarFactory,
        name: str | None = None,
        parameters: Cimtr4Parameters | None = None,
) -> RmsModelTemplate:
    """Build CIMTR4's unsaturated two-cage motor component.

    The model adds rotor-angle deviation to the CIMTR2 motor equations.
    ``SYNTOR`` applies only to starting and does not change post-start dynamics;
    startup sequencing is not modeled by this component.

    :param vf: Variable factory that owns the model symbols.
    :param name: Optional unique model name.
    :param parameters: PSS/E source constants and RAW stator resistance.
    :return: Six-state induction-motor template.
    :raises ValueError: Unsupported source modes or invalid two-cage constants.
    """
    label: str = 'CIMTR4' if name is None else name
    selected: Cimtr4Parameters = Cimtr4Parameters() if parameters is None else parameters
    values: tuple[float, ...] = (
        selected.t_prime, selected.t_double_prime, selected.inertia,
        selected.x, selected.x_prime, selected.x_double_prime,
        selected.x_leakage, selected.e1, selected.se1, selected.e2,
        selected.se2, selected.load_torque_exponent, selected.synchronous_torque,
        selected.ra,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('CIMTR4 parameters must be finite')
    elif (
            selected.t_prime <= 0.0 or selected.t_double_prime <= 0.0
            or selected.inertia <= 0.0 or selected.x <= selected.x_prime
            or selected.x_prime <= selected.x_double_prime
            or selected.x_double_prime <= 0.0 or selected.x_leakage < 0.0
            or selected.load_torque_exponent < 0.0 or selected.synchronous_torque >= 0.0
            or selected.ra < 0.0):
        raise ValueError('CIMTR4 requires ordered two-cage parameters and negative SYNTOR')
    elif selected.se1 != 0.0 or selected.se2 != 0.0:
        raise ValueError('CIMTR4 saturation is not represented by this native reduction')
    else:
        pass

    # The motor role uses its polynomial torque law; choose Tnom*speed**D exactly.
    template: RmsModelTemplate = build_induction_machine(
        vf=vf, name=label, role=InductionMachineRole.MOTOR,
        angle_deviation=True,
    )
    parameter_values: tuple[tuple[str, float], ...] = (
        ('RaPu_', selected.ra), ('XsPu_', selected.x),
        ('XpPu_', selected.x_prime), ('XppPu_', selected.x_double_prime),
        ('Tp0_', selected.t_prime), ('Tpp0_', selected.t_double_prime),
        ('H_', selected.inertia), ('D_', 1.0),
        ('E_', selected.load_torque_exponent),
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
    template.comment = 'PSS/E CIMTR4 post-start induction motor component'
    return template
