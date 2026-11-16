# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""PSS1A native graph follows the supplied PSS/E IEEEST coefficient map."""

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms import build_international_standard_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss1a import (
    Pss1aParameters,
    build_pss1a_template,
)
from VeraGridEngine.enumerations import InternationalStandardModel
from VeraGridEngine.Utils.Symbolic.symbolic import Const


def test_pss1a_catalogue_uses_native_ieeest_kernel_with_mapped_constants() -> None:
    """The standard builder carries the PSS1A table's structural zeroes."""
    parameters: Pss1aParameters = Pss1aParameters(
        filter_coefficients=(0.3, 0.04, 0.2), lead1=0.6, lag1=0.1,
        lead2=0.7, lag2=0.2, washout_time=4.0, gain=8.0,
        upper=0.12, lower=-0.13,
    )
    template = build_pss1a_template(VarFactory(), 'PSS1A_TEST', parameters)
    assert template.name == 'PSS1A_TEST'
    assert len(template.block.in_vars) == 2
    assert len(template.block.out_vars) == 1
    values: dict[str, float] = dict()
    for variable, expression in template.block.event_dict.items():
        if isinstance(expression, Const):
            values[variable.name.removesuffix('_PSS1A_TEST')] = expression.value
        else:
            pass
    assert values['A1'] == 0.3
    assert values['A2'] == 0.04
    assert values['A3'] == 0.2
    assert values['A4'] == 0.0
    assert values['A5'] == 0.0
    assert values['A6'] == 0.0
    assert values['T5'] == values['T6'] == 4.0
    assert values['VCU'] == values['VCL'] == 0.0
    assert values['KS'] == 8.0
    assert values['LSMAX'] == 0.12
    assert values['LSMIN'] == -0.13
    catalogue = build_international_standard_template(
        InternationalStandardModel.PSS1A, VarFactory(),
    )
    assert catalogue is not None
    assert catalogue.name == 'PSS1A'
