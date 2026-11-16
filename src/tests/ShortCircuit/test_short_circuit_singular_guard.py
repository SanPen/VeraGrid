# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import warnings

import numpy as np
from scipy.sparse import csc_matrix

from VeraGridEngine.Simulations.ShortCircuitStudies.NumericalMethods.short_circuit_sequences import calc_short_circuit_seq_unbalanced
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import FaultType


def test_unbalanced_short_circuit_singular_matrix_logs_error_without_warning() -> None:
    """
    Singular sequence matrices must be reported in the logger, not as SciPy warnings.

    :return: None.
    """
    n: int = 2
    logger: Logger = Logger()
    singular_ybus: csc_matrix = csc_matrix((n, n), dtype=complex)
    vbus: np.ndarray = np.ones(n, dtype=complex)
    vnom: np.ndarray = np.ones(n, dtype=float)
    fault_impedance: np.ndarray = np.zeros(n, dtype=complex)

    with warnings.catch_warnings(record=True) as recorded_warnings:
        warnings.simplefilter("always")
        v0, v1, v2, scc, icc = calc_short_circuit_seq_unbalanced(
            bus_idx=0,
            Y0=singular_ybus,
            Y1=singular_ybus,
            Y2=singular_ybus,
            Vbus=vbus,
            Vnom=vnom,
            Zf=fault_impedance,
            fault_type=FaultType.LG,
            baseMVA=100.0,
            logger=logger,
        )

    assert len(recorded_warnings) == 0
    assert logger.has_errors()
    assert np.all(np.isfinite(v0))
    assert np.all(np.isfinite(v1))
    assert np.all(np.isfinite(v2))
    assert np.all(np.isfinite(scc))
    assert np.all(np.isfinite(icc))
