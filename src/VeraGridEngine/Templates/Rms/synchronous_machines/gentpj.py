# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Colib GENTPJ saturated synchronous-machine template."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.synchronous_machines.genroe import (
    build_genroe_template,
)
from VeraGridEngine.Utils.Symbolic import symbolic as sym
from VeraGridEngine.Utils.Symbolic.block import Var


def build_gentpj_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """Build the GENTPJ six-state saturated round-rotor machine.

    GENTPJ and VeraGrid's GENROE share the round-rotor subtransient state set
    and power-law magnetic saturation structure. The Colib ``K_is`` parameter
    augments the saturation flux with the stator-current magnitude.

    :param vf: Variable factory used to allocate symbolic variables.
    :param name: Optional unique model instance name.
    :return: Native six-state saturated synchronous-machine template.
    """
    template_name: str = 'GENTPJ' if name is None else name
    template: RmsModelTemplate = build_genroe_template(vf=vf, name=template_name)
    machine_block = template.block.children[0]
    direct_current: Var = machine_block.algebraic_vars[2]
    quadrature_current: Var = machine_block.algebraic_vars[3]
    subtransient_flux: Var = machine_block.algebraic_vars[11]
    saturation_factor: Var = machine_block.algebraic_vars[12]
    saturation_at_unity: Var = next(
        parameter for parameter in machine_block.event_dict if parameter.name == 'S10'
    )
    saturation_at_twelve: Var = next(
        parameter for parameter in machine_block.event_dict if parameter.name == 'S12'
    )
    stator_current_gain: Var = vf.add_var('K_is')
    saturation_flux = subtransient_flux + stator_current_gain * sym.sqrt(
        direct_current ** 2 + quadrature_current ** 2
    )
    saturation_exponent = vf.add_const(1.0) + sym.log(
        saturation_at_twelve / saturation_at_unity
    ) / sym.log(vf.add_const(1.2))

    # Replace the native flux-only saturation law with the GENTPJ augmented flux.
    machine_block.algebraic_eqs[12] = (
        saturation_at_unity * saturation_flux ** saturation_exponent
        - subtransient_flux * saturation_factor
    )
    machine_block.event_dict[stator_current_gain] = vf.add_const(0.0)
    template.comment = 'Colib GENTPJ saturated round-rotor synchronous machine'
    return template
