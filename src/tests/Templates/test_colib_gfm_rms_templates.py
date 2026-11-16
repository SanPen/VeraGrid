# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Tests for the named Colib RMS grid-forming converter entries."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.renewable_controls.colib_gfm_rms_templates import (
    get_epri_gfm_rms_template,
    get_upc_gfm_rms_template,
)


def test_epri_gfm_template_builds_a_converter_block() -> None:
    """The EPRI entry point must expose the reusable RMS GFM block.

    :return: ``None``.
    """
    variable_factory: VarFactory = VarFactory()

    # Building verifies that the named Colib entry uses the existing GFM model.
    template: RmsModelTemplate = get_epri_gfm_rms_template(vf=variable_factory)

    assert len(template.block.algebraic_eqs) > 0


def test_upc_gfm_template_builds_a_converter_block() -> None:
    """The UPC entry point must expose the reusable RMS GFM block.

    :return: ``None``.
    """
    variable_factory: VarFactory = VarFactory()

    # Building verifies that the named Colib entry uses the existing GFM model.
    template: RmsModelTemplate = get_upc_gfm_rms_template(vf=variable_factory)

    assert len(template.block.algebraic_eqs) > 0
