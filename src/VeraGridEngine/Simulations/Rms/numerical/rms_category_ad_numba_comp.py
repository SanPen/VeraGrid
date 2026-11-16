# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Reusable four-block Jacobians filled by native, per-category colored AD."""

from enum import IntEnum
from typing import Any

import numpy as np
import numba as nb
from numba.typed import List as NumbaList
from scipy.sparse import csc_matrix

from VeraGridEngine.Utils.Symbolic.jit_compiler_rms_full_vectorized_numba_comp import RmsCategoryAdCompiler, compile_category_coordinator
from VeraGridEngine.Utils.Symbolic.symbolic import Expr, Var
from VeraGridEngine.Simulations.Rms.numerical.rms_numba_compile_worker import (
    LoadedKernel, kernel_compile_job, prepare_kernel_group,
)


class RmsJacobianBlock(IntEnum):
    """Identify the four numerical output buffers used by the native kernels."""

    STATE_STATE = 0
    STATE_ALGEBRAIC = 1
    ALGEBRAIC_STATE = 2
    ALGEBRAIC_ALGEBRAIC = 3


class CategoryRowTarget:
    """Describe one device equation or signed terminal contribution to a global row."""

    __slots__ = ("local_row", "instance", "global_row", "weight")

    def __init__(self, local_row: int, instance: int, global_row: int, weight: float) -> None:
        """Record a setup-time destination, allowing several terminals per nodal row.

        :param local_row: Representative equation or auxiliary terminal row.
        :param instance: Equivalent device column.
        :param global_row: State-then-algebraic residual row.
        :param weight: Signed nodal multiplier or one for an internal equation.
        :return: None.
        """
        self.local_row: int = local_row
        self.instance: int = instance
        self.global_row: int = global_row
        self.weight: float = weight


class CategoryAdSpec:
    """Hold the finalized symbolic and global bindings of one model category."""

    __slots__ = ("uid", "equations", "variables", "derivatives", "runtime", "constants",
                 "variable_indices", "targets")

    def __init__(self, uid: int, equations: list[Expr], variables: list[Var],
                 derivatives: list[Var], runtime: list[Var], constants: list[Var],
                 variable_indices: np.ndarray, targets: list[CategoryRowTarget]) -> None:
        """Capture an immutable-size category plan after FullVec preparation.

        :param uid: Existing equivalence-class identifier.
        :param equations: Differential, device and terminal output expressions.
        :param variables: Inputs ordered exactly like the existing gather matrix.
        :param derivatives: Existing local derivative slots.
        :param runtime: Existing local runtime parameter slots.
        :param constants: Existing local constant parameter slots.
        :param variable_indices: Local-variable/instance to global-column map.
        :param targets: Internal and nodal equation destinations.
        :return: None.
        """
        self.uid: int = uid
        self.equations: list[Expr] = equations
        self.variables: list[Var] = variables
        self.derivatives: list[Var] = derivatives
        self.runtime: list[Var] = runtime
        self.constants: list[Var] = constants
        self.variable_indices: np.ndarray = variable_indices
        self.targets: list[CategoryRowTarget] = targets


def split_jacobian_coordinate(row: int, column: int, state_count: int) -> tuple[RmsJacobianBlock, int, int]:
    """Classify a global derivative using global rather than local variable roles.

    :param row: State-then-algebraic equation row.
    :param column: State-then-algebraic variable column.
    :param state_count: Differential state count.
    :return: Block identifier and block-local row/column.
    """
    if row < state_count:
        if column < state_count:
            return RmsJacobianBlock.STATE_STATE, row, column
        else:
            return RmsJacobianBlock.STATE_ALGEBRAIC, row, column - state_count
    else:
        if column < state_count:
            return RmsJacobianBlock.ALGEBRAIC_STATE, row - state_count, column
        else:
            return RmsJacobianBlock.ALGEBRAIC_ALGEBRAIC, row - state_count, column - state_count


class CategoryContribution:
    """One local derivative's signed destination, resolved before integration."""

    __slots__ = ("color", "instance", "source_row", "block", "row", "column", "weight")

    def __init__(self, color: int, instance: int, source_row: int, block: RmsJacobianBlock,
                 row: int, column: int, weight: float) -> None:
        """Record a contribution without retaining any runtime expression traversal.

        :param color: Local directional sweep.
        :param instance: Device column.
        :param source_row: JVP output row.
        :param block: Destination block.
        :param row: Destination block-local row.
        :param column: Destination block-local column.
        :param weight: Accumulation multiplier.
        :return: None.
        """
        self.color: int = color
        self.instance: int = instance
        self.source_row: int = source_row
        self.block: RmsJacobianBlock = block
        self.row: int = row
        self.column: int = column
        self.weight: float = weight


class CategoryAdPlan:
    """Own a category kernel, fixed work buffers and final CSC scatter positions."""

    __slots__ = ("spec", "compiler", "contributions", "pointers", "rows", "blocks",
                 "positions", "weights", "work", "empty", "rhs_pointers", "rhs_rows",
                 "rhs_positions", "rhs_weights")

    def __init__(self, spec: CategoryAdSpec, state_count: int) -> None:
        """Compile the representative and discover all global derivative destinations.

        :param spec: Finalized category bindings.
        :param state_count: Global differential state count.
        :return: None.
        """
        self.spec: CategoryAdSpec = spec
        self.compiler: RmsCategoryAdCompiler = RmsCategoryAdCompiler(
            spec.equations, spec.variables, spec.derivatives, spec.runtime, spec.constants,
        )
        target_lookup: dict[tuple[int, int], list[CategoryRowTarget]] = dict()
        target: CategoryRowTarget
        for target in spec.targets:
            key: tuple[int, int] = (target.local_row, target.instance)
            matches: list[CategoryRowTarget] | None = target_lookup.get(key, None)
            if matches is None:
                matches = list()
                target_lookup[key] = matches
            else:
                pass
            matches.append(target)
        self.contributions: list[CategoryContribution] = list()
        instance_count: int = spec.variable_indices.shape[1]
        color_count: int = self.compiler.seeds.shape[0]
        self.pointers: np.ndarray = np.zeros((color_count, instance_count + 1), dtype=np.int64)
        color: int
        instance: int
        entry: int
        # Group contributions exactly in the order consumed by the native loops.
        for color in range(color_count):
            for instance in range(instance_count):
                self.pointers[color, instance] = len(self.contributions)
                for entry in range(self.compiler.rows.size):
                    column: int = int(self.compiler.columns[entry])
                    if self.compiler.colors[column] == color:
                        source_row: int = int(self.compiler.rows[entry])
                        destinations: list[CategoryRowTarget] | None = target_lookup.get((source_row, instance), None)
                        if destinations is not None:
                            for target in destinations:
                                block: RmsJacobianBlock
                                row: int
                                block_column: int
                                block, row, block_column = split_jacobian_coordinate(
                                    target.global_row, int(spec.variable_indices[column, instance]), state_count,
                                )
                                self.contributions.append(CategoryContribution(
                                    color, instance, source_row, block, row, block_column, target.weight,
                                ))
                        else:
                            pass
                    else:
                        pass
            self.pointers[color, instance_count] = len(self.contributions)
        count: int = len(self.contributions)
        self.rows: np.ndarray = np.empty(count, dtype=np.int64)
        self.blocks: np.ndarray = np.empty(count, dtype=np.int8)
        self.positions: np.ndarray = np.empty(count, dtype=np.int64)
        self.weights: np.ndarray = np.empty(count, dtype=np.float64)
        self.work: np.ndarray = np.empty(len(spec.equations), dtype=np.float64)
        self.empty: np.ndarray = np.empty((0, instance_count), dtype=np.float64)
        # Values need one instance pass, independent of the derivative colors.
        target_count: int = len(spec.targets)
        self.rhs_pointers: np.ndarray = np.empty(instance_count + 1, dtype=np.int64)
        self.rhs_rows: np.ndarray = np.empty(target_count, dtype=np.int64)
        self.rhs_positions: np.ndarray = np.empty(target_count, dtype=np.int64)
        self.rhs_weights: np.ndarray = np.empty(target_count, dtype=np.float64)
        target_index: int = 0
        for instance in range(instance_count):
            self.rhs_pointers[instance] = target_index
            for target in spec.targets:
                if target.instance == instance:
                    self.rhs_rows[target_index] = target.local_row
                    self.rhs_positions[target_index] = target.global_row
                    self.rhs_weights[target_index] = target.weight
                    target_index += 1
                else:
                    pass
        self.rhs_pointers[instance_count] = target_index

    def bind_positions(self, lookups: list[dict[tuple[int, int], int]]) -> None:
        """Freeze the CSC positions after all categories have contributed their patterns.

        :param lookups: Coordinate lookup for each output block.
        :return: None.
        """
        index: int
        contribution: CategoryContribution
        for index, contribution in enumerate(self.contributions):
            self.rows[index] = contribution.source_row
            self.blocks[index] = int(contribution.block)
            self.positions[index] = lookups[contribution.block][(contribution.row, contribution.column)]
            self.weights[index] = contribution.weight

    def evaluate(self, inputs: list[np.ndarray], h: float, blocks: tuple[csc_matrix, ...]) -> None:
        """Execute all colors and instances with a single native call.

        :param inputs: Existing FullVec variable/derivative/parameter gather matrices.
        :param h: Effective Backward Euler step.
        :param blocks: Four reusable output matrices.
        :return: None.
        """
        # Existing FullVec uses one-dimensional placeholders for unused inputs.
        derivatives: np.ndarray = inputs[1] if inputs[1].ndim == 2 else self.empty
        runtime: np.ndarray = inputs[2] if inputs[2].ndim == 2 else self.empty
        constants: np.ndarray = inputs[3] if inputs[3].ndim == 2 else self.empty
        self.compiler.kernel(
            inputs[0], derivatives, runtime, constants, h, self.compiler.seeds,
            self.pointers, self.rows, self.blocks, self.positions, self.weights, self.work,
            blocks[0].data, blocks[1].data, blocks[2].data, blocks[3].data,
        )


    def evaluate_rhs(self, inputs: list[np.ndarray], h: float, output: np.ndarray) -> None:
        """Evaluate all instances and accumulate their equations without Python terminal loops.

        :param inputs: Existing gathered variables, derivatives and parameters.
        :param h: Effective local step.
        :param output: Global state-then-algebraic equation accumulator.
        :return: None.
        """
        derivatives: np.ndarray = inputs[1] if inputs[1].ndim == 2 else self.empty
        runtime: np.ndarray = inputs[2] if inputs[2].ndim == 2 else self.empty
        constants: np.ndarray = inputs[3] if inputs[3].ndim == 2 else self.empty
        # The local work vector is overwritten completely by both value and AD kernels.
        self.compiler.residual_kernel(
            inputs[0], derivatives, runtime, constants, h, self.rhs_pointers,
            self.rhs_rows, self.rhs_positions, self.rhs_weights, self.work, output,
        )


@nb.njit(cache=True, fastmath=False, error_model="numpy")
def add_direct_nodal_values(values: np.ndarray, rows: np.ndarray, columns: np.ndarray,
                            weights: np.ndarray, output: np.ndarray) -> None:
    """Add direct nodal variables after the signed terminal contributions.

    :param values: Candidate global variables.
    :param rows: Global nodal equation destinations.
    :param columns: Direct global variable sources.
    :param weights: Signed multipliers, including capacitive DC terms.
    :param output: Global equation buffer receiving the contributions.
    :return: None.
    """
    index: int
    for index in range(rows.size):
        output[rows[index]] += weights[index] * values[columns[index]]


@nb.njit(cache=True, fastmath=False, error_model="numpy")
def form_backward_euler_residual(values: np.ndarray, previous: np.ndarray,
                                 equations: np.ndarray, state_count: int,
                                 h: float, output: np.ndarray) -> None:
    """Discretize state equations and copy algebraic rows into a persistent output.

    :param values: Current global candidate.
    :param previous: Previous accepted global vector.
    :param equations: Raw differential right-hand sides and algebraic equations.
    :param state_count: Number of differential rows.
    :param h: Effective local step.
    :param output: Borrowed implicit residual destination.
    :return: None.
    """
    index: int
    for index in range(state_count):
        output[index] = values[index] - previous[index] - h * equations[index]
    for index in range(state_count, equations.size):
        output[index] = equations[index]


@nb.njit(cache=True)
def fill_newton_values(j11: np.ndarray, j12: np.ndarray, j21: np.ndarray, j22: np.ndarray,
                       positions: np.ndarray, offsets: np.ndarray, diagonal: np.ndarray,
                       h: float, output: np.ndarray) -> None:
    """Write the Backward Euler matrix without allocating sparse intermediates.

    :param j11: State/state derivatives.
    :param j12: State/algebraic derivatives.
    :param j21: Algebraic/state derivatives.
    :param j22: Algebraic/algebraic derivatives.
    :param positions: Block entries mapped to global CSC data slots.
    :param offsets: Boundaries of the four position maps.
    :param diagonal: All state diagonal slots, including structurally absent derivatives.
    :param h: Current effective integration step.
    :param output: Persistent global CSC data.
    :return: None.
    """
    # Clear also structural entries whose numerical contribution currently vanishes.
    output[:] = 0.0
    index: int
    for index in range(j11.size):
        output[positions[offsets[0] + index]] = -h * j11[index]
    for index in range(j12.size):
        output[positions[offsets[1] + index]] = -h * j12[index]
    for index in range(j21.size):
        output[positions[offsets[2] + index]] = j21[index]
    for index in range(j22.size):
        output[positions[offsets[3] + index]] = j22[index]
    # Add the identity after derivatives so an existing diagonal is preserved.
    for index in range(diagonal.size):
        output[diagonal[index]] += 1.0


@nb.njit(cache=True, fastmath=False, error_model="numpy")
def coordinate_category_jacobian(kernels: Any, categories: Any, blocks: tuple[np.ndarray, ...],
                                 fixed_blocks: np.ndarray, fixed_positions: np.ndarray,
                                 fixed_weights: np.ndarray, h: float, assemble: bool,
                                 positions: np.ndarray, offsets: np.ndarray,
                                 diagonal: np.ndarray, output: np.ndarray) -> None:
    """Evaluate all categories and optionally assemble Newton in one native entry.

    :param kernels: Opaque native functions in category order.
    :param categories: Bound input matrices, seeds, scatter maps and scratch.
    :param blocks: Four persistent Jacobian numeric arrays.
    :param fixed_blocks: Block index of direct nodal contributions.
    :param fixed_positions: Corresponding block-local CSC positions.
    :param fixed_weights: Direct derivative values.
    :param h: Effective integration step.
    :param assemble: Whether to refresh the final Newton matrix too.
    :param positions: Global CSC destination of each block entry.
    :param offsets: Boundaries in the destination array.
    :param diagonal: Global differential identity positions.
    :param output: Persistent final Newton numeric storage.
    :return: None.
    """
    # Reset before accumulating: multiple categories can share one nodal row.
    block: int
    entry: int
    category: int
    for block in range(len(blocks)):
        blocks[block][:] = 0.0
    for entry in range(fixed_weights.size):
        blocks[fixed_blocks[entry]][fixed_positions[entry]] += fixed_weights[entry]
    for category in range(len(kernels)):
        data: Any = categories[category]
        kernels[category](data[0], data[1], data[2], data[3], h, data[4], data[5],
                          data[6], data[7], data[8], data[9], data[10],
                          blocks[0], blocks[1], blocks[2], blocks[3])
    if assemble:
        fill_newton_values(blocks[0], blocks[1], blocks[2], blocks[3],
                           positions, offsets, diagonal, h, output)
    else:
        pass


class NewtonCscAssembler:
    """Keep a fixed global CSC pattern and mappings from the category blocks."""

    __slots__ = ("_matrix", "_positions", "_offsets", "_diagonal")

    def __init__(self, blocks: tuple[csc_matrix, ...], state_count: int) -> None:
        """Reserve all block coordinates and differential identity entries once.

        :param blocks: Canonical, fixed-pattern derivative blocks.
        :param state_count: Number of differential variables.
        :return: None.
        """
        # Build the union once, retaining explicit structural zeros for future steps.
        size: int = state_count + blocks[3].shape[0]
        coordinates: set[tuple[int, int]] = set()
        row_offsets: tuple[int, ...] = (0, 0, state_count, state_count)
        column_offsets: tuple[int, ...] = (0, state_count, 0, state_count)
        block_index: int
        column: int
        entry: int
        row: int
        block: csc_matrix
        for block_index, block in enumerate(blocks):
            for column in range(block.shape[1]):
                for entry in range(block.indptr[column], block.indptr[column + 1]):
                    coordinates.add((column + column_offsets[block_index],
                                     int(block.indices[entry]) + row_offsets[block_index]))
        for row in range(state_count):
            coordinates.add((row, row))
        ordered: list[tuple[int, int]] = sorted(coordinates)
        indices: np.ndarray = np.empty(len(ordered), dtype=np.int32)
        indptr: np.ndarray = np.zeros(size + 1, dtype=np.int32)
        lookup: dict[tuple[int, int], int] = dict()
        for entry, (column, row) in enumerate(ordered):
            indices[entry] = row
            indptr[column + 1] += 1
            lookup[(column, row)] = entry
        np.cumsum(indptr, out=indptr)
        self._matrix: csc_matrix = csc_matrix(
            (np.zeros(len(ordered), dtype=np.float64), indices, indptr), shape=(size, size))
        # Resolve every scatter address before Newton iterations begin.
        self._offsets: np.ndarray = np.zeros(5, dtype=np.int64)
        for block_index, block in enumerate(blocks):
            self._offsets[block_index + 1] = self._offsets[block_index] + block.nnz
        self._positions: np.ndarray = np.empty(int(self._offsets[-1]), dtype=np.int64)
        self._diagonal: np.ndarray = np.empty(state_count, dtype=np.int64)
        for block_index, block in enumerate(blocks):
            for column in range(block.shape[1]):
                for entry in range(block.indptr[column], block.indptr[column + 1]):
                    self._positions[self._offsets[block_index] + entry] = lookup[
                        (column + column_offsets[block_index],
                         int(block.indices[entry]) + row_offsets[block_index])]
        for row in range(state_count):
            self._diagonal[row] = lookup[(row, row)]
        # Warm the native fill at preparation time, outside the simulation loop.
        fill_newton_values(blocks[0].data, blocks[1].data, blocks[2].data, blocks[3].data,
                           self._positions, self._offsets, self._diagonal, 0.0, self._matrix.data)

    def evaluate(self, blocks: tuple[csc_matrix, ...], h: float) -> csc_matrix:
        """Refresh values while preserving the matrix object and all CSC storage.

        :param blocks: Updated category derivative blocks with the prepared patterns.
        :param h: Effective integration step.
        :return: Borrowed global Newton matrix, overwritten on the next evaluation.
        """
        fill_newton_values(blocks[0].data, blocks[1].data, blocks[2].data, blocks[3].data,
                           self._positions, self._offsets, self._diagonal, h, self._matrix.data)
        return self._matrix


class FullVecCategoryAdJacobian:
    """Own native category equations and their four persistent CSC derivative blocks."""

    __slots__ = ("_plans", "_blocks", "_fixed", "_evaluation_count", "_raw_rhs", "_state_rhs",
                 "_algebraic_rhs", "_implicit_residual", "_state_count", "_rhs_evaluation_count",
                 "_fixed_rows", "_fixed_columns", "_fixed_weights", "_newton_assembler",
                 "_coordinator", "_category_inputs", "_runtime_dirty", "_constant_rhs",
                 "_jacobian_coordinator", "_jacobian_kernels", "_jacobian_inputs", "_jacobian_owner",
                 "_jacobian_fixed", "_jacobian_compile_seconds")

    def __init__(self, specifications: list[CategoryAdSpec], state_count: int,
                 algebraic_count: int, fixed_entries: list[tuple[int, int, float]],
                 constant_entries: list[tuple[int, float]] | None = None) -> None:
        """Reserve canonical patterns including duplicate nodal contributions.

        :param specifications: Structural categories to compile.
        :param state_count: Global differential state count.
        :param algebraic_count: Global algebraic variable/equation count.
        :param fixed_entries: Direct nodal terms, such as a capacitive DC power variable.
        :param constant_entries: Constant residual offsets, including fixed-voltage targets.
        :return: None.
        """
        self._plans: list[CategoryAdPlan] = list(CategoryAdPlan(spec, state_count) for spec in specifications)
        self._coordinator: Any = None
        self._category_inputs: tuple[tuple[np.ndarray, ...], ...] = tuple()
        self._runtime_dirty: bool = True
        self._evaluation_count: int = 0
        self._rhs_evaluation_count: int = 0
        self._state_count: int = state_count
        self._raw_rhs: np.ndarray = np.empty(state_count + algebraic_count, dtype=np.float64)
        # Constant offsets share the fixed global row layout and survive every reset.
        self._constant_rhs: np.ndarray = np.zeros(state_count + algebraic_count, dtype=np.float64)
        if constant_entries is not None:
            constant_row: int
            offset: float
            for constant_row, offset in constant_entries:
                self._constant_rhs[constant_row] += offset
        else:
            pass
        self._state_rhs: np.ndarray = np.empty(state_count, dtype=np.float64)
        self._algebraic_rhs: np.ndarray = np.empty(algebraic_count, dtype=np.float64)
        self._implicit_residual: np.ndarray = np.empty(state_count + algebraic_count, dtype=np.float64)
        self._fixed_rows: np.ndarray = np.empty(len(fixed_entries), dtype=np.int64)
        self._fixed_columns: np.ndarray = np.empty(len(fixed_entries), dtype=np.int64)
        self._fixed_weights: np.ndarray = np.empty(len(fixed_entries), dtype=np.float64)
        row: int
        column: int
        weight: float
        fixed_index: int
        for fixed_index, (row, column, weight) in enumerate(fixed_entries):
            self._fixed_rows[fixed_index] = row
            self._fixed_columns[fixed_index] = column
            self._fixed_weights[fixed_index] = weight
        coordinates: list[set[tuple[int, int]]] = list(set() for _ in range(4))
        plan: CategoryAdPlan
        contribution: CategoryContribution
        for plan in self._plans:
            for contribution in plan.contributions:
                coordinates[contribution.block].add((contribution.row, contribution.column))
        fixed_coordinates: list[tuple[RmsJacobianBlock, int, int, float]] = list()
        for row, column, weight in fixed_entries:
            block: RmsJacobianBlock
            local_row: int
            local_column: int
            block, local_row, local_column = split_jacobian_coordinate(row, column, state_count)
            coordinates[block].add((local_row, local_column))
            fixed_coordinates.append((block, local_row, local_column, weight))
        shapes: tuple[tuple[int, int], ...] = (
            (state_count, state_count), (state_count, algebraic_count),
            (algebraic_count, state_count), (algebraic_count, algebraic_count),
        )
        matrices: list[csc_matrix] = list()
        lookups: list[dict[tuple[int, int], int]] = list()
        block_index: int
        for block_index in range(4):
            # Sorting column-first creates one canonical slot for all contributions to a coordinate.
            ordered: list[tuple[int, int]] = sorted((column, row) for row, column in coordinates[block_index])
            indices: np.ndarray = np.empty(len(ordered), dtype=np.int32)
            indptr: np.ndarray = np.zeros(shapes[block_index][1] + 1, dtype=np.int32)
            lookup: dict[tuple[int, int], int] = dict()
            index: int
            for index, (column, row) in enumerate(ordered):
                indices[index] = row
                indptr[column + 1] += 1
                lookup[(row, column)] = index
            np.cumsum(indptr, out=indptr)
            matrices.append(csc_matrix((np.zeros(len(ordered)), indices, indptr), shape=shapes[block_index]))
            lookups.append(lookup)
        self._blocks: tuple[csc_matrix, ...] = tuple(matrices)
        self._newton_assembler: NewtonCscAssembler = NewtonCscAssembler(self._blocks, state_count)
        for plan in self._plans:
            plan.bind_positions(lookups)
        self._fixed: list[tuple[RmsJacobianBlock, int, float]] = list(
            (block, lookups[block][(row, column)], weight)
            for block, row, column, weight in fixed_coordinates
        )
        # Typed lists keep function addresses and heterogeneous-shaped matrices
        # in native memory. The coordinator ABI does not grow with category count.
        vector: Any = nb.float64[::1]
        matrix_type: Any = nb.float64[:, ::1]
        integers: Any = nb.int64[::1]
        kernel_signature: Any = nb.void(
            matrix_type, matrix_type, matrix_type, matrix_type, nb.float64,
            matrix_type, nb.int64[:, ::1], integers, nb.int8[::1], integers,
            vector, vector, vector, vector, vector, vector,
        )
        record_type: Any = nb.types.Tuple((matrix_type, matrix_type, matrix_type, matrix_type,
                                          matrix_type, nb.int64[:, ::1], integers,
                                          nb.int8[::1], integers, vector, vector))
        self._jacobian_kernels: Any = NumbaList.empty_list(nb.types.FunctionType(kernel_signature))
        self._jacobian_inputs: Any = NumbaList.empty_list(record_type)
        self._jacobian_owner: dict[int, list[np.ndarray]] | None = None
        for plan in self._plans:
            self._jacobian_kernels.append(plan.compiler.kernel)
        self._jacobian_fixed: tuple[np.ndarray, ...] = (
            np.array([int(item[0]) for item in self._fixed], dtype=np.int8),
            np.array([item[1] for item in self._fixed], dtype=np.int64),
            np.array([item[2] for item in self._fixed], dtype=np.float64),
        )
        loaded: tuple[LoadedKernel, ...] = prepare_kernel_group((kernel_compile_job(
            coordinate_category_jacobian, nb.void(
                nb.typeof(self._jacobian_kernels), nb.typeof(self._jacobian_inputs),
                nb.types.UniTuple(vector, 4), nb.int8[::1], integers, vector, nb.float64,
                nb.boolean, integers, integers, integers, vector,
            )),))
        self._jacobian_coordinator: Any = loaded[0].dispatcher
        self._jacobian_compile_seconds: float = loaded[0].compile_seconds

    def _bind_jacobian_inputs(self, inputs_by_category: dict[int, list[np.ndarray]]) -> None:
        """Bind persistent inputs outside the repeated numerical evaluation loop.

        :param inputs_by_category: Stable input matrices for each category.
        :return: None.
        """
        self._jacobian_inputs.clear()
        plan: CategoryAdPlan
        for plan in self._plans:
            inputs: list[np.ndarray] = inputs_by_category[plan.spec.uid]
            derivatives: np.ndarray = inputs[1] if inputs[1].ndim == 2 else plan.empty
            runtime: np.ndarray = inputs[2] if inputs[2].ndim == 2 else plan.empty
            constants: np.ndarray = inputs[3] if inputs[3].ndim == 2 else plan.empty
            self._jacobian_inputs.append((inputs[0], derivatives, runtime, constants,
                                          plan.compiler.seeds, plan.pointers, plan.rows,
                                          plan.blocks, plan.positions, plan.weights, plan.work))
        self._jacobian_owner = inputs_by_category

    def _evaluate_native_jacobian(self, h: float, assemble: bool) -> None:
        """Dispatch categories and assembly through one cache-loaded native call.

        :param h: Effective integration step.
        :param assemble: Whether to fill the final Newton CSC values.
        :return: None.
        """
        self._jacobian_coordinator(
            self._jacobian_kernels, self._jacobian_inputs,
            (self._blocks[0].data, self._blocks[1].data, self._blocks[2].data, self._blocks[3].data),
            self._jacobian_fixed[0], self._jacobian_fixed[1], self._jacobian_fixed[2], h, assemble,
            self._newton_assembler._positions, self._newton_assembler._offsets,
            self._newton_assembler._diagonal, self._newton_assembler._matrix.data,
        )
        self._evaluation_count += 1

    def get_worker_compile_seconds(self) -> float:
        """Report actual coordinator compilation time spent in the auxiliary.

        :return: Numba compilation seconds, excluding cache loading.
        """
        seconds: float = self._jacobian_compile_seconds
        return seconds

    def prepare_category_inputs(self, inputs_by_category: dict[int, list[np.ndarray]],
                                derivative_indices: dict[int, np.ndarray],
                                runtime_indices: dict[int, np.ndarray],
                                constant_indices: dict[int, np.ndarray],
                                constants: np.ndarray, values: np.ndarray,
                                derivatives: np.ndarray, runtime: np.ndarray) -> None:
        """Bind fixed buffers and copy immutable parameters before integration.

        :param inputs_by_category: Existing category input interface.
        :param derivative_indices: Category derivative gather maps.
        :param runtime_indices: Category variable parameter gather maps.
        :param constant_indices: Category constant parameter gather maps.
        :param constants: Global constant parameters.
        :param values: Initial global variables.
        :param derivatives: Initial derivative values.
        :param runtime: Current runtime parameters.
        :return: None.
        """
        records: list[tuple[np.ndarray, ...]] = list()
        plan: CategoryAdPlan
        for plan in self._plans:
            uid: int = plan.spec.uid
            instances: int = plan.spec.variable_indices.shape[1]
            empty_indices: np.ndarray = np.empty((0, instances), dtype=np.int64)
            dx_indices: np.ndarray = derivative_indices.get(uid, empty_indices)
            vp_indices: np.ndarray = runtime_indices.get(uid, empty_indices)
            cp_indices: np.ndarray = constant_indices.get(uid, empty_indices)
            buffers: list[np.ndarray] = list((
                np.empty(plan.spec.variable_indices.shape),
                np.empty(dx_indices.shape), np.empty(vp_indices.shape),
                np.empty(cp_indices.shape),
            ))
            # Advanced indexing is used only during preparation for constants.
            buffers[3][:] = constants[cp_indices]
            inputs_by_category[uid] = buffers
            records.append((buffers[0], buffers[1], buffers[2], buffers[3],
                            plan.spec.variable_indices, dx_indices, vp_indices,
                            plan.rhs_pointers, plan.rhs_rows, plan.rhs_positions,
                            plan.rhs_weights, plan.work))
        self._category_inputs = tuple(records)
        self._bind_jacobian_inputs(inputs_by_category)
        kernels: tuple[Any, ...] = tuple(plan.compiler.residual_kernel for plan in self._plans)
        self._coordinator = compile_category_coordinator(kernels)
        # Specialize the coordinator and initialize every input outside profiling.
        self.gather_inputs(values, derivatives, runtime)

    def invalidate_runtime_parameters(self) -> None:
        """Refresh gathered runtime parameters on the next native call.

        :return: None.
        """
        # Boundary updates can change parameters without advancing simulation time.
        self._runtime_dirty = True

    def gather_inputs(self, values: np.ndarray, derivatives: np.ndarray,
                      runtime: np.ndarray) -> None:
        """Refresh variable inputs in place, retaining prepared constant matrices.

        :param values: Candidate variables.
        :param derivatives: Candidate derivatives.
        :param runtime: Current global runtime parameters.
        :return: None.
        """
        self._coordinator(values, derivatives, values, 1.0, self._category_inputs, runtime,
                          self._raw_rhs, self._implicit_residual, self._fixed_rows,
                          self._fixed_columns, self._fixed_weights, self._constant_rhs, self._state_count,
                          self._runtime_dirty, True, False, False)
        self._runtime_dirty = False

    def evaluate_coordinated_residual(self, values: np.ndarray, derivatives: np.ndarray,
                                      previous: np.ndarray, runtime: np.ndarray, h: float,
                                      reuse_gather: bool = False) -> np.ndarray:
        """Gather and evaluate all categories through one Python-to-Numba call.

        :param values: Candidate global variables.
        :param derivatives: Candidate derivatives.
        :param previous: Previous accepted variables.
        :param runtime: Current global runtime parameters.
        :param h: Effective step size.
        :param reuse_gather: Whether candidate inputs have already been gathered.
        :return: Borrowed Backward Euler residual.
        """
        self._coordinator(values, derivatives, previous, h, self._category_inputs, runtime,
                          self._raw_rhs, self._implicit_residual, self._fixed_rows,
                          self._fixed_columns, self._fixed_weights, self._constant_rhs, self._state_count,
                          self._runtime_dirty, not reuse_gather, True, True)
        self._runtime_dirty = False
        self._rhs_evaluation_count += 1
        return self._implicit_residual

    def evaluate(self, inputs_by_category: dict[int, list[np.ndarray]], h: float) -> tuple[csc_matrix, ...]:
        """Recompute all four blocks without rebuilding any matrix or scatter map.

        :param inputs_by_category: Current FullVec gathered inputs.
        :param h: Effective local time step.
        :return: Borrowed J11/J12/J21/J22 matrices.
        """
        # Standalone diagnostic callers may replace their input matrices. The
        # prepared simulation path binds once in prepare_category_inputs.
        if self._coordinator is None or inputs_by_category is not self._jacobian_owner:
            self._bind_jacobian_inputs(inputs_by_category)
        else:
            pass
        self._evaluate_native_jacobian(h, False)
        return self._blocks

    def evaluate_newton(self, inputs_by_category: dict[int, list[np.ndarray]], h: float) -> csc_matrix:
        """Evaluate category derivatives once and refill the fixed Newton matrix.

        :param inputs_by_category: Gathered inputs for every model category.
        :param h: Effective integration step.
        :return: Borrowed global CSC matrix.
        """
        if self._coordinator is None or inputs_by_category is not self._jacobian_owner:
            self._bind_jacobian_inputs(inputs_by_category)
        else:
            pass
        self._evaluate_native_jacobian(h, True)
        return self._newton_assembler._matrix

    def get_evaluation_count(self) -> int:
        """Report joint evaluations, independently of the number of block getters.

        :return: Number of completed four-block evaluations.
        """
        count: int = self._evaluation_count
        return count

    def _evaluate_category_equations(self, inputs_by_category: dict[int, list[np.ndarray]], h: float) -> None:
        """Clear and refill the raw global equations with one native call per category.

        :param inputs_by_category: Current FullVec gathered inputs.
        :param h: Effective local step.
        :return: None.
        """
        self._raw_rhs[:] = self._constant_rhs
        plan: CategoryAdPlan
        for plan in self._plans:
            inputs: list[np.ndarray] | None = inputs_by_category.get(plan.spec.uid, None)
            if inputs is None:
                raise ValueError("A compiled RMS category has no residual input matrices")
            else:
                plan.evaluate_rhs(inputs, h, self._raw_rhs)
        self._rhs_evaluation_count += 1

    def evaluate_rhs(self, inputs_by_category: dict[int, list[np.ndarray]], values: np.ndarray,
                     h: float) -> np.ndarray:
        """Evaluate the undiscretized global equations, including direct nodal variables.

        :param inputs_by_category: Current category inputs.
        :param values: Candidate global variables.
        :param h: Effective local step.
        :return: Borrowed raw differential/algebraic equation buffer.
        """
        self._evaluate_category_equations(inputs_by_category, h)
        add_direct_nodal_values(values, self._fixed_rows, self._fixed_columns, self._fixed_weights, self._raw_rhs)
        return self._raw_rhs

    def evaluate_state_rhs(self, inputs_by_category: dict[int, list[np.ndarray]], h: float) -> np.ndarray:
        """Expose differential values without invalidating borrowed algebraic outputs.

        :param inputs_by_category: Current category inputs.
        :param h: Effective local step.
        :return: Borrowed differential right-hand-side buffer.
        """
        self._evaluate_category_equations(inputs_by_category, h)
        self._state_rhs[:] = self._raw_rhs[:self._state_count]
        return self._state_rhs

    def evaluate_algebraic_rhs(self, inputs_by_category: dict[int, list[np.ndarray]],
                               values: np.ndarray, h: float) -> np.ndarray:
        """Expose algebraic values to the shared initial projection interface.

        :param inputs_by_category: Current category inputs.
        :param values: Projection candidate in global variable order.
        :param h: Effective local step.
        :return: Borrowed algebraic buffer, independent of state and implicit outputs.
        """
        equations: np.ndarray = self.evaluate_rhs(inputs_by_category, values, h)
        self._algebraic_rhs[:] = equations[self._state_count:]
        return self._algebraic_rhs

    def evaluate_residual(self, inputs_by_category: dict[int, list[np.ndarray]], values: np.ndarray,
                          previous: np.ndarray, h: float) -> np.ndarray:
        """Form the complete Backward Euler residual without temporary global arrays.

        :param inputs_by_category: Current category inputs.
        :param values: Current global candidate.
        :param previous: Previous accepted state and algebraic vector.
        :param h: Effective local step.
        :return: Borrowed implicit residual, separate from raw and projection outputs.
        """
        equations: np.ndarray = self.evaluate_rhs(inputs_by_category, values, h)
        form_backward_euler_residual(values, previous, equations, self._state_count, h, self._implicit_residual)
        return self._implicit_residual

    def get_rhs_evaluation_count(self) -> int:
        """Report native value passes independently of derivative sweeps.

        :return: Number of completed category equation evaluations.
        """
        count: int = self._rhs_evaluation_count
        return count

    def get_statistics(self) -> list[tuple[int, int, int]]:
        """Describe the compiled category identifier, color count and instance count.

        :return: Setup diagnostics for each category.
        """
        statistics: list[tuple[int, int, int]] = list(
            (plan.spec.uid, plan.compiler.seeds.shape[0], plan.spec.variable_indices.shape[1])
            for plan in self._plans
        )
        return statistics
