# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""L2EP generic RMS grid-following voltage-source converter template."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.converters.vsc_gfl import VscGflBuild
from VeraGridEngine.enumerations import ConverterControlType
from VeraGridEngine.Utils.procedural_logic import flipflop


def get_l2ep_rms_gfl_template(
        vf: VarFactory,
        name: str = 'L2EP RMS GFL VSC',
) -> RmsModelTemplate:
    """Build the L2EP-style RMS grid-following VSC core.

    The native GFL core provides the differential transformer-current equations,
    PLL, active/reactive power controls, and reactive-current-first circular
    current limit required by the L2EP physical and control structure.

    :param vf: Variable factory used to allocate symbolic variables.
    :param name: Unique template instance name.
    :return: RMS grid-following VSC template.
    """
    # L2EP models a fixed DC side and regulates active and reactive AC power.
    template: RmsModelTemplate = VscGflBuild(
        vfactory=vf,
        name=name,
        control1=ConverterControlType.Pac,
        control2=ConverterControlType.Qac,
    )
    gfl_block = template.block.children[0]
    pll_blocked = vf.add_var('PLL_blocked')
    pll_block_voltage = vf.add_var('Vpll1')
    pll_restart_voltage = vf.add_var('Vpll2')
    pll_angle = gfl_block.state_vars[0]

    # L2EP freezes the PLL angle after undervoltage and releases it after recovery.
    gfl_block.state_eqs[0] = (vf.add_const(1.0) - pll_blocked) * gfl_block.state_eqs[0]
    gfl_block.event_dict[pll_block_voltage] = vf.add_const(0.4)
    gfl_block.event_dict[pll_restart_voltage] = vf.add_const(0.5)
    gfl_block.mode_dict[pll_blocked] = vf.add_const(0.0)
    gfl_block.procedural_logic.append(
        flipflop(
            boolset=template.block.in_vars[0] <= pll_block_voltage,
            boolreset=template.block.in_vars[0] >= pll_restart_voltage,
            output=pll_blocked,
            name='l2ep_pll_voltage_latch',
        )
    )
    gfl_block.init_eqs[pll_angle] = template.block.in_vars[1]
    template.comment = 'L2EP RMS GFL VSC with PLL low-voltage hysteresis'
    return template
