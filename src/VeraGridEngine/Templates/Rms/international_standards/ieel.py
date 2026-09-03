# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
# SPDX-License-Identifier: MPL-2.0
"""IEEL IEEE voltage- and frequency-dependent load."""

from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Templates.Rms.international_standards.auxiliary_functions import build_ieel

def build_ieel_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """Build the maintainable IEEL runtime template.

    :param vf: Variable factory used to allocate the symbolic model variables.
    :type vf: VarFactory
    :param name: Optional instance name.
    :type name: str | None
    :return: Fully assembled IEEL dynamic template.
    :rtype: RmsModelTemplate
    """
    template_name: str
    if name is None:
        template_name: str = 'IEEL'
    else:
        template_name: str = name
    template: RmsModelTemplate = build_ieel(vf=vf, name=template_name)
    template.tpe = DeviceType.GeneratorDevice
    template.comment = 'Generator excitation limiter IEEL'
    return template
