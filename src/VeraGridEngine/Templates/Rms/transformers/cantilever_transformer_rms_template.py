# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Colib cantilever-equivalent transformer RMS template."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.transformers.transformer_rms_template import TrafoRmsTemplate


def get_cantilever_transformer_rms_template(
        vf: VarFactory,
        name: str = 'Cantilever transformer',
) -> RmsModelTemplate:
    """Build the Colib fixed-ratio cantilever transformer equivalent.

    The native model supplies the series conductance/susceptance and shunt
    iron/magnetizing branch of the Colib steady-state cantilever circuit.

    :param vf: Variable factory used to allocate symbolic variables.
    :param name: Unique template instance name.
    :return: RMS two-winding cantilever-equivalent transformer template.
    """
    # Reuse the native two-winding DAE with series and magnetizing branches.
    template: RmsModelTemplate = TrafoRmsTemplate(vf=vf, name=name)
    template.comment = 'Colib fixed-ratio cantilever transformer RMS realization'
    return template
