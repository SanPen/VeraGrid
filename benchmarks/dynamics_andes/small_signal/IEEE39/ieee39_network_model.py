# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Static IEEE39 network normalization for the dynamic reference case."""

from __future__ import annotations

from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.Devices.Injections.shunt import Shunt
from VeraGridEngine.Devices.Substation.bus import Bus
import VeraGridEngine.api as gce


def _bus_number(bus: Bus) -> int:
    """Return the integer RAW bus code.

    :param bus: VeraGrid bus loaded from the IEEE39 RAW file.
    :return: One-based IEEE bus number.
    """
    return int(bus.code)


def _find_bus(grid: gce.MultiCircuit, bus_number: int) -> Bus | None:
    """Find one IEEE39 bus by its stable RAW bus code.

    :param grid: RAW-loaded VeraGrid network.
    :param bus_number: One-based IEEE bus number.
    :return: Matching bus or ``None``.
    """
    matching_bus: Bus | None = None
    bus: Bus
    for bus in grid.buses:
        if _bus_number(bus) == bus_number:
            matching_bus = bus
        else:
            pass
    return matching_bus


def _get_generator_operating_points() -> dict[int, tuple[float, float, float, float, float]]:
    """Return dynamic-case generator operating points in bus order.

    :return: Ten generator records for buses 30 through 39.
    """
    return {
        30: (436.086385, 1.035534, 1040.0, 153.18, -58.084),
        31: (645.999998, 1.013246, 836.0, 429.804, -122.665),
        32: (724.999998, 1.020528, 843.7, 446.722, -180.218),
        33: (651.999998, 1.01343, 1174.8, 548.208, -213.78),
        34: (507.999998, 1.019109, 1080.2, 611.495, -188.028),
        35: (686.999998, 1.06, 1085.7, 593.788, -234.972),
        36: (579.999998, 1.06, 1025.2, 568.372, -249.132),
        37: (321.521338, 1.013996, 970.2, 443.468, -216.122),
        38: (764.783381, 1.052803, 1684.1, 834.775, -356.889),
        39: (574.17, 1.03, 1199.0, 574.85, -173.261),
    }


def _get_load_operating_points() -> dict[int, tuple[float, float]]:
    """Return dynamic-case constant-power loads in bus order.

    :return: Nineteen load records.
    """
    return {
        3: (600.0, 250.0),
        4: (450.0, 184.0),
        7: (233.8, 84.0),
        8: (522.0, 176.6),
        12: (120.0, 30.0),
        15: (320.0, 153.0),
        16: (329.0, 32.3),
        18: (158.0, 30.0),
        20: (680.0, 103.0),
        21: (274.0, 115.0),
        23: (247.5, 84.6),
        24: (308.6, -92.2),
        25: (224.0, 47.2),
        26: (139.0, 17.0),
        27: (281.0, 75.5),
        28: (206.0, 27.6),
        29: (283.5, 126.9),
        31: (80.0, 40.0),
        39: (400.0, 250.0),
    }


def configure_ieee39_static_network(grid: gce.MultiCircuit) -> None:
    """Normalize a RAW-loaded network to the IEEE39 dynamic workbook.

    The RAW file contains four additional synchronous condensers and several
    stale load values.  The dynamic workbook retains only generators at buses
    30..39 and converts switched shunts at buses 4 and 5 to fixed shunts.

    :param grid: IEEE39 network loaded from the matching RAW case.
    :return: None.
    :raises ValueError: If a required generator or load is absent.
    """
    generator_points: dict[int, tuple[float, float, float, float, float]] = (
        _get_generator_operating_points()
    )
    load_points: dict[int, tuple[float, float]] = _get_load_operating_points()

    # Remove RAW-only condensers and configure the ten dynamic generators.
    generators: list[Generator] = list(grid.generators)
    generator: Generator
    configured_generator_count: int = 0
    for generator in generators:
        generator_bus_number: int = _bus_number(generator.bus)
        generator_point: tuple[float, float, float, float, float] | None = (
            generator_points.get(generator_bus_number, None)
        )
        if generator_point is None:
            grid.delete_injection_device(generator)
        else:
            p, vset, snom, qmax, qmin = generator_point
            generator.P = p
            generator.Vset = vset
            generator.Snom = snom
            generator.Qmax = qmax
            generator.Qmin = qmin
            generator.Pmax = snom
            generator.Pmin = 0.0
            configured_generator_count += 1
    if configured_generator_count != len(generator_points):
        raise ValueError(
            f"Configured {configured_generator_count} IEEE39 generators; "
            f"expected {len(generator_points)}."
        )
    else:
        pass

    # Parameter tables are indexed in bus order 30..39; reject a RAW importer
    # ordering change instead of silently applying a machine record to a
    # different generator.
    generator_index: int
    for generator_index in range(len(grid.generators)):
        ordered_bus_number: int = _bus_number(grid.generators[generator_index].bus)
        expected_bus_number: int = generator_index + 30
        if ordered_bus_number != expected_bus_number:
            raise ValueError(
                f"IEEE39 generator {generator_index + 1} is at bus "
                f"{ordered_bus_number}; expected bus {expected_bus_number}."
            )
        else:
            pass

    # Correct the load records to the values exported by the dynamic workbook.
    loads: list[Load] = list(grid.loads)
    load: Load
    configured_load_count: int = 0
    for load in loads:
        load_bus_number: int = _bus_number(load.bus)
        load_point: tuple[float, float] | None = load_points.get(load_bus_number, None)
        if load_point is None:
            grid.delete_injection_device(load)
        else:
            p, q = load_point
            load.P = p
            load.Q = q
            configured_load_count += 1
    if configured_load_count != len(load_points):
        raise ValueError(
            f"Configured {configured_load_count} IEEE39 loads; "
            f"expected {len(load_points)}."
        )
    else:
        pass

    # Replace switched RAW shunts with the two fixed workbook susceptances.
    shunt_devices: list[object] = list(grid.shunts)
    controllable_shunts: list[object] = list(grid.controllable_shunts)
    shunt_device: object
    for shunt_device in shunt_devices:
        grid.delete_injection_device(shunt_device)
    for shunt_device in controllable_shunts:
        grid.delete_injection_device(shunt_device)
    bus_four: Bus | None = _find_bus(grid=grid, bus_number=4)
    bus_five: Bus | None = _find_bus(grid=grid, bus_number=5)
    if bus_four is None or bus_five is None:
        raise ValueError("IEEE39 buses 4 and 5 are required for fixed shunts.")
    else:
        pass
    grid.add_shunt(bus=bus_four, api_obj=Shunt(name="IEEE39 fixed shunt 4", B=100.0))
    grid.add_shunt(bus=bus_five, api_obj=Shunt(name="IEEE39 fixed shunt 5", B=200.0))

    # The matching workbook contains 34 AC lines and 12 tap transformers.
    if len(grid.lines) != 34:
        raise ValueError(f"IEEE39 requires 34 lines; found {len(grid.lines)}.")
    else:
        pass
    if len(grid.transformers2w) != 12:
        raise ValueError(
            f"IEEE39 requires 12 two-winding transformers; "
            f"found {len(grid.transformers2w)}."
        )
    else:
        pass
    if len(grid.shunts) != 2:
        raise ValueError(f"IEEE39 requires 2 fixed shunts; found {len(grid.shunts)}.")
    else:
        pass
