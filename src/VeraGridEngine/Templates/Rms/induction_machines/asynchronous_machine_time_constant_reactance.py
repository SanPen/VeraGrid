# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""CGMES adapter for the shared RMS induction-machine realization."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.auxiliary_functions import (
    build_induction_machine,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import InductionMachineRole
from VeraGridEngine.Utils.Symbolic.symbolic import Const


def build_asynchronous_machine_time_constant_reactance_template(
        vfactory: VarFactory,
        name: str | None = None,
        role: InductionMachineRole = InductionMachineRole.GENERATOR,
        nominal_frequency_hz: float = 50.0,
) -> RmsModelTemplate:
    """Build an RMS induction machine and rename its settings to canonical RDF fields.

    :param vfactory: Factory used to allocate the model symbols.
    :param name: Optional runtime model name.
    :param role: Generator or motor sign convention selected from linked equipment.
    :param nominal_frequency_hz: Network electrical frequency in hertz.
    :return: Existing RMS induction-machine equations with CGMES parameter symbols.
    """
    template_name: str = 'AsynchronousMachineTimeConstantReactance' if name is None else name
    template: RmsModelTemplate = build_induction_machine(
        vf=vfactory,
        name=template_name,
        role=role,
    )
    frequency_variable: Var
    for frequency_variable in template.block.event_dict:
        if frequency_variable.name == f'FNomHz_{template_name}':
            template.block.event_dict[frequency_variable] = Const(nominal_frequency_hz)
        else:
            pass
    # Rename the eight equation settings so the generic CGMES copier writes RDF fields directly.
    rms_to_cgmes_names: tuple[tuple[str, str], ...] = (
        ('RaPu', 'statorResistance'),
        ('XsPu', 'xs'),
        ('XpPu', 'xp'),
        ('XppPu', 'xpp'),
        ('Tp0', 'tpo'),
        ('Tpp0', 'tppo'),
        ('H', 'inertia'),
        ('Damp', 'damping'),
    )
    variables_to_replace: list[Var] = list()
    canonical_variables: list[Var] = list()
    equation_variable: Var
    for equation_variable in template.block.event_dict:
        for rms_name, cgmes_name in rms_to_cgmes_names:
            if equation_variable.name == f'{rms_name}_{template_name}':
                variables_to_replace.append(equation_variable)
                canonical_variables.append(
                    vfactory.add_var(
                        f'AsynchronousMachineTimeConstantReactance.{cgmes_name}_{template_name}',
                    )
                )
            else:
                pass
    else:
        pass
    template.block.connect(
        vars_to_subs=variables_to_replace,
        incoming_vars=canonical_variables,
    )

    # The shared RDF fields define S(E1)/S(E2) in the synchronous-machine saturation diagram only.
    # TODO: apply these inherited values only if a source defines an induction-machine saturation law.
    parameter_block: Block = Block(name=f'{template_name}_CGMES_parameters')
    for parameter_name in (
            'enabled', 'saturationFactor', 'saturationFactor120', 'statorLeakageReactance',
    ):
        parameter_variable: Var = vfactory.add_var(
            f'AsynchronousMachineTimeConstantReactance.{parameter_name}_{template_name}',
        )
        parameter_block.event_dict[parameter_variable] = vfactory.add_const(value=None)
    template.block.children.insert(0, parameter_block)
    template.comment = (
        'CGMES AsynchronousMachineTimeConstantReactance using the shared RMS fifth-order '
        'induction-machine equations; canonical CGMES parameter symbols are adapted in this wrapper.'
    )
    return template
