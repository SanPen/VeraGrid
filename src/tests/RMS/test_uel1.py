# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Source-equation and topology checks for the IEEE 421.5 UEL1 limiter."""
from __future__ import annotations

import math

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Templates.Rms.excitation_limiters.uel1 import (
    Uel1Settings, build_uel1_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const


def evaluate_uel1_algebraics(
        block: Block,
        inputs: tuple[float, ...],
) -> dict[int, float]:
    """Evaluate one feed-forward UEL1 operating point.

    :param block: Native UEL1 block.
    :param inputs: Port values in declared input order.
    :return: Symbol UID bindings including solved algebraic values.
    """
    bindings: dict[int, float] = dict()
    for parameter, expression in block.event_dict.items():
        assert isinstance(expression, Const)
        bindings[parameter.uid] = float(expression.value)
    for port, value in zip(block.in_vars, inputs):
        bindings[port.uid] = value
    for state in block.state_vars:
        bindings[state.uid] = 0.0
    for variable, equation in zip(block.algebraic_vars, block.algebraic_eqs):
        bindings[variable.uid] = equation.right.eval_uid(bindings)
    return bindings


def test_uel1_uses_phasor_magnitudes_and_documented_state_order() -> None:
    """Evaluate the UEL1 phasor boundary and exact zero-time cascade."""
    settings: Uel1Settings = Uel1Settings(
        kur=.5, kuc=1., kuf=1., vurmax=5., vucmax=5., kui=.3, kul=2.,
        vuimax=4., vuimin=-4., tu1=0., tu2=0., tu3=0., tu4=0.,
        vulmax=5., vulmin=-5.,
    )
    template: RmsModelTemplate = build_uel1_template(VarFactory(), 'UEL1_TEST', settings)
    block: Block = template.block
    bindings: dict[int, float] = evaluate_uel1_algebraics(
        block, (1.02,.03,.3,-.4,.1,.15),
    )
    center: float = math.hypot(.62,-.27)
    radius: float = .25
    error: float = center-radius-.1
    expected: float = .15+2.*error

    assert len(block.in_vars) == 6
    assert len(block.state_vars) == 1
    assert [variable.name for variable in block.out_vars] == ['VUELPu_UEL1_TEST']
    assert bindings[block.out_vars[0].uid] == pytest.approx(expected)
    assert all(equation.eval_uid(bindings) == pytest.approx(0.)
               for equation in block.algebraic_eqs)


def test_uel1_capability_error_is_invariant_to_phasor_rotation() -> None:
    """A common terminal-frame rotation leaves UEL1's magnitudes unchanged."""
    template: RmsModelTemplate = build_uel1_template(
        VarFactory(), 'UEL1_ROTATION',
        Uel1Settings(kur=.7,kuc=1.2,kuf=.4,tu1=0.,tu2=0.,tu3=0.,tu4=0.),
    )
    angle: float = .61
    cosine: float = math.cos(angle)
    sine: float = math.sin(angle)
    voltage: complex = 1.01+.08j
    current: complex = .27-.16j
    rotated_voltage: complex = voltage*complex(cosine,sine)
    rotated_current: complex = current*complex(cosine,sine)
    original: dict[int,float] = evaluate_uel1_algebraics(
        template.block,
        (voltage.real,voltage.imag,current.real,current.imag,.2,0.),
    )
    rotated: dict[int,float] = evaluate_uel1_algebraics(
        template.block,
        (rotated_voltage.real,rotated_voltage.imag,
         rotated_current.real,rotated_current.imag,.2,0.),
    )
    error_index: int = 2
    assert original[template.block.algebraic_vars[error_index].uid] == pytest.approx(
        rotated[template.block.algebraic_vars[error_index].uid],
    )


@pytest.mark.parametrize(
    'settings',
    (
        Uel1Settings(tu1=1.,tu2=0.),
        Uel1Settings(vulmin=1.,vulmax=1.),
        Uel1Settings(vuimin=2.,vuimax=1.),
    ),
)
def test_uel1_rejects_improper_lead_lags_and_unordered_limits(
        settings: Uel1Settings,
) -> None:
    """Reject invalid source topology and output capabilities."""
    with pytest.raises(ValueError):
        build_uel1_template(VarFactory(), settings=settings)
