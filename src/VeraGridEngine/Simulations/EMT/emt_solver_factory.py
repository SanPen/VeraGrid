# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.Simulations.EMT.emt_options import EmtOptions
from VeraGridEngine.enumerations import EmtSolverTypes
from VeraGridEngine.Simulations.driver_template import DummySignal

from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Simulations.EMT.solvers.jit_symbolic_solver import JitSymbolicSolver
from VeraGridEngine.Simulations.EMT.solvers.solver_AD import JitAdSolver
from VeraGridEngine.Simulations.EMT.solvers.StructuralVectorizedSolver import StructuralVectorizedSolver
from VeraGridEngine.Simulations.EMT.solvers.structural_compiled_solver import StructuralCompiledSolver
from VeraGridEngine.enumerations import DynamicIntegrationMethod
from VeraGridEngine.Utils.NumericalMethods.emt_sparse_solver_registry import resolve_emt_sparse_solver_backend_provider
from VeraGridEngine.Utils.Symbolic.diagnostic import NewtonDiagnosticsConfig


EMT_SOLVER_CLASS_MAP = {
    EmtSolverTypes.Symbolic: JitSymbolicSolver,
    EmtSolverTypes.Automatic: JitAdSolver,
    EmtSolverTypes.StructuralAD: StructuralVectorizedSolver,
    EmtSolverTypes.StructuralCompiled: StructuralCompiledSolver,
}


def build_emt_solver(options: EmtOptions,
                     problem: EmtProblemTemplate,
                     t0: float,
                     t_end: float,
                     h: float,
                     method: DynamicIntegrationMethod = DynamicIntegrationMethod.DaeTrapezoidal,
                     newton_diag_config: NewtonDiagnosticsConfig | None = None):

    if options.solver_type in EMT_SOLVER_CLASS_MAP:
        solver_cls = EMT_SOLVER_CLASS_MAP[options.solver_type]
    else:
        raise ValueError(f"Unsupported EMT solver type: {options.solver_type}")

    if options.solver_type == EmtSolverTypes.StructuralCompiled:
        sparse_backend_provider = resolve_emt_sparse_solver_backend_provider(
            solver_type=options.sparse_solver,
            external_plugin_name=options.external_sparse_solver_plugin_name,
            external_plugin_directory=options.external_sparse_solver_directory,
            allow_internal_fallback=options.allow_internal_sparse_fallback,
        )
        return solver_cls(problem=problem,
                          t0=t0,
                          t_end=t_end,
                          h=h,
                          method=method,
                          warmup_policy=options.compiled_warmup_policy,
                          sparse_solver_backend_provider=sparse_backend_provider,
                          newton_diag_config=newton_diag_config)
    elif options.solver_type == EmtSolverTypes.StructuralAD:
        sparse_backend_provider = resolve_emt_sparse_solver_backend_provider(
            solver_type=options.sparse_solver,
            external_plugin_name=options.external_sparse_solver_plugin_name,
            external_plugin_directory=options.external_sparse_solver_directory,
            allow_internal_fallback=options.allow_internal_sparse_fallback,
        )
        return solver_cls(problem=problem,
                          t0=t0,
                          t_end=t_end,
                          h=h,
                          method=method,
                          sparse_solver_backend_provider=sparse_backend_provider,
                          newton_diag_config=newton_diag_config)
    else:
        return solver_cls(problem=problem,
                          t0=t0,
                          t_end=t_end,
                          h=h,
                          method=method,
                          newton_diag_config=newton_diag_config)
