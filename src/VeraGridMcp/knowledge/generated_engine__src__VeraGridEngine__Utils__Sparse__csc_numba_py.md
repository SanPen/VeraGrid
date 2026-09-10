# VeraGridEngine Module: src/VeraGridEngine/Utils/Sparse/csc_numba.py

- Original source path: `src/VeraGridEngine/Utils/Sparse/csc_numba.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 35
- Representative imports: numpy, numba, numba.typed, math, typing, VeraGridEngine.basic_structures

## Function: ialloc(n)

No docstring provided.

## Function: xalloc(n)

No docstring provided.

## Function: csc_spalloc_f(m, n, nzmax)

Allocate a sparse matrix (triplet form or compressed-column form).

## Function: _copy_f(src, dest, length)

No docstring provided.

## Function: _copy_i(src, dest, length)

No docstring provided.

## Function: csc_cumsum_i(p, c, n)

p [0..n] = cumulative sum of c [0..n-1], and then copy p [0..n-1] into c

## Function: csc_sprealloc_f(An, Aindptr, Aindices, Adata, nzmax)

Change the max # of entries a sparse matrix can hold.

## Function: csc_scatter_f(Ap, Ai, Ax, j, beta, w, x, mark, Ci, nz)

Scatters and sums a sparse vector A(:,j) into a dense vector, x = x + beta * A(:,j)

## Function: csc_scatter_ff(Aindptr, Aindices, Adata, j, beta, w, x, mark, Ci, nz)

Scatters and sums a sparse vector A(:,j) into a dense vector, x = x + beta * A(:,j)

## Function: csc_add_ff(Am, An, Aindptr, Aindices, Adata, Bm, Bn, Bindptr, Bindices, Bdata, alpha, beta)

C = alpha*A + beta*B

## Function: csc_multiply_ff(Am, An, Ap, Ai, Ax, Bm, Bn, Bp, Bi, Bx)

Sparse matrix multiplication, C = A*B where A and B are CSC sparse matrices

## Function: csc_mat_vec_ff(m, n, Ap, Ai, Ax, x)

Sparse matrix times dense column vector, y = A * x.

## Function: diag_positions(n, Ap, Ai)

get the positions of the diagonal in the CSC data scheme

## Function: coo_to_csc(m, n, Ti, Tj, Tx, nnz)

C = compressed-column form of a triplet matrix T.

## Function: csc_to_csr(m, n, Ap, Ai, Ax, Bp, Bi, Bx)

Convert a CSC Matrix into a CSR Matrix

## Function: csc_transpose(m, n, Ap, Ai, Ax)

Transpose matrix

## Function: binary_find(N, x, array)

Binary search

## Function: csc_sub_matrix_old(Am, Anz, Ap, Ai, Ax, rows, cols)

Get SCS arbitrary sub-matrix

## Function: csc_sub_matrix(Am, Annz, Ap, Ai, Ax, rows, cols)

CSC matrix sub-matrix view

## Function: csc_sub_matrix_cols(Am, Anz, Ap, Ai, Ax, cols)

Get SCS arbitrary sub-matrix with all the rows

## Function: csc_sub_matrix_rows(An, Anz, Ap, Ai, Ax, rows)

Get SCS arbitrary sub-matrix

## Function: csc_to_dense(m, n, indptr, indices, data)

Convert csc matrix to dense

## Function: csc_diagonal(m, value)

Build CSC diagonal matrix of the given value

## Function: csc_diagonal_from_array(array)

:param m:

## Function: csc_diagonal_from_complex_array(array)

:param m:

## Function: csc_diagonal_from_number(m, value)

:param m:

## Function: csc_stack_4_by_4_ff(am, an, Ai, Ap, Ax, bm, bn, Bi, Bp, Bx, cm, cn, Ci, Cp, Cx, dm, dn, Di, Dp, Dx)

stack csc sparse float matrices like this:

## Function: csc_stack_3_by_4_ff(am, an, Ai, Ap, Ax, bm, bn, Bi, Bp, Bx, cm, cn, Ci, Cp, Cx)

stack csc sparse float matrices like this:

## Function: csc_norm(n, Ap, Ax)

Computes the 1-norm of a sparse matrix = max (sum (abs (A))), largest

## Function: find_islands(node_number, indptr, indices)

Method to get the islands of a graph

## Function: sp_submat_c_numba(nrows, ptrs, indices, values, cols)

slice CSC columns

## Function: csc_stack_2d_ff_row_major(mats_data, mats_indptr, mats_indices, mats_cols, mats_rows, m_rows, m_cols)

Assemble matrix from a list of matrices representing a "super matrix"

## Function: csc_stack_2d_ff_col_major(mats_data, mats_indptr, mats_indices, mats_cols, mats_rows, m_rows, m_cols)

Assemble matrix from a list of matrices representing a "super matrix"

## Function: dense_to_csc_numba(mat, threshold)

Extract the sparse matrix from a dense matrix where abs values are below a threshold

## Function: get_sparse_array_numba(arr, threshold)

Extract the sparse array from a dense array where abs values are below a threshold
