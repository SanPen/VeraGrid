# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Colib grid-following EMT STATCOM template."""

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.converters.vsc_gfl_emt import VscGflEmtBuild


def get_statcom_gfl_emt_template(
        vf: VarFactory,
        name: str = 'STATCOM_GFL',
) -> EmtModelTemplate:
    """Build the Colib EMT STATCOM from the native GFL converter core.

    The shared realization supplies the balanced two-level VSC, PLL, filter,
    inner current control, and DC-link capacitor required by Colib. STATCOM
    operation selects the DC-voltage/AC-voltage control pair at configuration
    time rather than redefining the electrical converter equations.

    :param vf: Variable factory used to allocate symbolic variables.
    :param name: Unique template instance name.
    :return: Native EMT grid-following STATCOM template.
    """
    template: EmtModelTemplate = VscGflEmtBuild(vfactory=vf, name=name)
    template.comment = 'Colib grid-following EMT STATCOM realization'
    return template
