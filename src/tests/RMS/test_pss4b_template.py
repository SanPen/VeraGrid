# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""PSS4B graph matches the documented 32-state three-band structure."""

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms import build_international_standard_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss4b import (
    Pss4bParameters,
    build_pss4b_template,
)
from VeraGridEngine.enumerations import InternationalStandardModel
from VeraGridEngine.Utils.Symbolic.symbolic import Const


def test_pss4b_default_graph_has_documented_ports_and_states() -> None:
    """Each physical filter stage contributes the documented state count."""
    template = build_pss4b_template(VarFactory())
    assert template.name == 'PSS4B'
    assert len(template.block.in_vars) == 2
    assert len(template.block.out_vars) == 1
    assert len(template.block.state_vars) == 32
    assert len(template.block.event_dict) == 75
    catalogue = build_international_standard_template(
        InternationalStandardModel.PSS4B, VarFactory(),
    )
    assert catalogue is not None
    assert catalogue.name == 'PSS4B'


def test_pss4b_keeps_each_ordered_source_constant() -> None:
    """The template's named runtime constants preserve source field positions."""
    coefficients: list[float] = [0.0] * 75
    coefficients[2] = 2.0
    coefficients[5] = 1.0
    coefficients[7] = 1.0
    coefficients[8] = 3.0
    coefficients[9] = 4.0
    coefficients[11] = 0.0
    coefficients[13] = 1.0
    coefficients[15] = 1.0
    coefficients[33] = 2.0
    coefficients[34] = -2.0
    coefficients[52] = 2.0
    coefficients[53] = -2.0
    coefficients[71] = 2.0
    coefficients[72] = -2.0
    coefficients[73] = 0.2
    coefficients[74] = -0.2
    template = build_pss4b_template(
        VarFactory(), 'PSS4B_PARAMETERS', Pss4bParameters(tuple(coefficients)),
    )
    values: tuple[float, ...] = tuple(
        expression.value
        for expression in template.block.event_dict.values()
        if isinstance(expression, Const)
    )
    assert len(values) == 75
    assert values[2] == 2.0
    assert values[8] == 3.0
    assert values[9] == 4.0
    assert values[73] == 0.2
    assert values[74] == -0.2


def test_pss4b_rejects_incomplete_source_constant_vectors() -> None:
    """Malformed source payloads fail at the typed template boundary."""
    with pytest.raises(ValueError):
        Pss4bParameters(tuple())
