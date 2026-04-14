# VeraGridEngine Module: src/VeraGridEngine/data_logger.py

- Original source path: `src/VeraGridEngine/data_logger.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 3
- Top-level function count: 0
- Representative imports: typing, enum, datetime, VeraGridEngine.basic_structures

## Class: DataLogSeverity

- Bases: Enum
- Summary: DataLogSeverity

### Methods

- `argparse(s)`
  Summary: No docstring provided.
- `to_normal(self)`
  Summary: No docstring provided.

## Class: DataLogEntry

- Bases: none
- Summary: DataLogEntry

### Methods

- `to_list(self)`
  Summary: Get list of arguments
- `to_normal_entry(self)`
  Summary: No docstring provided.

## Class: DataLogger

- Bases: none
- Summary: DataLogger

### Methods

- `get_message(self)`
  Summary: Get a diagnostic message
- `add_debug(self, *args)`
  Summary: :param args:
- `append(self, txt)`
  Summary: :param txt:
- `has_logs(self)`
  Summary: Has logs?
- `add_info(self, msg, device, device_class, device_property, value, expected_value, comment)`
  Summary: :param msg:
- `add_warning(self, msg, device, device_class, device_property, value, expected_value, comment)`
  Summary: :param msg:
- `add_error(self, msg, device, device_class, device_property, value, expected_value, comment)`
  Summary: :param msg:
- `add_divergence(self, msg, device, device_class, device_property, value, expected_value, tol)`
  Summary: :param msg:
- `add(self, msg, severity, device, device_class, device_property, value, expected_value)`
  Summary: :param msg:
- `to_dict(self)`
  Summary: Get the logs sorted by severity and message
- `to_df(self)`
  Summary: Get DataFrame
- `to_csv(self, fname)`
  Summary: Save to CSV file
- `to_xlsx(self, fname, sheet_name)`
  Summary: Save to excel file
- `get_logger(self)`
  Summary: Convert logger entries
- `size(self)`
  Summary: Get size
