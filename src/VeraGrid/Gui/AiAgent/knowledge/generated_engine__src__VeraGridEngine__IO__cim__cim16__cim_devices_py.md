# VeraGridEngine Module: src/VeraGridEngine/IO/cim/cim16/cim_devices.py

- Original source path: `src/VeraGridEngine/IO/cim/cim16/cim_devices.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 66
- Top-level function count: 3
- Representative imports: datetime, numpy, typing, VeraGridEngine.IO.cim.cim16.cim_enums, VeraGridEngine.IO.base.units, VeraGridEngine.IO.cim.cim16.cim_enums, VeraGridEngine.basic_structures, VeraGridEngine.data_logger

## Function: rfid2uuid(val)

No docstring provided.

## Function: index_find(string, start, end)

version of substring that matches

## Function: str2num(val)

Try to convert to number, else keep as string

## Class: CimProperty

- Bases: none
- Summary: No docstring provided.

### Methods

- `get_unit(self)`
  Summary: No docstring provided.
- `get_class_name(self)`
  Summary: No docstring provided.
- `get_dict(self)`
  Summary: No docstring provided.

## Class: IdentifiedObject

- Bases: none
- Summary: No docstring provided.

### Methods

- `check(self, logger)`
  Summary: Check specific OCL rules
- `register_property(self, name, class_type, multiplier, unit, description, max_chars, mandatory, comment, out_of_the_standard)`
  Summary: Shortcut to add properties
- `get_properties(self)`
  Summary: No docstring provided.
- `add_reference(self, obj)`
  Summary: Adds a categorized reference to this object
- `parse_line(self, xml_line)`
  Summary: Parse xml line that eligibly belongs to this object
- `merge(self, other, overwrite)`
  Summary: Merge the properties of this object with another
- `print(self)`
  Summary: No docstring provided.
- `get_xml(self, level)`
  Summary: Returns an XML representation of the object
- `get_dict(self)`
  Summary: Get dictionary with the data
- `get_all_properties(self)`
  Summary: Get the list of properties of this object
- `list_not_implemented_properties(self)`
  Summary: This function lists all the properties that have not been implemented for this object
- `detect_circular_references(self, visited_ids)`
  Summary: No docstring provided.

## Class: MonoPole

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- `get_topological_node(self)`
  Summary: Get the TopologyNodes of this branch
- `get_bus(self)`
  Summary: Get the associated bus
- `get_dict(self)`
  Summary: Get dictionary with the data

## Class: DiPole

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- `get_topological_nodes(self)`
  Summary: Get the TopologyNodes of this branch
- `get_buses(self)`
  Summary: Get the associated bus
- `get_nodes(self)`
  Summary: Get the TopologyNodes of this branch

## Class: BaseVoltage

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: EquipmentContainer

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: PowerSystemResource

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: Equipment

- Bases: PowerSystemResource
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: ConductingEquipment

- Bases: Equipment
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: BusNameMarker

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: ACDCTerminal

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: Terminal

- Bases: ACDCTerminal
- Summary: No docstring provided.

### Methods

- `get_voltage(self)`
  Summary: Get the voltage of this terminal
- `check(self, logger)`
  Summary: :param logger:

## Class: ConnectivityNodeContainer

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: ConnectivityNode

- Bases: IdentifiedObject
- Summary: Connectivity nodes are points where terminals of AC conducting equipment are connected

### Methods

- No methods detected.

## Class: TopologicalNode

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- `get_voltage(self)`
  Summary: No docstring provided.
- `get_bus(self)`
  Summary: Get an associated BusBar, if any

## Class: BusbarSection

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- `get_topological_nodes(self)`
  Summary: Get the associated TopologicalNode instances
- `get_topological_node(self)`
  Summary: Get the first TopologicalNode found

## Class: Substation

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: OperationalLimitSet

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: OperationalLimitType

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: GeographicalRegion

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: SubGeographicalRegion

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: VoltageLevel

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: VoltageLimit

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: CurrentLimit

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: EquivalentNetwork

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: EnergyArea

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: ControlArea

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: EquivalentEquipment

- Bases: ConductingEquipment
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: EquivalentInjection

- Bases: EquivalentEquipment
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: Switch

- Bases: DiPole, ConductingEquipment
- Summary: No docstring provided.

### Methods

- `get_nodes(self)`
  Summary: Get the TopologyNodes of this branch

## Class: Breaker

- Bases: Switch
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: LoadBreakSwitch

- Bases: Switch
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: Line

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: ACLineSegment

- Bases: DiPole
- Summary: No docstring provided.

### Methods

- `get_voltage(self, logger)`
  Summary: No docstring provided.
- `get_pu_values(self, Sbase, logger)`
  Summary: Get the per-unit values of the equivalent PI model
- `get_rate(self)`
  Summary: No docstring provided.

## Class: PowerTransformerEnd

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- `get_voltage(self)`
  Summary: No docstring provided.
- `get_pu_values(self, Sbase_system)`
  Summary: Get the per-unit values of the equivalent PI model

## Class: PowerTransformer

- Bases: DiPole, ConductingEquipment
- Summary: No docstring provided.

### Methods

- `get_windings_number(self)`
  Summary: Get the number of windings
- `get_windings(self)`
  Summary: Get list of windings
- `get_pu_values(self, System_Sbase)`
  Summary: Get the transformer p.u. values
- `get_voltages(self, logger)`
  Summary: :return:
- `get_rate(self)`
  Summary: No docstring provided.

## Class: EnergyConsumer

- Bases: MonoPole, ConductingEquipment
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: ConformLoad

- Bases: EnergyConsumer
- Summary: No docstring provided.

### Methods

- `get_pq(self)`
  Summary: No docstring provided.

## Class: ConformLoadGroup

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: SubLoadArea

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: LoadArea

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: NonConformLoad

- Bases: EnergyConsumer
- Summary: No docstring provided.

### Methods

- `get_pq(self)`
  Summary: No docstring provided.

## Class: NonConformLoadGroup

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: LoadGroup

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: LoadResponseCharacteristic

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- `check(self, logger)`
  Summary: Check OCL rules

## Class: RegulatingControl

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: TapChanger

- Bases: PowerSystemResource
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: RatioTapChanger

- Bases: TapChanger
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: GeneratingUnit

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: HydroPump

- Bases: Equipment
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: RegulatingCondEq

- Bases: ConductingEquipment
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: RotatingMachine

- Bases: RegulatingCondEq
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: SynchronousMachine

- Bases: MonoPole, RotatingMachine
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: HydroGeneratingUnit

- Bases: GeneratingUnit
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: HydroPowerPlant

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: LinearShuntCompensator

- Bases: MonoPole
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: NuclearGeneratingUnit

- Bases: GeneratingUnit
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: RatioTapChangerTable

- Bases: IdentifiedObject
- Summary: Describes a curve for how the voltage magnitude and impedance varies with the tap step.

### Methods

- No methods detected.

## Class: RatioTapChangerTablePoint

- Bases: IdentifiedObject
- Summary: Describes each tap step in the ratio tap changer tabular curve.

### Methods

- No methods detected.

## Class: ReactiveCapabilityCurve

- Bases: IdentifiedObject
- Summary: Reactive power rating envelope versus the synchronous machine's active power, in both the

### Methods

- No methods detected.

## Class: StaticVarCompensator

- Bases: RegulatingCondEq
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: TapChangerControl

- Bases: RegulatingControl
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: ThermalGeneratingUnit

- Bases: GeneratingUnit
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: WindGeneratingUnit

- Bases: GeneratingUnit
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: FullModel

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: TieFlow

- Bases: IdentifiedObject
- Summary: No docstring provided.

### Methods

- No methods detected.
