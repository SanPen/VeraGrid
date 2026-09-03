"""Tests for contextual RMS parameter diagnostics."""

from __future__ import annotations

from typing import Dict

import pytest

from VeraGridEngine.Devices.Branches.dc_line import DcLine
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae import (
    _resolve_rms_constant_parameter_value,
    _resolve_rms_runtime_parameter_expression,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.enumerations import ParamPowerFlowReferenceType


def test_unresolved_constant_parameter_reports_device_block_and_mapping() -> None:
    """Fail a null constant with its complete RMS model context.

    :return: None.
    """
    device: DcLine = DcLine(name="DC link")
    parameter: Var = Var("r_dc")
    owner_block: Block = Block(
        name="R-L equations",
        parameters=dict(((parameter, Const(None)),)),
    )
    root_block: Block = Block(name="DC line", children=list((owner_block,)))
    static_parameter_values: Dict[Var, Const] = dict()

    with pytest.raises(ValueError) as exception_info:
        _resolve_rms_constant_parameter_value(
            device=device,
            root_block=root_block,
            owner_block=owner_block,
            parameter=parameter,
            declared_value=Const(None),
            static_parameter_values=static_parameter_values,
        )

    message: str = str(exception_info.value)
    assert "r_dc" in message
    assert "R-L equations" in message
    assert "DC link" in message
    assert "not targeted by any api_obj_mapping" in message


def test_resolved_static_parameter_accepts_uid_equivalent_mapping() -> None:
    """A cloned mapped variable with the same UID must resolve the constant.

    :return: None.
    """
    device: DcLine = DcLine(name="DC link")
    parameter: Var = Var("r_dc")
    mapped_parameter: Var = Var(
        "r_dc",
        uid=parameter.uid,
        non_mutable_uid=parameter.non_mutable_uid,
    )
    owner_block: Block = Block(
        name="R-L equations",
        parameters=dict(((parameter, Const(None)),)),
    )
    root_block: Block = Block(
        name="DC line",
        children=list((owner_block,)),
        api_obj_mapping=dict(((ParamPowerFlowReferenceType.dc_line_r_pu, parameter),)),
    )
    static_parameter_values: Dict[Var, Const] = dict(((mapped_parameter, Const(0.015)),))

    resolved_value: Const = _resolve_rms_constant_parameter_value(
        device=device,
        root_block=root_block,
        owner_block=owner_block,
        parameter=parameter,
        declared_value=Const(None),
        static_parameter_values=static_parameter_values,
    )

    assert resolved_value.value == pytest.approx(0.015)


def test_unresolved_dynamic_parameter_reports_required_initialization_source() -> None:
    """Require a default or initialization source for an event parameter.

    :return: None.
    """
    device: DcLine = DcLine(name="DC link")
    parameter: Var = Var("l_dc")
    owner_block: Block = Block(
        name="R-L equations",
        event_dict=dict(((parameter, Const(None)),)),
    )

    with pytest.raises(ValueError, match="Unresolved RMS dynamic parameter 'l_dc'"):
        _resolve_rms_runtime_parameter_expression(
            device=device,
            owner_block=owner_block,
            parameter=parameter,
            declared_expression=Const(None),
            is_discrete_parameter=False,
        )


def test_dynamic_parameter_uses_its_explicit_initialization_equation() -> None:
    """Expose a normalized legacy runtime initialization through event_dict.

    :return: None.
    """
    device: DcLine = DcLine(name="DC link")
    parameter: Var = Var("l_dc")
    initialization_expression: Expr | Const = Const(0.05)
    owner_block: Block = Block(
        name="R-L equations",
        event_dict=dict(((parameter, Const(None)),)),
        init_eqs=dict(((parameter, initialization_expression),)),
    )

    # Block construction migrates legacy event-parameter initialization from
    # init_eqs to event_dict, which is the authoritative runtime representation.
    normalized_expression: Expr | Const = owner_block.event_dict[parameter]
    resolved_expression: Expr | Const = _resolve_rms_runtime_parameter_expression(
        device=device,
        owner_block=owner_block,
        parameter=parameter,
        declared_expression=normalized_expression,
        is_discrete_parameter=False,
    )

    assert parameter not in owner_block.init_eqs
    assert isinstance(resolved_expression, Const)
    assert resolved_expression.value == pytest.approx(0.05)
