# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""REECA1 cascaded Q/V PI regulator checks."""

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.renewable_controls.reeca1_coordinated_qv import (
    Reeca1CoordinatedQvSettings,
    build_reeca1_coordinated_qv_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.renewable_partial_chain import build_renewable_partial_chain
from VeraGridEngine.Templates.Rms.renewable_controls.reeca1_constant_q import Reeca1ConstantQSettings
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def test_reeca1_coordinated_qv_cascades_and_freezes_both_pi_states() -> None:
    """Limit Q reference and Iq, and stop both memories during a voltage dip.

    :return: None.
    """
    block: Block = build_reeca1_coordinated_qv_template(vf=VarFactory()).block
    bindings: dict[int, float] = dict()
    parameter: Var
    value: Expr
    for parameter, value in block.event_dict.items():
        if isinstance(value, Const):
            bindings[parameter.uid] = float(value.value)
        else:
            pass
    bindings[block.in_vars[0].uid] = .4
    bindings[block.in_vars[1].uid] = .2
    bindings[block.in_vars[2].uid] = 1.
    bindings[block.in_vars[3].uid] = 0.
    bindings[block.in_vars[4].uid] = .5
    bindings[block.state_vars[0].uid] = .9
    bindings[block.state_vars[1].uid] = .1
    bindings[block.algebraic_vars[0].uid] = 1.1
    bindings[block.algebraic_vars[1].uid] = 0.
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(.2)
    assert block.state_eqs[1].eval_uid(bindings) == pytest.approx(.1)
    assert block.algebraic_eqs[0].eval_uid(bindings) == pytest.approx(0.)
    assert -block.algebraic_eqs[1].eval_uid(bindings) == pytest.approx(.2)
    bindings[block.in_vars[4].uid] = .15
    assert -block.algebraic_eqs[1].eval_uid(bindings) == pytest.approx(.15)
    bindings[block.in_vars[3].uid] = 1.
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(0.)
    assert block.state_eqs[1].eval_uid(bindings) == pytest.approx(0.)


def test_reeca1_coordinated_qv_rejects_invalid_mode_combinations() -> None:
    """Require fault feedback and exclusive QFLAG=1 path selection.

    :return: None.
    """
    with pytest.raises(ValueError, match='Q/V bounds'):
        build_reeca1_coordinated_qv_template(
            vf=VarFactory(), settings=Reeca1CoordinatedQvSettings(vmin=1.2, vmax=.8),
        )
    with pytest.raises(ValueError, match='requires voltage-fault settings'):
        build_renewable_partial_chain(
            vf=VarFactory(), coordinated_qv_settings=Reeca1CoordinatedQvSettings(),
        )
    with pytest.raises(ValueError, match='cannot be combined'):
        build_renewable_partial_chain(
            vf=VarFactory(), coordinated_qv_settings=Reeca1CoordinatedQvSettings(),
            reactive_power_settings=Reeca1ConstantQSettings(),
        )
