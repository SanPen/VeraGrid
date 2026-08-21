import pandas as pd

from VeraGridEngine.basic_structures import get_time_groups
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
