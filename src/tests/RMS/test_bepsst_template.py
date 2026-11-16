# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""BEPSST PSS signal path and restricted PSS/E constant binding checks."""

import pytest

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.IO.raw.dyr_parser import parse_dyr
from VeraGridEngine.IO.raw.dyr_to_veragrid import (
    PsseDynamicBinding,
    build_controller,
    dynamic_binding,
    validate_dynamic_parameters,
)
from VeraGridEngine.IO.raw.versioned.base.dyr import DyrRecord
from VeraGridEngine.Templates.Rms import build_international_standard_template
from VeraGridEngine.Utils.Symbolic.symbolic import Const
from VeraGridEngine.enumerations import InternationalStandardModel


def test_bepsst_catalogue_template_has_the_documented_pss_stages() -> None:
    """Expose two signal ports, terminal supervision and six PSS states."""
    template: RmsModelTemplate = build_international_standard_template(
        InternationalStandardModel.BEPSST, VarFactory(),
    )
    assert template.name == 'BEPSST'
    assert len(template.block.in_vars) == 4
    assert len(template.block.state_vars) == 6
    assert len(template.block.out_vars) == 1


def test_bepsst_binds_all_pss_path_constants_in_source_order() -> None:
    """Map the 16 represented PSS constants while the TEB branch stays disabled."""
    constants: str = '2 0 .1 .1 .2 .3 .1 .2 .1 .2 .1 .2 .1 -.1 0 0 0 .1 .1 0 0'
    record: DyrRecord = parse_dyr("1 'BEPSST' '01' 1 0 3 0 0 " + constants + ' /', version=35).records[0]
    binding: PsseDynamicBinding | None = dynamic_binding('BEPSST')
    assert binding is not None
    template: RmsModelTemplate = build_controller(
        record, binding, VarFactory(), 'BEPSST_SOURCE', 1.0,
    )
    values: dict[str, float] = dict(
        (variable.name, value.value)
        for variable, value in template.block.event_dict.items()
        if isinstance(value, Const)
    )
    assert len(binding.parameters) == 16
    assert values['K1_BEPSST_SOURCE'] == 2.0
    assert values['T3_BEPSST_SOURCE'] == pytest.approx(0.2)
    assert values['T4_BEPSST_SOURCE'] == pytest.approx(0.3)
    assert values['LSMAX_BEPSST_SOURCE'] == pytest.approx(0.1)
    assert values['VCL_BEPSST_SOURCE'] == 0.0


def test_bepsst_rejects_unrepresented_trip_boost_input() -> None:
    """Prevent ITS-triggered excitation boosting from silently disappearing."""
    constants: str = '2 0 .1 .1 .2 .3 .1 .2 .1 .2 .1 .2 .1 -.1 0 0 0 .1 .1 0 0'
    record: DyrRecord = parse_dyr(
        "1 'BEPSST' '01' 1 0 3 0 1 " + constants + ' /', version=35,
    ).records[0]
    with pytest.raises(ValueError, match='ITS must be zero'):
        validate_dynamic_parameters(record)
