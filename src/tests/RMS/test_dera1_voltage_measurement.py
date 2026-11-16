# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Check the DERA1 terminal-voltage transducer realization."""

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.renewable_controls.dera1_voltage_measurement import (
    Dera1VoltageMeasurementSettings,
    build_dera1_voltage_measurement_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var


def test_dera1_voltage_measurement_has_source_time_constant_state() -> None:
    """Trv creates a lag state initialized at the solved terminal voltage."""
    block: Block = build_dera1_voltage_measurement_template(
        VarFactory(),
        settings=Dera1VoltageMeasurementSettings(trv=0.1, initial_voltage=0.97),
    ).block
    assert len(block.state_vars) == 1
    bindings: dict[int, float] = dict()
    parameter: Var
    value: Const
    for parameter, value in block.event_dict.items():
        assert isinstance(value, Const)
        bindings[parameter.uid] = float(value.value)
    bindings[block.in_vars[0].uid] = 1.0
    bindings[block.state_vars[0].uid] = 0.97
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(0.3)
    assert block.init_eqs[block.state_vars[0]].eval_uid(bindings) == pytest.approx(0.97)


def test_dera1_zero_time_voltage_measurement_reduces_algebraically() -> None:
    """A zero Trv removes the unnecessary dynamic state."""
    block: Block = build_dera1_voltage_measurement_template(
        VarFactory(), settings=Dera1VoltageMeasurementSettings(trv=0.0),
    ).block
    assert len(block.state_vars) == 0
    assert len(block.algebraic_vars) == 1


def test_dera1_voltage_measurement_rejects_invalid_settings() -> None:
    """Reject nonphysical transducer time and initialization values."""
    with pytest.raises(ValueError, match='Trv'):
        build_dera1_voltage_measurement_template(
            VarFactory(), settings=Dera1VoltageMeasurementSettings(trv=-0.1),
        )
    with pytest.raises(ValueError, match='initial terminal voltage'):
        build_dera1_voltage_measurement_template(
            VarFactory(), settings=Dera1VoltageMeasurementSettings(initial_voltage=0.0),
        )
