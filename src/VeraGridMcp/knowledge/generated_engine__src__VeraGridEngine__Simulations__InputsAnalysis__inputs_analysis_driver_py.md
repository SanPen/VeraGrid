# VeraGridEngine Module: src/VeraGridEngine/Simulations/InputsAnalysis/inputs_analysis_driver.py

- Original source path: `src/VeraGridEngine/Simulations/InputsAnalysis/inputs_analysis_driver.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 2
- Top-level function count: 0
- Representative imports: __future__, typing, numpy, pandas, VeraGridEngine.Simulations.driver_template, VeraGridEngine.Simulations.results_template, VeraGridEngine.Simulations.results_table, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.enumerations, VeraGridEngine.basic_structures

## Class: InputsAnalysisResults

- Bases: ResultsTemplate
- Summary: No docstring provided.

### Methods

- `get_generators_df(self)`
  Summary: :return:
- `get_batteries_df(self)`
  Summary: :return:
- `get_loads_df(self)`
  Summary: :return:
- `get_static_generators_df(self)`
  Summary: :return:
- `group_by(self, group)`
  Summary: Return a DataFrame grouped by Area, Zone or Country
- `get_bus_zone_indices(self)`
  Summary: :return:
- `get_bus_area_indices(self)`
  Summary: :return:
- `get_bus_country_indices(self)`
  Summary: :return:
- `get_bus_substation_indices(self)`
  Summary: :return:
- `get_collection_attr_series(self, elms, magnitude, aggregation)`
  Summary: :param elms:
- `mdl(self, result_type)`
  Summary: Plot the results

## Class: InputsAnalysisDriver

- Bases: DriverTemplate
- Summary: No docstring provided.

### Methods

- `get_steps(self)`
  Summary: :return:
- `run(self)`
  Summary: Pack run_pf for the QThread
- `cancel(self)`
  Summary: No docstring provided.
