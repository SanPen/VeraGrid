# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Check the AC9C rotating-exciter field and rectifier equations."""

import math

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_rotating_exciter import (
    Ac9cRotatingExciterSettings,
    build_ac9c_rotating_exciter_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def make_exciter_bindings(block: Block, efe: float, ifd: float, ve: float,
                          vfe: float, efd: float, saturation: float) -> dict[int, float]:
    """Bind exciter parameters, ports, state and algebraic signals.

    :param block: Native AC9C rotating-exciter block.
    :param efe: Exciter input voltage.
    :param ifd: Field current.
    :param ve: Exciter field-voltage state.
    :param vfe: Computed field-feedback value.
    :param efd: Delivered field voltage.
    :param saturation: Saturation factor.
    :return: UID-keyed numeric expression bindings.
    """
    bindings: dict[int, float] = dict()
    parameter: Var
    value: Expr
    for parameter, value in block.event_dict.items():
        if isinstance(value, Const):
            bindings[parameter.uid] = float(value.value)
        else:
            pass
    bindings[block.in_vars[0].uid] = efe
    bindings[block.in_vars[1].uid] = ifd
    bindings[block.state_vars[0].uid] = ve
    bindings[block.algebraic_vars[0].uid] = saturation
    bindings[block.algebraic_vars[1].uid] = vfe
    bindings[block.algebraic_vars[2].uid] = efd
    return bindings


def test_ac9c_rotating_exciter_field_feedback_and_rectifier_output() -> None:
    """Check equilibrium field feedback, state rate and EFD conversion.

    :return: None.
    """
    settings: Ac9cRotatingExciterSettings = Ac9cRotatingExciterSettings(
        kc=.2, kd=.1, ke=1., te=.5, vfemax=5., vemin=.1,
        efe0=1.1, ifd0=1., ve0=1.,
    )
    block: Block = build_ac9c_rotating_exciter_template(
        vf=VarFactory(), settings=settings,
    ).block
    bindings: dict[int, float] = make_exciter_bindings(
        block, efe=1.1, ifd=1., ve=1., vfe=1.1, efd=0.8846, saturation=0.,
    )
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(0.)
    assert block.algebraic_eqs[1].eval_uid(bindings) == pytest.approx(0.)
    assert block.algebraic_eqs[2].eval_uid(bindings) == pytest.approx(0., abs=1e-4)


def test_ac9c_rotating_exciter_applies_saturation_and_dynamic_upper_stop() -> None:
    """Use the two-point saturation curve and stop outward field travel.

    :return: None.
    """
    settings: Ac9cRotatingExciterSettings = Ac9cRotatingExciterSettings(
        kc=.2, kd=.1, ke=1., te=.5, vfemax=5., vemin=.1,
        e1=3., se1=.1, e2=4., se2=.3, efe0=3.35, ifd0=.5, ve0=3.,
    )
    block: Block = build_ac9c_rotating_exciter_template(
        vf=VarFactory(), settings=settings,
    ).block
    bindings: dict[int, float] = make_exciter_bindings(
        block, efe=3.35, ifd=.5, ve=3., vfe=3.35, efd=2.9, saturation=.1,
    )
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(0.)
    assert block.algebraic_eqs[0].eval_uid(bindings) == pytest.approx(0.)
    bindings[block.state_vars[0].uid] = 4.5
    bindings[block.algebraic_vars[0].uid] = .3 * (4.5 - 2.0) ** 2 / 4.5
    bindings[block.algebraic_vars[1].uid] = 0.0
    bindings[block.in_vars[0].uid] = 10.0
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(0.)


def test_ac9c_rotating_exciter_stays_finite_at_zero_field_voltage() -> None:
    """Keep the rectifier FEX equation finite at the permitted zero lower stop."""
    block: Block = build_ac9c_rotating_exciter_template(
        vf=VarFactory(), settings=Ac9cRotatingExciterSettings(
            kc=.2, kd=.1, ke=1., te=.5, vfemax=5., vemin=0.,
            efe0=1.1, ifd0=1., ve0=1.,
        ),
    ).block
    bindings: dict[int, float] = make_exciter_bindings(
        block, efe=1.1, ifd=1., ve=0., vfe=.1, efd=0., saturation=0.,
    )
    assert math.isfinite(block.state_eqs[0].eval_uid(bindings))
    assert block.algebraic_eqs[2].eval_uid(bindings) == pytest.approx(0.)


def test_ac9c_rotating_exciter_rejects_invalid_saturation_and_initial_balance() -> None:
    """Reject degenerate saturation samples and non-equilibrium EFE seeds.

    :return: None.
    """
    with pytest.raises(ValueError, match='do not define a finite curve'):
        build_ac9c_rotating_exciter_template(
            vf=VarFactory(), settings=Ac9cRotatingExciterSettings(
                e1=3., se1=.1, e2=4., se2=.075,
            ),
        )
    with pytest.raises(ValueError, match='EFE must balance'):
        build_ac9c_rotating_exciter_template(
            vf=VarFactory(), settings=Ac9cRotatingExciterSettings(efe0=2.),
        )
    with pytest.raises(ValueError, match='field limits'):
        build_ac9c_rotating_exciter_template(
            vf=VarFactory(), settings=Ac9cRotatingExciterSettings(ve0=0.),
        )
