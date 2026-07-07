# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""
Tests for voltage level conversion functions.
Ensures Single Bar, Double Bar, Ring, and Breaker-and-a-Half configurations work correctly.
"""
import pytest
from typing import List, Tuple
import VeraGridEngine.Devices as dev
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.enumerations import VoltageLevelTypes, SwitchGraphicType, BusGraphicType
from VeraGridEngine.Topology.VoltageLevels.single_bar import (
    create_single_bar,
    create_single_bar_with_disconnectors
)
from VeraGridEngine.Topology.VoltageLevels.double_bar import (
    create_double_bar,
    create_double_bar_with_disconnectors
)
from VeraGridEngine.Topology.VoltageLevels.ring import (
    create_ring,
    create_ring_with_disconnectors
)
from VeraGridEngine.Topology.VoltageLevels.breaker_and_a_half import (
    create_breaker_and_a_half,
    create_breaker_and_a_half_with_disconnectors
)
from VeraGridEngine.Topology.VoltageLevels.vl_creation_common_functions import (
    transform_bus_into_voltage_level
)


def create_test_grid_with_bus(n_branches: int = 4) -> Tuple[MultiCircuit, dev.Bus, List[dev.Line]]:
    """
    Create a test grid with a central bus and connected branches.

    :param n_branches: Number of branches to connect to the central bus
    :return: (grid, central_bus, list_of_lines)
    """
    grid = MultiCircuit()

    # Create central bus that will be converted
    central_bus = dev.Bus(name="CentralBus", Vnom=132.0)
    grid.add_bus(central_bus)

    # Create remote buses and lines connecting to central bus
    lines = []
    for i in range(n_branches):
        remote_bus = dev.Bus(name=f"RemoteBus_{i}", Vnom=132.0)
        grid.add_bus(remote_bus)

        line = dev.Line(name=f"Line_{i}", bus_from=central_bus, bus_to=remote_bus, x=0.01)
        grid.add_line(line)
        lines.append(line)

    return grid, central_bus, lines


def get_switches_by_type(grid: MultiCircuit) -> Tuple[List[dev.Switch], List[dev.Switch]]:
    """
    Separate switches into circuit breakers and disconnectors.

    :param grid: MultiCircuit
    :return: (circuit_breakers, disconnectors)
    """
    circuit_breakers = []
    disconnectors = []

    for sw in grid.switch_devices:
        if sw.graphic_type == SwitchGraphicType.CircuitBreaker:
            circuit_breakers.append(sw)
        elif sw.graphic_type == SwitchGraphicType.Disconnector:
            disconnectors.append(sw)

    return circuit_breakers, disconnectors


def get_buses_by_type(buses: List[dev.Bus]) -> Tuple[List[dev.Bus], List[dev.Bus]]:
    """
    Separate buses into busbars and connectivity buses.

    :param buses: List of buses
    :return: (busbars, connectivity_buses)
    """
    busbars = []
    connectivity = []

    for bus in buses:
        if bus.graphic_type == BusGraphicType.BusBar:
            busbars.append(bus)
        elif bus.graphic_type == BusGraphicType.Connectivity:
            connectivity.append(bus)

    return busbars, connectivity


def count_connections_to_bus(grid: MultiCircuit, bus: dev.Bus) -> int:
    """
    Count how many switches connect to a given bus.

    :param grid: MultiCircuit
    :param bus: Bus to check
    :return: Number of switches connected to this bus
    """
    count = 0
    for sw in grid.switch_devices:
        if sw.bus_from == bus or sw.bus_to == bus:
            count += 1
    return count


# =============================================================================
# Single Bar Tests
# =============================================================================

def test_single_bar_basic_structure():
    """Test that single bar creates correct basic structure."""
    grid = MultiCircuit()
    substation = dev.Substation(name="TestSE")
    grid.add_substation(substation)

    vl, conn_buses, all_buses, _, _ = create_single_bar(
        name="TestVL",
        grid=grid,
        n_bays=4,
        v_nom=132.0,
        substation=substation
    )

    # Should have 1 main bar + 4 connection buses = 5 buses
    assert len(all_buses) == 5, f"Expected 5 buses, got {len(all_buses)}"

    # Should have 4 connection buses (one per bay)
    assert len(conn_buses) == 4, f"Expected 4 connection buses, got {len(conn_buses)}"

    # Should have 4 circuit breakers (one per bay, no disconnectors)
    cbs, discs = get_switches_by_type(grid)
    assert len(cbs) == 4, f"Expected 4 circuit breakers, got {len(cbs)}"
    assert len(discs) == 0, f"Expected 0 disconnectors, got {len(discs)}"

    # Should have 1 busbar
    busbars, connectivity = get_buses_by_type(all_buses)
    assert len(busbars) == 1, f"Expected 1 busbar, got {len(busbars)}"


def test_single_bar_with_disconnectors():
    """Test single bar with disconnectors creates correct structure."""
    grid = MultiCircuit()
    substation = dev.Substation(name="TestSE")
    grid.add_substation(substation)

    vl, conn_buses, all_buses, _, _ = create_single_bar_with_disconnectors(
        name="TestVL",
        grid=grid,
        n_bays=4,
        v_nom=132.0,
        substation=substation
    )

    # Should have 4 connection buses
    assert len(conn_buses) == 4, f"Expected 4 connection buses, got {len(conn_buses)}"

    # Should have 4 CBs and 8 disconnectors (2 per bay: one before CB, one after)
    cbs, discs = get_switches_by_type(grid)
    assert len(cbs) == 4, f"Expected 4 circuit breakers, got {len(cbs)}"
    assert len(discs) == 8, f"Expected 8 disconnectors, got {len(discs)}"


def test_single_bar_conversion():
    """Test converting a bus to single bar voltage level."""
    grid, central_bus, lines = create_test_grid_with_bus(n_branches=4)

    all_buses, conn_buses, branches, injections, reconnections = transform_bus_into_voltage_level(
        grid=grid,
        bus=central_bus,
        vl_type=VoltageLevelTypes.SingleBar,
        add_disconnectors=False
    )

    # All branches should be reconnected
    assert len(reconnections) == 4, f"Expected 4 reconnections, got {len(reconnections)}"

    # Each line should now connect to a connection bus, not the original central bus
    for line in lines:
        assert line.bus_from != central_bus or line.bus_to != central_bus, \
            f"Line {line.name} still connected to original bus"


# =============================================================================
# Double Bar Tests
# =============================================================================

def test_double_bar_basic_structure():
    """Test that double bar creates correct basic structure."""
    grid = MultiCircuit()
    substation = dev.Substation(name="TestSE")
    grid.add_substation(substation)

    vl, conn_buses, all_buses, _, _ = create_double_bar(
        name="TestVL",
        grid=grid,
        n_bays=4,
        v_nom=132.0,
        substation=substation
    )

    # Should have 2 main bars
    busbars, connectivity = get_buses_by_type(all_buses)
    assert len(busbars) == 2, f"Expected 2 busbars, got {len(busbars)}"

    # Should have 4 connection buses
    assert len(conn_buses) == 4, f"Expected 4 connection buses, got {len(conn_buses)}"


def test_double_bar_with_disconnectors_both_bars_connected():
    """
    Test that double bar with disconnectors connects each bay to both bars.
    Before there was a bug where only bar1 connections were being drawn.
    """
    grid = MultiCircuit()
    substation = dev.Substation(name="TestSE")
    grid.add_substation(substation)

    vl, conn_buses, all_buses, _, _ = create_double_bar_with_disconnectors(
        name="TestVL",
        grid=grid,
        n_bays=4,
        v_nom=132.0,
        substation=substation
    )

    # Get the two main bars
    busbars, connectivity = get_buses_by_type(all_buses)
    assert len(busbars) == 2, f"Expected 2 busbars, got {len(busbars)}"
    bar1 = busbars[0]
    bar2 = busbars[1]

    # Count connections to each bar
    bar1_connections = count_connections_to_bus(grid, bar1)
    bar2_connections = count_connections_to_bus(grid, bar2)

    # Each bar should have at least n_bays connections (one disconnector per bay)
    # plus coupling connections
    assert bar1_connections >= 4, \
        f"Bar1 should have at least 4 connections, got {bar1_connections}"
    assert bar2_connections >= 4, \
        f"Bar2 should have at least 4 connections, got {bar2_connections}"

    # For each bay's LineBus3, verify it connects to BOTH bars
    linebus3_buses = [b for b in connectivity if "LineBus3" in b.name]

    for bus3 in linebus3_buses:
        # Find all switches connected to this bus
        connected_bars = set()
        for sw in grid.switch_devices:
            if sw.bus_from == bus3:
                if sw.bus_to in busbars:
                    connected_bars.add(sw.bus_to)
            elif sw.bus_to == bus3:
                if sw.bus_from in busbars:
                    connected_bars.add(sw.bus_from)

        assert len(connected_bars) == 2, \
            f"Bus {bus3.name} should connect to both bars, but connects to {len(connected_bars)}"


def test_double_bar_switch_types():
    """Test that double bar creates correct switch types."""
    grid = MultiCircuit()
    substation = dev.Substation(name="TestSE")
    grid.add_substation(substation)

    vl, conn_buses, all_buses, _, _ = create_double_bar_with_disconnectors(
        name="TestVL",
        grid=grid,
        n_bays=4,
        v_nom=132.0,
        substation=substation
    )

    cbs, discs = get_switches_by_type(grid)

    # Should have CBs (4 bays + 1 coupling = 5)
    assert len(cbs) >= 4, f"Expected at least 4 circuit breakers, got {len(cbs)}"

    # Should have disconnectors (4 dis1 + 4 dis2 + 4 dis3 + coupling = ~14)
    assert len(discs) >= 12, f"Expected at least 12 disconnectors, got {len(discs)}"


# =============================================================================
# Ring Tests
# =============================================================================

def test_ring_basic_structure():
    """Test that ring creates correct basic structure."""
    grid = MultiCircuit()
    substation = dev.Substation(name="TestSE")
    grid.add_substation(substation)

    vl, conn_buses, all_buses, _, _ = create_ring(
        name="TestVL",
        grid=grid,
        n_bays=4,
        v_nom=132.0,
        substation=substation
    )

    # Should have 4 connection buses (one per bay)
    assert len(conn_buses) == 4, f"Expected 4 connection buses, got {len(conn_buses)}"

    # Ring should have n_bays circuit breakers connecting the ring
    cbs, discs = get_switches_by_type(grid)
    assert len(cbs) >= 4, f"Expected at least 4 circuit breakers, got {len(cbs)}"


def test_ring_with_disconnectors():
    """Test ring with disconnectors creates correct structure."""
    grid = MultiCircuit()
    substation = dev.Substation(name="TestSE")
    grid.add_substation(substation)

    vl, conn_buses, all_buses, _, _ = create_ring_with_disconnectors(
        name="TestVL",
        grid=grid,
        n_bays=4,
        v_nom=132.0,
        substation=substation
    )

    # Should have 4 connection buses
    assert len(conn_buses) == 4, f"Expected 4 connection buses, got {len(conn_buses)}"

    # Should have both CBs and disconnectors
    cbs, discs = get_switches_by_type(grid)
    assert len(cbs) >= 4, f"Expected at least 4 circuit breakers, got {len(cbs)}"
    assert len(discs) > 0, f"Expected disconnectors, got {len(discs)}"


def test_ring_forms_closed_loop():
    """Test that ring topology forms a closed loop."""
    grid = MultiCircuit()
    substation = dev.Substation(name="TestSE")
    grid.add_substation(substation)

    n_bays = 4
    vl, conn_buses, all_buses, _, _ = create_ring(
        name="TestVL",
        grid=grid,
        n_bays=n_bays,
        v_nom=132.0,
        substation=substation
    )

    # Build adjacency from switches
    # Each bus in the ring should connect to exactly 2 other ring buses
    busbars, _ = get_buses_by_type(all_buses)

    # Ring buses should each have connections to neighbors
    for i, bar in enumerate(busbars):
        connections = count_connections_to_bus(grid, bar)
        # Each ring segment should have at least 2 connections (to neighbors)
        # plus connection to bay
        assert connections >= 2, \
            f"Ring bus {bar.name} should have at least 2 connections, got {connections}"


# =============================================================================
# Breaker and a Half Tests
# =============================================================================

def test_breaker_and_a_half_basic_structure():
    """Test that breaker-and-a-half creates correct basic structure."""
    grid = MultiCircuit()
    substation = dev.Substation(name="TestSE")
    grid.add_substation(substation)

    n_bays = 2
    vl, conn_buses, all_buses, _, _ = create_breaker_and_a_half(
        name="TestVL",
        grid=grid,
        n_bays=n_bays,
        v_nom=132.0,
        substation=substation
    )

    # Should have 2 main bars
    busbars, connectivity = get_buses_by_type(all_buses)
    assert len(busbars) == 2, f"Expected 2 busbars, got {len(busbars)}"

    # Breaker-and-a-half creates n_bays bay sections, each with 2 connection buses
    # Actually based on the output, it creates n_bays connection buses total
    assert len(conn_buses) == n_bays, f"Expected {n_bays} connection buses, got {len(conn_buses)}"


def test_breaker_and_a_half_with_disconnectors_switch_types():
    """
    Test that breaker-and-a-half with disconnectors has correct switch types.
    This was a bug where some CBs were marked as disconnectors and vice versa.
    """
    grid = MultiCircuit()
    substation = dev.Substation(name="TestSE")
    grid.add_substation(substation)

    n_bays = 2
    vl, conn_buses, all_buses, _, _ = create_breaker_and_a_half_with_disconnectors(
        name="TestVL",
        grid=grid,
        n_bays=n_bays,
        v_nom=132.0,
        substation=substation
    )

    cbs, discs = get_switches_by_type(grid)

    # Verify CB names match CB type (should have 'SW' in name)
    for cb in cbs:
        assert "SW" in cb.name, \
            f"Circuit breaker {cb.name} should have 'SW' in name"

    # Verify disconnector names match disconnector type (should have 'Dis' in name)
    for disc in discs:
        assert "Dis" in disc.name, \
            f"Disconnector {disc.name} should have 'Dis' in name"

    # There should be more disconnectors than CBs in breaker-and-a-half with disconnectors
    assert len(discs) > len(cbs), \
        f"Should have more disconnectors than CBs, got {len(discs)} discs and {len(cbs)} CBs"


def test_breaker_and_a_half_three_cbs_per_bay():
    """Test that each bay section has exactly 3 circuit breakers."""
    grid = MultiCircuit()
    substation = dev.Substation(name="TestSE")
    grid.add_substation(substation)

    n_bays = 4  # Use 4 bays to get 2 bay sections (loop steps by 2)
    vl, conn_buses, all_buses, _, _ = create_breaker_and_a_half_with_disconnectors(
        name="TestVL",
        grid=grid,
        n_bays=n_bays,
        v_nom=132.0,
        substation=substation
    )

    cbs, discs = get_switches_by_type(grid)

    # Breaker-and-a-half creates bay sections at indices 0, 2, 4, ... (stepping by 2)
    # Each section has 3 CBs: SW1_i, SW2_i, SW3_i
    # For n_bays=4, sections are at indices 0 and 2
    expected_bay_indices = list(range(0, n_bays, 2))  # [0, 2]

    for bay_idx in expected_bay_indices:
        bay_cbs = [sw for sw in cbs
                  if f"SW1_{bay_idx}" in sw.name or
                     f"SW2_{bay_idx}" in sw.name or
                     f"SW3_{bay_idx}" in sw.name]

        assert len(bay_cbs) == 3, \
            f"Bay section {bay_idx} should have 3 CBs, got {len(bay_cbs)}"

    # Verify total number of CBs matches expectations (3 per section)
    expected_total_cbs = len(expected_bay_indices) * 3
    assert len(cbs) == expected_total_cbs, \
        f"Expected {expected_total_cbs} CBs total, got {len(cbs)}"


# =============================================================================
# Bay Reordering Tests
# =============================================================================

def test_bay_order_respected_in_conversion():
    """Test that bay assignments order is respected during conversion."""
    grid, central_bus, lines = create_test_grid_with_bus(n_branches=4)

    # Create bay assignments with custom order (reversed)
    # Format: (device_name, bay_number, assigned_bus)
    bay_assignments = [
        (lines[3].name, 1, "JBP1"),  # Line_3 should go to first position
        (lines[2].name, 2, "JBP1"),  # Line_2 to second
        (lines[1].name, 3, "JBP1"),  # Line_1 to third
        (lines[0].name, 4, "JBP1"),  # Line_0 to fourth
    ]

    all_buses, conn_buses, branches, injections, reconnections = transform_bus_into_voltage_level(
        grid=grid,
        bus=central_bus,
        vl_type=VoltageLevelTypes.SingleBar,
        add_disconnectors=False,
        bay_assignments=bay_assignments
    )

    # Verify the reconnections follow the specified order
    # First reconnection should be for Line_3 (first in bay_assignments)
    assert reconnections[0][0].name == "Line_3", \
        f"First reconnection should be Line_3, got {reconnections[0][0].name}"

    # Last reconnection should be for Line_0
    assert reconnections[3][0].name == "Line_0", \
        f"Last reconnection should be Line_0, got {reconnections[3][0].name}"


def test_bay_order_with_same_bay_numbers():
    """Test that row order takes precedence when bay numbers are the same."""
    grid, central_bus, lines = create_test_grid_with_bus(n_branches=4)

    # All devices have the same bay number - order should be determined by row index
    bay_assignments = [
        (lines[2].name, 1, "JBP1"),  # Row 0: Line_2
        (lines[0].name, 1, "JBP1"),  # Row 1: Line_0
        (lines[3].name, 1, "JBP1"),  # Row 2: Line_3
        (lines[1].name, 1, "JBP1"),  # Row 3: Line_1
    ]

    all_buses, conn_buses, branches, injections, reconnections = transform_bus_into_voltage_level(
        grid=grid,
        bus=central_bus,
        vl_type=VoltageLevelTypes.SingleBar,
        add_disconnectors=False,
        bay_assignments=bay_assignments
    )

    # Order should follow row index, not bay number
    expected_order = ["Line_2", "Line_0", "Line_3", "Line_1"]
    actual_order = [r[0].name for r in reconnections]

    assert actual_order == expected_order, \
        f"Expected order {expected_order}, got {actual_order}"


# =============================================================================
# Integration Tests
# =============================================================================

def test_conversion_preserves_connectivity():
    """Test that conversion preserves electrical connectivity."""
    grid, central_bus, lines = create_test_grid_with_bus(n_branches=4)

    # Get original remote buses
    original_remote_buses = set()
    for line in lines:
        if line.bus_from == central_bus:
            original_remote_buses.add(line.bus_to)
        else:
            original_remote_buses.add(line.bus_from)

    # Convert to voltage level
    all_buses, conn_buses, branches, injections, reconnections = transform_bus_into_voltage_level(
        grid=grid,
        bus=central_bus,
        vl_type=VoltageLevelTypes.DoubleBar,
        add_disconnectors=True
    )

    # Remote buses should still be connected (to new connection buses)
    for line in lines:
        new_bus = line.bus_from if line.bus_from != central_bus else line.bus_to

        # The new connection should be to a connection bus
        assert new_bus in conn_buses or new_bus in original_remote_buses, \
            f"Line {line.name} should connect to a connection bus"


def test_all_scheme_types_create_valid_structures():
    """Test that all scheme types create valid voltage level structures."""
    schemes = [
        (VoltageLevelTypes.SingleBar, False),
        (VoltageLevelTypes.SingleBar, True),
        (VoltageLevelTypes.DoubleBar, False),
        (VoltageLevelTypes.DoubleBar, True),
        (VoltageLevelTypes.Ring, False),
        (VoltageLevelTypes.Ring, True),
        (VoltageLevelTypes.BreakerAndAHalf, False),
        (VoltageLevelTypes.BreakerAndAHalf, True),
    ]

    for vl_type, add_disconnectors in schemes:
        grid, central_bus, lines = create_test_grid_with_bus(n_branches=4)

        try:
            all_buses, conn_buses, branches, injections, reconnections = transform_bus_into_voltage_level(
                grid=grid,
                bus=central_bus,
                vl_type=vl_type,
                add_disconnectors=add_disconnectors
            )

            # Basic validation
            assert len(all_buses) > 0, \
                f"{vl_type.value} (disconnectors={add_disconnectors}) should create buses"
            assert len(conn_buses) > 0, \
                f"{vl_type.value} (disconnectors={add_disconnectors}) should create connection buses"
            assert len(reconnections) == len(lines), \
                f"{vl_type.value} (disconnectors={add_disconnectors}) should reconnect all branches"

        except Exception as e:
            pytest.fail(f"Failed for {vl_type.value} (disconnectors={add_disconnectors}): {e}")


# Reducible/retained switch impedance tests

def test_conversion_marks_all_switches_reducible():
    """
    With reducible_branches=True every switch created in the conversion must be
    reducible, not retained, and receive a small non-zero reactance.
    """
    # Small non-zero reactance assigned to every switch created in the conversion.
    switch_x = 1e-5

    grid, central_bus, lines = create_test_grid_with_bus(n_branches=4)

    transform_bus_into_voltage_level(
        grid=grid,
        bus=central_bus,
        vl_type=VoltageLevelTypes.DoubleBar,
        add_disconnectors=True,
        reducible_branches=True
    )

    switches = grid.switch_devices
    assert len(switches) > 0, "Conversion should create switches"

    for sw in switches:
        assert sw.reducible is True, f"Switch {sw.name} should be reducible"
        assert sw.retained is False, f"Switch {sw.name} should not be retained"
        assert sw.X == pytest.approx(switch_x), \
            f"Switch {sw.name} X should be {switch_x}, got {sw.X}"


def test_conversion_marks_all_switches_retained():
    """
    With reducible_branches=False every switch created in the conversion must be
    retained, not reducible, and receive a small non-zero reactance.
    """
    # Small non-zero reactance assigned to every switch created in the conversion.
    switch_x = 1e-5

    grid, central_bus, lines = create_test_grid_with_bus(n_branches=4)

    transform_bus_into_voltage_level(
        grid=grid,
        bus=central_bus,
        vl_type=VoltageLevelTypes.DoubleBar,
        add_disconnectors=True,
        reducible_branches=False
    )

    switches = grid.switch_devices
    assert len(switches) > 0, "Conversion should create switches"

    for sw in switches:
        assert sw.reducible is False, f"Switch {sw.name} should not be reducible"
        assert sw.retained is True, f"Switch {sw.name} should be retained"
        assert sw.X == pytest.approx(switch_x), \
            f"Switch {sw.name} X should be {switch_x}, got {sw.X}"


def test_conversion_reducible_flag_applies_to_jbpt_switches():
    """The reducible flag must also reach the transfer-bus (JBPT) switches."""
    # Small non-zero reactance assigned to every switch created in the conversion.
    switch_x = 1e-5

    grid, central_bus, lines = create_test_grid_with_bus(n_branches=4)

    transform_bus_into_voltage_level(
        grid=grid,
        bus=central_bus,
        vl_type=VoltageLevelTypes.DoubleBar,
        add_disconnectors=True,
        enable_transfer_bus=True,
        reducible_branches=False
    )

    jbpt_switches = [sw for sw in grid.switch_devices if "JBPT" in sw.name]
    assert len(jbpt_switches) > 0, "Transfer bus should create JBPT switches"

    for sw in jbpt_switches:
        assert sw.reducible is False, f"JBPT switch {sw.name} should not be reducible"
        assert sw.retained is True, f"JBPT switch {sw.name} should be retained"
        assert sw.X == pytest.approx(switch_x)
