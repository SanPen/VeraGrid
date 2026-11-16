# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from pathlib import Path
from typing import Dict, List

import numpy as np
import pytest

from VeraGridEngine.Devices.Branches.transformer import Transformer2W
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Injections.battery import Battery
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
from VeraGridEngine.IO.dgs.dgs_objects import ElmGenstat, ElmSym, IntQlim
from VeraGridEngine.IO.dgs.dgs_import_metadata import assign_import_template
from VeraGridEngine.IO.dgs.dgs_to_veragrid import (
    _get_capability_points,
    _get_parallel_device_idtag,
    _set_generator_capability_curves,
    _set_generators_nominal_frequency,
)
from VeraGridEngine.IO.dgs.dynamic_models.dynamic_model_import import DynamicModelImport
from VeraGridEngine.IO.file_open import FileOpen, FileOpenOptions
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import (DeviceType, DynamicSimulationMode, FileType, ShuntControlMode,
                                         TapModuleControl, VarPowerFlowReferenceType)
import VeraGridEngine.api as gce

DGS_FOLDER: Path = Path(__file__).parents[2] / "data" / "grids" / "DGS"


def _read_dgs_rows(path: Path, element_class: str) -> Dict[str, Dict[str, str]]:
    """Read the rows of one DGS class, results included, by FID.

    :param path: DGS file
    :param element_class: DGS class name
    :return: Column-name dictionaries by FID
    """
    rows: Dict[str, Dict[str, str]] = dict()
    columns: List[str] = list()
    reading: bool = False
    with open(path, "r", encoding="latin-1") as handle:
        for raw in handle:
            line: str = raw.rstrip("\r\n")
            if line.startswith("$$"):
                header: List[str] = line[2:].split(";")
                reading = header[0] == element_class
                columns = [column.split("(")[0] for column in header[1:]]
            elif reading and line and not line.startswith("*"):
                row: Dict[str, str] = dict(zip(columns, [value.strip() for value in line.split(";")]))
                rows[row["FID"]] = row
            else:
                pass
    return rows


def test_gb_svs_follow_the_powerfactory_law() -> None:
    """Each GB SVS is a Q-V droop shunt: at the PowerFactory voltages its law gives m:Q, and the load flow with
    reactive limits converges within the default iterations with every SVS on its law.

    :return: None.
    """
    path: Path = DGS_FOLDER / "gb_reduced_complete_static_dynamic.dgs"
    svs_rows: Dict[str, Dict[str, str]] = _read_dgs_rows(path, "ElmSvs")
    terms: Dict[str, Dict[str, str]] = _read_dgs_rows(path, "ElmTerm")
    cubic_terms: Dict[str, str] = {row["obj_id"]: row["fold_id"] for row in _read_dgs_rows(path, "StaCubic").values()}
    grid: MultiCircuit = FileOpen(
        file_name=str(path),
        options=FileOpenOptions(file_type=FileType.DGS, dgs_use_dynamic_information=False),
    ).open()
    shunts: List[gce.ControllableShunt] = [shunt for shunt in grid.controllable_shunts
                                           if shunt.control_mode == ShuntControlMode.QVDroop]
    assert len(shunts) == len(svs_rows) == 29
    with_node: int = 0
    for shunt in shunts:
        row: Dict[str, str] = svs_rows[shunt.idtag]
        if row["cpCtrlNode"]:
            vm: float = float(terms[cubic_terms[shunt.idtag]]["m:u"])
            vc: float = float(terms[shunt.control_bus.idtag]["m:u"])
            law: float = float(np.clip(shunt.Qdroop * (shunt.Vset - vc), shunt.Bmin * vm ** 2, shunt.Bmax * vm ** 2))
            assert law == pytest.approx(float(row["m:Q:bus1"]), abs=0.5)
            with_node += 1
        else:
            pass
    assert with_node == 27

    results = gce.power_flow(grid, gce.PowerFlowOptions(control_q=True))
    assert results.converged
    buses: List[Bus] = list(grid.buses)
    for k, shunt in enumerate(grid.controllable_shunts):
        if shunt.control_mode == ShuntControlMode.QVDroop:
            vm = float(abs(results.voltage[buses.index(shunt.bus)]))
            vc = float(abs(results.voltage[buses.index(shunt.control_bus)]))
            law = float(np.clip(shunt.Qdroop * (shunt.Vset - vc), shunt.Bmin * vm ** 2, shunt.Bmax * vm ** 2))
            assert -results.shunt_q[len(grid.shunts) + k] == pytest.approx(law, abs=1e-6 * grid.Sbase)
        else:
            pass


def test_gb_dgs_activates_its_controllers_when_opened() -> None:
    """Assign every controller of the GB export through the user file-open path.

    :return: None.
    """
    path: Path = DGS_FOLDER / "gb_reduced_complete_static_dynamic.dgs"
    grid: MultiCircuit = FileOpen(
        file_name=str(path),
        options=FileOpenOptions(
            file_type=FileType.DGS,
            dgs_use_dynamic_information=True,
            dgs_dynamic_simulation_mode=DynamicSimulationMode.RMS,
        ),
    ).open()
    counts: Dict[str, int] = dict()
    for generator in grid.generators:
        if generator.rms_template is not None:
            name: str = generator.rms_template.name.split(" [")[0]
            counts[name] = counts.get(name, 0) + 1
            assert not generator.rms_model.empty()
        else:
            pass
    # Out-of-service equipment keeps no dynamics: Z07, Z08 and Z16 Battery are outserv=1
    assert counts.get("WECC BESS Control System", 0) == 25
    assert counts.get("WECC WT Control System Type 4B", 0) == 28
    assert counts.get("Gen Control-Sync Condenser", 0) == 6
    assert sum(count for name, count in counts.items() if name.startswith("WECC HVDC")) == 7
    assert grid.fBase == 50.0
    assert all(generator.freq == 50.0 for generator in grid.generators)
    assert sum(generator.use_reactive_power_curve for generator in grid.generators) == 242
    transformers: Dict[str, float] = {branch.idtag: branch.tap_module for branch in grid.transformers2w}
    assert transformers["5817"] == pytest.approx(0.988888, abs=1e-6)
    assert all(branch.tap_module_control_mode != TapModuleControl.Vm for branch in grid.transformers2w)
    assert all(abs(branch.tap_module - branch.tap_changer.get_tap_module()) < 1e-9 for branch in grid.transformers2w)
    moved: Transformer2W = [branch for branch in grid.transformers2w if branch.idtag == "5817"][0]
    moved.tap_up()
    assert moved.tap_module == pytest.approx(0.977778, abs=1e-6)
    moved.tap_down()
    assert moved.tap_module == pytest.approx(0.988888, abs=1e-6)
    assert gce.power_flow(grid).converged


def test_capability_curve_reads_the_units_it_declares() -> None:
    """Read the p.u. columns of a curve in per-unit input mode.

    :return: None.
    """
    header_map: Dict[str, int] = {"ID": 0, "inputmod": 1, "cap_Ppu:SIZEROW": 2, "cap_Ppu:0": 3, "cap_Ppu:1": 4,
                                  "cap_Qmnpu:SIZEROW": 5, "cap_Qmnpu:0": 6, "cap_Qmnpu:1": 7,
                                  "cap_Qmxpu:SIZEROW": 8, "cap_Qmxpu:0": 9, "cap_Qmxpu:1": 10}
    curve: IntQlim = IntQlim.parse_line("1;1;2;1;0;2;-0.2;-0.5;2;0.2;0.5", header_map)
    assert curve.active_power == [1.0, 0.0]
    machine: ElmSym = ElmSym()
    machine.scaleQmin = 50.0
    machine.scaleQmax = 200.0
    points: np.ndarray = _get_capability_points(curve=curve, source=machine, snom=10.0)
    assert points.tolist() == [[0.0, -2.5, 10.0], [10.0, -1.0, 4.0]]


@pytest.mark.parametrize("row, expected", [
    ("1;1;2;0,5;1;2;-0,2;-0,5;2;0,2;0,5", [0.5, 1.0]),
    ("1;1;2;;1;2;-0.2;-0.5;2;0.2;0.5", []),
    ("1;1;3;0;1;2;-0.2;-0.5;2;0.2;0.5", []),
])
def test_capability_curve_survives_what_the_export_writes(row: str, expected: List[float]) -> None:
    """Read decimal commas, and drop a curve with a missing point without failing.

    :param row: Raw DGS row.
    :param expected: Expected active power points.
    :return: None.
    """
    header_map: Dict[str, int] = {"ID": 0, "inputmod": 1, "cap_Ppu:SIZEROW": 2, "cap_Ppu:0": 3, "cap_Ppu:1": 4,
                                  "cap_Qmnpu:SIZEROW": 5, "cap_Qmnpu:0": 6, "cap_Qmnpu:1": 7,
                                  "cap_Qmxpu:SIZEROW": 8, "cap_Qmxpu:0": 9, "cap_Qmxpu:1": 10}
    assert IntQlim.parse_line(row, header_map).active_power == expected


@pytest.mark.parametrize("row, expected", [("1;;", (None, None)), ("1;50;200", (50.0, 200.0))])
def test_blank_capability_scale_means_no_scaling(row: str, expected: tuple[float | None, float | None]) -> None:
    """Keep a blank scale cell apart from a scale of zero.

    :param row: Raw DGS row.
    :param expected: Expected lower and upper scale.
    :return: None.
    """
    machine: ElmSym = ElmSym.parse_line(row, {"ID": 0, "scaleQmin": 1, "scaleQmax": 2})
    assert (machine.scaleQmin, machine.scaleQmax) == expected


def test_curves_warn_only_when_they_cannot_be_applied_as_declared() -> None:
    """Warn on a voltage-dependent curve, and stay silent on a machine without a curve.

    :return: None.
    """
    grid: MultiCircuit = MultiCircuit()
    bus: Bus = Bus(name="Bus")
    grid.add_bus(bus)
    dgs_grid: DgsCircuit = DgsCircuit()
    curve: IntQlim = IntQlim()
    curve.ID = "9"
    curve.voltagedep = 1
    curve.active_power = [0.0]
    curve.reactive_power_min = [-1.0]
    curve.reactive_power_max = [1.0]
    dgs_grid.intqlims.append(curve)
    dependent: ElmSym = ElmSym()
    dependent.ID = "1"
    dependent.pQlimType = "9"
    plain: ElmSym = ElmSym()
    plain.ID = "2"
    dgs_grid.elmsyms.extend([dependent, plain])
    grid.add_generator(bus=bus, api_obj=Generator(name="A", idtag="1"))
    grid.add_generator(bus=bus, api_obj=Generator(name="B", idtag="2"))
    logger: Logger = Logger()
    _set_generator_capability_curves(grid=grid, dgs_grid=dgs_grid, logger=logger)
    assert [entry.device for entry in logger.entries] == ["A"]
    assert "voltage dependency" in logger.entries[0].msg


def test_every_parallel_machine_and_battery_takes_its_curve() -> None:
    """Assign the curve across parallel machines and batteries, and warn on a dangling pointer.

    :return: None.
    """
    grid: MultiCircuit = MultiCircuit()
    bus: Bus = Bus(name="Bus")
    grid.add_bus(bus)
    dgs_grid: DgsCircuit = DgsCircuit()
    curve: IntQlim = IntQlim()
    curve.ID = "9"
    curve.inputmod = 1
    curve.active_power = [0.0, 1.0]
    curve.reactive_power_min = [-0.5, -0.1]
    curve.reactive_power_max = [0.5, 0.1]
    dgs_grid.intqlims.append(curve)
    parallel: ElmSym = ElmSym()
    parallel.ID = "1"
    parallel.ngnum = 2
    parallel.pQlimType = "9"
    storage: ElmGenstat = ElmGenstat()
    storage.ID = "2"
    storage.pQlimType = "9"
    dangling: ElmGenstat = ElmGenstat()
    dangling.ID = "3"
    dangling.pQlimType = "8"
    dgs_grid.elmsyms.append(parallel)
    dgs_grid.elmgenstats.extend([storage, dangling])
    first: Generator = Generator(name="A", idtag=_get_parallel_device_idtag("1", 0, 2), Snom=10.0)
    second: Generator = Generator(name="B", idtag=_get_parallel_device_idtag("1", 1, 2), Snom=10.0)
    lost: Generator = Generator(name="C", idtag="3", Snom=10.0)
    battery: Battery = Battery(name="D", idtag="2", Snom=10.0)
    for generator in (first, second, lost):
        grid.add_generator(bus=bus, api_obj=generator)
    grid.add_battery(bus=bus, api_obj=battery)
    logger: Logger = Logger()
    _set_generator_capability_curves(grid=grid, dgs_grid=dgs_grid, logger=logger)
    for machine in (first, second, battery):
        assert machine.use_reactive_power_curve
        assert (machine.Qmin, machine.Qmax) == (-5.0, 5.0)
    assert not lost.use_reactive_power_curve
    assert any("capability curve unavailable" in entry.msg for entry in logger.entries)


def test_rejected_tap_table_is_reported(tmp_path: Path) -> None:
    """Warn when a tap law reaches a module the changer cannot hold.

    :param tmp_path: Temporary folder fixture.
    :return: None.
    """
    source: Path = DGS_FOLDER / "hvdc_vsc_v3_complete_static_dynamic.dgs"
    lines: List[str] = source.read_bytes().decode("utf-8").split("\n")
    header: int = [index for index, line in enumerate(lines) if line.startswith("$$TypTr2;")][0]
    dutap: int = [column.split("(")[0] for column in lines[header].strip().split(";")[1:]].index("dutap")
    index: int = header + 1
    while lines[index].strip() != "":
        fields: List[str] = lines[index].split(";")
        fields[dutap] = "200"
        lines[index] = ";".join(fields)
        index += 1
    path: Path = tmp_path / "steep.dgs"
    path.write_bytes("\n".join(lines).encode("utf-8"))
    opened: FileOpen = FileOpen(file_name=str(path), options=FileOpenOptions(file_type=FileType.DGS))
    opened.open()
    assert any("tap table rejected" in entry.msg for entry in opened.logger.entries)


def test_tap_control_stays_without_a_solved_position(tmp_path: Path) -> None:
    """Keep the Vm control of a DGS that has no solved tap position, and freeze it otherwise.

    :param tmp_path: Temporary folder fixture.
    :return: None.
    """
    source: Path = DGS_FOLDER / "hvdc_vsc_v3_complete_static_dynamic.dgs"
    solved: MultiCircuit = FileOpen(file_name=str(source), options=FileOpenOptions(file_type=FileType.DGS)).open()
    assert all(branch.tap_module_control_mode != TapModuleControl.Vm for branch in solved.transformers2w)
    unsolved_path: Path = tmp_path / "unsolved.dgs"
    unsolved_path.write_bytes(source.read_bytes().replace(b"c:nntap", b"c:unused"))
    unsolved: MultiCircuit = FileOpen(file_name=str(unsolved_path), options=FileOpenOptions(file_type=FileType.DGS)).open()
    assert all(branch.tap_module_control_mode == TapModuleControl.Vm for branch in unsolved.transformers2w)


def test_absolute_capability_curve_ignores_the_machine_rating() -> None:
    """Take MW and Mvar as they are when the curve is not in per unit.

    :return: None.
    """
    curve: IntQlim = IntQlim()
    curve.active_power = [0.0]
    curve.reactive_power_min = [-1.0]
    curve.reactive_power_max = [1.0]
    points: np.ndarray = _get_capability_points(curve=curve, source=ElmSym(), snom=10.0)
    assert points.tolist() == [[0.0, -1.0, 1.0]]


def _open_with_nominal_frequency(frequency: str, folder: Path) -> MultiCircuit:
    """Open a small repository DGS after rewriting the ``frnom`` of its ElmNet.

    :param frequency: Text written in the ``frnom`` column.
    :param folder: Temporary folder receiving the rewritten file.
    :return: Opened circuit.
    """
    text: str = (DGS_FOLDER / "SinglePhasePowerGroundedStar.dgs").read_bytes().decode("utf-8")
    lines: List[str] = text.split("\n")
    header: int = [index for index, line in enumerate(lines) if line.startswith("$$ElmNet;")][0]
    fields: List[str] = lines[header + 1].split(";")
    fields[4] = frequency
    lines[header + 1] = ";".join(fields)
    path: Path = folder / "frequency.dgs"
    path.write_bytes("\n".join(lines).encode("utf-8"))
    return FileOpen(file_name=str(path), options=FileOpenOptions(file_type=FileType.DGS)).open()


@pytest.mark.parametrize("frnom, expected", [("60", 60.0), ("0", 50.0)])
def test_elmnet_frequency_owns_the_system_frequency(tmp_path: Path, frnom: str, expected: float) -> None:
    """Take the system frequency from the ElmNet, and refuse a null one.

    :param tmp_path: Temporary folder fixture.
    :param frnom: Text written in the ``frnom`` column.
    :param expected: Expected system frequency in Hz.
    :return: None.
    """
    assert _open_with_nominal_frequency(frnom, tmp_path).fBase == expected


def test_every_machine_takes_the_nominal_frequency() -> None:
    """Give generators and batteries the same nominal frequency.

    :return: None.
    """
    grid: MultiCircuit = MultiCircuit()
    bus: Bus = Bus(name="Bus")
    grid.add_bus(bus)
    generator: Generator = Generator(name="Machine", freq=50.0)
    battery: Battery = Battery(name="Storage")
    grid.add_generator(bus=bus, api_obj=generator)
    grid.add_battery(bus=bus, api_obj=battery)
    _set_generators_nominal_frequency(grid=grid, frequency=60.0)
    assert generator.freq == 60.0
    assert battery.freq == 60.0


def _build_unbuildable_block(name: str) -> Block:
    """Build a block that declares a generator interface but cannot build a model.

    :param name: Block name.
    :return: Block rejected by the template setters.
    """
    block: Block = Block(name=name)
    block.in_vars = [Var(name="Vm", reference=VarPowerFlowReferenceType.Vm),
                     Var(name="Va", reference=VarPowerFlowReferenceType.Va)]
    block.external_mapping = {VarPowerFlowReferenceType.P: Var(name="Pg"), VarPowerFlowReferenceType.Q: Var(name="Qg")}
    block.out_vars = None
    return block


def test_rejected_rms_template_is_not_left_on_its_host() -> None:
    """Leave the host empty when its RMS template cannot build a model.

    :return: None.
    """
    host: Generator = Generator(name="Host")
    host.set_var_factory(VarFactory())
    template: RmsModelTemplate = RmsModelTemplate(name="Broken")
    template.block = _build_unbuildable_block("Broken")
    with pytest.raises((TypeError, ValueError, KeyError)):
        assign_import_template(host, template)
    assert host.rms_template is None


class _UnattachableGenerator(Generator):
    """Generator whose bus refuses the attachment that follows the model publication."""

    @property
    def bus(self) -> Bus:
        """Refuse every read of the connection bus.

        :return: Never returns.
        """
        raise ValueError("Bus refuses the attachment")

    @bus.setter
    def bus(self, val: Bus | None) -> None:
        """Ignore the connection bus.

        :param val: Connection bus.
        :return: None.
        """
        pass


def test_rejected_emt_template_restores_the_previous_model() -> None:
    """Bring back the previous EMT model when attaching the new one fails.

    The EMT setter publishes the new model before it attaches it to the bus.

    :return: None.
    """
    host: Generator = _UnattachableGenerator(name="Host")
    host.set_var_factory(VarFactory())
    previous_model: Block = host.emt_model
    template: EmtModelTemplate = EmtModelTemplate(name="Unattachable")
    template.block = Block(name="Unattachable")
    with pytest.raises(ValueError):
        assign_import_template(host, template)
    assert host.emt_template is None
    assert host.emt_model is previous_model


def test_host_rejection_warns_and_retires_the_template() -> None:
    """Report a rejected template and keep it out of the assignable catalogue.

    :return: None.
    """
    grid: MultiCircuit = MultiCircuit()
    bus: Bus = Bus(name="Bus")
    grid.add_bus(bus)
    host: Generator = Generator(name="Host", idtag="GEN_FID")
    grid.add_generator(bus=bus, api_obj=host)
    logger: Logger = Logger()
    importer: DynamicModelImport = DynamicModelImport(DgsCircuit(), grid, DynamicSimulationMode.RMS, logger)
    template: RmsModelTemplate = RmsModelTemplate(name="Broken")
    template.block = _build_unbuildable_block("Broken")
    template.tpe = DeviceType.GeneratorDevice
    activated: bool = importer._activate_dgs_direct_template(
        template_obj=template,
        host_identity=("GEN_FID", DeviceType.GeneratorDevice, "ElmGenstat", "Host"),
        native_kind=None,
    )
    assert not activated
    assert host.rms_template is None
    assert template.tpe == DeviceType.DynamicModelHostDevice
    assert any("rejected its template" in entry.msg for entry in logger.entries)
