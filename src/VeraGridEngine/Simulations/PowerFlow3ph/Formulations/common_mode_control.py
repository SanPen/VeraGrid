# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import numpy as np
from scipy.linalg import null_space
from scipy.sparse import csc_matrix, diags, vstack, eye
from scipy.sparse.csgraph import connected_components

from VeraGridEngine.basic_structures import IntVec, CxVec, Vec, BoolVec
from VeraGridEngine.DataStructures.load_data import LoadData
from VeraGridEngine.DataStructures.generator_data import GeneratorData
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.DataStructures.shunt_data import ShuntData
from VeraGridEngine.enumerations import GeneratorType, ShuntConnectionType, ShuntControlMode, WindingType
from VeraGridEngine.Simulations.PowerFlow3ph.Formulations.positive_sequence_control import PositiveSequenceControl
from VeraGridEngine.Utils.Sparse.csc2 import CSC, mat_to_scipy, scipy_to_mat


def common_mode_constraints(matrix: csc_matrix, shifts: csc_matrix) -> csc_matrix:
    """Project a linear device response onto bus common shifts, allowing only summation roundoff.

    :param matrix: Terminal current coefficients, before combining different devices.
    :param shifts: One common NABC displacement per bus.
    :return: Row-scaled constraints on the bus displacements.
    """
    response: csc_matrix = (matrix @ shifts).tocsc()
    scale: csc_matrix = (abs(matrix) @ abs(shifts)).tocsc()
    columns: IntVec = np.repeat(np.arange(response.shape[1]), np.diff(response.indptr))
    bounds: Vec = np.asarray(scale[response.indices, columns]).ravel()
    response.data[np.abs(response.data) <= 32 * np.finfo(float).eps * bounds] = 0.0
    response.eliminate_zeros()
    # Scale by the original coefficients, before cancellation in the common response.
    # Dividing by that small response would amplify its summation roundoff before SVD.
    norms: Vec = np.asarray(scale.sum(axis=1)).ravel()
    nonzero: BoolVec = norms > 0
    norms[nonzero] = 1.0 / norms[nonzero]
    return (diags(norms, format='csc') @ response).tocsc()


class CommonModeControl:
    """Handle free/ideal U0 constraints and scale physical common-mode balances."""

    __slots__ = ('phases', 'real_rows', 'imag_rows', 'ideal_phases',
                 'balance', 'balance_real_rows', 'balance_imag_rows',
                 'positive', 'slack_real_rows', 'slack_imag_rows',
                 'constraints', 'constraint_targets', 'constraint_real_rows', 'constraint_imag_rows')

    def __init__(self, nc: NumericalCircuit, ybus: csc_matrix, yf: csc_matrix,
                 yt: csc_matrix, mask: BoolVec, full_lookup: IntVec, lookup: IntVec,
                 idx_p: IntVec, idx_q: IntVec, positive: PositiveSequenceControl,
                 reduced_ybus: csc_matrix) -> None:
        """Find independent floating groups using existing terminal matrices and injection models.

        :param nc: Compiled island, with the current topology and active devices.
        :param ybus: Original full nodal admittance before passive reduction.
        :param yf: Original from-terminal admittance.
        :param yt: Original to-terminal admittance.
        :param mask: Connected original NABC conductors.
        :param full_lookup: Original NABC to connected-conductor lookup.
        :param lookup: Retained voltage indices after passive-neutral reduction.
        :param idx_p: Voltage indices with a real current-balance equation.
        :param idx_q: Voltage indices with an imaginary current-balance equation.
        :param positive: Existing positive-sequence injection and control classification.
        :param reduced_ybus: Admittance acting on the retained solver voltages.
        """
        phases: np.ndarray = lookup[4 * np.arange(nc.nbus)[:, None] + np.arange(1, 4)]
        connected: np.ndarray = phases >= 0
        has_equations: np.ndarray = np.isin(phases, idx_p) & np.isin(phases, idx_q)
        available: BoolVec = np.any(connected, axis=1) & ~np.any(connected & ~has_equations, axis=1)
        full_phases: np.ndarray = full_lookup[4 * np.arange(nc.nbus)[:, None] + np.arange(1, 4)]
        eliminated: BoolVec = np.all((phases < 0) & (full_phases >= 0), axis=1)
        # An eliminated passive centre is not a physical voltage reference.
        blocked: BoolVec = ~(available | eliminated)
        # Summed ABC KCL is linear when the nonlinear injections have no I0.
        passive: BoolVec = ~blocked & (full_lookup[4 * np.arange(nc.nbus)] < 0)
        devices: LoadData | GeneratorData | ShuntData
        # All retained conductors at a bus translate together, including an explicit neutral.
        slots: IntVec = np.flatnonzero(mask)
        shifts: csc_matrix = csc_matrix((np.ones(len(slots)), (np.arange(len(slots)), slots // 4)),
                                        shape=(len(slots), nc.nbus))
        constraints: list[csc_matrix] = list((common_mode_constraints(yf, shifts),
                                              common_mode_constraints(yt, shifts)))
        # Check each shunt separately: opposite admittances must not cancel a real earth path.
        # This also detects static-generator I0 paths directly from their stored ABC admittance.
        k: int
        for devices in (nc.load_data, nc.shunt_data):
            for k in range(devices.nelm):
                bus: int = devices.bus_idx[k]
                local: IntVec = np.flatnonzero(mask[4 * bus:4 * bus + 4])
                block: np.ndarray = devices.Y3_star[4 * k + local, :][:, local]
                ones: csc_matrix = csc_matrix(np.ones((len(local), 1)))
                if common_mode_constraints(csc_matrix(block), ones).nnz:
                    blocked[bus] = True
                else:
                    pass
        # Explicit branch shunts remain references even below the precision of a large series stamp.
        connection: int
        for k in range(nc.nbr):
            if nc.passive_branch_data.G0[k] != 0 or nc.passive_branch_data.B0[k] != 0:
                for bus, connection in ((nc.passive_branch_data.F[k], nc.passive_branch_data.conn_f[k]),
                                        (nc.passive_branch_data.T[k], nc.passive_branch_data.conn_t[k])):
                    # A complete ABC line retains its explicit zero-sequence
                    # shunt even below series-stamp roundoff. Partial-phase
                    # lines use their actual terminal matrices, as in devel.
                    complete_line: bool = (not nc.passive_branch_data.is_transformer[k]
                        and nc.passive_branch_data.phA[k] and nc.passive_branch_data.phB[k]
                        and nc.passive_branch_data.phC[k]
                        and connection not in (WindingType.Delta.idx(), WindingType.FloatingStar.idx()))
                    grounded_transformer: bool = nc.passive_branch_data.is_transformer[k] and connection in (
                        WindingType.GroundedStar.idx(), WindingType.NeutralZigZag.idx(),
                        WindingType.FloatingZigZag.idx(), WindingType.GroundedZigZag.idx())
                    if complete_line or grounded_transformer:
                        blocked[bus] = True
                    else:
                        pass
            else:
                pass
        # Delta and floating-star P/I models depend only on voltage differences. A star model
        # is invariant only if its current also returns through the translated explicit neutral.
        values: CxVec
        for k in range(nc.load_data.nelm):
            bus = nc.load_data.bus_idx[k]
            for values in (nc.load_data.S3_star, nc.load_data.I3_star):
                if np.any(values[4 * k + 1:4 * k + 4] != 0):
                    if nc.load_data.active[k]:
                        passive[bus] = False
                    else:
                        pass
                    if values[4 * k] == 0 or full_lookup[4 * bus] < 0:
                        blocked[bus] = True
                    else:
                        pass
                else:
                    pass
        # Legacy per-phase generator powers are earth-referenced. U1 sources and induction
        # machines are invariant only when their actual connection blocks I0.
        ideal: BoolVec = np.zeros(nc.nbus, dtype=bool)
        generators: GeneratorData
        for generators in (nc.generator_data, nc.battery_data):
            for k in range(generators.nelm):
                if generators.active[k]:
                    regular: bool = generators is nc.generator_data and k in positive.regular_idx
                    asynchronous: bool = generators.tpe_int[k] == GeneratorType.Asynchronous.idx()
                    if (not regular and not asynchronous
                            and generators.conn[k] == ShuntConnectionType.GroundedStar.idx()
                            and generators.r0[k] == 0.0 and generators.x0[k] == 0.0):
                        ideal[generators.bus_idx[k]] = True
                    else:
                        pass
                    if ((regular and not asynchronous) or generators.conn[k] not in
                            (ShuntConnectionType.Delta.idx(), ShuntConnectionType.FloatingStar.idx())):
                        blocked[generators.bus_idx[k]] = True
                        passive[generators.bus_idx[k]] = False
                    else:
                        pass
                else:
                    pass
        # A variable grounded shunt remains a reference even when its present B is zero.
        # The connection also protects tiny fixed earth paths in sequence-based stamps.
        for k in range(nc.shunt_data.nelm):
            if (nc.shunt_data.active[k] and nc.shunt_data.conn[k] == ShuntConnectionType.GroundedStar.idx()
                    and (nc.shunt_data.control_mode_int[k] in (ShuntControlMode.Continuous.idx(),
                                                              ShuntControlMode.QVDroop.idx())
                         or np.any(nc.shunt_data.Y3_star[4 * k:4 * k + 4] != 0))):
                blocked[nc.shunt_data.bus_idx[k]] = True
                passive[nc.shunt_data.bus_idx[k]] = False
            else:
                pass
        # Retain the assembled check too, including any additional compiled passive contribution.
        constraints.append(common_mode_constraints(ybus, shifts))
        constraints.append(diags(blocked.astype(float), format='csc'))
        matrix: csc_matrix = vstack(constraints, format='csc')
        pattern: csc_matrix = abs(matrix)
        count: int
        groups: IntVec
        count, groups = connected_components((pattern.T @ pattern).tocsc(), directed=False)
        references: IntVec = np.empty(nc.nbus, dtype=int)
        used: int = 0
        balances: list[csc_matrix] = list()
        balance_phases: list[int] = list()
        group: int
        for group in range(count):
            buses: IntVec = np.flatnonzero(groups == group)
            retained: IntVec = np.flatnonzero(available[buses])
            free_reference: bool = False
            if np.any(blocked[buses]):
                # Conservative: do not constrain partially referenced or unsupported groups.
                pass
            else:
                subset: csc_matrix = matrix[:, buses]
                rows: IntVec = np.unique(subset.indices)
                kernel: np.ndarray = null_space(subset[rows, :].toarray(),
                    rcond=32 * np.finfo(float).eps * max(1, len(rows), len(buses)))
                if kernel.shape[1] == 1 and len(retained) and np.any(kernel[retained, 0] != 0):
                    # One complex reference per independent group; never set U0 at every bus.
                    references[used] = buses[retained[np.argmax(abs(kernel[retained, 0]))]]
                    used += 1
                    free_reference = True
                else:
                    # Ambiguous groups keep their original equations rather than adding a reference.
                    pass
            if not free_reference and len(retained) and np.all(passive[buses] | eliminated[buses]):
                phase_rows: IntVec = phases[buses[retained]].ravel()
                phase_rows = phase_rows[phase_rows >= 0]
                block: csc_matrix = reduced_ybus[phase_rows, :]
                response: csc_matrix = (csc_matrix(np.ones((1, len(phase_rows)))) @ block).tocsc()
                norm: float = float(np.linalg.norm(response.data))
                # Sum coefficients before multiplying V, so large internal currents cancel
                # before evaluating a weak earth balance. Do not amplify summation roundoff.
                if norm > 32 * np.finfo(float).eps * np.sum(np.abs(block.data)):
                    balances.append(response / norm)
                    balance_phases.append(int(phase_rows[0]))
                else:
                    pass
            else:
                pass
        # Fixed slack voltages have no KCL unknown to eliminate. Colocated ideal
        # sources impose one physical condition; only their total I0 is determined.
        ideal &= np.all(connected & has_equations, axis=1)
        self.ideal_phases: np.ndarray = phases[ideal]
        self.phases: np.ndarray = np.vstack((phases[references[:used]], self.ideal_phases))
        # Explicit lookup also works when the legacy PQ/PV equation order is not sorted.
        p_rows: IntVec = np.full(len(lookup), -1, dtype=int)
        q_rows: IntVec = np.full(len(lookup), -1, dtype=int)
        p_rows[idx_p] = np.arange(len(idx_p))
        q_rows[idx_q] = len(idx_p) + np.arange(len(idx_q))
        first_phase: IntVec = np.min(np.where(self.phases >= 0, self.phases, len(lookup)), axis=1)
        self.real_rows: IntVec = p_rows[first_phase]
        self.imag_rows: IntVec = q_rows[first_phase]
        self.positive: PositiveSequenceControl = positive
        # U0 uses phase A above; the independent complex U1 reference uses phase B.
        self.slack_real_rows: IntVec = p_rows[positive.slack_phases[:, 1]]
        self.slack_imag_rows: IntVec = q_rows[positive.slack_phases[:, 1]]
        self.balance: csc_matrix = (vstack(balances, format='csc') if balances else
                                    csc_matrix((0, reduced_ybus.shape[1]), dtype=complex))
        self.balance_real_rows: IntVec = p_rows[balance_phases]
        self.balance_imag_rows: IntVec = q_rows[balance_phases]
        # Keep one linear complex constraint matrix for both residual evaluation
        # and analytic row derivatives, including partially connected phases.
        present: np.ndarray = self.phases >= 0
        mean_rows: np.ndarray = np.broadcast_to(np.arange(len(self.phases))[:, None], self.phases.shape)
        mean_values: np.ndarray = np.broadcast_to(
            1.0 / np.sum(present, axis=1)[:, None], self.phases.shape)
        mean: csc_matrix = csc_matrix((mean_values[present],
            (mean_rows[present], self.phases[present])), shape=(len(self.phases), reduced_ybus.shape[0]))
        slack_rows: IntVec = np.repeat(np.arange(len(positive.slack_phases)), 3)
        slack_values: CxVec = np.tile(positive.rotation.conj() / 3.0, len(positive.slack_phases))
        slack: csc_matrix = csc_matrix((slack_values,
            (slack_rows, positive.slack_phases.ravel())), shape=(len(positive.slack_phases), reduced_ybus.shape[0]))
        self.constraints: csc_matrix = vstack((mean, slack, self.balance), format='csc')
        self.constraint_targets: CxVec = np.r_[np.zeros(len(mean_rows), dtype=complex),
                                               positive.slack_vset, np.zeros(len(balances), dtype=complex)]
        self.constraint_real_rows: IntVec = np.r_[self.real_rows, self.slack_real_rows, self.balance_real_rows]
        self.constraint_imag_rows: IntVec = np.r_[self.imag_rows, self.slack_imag_rows, self.balance_imag_rows]

    def remove_ideal_current(self, voltage: CxVec, mismatch: CxVec) -> None:
        """Eliminate unconstrained ideal-source currents from phase-aligned KCL.

        :param voltage: Retained NABC voltages in pu.
        :param mismatch: Current mismatch divided by each voltage's unit phasor; updated in place.
        :return: None. apply() supplies the corresponding complex voltage references.
        """
        rotation: np.ndarray = voltage[self.ideal_phases] / np.abs(voltage[self.ideal_phases])
        i0: CxVec = np.mean(mismatch[self.ideal_phases] * rotation, axis=1)
        mismatch[self.ideal_phases] -= i0[:, None] / rotation
        phases: np.ndarray = self.positive.slack_phases
        rotation = voltage[phases] / np.abs(voltage[phases])
        i1: CxVec = (mismatch[phases] * rotation) @ self.positive.rotation.conj() / 3.0
        mismatch[phases] -= i1[:, None] * self.positive.rotation / rotation

    def apply(self, voltage: CxVec, residual: Vec) -> None:
        """Apply references and equivalent KCL sums for groups without nonlinear I0.

        :param voltage: Current retained NABC voltages.
        :param residual: Existing real current/control equations, updated in place.
        :return: None.
        """
        reference: CxVec = self.constraints @ voltage - self.constraint_targets
        residual[self.constraint_real_rows] = reference.real
        residual[self.constraint_imag_rows] = reference.imag

    def project_jacobian(self, jacobian: CSC, voltage: CxVec, mismatch: CxVec,
                         lookup_p: IntVec, lookup_q: IntVec, lookup_angle: IntVec) -> CSC:
        """Differentiate the ideal-source current projections in rotated KCL.

        For a constant physical projector P and E=V/abs(V), the residual is
        E^-1 (I-P) E R. Its derivative includes both the projected current
        derivative and the angular derivative of E. Left multiplication also
        projects every controlled-Q column; the added term has angle columns only.

        :param jacobian: Unprojected analytic current/control Jacobian.
        :param voltage: Retained conductor voltages at the Jacobian point.
        :param mismatch: Unprojected current mismatch divided by E.
        :param lookup_p: Conductor to real KCL row, excluding control rows.
        :param lookup_q: Conductor to imaginary KCL row within its own block.
        :param lookup_angle: Conductor to solver angle column.
        :return: Projected analytic Jacobian before voltage-row replacements.
        """
        groups: int = len(self.ideal_phases) + len(self.positive.slack_phases)
        if groups == 0:
            return jacobian
        else:
            pass

        phases: np.ndarray = np.vstack((self.ideal_phases, self.positive.slack_phases))
        weights: np.ndarray = np.vstack((np.ones(self.ideal_phases.shape, dtype=complex),
            np.tile(self.positive.rotation, (len(self.positive.slack_phases), 1))))
        unit: CxVec = voltage / np.abs(voltage)
        # Each 3x3 complex projector has 36 real row-transform entries and
        # 18 real entries from differentiating the row/column voltage rotations.
        transform_rows: IntVec = np.empty(36 * groups, dtype=np.int32)
        transform_columns: IntVec = np.empty(36 * groups, dtype=np.int32)
        transform_values: Vec = np.empty(36 * groups)
        correction_rows: IntVec = np.empty(18 * groups, dtype=np.int32)
        correction_columns: IntVec = np.empty(18 * groups, dtype=np.int32)
        correction_values: Vec = np.empty(18 * groups)
        transform_position: int = 0
        correction_position: int = 0
        n_real: int = int(np.count_nonzero(lookup_p >= 0))
        group: int
        row: int
        column: int
        for group in range(groups):
            terminals: IntVec = phases[group]
            projector: np.ndarray = (weights[group, :, None] * weights[group, None, :].conj()
                * unit[terminals][None, :] / unit[terminals][:, None] / 3.0)
            removed: CxVec = projector @ mismatch[terminals]
            for row in range(3):
                p_row: int = lookup_p[terminals[row]]
                q_row: int = n_real + lookup_q[terminals[row]]
                for column in range(3):
                    p_column: int = lookup_p[terminals[column]]
                    q_column: int = n_real + lookup_q[terminals[column]]
                    value: complex = -projector[row, column]
                    transform_rows[transform_position:transform_position + 4] = (p_row, p_row, q_row, q_row)
                    transform_columns[transform_position:transform_position + 4] = (
                        p_column, q_column, p_column, q_column)
                    transform_values[transform_position:transform_position + 4] = (
                        value.real, -value.imag, value.imag, value.real)
                    transform_position += 4
                    # d(E^-1 P E)/dtheta affects the raw residual even away
                    # from a root; omitting this term only looks correct at convergence.
                    angle_column: int = lookup_angle[terminals[column]]
                    change: complex = -1j * projector[row, column] * mismatch[terminals[column]]
                    if row == column:
                        change += 1j * removed[row]
                    else:
                        pass
                    correction_rows[correction_position:correction_position + 2] = (p_row, q_row)
                    correction_columns[correction_position:correction_position + 2] = angle_column
                    correction_values[correction_position:correction_position + 2] = (change.real, change.imag)
                    correction_position += 2

        transform: csc_matrix = eye(jacobian.n_rows, format='csc') + csc_matrix(
            (transform_values, (transform_rows, transform_columns)), shape=(jacobian.n_rows, jacobian.n_rows))
        correction: csc_matrix = csc_matrix(
            (correction_values, (correction_rows, correction_columns)), shape=(jacobian.n_rows, jacobian.n_cols))
        projected: csc_matrix = (transform @ mat_to_scipy(jacobian) + correction).tocsc()
        return scipy_to_mat(projected)
