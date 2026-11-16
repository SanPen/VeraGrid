# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import numpy as np
import pandas as pd
import pytest
from VeraGridEngine.Devices.Branches.tap_changer import TapChanger, TapChangerTypes


def test_tap_changer1():
    """
    Test the TapChanger 1
    :return:
    """
    tc = TapChanger(total_positions=13,
                    neutral_position=6,
                    dV=0.01,  # p.u.
                    asymmetry_angle=90,  # deg
                    tc_type=TapChangerTypes.VoltageRegulation)

    print(tc.to_df())

    tc.tap_position = 0
    a = tc.get_tap_phase()
    r = tc.get_tap_module()

    tc.tap_position = 3
    a = tc.get_tap_phase()
    r = tc.get_tap_module()

    tc.tap_position = -3
    a = tc.get_tap_phase()
    r = tc.get_tap_module()

    print()


def _build_inverted_tap_changer() -> tuple[TapChanger, np.ndarray]:
    """Build a changer whose exact table falls as the position rises.

    :return: Tap changer and its table.
    """
    table: np.ndarray = 1.0 - 0.01 * (np.arange(11) - 5)
    changer: TapChanger = TapChanger(total_positions=11, neutral_position=5, dV=0.01,
                                     tc_type=TapChangerTypes.VoltageRegulation)
    assert changer.set_tap_module_phase_values(tap_modules=table, tap_phases=np.zeros(11))
    return changer, table


def test_moving_the_tap_keeps_an_exact_table() -> None:
    """Stay on the installed table through every way of moving the tap.

    :return: None.
    """
    changer, table = _build_inverted_tap_changer()
    changer.tap_position = 7
    assert changer.get_tap_module() == table[7]
    changer.tap_up()
    assert changer.get_tap_module() == table[8]
    changer.tap_down()
    assert changer.get_tap_module() == table[7]
    assert changer.set_tap_module(tap_module=0.96) == pytest.approx(0.96)
    assert changer.tap_position == 9
    assert changer.uses_explicit_table
    assert np.array_equal(changer.tap_modules_array, table)


def test_changing_the_configuration_returns_to_the_generic_law() -> None:
    """Keep the documented contract: a configuration setter discards the exact table.

    :return: None.
    """
    changer, table = _build_inverted_tap_changer()
    changer.dV = 0.02
    assert not changer.uses_explicit_table
    assert not np.array_equal(changer.tap_modules_array, table)


def test_exact_table_survives_save_and_reload() -> None:
    """Reload the table and keep moving along it.

    :return: None.
    """
    changer, table = _build_inverted_tap_changer()
    changer.tap_position = 7
    loaded: TapChanger = TapChanger()
    loaded.parse(changer.to_dict())
    assert loaded.uses_explicit_table
    assert loaded.tap_position == 7
    loaded.tap_up()
    assert loaded.get_tap_module() == table[8]


@pytest.mark.parametrize("tc_type", [TapChangerTypes.VoltageRegulation, TapChangerTypes.Asymmetrical,
                                     TapChangerTypes.Symmetrical, TapChangerTypes.NoRegulation])
def test_moving_the_tap_leaves_a_generic_table_as_it_is(tc_type: TapChangerTypes) -> None:
    """Keep every generic law independent of the current position.

    :param tc_type: Tap changer type.
    :return: None.
    """
    changer: TapChanger = TapChanger(total_positions=9, neutral_position=4, dV=0.0125, asymmetry_angle=60.0, tc_type=tc_type)
    modules: np.ndarray = changer.tap_modules_array.copy()
    angles: np.ndarray = changer.tap_angles_array.copy()
    for position in range(9):
        changer.tap_position = position
        assert np.array_equal(changer.tap_modules_array, modules)
        assert np.array_equal(changer.tap_angles_array, angles)
        assert changer.get_tap_module() == modules[position]
