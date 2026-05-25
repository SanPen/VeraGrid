# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from pathlib import Path
import zipfile

import pandas as pd
import pytest

import VeraGridEngine.Devices as dev
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.IO.file_open import open_ucte
from VeraGridEngine.IO.file_save import save_ucte_batch_zip
from VeraGridEngine.IO.ucte.veragrid_to_ucte import write_ucte
from VeraGridEngine.basic_structures import Logger, LogSeverity


def get_errors(logger: Logger) -> list[str]:
    """
    Extract error messages from one logger.

    :param logger: Logger to inspect.
    :return: Error-message list.
    """
    return [entry.msg for entry in logger.entries if entry.severity == LogSeverity.Error]


def build_export_grid() -> MultiCircuit:
    """
    Build one small AC grid that exercises the supported UCTE export elements.

    :return: MultiCircuit instance.
    """
    grid: MultiCircuit = MultiCircuit(name="ucte-export-grid", Sbase=100.0, fbase=50.0)
    grid.time_profile = pd.to_datetime(["2024-01-01 00:00:00", "2024-01-01 01:00:00"])

    bus_slack: dev.Bus = dev.Bus(name="SlackBus", Vnom=380.0, is_slack=True, Vm0=1.0)
    bus_load: dev.Bus = dev.Bus(name="LoadBus", Vnom=380.0, Vm0=1.0)
    bus_switch: dev.Bus = dev.Bus(name="SwitchBus", Vnom=380.0, Vm0=1.0)
    bus_low: dev.Bus = dev.Bus(name="LowBus", Vnom=220.0, Vm0=1.0)
    grid.add_bus(obj=bus_slack)
    grid.add_bus(obj=bus_load)
    grid.add_bus(obj=bus_switch)
    grid.add_bus(obj=bus_low)

    generator: dev.Generator = dev.Generator(name="GenSlack",
                                             P=50.0,
                                             Q=1.0,
                                             Pmin=0.0,
                                             Pmax=120.0,
                                             Qmin=-20.0,
                                             Qmax=20.0,
                                             vset=1.0,
                                             is_controlled=True)
    generator.P_prof = pd.Series([50.0, 60.0]).to_numpy()
    generator.Q_prof = pd.Series([1.0, 2.0]).to_numpy()
    generator.Vset_prof = pd.Series([1.0, 1.02]).to_numpy()
    grid.add_generator(bus=bus_slack, api_obj=generator)

    load: dev.Load = dev.Load(name="LoadBusLoad", P=10.0, Q=5.0)
    load.P_prof = pd.Series([10.0, 20.0]).to_numpy()
    load.Q_prof = pd.Series([5.0, 6.0]).to_numpy()
    grid.add_load(bus=bus_load, api_obj=load)

    shunt: dev.Shunt = dev.Shunt(name="LoadBusShunt", G=0.0, B=50.0)
    grid.add_shunt(bus=bus_load, api_obj=shunt)

    line: dev.Line = dev.Line(bus_from=bus_slack,
                              bus_to=bus_load,
                              name="L1",
                              r=0.01,
                              x=0.05,
                              b=0.02,
                              rate=200.0)
    grid.add_line(obj=line)

    switch_obj: dev.Switch = dev.Switch(bus_from=bus_load,
                                        bus_to=bus_switch,
                                        name="SW1",
                                        rated_current=3.0,
                                        active=True)
    grid.add_switch(obj=switch_obj)

    transformer: dev.Transformer2W = dev.Transformer2W(bus_from=bus_load,
                                                       bus_to=bus_low,
                                                       name="TR1",
                                                       HV=380.0,
                                                       LV=220.0,
                                                       nominal_power=150.0,
                                                       r=0.01,
                                                       x=0.08,
                                                       g=0.0,
                                                       b=0.01,
                                                       rate=150.0,
                                                       tap_module=1.0)
    grid.add_transformer2w(obj=transformer)

    return grid


def test_write_ucte_exports_one_parseable_profile_point(tmp_path: Path) -> None:
    """
    Export one time-series point to UCTE and verify the importer sees the same state.

    :param tmp_path: Pytest temporary directory.
    :return: None.
    """
    grid: MultiCircuit = build_export_grid()
    export_path: Path = tmp_path / "grid_t1.uct"
    export_logger: Logger = Logger()

    write_ucte(file_name=str(export_path), circuit=grid, t_idx=1, logger=export_logger)

    imported_logger: Logger = Logger()
    imported_grid: MultiCircuit = open_ucte(str(export_path), logger=imported_logger)

    assert export_path.exists()
    assert imported_grid.get_bus_number() == 4
    assert imported_grid.get_lines_number() == 1
    assert imported_grid.get_switches_number() == 1
    assert imported_grid.get_transformers2w_number() == 1
    assert imported_grid.get_shunts_number() == 1
    assert imported_grid.get_generators_number() == 1
    assert imported_grid.get_loads_number() == 1

    imported_generator: dev.Generator = imported_grid.get_generators()[0]
    imported_load: dev.Load = imported_grid.get_loads()[0]
    imported_shunt: dev.Shunt = imported_grid.get_shunts()[0]

    assert imported_generator.P == pytest.approx(60.0)
    assert imported_generator.Q == pytest.approx(2.0)
    assert imported_load.P == pytest.approx(20.0)
    assert imported_load.Q == pytest.approx(6.0)
    assert imported_shunt.B == pytest.approx(50.0)
    assert get_errors(imported_logger) == []


def test_save_ucte_batch_zip_exports_all_profile_points(tmp_path: Path) -> None:
    """
    Export every profile point to one ZIP package and verify both members.

    :param tmp_path: Pytest temporary directory.
    :return: None.
    """
    grid: MultiCircuit = build_export_grid()
    zip_path: Path = tmp_path / "grid_profiles.zip"
    logger: Logger = save_ucte_batch_zip(circuit=grid, file_name=str(zip_path))

    assert zip_path.exists()
    assert get_errors(logger) == []

    with zipfile.ZipFile(zip_path, "r") as zip_pointer:
        member_names: list[str] = sorted(zip_pointer.namelist())
        assert len(member_names) == 2

        first_path: Path = tmp_path / member_names[0]
        second_path: Path = tmp_path / member_names[1]
        first_path.write_bytes(zip_pointer.read(member_names[0]))
        second_path.write_bytes(zip_pointer.read(member_names[1]))

    first_grid: MultiCircuit = open_ucte(str(first_path), logger=Logger())
    second_grid: MultiCircuit = open_ucte(str(second_path), logger=Logger())

    assert first_grid.get_loads()[0].P == pytest.approx(10.0)
    assert second_grid.get_loads()[0].P == pytest.approx(20.0)
