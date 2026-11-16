# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Preserve native lookup payload before implementing interpolation semantics."""
import hashlib
import json
from pathlib import Path

import pytest

from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
from VeraGridEngine.IO.dgs.dgs_objects import ElmDsl
from VeraGridEngine.IO.dgs.dgs_to_blocks import get_elmdsl_lookup_tables

DATA = Path(__file__).resolve().parents[2] / 'data/grids/DGS/native_lookup_pf2024'
MANIFEST = json.loads((DATA / 'manifest.json').read_text())


@pytest.mark.parametrize('record', MANIFEST['files'], ids=lambda record: record['file'])
def test_lookup_native_exports_are_intact_and_payload_is_retained(record):
    path = DATA / record['file']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256']
    assert record['code'] == 0 and not record['errors'] and not record['warnings']
    circuit = DgsCircuit()
    circuit.parse_dgs(str(path))
    if record['class'] == 'ElmGenstat':
        pq = next(obj for obj in circuit.elmdsls if obj.loc_name == 'PQ_ctrl')
        assert pq.matrix == [[2., 2., 2., 2.], [0., 0., 0., 0.], [1., 1., 1., 1.]]
        signals = next(obj for obj in circuit.elmdsls if obj.loc_name == 'Señales')
        assert len(signals.matrix) == 9 and len(signals.matrix[0]) == 6
        assert signals.matrix[0] == [7., 7., 4., 4., 8., 8.]
    else:
        control = next(obj for obj in circuit.elmdsls if obj.loc_name == 'Control')
        assert len(control.matrix) == 24
        assert control.matrix[:2] == [[23., 0.], [0., 1.1]]
        turbine = next(obj for obj in circuit.elmdsls if obj.loc_name == 'Turbine')
        assert len(turbine.matrix2) == 67
        assert len(turbine.matrix2[0]) == 49
        assert turbine.matrix2[0][:2] == [66., 49.]
        assert turbine.matrix2[1][:4] == [0., .8, 1.2, 1.6]


def test_matrix_dimensions_exclude_padding_and_legacy_files_remain_empty():
    obj = ElmDsl.parse_line('1;1;2;3;4;discard', {
        'FID': 0, 'matrix:SIZEROW': 1, 'matrix:SIZECOL': 2,
        'matrix:0:0': 3, 'matrix:0:1': 4, 'matrix:1:0': 5})
    assert obj.matrix == [[3., 4.]]
    assert obj.matrix2 == []
    legacy = ElmDsl.parse_line('1', {'FID': 0})
    assert legacy.matrix == legacy.matrix2 == []


@pytest.mark.parametrize('line,expected', [('1;1;1;*', [[None]]), ('1;1;1;bad', [[None]]),
                                           ('1;-1;1;2', []), ('1;1000000;1;2', [])])
def test_invalid_lookup_matrix_is_not_silently_replaced_with_zeros(line, expected):
    """A malformed cell is unknown and malformed sizes read as empty, never as zeros.

    The characteristic using it is then left out, so only its root fails closed.
    """
    obj = ElmDsl.parse_line(line, {'FID': 0, 'matrix:SIZEROW': 1, 'matrix:SIZECOL': 2, 'matrix:0:0': 3})
    assert obj.matrix == expected


def test_native_array_names_resolve_to_their_instance_columns():
    circuit = DgsCircuit()
    circuit.parse_dgs(str(DATA / 'genstat_lookup_tables.dgs'))
    types = {obj.ID: obj for obj in circuit.blkdefs}
    source = next(obj for obj in circuit.elmdsls if obj.loc_name == 'PQ_ctrl')
    tables = get_elmdsl_lookup_tables(source, types[source.typ_id], circuit.intmats)
    assert {name: (table.x_points, table.y_points) for name, table in tables.items()} == {
        'array_PFP': ((0., 1.), (0., 1.)), 'array_QU': ((0., 1.), (0., 1.))}
    protection = next(obj for obj in circuit.elmdsls if obj.loc_name == 'prot')
    tables = get_elmdsl_lookup_tables(protection, types[protection.typ_id], circuit.intmats)
    # Declaration order: the HVRT pair (never trips high) precedes the LVRT pair (never trips low).
    assert set(tables['array_HVRT'].y_points) == {10000.}
    assert set(tables['array_LVRT'].y_points) == {0.}
    signal = next(obj for obj in circuit.elmdsls if obj.loc_name == 'Señales')
    tables = get_elmdsl_lookup_tables(signal, types[signal.typ_id], circuit.intmats)
    # Repeated native times are not sorted or deduplicated silently: those curves are left out.
    assert {name: len(table.x_points) for name, table in tables.items()} == {'array_u3_t': 8}
