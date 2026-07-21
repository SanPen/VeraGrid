# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.bridge_filter_2level_3ph_emt_mti_template import (
    get_bridge_filter_2level_3ph_emt_mti_template,
)
from VeraGridEngine.Utils.Symbolic.block import find_name_in_block
import VeraGridEngine.Templates.Emt.bridge_filter_control_2level_3ph_emt_template as control_ref


def get_bridge_filter_control_2level_3ph_emt_mti_template(
        vf: VarFactory,
        name: str = "bridge_filter_control_2level_3ph_emt_mti",
) -> EmtModelTemplate:
    """Build the standard bridge/filter/control stack with an MTI bridge plant."""
    original_builder = control_ref.get_bridge_filter_2level_3ph_emt_template
    control_ref.get_bridge_filter_2level_3ph_emt_template = get_bridge_filter_2level_3ph_emt_mti_template
    try:
        templ = control_ref.get_bridge_filter_control_2level_3ph_emt_template(vf=vf, name=name)
    finally:
        control_ref.get_bridge_filter_2level_3ph_emt_template = original_builder

    omega_sw_in = find_name_in_block(f"omega_sw_in_{name}", templ.block)
    omega_meas_in = find_name_in_block(f"omega_meas_in_{name}", templ.block)
    templ.block.update_model(omega_sw_in, omega_meas_in)
    return templ
