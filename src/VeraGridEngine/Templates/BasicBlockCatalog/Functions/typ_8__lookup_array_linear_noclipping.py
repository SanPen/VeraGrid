# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone EMT template for the basic catalog block 'Lookup array (linear_noclipping)'.

This module is generated from the shipped VeraGrid catalog artifacts and keeps the
symbolic surface explicit so both humans and tools can inspect it directly.
"""

from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.BasicBlockCatalog.lookup_array_runtime_templates import (
    build_lookup_array_linear_runtime_template,
)


def build_typ_8__lookup_array_linear_noclipping_default_template_name() -> str:
    """
    Return the canonical runtime name for this standalone template.

    :returns: Default template name.
    """
    return 'Lookup array (linear_noclipping)__8'


def build_typ_8__lookup_array_linear_noclipping_template(vf: VarFactory, name: str | None = None) -> EmtModelTemplate:
    """
    Materialize the standalone EMT template.

    :param vf: Variable factory used to allocate the symbolic surface.
    :param name: Optional explicit runtime template name.
    :returns: Materialized EMT template.
    """
    template_name: str

    if name is None:
        template_name = build_typ_8__lookup_array_linear_noclipping_default_template_name()
    else:
        template_name = name

    return build_lookup_array_linear_runtime_template(
        vf=vf,
        x_points=(0.0, 1.0, 2.0),
        y_points=(0.0, 10.0, 20.0),
        clip=False,
        name=template_name,
    )
