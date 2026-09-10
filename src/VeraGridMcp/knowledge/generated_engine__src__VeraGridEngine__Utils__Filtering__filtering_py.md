# VeraGridEngine Module: src/VeraGridEngine/Utils/Filtering/filtering.py

- Original source path: `src/VeraGridEngine/Utils/Filtering/filtering.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 5
- Top-level function count: 5
- Representative imports: typing, enum, re, numpy

## Function: is_odd(number)

Check if number is odd

## Function: is_numeric(obj)

Checks if the numpy array is numeric

## Class: CompOps

- Bases: Enum
- Summary: Enumeration of filter oprations

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: FilterOps

- Bases: Enum
- Summary: Enumeration of filter operations

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: FilterSubject

- Bases: Enum
- Summary: Enumeration of filter operations

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: Filter

- Bases: none
- Summary: Filter

### Methods

- `is_negative(self)`
  Summary: Is the filter operation negative?
- `get_list_of_values(self)`
  Summary: Get a list of values to compare to
- `try_numeric(value)`
  Summary: Try to convert a value to a numeric type
- `apply_filter_op(self, obj_val, val)`
  Summary: Apply the filter operation

## Class: MasterFilter

- Bases: none
- Summary: MasterFilter

### Methods

- `add(self, elm)`
  Summary: Add filter or filter operation to the stack
- `size(self)`
  Summary: Get the size of the stack
- `is_correct_size(self)`
  Summary: Returns if the stack has the right size: an odd number

## Function: parse_single(token)

Parse single token, these are tokens that are composed on 3 parts: element, operation, comparison value

## Function: has_operators(token)

Check if there are operators and , or in the token

## Function: parse_expression(expression)

Parses the query expression
