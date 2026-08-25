# 🕸️ Procedural Grid Expansion

## Introduction
Transmission Network Expansion Planning (TNEP) represents a complex optimization problem requiring 
the simultaneous integration of interdependent technical and economic variables. Neglecting these 
factors results in suboptimal network designs characterized by excessive costs, operational 
inefficiencies, and reduced system security.

The literature identifies optimization techniques like Genetic Algorithms to isolate high performing 
solutions through population based evolution. However, these methodologies are typically constrained 
by the requirement for a fixed network topology.

The Procedural Grid Expansion feature overcomes the topological rigidity of traditional optimization 
which in turn minimizes the risk of local optima entrapment and enables a flexible evaluation of 
transmission expansion alternatives.

## Methodology
There are many ways to approach and solve a TNEP problem, and the best candidate depends on the 
problem conditions. That is why the procedural grid expansion feature offers a range of methods 
the user can choose from.

Since the Transmission Expansion Planning problem can be broken down into two subproblems - topology 
design and template allocation - the user can choose to solve one or both problems simultaneously. 
This could be useful in a case where the topology has already been decided and only the selection of 
templates is to be decided.

### Topology design methods

**Steiner Tree:** Steiner trees are graphs with N-1 edges that leverage auxiliary nodes called 
Steiner Points to minimize overall cable length. Once the nodes to be connected are known, a Minimum 
Spanning Tree algorithm finds the length-minimizing edge combination. The algorithm used to find optimal 
Steiner Point connections is the Vortex Search Algorithm (VSA), a nature-inspired method that mimics 
the behavior of vortices in fluid dynamics. More details can be found in the source paper 
[Sustainable Metaheuristic-Based Planning of Rural Medium-Voltage Grids: A Comparative Study of Spanning and Steiner Tree Topologies for Cost-Efficient Electrification](https://www.mdpi.com/2071-1050/17/18/8145).

### Template allocation methods

**NSGA3:** Genetic Algorithms perform remarkably well for optimization problems with discrete 
decision variables, particularly once the topology is fixed. In this context, the catalogue 
elements are defined by the topology, and the options are limited by the catalogue. For example, 
if two buses have different nominal voltages, the algorithm will only try to allocate transformers 
from the catalogue that have the same high and low rated voltages. More details can be found 
in [Investment Optimization](investment_optimization.md).

## User guide

To expand your network using VeraGrid, follow the steps below. This example was made using the New York transmission grid:

**Step 1:** Open a grid model that has a Map widget associated with it.

![](figures/Procedural%20grid/Screenshot_1.png)

**Step 2:** Add the substations that are planned for construction in the map.

![](figures/Procedural%20grid/Screenshot_2_1.png)

⚠️ WARNING - If the added substations have a voltage level that does not exist in the current grid, the following message will pop up.

![](figures/Procedural%20grid/Screenshot_2_2.png)

This is done because the Steiner Tree method uses the existing grid infrastructure as the source database to expand the network. Indeed, it is unusual to consider new voltage levels in the grid.

**Step 3:** Select the substations you want to connect with the rest of the network.

![](figures/Procedural%20grid/Screenshot_3.png)

**Step 4:** Click on the Procedural Grid Expansion button. Do not forget to click on the Map Widget on the right hand side panel before!

![](figures/Procedural%20grid/Screenshot_4.png)

**Step 5:** Select the amount of candidate substations to connect the planned to be constructed substations and click on Get candidates. The closest ones will be chosen automatically and will appear on the Connection substations candidates box.

![](figures/Procedural%20grid/Screenshot_5.png)

**Step 6:** Select the method that adapts best to the planning process you follow and click on Preview to observe the topology.

![](figures/Procedural%20grid/Screenshot_6.png)

**Step 7:** If you are satisfied with the preview, click on Apply to add the expansion to the database and the Map widget.

A pop-up window will appear to add the grid expansion as an investment. This could be useful to run an Investment Evaluation later.

<img src="figures/Procedural%20grid/Screenshot_7_1.png" alt="drawing" width="200"/>


You can visualize the expanded grid in the Map widget view.

![](figures/Procedural%20grid/Screenshot_7_2.png)

You can also inspect the circuit diagram of the expansion that has been automatically added on the right panel.

![](figures/Procedural%20grid/Screenshot_7_3.png)
