# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Physical signs, bases and reference rotation at the native VSC boundary."""
import math

import pytest

from VeraGridEngine.IO.dgs.dynamic_models.dgs_adapter_block_from_native_dgs import (
    build_dgs_elmvsc_two_level_block,
)
from VeraGridEngine.IO.dgs.dynamic_models.dgs_vsc_interfaces import add_native_vsc_dq_interface


@pytest.mark.parametrize('angle', [0., math.pi / 2., -.7])
@pytest.mark.parametrize('power', [.4, -.4])
def test_native_dq_current_observers_and_modulation_rotation(angle, power):
    block = build_dgs_elmvsc_two_level_block(100., 50., 220., 320., 320., .01, .1)
    original_equations = len(block.algebraic_eqs)
    block = add_native_vsc_dq_interface(block, 100., 50.)
    variables = {v.name: v for v in block.in_vars + block.algebraic_vars + block.out_vars}
    cosine, sine = math.cos(angle), math.sin(angle)
    # Terminal power is load-oriented on system base. Native dq currents are
    # generator-oriented on the equipment base, referenced to terminal voltage.
    assignments = {'Vm': 1., 'Va': angle, 'Pac': power, 'Qac': .2,
                   'cosref': cosine, 'sinref': sine, 'Pmd': .8, 'Pmq': -.1,
                   'Pmr': .8*cosine + .1*sine, 'Pmi': .8*sine - .1*cosine,
                   'id': -2.*power/(1.+1e-9), 'iq': .4/(1.+1e-9)}
    values = {variables[name].uid: value for name, value in assignments.items()}
    assert all(abs(eq.eval_uid(values)) < 1e-12
               for eq in block.algebraic_eqs[original_equations:])
    assert {'Pmd', 'Pmq', 'cosref', 'sinref'} <= {v.name for v in block.in_vars}
    assert not {'Pmr', 'Pmi'} & {v.name for v in block.in_vars}
    assert len(block.algebraic_vars) == len(block.algebraic_eqs)
    assert len({v.uid for v in block.algebraic_vars}) == len(block.algebraic_vars)
