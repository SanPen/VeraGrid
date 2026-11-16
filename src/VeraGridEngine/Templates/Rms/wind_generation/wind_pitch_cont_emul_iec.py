# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""IEC Type 2 pitch-control-emulator equations."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class WindPitchContEmulIECParameters:
    """CGMES 2.4.15 IEC pitch-emulator parameters."""

    __slots__ = (
        'kdroop', 'kipce', 'komegaaero', 'kppce', 'omegaref', 'pimax',
        'pimin', 't1', 't2', 'tpe',
    )

    def __init__(
            self,
            kdroop: float = 0.0,
            kipce: float = 0.0,
            komegaaero: float = 0.0,
            kppce: float = 0.0,
            omegaref: float = 1.0,
            pimax: float = 1.0,
            pimin: float = 0.0,
            t1: float = 0.0,
            t2: float = 0.0,
            tpe: float = 0.0,
    ) -> None:
        """Store the ten scalar values declared by the canonical RDF.

        :param kdroop: Power-error gain.
        :param kipce: Pitch-emulator integral gain.
        :param komegaaero: Aerodynamic power change per rotor-speed change.
        :param kppce: Pitch-emulator proportional gain.
        :param omegaref: Initial steady-state rotor speed.
        :param pimax: Maximum steady-state pitch power command.
        :param pimin: Minimum steady-state pitch power command.
        :param t1: First pitch-command lag time.
        :param t2: Second pitch-command lag time.
        :param tpe: Generator air-gap power measurement lag time.
        """
        self.kdroop: float = kdroop
        self.kipce: float = kipce
        self.komegaaero: float = komegaaero
        self.kppce: float = kppce
        self.omegaref: float = omegaref
        self.pimax: float = pimax
        self.pimin: float = pimin
        self.t1: float = t1
        self.t2: float = t2
        self.tpe: float = tpe


def build_wind_pitch_cont_emul_i_e_c_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: WindPitchContEmulIECParameters | None = None,
        initial_power: float = 0.0,
        initial_speed: float | None = None,
) -> RmsModelTemplate:
    """Build the IEC Figure 7.11 power-to-pitch-servo control graph.

    :param vfactory: Factory allocating runtime variables.
    :param name: Optional unique template name.
    :param parameters: Canonical CGMES parameter values.
    :param initial_power: Solved generator power on the turbine power base.
    :param initial_speed: Solved turbine rotor speed in per unit.
    :return: Equation-backed ``PservoPu`` output with an external power reference.
    :raises ValueError: Invalid finite values, limits, or time constants.
    """
    settings: WindPitchContEmulIECParameters = (
        WindPitchContEmulIECParameters() if parameters is None else parameters
    )
    speed_initial: float = settings.omegaref if initial_speed is None else initial_speed
    numeric_values: tuple[float, ...] = (
        settings.kdroop, settings.kipce, settings.komegaaero, settings.kppce,
        settings.omegaref, settings.pimax, settings.pimin, settings.t1,
        settings.t2, settings.tpe, initial_power, speed_initial,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('CGMES WindPitchContEmulIEC values must be finite')
    elif min(settings.kdroop, settings.kipce, settings.komegaaero, settings.kppce,
             settings.t1, settings.t2, settings.tpe) < 0.0:
        raise ValueError('CGMES WindPitchContEmulIEC gains and times must be nonnegative')
    elif settings.pimin >= settings.pimax:
        raise ValueError('CGMES WindPitchContEmulIEC requires pimin < pimax')
    else:
        pass

    initial_power_order: float = min(max(0.0, settings.pimin), settings.pimax)
    initial_controller_error: float = settings.komegaaero * (speed_initial - settings.omegaref)
    initial_integral_order: float = initial_power_order - settings.kppce * initial_controller_error
    template_name: str = 'WindPitchContEmulIEC' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    kdroop: Var = model.parameter('WindPitchContEmulIEC.kdroop', settings.kdroop)
    kipce: Var = model.parameter('WindPitchContEmulIEC.kipce', settings.kipce)
    komegaaero: Var = model.parameter('WindPitchContEmulIEC.komegaaero', settings.komegaaero)
    kppce: Var = model.parameter('WindPitchContEmulIEC.kppce', settings.kppce)
    omegaref: Var = model.parameter('WindPitchContEmulIEC.omegaref', settings.omegaref)
    pimax: Var = model.parameter('WindPitchContEmulIEC.pimax', settings.pimax)
    pimin: Var = model.parameter('WindPitchContEmulIEC.pimin', settings.pimin)
    t1: Var = model.parameter('WindPitchContEmulIEC.t1', settings.t1)
    t2: Var = model.parameter('WindPitchContEmulIEC.t2', settings.t2)
    tpe: Var = model.parameter('WindPitchContEmulIEC.tpe', settings.tpe)

    generator_power: Var = model.input('PGenPu', Const(initial_power))
    wind_rotor_speed: Var = model.input('OmegaWtrPu', Const(speed_initial))
    power_reference: Var = model.input('PwtRefPu', Const(initial_power))
    filtered_power: Var = model.lag(
        'FilteredPGenPu', generator_power, tpe, settings.tpe, Const(initial_power),
    )
    power_error: Expr = kdroop * (filtered_power - power_reference)
    speed_error: Expr = komegaaero * (wind_rotor_speed - omegaref)
    controller_error: Expr = power_error + speed_error
    proportional_output: Expr = kppce * controller_error
    controller_state: Var = vfactory.add_var(f'PitchEmulatorIntegralPu_{template_name}')
    model.differential(
        controller_state,
        kipce * controller_error,
        Const(initial_integral_order),
        pimin - proportional_output,
        pimax - proportional_output,
    )
    limited_power_order: Var = model.algebraic(
        'LimitedPowerOrderPu',
        sym.hard_sat(proportional_output + controller_state, pimin, pimax),
        Const(initial_power_order),
    )
    first_pitch_lag: Var = model.lag(
        'PitchLag1Pu', limited_power_order, t1, settings.t1, Const(initial_power_order),
    )
    servo_power: Var = model.lag(
        'PservoPu', first_pitch_lag, t2, settings.t2, Const(initial_power_order),
    )
    return model.finish(
        (servo_power,),
        'IEC 61400-27-1 Figure 7.11 pitch-control emulator; diagram cross-checked against Chandrasekaran 2014 Figure 7.11.',
    )
