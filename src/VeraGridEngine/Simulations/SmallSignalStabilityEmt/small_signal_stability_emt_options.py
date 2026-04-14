# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Optional, Tuple
from VeraGridEngine.Simulations.options_template import OptionsTemplate
from VeraGridEngine.enumerations import SmallSignalEmtBuildTypes
from VeraGridEngine.Devices.Parents.editable_device import GCProp



class EmtSmallSignalStabilityOptions(OptionsTemplate):
    """
    EmtFloquetOptions

    Parameters
    ----------
    k : int
        Number of Floquet multipliers to be calculated.
    target_period : float
        Period of the periodic orbit in seconds (e.g., 0.02 for 50 Hz).
    target_frequency_hz : float | None
        Specific oscillation frequency to target. None for standard analysis.
    max_krylov_dim : int
        Nominal Krylov subspace dimension budget for each restart cycle.
    ss_assessment_time : float
        Time to simulate before starting Floquet to ensure steady-state (s).
    verbose : int
        Verbosity level.

    Restart / robustness knobs
    --------------------------
    max_restarts : int
        Maximum number of explicit restart cycles (total cycles = max_restarts + 1).
    restart_tol : float
        Relative residual tolerance for converged Ritz pairs.
    use_refined_ritz : bool
        Use refined Ritz vectors to seed restarts and improve convergence robustness.
    adaptive_restart : bool
        Enable residual-stagnation detection with elastic block/depth adaptation.
    stagnation_improve_ratio : float
        If residual improvement is worse than this factor, adaptation is triggered.
    stagnation_patience : int
        Number of cycles to observe before declaring stagnation.
    deflation_tol : float
        Singular-value threshold for block deflation.

    Performance knobs
    -----------------
    prefer_ak_operator : bool
        Prefer an explicit EMT A_k operator if the problem exposes it.
    use_numba_kernels : bool
        Enable Numba-accelerated kernels (BMGS / A_k block propagator) when available.
    min_block_size, max_block_size : int | None
        Elastic block-size limits for restarted Block-Arnoldi.
    max_krylov_dim_cap : int | None
        Upper cap for adaptive Krylov dimension expansion.
    """

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(key="k", tpe=int),
        GCProp(key="target_period", tpe=float),
        GCProp(key="target_frequency_hz", tpe=float),
        GCProp(key="max_krylov_dim", tpe=int),
        GCProp(key="ss_assessment_time", tpe=float),
        GCProp(key="verbose", tpe=int),
        GCProp(key="max_restarts", tpe=int),
        GCProp(key="restart_tol", tpe=float),
        GCProp(key="use_refined_ritz", tpe=bool),
        GCProp(key="adaptive_restart", tpe=bool),
        GCProp(key="stagnation_improve_ratio", tpe=float),
        GCProp(key="stagnation_patience", tpe=int),
        GCProp(key="deflation_tol", tpe=float),
        GCProp(key="prefer_ak_operator", tpe=bool),
        GCProp(key="use_numba_kernels", tpe=bool),
        GCProp(key="min_block_size", tpe=int),
        GCProp(key="max_block_size", tpe=int),
        GCProp(key="max_krylov_dim_cap", tpe=int),
        GCProp(key="build_type", tpe=SmallSignalEmtBuildTypes),
    )

    def __init__(self,
                 k: int = 6,
                 target_period: float = 0.02,
                 target_frequency_hz: float = None,
                 max_krylov_dim: int = 30,
                 ss_assessment_time: float = 0.1,
                 verbose: int = 0,
                 max_restarts: int = 4,
                 restart_tol: float = 1e-6,
                 use_refined_ritz: bool = True,
                 adaptive_restart: bool = True,
                 stagnation_improve_ratio: float = 0.90,
                 stagnation_patience: int = 2,
                 deflation_tol: float = 1e-12,
                 prefer_ak_operator: bool = True,
                 use_numba_kernels: bool = True,
                 min_block_size: Optional[int] = None,
                 max_block_size: Optional[int] = None,
                 max_krylov_dim_cap: Optional[int] = None,
                 build_type: SmallSignalEmtBuildTypes = SmallSignalEmtBuildTypes.Arnoldi):
        OptionsTemplate.__init__(self, name='EmtFloquetOptions')

        self.k: int = k
        self.target_period: float = target_period
        self.target_frequency_hz: Optional[float] = target_frequency_hz
        self.max_krylov_dim: int = max_krylov_dim
        self.ss_assessment_time: float = ss_assessment_time
        self.verbose: int = verbose

        self.max_restarts: int = max_restarts
        self.restart_tol: float = restart_tol
        self.use_refined_ritz: bool = use_refined_ritz
        self.adaptive_restart: bool = adaptive_restart
        self.stagnation_improve_ratio: float = stagnation_improve_ratio
        self.stagnation_patience: int = stagnation_patience
        self.deflation_tol: float = deflation_tol

        self.prefer_ak_operator: bool = prefer_ak_operator
        self.use_numba_kernels: bool = use_numba_kernels
        self.min_block_size: Optional[int] = min_block_size
        self.max_block_size: Optional[int] = max_block_size
        self.max_krylov_dim_cap: Optional[int] = max_krylov_dim_cap
        self.build_type: SmallSignalEmtBuildTypes = build_type




