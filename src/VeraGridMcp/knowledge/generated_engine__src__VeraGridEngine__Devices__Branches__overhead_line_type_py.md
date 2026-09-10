# VeraGridEngine Module: src/VeraGridEngine/Devices/Branches/overhead_line_type.py

- Original source path: `src/VeraGridEngine/Devices/Branches/overhead_line_type.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 3
- Top-level function count: 16
- Representative imports: __future__, typing, numpy, numpy, matplotlib, math, VeraGridEngine, VeraGridEngine.Devices.admittance_matrix, VeraGridEngine.basic_structures, VeraGridEngine.Devices.Parents.editable_device, VeraGridEngine.Devices.Parents.dynamic_parent, VeraGridEngine.Devices.Branches.wire, VeraGridEngine.enumerations

## Function: phase2circuit(phase)

Convert a phase to a circuit number

## Function: build_y_4x4(y_nxn, circuit_idx)

:param y_nxn:

## Function: n_circuits(idx)

:param idx:

## Function: get_d_ij(xi, yi, xj, yj)

Distance module between wires

## Function: get_D_ij(xi, yi, xj, yj)

Distance module between the wire i and the image of the wire j

## Function: abc_2_seq(mat)

Convert ABC to sequence components

## Function: kron_reduction(mat, keep, embed)

Perform the Kron reduction

## Function: wire_bundling(phases_set, primitive, phases_vector)

Algorithm to bundle wires per phase

## Function: calc_L_int(is_tube, r, q)

Calculates internal inductance of solid or tubular conductor

## Function: calc_GMR(is_tube, r, q)

Calculates geometric mean radius (GMR) of solid or tubular conductor

## Function: carsons(is_self, h_i, h_k, x_ik, f, rho, err_tol)

Calculates Carson's earth return correction factors Rp and Xp for both self and mutual terms.

## Function: calc_z_ii(R_int, is_tube, r_outer, r_inner, y_i, f, rho, err_tol, use_dubanton_aprox)

Calculates self impedance term [Ohm/km]

## Function: calc_z_ij(y_i, y_j, x_i, x_j, f, rho, err_tol, use_dubanton_aprox)

Calculates mutual impedance term [Ohm/km]

## Function: calc_z_matrix(wires_in_tower, f, rho, use_dubanton_aprox)

Impedance matrix

## Function: calc_y_matrix(wires_in_tower, f)

Impedance matrix

## Function: create_known_abc_overhead_template(name, z_nabc, ysh_nabc, phases, Vnom, earth_resistivity, frequency)

:param name:

## Class: WireInTower

- Bases: none
- Summary: Wire -> Tower association

### Methods

- `set_phase(self, phase)`
  Summary: Pase setter
- `phase(self)`
  Summary: No docstring provided.
- `phase(self, phase)`
  Summary: Pase setter
- `to_dict(self)`
  Summary: data to dict
- `parse(self, data, wire_dict)`
  Summary: Parse data from json dictionary

## Class: ListOfWires

- Bases: none
- Summary: No docstring provided.

### Methods

- `append(self, elm)`
  Summary: No docstring provided.
- `to_list(self)`
  Summary: Generate list of WireInTower objects
- `parse(self, data, wire_dict)`
  Summary: Parse data from json dictionary
- `get_phases(self)`
  Summary: Get the introduced phases
- `get_circuits(self)`
  Summary: Get the introduced circuits
- `copy(self)`
  Summary: No docstring provided.

## Class: OverheadLineType

- Bases: DynamicDevice
- Summary: No docstring provided.

### Methods

- `Vnom(self)`
  Summary: :return:
- `Vnom(self, val)`
  Summary: No docstring provided.
- `n_circuits(self)`
  Summary: Get the number of circuits
- `Imax(self)`
  Summary: Current rating of the tower in kA.
- `z_nabc(self)`
  Summary: :return:
- `z_phases_nabc(self)`
  Summary: :return:
- `z_abc(self)`
  Summary: :return:
- `z_abc(self, val)`
  Summary: No docstring provided.
- `z_phases_abc(self)`
  Summary: :return:
- `z_seq(self)`
  Summary: :return:
- `z_0123(self)`
  Summary: :return:
- `y_nabc(self)`
  Summary: :return:
- `y_phases_nabc(self)`
  Summary: :return:
- `y_abc(self)`
  Summary: :return:
- `y_abc(self, val)`
  Summary: No docstring provided.
- `y_phases_abc(self)`
  Summary: :return:
- `y_seq(self)`
  Summary: :return:
- `y_0123(self)`
  Summary: :return:
- `get_phN(self)`
  Summary: :return:
- `get_phA(self)`
  Summary: :return:
- `get_phB(self)`
  Summary: :return:
- `get_phC(self)`
  Summary: :return:
- `get_ys(self, circuit_idx, Sbase, length, Vnom)`
  Summary: get the series admittance matrix in p.u. (total)
- `get_ysh(self, circuit_idx, Sbase, length, Vnom)`
  Summary: get the shunt admittance matrix in p.u. (total)
- `add_wire_relationship(self, wire, xpos, ypos, phase)`
  Summary: Wire in a tower
- `plot(self, ax)`
  Summary: Plot wires position
- `is_computed(self)`
  Summary: Boolean that tells if the template has already been computed or not
- `has_sequence_data(self)`
  Summary: Boolean that tells if the template has already been computed or not
- `check(self, logger)`
  Summary: Check that the wires configuration make sense
- `compute_rating(self)`
  Summary: Compute the sum of the wires max current in A
- `compute(self)`
  Summary: Compute the tower matrices
- `is_used(self, wire)`
  Summary: :param wire:
- `get_sequence_values(self, circuit_idx, seq)`
  Summary: Get the positive sequence values R1 [Ohm], X1[Ohm] and Bsh1 [S].
- `get_values(self, Sbase, length, circuit_index, round_vals, Vnom)`
  Summary: Get the sequence values of the template
- `earth_resistivity(self)`
  Summary: Get ``earth_resistivity``.
- `earth_resistivity(self, val)`
  Summary: Set ``earth_resistivity``.
- `frequency(self)`
  Summary: Get ``frequency``.
- `frequency(self, val)`
  Summary: Set ``frequency``.
- `capex(self)`
  Summary: Get ``capex``.
- `capex(self, val)`
  Summary: Set ``capex``.
- `opex(self)`
  Summary: Get ``opex``.
- `opex(self, val)`
  Summary: Set ``opex``.
