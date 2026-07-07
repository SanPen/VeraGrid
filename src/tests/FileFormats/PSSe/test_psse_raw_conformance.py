# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Regression tests for PSSE RAW parser and writer conformance."""

from pathlib import Path

import VeraGridEngine.Devices as dev
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.IO.raw.devices.switched_shunt import RawSwitchedShunt
from VeraGridEngine.IO.raw.devices.system_switching_device import RawSystemSwitchingDevice
from VeraGridEngine.IO.raw.devices.transformer import RawTransformer
from VeraGridEngine.IO.raw.raw_parser_writer import interpret_line, read_and_split, read_raw
from VeraGridEngine.IO.raw.veragrid_to_raw import veragrid_to_raw
from VeraGridEngine.basic_structures import Logger


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

    switched_shunt = RawSwitchedShunt()
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


def test_switched_shunt_writer_uses_swrem_before_psse35() -> None:
    """PSSE 34 switched shunts must write SWREM instead of the PSSE 35 SWREG field."""

    switched_shunt = RawSwitchedShunt()
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


def test_system_switching_device_writer_supports_psse34_and_psse35() -> None:
    """System switching device export must use the actual property names for both supported revisions."""

    switching_device = RawSystemSwitchingDevice()
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

    raw_values_34 = interpret_line(switching_device.get_raw_line(34))
    raw_values_35 = interpret_line(switching_device.get_raw_line(35))

    assert raw_values_34[16:21] == [1, 0, 2, 3, "SW1"]
    assert raw_values_35[16:21] == [1, 0, 2, 3, "SW1"]


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

    psse_circuit = veragrid_to_raw(grid=grid, logger=logger)

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
    psse_circuit = veragrid_to_raw(grid=grid, logger=logger)

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

    assert transformer.RATE2_2 == 201.0
    assert second_winding_values[4] == 201.0
