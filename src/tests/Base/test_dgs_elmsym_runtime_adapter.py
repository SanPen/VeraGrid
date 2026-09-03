from VeraGridEngine.IO.dgs.dgs_to_blocks import (
    DgsDirectRootBuildResult,
    ElmCompInstanceEntry,
)
from VeraGridEngine.IO.dgs.dynamic_models.dgs_elmsym_runtime_adapter import (
    is_dgs_elmsym_direct_slot_contract,
)
from VeraGridEngine.Utils.Symbolic.block import Block


def _build_elmsym_direct_result(slot_inputs: list[str]) -> DgsDirectRootBuildResult:
    """Build one transient direct ElmSym relation for contract tests.

    :param slot_inputs: Exact signals consumed by the equipment slot.
    :return: Direct conversion result containing one resolved ElmSym relation.
    """
    root_block: Block = Block()
    entry: ElmCompInstanceEntry = ElmCompInstanceEntry(
        slot_id="machine_slot",
        slot_name="Synchronous machine",
        element_id="machine_fid",
        element_name="Machine",
        element_kind="ElmSym",
        element_outserv=0,
        type_id=None,
        type_name=None,
        slot_filter="ElmSym*",
        slot_outputs=list([
            "ID;IQ;IFDIEEE;RPOWER;SG;VT;VTD;VTQ;cosn;speed",
        ]),
        slot_inputs=slot_inputs,
        slot_reference_is_resolved=True,
        element_reference_is_resolved=True,
    )
    return DgsDirectRootBuildResult(
        root_block=root_block,
        child_block_by_slot_id=dict(),
        graphical_tree_by_slot_id=dict(),
        direct_entries=list([entry]),
    )


def test_elmsym_slot_contract_accepts_complete_direct_interface() -> None:
    """Recognize a complete PowerFactory synchronous-machine slot.

    :return: None.
    """
    direct_result: DgsDirectRootBuildResult = _build_elmsym_direct_result(
        slot_inputs=list(["pt;ve"]),
    )
    assert is_dgs_elmsym_direct_slot_contract(direct_result=direct_result)


def test_elmsym_slot_contract_rejects_incomplete_direct_interface() -> None:
    """Reject a synchronous-machine slot without its excitation input.

    :return: None.
    """
    direct_result: DgsDirectRootBuildResult = _build_elmsym_direct_result(
        slot_inputs=list(["pt"]),
    )
    assert not is_dgs_elmsym_direct_slot_contract(direct_result=direct_result)
