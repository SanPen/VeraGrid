# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
from typing import Dict, Tuple

from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.equation_decomposer import EquationDecomposer
from VeraGridEngine.Devices.Dynamic import VarFactory
from VeraGridEngine.Devices.Diagrams.block_diagram import BlockDiagram
from VeraGridEngine.enumerations import BlockType


def prepare_block_for_editing(
        block: Block,
        var_factory: VarFactory,
) -> Tuple[Block, Dict[int, BlockType]]:
    """
    Prepare a block for display in the editor **without cloning it**.

    This function assumes *block* already lives inside the working tree
    (owned by :class:`DynamicEditorDocument`).  It only performs
    in-place decomposition when needed.

    The returned block is always the same object that was passed in.

    :param block: The working-tree block to prepare.
    :param var_factory: The ``VarFactory`` used during decomposition.
    :return: The same *block* reference after in-place preparation.
    """
    block2blocktype = dict()
    if not block.children and not block.empty() and block.is_eq_decomposable():
        block2blocktype= decompose_block_in_place(block, var_factory)
    return block, block2blocktype


def decompose_block_in_place(block: Block, var_factory: VarFactory) -> Dict[int, BlockType]:
    """
    Decompose the equations of *block* in place and generate its diagram.

    This is a Qt-free helper that performs the same work that was previously
    done inside :meth:`DynamicBlockEditorGUI.decompose_block_in_place`.

    :param block: Block whose equations will be decomposed.
    :param var_factory: ``VarFactory`` instance required by the decomposer.
    :return: None.
    """
    decomposer = EquationDecomposer(var_factory)
    decomposed, block2blocktype = decomposer.decompose(block)
    preserved_uid = block.uid
    block.name = decomposed.name
    block.is_decomposable = decomposed.is_decomposable
    block.vars_glob_name2uid = decomposed.vars_glob_name2uid
    block.state_vars = decomposed.state_vars
    block.state_eqs = decomposed.state_eqs
    block.algebraic_vars = decomposed.algebraic_vars
    block.algebraic_eqs = decomposed.algebraic_eqs
    block.diff_vars = decomposed.diff_vars
    block.reformulated_vars = decomposed.reformulated_vars
    block.differential_eqs = decomposed.differential_eqs
    block.init_eqs = decomposed.init_eqs
    block.diff_init_eqs = decomposed.diff_init_eqs
    block.children = decomposed.children
    block.in_vars = decomposed.in_vars
    block.out_vars = decomposed.out_vars
    block.parameters = decomposed.parameters
    block.discrete_eqs = decomposed.discrete_eqs
    block.external_mapping = decomposed.external_mapping
    block.api_obj_mapping = decomposed.api_obj_mapping
    block.init_values = decomposed.init_values
    block.var_mapping = decomposed.var_mapping
    block.event_dict = decomposed.event_dict
    block.mode_dict = decomposed.mode_dict
    block.uid = preserved_uid
    block.diagram = BlockDiagram()

    return block2blocktype
