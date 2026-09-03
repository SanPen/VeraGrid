from VeraGridEngine.IO.dgs.dynamic_models.dgs_elmvsc_runtime_adapter import (
    is_dgs_elmvsc_slot_contract,
    is_dgs_elmvscmono_slot_contract,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var


def test_elmvsc_slot_contract_accepts_complete_converter_boundary() -> None:
    """Recognize a complete PowerFactory MMC converter slot."""

    block: Block = Block(
        in_vars=[Var(name="Pmr"), Var(name="Pmi"), Var(name="mdc")],
        out_vars=[Var(name="idc"), Var(name="Ucap")],
    )

    assert is_dgs_elmvsc_slot_contract(block=block)


def test_elmvsc_slot_contract_rejects_incomplete_converter_boundary() -> None:
    """Reject an MMC converter slot without its DC modulation input."""

    block: Block = Block(
        in_vars=[Var(name="Pmr"), Var(name="Pmi")],
        out_vars=[Var(name="idc"), Var(name="Ucap")],
    )

    assert not is_dgs_elmvsc_slot_contract(block=block)


def test_elmvsc_slot_contract_does_not_search_unrelated_children() -> None:
    """Require the isolated equipment boundary instead of recursive names.

    :return: None.
    """
    unrelated_child: Block = Block(
        in_vars=[Var(name="Pmr"), Var(name="Pmi"), Var(name="mdc")],
        out_vars=[Var(name="idc"), Var(name="Ucap")],
    )
    composite_root: Block = Block(children=[unrelated_child])

    assert not is_dgs_elmvsc_slot_contract(block=composite_root)


def test_elmvscmono_slot_contract_accepts_complete_bridge_boundary() -> None:
    """Recognize a complete PowerFactory monopolar converter slot."""

    block: Block = Block(
        in_vars=[
            Var(name="Pmd"),
            Var(name="Pmq"),
            Var(name="cosref"),
            Var(name="sinref"),
        ],
        out_vars=[Var(name="id"), Var(name="iq"), Var(name="uDC")],
    )

    assert is_dgs_elmvscmono_slot_contract(block=block)


def test_elmvscmono_slot_contract_rejects_incomplete_bridge_boundary() -> None:
    """Reject a monopolar converter slot without its sine reference."""

    block: Block = Block(
        in_vars=[Var(name="Pmd"), Var(name="Pmq"), Var(name="cosref")],
        out_vars=[Var(name="id"), Var(name="iq"), Var(name="uDC")],
    )

    assert not is_dgs_elmvscmono_slot_contract(block=block)
