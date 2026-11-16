# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Release-specific REGCA1 source record layout checks."""

from VeraGridEngine.IO.raw.dyr_parser import parse_dyr
from VeraGridEngine.IO.raw.versioned.base.auxiliary import RecordStatus
from VeraGridEngine.IO.raw.versioned.base.dyr import DyrRecord
from VeraGridEngine.IO.raw.versioned.v33.dyr import RawDyrV33
from VeraGridEngine.IO.raw.versioned.v34.dyr import RawDyrV34


def test_regca1_direct_35_layout_preserves_every_source_field() -> None:
    """Parse the direct 35.2 converter assignment without implying a binding.

    :return: None.
    """
    source: str = "1 'REGCA1' '01' 1 .02 10 .9 .4 1.2 1.3 .8 .4 -1 .02 .7 .5 -.5 .6 /"
    record: DyrRecord = parse_dyr(source, version=35).records[0]
    assert record.status is RecordStatus.VALID
    assert record.icons == (1,)
    assert len(record.parameters) == 14
    assert record.parameters[0].name == 'TG' and record.parameters[0].value == 0.02
    assert record.parameters[13].name == 'ACCEL' and record.parameters[13].value == 0.6
    assert RawDyrV33().get_model_schema('REGCA1') is None
    assert RawDyrV34().get_model_schema('REGCA1') is None


def test_regca1_rejects_truncated_direct_record() -> None:
    """Retain an incomplete direct assignment as an invalid source record.

    :return: None.
    """
    source: str = "1 'REGCA1' '01' 1 .02 10 .9 .4 1.2 1.3 .8 .4 -1 .02 .7 .5 -.5 /"
    record: DyrRecord = parse_dyr(source, version=35).records[0]
    assert record.status is RecordStatus.INVALID
