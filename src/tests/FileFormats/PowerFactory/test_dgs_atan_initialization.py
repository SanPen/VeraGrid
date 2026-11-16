# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Preserve PowerFactory's one-argument atan in initialization equations."""

import math

import pytest

from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
from VeraGridEngine.IO.dgs.dgs_objects import BlkDef
from VeraGridEngine.IO.dgs.dgs_to_blocks import (
    ParsedDgsBlockDefinition, parse_dgs_block_definitions_from_circuit,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Expr


@pytest.mark.parametrize(('alpha', 'beta'), ((2.0, 1.0), (-2.0, 1.0), (2.0, -1.0), (-2.0, -1.0), (1.0, 0.0)))
def test_atan_initialization_preserves_ratio_and_principal_angle(alpha: float, beta: float) -> None:
    """Parse and evaluate the exported PLL initialization without atan2 substitution.

    :param alpha: Nonzero denominator, including negative values to distinguish quadrants.
    :param beta: Numerator of the exported ratio.
    :return: None.
    """
    definition: BlkDef = BlkDef()
    definition.ID = 'pll'
    definition.loc_name = 'PLL'
    definition.inputs = list(('alpha', 'beta'))
    definition.states = list(('x1',))
    definition.equations_raw = list(('inc(x1)=atan(beta/alpha)',))
    circuit: DgsCircuit = DgsCircuit()
    circuit.blkdefs.append(definition)
    parsed: ParsedDgsBlockDefinition = parse_dgs_block_definitions_from_circuit(circuit)['pll']
    assert parsed.unsupported_lines == list()
    expression: Expr = parsed.init_rhs['x1']
    bindings: dict[int, float] = dict((
        (parsed.symbol_table['alpha'].uid, alpha),
        (parsed.symbol_table['beta'].uid, beta),
    ))
    assert expression.eval_uid(bindings) == pytest.approx(math.atan(beta / alpha))
