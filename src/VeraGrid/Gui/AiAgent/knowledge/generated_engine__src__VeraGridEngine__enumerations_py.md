# VeraGridEngine Module: src/VeraGridEngine/enumerations.py

- Original source path: `src/VeraGridEngine/enumerations.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 81
- Top-level function count: 0
- Representative imports: enum

## Class: BusMode

- Bases: Enum
- Summary: Bus modes

### Methods

- `argparse(s)`
  Summary: :param s:
- `as_str(val)`
  Summary: Get the string representation of the numeric value

## Class: BusGraphicType

- Bases: Enum
- Summary: Bus graphical modes

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: SwitchGraphicType

- Bases: Enum
- Summary: Bus graphical modes

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: CpfStopAt

- Bases: Enum
- Summary: CpfStopAt

### Methods

- No methods detected.

## Class: CpfParametrization

- Bases: Enum
- Summary: CpfParametrization

### Methods

- No methods detected.

## Class: ExternalGridMode

- Bases: Enum
- Summary: Modes of operation of external grids

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: ShuntControlMode

- Bases: Enum
- Summary: Modes of operation of shunt control modes

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: InvestmentEvaluationMethod

- Bases: Enum
- Summary: Investment evaluation methods

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: BranchImpedanceMode

- Bases: Enum
- Summary: Enumeration of branch impedance modes

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: SolverType

- Bases: Enum
- Summary: Refer to the :ref:`Power Flow section<power_flow>` for details about the different

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: SyncIssueType

- Bases: Enum
- Summary: Sync issues enumeration

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: EngineType

- Bases: Enum
- Summary: Available engines enumeration

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: MIPSolvers

- Bases: Enum
- Summary: MIP solvers enumeration

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: MIPFramework

- Bases: Enum
- Summary: MIP framework enumeration

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: TimeGrouping

- Bases: Enum
- Summary: Time groupings enumeration

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: ZonalGrouping

- Bases: Enum
- Summary: Zonal groupings enumeration

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: ContingencyMethod

- Bases: Enum
- Summary: Enumeratio of contingency calculation engines

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: DiagramType

- Bases: Enum
- Summary: Types of diagrams

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: SchematicBranchEndpoint

- Bases: Enum
- Summary: Schematic branch endpoint identifiers.

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: SchematicAttachmentSide

- Bases: Enum
- Summary: Schematic attachment-side identifiers.

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: SchematicAttachmentOwnerKind

- Bases: Enum
- Summary: Schematic attachment owner kinds.

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: SchematicRouteKind

- Bases: Enum
- Summary: Schematic route kinds.

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: SchematicAutoRouteStyle

- Bases: Enum
- Summary: Schematic automatic route styles.

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: AcOpfMode

- Bases: Enum
- Summary: AC-OPF problem types

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: TapModuleControl

- Bases: Enum
- Summary: Tap module control types

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: TapPhaseControl

- Bases: Enum
- Summary: Tap angle control types

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: ConverterControlType

- Bases: Enum
- Summary: Converter control types

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: HvdcControlType

- Bases: Enum
- Summary: Simple HVDC control types

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: GenerationNtcFormulation

- Bases: Enum
- Summary: NTC formulation type

### Methods

- No methods detected.

## Class: TimeFrame

- Bases: Enum
- Summary: Time frame

### Methods

- No methods detected.

## Class: FaultType

- Bases: Enum
- Summary: Short circuit type

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: MethodShortCircuit

- Bases: Enum
- Summary: Short circuit type

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: PhasesShortCircuit

- Bases: Enum
- Summary: Short circuit type

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: WindingsConnection

- Bases: Enum
- Summary: Transformer windings connection types

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: TerminalType

- Bases: Enum
- Summary: Terminal types

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: WindingType

- Bases: Enum
- Summary: Transformer windings connection types

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: ShuntConnectionType

- Bases: Enum
- Summary: Loads, shunts, etc.. connection types

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: ActionType

- Bases: Enum
- Summary: ActionType

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: DeviceType

- Bases: Enum
- Summary: Device types

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: SubObjectType

- Bases: Enum
- Summary: Types of objects that act as complicated variable types

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: TapChangerTypes

- Bases: Enum
- Summary: Types of objects that act as complicated variable types

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: BuildStatus

- Bases: Enum
- Summary: Asset build status options

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: StudyResultsType

- Bases: Enum
- Summary: Types of simulation results

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: AvailableTransferMode

- Bases: Enum
- Summary: AvailableTransferMode

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: InvestmentsEvaluationObjectives

- Bases: Enum
- Summary: Types of investment optimization objectives

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: LogSeverity

- Bases: Enum
- Summary: Enumeration of logs severities

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: FileType

- Bases: Enum
- Summary: Enumeration of logs severities

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: CGMESVersions

- Bases: Enum
- Summary: Enumeration of logs severities

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: CgmesTopologyMode

- Bases: Enum
- Summary: Topology conversion mode for CGMES imports.

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: SparseSolver

- Bases: Enum
- Summary: Sparse solvers to use

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: NodalCapacityMethod

- Bases: Enum
- Summary: Sparse solvers to use

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: ResultTypes

- Bases: Enum
- Summary: ResultTypes

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: SimulationTypes

- Bases: Enum
- Summary: Enumeration of simulation types

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: JobStatus

- Bases: Enum
- Summary: Job status types

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: ContingencyFilteringMethods

- Bases: Enum
- Summary: Contingency filtering methods

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: Colormaps

- Bases: Enum
- Summary: Available colormaps

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: VoltageLevelTypes

- Bases: Enum
- Summary: Types of substation types

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: ContingencyOperationTypes

- Bases: Enum
- Summary: Types of contingency operations

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: BranchGroupTypes

- Bases: Enum
- Summary: Branch group types

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: CascadeType

- Bases: Enum
- Summary: No docstring provided.

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: DynamicIntegrationMethod

- Bases: Enum
- Summary: Dynamic integration methods.

### Methods

- `argparse(s)`
  Summary: No docstring provided.
- `list(cls)`
  Summary: No docstring provided.

## Class: EmtSolverTypes

- Bases: Enum
- Summary: Jacobian construction backends for implicit solvers.

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: RmsProblemTypes

- Bases: Enum
- Summary: No docstring provided.

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: EmtProblemTypes

- Bases: Enum
- Summary: No docstring provided.

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: SmallSignalEmtBuildTypes

- Bases: Enum
- Summary: Jacobian construction backends for implicit solvers.

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: EraSvdSolverType

- Bases: Enum
- Summary: Enumeration for the SVD solver backend.

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: RmsInitializationMethod

- Bases: Enum
- Summary: No docstring provided.

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: EmtInitializationMethod

- Bases: Enum
- Summary: EMT initialization workflow options.

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: GridReductionMethod

- Bases: Enum
- Summary: GridReductionMethod

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: BusReductionMethod

- Bases: Enum
- Summary: GridReductionMethod

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: VarPowerFlowReferenceType

- Bases: Enum
- Summary: VarPowerFlowReferenceType

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: ParamPowerFlowReferenceType

- Bases: Enum
- Summary: ParamPowerFlowReferenceType

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: ReliabilityMode

- Bases: Enum
- Summary: ReliabilityMode

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: OpfDispatchMode

- Bases: Enum
- Summary: OpfGenerationMode

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: TimeSeriesSearchPoint

- Bases: Enum
- Summary: TimeSeriesSearchPoint

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: EmtLineTypes

- Bases: Enum
- Summary: EmtLineTypes

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: BlockScopeMode

- Bases: Enum
- Summary: Block extraction scope modes for DGS block parsing.

### Methods

- `argparse(s)`
  Summary: :param s:
- `list(cls)`
  Summary: :return:

## Class: BlockType

- Bases: Enum
- Summary: this class contains the existing types of blocks

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: ProceduralGridMethods

- Bases: Enum
- Summary: this class contains the existing types of blocks

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: ProceduralLogicType

- Bases: Enum
- Summary: Enumeration of procedural logic entry kinds.

### Methods

- `argparse(s)`
  Summary: :param s:

## Class: EmtInitializationStatus

- Bases: Enum
- Summary: Enumeration to track the progress of the initialization solver.

### Methods

- `argparse(s)`
  Summary: :param s:
