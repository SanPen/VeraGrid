# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
import VeraGridEngine as vg


def test_find_different_states():
    mat = np.array([
        [1, 0, 1],
        [1, 0, 1],
        [0, 1, 0],
        [1, 0, 1],
        [0, 1, 0],
    ])

    groups, mapping = vg.find_different_states(mat)

    expected_mapping = np.array([0, 0, 2, 0, 2], dtype=int)

    assert np.allclose(mapping, expected_mapping)


def grouping_helper(n_rows=1000, n_cols=10, seed=None):
    """
    Helper function to test the find different states
    :param n_rows:
    :param n_cols:
    :param seed:
    :return:
    """
    rng = np.random.default_rng(seed)
    mat = rng.integers(0, 2, size=(n_rows, n_cols), dtype=np.uint8)

    groups, mapping = vg.find_different_states(mat)

    # --- Assertions ---
    # 1. All rows covered
    all_rows_from_groups = sorted([r for g in groups.values() for r in g])
    assert all_rows_from_groups == list(range(n_rows)), "Not all rows are covered!"

    # 2. Representative consistency
    for rep, rows in groups.items():
        for r in rows:
            assert np.array_equal(mat[rep], mat[r]), f"Row {r} doesn't match representative {rep}"

    # 3. Mapping consistency
    for r in range(n_rows):
        rep = mapping[r]
        assert r in groups[rep], f"Mapping mismatch at row {r}"

    print(f"Test passed ✅ (rows={n_rows}, cols={n_cols}, groups={len(groups)})")


def test_find_different_states_random():
    # Run multiple random tests
    for n in [100, 1000, 5000]:
        grouping_helper(n_rows=2 * n, n_cols=n, seed=42)
