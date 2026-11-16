# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Colib frequency-dependent Martí line EMT template."""

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.line.jmarti_line_emt_template import get_jmarti_line_emt_template


def get_frequency_dependent_line_emt_template(
        vf: VarFactory,
        name: str = 'Frequency-dependent line',
) -> EmtModelTemplate:
    """Build the Colib frequency-dependent three-phase Martí line.

    The companion JMARTI runtime consumes the modal frequency samples and
    updates the retained Norton history terms for the fitted line response.

    :param vf: Variable factory used to allocate symbolic variables.
    :param name: Unique template instance name.
    :return: EMT frequency-dependent Martí line template.
    """
    # Colib uses a three-phase line without an explicit neutral conductor.
    template: EmtModelTemplate = get_jmarti_line_emt_template(
        vf=vf,
        phN=False,
        phA=True,
        phB=True,
        phC=True,
        name=name,
    )
    template.comment = 'Colib frequency-dependent Martí line with modal runtime'
    return template
