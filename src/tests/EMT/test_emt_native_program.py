# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Native EMT program: compiler, families, validation, artifact and parity with VeraGrid."""

from __future__ import annotations

import hashlib
import json
import math
import os
from typing import BinaryIO, Dict, List, Set, Tuple

import numpy as np
import numpy.typing as npt
import pytest

from tests.EMT.emt_native_program_reference import ProgramPoint, differential_value, evaluate_program_jacobian, evaluate_program_residual
from tests.EMT.test_kundur_emt_initialization import _build_kundur_problem
from VeraGridEngine.enumerations import DynamicIntegrationMethod, EmtNativeOpcode
from VeraGridEngine.IO.emt_native_program_io import read_emt_native_program, write_emt_native_program
from VeraGridEngine.Simulations.EMT.problems.emt_native_program import EmtNativeProgram, compile_emt_native_program
from VeraGridEngine.Simulations.EMT.problems.emt_problem_dae import EmtProblemDae
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Simulations.EMT.solvers.structural_compiled_solver import StructuralCompiledSolver, StructuralCompiledWarmupPolicy
from VeraGridEngine.Utils.canonical_json import canonical_json_bytes
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import BinOp, Const, Expr, Func, Func2, UnOp, Var, cos, exp, heaviside, log, sin, sqrt
from VeraGridEngine.Utils.Symbolic.symbolic import abs as symbolic_abs


@pytest.fixture(scope="module")
def kundur_problem() -> EmtProblemDae:
    """
    Build the self-contained Kundur EMT problem once for this module.

    :return: Kundur EMT problem.
    """
    return _build_kundur_problem()[0]


@pytest.fixture(scope="module")
def kundur_program(kundur_problem: EmtProblemDae) -> EmtNativeProgram:
    """
    Compile the Kundur problem once for this module.

    :param kundur_problem: Kundur EMT problem.
    :return: Native program bound to the identity "kundur".
    """
    return compile_emt_native_program(kundur_problem, "kundur")


def _synthetic_problem(extra_rows: List[Tuple[Var, Expr]], states: Tuple[Var, Var] | None = None) -> EmtProblemTemplate:
    """
    Build a small EMT problem covering every opcode, plus optional extra algebraic rows.

    :param extra_rows: (algebraic variable, equation) pairs appended to the block.
    :param states: The two state variables when extra rows reference them; fresh ones otherwise.
    :return: Problem with initial guesses set for every unknown.
    """
    if states is None:
        x1: Var = Var("x1")
        x2: Var = Var("x2")
    else:
        x1 = states[0]
        x2 = states[1]
    y1: Var = Var("y1")
    y2: Var = Var("y2")
    y3: Var = Var("y3")
    y4: Var = Var("y4")
    y5: Var = Var("y5")
    y6: Var = Var("y6")
    y7: Var = Var("y7")
    y8: Var = Var("y8")
    y9: Var = Var("y9")
    p: Var = Var("p")
    algebraic_vars: List[Var] = list((y1, y2, y3, y4, y5, y6, y7, y8, y9))
    algebraic_eqs: List[Expr] = list((
        y1 - (x1 + Const(2.0) * x2),
        y2 - cos(x1) + exp(Const(0.1) * x2) / (Const(1.0) + y1 ** Const(2.0)),
        y3 - log(x1 * x1 + Const(1.0)) - sqrt(y1 * y1 + Const(2.0)),
        y4 - symbolic_abs(x2 - Const(0.3)) * heaviside(x1 - Const(0.1)),
        y5 - (x1 + Const(1.5)) ** (Const(0.5) + Const(0.0) * x2),
        y6 + (-y1) - p * x1,
        y7 - x1 ** Const(0.0) - x2 ** Const(3.0),
        y8 - Const(3.0) * x1,
        y9 - Const(4.0) * x2,
    ))
    pair: Tuple[Var, Expr]
    for pair in extra_rows:
        algebraic_vars.append(pair[0])
        algebraic_eqs.append(pair[1])
    derivatives: List[Var] = list((Var("d_x1", base_var=x1), Var("d_x2", base_var=x2)))
    block: Block = Block(name="synthetic", state_vars=list((x1, x2)), state_eqs=list((-x1 + y1, sin(x2) * y2)), diff_vars=derivatives,
                         algebraic_vars=algebraic_vars, algebraic_eqs=algebraic_eqs, parameters=dict(((p, Const(2.5)),)))
    problem: EmtProblemTemplate = EmtProblemTemplate(sys_block=block, static_parameter_values_mapping=dict(((p, Const(2.5)),)), glob_time=Var("time"))
    values: List[float] = list((0.4, 0.7))
    variable: Var
    for variable in algebraic_vars:
        values.append(0.2 + 0.1 * len(values))
    index: int
    for index, variable in enumerate(list((x1, x2)) + algebraic_vars):
        problem.init_guess[variable.uid] = values[index]
    return problem


def _construct(program: EmtNativeProgram, arrays: Dict[str, npt.NDArray], model_identity: str, n_states: int) -> EmtNativeProgram:
    """
    Construct a program from a valid one with some arrays or counts replaced.

    :param program: Valid program supplying every field not replaced.
    :param arrays: Replacement arrays by getter name.
    :param model_identity: Model identity to use.
    :param n_states: State count to use.
    :return: New program (validation runs in the constructor).
    """
    source: Dict[str, npt.NDArray] = dict()
    source["instructions"] = program.get_instructions()
    source["instruction_literals"] = program.get_instruction_literals()
    source["groups"] = program.get_groups()
    source["runtime_map"] = program.get_runtime_map()
    source["parameter_map"] = program.get_parameter_map()
    source["residual_map"] = program.get_residual_map()
    source["column_pointers"] = program.get_column_pointers()
    source["row_indices"] = program.get_row_indices()
    source["literal_parameter_values"] = program.get_literal_parameter_values()
    source["group_affinity"] = program.get_group_affinity()
    name: str
    for name in arrays:
        source[name] = arrays[name]
    return EmtNativeProgram(model_identity=model_identity, n_unknowns=program.get_n_unknowns(), n_states=n_states,
                            n_event_parameters=program.get_n_event_parameters(), n_constant_parameters=program.get_n_constant_parameters(),
                            instructions=source["instructions"], instruction_literals=source["instruction_literals"], groups=source["groups"],
                            runtime_map=source["runtime_map"], parameter_map=source["parameter_map"], residual_map=source["residual_map"],
                            column_pointers=source["column_pointers"], row_indices=source["row_indices"],
                            literal_parameter_values=source["literal_parameter_values"], group_affinity=source["group_affinity"])


def _first_instruction(program: EmtNativeProgram, opcodes: Set[int]) -> int:
    """
    Return the global index of the first instruction whose opcode is in a set.

    :param program: Program.
    :param opcodes: Accepted opcodes.
    :return: Instruction index.
    """
    instructions: npt.NDArray[np.int32] = program.get_instructions()
    index: int
    for index in range(instructions.shape[0] // 4):
        if int(instructions[4 * index]) in opcodes:
            return index
        else:
            pass
    raise AssertionError("No instruction with the requested opcodes")


def _row_unknown_dependencies(problem: EmtProblemTemplate) -> Set[Tuple[int, int]]:
    """
    Recompute the (row, unknown) dependencies directly from the expressions.

    :param problem: EMT problem.
    :return: Dependency pairs.
    """
    states: List[Var] = problem.get_state_vars()
    rows: List[Expr] = list(problem.get_state_eqs()) + list(problem.get_algebraic_eqs())
    dependencies: Set[Tuple[int, int]] = set()
    row: int
    expression: Expr
    for row, expression in enumerate(rows):
        if row < len(states):
            dependencies.add((row, problem.uid2idx_vars[states[row].uid]))
        else:
            pass
        pending: List[Expr] = list((expression,))
        while len(pending) > 0:
            node: Expr = pending.pop()
            if type(node) is BinOp:
                pending.append(node.left)
                pending.append(node.right)
            elif type(node) is UnOp:
                pending.append(node.operand)
            elif type(node) is Func:
                pending.append(node.arg)
            elif type(node) is Var and node.base_var is not None:
                dependencies.add((row, problem.uid2idx_vars[node.base_var.uid]))
            elif type(node) is Var and node.uid in problem.uid2idx_vars:
                dependencies.add((row, problem.uid2idx_vars[node.uid]))
            else:
                pass
    return dependencies


def test_opcode_table() -> None:
    """
    EmtNativeOpcode reproduces GSLV's closed opcode set and values.

    :return: None.
    """
    expected: List[str] = list(("CONSTANT", "RUNTIME", "DIFFERENTIAL", "PARAMETER", "ADD", "SUBTRACT", "MULTIPLY", "DIVIDE", "POWER_CONSTANT",
                                "POWER", "NEGATE", "SIN", "COS", "EXP", "LOG", "SQRT", "ABSOLUTE", "HEAVISIDE"))
    value: int
    name: str
    for value, name in enumerate(expected):
        assert int(EmtNativeOpcode[name]) == value
    assert len(EmtNativeOpcode) == 18


def test_families_split_by_structure_exponent_and_promote_per_lane_literals() -> None:
    """
    Rows differing only in constants share a family with promoted literals; exponents split families.

    :return: None.
    """
    z1: Var = Var("z1")
    z2: Var = Var("z2")
    z3: Var = Var("z3")
    z4: Var = Var("z4")
    x1: Var = Var("x1")
    x2: Var = Var("x2")
    problem: EmtProblemTemplate = _synthetic_problem(list(((z1, z1 - x1 ** Const(2.0)), (z2, z2 - x2 ** Const(3.0)),
                                                           (z3, z3 - Const(3.0) * x1), (z4, z4 - Const(-0.0) * x2))), (x1, x2))
    program: EmtNativeProgram = compile_emt_native_program(problem, "synthetic")
    groups: npt.NDArray[np.int32] = program.get_groups()
    residual_map: npt.NDArray[np.int32] = program.get_residual_map()
    rows_by_group: List[List[int]] = list()
    group: int
    for group in range(program.get_n_groups()):
        begin: int = int(groups[10 * group + 8])
        rows_by_group.append(residual_map[begin:begin + int(groups[10 * group + 2])].tolist())
    family_of: Dict[int, int] = dict()
    rows: List[int]
    for group, rows in enumerate(rows_by_group):
        row: int
        for row in rows:
            family_of[row] = group

    # y8 - 3x1, y9 - 4x2, z3 - 3x1 and z4 - (-0.0)x2 share one family; the constant is promoted.
    assert family_of[9] == family_of[10] == family_of[13] == family_of[14]
    assert program.get_n_literal_parameters() >= 4
    assert 4.0 in program.get_literal_parameter_values().tolist()
    signs: List[bool] = list()
    value: float
    for value in program.get_literal_parameter_values().tolist():
        if value == 0.0:
            signs.append(math.copysign(1.0, value) < 0.0)
        else:
            pass
    assert True in signs

    # Different exponents never share a family.
    assert family_of[11] != family_of[12]

    # Families are ordered by their smallest row and lanes ascend.
    firsts: List[int] = list()
    for rows in rows_by_group:
        assert rows == sorted(rows)
        firsts.append(rows[0])
    assert firsts == sorted(firsts)


def test_lowering_covers_every_opcode_and_fixed_unused_fields() -> None:
    """
    The synthetic problem lowers to every opcode with -1 unused operands and 0.0 literals on non-literal opcodes.

    :return: None.
    """
    program: EmtNativeProgram = compile_emt_native_program(_synthetic_problem(list()), "synthetic")
    instructions: npt.NDArray[np.int32] = program.get_instructions().reshape(-1, 4)
    literals: npt.NDArray[np.float64] = program.get_instruction_literals()
    seen: Set[int] = set(instructions[:, 0].tolist())
    opcode: EmtNativeOpcode
    for opcode in EmtNativeOpcode:
        assert int(opcode) in seen, opcode.name
    index: int
    for index in range(instructions.shape[0]):
        code: int = int(instructions[index, 0])
        if code != int(EmtNativeOpcode.CONSTANT) and code != int(EmtNativeOpcode.POWER_CONSTANT):
            assert literals[index] == 0.0
        else:
            pass


@pytest.mark.parametrize("case", ["func2_max", "asin", "floor", "complex_constant", "time", "unknown_variable", "algebraic_derivative"])
def test_unsupported_nodes_raise_with_row_index(case: str) -> None:
    """
    Nodes without an opcode raise ValueError naming the row.

    :param case: Unsupported node class.
    :return: None.
    """
    w: Var = Var("w")
    x1: Var = Var("x_extra")
    if case == "func2_max":
        equation: Expr = w - Func2("max", Const(1.0), Const(2.0))
    elif case == "asin":
        equation = w - Func(Const(0.5), op="asin")
    elif case == "floor":
        equation = w - Func(Const(0.5), op="floor")
    elif case == "complex_constant":
        equation = w - Const(1j)
    elif case == "time":
        equation = w - Var("time")
    elif case == "unknown_variable":
        equation = w - x1
    else:
        equation = w - Var("d_w", base_var=w)
    with pytest.raises(ValueError, match="Row "):
        compile_emt_native_program(_synthetic_problem(list(((w, equation),))), "synthetic")


def test_nested_state_and_identity_are_rejected() -> None:
    """
    Nested states and invalid identities are rejected before lowering.

    :return: None.
    """
    with pytest.raises(ValueError):
        compile_emt_native_program(_synthetic_problem(list()), "bad\tidentity")
    problem: EmtProblemTemplate = _synthetic_problem(list())
    problem.get_state_vars().append(Var("nested", base_var=Var("origin")))
    with pytest.raises(ValueError):
        compile_emt_native_program(problem, "synthetic")


def test_compile_after_building_the_reference_gives_the_same_program() -> None:
    """
    Building StructuralCompiledSolver (which rebinds diff_var) does not change the compiled program.

    :return: None.
    """
    problem: EmtProblemTemplate = _synthetic_problem(list())
    before: str = compile_emt_native_program(problem, "synthetic").get_fingerprint()
    StructuralCompiledSolver(problem, t0=0.0, t_end=1.0e-4, h=5.0e-6, method=DynamicIntegrationMethod.DaeTrapezoidal,
                             warmup_policy=StructuralCompiledWarmupPolicy.Off)
    assert compile_emt_native_program(problem, "synthetic").get_fingerprint() == before


def test_kundur_structure_matches_the_expressions(kundur_problem: EmtProblemDae, kundur_program: EmtNativeProgram) -> None:
    """
    Kundur: residual_map is a bijection and the CSC equals the dependencies recomputed from the expressions.

    :param kundur_problem: Kundur EMT problem.
    :param kundur_program: Kundur native program.
    :return: None.
    """
    pattern: Set[Tuple[int, int]] = set()
    pointers: npt.NDArray[np.int32] = kundur_program.get_column_pointers()
    rows: npt.NDArray[np.int32] = kundur_program.get_row_indices()
    column: int
    for column in range(kundur_program.get_n_unknowns()):
        row: int
        for row in rows[int(pointers[column]):int(pointers[column + 1])].tolist():
            pattern.add((row, column))
    assert kundur_program.get_n_unknowns() == 537
    assert kundur_program.get_n_states() == 220
    assert sorted(kundur_program.get_residual_map().tolist()) == list(range(537))
    assert pattern == _row_unknown_dependencies(kundur_problem)
    lanes: List[int] = kundur_program.get_groups().reshape(-1, 10)[:, 2].tolist()
    print("Kundur families", kundur_program.get_n_groups(), "lane widths", sorted(lanes), "instructions",
          kundur_program.get_instructions().shape[0] // 4, "literal parameters", kundur_program.get_n_literal_parameters())


def test_two_independent_kundur_builds_give_identical_artifacts(kundur_program: EmtNativeProgram, tmp_path: object) -> None:
    """
    Two independently built Kundur problems compile to byte-identical artifacts and equal fingerprints.

    :param kundur_program: Kundur native program.
    :param tmp_path: Temporary directory.
    :return: None.
    """
    second: EmtNativeProgram = compile_emt_native_program(_build_kundur_problem()[0], "kundur")
    assert second.get_fingerprint() == kundur_program.get_fingerprint()
    first_directory: str = os.path.join(str(tmp_path), "first")
    second_directory: str = os.path.join(str(tmp_path), "second")
    write_emt_native_program(kundur_program, first_directory)
    write_emt_native_program(second, second_directory)
    name: str
    for name in sorted(os.listdir(first_directory)):
        handle: BinaryIO
        with open(os.path.join(first_directory, name), "rb") as handle:
            first_bytes: bytes = handle.read()
        with open(os.path.join(second_directory, name), "rb") as handle:
            second_bytes: bytes = handle.read()
        assert first_bytes == second_bytes, name


def _mutated_arrays(program: EmtNativeProgram, case: str) -> Tuple[Dict[str, npt.NDArray], str, int]:
    """
    Return replacement arrays, identity and state count that break exactly one rule.

    :param program: Valid synthetic program.
    :param case: Rule case name.
    :return: Arrays by getter name, model identity and state count.
    """
    arrays: Dict[str, npt.NDArray] = dict()
    identity: str = "synthetic"
    n_states: int = program.get_n_states()
    instructions: npt.NDArray[np.int32] = np.array(program.get_instructions())
    literals: npt.NDArray[np.float64] = np.array(program.get_instruction_literals())
    groups: npt.NDArray[np.int32] = np.array(program.get_groups())
    pointers: npt.NDArray[np.int32] = np.array(program.get_column_pointers())
    rows: npt.NDArray[np.int32] = np.array(program.get_row_indices())
    binary_codes: Set[int] = set((int(EmtNativeOpcode.ADD), int(EmtNativeOpcode.SUBTRACT), int(EmtNativeOpcode.MULTIPLY), int(EmtNativeOpcode.DIVIDE)))
    if case == "identity":
        identity = "bad\tidentity"
    elif case == "state_count":
        n_states = program.get_n_unknowns() + 1
    elif case == "groups_length":
        arrays["groups"] = groups[:-1]
    elif case == "group_gap":
        groups[10 + 0] += 1
        arrays["groups"] = groups
    elif case == "lane_zero":
        groups[2] = 0
        arrays["groups"] = groups
    elif case == "output_slot":
        groups[9] = 0
        arrays["groups"] = groups
    elif case == "runtime_map_range":
        runtime_map: npt.NDArray[np.int32] = np.array(program.get_runtime_map())
        runtime_map[0] = program.get_n_unknowns()
        arrays["runtime_map"] = runtime_map
    elif case == "parameter_map_range":
        parameter_map: npt.NDArray[np.int32] = np.array(program.get_parameter_map())
        parameter_map[0] = program.get_n_parameters()
        arrays["parameter_map"] = parameter_map
    elif case == "affinity_range":
        affinity: npt.NDArray[np.int32] = np.array(program.get_group_affinity())
        affinity[0] = 9
        arrays["group_affinity"] = affinity
    elif case == "output_not_local":
        instructions[3] = 5
        arrays["instructions"] = instructions
    elif case == "operand_unwritten":
        index: int = _first_instruction(program, binary_codes)
        instructions[4 * index + 1] = int(instructions[4 * index + 3])
        arrays["instructions"] = instructions
    elif case == "unused_operand":
        index = _first_instruction(program, set((int(EmtNativeOpcode.RUNTIME),)))
        instructions[4 * index + 2] = 0
        arrays["instructions"] = instructions
    elif case == "literal_on_non_literal":
        index = _first_instruction(program, set((int(EmtNativeOpcode.RUNTIME),)))
        literals[index] = 1.0
        arrays["instruction_literals"] = literals
    elif case == "non_finite_literal":
        index = _first_instruction(program, set((int(EmtNativeOpcode.CONSTANT),)))
        literals[index] = float("nan")
        arrays["instruction_literals"] = literals
    elif case == "unknown_opcode":
        instructions[0] = 42
        arrays["instructions"] = instructions
    elif case == "differential_non_state":
        n_states = 0
    elif case == "residual_map_bijection":
        residual_map: npt.NDArray[np.int32] = np.array(program.get_residual_map())
        residual_map[0] = residual_map[1]
        arrays["residual_map"] = residual_map
    elif case == "csc_missing_entry":
        arrays["row_indices"] = rows[1:]
        pointers[1:] -= 1
        arrays["column_pointers"] = pointers
    elif case == "csc_extra_entry":
        column_rows: List[int] = rows[int(pointers[0]):int(pointers[1])].tolist()
        candidate: int = 0
        while candidate in column_rows:
            candidate += 1
        arrays["row_indices"] = np.concatenate((np.array(sorted(column_rows + list((candidate,))), dtype=np.int32), rows[int(pointers[1]):]))
        pointers[1:] += 1
        arrays["column_pointers"] = pointers
    elif case == "csc_not_canonical":
        column: int = 0
        while int(pointers[column + 1]) - int(pointers[column]) < 2:
            column += 1
        start: int = int(pointers[column])
        rows[start], rows[start + 1] = rows[start + 1], rows[start]
        arrays["row_indices"] = rows
    elif case == "literal_parameter_non_finite":
        tail: npt.NDArray[np.float64] = np.array(program.get_literal_parameter_values())
        tail[0] = float("inf")
        arrays["literal_parameter_values"] = tail
    else:
        raise AssertionError("Unknown case " + case)
    return arrays, identity, n_states


@pytest.mark.parametrize("case", ["identity", "state_count", "groups_length", "group_gap", "lane_zero", "output_slot", "runtime_map_range",
                                  "parameter_map_range", "affinity_range", "output_not_local", "operand_unwritten", "unused_operand",
                                  "literal_on_non_literal", "non_finite_literal", "unknown_opcode", "differential_non_state",
                                  "residual_map_bijection", "csc_missing_entry", "csc_extra_entry", "csc_not_canonical",
                                  "literal_parameter_non_finite"])
def test_constructor_rejects_each_rule(case: str) -> None:
    """
    The constructor accepts the valid program and rejects each broken GSLV rule with ValueError.

    :param case: Rule case name.
    :return: None.
    """
    program: EmtNativeProgram = compile_emt_native_program(_synthetic_problem(list()), "synthetic")
    assert _construct(program, dict(), "synthetic", program.get_n_states()).get_fingerprint() == program.get_fingerprint()
    arrays: Dict[str, npt.NDArray]
    identity: str
    n_states: int
    arrays, identity, n_states = _mutated_arrays(program, case)
    with pytest.raises(ValueError):
        _construct(program, arrays, identity, n_states)


def test_fingerprint_detects_sign_of_zero_and_last_ulp() -> None:
    """
    Literals differing only in the sign of zero or in the last ulp give different fingerprints.

    :return: None.
    """
    fingerprints: List[str] = list()
    value: float
    for value in (0.0, -0.0, 3.0, float(np.nextafter(3.0, 4.0))):
        w: Var = Var("w")
        program: EmtNativeProgram = compile_emt_native_program(_synthetic_problem(list(((w, w - Const(value)),))), "synthetic")
        fingerprints.append(program.get_fingerprint())
    assert fingerprints[0] != fingerprints[1]
    assert fingerprints[2] != fingerprints[3]


def test_round_trip(kundur_program: EmtNativeProgram, tmp_path: object) -> None:
    """
    Write then read gives an equal program; files are little-endian with the declared sizes.

    :param kundur_program: Kundur native program.
    :param tmp_path: Temporary directory.
    :return: None.
    """
    directory: str = str(tmp_path)
    write_emt_native_program(kundur_program, directory)
    read_program: EmtNativeProgram = read_emt_native_program(directory, "kundur")
    assert read_program.get_fingerprint() == kundur_program.get_fingerprint()
    assert read_program.get_instructions().tobytes() == kundur_program.get_instructions().tobytes()
    assert read_program.get_instruction_literals().tobytes() == kundur_program.get_instruction_literals().tobytes()
    handle: BinaryIO
    with open(os.path.join(directory, "instructions.i32le"), "rb") as handle:
        assert handle.read() == kundur_program.get_instructions().astype("<i4").tobytes()
    with open(os.path.join(directory, "manifest.json"), "rb") as handle:
        manifest_bytes: bytes = handle.read()
    assert canonical_json_bytes(json.loads(manifest_bytes.decode("utf-8"))) == manifest_bytes


def _store_manifest(directory: str, manifest: Dict[str, object], refresh_payload_hash: bool) -> None:
    """
    Write a manifest in canonical form, optionally refreshing its payload hash.

    :param directory: Artifact directory.
    :param manifest: Manifest to write.
    :param refresh_payload_hash: Recompute manifest_payload_sha256.
    :return: None.
    """
    if refresh_payload_hash:
        payload: Dict[str, object] = dict(manifest)
        payload.pop("manifest_payload_sha256", None)
        manifest["manifest_payload_sha256"] = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
    else:
        pass
    handle: BinaryIO
    with open(os.path.join(directory, "manifest.json"), "wb") as handle:
        handle.write(canonical_json_bytes(manifest))


@pytest.mark.parametrize("case", ["directory_is_file", "missing_manifest", "missing_array_file", "non_canonical_manifest", "extra_manifest_key",
                                  "files_key_set", "file_sha256", "payload_hash", "fingerprint", "opcode_table", "semantics", "encoding",
                                  "literal_count", "structural_rule", "manifest_over_limit", "wrong_identity"])
def test_reader_rejects_each_failure_class(case: str, tmp_path: object) -> None:
    """
    Every failure class makes the reader raise ValueError; the untouched artifact reads back.

    :param case: Failure class name.
    :param tmp_path: Temporary directory.
    :return: None.
    """
    program: EmtNativeProgram = compile_emt_native_program(_synthetic_problem(list()), "synthetic")
    directory: str = os.path.join(str(tmp_path), "artifact")
    write_emt_native_program(program, directory)
    assert read_emt_native_program(directory, "synthetic").get_fingerprint() == program.get_fingerprint()
    handle: BinaryIO
    with open(os.path.join(directory, "manifest.json"), "rb") as handle:
        manifest: Dict[str, object] = json.loads(handle.read().decode("utf-8"))
    read_directory: str = directory
    identity: str = "synthetic"
    manifest_limit: int = 1048576
    if case == "directory_is_file":
        read_directory = os.path.join(directory, "manifest.json")
    elif case == "missing_manifest":
        os.remove(os.path.join(directory, "manifest.json"))
    elif case == "missing_array_file":
        os.remove(os.path.join(directory, "groups.i32le"))
    elif case == "non_canonical_manifest":
        with open(os.path.join(directory, "manifest.json"), "wb") as handle:
            handle.write(json.dumps(manifest, sort_keys=True, indent=1).encode("utf-8"))
    elif case == "extra_manifest_key":
        manifest["extra"] = 1
        _store_manifest(directory, manifest, True)
    elif case == "files_key_set":
        manifest["files"].pop("groups.i32le")
        _store_manifest(directory, manifest, True)
    elif case == "file_sha256":
        with open(os.path.join(directory, "groups.i32le"), "r+b") as handle:
            handle.write(b"\x07")
    elif case == "payload_hash":
        manifest["manifest_payload_sha256"] = "0" * 64
        _store_manifest(directory, manifest, False)
    elif case == "fingerprint":
        manifest["fingerprint"] = "0" * 64
        _store_manifest(directory, manifest, True)
    elif case == "opcode_table":
        manifest["opcodes"]["ADD"] = 99
        _store_manifest(directory, manifest, True)
    elif case == "semantics":
        manifest["semantics"] = "AFFINE rows are constant."
        _store_manifest(directory, manifest, True)
    elif case == "encoding":
        manifest["encoding"] = "big-endian"
        _store_manifest(directory, manifest, True)
    elif case == "literal_count":
        manifest["n_literal_parameters"] = program.get_n_literal_parameters() + 1
        _store_manifest(directory, manifest, True)
    elif case == "structural_rule":
        broken: bytes = np.array(program.get_residual_map()[::-1].tolist()[:1] * program.get_n_unknowns(), dtype="<i4").tobytes()
        with open(os.path.join(directory, "residual_map.i32le"), "wb") as handle:
            handle.write(broken)
        manifest["files"]["residual_map.i32le"]["sha256"] = hashlib.sha256(broken).hexdigest()
        _store_manifest(directory, manifest, True)
    elif case == "manifest_over_limit":
        manifest_limit = 10
    else:
        identity = "another model"
    with pytest.raises(ValueError):
        read_emt_native_program(read_directory, identity, maximum_manifest_bytes=manifest_limit)


def _reference_solver(problem: EmtProblemTemplate, method: DynamicIntegrationMethod, h: float) -> StructuralCompiledSolver:
    """
    Build the parity reference: StructuralCompiledSolver without fastmath (warmup Off), backend built for one method.

    :param problem: EMT problem.
    :param method: Integration method.
    :param h: Step size.
    :return: Reference solver (read-only use of its evaluators).
    """
    solver: StructuralCompiledSolver = StructuralCompiledSolver(problem, t0=0.0, t_end=1.0e-4, h=h, method=method,
                                                                warmup_policy=StructuralCompiledWarmupPolicy.Off, auto_build=False)
    solver._build_vectorized_backend(method)
    return solver


def _parity_points(problem: EmtProblemTemplate) -> List[Tuple[npt.NDArray, npt.NDArray, npt.NDArray, npt.NDArray]]:
    """
    Return the parity points P0, P1 and P2 (states, history, history2, derivative history).

    :param problem: EMT problem.
    :return: Three points.
    """
    x0: npt.NDArray[np.float64] = np.asarray(problem.get_x0(), dtype=np.float64)
    dx0: npt.NDArray[np.float64] = np.asarray(problem.get_dx0(), dtype=np.float64)
    points: List[Tuple[npt.NDArray, npt.NDArray, npt.NDArray, npt.NDArray]] = list()
    points.append((x0.copy(), x0.copy(), x0.copy(), dx0.copy()))
    generator: np.random.Generator = np.random.default_rng(20261022)
    seed_round: int
    for seed_round in range(2):
        scale: npt.NDArray[np.float64] = 1.0e-3 * (1.0 + np.abs(x0))
        points.append((x0 + scale * generator.standard_normal(x0.shape), x0.copy(), x0 - scale * generator.standard_normal(x0.shape),
                       dx0 + 1.0e-3 * (1.0 + np.abs(dx0)) * generator.standard_normal(dx0.shape)))
    return points


def _residual_bound(program: EmtNativeProgram, point: ProgramPoint, reference: npt.NDArray, magnitude: npt.NDArray) -> npt.NDArray:
    """
    Return the sealed REQ-007 residual tolerance per row.

    :param program: Native program.
    :param point: Evaluation point.
    :param reference: Reference residual.
    :param magnitude: Largest absolute intermediate per row.
    :return: Tolerance per row.
    """
    eps: float = 2.22e-16
    bound: npt.NDArray[np.float64] = 1.0e-12 * np.maximum(1.0, np.maximum(np.abs(reference), magnitude))
    states: int = program.get_n_states()
    row: int
    for row in range(states):
        if point.method == DynamicIntegrationMethod.DaeBDF2:
            bound[row] += 16.0 * eps * (1.5 * abs(point.states[row]) + 2.0 * abs(point.history[row]) + 0.5 * abs(point.history2[row])) / point.h
        else:
            bound[row] += 8.0 * eps * (abs(point.states[row] - point.history[row]) * 2.0 / point.h + abs(point.derivative_history[row]))
    return bound


def _assert_parity(problem: EmtProblemTemplate, program: EmtNativeProgram, label: str) -> Dict[str, float]:
    """
    Check residual and Jacobian parity at P0, P1, P2 for the three methods, with the sealed attribution rule.

    :param problem: EMT problem.
    :param program: Its native program.
    :param label: Case label used in messages.
    :return: Maximum error/bound ratio per method and row kind.
    """
    h: float = 5.0e-6
    ratios: Dict[str, float] = dict()
    reference_defects: List[str] = list()
    method: DynamicIntegrationMethod
    for method in (DynamicIntegrationMethod.DaeTrapezoidal, DynamicIntegrationMethod.DaeBackEuler, DynamicIntegrationMethod.DaeBDF2):
        solver: StructuralCompiledSolver = _reference_solver(problem, method, h)
        external: npt.NDArray[np.float64] = np.concatenate((np.asarray(problem.event_params_values, dtype=np.float64),
                                                            np.asarray(solver._static_parameter_buffer, dtype=np.float64)))
        parameters: npt.NDArray[np.float64] = np.concatenate((external, program.get_literal_parameter_values()))
        point_index: int
        values: Tuple[npt.NDArray, npt.NDArray, npt.NDArray, npt.NDArray]
        for point_index, values in enumerate(_parity_points(problem)):
            x: npt.NDArray[np.float64] = values[0]
            point: ProgramPoint = ProgramPoint(x, parameters, values[1], values[2], values[3], h, method)
            reference_residual: npt.NDArray[np.float64] = np.zeros_like(x)
            solver._residual_assembler.evaluate(x, external, values[1], values[3], h, values[2], reference_residual)
            reference_jacobian: npt.NDArray[np.float64] = solver._jacobian_evaluator.evaluate(x, external, values[1], values[3], h, values[2]).toarray()
            residual: npt.NDArray[np.float64]
            residual_magnitude: npt.NDArray[np.float64]
            residual, residual_magnitude = evaluate_program_residual(program, point)
            jacobian: npt.NDArray[np.float64]
            tangent_magnitude: npt.NDArray[np.float64]
            jacobian, tangent_magnitude = evaluate_program_jacobian(program, point)
            residual_bound: npt.NDArray[np.float64] = _residual_bound(program, point, reference_residual, residual_magnitude)
            residual_error: npt.NDArray[np.float64] = np.abs(residual - reference_residual)
            assert bool(np.all(residual_error <= residual_bound)), label + " residual " + method.name + " P" + str(point_index)
            jacobian_scale: npt.NDArray[np.float64] = np.maximum(1.0, np.maximum(np.abs(reference_jacobian), tangent_magnitude[:, None]))
            jacobian_error: npt.NDArray[np.float64] = np.abs(jacobian - reference_jacobian)
            entry: npt.NDArray
            for entry in np.argwhere(jacobian_error > 1.0e-12 * jacobian_scale):
                row: int = int(entry[0])
                column: int = int(entry[1])
                step: float = 1.0e-7 * max(1.0, abs(float(x[column])))
                plus: npt.NDArray[np.float64] = x.copy()
                minus: npt.NDArray[np.float64] = x.copy()
                plus[column] += step
                minus[column] -= step
                plus_residual: npt.NDArray[np.float64]
                minus_residual: npt.NDArray[np.float64]
                unused_plus: npt.NDArray[np.float64]
                unused_minus: npt.NDArray[np.float64]
                plus_residual, unused_plus = evaluate_program_residual(program, ProgramPoint(plus, parameters, values[1], values[2], values[3], h, method))
                minus_residual, unused_minus = evaluate_program_residual(program, ProgramPoint(minus, parameters, values[1], values[2], values[3], h, method))
                central: float = (float(plus_residual[row]) - float(minus_residual[row])) / (2.0 * step)
                assert abs(float(jacobian[row, column]) - central) <= 1.0e-6 * max(1.0, abs(central)), label + " program Jacobian defect"
                if float(jacobian_error[row, column]) <= 1.0e-9 * float(jacobian_scale[row, column]):
                    pass
                else:
                    reference_defects.append(method.name + " P" + str(point_index) + " (" + str(row) + ", " + str(column) + ")")
            state_ratio: float = float(np.max(residual_error[:program.get_n_states()] / residual_bound[:program.get_n_states()]))
            algebraic_ratio: float = float(np.max(residual_error[program.get_n_states():] / residual_bound[program.get_n_states():]))
            ratios[method.name + " state"] = max(ratios.get(method.name + " state", 0.0), state_ratio)
            ratios[method.name + " algebraic"] = max(ratios.get(method.name + " algebraic", 0.0), algebraic_ratio)
    print(label, "residual error/bound ratios", ratios)
    assert len(reference_defects) == 0, label + ": reference Jacobian defects to escalate: " + "; ".join(reference_defects[:16]) + " (" + str(len(reference_defects)) + " total)"
    return ratios


def test_synthetic_parity_with_structural_compiled_solver() -> None:
    """
    The synthetic problem matches StructuralCompiledSolver's residual and Jacobian for the three methods at P0, P1, P2.

    :return: None.
    """
    problem: EmtProblemTemplate = _synthetic_problem(list())
    _assert_parity(problem, compile_emt_native_program(problem, "synthetic"), "synthetic")


def test_kundur_parity_with_structural_compiled_solver(kundur_problem: EmtProblemDae, kundur_program: EmtNativeProgram) -> None:
    """
    Kundur matches StructuralCompiledSolver's residual and Jacobian for the three methods at P0, P1, P2.

    :param kundur_problem: Kundur EMT problem.
    :param kundur_program: Kundur native program.
    :return: None.
    """
    _assert_parity(kundur_problem, kundur_program, "Kundur")


def test_differential_term_is_exact_at_p0_for_trapezoidal_and_backward_euler(kundur_problem: EmtProblemDae, kundur_program: EmtNativeProgram) -> None:
    """
    At P0 (x = xh) the DIFFERENTIAL term equals -dxh (trapezoidal) and 0 (backward Euler) exactly.

    :param kundur_problem: Kundur EMT problem.
    :param kundur_program: Kundur native program.
    :return: None.
    """
    x0: npt.NDArray[np.float64] = np.asarray(kundur_problem.get_x0(), dtype=np.float64)
    dx0: npt.NDArray[np.float64] = np.asarray(kundur_problem.get_dx0(), dtype=np.float64)
    parameters: npt.NDArray[np.float64] = np.zeros(kundur_program.get_n_parameters())
    state: int
    for state in range(kundur_program.get_n_states()):
        trapezoidal: ProgramPoint = ProgramPoint(x0, parameters, x0, x0, dx0, 5.0e-6, DynamicIntegrationMethod.DaeTrapezoidal)
        backward: ProgramPoint = ProgramPoint(x0, parameters, x0, x0, dx0, 5.0e-6, DynamicIntegrationMethod.DaeBackEuler)
        assert differential_value(trapezoidal, state) == -float(dx0[state])
        assert differential_value(backward, state) == 0.0


def test_kundur_pre_scan_of_reference_ad_patterns(kundur_problem: EmtProblemDae) -> None:
    """
    Record how many Kundur nodes have the pattern the reference AD value strings mishandle.

    The pattern is the right operand of - (or of a zero-left -) whose operator is + or -,
    or the right operand of / whose operator is * or /, occurring as an operand of *, / or **.

    :param kundur_problem: Kundur EMT problem.
    :return: None.
    """
    count: int = 0
    pending: List[Tuple[Expr, bool]] = list()
    expression: Expr
    for expression in list(kundur_problem.get_state_eqs()) + list(kundur_problem.get_algebraic_eqs()):
        pending.append((expression, False))
    while len(pending) > 0:
        node: Expr
        inside_product: bool
        node, inside_product = pending.pop()
        if type(node) is BinOp:
            risky_minus: bool = node.op == "-" and type(node.right) is BinOp and node.right.op in ("+", "-")
            risky_divide: bool = node.op == "/" and type(node.right) is BinOp and node.right.op in ("*", "/")
            if inside_product and (risky_minus or risky_divide):
                count += 1
            else:
                pass
            child_inside: bool = node.op in ("*", "/", "**")
            pending.append((node.left, child_inside))
            pending.append((node.right, child_inside))
        elif type(node) is UnOp:
            pending.append((node.operand, inside_product))
        elif type(node) is Func:
            pending.append((node.arg, inside_product))
        else:
            pass
    print("Kundur pre-scan count of reference AD risk patterns:", count)
    assert count >= 0
