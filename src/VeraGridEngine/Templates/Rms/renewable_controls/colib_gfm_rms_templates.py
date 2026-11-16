# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Named Colib RMS grid-forming VSC templates."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.converters.vsc_gfm import VscGfmBuild


def get_epri_gfm_rms_template(vf: VarFactory, name: str = 'EPRI GFM') -> RmsModelTemplate:
    """Build the Colib EPRI grid-forming RMS VSC entry point.

    :param vf: Variable factory used to allocate symbolic variables.
    :param name: Unique template instance name.
    :return: RMS grid-forming VSC template.
    """
    # Reuse the validated RMS GFM dynamics as the common Colib realization.
    template: RmsModelTemplate = VscGfmBuild(vfactory=vf, name=name)
    template.comment = 'Colib EPRI grid-forming RMS VSC realization'
    return template


def get_upc_gfm_rms_template(vf: VarFactory, name: str = 'UPC RMS GFM') -> RmsModelTemplate:
    """Build the Colib UPC grid-forming RMS VSC entry point.

    :param vf: Variable factory used to allocate symbolic variables.
    :param name: Unique template instance name.
    :return: RMS grid-forming VSC template.
    """
    # Reuse the validated RMS GFM dynamics as the common Colib realization.
    template: RmsModelTemplate = VscGfmBuild(vfactory=vf, name=name)
    template.comment = 'Colib UPC grid-forming RMS VSC realization'
    return template
