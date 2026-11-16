# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Colib steady-state pi-equivalent line RMS template."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.line.line_phasor_rms_template import get_line_phasor_rms_template


def get_pi_equivalent_line_rms_template(
        vf: VarFactory,
        name: str = 'Pi-equivalent line',
) -> RmsModelTemplate:
    """Build the Colib steady-state pi-equivalent transmission line.

    The native phasor line applies series admittance and equal half-shunt
    admittances at each terminal, matching the Colib pi-equivalent circuit.

    :param vf: Variable factory used to allocate symbolic variables.
    :param name: Unique template instance name.
    :return: RMS phasor pi-line template.
    """
    # Reuse the native current-balance form of the Colib terminal equations.
    template: RmsModelTemplate = get_line_phasor_rms_template(vfactory=vf, name=name)
    template.comment = 'Colib steady-state pi-equivalent RMS line realization'
    return template
