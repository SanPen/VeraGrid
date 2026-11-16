# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os

import pytest
from pathlib import Path
import pandas as pd
import numpy as np
from types import SimpleNamespace

import VeraGridEngine.Devices as dev
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.file_open import FileOpen
from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
from VeraGridEngine.IO.dgs.dgs_objects import ElmGenstat, ElmSind, ElmLne, ElmLnesec, ElmSvs, ElmTerm, TypTr2
from VeraGridEngine.IO.dgs.dgs_to_veragrid import (_add_elmgenstat_devices, _apply_elmtow_tower_coupling,
                                                  convert_dgs_svs_to_droop_shunt, convert_dgs_to_line)
from VeraGridEngine.enumerations import (DeviceType, GeneratorControlMode, ShuntConnectionType, ShuntControlMode,
                                         StaticGeneratorControlMode, ConverterControlType, TapChangerTypes,
                                         TapModuleControl)
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.Simulations.PowerFlow3ph.Formulations.positive_sequence_control import PositiveSequenceControl
from VeraGridEngine.Simulations.PowerFlow.power_flow_worker import PowerFlowOptions
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import SolverType
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowDriver
from VeraGridEngine.IO.dgs.veragrid_to_dgs import circuit_to_dgs


@pytest.mark.parametrize("parallel_count", (1, 2))
@pytest.mark.parametrize(
    "category,control_mode,use_vsc,out_of_service,expected_device",
    (("Wind", "constv", False, False, DeviceType.GeneratorDevice),
     ("Wind", "constv", False, True, DeviceType.GeneratorDevice),
     ("Other", "constv", False, False, DeviceType.GeneratorDevice),
     ("Wind", "constq", False, False, DeviceType.StaticGeneratorDevice),
     ("Wind", "constq", True, False, DeviceType.VscDevice),
     ("Wind", "constv", True, False, DeviceType.VscDevice),
     ("Storage", "vdroop", False, False, DeviceType.StaticGeneratorDevice),
     ("Storage", "vdroop", False, True, DeviceType.StaticGeneratorDevice),
     ("Storage", "vdroop", True, False, DeviceType.VscDevice),
     ("Storage", "vdroop", True, True, DeviceType.VscDevice),
     ("Storage", "constq", False, False, DeviceType.BatteryDevice),
     ("Storage", "constq", True, False, DeviceType.BatteryDevice)),
)
def test_dgs_static_generator_voltage_control_mapping(
        category: str, control_mode: str, use_vsc: bool, out_of_service: bool,
        expected_device: DeviceType, parallel_count: int,
) -> None:
    """Preserve PV and storage droop while respecting explicit VSC selection.

    :param category: Technology label in the DGS element.
    :param control_mode: Native PowerFactory voltage/reactive-power mode.
    :param use_vsc: Explicit converter import option.
    :param out_of_service: Source element availability.
    :param expected_device: Expected VeraGrid device category.
    :param parallel_count: Number of units represented by the source element.
    :return: None.
    """
    # Exercise real DGS objects and existing converters, with synthetic public data.
    dgs_grid: DgsCircuit = DgsCircuit()
    source: ElmGenstat = ElmGenstat()
    source.ID = "wind-generator"
    source.loc_name = "Wind generator"
    source.cCategory = category
    source.av_mode = control_mode
    source.outserv = int(out_of_service)
    source.ngnum = parallel_count
    source.pgini = 19.2
    source.qgini = 2.5
    source.sgn = 50.0
    source.usetp = 1.01
    source.ddroop, source.usp_min, source.usp_max = 2.5, 0.92, 1.08
    source.phtech, source.nneutral = 1, 0
    source.r0, source.x0, source.r2, source.x2 = 0.01, 0.08, 0.02, 0.10
    dgs_grid.elmgenstats.append(source)
    grid: dev.MultiCircuit = dev.MultiCircuit()
    bus: dev.Bus = grid.add_bus(dev.Bus(name="Terminal", Vnom=33.0))
    _add_elmgenstat_devices(
        dgs_grid=dgs_grid, grid=grid,
        stacubic_dict=dict(((source.ID, list((0,))),)),
        use_vsc_for_injections=use_vsc, logger=Logger(),
        cubics_by_objid=dict(), bus_by_term_id=dict(),
    )

    # Only the requested representation is created, including parallel units and state.
    devices: list[dev.Generator | dev.StaticGenerator | dev.VSC] = list(
        grid.get_elements_by_type(device_type=expected_device)
    )
    assert len(devices) == parallel_count
    assert (len(grid.generators) + len(grid.static_generators) + len(grid.vsc_devices)
            + len(grid.batteries)) == parallel_count
    assert len(grid.buses) == 1 + (parallel_count if expected_device == DeviceType.VscDevice else 0)
    assert len(set(device.idtag for device in devices)) == parallel_count
    device: dev.Generator | dev.StaticGenerator | dev.VSC
    for device in devices:
        assert device.active == (not out_of_service)
        if isinstance(device, dev.Battery):
            assert device.bus is bus
            assert device.P == source.pgini and device.Q == source.qgini
            assert device.control_mode == GeneratorControlMode.Q
        elif isinstance(device, dev.Generator):
            assert device.bus is bus
            assert device.P == source.pgini and device.Snom == source.sgn
            assert device.control_mode == GeneratorControlMode.V
            assert device.Vset == source.usetp
        elif isinstance(device, dev.StaticGenerator):
            assert device.bus is bus
            assert device.P == source.pgini and device.Q == source.qgini
            if category == 'Storage' and control_mode == 'vdroop':
                assert device.control_mode == StaticGeneratorControlMode.QVDroop
                assert device.Snom == source.sgn and device.Vset == source.usetp
                assert device.droop == source.ddroop
                assert device.Vset_min == source.usp_min and device.Vset_max == source.usp_max
                assert device.conn == ShuntConnectionType.GroundedStar
                np.testing.assert_allclose((device.R0, device.X0, device.R2, device.X2),
                    np.array((source.r0, source.x0, source.r2, source.x2)) * grid.Sbase / source.sgn)
            else:
                assert device.control_mode == StaticGeneratorControlMode.PQ
        else:
            assert device.bus_to is bus
            assert device.bus_from.is_dc
            if control_mode == 'vdroop':
                assert device.control1 == ConverterControlType.Pac
                assert device.control2 == ConverterControlType.Q_droop
                assert device.control1_val == -source.pgini and device.control2_val == -source.qgini
                assert device.control2_val_droop == source.ddroop
                assert device.control2_droop_val == source.usetp
                assert device.control2_droop_val_min == source.usp_min
                assert device.control2_droop_val_max == source.usp_max
            else:
                pass


@pytest.mark.parametrize("Sbase,parallel_count", ((100.0, 1), (25.0, 2)))
@pytest.mark.parametrize("technology,neutral,connection",
                         ((0, 0, ShuntConnectionType.FloatingStar),
                          (1, 0, ShuntConnectionType.GroundedStar),
                          (1, 1, ShuntConnectionType.NeutralStar),
                          (1, 2, ShuntConnectionType.NeutralStar),
                          (1, None, None), (None, None, None), (2, 0, None)))
def test_dgs_generator_sequence_connection_and_bases(
        tmp_path: Path, Sbase: float, parallel_count: int, technology: int | None,
        neutral: int | None, connection: ShuntConnectionType | None,
) -> None:
    """Respect the exported return path and each parallel machine's power base.

    :param tmp_path: Isolated DGS round-trip directory.
    :param Sbase: Network power base in MVA.
    :param parallel_count: Number of identical machines exported in one element.
    :param technology: PowerFactory phase technology, or an absent export field.
    :param neutral: PowerFactory neutral connection, or an absent export field.
    :param connection: Expected physical connection, or missing/unsupported source data.
    :return: None.
    """
    source: ElmGenstat = ElmGenstat()
    source.ID = "sequence-generator"
    source.loc_name = "Sequence generator"
    source.cCategory = "Wind"
    source.av_mode = "constv"
    source.phtech = technology
    source.nneutral = neutral
    source.sgn = 50.0
    source.ngnum = parallel_count
    source.r0, source.x0 = 0.0, 0.10
    source.r2, source.x2 = 0.01, 0.15
    exported: DgsCircuit = DgsCircuit()
    exported.elmgenstats.append(source)
    path: Path = tmp_path / "generator_sequences.dgs"
    exported.write_dgs(path=str(path))
    imported: DgsCircuit = DgsCircuit()
    imported.parse_dgs(path=str(path))
    assert imported.elmgenstats[0].phtech == technology
    assert imported.elmgenstats[0].nneutral == neutral
    assert imported.elmgenstats[0].r0 == 0.0

    grid: dev.MultiCircuit = dev.MultiCircuit(Sbase=Sbase)
    grid.add_bus(dev.Bus(name="Terminal", Vnom=33.0))
    logger: Logger = Logger()
    _add_elmgenstat_devices(
        dgs_grid=imported, grid=grid,
        stacubic_dict=dict(((source.ID, list((0,))),)),
        use_vsc_for_injections=False, logger=logger,
        cubics_by_objid=dict(), bus_by_term_id=dict(),
    )
    assert len(grid.generators) == parallel_count
    gen: dev.Generator
    for gen in grid.generators:
        if connection is not None:
            assert gen.conn == connection
            assert complex(gen.R2, gen.X2) == pytest.approx(complex(0.01, 0.15) * Sbase / 50.0)
            # A blocked connection retains its data without activating a return path.
            assert complex(gen.R0, gen.X0) == pytest.approx(0.10j * Sbase / 50.0)
        else:
            assert len(logger.entries) > 0
    numerical: NumericalCircuit = compile_numerical_circuit_at(circuit=grid, fill_three_phase=True)
    if connection is None or connection == ShuntConnectionType.NeutralStar:
        # Invalid source data or an explicit neutral must never become an implicit ground.
        with pytest.raises(ValueError, match='finite and nonzero|explicit neutral'):
            PositiveSequenceControl(numerical, np.arange(4))
    else:
        controls: PositiveSequenceControl = PositiveSequenceControl(numerical, np.arange(4))
        assert len(controls.bus_idx) == 1


@pytest.mark.parametrize("r0,x0,r2,x2,sgn,valid_zero,valid_negative",
                         ((None, None, None, None, 50.0, False, False),
                          (0.0, None, None, 0.15, 50.0, False, False),
                          (0.0, 0.0, 0.0, 0.0, 50.0, False, False),
                          (np.nan, 0.1, 0.01, np.inf, 50.0, False, False),
                          (0.0, 0.1, 0.01, 0.15, 0.0, False, False),
                          (0.0, 0.1, None, None, 50.0, True, False),
                          (None, None, 0.01, 0.15, 50.0, False, True)))
def test_dgs_missing_or_invalid_generator_sequences(
        r0: float | None, x0: float | None, r2: float | None, x2: float | None,
        sgn: float, valid_zero: bool, valid_negative: bool,
) -> None:
    """Report missing data and reject an incomplete U1 model before solving.

    :param r0: Optional zero-sequence resistance.
    :param x0: Optional zero-sequence reactance.
    :param r2: Optional negative-sequence resistance.
    :param x2: Optional negative-sequence reactance.
    :param sgn: Machine base in MVA.
    :param valid_zero: Whether usable Z0 data were exported.
    :param valid_negative: Whether usable Z2 data were exported.
    :return: None.
    """
    source: ElmGenstat = ElmGenstat()
    source.ID = "incomplete-generator"
    source.av_mode = "constv"
    source.phtech, source.nneutral = 1, 0
    source.sgn = sgn
    source.r0, source.x0, source.r2, source.x2 = r0, x0, r2, x2
    dgs_grid: DgsCircuit = DgsCircuit()
    dgs_grid.elmgenstats.append(source)
    grid: dev.MultiCircuit = dev.MultiCircuit()
    grid.add_bus(dev.Bus(name="Terminal", Vnom=33.0))
    logger: Logger = Logger()
    _add_elmgenstat_devices(
        dgs_grid=dgs_grid, grid=grid,
        stacubic_dict=dict(((source.ID, list((0,))),)),
        use_vsc_for_injections=False, logger=logger,
        cubics_by_objid=dict(), bus_by_term_id=dict(),
    )
    gen: dev.Generator = grid.generators[0]
    assert bool(abs(complex(gen.R0, gen.X0)) >= 1e-12) == valid_zero
    assert bool(abs(complex(gen.R2, gen.X2)) >= 1e-12) == valid_negative
    assert len(logger.entries) > 0
    numerical: NumericalCircuit = compile_numerical_circuit_at(circuit=grid, fill_three_phase=True)
    with pytest.raises(ValueError, match='finite and nonzero'):
        PositiveSequenceControl(numerical, np.arange(4))


def test_elm_sind_writer_preserves_resistance_envelope(
        tmp_path: Path,
) -> None:
    """Preserve legacy and enriched ``ElmSind.s:Rin`` table semantics.

    :param tmp_path: Isolated directory for generated DGS files.
    :return: None.
    """
    legacy_circuit: DgsCircuit = DgsCircuit()
    legacy_element: ElmSind = ElmSind()
    legacy_element.ID = "legacy-series-impedance"
    legacy_circuit.elmsinds.append(legacy_element)
    legacy_path: Path = tmp_path / "legacy_elm_sind.dgs"
    legacy_circuit.write_dgs(path=str(legacy_path))
    legacy_text: str = legacy_path.read_text(encoding="utf-8")
    assert "s:Rin(r)" not in legacy_text

    legacy_roundtrip: DgsCircuit = DgsCircuit()
    legacy_roundtrip.parse_dgs(path=str(legacy_path))
    assert len(legacy_roundtrip.elmsinds) == 1
    assert not legacy_roundtrip.elmsinds[0].initial_resistance_column_declared
    assert legacy_roundtrip.elmsinds[0].Rin is None

    enriched_circuit: DgsCircuit = DgsCircuit()
    enriched_element: ElmSind = ElmSind()
    enriched_element.ID = "enriched-series-impedance"
    enriched_element.Rin = 99999.0
    enriched_element.initial_resistance_column_declared = True
    enriched_circuit.elmsinds.append(enriched_element)
    enriched_path: Path = tmp_path / "enriched_elm_sind.dgs"
    enriched_circuit.write_dgs(path=str(enriched_path))
    enriched_text: str = enriched_path.read_text(encoding="utf-8")
    assert "s:Rin(r)" in enriched_text

    enriched_roundtrip: DgsCircuit = DgsCircuit()
    enriched_roundtrip.parse_dgs(path=str(enriched_path))
    assert len(enriched_roundtrip.elmsinds) == 1
    assert enriched_roundtrip.elmsinds[0].initial_resistance_column_declared
    assert enriched_roundtrip.elmsinds[0].Rin == 99999.0

    mixed_circuit: DgsCircuit = DgsCircuit()
    mixed_legacy_element: ElmSind = ElmSind()
    mixed_legacy_element.ID = "mixed-legacy-series-impedance"
    mixed_enriched_element: ElmSind = ElmSind()
    mixed_enriched_element.ID = "mixed-enriched-series-impedance"
    mixed_enriched_element.Rin = 99999.0
    mixed_enriched_element.initial_resistance_column_declared = True
    mixed_circuit.elmsinds.append(mixed_legacy_element)
    mixed_circuit.elmsinds.append(mixed_enriched_element)
    mixed_path: Path = tmp_path / "mixed_elm_sind.dgs"
    with pytest.raises(ValueError):
        mixed_circuit.write_dgs(path=str(mixed_path))
    assert not mixed_path.exists()

def test_dgs_ieee_grids() -> None:
    """Validate DGS IEEE grids against their tracked power-flow results."""
    files: list[tuple[str, str]] = [
        ('IEEE14_test.dgs', 'IEEE 14 bus.sav.xlsx'),
        ('IEEE30_test.dgs', 'IEEE 30 bus.sav.xlsx'),
        ('IEEE118_v2_test.dgs', 'IEEE 118 Bus.sav.xlsx'),
    ]

    data_dir: Path = Path(__file__).resolve().parents[2] / "data"
    solver_types: tuple[SolverType, ...] = (
        SolverType.NR,
        SolverType.IWAMOTO,
        SolverType.LM,
        SolverType.FASTDECOUPLED,
        SolverType.PowellDogLeg,
        SolverType.HELM,
    )
    solver_type: SolverType
    for solver_type in solver_types:

        options: PowerFlowOptions = PowerFlowOptions(
            solver_type,
            verbose=0,
            control_q=False,
            retry_with_other_methods=False,
        )

        f1: str
        f2: str
        for f1, f2 in files:
            fname: Path = data_dir / "grids" / "DGS" / f1
            main_circuit: dev.MultiCircuit = FileOpen(str(fname)).open()
            power_flow: PowerFlowDriver = PowerFlowDriver(main_circuit, options)
            power_flow.run()

            results_file: Path = data_dir / "results" / f2
            df_v: pd.DataFrame = pd.read_excel(
                results_file,
                sheet_name='Vabs',
                index_col=0,
            )
            df_p: pd.DataFrame = pd.read_excel(
                results_file,
                sheet_name='Pbranch',
                index_col=0,
            )

            v_gc: np.ndarray = np.abs(power_flow.results.voltage)
            v_psse: np.ndarray = df_v.values[:, 0]
            p_gc: np.ndarray = power_flow.results.Sf.real
            p_psse: np.ndarray = df_p.values[:, 0]

            v_ok: bool = bool(np.allclose(v_gc, v_psse, atol=1e-4))
            flow_ok: bool = bool(np.allclose(p_gc, p_psse, atol=1e-2))

            assert v_ok
            assert flow_ok

        print(solver_type, 'ok')

def test_roundtrip_raw_to_dgs_to_dgs_ieee_grids(tmp_path: Path) -> None:
    """Compare power-flow results before and after a RAW-to-DGS roundtrip.

    :param tmp_path: Isolated pytest directory for generated DGS exports.
    :return: None.
    """
    files: list[tuple[str, str]] = [
        ('IEEE 14 bus.raw', 'IEEE 14 bus.sav.xlsx'),
        ('IEEE 30 bus.raw', 'IEEE 30 bus.sav.xlsx'),
        ('IEEE 118 Bus v2.raw', 'IEEE 118 Bus.sav.xlsx'),
    ]
    data_dir: Path = Path(__file__).resolve().parents[2] / "data"
    out_dir: Path = tmp_path / "dgs_roundtrip"
    out_dir.mkdir()
    solver_types: tuple[SolverType, ...] = (
        SolverType.NR,
        SolverType.IWAMOTO,
        SolverType.LM,
        SolverType.FASTDECOUPLED,
        SolverType.PowellDogLeg,
        SolverType.HELM,
    )
    solver_type: SolverType
    for solver_type in solver_types:

        options: PowerFlowOptions = PowerFlowOptions(
            solver_type,
            verbose=0,
            control_q=False,
            retry_with_other_methods=False,
        )

        f1: str
        unused_result_file: str
        for f1, unused_result_file in files:
            raw_path: Path = data_dir / "grids" / "RAW" / f1
            main_circuit: dev.MultiCircuit = FileOpen(str(raw_path)).open()

            pf1: PowerFlowDriver = PowerFlowDriver(main_circuit, options)
            pf1.run()

            v1: np.ndarray = np.abs(pf1.results.voltage)
            p1: np.ndarray = pf1.results.Sf.real

            # export to dgs (same logic as FileHandler.save_dgs)
            dgs_path: Path = out_dir / f1.replace(
                '.raw',
                f'__{solver_type.name}.dgs',
            )
            dgs: DgsCircuit = circuit_to_dgs(grid=main_circuit)
            dgs.write_dgs(path=str(dgs_path))

            # import the same dgs and run again
            rt_circuit: dev.MultiCircuit = FileOpen(str(dgs_path)).open()

            pf2: PowerFlowDriver = PowerFlowDriver(rt_circuit, options)
            pf2.run()

            v2: np.ndarray = np.abs(pf2.results.voltage)
            p2: np.ndarray = pf2.results.Sf.real

            v_ok: bool = bool(np.allclose(v1, v2, atol=1e-4))
            flow_ok: bool = bool(np.allclose(p1, p2, atol=1e-2))
            assert v_ok
            assert flow_ok

        print(solver_type, 'ok')


def test_circuit_to_dgs_uses_profile_values_when_t_idx_is_provided() -> None:
    """DGS export must use profile values when ``t_idx`` is provided."""

    grid: dev.MultiCircuit = dev.MultiCircuit(name="profile-export")

    bus_1: dev.Bus = dev.Bus(name="B1", Vnom=110.0, active=True)
    bus_2: dev.Bus = dev.Bus(name="B2", Vnom=110.0, active=True)
    bus_1.active_prof = np.array([True, False])
    grid.add_bus(bus_1)
    grid.add_bus(bus_2)

    load: dev.Load = dev.Load(name="LD1", P=10.0, Q=2.0, active=True)
    load.P_prof = np.array([12.0, 22.0])
    load.Q_prof = np.array([3.0, 5.0])
    load.active_prof = np.array([True, False])
    grid.add_load(bus=bus_1, api_obj=load)

    line: dev.Line = dev.Line(
        bus_from=bus_1,
        bus_to=bus_2,
        name="L12",
        r=0.01,
        x=0.05,
        b=0.001,
        rate=100.0,
        active=True,
    )
    line.rate_prof = np.array([120.0, 220.0])
    line.active_prof = np.array([True, False])
    grid.add_line(line)

    switch: dev.Switch = dev.Switch(
        bus_from=bus_1,
        bus_to=bus_2,
        name="SW12",
        rate=80.0,
        active=True,
        rated_current=0.0,
    )
    switch.rate_prof = np.array([90.0, 180.0])
    switch.active_prof = np.array([True, False])
    grid.add_switch(switch)

    snapshot_export = circuit_to_dgs(grid=grid, t_idx=None)
    profile_export = circuit_to_dgs(grid=grid, t_idx=1)

    snapshot_line_current: float = 100.0 / (np.sqrt(3.0) * 110.0)
    profile_line_current: float = 220.0 / (np.sqrt(3.0) * 110.0)
    snapshot_switch_current: float = 80.0 / (np.sqrt(3.0) * 110.0)
    profile_switch_current: float = 180.0 / (np.sqrt(3.0) * 110.0)

    assert snapshot_export.elmterms[0].outserv == 0
    assert profile_export.elmterms[0].outserv == 1

    assert snapshot_export.elmlods[0].plini == 10.0
    assert profile_export.elmlods[0].plini == 22.0
    assert snapshot_export.elmlods[0].qlini == 2.0
    assert profile_export.elmlods[0].qlini == 5.0
    assert snapshot_export.elmlods[0].outserv == 0
    assert profile_export.elmlods[0].outserv == 1

    assert np.isclose(snapshot_export.typlnes[0].InomAir, snapshot_line_current)
    assert np.isclose(profile_export.typlnes[0].InomAir, profile_line_current)
    assert snapshot_export.elmlnes[0].outserv == 0
    assert profile_export.elmlnes[0].outserv == 1

    assert np.isclose(snapshot_export.typswitches[0].InomA, snapshot_switch_current)
    assert np.isclose(profile_export.typswitches[0].InomA, profile_switch_current)
    assert snapshot_export.elmcoups[0].on_off == 1
    assert profile_export.elmcoups[0].on_off == 0


@pytest.mark.skip(reason="Faulty implementation")
def test_dgs_tower_coupling_logs_non_empty_message_for_blank_value_error() -> None:
    class FakeLine:
        def __init__(self) -> None:
            self.name = "L1"

        def set_circuit_idx(self, val: int, obj) -> None:
            pass

        def apply_template(self, obj, Sbase: float, freq: float, logger: Logger) -> None:
            raise ValueError()

    logger = Logger()
    # TODO: this must be a DgsCircuit
    dgs_grid = SimpleNamespace(
        elmtows=[
            SimpleNamespace(
                outserv=0,
                pGeo=["tower-1"],
                loc_name="Tower 1",
                ID="tower-id",
                plines=["line-1"],
            )
        ]
    )

    _apply_elmtow_tower_coupling(
        dgs_grid=dgs_grid,
        line_by_dgs_id={"line-1": [FakeLine()]},
        overhead_line_type_dict={"tower-1": SimpleNamespace(n_circuits=1)},
        baseMVA=100.0,
        frequency=50.0,
        logger=logger,
    )

    assert len(logger.entries) == 1
    assert logger.entries[0].msg == "Failed to apply tower template."


def test_dgs_shared_tower_type_creates_phase_layout_variants() -> None:
    grid = FileOpen(os.path.join("data", "grids", "DGS", "IEEE13_NoCables.dgs")).open()
    line_by_name = {line.name: line for line in grid.lines}

    assert line_by_name["LOHL632-645"].template.name == "LineConfig603-604_CBN"
    assert line_by_name["LOHL645-646"].template.name == "LineConfig603-604_CBN"
    assert line_by_name["LOHL671-684"].template.name == "LineConfig603-604_ACN"
    assert line_by_name["LOHL632-645"].template is not line_by_name["LOHL671-684"].template

    expected_by_line = {
        "LOHL632-645": [True, False, True, True],
        "LOHL645-646": [True, False, True, True],
        "LOHL671-684": [True, True, False, True],
    }
    for line_name, expected_phases in expected_by_line.items():
        line = line_by_name[line_name]
        declared_phases = [line.ys.phN, line.ys.phA, line.ys.phB, line.ys.phC]
        matrix_phases = np.any(np.abs(line.ys.values) > 1e-12, axis=0)
        assert declared_phases == expected_phases
        assert np.array_equal(matrix_phases, expected_phases)


@pytest.mark.parametrize("use_capacitance", (False, True))
@pytest.mark.parametrize("frequency", (50.0, 60.0))
@pytest.mark.parametrize("base_power", (100.0, 25.0))
def test_dgs_sequence_sections_preserve_parameter_contract(
        use_capacitance: bool, frequency: float, base_power: float,
) -> None:
    """Preserve each imported section parameter when the sequence tuple grows.

    :param use_capacitance: Select Cnf/Cnf0 instead of B/B0 source inputs.
    :param frequency: Frequency used to convert capacitance, in Hz.
    :param base_power: Three-phase system power base in MVA.
    :return: None.
    """
    # Different section types expose shifted zero-sequence and rating positions;
    # positive and zero conductances deliberately differ from every other field.
    first_template: dev.SequenceLineType = dev.SequenceLineType(
        name="First section", Imax=0.7,
        R=0.08, X=0.16, B=2.4, G=1.3,
        R0=0.24, X0=0.48, B0=0.9, G0=0.4,
        CnF=7.0, CnF0=3.0, use_conductance=use_capacitance,
    )
    second_template: dev.SequenceLineType = dev.SequenceLineType(
        name="Second section", Imax=0.4,
        R=0.12, X=0.27, B=3.6, G=2.1,
        R0=0.36, X0=0.81, B0=1.5, G0=0.8,
        CnF=11.0, CnF0=5.0, use_conductance=use_capacitance,
    )
    first_section: ElmLnesec = ElmLnesec()
    first_section.ID = "first-section"
    first_section.typ_id = "first-type"
    first_section.index = 1.0
    first_section.dline = 0.5
    first_section.fline = 0.8
    second_section: ElmLnesec = ElmLnesec()
    second_section.ID = "second-section"
    second_section.typ_id = "second-type"
    second_section.index = 2.0
    second_section.dline = 2.0
    second_section.fline = 0.6
    source: ElmLne = ElmLne()
    source.ID = "sectioned-line"
    source.loc_name = "Sectioned line"
    source.dline = 2.5
    source.fline = 0.9
    voltage: float = 33.0
    buses: list[dev.Bus] = list((
        dev.Bus(name="From", Vnom=voltage),
        dev.Bus(name="To", Vnom=voltage),
    ))
    terminal_indices: dict[str, list[int]] = dict((
        (source.ID, list((0, 1))),
    ))
    sequence_templates: dict[str, dev.SequenceLineType] = dict((
        (first_section.typ_id, first_template),
        (second_section.typ_id, second_template),
    ))
    sections_by_line: dict[str, list[ElmLnesec]] = dict((
        (source.ID, list((second_section, first_section))),
    ))

    # Exercise the real converter with reverse source ordering. No parallel
    # import representation is needed to obtain the canonical Line instance.
    converted: dev.Line | dev.DcLine = convert_dgs_to_line(
        lne=source, buses=buses, stacubic_dict=terminal_indices,
        sequence_templates_dict=sequence_templates,
        dc_cable_type_dict=dict(), source_line_type_dict=dict(),
        overhead_line_type_dict=dict(), underground_line_type_dict=dict(),
        line_type_by_line_id=dict(), line_sections_by_line_id=sections_by_line,
        tower_template_by_line_id=dict(), freq=frequency, baseMVA=base_power,
        logger=Logger(), cubics_by_objid=dict(), bus_by_term_id=dict(), phase_map=dict(),
    )
    assert isinstance(converted, dev.Line)
    assert not converted.reducible

    # Compute the physical oracle directly, without get_values/apply_template.
    # Series Ohms sum, while total charging Siemens use the selected input mode.
    impedance_base: float = voltage * voltage / base_power
    susceptance: float
    zero_susceptance: float
    if use_capacitance:
        susceptance = 2.0 * np.pi * frequency * (7.0 * 0.5 + 11.0 * 2.0) * 1.0e-9
        zero_susceptance = 2.0 * np.pi * frequency * (3.0 * 0.5 + 5.0 * 2.0) * 1.0e-9
    else:
        susceptance = (2.4 * 0.5 + 3.6 * 2.0) * 1.0e-6
        zero_susceptance = (0.9 * 0.5 + 1.5 * 2.0) * 1.0e-6
    expected: np.ndarray = np.array((
        (0.08 * 0.5 + 0.12 * 2.0) / impedance_base,
        (0.16 * 0.5 + 0.27 * 2.0) / impedance_base,
        susceptance * impedance_base,
        (0.24 * 0.5 + 0.36 * 2.0) / impedance_base,
        (0.48 * 0.5 + 0.81 * 2.0) / impedance_base,
        zero_susceptance * impedance_base,
        min(0.7 * 0.8, 0.4 * 0.6) * voltage * np.sqrt(3.0) * 0.9,
    ))
    np.testing.assert_allclose(
        (converted.R, converted.X, converted.B,
         converted.R0, converted.X0, converted.B0, converted.rate),
        expected, rtol=1.0e-10, atol=1.0e-12,
    )
    # Section G/G0 aggregation is pre-existing import debt outside this API fix.
    # Changing tuple positions must neither invent that policy nor retain a shift.
    assert converted.G == 0.0 and converted.G0 == 0.0


def _grid_with_an_exact_tap_table(table: np.ndarray, neutral: int = 8, hv_at_from: bool = True,
                                  bus_voltages: tuple[float, float] = (132.0, 33.0),
                                  tc_type: TapChangerTypes = TapChangerTypes.VoltageRegulation) -> dev.MultiCircuit:
    """Two buses and a transformer on an exact table at position 12.

    :param table: Exact table of the tap.
    :param neutral: Neutral position.
    :param hv_at_from: Whether the first bus is the from bus.
    :param bus_voltages: Nominal voltages of the two buses.
    :param tc_type: Tap changer type.
    :return: The grid.
    """
    grid: dev.MultiCircuit = dev.MultiCircuit(name="signed-tap")
    first: dev.Bus = dev.Bus(name="B1", Vnom=bus_voltages[0], is_slack=True)
    second: dev.Bus = dev.Bus(name="B2", Vnom=bus_voltages[1])
    grid.add_bus(first)
    grid.add_bus(second)
    transformer: dev.Transformer2W
    if hv_at_from:
        transformer = dev.Transformer2W(bus_from=first, bus_to=second, name="T1", HV=max(bus_voltages) + 1.5,
                                        LV=min(bus_voltages), nominal_power=100.0, r=0.001, x=0.1)
    else:
        transformer = dev.Transformer2W(bus_from=second, bus_to=first, name="T1", HV=max(bus_voltages) + 1.5,
                                        LV=min(bus_voltages), nominal_power=100.0, r=0.001, x=0.1)
    grid.add_transformer2w(transformer)
    transformer.tap_changer.total_positions = len(table)
    transformer.tap_changer.neutral_position = neutral
    transformer.tap_changer.dV = 0.0125
    transformer.tap_changer.tc_type = tc_type
    assert transformer.tap_changer.set_tap_module_phase_values(tap_modules=table, tap_phases=np.zeros(len(table)))
    transformer.tap_changer.tap_position = 12
    transformer.tap_module = table[12]
    return grid


def _table(shape: str, neutral: int) -> np.ndarray:
    """A 17 position table of one shape around a neutral.

    :param shape: Shape of the table.
    :param neutral: Neutral position.
    :return: The table.
    """
    offsets: np.ndarray = np.arange(17) - neutral
    if shape == "rising":
        return 1.0 + 0.0125 * offsets
    elif shape == "falling":
        return 1.0 - 0.0125 * offsets
    elif shape == "falling_on_the_to_bus":
        return 1.0 / (1.0 + 0.0125 * offsets)
    else:
        return 1.0 / (1.0 - 0.0125 * offsets)


def _assert_the_table_survives_a_dgs_file(tmp_path: Path, grid: dev.MultiCircuit, table: np.ndarray) -> None:
    """Write a grid to a DGS file and read its transformer back.

    :param tmp_path: Isolated pytest directory for the DGS file.
    :param grid: Grid with one transformer at position 12.
    :param table: Exact table of the tap.
    :return: None.
    """
    path: Path = tmp_path / "signed_tap.dgs"
    dgs: DgsCircuit = circuit_to_dgs(grid=grid)
    dgs.write_dgs(path=str(path))
    imported: dev.Transformer2W = FileOpen(str(path)).open().transformers2w[0]

    assert not dgs.logger.has_logs()
    assert imported.tap_changer.tap_position == 12
    assert imported.tap_module == pytest.approx(table[12])
    assert imported.tap_module_control_mode == TapModuleControl.fixed
    assert imported.tap_changer.tap_modules_array == pytest.approx(table)


@pytest.mark.parametrize("neutral", [8, 5])
@pytest.mark.parametrize("hv_at_from", [True, False])
@pytest.mark.parametrize("shape", ["rising", "falling", "falling_on_the_to_bus", "rising_on_the_to_bus"])
def test_exported_dgs_keeps_an_exact_tap_table(tmp_path: Path, shape: str, hv_at_from: bool, neutral: int) -> None:
    """A DGS round trip keeps the table, the position and the frozen control of a signed tap.

    :param tmp_path: Isolated pytest directory for the DGS file.
    :param shape: Shape of the table.
    :param hv_at_from: Whether the high voltage bus is the from bus.
    :param neutral: Neutral position.
    :return: None.
    """
    table: np.ndarray = _table(shape=shape, neutral=neutral)
    grid: dev.MultiCircuit = _grid_with_an_exact_tap_table(table=table, neutral=neutral, hv_at_from=hv_at_from)
    _assert_the_table_survives_a_dgs_file(tmp_path=tmp_path, grid=grid, table=table)


@pytest.mark.parametrize("shape", ["rising", "falling", "falling_on_the_to_bus", "rising_on_the_to_bus"])
def test_exported_dgs_keeps_a_table_between_equal_bus_voltages(tmp_path: Path, shape: str) -> None:
    """The buses decide the tap side as in the importer, whatever voltages the transformer declares.

    :param tmp_path: Isolated pytest directory for the DGS file.
    :param shape: Shape of the table.
    :return: None.
    """
    table: np.ndarray = _table(shape=shape, neutral=8)
    grid: dev.MultiCircuit = _grid_with_an_exact_tap_table(table=table, bus_voltages=(33.0, 33.0))
    _assert_the_table_survives_a_dgs_file(tmp_path=tmp_path, grid=grid, table=table)


@pytest.mark.parametrize("amplitude", [5e-4, 1e-7])
@pytest.mark.parametrize("shape", ["falling", "falling_on_the_to_bus"])
def test_exported_dgs_keeps_the_module_of_a_table_without_a_tap_law(tmp_path: Path, shape: str,
                                                                    amplitude: float) -> None:
    """A table close to a law but off it keeps its operating module, and the export says so.

    :param tmp_path: Isolated pytest directory for the DGS file.
    :param shape: Shape the table stays close to.
    :param amplitude: Distance of the table from that law.
    :return: None.
    """
    table: np.ndarray = _table(shape=shape, neutral=8) + amplitude * np.sin(np.arange(17))
    path: Path = tmp_path / "signed_tap.dgs"
    dgs: DgsCircuit = circuit_to_dgs(grid=_grid_with_an_exact_tap_table(table=table))
    dgs.write_dgs(path=str(path))

    assert dgs.logger.has_logs()
    assert FileOpen(str(path)).open().transformers2w[0].tap_module == pytest.approx(table[12])


@pytest.mark.parametrize("slope, neutral, keeps_the_direction",
                         [(0.0125, 8, True), (0.0125, 0, False), (0.0125, 16, True),
                          (-0.0125, 8, True), (-0.0125, 0, True), (-0.0125, 16, False)])
def test_exported_dgs_keeps_the_module_of_a_table_without_a_tap_law_at_its_neutral(tmp_path: Path, slope: float,
                                                                                  neutral: int,
                                                                                  keeps_the_direction: bool) -> None:
    """A neutral whose module is not 1 cannot carry it, so the position beside takes the neutral, in range and on
    the side that keeps the direction of the table unless the table ends there.

    :param tmp_path: Isolated pytest directory for the DGS file.
    :param slope: Slope of the table.
    :param neutral: Neutral position, where the tap sits.
    :param keeps_the_direction: Whether the side that keeps the direction is in range.
    :return: None.
    """
    table: np.ndarray = 1.02 + slope * (np.arange(17) - neutral)
    grid: dev.MultiCircuit = _grid_with_an_exact_tap_table(table=table, neutral=neutral)
    grid.transformers2w[0].tap_changer.tap_position = neutral
    grid.transformers2w[0].tap_module = table[neutral]
    path: Path = tmp_path / "signed_tap.dgs"
    dgs: DgsCircuit = circuit_to_dgs(grid=grid)
    dgs.write_dgs(path=str(path))
    tap_type: TypTr2 = dgs.typtr2s[0]
    imported: dev.Transformer2W = FileOpen(str(path)).open().transformers2w[0]

    assert dgs.logger.has_logs()
    assert tap_type.ntpmn <= tap_type.nntap0 <= tap_type.ntpmx
    assert abs(tap_type.nntap0 - neutral) == 1
    assert imported.tap_module == pytest.approx(1.02)
    modules: np.ndarray = imported.tap_changer.tap_modules_array
    assert ((modules[-1] > modules[0]) == (slope > 0.0)) == keeps_the_direction


def test_exported_dgs_warns_about_a_module_off_its_table_position() -> None:
    """DGS carries the position, so a module the table does not hold there is reported.

    :return: None.
    """
    grid: dev.MultiCircuit = _grid_with_an_exact_tap_table(table=_table(shape="rising", neutral=8))
    grid.transformers2w[0].tap_module = 1.043

    assert circuit_to_dgs(grid=grid).logger.has_logs()


def test_exported_dgs_writes_a_flat_table_at_zero_degrees() -> None:
    """A flat table has no direction and stays on the high voltage side.

    :return: None.
    """
    tap_type: TypTr2 = circuit_to_dgs(grid=_grid_with_an_exact_tap_table(table=np.ones(17))).typtr2s[0]

    assert tap_type.phitr == 0.0
    assert tap_type.dutap == 0.0
    assert tap_type.tap_side == 0


@pytest.mark.parametrize("tc_type", [TapChangerTypes.VoltageRegulation, TapChangerTypes.NoRegulation])
@pytest.mark.parametrize("dv, phase", [(0.0125, 0.0), (-0.0125, 180.0)])
def test_exported_dgs_writes_a_generic_tap_as_a_positive_step(dv: float, phase: float,
                                                              tc_type: TapChangerTypes) -> None:
    """A tap on the generic law has no table to read, and its step leaves positive with its angle.

    :param dv: Step of the generic law.
    :param phase: Angle it leaves with.
    :param tc_type: Tap changer type, frozen or regulating.
    :return: None.
    """
    grid: dev.MultiCircuit = _grid_with_an_exact_tap_table(table=np.ones(17), tc_type=tc_type)
    grid.transformers2w[0].tap_changer.dV = dv

    tap_type: TypTr2 = circuit_to_dgs(grid=grid).typtr2s[0]

    assert tap_type.dutap == pytest.approx(1.25)
    assert tap_type.phitr == phase
    assert tap_type.tap_side == 0


def test_exported_dgs_takes_an_exact_table_of_one_position() -> None:
    """One position has no slope, so the tap keeps its step.

    :return: None.
    """
    grid: dev.MultiCircuit = _grid_with_an_exact_tap_table(table=np.ones(17))
    tap_changer: dev.TapChanger = grid.transformers2w[0].tap_changer
    tap_changer.total_positions = 1
    tap_changer.neutral_position = 0
    assert tap_changer.set_tap_module_phase_values(tap_modules=np.array([1.0]), tap_phases=np.zeros(1))

    tap_type: TypTr2 = circuit_to_dgs(grid=grid).typtr2s[0]

    assert tap_type.dutap == pytest.approx(1.25)


def test_exported_dgs_reads_the_table_of_voltage_regulating_taps_only() -> None:
    """A changer with no voltage regulation writes its own step.

    :return: None.
    """
    grid: dev.MultiCircuit = _grid_with_an_exact_tap_table(table=1.0 + 0.02 * (np.arange(17) - 8),
                                                           tc_type=TapChangerTypes.NoRegulation)

    tap_type: TypTr2 = circuit_to_dgs(grid=grid).typtr2s[0]

    assert tap_type.dutap == pytest.approx(1.25)


@pytest.mark.parametrize("tc_type, phase", [(TapChangerTypes.Asymmetrical, 30.0), (TapChangerTypes.Symmetrical, 180.0)])
def test_exported_dgs_keeps_the_angle_of_a_phase_shifting_tap(tc_type: TapChangerTypes, phase: float) -> None:
    """A phase shifting tap keeps its own step and angle, out of the signed step of a voltage tap.

    :param tc_type: Phase shifting tap changer type.
    :param phase: Angle it leaves with.
    :return: None.
    """
    grid: dev.MultiCircuit = _grid_with_an_exact_tap_table(table=np.ones(17), tc_type=tc_type)
    grid.transformers2w[0].tap_changer.asymmetry_angle = 30.0

    tap_type: TypTr2 = circuit_to_dgs(grid=grid).typtr2s[0]

    assert tap_type.dutap == pytest.approx(1.25)
    assert tap_type.phitr == phase


def test_circuit_to_dgs_exports_static_generators_and_batteries(tmp_path: Path) -> None:
    """The injections written as ElmGenstat carry their scaling column in the file.

    :param tmp_path: Isolated pytest directory for the DGS file.
    :return: None.
    """
    grid: dev.MultiCircuit = dev.MultiCircuit(name="genstat")
    bus: dev.Bus = dev.Bus(name="B1", Vnom=33.0)
    grid.add_bus(bus)
    grid.add_static_generator(bus, dev.StaticGenerator(name="G1", P=10.0, Q=1.0))
    grid.add_battery(bus, dev.Battery(name="BESS1", P=5.0))

    path: Path = tmp_path / "genstat.dgs"
    dgs: DgsCircuit = circuit_to_dgs(grid=grid)
    dgs.write_dgs(path=str(path))

    assert sorted(genstat.loc_name for genstat in dgs.elmgenstats) == ["BESS1", "G1"]
    assert all(genstat.scale0 == 1.0 for genstat in dgs.elmgenstats)
    lines: list[str] = path.read_text(encoding="utf-8").splitlines()
    header: str = next(line for line in lines if line.startswith("$$ElmGenstat"))
    assert "scale0" in header
    assert ElmGenstat().scale0 == 1.0


@pytest.mark.parametrize("uset_mode, node, expected_vset, controls_node", [
    (1, "node", 1.0, True),
    (0, "node", 1.03, True),
    (1, "", 1.03, False),
])
def test_droop_svs_imports_as_a_qv_droop_shunt(uset_mode: int, node: str, expected_vset: float,
                                                controls_node: bool) -> None:
    """A voltage-controlled ElmSvs with droop keeps the PowerFactory band, slope and setpoint (TechRef SVS eq. 15-16).

    :param uset_mode: PowerFactory setpoint source
    :param node: Controlled node reference, empty for none
    :param expected_vset: Setpoint the shunt must take
    :param controls_node: Whether the shunt must control the node bus
    """
    elmsvs = ElmSvs()
    elmsvs.ID, elmsvs.loc_name = "svs", "SVS"
    elmsvs.i_ctrl, elmsvs.i_droop = 1, 1
    elmsvs.qmin, elmsvs.nxcap, elmsvs.nncap = -100.0, 4, 2
    elmsvs.tcrmax, elmsvs.tcrqact = 150.0, 30.0
    elmsvs.Qfixcap, elmsvs.nfixcap = -10.0, 1
    elmsvs.Srated, elmsvs.ddroop, elmsvs.usetp = 400.0, 4.0, 1.03
    elmsvs.uset_mode, elmsvs.cpCtrlNode = uset_mode, node
    terminal = ElmTerm()
    terminal.ID, terminal.vtarget = "node", 1.0
    own_bus, node_bus = dev.Bus(name="own"), dev.Bus(name="node")

    shunt = convert_dgs_svs_to_droop_shunt(elmsvs=elmsvs, bus=own_bus, terms_by_id={"node": terminal},
                                           bus_by_term_id={"node": node_bus})

    assert shunt.control_mode == ShuntControlMode.QVDroop
    assert shunt.Bmin == pytest.approx(-140.0)  # -(tcrmax + Qfixcap * nfixcap)
    assert shunt.Bmax == pytest.approx(410.0)  # -(qmin * nxcap + Qfixcap * nfixcap)
    assert shunt.B == pytest.approx(180.0)  # -(qmin * nncap + tcrqact + Qfixcap * nfixcap)
    assert shunt.Qdroop == pytest.approx(10000.0)  # Srated * 100 / ddroop
    assert shunt.Vset == pytest.approx(expected_vset)
    assert shunt.control_bus is (node_bus if controls_node else own_bus)
    assert shunt.conn == ShuntConnectionType.Delta
