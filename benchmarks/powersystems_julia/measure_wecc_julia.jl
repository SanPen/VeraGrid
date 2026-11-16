"""Measure the same WECC 240 line trip as run_rms_time_series.py.

Run from the VeraGrid root with the sibling Julia environment:
    julia --startup-file=no --project="../power systems julia" benchmarks/powersystems_julia/measure_wecc_julia.jl

Simulation outputs are temporary; copy the printed WECC_TIMING rows into
julia_rms_time_series_timings.csv after reviewing the run.
"""
using Logging
using PowerSystems
using PowerSystemCaseBuilder
using PowerSimulationsDynamics
using Sundials

for repetition in 1:2
    start = time_ns()
    sys = build_system(PSIDSystems, "WECC 240 Bus"; runchecks=false)
    for load in get_components(PowerSystems.StandardLoad, sys)
        transform_load_to_constant_impedance(load)
    end
    build_seconds = (time_ns() - start) / 1e9
    event = BranchTrip(1.0, Line, "CORONADO    -1101-PALOVRDE    -1401-i_10")
    path = mktempdir()
    start = time_ns()
    sim = Simulation(ResidualModel, sys, path, (0.0, 20.0), event;
                     console_level=Logging.Error)
    compilation_seconds = (time_ns() - start) / 1e9
    start = time_ns()
    status = execute!(sim, Sundials.IDA(); dtmax=0.01, saveat=0.01,
                      enable_progress_bar=false)
    compute_seconds = (time_ns() - start) / 1e9
    occursin("FINALIZED", string(status)) || error("WECC 240 failed: $status")
    total_seconds = build_seconds + compilation_seconds + compute_seconds
    println("WECC_TIMING,$repetition,$build_seconds,$compilation_seconds,$compute_seconds,$total_seconds")
    flush(stdout)
end
