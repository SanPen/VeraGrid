# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://www.mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcCZ Czech PI excitation system."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcCZParameters:
    """Numeric settings declared by the canonical CGMES ExcCZ class."""

    __slots__ = ('kp', 'tc', 'vrmax', 'vrmin', 'ka', 'ta', 'ke', 'te', 'efdmax', 'efdmin')

    def __init__(
            self,
            kp: float = 0.0,
            tc: float = 1.0,
            vrmax: float = 5.0,
            vrmin: float = -5.0,
            ka: float = 1.0,
            ta: float = 0.0,
            ke: float = 1.0,
            te: float = 0.0,
            efdmax: float = 5.0,
            efdmin: float = -5.0,
    ) -> None:
        """Store the parsed gains, time constants, and output limits.

        :param kp: Proportional controller gain.
        :param tc: Integral controller time constant in seconds.
        :param vrmax: Upper controller output limit.
        :param vrmin: Lower controller output limit.
        :param ka: Amplifier gain.
        :param ta: Amplifier time constant in seconds.
        :param ke: Exciter gain.
        :param te: Exciter time constant in seconds.
        :param efdmax: Upper field-voltage limit.
        :param efdmin: Lower field-voltage limit.
        """
        self.kp: float = kp
        self.tc: float = tc
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin
        self.ka: float = ka
        self.ta: float = ta
        self.ke: float = ke
        self.te: float = te
        self.efdmax: float = efdmax
        self.efdmin: float = efdmin


def build_exc_c_z_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcCZParameters | None = None,
) -> RmsModelTemplate:
    """Build the ExcCZ PI controller, amplifier, and limited exciter stages.

    :param vfactory: Factory owning the symbolic graph.
    :param name: Optional runtime model name.
    :param parameters: Parsed canonical CGMES settings.
    :return: Equation-backed model with voltage, reference, Vs, and Efd ports.
    :raises ValueError: Invalid time constants, nonfinite values, or unordered limits.
    """
    settings: ExcCZParameters = ExcCZParameters() if parameters is None else parameters
    template_name: str = 'ExcCZ' if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.kp, settings.tc, settings.vrmax, settings.vrmin, settings.ka,
        settings.ta, settings.ke, settings.te, settings.efdmax, settings.efdmin,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcCZ parameters must be finite')
    elif settings.tc <= 0.0 or settings.ta < 0.0 or settings.te < 0.0:
        raise ValueError('ExcCZ requires TC > 0 and nonnegative TA/TE')
    elif settings.vrmin >= settings.vrmax or settings.efdmin >= settings.efdmax:
        raise ValueError('ExcCZ controller and field limits must be ordered')
    else:
        pass

    builder: ControlRealization = ControlRealization(vfactory, template_name)
    kp: Var = builder.parameter('KP', settings.kp)
    tc: Var = builder.parameter('TC', settings.tc)
    vrmax: Var = builder.parameter('VRMAX', settings.vrmax)
    vrmin: Var = builder.parameter('VRMIN', settings.vrmin)
    ka: Var = builder.parameter('KA', settings.ka)
    ta: Var = builder.parameter('TA', settings.ta)
    ke: Var = builder.parameter('KE', settings.ke)
    te: Var = builder.parameter('TE', settings.te)
    efdmax: Var = builder.parameter('EFDMAX', settings.efdmax)
    efdmin: Var = builder.parameter('EFDMIN', settings.efdmin)
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    supplementary: Var = builder.input('UpssPu', Const(0.0))
    voltage_error: Expr = reference - terminal_voltage + supplementary

    integral_state: Var = vfactory.add_var(f'IntegralPu_{template_name}')
    proportional_output: Expr = kp * voltage_error + integral_state
    regulator_output: Var = builder.algebraic(
        'RegulatorOutputPu', sym.hard_sat(proportional_output, vrmin, vrmax), Const(0.0),
    )
    builder.differential(
        integral_state,
        voltage_error / tc,
        Const(0.0),
        vrmin,
        vrmax,
    )
    amplifier_output: Var = builder.lag(
        'AmplifierPu', ka * regulator_output, ta, settings.ta,
        sym.hard_sat(ka * Const(0.0), vrmin, vrmax),
    )
    field_voltage: Var = builder.lag(
        'EfdPu', ke * amplifier_output, te, settings.te, Const(0.0), efdmin, efdmax,
    )
    return builder.finish((field_voltage,), 'CGMES ExcCZ Czech PI excitation system')
