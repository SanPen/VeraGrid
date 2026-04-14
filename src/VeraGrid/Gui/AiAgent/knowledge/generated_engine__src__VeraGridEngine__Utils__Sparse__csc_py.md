# VeraGridEngine Module: src/VeraGridEngine/Utils/Sparse/csc.py

- Original source path: `src/VeraGridEngine/Utils/Sparse/csc.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 14
- Representative imports: numpy, numba, scipy.sparse.sparsetools, scipy.sparse, VeraGridEngine.Utils.Sparse.csc_numba, VeraGridEngine.basic_structures

## Function: Csc0(m, n)

No docstring provided.

## Class: CscMat

- Bases: csc_matrix
- Summary: Matrix in compressed-column or triplet form.

### Methods

- `dot(self, o)`
  Summary: Dot product
- `islands(self)`
  Summary: Find islands in the matrix

## Function: scipy_to_mat(scipy_mat)

Build CsCMat from csc_matrix

## Function: pack_4_by_4(A11, A12, A21, A22)

Stack 4 CSC matrices in a 2 by 2 structure

## Function: pack_4_by_4_scipy(A11, A12, A21, A22)

Stack 4 CSC matrices in a 2 by 2 structure

## Function: pack_3_by_4(A11, A12, A21)

Stack 3 CSC matrices in a 2 by 2 structure

## Function: sp_transpose(mat)

Actual CSC transpose unlike scipy's

## Function: sp_slice_cols(mat, cols)

Slice columns

## Function: sp_slice_rows(mat, rows)

Slice rows

## Function: sp_slice(mat, rows, cols)

/*

## Function: csc_stack_2d_ff(mats, m_rows, m_cols, row_major)

Assemble matrix from a list of matrices representing a "super matrix"

## Function: csc_stack_2d_ff_old(mats, m_rows, m_cols)

Assemble matrix from a list of matrices representing a "super matrix"

## Function: dense_to_csc(mat, threshold)

Extract the sparse matrix from a dense matrix where abs values are below a threshold

## Function: diags(array)

Convert array to CSC diagonal matrix

## Function: diagc(n, value)

Create constant value diagonal matrix
