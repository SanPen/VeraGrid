# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Colib constant-parameter travelling-wave line EMT template."""

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.line.bergeron_line_emt_template import (
    get_bergeron_line_emt_template,
)


def get_constant_parameter_line_emt_template(
        vf: VarFactory,
        name: str = 'Constant-parameter line',
) -> EmtModelTemplate:
    """Build the Colib Bergeron constant-parameter three-phase line.

    :param vf: Variable factory used to allocate symbolic variables.
    :param name: Unique template instance name.
    :return: EMT Bergeron line with travel-time history channels.
    """
    # Colib assumes the usual three phase conductors without a neutral return.
    template: EmtModelTemplate = get_bergeron_line_emt_template(
        vf=vf,
        phN=False,
        phA=True,
        phB=True,
        phC=True,
        name=name,
    )
    template.comment = 'Colib constant-parameter Bergeron travelling-wave line'
    return template
