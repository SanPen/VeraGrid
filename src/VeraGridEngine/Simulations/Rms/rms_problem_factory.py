# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Any
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae import RmsProblemDae
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae_vectorized import RmsProblemDaeVec
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae_full_vectorized import RmsProblemDaeFullVec
from VeraGridEngine.Simulations.Rms.problems.rms_problem_phasor  import RmsProblemPhasor
from VeraGridEngine.Simulations.Rms.problems.rms_problem_multilinear import RmsProblemMultilinear
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions, RmsProblemTypes


RMS_PROBLEM_CLASS_MAP = {
    RmsProblemTypes.PowerBalance: RmsProblemDae,
    RmsProblemTypes.PowerBalanceVectorized: RmsProblemDaeVec,
    RmsProblemTypes.PowerBalanceFullVectorized: RmsProblemDaeFullVec,
    RmsProblemTypes.CurrentBalance: RmsProblemPhasor,
    RmsProblemTypes.Multilinear: RmsProblemMultilinear,
}


def build_rms_problem(grid: Any,
                      options: RmsOptions,
                      pf_results: Any,
                      progress_signal: Any,
                      logger: Logger|None = None) -> Any:
    if options.problem_type in RMS_PROBLEM_CLASS_MAP:
        problem_cls = RMS_PROBLEM_CLASS_MAP[options.problem_type]
    else:
        raise ValueError(f"Unsupported RMS problem type: {options.problem_type}")

    return problem_cls(
        grid=grid,
        options=options,
        pf_results=pf_results,
        progress_signal=progress_signal,
        logger= logger,
    )
