# VeraGridEngine Module: src/VeraGridEngine/Simulations/results_table.py

- Original source path: `src/VeraGridEngine/Simulations/results_table.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: typing, numpy, pandas, matplotlib, VeraGridEngine.enumerations, VeraGridEngine.basic_structures, VeraGridEngine.Devices.types

## Class: ResultsTable

- Bases: none
- Summary: Class to populate a Qt table view with data from the results

### Methods

- `col_devices(self)`
  Summary: :return:
- `idx_devices(self)`
  Summary: :return:
- `set_col_devices(self, devices_list)`
  Summary: Set the list of devices that matches the results for filtering
- `set_idx_devices(self, devices_list)`
  Summary: Set the list of devices that matches the results for filtering
- `transpose(self)`
  Summary: Transpose the results in-place
- `sort_column(self, c, max_to_min)`
  Summary: :param c:
- `slice_cols(self, col_idx)`
  Summary: Make column slicing
- `slice_rows(self, idx)`
  Summary: Make rows slicing
- `slice_all(self, row_idx, col_idx)`
  Summary: Make rows slicing
- `search_in_columns(self, txt)`
  Summary: Search stuff
- `search_in_rows(self, txt)`
  Summary: Search stuff
- `copy_to_column(self, row, col)`
  Summary: Copies one value to all the column
- `is_complex(self)`
  Summary: Is the data complex?
- `get_data(self)`
  Summary: Returns: index, columns, data
- `convert_to_cdf(self)`
  Summary: Convert the data in-place to CDF based
- `convert_to_abs(self)`
  Summary: Convert the data to abs
- `to_df(self)`
  Summary: get DataFrame
- `save_to_excel(self, file_name)`
  Summary: save data to excel
- `save_to_csv(self, file_name)`
  Summary: Save data to csv
- `get_data_frame(self)`
  Summary: Save data to csv
- `plot(self, ax, selected_col_idx, selected_rows, stacked)`
  Summary: Plot the data model
- `plot_device(self, ax, device_idx, stacked, title)`
  Summary: Plot the data model
