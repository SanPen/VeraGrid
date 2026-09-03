# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple, Any, List
import numpy as np
from VeraGridEngine.Simulations.results_table import ResultsTable
from VeraGridEngine.basic_structures import BoolVec, Mat
from VeraGridEngine.enumerations import ResultTablePlotType
from VeraGridEngine.Utils.Filtering.filtering import (MasterFilter, Filter, FilterOps, FilterSubject,
                                                      is_numeric, parse_expression)
from VeraGridEngine.Devices.types import ALL_DEV_TYPES


def object_extract(elm: ALL_DEV_TYPES, args: List[str]) -> Any:
    """
    Extract value from object's property chain
    :param elm: Device
    :param args: list of properties (i.e. bus.area.name as ['bus', 'area', 'name'])
    :return: value
    """
    p = elm
    for arg in args:
        if hasattr(p, arg):
            p = getattr(p, arg)
        else:
            return None
    return p

def try_numeric(value: object) -> bool:
    """
    Check whether a value can be converted to a floating-point number.

    :param value: Value to inspect.
    :return: ``True`` when the value is numeric.
    """
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def results_table_value_to_search_text(table: ResultsTable, value: object) -> str:
    """
    Build the searchable text for one results-table value.

    Both the raw value and the value formatted as shown by ``ResultsModel`` are
    included so a user can search for the exact text visible in the table.

    :param table: Results table that defines the display precision.
    :param value: Cell value to convert.
    :return: Case-normalized searchable text.
    """
    raw_text: str = str(value)

    try:
        if value == 0:
            formatted_text: str = "0"
        else:
            formatted_text = format(value, table.format_string)
    except (TypeError, ValueError):
        # Text and other non-numeric result types have no numeric formatter.
        formatted_text = raw_text

    return (raw_text + "\n" + formatted_text).casefold()


def search_results_table(table: ResultsTable, text: str) -> ResultsTable:
    """
    Search row labels, column labels, and displayed cell values.

    Matching rows retain all columns to preserve the context of the result.
    A query matching only column labels retains all rows for those columns.

    :param table: Source results table.
    :param text: Free-text query.
    :return: Sliced results table containing every matching row or column.
    """
    query: str = text.casefold()
    row_mask: BoolVec = np.zeros(table.r, dtype=bool)
    column_mask: BoolVec = np.zeros(table.c, dtype=bool)

    # A row-label match selects that complete result row.
    row_index: int
    for row_index in range(table.r):
        if query in str(table.index_c[row_index]).casefold():
            row_mask[row_index] = True
        else:
            pass

    # A cell match selects its row, allowing users to search the text that is
    # actually visible after the table's numeric formatting has been applied.
    column_index: int
    for row_index in range(table.r):
        for column_index in range(table.c):
            value_text: str = results_table_value_to_search_text(
                table=table,
                value=table.data_c[row_index, column_index],
            )
            if query in value_text:
                row_mask[row_index] = True
            else:
                pass

    # Column-label matches are evaluated independently because a result may
    # have many rows but only one column relevant to the query.
    for column_index in range(table.c):
        if query in str(table.cols_c[column_index]).casefold():
            column_mask[column_index] = True
        else:
            pass

    has_matching_rows: bool = bool(np.any(row_mask))
    has_matching_columns: bool = bool(np.any(column_mask))

    if has_matching_rows:
        if has_matching_columns:
            pass
        else:
            column_mask = np.ones(table.c, dtype=bool)
    else:
        if has_matching_columns:
            row_mask = np.ones(table.r, dtype=bool)
        else:
            pass

    row_indices: np.ndarray = np.where(row_mask)[0]
    column_indices: np.ndarray = np.where(column_mask)[0]
    return table.slice_all(row_idx=row_indices, col_idx=column_indices)


def compute_results_table_masks(table: ResultsTable, flt: Filter) -> Tuple[BoolVec, BoolVec, Mat]:
    """

    :param table:
    :param flt:
    :return:
    """

    lst = flt.get_list_of_values()
    is_neg = flt.is_negative()

    if is_neg:
        final_idx_mask = np.ones(table.r, dtype=bool)
        final_col_mask = np.ones(table.c, dtype=bool)
        final_data_mask = np.ones((table.r, table.c), dtype=bool)
    else:
        final_idx_mask = np.zeros(table.r, dtype=bool)
        final_col_mask = np.zeros(table.c, dtype=bool)
        final_data_mask = np.zeros((table.r, table.c), dtype=bool)

    for value in lst:
        if flt.element == FilterSubject.VAL:
            if try_numeric(value) and is_numeric(table.data_c):
                val = float(value)
            else:
                val = value

            data_mask = np.zeros((table.r, table.c), dtype=bool)
            idx_mask = np.zeros(table.r, dtype=bool)
            col_mask = np.zeros(table.c, dtype=bool)

            for i in range(table.r):
                for j in range(table.c):
                    if flt.apply_filter_op(table.data_c[i, j], val):
                        idx_mask[i] = True
                        col_mask[j] = True
                        data_mask[i, j] = True

        elif flt.element == FilterSubject.IDX:

            val = value
            idx_mask = np.zeros(table.r, dtype=bool)
            col_mask = np.ones(table.c, dtype=bool)
            data_mask = np.zeros((table.r, table.c), dtype=bool)

            for i in range(table.r):

                if flt.apply_filter_op(table.index_c[i], val):
                    idx_mask[i] = True
                    data_mask[i, :] = True

        elif flt.element == FilterSubject.COL:

            val = value
            idx_mask = np.ones(table.r, dtype=bool)
            col_mask = np.zeros(table.c, dtype=bool)
            data_mask = np.zeros((table.r, table.c), dtype=bool)

            for j in range(table.c):

                if flt.apply_filter_op(table.cols_c[j], val):
                    col_mask[j] = True
                    data_mask[:, j] = True

        elif flt.element == FilterSubject.COL_OBJECT:

            val = value

            idx_mask = np.ones(table.r, dtype=bool)
            col_mask = np.zeros(table.c, dtype=bool)
            data_mask = np.zeros((table.r, table.c), dtype=bool)
            if len(table.idx_devices):
                for j in range(table.c):

                    if len(flt.element_args):
                        obj_val = object_extract(elm=table.col_devices[j], args=flt.element_args)
                    else:
                        obj_val = str(table.col_devices[j])

                    if obj_val is not None:

                        tpe = type(obj_val)

                        try:
                            val = tpe(val)
                        except TypeError:
                            # if the casting failed, try string comparison
                            val = str(val)
                            obj_val = str(obj_val)

                        if flt.apply_filter_op(obj_val, val):
                            col_mask[j] = True
                            data_mask[:, j] = True
                    else:
                        # the object_val is None
                        a = ".".join(flt.element_args)
                        raise ValueError(f"{a} cannot be found for the objects :(")

        elif flt.element == FilterSubject.IDX_OBJECT:

            val = value

            idx_mask = np.zeros(table.r, dtype=bool)
            col_mask = np.ones(table.c, dtype=bool)
            data_mask = np.zeros((table.r, table.c), dtype=bool)

            if len(table.idx_devices):

                for i in range(table.r):

                    if len(flt.element_args):
                        obj_val = object_extract(elm=table.idx_devices[i], args=flt.element_args)
                    else:
                        obj_val = str(table.idx_devices[i])

                    if obj_val is not None:

                        tpe = type(obj_val)

                        try:
                            val = tpe(val)
                        except TypeError:
                            # if the casting failed, try string comparison
                            val = str(val)
                            obj_val = str(obj_val)

                        if flt.apply_filter_op(obj_val, val):
                            idx_mask[i] = True
                            data_mask[i, :] = True
                    else:
                        # the object_val is None
                        a = ".".join(flt.element_args)
                        raise ValueError(f"{a} cannot be found for the objects :(")

        else:
            raise Exception("Invalid FilterSubject")

        if is_neg:
            final_idx_mask *= idx_mask
            final_col_mask *= col_mask
            final_data_mask *= data_mask
        else:
            final_idx_mask += idx_mask
            final_col_mask += col_mask
            final_data_mask += data_mask

    return final_idx_mask, final_col_mask, final_data_mask


class FilterResultsTable:
    """
    FilterResultsTable class
    """
    __slots__ = (
        "table",
        "master_filter",
        "search_text",
    )

    def __init__(self, table: ResultsTable) -> None:
        """
        Initialize a filter for one source results table.

        :param table: Results table to filter.
        :return: None.
        """
        self.table = table

        self.master_filter = MasterFilter()
        self.search_text: str | None = None

    def parse(self, expression: str) -> None:
        """
        Parses the query expression
        :param expression:
        :return:
        """
        clean_expression: str = expression.strip()
        self.search_text = None

        if (clean_expression.startswith("=")
                or clean_expression.startswith(">")
                or clean_expression.startswith("<")):
            clean_expression = "val " + clean_expression
        else:
            pass

        self.master_filter = parse_expression(expression=clean_expression)

        # The search box presents itself as a regular text search. When no
        # structured filter can be parsed, search every visible table field.
        if len(clean_expression) > 0 and self.master_filter.size() == 0:
            self.search_text = clean_expression
        else:
            pass

    def apply(self) -> ResultsTable:
        """

        :return:
        """
        if self.search_text is not None:
            return search_results_table(table=self.table, text=self.search_text)
        else:
            pass

        if len(self.master_filter.stack):
            first_filter: Filter = self.master_filter.stack[0]
            _, _, data_mask = compute_results_table_masks(table=self.table, flt=first_filter)
            if self.master_filter.is_correct_size():

                for st_idx in range(1, self.master_filter.size(), 2):

                    oper: FilterOps = self.master_filter.stack[st_idx]
                    flt: Filter = self.master_filter.stack[st_idx + 1]

                    _, _, data_mask2 = compute_results_table_masks(table=self.table, flt=flt)

                    if oper == FilterOps.OR:
                        data_mask = np.logical_or(data_mask, data_mask2)

                    elif oper == FilterOps.AND:
                        data_mask = np.logical_and(data_mask, data_mask2)

                    else:
                        raise Exception("Unsupported master filter opration")

            else:
                raise Exception("Unsupported number of filters. Use and or concatenation")

            # Derive table dimensions from the final cell-level mask. Complex
            # points retain both coordinate columns because Real and Imaginary
            # are an inseparable pair once a matching mode row is retained.
            row_mask: BoolVec = np.any(data_mask, axis=1)
            row_indices: np.ndarray = np.where(row_mask)[0]
            column_indices: np.ndarray
            data: np.ndarray
            has_column_filter: bool = False
            filter_stack_position: int
            for filter_stack_position in range(0, self.master_filter.size(), 2):
                coordinate_filter: Filter = self.master_filter.stack[filter_stack_position]
                if coordinate_filter.element == FilterSubject.COL:
                    has_column_filter = True
                else:
                    pass

            if self.table.plot_type == ResultTablePlotType.COMPLEX_POINTS and not has_column_filter:
                column_indices = np.arange(self.table.c, dtype=np.int64)
                data = self.table.data_c.copy()
            else:
                column_mask: BoolVec = np.any(data_mask, axis=0)
                column_indices = np.where(column_mask)[0]

                # Preserve floating and complex arrays when they can represent
                # NaN. Other result types use an object array so unmatched
                # cells can be blanked without coercing text or integers.
                if np.issubdtype(self.table.data_c.dtype, np.inexact):
                    data = self.table.data_c.copy()
                else:
                    data = self.table.data_c.astype(object, copy=True)
                data[np.logical_not(data_mask)] = np.nan

            return ResultsTable(data=data[np.ix_(row_indices, column_indices)],
                                columns=np.array([self.table.cols_c[j] for j in column_indices]),
                                index=np.array([self.table.index_c[i] for i in row_indices]),
                                title=self.table.title,
                                xlabel=self.table.x_label,
                                ylabel=self.table.y_label,
                                units=self.table.units,
                                editable=self.table.editable,
                                editable_min_idx=self.table.editable_min_idx,
                                decimals=self.table.decimals,
                                cols_device_type=self.table.cols_device_type,
                                idx_device_type=self.table.idx_device_type,
                                plot_type=self.table.plot_type,
                                damping_ratio_boundary=self.table.damping_ratio_boundary,
                                plot_title=self.table.plot_title,
                                complex_plot_x_column=self.table.complex_plot_x_column,
                                complex_plot_y_columns=self.table.complex_plot_y_columns,
                                complex_plot_y_scales=self.table.complex_plot_y_scales)

        else:
            return self.table
