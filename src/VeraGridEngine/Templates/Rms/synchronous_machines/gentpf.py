# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Colib GENTPF saturated synchronous-machine template."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.synchronous_machines.genroe import (
    build_genroe_template,
)


def build_gentpf_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """Build the GENTPF saturated round-rotor machine.

    GENTPF is the GENTPJ saturation family with its stator-current gain fixed
    to zero. VeraGrid's power-law GENROE realization already has that form.

    :param vf: Variable factory used to allocate symbolic variables.
    :param name: Optional unique model instance name.
    :return: Six-state saturated synchronous-machine template.
    """
    template_name: str = 'GENTPF' if name is None else name
    template: RmsModelTemplate = build_genroe_template(vf=vf, name=template_name)
    template.comment = 'Colib GENTPF saturated round-rotor synchronous machine'
    return template
