# Ten fresh Julia RMS runs per case; execute from the VeraGrid repository root.
include(joinpath(@__DIR__, "..", "..", "..", "power systems julia", "src", "dynamic_analysis.jl"))
using PowerSystemCaseBuilder

const OUTPUT = length(ARGS) >= 3 ? ARGS[3] : joinpath(@__DIR__, "results", "ten_run_timing", "julia.csv")
const SELECTED_CASES = isempty(ARGS) ? ("2_bus", "3_bus", "ieee9", "wecc_240") : (ARGS[1],)
const DURATION = length(ARGS) >= 2 ? parse(Float64, ARGS[2]) : nothing
const REPETITIONS = length(ARGS) >= 4 ? parse(Int, ARGS[4]) : 10
REPETITIONS >= 1 || error("Repetitions must be positive")
const HEADER = "case,repetition,setup_s,simulation_build_s,integration_s,rhs_evaluation_s,jacobian_evaluation_s,unattributed_integration_s,total_s"

function case_data(name)
    if name == "2_bus"
        sys=build_system(PSIDSystems,"OMIB System")
        dyn=get_dynamic_injector(get_component(ThermalStandard,sys,"generator-102-1"))
        return sys,ControlReferenceChange(1.0,dyn,:P_ref,0.55),(0.0,10.0),0.02,r->get_state_series(r,("generator-102-1",:δ))
    elseif name == "3_bus"
        sys=build_system(PSIDSystems,"Three Bus Dynamic data Example System")
        dyn=get_dynamic_injector(get_component(ThermalStandard,sys,"generator-103-1"))
        return sys,ControlReferenceChange(1.0,dyn,:P_ref,0.85),(0.0,10.0),0.02,r->get_voltage_magnitude_series(r,102)
    else
        sys=build_system(PSIDTestSystems,"psid_test_ieee_9bus");transform_standard_loads!(sys)
        dyn=get_dynamic_injector(get_component(ThermalStandard,sys,"generator-2-1"))
        return sys,ControlReferenceChange(1.0,dyn,:P_ref,0.78),(0.0,2.0),0.01,r->get_voltage_magnitude_series(r,5)
    end
end

function timed_case(name, repetition)
    start = time_ns()
    if name == "wecc_240"
        sys = build_system(PSIDSystems, "WECC 240 Bus"; runchecks=false)
        for load in get_components(PowerSystems.StandardLoad, sys)
            transform_load_to_constant_impedance(load)
        end
        event = BranchTrip(1.0, Line, "CORONADO    -1101-PALOVRDE    -1401-i_10")
        tspan, step = (0.0, 20.0), 0.01
    else
        sys, event, tspan, step, _ = case_data(name)
    end
    if DURATION !== nothing
        1.0 < DURATION <= tspan[2] || error("Duration must exceed the event and not exceed the case horizon")
        tspan = (0.0, DURATION)
    end
    setup = (time_ns()-start)/1e9
    mktempdir() do path
        start = time_ns()
        sim = Simulation(ResidualModel, sys, path, tspan, event; console_level=Logging.Error)
        build = (time_ns()-start)/1e9
        rhs_ns = Ref(0)
        jac_ns = Ref(0)
        old_problem = sim.problem
        old_function = old_problem.f
        old_rhs = old_function.f
        old_jac = old_function.jac
        function timed_rhs!(out, du, u, params, t)
            tick = time_ns()
            try
                old_rhs(out, du, u, params, t)
            finally
                rhs_ns[] += time_ns() - tick
            end
        end
        function timed_jac!(matrix, du, u, params, gamma, t)
            tick = time_ns()
            try
                old_jac(matrix, du, u, params, gamma, t)
            finally
                jac_ns[] += time_ns() - tick
            end
        end
        timed_function = SciMLBase.DAEFunction{true}(
            timed_rhs!; jac=timed_jac!,
            jac_prototype=old_function.jac_prototype,
            tgrad=old_function.tgrad,
        )
        sim.problem = SciMLBase.remake(old_problem; f=timed_function)
        start = time_ns()
        status = execute!(sim, Sundials.IDA(); dtmax=step, saveat=step,
                          enable_progress_bar=false)
        integration = (time_ns()-start)/1e9
        occursin("FINALIZED", string(status)) || error("$name repetition $repetition failed: $status")
        row = join((name, repetition, setup, build, integration,
                    rhs_ns[] / 1e9, jac_ns[] / 1e9,
                    integration - (rhs_ns[] + jac_ns[]) / 1e9,
                    setup + build + integration), ',')
        open(OUTPUT, "a") do io
            println(io, row)
        end
        println(row)
        flush(stdout)
    end
end

mkpath(dirname(OUTPUT))
open(OUTPUT, "w") do io
    println(io, HEADER)
end
println(HEADER)
for repetition in 1:REPETITIONS, name in SELECTED_CASES
    timed_case(name, repetition)
end
