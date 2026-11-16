# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Validation shared by the interchange artifacts exported for external solvers.

It covers the model identity that binds an artifact to its consumer program
and the immutable numpy arrays the artifacts expose.
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt


def validate_model_identity(model_identity: object) -> str:
    """
    Validate the identity that binds an artifact to its consumer model.

    :param model_identity: Candidate identity.
    :return: The identity, a str of 1..256 characters in 0x20..0x7E.
    :raises ValueError: When the identity is not such a str.
    """
    if type(model_identity) is not str or len(model_identity) < 1 or len(model_identity) > 256:
        raise ValueError("model_identity must be a str of 1..256 characters")
    else:
        pass
    character: str
    for character in model_identity:
        if ord(character) < 0x20 or ord(character) > 0x7E:
            raise ValueError("model_identity must contain only printable ASCII characters")
        else:
            pass
    return model_identity


def immutable_array(values: object, name: str, dtype: np.dtype) -> npt.NDArray:
    """
    Validate a one-dimensional array and return an immutable native copy.

    For ``int32`` any integer (not bool) dtype is accepted when its values fit
    in int32; for ``float64`` any floating dtype is accepted.

    :param values: One-dimensional numpy array.
    :param name: Array name used in error messages.
    :param dtype: Target dtype, ``np.dtype(np.int32)`` or ``np.dtype(np.float64)``.
    :return: C-contiguous array of the target dtype backed by immutable bytes.
    :raises ValueError: When the array has the wrong shape, dtype or range.
    """
    if not isinstance(values, np.ndarray):
        raise ValueError(name + " must be a numpy array")
    elif values.ndim != 1:
        raise ValueError(name + " must be one-dimensional")
    else:
        pass

    if dtype == np.dtype(np.int32):
        if values.dtype == np.bool_ or not np.issubdtype(values.dtype, np.integer):
            raise ValueError(name + " must have an integer dtype")
        else:
            pass
        int32_info: np.iinfo = np.iinfo(np.int32)
        if values.size > 0 and (int(values.min()) < int(int32_info.min) or int(values.max()) > int(int32_info.max)):
            raise ValueError(name + " holds values outside the int32 range")
        else:
            pass
    elif dtype == np.dtype(np.float64):
        if not np.issubdtype(values.dtype, np.floating):
            raise ValueError(name + " must have a floating dtype")
        else:
            pass
    else:
        raise ValueError(name + " requests an unsupported dtype")

    # Backing the array with immutable bytes makes writeable impossible to re-enable.
    native: npt.NDArray = np.ascontiguousarray(values, dtype=dtype)
    return np.frombuffer(native.tobytes(), dtype=dtype)
