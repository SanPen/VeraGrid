# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Retain ideal external-grid boundaries only in the ABC compiled data."""
import numpy as np
import pytest

import VeraGridEngine.api as vge
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.enumerations import ExternalGridMode


@pytest.mark.parametrize('three_phase', (False, True))
def test_external_voltage_source_compilation_copy_and_slice(three_phase: bool) -> None:
    """Distinguish VD sources from loads/PV/PQ sources and preserve their island mapping.

    :param three_phase: Only ABC compilation allocates the source-origin vector.
    """
    grid = vge.MultiCircuit()
    first = grid.add_bus(vge.Bus(name='First', Vnom=20))
    second = grid.add_bus(vge.Bus(name='Second', Vnom=20))
    grid.add_line(vge.Line(bus_from=first, bus_to=second, r=0.01, x=0.1))
    grid.add_load(second, vge.Load(name='Ordinary load', P=3, Q=1))
    for name, mode, active in (('VD', ExternalGridMode.VD, True),
                               ('PV', ExternalGridMode.PV, True),
                               ('PQ', ExternalGridMode.PQ, True),
                               ('Offline VD', ExternalGridMode.VD, False)):
        grid.add_external_grid(first if name == 'VD' else second,
                               vge.ExternalGrid(name=name, mode=mode, active=active))
    data = compile_numerical_circuit_at(grid, fill_three_phase=three_phase).load_data
    by_name = {name: i for i, name in enumerate(data.names)}
    indices = np.array([by_name[name] for name in ('Offline VD', 'VD', 'Ordinary load')])
    copied = data.copy()
    sliced = data.slice(indices, np.array((1, 0)), np.array((1, 0)))
    np.testing.assert_array_equal(sliced.bus_idx, (0, 1, 0))
    if not three_phase:
        assert data.fixed_voltage is copied.fixed_voltage is sliced.fixed_voltage is None
        return
    assert {name: bool(data.fixed_voltage[i]) for name, i in by_name.items()} == {
        'Ordinary load': False, 'VD': True, 'PV': False, 'PQ': False, 'Offline VD': True}
    np.testing.assert_array_equal(copied.fixed_voltage, data.fixed_voltage)
    np.testing.assert_array_equal(sliced.fixed_voltage, (True, True, False))
    assert list(data.names[data.active & data.fixed_voltage]) == ['VD']
    copied.fixed_voltage[by_name['VD']] = False
    sliced.fixed_voltage[1] = False
    assert data.fixed_voltage[by_name['VD']]
