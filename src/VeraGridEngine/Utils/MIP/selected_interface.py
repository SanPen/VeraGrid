# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

"""
Uncomment the appropriate interface imports to use: Pulp or OrTools
"""
from typing import List, Union, Tuple
import numpy as np
from scipy.sparse import csc_matrix
from VeraGridEngine.basic_structures import ObjVec, ObjMat
from VeraGridEngine.enumerations import MIPFramework, MIPSolvers

from VeraGridEngine.Utils.MIP.pulp_interface import (LpExp as PulpLpExp,
                                                     LpVar as PulpLpVar,
                                                     PulpLpModel,
                                                     get_pulp_available_mip_solvers)

try:
    from VeraGridEngine.Utils.MIP.ortools_interface import (LpExp as OrToolsLpExp,
                                                            LpVar as OrToolsLpVar,
                                                            OrToolsLpModel,
                                                            get_ortools_available_mip_solvers)

    ORTOOLS_AVAILABLE = True
    print("ortools available")
except ImportError:
    ORTOOLS_AVAILABLE = False
    OrToolsLpModel = None
    OrToolsLpExp = None
    OrToolsLpVar = None
    get_ortools_available_mip_solvers = None

LpExp = Union[PulpLpExp, OrToolsLpExp]
LpVar = Union[PulpLpVar, OrToolsLpVar]
LpModel = Union[PulpLpModel, OrToolsLpModel]


def get_available_mip_frameworks() -> List[MIPFramework]:
    """
    Get list of available frameworks
    :return: List[MIPFramework]
    """
    lst = [MIPFramework.PuLP]

    if ORTOOLS_AVAILABLE:
        lst.append(MIPFramework.OrTools)

    return lst


def get_model_instance(tpe: MIPFramework, solver_type: MIPSolvers) -> LpModel:
    """
    Get an instance of the solver framework and the selected solver
    :param tpe: MIPInterface framework
    :param solver_type: MIPSolvers
    :return: OrToolsLpModel or PulpLpModel
    """
    if tpe == MIPFramework.OrTools and ORTOOLS_AVAILABLE:
        return OrToolsLpModel(solver_type)
    elif tpe == MIPFramework.PuLP:
        return PulpLpModel(solver_type)
    else:
        return PulpLpModel(solver_type)


def get_available_mip_solvers(tpe: MIPFramework) -> List[str]:
    """
    Get the solvers available in the selected interface
    :param tpe:
    :return:
    """
    if tpe == MIPFramework.OrTools and ORTOOLS_AVAILABLE:
        return get_ortools_available_mip_solvers()
    elif tpe == MIPFramework.PuLP:
        return get_pulp_available_mip_solvers()
    else:
        return get_pulp_available_mip_solvers()


def join(init: str, vals: List[int], sep="_"):
    """
    Generate naming string
    :param init: initial string
    :param vals: concatenation of indices
    :param sep: separator
    :return: naming string
    """
    return init + sep.join([str(x) for x in vals])


def lpDot(mat: csc_matrix, arr: Union[ObjVec, ObjMat]) -> Union[ObjVec, ObjMat]:
    """
    CSC matrix-vector or CSC matrix-matrix dot product (A x b)
    :param mat: CSC sparse matrix (A)
    :param arr: dense vector or matrix of object type (b)
    :return: vector or matrix result of the product
    """
    n_rows, n_cols = mat.shape

    # check dimensional compatibility
    assert (n_cols == arr.shape[0])

    # check that the sparse matrix is indeed of CSC format
    if mat.format != 'csc':
        raise Exception("lpDot: Sparse matrix must be in CSC format")

    if arr.ndim == 1:
        """
        Uni-dimensional sparse matrix - vector product
        """
        res = np.zeros(n_rows, dtype=arr.dtype)
        for i in range(n_cols):
            for ii in range(mat.indptr[i], mat.indptr[i + 1]):
                j = mat.indices[ii]  # row index
                if mat.data[ii] != 0.0:
                    res[j] += mat.data[ii] * arr[i]  # C.data[ii] is equivalent to C[i, j]

        return res

    elif arr.ndim == 2:
        """
        Multi-dimensional sparse matrix - matrix product
        """
        cols_vec = arr.shape[1]
        res = np.zeros((n_rows, cols_vec), dtype=arr.dtype)

        for k in range(cols_vec):  # for each column of the matrix "vec", do the matrix vector product
            for i in range(n_cols):
                for ii in range(mat.indptr[i], mat.indptr[i + 1]):
                    j = mat.indices[ii]  # row index
                    if mat.data[ii] != 0.0:
                        res[j, k] += mat.data[ii] * arr[i, k]  # C.data[ii] is equivalent to C[i, j]

        return res

    else:
        raise Exception("lpDot: Unsupported number of dimensions")


def lpDot1D_changes(mat: csc_matrix, arr: Union[ObjVec, ObjMat]) -> Tuple[ObjVec, List[int]]:
    """
    CSC matrix-vector or CSC matrix-matrix dot product (A x b)
    :param mat: CSC sparse matrix (A)
    :param arr: dense vector or matrix of object type (b)
    :return: vector or matrix result of the product
    """
    n_rows, n_cols = mat.shape

    # check dimensional compatibility
    assert (n_cols == arr.shape[0])

    # check that the sparse matrix is indeed of CSC format
    if mat.format != 'csc':
        raise Exception("lpDot: Sparse matrix must be in CSC format")

    if arr.ndim == 1:
        """
        Uni-dimensional sparse matrix - vector product
        """
        res = np.zeros(n_rows, dtype=arr.dtype)
        indices = list()
        for i in range(n_cols):
            for ii in range(mat.indptr[i], mat.indptr[i + 1]):
                j = mat.indices[ii]  # row index
                if mat.data[ii] != 0.0:
                    res[j] += mat.data[ii] * arr[i]  # C.data[ii] is equivalent to C[i, j]
                    indices.append(j)

        return res, indices

    else:
        raise Exception("lpDot1D_changes: Unsupported number of dimensions")
