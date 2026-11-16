# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES IEEE Type 2 cross-current voltage compensation."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class VCompIEEEType2Parameters:
    """IEEE Type 2 transducer and cross-current compensation fields."""

    __slots__ = ('tr', 'compensations')

    def __init__(
            self,
            tr: float = 0.0,
            compensations: tuple[tuple[float, float], ...] = tuple(),
    ) -> None:
        """Store the canonical compensator and associated pair fields.

        :param tr: Combined voltage-sensing and compensation time constant.
        :param compensations: Ordered ``(rcij, xcij)`` records, one per GenJ machine.
        """
        self.tr: float = tr
        self.compensations: tuple[tuple[float, float], ...] = compensations


def build_v_comp_i_e_e_e_type2_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: VCompIEEEType2Parameters | None = None,
) -> RmsModelTemplate:
    """Build IEEE 421.5-2005 Eq. (1) cross-current compensation and transducer.

    :param vfactory: Factory allocating equation and parameter symbols.
    :param name: Optional runtime instance name.
    :param parameters: Vcomp and associated GenICompensationForGenJ settings.
    :return: Phasor-input compensated-voltage transducer with ``UsPu`` output.
    :raises ValueError: A parameter is nonfinite or the time constant is negative.
    """
    settings: VCompIEEEType2Parameters = (
        VCompIEEEType2Parameters() if parameters is None else parameters
    )
    numeric_values: tuple[float, ...] = (settings.tr,)
    for resistance_value, reactance_value in settings.compensations:
        numeric_values += (resistance_value, reactance_value)
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('VCompIEEEType2 parameters must be finite')
    elif settings.tr < 0.0:
        raise ValueError('VCompIEEEType2 transducer time must be nonnegative')
    else:
        pass

    template_name: str = 'VCompIEEEType2' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    transducer_time: Var = model.parameter('VCompIEEEType2.tr', settings.tr)
    voltage_real: Var = model.input('VtRePu', Const(1.0))
    voltage_imaginary: Var = model.input('VtImPu', Const(0.0))

    compensated_real_expression: Expr = voltage_real
    compensated_imaginary_expression: Expr = voltage_imaginary
    for pair_index in range(len(settings.compensations)):
        resistance_value, reactance_value = settings.compensations[pair_index]
        resistance: Var = model.parameter(
            f'GenICompensationForGenJ[{pair_index}].rcij', resistance_value,
        )
        reactance: Var = model.parameter(
            f'GenICompensationForGenJ[{pair_index}].xcij', reactance_value,
        )
        remote_current_real: Var = model.input(f'IjRePu{pair_index}', Const(0.0))
        remote_current_imaginary: Var = model.input(f'IjImPu{pair_index}', Const(0.0))
        compensated_real_expression += (
            resistance * remote_current_real - reactance * remote_current_imaginary
        )
        compensated_imaginary_expression += (
            reactance * remote_current_real + resistance * remote_current_imaginary
        )

    # Eq. (1): sum each RDF compensation record's impedance drop from its GenJ current.
    compensated_real: Var = model.algebraic(
        'VcompRePu',
        compensated_real_expression,
        Const(1.0),
    )
    compensated_imaginary: Var = model.algebraic(
        'VcompImPu',
        compensated_imaginary_expression,
        Const(0.0),
    )
    compensated_magnitude: Var = model.algebraic(
        'VcompPu', sym.sqrt(compensated_real ** 2 + compensated_imaginary ** 2), Const(1.0),
    )
    sensed_voltage: Var = model.lag(
        'UsPu', compensated_magnitude, transducer_time, settings.tr, Const(1.0),
    )
    template: RmsModelTemplate = model.finish(
        (sensed_voltage,), 'CGMES IEEE VCompIEEEType2 cross-current compensator',
    )
    template.comment = (
        'IEEE 421.5-2005 Eq. (1) Vc=|Vt+sum((Rcij+jXcij)Itj)|, followed by the '
        'combined transducer/compensation Tr lag. Each CGMES GenICompensationForGenJ '
        'record supplies one pair impedance and identifies the corresponding GenJ machine.'
    )
    enabled_name: str = f'VCompIEEEType2.enabled_{template_name}'
    enabled_variable: Var = vfactory.add_var(enabled_name)
    model.block.event_dict[enabled_variable] = vfactory.add_const(value=None, name=enabled_name)
    return template
