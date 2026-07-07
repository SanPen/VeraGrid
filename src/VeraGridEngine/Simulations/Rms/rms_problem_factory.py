from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae import RmsProblemDae
from VeraGridEngine.Simulations.Rms.problems.rms_problem_phasor  import RmsProblemPhasor
from VeraGridEngine.Simulations.Rms.problems.rms_problem_tensygrid  import RmsProblemTensygrid
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions, RmsProblemTypes


RMS_PROBLEM_CLASS_MAP = {
    RmsProblemTypes.Tensygrid: RmsProblemTensygrid,
    RmsProblemTypes.PowerBalance: RmsProblemDae,
    RmsProblemTypes.CurrentBalance: RmsProblemPhasor,
}


def build_rms_problem(grid, options: RmsOptions, pf_results, progress_signal):
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