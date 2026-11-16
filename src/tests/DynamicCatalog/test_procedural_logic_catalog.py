# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Contract tests for native standalone procedural-logic templates."""

from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.template_catalogue import (
    ProceduralBlockTemplateDescriptor,
    build_procedural_block_catalog_template,
)
from VeraGrid.Gui.DynamicModelEditor.Editor.DynamicLibrary.dynamic_editor_library import (
    get_dynamic_library_procedural_descriptors,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var


def _collect_block_variables(block: Block) -> list[Var]:
    """Collect the symbolic surface allocated directly by one catalogue block.

    :param block: Materialized standalone procedural block.
    :return: Ordered variables from ports, equations and runtime dictionaries.
    """
    variables: list[Var] = list()
    variables.extend(block.in_vars)
    variables.extend(block.out_vars)
    variables.extend(block.algebraic_vars)
    variables.extend(list(block.event_dict.keys()))
    variables.extend(list(block.mode_dict.keys()))
    return variables


def test_procedural_catalog_allocates_fresh_symbolic_identities() -> None:
    """Repeated materialization must never share mutable symbolic variables.

    :return: None.
    """
    var_factory: VarFactory = VarFactory()
    descriptor: ProceduralBlockTemplateDescriptor = list(
        get_dynamic_library_procedural_descriptors()
    )[0]
    first_template: EmtModelTemplate = build_procedural_block_catalog_template(
        descriptor=descriptor,
        var_factory=var_factory,
    )
    second_template: EmtModelTemplate = build_procedural_block_catalog_template(
        descriptor=descriptor,
        var_factory=var_factory,
    )
    first_uids: set[int] = set(
        variable.non_mutable_uid for variable in _collect_block_variables(first_template.block)
    )
    second_uids: set[int] = set(
        variable.non_mutable_uid for variable in _collect_block_variables(second_template.block)
    )

    assert first_uids.isdisjoint(second_uids)
