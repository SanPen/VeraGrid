# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""FRQTPA under/overfrequency generator trip relay."""

from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Templates.Rms.international_standards.auxiliary_functions import build_generator_band_trip_relay

def build_frqtpa_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """Build the default 57.5/61.8 Hz FRQTPA relay instance.

    :param vf: Variable factory used to allocate the relay symbols.
    :type vf: VarFactory
    :param name: Optional instance name.
    :type name: str | None
    :return: Fully assembled FRQTPA dynamic relay template.
    :rtype: RmsModelTemplate
    """
    template_name: str
    if name is None:
        template_name: str = 'FRQTPA'
    else:
        template_name: str = name

    # Bind the frequency-specific pickup thresholds to the shared procedural
    # relay algorithm while keeping one public construction entry point.
    template: RmsModelTemplate = build_generator_band_trip_relay(
        vf=vf,
        name=template_name,
        measurement_name="FHz",
        lower_name="FL",
        upper_name="FU",
        lower_default=57.5,
        upper_default=61.8,
    )
    template.tpe = DeviceType.GeneratorDevice
    template.comment = 'Generator frequency trip relay FRQTPA'
    return template
