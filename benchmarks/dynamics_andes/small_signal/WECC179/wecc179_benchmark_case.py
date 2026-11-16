# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Construct the WECC179 network and its benchmark RMS models."""

from __future__ import annotations

from pathlib import Path

import andes

from VeraGridEngine.Utils.Symbolic.templates_common_functions import set_rms_model
import VeraGridEngine.api as gce

from benchmarks.dynamics_andes.small_signal.npcc140_wecc179_network_models import assign_standard_network_rms_models
from benchmarks.dynamics_andes.small_signal.WECC179.wecc179_dynamic_model import get_wecc179_generator_rms_template
from benchmarks.dynamics_andes.small_signal.WECC179.wecc179_dynamic_model import load_wecc179_dynamic_tables
from benchmarks.dynamics_andes.small_signal.WECC179.wecc179_dynamic_model import Wecc179DynamicTables


def _base_grid_path() -> Path:
    """Return the ANDES-distributed WECC RAW network path.

    :return: Absolute RAW path.
    """
    return Path(andes.get_case("wecc/wecc.raw")).resolve()


def build_wecc179_rms_benchmark_grid() -> gce.MultiCircuit:
    """Import WECC topology and assign every physical RMS device model.

    :return: RMS-ready WECC grid.
    """
    grid: gce.MultiCircuit = gce.open_file(str(_base_grid_path()))
    assign_standard_network_rms_models(grid=grid, prefix="wecc179")
    dynamic_tables: Wecc179DynamicTables = load_wecc179_dynamic_tables()
    generator_index: int
    for generator_index, generator in enumerate(grid.generators):
        set_rms_model(
            device=generator,
            model=get_wecc179_generator_rms_template(
                vfactory=grid.var_factory,
                generator_index=generator_index,
                system_base=float(grid.Sbase),
                tables=dynamic_tables,
            ).block,
            var_factory=grid.var_factory,
        )
    return grid
