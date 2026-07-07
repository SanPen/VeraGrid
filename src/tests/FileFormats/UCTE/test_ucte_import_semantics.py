# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from pathlib import Path

import pytest

from VeraGridEngine.IO.file_open import open_ucte
from VeraGridEngine.IO.ucte.devices.ucte_node import UcteNode
from VeraGridEngine.IO.ucte.devices.ucte_transformer_regulation import UcteTransformerRegulation
from VeraGridEngine.basic_structures import Logger, LogSeverity


UCTE_FIXTURES = Path(__file__).resolve().parents[2] / "data" / "grids" / "ucte"


def get_errors(logger: Logger) -> list[str]:
    return [entry.msg for entry in logger.entries if entry.severity == LogSeverity.Error]


def get_warnings(logger: Logger) -> list[str]:
    return [entry.msg for entry in logger.entries if entry.severity == LogSeverity.Warning]


def test_node_nominal_voltage_comes_from_node_code():
    logger = Logger()
    node = UcteNode()

    node.parse(
        "XXXXXX14              0 2 409.07 0.00000 0.00000 -1.0000 0.00000 2.00000 -2.0000 1.00000 -1.0000",
        logger,
    )

    assert node.voltage == pytest.approx(380.0)
    assert node.voltage_reference == pytest.approx(409.07)


def test_same_id_import_creates_transformer_and_switch():
    logger = Logger()
    grid = open_ucte(str(UCTE_FIXTURES / "sameId.uct"), logger=logger)

    assert grid.get_lines_number() == 0
    assert grid.get_transformers2w_number() == 1
    assert grid.get_switches_number() == 1
    assert get_errors(logger) == []


def test_voltage_regulating_xnode_uses_voltage_reference_for_generator_setpoint():
    logger = Logger()
    grid = open_ucte(str(UCTE_FIXTURES / "frVoltageRegulatingXnode.uct"), logger=logger)

    bus = next(bus for bus in grid.get_buses() if bus.code == "XXXXXX14")
    gen = next(gen for gen in grid.get_generators() if gen.code == "XXXXXX14")

    assert bus.Vnom == pytest.approx(380.0)
    assert bus.Vm0 == pytest.approx(409.07 / 380.0, rel=1e-4)
    assert bus.internal is True

    assert gen.P == pytest.approx(1.0)
    assert gen.Vset == pytest.approx(409.07 / 380.0, rel=1e-4)
    assert gen.is_controlled is True
    assert gen.Qmin == pytest.approx(-1.0)
    assert gen.Qmax == pytest.approx(1.0)


def test_different_nominal_voltage_line_is_rejected():
    logger = Logger()
    grid = open_ucte(str(UCTE_FIXTURES / "differentLinesVoltage.uct"), logger=logger)

    assert grid.get_lines_number() == 0
    assert "UCTE line/coupler endpoints have different nominal voltages" in get_errors(logger)


def test_line_between_two_xnodes_is_rejected():
    logger = Logger()
    grid = open_ucte(str(UCTE_FIXTURES / "lineBetweenTwoXnodes.uct"), logger=logger)

    assert grid.get_lines_number() == 0
    assert grid.get_switches_number() == 0
    assert "Line between 2 X-nodes is not supported" in get_errors(logger)


def test_tap_positions_range_is_extended():
    logger = Logger()
    grid = open_ucte(str(UCTE_FIXTURES / "tapPositionsRange.uct"), logger=logger)

    trafos = {(tr.bus_from.code, tr.bus_to.code): tr for tr in grid.get_transformers2w()}

    ratio_trafo = trafos[("0AAAAA2", "0BBBBB5")]
    assert ratio_trafo.tap_changer.total_positions == 15
    assert ratio_trafo.tap_changer.neutral_position == 7
    assert ratio_trafo.tap_changer.tap_position == 0

    phase_trafo = trafos[("HCCCCC1", "HDDDDD2")]
    assert phase_trafo.tap_changer.total_positions == 19
    assert phase_trafo.tap_changer.neutral_position == 9
    assert phase_trafo.tap_changer.tap_position == 18

    symm_trafo = trafos[("ZEFGH221", "ZABCD221")]
    assert symm_trafo.tap_changer.total_positions == 17
    assert symm_trafo.tap_changer.neutral_position == 8
    assert symm_trafo.tap_changer.tap_position == 0


def test_invalid_regulation_network_is_normalized_without_errors():
    logger = Logger()
    grid = open_ucte(str(UCTE_FIXTURES / "invalidRegulationNetwork.uct"), logger=logger)

    assert grid.get_transformers2w_number() == 6
    assert grid.get_switches_number() == 1
    assert get_errors(logger) == []


def test_transformer_coupler_is_imported_as_switch(tmp_path):
    logger = Logger()
    path = tmp_path / "transformer-coupler.uct"
    path.write_text(
        "##C 2007.05.01\n"
        "##N\n"
        "AAAAAA10 BUS_A        0 0\n"
        "BBBBBB10 BUS_B        0 0\n"
        "##T\n"
        "AAAAAA10 BBBBBB10 1 2 380.0 380.0 1000. 0.0000 0.0000 0.00000 0.0000 2500 Coupler T1\n",
        encoding="utf-8",
    )

    grid = open_ucte(str(path), logger=logger)

    assert grid.get_transformers2w_number() == 0
    assert grid.get_switches_number() == 1
    switch = grid.get_switches()[0]
    assert switch.active is True
    assert switch.code == "1"
    assert get_errors(logger) == []


def test_invalid_angle_regulation_type_defaults_to_asym():
    logger = Logger()
    regulation = UcteTransformerRegulation()
    regulation.node1 = "AAAAAA10"
    regulation.node2 = "BBBBBB10"
    regulation.order_code = "1"
    regulation.delta_u2 = 1.5
    regulation.theta = 90.0
    regulation.n2 = 4
    regulation.n2_prime = 0
    regulation.regulation_type = "BAD"

    regulation.normalize(nominal_voltage=380.0, logger=logger)

    assert regulation.regulation_type == "ASYM"
    assert "Invalid angle regulation type, defaulting to ASYM" in get_warnings(logger)
