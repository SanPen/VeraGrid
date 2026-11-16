# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Physical-equation and equilibrium checks for unsaturated WT2G1."""

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.induction_machines.wt2g1_electrical_core import (
    Wt2g1ElectricalSettings,
    build_wt2g1_electrical_core,
    derive_wt2g1_operating_point,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from tests.symbolic_block_roundtrip import roundtrip_block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def _initial_bindings(block: Block) -> dict[int, float]:
    """Collect constant source parameters and analytic machine seeds.

    :param block: WT2G1 electrical block.
    :return: UID values for direct residual evaluation.
    """
    bindings: dict[int, float] = dict()
    variable: Var
    expression: Expr
    for variable, expression in block.init_eqs.items():
        if isinstance(expression, Const):
            bindings[variable.uid] = float(expression.value)
        else:
            pass
    for variable, expression in block.event_dict.items():
        if isinstance(expression, Const):
            bindings[variable.uid] = float(expression.value)
        else:
            pass
    return bindings


def test_wt2g1_machine_equilibrium_and_generator_sign() -> None:
    """Balance rotor flux and stator current at generating slip without inertia.

    :return: None.
    """
    block: Block = build_wt2g1_electrical_core(VarFactory()).block
    bindings: dict[int, float] = _initial_bindings(block)
    assert len(block.state_vars) == 2
    assert len(block.in_vars) == 4
    assert bindings[block.out_vars[0].uid] > 0.
    assert bindings[block.out_vars[1].uid] < 0.
    assert bindings[block.out_vars[2].uid] * bindings[block.in_vars[2].uid] == pytest.approx(
        bindings[block.out_vars[0].uid],
    )
    equation: Expr
    for equation in block.state_eqs:
        assert equation.eval_uid(bindings) == pytest.approx(0., abs=1e-12)
    for equation in block.algebraic_eqs:
        assert equation.eval_uid(bindings) == pytest.approx(0., abs=1e-12)
    bindings[block.in_vars[2].uid] = 1.03
    assert block.state_eqs[0].eval_uid(bindings) != pytest.approx(0.)
    bindings[block.in_vars[2].uid] = 1.02
    bindings[block.in_vars[3].uid] = .99
    assert block.state_eqs[0].eval_uid(bindings) != pytest.approx(0.)


def test_wt2g1_stator_copper_loss_and_nonzero_voltage_angle() -> None:
    """Preserve terminal-current signs and air-gap torque with stator loss.

    :return: None.
    """
    block: Block = build_wt2g1_electrical_core(
        VarFactory(), settings=Wt2g1ElectricalSettings(
            ra=.015, initial_vd=.2, initial_vq=.98,
        ),
    ).block
    bindings: dict[int, float] = _initial_bindings(block)
    equation: Expr
    for equation in block.state_eqs:
        assert equation.eval_uid(bindings) == pytest.approx(0., abs=1e-12)
    for equation in block.algebraic_eqs:
        assert equation.eval_uid(bindings) == pytest.approx(0., abs=1e-12)
    current_d: float = bindings[block.out_vars[3].uid]
    current_q: float = bindings[block.out_vars[4].uid]
    electrical_power: float = bindings[block.out_vars[0].uid]
    electrical_torque: float = bindings[block.out_vars[2].uid]
    assert electrical_torque * bindings[block.in_vars[2].uid] - electrical_power == pytest.approx(
        .015 * (current_d ** 2 + current_q ** 2),
    )
    restored: Block = roundtrip_block(block)
    assert len(restored.state_vars) == 2
    assert len(restored.out_vars) == 5


def test_wt2g1_fits_initial_slip_and_resistance_to_power_flow() -> None:
    """Invert the WT2G1 curve and rotor circuit for a solved generator P.

    :return: None.
    """
    curve: tuple[tuple[float, float], ...] = (
        (0., 0.), (.0054, .0217), (.02, .8988), (.04, .9), (.1, .905),
    )
    settings: Wt2g1ElectricalSettings = derive_wt2g1_operating_point(
        Wt2g1ElectricalSettings(), target_power=.6, voltage_d=0., voltage_q=1.,
        curve=curve,
    )
    assert 1.0054 < settings.initial_speed < 1.02
    assert 0. < settings.initial_resistance_fraction < 1.
    block: Block = build_wt2g1_electrical_core(VarFactory(), settings=settings).block
    power_seed: Expr = block.init_eqs[block.out_vars[0]]
    assert isinstance(power_seed, Const)
    assert float(power_seed.value) == pytest.approx(.6, abs=1e-9)
    with pytest.raises(ValueError, match='exceeds'):
        derive_wt2g1_operating_point(Wt2g1ElectricalSettings(), 1., 0., 1., curve)


@pytest.mark.parametrize('settings', (
    Wt2g1ElectricalSettings(se1=.03),
    Wt2g1ElectricalSettings(xm=0.),
    Wt2g1ElectricalSettings(r_rot_max=.001),
    Wt2g1ElectricalSettings(initial_resistance_fraction=1.2),
    Wt2g1ElectricalSettings(initial_speed=0.),
    Wt2g1ElectricalSettings(initial_vd=0., initial_vq=0.),
))
def test_wt2g1_rejects_unsupported_or_singular_data(settings: Wt2g1ElectricalSettings) -> None:
    """Keep unsupported saturation and impossible electrical data explicit.

    :param settings: Invalid source or host context.
    :return: None.
    """
    with pytest.raises(ValueError):
        build_wt2g1_electrical_core(VarFactory(), settings=settings)
