import VeraGridEngine as gce
import numpy as np
import matplotlib.pyplot as plt

grid = gce.open_file("/home/santi/Descargas/IEEE 14 Contingencies.veragrid")

# ----------------------------------------------------------------------------------------------------------------------
# Generate contingencies
# ----------------------------------------------------------------------------------------------------------------------
contingency_groups = list(grid.get_contingency_groups())
for contin in contingency_groups:
    grid.delete_contingency_group(contin)

branches = grid.get_branches()
generators = grid.get_generators()

for i, br in enumerate(branches):
    group_name = "contingency branch {}-{}".format(
        br.bus_from.name.lower(),
        br.bus_to.name.lower()
    )
    group = gce.ContingencyGroup(name=group_name)
    print(f"  [{i + 1}/{len(branches)}] Added group: {group.name}")
    grid.add_contingency_group(group)

    con = gce.Contingency(device=br, name=br.name, group=group)
    grid.add_contingency(con)

for i, gen in enumerate(generators):
    group_name = "contingency generator {}".format(gen.name.lower())
    group = gce.ContingencyGroup(name=group_name)
    print(f"  [{i + 1}/{len(generators)}] Added group: {group.name}")
    grid.add_contingency_group(group)

    con = gce.Contingency(device=gen, name=gen.name, group=group)
    grid.add_contingency(con)

# ----------------------------------------------------------------------------------------------------------------------
# Run nonlinear PF
# ----------------------------------------------------------------------------------------------------------------------
nl_power_flow = gce.PowerFlowDriver(
    grid=grid,
    options=gce.PowerFlowOptions(solver_type=gce.SolverType.NR)
)
nl_power_flow.run()

# ----------------------------------------------------------------------------------------------------------------------
# Run Linear PF
# ----------------------------------------------------------------------------------------------------------------------
lin_power_flow = gce.PowerFlowDriver(
    grid=grid,
    options=gce.PowerFlowOptions(solver_type=gce.SolverType.Linear)
)
lin_power_flow.run()

# ----------------------------------------------------------------------------------------------------------------------
# Run nonlinear contingencies
# ----------------------------------------------------------------------------------------------------------------------
pf_contingencies = gce.ContingencyAnalysisDriver(
    grid=grid,
    options=gce.ContingencyAnalysisOptions(
        contingency_method=gce.ContingencyMethod.PowerFlow,
        contingency_groups=grid.contingency_groups,
        pf_options=gce.PowerFlowOptions(solver_type=gce.SolverType.NR)
    ),
)
pf_contingencies.run()

# ----------------------------------------------------------------------------------------------------------------------
# Run linear contingencies
# ----------------------------------------------------------------------------------------------------------------------
lin_contingencies = gce.ContingencyAnalysisDriver(
    grid=grid,
    options=gce.ContingencyAnalysisOptions(
        contingency_method=gce.ContingencyMethod.Linear,
        contingency_groups=grid.contingency_groups
    )
)
lin_contingencies.run()

# ----------------------------------------------------------------------------------------------------------------------
# Plotting
# ----------------------------------------------------------------------------------------------------------------------

print("Extracting contingency branch active power results...")
# df = pf_contingencies.results.mdl(gce.ResultTypes.BranchLoading).to_df()
# df2 = lin_contingencies.results.mdl(gce.ResultTypes.BranchLoading).to_df()
# nl_pf_results = nl_power_flow.results.mdl(gce.ResultTypes.BranchLoading).to_df()
# lin_pf_results = lin_power_flow.results.mdl(gce.ResultTypes.BranchLoading).to_df()

# extract numeric arrays
max_pf_cont = np.abs(pf_contingencies.results.loading).max(axis=0)
max_lin_cont = np.abs(lin_contingencies.results.loading).max(axis=0)

print("Plotting branch loadings...")

# Figure 1: branch loading
fig1, ax1 = plt.subplots(figsize=(10, 6))

ax1.plot(max_pf_cont)
ax1.plot(max_lin_cont)
ax1.plot(np.abs(pf_contingencies.results.loading))
ax1.plot(np.abs(lin_contingencies.results.loading))

n_points = len(max_pf_cont)

ax1.set_xticks(np.arange(n_points))
ax1.set_xticklabels(np.arange(1, n_points + 1))

ax1.set_xlabel("Branch number")
ax1.set_ylabel("Branch loading (%)")
ax1.set_title("Branch loading for contingency and power flow cases")

ax1.legend([
    "Nonlinear contingency",
    "Linear contingency",
    "Nonlinear power flow",
    "Linear power flow"
])

fig1.tight_layout()
plt.show()

print("Extracting bus voltage results...")

# Voltage magnitude results
dfV = pf_contingencies.results.mdl(gce.ResultTypes.BusVoltageModule).to_df()
dfV2 = lin_contingencies.results.mdl(gce.ResultTypes.BusVoltageModule).to_df()
nl_V = nl_power_flow.results.mdl(gce.ResultTypes.BusVoltageModule).to_df()
lin_V = lin_power_flow.results.mdl(gce.ResultTypes.BusVoltageModule).to_df()

# Assume nominal voltage is 1.0 p.u.
V_nom = 1.0

# Convert to numeric only if needed
dfV_num = dfV.select_dtypes(include=[np.number])
dfV2_num = dfV2.select_dtypes(include=[np.number])
nl_V_num = nl_V.select_dtypes(include=[np.number])
lin_V_num = lin_V.select_dtypes(include=[np.number])

# Max deviation from nominal per bus for contingency cases
max_vdev_pf_cont = np.abs(dfV_num.values - V_nom).max(axis=0)
max_vdev_lin_cont = np.abs(dfV2_num.values - V_nom).max(axis=0)

# Single state deviations for base power flow cases
vdev_nl_pf = np.abs(nl_V_num.values.flatten() - V_nom)
vdev_lin_pf = np.abs(lin_V_num.values.flatten() - V_nom)

print("Plotting voltage deviations...")

# Figure 2: voltage deviations
fig2, ax2 = plt.subplots(figsize=(10, 6))

ax2.plot(max_vdev_pf_cont)
ax2.plot(max_vdev_lin_cont)
ax2.plot(vdev_nl_pf)
ax2.plot(vdev_lin_pf)

n_buses = len(max_vdev_pf_cont)

ax2.set_xticks(np.arange(n_buses))
ax2.set_xticklabels(np.arange(1, n_buses + 1))

ax2.set_xlabel("Bus number")
ax2.set_ylabel("Voltage deviation (p.u.)")
ax2.set_title("Maximum bus voltage deviation from nominal")

ax2.legend([
    "Nonlinear contingency",
    "Linear contingency",
    "Nonlinear power flow",
    "Linear power flow"
])

fig2.tight_layout()
plt.show()

print("\nScript completed successfully.")
