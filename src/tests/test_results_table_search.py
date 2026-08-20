# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np

from VeraGridEngine.Simulations.results_table import ResultsTable
from VeraGridEngine.Utils.Filtering.results_table_filtering import FilterResultsTable
from VeraGridEngine.enumerations import DeviceType, ResultTablePlotType


def build_results_table() -> ResultsTable:
    """
    Build a mixed results table covering labels, text, and numeric values.

    :return: Results table used by the search tests.
    """
    data: np.ndarray = np.array(
        (
            ("Stable", 1.2345678),
            ("Critical", 349.9999784),
            ("Unstable", -12.0),
        ),
        dtype=object,
    )
    columns: np.ndarray = np.array(("Status", "Pf: Active power from"), dtype=str)
    index: np.ndarray = np.array(("bus alpha", "line 5-6-1", "generator gamma"), dtype=str)
    return ResultsTable(
        data=data,
        columns=columns,
        index=index,
        title="Search test",
        cols_device_type=DeviceType.NoDevice,
        idx_device_type=DeviceType.NoDevice,
        decimals=6,
    )


def apply_search(table: ResultsTable, expression: str) -> ResultsTable:
    """
    Apply the public results-table filtering workflow.

    :param table: Source results table.
    :param expression: Free-text query or advanced filter expression.
    :return: Filtered results table.
    """
    table_filter: FilterResultsTable = FilterResultsTable(table=table)
    table_filter.parse(expression=expression)
    return table_filter.apply()


def test_free_text_search_matches_row_labels_case_insensitively() -> None:
    """
    Verify a plain query selects matching result rows without filter syntax.

    :return: None.
    """
    filtered_table: ResultsTable = apply_search(table=build_results_table(), expression="LINE 5-6")

    assert filtered_table.data_c.shape == (1, 2)
    assert tuple(filtered_table.index_c.tolist()) == ("line 5-6-1",)


def test_free_text_search_matches_column_labels() -> None:
    """
    Verify a plain query selects matching result columns and retains all rows.

    :return: None.
    """
    filtered_table: ResultsTable = apply_search(table=build_results_table(), expression="active power")

    assert filtered_table.data_c.shape == (3, 1)
    assert tuple(filtered_table.cols_c.tolist()) == ("Pf: Active power from",)


def test_free_text_search_matches_displayed_numeric_values() -> None:
    """
    Verify numeric searches use the same rounded representation as the GUI.

    :return: None.
    """
    filtered_table: ResultsTable = apply_search(table=build_results_table(), expression="349.999978")

    assert filtered_table.data_c.shape == (1, 2)
    assert tuple(filtered_table.index_c.tolist()) == ("line 5-6-1",)


def test_free_text_search_matches_string_cell_contents() -> None:
    """
    Verify plain queries also inspect textual table contents.

    :return: None.
    """
    filtered_table: ResultsTable = apply_search(table=build_results_table(), expression="UNSTABLE")

    assert filtered_table.data_c.shape == (1, 2)
    assert tuple(filtered_table.index_c.tolist()) == ("generator gamma",)


def test_free_text_search_matches_displayed_complex_values() -> None:
    """
    Verify complex modal results are searchable using their displayed text.

    :return: None.
    """
    data: np.ndarray = np.array(((1.0 + 2.0j,),), dtype=complex)
    columns: np.ndarray = np.array(("Right eigenvector",), dtype=str)
    index: np.ndarray = np.array(("mode 1",), dtype=str)
    table: ResultsTable = ResultsTable(
        data=data,
        columns=columns,
        index=index,
        title="Complex search test",
        cols_device_type=DeviceType.NoDevice,
        idx_device_type=DeviceType.NoDevice,
        decimals=6,
    )

    filtered_table: ResultsTable = apply_search(table=table, expression="1.000000+2.000000j")

    assert filtered_table.data_c.shape == (1, 1)


def test_empty_search_restores_the_complete_table() -> None:
    """
    Verify clearing the search expression returns the source table unchanged.

    :return: None.
    """
    table: ResultsTable = build_results_table()
    filtered_table: ResultsTable = apply_search(table=table, expression="")

    assert filtered_table is table


def test_free_text_search_without_matches_returns_an_empty_table() -> None:
    """
    Verify an unmatched plain query communicates that no result was found.

    :return: None.
    """
    filtered_table: ResultsTable = apply_search(table=build_results_table(), expression="not present")

    assert filtered_table.data_c.shape == (0, 0)


def test_advanced_filter_syntax_remains_available() -> None:
    """
    Verify the existing structured filtering language still takes precedence.

    :return: None.
    """
    filtered_table: ResultsTable = apply_search(table=build_results_table(), expression="idx like gamma")

    assert filtered_table.data_c.shape == (1, 2)
    assert tuple(filtered_table.index_c.tolist()) == ("generator gamma",)


def test_numeric_filter_masks_values_that_do_not_match() -> None:
    """
    Verify a numeric threshold retains only cells satisfying the comparison.

    :return: None.
    """
    data: np.ndarray = np.array(((0.122, 0.200), (0.300, 0.110)), dtype=float)
    columns: np.ndarray = np.array(("Mode 0", "Mode 1"), dtype=str)
    index: np.ndarray = np.array(("delta1", "omega1"), dtype=str)
    table: ResultsTable = ResultsTable(
        data=data,
        columns=columns,
        index=index,
        title="Threshold test",
        cols_device_type=DeviceType.NoDevice,
        idx_device_type=DeviceType.NoDevice,
    )

    filtered_table: ResultsTable = apply_search(table=table, expression="val > 0.123")

    expected_data: np.ndarray = np.array(((np.nan, 0.200), (0.300, np.nan)), dtype=float)
    assert filtered_table.data_c.shape == (2, 2)
    assert np.allclose(filtered_table.data_c, expected_data, equal_nan=True)


def test_complex_point_filter_preserves_coordinate_pairs() -> None:
    """
    Verify a matching complex point retains both graphical coordinates.

    :return: None.
    """
    table: ResultsTable = ResultsTable(
        data=np.array(((-1.0, 2.0), (-2.0, -3.0)), dtype=float),
        columns=np.array(("Real", "Imaginary"), dtype=str),
        index=np.array(("Mode 0", "Mode 1"), dtype=str),
        title="Complex points",
        cols_device_type=DeviceType.NoDevice,
        idx_device_type=DeviceType.NoDevice,
        plot_type=ResultTablePlotType.COMPLEX_POINTS,
        damping_ratio_boundary=0.05,
        complex_plot_x_column="Real",
        complex_plot_y_columns=np.array(("Imaginary",), dtype=str),
        complex_plot_y_scales=np.array((1.0,), dtype=float),
    )

    filtered_table: ResultsTable = apply_search(table=table, expression="val > 0")
    column_search_table: ResultsTable = apply_search(table=table, expression="Real")
    structured_column_table: ResultsTable = apply_search(table=table, expression="col like Imaginary")

    assert filtered_table.plot_type == ResultTablePlotType.COMPLEX_POINTS
    assert filtered_table.damping_ratio_boundary == 0.05
    assert filtered_table.complex_plot_x_column == "Real"
    assert tuple(filtered_table.index_c.tolist()) == ("Mode 0",)
    assert np.array_equal(filtered_table.data_c, np.array(((-1.0, 2.0),), dtype=float))
    assert tuple(column_search_table.cols_c.tolist()) == ("Real",)
    assert tuple(structured_column_table.cols_c.tolist()) == ("Imaginary",)


def test_numeric_range_conditions_apply_to_the_same_cell() -> None:
    """
    Verify range bounds cannot be satisfied by two different table cells.

    :return: None.
    """
    data: np.ndarray = np.array(((5.0, 25.0), (15.0, 30.0)), dtype=float)
    columns: np.ndarray = np.array(("Mode 0", "Mode 1"), dtype=str)
    index: np.ndarray = np.array(("delta1", "omega1"), dtype=str)
    table: ResultsTable = ResultsTable(
        data=data,
        columns=columns,
        index=index,
        title="Range test",
        cols_device_type=DeviceType.NoDevice,
        idx_device_type=DeviceType.NoDevice,
    )

    filtered_table: ResultsTable = apply_search(
        table=table,
        expression="val >= 10 and val <= 20",
    )

    assert filtered_table.data_c.shape == (1, 1)
    assert filtered_table.data_c[0, 0] == 15.0


def test_first_results_search_tooltip_example() -> None:
    """
    Verify the composite column, value, and index example from the tooltip.

    The expression is ``col != [column1, column2] and val > 5 or idx like [ab, mn]``.

    :return: None.
    """
    data: np.ndarray = np.array(
        (
            (10.0, 20.0, 6.0),
            (1.0, 2.0, 3.0),
            (1.0, 2.0, 4.0),
            (7.0, 8.0, 1.0),
        ),
        dtype=float,
    )
    columns: np.ndarray = np.array(("column1", "column2", "column3"), dtype=str)
    index: np.ndarray = np.array(("regular", "ab row", "other", "mn row"), dtype=str)
    table: ResultsTable = ResultsTable(
        data=data,
        columns=columns,
        index=index,
        title="First tooltip example",
        cols_device_type=DeviceType.NoDevice,
        idx_device_type=DeviceType.NoDevice,
    )

    filtered_table: ResultsTable = apply_search(
        table=table,
        expression="col != [column1, column2] and val > 5 or idx like [ab, mn]",
    )

    expected_data: np.ndarray = np.array(
        (
            (np.nan, np.nan, 6.0),
            (1.0, 2.0, 3.0),
            (7.0, 8.0, 1.0),
        ),
        dtype=float,
    )
    assert tuple(filtered_table.index_c.tolist()) == ("regular", "ab row", "mn row")
    assert tuple(filtered_table.cols_c.tolist()) == ("column1", "column2", "column3")
    assert np.allclose(filtered_table.data_c, expected_data, equal_nan=True)


def test_second_results_search_tooltip_example() -> None:
    """
    Verify the exclusive numeric range example from the results tooltip.

    The expression is ``val > 0.5 and val < 20.0``.

    :return: None.
    """
    data: np.ndarray = np.array(
        (
            (0.5, 0.500001),
            (19.999999, 20.0),
            (25.0, 10.0),
        ),
        dtype=float,
    )
    columns: np.ndarray = np.array(("column1", "column2"), dtype=str)
    index: np.ndarray = np.array(("lower bound", "upper bound", "mixed"), dtype=str)
    table: ResultsTable = ResultsTable(
        data=data,
        columns=columns,
        index=index,
        title="Second tooltip example",
        cols_device_type=DeviceType.NoDevice,
        idx_device_type=DeviceType.NoDevice,
    )

    filtered_table: ResultsTable = apply_search(
        table=table,
        expression="val > 0.5 and val < 20.0",
    )

    expected_data: np.ndarray = np.array(
        (
            (np.nan, 0.500001),
            (19.999999, np.nan),
            (np.nan, 10.0),
        ),
        dtype=float,
    )
    assert np.allclose(filtered_table.data_c, expected_data, equal_nan=True)
