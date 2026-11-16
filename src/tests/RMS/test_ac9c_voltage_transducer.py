# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Check the AC9C compensated-voltage transducer reductions."""

import math

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_voltage_transducer import (
    build_ac9c_voltage_transducer_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def make_transducer_bindings(block: Block, ecomp: float, sensed_voltage: float) -> dict[int, float]:
    """Bind transducer parameters, input and state for equation checks.

    :param block: Native AC9C transducer block.
    :param ecomp: Compensated terminal voltage input.
    :param sensed_voltage: Filter state or algebraic output value.
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
    bindings[block.in_vars[0].uid] = ecomp
    if len(block.state_vars) > 0:
        bindings[block.state_vars[0].uid] = sensed_voltage
    else:
        bindings[block.algebraic_vars[0].uid] = sensed_voltage
    return bindings


def test_ac9c_voltage_transducer_has_source_first_order_state() -> None:
    """Retain the 1/(1+s*TR) memory when TR is positive.

    :return: None.
    """
    block: Block = build_ac9c_voltage_transducer_template(
        vf=VarFactory(), tr=0.2, ecomp0=1.0,
    ).block
    bindings: dict[int, float] = make_transducer_bindings(block, 1.4, 1.1)
    assert len(block.state_vars) == 1
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(1.5)


def test_ac9c_voltage_transducer_zero_time_is_algebraic() -> None:
    """Reduce a zero transducer time constant directly to ECOMP.

    :return: None.
    """
    block: Block = build_ac9c_voltage_transducer_template(
        vf=VarFactory(), tr=0.0, ecomp0=1.0,
    ).block
    bindings: dict[int, float] = make_transducer_bindings(block, 1.2, 1.2)
    assert len(block.state_vars) == 0
    assert block.algebraic_eqs[0].eval_uid(bindings) == pytest.approx(0.0)


@pytest.mark.parametrize('tr,ecomp0', [(-0.1, 1.0), (math.inf, 1.0), (0.1, math.nan)])
def test_ac9c_voltage_transducer_rejects_invalid_settings(tr: float, ecomp0: float) -> None:
    """Reject nonfinite values and negative measurement time constants.

    :param tr: Candidate time constant.
    :param ecomp0: Candidate initial compensated voltage.
    :return: None.
    """
    with pytest.raises(ValueError, match='finite with TR nonnegative'):
        build_ac9c_voltage_transducer_template(vf=VarFactory(), tr=tr, ecomp0=ecomp0)
