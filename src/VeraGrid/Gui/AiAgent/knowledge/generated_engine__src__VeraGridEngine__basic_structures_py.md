# VeraGridEngine Module: src/VeraGridEngine/basic_structures.py

- Original source path: `src/VeraGridEngine/basic_structures.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 7
- Top-level function count: 4
- Representative imports: __future__, typing, pandas, numpy, numpy.typing, datetime, scipy.sparse, VeraGridEngine.enumerations, copy

## Class: CDF

- Bases: none
- Summary: Inverse Cumulative density function of a given array of data

### Methods

- `get_sample(self, npoints)`
  Summary: Samples a number of uniform distributed points and
- `get_at(self, prob)`
  Summary: Samples a number of uniform distributed points and
- `expectation(self)`
  Summary: Returns the CDF expected value (AKA the mean)
- `plot(self, plt, LINEWIDTH, ax)`
  Summary: Plots the CFD

## Function: classify_by_hour(t)

Passes an array of TimeStamps to an array of arrays of indices

## Function: classify_by_day(t)

Passes an array of TimeStamps to an array of arrays of indices

## Function: get_time_groups(t_array, grouping)

Get the indices delimiting a number of groups

## Class: LogEntry

- Bases: none
- Summary: Logger entry

### Methods

- `to_list(self)`
  Summary: Get list representation of this entry
- `to_list_reduced(self)`
  Summary: Get list representation of this entry

## Class: Logger

- Bases: none
- Summary: Logger class

### Methods

- `add_debug(self, *args)`
  Summary: Add debug entry
- `append(self, txt)`
  Summary: simple text log
- `has_logs(self)`
  Summary: Are there any logs?
- `add_info(self, msg, device, value, expected_value, device_class, comment, device_property, object_value, expected_object_value)`
  Summary: Add info entry
- `add_warning(self, msg, device, value, expected_value, device_class, comment, device_property, object_value, expected_object_value)`
  Summary: Add warning entry
- `add_error(self, msg, device, value, expected_value, device_class, comment, device_property, object_value, expected_object_value)`
  Summary: Add error entry
- `add_divergence(self, msg, device, value, expected_value, tol)`
  Summary: Add divergence entry
- `add(self, msg, severity, device, value, expected_value, device_class, comment, device_property, object_value, expected_object_value)`
  Summary: Add general entry
- `to_dict(self)`
  Summary: Get the logs sorted by severity and message
- `to_df(self)`
  Summary: Get DataFrame
- `parse_df(self, df)`
  Summary: Parse DataFrame
- `to_csv(self, fname)`
  Summary: Save to CSV
- `to_xlsx(self, fname)`
  Summary: To Excel
- `print(self, title)`
  Summary: Print the logs
- `size(self)`
  Summary: Number of logs
- `count_type(self, severity)`
  Summary: Count the number of entries of a certain severity
- `info_count(self)`
  Summary: Count the number of information occurences
- `warning_count(self)`
  Summary: Count number of warnings
- `error_count(self)`
  Summary: Count number of errors
- `has_errors(self)`
  Summary: Check if there are errors

## Class: ConvergenceReport

- Bases: none
- Summary: Convergence report

### Methods

- `add(self, method, converged, error, elapsed, iterations)`
  Summary: :param method:
- `converged(self)`
  Summary: :return:
- `error(self)`
  Summary: :return:
- `elapsed(self)`
  Summary: :return:
- `iterations(self)`
  Summary: :return:
- `to_dataframe(self)`
  Summary: :return:

## Function: get_list_dim(a)

Get the dimensions of a List, this is for the case were a matrix is represented by lists of lists

## Class: CompressedJsonStruct

- Bases: none
- Summary: Compressed json block

### Methods

- `get_position_dict(self)`
  Summary: :return:
- `set_fields(self, fields)`
  Summary: Set the block fields and initialize the reverse index lookup
- `set_data(self, dta)`
  Summary: Set the data and check its consistency
- `get_data(self)`
  Summary: :return:
- `get_row_number(self)`
  Summary: :return:
- `get_col_index(self, prop)`
  Summary: :param prop:
- `get_final_dict(self)`
  Summary: :return:
- `get_dict_at(self, i)`
  Summary: :param i:
- `declare_n_entries(self, n)`
  Summary: Add n entries to the data
- `set_at(self, i, col_name, val)`
  Summary: Set value at a position, counts that the data has been declared

## Class: ListSet

- Bases: list
- Summary: This is a class that behaves like a list except for the query "in" where it behaves like a set O(1)

### Methods

- `append(self, value)`
  Summary: Append an item to the list if it's not already present.
- `extend(self, iterable)`
  Summary: Extend the list by appending elements from the iterable, ensuring uniqueness.
- `insert(self, index, value)`
  Summary: Insert an item at a given position if it's not already present.
- `remove(self, value)`
  Summary: Remove the first occurrence of a value. Raises ValueError if not found.
- `pop(self, index)`
  Summary: Remove and return the item at the given position.
- `clear(self)`
  Summary: Remove all items from the list.
- `copy(self)`
  Summary: Return a shallow copy of the ListSet.

## Class: Vector

- Bases: none
- Summary: Python implementation of a C++ like std::vector

### Methods

- `push_back(self, value)`
  Summary: Append a value at the end.
- `pop_back(self)`
  Summary: Remove and return the last element.
- `clear(self)`
  Summary: Remove all elements.
- `resize(self, new_size, value)`
  Summary: Resize the vector like in C++ std::vector.
- `copy(self)`
  Summary: Return a deep copy of the vector.
