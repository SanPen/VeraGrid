# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""AC9C selected source and dual rectifier-channel composition."""
from __future__ import annotations

from enum import Enum

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_potential_source import (
    Ac9cPotentialSourceSettings,
    build_ac9c_potential_source_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_power_exciter import (
    substitute_component_input,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_rectifier_supply import (
    Ac9cRectifierSupplySettings,
    _ac9c_fex_value,
    build_ac9c_rectifier_supply_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.enumerations import DeviceType


class Ac9cPotentialSourceSelection(Enum):
    """Select terminal-fed source A or independent source B with PSS/E SW1."""

    TERMINAL_FED = 1
    INDEPENDENT = 2


def ac9c_potential_source_selection_from_psse(sw1: int) -> Ac9cPotentialSourceSelection:
    """Translate the documented PSS/E SW1 positions to the native selector.

    :param sw1: PSS/E ICON value, where 1 is position A and 2 is position B.
    :return: Terminal-fed or independent source selection.
    :raises ValueError: SW1 is not a documented position.
    """
    if sw1 == 1:
        return Ac9cPotentialSourceSelection.TERMINAL_FED
    elif sw1 == 2:
        return Ac9cPotentialSourceSelection.INDEPENDENT
    else:
        raise ValueError('AC9C SW1 must select position 1 or 2')


def build_ac9c_rectifier_sources_template(
        vf: VarFactory,
        name: str = 'AC9C rectifier source network',
        selection: Ac9cPotentialSourceSelection = Ac9cPotentialSourceSelection.TERMINAL_FED,
        potential_settings: Ac9cPotentialSourceSettings | None = None,
        channel1_settings: Ac9cRectifierSupplySettings | None = None,
        channel2_settings: Ac9cRectifierSupplySettings | None = None,
) -> RmsModelTemplate:
    """Build both source channels and multiply their limited outputs into VCT.

    PSS/E 35.2 Model Library §6.14 selects ``y`` or ``KP`` through SW1, forms
    the independent current source from ``KI2*|IT|`` with a 0.001 pu floor,
    applies each channel's own ``KC*``/``VB*MAX`` characteristic, and defines
    ``VCT=VB1*VB2``.

    :param vf: Shared symbol factory for all component equations.
    :param name: Unique composition label.
    :param selection: Source A (terminal) or source B (independent pilot).
    :param potential_settings: Terminal/current source coefficients.
    :param channel1_settings: First rectifier channel loading and cap.
    :param channel2_settings: Second rectifier channel loading and cap.
    :return: Composed source block with four phasor inputs, VE input and VCT output.
    :raises ValueError: The selector is invalid.
    """
    if not isinstance(selection, Ac9cPotentialSourceSelection):
        raise ValueError('AC9C potential-source selection is invalid')
    else:
        pass

    selected_potential: Ac9cPotentialSourceSettings = (
        Ac9cPotentialSourceSettings() if potential_settings is None else potential_settings
    )
    selected_channel1: Ac9cRectifierSupplySettings = (
        Ac9cRectifierSupplySettings(
            source0=abs(selected_potential.kp),
        ) if channel1_settings is None else channel1_settings
    )
    selected_channel2: Ac9cRectifierSupplySettings = (
        Ac9cRectifierSupplySettings(source0=0.001)
        if channel2_settings is None else channel2_settings
    )
    channel1_initial_source: float = abs(selected_potential.kp)

    potential_block: Block = build_ac9c_potential_source_template(
        vf, name + ' potential sources', selected_potential,
    ).block
    channel1_block: Block = build_ac9c_rectifier_supply_template(
        vf, name + ' channel 1', selected_channel1,
    ).block
    channel2_block: Block = build_ac9c_rectifier_supply_template(
        vf, name + ' channel 2', selected_channel2,
    ).block

    ve: Var = vf.add_var('ExciterVoltagePu_' + name)
    channel1_source_port: Var = channel1_block.in_vars[0]
    channel1_ve_port: Var = channel1_block.in_vars[1]
    channel2_source_port: Var = channel2_block.in_vars[0]
    channel2_ve_port: Var = channel2_block.in_vars[1]
    if selection is Ac9cPotentialSourceSelection.TERMINAL_FED:
        source1: Expr = potential_block.out_vars[0]
    else:
        source1 = Const(abs(selected_potential.kp))
    substitute_component_input(channel1_block, channel1_source_port, source1)
    substitute_component_input(channel1_block, channel1_ve_port, ve)
    substitute_component_input(channel2_block, channel2_source_port, potential_block.out_vars[1])
    substitute_component_input(channel2_block, channel2_ve_port, ve)

    channel1_voltage: Var = channel1_block.out_vars[0]
    channel2_voltage: Var = channel2_block.out_vars[0]
    initial_channel1_loading: float = (
        selected_channel1.kc * channel1_initial_source / selected_channel1.ve0
    )
    initial_channel1_voltage: float = min(
        selected_channel1.vbmax,
        channel1_initial_source * _ac9c_fex_value(initial_channel1_loading),
    )
    initial_channel2_loading: float = (
        selected_channel2.kc * selected_channel2.source0 / selected_channel2.ve0
    )
    initial_channel2_voltage: float = min(
        selected_channel2.vbmax,
        selected_channel2.source0*_ac9c_fex_value(initial_channel2_loading),
    )
    combiner: ControlRealization = ControlRealization(vf, name + ' VCT product')
    channel1_input: Var = combiner.input('VB1Pu', Const(initial_channel1_voltage))
    channel2_input: Var = combiner.input('VB2Pu', Const(initial_channel2_voltage))
    terminal_source_voltage: Var = combiner.algebraic(
        'VCTPu', channel1_input * channel2_input,
        Const(initial_channel1_voltage * initial_channel2_voltage),
    )
    combiner_block: Block = combiner.finish(
        (terminal_source_voltage,), 'AC9C VCT source-channel product',
    ).block
    substitute_component_input(combiner_block, channel1_input, channel1_voltage)
    substitute_component_input(combiner_block, channel2_input, channel2_voltage)

    root: Block = Block(name=name)
    root.children = list((potential_block, channel1_block, channel2_block, combiner_block))
    root.in_vars = list(potential_block.in_vars) + [ve]
    root.out_vars = list((terminal_source_voltage, channel1_voltage, channel2_voltage))
    root.unify_blocks()
    root.in_vars = list(potential_block.in_vars) + [ve]
    root.out_vars = list((terminal_source_voltage, channel1_voltage, channel2_voltage))

    template: RmsModelTemplate = RmsModelTemplate(name=name)
    template.tpe = DeviceType.NoDevice
    template.block = root
    template.comment = 'AC9C SW1 source selection and independently limited dual-channel VCT composition'
    return template
