from __future__ import annotations

import json
from typing import Any

from VeraGrid.Gui.AiAgent.backend.types_and_tools import (
    ApprovalPolicy,
    ToolErrorCode,
    ToolExecutionResult,
    ToolRegistry,
    ToolRisk,
    ToolSpec,
)


class RunPowerFlowTool:
    """Example power-flow tool."""

    __slots__ = ()

    def execute(self, arguments: dict[str, Any]) -> ToolExecutionResult:
        """
        Execute the power-flow tool.

        :param arguments: Tool arguments.
        :returns: Tool result.
        """
        case_id: Any = arguments.get("case_id", None)
        result_obj: dict[str, Any] = dict()

        if isinstance(case_id, str):
            result_obj["case_id"] = case_id
            result_obj["status"] = "converged"
            result_obj["min_voltage_pu"] = 0.95
            result_obj["max_voltage_pu"] = 1.01
            result_obj["max_branch_loading_pct"] = 91.2
            return ToolExecutionResult(
                success=True,
                error_code=ToolErrorCode.NONE,
                error_message="",
                payload_json=json.dumps(result_obj, ensure_ascii=False),
            )
        else:
            return ToolExecutionResult(
                success=False,
                error_code=ToolErrorCode.EXECUTION_ERROR,
                error_message="Invalid or missing case_id.",
                payload_json="{}",
            )


class ListBusesTool:
    """Example bus-listing tool."""

    __slots__ = ()

    def execute(self, arguments: dict[str, Any]) -> ToolExecutionResult:
        """
        Execute the bus-listing tool.

        :param arguments: Tool arguments.
        :returns: Tool result.
        """
        kv_min_obj: Any = arguments.get("kv_min", None)
        items: list[dict[str, Any]] = list()
        result_obj: dict[str, Any] = dict()

        items.append({"id": "Bus1", "kv": 400.0, "vm_pu": 1.01})
        items.append({"id": "Bus2", "kv": 220.0, "vm_pu": 0.97})
        items.append({"id": "Bus3", "kv": 132.0, "vm_pu": 0.95})

        if kv_min_obj is None:
            filtered_items: list[dict[str, Any]] = items
        else:
            if isinstance(kv_min_obj, (int, float)):
                filtered_items = list()
                index: int = 0
                while index < len(items):
                    item: dict[str, Any] = items[index]
                    item_kv: Any = item.get("kv", None)
                    if isinstance(item_kv, (int, float)) and (item_kv >= float(kv_min_obj)):
                        filtered_items.append(item)
                    else:
                        pass
                    index += 1
            else:
                return ToolExecutionResult(
                    success=False,
                    error_code=ToolErrorCode.EXECUTION_ERROR,
                    error_message="Invalid kv_min.",
                    payload_json="{}",
                )

        result_obj["count"] = len(filtered_items)
        result_obj["items"] = filtered_items
        return ToolExecutionResult(
            success=True,
            error_code=ToolErrorCode.NONE,
            error_message="",
            payload_json=json.dumps(result_obj, ensure_ascii=False),
        )


class ApplyParameterPatchTool:
    """Example mutating patch tool."""

    __slots__ = ()

    def execute(self, arguments: dict[str, Any]) -> ToolExecutionResult:
        """
        Execute the patch tool.

        :param arguments: Tool arguments.
        :returns: Tool result.
        """
        element_id: Any = arguments.get("element_id", None)
        patch_obj: Any = arguments.get("patch", None)
        result_obj: dict[str, Any] = dict()

        if isinstance(element_id, str):
            if isinstance(patch_obj, dict):
                result_obj["status"] = "updated"
                result_obj["element_id"] = element_id
                result_obj["applied_patch"] = patch_obj
                return ToolExecutionResult(
                    success=True,
                    error_code=ToolErrorCode.NONE,
                    error_message="",
                    payload_json=json.dumps(result_obj, ensure_ascii=False),
                )
            else:
                return ToolExecutionResult(
                    success=False,
                    error_code=ToolErrorCode.EXECUTION_ERROR,
                    error_message="Invalid patch object.",
                    payload_json="{}",
                )
        else:
            return ToolExecutionResult(
                success=False,
                error_code=ToolErrorCode.EXECUTION_ERROR,
                error_message="Invalid element_id.",
                payload_json="{}",
            )


def build_default_tool_registry() -> ToolRegistry:
    """
    Build a default registry with demo tools.

    :returns: Tool registry.
    """
    approval_policy: ApprovalPolicy = ApprovalPolicy(
        require_mutating=False,
        require_destructive=False,
    )
    registry: ToolRegistry = ToolRegistry(approval_policy=approval_policy)

    run_pf_schema: str = json.dumps(
        {
            "type": "object",
            "properties": {
                "case_id": {"type": "string"},
            },
            "required": ["case_id"],
            "additionalProperties": False,
        }
    )
    list_buses_schema: str = json.dumps(
        {
            "type": "object",
            "properties": {
                "kv_min": {"type": "number"},
            },
            "additionalProperties": False,
        }
    )
    patch_schema: str = json.dumps(
        {
            "type": "object",
            "properties": {
                "element_id": {"type": "string"},
                "patch": {"type": "object"},
            },
            "required": ["element_id", "patch"],
            "additionalProperties": False,
        }
    )

    registry.register(
        ToolSpec(
            name="run_power_flow",
            description="Run a power flow for a selected study case.",
            input_schema_json=run_pf_schema,
            risk=ToolRisk.COMPUTE,
            handler=RunPowerFlowTool(),
        )
    )
    registry.register(
        ToolSpec(
            name="list_buses",
            description="List buses, optionally filtered by minimum nominal voltage.",
            input_schema_json=list_buses_schema,
            risk=ToolRisk.READ_ONLY,
            handler=ListBusesTool(),
        )
    )
    registry.register(
        ToolSpec(
            name="apply_parameter_patch",
            description="Apply a parameter patch to a project element.",
            input_schema_json=patch_schema,
            risk=ToolRisk.MUTATING,
            handler=ApplyParameterPatchTool(),
        )
    )

    return registry
