# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""VTGTPA under/overvoltage generator trip relay."""

from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Templates.Rms.international_standards.auxiliary_functions import build_generator_band_trip_relay

def build_vtgtpa_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """Build the default 0.45/1.20 pu VTGTPA relay instance.

    :param vf: Variable factory used to allocate the relay symbols.
    :type vf: VarFactory
    :param name: Optional instance name.
    :type name: str | None
    :return: Fully assembled VTGTPA dynamic relay template.
    :rtype: RmsModelTemplate
    """
    template_name: str
    if name is None:
        template_name: str = 'VTGTPA'
    else:
        template_name: str = name

    # Bind the voltage-specific pickup thresholds to the shared procedural
    # relay algorithm while keeping one public construction entry point.
    template: RmsModelTemplate = build_generator_band_trip_relay(
        vf=vf,
        name=template_name,
        measurement_name="UPu",
        lower_name="VL",
        upper_name="VU",
        lower_default=0.45,
        upper_default=1.2,
    )
    template.tpe = DeviceType.GeneratorDevice
    template.comment = 'Generator voltage trip relay VTGTPA'
    return template
