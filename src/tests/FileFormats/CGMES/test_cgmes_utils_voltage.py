# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Tests for CGMES voltage lookup helpers shared across devices."""

from VeraGridEngine.IO.cim.cgmes.cgmes_utils import get_nominal_voltage, get_voltage_terminal
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.base_voltage import BaseVoltage
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.terminal import Terminal
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.topological_node import TopologicalNode
from VeraGridEngine.data_logger import DataLogger


def test_get_voltage_terminal_topological_node_nominal_voltage_set_returns_value() -> float | None:
    """Resolve a terminal voltage from its connected topological node nominal voltage."""
    terminal = Terminal()
    terminal.TopologicalNode = TopologicalNode()
    terminal.TopologicalNode.BaseVoltage = BaseVoltage()
    terminal.TopologicalNode.BaseVoltage.nominalVoltage = 10

    assert get_voltage_terminal(terminal, None) == 10


def test_get_voltage_terminal_no_topological_node_returns_none() -> float | None:
    """Return ``None`` when a terminal is not linked to any topological node."""
    terminal = Terminal()
    terminal.TopologicalNode = None

    assert get_voltage_terminal(terminal, None) is None


def test_get_nominal_voltage_correct_nominal_voltage_returns_value():
    """Read the nominal voltage from a topological node that has a valid base voltage."""
    topological_node = TopologicalNode()
    topological_node.BaseVoltage = BaseVoltage()
    topological_node.BaseVoltage.nominalVoltage = 220

    voltage = get_nominal_voltage(topological_node, None)

    assert voltage == 220
    assert isinstance(voltage, float)


def test_get_nominal_voltage_no_base_voltage_returns_0():
    """Return zero and avoid crashing when a topological node has no base voltage assigned."""
    topological_node = TopologicalNode()
    logger = DataLogger()

    voltage = get_nominal_voltage(topological_node, logger)

    assert voltage == 0
    assert isinstance(voltage, float)


def test_get_nominal_voltage_base_voltage_is_string_log_error():
    """Log a missing-reference error when the base-voltage link is still a raw string token."""
    topological_node = TopologicalNode()
    topological_node.BaseVoltage = "str"
    logger = DataLogger()

    get_nominal_voltage(topological_node, logger)

    assert len(logger.entries) == 1
    assert logger.entries[0].msg == "Missing reference"
