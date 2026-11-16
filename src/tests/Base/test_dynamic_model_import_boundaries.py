# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import json

from VeraGridEngine.IO.dgs.dynamic_models.dynamic_model_import import _build_user_dynamic_template_payload_text
from VeraGridEngine.IO.dgs.dynamic_models.dgs_dynamic_association import (
    DgsDynamicAssociation,
)
from VeraGridEngine.IO.dynamic_model_import_types import (
    DynamicModelImportEntryStatus,
    DynamicModelImportSource,
)
from VeraGridEngine.IO.modelica.dynamic_model_import import _collect_vars_from_modelica_expr
from VeraGridEngine.IO.modelica.modelica_parser import ExternalFunc, LogicExpr
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Func, Func2, Var
from VeraGridEngine.enumerations import (
    DeviceType,
    DgsDynamicAssociationRole,
    DynamicSimulationMode,
)

def test_dynamic_model_import_source_contract_is_format_neutral() -> None:
    """Expose source-format identifiers without importing through a parser."""

    assert [source.value for source in DynamicModelImportSource] == [
        "Modelica XML",
        "PowerFactory DGS",
    ]


def test_dynamic_dgs_association_uses_neutral_import_contract_enums() -> None:
    """Expose the neutral import-contract values on a new association."""

    association = DgsDynamicAssociation()

    assert association.device_type is DeviceType.DynamicModelHostDevice
    assert association.target_domain is DynamicSimulationMode.RMS
    assert association.status is DynamicModelImportEntryStatus.Skipped


def test_modelica_expression_variable_collection_visits_each_node_type() -> None:
    """Collect variables through nested arithmetic, functions and logic."""

    first_var: Var = Var("first_var")
    second_var: Var = Var("second_var")
    third_var: Var = Var("third_var")
    fourth_var: Var = Var("fourth_var")
    expression: LogicExpr = LogicExpr(
        op="and",
        args=(
            first_var + second_var,
            ExternalFunc(
                name="external_modelica_function",
                args=(
                    Func(arg=-third_var, op="sin"),
                    Func2(name="max", arg1=fourth_var, arg2=first_var),
                ),
            ),
        ),
    )
    vars_found: dict[int, Var] = dict()

    _collect_vars_from_modelica_expr(
        expression=expression,
        vars_found=vars_found,
    )

    assert set(vars_found) == {
        first_var.uid,
        second_var.uid,
        third_var.uid,
        fourth_var.uid,
    }


def test_dynamic_model_metadata_remains_declarative_json_data() -> None:
    """Keep persisted dynamic-model metadata as declarative JSON data."""

    source_block: Block = Block(name="Data-only dynamic model")
    payload_text: str = _build_user_dynamic_template_payload_text(
        block=source_block,
        template_name="Data-only dynamic model",
        target_domain=DynamicSimulationMode.RMS,
        device_tpe=DeviceType.GeneratorDevice,
    )
    payload_obj: object = json.loads(payload_text)

    assert isinstance(payload_obj, dict)
    assert payload_obj.get("template_name", None) == "Data-only dynamic model"
    assert payload_obj.get("target_domain", None) == DynamicSimulationMode.RMS.value
    assert payload_obj.get("device_tpe", None) == DeviceType.GeneratorDevice.name
    assert isinstance(payload_obj.get("block_data", None), dict)
