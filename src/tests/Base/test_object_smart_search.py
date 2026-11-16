# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Aggregation.market_unit import MarketUnit
from VeraGridEngine.Devices.Aggregation.market_units_group import MarketUnitsGroup
from VeraGridEngine.Devices.Aggregation.facility import Facility
from VeraGridEngine.Utils.Filtering.objects_filtering import FilterObjects


def build_generator_filter_engine() -> FilterObjects:
    """
    Build a reusable filter engine with representative generator objects.

    :return: Initialized object filter.
    """
    bus_1: Bus = Bus(name="Bus-1")
    bus_2: Bus = Bus(name="Bus-2")
    generator_without_bus: Generator = Generator(
        name="Alpha",
        P=10.0,
        vset=1.00,
    )
    generator_with_bus_1: Generator = Generator(
        name="Beta",
        P=25.0,
        vset=1.05,
    )
    generator_with_bus_1.bus = bus_1
    generator_with_bus_2: Generator = Generator(
        name="Gamma",
        P=40.0,
        vset=1.10,
    )
    generator_with_bus_2.bus = bus_2
    objects: list[Generator] = list([
        generator_without_bus,
        generator_with_bus_1,
        generator_with_bus_2,
    ])

    return FilterObjects(objects)


def test_object_smart_search_can_filter_none_values() -> None:
    """
    Verify that smart object filtering can match explicit ``None`` values.

    :return: None.
    """
    filter_engine: FilterObjects = build_generator_filter_engine()

    filter_engine.filter("bus = None")
    assert list(filter_engine.filtered_indices) == list([0])

    filter_engine.filter("bus = none")
    assert list(filter_engine.filtered_indices) == list([0])

    filter_engine.filter("bus != None")
    assert list(filter_engine.filtered_indices) == list([1, 2])


def test_object_smart_search_can_filter_numeric_properties() -> None:
    """
    Verify numeric comparison filtering on direct object properties.

    :return: None.
    """
    filter_engine: FilterObjects = build_generator_filter_engine()

    filter_engine.filter("P >= 25")
    assert list(filter_engine.filtered_indices) == list([1, 2])

    filter_engine.filter("Vset < 1.10")
    assert list(filter_engine.filtered_indices) == list([0, 1])


def test_object_smart_search_can_filter_nested_device_names() -> None:
    """
    Verify nested property-chain filtering through linked objects.

    :return: None.
    """
    filter_engine: FilterObjects = build_generator_filter_engine()

    filter_engine.filter("bus.name = Bus-1")
    assert list(filter_engine.filtered_indices) == list([1])

    filter_engine.filter("bus.name like Bus-")
    assert list(filter_engine.filtered_indices) == list([1, 2])


def test_object_smart_search_can_combine_conditions() -> None:
    """
    Verify multi-clause smart-search expressions using ``and`` and ``or``.

    :return: None.
    """
    filter_engine: FilterObjects = build_generator_filter_engine()

    filter_engine.filter("bus != None and P > 30")
    assert list(filter_engine.filtered_indices) == list([2])

    filter_engine.filter("name starts Al or bus.name = Bus-2")
    assert list(filter_engine.filtered_indices) == list([0, 2])


def test_object_smart_search_name_fallback_without_operators() -> None:
    """
    Verify the legacy plain-text fallback that searches by object name.

    :return: None.
    """
    filter_engine: FilterObjects = build_generator_filter_engine()

    filter_engine.filter("alp")
    assert list(filter_engine.filtered_indices) == list([0])

    filter_engine.filter("Alpha")
    assert list(filter_engine.filtered_indices) == list([0])


def test_object_smart_search_can_filter_pointer_devices() -> None:
    """
    Verify smart filtering on pointer devices like MarketUnit pointing to Facility.

    :return: None.
    """
    group_1: MarketUnitsGroup = MarketUnitsGroup(name="Group 1")
    facility_1: Facility = Facility(name="Facility 1")

    market_unit_with_device: MarketUnit = MarketUnit(
        name="MU 1",
        device=facility_1,
        group=group_1,
    )
    market_unit_without_device: MarketUnit = MarketUnit(
        name="MU 2",
        device=None,
        group=None,
    )

    objects: list[MarketUnit] = list([
        market_unit_with_device,
        market_unit_without_device,
    ])
    filter_engine: FilterObjects = FilterObjects(objects)

    filter_engine.filter("device = None")
    assert list(filter_engine.filtered_indices) == list([1])

    filter_engine.filter("group = None")
    assert list(filter_engine.filtered_indices) == list([1])

    filter_engine.filter("device.name = Facility 1")
    assert list(filter_engine.filtered_indices) == list([0])

    filter_engine.filter("group.name = Group 1")
    assert list(filter_engine.filtered_indices) == list([0])

