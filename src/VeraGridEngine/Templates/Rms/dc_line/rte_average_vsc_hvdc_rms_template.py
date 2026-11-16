# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Colib RTE average phasor VSC-HVDC terminal template."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.converters.hvdc_vsc_gfl_rms_template_v2 import (
    get_hvdc_vdc_q_vsc_rms,
)


def get_rte_average_vsc_hvdc_rms_template(
        vf: VarFactory,
        name: str = 'RTE average VSC-HVDC',
) -> RmsModelTemplate:
    """Build one RTE-style average phasor VSC-HVDC terminal.

    The native terminal provides the Colib DC-voltage, active/reactive-current,
    and U/Q-control boundary. Two instances, one Vdc/Q and one Pdc/Q, compose a
    point-to-point RTE link through VeraGrid's DC network components.

    :param vf: Variable factory used to allocate symbolic variables.
    :param name: Unique converter-station name.
    :return: Explicit-state RMS VSC-HVDC terminal template.
    """
    template: RmsModelTemplate = get_hvdc_vdc_q_vsc_rms(vfactory=vf, name=name)
    template.comment = 'Colib RTE average phasor VSC-HVDC terminal realization'
    return template
