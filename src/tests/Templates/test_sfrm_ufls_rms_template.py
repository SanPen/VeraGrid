# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Construction checks for the Colib SFRM/UFLS RMS template."""

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.protection_relays.sfrm_ufls_rms_template import get_sfrm_ufls_rms_template


def test_sfrm_ufls_has_frequency_and_governor_states() -> None:
    """Ensure the Colib transfer functions are represented as RMS states."""
    template = get_sfrm_ufls_rms_template(vf=VarFactory())
    names: set[str] = set(variable.name for variable in template.block.state_vars)

    assert {'FrequencyPu_SFRM_UFLS', 'GovernorMemoryPu_SFRM_UFLS'} <= names
