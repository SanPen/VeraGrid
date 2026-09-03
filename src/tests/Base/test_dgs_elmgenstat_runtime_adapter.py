from VeraGridEngine.IO.dgs.dgs_to_blocks import (
    DgsDirectRootBuildResult,
    ElmCompInstanceEntry,
)
from VeraGridEngine.IO.dgs.dynamic_models.dgs_elmgenstat_runtime_adapter import (
    is_dgs_elmgenstat_direct_slot_contract,
)
from VeraGridEngine.Utils.Symbolic.block import Block


def _build_elmgenstat_direct_result(
        slot_inputs: list[str],
) -> DgsDirectRootBuildResult:
    """Build one transient direct ElmGenstat relation for contract tests.

    :param slot_inputs: Exact signals consumed by the equipment slot.
    :return: Direct conversion result with one resolved static generator.
    """
    entry: ElmCompInstanceEntry = ElmCompInstanceEntry(
        slot_id="generator_slot",
        slot_name="Static generator",
        element_id="generator_fid",
        element_name="Generator",
        element_kind="ElmGenstat",
        element_outserv=0,
        type_id=None,
        type_name=None,
        slot_inputs=slot_inputs,
        slot_reference_is_resolved=True,
        element_reference_is_resolved=True,
    )
    return DgsDirectRootBuildResult(
        root_block=Block(),
        child_block_by_slot_id=dict(),
        graphical_tree_by_slot_id=dict(),
        direct_entries=list([entry]),
    )


def test_elmgenstat_slot_contract_accepts_current_reference_pair() -> None:
    """Recognize a complete PowerFactory static-generator slot.

    :return: None.
    """
    direct_result: DgsDirectRootBuildResult = _build_elmgenstat_direct_result(
        slot_inputs=list(["id_ref;iq_ref"]),
    )
    assert is_dgs_elmgenstat_direct_slot_contract(direct_result=direct_result)


def test_elmgenstat_slot_contract_rejects_incomplete_reference_pair() -> None:
    """Reject a static-generator slot without its reactive-current input.

    :return: None.
    """
    direct_result: DgsDirectRootBuildResult = _build_elmgenstat_direct_result(
        slot_inputs=list(["id_ref"]),
    )
    assert not is_dgs_elmgenstat_direct_slot_contract(direct_result=direct_result)
