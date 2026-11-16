# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Compilation of an EMT problem into the native program of external EMT solvers.

The program follows the GSLV native EMT structural format: homogeneous groups
(families) of residual rows share one topologically ordered SSA instruction
tape over a closed opcode set; per-lane unknowns, parameters and constants are
reached through slot-major, lane-minor maps. Rows share a family when they have
the same structure after renaming unknowns, parameters and constants to slots,
the same residual row affinity and the same row kind. The CSC pattern is the
exact set of unknowns each row reads.
"""

from __future__ import annotations

import hashlib
import struct
from typing import Dict, List, Set, Tuple

import numpy as np
import numpy.typing as npt

from VeraGridEngine.enumerations import EmtNativeOpcode, ExpressionAffinity, ResidualRowAffinityCode
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Simulations.EMT.problems.emt_residual_row_classification import (
    EmtResidualRowClassification,
    classify_emt_residual_rows,
)
from VeraGridEngine.Utils.artifact_validation import immutable_array, validate_model_identity
from VeraGridEngine.Utils.canonical_json import canonical_json_bytes
from VeraGridEngine.Utils.Symbolic.symbolic import BinOp, Const, Func, UnOp, Var


def _float_bits(value: float) -> int:
    """
    Return the IEEE-754 bit pattern of a float64.

    :param value: Float value.
    :return: Unsigned 64-bit pattern as int.
    """
    return int(struct.unpack("<Q", struct.pack("<d", value))[0])


def _array_digest(values: npt.NDArray) -> Dict[str, object]:
    """
    Describe one int32 or float64 program array for the fingerprint payload.

    :param values: Array in native byte order.
    :return: Interchange dtype, element count and SHA-256 of the little-endian bytes.
    """
    if values.dtype == np.dtype(np.int32):
        data: bytes = values.astype("<i4").tobytes()
        dtype_name: str = "i32le"
    else:
        data = values.astype("<f8").tobytes()
        dtype_name = "f64le"
    description: Dict[str, object] = dict()
    description["dtype"] = dtype_name
    description["element_count"] = int(values.shape[0])
    description["sha256"] = hashlib.sha256(data).hexdigest()
    return description


class _RowLowering:
    """
    Lower one residual row into a slot-renamed SSA tape with hash-consing.

    Unknowns, parameters and constants become runtime, parameter and literal
    slots numbered by first occurrence in a post-order walk (left before
    right). Exponents of ``**`` stay in the structure exactly.
    """

    __slots__ = (
        "_row_index",
        "_unknown_index",
        "_state_uids",
        "_parameter_index",
        "_nodes",
        "_node_ids",
        "_runtime_slot_of_uid",
        "_runtime_unknowns",
        "_parameter_slot_of_uid",
        "_parameter_indices",
        "_literal_values",
    )

    def __init__(self,
                 row_index: int,
                 unknown_index: Dict[int, int],
                 state_uids: Set[int],
                 parameter_index: Dict[int, int]) -> None:
        """
        Prepare the lowering of one row.

        :param row_index: Residual row index, used in error messages.
        :param unknown_index: Unknown uid to unknown (column) index.
        :param state_uids: Uids of the state variables.
        :param parameter_index: Parameter uid to index in the [event | constant] vector.
        """
        self._row_index: int = row_index
        self._unknown_index: Dict[int, int] = unknown_index
        self._state_uids: Set[int] = state_uids
        self._parameter_index: Dict[int, int] = parameter_index
        self._nodes: List[Tuple] = list()
        self._node_ids: Dict[Tuple, int] = dict()
        self._runtime_slot_of_uid: Dict[int, int] = dict()
        self._runtime_unknowns: List[int] = list()
        self._parameter_slot_of_uid: Dict[int, int] = dict()
        self._parameter_indices: List[int] = list()
        self._literal_values: List[float] = list()

    def _emit(self, key: Tuple) -> int:
        """
        Return the node id of a structural key, creating it when new (hash-consing).

        :param key: Slot-renamed structural key of the node.
        :return: Node id (position in the tape).
        """
        existing: int = self._node_ids.get(key, -1)
        if existing >= 0:
            return existing
        else:
            node_id: int = len(self._nodes)
            self._nodes.append(key)
            self._node_ids[key] = node_id
            return node_id

    def _runtime_slot(self, uid: int) -> int:
        """
        Return the runtime slot of an unknown, assigned at its first occurrence.

        :param uid: Unknown uid.
        :return: Runtime slot.
        """
        slot: int = self._runtime_slot_of_uid.get(uid, -1)
        if slot >= 0:
            return slot
        else:
            slot = len(self._runtime_unknowns)
            self._runtime_slot_of_uid[uid] = slot
            self._runtime_unknowns.append(self._unknown_index[uid])
            return slot

    def _leaf(self, node: object) -> int:
        """
        Lower one leaf (Var or Const).

        :param node: Leaf expression.
        :return: Node id.
        :raises ValueError: For leaves without an opcode.
        """
        if type(node) is Const:
            value: object = node.value
            if type(value) is bool or not isinstance(value, (int, float)) or isinstance(value, complex):
                raise ValueError("Row " + str(self._row_index) + ": unsupported constant " + repr(value))
            else:
                slot: int = len(self._literal_values)
                self._literal_values.append(float(value))
                # A literal slot is a CONSTANT keyed by its slot (two fields).
                return self._emit((int(EmtNativeOpcode.CONSTANT), slot))
        elif type(node) is Var:
            if node.base_var is not None:
                base: Var = node.base_var
                if base.base_var is not None:
                    raise ValueError("Row " + str(self._row_index) + ": nested derivative " + node.name)
                elif base.uid not in self._state_uids:
                    raise ValueError("Row " + str(self._row_index) + ": derivative of a non-state variable " + node.name)
                else:
                    return self._emit((int(EmtNativeOpcode.DIFFERENTIAL), self._runtime_slot(base.uid)))
            elif node.uid in self._unknown_index:
                return self._emit((int(EmtNativeOpcode.RUNTIME), self._runtime_slot(node.uid)))
            elif node.uid in self._parameter_index:
                slot = self._parameter_slot_of_uid.get(node.uid, -1)
                if slot < 0:
                    slot = len(self._parameter_indices)
                    self._parameter_slot_of_uid[node.uid] = slot
                    self._parameter_indices.append(self._parameter_index[node.uid])
                else:
                    pass
                return self._emit((int(EmtNativeOpcode.PARAMETER), slot))
            else:
                raise ValueError("Row " + str(self._row_index) + ": variable " + node.name + " is neither an unknown nor a parameter")
        else:
            raise ValueError("Row " + str(self._row_index) + ": unsupported node type " + type(node).__name__)

    def lower(self, expression: object, state_uid: int) -> None:
        """
        Lower a residual row; for a state row the residual is DIFFERENTIAL(state) - expression.

        :param expression: Row expression (``f`` for state rows).
        :param state_uid: Uid of the row's state, or -1 for an algebraic row.
        :raises ValueError: For nodes without an opcode.
        """
        binary_opcodes: Dict[str, int] = dict()
        binary_opcodes["+"] = int(EmtNativeOpcode.ADD)
        binary_opcodes["-"] = int(EmtNativeOpcode.SUBTRACT)
        binary_opcodes["*"] = int(EmtNativeOpcode.MULTIPLY)
        binary_opcodes["/"] = int(EmtNativeOpcode.DIVIDE)
        function_opcodes: Dict[str, int] = dict()
        function_opcodes["sin"] = int(EmtNativeOpcode.SIN)
        function_opcodes["cos"] = int(EmtNativeOpcode.COS)
        function_opcodes["exp"] = int(EmtNativeOpcode.EXP)
        function_opcodes["log"] = int(EmtNativeOpcode.LOG)
        function_opcodes["sqrt"] = int(EmtNativeOpcode.SQRT)
        function_opcodes["abs"] = int(EmtNativeOpcode.ABSOLUTE)
        function_opcodes["heaviside"] = int(EmtNativeOpcode.HEAVISIDE)

        # State rows start with the discretised derivative of their own unknown.
        differential_id: int = -1
        if state_uid >= 0:
            differential_id = self._emit((int(EmtNativeOpcode.DIFFERENTIAL), self._runtime_slot(state_uid)))
        else:
            pass

        # Iterative post-order walk, left operand before right operand.
        results: List[int] = list()
        pending: List[Tuple[object, bool]] = list()
        pending.append((expression, False))
        while len(pending) > 0:
            node: object
            expanded: bool
            node, expanded = pending.pop()
            node_type: type = type(node)
            if node_type is BinOp:
                is_constant_power: bool = node.op == "**" and type(node.right) is Const
                if node.op not in binary_opcodes and node.op != "**":
                    raise ValueError("Row " + str(self._row_index) + ": unsupported operator " + node.op)
                elif not expanded:
                    pending.append((node, True))
                    if is_constant_power:
                        pending.append((node.left, False))
                    else:
                        pending.append((node.right, False))
                        pending.append((node.left, False))
                elif is_constant_power:
                    exponent_value: object = node.right.value
                    base_id: int = results.pop()
                    if type(exponent_value) is bool or not isinstance(exponent_value, (int, float)) or isinstance(exponent_value, complex):
                        raise ValueError("Row " + str(self._row_index) + ": unsupported exponent " + repr(exponent_value))
                    elif float(exponent_value) == 0.0:
                        # x ** 0 is the fixed constant 1.0 (three fields: CONSTANT, -1, bits).
                        results.append(self._emit((int(EmtNativeOpcode.CONSTANT), -1, _float_bits(1.0))))
                    else:
                        results.append(self._emit((int(EmtNativeOpcode.POWER_CONSTANT), base_id, _float_bits(float(exponent_value)))))
                else:
                    right_id: int = results.pop()
                    left_id: int = results.pop()
                    if node.op == "**":
                        results.append(self._emit((int(EmtNativeOpcode.POWER), left_id, right_id)))
                    else:
                        results.append(self._emit((binary_opcodes[node.op], left_id, right_id)))
            elif node_type is UnOp:
                if node.op != "-":
                    raise ValueError("Row " + str(self._row_index) + ": unsupported unary operator " + node.op)
                elif not expanded:
                    pending.append((node, True))
                    pending.append((node.operand, False))
                else:
                    results.append(self._emit((int(EmtNativeOpcode.NEGATE), results.pop())))
            elif node_type is Func:
                if node.op not in function_opcodes:
                    raise ValueError("Row " + str(self._row_index) + ": unsupported function " + node.op)
                elif not expanded:
                    pending.append((node, True))
                    pending.append((node.arg, False))
                else:
                    results.append(self._emit((function_opcodes[node.op], results.pop())))
            else:
                results.append(self._leaf(node))

        # The state residual closes with DIFFERENTIAL - f.
        if state_uid >= 0:
            self._emit((int(EmtNativeOpcode.SUBTRACT), differential_id, results.pop()))
        else:
            pass

    def get_structure(self) -> Tuple:
        """
        Return the slot-renamed tape structure.

        :return: Tuple of node keys in emission order.
        """
        return tuple(self._nodes)

    def get_runtime_unknowns(self) -> List[int]:
        """
        Return the unknown index of every runtime slot.

        :return: Unknown indices by runtime slot.
        """
        return self._runtime_unknowns

    def get_parameter_indices(self) -> List[int]:
        """
        Return the parameter index of every problem-parameter slot.

        :return: Parameter indices by parameter slot.
        """
        return self._parameter_indices

    def get_literal_values(self) -> List[float]:
        """
        Return the value of every literal slot.

        :return: Literal values by literal slot.
        """
        return self._literal_values


def _check_square_and_aligned(problem: EmtProblemTemplate) -> None:
    """
    Check block squareness and derivative-history alignment with the states.

    :param problem: EMT problem.
    :raises ValueError: When the blocks are not square, a state is nested or the
        derivative history is not aligned with the state order.
    """
    states: List[Var] = problem.get_state_vars()
    state_index: Dict[int, int] = dict()
    position: int
    state: Var
    for position, state in enumerate(states):
        if state.base_var is not None:
            raise ValueError("State " + state.name + " is nested (non-None base_var)")
        else:
            state_index[state.uid] = position
    if len(problem.get_state_eqs()) != len(states) or len(problem.get_algebraic_eqs()) != len(problem.get_algebraic_vars()):
        raise ValueError("The state or algebraic blocks are not square")
    elif len(problem.uid2idx_vars) != len(states) + len(problem.get_algebraic_vars()):
        raise ValueError("The unknown index does not match the state and algebraic variables")
    elif len(problem.get_diff_vars()) != len(states):
        raise ValueError("The derivative history size differs from the number of states")
    else:
        pass
    diff_index: Dict[int, int] = problem.uid2idx_diff
    derivative: Var
    for derivative in problem.get_diff_vars():
        if derivative.base_var is None or derivative.base_var.uid not in state_index:
            raise ValueError("Derivative " + derivative.name + " does not belong to a state")
        elif diff_index[derivative.uid] != state_index[derivative.base_var.uid]:
            raise ValueError("Derivative history of " + derivative.name + " is not aligned with its state")
        else:
            pass


class EmtNativeProgram:
    """
    Immutable native EMT program, validated against the GSLV structural rules.

    Instructions are ``[opcode, op1, op2, out]`` with one literal each; groups are
    ``[instruction_begin, instruction_count, lane_count, scratch_slot_count,
    runtime_map_begin, runtime_map_count, parameter_map_begin,
    parameter_map_count, residual_row_begin, output_slot]``. Runtime and
    parameter maps are slot-major, lane-minor; ``residual_map`` is group-major,
    lane-minor; the parameter vector is ``[event | constant | literal]``.
    """

    __slots__ = (
        "_model_identity",
        "_n_unknowns",
        "_n_states",
        "_n_event_parameters",
        "_n_constant_parameters",
        "_n_literal_parameters",
        "_instructions",
        "_instruction_literals",
        "_groups",
        "_runtime_map",
        "_parameter_map",
        "_residual_map",
        "_column_pointers",
        "_row_indices",
        "_literal_parameter_values",
        "_group_affinity",
        "_fingerprint",
    )

    def __init__(self,
                 model_identity: str,
                 n_unknowns: int,
                 n_states: int,
                 n_event_parameters: int,
                 n_constant_parameters: int,
                 instructions: npt.NDArray,
                 instruction_literals: npt.NDArray,
                 groups: npt.NDArray,
                 runtime_map: npt.NDArray,
                 parameter_map: npt.NDArray,
                 residual_map: npt.NDArray,
                 column_pointers: npt.NDArray,
                 row_indices: npt.NDArray,
                 literal_parameter_values: npt.NDArray,
                 group_affinity: npt.NDArray) -> None:
        """
        Validate and store one program.

        :param model_identity: Identity of the consumer model.
        :param n_unknowns: Number of unknowns (= residual rows).
        :param n_states: Number of leading state unknowns.
        :param n_event_parameters: Runtime (event) parameters at the head of the vector.
        :param n_constant_parameters: Constant parameters after the event parameters.
        :param instructions: Flat int32 instructions, 4 per instruction.
        :param instruction_literals: One float64 literal per instruction.
        :param groups: Flat int32 group descriptors, 10 per group.
        :param runtime_map: Unknown index per runtime slot and lane.
        :param parameter_map: Parameter index per parameter slot and lane.
        :param residual_map: Residual row per group lane.
        :param column_pointers: CSC column pointers (N + 1).
        :param row_indices: CSC row indices.
        :param literal_parameter_values: Program-owned literal parameters.
        :param group_affinity: ResidualRowAffinityCode of each group.
        :raises ValueError: When any GSLV structural rule does not hold.
        """
        validate_model_identity(model_identity)
        if (type(n_unknowns) is not int or type(n_states) is not int or type(n_event_parameters) is not int
                or type(n_constant_parameters) is not int):
            raise ValueError("Program counts must be int")
        elif n_unknowns <= 0 or n_states < 0 or n_states > n_unknowns or n_event_parameters < 0 or n_constant_parameters < 0:
            raise ValueError("Program counts out of range")
        else:
            pass
        int32: np.dtype = np.dtype(np.int32)
        float64: np.dtype = np.dtype(np.float64)
        self._model_identity: str = model_identity
        self._n_unknowns: int = n_unknowns
        self._n_states: int = n_states
        self._n_event_parameters: int = n_event_parameters
        self._n_constant_parameters: int = n_constant_parameters
        self._instructions: npt.NDArray[np.int32] = immutable_array(instructions, "instructions", int32)
        self._instruction_literals: npt.NDArray[np.float64] = immutable_array(instruction_literals, "instruction_literals", float64)
        self._groups: npt.NDArray[np.int32] = immutable_array(groups, "groups", int32)
        self._runtime_map: npt.NDArray[np.int32] = immutable_array(runtime_map, "runtime_map", int32)
        self._parameter_map: npt.NDArray[np.int32] = immutable_array(parameter_map, "parameter_map", int32)
        self._residual_map: npt.NDArray[np.int32] = immutable_array(residual_map, "residual_map", int32)
        self._column_pointers: npt.NDArray[np.int32] = immutable_array(column_pointers, "column_pointers", int32)
        self._row_indices: npt.NDArray[np.int32] = immutable_array(row_indices, "row_indices", int32)
        self._literal_parameter_values: npt.NDArray[np.float64] = immutable_array(literal_parameter_values, "literal_parameter_values", float64)
        self._group_affinity: npt.NDArray[np.int32] = immutable_array(group_affinity, "group_affinity", int32)
        self._n_literal_parameters: int = int(self._literal_parameter_values.shape[0])

        _validate_group_windows(self)
        _validate_maps(self)
        _validate_tapes(self)
        _validate_residual_map(self)
        _validate_pattern(self)

        # Fingerprint: per-array SHA-256 of the little-endian bytes inside canonical JSON.
        arrays: Dict[str, object] = dict()
        arrays["instructions"] = _array_digest(self._instructions)
        arrays["instruction_literals"] = _array_digest(self._instruction_literals)
        arrays["groups"] = _array_digest(self._groups)
        arrays["runtime_map"] = _array_digest(self._runtime_map)
        arrays["parameter_map"] = _array_digest(self._parameter_map)
        arrays["residual_map"] = _array_digest(self._residual_map)
        arrays["column_pointers"] = _array_digest(self._column_pointers)
        arrays["row_indices"] = _array_digest(self._row_indices)
        arrays["literal_parameter_values"] = _array_digest(self._literal_parameter_values)
        arrays["group_affinity"] = _array_digest(self._group_affinity)
        payload: Dict[str, object] = dict()
        payload["schema"] = self.get_schema()
        payload["model_identity"] = model_identity
        payload["n_unknowns"] = n_unknowns
        payload["n_states"] = n_states
        payload["n_event_parameters"] = n_event_parameters
        payload["n_constant_parameters"] = n_constant_parameters
        payload["n_literal_parameters"] = self._n_literal_parameters
        payload["arrays"] = arrays
        self._fingerprint: str = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()

    def get_schema(self) -> str:
        """
        Return the interchange schema name.

        :return: Schema name.
        """
        return "veragrid-gslv-emt-program-v1"

    def get_model_identity(self) -> str:
        """
        Return the identity of the consumer model.

        :return: Model identity.
        """
        return self._model_identity

    def get_n_unknowns(self) -> int:
        """
        Return the number of unknowns, equal to the number of residual rows.

        :return: Number of unknowns.
        """
        return self._n_unknowns

    def get_n_states(self) -> int:
        """
        Return the number of leading state unknowns.

        :return: Number of states.
        """
        return self._n_states

    def get_n_event_parameters(self) -> int:
        """
        Return the number of runtime (event) parameters at the head of the parameter vector.

        :return: Number of event parameters.
        """
        return self._n_event_parameters

    def get_n_constant_parameters(self) -> int:
        """
        Return the number of constant parameters after the event parameters.

        :return: Number of constant parameters.
        """
        return self._n_constant_parameters

    def get_n_literal_parameters(self) -> int:
        """
        Return the number of program-owned literal parameters at the tail of the parameter vector.

        :return: Number of literal parameters.
        """
        return self._n_literal_parameters

    def get_n_parameters(self) -> int:
        """
        Return the total parameter count (event + constant + literal).

        :return: Total parameter count.
        """
        return self._n_event_parameters + self._n_constant_parameters + self._n_literal_parameters

    def get_n_groups(self) -> int:
        """
        Return the number of groups (families).

        :return: Number of groups.
        """
        return int(self._groups.shape[0] // 10)

    def get_instructions(self) -> npt.NDArray[np.int32]:
        """
        Return the flat instructions, 4 int32 per instruction.

        :return: Read-only array.
        """
        return self._instructions

    def get_instruction_literals(self) -> npt.NDArray[np.float64]:
        """
        Return one literal per instruction.

        :return: Read-only array.
        """
        return self._instruction_literals

    def get_groups(self) -> npt.NDArray[np.int32]:
        """
        Return the flat group descriptors, 10 int32 per group.

        :return: Read-only array.
        """
        return self._groups

    def get_runtime_map(self) -> npt.NDArray[np.int32]:
        """
        Return the unknown index of every runtime slot and lane.

        :return: Read-only array.
        """
        return self._runtime_map

    def get_parameter_map(self) -> npt.NDArray[np.int32]:
        """
        Return the parameter index of every parameter slot and lane.

        :return: Read-only array.
        """
        return self._parameter_map

    def get_residual_map(self) -> npt.NDArray[np.int32]:
        """
        Return the residual row of every group lane.

        :return: Read-only array.
        """
        return self._residual_map

    def get_column_pointers(self) -> npt.NDArray[np.int32]:
        """
        Return the CSC column pointers.

        :return: Read-only array of N + 1 entries.
        """
        return self._column_pointers

    def get_row_indices(self) -> npt.NDArray[np.int32]:
        """
        Return the CSC row indices.

        :return: Read-only array.
        """
        return self._row_indices

    def get_literal_parameter_values(self) -> npt.NDArray[np.float64]:
        """
        Return the program-owned literal parameters.

        :return: Read-only array.
        """
        return self._literal_parameter_values

    def get_group_affinity(self) -> npt.NDArray[np.int32]:
        """
        Return the ResidualRowAffinityCode of every group.

        :return: Read-only array.
        """
        return self._group_affinity

    def get_fingerprint(self) -> str:
        """
        Return the SHA-256 fingerprint of the program.

        :return: Hex digest.
        """
        return self._fingerprint


def _validate_group_windows(program: EmtNativeProgram) -> None:
    """
    Check group descriptors: contiguous cumulative windows and positive counts.

    :param program: Program under construction.
    :raises ValueError: On any window or count violation.
    """
    groups: npt.NDArray[np.int32] = program.get_groups()
    if groups.shape[0] == 0 or groups.shape[0] % 10 != 0:
        raise ValueError("groups must hold a positive multiple of 10 entries")
    else:
        pass
    instruction_end: int = 0
    runtime_end: int = 0
    parameter_end: int = 0
    residual_end: int = 0
    group: int
    for group in range(program.get_n_groups()):
        field: List[int] = groups[10 * group:10 * group + 10].tolist()
        lane_count: int = field[2]
        if field[0] != instruction_end or field[4] != runtime_end or field[6] != parameter_end or field[8] != residual_end:
            raise ValueError("Group " + str(group) + " windows are not contiguous")
        elif field[1] <= 0 or lane_count <= 0 or field[3] <= 0:
            raise ValueError("Group " + str(group) + " counts must be positive")
        elif field[5] % lane_count != 0 or field[7] % lane_count != 0:
            raise ValueError("Group " + str(group) + " map counts must be multiples of the lane count")
        elif field[3] != field[1] or field[9] != field[1] - 1:
            raise ValueError("Group " + str(group) + " must be SSA with the last instruction as output")
        else:
            instruction_end += field[1]
            runtime_end += field[5]
            parameter_end += field[7]
            residual_end += lane_count
    if 4 * instruction_end != program.get_instructions().shape[0] or instruction_end != program.get_instruction_literals().shape[0]:
        raise ValueError("Instructions and literals do not match the group windows")
    elif runtime_end != program.get_runtime_map().shape[0] or parameter_end != program.get_parameter_map().shape[0]:
        raise ValueError("Maps do not match the group windows")
    elif residual_end != program.get_n_unknowns() or program.get_residual_map().shape[0] != residual_end:
        raise ValueError("Residual rows do not match the group windows")
    elif program.get_group_affinity().shape[0] != program.get_n_groups():
        raise ValueError("group_affinity must have one entry per group")
    else:
        pass


def _validate_maps(program: EmtNativeProgram) -> None:
    """
    Check map entries and group affinity codes against their domains.

    :param program: Program under construction.
    :raises ValueError: On any out-of-domain entry.
    """
    runtime_map: npt.NDArray[np.int32] = program.get_runtime_map()
    parameter_map: npt.NDArray[np.int32] = program.get_parameter_map()
    affinity: npt.NDArray[np.int32] = program.get_group_affinity()
    if runtime_map.size > 0 and (int(runtime_map.min()) < 0 or int(runtime_map.max()) >= program.get_n_unknowns()):
        raise ValueError("runtime_map entries must lie within [0, N)")
    elif parameter_map.size > 0 and (int(parameter_map.min()) < 0 or int(parameter_map.max()) >= program.get_n_parameters()):
        raise ValueError("parameter_map entries must lie within [0, P)")
    elif int(affinity.min()) < int(ResidualRowAffinityCode.CONSTANT) or int(affinity.max()) > int(ResidualRowAffinityCode.NONLINEAR):
        raise ValueError("group_affinity holds codes outside ResidualRowAffinityCode")
    elif not bool(np.all(np.isfinite(program.get_literal_parameter_values()))):
        raise ValueError("literal_parameter_values must be finite")
    else:
        pass


def _validate_tapes(program: EmtNativeProgram) -> None:
    """
    Check every instruction: opcode, SSA operands, sources, unused fields and literals.

    :param program: Program under construction.
    :raises ValueError: On any tape violation.
    """
    instructions: npt.NDArray[np.int32] = program.get_instructions()
    literals: npt.NDArray[np.float64] = program.get_instruction_literals()
    groups: npt.NDArray[np.int32] = program.get_groups()
    runtime_map: npt.NDArray[np.int32] = program.get_runtime_map()
    unary: Set[int] = set((int(EmtNativeOpcode.NEGATE), int(EmtNativeOpcode.SIN), int(EmtNativeOpcode.COS), int(EmtNativeOpcode.EXP),
                           int(EmtNativeOpcode.LOG), int(EmtNativeOpcode.SQRT), int(EmtNativeOpcode.ABSOLUTE), int(EmtNativeOpcode.HEAVISIDE),
                           int(EmtNativeOpcode.POWER_CONSTANT)))
    binary: Set[int] = set((int(EmtNativeOpcode.ADD), int(EmtNativeOpcode.SUBTRACT), int(EmtNativeOpcode.MULTIPLY), int(EmtNativeOpcode.DIVIDE),
                            int(EmtNativeOpcode.POWER)))
    literal_opcodes: Set[int] = set((int(EmtNativeOpcode.CONSTANT), int(EmtNativeOpcode.POWER_CONSTANT)))
    group: int
    for group in range(program.get_n_groups()):
        field: List[int] = groups[10 * group:10 * group + 10].tolist()
        lane_count: int = field[2]
        runtime_slots: int = field[5] // lane_count
        parameter_slots: int = field[7] // lane_count
        local: int
        for local in range(field[1]):
            index: int = field[0] + local
            opcode: int
            first: int
            second: int
            out: int
            opcode, first, second, out = instructions[4 * index:4 * index + 4].tolist()
            literal: float = float(literals[index])
            if out != local:
                raise ValueError("Instruction " + str(index) + " must write its own SSA slot")
            elif not np.isfinite(literal):
                raise ValueError("Instruction " + str(index) + " has a non-finite literal")
            elif opcode not in literal_opcodes and literal != 0.0:
                raise ValueError("Instruction " + str(index) + " must carry literal 0.0")
            elif opcode == int(EmtNativeOpcode.CONSTANT):
                if first != -1 or second != -1:
                    raise ValueError("Instruction " + str(index) + " must encode unused operands as -1")
                else:
                    pass
            elif opcode == int(EmtNativeOpcode.RUNTIME) or opcode == int(EmtNativeOpcode.DIFFERENTIAL):
                if first < 0 or first >= runtime_slots or second != -1:
                    raise ValueError("Instruction " + str(index) + " reads an invalid runtime slot")
                elif opcode == int(EmtNativeOpcode.DIFFERENTIAL):
                    window: npt.NDArray[np.int32] = runtime_map[field[4] + first * lane_count:field[4] + (first + 1) * lane_count]
                    if int(window.max()) >= program.get_n_states():
                        raise ValueError("Instruction " + str(index) + " differentiates a non-state unknown")
                    else:
                        pass
                else:
                    pass
            elif opcode == int(EmtNativeOpcode.PARAMETER):
                if first < 0 or first >= parameter_slots or second != -1:
                    raise ValueError("Instruction " + str(index) + " reads an invalid parameter slot")
                else:
                    pass
            elif opcode in unary:
                if first < 0 or first >= local or second != -1:
                    raise ValueError("Instruction " + str(index) + " reads an unwritten slot")
                else:
                    pass
            elif opcode in binary:
                if first < 0 or first >= local or second < 0 or second >= local:
                    raise ValueError("Instruction " + str(index) + " reads an unwritten slot")
                else:
                    pass
            else:
                raise ValueError("Instruction " + str(index) + " has an unknown opcode")


def _validate_residual_map(program: EmtNativeProgram) -> None:
    """
    Check that residual_map is a bijection onto the residual rows.

    :param program: Program under construction.
    :raises ValueError: When a row is missing or repeated.
    """
    residual_map: npt.NDArray[np.int32] = program.get_residual_map()
    if not np.array_equal(np.sort(residual_map), np.arange(program.get_n_unknowns(), dtype=np.int32)):
        raise ValueError("residual_map must be a bijection onto the residual rows")
    else:
        pass


def _program_dependencies(program: EmtNativeProgram) -> Set[Tuple[int, int]]:
    """
    Recompute the (residual row, unknown index) pairs read by every lane.

    :param program: Program under construction.
    :return: Dependency pairs.
    """
    instructions: npt.NDArray[np.int32] = program.get_instructions()
    groups: npt.NDArray[np.int32] = program.get_groups()
    runtime_map: npt.NDArray[np.int32] = program.get_runtime_map()
    residual_map: npt.NDArray[np.int32] = program.get_residual_map()
    dependencies: Set[Tuple[int, int]] = set()
    group: int
    for group in range(program.get_n_groups()):
        field: List[int] = groups[10 * group:10 * group + 10].tolist()
        lane_count: int = field[2]
        read_slots: Set[int] = set()
        local: int
        for local in range(field[1]):
            index: int = field[0] + local
            opcode: int = int(instructions[4 * index])
            if opcode == int(EmtNativeOpcode.RUNTIME) or opcode == int(EmtNativeOpcode.DIFFERENTIAL):
                read_slots.add(int(instructions[4 * index + 1]))
            else:
                pass
        lane: int
        for lane in range(lane_count):
            row: int = int(residual_map[field[8] + lane])
            slot: int
            for slot in read_slots:
                dependencies.add((row, int(runtime_map[field[4] + slot * lane_count + lane])))
    return dependencies


def _validate_pattern(program: EmtNativeProgram) -> None:
    """
    Check the CSC pattern: square, canonical, and exactly the tape dependencies.

    :param program: Program under construction.
    :raises ValueError: When the pattern is malformed or differs from the dependencies.
    """
    pointers: npt.NDArray[np.int32] = program.get_column_pointers()
    rows: npt.NDArray[np.int32] = program.get_row_indices()
    n: int = program.get_n_unknowns()
    if pointers.shape[0] != n + 1 or int(pointers[0]) != 0 or int(pointers[-1]) != rows.shape[0] or bool(np.any(np.diff(pointers) < 0)):
        raise ValueError("column_pointers are not a valid CSC pointer array")
    elif rows.size > 0 and (int(rows.min()) < 0 or int(rows.max()) >= n):
        raise ValueError("row_indices must lie within [0, N)")
    else:
        pass
    pattern: Set[Tuple[int, int]] = set()
    column: int
    for column in range(n):
        column_rows: npt.NDArray[np.int32] = rows[int(pointers[column]):int(pointers[column + 1])]
        if column_rows.size > 1 and not bool(np.all(np.diff(column_rows) > 0)):
            raise ValueError("CSC rows must be strictly increasing in every column")
        else:
            pass
        row: int
        for row in column_rows.tolist():
            pattern.add((row, column))
    if pattern != _program_dependencies(program):
        raise ValueError("The CSC pattern differs from the tape dependencies")
    else:
        pass


def compile_emt_native_program(problem: EmtProblemTemplate, model_identity: str) -> EmtNativeProgram:
    """
    Compile an initialised EMT problem into a native EMT program.

    :param problem: EMT problem.
    :param model_identity: Identity of the consumer model.
    :return: Validated native program.
    :raises ValueError: For unsupported nodes, misaligned derivative history,
        nested states or non-square blocks.
    """
    validate_model_identity(model_identity)
    _check_square_and_aligned(problem)

    # Unknown, state and parameter indexing in VeraGrid solver order.
    states: List[Var] = problem.get_state_vars()
    unknown_index: Dict[int, int] = problem.uid2idx_vars
    state_uids: Set[int] = set()
    state: Var
    for state in states:
        state_uids.add(state.uid)
    event_parameters: List[Var] = problem.get_variable_parameters()
    constant_parameters: List[Var] = problem.get_constant_parameters()
    parameter_index: Dict[int, int] = dict()
    parameter: Var
    for parameter in list(event_parameters) + list(constant_parameters):
        parameter_index[parameter.uid] = len(parameter_index)
    n_external_parameters: int = len(event_parameters) + len(constant_parameters)

    # Row affinity codes from the structural classification.
    classification: EmtResidualRowClassification = classify_emt_residual_rows(problem)
    code_of: Dict[ExpressionAffinity, int] = dict()
    affinity: ExpressionAffinity
    for affinity in ExpressionAffinity:
        code_of[affinity] = int(ResidualRowAffinityCode[affinity.name])
    row_codes: List[int] = list()
    for affinity in classification.get_row_affinities():
        row_codes.append(code_of[affinity])
    opaque: int
    for opaque in classification.get_opaque_row_indices():
        row_codes[opaque] = int(ResidualRowAffinityCode.NONLINEAR)

    # Lower every row and gather families keyed by structure, affinity and row kind.
    rows: List[object] = list(problem.get_state_eqs()) + list(problem.get_algebraic_eqs())
    families: Dict[Tuple, List[Tuple[int, _RowLowering]]] = dict()
    row_index: int
    expression: object
    for row_index, expression in enumerate(rows):
        lowering: _RowLowering = _RowLowering(row_index, unknown_index, state_uids, parameter_index)
        if row_index < len(states):
            lowering.lower(expression, states[row_index].uid)
        else:
            lowering.lower(expression, -1)
        key: Tuple = (row_index < len(states), row_codes[row_index], lowering.get_structure())
        members: List[Tuple[int, _RowLowering]] = families.get(key, list())
        members.append((row_index, lowering))
        families[key] = members

    # Emit groups in family order (smallest row first), lanes ascending by row.
    instructions: List[int] = list()
    literals: List[float] = list()
    groups: List[int] = list()
    runtime_map: List[int] = list()
    parameter_map: List[int] = list()
    residual_map: List[int] = list()
    literal_tail: List[float] = list()
    group_affinity: List[int] = list()
    dependency_rows: List[List[int]] = list()
    column_index: int
    for column_index in range(len(rows)):
        dependency_rows.append(list())
    family_key: Tuple
    lanes: List[Tuple[int, _RowLowering]]
    for family_key, lanes in families.items():
        structure: Tuple = family_key[2]
        lane_count: int = len(lanes)
        template: _RowLowering = lanes[0][1]
        runtime_slots: int = len(template.get_runtime_unknowns())
        problem_slots: int = len(template.get_parameter_indices())
        literal_slots: int = len(template.get_literal_values())

        # Literal slots: bitwise-equal values become CONSTANT literals, others PARAMETER slots.
        literal_constant: Dict[int, float] = dict()
        literal_parameter_slot: Dict[int, int] = dict()
        promoted: List[int] = list()
        literal_slot: int
        for literal_slot in range(literal_slots):
            first_bits: int = _float_bits(template.get_literal_values()[literal_slot])
            uniform: bool = True
            lane_entry: Tuple[int, _RowLowering]
            for lane_entry in lanes:
                if _float_bits(lane_entry[1].get_literal_values()[literal_slot]) != first_bits:
                    uniform = False
                else:
                    pass
            if uniform:
                literal_constant[literal_slot] = template.get_literal_values()[literal_slot]
            else:
                literal_parameter_slot[literal_slot] = problem_slots + len(promoted)
                promoted.append(literal_slot)

        # Group descriptor and SSA instructions.
        groups.extend((len(literals), len(structure), lane_count, len(structure), len(runtime_map), runtime_slots * lane_count,
                       len(parameter_map), (problem_slots + len(promoted)) * lane_count, len(residual_map), len(structure) - 1))
        local: int
        node: Tuple
        for local, node in enumerate(structure):
            if node[0] == int(EmtNativeOpcode.CONSTANT) and len(node) == 2:
                if node[1] in literal_constant:
                    instructions.extend((int(EmtNativeOpcode.CONSTANT), -1, -1, local))
                    literals.append(literal_constant[node[1]])
                else:
                    instructions.extend((int(EmtNativeOpcode.PARAMETER), literal_parameter_slot[node[1]], -1, local))
                    literals.append(0.0)
            elif node[0] == int(EmtNativeOpcode.CONSTANT):
                instructions.extend((int(EmtNativeOpcode.CONSTANT), -1, -1, local))
                literals.append(float(struct.unpack("<d", struct.pack("<Q", node[2]))[0]))
            elif node[0] == int(EmtNativeOpcode.POWER_CONSTANT):
                instructions.extend((node[0], node[1], -1, local))
                literals.append(float(struct.unpack("<d", struct.pack("<Q", node[2]))[0]))
            elif len(node) == 3:
                instructions.extend((node[0], node[1], node[2], local))
                literals.append(0.0)
            else:
                instructions.extend((node[0], node[1], -1, local))
                literals.append(0.0)

        # Slot-major, lane-minor maps; literal tail per promoted slot with lanes contiguous.
        slot: int
        for slot in range(runtime_slots):
            for lane_entry in lanes:
                runtime_map.append(lane_entry[1].get_runtime_unknowns()[slot])
        for slot in range(problem_slots):
            for lane_entry in lanes:
                parameter_map.append(lane_entry[1].get_parameter_indices()[slot])
        for literal_slot in promoted:
            for lane_entry in lanes:
                parameter_map.append(n_external_parameters + len(literal_tail))
                literal_tail.append(lane_entry[1].get_literal_values()[literal_slot])
        for lane_entry in lanes:
            residual_map.append(lane_entry[0])
            unknown: int
            for unknown in lane_entry[1].get_runtime_unknowns():
                dependency_rows[unknown].append(lane_entry[0])
        group_affinity.append(family_key[1])

    # CSC pattern: exactly the unknowns every row reads.
    column_pointers: List[int] = list((0,))
    row_indices: List[int] = list()
    for column_index in range(len(rows)):
        row_indices.extend(sorted(set(dependency_rows[column_index])))
        column_pointers.append(len(row_indices))

    return EmtNativeProgram(
        model_identity=model_identity,
        n_unknowns=len(rows),
        n_states=len(states),
        n_event_parameters=len(event_parameters),
        n_constant_parameters=len(constant_parameters),
        instructions=np.array(instructions, dtype=np.int32),
        instruction_literals=np.array(literals, dtype=np.float64),
        groups=np.array(groups, dtype=np.int32),
        runtime_map=np.array(runtime_map, dtype=np.int32),
        parameter_map=np.array(parameter_map, dtype=np.int32),
        residual_map=np.array(residual_map, dtype=np.int32),
        column_pointers=np.array(column_pointers, dtype=np.int32),
        row_indices=np.array(row_indices, dtype=np.int32),
        literal_parameter_values=np.array(literal_tail, dtype=np.float64),
        group_affinity=np.array(group_affinity, dtype=np.int32),
    )
