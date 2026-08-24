# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os
import numpy as np
import VeraGridEngine.api as gce
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.Simulations.LinearFactors.linear_analysis import make_acdc_ptdf
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import ConverterControlType


def build_ptdf(grid: gce.MultiCircuit, converters_as_setpoint: bool) -> np.ndarray:
    """
    Compile the grid and build its AC-DC PTDF.

    :param grid: grid with at least one DC bus
    :param converters_as_setpoint: forwarded to make_acdc_ptdf
    :return: PTDF matrix
    """
    nc = compile_numerical_circuit_at(grid, t_idx=None)
    return make_acdc_ptdf(nc=nc,
                          logger=Logger(),
                          bus_types=nc.bus_data.bus_types,
                          distribute_slack=False,
                          converters_as_setpoint=converters_as_setpoint)


def flip_droop_to_free(grid: gce.MultiCircuit) -> int:
    """
    Turn every P-mode 3 (angle droop) VSC of the grid into a free-power one.

    :param grid: grid to modify in place
    :return: number of converters flipped
    """
    n_flipped: int = 0
    for v in grid.vsc_devices:
        if v.control1 == ConverterControlType.Pdc_angle_droop:
            v.control2 = ConverterControlType.Pdc
            v.control2_val = 0.0
            v.control1 = ConverterControlType.Pac
            v.control1_val = 0.0
            v.control1_dev = None
            assert (v.control1, v.control2) == (ConverterControlType.Pac,
                                                ConverterControlType.Pdc)
            n_flipped += 1
        else:
            pass  # not a droop converter
    return n_flipped


def test_acdc_ptdf_droop_response_is_kept_by_default() -> None:
    """
    The default AC-DC PTDF must model droop converters with their droop constant
    """
    fname = os.path.join('data', 'grids', 'NTC_8_bus_2pmode3_dc_bottleneck.veragrid')
    grid_droop = gce.open_file(fname)
    grid_free = gce.open_file(fname)
    n_flipped = flip_droop_to_free(grid_free)
    assert n_flipped > 0, "the fixture must contain droop converters"

    ptdf_droop = build_ptdf(grid_droop, converters_as_setpoint=False)
    ptdf_free = build_ptdf(grid_free, converters_as_setpoint=False)

    assert np.max(np.abs(ptdf_droop - ptdf_free)) > 1e-3, \
        "the default PTDF lost the droop response, so droop and free builds are identical"


def test_acdc_ptdf_setpoint_flag_is_control_mode_independent() -> None:
    """
    With converters_as_setpoint=True the AC-DC PTDF must be identical regardless of the
    converter control modes
    """
    fname = os.path.join('data', 'grids', 'NTC_8_bus_2pmode3_dc_bottleneck.veragrid')
    grid_droop = gce.open_file(fname)
    grid_free = gce.open_file(fname)
    n_flipped = flip_droop_to_free(grid_free)
    assert n_flipped > 0, "the fixture must contain droop converters"

    ptdf_droop = build_ptdf(grid_droop, converters_as_setpoint=True)
    ptdf_free = build_ptdf(grid_free, converters_as_setpoint=True)

    assert np.allclose(ptdf_droop, ptdf_free, atol=1e-12), \
        "converters_as_setpoint must make the PTDF independent of the control mode"
