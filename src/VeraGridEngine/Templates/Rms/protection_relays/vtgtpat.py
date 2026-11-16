# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""PSS/E VTGTPAT voltage pickup and generator trip relay block."""

from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.auxiliary_functions import (
    build_generator_band_trip_relay,
)
from VeraGridEngine.enumerations import DeviceType


def build_vtgtpat_template(
        vf: VarFactory,
        name: str | None = None,
        lower_threshold_pu: float = 0.45,
        upper_threshold_pu: float = 1.2,
        pickup_time_s: float = 0.0,
        breaker_time_s: float = 0.0,
) -> RmsModelTemplate:
    """Build the voltage relay stages declared by PSS/E MINS VTGTPAT.

    :param vf: Variable factory shared with the target generator assembly.
    :param name: Optional source/model instance identity.
    :param lower_threshold_pu: Undervoltage pickup threshold.
    :param upper_threshold_pu: Overvoltage pickup threshold.
    :param pickup_time_s: Continuous pickup time outside the admissible band.
    :param breaker_time_s: Additional source breaker delay.
    :return: Native voltage relay with measurement and trip ports.
    """
    template_name: str = 'VTGTPAT' if name is None else name
    template: RmsModelTemplate = build_generator_band_trip_relay(
        vf=vf,
        name=template_name,
        measurement_name='UPu',
        lower_name='VL',
        upper_name='VU',
        lower_default=lower_threshold_pu,
        upper_default=upper_threshold_pu,
        pickup_default=pickup_time_s,
        breaker_default=breaker_time_s,
    )
    template.tpe = DeviceType.GeneratorDevice
    template.comment = 'PSS/E VTGTPAT voltage relay stages; bus routing and trip action are host responsibilities'
    return template
