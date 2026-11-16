# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcAVR5 effective-output-resistance exciter."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


class ExcAVR5Parameters:
    """Numeric settings declared by the canonical CGMES ExcAVR5 class."""

    __slots__ = ('ka', 'ta', 'rex')

    def __init__(self, ka: float = 1.0, ta: float = 0.0, rex: float = 0.0) -> None:
        """Store AVR gain, time constant, and effective output resistance.

        :param ka: AVR gain.
        :param ta: AVR time constant in seconds.
        :param rex: Effective output resistance.
        """
        self.ka: float = ka
        self.ta: float = ta
        self.rex: float = rex


def build_exc_a_v_r5_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcAVR5Parameters | None = None,
) -> RmsModelTemplate:
    """Build AVR5's first-order regulator and effective resistance drop.

    :param vfactory: Factory owning the symbolic block.
    :param name: Optional runtime template name.
    :param parameters: Parsed CGMES settings.
    :return: Equation-backed AVR5 with voltage, Ifd, and Efd ports.
    :raises ValueError: Nonfinite gain/resistance or negative time constant.
    """
    settings: ExcAVR5Parameters = ExcAVR5Parameters() if parameters is None else parameters
    template_name: str = 'ExcAVR5' if name is None else name
    numeric_values: tuple[float, ...] = (settings.ka, settings.ta, settings.rex)
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcAVR5 numeric parameters must be finite')
    elif settings.ta < 0.0:
        raise ValueError('ExcAVR5 TA must be nonnegative')
    else:
        pass

    builder: ControlRealization = ControlRealization(vfactory, template_name)
    ka: Var = builder.parameter('KA', settings.ka)
    ta: Var = builder.parameter('TA', settings.ta)
    rex: Var = builder.parameter('REX', settings.rex)
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    stabilizer: Var = builder.input('UpssPu', Const(0.0))
    field_current: Var = builder.input('IfdPu', Const(1.0))
    voltage_error: Expr = reference - terminal_voltage + stabilizer
    regulator_output: Var = builder.lag(
        'RegulatorPu', ka * voltage_error, ta, settings.ta, Const(1.0),
    )
    field_voltage: Var = builder.algebraic(
        'EfdPu', regulator_output - rex * field_current, Const(1.0),
    )
    return builder.finish((field_voltage,), 'CGMES ExcAVR5 excitation system')
