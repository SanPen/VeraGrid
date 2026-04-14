# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from pathlib import Path

from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.ucte.devices.ucte_base import ucte_split
from VeraGridEngine.IO.ucte.devices.ucte_circuit import UcteCircuit
from VeraGridEngine.IO.ucte.devices.ucte_line import UcteLine
from VeraGridEngine.IO.ucte.devices.ucte_node import UcteNode
from VeraGridEngine.IO.ucte.devices.ucte_transformer import UcteTransformer


UCTE_FIXTURES = Path(__file__).resolve().parents[2] / "data" / "grids" / "ucte"


def test_ucte_split_preserves_fixed_width_prefix_and_tail_text():
    line = "ISSUE 21 ISSUE 22 1 7      0 0.0000        0   5051 Test Name"

    chunks = ucte_split(line, prefix_lengths=(8, 8, 1), total_fields=9, greedy_tail=True)

    assert chunks == [
        "ISSUE 21",
        "ISSUE 22",
        "1",
        "7",
        "0",
        "0.0000",
        "0",
        "5051",
        "Test Name",
    ]


def test_ucte_node_fallback_preserves_embedded_space_identifier():
    logger = Logger()
    node = UcteNode()

    node.parse("ISSUE 21              0 0 217.41       0       0       0       0       0       0       0       0", logger)

    assert node.node_code == "ISSUE 21"
    assert node.geo_name == ""
    assert node.status == 0
    assert node.node_type == 0


def test_ucte_line_fallback_preserves_embedded_space_identifiers():
    logger = Logger()
    line = UcteLine()

    line.parse("ISSUE 21 ISSUE 22 1 7      0 0.0000        0   5051", logger)

    assert line.node1 == "ISSUE 21"
    assert line.node2 == "ISSUE 22"
    assert line.order_code == "1"
    assert line.status == 7
    assert line.current_limit == 5051


def test_ucte_transformer_fallback_preserves_multi_word_name():
    logger = Logger()
    transformer = UcteTransformer()

    transformer.parse(
        "F_SU1_11 F_SU1_21 1 0 400.0 225.0 5000. 0.5500 1.6800 13.25000 0.0000   5000 Test 2WT 1",
        logger,
    )

    assert transformer.node1 == "F_SU1_11"
    assert transformer.node2 == "F_SU1_21"
    assert transformer.order_code == "1"
    assert transformer.name == "Test 2WT 1"


def test_country_block_strips_newline_from_country_code():
    logger = Logger()
    circuit = UcteCircuit()

    circuit.parse_file([str(UCTE_FIXTURES / "countryIssue.uct")], logger)

    assert circuit.nodes[0].current_country == "ES"
    assert circuit.nodes[1].current_country == "BE"


def test_tt_block_is_routed_to_tap_tables(tmp_path):
    logger = Logger()
    circuit = UcteCircuit()
    path = tmp_path / "tap-table-only.uct"
    path.write_text(
        "##C 2007.05.01\n"
        "##TT\n"
        "NODE0001 NODE0002 1 0 0.2500 10.686 0.000000 0.0000\n",
        encoding="utf-8",
    )

    circuit.parse_file([str(path)], logger)

    assert len(circuit.transformers) == 0
    assert len(circuit.transformer_tap_tables) == 1
    assert len(circuit.transformer_tap_tables_dict["NODE0001_NODE0002_1"]) == 1


def test_tt_rows_with_same_key_are_grouped(tmp_path):
    logger = Logger()
    circuit = UcteCircuit()
    path = tmp_path / "tap-table-grouped.uct"
    path.write_text(
        "##C 2007.05.01\n"
        "##TT\n"
        "NODE0001 NODE0002 1  0 0.2500 10.686 0.000000 0.0000\n"
        "NODE0001 NODE0002 1  1 0.2600 10.900 0.100000 1.5000\n",
        encoding="utf-8",
    )

    circuit.parse_file([str(path)], logger)

    assert len(circuit.transformer_tap_tables) == 2
    assert len(circuit.transformer_tap_tables_dict["NODE0001_NODE0002_1"]) == 2
