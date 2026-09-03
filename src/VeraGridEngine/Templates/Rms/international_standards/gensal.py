# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
# SPDX-License-Identifier: MPL-2.0
"""GENSAL salient-pole synchronous generator."""

from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Templates.Rms.international_standards.auxiliary_functions import build_gensal

def build_gensal_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """Build the maintainable GENSAL runtime template.

    :param vf: Variable factory used to allocate the symbolic model variables.
    :type vf: VarFactory
    :param name: Optional instance name.
    :type name: str | None
    :return: Fully assembled GENSAL dynamic template.
    :rtype: RmsModelTemplate
    """
    template_name: str
    if name is None:
        template_name: str = 'GENSAL'
    else:
        template_name: str = name
    template: RmsModelTemplate = build_gensal(vf=vf, name=template_name)
    template.tpe = DeviceType.GeneratorDevice
    template.comment = 'Generator salient-pole synchronous machine'
    return template
