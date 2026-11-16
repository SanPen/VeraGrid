# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
# SPDX-License-Identifier: MPL-2.0
"""CIMTR1 induction generator with rotor-flux transients."""

from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Templates.Rms.common.auxiliary_functions import (
    InductionMachineRole,
    build_induction_machine,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var


class Cimtr1Parameters:
    """Store CIMTR1 source values for the provisional unsaturated kernel."""

    __slots__ = (
        't_prime', 't_double_prime', 'inertia', 'x', 'x_prime',
        'x_double_prime', 'x_leakage', 'e1', 'se1', 'e2', 'se2', 'ra',
    )

    def __init__(self, t_prime: float = 0.6, t_double_prime: float = 0.05,
                 inertia: float = 0.8, x: float = 3.0, x_prime: float = 0.3,
                 x_double_prime: float = 0.2, x_leakage: float = 0.2,
                 e1: float = 0.0, se1: float = 0.0, e2: float = 0.0,
                 se2: float = 0.0, ra: float = 0.015) -> None:
        """Store source parameters, including machine-source resistance.

        :param t_prime: Transient rotor time constant in seconds.
        :param t_double_prime: Subtransient rotor time constant in seconds.
        :param inertia: Machine-base inertia constant in seconds.
        :param x: Synchronous reactance in machine pu.
        :param x_prime: Transient reactance in machine pu.
        :param x_double_prime: Subtransient reactance in machine pu.
        :param x_leakage: Leakage reactance in machine pu; retained for validation.
        :param e1: First saturation voltage point.
        :param se1: Saturation factor at ``e1``.
        :param e2: Second saturation voltage point.
        :param se2: Saturation factor at ``e2``.
        :param ra: Machine source resistance in pu, supplied from machine data.
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
        self.ra: float = ra


def build_cimtr1_template(
        vf: VarFactory,
        name: str | None = None,
        parameters: Cimtr1Parameters | None = None,
) -> RmsModelTemplate:
    """Build the CIMTR1 induction-generator template.

    :param vf: Variable factory used to allocate the symbolic model variables.
    :type vf: VarFactory
    :param name: Optional instance name for the returned template.
        :param parameters: Source-order CIMTR1 machine data. The existing
        unsaturated fifth-order kernel is parameterized; full source conversion
        still requires saturation and initialization support.
    :returns: Fully assembled CIMTR1 dynamic template.
    :raises ValueError: Saturation or single-cage reductions are requested.
    """
    # Resolve the optional name before building the model so the shared
    # induction-machine implementation always receives an explicit identity.
    template_name: str
    if name is None:
        template_name: str = 'CIMTR1'
    else:
        template_name: str = name

    selected: Cimtr1Parameters = Cimtr1Parameters() if parameters is None else parameters
    values: tuple[float, ...] = (
        selected.t_prime, selected.t_double_prime, selected.inertia, selected.x,
        selected.x_prime, selected.x_double_prime, selected.x_leakage,
        selected.e1, selected.se1, selected.e2, selected.se2, selected.ra,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('CIMTR1 parameters must be finite')
    elif (selected.t_prime <= 0.0 or selected.t_double_prime <= 0.0
          or selected.inertia <= 0.0 or selected.x_prime <= 0.0
          or selected.x_double_prime <= 0.0 or selected.x <= selected.x_prime
          or selected.x_prime <= selected.x_double_prime
          or selected.x_leakage < 0.0 or selected.ra < 0.0):
        raise ValueError('CIMTR1 requires ordered positive two-cage machine parameters')
    elif selected.se1 != 0.0 or selected.se2 != 0.0:
        raise ValueError('CIMTR1 saturation is not represented by this native reduction')
    else:
        pass

    # Select the generator equations explicitly; the Enum prevents a string
    # option from silently choosing the wrong active-power sign convention.
    template: RmsModelTemplate = build_induction_machine(
        vf=vf,
        name=template_name,
        role=InductionMachineRole.GENERATOR,
    )
    # Xl is not present in the published unsaturated fifth-order state equations.
    # Bind the remaining source constants directly to the shared flux kernel.
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
            if parameter.name == suffix + template_name:
                template.block.event_dict[parameter] = Const(value)
            else:
                pass
    template.tpe = DeviceType.GeneratorDevice
    template.comment = 'Generator CIMTR1 induction generator'
    return template
