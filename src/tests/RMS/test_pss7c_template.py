# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""PSS7C independent frequency-response and allocation checks."""
from __future__ import annotations

import json
import numpy as np
import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss7c import build_pss7c_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.ramp_tracking_stabilizer import RampStabilizerParameters
from VeraGridEngine.Utils.Symbolic.symbolic import Const
from VeraGridEngine.Utils.Symbolic.block import Block
from tests.RMS.test_native_turbine_governors import initialized_values, linearized_response
from tests.symbolic_block_roundtrip import roundtrip_block


def build_test_controller() -> RmsModelTemplate:
    """Create one linear PSS7C operating point for independent response checks.

    :return: PSS7C RMS template with unsaturated and continuously enabled output.
    """
    ramp: RampStabilizerParameters = RampStabilizerParameters(
        washout_times=(3.0,5.0,4.0,6.0), transducer_times=(.02,.03),
        ks1=5.0,ks2=.4,ks3=.7,t8=.1,t9=.2,ramp_m=2,ramp_n=2,
        upper=10.0,lower=-10.0,input_limits=((-100.0,100.0),(-100.0,100.0)))
    return build_pss7c_template(VarFactory(),'pss7c_response',ramp,
        (.4,1.2,.3,.2,.1),(.1,.2,.3,.4),(1.0,1.0),-1.0,0.0,0.0,1.0)


@pytest.mark.parametrize('path',(0,1))
@pytest.mark.parametrize('frequency',(.02,.4,2.0))
def test_pss7c_dual_input_frequency_response(path: int, frequency: float) -> None:
    """Both selected input channels match the source block transfer structure.

    :param path: Independently perturbed measured input channel.
    :param frequency: Perturbation frequency in hertz.
    :return: None.
    """
    block: Block = build_test_controller().block
    values: dict[int,float] = initialized_values(block)
    if path == 1:
        block.in_vars[0], block.in_vars[1] = block.in_vars[1], block.in_vars[0]
    else:
        pass
    s: complex = 2j*np.pi*frequency
    ramp_filter: complex = ((1.0+.1*s)/(1.0+.2*s)**2)**2
    canonical_denominator: complex = (.1*.2*.3*.4*s**4 + .2*.3*.4*s**3 + .3*.4*s**2 + .4*s + 1.0)
    canonical_numerator: complex = (.4*.1*.2*.3*.4*s**4 + 1.2*.2*.3*.4*s**3 +
        .3*.3*.4*s**2 + .2*.4*s + .1)
    canonical: complex = canonical_numerator/canonical_denominator
    first_path: complex = 5.0*canonical*ramp_filter*(3.0*s/(1.0+3.0*s))*(5.0*s/(1.0+5.0*s))/(1.0+.02*s)
    second_path: complex = (5.0*canonical*(.7*ramp_filter-1.0)*.4*
        (4.0*s/(1.0+4.0*s))*(6.0*s/(1.0+6.0*s))/(1.0+.03*s))
    expected: complex = first_path if path == 0 else second_path
    assert linearized_response(block,values,path,frequency) == pytest.approx(expected,rel=1e-7,abs=1e-9)


def test_pss7c_fixed_nineteen_states_initialize_from_nonzero_inputs() -> None:
    """Washout memories seed from both selected inputs and retain 19 allocated states.

    :return: None.
    """
    block: Block = build_test_controller().block
    block.init_eqs[block.in_vars[0]] = Const(.3)
    block.init_eqs[block.in_vars[1]] = Const(.4)
    block.init_eqs[block.in_vars[2]] = Const(.5)
    values: dict[int,float] = initialized_values(block)
    assert len(block.state_vars) == 19
    np.testing.assert_allclose([equation.eval_uid(values) for equation in block.state_eqs],0.0,atol=1e-12)
    assert block.out_vars[0].uid in values
    assert values[block.out_vars[0].uid] == pytest.approx(0.0)


def test_pss7c_graph_round_trips_through_json() -> None:
    """Preserve the fixed state allocation and public signal ports.

    :return: None.
    """
    block: Block = build_test_controller().block
    payload: dict[str, object] = json.loads(json.dumps(block.to_dict()))
    restored: Block = roundtrip_block(block)
    assert json.loads(json.dumps(restored.to_dict())) == payload
    assert len(restored.state_vars) == 19
    assert len(restored.in_vars) == 3
    assert len(restored.out_vars) == 1
