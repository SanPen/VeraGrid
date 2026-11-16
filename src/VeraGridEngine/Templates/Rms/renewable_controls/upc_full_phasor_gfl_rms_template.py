# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Colib UPC full-phasor grid-following VSC RMS template."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.converters.vsc_gfl import VscGflBuild
from VeraGridEngine.enumerations import ConverterControlType


def get_upc_full_phasor_gfl_rms_template(
        vf: VarFactory,
        name: str = 'UPC full-phasor GFL VSC',
) -> RmsModelTemplate:
    """Build the UPC full-phasor grid-following VSC realization.

    The native RMS GFL builder provides the full current-control and power-loop
    structure used by the Colib full-phasor model. DC-voltage and reactive-power
    modes preserve the usual HVDC station boundary.

    :param vf: Variable factory used to allocate symbolic variables.
    :param name: Unique template instance name.
    :return: RMS full-phasor grid-following VSC template.
    """
    template: RmsModelTemplate = VscGflBuild(
        vfactory=vf,
        name=name,
        control1=ConverterControlType.Vm_dc,
        control2=ConverterControlType.Qac,
    )
    template.comment = 'Colib UPC full-phasor grid-following VSC realization'
    return template
