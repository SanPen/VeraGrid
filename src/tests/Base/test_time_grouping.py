# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import pandas as pd

from VeraGridEngine.basic_structures import (
    classify_by_day,
    classify_by_hour,
    get_time_groups,
)
from VeraGridEngine.enumerations import TimeGrouping


def materialize_groups(timestamps: pd.DatetimeIndex, grouping: TimeGrouping) -> list[list[int]]:
    """
    Convert VeraGrid's delimiter list into explicit index groups for assertions.
    """
    groups = get_time_groups(t_array=timestamps, grouping=grouping)
    materialized: list[list[int]] = list()

    for i in range(1, len(groups)):
        start_index = groups[i - 1]
        end_index = groups[i]
        if i == len(groups) - 1:
            materialized.append([int(v) for v in range(start_index, end_index + 1)])
        else:
            materialized.append([int(v) for v in range(start_index, end_index)])

    return materialized


def test_no_grouping_keeps_all_timestamps_together() -> None:
    """
    No grouping must preserve the whole selection as a single chunk.
    """
    timestamps = pd.DatetimeIndex([
        "2026-01-01 00:00:00",
        "2026-02-01 00:00:00",
        "2026-02-01 12:00:00",
        "2026-02-02 00:00:00",
    ])

    groups = materialize_groups(timestamps=timestamps, grouping=TimeGrouping.NoGrouping)

    assert groups == [[0, 1, 2, 3]]


def test_hourly_grouping_uses_calendar_hour_boundaries() -> None:
    """
    Hourly grouping must split on full calendar hours, not only on the hour number.
    """
    timestamps = pd.DatetimeIndex([
        "2026-01-01 00:00:00",
        "2026-02-01 00:00:00",
        "2026-02-01 12:00:00",
        "2026-02-02 00:00:00",
    ])

    groups = materialize_groups(timestamps=timestamps, grouping=TimeGrouping.Hourly)

    assert groups == [[0], [1], [2], [3]]


def test_daily_grouping_uses_calendar_day_boundaries() -> None:
    """
    Daily grouping must split when the calendar date changes, even if the
    day-of-month number repeats across months.
    """
    timestamps = pd.DatetimeIndex([
        "2026-01-01 00:00:00",
        "2026-02-01 00:00:00",
        "2026-02-01 12:00:00",
        "2026-02-02 00:00:00",
    ])

    groups = materialize_groups(timestamps=timestamps, grouping=TimeGrouping.Daily)

    assert groups == [[0], [1, 2], [3]]


def test_weekly_grouping_uses_year_aware_week_boundaries() -> None:
    """
    Weekly grouping must split on year-aware ISO week boundaries.
    """
    timestamps = pd.DatetimeIndex([
        "2025-01-01 00:00:00",
        "2025-01-02 00:00:00",
        "2025-01-08 00:00:00",
        "2026-01-01 00:00:00",
    ])

    groups = materialize_groups(timestamps=timestamps, grouping=TimeGrouping.Weekly)

    assert groups == [[0, 1], [2], [3]]


def test_monthly_grouping_uses_year_aware_month_boundaries() -> None:
    """
    Monthly grouping must split on year-aware month boundaries.
    """
    timestamps = pd.DatetimeIndex([
        "2025-01-31 00:00:00",
        "2025-01-31 12:00:00",
        "2025-02-01 00:00:00",
        "2026-01-01 00:00:00",
    ])

    groups = materialize_groups(timestamps=timestamps, grouping=TimeGrouping.Monthly)

    assert groups == [[0, 1], [2], [3]]


def test_daily_grouping_splits_hourly_year_into_365_days() -> None:
    """
    Daily grouping over a full non-leap-year hourly profile must yield one
    group per calendar day.
    """
    timestamps = pd.date_range(start="2025-01-01 00:00:00", periods=8760, freq="h")

    groups = materialize_groups(timestamps=timestamps, grouping=TimeGrouping.Daily)

    assert len(groups) == 365
    assert groups[0] == [i for i in range(24)]
    assert groups[1] == [i for i in range(24, 48)]
    assert groups[-1] == [i for i in range(8736, 8760)]


def test_classify_by_hour_empty_index() -> None:
    """
    Classifying an empty index must safely return an empty list without IndexError.
    """
    timestamps: pd.DatetimeIndex = pd.DatetimeIndex([])
    result: list[list[int]] = classify_by_hour(t=timestamps)
    assert result == list()


def test_classify_by_hour_midnight_boundary() -> None:
    """
    Timeseries ending at midnight (hour 0) must not cause range inversion bugs.
    """
    # 25 timestamps spanning exactly 24 hours from 00:00 on day 1 to 00:00 on day 2
    timestamps: pd.DatetimeIndex = pd.date_range(
        start="2026-01-01 00:00:00",
        end="2026-01-02 00:00:00",
        freq="h",
    )
    result: list[list[int]] = classify_by_hour(t=timestamps)

    assert len(result) == 25
    expected_idx: int
    for expected_idx in range(25):
        assert result[expected_idx] == [expected_idx]


def test_classify_by_hour_spans_year_boundary() -> None:
    """
    Timeseries crossing year boundaries must maintain continuous hourly buckets.
    """
    timestamps: pd.DatetimeIndex = pd.date_range(
        start="2025-12-31 22:00:00",
        end="2026-01-01 02:00:00",
        freq="h",
    )
    result: list[list[int]] = classify_by_hour(t=timestamps)

    assert len(result) == 5
    assert result[0] == [0]  # 2025-12-31 22:00
    assert result[1] == [1]  # 2025-12-31 23:00
    assert result[2] == [2]  # 2026-01-01 00:00
    assert result[3] == [3]  # 2026-01-01 01:00
    assert result[4] == [4]  # 2026-01-01 02:00


def test_classify_by_hour_sub_hourly() -> None:
    """
    Sub-hourly timestamps must be grouped into their corresponding hour bucket.
    """
    timestamps: pd.DatetimeIndex = pd.date_range(
        start="2026-06-01 00:00:00",
        end="2026-06-01 01:45:00",
        freq="15min",
    )
    result: list[list[int]] = classify_by_hour(t=timestamps)

    assert len(result) == 2
    assert result[0] == [0, 1, 2, 3]  # 00:00, 00:15, 00:30, 00:45
    assert result[1] == [4, 5, 6, 7]  # 01:00, 01:15, 01:30, 01:45


def test_classify_by_day_empty_index() -> None:
    """
    Classifying an empty index by day must safely return an empty list without IndexError.
    """
    timestamps: pd.DatetimeIndex = pd.DatetimeIndex([])
    result: list[list[int]] = classify_by_day(t=timestamps)
    assert result == list()


def test_classify_by_day_single_day_hourly() -> None:
    """
    All hourly timestamps within a single calendar day must group into bucket 0.
    """
    timestamps: pd.DatetimeIndex = pd.date_range(
        start="2026-01-01 00:00:00",
        end="2026-01-01 23:00:00",
        freq="h",
    )
    result: list[list[int]] = classify_by_day(t=timestamps)

    assert len(result) == 1
    assert result[0] == list(range(24))


def test_classify_by_day_spans_year_boundary() -> None:
    """
    Timeseries crossing year boundaries must maintain continuous daily buckets without index inversion.
    """
    timestamps: pd.DatetimeIndex = pd.date_range(
        start="2025-12-30 00:00:00",
        end="2026-01-02 00:00:00",
        freq="D",
    )
    result: list[list[int]] = classify_by_day(t=timestamps)

    assert len(result) == 4
    assert result[0] == [0]  # 2025-12-30
    assert result[1] == [1]  # 2025-12-31
    assert result[2] == [2]  # 2026-01-01
    assert result[3] == [3]  # 2026-01-02


def test_classify_by_day_leap_year() -> None:
    """
    Timeseries traversing February 29 on leap years must partition each calendar day correctly.
    """
    timestamps: pd.DatetimeIndex = pd.date_range(
        start="2024-02-28 00:00:00",
        end="2024-03-01 00:00:00",
        freq="D",
    )
    result: list[list[int]] = classify_by_day(t=timestamps)

    assert len(result) == 3
    assert result[0] == [0]  # 2024-02-28
    assert result[1] == [1]  # 2024-02-29 (leap day)
    assert result[2] == [2]  # 2024-03-01


def test_classify_by_day_timezone_aware() -> None:
    """
    Timezone-aware timestamps across daylight saving boundaries must allocate calendar days accurately.
    """
    timestamps: pd.DatetimeIndex = pd.date_range(
        start="2026-03-28 12:00:00",
        end="2026-03-30 12:00:00",
        freq="6h",
        tz="Europe/Madrid",
    )
    result: list[list[int]] = classify_by_day(t=timestamps)

    assert len(result) == 3
    assert result[0] == [0, 1]        # 2026-03-28 12:00, 18:00
    assert result[1] == [2, 3, 4, 5]  # 2026-03-29 00:00, 07:00, 13:00, 19:00
    assert result[2] == [6, 7]        # 2026-03-30 01:00, 07:00



