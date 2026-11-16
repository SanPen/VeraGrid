# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Check the separate native AC6A and ESAC6A limiter realizations."""
from __future__ import annotations

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms import build_international_standard_template
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.enumerations import InternationalStandardModel
from tests.RMS.test_native_turbine_governors import initialized_values


@pytest.mark.parametrize('model', (InternationalStandardModel.AC6A, InternationalStandardModel.ESAC6A))
def test_ac6a_family_has_source_ports_and_balanced_initial_state(model: InternationalStandardModel) -> None:
    """Both five-state source forms initialize and retain their DAE equations."""
    block: Block = build_international_standard_template(model, VarFactory(), 'ac6a_check').block
    values: dict[int, float] = initialized_values(block)

    assert len(block.in_vars) == 6
    assert len(block.out_vars) == 3
    assert len(block.state_vars) == 5
    assert len(block.diff_vars) == 5
    assert all(abs(equation.eval_uid(values)) < 1e-10 for equation in block.state_eqs)
    assert all(abs(equation.eval_uid(values)) < 1e-10 for equation in block.algebraic_eqs)

    regulator_states: tuple[str, ...] = tuple(
        variable.name for variable in block.state_vars
        if 'RegulatorPu' in variable.name
    )
    if model == InternationalStandardModel.AC6A:
        assert any('BoundedRegulatorPuMemory' in name for name in regulator_states)
        assert not any('UnboundedRegulatorPuState' in name for name in regulator_states)
    else:
        assert any('UnboundedRegulatorPuState' in name for name in regulator_states)
        assert not any('BoundedRegulatorPuMemory' in name for name in regulator_states)


def test_ac6a_and_esac6a_have_distinct_second_stage_equations() -> None:
    """The revised tracking memory is not aliased to the original lag state."""
    ac6a: Block = build_international_standard_template(
        InternationalStandardModel.AC6A, VarFactory(), 'revised'
    ).block
    esac6a: Block = build_international_standard_template(
        InternationalStandardModel.ESAC6A, VarFactory(), 'original'
    ).block
    ac6a_regulator: str = next(
        str(equation) for state, equation in zip(ac6a.state_vars, ac6a.state_eqs)
        if 'BoundedRegulatorPuMemory' in state.name
    )
    esac6a_regulator: str = next(
        str(equation) for state, equation in zip(esac6a.state_vars, esac6a.state_eqs)
        if 'UnboundedRegulatorPuState' in state.name
    )

    assert ac6a_regulator != esac6a_regulator
    assert 'BoundedRegulatorPu' in ac6a_regulator
    assert 'BoundedRegulatorPu' not in esac6a_regulator


@pytest.mark.parametrize('model', (InternationalStandardModel.AC6A, InternationalStandardModel.ESAC6A))
def test_ac6a_feedback_and_uel_follow_the_source_diagram(model: InternationalStandardModel) -> None:
    """UEL adds at the reference summer and field feedback subtracts after the lead-lag."""
    block: Block = build_international_standard_template(model, VarFactory(), 'diagram_check').block
    equations: tuple[str, ...] = tuple(str(equation) for equation in block.algebraic_eqs)
    first_regulator_state: str = next(
        str(equation) for state, equation in zip(block.state_vars, block.state_eqs)
        if 'FirstRegulatorPuState' in state.name
    )
    forcing_equation: str = next(
        equation for equation in equations if 'FieldForcingPu_diagram_check' in equation
    )

    assert 'UelPu_diagram_check' in first_regulator_state
    assert 'FeedbackPu_diagram_check' not in first_regulator_state
    assert 'FeedbackPu_diagram_check' in forcing_equation
    assert 'BoundedRegulatorPu_diagram_check' in forcing_equation
