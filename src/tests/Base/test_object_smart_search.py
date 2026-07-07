from VeraGridEngine.Devices.Aggregation.market_unit import MarketUnit
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Utils.Filtering.objects_filtering import FilterObjects


def build_generator_filter_engine() -> FilterObjects:
    """
    Build a reusable filter engine with representative generator objects.

    :return: Initialized object filter.
    """
    market_unit_1: MarketUnit = MarketUnit(name="MU-1")
    market_unit_2: MarketUnit = MarketUnit(name="MU-2")
    generator_without_market: Generator = Generator(
        name="Alpha",
        P=10.0,
        vset=1.00,
        market_unit=None,
    )
    generator_with_market_1: Generator = Generator(
        name="Beta",
        P=25.0,
        vset=1.05,
        market_unit=market_unit_1,
    )
    generator_with_market_2: Generator = Generator(
        name="Gamma",
        P=40.0,
        vset=1.10,
        market_unit=market_unit_2,
    )
    objects: list[Generator] = [
        generator_without_market,
        generator_with_market_1,
        generator_with_market_2,
    ]

    return FilterObjects(objects)


def test_object_smart_search_can_filter_none_values() -> None:
    """
    Verify that smart object filtering can match explicit ``None`` values.

    :return: None.
    """
    filter_engine: FilterObjects = build_generator_filter_engine()

    filter_engine.filter("market_unit = None")
    assert list(filter_engine.filtered_indices) == [0]

    filter_engine.filter("market_unit = none")
    assert list(filter_engine.filtered_indices) == [0]

    filter_engine.filter("market_unit != None")
    assert list(filter_engine.filtered_indices) == [1, 2]


def test_object_smart_search_can_filter_numeric_properties() -> None:
    """
    Verify numeric comparison filtering on direct object properties.

    :return: None.
    """
    filter_engine: FilterObjects = build_generator_filter_engine()

    filter_engine.filter("P >= 25")
    assert list(filter_engine.filtered_indices) == [1, 2]

    filter_engine.filter("Vset < 1.10")
    assert list(filter_engine.filtered_indices) == [0, 1]


def test_object_smart_search_can_filter_nested_device_names() -> None:
    """
    Verify nested property-chain filtering through linked objects.

    :return: None.
    """
    filter_engine: FilterObjects = build_generator_filter_engine()

    filter_engine.filter("market_unit.name = MU-1")
    assert list(filter_engine.filtered_indices) == [1]

    filter_engine.filter("market_unit.name like MU-")
    assert list(filter_engine.filtered_indices) == [1, 2]


def test_object_smart_search_can_combine_conditions() -> None:
    """
    Verify multi-clause smart-search expressions using ``and`` and ``or``.

    :return: None.
    """
    filter_engine: FilterObjects = build_generator_filter_engine()

    filter_engine.filter("market_unit != None and P > 30")
    assert list(filter_engine.filtered_indices) == [2]

    filter_engine.filter("name starts Al or market_unit.name = MU-2")
    assert list(filter_engine.filtered_indices) == [0, 2]


def test_object_smart_search_name_fallback_without_operators() -> None:
    """
    Verify the legacy plain-text fallback that searches by object name.

    :return: None.
    """
    filter_engine: FilterObjects = build_generator_filter_engine()

    filter_engine.filter("alp")
    assert list(filter_engine.filtered_indices) == [0]
