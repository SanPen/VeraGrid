# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.bridge_filter_control_2level_3ph_emt_mti_template import (
    get_bridge_filter_control_2level_3ph_emt_mti_template,
)
import VeraGridEngine.Templates.Emt.converter_switched_emt_template as switched_ref


def get_switched_emt_converter_mti(
        vf: VarFactory,
        name: str = "switched_converter_emt_mti",
) -> EmtModelTemplate:
    """Build the normal switched converter with only the PWM bridge handled by MTI."""
    original_builder = switched_ref.get_bridge_filter_control_2level_3ph_emt_template
    switched_ref.get_bridge_filter_control_2level_3ph_emt_template = get_bridge_filter_control_2level_3ph_emt_mti_template
    try:
        return switched_ref.get_switched_emt_converter(vf=vf, name=name)
    finally:
        switched_ref.get_bridge_filter_control_2level_3ph_emt_template = original_builder
