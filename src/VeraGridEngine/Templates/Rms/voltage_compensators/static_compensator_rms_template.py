# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Colib static compensator RMS template."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.buses.shunt_template import ShuntLoadBuild


def get_static_compensator_rms_template(
        vf: VarFactory,
        name: str = 'Static compensator',
) -> RmsModelTemplate:
    """Build the fixed-reactance Colib static compensator.

    The Colib equation ``Qc = Vr**2 / Xc`` is the constant-susceptance shunt
    realization with ``b = 1 / Xc``. Positive or negative ``b`` therefore
    selects capacitive injection or inductive absorption.

    :param vf: Variable factory used to allocate symbolic variables.
    :param name: Unique template instance name.
    :return: RMS constant-reactance compensator template.
    """
    # Reuse the native static shunt because the Colib model has no dynamics.
    template: RmsModelTemplate = ShuntLoadBuild(vfactory=vf, name=name)
    template.comment = 'Colib fixed-reactance static compensator RMS realization'
    return template
