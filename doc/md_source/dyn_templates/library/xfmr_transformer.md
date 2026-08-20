# XFMR Transformer

<!-- veragrid-block-introduction:start -->
**XFMR Transformer** represents passive network physics through resistance, inductance, capacitance, coupling, or switching topology. Its equations enforce voltage-current constitutive relations and therefore affect energy storage, damping, propagation, fault current, or grounding behavior.

## Typical use

- Use it to reproduce the electrical path between sources, converters, machines, and loads.
- Keep phases, terminal orientation, connection type, and SI/per-unit parameter bases consistent.
<!-- veragrid-block-introduction:end -->

Detailed EMT transformer template based on the XFMR formulation. It represents
the two winding sides in the phase domain and builds the winding constraints
needed by the selected from-side and to-side connections.

## Configuration and behavior

General options expose both winding connection types. Grounded star is the
default on each side; changing a winding to delta or ungrounded star rebuilds
the internal incidence equations and the associated terminal interface.

Compared with the simpler Transformer EMT entry, this variant is intended for
the detailed XFMR equation set and its magnetizing/leakage representation. The
electrical values originate from the associated static transformer data.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Terminal | `hv` | High-voltage winding terminals | model-dependent |
| Terminal | `lv` | Low-voltage winding terminals | model-dependent |
| Parameter | `ratio` | Turns ratio | pu |
| Parameter | `magnetizing` | Magnetizing branch setting | model-dependent |

## How to use it

- Keep both winding choices consistent with the physical transformer vector group.
- Verify that the dynamic ports match the enabled static phases after rebuilding.
- Use the ordinary Transformer EMT block when the XFMR-specific detail is not required.
