# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
# SPDX-License-Identifier: MPL-2.0
"""GGOV1 GE general-purpose turbine governor."""

from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Templates.Rms.international_standards.auxiliary_functions import build_ggov1

def build_ggov1_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """Build the maintainable GGOV1 runtime template.

    :param vf: Variable factory used to allocate the symbolic model variables.
    :type vf: VarFactory
    :param name: Optional instance name.
    :type name: str | None
    :return: Fully assembled GGOV1 dynamic template.
    :rtype: RmsModelTemplate
    """
    template_name: str
    if name is None:
        template_name: str = 'GGOV1'
    else:
        template_name: str = name
    template: RmsModelTemplate = build_ggov1(vf=vf, name=template_name)
    template.tpe = DeviceType.GeneratorDevice
    template.comment = 'Generator governor GGOV1'
    return template
