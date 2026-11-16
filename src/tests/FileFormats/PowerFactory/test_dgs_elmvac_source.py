# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Import native AC voltage sources with the same physical PF and RMS circuit."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

import VeraGridEngine.api as gce
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
from VeraGridEngine.IO.dgs.dgs_objects import ElmVac
from VeraGridEngine.IO.dgs.dgs_to_veragrid import _add_elmvac_loads, _add_elmvac_voltage_source
from VeraGridEngine.IO.dgs.dgs_rms_preparation import prepare_dgs_circuit_for_rms
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae import RmsProblemDae
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions
from VeraGridEngine.Simulations.Rms.numerical.back_euler_fx import BackEulerImplicitIntegration
from VeraGridEngine.basic_structures import Logger


def make_source() -> ElmVac:
    """Declare an exported finite voltage source with nontrivial units.

    :return: Voltage source in its native units.
    """
    source: ElmVac = ElmVac()
    source.ID = 'source'
    source.loc_name = 'AC source'
    source.usetp = 1.03
    source.phisetp = 12.0
    source.Unom = 120.0
    source.R1 = 1.0
    source.X1 = 9.0
    source.R0 = 3.0
    source.X0 = 30.0
    source.R2 = 2.0
    source.X2 = 10.0
    source.freq = 50.0
    return source


def test_elmvac_parser_retains_source_fields(tmp_path: Path) -> None:
    """Read physical source fields rather than discarding unregistered columns.

    :param tmp_path: Temporary export directory.
    :return: None.
    """
    path: Path = tmp_path / 'source.dgs'
    path.write_text('$$ElmVac;FID(a:40);itype(i);usetp(r);phisetp(r);R1(r);X1(r);R0(r);X0(r);R2(r);X2(r);Unom(r);freq(r);contbar(p);c_pmod(p)\n'
                    'source;0;1.03;12;1;9;3;30;2;10;120;50;terminal;model\n')
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(path))
    source: ElmVac = circuit.elmvacs[0]
    assert source.usetp == 1.03 and source.phisetp == 12.0
    assert (source.R1, source.X1, source.R0, source.X0, source.R2, source.X2) == (1, 9, 3, 30, 2, 10)
    assert source.Unom == 120.0 and source.freq == 50.0
    assert source.contbar == 'terminal' and source.c_pmod == 'model'


@pytest.mark.parametrize('active', (True, False))
def test_elmvac_impedance_and_boundary_preserve_units_and_service(active: bool) -> None:
    """Keep the terminal distinct from the internal ideal source voltage.

    :param active: Exported source service state.
    :return: None.
    """
    grid: MultiCircuit = MultiCircuit()
    terminal: Bus = Bus(name='Terminal', Vnom=110.0)
    grid.add_bus(terminal)
    source: ElmVac = make_source()
    source.outserv = 0 if active else 1
    _add_elmvac_voltage_source(source, grid, terminal, Logger())
    assert len(grid.buses) == 2 and len(grid.external_grids) == 1 and len(grid.series_reactances) == 1
    assert grid.external_grids[0].active == active
    assert grid.external_grids[0].Vm == pytest.approx(1.03 * 120 / 110)
    assert grid.external_grids[0].Va == pytest.approx(math.radians(12.0))
    assert grid.external_grids[0].bus is not terminal
    assert not terminal.is_slack
    assert grid.external_grids[0].bus.is_slack == active
    assert grid.series_reactances[0].active == active
    assert grid.series_reactances[0].bus_to is terminal
    assert grid.series_reactances[0].R == pytest.approx(1 / 121)
    assert grid.series_reactances[0].X == pytest.approx(9 / 121)
    assert grid.series_reactances[0].X2 == pytest.approx(10 / 121)


def test_elmvac_ideal_source_does_not_manufacture_impedance() -> None:
    """Attach a truly ideal source directly to its physical terminal.

    :return: None.
    """
    grid: MultiCircuit = MultiCircuit()
    terminal: Bus = Bus(Vnom=120.0)
    grid.add_bus(terminal)
    source: ElmVac = make_source()
    source.R1 = 0.0
    source.X1 = 0.0
    _add_elmvac_voltage_source(source, grid, terminal, Logger())
    assert len(grid.buses) == 1 and len(grid.series_reactances) == 0
    assert grid.external_grids[0].bus is terminal


def test_elmvac_source_runs_pf_and_rms_under_load() -> None:
    """Solve a loaded source circuit with real convergence reports and RMS.

    :return: None.
    """
    grid: MultiCircuit = MultiCircuit()
    terminal: Bus = Bus(name='Terminal', Vnom=110.0)
    grid.add_bus(terminal)
    source: ElmVac = make_source()
    _add_elmvac_voltage_source(source, grid, terminal, Logger())
    grid.add_load(terminal, gce.Load(P=10.0, Q=3.0))
    prepare_dgs_circuit_for_rms(grid, set(), Logger())
    pf: gce.PowerFlowResults = gce.power_flow(grid)
    assert len(pf.convergence_reports) > 0 and pf.converged
    assert np.all(np.abs(pf.voltage) > 0.5)
    assert abs(pf.Sf[0]) > 0.0
    assert abs(pf.voltage[0]) < abs(pf.voltage[1])
    problem: RmsProblemDae = RmsProblemDae(grid, RmsOptions(), pf, logger=Logger())
    problem.set_events_group(None)
    solver: BackEulerImplicitIntegration = BackEulerImplicitIntegration(
        problem=problem, t0=0.0, t_end=0.01, h=0.001, max_iter=25)
    times: np.ndarray
    values: np.ndarray
    initialized: bool
    converged: bool
    times, values, initialized, converged = solver.simulate()
    assert initialized and converged
    assert times[-1] == pytest.approx(0.01)
    assert np.all(np.isfinite(values))


def test_elmvac_ward_equivalent_remains_a_load() -> None:
    """Retain existing Ward net power and shunt conversion.

    :return: None.
    """
    source: ElmVac = make_source()
    source.itype = 2
    source.Pload = 10.0
    source.Pgen = 2.0
    source.Qload = 4.0
    source.Qgen = 1.0
    dgs: DgsCircuit = DgsCircuit()
    dgs.elmvacs.append(source)
    grid: MultiCircuit = MultiCircuit()
    terminal: Bus = Bus(Vnom=120.0)
    grid.add_bus(terminal)
    _add_elmvac_loads(dgs, grid, dict(((source.ID, list((0,))),)), Logger(), dict(), dict())
    assert len(grid.loads) == 1 and len(grid.external_grids) == 0
    assert grid.loads[0].P == 8.0 and grid.loads[0].Q == 3.0
