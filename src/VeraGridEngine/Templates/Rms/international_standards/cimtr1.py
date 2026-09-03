# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
# SPDX-License-Identifier: MPL-2.0
"""CIMTR1 induction generator with rotor-flux transients."""

from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Templates.Rms.international_standards.auxiliary_functions import (
    InductionMachineRole,
    build_induction_machine,
)

def build_cimtr1_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """Build the CIMTR1 induction-generator template.

    :param vf: Variable factory used to allocate the symbolic model variables.
    :type vf: VarFactory
    :param name: Optional instance name for the returned template.
    :type name: str | None
    :returns: Fully assembled CIMTR1 dynamic template.
    :rtype: RmsModelTemplate
    """
    # Resolve the optional name before building the model so the shared
    # induction-machine implementation always receives an explicit identity.
    template_name: str
    if name is None:
        template_name: str = 'CIMTR1'
    else:
        template_name: str = name

    # Select the generator equations explicitly; the Enum prevents a string
    # option from silently choosing the wrong active-power sign convention.
    template: RmsModelTemplate = build_induction_machine(
        vf=vf,
        name=template_name,
        role=InductionMachineRole.GENERATOR,
    )
    template.tpe = DeviceType.GeneratorDevice
    template.comment = 'Generator CIMTR1 induction generator'
    return template
