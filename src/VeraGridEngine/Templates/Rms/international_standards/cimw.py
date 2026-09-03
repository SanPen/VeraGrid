# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
# SPDX-License-Identifier: MPL-2.0
"""CIMW WECC induction motor."""

from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Templates.Rms.international_standards.auxiliary_functions import (
    InductionMachineRole,
    build_induction_machine,
)

def build_cimw_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """Build the CIMW induction-motor template.

    :param vf: Variable factory used to allocate the symbolic model variables.
    :type vf: VarFactory
    :param name: Optional instance name for the returned template.
    :type name: str | None
    :returns: Fully assembled CIMW dynamic template.
    :rtype: RmsModelTemplate
    """
    # Resolve the instance name before entering the shared machine equations so
    # that the returned dynamic model always has a stable public identity.
    template_name: str
    if name is None:
        template_name: str = 'CIMW'
    else:
        template_name: str = name

    # Select the motor equations explicitly to activate the CIMW load-torque
    # law and its consumption-oriented active-power sign convention.
    template: RmsModelTemplate = build_induction_machine(
        vf=vf,
        name=template_name,
        role=InductionMachineRole.MOTOR,
    )
    template.tpe = DeviceType.LoadDevice
    template.comment = 'Load CIMW induction motor'
    return template
