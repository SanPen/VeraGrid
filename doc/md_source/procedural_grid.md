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

> 🚧 Work in progress 🚧

1. Open a grid model that has a Map widget associated with it.
2. Add the substations that are planned to be constructed in the map.
3. Select the Map Widget on the right hand side panel.
4. Click on the **Procedural Grid Expansion** button.
5. Select the number of candidate substations to connect the planned to be constructed substations. 
The closest ones will be chosen automatically.
