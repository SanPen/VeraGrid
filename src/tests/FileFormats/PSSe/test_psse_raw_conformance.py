# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Regression tests for PSSE RAW parser and writer conformance."""

from pathlib import Path

import numpy as np
import VeraGridEngine.Devices as dev
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.IO.raw.versioned.v34.switched_shunt import RawSwitchedShuntV34
from VeraGridEngine.IO.raw.versioned.v35.switched_shunt import RawSwitchedShuntV35
from VeraGridEngine.IO.raw.versioned.v36.switched_shunt import RawSwitchedShuntV36
from VeraGridEngine.IO.raw.versioned.base.area import RawArea
from VeraGridEngine.IO.raw.versioned.base.bus import RawBus
from VeraGridEngine.IO.raw.versioned.base.facts import RawFACTS
from VeraGridEngine.IO.raw.versioned.base.generator import RawGenerator
from VeraGridEngine.IO.raw.versioned.base.gne_device import RawGneDevice
from VeraGridEngine.IO.raw.versioned.base.multi_section_line import RawMultiLineSection
from VeraGridEngine.IO.raw.versioned.base.switched_shunt import RawSwitchedShunt
from VeraGridEngine.IO.raw.versioned.base.two_terminal_dc_line import RawTwoTerminalDCLine
from VeraGridEngine.IO.raw.versioned.base.vsc_dc_line import RawVscDCLine
from VeraGridEngine.IO.raw.versioned.v34.system_switching_device import RawSystemSwitchingDeviceV34
from VeraGridEngine.IO.raw.versioned.v35.system_switching_device import RawSystemSwitchingDeviceV35
from VeraGridEngine.IO.raw.versioned.v36.system_switching_device import RawSystemSwitchingDeviceV36
from VeraGridEngine.IO.raw.versioned.v35.equipment_terminal import RawEquipmentTerminalV35
from VeraGridEngine.IO.raw.versioned.v35.substation_switching_device import RawSubstationSwitchingDeviceV35
from VeraGridEngine.IO.raw.versioned.v29.transformer import RawTransformerV29 as RawTransformer
from VeraGridEngine.IO.raw.versioned.v33.branch import RawBranchV33
from VeraGridEngine.IO.raw.versioned.v35.branch import RawBranchV35
from VeraGridEngine.IO.raw.versioned.v35.node import RawNodeV35
from VeraGridEngine.IO.raw.versioned.v35.induction_machine import RawInductionMachineV35
from VeraGridEngine.IO.raw.versioned.v35.gne_device import RawGneDeviceV35
from VeraGridEngine.IO.raw.versioned.v36.load import RawLoadV36
from VeraGridEngine.IO.raw.versioned.v36.fixed_shunt import RawFixedShuntV36
from VeraGridEngine.IO.raw.versioned.v36.generator import RawGeneratorV36
from VeraGridEngine.IO.raw.versioned.v34.transformer import RawTransformerV34
from VeraGridEngine.IO.raw.versioned.v35.transformer import RawTransformerV35
from VeraGridEngine.IO.raw.versioned.v34.vsc_dc_line import RawVscDCLineV34
from VeraGridEngine.IO.raw.versioned.v35.vsc_dc_line import RawVscDCLineV35
from VeraGridEngine.IO.raw.raw_parser_writer import interpret_line, read_and_split, read_raw
from VeraGridEngine.IO.raw.raw_to_veragrid import get_veragrid_transformer, psse_to_veragrid
from VeraGridEngine.IO.raw.veragrid_to_raw import (RawNodeBreakerExportData, append_psse_terminal,
                                                   get_psse_substation_switch, veragrid_to_raw)
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import PsseTopologyExportMode, TapModuleControl


def test_psse35_branch_parser_keeps_ownership_fields() -> None:
    """PSSE 35 branch parsing must preserve owner/fraction pairs from the input row."""

    branch = RawBranchV35()
    row = [101, 102, "1", 0.001, 0.01, 0.0, 100.0, 110.0, 120.0, 0.0, 0.0, 0.0, 0.0, 1, 1, 5.0,
           42, 0.5, 18, 0.5, 0, 0.0, 0, 0.0]

    # This reproduces the reported short PSSE 35 branch record that carries ownership data.
    branch.parse([row], version=35, logger=Logger())

    assert branch.O1 == 42
    assert branch.F1 == 0.5
    assert branch.O2 == 18
    assert branch.F2 == 0.5
    assert branch.O3 == 0
    assert branch.F3 == 0.0
    assert branch.O4 == 0
    assert branch.F4 == 0.0


def test_branch_ownership_helper_accepts_single_owner_pair() -> None:
    """Branch ownership parsing must accept PSSE tails with a single owner/fraction pair."""

    branch = RawBranchV35()

    branch.parse_ownership_fields([42, 0.5])

    assert branch.O1 == 42
    assert branch.F1 == 0.5
    assert branch.O2 == 0
    assert branch.F2 == 0.0
    assert branch.O3 == 0
    assert branch.F3 == 0.0
    assert branch.O4 == 0
    assert branch.F4 == 0.0


def test_read_raw_keeps_psse35_system_wide_records_out_of_bus_section(tmp_path: Path) -> None:
    """PSSE 35 system-wide records must not be parsed as bus records."""

    raw_text: str = "\n".join(
        [
            "0,100.0,35,0,0,60.0",
            "Test case",
            "Test case 2",
            "GENERAL, THRSHZ=0.0001",
            "SOLVER, FNSL, ACTAPS=0",
            "0 / END OF SYSTEM-WIDE DATA, BEGIN BUS DATA",
            "1,'BUS1',230.0,3,1,1,1,1.0,0.0,1.1,0.9,1.1,0.9",
            "0 / END OF BUS DATA",
            "Q",
        ]
    )
    raw_path: Path = tmp_path / "psse35_system_wide.raw"
    raw_path.write_text(raw_text, encoding="utf-8")

    sections_dict = read_and_split(str(raw_path))
    psse_circuit = read_raw(str(raw_path), logger=Logger())

    assert "system-wide" in sections_dict
    assert len(sections_dict["system-wide"]) == 2
    assert len(sections_dict["bus"]) == 1
    assert len(psse_circuit.buses) == 1
    assert psse_circuit.buses[0].I == 1


def test_switched_shunt_writer_uses_psse35_status_triplets() -> None:
    """PSSE 35 switched shunts must write S/N/B triplets for each block."""

    switched_shunt = RawSwitchedShuntV35()
    switched_shunt.I = 10
    switched_shunt.ID = "A1"
    switched_shunt.MODSW = 1
    switched_shunt.ADJM = 0
    switched_shunt.STAT = 1
    switched_shunt.VSWHI = 1.05
    switched_shunt.VSWLO = 0.95
    switched_shunt.SWREG = 11
    switched_shunt.NREG = 0
    switched_shunt.RMPCT = 100.0
    switched_shunt.RMIDNT = ""
    switched_shunt.BINIT = 0.25
    switched_shunt.S1 = 1
    switched_shunt.N1 = 3
    switched_shunt.B1 = 0.25

    raw_values = interpret_line(switched_shunt.get_raw_line(35))

    assert len(raw_values) == 36
    assert raw_values[12:15] == [1, 3, 0.25]


def test_switched_shunt_writer_uses_psse36_name_field() -> None:
    """PSSE 36 switched shunts must write NAME before the S/N/B triplets."""

    switched_shunt = RawSwitchedShuntV36()
    switched_shunt.I = 10
    switched_shunt.ID = "A1"
    switched_shunt.MODSW = 1
    switched_shunt.ADJM = 0
    switched_shunt.STAT = 1
    switched_shunt.VSWHI = 1.05
    switched_shunt.VSWLO = 0.95
    switched_shunt.SWREG = 11
    switched_shunt.NREG = 0
    switched_shunt.RMPCT = 100.0
    switched_shunt.RMIDNT = ""
    switched_shunt.BINIT = 0.25
    switched_shunt.NAME = "SVD1"
    switched_shunt.S1 = 1
    switched_shunt.N1 = 3
    switched_shunt.B1 = 0.25

    raw_values = interpret_line(switched_shunt.get_raw_line(36))

    assert len(raw_values) == 37
    assert raw_values[12] == "SVD1"
    assert raw_values[13:16] == [1, 3, 0.25]


def test_switched_shunt_writer_uses_swrem_before_psse35() -> None:
    """PSSE 34 switched shunts must write SWREM instead of the PSSE 35 SWREG field."""

    switched_shunt = RawSwitchedShuntV34()
    switched_shunt.I = 20
    switched_shunt.MODSW = 1
    switched_shunt.ADJM = 0
    switched_shunt.STAT = 1
    switched_shunt.VSWHI = 1.05
    switched_shunt.VSWLO = 0.95
    switched_shunt.SWREM = 77
    switched_shunt.SWREG = 88
    switched_shunt.RMPCT = 100.0
    switched_shunt.BINIT = 0.10

    raw_values = interpret_line(switched_shunt.get_raw_line(34))

    assert raw_values[6] == 77


def test_vsc_dc_line_writer_uses_version_specific_control_fields() -> None:
    """PSSE 34 uses REMOT while PSSE 35 uses VSREG/NREG in VSC dc records."""

    vsc_34 = RawVscDCLineV34()
    vsc_35 = RawVscDCLineV35()

    for vsc_line in (vsc_34, vsc_35):
        vsc_line.NAME = "VSC1"
        vsc_line.MDC = 1
        vsc_line.RDC = 2.5
        vsc_line.IBUS1 = 101
        vsc_line.TYPE1 = 1
        vsc_line.MODE1 = 1
        vsc_line.DCSET1 = 50.0
        vsc_line.ACSET1 = 1.01
        vsc_line.ALOSS1 = 1.0
        vsc_line.BLOSS1 = 2.0
        vsc_line.MINLOSS1 = 3
        vsc_line.SMAX1 = 120.0
        vsc_line.IMAX1 = 400.0
        vsc_line.PWF1 = 0.5
        vsc_line.MAXQ1 = 40.0
        vsc_line.MINQ1 = -40.0
        vsc_line.RMPCT1 = 100.0
        vsc_line.IBUS2 = 102
        vsc_line.TYPE2 = 2
        vsc_line.MODE2 = 1
        vsc_line.DCSET2 = -50.0
        vsc_line.ACSET2 = 0.99
        vsc_line.ALOSS2 = 1.0
        vsc_line.BLOSS2 = 2.0
        vsc_line.MINLOSS2 = 3
        vsc_line.SMAX2 = 120.0
        vsc_line.IMAX2 = 400.0
        vsc_line.PWF2 = 0.5
        vsc_line.MAXQ2 = 40.0
        vsc_line.MINQ2 = -40.0
        vsc_line.RMPCT2 = 100.0

    vsc_34.REMOT1 = 201
    vsc_34.REMOT2 = 202
    vsc_35.VSREG1 = 301
    vsc_35.NREG1 = 1
    vsc_35.VSREG2 = 302
    vsc_35.NREG2 = 2

    raw_values_34_line_2 = interpret_line(vsc_34.get_raw_line(34).splitlines()[1])
    raw_values_35_line_2 = interpret_line(vsc_35.get_raw_line(35).splitlines()[1])

    assert len(raw_values_34_line_2) == 15
    assert raw_values_34_line_2[13] == 201
    assert len(raw_values_35_line_2) == 16
    assert raw_values_35_line_2[13:15] == [301, 1]


def test_system_switching_device_writer_supports_psse34_and_psse35() -> None:
    """System switching device export must use the actual property names for both supported revisions."""

    switching_device_34 = RawSystemSwitchingDeviceV34()
    switching_device_35 = RawSystemSwitchingDeviceV35()

    for switching_device in (switching_device_34, switching_device_35):
        switching_device.I = 1
        switching_device.J = 2
        switching_device.CKT = "1"
        switching_device.X = 0.001
        switching_device.RATE1 = 100.0
        switching_device.STATUS = 1
        switching_device.NSTATUS = 0
        switching_device.METERED = 2
        switching_device.STYPE = 3
        switching_device.NAME = "SW1"

    raw_values_34 = interpret_line(switching_device_34.get_raw_line(34))
    raw_values_35 = interpret_line(switching_device_35.get_raw_line(35))

    assert switching_device_34.CKTID == "1"
    assert raw_values_34[16:21] == [1, 0, 2, 3, "SW1"]
    assert raw_values_35[16:21] == [1, 0, 2, 3, "SW1"]


def test_system_switching_device_writer_uses_psse36_rating_set_name() -> None:
    """PSSE 36 system switching devices must write RSETNAM instead of RATE fields."""

    switching_device = RawSystemSwitchingDeviceV36()
    switching_device.I = 1
    switching_device.J = 2
    switching_device.CKT = "1"
    switching_device.X = 0.0001
    switching_device.RSETNAM = "BREAKER_01"
    switching_device.STATUS = 1
    switching_device.NSTATUS = 1
    switching_device.METERED = 2
    switching_device.STYPE = 3
    switching_device.NAME = "SW1"

    raw_values = interpret_line(switching_device.get_raw_line(36))

    assert len(raw_values) == 10
    assert raw_values[4] == "BREAKER_01"
    assert raw_values[5:10] == [1, 1, 2, 3, "SW1"]


def test_psse35_substation_block_maps_load_to_node_bus(tmp_path: Path) -> None:
    """PSSE 35 substation terminals must attach loads to the imported node bus."""

    raw_text: str = "\n".join(
        [
            "0,100.0,35,0,0,60.0",
            "Node breaker case",
            "Node breaker case 2",
            "GENERAL, THRSHZ=0.0001",
            "0 / END OF SYSTEM-WIDE DATA, BEGIN BUS DATA",
            "101,'BUS101',230.0,1,1,1,1,1.0,0.0,1.1,0.9,1.1,0.9",
            "0 / END OF BUS DATA, BEGIN LOAD DATA",
            "101,'1',1,1,1,10.0,2.0,0.0,0.0,0.0,0.0,1,1,0,0,0,'',''",
            "0 / END OF LOAD DATA, BEGIN SUBSTATION DATA",
            "1,'SUB1',0.0,0.0,0.1",
            "1,'NODE1',101,1,1.0,0.0",
            "0",
            "0",
            "101,1,'L','1'",
            "0",
            "0",
            "0 / END OF SUBSTATION DATA",
            "Q",
        ]
    )
    raw_path: Path = tmp_path / "psse35_node_load.raw"
    raw_path.write_text(raw_text, encoding="utf-8")

    psse_circuit = read_raw(str(raw_path), logger=Logger())
    circuit = psse_to_veragrid(psse_circuit, logger=Logger())

    assert len(psse_circuit.substations) == 1
    assert len(psse_circuit.nodes) == 1
    assert len(psse_circuit.equipment_terminals) == 1
    assert len(circuit.substations) == 1
    assert len(circuit.buses) == 1
    assert len(circuit.loads) == 1
    assert circuit.loads[0].bus == circuit.buses[0]
    assert circuit.buses[0].code == "101:1"


def test_psse35_substation_switch_is_imported_between_node_buses(tmp_path: Path) -> None:
    """PSSE 35 substation switching devices must become VeraGrid switches between node buses."""

    raw_text: str = "\n".join(
        [
            "0,100.0,35,0,0,60.0",
            "Node breaker switch case",
            "Node breaker switch case 2",
            "GENERAL, THRSHZ=0.0001",
            "0 / END OF SYSTEM-WIDE DATA, BEGIN BUS DATA",
            "101,'BUS101',230.0,1,1,1,1,1.0,0.0,1.1,0.9,1.1,0.9",
            "0 / END OF BUS DATA, BEGIN SUBSTATION DATA",
            "1,'SUB1',0.0,0.0,0.1",
            "1,'NODE1',101,1,1.0,0.0",
            "2,'NODE2',101,1,1.0,0.0",
            "0",
            "1,2,'1','BRK_12',2,1,1,0.0001,0.0,0.0,0.0",
            "0",
            "0",
            "0",
            "0 / END OF SUBSTATION DATA",
            "Q",
        ]
    )
    raw_path: Path = tmp_path / "psse35_node_switch.raw"
    raw_path.write_text(raw_text, encoding="utf-8")

    psse_circuit = read_raw(str(raw_path), logger=Logger())
    circuit = psse_to_veragrid(psse_circuit, logger=Logger())
    switches = circuit.get_switches()

    assert len(psse_circuit.substation_switching_devices) == 1
    assert len(circuit.buses) == 2
    assert len(switches) == 1
    assert switches[0].bus_from.code == "101:1"
    assert switches[0].bus_to.code == "101:2"


def test_psse35_substation_switch_export_handles_missing_from_substation() -> None:
    """PSSE substation switch export must not fail when the from-bus substation is missing."""

    substation = dev.Substation(name="SUB1")
    bus_from = dev.Bus(name="B1", Vnom=110.0, code="101")
    bus_to = dev.Bus(name="B2", Vnom=110.0, code="102", substation=substation)
    switch = dev.Switch(bus_from=bus_from, bus_to=bus_to, name="SW12", active=True)

    node_breaker_data = RawNodeBreakerExportData()
    node_breaker_data.substation_number_by_substation[substation] = 7
    node_breaker_data.node_number_by_bus[bus_from] = 11
    node_breaker_data.node_number_by_bus[bus_to] = 12

    psse_switch = get_psse_substation_switch(switch=switch,
                                             node_breaker_data=node_breaker_data,
                                             ckt=1,
                                             version=35)

    assert psse_switch.ISUB == 7
    assert psse_switch.NI == 11
    assert psse_switch.NJ == 12


def test_psse35_equipment_terminal_export_handles_missing_substation() -> None:
    """PSSE equipment terminal export must not fail when the bus substation is missing."""

    bus = dev.Bus(name="B1", Vnom=110.0, code="101")
    node_breaker_data = RawNodeBreakerExportData()
    node_breaker_data.node_number_by_bus[bus] = 9

    append_psse_terminal(node_breaker_data=node_breaker_data,
                         bus=bus,
                         type_code="L",
                         eqid="1",
                         version=35,
                         ibus=101)

    assert len(node_breaker_data.equipment_terminals) == 1
    assert node_breaker_data.equipment_terminals[0].ISUB == 0
    assert node_breaker_data.equipment_terminals[0].NI == 9


def test_veragrid_to_raw_uses_profile_values_when_t_idx_is_provided() -> None:
    """RAW export must use profile values when ``t_idx`` is provided."""

    circuit = MultiCircuit()

    bus_1 = dev.Bus(name="B1", Vnom=110.0, code="101", vmin=0.91, vmax=1.09)
    bus_2 = dev.Bus(name="B2", Vnom=110.0, code="102", vmin=0.92, vmax=1.08)
    bus_1.Vmin_prof = np.array([0.93, 0.95])
    bus_1.Vmax_prof = np.array([1.07, 1.05])
    circuit.add_bus(bus_1)
    circuit.add_bus(bus_2)

    load = dev.Load(name="LD1", P=10.0, Q=2.0, G=0.1, B=0.2, Ir=0.3, Ii=0.4, active=True)
    load.P_prof = np.array([11.0, 21.0])
    load.Q_prof = np.array([3.0, 4.0])
    load.G_prof = np.array([0.11, 0.22])
    load.B_prof = np.array([0.21, 0.32])
    load.Ir_prof = np.array([0.31, 0.42])
    load.Ii_prof = np.array([0.41, 0.52])
    load.active_prof = np.array([True, False])
    circuit.add_load(bus=bus_1, api_obj=load)

    line = dev.Line(bus_from=bus_1, bus_to=bus_2, name="L12", r=0.01, x=0.05, b=0.001, rate=100.0, active=True)
    line.rate_prof = np.array([110.0, 210.0])
    line.contingency_factor_prof = np.array([1.1, 1.2])
    line.protection_rating_factor_prof = np.array([1.3, 1.4])
    line.active_prof = np.array([True, False])
    circuit.add_line(line)

    snapshot_export = veragrid_to_raw(grid=circuit, version=35, logger=Logger(), t_idx=None)
    profile_export = veragrid_to_raw(grid=circuit, version=35, logger=Logger(), t_idx=1)

    assert snapshot_export.buses[0].EVLO == 0.91
    assert profile_export.buses[0].EVLO == 0.95
    assert snapshot_export.buses[0].EVHI == 1.09
    assert profile_export.buses[0].EVHI == 1.05

    assert snapshot_export.loads[0].PL == 10.0
    assert profile_export.loads[0].PL == 21.0
    assert snapshot_export.loads[0].QL == 2.0
    assert profile_export.loads[0].QL == 4.0
    assert snapshot_export.loads[0].YP == 0.1
    assert profile_export.loads[0].YP == 0.22
    assert snapshot_export.loads[0].YQ == 0.2
    assert profile_export.loads[0].YQ == 0.32
    assert snapshot_export.loads[0].IP == 0.3
    assert profile_export.loads[0].IP == 0.42
    assert snapshot_export.loads[0].IQ == -0.4
    assert profile_export.loads[0].IQ == -0.52
    assert snapshot_export.loads[0].STATUS == 1
    assert profile_export.loads[0].STATUS == 0

    assert snapshot_export.branches[0].RATE1 == 100.0
    assert profile_export.branches[0].RATE1 == 210.0
    assert snapshot_export.branches[0].RATE2 == 100.0
    assert profile_export.branches[0].RATE2 == 252.0
    assert snapshot_export.branches[0].RATE3 == 140.0
    assert profile_export.branches[0].RATE3 == 294.0
    assert snapshot_export.branches[0].ST == 1
    assert profile_export.branches[0].ST == 0


def test_psse35_export_keeps_plain_bus_branch_mode_by_default() -> None:
    """PSSE 35 export must keep the direct bus model unless node-breaker mode is requested."""

    circuit = MultiCircuit()
    substation = dev.Substation(name="SUB1")
    circuit.add_substation(substation)

    bus_1 = dev.Bus(name="B1", Vnom=110.0, code="101", substation=substation)
    bus_2 = dev.Bus(name="B2", Vnom=110.0, code="102", substation=substation)
    circuit.add_bus(bus_1)
    circuit.add_bus(bus_2)

    switch = dev.Switch(bus_from=bus_1, bus_to=bus_2, name="SW12", active=True)
    circuit.add_switch(switch)

    psse_circuit = veragrid_to_raw(circuit,
                                   version=35,
                                   logger=Logger(),
                                   topology_mode=PsseTopologyExportMode.BusBranch)

    assert len(psse_circuit.buses) == 2
    assert len(psse_circuit.substations) == 0
    assert len(psse_circuit.nodes) == 0
    assert len(psse_circuit.substation_switching_devices) == 0
    assert len(psse_circuit.switches) == 1


def test_psse35_export_node_breaker_mode_maps_substation_buses_to_nodes() -> None:
    """PSSE 35 node-breaker export must map each substation bus to its own node."""

    circuit = MultiCircuit()
    substation = dev.Substation(name="SUB1")
    circuit.add_substation(substation)

    bus_1 = dev.Bus(name="B1", Vnom=110.0, code="101", substation=substation)
    bus_2 = dev.Bus(name="B2", Vnom=110.0, code="102", substation=substation)
    bus_3 = dev.Bus(name="B3", Vnom=110.0, code="103")
    circuit.add_bus(bus_1)
    circuit.add_bus(bus_2)
    circuit.add_bus(bus_3)

    switch = dev.Switch(bus_from=bus_1, bus_to=bus_2, name="SW12", active=True)
    line = dev.Line(bus_from=bus_2, bus_to=bus_3, name="L23", r=0.01, x=0.05, b=0.0, rate=100.0)
    load = dev.Load(name="LD2", P=10.0, Q=2.0)
    circuit.add_switch(switch)
    circuit.add_line(line)
    circuit.add_load(bus=bus_2, api_obj=load)

    psse_circuit = veragrid_to_raw(circuit,
                                   version=35,
                                   logger=Logger(),
                                   topology_mode=PsseTopologyExportMode.NodeBreaker)

    assert len(psse_circuit.substations) == 1
    assert len(psse_circuit.nodes) == 2
    assert len(psse_circuit.buses) == 3
    assert len(psse_circuit.substation_switching_devices) == 1
    assert len(psse_circuit.switches) == 0
    assert len(psse_circuit.equipment_terminals) == 2
    assert psse_circuit.nodes[0].I != psse_circuit.nodes[1].I
    assert psse_circuit.nodes[0].NI != psse_circuit.nodes[1].NI


def test_psse36_load_fixed_shunt_and_generator_include_new_name_fields() -> None:
    """PSSE 36 adds NAME to loads and fixed shunts, plus DROOPNAME/NAME to generators."""

    load = RawLoadV36()
    load.I = 101
    load.ID = "1"
    load.STATUS = 1
    load.AREA = 1
    load.ZONE = 1
    load.OWNER = 1
    load.LOADTYPE = "IND"
    load.NAME = "LOAD_A"

    fixed_shunt = RawFixedShuntV36()
    fixed_shunt.I = 102
    fixed_shunt.ID = "1"
    fixed_shunt.STATUS = 1
    fixed_shunt.NAME = "FSH_A"

    generator = RawGeneratorV36()
    generator.I = 103
    generator.ID = "1"
    generator.STAT = 1
    generator.O1 = 1
    generator.F1 = 1.0
    generator.DROOPNAME = "DROOP_A"
    generator.NAME = "GEN_A"

    load_values = interpret_line(load.get_raw_line(36))
    fixed_shunt_values = interpret_line(fixed_shunt.get_raw_line(36))
    generator_values = interpret_line(generator.get_raw_line(36))

    assert len(load_values) == 19
    assert load_values[-1] == "LOAD_A"
    assert len(fixed_shunt_values) == 6
    assert fixed_shunt_values[-1] == "FSH_A"
    assert len(generator_values) == 32
    assert generator_values[-2:] == ["DROOP_A", "GEN_A"]


def test_transformer_writer_uses_version_specific_psse34_and_psse35_layouts() -> None:
    """PSSE 34 omits NODE and two-winding ZCOD, while PSSE 35 keeps NODE but still omits two-winding ZCOD."""

    transformer_34 = RawTransformerV34()
    transformer_35 = RawTransformerV35()

    for transformer in (transformer_34, transformer_35):
        transformer.windings = 2
        transformer.I = 1
        transformer.J = 2
        transformer.K = 0
        transformer.CKT = "1"
        transformer.CW = 1
        transformer.CZ = 1
        transformer.CM = 1
        transformer.MAG1 = 0.0
        transformer.MAG2 = 0.0
        transformer.NMETR = 2
        transformer.NAME = "TX"
        transformer.STAT = 1
        transformer.O1 = 1
        transformer.F1 = 1.0
        transformer.VECGRP = "YN"
        transformer.ZCOD = 1
        transformer.R1_2 = 0.01
        transformer.X1_2 = 0.10
        transformer.SBASE1_2 = 100.0
        transformer.WINDV1 = 1.0
        transformer.NOMV1 = 220.0
        transformer.ANG1 = 0.0
        transformer.RATE1_1 = 100.0
        transformer.RATE1_2 = 101.0
        transformer.RATE1_3 = 102.0
        transformer.RATE1_4 = 103.0
        transformer.RATE1_5 = 104.0
        transformer.RATE1_6 = 105.0
        transformer.RATE1_7 = 106.0
        transformer.RATE1_8 = 107.0
        transformer.RATE1_9 = 108.0
        transformer.RATE1_10 = 109.0
        transformer.RATE1_11 = 110.0
        transformer.RATE1_12 = 111.0
        transformer.COD1 = 1
        transformer.CONT1 = 11
        transformer.NODE1 = 7
        transformer.RMA1 = 1.1
        transformer.RMI1 = 0.9
        transformer.VMA1 = 1.1
        transformer.VMI1 = 0.9
        transformer.NTP1 = 33
        transformer.TAB1 = 0
        transformer.CR1 = 0.0
        transformer.CX1 = 0.0
        transformer.CNXA1 = 0.0
        transformer.WINDV2 = 1.0
        transformer.NOMV2 = 110.0

    raw_values_34_line_1 = interpret_line(transformer_34.get_raw_line(34).splitlines()[0])
    raw_values_34_line_3 = interpret_line(transformer_34.get_raw_line(34).splitlines()[2])
    raw_values_35_line_1 = interpret_line(transformer_35.get_raw_line(35).splitlines()[0])
    raw_values_35_line_3 = interpret_line(transformer_35.get_raw_line(35).splitlines()[2])

    assert len(raw_values_34_line_1) == 21
    assert len(raw_values_34_line_3) == 26
    assert len(raw_values_35_line_1) == 21
    assert len(raw_values_35_line_3) == 27
    assert raw_values_35_line_3[17] == 7


def test_psse_cw3_two_winding_import_keeps_tap_ratio_on_bus_base() -> None:
    """
    CW=3 two-winding imports must keep the nominal-voltage ratio out of the effective tap.
    See: https://github.com/SanPen/VeraGrid/issues/463
    """

    logger: Logger = Logger()
    psse_bus_dict: dict[int, dev.Bus] = dict()
    psse_bus_dict[1] = dev.Bus(name="HV", code="1", Vnom=275.0)
    psse_bus_dict[2] = dev.Bus(name="LV", code="2", Vnom=1.0)

    # This matches the reported 275 kV -> 1 kV step-up case where the tap should stay near unity.
    raw_transformer: RawTransformerV35 = RawTransformerV35()
    raw_transformer.windings = 2
    raw_transformer.I = 1
    raw_transformer.J = 2
    raw_transformer.K = 0
    raw_transformer.CKT = "1"
    raw_transformer.NAME = "CW3_2W"
    raw_transformer.CW = 3
    raw_transformer.CZ = 1
    raw_transformer.CM = 1
    raw_transformer.R1_2 = 0.0
    raw_transformer.X1_2 = 5.0e-3
    raw_transformer.SBASE1_2 = 100.0
    raw_transformer.WINDV1 = 1.075
    raw_transformer.NOMV1 = 275.0
    raw_transformer.WINDV2 = 1.0
    raw_transformer.NOMV2 = 1.0

    result: tuple[dev.Transformer2W | dev.Transformer3W, int] = get_veragrid_transformer(
        psse_elm=raw_transformer,
        psse_bus_dict=psse_bus_dict,
        Sbase=100.0,
        logger=logger,
        adjust_taps_to_discrete_positions=False,
        simple_naming=True,
        flatten_virtual_taps=False,
    )
    imported_transformer: dev.Transformer2W | dev.Transformer3W = result[0]
    winding_count: int = result[1]

    assert winding_count == 2
    assert np.isclose(imported_transformer.tap_module, 1.075)


def test_psse_phase_shifter_with_single_tap_position_imports_without_dividing_by_zero() -> None:
    """
    NTP1=1 phase shifters must import as fixed single-position changers without crashing.
    See: https://github.com/SanPen/VeraGrid/issues/463
    """

    logger: Logger = Logger()
    psse_bus_dict: dict[int, dev.Bus] = dict()
    psse_bus_dict[1] = dev.Bus(name="FROM", code="1", Vnom=110.0)
    psse_bus_dict[2] = dev.Bus(name="TO", code="2", Vnom=110.0)

    # COD1=3 takes the phase-shifter path that previously divided by zero when NTP1 was 1.
    raw_transformer: RawTransformerV35 = RawTransformerV35()
    raw_transformer.windings = 2
    raw_transformer.I = 1
    raw_transformer.J = 2
    raw_transformer.K = 0
    raw_transformer.CKT = "1"
    raw_transformer.NAME = "NTP1_EQ_1"
    raw_transformer.CW = 1
    raw_transformer.CZ = 1
    raw_transformer.CM = 1
    raw_transformer.R1_2 = 0.0
    raw_transformer.X1_2 = 0.1
    raw_transformer.SBASE1_2 = 100.0
    raw_transformer.WINDV1 = 1.0
    raw_transformer.NOMV1 = 110.0
    raw_transformer.WINDV2 = 1.0
    raw_transformer.NOMV2 = 110.0
    raw_transformer.COD1 = 3
    raw_transformer.RMA1 = 10.0
    raw_transformer.NTP1 = 1

    result: tuple[dev.Transformer2W | dev.Transformer3W, int] = get_veragrid_transformer(
        psse_elm=raw_transformer,
        psse_bus_dict=psse_bus_dict,
        Sbase=100.0,
        logger=logger,
        adjust_taps_to_discrete_positions=False,
        simple_naming=True,
        flatten_virtual_taps=False,
    )
    imported_transformer: dev.Transformer2W | dev.Transformer3W = result[0]
    winding_count: int = result[1]

    assert winding_count == 2
    assert imported_transformer.tap_changer.total_positions == 1
    assert imported_transformer.tap_changer.neutral_position == 0
    assert imported_transformer.tap_changer.normal_position == 0
    assert np.isclose(imported_transformer.tap_changer.dV, 0.0)


def test_psse33_branch_writer_uses_rateabc_field_order() -> None:
    """PSSE 33 branches must expose RATEA/RATEB/RATEC."""

    branch = RawBranchV33()
    branch.I = 1
    branch.J = 2
    branch.CKT = "1"
    branch.R = 0.01
    branch.X = 0.10
    branch.B = 0.001
    branch.RATEA = 100.0
    branch.RATEB = 110.0
    branch.RATEC = 120.0
    branch.GI = 0.0
    branch.BI = 0.0
    branch.GJ = 0.0
    branch.BJ = 0.0
    branch.ST = 1
    branch.MET = 1
    branch.LEN = 10.0

    raw_values = interpret_line(branch.get_raw_line(33))

    assert raw_values[6:9] == [100.0, 110.0, 120.0]
    assert branch.RATE1 == 100.0
    assert branch.RATE2 == 110.0
    assert branch.RATE3 == 120.0


def test_psse35_branch_import_defaults_string_len_to_one(tmp_path: Path) -> None:
    """String PSSE branch LEN fields must import as one instead of crashing."""

    raw_text: str = "\n".join(
        [
            "0,100.0,35,0,0,60.0",
            "Branch length case",
            "Branch length case 2",
            "GENERAL, THRSHZ=0.0001",
            "0 / END OF SYSTEM-WIDE DATA, BEGIN BUS DATA",
            "101,'BUS101',230.0,3,1,1,1,1.0,0.0,1.1,0.9,1.1,0.9",
            "102,'BUS102',230.0,1,1,1,1,1.0,0.0,1.1,0.9,1.1,0.9",
            "0 / END OF BUS DATA, BEGIN BRANCH DATA",
            "101,102,'1',0.01,0.05,0.001,'',100.0,110.0,120.0,0.0,0.0,0.0,0.0,1,1,,1,1.0",
            "0 / END OF BRANCH DATA",
            "Q",
        ]
    )
    raw_path: Path = tmp_path / "psse35_blank_branch_len.raw"
    raw_path.write_text(raw_text, encoding="utf-8")

    psse_circuit = read_raw(str(raw_path), logger=Logger())
    circuit = psse_to_veragrid(psse_circuit, logger=Logger())

    assert len(psse_circuit.branches) == 1
    assert psse_circuit.branches[0].LEN == 1.0
    assert len(circuit.lines) == 1
    assert circuit.lines[0].length == 1.0


def test_branch_setters_coerce_declared_types() -> None:
    """Branch setters must coerce declared types and preserve defaults on blank values."""

    branch = RawBranchV33()
    branch.I = "7"
    branch.CKT = 9
    branch.R = 0.25
    branch.R = ""
    branch.ST = "0"
    branch.LEN = ""

    assert branch.I == 7
    assert branch.CKT == "9"
    assert branch.R == 0.25
    assert branch.ST == 0
    assert branch.LEN == 1.0


def test_other_base_alias_setters_coerce_declared_types() -> None:
    """Base alias setters must coerce through the shared PSSE helper functions."""

    transformer = RawTransformerV35()
    switch = RawSystemSwitchingDeviceV35()
    machine = RawInductionMachineV35()

    transformer.RATA1 = 12.5
    transformer.RATA1 = ""
    switch.CKTID = 7
    machine.STATUS = "0"

    assert transformer.RATA1 == 12.5
    assert transformer.RATE1_1 == 12.5
    assert switch.CKTID == "7"
    assert switch.CKT == "7"
    assert machine.STATUS == 0
    assert machine.STAT == 0


def test_small_base_object_setters_coerce_declared_types() -> None:
    """Small base RAW objects must keep typed defaults through explicit setters."""

    area = RawArea()
    bus = RawBus()
    load = RawLoadV36()
    terminal = RawEquipmentTerminalV35()
    station_switch = RawSubstationSwitchingDeviceV35()
    section = RawMultiLineSection()

    area.PDES = ""
    area.ARNAME = 9
    bus.I = "11"
    bus.VM = ""
    load.PL = ""
    load.LOADTYPE = 4
    terminal.TYPE = 3
    terminal.IBUS = "101"
    station_switch.X = ""
    station_switch.NAME = 12
    section.ID = ""
    section.DUM3 = "8"

    assert area.PDES == 0.0
    assert area.ARNAME == "9"
    assert bus.I == 11
    assert bus.VM == 1.0
    assert load.PL == 0.0
    assert load.LOADTYPE == "4"
    assert terminal.TYPE == "3"
    assert terminal.IBUS == 101
    assert station_switch.X == 0.0001
    assert station_switch.NAME == "12"
    assert section.ID == 0.0
    assert section.DUM3 == 8


def test_medium_base_object_setters_coerce_declared_types() -> None:
    """Medium base RAW objects must keep typed defaults through explicit setters."""

    facts = RawFACTS()
    generator = RawGenerator()

    facts.MODE = "2"
    facts.PDES = ""
    facts.MNAME = 5
    generator.ID = 7
    generator.PG = ""
    generator.O2 = "9"
    generator.WPF = ""

    assert facts.MODE == 2
    assert facts.PDES == 0.0
    assert facts.MNAME == "5"
    assert generator.ID == "7"
    assert generator.PG == 0.0
    assert generator.O2 == 9
    assert generator.WPF == 0.0


def test_large_base_object_setters_coerce_declared_types() -> None:
    """Large base RAW objects must keep typed defaults through explicit setters."""

    gne = RawGneDevice()
    shunt = RawSwitchedShunt()
    vsc = RawVscDCLine()
    dc_line = RawTwoTerminalDCLine()

    gne.NTERM = "3"
    gne.REAL4 = ""
    gne.CHAR2 = 8
    shunt.MODSW = "4"
    shunt.BINIT = ""
    shunt.S3 = "1"
    shunt.B6 = "2.5"
    vsc.NAME = 6
    vsc.RDC = ""
    vsc.TYPE2 = "2"
    vsc.RMPCT2 = ""
    dc_line.METER = 5
    dc_line.CCCITMX = ""
    dc_line.TRR = ""
    dc_line.IDR = 4

    assert gne.NTERM == 3
    assert gne.REAL4 == 0.0
    assert gne.CHAR2 == "8"
    assert shunt.MODSW == 4
    assert shunt.BINIT == 0.0
    assert shunt.S3 == 1
    assert shunt.B6 == 2.5
    assert vsc.NAME == "6"
    assert vsc.RDC == 0.0
    assert vsc.TYPE2 == 2
    assert vsc.RMPCT2 == 100.0
    assert dc_line.METER == "5"
    assert dc_line.CCCITMX == 20
    assert dc_line.TRR == 1.0
    assert dc_line.IDR == "4"


def test_psse35_node_writer_omits_isub_from_raw_record() -> None:
    """PSSE 35 node RAW records are NI, NAME, I, STATUS, VM, VA without ISUB in-line."""

    node = RawNodeV35()
    node.ISUB = 99
    node.NI = 4
    node.NAME = "NODE_4"
    node.I = 3009
    node.STATUS = 1
    node.VM = 1.02
    node.VA = 3.5

    raw_values = interpret_line(node.get_raw_line(35))

    assert raw_values == [4, "NODE_4", 3009, 1, 1.02, 3.5]


def test_psse35_induction_machine_uses_stat_field_name() -> None:
    """Induction machine classes should expose STAT per the manual while keeping compatibility aliasing."""

    machine = RawInductionMachineV35()
    machine.I = 3010
    machine.ID = "1"
    machine.STAT = 1
    machine.SCODE = 1
    machine.DCODE = 2
    machine.AREA = 5
    machine.ZONE = 4
    machine.OWNER = 5
    machine.TCODE = 1
    machine.BCODE = 1
    machine.MBASE = 1.0
    machine.RATEKV = 21.6
    machine.PCODE = 1
    machine.PSET = 1.0
    machine.H = 1.0
    machine.A = 1.0
    machine.B = 1.0
    machine.D = 1.0
    machine.E = 1.0
    machine.RA = 0.0
    machine.XA = 0.0
    machine.XM = 0.0
    machine.R1 = 0.0
    machine.X1 = 0.0
    machine.R2 = 0.0
    machine.X2 = 0.0
    machine.X3 = 0.0
    machine.E1 = 0.0
    machine.SE1 = 0.0
    machine.E2 = 0.0
    machine.SE2 = 0.0
    machine.IA1 = 0.0
    machine.IA2 = 0.0
    machine.XAMULT = 1.0

    raw_values = interpret_line(machine.get_raw_line(35).splitlines()[0])

    assert raw_values[2] == 1
    assert machine.STATUS == 1


def test_psse35_gne_writer_uses_nmet_field_name() -> None:
    """PSSE 35 GNE records should use NMET rather than older NMETR spelling."""

    gne = RawGneDeviceV35()
    gne.NAME = "GNE1"
    gne.MODEL = "MODEL1"
    gne.NTERM = 2
    gne.BUS1 = 101
    gne.BUS2 = 102
    gne.NREAL = 2
    gne.NINTG = 1
    gne.NCHAR = 1
    gne.STATUS = 1
    gne.OWNER = 5
    gne.NMET = 2
    gne.REAL1 = 1.5
    gne.REAL2 = 2.5
    gne.INTG1 = 7
    gne.CHAR1 = "A1"

    lines = gne.get_raw_line(35).splitlines()
    header_values = interpret_line(lines[0])
    status_values = interpret_line(lines[1])

    assert header_values == ["GNE1", "MODEL1", 2, 101, 102, 2, 1, 1]
    assert status_values == [1, 5, 2]


def test_veragrid_to_raw_exports_each_hvdc_line_once() -> None:
    """Generic VeraGrid HVDC lines must not be exported into both PSSE HVDC categories."""

    logger = Logger()
    grid = MultiCircuit()

    bus_from = dev.Bus(name="B1", code="1", Vnom=220.0)
    bus_to = dev.Bus(name="B2", code="2", Vnom=220.0)
    grid.add_bus(bus_from)
    grid.add_bus(bus_to)

    hvdc_line = dev.HvdcLine(
        bus_from=bus_from,
        bus_to=bus_to,
        name="HVDC1",
        code="1_2_1",
        Pset=50.0,
        r=5.0,
        Vset_f=1.0,
        Vset_t=1.0,
        rate=100.0,
    )
    grid.add_hvdc(hvdc_line)

    psse_circuit = veragrid_to_raw(grid=grid, version=35, logger=logger)

    assert len(psse_circuit.two_terminal_dc_lines) == 1
    assert len(psse_circuit.vsc_dc_lines) == 0


def test_veragrid_to_raw_preserves_vsc_hvdc_endpoint_data() -> None:
    """
    Ensure the VSC exporter writes the converter bus and control records needed for roundtrip parsing.
    """
    grid: MultiCircuit = MultiCircuit()
    bus_from: dev.Bus = dev.Bus(name="From", Vnom=220.0, code="101")
    bus_to: dev.Bus = dev.Bus(name="To", Vnom=220.0, code="102")

    grid.add_bus(bus_from)
    grid.add_bus(bus_to)

    hvdc_line: dev.HvdcLine = dev.HvdcLine(
        bus_from=bus_from,
        bus_to=bus_to,
        name="VSC link",
        Pset=75.0,
        Vset_f=0.97,
        Vset_t=1.01,
        rate=120.0,
    )
    grid.add_hvdc(hvdc_line)

    logger: Logger = Logger()
    psse_circuit = veragrid_to_raw(grid=grid, version=35, logger=logger)

    assert len(psse_circuit.two_terminal_dc_lines) == 0
    assert len(psse_circuit.vsc_dc_lines) == 1

    exported_vsc = psse_circuit.vsc_dc_lines[0]

    assert exported_vsc.IBUS1 == 101
    assert exported_vsc.IBUS2 == 102
    assert exported_vsc.TYPE1 == 1
    assert exported_vsc.TYPE2 == 2
    assert exported_vsc.MODE1 == 1
    assert exported_vsc.MODE2 == 1
    assert exported_vsc.DCSET1 == 75.0
    assert exported_vsc.DCSET2 == -75.0
    assert exported_vsc.ACSET1 == 0.97
    assert exported_vsc.ACSET2 == 1.01
    assert exported_vsc.SMAX1 == 120.0
    assert exported_vsc.SMAX2 == 120.0
    assert exported_vsc.VSREG1 == 101
    assert exported_vsc.VSREG2 == 102


def test_veragrid_to_raw_uses_requested_version_specific_classes() -> None:
    """Export must instantiate the target version object classes, not generic v29 shells."""

    grid = MultiCircuit()
    bus = dev.Bus(name="B1", code="1", Vnom=220.0)
    grid.add_bus(bus)
    grid.add_load(bus, dev.Load(name="LOAD_A"))
    grid.add_shunt(bus, dev.Shunt(name="FSH_A"))

    logger = Logger()
    psse_circuit = veragrid_to_raw(grid=grid, version=36, logger=logger)

    assert psse_circuit.REV == 36
    assert type(psse_circuit.loads[0]).__name__ == "RawLoadV36"
    assert type(psse_circuit.fixed_shunts[0]).__name__ == "RawFixedShuntV36"
    assert interpret_line(psse_circuit.loads[0].get_raw_line(36))[-1] == "LOAD_A"
    assert interpret_line(psse_circuit.fixed_shunts[0].get_raw_line(36))[-1] == "FSH_A"


def test_veragrid_to_raw_v34_vsc_export_uses_remot_fields() -> None:
    """PSSE 34 VSC export must populate REMOT instead of VSREG/NREG."""

    grid = MultiCircuit()
    bus_from = dev.Bus(name="From", Vnom=220.0, code="101")
    bus_to = dev.Bus(name="To", Vnom=220.0, code="102")
    grid.add_bus(bus_from)
    grid.add_bus(bus_to)
    grid.add_hvdc(dev.HvdcLine(
        bus_from=bus_from,
        bus_to=bus_to,
        name="VSC34",
        Pset=75.0,
        Vset_f=0.97,
        Vset_t=1.01,
        rate=120.0,
    ))

    exported_vsc = veragrid_to_raw(grid=grid, version=34, logger=Logger()).vsc_dc_lines[0]

    assert type(exported_vsc).__name__ == "RawVscDCLineV34"
    assert exported_vsc.REMOT1 == 101
    assert exported_vsc.REMOT2 == 102


def test_veragrid_to_raw_switch_normal_status_uses_psse_semantics() -> None:
    """Normal-open VeraGrid switches must export NSTATUS=0; normally closed must export NSTATUS=1."""

    grid = MultiCircuit()
    bus_from = dev.Bus(name="From", Vnom=220.0, code="1")
    bus_to = dev.Bus(name="To", Vnom=220.0, code="2")
    grid.add_bus(bus_from)
    grid.add_bus(bus_to)
    grid.add_branch(dev.Switch(bus_from=bus_from, bus_to=bus_to, name="SW_OPEN", normal_open=True))
    grid.add_branch(dev.Switch(bus_from=bus_from, bus_to=bus_to, name="SW_CLOSED", normal_open=False))

    exported_switches = veragrid_to_raw(grid=grid, version=35, logger=Logger()).switches

    assert exported_switches[0].NSTATUS == 0
    assert exported_switches[1].NSTATUS == 1


def test_veragrid_to_raw_preserves_three_winding_voltage_regulation_fields() -> None:
    """Three-winding tap regulation must export the RAW control fields explicitly."""

    grid = MultiCircuit()
    bus1 = dev.Bus(name="Bus1", Vnom=220.0, code="1")
    bus2 = dev.Bus(name="Bus2", Vnom=110.0, code="2")
    bus3 = dev.Bus(name="Bus3", Vnom=33.0, code="3")
    grid.add_bus(bus1)
    grid.add_bus(bus2)
    grid.add_bus(bus3)

    transformer = dev.Transformer3W(V1=220.0,
                                    V2=110.0,
                                    V3=33.0,
                                    bus1=bus1,
                                    bus2=bus2,
                                    bus3=bus3,
                                    x12=0.01,
                                    x23=0.01,
                                    x31=0.01,
                                    rate12=100.0,
                                    rate23=90.0,
                                    rate31=80.0)
    transformer.code = "1_2_3_1"
    grid.add_transformer3w(obj=transformer)

    transformer.winding1.tap_module_control_mode = TapModuleControl.Vm
    transformer.winding1.regulation_bus = bus2
    transformer.winding1.tap_module_max = 1.10
    transformer.winding1.tap_module_min = 0.90
    transformer.winding1.vset = 1.03
    transformer.winding1.tap_changer.total_positions = 17

    transformer.winding2.tap_module_control_mode = TapModuleControl.Vm
    transformer.winding2.regulation_bus = bus3
    transformer.winding2.tap_module_max = 1.08
    transformer.winding2.tap_module_min = 0.92
    transformer.winding2.vset = 0.99
    transformer.winding2.tap_changer.total_positions = 9

    exported_transformer = veragrid_to_raw(grid=grid, version=35, logger=Logger()).transformers[0]

    assert exported_transformer.COD1 == 1
    assert exported_transformer.CONT1 == exported_transformer.J
    assert exported_transformer.RMA1 == 1.10
    assert exported_transformer.RMI1 == 0.90
    assert exported_transformer.VMA1 == 1.03
    assert exported_transformer.VMI1 == 1.03
    assert exported_transformer.NTP1 == 17

    assert exported_transformer.COD2 == 1
    assert exported_transformer.CONT2 == exported_transformer.K
    assert exported_transformer.RMA2 == 1.08
    assert exported_transformer.RMI2 == 0.92
    assert exported_transformer.VMA2 == 0.99
    assert exported_transformer.VMI2 == 0.99
    assert exported_transformer.NTP2 == 9

    assert exported_transformer.COD3 == 0


def test_psse33_transformer_preserves_second_winding_rate_b_value() -> None:
    """PSSE 33 three-winding transformer parsing and writing must preserve RATE2-2."""

    transformer = RawTransformer()
    transformer.parse(
        data=[
            [1, 2, 3, "1", 1, 1, 1, 0.0, 0.0, 2, "TR3", 1, 1, 1.0, 0, 0.0, 0, 0.0, 0, 0.0, "VG"],
            [0.01, 0.10, 100.0, 0.02, 0.20, 100.0, 0.03, 0.30, 100.0, 1.0, 0.0],
            [1.0, 220.0, 0.0, 100.0, 101.0, 102.0, 1, 0, 1.1, 0.9, 1.1, 0.9, 33, 0, 0.0, 0.0, 0.0],
            [1.0, 110.0, 0.0, 200.0, 201.0, 202.0, 1, 0, 1.1, 0.9, 1.1, 0.9, 33, 0, 0.0, 0.0, 0.0],
            [1.0, 33.0, 0.0, 300.0, 301.0, 302.0, 1, 0, 1.1, 0.9, 1.1, 0.9, 33, 0, 0.0, 0.0, 0.0],
        ],
        version=33,
        logger=Logger(),
    )

    raw_lines = transformer.get_raw_line(33).splitlines()
    second_winding_values = interpret_line(raw_lines[3])

    assert transformer.RATB2 == 201.0
    assert transformer.RATE2_2 == 201.0
    assert second_winding_values[4] == 201.0
