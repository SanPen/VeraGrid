# Converter

This page summarizes the EMT converter model family and the available converter variants.

### Purpose

The EMT converter family groups the main voltage-source-converter implementations available in the dynamic editor. These templates all exchange three-phase electrical variables with the EMT network, but they differ in how much internal detail they expose.

### Behavior

- Interfaces with the EMT network through instantaneous phase voltages and currents.
- Converts power between AC and DC sides.
- Depending on the selected variant, may include PLL dynamics, outer-loop control, inner current control, switching logic, or grid-forming source dynamics.
- Lets the user choose the right balance between simulation speed and physical detail.

### Characteristics

- EMT abc-domain converter family.
- Covers averaged, hybrid, and grid-forming formulations.
- Intended as a navigation page for the individual converter templates listed below.

## How the family is organized

- `Ideal converter`: reduced averaged converter driven directly by power commands.
- `Full pseudo converter`: averaged converter with explicit control subblocks such as PLL, outer loop, and inner current loop.
- `Switched converter`: more detailed EMT converter that introduces explicit switching behavior.
- `VSC Grid-Forming (GFM)`: source-based converter formulation that imposes its own internal voltage behind an output branch.

## Characteristic equations

The exact equations depend on the selected converter variant. Typical relations used across this family include:

$$
p = v_A i_A + v_B i_B + v_C i_C
$$

$$
q = \frac{1}{\sqrt{3}}\left((v_A-v_B)i_C + (v_B-v_C)i_A + (v_C-v_A)i_B\right)
$$

$$
p_{dc} \approx p_{ac} + p_{loss}
$$

These equations express AC power measurement and the approximate balance between AC-side power, DC-side power, and converter losses.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Parameter | `Ideal converter` | Averaged EMT converter template that synthesizes abc current from power commands and enforces DC power balance | template name |
| Parameter | `Full pseudo converter` | Averaged EMT converter template with explicit PLL, outer-loop, inner-loop, and interface subblocks | template name |
| Parameter | `Switched converter` | Hybrid EMT converter template that starts averaged and then enables explicit switching | template name |
| Parameter | `VSC Grid-Forming (GFM)` | EMT grid-forming converter template represented by an internal source behind an RL branch | template name |

## How to use it

- Read this page first to choose the converter family member that matches your study objective.
- Use the individual template pages when you need the detailed interface and behavior of one specific converter variant.
