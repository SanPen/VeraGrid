# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Translate historical FMU payloads to canonical symbolic tables."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from VeraGridEngine.enumerations import VarPowerFlowReferenceType


class LegacySnapshotTables:
    """Collect declarative identities without constructing symbolic objects."""

    __slots__ = ("constants", "variables", "derivatives", "references", "blocks")

    def __init__(self) -> None:
        """Allocate the tables consumed exclusively by BlockParser.

        :return: None.
        """
        self.constants: dict[int, dict[str, Any]] = dict()
        self.variables: dict[int, dict[str, Any]] = dict()
        self.derivatives: dict[int, dict[str, Any]] = dict()
        self.references: dict[int, dict[str, Any]] = dict()
        self.blocks: dict[int, dict[str, Any]] = dict()

    def convert_expression(self, data: Any) -> Any:
        """Extract atomic definitions and retain the serialized expression tree.

        :param data: Historical expression or nested declarative value.
        :return: Equivalent data using canonical stable-identity references.
        """
        if isinstance(data, list):
            return list(self.convert_expression(item) for item in data)
        elif isinstance(data, dict):
            tpe: Any = data.get("type", None)
            if tpe == "Const":
                constant_uid: int = int(data["uid"])
                self.constants[constant_uid] = deepcopy(data)
                return dict(type="Const", uid=constant_uid)
            elif tpe == "Var":
                variable_uid: int = int(data.get("non_mutable_uid", data["uid"]))
                base_data: Any = data.get("base_var", None)
                base_uid: int | None = None
                if isinstance(base_data, dict):
                    base_uid = self.convert_expression(base_data)["uid"]
                else:
                    pass
                reference_name: Any = data.get("reference", None)
                reference: VarPowerFlowReferenceType | None = None
                if reference_name is not None:
                    reference = VarPowerFlowReferenceType[reference_name]
                else:
                    pass
                shared: Any = data.get("shared_reference", None)
                if isinstance(shared, dict):
                    self.references[int(shared["uid"])] = dict(
                        type="share_reference", name=shared["name"], uid=int(shared["uid"]))
                else:
                    pass
                record: dict[str, Any] = dict(
                    type="Var" if base_uid is None else "DiffVar", name=data["name"],
                    uid=int(data["uid"]), non_mutable_uid=variable_uid,
                    base_var=base_uid, shared_ref=deepcopy(shared),
                    ref=None if reference is None else reference.value,
                )
                if base_uid is None:
                    self.variables[variable_uid] = record
                else:
                    self.derivatives[variable_uid] = record
                return dict(type=record["type"], uid=variable_uid)
            else:
                return dict((key, self.convert_expression(value)) for key, value in data.items())
        else:
            return data

    def convert_block(self, data: dict[str, Any]) -> int:
        """Translate block field shapes while leaving decoding to BlockParser.

        :param data: One historical self-contained block and its children.
        :return: Stable root UID registered in the block table.
        """
        uid: int = int(data["uid"])
        if uid in self.blocks:
            raise ValueError(f"Duplicate block UID in legacy FMU snapshot: {uid}")
        else:
            pass
        record: dict[str, Any] = dict()
        self.blocks[uid] = record
        field: str
        value: Any
        for field, value in data.items():
            if field == "children":
                record[field] = list(self.convert_block(child) for child in value)
            elif field in ("state_vars", "algebraic_vars", "diff_vars", "reformulated_vars", "in_vars", "out_vars"):
                record[field] = list(self.convert_expression(item)["uid"] for item in value)
            elif field in ("init_eqs", "diff_init_eqs", "post_init_seed_eqs", "event_dict", "mode_dict",
                           "boolean_guards", "discrete_eqs", "parameters", "init_values"):
                record[field] = list(dict(var=self.convert_expression(item["key"])["uid"],
                                          expr=self.convert_expression(item["value"])) for item in value.values())
            elif field in ("external_mapping", "api_obj_mapping"):
                record[field] = dict((key, None if item is None else self.convert_expression(item)["uid"])
                                     for key, item in value.items())
            elif field in ("procedural_logic", "diagram", "connection_intents"):
                # The codec owns its self-contained expression representation.
                # Collect dependencies, but never rewrite the codec's payload.
                if field == "procedural_logic":
                    self.convert_expression(value)
                else:
                    pass
                record[field] = deepcopy(value)
            else:
                record[field] = self.convert_expression(value)
        record["vars_glob_name2uid"] = dict()
        return uid


def convert_legacy_snapshot(block_payload: dict[str, Any]) -> dict[str, Any]:
    """Adapt version-one data to the single supported reconstruction route.

    :param block_payload: Historical Block.to_dict representation.
    :return: Canonical symbolic tables; no runtime blocks have been created.
    """
    tables: LegacySnapshotTables = LegacySnapshotTables()
    tables.convert_block(block_payload)
    return dict(references=list(tables.references.values()), constants=list(tables.constants.values()),
                variables=list(tables.variables.values()), differential_variables=list(tables.derivatives.values()),
                connections=dict(), blocks=tables.blocks)
