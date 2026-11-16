# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Construction checks for the Colib EMT STATCOM template."""

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.converters.statcom_gfl_emt_template import get_statcom_gfl_emt_template


def test_statcom_builds_the_grid_following_converter() -> None:
    """Ensure the STATCOM exposes an EMT dynamic block."""
    template = get_statcom_gfl_emt_template(vf=VarFactory())

    assert len(template.block.children) > 0
