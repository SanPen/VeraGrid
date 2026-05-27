from typing import Any

from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae import RmsProblemDae
from VeraGridEngine.Simulations.Rms.problems.rms_problem_phasor  import RmsProblemPhasor
from VeraGridEngine.Simulations.Rms.problems.rms_problem_multilinear import RmsProblemMultilinear
from VeraGridEngine.Simulations.Rms.problems.rms_problem_tensygrid  import RmsProblemTensygrid
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions, RmsProblemTypes


RMS_PROBLEM_CLASS_MAP = {
    RmsProblemTypes.Tensygrid: RmsProblemTensygrid,
    RmsProblemTypes.PowerBalance: RmsProblemDae,
    RmsProblemTypes.CurrentBalance: RmsProblemPhasor,
    RmsProblemTypes.Multilinear: RmsProblemMultilinear,
}


def build_rms_problem(grid: Any,
                      options: RmsOptions,
                      pf_results: Any,
                      progress_signal: Any) -> Any:
    if options.problem_type in RMS_PROBLEM_CLASS_MAP:
        problem_cls = RMS_PROBLEM_CLASS_MAP[options.problem_type]
    else:
        raise ValueError(f"Unsupported RMS problem type: {options.problem_type}")

    return problem_cls(
        grid=grid,
        options=options,
        pf_results=pf_results,
        progress_signal=progress_signal,
    )
