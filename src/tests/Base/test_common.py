# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import numpy as np
import pytest
from VeraGridEngine.Utils.NumericalMethods.common import find_closest_number
from VeraGridEngine.Simulations.OPF.NumericalMethods.newton_raphson_ips_fx import max_abs


def test_find_closest_number():
    arr = np.arange(1, 10, 0.1)
    # print(arr)

    """
    0	1
    1	1,1
    2	1,2
    3	1,3
    4	1,4
    5	1,5
    6	1,6
    7	1,7
    8	1,8
    9	1,9
    10	2
    11	2,1
    12	2,2
    13	2,3
    14	2,4
    15	2,5
    16	2,6
    17	2,7
    18	2,8
    19	2,9
    20	3
    21	3,1
    22	3,2
    23	3,3
    24	3,4
    25	3,5
    26	3,6
    27	3,7
    28	3,8
    29	3,9
    30	4
    31	4,1
    32	4,2
    33	4,3
    34	4,4
    35	4,5
    36	4,6
    37	4,7
    38	4,8
    39	4,9
    40	5
    41	5,1
    42	5,2
    43	5,3
    44	5,4
    45	5,5
    46	5,6
    47	5,7
    48	5,8
    49	5,9
    50	6
    51	6,1
    52	6,2
    53	6,3
    54	6,4
    55	6,5
    56	6,6
    57	6,7
    58	6,8
    59	6,9
    60	7
    61	7,1
    62	7,2
    63	7,3
    64	7,4
    65	7,5
    66	7,6
    67	7,7
    68	7,8
    69	7,9
    70	8
    71	8,1
    72	8,2
    73	8,3
    74	8,4
    75	8,5
    76	8,6
    77	8,7
    78	8,8
    79	8,9
    80	9
    81	9,1
    82	9,2
    83	9,3
    84	9,4
    85	9,5
    86	9,6
    87	9,7
    88	9,8
    89	9,9
    90	10
    """

    # test upper outside bounds
    target = 11
    idx, val = find_closest_number(arr, target)

    assert idx == len(arr) - 1
    assert val == arr[len(arr) - 1]

    # test lower outside bounds
    target = 0.3
    idx, val = find_closest_number(arr, target)

    assert idx == 0
    assert val == arr[0]

    # test some middle points
    target = 3.95
    idx, val = find_closest_number(arr, target)

    assert idx == 30
    assert val == arr[30]

    target = 3.91
    idx, val = find_closest_number(arr, target)

    assert idx == 29
    assert val == arr[29]


def test_opf_max_abs_uses_absolute_value():
    x = np.array([-5.0, 3.0, -4.0])

    assert max_abs(x) == 5.0


def test_find_closest_number_in_a_falling_array() -> None:
    """
    A falling array gives the value of its rising mirror, at the mirrored index
    :return:
    """
    rising: np.ndarray = np.linspace(0.9, 1.1, 21)
    falling: np.ndarray = rising[::-1].copy()
    midpoints: np.ndarray = (rising[:-1] + rising[1:]) / 2.0
    targets: np.ndarray = np.linspace(0.85, 1.15, 301)
    for target in targets[np.abs(targets[:, None] - midpoints).min(axis=1) > 1e-9]:
        rising_index, rising_value = find_closest_number(rising, target)
        falling_index, falling_value = find_closest_number(falling, target)
        assert falling_value == rising_value
        assert falling_index == len(rising) - 1 - rising_index


def test_find_closest_number_lands_as_close_at_the_midpoint_of_a_falling_array() -> None:
    """
    A midpoint has two closest values, so a falling array may land on either
    :return:
    """
    rising: np.ndarray = np.linspace(0.9, 1.1, 21)
    falling: np.ndarray = rising[::-1].copy()
    for target in (rising[:-1] + rising[1:]) / 2.0:
        _, rising_value = find_closest_number(rising, target)
        _, falling_value = find_closest_number(falling, target)
        assert abs(falling_value - target) == pytest.approx(abs(rising_value - target))


def test_find_closest_number_keeps_the_rising_search_on_equal_ends() -> None:
    """
    Only a first value above the last one means a falling table
    :return:
    """
    index, value = find_closest_number(np.array([1.0, 1.1, 1.0]), 1.05)
    assert (index, value) == (2, 1.0)


def test_find_closest_number_takes_any_falling_table() -> None:
    """
    A table that falls from first to last gives the closest value even with steps out of order
    :return:
    """
    index, value = find_closest_number(np.array([1.1, 0.9, 1.0, 0.8]), 0.98)
    assert (index, value) == (2, 1.0)


def test_find_closest_number_still_rejects_a_disordered_rising_array() -> None:
    """
    An array that ends above its start keeps the check of the rising search
    :return:
    """
    with pytest.raises(Exception, match="monotonically increasing"):
        find_closest_number(np.array([0.8, 1.0, 0.9, 1.1]), 1.05)
