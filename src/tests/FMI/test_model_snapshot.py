# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Exercise FMU symbolic archives and historical snapshot conversion."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.IO.fmu.model import (
    FmuModelSnapshot, build_model_snapshot, load_snapshot, reconstruct_block, save_snapshot,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, SharedVarReferenceType, Var
from VeraGridEngine.Utils.procedural_logic import HardSaturationLogic
from VeraGridEngine.enumerations import VarPowerFlowReferenceType


def _snapshot_model() -> Block:
    """Construct a nested model covering identity and declarative persistence.

    :return: Root with derivatives, shared references, logic and unused variables.
    """
    state: Var = Var("x", reference=VarPowerFlowReferenceType.Vm,
                     shared_reference=SharedVarReferenceType("frame"))
    derivative: Var = Var("dx", base_var=state)
    second_derivative: Var = Var("ddx", base_var=derivative)
    output: Var = Var("y")
    unused: Var = Var("unused")
    mode: Var = Var("mode")
    child: Block = Block(
        name="plant", state_vars=list((state,)), state_eqs=list((-state,)),
        algebraic_vars=list((output, unused)), algebraic_eqs=list((output - state, unused)),
        diff_vars=list((derivative, second_derivative)),
        differential_eqs=list((derivative - state, second_derivative - derivative)),
        in_vars=list((state,)), out_vars=list((output,)),
        init_eqs=dict(((state, Const(1.0)),)),
        parameters=dict(((mode, Const(0.0)),)), event_dict=dict(((mode, Const(0.0)),)),
        external_mapping=dict(((VarPowerFlowReferenceType.Vm, state),)),
        procedural_logic=list((HardSaturationLogic("mode", state, Const(-1.0), Const(1.0), name="limit"),)),
    )
    return Block(name="snapshot", children=list((child,)))


@pytest.mark.parametrize("version", (1, 2))
def test_snapshot_json_roundtrip(version: int, tmp_path: Path) -> None:
    """Restore both formats through the same symbolic parser after JSON storage.

    :param version: Historical or current schema to exercise.
    :param tmp_path: Owned snapshot location.
    :return: None.
    """
    model: Block = _snapshot_model()
    snapshot: FmuModelSnapshot = build_model_snapshot(model)
    if version == 1:
        snapshot["schema_version"] = 1
        snapshot["block"] = model.to_dict()
    else:
        assert snapshot["schema_version"] == 2
        assert snapshot["block"]["references"]
    save_snapshot(snapshot, tmp_path / "model.json")
    restored: Block = reconstruct_block(load_snapshot(tmp_path / "model.json"))
    source: Block = model.children[0]
    child: Block = restored.children[0]
    assert restored.uid == model.uid
    assert child.uid == source.uid
    assert child.state_vars[0].non_mutable_uid == source.state_vars[0].non_mutable_uid
    assert child.state_vars[0] is child.in_vars[0]
    assert child.external_mapping[VarPowerFlowReferenceType.Vm] is child.state_vars[0]
    assert child.state_vars[0].shared_ref.name == "frame"
    assert child.state_vars[0].ref == VarPowerFlowReferenceType.Vm
    assert child.diff_vars[0].base_var is child.state_vars[0]
    assert child.diff_vars[1].base_var is child.diff_vars[0]
    assert child.algebraic_vars[1].name == "unused"
    assert child.procedural_logic[0].to_data() == source.procedural_logic[0].to_data()
    assert child.init_eqs[child.state_vars[0]].eval() == 1.0


@pytest.mark.parametrize("version", (1, 2))
def test_snapshot_preserves_aliases_without_mutating_source(version: int) -> None:
    """Retain internal alias edges independently of the live factory.

    :param version: Snapshot representation of the connected model.
    :return: None.
    """
    factory: VarFactory = VarFactory()
    source: Var = factory.add_var("source")
    target: Var = factory.add_var("target")
    factory.register_symbolic_connection(source_var=source, target_var=target)
    model: Block = Block(in_vars=list((source,)), out_vars=list((target,)))
    before: dict[str, Any] = deepcopy(model.to_dict())
    snapshot: FmuModelSnapshot = build_model_snapshot(model)
    assert model.to_dict() == before
    assert snapshot["block"]["connections"]
    if version == 1:
        snapshot["schema_version"] = 1
        snapshot["block"] = before
    else:
        pass
    restored: Block = reconstruct_block(snapshot)
    assert restored.in_vars[0].uid == restored.out_vars[0].uid
    assert restored.in_vars[0].non_mutable_uid == source.non_mutable_uid
    assert restored.out_vars[0].non_mutable_uid == target.non_mutable_uid


def test_snapshot_requires_one_structural_root() -> None:
    """Reject snapshot block tables containing zero or multiple structural roots.

    :return: None.
    """
    model: Block = _snapshot_model()
    snapshot: FmuModelSnapshot = build_model_snapshot(model)
    snapshot["block"]["blocks"] = dict()
    with pytest.raises(ValueError, match="exactly one root"):
        reconstruct_block(snapshot)

    snapshot = build_model_snapshot(model)
    snapshot["block"]["blocks"][model.uid]["children"] = list()
    with pytest.raises(ValueError, match="exactly one root"):
        reconstruct_block(snapshot)


def test_snapshot_rejects_missing_child_and_future_version() -> None:
    """Prevent partial reconstruction and accidental future-format decoding.

    :return: None.
    """
    model: Block = _snapshot_model()
    snapshot: FmuModelSnapshot = build_model_snapshot(model)
    snapshot["schema_version"] = 100
    with pytest.raises(ValueError, match="Unsupported"):
        reconstruct_block(snapshot)
    snapshot["schema_version"] = 2
    root_uid: int = model.uid
    child_uid: int = snapshot["block"]["blocks"][root_uid]["children"][0]
    del snapshot["block"]["blocks"][child_uid]
    with pytest.raises(ValueError, match="Incomplete"):
        reconstruct_block(snapshot)


def test_direct_legacy_block_payload() -> None:
    """Accept historical callers supplying a direct block dictionary.

    :return: None.
    """
    model: Block = _snapshot_model()
    restored: Block = reconstruct_block(cast(FmuModelSnapshot, model.to_dict()))
    assert restored.uid == model.uid
    assert len(restored.children[0].diff_vars) == 2
