# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""PSS/E CIMW WECC induction-motor catalog entry."""

from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.induction_machines.psse_cim_motor import (
    PsseCimMotorParameters,
    PsseCimMotorType,
    build_cimw_psse_template,
)


def build_cimw_template(
        vf: VarFactory,
        name: str | None = None,
        parameters: PsseCimMotorParameters | None = None,
        motor_type: PsseCimMotorType = PsseCimMotorType.TYPE_A,
) -> RmsModelTemplate:
    """Build the PSS/E CIMW load-motor RMS template.

    :param vf: Variable factory used for symbolic model construction.
    :param name: Optional runtime instance name.
    :param parameters: Optional source parameters and resolved load bases.
    :param motor_type: PSS/E Type A or Type B rotor-cage circuit.
    :return: Native PSS/E CIMW load-motor template.
    """
    template: RmsModelTemplate = build_cimw_psse_template(
        vf=vf,
        name=name,
        parameters=parameters,
        motor_type=motor_type,
    )
    return template
