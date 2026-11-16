# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Colib WECC rotor-flux induction-motor RMS template."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.induction_machines.load_motor import (
    build_load_motor_template,
)
from VeraGridEngine.enumerations import InductionMachineRole


def get_wecc_rotor_flux_induction_motor_rms_template(
        vf: VarFactory,
        name: str = 'WECC rotor-flux induction motor',
) -> RmsModelTemplate:
    """Build the Colib fifth-order rotor-flux induction motor.

    :param vf: Variable factory used to allocate symbolic variables.
    :param name: Unique template instance name.
    :return: Fifth-order RMS rotor-flux induction-motor template.
    """
    # Retain both flux pairs and rotor speed for the published fifth-order form.
    template: RmsModelTemplate = build_load_motor_template(
        vfactory=vf,
        name=name,
        role=InductionMachineRole.MOTOR,
        single_cage=False,
    )
    template.comment = 'Colib fifth-order rotor-flux induction motor RMS realization'
    return template
