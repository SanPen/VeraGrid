# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Construct the NPCC140 network and its benchmark RMS models."""

from __future__ import annotations

from pathlib import Path

import andes

from VeraGridEngine.Utils.Symbolic.templates_common_functions import set_rms_model
import VeraGridEngine.api as gce

from benchmarks.dynamics_andes.small_signal.NPCC140.npcc140_dynamic_model import get_npcc140_generator_rms_template
from benchmarks.dynamics_andes.small_signal.NPCC140.npcc140_dynamic_model import load_npcc140_dynamic_tables
from benchmarks.dynamics_andes.small_signal.NPCC140.npcc140_dynamic_model import Npcc140DynamicTables
from benchmarks.dynamics_andes.small_signal.npcc140_wecc179_network_models import assign_standard_network_rms_models


def _base_grid_path() -> Path:
    """Return the ANDES-distributed NPCC RAW network path.

    :return: Absolute RAW path.
    """
    return Path(andes.get_case("npcc/npcc.raw")).resolve()


def _remove_raw_line_virtual_taps(grid: gce.MultiCircuit) -> None:
    """Match the ANDES NPCC branch convention for nominal-voltage aliases.

    Several NPCC RAW line endpoints use 220 kV and 230 kV labels while the
    ANDES ``Line`` records retain ``tap=1``. VeraGrid correctly interprets a
    nominal-voltage mismatch as an implicit virtual tap for a general RAW case,
    but that is not the convention of this benchmark. Buses joined by ordinary
    lines are therefore assigned one component nominal voltage; transformer
    winding ratings are then aligned with their oriented endpoint buses so every
    implicit virtual tap is exactly one, matching the ANDES admittance matrix.

    :param grid: Imported NPCC RAW grid.
    :return: None.
    """
    bus_index_by_idtag: dict[str, int] = dict()
    bus_index: int
    for bus_index, bus in enumerate(grid.buses):
        bus_index_by_idtag[bus.idtag] = bus_index
    component_ids: list[int] = list(range(len(grid.buses)))
    for line in grid.lines:
        from_index: int = bus_index_by_idtag[line.bus_from.idtag]
        to_index: int = bus_index_by_idtag[line.bus_to.idtag]
        from_component: int = component_ids[from_index]
        to_component: int = component_ids[to_index]
        if from_component == to_component:
            pass
        else:
            retained_component: int = min(from_component, to_component)
            replaced_component: int = max(from_component, to_component)
            replacement_index: int
            for replacement_index in range(len(component_ids)):
                if component_ids[replacement_index] == replaced_component:
                    component_ids[replacement_index] = retained_component
                else:
                    pass
    component_nominal_voltage: dict[int, float] = dict()
    for bus_index, bus in enumerate(grid.buses):
        component_index: int = component_ids[bus_index]
        current_voltage: float = component_nominal_voltage.get(component_index, 0.0)
        component_nominal_voltage[component_index] = max(current_voltage, float(bus.Vnom))
    for bus_index, bus in enumerate(grid.buses):
        bus.Vnom = component_nominal_voltage[component_ids[bus_index]]
    for transformer in grid.transformers2w:
        # ``HV`` and ``LV`` are the oriented winding ratings consumed by the RMS
        # template. Their names do not imply that the RAW from side is always
        # the higher-voltage side.
        transformer.HV = float(transformer.bus_from.Vnom)
        transformer.LV = float(transformer.bus_to.Vnom)


def _match_andes_branch_regularization(grid: gce.MultiCircuit) -> None:
    """Apply the explicit ANDES ``r+1e-8`` and ``x+1e-8`` convention.

    :param grid: NPCC benchmark grid.
    :return: None.
    """
    for line in grid.lines:
        line.R = float(line.R) + 1.0e-8
        line.X = float(line.X) + 1.0e-8
    for transformer in grid.transformers2w:
        transformer.R = float(transformer.R) + 1.0e-8
        transformer.X = float(transformer.X) + 1.0e-8


def _match_andes_parallel_generator_reactive_allocation(
    grid: gce.MultiCircuit,
) -> None:
    """Match the RAW reactive-power split of co-located generators.

    ANDES retains the RAW generator reactive-power proportions when multiple
    voltage-controlling generators share one bus. VeraGrid allocates the bus
    reactive requirement using each generator's available range. The NPCC RAW
    file uses unequal placeholder limits for otherwise equivalent units, so the
    default allocation changes their individual dynamic operating points even
    though the aggregate bus power flow is identical. Symmetric ranges weighted
    by active power recover the RAW proportions used by this benchmark.

    :param grid: Imported NPCC RAW grid.
    :return: None.
    """
    generator_count_by_bus: dict[str, int] = dict()
    for generator in grid.generators:
        bus_idtag: str = generator.bus.idtag
        generator_count: int | None = generator_count_by_bus.get(bus_idtag, None)
        if generator_count is None:
            generator_count_by_bus[bus_idtag] = 1
        else:
            generator_count_by_bus[bus_idtag] = generator_count + 1
    for generator in grid.generators:
        if generator_count_by_bus[generator.bus.idtag] > 1:
            reactive_weight: float = max(abs(float(generator.P)), 1.0e-6)
            generator.Qmin = -reactive_weight
            generator.Qmax = reactive_weight
        else:
            pass


def build_npcc140_rms_benchmark_grid() -> gce.MultiCircuit:
    """Import NPCC topology and assign every physical RMS device model.

    :return: RMS-ready NPCC grid.
    """
    grid: gce.MultiCircuit = gce.open_file(str(_base_grid_path()))
    _remove_raw_line_virtual_taps(grid)
    _match_andes_branch_regularization(grid)
    _match_andes_parallel_generator_reactive_allocation(grid)
    assign_standard_network_rms_models(grid=grid, prefix="npcc140")
    dynamic_tables: Npcc140DynamicTables = load_npcc140_dynamic_tables()
    generator_index: int
    for generator_index, generator in enumerate(grid.generators):
        set_rms_model(
            device=generator,
            model=get_npcc140_generator_rms_template(
                vfactory=grid.var_factory,
                generator_index=generator_index,
                system_base=float(grid.Sbase),
                tables=dynamic_tables,
            ).block,
            var_factory=grid.var_factory,
        )
    return grid
