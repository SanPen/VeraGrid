"""Helpers to convert stored branch matrices into EMT line matrices."""

from __future__ import annotations

from typing import Any, Tuple

import numpy as np


def build_physical_line_matrices_from_stored_admittances(
        line: Any,
        sbase_mva: float,
) -> Tuple[np.ndarray | None, np.ndarray | None]:
    """
    Reconstruct physical total-line ``Z`` and ``Y`` matrices from stored branch data.

    The saved line object keeps ``line.ys`` as the total per-unit series admittance
    matrix and ``line.ysh`` as the total per-unit shunt admittance matrix. Static
    EMT pi-line mapping needs the corresponding physical total-line impedance and
    shunt-admittance matrices. This helper performs that inverse conversion so EMT
    builders can consume persisted matrices instead of recomputing the original line
    template Carson data.

    :param line: Line-like branch device.
    :param sbase_mva: System base power in MVA.
    :return: Tuple ``(z_phys_total, y_phys_total)`` in physical units, or
        ``(None, None)`` when the stored matrices are unavailable.
    """
    if line.ys is None or line.ysh is None:
        return None, None
    else:
        pass

    voltage_base_volt: float = float(line.bus_from.Vnom) * 1.0e3
    sbase_va: float = float(sbase_mva) * 1.0e6
    zbase_ohm: float = (voltage_base_volt * voltage_base_volt) / sbase_va
    ybase_siemens: float = 1.0 / zbase_ohm
    ys_matrix_pu: np.ndarray = np.asarray(line.ys.values, dtype=np.complex128)
    ysh_matrix_pu: np.ndarray = np.asarray(line.ysh.values, dtype=np.complex128)
    ys_matrix_phys: np.ndarray = ys_matrix_pu * ybase_siemens
    # Persisted overhead-line shunt data carries the historical ``1e6`` scaling
    # introduced by ``OverheadLineType.get_ysh()``. Recovering the physical total
    # shunt admittance therefore requires dividing by that same factor.
    ysh_matrix_phys: np.ndarray = (ysh_matrix_pu * ybase_siemens) / 1.0e6

    try:
        z_phys_total: np.ndarray = np.linalg.inv(ys_matrix_phys)
    except np.linalg.LinAlgError:
        z_phys_total = np.linalg.pinv(ys_matrix_phys)

    return z_phys_total, ysh_matrix_phys


def build_overhead_line_per_length_shunt_matrix_from_stored_admittances(
        line: Any,
        sbase_mva: float,
) -> np.ndarray | None:
    """
    Recover the overhead-line shunt matrix in physical ``S/km`` from ``line.ysh``.

    Overhead-line templates store ``template.y_nabc`` in ``S/km``. The persisted
    line object converts that matrix to total per-unit shunt admittance using an
    additional ``1e6`` factor. Bergeron still needs the original per-length physical
    representation, so this helper reverses that exact storage convention.

    :param line: Line-like branch device.
    :param sbase_mva: System base power in MVA.
    :return: Shunt admittance matrix in physical ``S/km`` or ``None``.
    """
    if line.ysh is None:
        return None
    else:
        pass

    voltage_base_volt: float = float(line.bus_from.Vnom) * 1.0e3
    sbase_va: float = float(sbase_mva) * 1.0e6
    zbase_ohm: float = (voltage_base_volt * voltage_base_volt) / sbase_va
    ybase_siemens: float = 1.0 / zbase_ohm
    ysh_matrix_pu: np.ndarray = np.asarray(line.ysh.values, dtype=np.complex128)
    ysh_matrix_phys_km: np.ndarray = (ysh_matrix_pu * ybase_siemens) / 1.0e6
    return ysh_matrix_phys_km
