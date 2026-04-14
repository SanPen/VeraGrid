# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.Substation.voltage_level_template import VoltageLevelTemplate


def test_slotted_device_declared_properties_coerce_values() -> None:
    """
    Check that slotted device properties coerce assigned values.

    :return: None
    """
    bus = Bus()

    bus.Vnom = "132.5"
    bus.is_slack = "1"

    assert isinstance(bus.Vnom, float)
    assert isinstance(bus.is_slack, bool)
    assert bus.Vnom == 132.5
    assert bus.is_slack is True


def test_plain_device_declared_properties_coerce_values() -> None:
    """
    Check that dict-backed device properties coerce assigned values.

    :return: None
    """
    template = VoltageLevelTemplate()

    template.voltage = "33.0"
    template.n_bays = "4"
    template.add_disconnectors = "1"

    assert isinstance(template.voltage, float)
    assert isinstance(template.n_bays, int)
    assert isinstance(template.add_disconnectors, bool)
    assert template.voltage == 33.0
    assert template.n_bays == 4
    assert template.add_disconnectors is True


def test_parent_declared_properties_coerce_on_child_instances() -> None:
    """
    Check that parent-declared properties still coerce on child instances.

    :return: None
    """
    generator = Generator()

    generator.capex = "12.5"
    generator.active = "1"
    generator.Pf = "0.85"

    assert isinstance(generator.capex, float)
    assert isinstance(generator.active, bool)
    assert isinstance(generator.Pf, float)
    assert generator.capex == 12.5
    assert generator.active is True
    assert generator.Pf == 0.85
