"""Tests for transparent-container navigation in the Dynamic Editor."""

from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_tab import (
    block_has_direct_computational_content,
    resolve_navigation_content_block,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var


def test_single_child_empty_containers_collapse_to_first_content_block() -> None:
    """Ctrl-click must skip redundant wrappers without changing the root scene."""
    state_variable: Var = Var("x")
    content: Block = Block(
        name="content",
        state_vars=list([state_variable]),
        state_eqs=list([state_variable]),
    )
    inner_wrapper: Block = Block(name="inner_wrapper", children=list([content]))
    outer_wrapper: Block = Block(name="outer_wrapper", children=list([inner_wrapper]))

    resolved: Block = resolve_navigation_content_block(outer_wrapper)

    assert resolved is content
    assert not block_has_direct_computational_content(outer_wrapper)
    assert block_has_direct_computational_content(content)


def test_branching_or_behavioral_container_remains_a_navigation_level() -> None:
    """A branching container or a wrapper with behavior has meaningful content."""
    first_child: Block = Block(name="first_child")
    second_child: Block = Block(name="second_child")
    branching: Block = Block(name="branching", children=list([first_child, second_child]))
    behavior_variable: Var = Var("y")
    behavioral: Block = Block(
        name="behavioral",
        algebraic_vars=list([behavior_variable]),
        algebraic_eqs=list([behavior_variable]),
        children=list([first_child]),
    )

    assert resolve_navigation_content_block(branching) is branching
    assert resolve_navigation_content_block(behavioral) is behavioral
