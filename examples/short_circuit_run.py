import os
import VeraGridEngine.api as gce

folder = os.path.join('..', 'Grids_and_profiles', 'grids')
fname = os.path.join(folder, 'South Island of New Zealand.gridcal')

grid = gce.open_file(filename=fname)

pf_options = gce.PowerFlowOptions()
pf = gce.PowerFlowDriver(grid, pf_options)
pf.run()

fault_index = 2
sc_options = gce.ShortCircuitOptions()

grid.add_short_circuit_event(
    gce.ShortCircuitEvent(
        device=grid.buses[fault_index],
        fault_type=gce.FaultType.LG,
        method=gce.MethodShortCircuit.phases,
        phases=gce.PhasesShortCircuit.a
    )
)

sc = gce.ShortCircuitDriver(grid, options=sc_options, pf_options=pf_options, pf_results=pf.results, pf_results3ph=None)
sc.run()

print("Short circuit power: ", sc.results.SCpower[fault_index])
