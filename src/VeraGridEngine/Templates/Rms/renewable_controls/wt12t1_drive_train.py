# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""WT12T1 Type 1/2 wind two-mass shaft with torque-input ports."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


class Wt12t1DriveTrainSettings:
    """Store the five PSS/E shaft constants and host frequency/slip context."""

    __slots__ = ('h', 'damp', 'htfrac', 'freq1', 'dshaft', 'nominal_frequency_hz', 'initial_speed')

    def __init__(self, h: float = 4., damp: float = 0., htfrac: float = .5,
                 freq1: float = 2., dshaft: float = 1.,
                 nominal_frequency_hz: float = 50., initial_speed: float = 1.) -> None:
        """Store source data on the generator MVA base.

        :param h: Total inertia constant in seconds.
        :param damp: Generator damping torque per unit speed.
        :param htfrac: Turbine share of total inertia; zero selects one mass.
        :param freq1: First torsional resonant frequency in hertz.
        :param dshaft: Shaft damping torque per unit speed difference.
        :param nominal_frequency_hz: Network base frequency in hertz.
        :param initial_speed: Machine initial generator/turbine speed in per unit.
        :return: None.
        """
        self.h: float = h
        self.damp: float = damp
        self.htfrac: float = htfrac
        self.freq1: float = freq1
        self.dshaft: float = dshaft
        self.nominal_frequency_hz: float = nominal_frequency_hz
        self.initial_speed: float = initial_speed


def build_wt12t1_drive_train_template(
        vf: VarFactory, name: str = 'WT12T1 drive train',
        settings: Wt12t1DriveTrainSettings | None = None,
) -> RmsModelTemplate:
    """Build Type 1/2 shaft motion from mechanical and electrical torques.

    The induction-machine host must supply both torques and the initial slip.
    The first output is generator speed for WT12A1 feedback.

    :param vf: Shared symbolic variable factory.
    :param name: Unique model name.
    :param settings: Source shaft and host context values.
    :return: Native one- or two-mass Type 1/2 shaft template.
    :raises ValueError: Invalid inertia, damping, frequency or initial speed.
    """
    selected: Wt12t1DriveTrainSettings = Wt12t1DriveTrainSettings() if settings is None else settings
    values: tuple[float, ...] = (selected.h, selected.damp, selected.htfrac,
                                 selected.freq1, selected.dshaft,
                                 selected.nominal_frequency_hz, selected.initial_speed)
    if not all(math.isfinite(value) for value in values):
        raise ValueError('WT12T1 settings must be finite')
    elif selected.h <= 0 or not 0 <= selected.htfrac < 1:
        raise ValueError('WT12T1 inertia or turbine fraction is invalid')
    elif selected.damp < 0 or selected.dshaft < 0 or selected.nominal_frequency_hz <= 0:
        raise ValueError('WT12T1 damping or base frequency is invalid')
    elif selected.htfrac > 0 and selected.freq1 <= 0:
        raise ValueError('WT12T1 two-mass shaft frequency must be positive')
    elif selected.initial_speed <= 0:
        raise ValueError('WT12T1 initial speed must be positive')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, name)
    electrical_torque: Var = control.input('ElectricalTorquePu', Const(0.))
    mechanical_torque: Var = control.input('MechanicalTorquePu', electrical_torque)
    h: Var = control.parameter('H', selected.h)
    damp: Var = control.parameter('DAMP', selected.damp)
    htfrac: Var = control.parameter('HTFRAC', selected.htfrac)
    freq1: Var = control.parameter('FREQ1', selected.freq1)
    dshaft: Var = control.parameter('DSHAFT', selected.dshaft)
    base_frequency: Var = control.parameter('NominalFrequencyHz', selected.nominal_frequency_hz)
    initial_speed: Var = control.parameter('InitialSpeedPu', selected.initial_speed)
    omega_base: Expr = Const(2. * math.pi) * base_frequency
    rotor_angle: Var = vf.add_var('GeneratorRotorAngleDeviation_' + name)

    if selected.htfrac == 0:
        # The source's Htfrac=0 removes the singular shaft and turbine mass.
        generator_speed: Var = vf.add_var('GeneratorSpeedPu_' + name)
        control.differential(
            generator_speed,
            (mechanical_torque - electrical_torque
             - damp * (generator_speed - initial_speed)) / (Const(2.) * h),
            initial_speed,
        )
        control.differential(rotor_angle, omega_base * (generator_speed - initial_speed), Const(0.))
        turbine_speed: Var = control.algebraic('TurbineSpeedPu', generator_speed, initial_speed)
    else:
        # Shaft torque integrates speed separation through the source stiffness.
        turbine_inertia: Expr = h * htfrac
        generator_inertia: Expr = h - turbine_inertia
        stiffness: Expr = (Const(2.) * turbine_inertia * generator_inertia
                           * (Const(2. * math.pi) * freq1) ** Const(2.) / h)
        shaft_twist: Var = vf.add_var('ShaftTwistAngle_' + name)
        turbine_speed = vf.add_var('TurbineSpeedPu_' + name)
        generator_speed = vf.add_var('GeneratorSpeedPu_' + name)
        speed_difference: Expr = turbine_speed - generator_speed
        shaft_torque: Expr = stiffness * shaft_twist / omega_base
        damping_torque: Expr = dshaft * speed_difference
        initial_twist: Expr = electrical_torque * omega_base / stiffness
        control.differential(shaft_twist, omega_base * speed_difference, initial_twist)
        control.differential(
            turbine_speed,
            (mechanical_torque - shaft_torque - damping_torque) / (Const(2.) * turbine_inertia),
            initial_speed,
        )
        control.differential(
            generator_speed,
            (shaft_torque + damping_torque - electrical_torque
             - damp * (generator_speed - initial_speed)) / (Const(2.) * generator_inertia),
            initial_speed,
        )
        control.differential(rotor_angle, omega_base * (generator_speed - initial_speed), Const(0.))

    return control.finish((generator_speed, turbine_speed, rotor_angle),
                          'Type 1/2 wind shaft with torque-input coupling')
