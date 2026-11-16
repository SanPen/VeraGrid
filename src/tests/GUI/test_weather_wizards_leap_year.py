# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from datetime import datetime, timedelta
import pandas as pd
from VeraGrid.Gui.DeviceEditors.GeneratorEditor.WindPowerWizard.wind_power_wizzard import (
    build_mapped_wind_time_index,
)
from VeraGrid.Gui.DeviceEditors.LoadDesigner.load_designer import (
    build_mapped_load_weather_time_index,
)
from VeraGrid.Gui.profile_wizard_utils import (
    build_mapped_time_index,
    get_longitude_time_offset,
    remap_timestamp_to_base_year,
)


def test_remap_timestamp_to_base_year_clamp_feb29() -> None:
    """
    Test that remapping February 29 from a leap year to a non-leap year clamps to February 28.
    """
    ts_leap: datetime = datetime(year=2024, month=2, day=29, hour=14, minute=30, second=15, microsecond=500)
    remapped: datetime = remap_timestamp_to_base_year(ts=ts_leap, base_year=2025)

    assert remapped.year == 2025
    assert remapped.month == 2
    assert remapped.day == 28
    assert remapped.hour == 14
    assert remapped.minute == 30
    assert remapped.second == 15
    assert remapped.microsecond == 500


def test_remap_timestamp_to_base_year_preserve_feb29() -> None:
    """
    Test that remapping February 29 from a leap year to another leap year preserves February 29.
    """
    ts_leap: datetime = datetime(year=2024, month=2, day=29, hour=18, minute=45, second=0)
    remapped: datetime = remap_timestamp_to_base_year(ts=ts_leap, base_year=2020)

    assert remapped.year == 2020
    assert remapped.month == 2
    assert remapped.day == 29
    assert remapped.hour == 18
    assert remapped.minute == 45
    assert remapped.second == 0


def test_remap_timestamp_to_base_year_with_start_year() -> None:
    """
    Test that remapping with a multi-year profile start_year correctly computes the target year.
    """
    ts_multi: datetime = datetime(year=2026, month=5, day=10, hour=12, minute=0, second=0)
    remapped: datetime = remap_timestamp_to_base_year(ts=ts_multi, base_year=2010, start_year=2024)

    # 2010 + (2026 - 2024) = 2012
    assert remapped.year == 2012
    assert remapped.month == 5
    assert remapped.day == 10
    assert remapped.hour == 12


def test_build_mapped_time_index_empty() -> None:
    """
    Test that building a mapped time index on an empty index returns an empty DatetimeIndex without error.
    """
    empty_index: pd.DatetimeIndex = pd.DatetimeIndex(list())
    mapped: pd.DatetimeIndex = build_mapped_time_index(time_index=empty_index, base_year=2020)

    assert len(mapped) == 0


def test_wind_power_wizard_leap_year_mapping() -> None:
    """
    Mapping leap year timestamps onto non-leap years must not raise ValueError.
    """
    t_leap: pd.DatetimeIndex = pd.date_range(
        start="2024-02-28 20:00:00",
        end="2024-03-01 04:00:00",
        freq="h",
    )
    assert any(ts.day == 29 for ts in t_leap)

    # Map onto a non-leap year (2025)
    mapped_index: pd.DatetimeIndex = build_mapped_wind_time_index(
        time_index=t_leap,
        base_year=2025,
    )

    assert len(mapped_index) == len(t_leap)
    assert all(ts.year == 2025 for ts in mapped_index)

    # Verify Feb 29 was clamped to Feb 28
    feb_days: set[int] = {ts.day for ts in mapped_index if ts.month == 2}
    assert 29 not in feb_days
    assert 28 in feb_days


def test_wind_power_wizard_leap_to_leap_mapping() -> None:
    """
    Mapping leap year timestamps onto another leap year must preserve Feb 29.
    """
    t_leap: pd.DatetimeIndex = pd.date_range(
        start="2024-02-28 20:00:00",
        end="2024-03-01 04:00:00",
        freq="h",
    )

    # 2020 is also a leap year
    mapped_index: pd.DatetimeIndex = build_mapped_wind_time_index(
        time_index=t_leap,
        base_year=2020,
    )

    assert len(mapped_index) == len(t_leap)
    assert all(ts.year == 2020 for ts in mapped_index)
    feb_days: set[int] = {ts.day for ts in mapped_index if ts.month == 2}
    assert 29 in feb_days


def test_load_designer_wizard_mapping_equivalence() -> None:
    """
    Verify that build_mapped_load_weather_time_index delegates correctly to build_mapped_time_index.
    """
    t_leap: pd.DatetimeIndex = pd.date_range(
        start="2024-02-28 20:00:00",
        end="2024-03-01 04:00:00",
        freq="h",
    )

    load_mapped: pd.DatetimeIndex = build_mapped_load_weather_time_index(
        time_index=t_leap,
        base_year=2025,
    )
    direct_mapped: pd.DatetimeIndex = build_mapped_time_index(
        time_index=t_leap,
        base_year=2025,
    )

    assert len(load_mapped) == len(direct_mapped)
    assert (load_mapped == direct_mapped).all()


def test_get_longitude_time_offset() -> None:
    """
    Test solar time offset calculation from site longitude.
    """
    offset_zero: timedelta = get_longitude_time_offset(longitude=0.0)
    assert offset_zero == timedelta(hours=0.0)

    offset_east: timedelta = get_longitude_time_offset(longitude=15.0)
    assert offset_east == timedelta(hours=1.0)

    offset_west: timedelta = get_longitude_time_offset(longitude=-30.0)
    assert offset_west == timedelta(hours=-2.0)

