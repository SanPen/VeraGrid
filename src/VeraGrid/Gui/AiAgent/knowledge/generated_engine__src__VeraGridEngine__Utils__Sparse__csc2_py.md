# VeraGridEngine Module: src/VeraGridEngine/Utils/Sparse/csc2.py

- Original source path: `src/VeraGridEngine/Utils/Sparse/csc2.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 2
- Top-level function count: 29
- Representative imports: __future__, warnings, math, typing, numba, numba, numba.experimental, numpy, scipy.sparse, scipy.sparse.linalg._dsolve._superlu, VeraGridEngine.basic_structures

## Class: CSC

- Bases: none
- Summary: numba CSC matrix struct

### Methods

- `set(self, indices, indptr, data)`
  Summary: Set the internal arrays
- `fill_from_coo(self, Ti, Tj, Tx, nnz)`
  Summary: C = compressed-column form of a triplet matrix T.
- `shape(self)`
  Summary: Shape for scipy compatibility
- `resize(self, nnz)`
  Summary: Resize this matrix
- `todense(self)`
  Summary: Get dense array representation
- `toarray(self)`
  Summary: Get dense array representation
- `copy(self)`
  Summary: Create a copy of this matrix
- `dot(self, x)`
  Summary: Mat-vector multiplication
- `get_diag_max(self)`
  Summary: Get the maximum value of the diagonal
- `add_val_to_diagonal(self, val)`
  Summary: Add value to the diagonal in-place
- `mul(self, B)`
  Summary: @ operator
- `sum(self, B)`
  Summary: @ operator
- `add_scalar(self, val)`
  Summary: No docstring provided.
- `prod_scalar(self, val)`
  Summary: No docstring provided.

## Class: CxCSC

- Bases: none
- Summary: numba CSC matrix struct

### Methods

- `set(self, indices, indptr, data)`
  Summary: Set the internal arrays
- `fill_from_coo(self, Ti, Tj, Tx, nnz)`
  Summary: C = compressed-column form of a triplet matrix T.
- `shape(self)`
  Summary: Shape for scipy compatibility
- `real(self)`
  Summary: Get the real representation of this matrix
- `imag(self)`
  Summary: Get the imaginary representation of this matrix
- `resize(self, nnz)`
  Summary: Resize this matrix
- `todense(self)`
  Summary: Get dense array representation
- `toarray(self)`
  Summary: Get dense array representation
- `copy(self)`
  Summary: Create a copy of this matrix
- `dot(self, x)`
  Summary: Mat-vector multiplication
- `csc_matrix_matrix_addition(self, b)`
  Summary: No docstring provided.

## Function: mat_to_scipy(csc)

CSC or CxCSC Matrix to Scipy

## Function: scipy_to_mat(mat)

Scipy CSC matrix to CSC marix

## Function: scipy_to_cxmat(mat)

Scipy CSC matrix to CxCSC marix

## Function: spfactor(A)

Sparse factorization with SuperLU

## Function: spsolve_csc(A, x)

Sparse solution

## Function: pack_4_by_4(A, B, C, D)

Stack 4 CSC matrices in a 2 by 2 structure

## Function: pack_3_by_4(A, B, C)

Stack 3 CSC matrices in a 2 by 2 structure

## Function: csc_cumsum_i(p, c, n)

p [0..n] = cumulative sum of c [0..n-1], and then copy p [0..n-1] into c

## Function: sp_transpose(A)

Actual CSC transpose unlike scipy's

## Function: sp_slice_cols(A, cols)

Slice columns

## Function: sp_slice_rows(mat, rows)

Slice rows

## Function: sp_slice(A, rows, cols)

/*

## Function: csc_stack_2d_ff(mats, n_rows, n_cols)

Assemble matrix from a list of matrices representing a "super matrix"

## Function: diags(array)

Get diagonal sparse matrix from array

## Function: diagc(m, value)

Get diagonal sparse matrix from value

## Function: extend(A, last_col, last_row, corner_val)

B = |   A       last_col |

## Function: csc_multiply_ff(A, B)

Sparse matrix multiplication, C = A*B where A and B are CSC sparse matrices

## Function: csc_multiply_ff2(Am, An, Ap, Ai, Ax, Bm, Bn, Bp, Bi, Bx)

Sparse matrix multiplication, C = A*B where A and B are CSC sparse matrices

## Function: csc_multiply_cx(A, B)

Sparse matrix multiplication, C = A*B where A and B are CSC sparse matrices

## Function: csc_matvec_ff(A, x)

:param A:

## Function: csc_matvec_cx(A, x)

:param A:

## Function: csc_scatter_f(Ap, Ai, Ax, j, beta, w, x, mark, Ci, nz)

Scatters and sums a sparse vector A(:,j) into a dense vector, x = x + beta * A(:,j)

## Function: csc_scatter_cx(Ap, Ai, Ax, j, beta, w, x, mark, Ci, nz)

Scatters and sums a sparse vector A(:,j) into a dense vector, x = x + beta * A(:,j)

## Function: csc_spalloc_f(m, n, nzmax)

Allocate a sparse matrix (triplet form or compressed-column form).

## Function: csc_spalloc_cx(m, n, nzmax)

Allocate a sparse matrix (triplet form or compressed-column form).

## Function: csc_add_ff(A, B, alpha, beta)

C = alpha*A + beta*B

## Function: csc_add_ff2(Am, An, Aindptr, Aindices, Adata, Bn, Bindptr, Bindices, Bdata)

C = A + B

## Function: csc_add_cx2(Am, An, Aindptr, Aindices, Adata, Bn, Bindptr, Bindices, Bdata)

C = A + B

## Function: csc_add_cx3(A, B)

No docstring provided.
