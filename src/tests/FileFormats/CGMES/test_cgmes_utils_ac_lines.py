# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Tests for AC-line-specific CGMES utility helpers."""

from VeraGridEngine.IO.cim.cgmes.cgmes_utils import (
    get_pu_values_ac_line_segment,
    get_rate_ac_line_segment,
    get_voltage_ac_line_segment,
)
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.ac_line_segment import ACLineSegment
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.base_voltage import BaseVoltage
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.terminal import Terminal
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.topological_node import TopologicalNode


def test_get_voltage_ac_line_segment_base_voltage_exists_returns_nominal_voltage():
    """Read the AC line nominal voltage directly from the attached base-voltage object."""
    ac_line_segment = ACLineSegment()
    ac_line_segment.BaseVoltage = BaseVoltage()
    ac_line_segment.BaseVoltage.nominalVoltage = 220

    assert get_voltage_ac_line_segment(ac_line_segment, None) == 220


def test_get_voltage_ac_line_segment_base_voltage_none_terminal_none_returns_none():
    """Return ``None`` when an AC line has neither a base voltage nor connected terminals."""
    ac_line_segment = ACLineSegment()
    assert get_voltage_ac_line_segment(ac_line_segment, None) is None


def test_get_voltage_ac_line_segment_base_voltage_none_terminal_not_none_returns_first_elements_voltage():
    """Use the first connected terminal's topological node voltage when the line has no base voltage."""
    ac_line_segment = ACLineSegment()
    terminal = Terminal()
    terminal.TopologicalNode = TopologicalNode()
    terminal.TopologicalNode.BaseVoltage = BaseVoltage()
    terminal.TopologicalNode.BaseVoltage.nominalVoltage = 220
    ac_line_segment.references_to_me["Terminal"] = [terminal]

    assert get_voltage_ac_line_segment(ac_line_segment, None) == 220


def test_get_voltage_ac_line_segment_base_voltage_none_terminal_length_zero_returns_none():
    """Return ``None`` when the AC line terminal back-reference exists but is empty."""
    ac_line_segment = ACLineSegment()
    terminal = Terminal()
    terminal.TopologicalNode = TopologicalNode()
    terminal.TopologicalNode.BaseVoltage = BaseVoltage()
    terminal.TopologicalNode.BaseVoltage.nominalVoltage = 220
    ac_line_segment.references_to_me["Terminal"] = []

    assert get_voltage_ac_line_segment(ac_line_segment, None) is None


def test_get_pu_values_ac_line_segment_base_voltage_is_none_returns_zero():
    """Return fallback per-unit values when an AC line has no voltage base for conversion."""
    ac_line_segment = ACLineSegment()

    resistance, reactance, conductance, susceptance, resistance_zero, reactance_zero, conductance_zero, \
        susceptance_zero = get_pu_values_ac_line_segment(ac_line_segment, None)

    assert resistance == 1e-20
    assert reactance == 0.00001
    assert conductance == 1e-20
    assert susceptance == 1e-20
    assert resistance_zero == 1e-20
    assert reactance_zero == 1e-20
    assert conductance_zero == 1e-20
    assert susceptance_zero == 1e-20


def test_get_pu_values_ac_line_segment_base_voltage_is_filled_returns_correct_values():
    """Convert a fully populated AC line segment into the expected per-unit values."""
    ac_line_segment = ACLineSegment()
    ac_line_segment.BaseVoltage = BaseVoltage()
    ac_line_segment.BaseVoltage.nominalVoltage = 10
    ac_line_segment.r = 100
    ac_line_segment.x = 100
    ac_line_segment.gch = 100
    ac_line_segment.bch = 100
    ac_line_segment.r0 = 100
    ac_line_segment.x0 = 100
    ac_line_segment.g0ch = 100
    ac_line_segment.b0ch = 100

    resistance, reactance, conductance, susceptance, resistance_zero, reactance_zero, conductance_zero, \
        susceptance_zero = get_pu_values_ac_line_segment(ac_line_segment, None)

    assert resistance == 100
    assert reactance == 100
    assert conductance == 100
    assert susceptance == 100
    assert resistance_zero == 100
    assert reactance_zero == 100
    assert conductance_zero == 100
    assert susceptance_zero == 100


def test_get_rate_ac_line_segment_returns_constant():
    """Expose the current placeholder thermal rating used for AC line conversion."""
    assert get_rate_ac_line_segment() == 1e-20
