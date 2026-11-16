# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Shared test fixtures for round trips through the symbolic archive parser."""

import copy
from typing import Any

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic_io import BlockParser, BlockSaver
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.Utils.procedural_logic import ProceduralLogicCodec


def save_block_fixture(block: Block) -> tuple[dict[int, dict[str, Any]], BlockSaver]:
    """Save an editable flat block table alongside its symbolic dependencies.

    :param block: Source model used by a persistence or migration test.
    :return: Independent block table and the saver containing its dependencies.
    """
    factory: VarFactory = VarFactory()
    owner: Block
    variables: list[Var]
    variable: Var
    # Tests often construct the template with a temporary factory. Rebuild its
    # complete registry, including declared startup variables absent from every
    # equation, before handing the model to the archive writer.
    for owner in block.get_all_blocks():
        for variables in (owner.state_vars, owner.algebraic_vars, owner.in_vars,
                          owner.out_vars, owner.reformulated_vars):
            for variable in variables:
                factory.get_vars_dict()[variable.non_mutable_uid] = variable
        for variable in owner.diff_vars:
            factory.get_diff_var_dict()[variable.non_mutable_uid] = variable
    saver: BlockSaver = BlockSaver(factory)
    saver.save_block(block)
    records: dict[int, dict[str, Any]] = copy.deepcopy(saver.get_blocks())
    return records, saver


def parse_saved_blocks(parser: BlockParser,
                       saver: BlockSaver,
                       data: dict[int | str, dict[str, Any]]) -> list[Block]:
    """Restore saved block records through the complete production parser entry point.

    :param parser: Parser configured with the factory, logger and codec required by the test.
    :param saver: Saver containing every symbolic dependency of the block records.
    :param data: Flat block table, optionally edited to represent a historical format.
    :return: Root blocks reconstructed by :meth:`BlockParser.parse`.
    """
    # Recreate the complete symbolic section written by VeraGrid so tests cannot
    # bypass references, connections or the parser dependency order.
    symbolic_data: dict[str, Any] = dict(
        shared_references=saver.get_shared_references_to_save(),
        consts=saver.get_const_to_save(),
        vars=saver.get_vars_to_save(),
        diff_vars=saver.get_diff_vars_to_save(),
        connections=saver.get_connections_to_save(),
        blocks=data,
    )
    return parser.parse(data=symbolic_data)


def parse_saved_block(data: dict[int, dict[str, Any]], saver: BlockSaver,
                      procedural_logic_codec: ProceduralLogicCodec | None = None) -> Block:
    """Restore one root from the flat tables produced by the archive saver.

    :param data: Flat block table, optionally edited to represent a historical format.
    :param saver: Variable, constant and connection tables for the root.
    :param procedural_logic_codec: Explicit decoder when the model declares logic.
    :return: The single root returned by BlockParser.parse().
    """
    parser: BlockParser = BlockParser(VarFactory(), procedural_logic_codec=procedural_logic_codec)
    roots: list[Block] = parse_saved_blocks(parser=parser, saver=saver, data=data)
    assert len(roots) == 1
    return roots[0]


def roundtrip_block(block: Block,
                    procedural_logic_codec: ProceduralLogicCodec | None = None) -> Block:
    """Save and reconstruct a test model without the removed Block.parse API.

    :param block: Source block tree with live symbolic variables.
    :param procedural_logic_codec: Explicit decoder for declared procedural logic.
    :return: Restored root with its variables and symbolic dependencies.
    """
    data: dict[int, dict[str, Any]]
    saver: BlockSaver
    data, saver = save_block_fixture(block)
    return parse_saved_block(data, saver, procedural_logic_codec)
