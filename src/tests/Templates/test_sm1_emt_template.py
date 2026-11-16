# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Construction checks for the Colib SM1 EMT template."""

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.synchronous_machines.sm1_emt_template import get_sm1_emt_template


def test_sm1_uses_the_physical_winding_machine() -> None:
    """Ensure SM1 keeps the flux and mechanical states required by Colib."""
    factory: VarFactory = VarFactory()
    template = get_sm1_emt_template(vf=factory)
    names: set[str] = set(variable.name for variable in template.block.state_vars)

    assert {'psi_d', 'psi_q', 'psi_0', 'psi_f', 'theta_elec', 'w_mec'} <= names
