# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Tests for transformer-specific CGMES utility helpers."""

import pytest

from VeraGridEngine.IO.cim.cgmes.cgmes_utils import (
    get_pu_values_power_transformer,
    get_pu_values_power_transformer_end,
    get_voltage_power_transformer_end,
)
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.base_voltage import BaseVoltage
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.power_transformer import PowerTransformer
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.power_transformer_end import PowerTransformerEnd


@pytest.fixture
def transformer_end_with_rated_u():
    """Build a transformer end that exposes its voltage through ``ratedU``."""
    transformer_end = PowerTransformerEnd()
    transformer_end.ratedU = 110
    transformer_end.BaseVoltage = None
    return transformer_end


@pytest.fixture
def transformer_end_with_base_voltage():
    """Build a transformer end that exposes its voltage through ``BaseVoltage``."""
    transformer_end = PowerTransformerEnd()
    transformer_end.ratedU = 0
    transformer_end.BaseVoltage = BaseVoltage()
    transformer_end.BaseVoltage.nominalVoltage = 220
    return transformer_end


@pytest.fixture
def transformer_end_without_voltage():
    """Build a transformer end with no available voltage information."""
    transformer_end = PowerTransformerEnd()
    transformer_end.ratedU = 0
    transformer_end.BaseVoltage = None
    return transformer_end


def test_get_windings_no_windings_returns_no_element():
    """Keep an empty transformer end reference list unset when no windings are attached."""
    power_transformer = PowerTransformer("a", "b")
    assert power_transformer.PowerTransformerEnd is None


def test_get_pu_values_power_transformer_no_power_transformer():
    """Raise an attribute error when the aggregate helper is called with no transformer object."""
    with pytest.raises(AttributeError) as excinfo:
        get_pu_values_power_transformer(None, 100.0)

    assert "NoneType" in str(excinfo.value)


def test_get_pu_values_power_transformer_no_winding():
    """Return zeros when a transformer has no ends to contribute series or shunt values."""
    power_transformer = PowerTransformer()
    power_transformer.PowerTransformerEnd = []

    resistance, reactance, conductance, susceptance, resistance_zero, reactance_zero, conductance_zero, \
        susceptance_zero = get_pu_values_power_transformer(power_transformer, 100.0)

    assert resistance == 0
    assert reactance == 0
    assert conductance == 0
    assert susceptance == 0
    assert resistance_zero == 0
    assert reactance_zero == 0
    assert conductance_zero == 0
    assert susceptance_zero == 0


def test_get_pu_values_power_transformer_two_windings():
    """Aggregate two identical transformer ends into the expected per-unit branch values."""
    power_transformer = PowerTransformer()

    power_transformer_end = PowerTransformerEnd()
    power_transformer_end.ratedS = 1
    power_transformer_end.ratedU = 2
    power_transformer_end.r = 1
    power_transformer_end.x = 1
    power_transformer_end.g = 1
    power_transformer_end.b = 1
    power_transformer_end.r0 = 1
    power_transformer_end.x0 = 1
    power_transformer_end.g0 = 1
    power_transformer_end.b0 = 1
    power_transformer_end.endNumber = 1

    power_transformer.PowerTransformerEnd = [power_transformer_end, power_transformer_end]

    resistance, reactance, conductance, susceptance, resistance_zero, reactance_zero, conductance_zero, \
        susceptance_zero = get_pu_values_power_transformer(power_transformer, 100.0)

    assert resistance == 50
    assert reactance == 50
    assert conductance == 800
    assert susceptance == 800
    assert resistance_zero == 50
    assert reactance_zero == 50
    assert conductance_zero == 800
    assert susceptance_zero == 800


def test_get_voltage_power_transformer_end_has_rated_u_value_returns_value(transformer_end_with_rated_u):
    """Prefer the explicit rated voltage when it is available on a transformer end."""
    assert get_voltage_power_transformer_end(transformer_end_with_rated_u) == 110


def test_get_voltage_power_transformer_end_has_base_voltage_value_returns_value(
        transformer_end_with_base_voltage):
    """Fall back to the linked base-voltage nominal value when ``ratedU`` is not usable."""
    assert get_voltage_power_transformer_end(transformer_end_with_base_voltage) == 220


def test_get_voltage_power_transformer_end_has_no_voltage_returns_none(transformer_end_without_voltage):
    """Return ``None`` when a transformer end has neither ``ratedU`` nor ``BaseVoltage``."""
    assert get_voltage_power_transformer_end(transformer_end_without_voltage) is None


def test_get_pu_values_power_transformer_end_no_rated_s_and_rated_u_returns_default():
    """Use the defensive tiny defaults when a transformer end lacks rating data."""
    power_transformer_end = PowerTransformerEnd()

    resistance, reactance, conductance, susceptance, resistance_zero, reactance_zero, conductance_zero, \
        susceptance_zero = get_pu_values_power_transformer_end(power_transformer_end)

    assert resistance == 1e-20
    assert reactance == 1e-20
    assert conductance == 1e-20
    assert susceptance == 1e-20
    assert resistance_zero == 1e-20
    assert reactance_zero == 1e-20
    assert conductance_zero == 1e-20
    assert susceptance_zero == 1e-20
