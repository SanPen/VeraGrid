import VeraGridEngine as vg
import pandas as pd
import numpy as np

np.set_printoptions(linewidth=2000, suppress=True)
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

# fname = '../Grids_and_profiles/grids//IEEE39_1W.gridcal'
fname = '../Grids_and_profiles/grids//IEEE 14.xlsx'
# fname = '../Grids_and_profiles/grids//lynn5buspv.xlsx'
# fname = '../Grids_and_profiles/grids//IEEE 118.xlsx'
# fname = '../Grids_and_profiles/grids//1354 Pegase.xlsx'
# fname = 'helm_data1.gridcal'

grid = vg.FileOpen(fname).open()

nc = vg.compile_numerical_circuit_at(grid)
island = nc.split_into_islands()[0]  # pick the first island

adm = island.get_admittance_matrices()
adms = island.get_series_admittance_matrices()
Sbus = island.get_power_injections_pu()
ind = island.get_simulation_indices(Sbus=Sbus)

results = vg.helm_josep(nc=nc,
                        Ybus=adm.Ybus,
                        Yf=adm.Yf,
                        Yt=adm.Yt,
                        Yshunt_bus=adm.Yshunt_bus,
                        Yseries=adms.Yseries,
                        V0=nc.bus_data.Vbus,
                        S0=Sbus,
                        Ysh0=adms.Yshunt,
                        pq=ind.pq,
                        pv=ind.pv,
                        vd=ind.vd,
                        no_slack=ind.no_slack,
                        tolerance=1e-6,
                        max_coefficients=10,
                        use_pade=False,
                        verbose=False)
Vm = np.abs(results.V)
Va = np.angle(results.V)
df = pd.DataFrame(data=np.c_[ind.bus_types, Vm, Va, np.abs(nc.bus_data.Vbus)],
                  columns=['Types', 'Vm', 'Va', 'Vset'])
print(df)
print('Error', results.norm_f)
print('Elapsed', results.elapsed)
