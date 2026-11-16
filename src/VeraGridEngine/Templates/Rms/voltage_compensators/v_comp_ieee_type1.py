# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES IEEE terminal-voltage transducer and load compensator."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class VCompIEEEType1Parameters:
    """Canonical IEEE terminal-voltage transducer settings."""

    __slots__ = ('rc', 'xc', 'tr')

    def __init__(self, rc: float = 0.0, xc: float = 0.0, tr: float = 0.0) -> None:
        """Store canonical load-compensation impedance and transducer time.

        :param rc: Resistive load-compensation coefficient.
        :param xc: Reactive load-compensation coefficient.
        :param tr: Terminal-voltage transducer time constant.
        """
        self.rc: float = rc
        self.xc: float = xc
        self.tr: float = tr


def build_v_comp_i_e_e_e_type1_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: VCompIEEEType1Parameters | None = None,
) -> RmsModelTemplate:
    """Build compensated voltage magnitude followed by the IEEE transducer.

    :param vfactory: Factory used to allocate equation and parameter symbols.
    :param name: Optional runtime model name.
    :param parameters: Parsed canonical CGMES settings.
    :return: Template exposing terminal-voltage and current phasor inputs.
    :raises ValueError: Nonfinite settings or negative transducer time.
    """
    settings: VCompIEEEType1Parameters = (
        VCompIEEEType1Parameters() if parameters is None else parameters
    )
    numeric_values: tuple[float, ...] = (settings.rc, settings.xc, settings.tr)
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('VCompIEEEType1 settings must be finite')
    elif settings.tr < 0.0:
        raise ValueError('VCompIEEEType1 transducer time must be nonnegative')
    else:
        pass

    template_name: str = 'VCompIEEEType1' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    resistance: Var = model.parameter('VCompIEEEType1.rc', settings.rc)
    reactance: Var = model.parameter('VCompIEEEType1.xc', settings.xc)
    transducer_time: Var = model.parameter('VCompIEEEType1.tr', settings.tr)
    voltage_real: Var = model.input('VtRePu', Const(1.0))
    voltage_imaginary: Var = model.input('VtImPu', Const(0.0))
    current_real: Var = model.input('ItRePu', Const(0.0))
    current_imaginary: Var = model.input('ItImPu', Const(0.0))
    compensated_real: Expr = voltage_real + resistance * current_real - reactance * current_imaginary
    compensated_imaginary: Expr = voltage_imaginary + resistance * current_imaginary + reactance * current_real
    compensated_magnitude: Expr = sym.sqrt(compensated_real ** 2 + compensated_imaginary ** 2)
    sensed_voltage: Var = model.lag(
        'VcPu', compensated_magnitude, transducer_time, settings.tr, Const(1.0),
    )
    template: RmsModelTemplate = model.finish(
        (sensed_voltage,), 'CGMES VCompIEEEType1 complex load compensation and transducer',
    )
    template.comment = (
        'IEEE 421.5-2005 §4 terminal sensing: Vc=abs(Vt+(Rc+jXc)It), followed by '
        'Tr/(1+sTr); Tr=0 is an algebraic magnitude.'
    )
    enabled_name: str = f'VCompIEEEType1.enabled_{template_name}'
    enabled_variable: Var = vfactory.add_var(enabled_name)
    template.block.event_dict[enabled_variable] = vfactory.add_const(value=None, name=enabled_name)
    return template
