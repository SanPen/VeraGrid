# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed template for CGMES IEEE DEC3A."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.procedural_logic import pickup_dropoff
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var


class DiscExcContIEEEDEC3AParameters:
    """Store the canonical DEC3A threshold and reset delay."""

    __slots__ = ('vtmin', 'tdr')

    def __init__(self, vtmin: float = 0.0, tdr: float = 0.0) -> None:
        """Set the RDF undervoltage threshold and reset delay.

        :param vtmin: Terminal-voltage threshold in per unit.
        :param tdr: Time to keep the PSS switch open after voltage recovery.
        """
        self.vtmin: float = vtmin
        self.tdr: float = tdr


def build_disc_exc_cont_i_e_e_e_d_e_c3_a_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: DiscExcContIEEEDEC3AParameters | None = None,
) -> RmsModelTemplate:
    """Build the terminal-undervoltage PSS interruption logic.

    :param vfactory: Factory allocating equations and runtime relay state.
    :param name: Optional unique runtime model name.
    :param parameters: Canonical ``vtmin`` and ``tdr`` values.
    :return: DEC3A template with terminal-voltage/PSS inputs and a gated output.
    :raises ValueError: Nonfinite threshold or negative reset delay.
    """
    settings: DiscExcContIEEEDEC3AParameters = (
        DiscExcContIEEEDEC3AParameters() if parameters is None else parameters
    )
    if not math.isfinite(settings.vtmin) or not math.isfinite(settings.tdr):
        raise ValueError('CGMES DEC3A parameters must be finite')
    elif settings.tdr < 0.0:
        raise ValueError('CGMES DEC3A reset delay must be nonnegative')
    else:
        pass

    template_name: str = 'DiscExcContIEEEDEC3A' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    terminal_voltage: Var = model.input('VtPu', Const(1.0))
    stabilizer: Var = model.input('VstPu', Const(0.0))
    undervoltage_latch: Var = vfactory.add_var(f'UndervoltageLatch_{template_name}')
    model.block.event_dict[undervoltage_latch] = vfactory.add_const(value=0.0)
    model.block.procedural_logic.append(
        pickup_dropoff(
            output=undervoltage_latch,
            boolexpr=terminal_voltage < Const(settings.vtmin),
            Tpick=Const(0.0),
            Tdrop=Const(settings.tdr),
            name=f'DEC3A.ResetDelay_{template_name}',
        )
    )
    output: Var = model.algebraic(
        'VsPu', (Const(1.0) - undervoltage_latch) * stabilizer, stabilizer,
    )
    template: RmsModelTemplate = model.finish(
        (output,), 'IEEE DEC3A terminal-undervoltage stabilizer interruption',
    )
    enabled_variable: Var = vfactory.add_var(f'DiscExcContIEEEDEC3A.enabled_{template_name}')
    template.block.event_dict[enabled_variable] = vfactory.add_const(
        value=None, name=f'DiscExcContIEEEDEC3A.enabled_{template_name}',
    )
    for parameter_name, parameter_value in (('vtmin', settings.vtmin), ('tdr', settings.tdr)):
        event_name: str = f'DiscExcContIEEEDEC3A.{parameter_name}_{template_name}'
        event_variable: Var = vfactory.add_var(event_name)
        template.block.event_dict[event_variable] = vfactory.add_const(
            value=parameter_value, name=event_name,
        )
    template.comment = (
        'CGMES DEC3A opens the PSS signal below Vtmin and applies Tdr as the '
        'undervoltage-latch reset delay.'
    )
    return template
