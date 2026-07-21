from __future__ import annotations

from typing import Iterable

from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at, normalize_upper_bound
from VeraGridEngine.Devices.Branches.transformer import Transformer2W
from VeraGridEngine.Devices.Fluid.fluid_node import FluidNode
from VeraGridEngine.Devices.Fluid.fluid_path import FluidPath
from VeraGridEngine.Devices.Injections.battery import Battery
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.basic_structures import Logger, LogSeverity


def get_warning_properties(logger: Logger) -> set[tuple[str, str]]:
    """
    Collect warning pairs ``(device, property)`` from the logger.

    :param logger: Logger instance to inspect.
    :return: Set of warning pairs.
    """
    warning_properties: set[tuple[str, str]] = set()

    for entry in logger.entries:
        if entry.severity == LogSeverity.Warning:
            warning_properties.add((str(entry.device), str(entry.device_property)))
        else:
            pass

    return warning_properties


def assert_warning_properties_present(
    logger: Logger,
    expected: Iterable[tuple[str, str]],
) -> None:
    """
    Assert that the expected warning triples are present in the logger.

    :param logger: Logger with warning entries.
    :param expected: Expected warning triples.
    :return: ``None``.
    """
    warning_properties: set[tuple[str, str, str]] = get_warning_properties(logger=logger)

    for item in expected:
        assert item in warning_properties


def build_grid_with_reversed_box_constraints() -> MultiCircuit:
    """
    Build a tiny grid with intentionally reversed min/max box constraints.

    :return: Grid prepared for compiler clamping checks.
    """
    grid: MultiCircuit = MultiCircuit(name="compiler-box-constraints")

    slack_bus: Bus = Bus(name="Slack", Vnom=110.0, is_slack=True)
    load_bus: Bus = Bus(name="Load", Vnom=110.0)
    slack_bus.angle_min = 0.5
    slack_bus.angle_max = -0.5
    grid.add_bus(slack_bus)
    grid.add_bus(load_bus)

    generator: Generator = Generator(name="GenClamp", Pmin=12.0, Pmax=5.0, enabled_dispatch=True)
    grid.add_generator(bus=slack_bus, api_obj=generator)

    battery: Battery = Battery(
        name="BattClamp",
        Pmin=7.0,
        Pmax=2.0,
        Enom=20.0,
        min_soc=0.8,
        max_soc=0.2,
        enabled_dispatch=True,
    )
    grid.add_battery(bus=slack_bus, api_obj=battery)

    transformer: Transformer2W = Transformer2W(
        bus_from=slack_bus,
        bus_to=load_bus,
        name="TrClamp",
        r=0.01,
        x=0.05,
    )
    transformer.tap_module_min = 1.1
    transformer.tap_module_max = 0.9
    transformer.tap_phase_min = 0.2
    transformer.tap_phase_max = -0.1
    grid.add_transformer2w(transformer)

    source_node: FluidNode = FluidNode(
        name="NodeClamp",
        min_level=5.0,
        max_level=1.0,
        min_soc=0.9,
        max_soc=0.3,
    )
    target_node: FluidNode = FluidNode(name="NodeTarget", min_level=0.0, max_level=2.0)
    path: FluidPath = FluidPath(
        name="PathClamp",
        source=source_node,
        target=target_node,
        min_flow=4.0,
        max_flow=1.0,
    )
    grid.fluid_nodes.append(source_node)
    grid.fluid_nodes.append(target_node)
    grid.fluid_paths.append(path)

    return grid


def test_normalize_upper_bound_clamps_reversed_box() -> None:
    """
    Check that a reversed bound pair is clamped and logged.

    :return: ``None``.
    """
    logger: Logger = Logger()

    lower_value: float
    upper_value: float
    lower_value, upper_value = normalize_upper_bound(
        lower=8.0,
        upper=3.0,
        logger=logger,
        device_name="ClampDevice",
        device_class="TestDevice",
        lower_name="lower_limit",
        upper_name="upper_limit",
    )

    assert lower_value == 8.0
    assert upper_value == 8.0
    assert logger.warning_count() == 1
    assert logger.error_count() == 0

    entry = logger.entries[0]
    assert entry.msg == "Invalid bounds corrected: upper_limit < lower_limit"
    assert entry.device == "ClampDevice"
    assert entry.device_class == "TestDevice"
    assert entry.device_property == "upper_limit"
    assert entry.expected_value == "8.0"


def test_compile_numerical_circuit_clamps_reversed_box_constraints() -> None:
    """
    Check that representative compiler box constraints are clamped and reported.

    :return: ``None``.
    """
    grid: MultiCircuit = build_grid_with_reversed_box_constraints()
    logger: Logger = Logger()

    nc = compile_numerical_circuit_at(circuit=grid, t_idx=None, logger=logger)

    assert nc.bus_data.angle_min[0] == 0.5
    assert nc.bus_data.angle_max[0] == 0.5

    assert nc.generator_data.pmin[0] == 12.0
    assert nc.generator_data.pmax[0] == 12.0

    assert nc.battery_data.pmin[0] == 7.0
    assert nc.battery_data.pmax[0] == 7.0
    assert nc.battery_data.min_soc[0] == 0.8
    assert nc.battery_data.max_soc[0] == 0.8
    assert nc.battery_data.e_min[0] == 16.0
    assert nc.battery_data.e_max[0] == 16.0

    assert nc.active_branch_data.tap_module_min[0] == 1.1
    assert nc.active_branch_data.tap_module_max[0] == 1.1
    assert nc.active_branch_data.tap_angle_min[0] == 0.2
    assert nc.active_branch_data.tap_angle_max[0] == 0.2

    assert nc.fluid_node_data.min_level[0] == 5.0e6
    assert nc.fluid_node_data.max_level[0] == 5.0e6
    assert nc.fluid_node_data.min_soc[0] == 0.9
    assert nc.fluid_node_data.max_soc[0] == 0.9

    assert nc.fluid_path_data.min_flow[0] == 4.0
    assert nc.fluid_path_data.max_flow[0] == 4.0

    assert logger.warning_count() >= 7
    assert logger.error_count() == 0
    assert_warning_properties_present(
        logger=logger,
        expected=(
            ("Slack", "angle_max"),
            ("GenClamp", "Pmax"),
            ("BattClamp", "Pmax"),
            ("BattClamp", "max_soc"),
            ("NodeClamp", "max_level"),
            ("NodeClamp", "max_soc"),
            ("PathClamp", "max_flow"),
        ),
    )
