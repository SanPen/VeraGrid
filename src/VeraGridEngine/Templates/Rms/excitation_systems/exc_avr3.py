# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcAVR3 excitation system."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcAVR3Parameters:
    """Numeric settings for the canonical CGMES ExcAVR3 model."""

    __slots__ = ('ka', 'vrmn', 'vrmx', 't1', 't2', 't3', 't4', 'te', 'e1', 'se1', 'e2', 'se2')

    def __init__(
            self,
            ka: float = 3000.0,
            vrmn: float = -7.5,
            vrmx: float = 7.5,
            t1: float = 220.0,
            t2: float = 1.6,
            t3: float = 0.66,
            t4: float = 0.07,
            te: float = 1.0,
            e1: float = 4.18,
            se1: float = 0.1,
            e2: float = 3.14,
            se2: float = 0.03,
    ) -> None:
        """Store settings with the local EA typical values as defaults.

        :param ka: AVR gain.
        :param vrmn: Lower regulator limit.
        :param vrmx: Upper regulator limit.
        :param t1: First lead-lag denominator time.
        :param t2: First stage state time.
        :param t3: Second lead-lag denominator time.
        :param t4: Second stage state time.
        :param te: Exciter time constant.
        :param e1: First saturation voltage point.
        :param se1: Saturation at ``e1``.
        :param e2: Second saturation voltage point.
        :param se2: Saturation at ``e2``.
        """
        self.ka: float = ka
        self.vrmn: float = vrmn
        self.vrmx: float = vrmx
        self.t1: float = t1
        self.t2: float = t2
        self.t3: float = t3
        self.t4: float = t4
        self.te: float = te
        self.e1: float = e1
        self.se1: float = se1
        self.e2: float = e2
        self.se2: float = se2


def build_exc_a_v_r3_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcAVR3Parameters | None = None,
) -> RmsModelTemplate:
    """Build AVR3's two bounded filter stages, saturation feedback, and exciter.

    :param vfactory: Factory that owns the symbolic graph.
    :param name: Optional runtime instance name.
    :param parameters: Parsed CGMES AVR3 settings.
    :return: Equation-backed AVR3 voltage regulator and excitation system.
    :raises ValueError: Invalid time, limit, or saturation parameters.
    """
    settings: ExcAVR3Parameters = ExcAVR3Parameters() if parameters is None else parameters
    template_name: str = 'ExcAVR3' if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.ka, settings.vrmn, settings.vrmx, settings.t1, settings.t2,
        settings.t3, settings.t4, settings.te, settings.e1, settings.se1,
        settings.e2, settings.se2,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcAVR3 parameters must be finite')
    elif min(settings.t1, settings.t2, settings.t3, settings.t4, settings.te) < 0.0:
        raise ValueError('ExcAVR3 times must be nonnegative')
    elif min(settings.t1, settings.t2, settings.t3, settings.t4, settings.te) <= 0.0:
        raise ValueError('ExcAVR3 stage and exciter times must be positive')
    elif settings.vrmn >= settings.vrmx:
        raise ValueError('ExcAVR3 regulator limits must be ordered')
    elif settings.e1 <= 0.0 or settings.e2 <= 0.0 or settings.e1 == settings.e2:
        raise ValueError('ExcAVR3 saturation points must be distinct and positive')
    elif settings.se1 <= 0.0 or settings.se2 <= 0.0:
        raise ValueError('ExcAVR3 saturation values must be positive')
    else:
        pass

    builder: ControlRealization = ControlRealization(vfactory, template_name)
    ka: Var = builder.parameter('KA', settings.ka)
    vrmn: Var = builder.parameter('VRMN', settings.vrmn)
    vrmx: Var = builder.parameter('VRMX', settings.vrmx)
    t1: Var = builder.parameter('T1', settings.t1)
    t2: Var = builder.parameter('T2', settings.t2)
    t3: Var = builder.parameter('T3', settings.t3)
    t4: Var = builder.parameter('T4', settings.t4)
    te: Var = builder.parameter('TE', settings.te)
    e1: Var = builder.parameter('E1', settings.e1)
    se1: Var = builder.parameter('SE1', settings.se1)
    e2: Var = builder.parameter('E2', settings.e2)
    se2: Var = builder.parameter('SE2', settings.se2)
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    stabilizer: Var = builder.input('UpssPu', Const(0.0))

    voltage_error: Expr = reference - terminal_voltage + stabilizer
    avr_demand: Expr = ka * voltage_error
    first_ratio: Var = t2 / t1
    first_memory: Var = vfactory.add_var(f'FirstStageMemoryPu_{template_name}')
    first_lower: Expr = vrmn - avr_demand * first_ratio
    first_upper: Expr = vrmx - avr_demand * first_ratio
    builder.differential(
        first_memory,
        (avr_demand - first_memory) / t2,
        Const(0.0),
        first_lower,
        first_upper,
    )
    first_output: Expr = first_ratio * avr_demand + (Const(1.0) - first_ratio) * first_memory
    second_ratio: Var = t3 / t4
    second_memory: Var = vfactory.add_var(f'SecondStageMemoryPu_{template_name}')
    second_lower: Expr = vrmn - avr_demand * second_ratio
    second_upper: Expr = vrmx - avr_demand * second_ratio
    builder.differential(
        second_memory,
        (first_output - second_memory) / t4,
        Const(0.0),
        second_lower,
        second_upper,
    )
    regulator_output: Expr = second_ratio * first_output + (Const(1.0) - second_ratio) * second_memory
    exciter_voltage: Var = vfactory.add_var(f'EfdPu_{template_name}')
    saturation_slope: float = math.log(settings.se2 / settings.se1) / (settings.e2 - settings.e1)
    saturation_scale: float = settings.se1 * math.exp(-saturation_slope * settings.e1)
    saturation_ratio: Expr = Const(saturation_scale) * sym.exp(Const(saturation_slope) * exciter_voltage)
    saturation_voltage: Expr = saturation_ratio * exciter_voltage
    exciter_derivative: Expr = (regulator_output - saturation_voltage) / te
    builder.differential(exciter_voltage, exciter_derivative, Const(1.0), Const(0.0), Const(1e12))
    return builder.finish((exciter_voltage,), 'CGMES ExcAVR3 excitation system')
