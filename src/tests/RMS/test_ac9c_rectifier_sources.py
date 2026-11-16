# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Check the composed AC9C dual potential-source channels and SW1 mapping."""

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_potential_source import (
    Ac9cPotentialSourceSettings,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_rectifier_sources import (
    Ac9cPotentialSourceSelection,
    ac9c_potential_source_selection_from_psse,
    build_ac9c_rectifier_sources_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_rectifier_supply import (
    Ac9cRectifierSupplySettings,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def evaluate_ac9c_source_network(
        block: Block,
        voltage: complex,
        current: complex,
        ve: float,
) -> tuple[float, float, float]:
    """Evaluate all source-network algebraics at one phasor operating point.

    :param block: Composed AC9C source network.
    :param voltage: Terminal-voltage phasor.
    :param current: Outgoing terminal-current phasor.
    :param ve: Exciter field-voltage state.
    :return: VCT, VB1 and VB2 values.
    """
    bindings: dict[int, float] = dict()
    for parameter, value in block.event_dict.items():
        if isinstance(value, Const):
            bindings[parameter.uid] = float(value.value)
        else:
            pass
    input_values: tuple[float, ...] = (
        voltage.real, voltage.imag, current.real, current.imag, ve,
    )
    for variable, value in zip(block.in_vars, input_values):
        bindings[variable.uid] = value
    for variable, equation in zip(block.algebraic_vars, block.algebraic_eqs):
        bindings[variable.uid] = equation.right.eval_uid(bindings)
    assert all(equation.eval_uid(bindings) == pytest.approx(0.0)
               for equation in block.algebraic_eqs)
    return tuple(bindings[variable.uid] for variable in block.out_vars)


@pytest.mark.parametrize(
    'selection,expected_vct',
    ((Ac9cPotentialSourceSelection.TERMINAL_FED, .16),
     (Ac9cPotentialSourceSelection.INDEPENDENT, .2)),
)
def test_ac9c_source_network_selects_and_multiplies_both_channels(
        selection: Ac9cPotentialSourceSelection,
        expected_vct: float,
) -> None:
    """Select V1 or KP, rectify both channels and form VCT=VB1*VB2."""
    potential: Ac9cPotentialSourceSettings = Ac9cPotentialSourceSettings(
        kp=1.0, ki1=0.0, ki2=1.0, xl=0.0, theta_p=0.0,
    )
    source1: float = .8 if selection is Ac9cPotentialSourceSelection.TERMINAL_FED else 1.0
    block: Block = build_ac9c_rectifier_sources_template(
        VarFactory(), selection=selection, potential_settings=potential,
        channel1_settings=Ac9cRectifierSupplySettings(
            kc=0.0, vbmax=2.0, source0=source1, ve0=1.0,
        ),
        channel2_settings=Ac9cRectifierSupplySettings(
            kc=0.0, vbmax=2.0, source0=.2, ve0=1.0,
        ),
    ).block
    vct: float
    vb1: float
    vb2: float
    vct, vb1, vb2 = evaluate_ac9c_source_network(
        block, voltage=.8+0j, current=.2+0j, ve=1.0,
    )
    assert vb1 == pytest.approx(source1)
    assert vb2 == pytest.approx(.2)
    assert vct == pytest.approx(expected_vct)


@pytest.mark.parametrize(
    'sw1,expected',
    ((1, Ac9cPotentialSourceSelection.TERMINAL_FED),
     (2, Ac9cPotentialSourceSelection.INDEPENDENT)),
)
def test_psse_sw1_maps_to_the_documented_source_position(
        sw1: int,
        expected: Ac9cPotentialSourceSelection,
) -> None:
    """Map PSS/E positions A/B without reversing source meaning."""
    assert ac9c_potential_source_selection_from_psse(sw1) is expected


def test_psse_sw1_rejects_undocumented_positions() -> None:
    """Reject SW1 values outside the two documented settings."""
    with pytest.raises(ValueError, match='position 1 or 2'):
        ac9c_potential_source_selection_from_psse(3)
