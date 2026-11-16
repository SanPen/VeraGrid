# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Native wind drive-train equations shared by the WTDTA1 model family."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


class Wtdta1DriveTrainSettings:
    """Store the five drive-train parameters and system-frequency context."""

    __slots__ = ('h', 'damp', 'htfrac', 'freq1', 'dshaft', 'nominal_frequency_hz', 'initial_speed')

    def __init__(self, h: float = 4., damp: float = 0., htfrac: float = .5,
                 freq1: float = 2., dshaft: float = 1.,
                 nominal_frequency_hz: float = 50., initial_speed: float = 1.) -> None:
        """Store source parameters on the generator MVA base.

        :param h: Total inertia constant, seconds.
        :param damp: Generator speed damping, per-unit torque per-unit speed.
        :param htfrac: Turbine fraction of total inertia; zero selects one mass.
        :param freq1: First shaft torsional resonant frequency, hertz.
        :param dshaft: Shaft speed-difference damping, per unit.
        :param nominal_frequency_hz: Network nominal frequency, hertz.
        :param initial_speed: Initial turbine and generator speed, per unit.
        :return: None.
        """
        self.h: float = h
        self.damp: float = damp
        self.htfrac: float = htfrac
        self.freq1: float = freq1
        self.dshaft: float = dshaft
        self.nominal_frequency_hz: float = nominal_frequency_hz
        self.initial_speed: float = initial_speed


def build_wtdta1_drive_train_template(
        vf: VarFactory,
        name: str = 'WTDTA1 drive train',
        settings: Wtdta1DriveTrainSettings | None = None,
) -> RmsModelTemplate:
    """Build the two-mass shaft or source-declared one-mass reduction.

    The first two inputs are electrical and aerodynamic power on machine base.
    Generator speed, turbine speed and rotor-angle deviation are outputs.
    Source binding still requires neighboring torque/aerodynamic controls and
    explicit machine-base power wiring.

    :param vf: Shared symbolic variable factory.
    :param name: Unique drive-train instance name.
    :param settings: WTDTA1 physical and system-frequency settings.
    :return: Stand-alone native drive-train control template.
    :raises ValueError: Invalid inertia, frequency, damping or speed.
    """
    selected: Wtdta1DriveTrainSettings = Wtdta1DriveTrainSettings() if settings is None else settings
    values: tuple[float, ...] = (selected.h, selected.damp, selected.htfrac,
                                 selected.freq1, selected.dshaft,
                                 selected.nominal_frequency_hz, selected.initial_speed)
    if not all(math.isfinite(value) for value in values):
        raise ValueError('WTDTA1 settings must be finite')
    elif selected.h <= 0 or selected.htfrac < 0 or selected.htfrac >= 1:
        raise ValueError('WTDTA1 inertia or turbine fraction is invalid')
    elif selected.damp < 0 or selected.dshaft < 0 or selected.nominal_frequency_hz <= 0:
        raise ValueError('WTDTA1 damping or nominal frequency is invalid')
    elif selected.htfrac > 0 and selected.freq1 <= 0:
        raise ValueError('WTDTA1 two-mass shaft frequency must be positive')
    elif selected.initial_speed <= 0:
        raise ValueError('WTDTA1 initial speed must be positive')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, name)
    electrical_power: Var = control.input('ElectricalPowerPu', Const(0.))
    mechanical_power: Var = control.input('MechanicalPowerPu', electrical_power)
    h: Var = control.parameter('H', selected.h)
    damp: Var = control.parameter('DAMP', selected.damp)
    htfrac: Var = control.parameter('HTFRAC', selected.htfrac)
    freq1: Var = control.parameter('FREQ1', selected.freq1)
    dshaft: Var = control.parameter('DSHAFT', selected.dshaft)
    nominal_frequency: Var = control.parameter('NominalFrequencyHz', selected.nominal_frequency_hz)
    initial_speed: Var = control.parameter('InitialSpeedPu', selected.initial_speed)
    omega_base: Expr = Const(2. * math.pi) * nominal_frequency
    rotor_angle: Var = vf.add_var('GeneratorRotorAngleDeviation_' + name)

    if selected.htfrac == 0:
        # The zero turbine inertia declared by PSS/E removes the shaft mode.
        generator_speed: Var = vf.add_var('GeneratorSpeedPu_' + name)
        generator_acceleration: Expr = ((mechanical_power - electrical_power) / generator_speed
                                        - damp * (generator_speed - initial_speed)) / (Const(2.) * h)
        control.differential(generator_speed, generator_acceleration, initial_speed)
        control.differential(rotor_angle, omega_base * (generator_speed - initial_speed), Const(0.))
        turbine_speed: Var = control.algebraic('TurbineSpeedPu', generator_speed, initial_speed)
    else:
        # The source stiffness is given in torque per per-unit speed integral;
        # convert the shaft-angle state in radians using network base speed.
        turbine_inertia: Expr = h * htfrac
        generator_inertia: Expr = h - turbine_inertia
        stiffness: Expr = (Const(2.) * turbine_inertia * generator_inertia
                           * (Const(2. * math.pi) * freq1) ** Const(2.) / h)
        shaft_angle: Var = vf.add_var('ShaftTwistAngle_' + name)
        turbine_speed = vf.add_var('TurbineSpeedPu_' + name)
        generator_speed = vf.add_var('GeneratorSpeedPu_' + name)
        speed_difference: Expr = turbine_speed - generator_speed
        shaft_torque: Expr = stiffness * shaft_angle / omega_base
        damping_torque: Expr = dshaft * speed_difference
        initial_twist: Expr = electrical_power / initial_speed * omega_base / stiffness
        control.differential(shaft_angle, omega_base * speed_difference, initial_twist)
        control.differential(
            turbine_speed,
            (mechanical_power / turbine_speed - shaft_torque - damping_torque)
            / (Const(2.) * turbine_inertia), initial_speed,
        )
        control.differential(
            generator_speed,
            (shaft_torque + damping_torque - electrical_power / generator_speed
             - damp * (generator_speed - initial_speed))
            / (Const(2.) * generator_inertia), initial_speed,
        )
        control.differential(rotor_angle, omega_base * (generator_speed - initial_speed), Const(0.))

    return control.finish(
        (generator_speed, turbine_speed, rotor_angle),
        'Wind drive-train shaft and generator-speed dynamics',
    )
