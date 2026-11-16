# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcIEEEAC5A brushless excitation system."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcIEEEAC5AParameters:
    """CGMES AC5A regulator, stabilizer, exciter, and loaded saturation values."""

    __slots__ = (
        'ka', 'ta', 'vrmax', 'vrmin', 'ke', 'te', 'kf', 'tf1', 'tf2', 'tf3',
        'efd1', 'seefd1', 'efd2', 'seefd2',
    )

    def __init__(
            self,
            ka: float = 400.0,
            ta: float = 0.02,
            vrmax: float = 7.3,
            vrmin: float = -7.3,
            ke: float = 1.0,
            te: float = 0.8,
            kf: float = 0.03,
            tf1: float = 1.0,
            tf2: float = 1.0,
            tf3: float = 1.0,
            efd1: float = 5.6,
            seefd1: float = 0.86,
            efd2: float = 4.2,
            seefd2: float = 0.5,
    ) -> None:
        """Store canonical CGMES quantities in per-unit and seconds.

        :param ka: Voltage regulator gain.
        :param ta: Voltage regulator time constant.
        :param vrmax: Regulator upper output limit.
        :param vrmin: Regulator lower output limit.
        :param ke: Exciter field constant.
        :param te: Exciter integration time.
        :param kf: Stabilizing feedback gain.
        :param tf1: First stabilizer filter time.
        :param tf2: Second stabilizer filter time.
        :param tf3: Stabilizer feedback zero time.
        :param efd1: First loaded saturation voltage point.
        :param seefd1: Saturation at ``efd1``.
        :param efd2: Second loaded saturation voltage point.
        :param seefd2: Saturation at ``efd2``.
        """
        self.ka: float = ka
        self.ta: float = ta
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin
        self.ke: float = ke
        self.te: float = te
        self.kf: float = kf
        self.tf1: float = tf1
        self.tf2: float = tf2
        self.tf3: float = tf3
        self.efd1: float = efd1
        self.seefd1: float = seefd1
        self.efd2: float = efd2
        self.seefd2: float = seefd2


def build_exc_i_e_e_e_a_c5_a_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcIEEEAC5AParameters | None = None,
) -> RmsModelTemplate:
    """Build the CGMES AC5A regulator, washout feedback, and exciter equations.

    :param vfactory: Factory that owns the symbolic model.
    :param name: Optional unique runtime model name.
    :param parameters: Parsed RDF settings controlling equations and limits.
    :return: Executable AC5A excitation system with terminal voltage and Efd ports.
    :raises ValueError: Invalid time constants, bounds, or saturation points.
    """
    settings: ExcIEEEAC5AParameters = (
        ExcIEEEAC5AParameters() if parameters is None else parameters
    )
    template_name: str = 'ExcIEEEAC5A' if name is None else name
    values: tuple[float, ...] = (
        settings.ka, settings.ta, settings.vrmax, settings.vrmin, settings.ke,
        settings.te, settings.kf, settings.tf1, settings.tf2, settings.tf3,
        settings.efd1, settings.seefd1, settings.efd2, settings.seefd2,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('ExcIEEEAC5A parameters must be finite')
    elif min(settings.ta, settings.tf1, settings.tf2, settings.tf3) < 0.0:
        raise ValueError('ExcIEEEAC5A times must be nonnegative')
    elif settings.te <= 0.0 or settings.tf1 <= 0.0 or settings.tf2 <= 0.0:
        raise ValueError('ExcIEEEAC5A T_E, T_F1, and T_F2 must be positive')
    elif settings.vrmin >= settings.vrmax:
        raise ValueError('ExcIEEEAC5A lower limit must be below upper limit')
    elif settings.efd1 <= 0.0 or settings.efd2 <= 0.0 or settings.efd1 == settings.efd2:
        raise ValueError('ExcIEEEAC5A saturation points must be distinct and positive')
    elif settings.seefd1 <= 0.0 or settings.seefd2 <= 0.0 or settings.ke <= 0.0:
        raise ValueError('ExcIEEEAC5A saturation values and K_E must be positive')
    else:
        pass

    builder: ControlRealization = ControlRealization(vfactory, template_name)
    ka: Var = builder.parameter('KA', settings.ka)
    ta: Var = builder.parameter('TA', settings.ta)
    vrmax: Var = builder.parameter('VRMAX', settings.vrmax)
    vrmin: Var = builder.parameter('VRMIN', settings.vrmin)
    ke: Var = builder.parameter('KE', settings.ke)
    te: Var = builder.parameter('TE', settings.te)
    kf: Var = builder.parameter('KF', settings.kf)
    tf1: Var = builder.parameter('TF1', settings.tf1)
    tf2: Var = builder.parameter('TF2', settings.tf2)
    tf3: Var = builder.parameter('TF3', settings.tf3)
    efd1: Var = builder.parameter('EFD1', settings.efd1)
    seefd1: Var = builder.parameter('SEefd1', settings.seefd1)
    efd2: Var = builder.parameter('EFD2', settings.efd2)
    seefd2: Var = builder.parameter('SEefd2', settings.seefd2)
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    stabilizer: Var = builder.input('UpssPu', Const(0.0))

    # The feedback path is a two-pole washout with the RDF zero on its output.
    regulator_state: Var = vfactory.add_var(f'RegulatorPu_{template_name}')
    first_feedback_state: Var = builder.lag(
        'FeedbackFirstMemoryPu', regulator_state, tf1, settings.tf1, Const(0.0),
    )
    second_feedback_state: Var = builder.lag(
        'FeedbackSecondMemoryPu', first_feedback_state, tf2, settings.tf2, Const(0.0),
    )
    first_feedback_derivative: Expr = (regulator_state - first_feedback_state) / tf1
    second_feedback_derivative: Expr = (first_feedback_state - second_feedback_state) / tf2
    second_feedback_acceleration: Expr = (
        first_feedback_derivative - second_feedback_derivative
    ) / tf2
    feedback: Expr = kf * (
        second_feedback_derivative + tf3 * second_feedback_acceleration
    )
    voltage_error: Var = builder.algebraic(
        'VoltageErrorPu', reference - terminal_voltage + stabilizer - feedback, Const(0.0),
    )
    regulator: Var = builder.lag(
        'RegulatorPu', ka * voltage_error, ta, settings.ta, Const(0.0),
        vrmin, vrmax, output=regulator_state,
    )

    # Loaded saturation data determines the exponential exciter characteristic.
    saturation_b: Expr = sym.log(seefd2 / seefd1) / (efd2 - efd1)
    saturation_a: Expr = seefd1 * sym.exp(-saturation_b * efd1)
    exciter_voltage: Var = vfactory.add_var(f'VePu_{template_name}')
    saturation: Expr = saturation_a * sym.exp(saturation_b * exciter_voltage)
    exciter_derivative: Expr = (regulator - (ke + saturation) * exciter_voltage) / te
    builder.differential(exciter_voltage, exciter_derivative, Const(1.0))
    field_voltage: Var = builder.algebraic('EfdPu', exciter_voltage, Const(1.0))
    template: RmsModelTemplate = builder.finish(
        (field_voltage,), 'CGMES ExcIEEEAC5A brushless excitation system',
    )

    # Expose exactly the scalar property surface declared by ExcIEEEAC5A RDF.
    for parameter_name in (
            'enabled', 'ka', 'ta', 'vrmax', 'vrmin', 'ke', 'te', 'kf', 'tf1',
            'tf2', 'tf3', 'efd1', 'seefd1', 'efd2', 'seefd2',
    ):
        variable_name: str = f'ExcIEEEAC5A.{parameter_name}_{template_name}'
        parameter_variable: Var = vfactory.add_var(variable_name)
        template.block.event_dict[parameter_variable] = vfactory.add_const(value=None, name=variable_name)
    return template
