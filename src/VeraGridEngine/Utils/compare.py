# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import numpy as np

from VeraGridEngine.basic_structures import Logger


def compare_arr(arr, arr_expected, tol: float, name: str, test: str, logger: Logger) -> None:
    if arr.shape != arr_expected.shape:
        logger.add_error(msg="Different shape",
                         device=name,
                         device_property=test,
                         value=str(arr.shape),
                         expected_value=str(arr_expected.shape))
        return

    if np.allclose(arr, arr_expected, atol=tol):
        return

    if arr.dtype in (np.bool_, bool):
        diff = arr.astype(int) - arr_expected.astype(int)
    else:
        diff = arr - arr_expected

    logger.add_error(msg="Numeric differences",
                     device=name,
                     device_property=test,
                     value=f"min diff: {diff.min()}, max diff: {diff.max()}",
                     expected_value=tol)
