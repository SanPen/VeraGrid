# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.bridge_2level_3ph_emt_mti_template import get_bridge_2level_3ph_emt_mti_template
import VeraGridEngine.Templates.Emt.bridge_filter_2level_3ph_emt_template as bridge_filter_ref


def get_bridge_filter_2level_3ph_emt_mti_template(
        vf: VarFactory,
        name: str = "bridge_filter_2level_3ph_emt_mti",
) -> EmtModelTemplate:
    """Build the standard bridge/filter plant with the bridge swapped to MTI PWM."""
    original_builder = bridge_filter_ref.get_bridge_2level_3ph_emt_template
    bridge_filter_ref.get_bridge_2level_3ph_emt_template = get_bridge_2level_3ph_emt_mti_template
    try:
        return bridge_filter_ref.get_bridge_filter_2level_3ph_emt_template(vf=vf, name=name)
    finally:
        bridge_filter_ref.get_bridge_2level_3ph_emt_template = original_builder
