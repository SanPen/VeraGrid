# VeraGridEngine Module: src/VeraGridEngine/Devices/profile.py

- Original source path: `src/VeraGridEngine/Devices/profile.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 2
- Representative imports: typing, collections, numpy, numba, VeraGridEngine.basic_structures, VeraGridEngine.enumerations, VeraGridEngine.Utils.Sparse.sparse_array

## Function: compress_array_numba(arr, base)

Compress Array

## Function: check_if_sparse(arr, sparsity)

Check if the array is sparse

## Class: Profile

- Bases: none
- Summary: Profile

### Methods

- `clear(self)`
  Summary: Clear the profile
- `info(self)`
  Summary: Return dictionary with information about the profile object and its content
- `get_sparse_map(self)`
  Summary: Return the dictionary hosting the sparse data if this profile is sparse
- `dtype(self)`
  Summary: Get the declared data type
- `default_value(self)`
  Summary: Get the declared type
- `default_value(self, val)`
  Summary: :param val:
- `is_sparse(self)`
  Summary: is the profile sparse?
- `is_initialized(self)`
  Summary: is the profile initialized?
- `set_initialized(self)`
  Summary: Set the profile to initialized
- `sparse_array(self)`
  Summary: Sparse array getter
- `dense_array(self)`
  Summary: Dense array getter
- `create_sparse(self, size, default_value, map_data)`
  Summary: Build sparse from definition
- `create_dense(self, size, default_value)`
  Summary: Create a dense profile
- `sparsity(self)`
  Summary: Get the profile sparsity
- `set(self, arr)`
  Summary: Set array value
- `convert_sparse_to_dense(self)`
  Summary: Convert this profile to sparse
- `resize(self, n)`
  Summary: Resize the profile
- `resample(self, indices)`
  Summary: Resample this profile in-place
- `fill(self, value)`
  Summary: Fill this profile with the same value
- `scale(self, value)`
  Summary: Scale this profile with the same value
- `size(self)`
  Summary: Get the size
- `toarray(self)`
  Summary: Get dense numpy array representation
- `tolist(self)`
  Summary: Get dense list representation
- `astype(self, tpe)`
  Summary: get the dense array as type specified by tpe
- `get_sparse_representation(self)`
  Summary: Get the sparse representation of the sparse data
- `set_sparse_data_from_data(self, indptr, data)`
  Summary: Set sparse data from indices
- `fix_nan(self, default_value)`
  Summary: Replace NaN values with default value in-place
- `copy(self)`
  Summary: Deep copy
