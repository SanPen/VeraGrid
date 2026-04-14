# VeraGridEngine Module: src/VeraGridEngine/Utils/Sparse/sparse_array.py

- Original source path: `src/VeraGridEngine/Utils/Sparse/sparse_array.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 2
- Top-level function count: 1
- Representative imports: typing, numpy, enum, VeraGridEngine.enumerations, VeraGridEngine.basic_structures

## Function: check_type(dtype, value)

Checks that the type of value is the declared type in the profile

## Class: SparseArray

- Bases: none
- Summary: SparseArray

### Methods

- `copy(self)`
  Summary: Get a deep copy of this object
- `dtype(self)`
  Summary: Get the declared type
- `default_value(self)`
  Summary: Default value getter
- `default_value(self, val)`
  Summary: Set the default value, updating the map to maintain consistency.
- `info(self)`
  Summary: Return dictionary with information about the profile object and its content
- `get_map(self)`
  Summary: Return the dictionary hosting the sparse data
- `insert(self, i, x)`
  Summary: Insert an element in the data dictionary
- `get_sparsity(self)`
  Summary: Get the sparsity of this profile
- `create(self, size, default_value, data)`
  Summary: Build sparse from definition
- `create_from_array(self, array, default_value)`
  Summary: Build sparse from array
- `create_from_dict(self, default_value, size, map_data)`
  Summary: Create this array from dict data
- `fill(self, value)`
  Summary: Fill the sparse array with the same value
- `toarray(self)`
  Summary: Get numpy vector from this sparse structure
- `at(self, idx)`
  Summary: Get the array at a position
- `size(self)`
  Summary: Get the size
- `clear(self)`
  Summary: Clear the sparse array
- `set_data(self, d)`
  Summary: No docstring provided.
- `resize(self, n)`
  Summary: Resize the array
- `resample(self, indices)`
  Summary: Resample this sparse array in-place
- `slice(self, indices)`
  Summary: Get a resampled copy of this sparse array
- `get_sparse_representation(self)`
  Summary: Get the sparse representation of the sparse data
- `set_sparse_data_from_data(self, indptr, data)`
  Summary: :param indptr:

## Class: SparseObjectArray

- Bases: none
- Summary: SparseArray

### Methods

- `copy(self)`
  Summary: Get a deep copy of this object
- `info(self)`
  Summary: Return dictionary with information about the profile object and its content
- `get_map(self)`
  Summary: Return the dictionary hosting the sparse data
- `insert(self, i, x)`
  Summary: Insert an element in the data dictionary
- `get_sparsity(self)`
  Summary: Get the sparsity of this profile
- `at(self, idx)`
  Summary: Get the array at a position
- `size(self)`
  Summary: Get the size
- `resize(self, n)`
  Summary: Resize the array
- `resample(self, indices)`
  Summary: Resample this sparse array in-place
- `slice(self, indices)`
  Summary: Get a resampled copy of this sparse array
