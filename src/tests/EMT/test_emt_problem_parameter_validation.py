"""Tests for contextual EMT parameter diagnostics."""

from __future__ import annotations

from typing import Dict

import pytest

from VeraGridEngine.Devices.Branches.dc_line import DcLine
from VeraGridEngine.Simulations.EMT.problems.emt_problem_dae import (
    EmtProblemDae,
    _resolve_emt_constant_parameter_value,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
from VeraGridEngine.enumerations import ParamPowerFlowReferenceType


def test_unresolved_emt_constant_reports_device_block_and_mapping() -> None:
    """Report the complete model ownership of a null EMT constant.

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
        _resolve_emt_constant_parameter_value(
            device=device,
            root_block=root_block,
            owner_block=owner_block,
            parameter=parameter,
            declared_value=Const(None),
            static_parameter_values=static_parameter_values,
        )

    message: str = str(exception_info.value)
    assert "Unresolved EMT constant parameter" in message
    assert "r_dc" in message
    assert "R-L equations" in message
    assert "DC link" in message
    assert "not targeted by any api_obj_mapping" in message


def test_emt_constant_accepts_a_uid_equivalent_static_mapping() -> None:
    """Resolve an EMT constant from a cloned variable with the same UID.

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
    static_parameter_values: Dict[Var, Const] = dict(((mapped_parameter, Const(0.02)),))

    resolved_value: Const = _resolve_emt_constant_parameter_value(
        device=device,
        root_block=root_block,
        owner_block=owner_block,
        parameter=parameter,
        declared_value=Const(None),
        static_parameter_values=static_parameter_values,
    )

    assert resolved_value.value == pytest.approx(0.02)


def test_unresolved_emt_runtime_parameter_reports_required_source() -> None:
    """A runtime placeholder without PF or explicit initialization must fail.

    :return: None.
    """
    device: DcLine = DcLine(name="DC link")
    parameter: Var = Var("l_dc")
    owner_block: Block = Block(
        name="R-L equations",
        event_dict=dict(((parameter, Const(None)),)),
    )

    problem: EmtProblemDae = EmtProblemDae.__new__(EmtProblemDae)
    problem._variable_parameters = list((parameter,))
    problem._event_parameters_eqs = list((Const(None),))
    problem._init_eqs_flat = dict()
    problem._runtime_parameter_owner_blocks = dict(((parameter.uid, owner_block),))
    problem._runtime_parameter_devices = dict(((parameter.uid, device),))
    problem._temp_init_guess = dict()
    problem._temp_post_init_guess = dict()
    problem.event_params_init_dict = dict()
    problem._runtime_mode_uids = set()

    with pytest.raises(ValueError, match="Unresolved EMT dynamic parameter 'l_dc'"):
        problem._validate_runtime_parameter_sources_after_power_flow()


def test_emt_runtime_parameter_accepts_power_flow_seed() -> None:
    """A PF-owned EMT placeholder is valid after its seed was recorded.

    :return: None.
    """
    device: DcLine = DcLine(name="DC link")
    parameter: Var = Var("i_dc_0")
    owner_block: Block = Block(
        name="R-L equations",
        event_dict=dict(((parameter, Const(None)),)),
    )

    problem: EmtProblemDae = EmtProblemDae.__new__(EmtProblemDae)
    problem._variable_parameters = list((parameter,))
    problem._event_parameters_eqs = list((Const(None),))
    problem._init_eqs_flat = dict()
    problem._runtime_parameter_owner_blocks = dict(((parameter.uid, owner_block),))
    problem._runtime_parameter_devices = dict(((parameter.uid, device),))
    problem._temp_init_guess = dict(((parameter.uid, 0.0),))
    problem._temp_post_init_guess = dict()
    problem.event_params_init_dict = dict()
    problem._runtime_mode_uids = set()

    problem._validate_runtime_parameter_sources_after_power_flow()
