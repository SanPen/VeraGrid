# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Colib single-cage induction-motor RMS template."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.induction_machines.load_motor import (
    build_load_motor_template,
)
from VeraGridEngine.enumerations import InductionMachineRole


def get_single_cage_induction_motor_rms_template(
        vf: VarFactory,
        name: str = 'Single-cage induction motor',
) -> RmsModelTemplate:
    """Build the Colib balanced linear single-cage induction motor.

    :param vf: Variable factory used to allocate symbolic variables.
    :param name: Unique template instance name.
    :return: Third-order one-cage RMS induction-motor template.
    """
    # Select the native one-cage reduction and motor power-flow sign convention.
    template: RmsModelTemplate = build_load_motor_template(
        vfactory=vf,
        name=name,
        role=InductionMachineRole.MOTOR,
        single_cage=True,
    )
    template.comment = 'Colib balanced linear single-cage induction motor RMS realization'
    return template
