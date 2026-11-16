# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Composite IEC 61400-27-1 Type-3 wind-turbine RMS template."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.wind_generation.wind_cont_p_type3_iec import (
    build_wind_cont_p_type3_i_e_c_template,
)
from VeraGridEngine.Templates.Rms.wind_generation.wind_cont_q_iec import (
    build_wind_cont_q_i_e_c_template,
)
from VeraGridEngine.Templates.Rms.wind_generation.wind_gen_type3a_iec import (
    build_wind_gen_type3a_i_e_c_template,
)
from VeraGridEngine.Templates.Rms.wind_generation.wind_mech_iec import (
    build_wind_mech_i_e_c_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import DeviceType, VarPowerFlowReferenceType


def get_iec_type3_wind_turbine_rms_template(
        vf: VarFactory,
        name: str = 'IEC Type 3 wind turbine',
) -> RmsModelTemplate:
    """Build the Colib IEC Type-3 DFIG turbine and controller composition.

    :param vf: Variable factory used to allocate symbolic variables.
    :param name: Unique template instance name.
    :return: RMS Type-3 P/Q control, generator, and drivetrain composition.
    """
    # The component defaults keep the composite instantiable; imports replace their parameters.
    p_controller: RmsModelTemplate = build_wind_cont_p_type3_i_e_c_template(
        vfactory=vf,
        name=name + ' P control',
        omegap_curve=((0.0, 0.8), (1.0, 1.0)),
    )
    q_controller: RmsModelTemplate = build_wind_cont_q_i_e_c_template(
        vfactory=vf,
        name=name + ' Q control',
    )
    generator: RmsModelTemplate = build_wind_gen_type3a_i_e_c_template(
        vfactory=vf,
        name=name + ' generator',
    )
    drivetrain: RmsModelTemplate = build_wind_mech_i_e_c_template(
        vfactory=vf,
        name=name + ' drivetrain',
    )

    # Connect commanded currents and measured electrical power through the DFIG package.
    generator.block.connect([generator.block.in_vars[0]], [p_controller.block.out_vars[0]])
    generator.block.connect([generator.block.in_vars[1]], [q_controller.block.out_vars[0]])
    p_controller.block.connect([p_controller.block.in_vars[1]], [generator.block.out_vars[6]])
    q_controller.block.connect(
        [q_controller.block.in_vars[0], q_controller.block.in_vars[1]],
        [generator.block.out_vars[6], generator.block.out_vars[7]],
    )

    # The drivetrain closes the air-gap-power and generator-speed feedback path.
    drivetrain.block.connect([drivetrain.block.in_vars[1]], [generator.block.out_vars[6]])
    p_controller.block.connect([p_controller.block.in_vars[2]], [drivetrain.block.out_vars[2]])

    # Share terminal magnitude and angle with the P/Q controls and current source.
    terminal_voltage: Var = generator.block.external_mapping[VarPowerFlowReferenceType.Vm]
    terminal_angle: Var = generator.block.external_mapping[VarPowerFlowReferenceType.Va]
    p_controller.block.connect([p_controller.block.in_vars[3]], [terminal_voltage])
    q_controller.block.connect([q_controller.block.in_vars[2]], [terminal_voltage])
    generator.block.connect([generator.block.in_vars[5]], [terminal_angle])

    # The active-current capability is common to the P controller and generator.
    generator.block.connect([generator.block.in_vars[2]], [p_controller.block.in_vars[4]])

    root_block: Block = Block(name=name)
    root_block.merge_incoming_block(p_controller.block)
    root_block.merge_incoming_block(q_controller.block)
    root_block.merge_incoming_block(generator.block)
    root_block.merge_incoming_block(drivetrain.block)
    root_block.in_vars = list((
        p_controller.block.in_vars[0],
        p_controller.block.in_vars[4],
        q_controller.block.in_vars[3],
        q_controller.block.in_vars[4],
        generator.block.in_vars[3],
        generator.block.in_vars[4],
        drivetrain.block.in_vars[0],
    ))
    root_block.out_vars = list((
        generator.block.out_vars[2],
        generator.block.out_vars[3],
        generator.block.out_vars[6],
        generator.block.out_vars[7],
        drivetrain.block.out_vars[1],
        drivetrain.block.out_vars[2],
    ))

    template: RmsModelTemplate = RmsModelTemplate(name=name)
    template.tpe = DeviceType.NoDevice
    template.block = root_block
    template.comment = (
        'Colib IEC Type-3 DFIG composition: P/Q controls, Type-3A current source, '
        'and two-mass drivetrain. Importers must replace default component parameters.'
    )
    return template
