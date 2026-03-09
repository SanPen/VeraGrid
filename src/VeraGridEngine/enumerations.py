# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from enum import Enum


class BusMode(Enum):
    """
    Bus modes
    """
    PQ_tpe = 1  # control P, Q
    PV_tpe = 2  # Control P, Vm
    Slack_tpe = 3  # Control Vm, Va (slack)
    PQV_tpe = 4  # voltage-controlled bus (P, Q, V set, theta computed)
    P_tpe = 5  # voltage-controlling bus (P set, Q, V, theta computed)

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return BusMode[s]
        except KeyError:
            return s

    @staticmethod
    def as_str(val: int) -> str:
        """
        Get the string representation of the numeric value
        :param val:
        :return:
        """
        if val == 1:
            return "PQ"
        elif val == 2:
            return "PV"
        elif val == 3:
            return "Slack"
        elif val == 4:
            return "PQV"
        elif val == 5:
            return "P"
        else:
            return ""


class BusGraphicType(Enum):
    """
    Bus graphical modes
    """
    BusBar = "BusBar"
    Connectivity = "Connectivity"
    Internal = "Internal"

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return BusGraphicType[s]
        except KeyError:
            return s


class SwitchGraphicType(Enum):
    """
    Bus graphical modes
    """
    CircuitBreaker = "CircuitBreaker"
    Disconnector = "Disconnector"

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return BusGraphicType[s]
        except KeyError:
            return s


class CpfStopAt(Enum):
    """
    CpfStopAt
    """
    Nose = 'Nose'
    ExtraOverloads = 'Extra overloads'
    Full = 'Full curve'


class CpfParametrization(Enum):
    """
    CpfParametrization
    """
    Natural = 'Natural'
    ArcLength = 'Arc Length'
    PseudoArcLength = 'Pseudo Arc Length'


class ExternalGridMode(Enum):
    """
    Modes of operation of external grids
    """
    PQ = "PQ"
    PV = "PV"
    VD = "VD"

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return ExternalGridMode[s]
        except KeyError:
            return s


class InvestmentEvaluationMethod(Enum):
    """
    Investment evaluation methods
    """
    Independent = "Independent"
    Hyperopt = "Hyperopt"
    MVRSM = "MVRSM"
    NSGA3 = "NSGA3"
    Random = "Random"
    MixedVariableGA = "Mixed Variable NSGA2"
    FromPlugin = "From plugin"

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return InvestmentEvaluationMethod[s]
        except KeyError:
            return s


class BranchImpedanceMode(Enum):
    """
    Enumeration of branch impedance modes
    """
    Specified = 0
    Upper = 1
    Lower = 2

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return BranchImpedanceMode[s]
        except KeyError:
            return s


class SolverType(Enum):
    """
    Refer to the :ref:`Power Flow section<power_flow>` for details about the different
    algorithms supported by **VeraGrid**.
    """

    NR = 'Newton Raphson'
    GAUSS = 'Gauss-Seidel'
    Decoupled_LU = 'Decoupled-LU Decomposition'
    GN = "Gauss-Newton"
    Linear = 'Linear'
    HELM = 'Holomorphic Embedding'
    # ZBUS = 'Z-Gauss-Seidel'
    PowellDogLeg = "Powell's Dog Leg"
    IWAMOTO = 'Iwamoto-Newton-Raphson'
    CONTINUATION_NR = 'Continuation-Newton-Raphson'

    LM = 'Levenberg-Marquardt'
    FASTDECOUPLED = 'Fast decoupled'
    LACPF = 'Linear AC'
    LINEAR_OPF = 'Linear OPF'
    NONLINEAR_OPF = 'Nonlinear OPF'
    GREEDY_DISPATCH_OPF = 'Greedy dispatch'
    Proportional_OPF = 'Proportional OPF'

    BFS = 'Backwards-Forward substitution'  # for PGM
    BFS_linear = 'Backwards-Forward substitution (linear)'  # for PGM
    Constant_Impedance_linear = 'Constant impedance linear'  # for PGM
    NoSolver = 'No Solver'

    def __str__(self) -> str:
        """

        :return:
        """
        return str(self.value)

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return SolverType[s]
        except KeyError:
            return s


class SyncIssueType(Enum):
    """
    Sync issues enumeration
    """
    Added = 'Added'
    Deleted = 'Deleted'
    Conflict = 'Conflict'

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return SyncIssueType[s]
        except KeyError:
            return s


class EngineType(Enum):
    """
    Available engines enumeration
    """
    VeraGrid = 'VeraGrid'
    Bentayga = 'Bentayga'
    NewtonPA = 'Newton Power Analytics'
    PGM = 'Power Grid Model'
    GSLV = "gslv"

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return EngineType[s]
        except KeyError:
            return s


class MIPSolvers(Enum):
    """
    MIP solvers enumeration
    """
    HIGHS = 'HIGHS'
    SCIP = 'SCIP'
    CPLEX = 'CPLEX'
    GUROBI = 'GUROBI'
    XPRESS = 'XPRESS'
    CBC = 'CBC'
    PDLP = 'PDLP'

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return MIPSolvers[s]
        except KeyError:
            return MIPSolvers.HIGHS


class MIPFramework(Enum):
    """
    MIP framework enumeration
    """
    OrTools = 'or-tools'
    PuLP = 'PuLP'

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return MIPFramework[s]
        except KeyError:
            return MIPFramework.PuLP


class TimeGrouping(Enum):
    """
    Time groupings enumeration
    """
    NoGrouping = 'No grouping'
    Monthly = 'Monthly'
    Weekly = 'Weekly'
    Daily = 'Daily'
    Hourly = 'Hourly'

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return TimeGrouping[s]
        except KeyError:
            return s


class ZonalGrouping(Enum):
    """
    Zonal groupings enumeration
    """
    NoGrouping = 'No grouping'
    Area = 'Area'
    All = 'All (copper plate)'

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return ZonalGrouping[s]
        except KeyError:
            return s


class ContingencyMethod(Enum):
    """
    Enumeratio of contingency calculation engines
    """
    PowerFlow = 'Power flow'
    OptimalPowerFlow = 'Optimal power flow'
    HELM = 'HELM'
    Linear = 'Linear'
    PTDF_scan = "PTDF Scan"

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return ZonalGrouping[s]
        except KeyError:
            return s


class DiagramType(Enum):
    """
    Types of diagrams
    """
    Schematic = 'schematic'
    SubstationLineMap = 'substation-line-map'

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return DiagramType[s]
        except KeyError:
            return s

    @classmethod
    def list(cls):
        """

        :return:
        """
        return list(map(lambda c: c.value, cls))


class AcOpfMode(Enum):
    """
    AC-OPF problem types
    """
    ACOPFstd = 'ACOPFstd'
    ACOPFslacks = 'ACOPFslacks'
    ACOPFMaxInjections = 'ACOPFMaxInjections'

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return AcOpfMode[s]
        except KeyError:
            return s

    @classmethod
    def list(cls):
        """

        :return:
        """
        return list(map(lambda c: c.value, cls))


class TapModuleControl(Enum):
    """
    Tap module control types
    """
    fixed = 'Fixed'
    Vm = 'Vm'
    Qf = 'Qf'
    Qt = 'Qt'

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return TapModuleControl[s]
        except KeyError:
            return s

    @classmethod
    def list(cls):
        """

        :return:
        """
        return list(map(lambda c: c.value, cls))


class TapPhaseControl(Enum):
    """
    Tap angle control types
    """
    fixed = 'Fixed'
    Pf = 'Pf'
    Pt = 'Pt'

    # Droop = "Droop"

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return TapPhaseControl[s]
        except KeyError:
            return s

    @classmethod
    def list(cls):
        """

        :return:
        """
        return list(map(lambda c: c.value, cls))


class ConverterControlType(Enum):
    """
    Converter control types
    """
    Vm_dc = 'Vm_dc'
    Vm_ac = 'Vm_ac'
    Va_ac = 'Va_ac'
    Qac = 'Q_ac'
    Pdc = 'P_dc'
    Pac = 'P_ac'
    Pdc_angle_droop = 'P_dc_angle_droop'  # PMODE3
    Imax = 'Imax'

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return ConverterControlType[s]
        except KeyError:
            return s

    @classmethod
    def list(cls):
        """

        :return:
        """
        return list(map(lambda c: c.value, cls))


class HvdcControlType(Enum):
    """
    Simple HVDC control types
    """
    type_0_free = '0:Free'
    type_1_Pset = '1:Pdc'

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return HvdcControlType[s]
        except KeyError:
            return s

    @classmethod
    def list(cls):
        """

        :return:
        """
        return list(map(lambda c: c.value, cls))


class GenerationNtcFormulation(Enum):
    """
    NTC formulation type
    """
    Proportional = 'Proportional'
    Optimal = 'Optimal'


class TimeFrame(Enum):
    """
    Time frame
    """
    Continuous = 'Continuous'


class FaultType(Enum):
    """
    Short circuit type
    """
    LG = 'LG'
    LL = 'LL'
    LLG = 'LLG'
    LLL = 'LLL'
    LLLG = 'LLLG'

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return FaultType[s]
        except KeyError:
            return s

    @classmethod
    def list(cls):
        """

        :return:
        """
        return list(map(lambda c: c.value, cls))


class MethodShortCircuit(Enum):
    """
    Short circuit type
    """
    sequences = 'sequences'
    sequences_vsc = 'sequences_vsc'
    phases = 'phases'

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """
        :param s:
        :return:
        """
        try:
            return MethodShortCircuit[s]
        except KeyError:
            return s

    @classmethod
    def list(cls):
        """
        :return:
        """
        return list(map(lambda c: c.value, cls))


class PhasesShortCircuit(Enum):
    """
    Short circuit type
    """
    abc = 'abc'
    ab = 'ab'
    bc = 'bc'
    ca = 'ca'
    a = 'a'
    b = 'b'
    c = 'c'

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """
        :param s:
        :return:
        """
        try:
            return PhasesShortCircuit[s]
        except KeyError:
            return s

    @classmethod
    def list(cls):
        """
        :return:
        """
        return list(map(lambda c: c.value, cls))


class WindingsConnection(Enum):
    """
    Transformer windings connection types
    """
    # G: grounded star
    # S: ungrounded star
    # D: delta
    GG = 'GG'
    GS = 'GS'
    GD = 'GD'
    SS = 'SS'
    SD = 'SD'
    DD = 'DD'

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return WindingsConnection[s]
        except KeyError:
            return s

    @classmethod
    def list(cls):
        """

        :return:
        """
        return list(map(lambda c: c.value, cls))


class TerminalType(Enum):
    """
    Terminal types
    """
    # AC: AC converter side
    # DC+: DC+ converter side
    # DC-: DC- converter side
    # OTHER: Other terminal type such as in transformer3w
    AC = 'AC'
    DC_P = 'DC+'
    DC_N = 'DC-'
    OTHER = 'Other'

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return TerminalType[s]
        except KeyError:
            return s

    @classmethod
    def list(cls):
        """

        :return:
        """
        return list(map(lambda c: c.value, cls))


class WindingType(Enum):
    """
    Transformer windings connection types
    """
    FloatingStar = "Y"
    GroundedStar = "Yg"
    NeutralStar = "Yn"
    Delta = "D"
    ZigZag = "Z"

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return WindingType[s]
        except KeyError:
            return s

    @classmethod
    def list(cls):
        """

        :return:
        """
        return list(map(lambda c: c.value, cls))


class ShuntConnectionType(Enum):
    """
    Loads, shunts, etc.. connection types
    """
    FloatingStar = "Y"
    GroundedStar = "Yg"
    NeutralStar = "Yn"
    Delta = "D"

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return ShuntConnectionType[s]
        except KeyError:
            return s

    @classmethod
    def list(cls):
        """

        :return:
        """
        return list(map(lambda c: c.value, cls))


class ActionType(Enum):
    """
    ActionType
    """
    NoAction = 'No action'
    Add = 'Add'
    Modify = 'Modify'
    Delete = 'Delete'

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return ActionType[s]
        except KeyError:
            return s

    @classmethod
    def list(cls):
        """

        :return:
        """
        return list(map(lambda c: c.value, cls))


# class GpfControlType(Enum):
#     """
#     GENERALISED PF Control types
#     """
#     type_None = '0:None'
#     type_Vm = '1:Vm'
#     type_Va = '2:Va'
#     type_Pzip = '3:Pzip'
#     type_Qzip = '4:Qzip'
#     type_Pf = '5:Pf'
#     type_Qf = '6:Qf'
#     type_Pt = '7:Pt'
#     type_Qt = '8:Qt'
#     type_TapMod = '9:m'
#     type_TapAng = '10:tau'
#
#     def __str__(self) -> str:
#         return str(self.value)
#
#     def __repr__(self):
#         return str(self)
#
#     @staticmethod
#     def argparse(s):
#         """
#         :param s:
#         :return:
#         """
#         try:
#             return GpfControlType[s]
#         except KeyError:
#             return s
#
#     @classmethod
#     def list(cls):
#         """
#         :return:
#         """
#         return list(map(lambda c: c.value, cls))


class DeviceType(Enum):
    """
    Device types
    """
    NoDevice = 'NoDevice'
    TimeDevice = 'Time'
    CircuitDevice = 'Circuit'
    BusDevice = 'Bus'
    BranchDevice = 'Branch'
    BranchTypeDevice = 'Branch template'
    LineDevice = 'Line'
    LineTypeDevice = 'Line Template'
    Transformer2WDevice = 'Transformer'
    Transformer3WDevice = 'Transformer3W'
    WindingDevice = 'Winding'
    SeriesReactanceDevice = 'Series reactance'
    HVDCLineDevice = 'HVDC Line'
    DCLineDevice = 'DC line'
    VscDevice = 'VSC'
    BatteryDevice = 'Battery'
    LoadDevice = 'Load'
    CurrentInjectionDevice = 'Current injection'
    ControllableShuntDevice = 'Controllable shunt'
    GeneratorDevice = 'Generator'
    StaticGeneratorDevice = 'Static Generator'
    ShuntDevice = 'Shunt'
    ShuntLikeDevice = 'Shunt like devices'
    UpfcDevice = 'UPFC'  # unified power flow controller
    ExternalGridDevice = 'External grid'
    LoadLikeDevice = 'Load like'
    BranchGroupDevice = 'Branch group'
    LambdaDevice = r"Loading from the base situation ($\lambda$)"
    ExciterDevice = "Exciter"
    GovernorDevice = "Governor"
    StabilizerDevice = "Stabilizer"

    PMeasurementDevice = 'Pi Measurement'
    QMeasurementDevice = 'Qi Measurement'
    PgMeasurementDevice = 'Pg Measurement'
    QgMeasurementDevice = 'Qg Measurement'
    PfMeasurementDevice = 'Pf Measurement'
    QfMeasurementDevice = 'Qf Measurement'
    PtMeasurementDevice = 'Pt Measurement'
    QtMeasurementDevice = 'Qt Measurement'
    VmMeasurementDevice = 'Vm Measurement'
    VaMeasurementDevice = 'Va Measurement'
    IfMeasurementDevice = 'If Measurement'
    ItMeasurementDevice = 'It Measurement'

    WireDevice = 'Wire'
    SequenceLineDevice = 'Sequence line'
    UnderGroundLineDevice = 'Underground line'
    OverheadLineTypeDevice = 'Tower'
    AnyLineTemplateDevice = "Any line template"
    TransformerTypeDevice = 'Transformer type'
    SwitchDevice = 'Switch'

    GenericArea = 'Generic Area'
    SubstationDevice = 'Substation'
    AreaDevice = 'Area'
    ZoneDevice = 'Zone'
    CountryDevice = 'Country'
    CommunityDevice = 'Community'
    RegionDevice = 'Region'
    MunicipalityDevice = 'Municipality'
    BusBarDevice = 'BusBar'
    VoltageLevelDevice = 'Voltage level'
    VoltageLevelTemplate = 'Voltage level template'

    Technology = 'Technology'
    TechnologyGroup = 'Technology Group'
    TechnologyCategory = 'Technology Category'
    Owner = 'Owner'

    ContingencyDevice = 'Contingency'
    ContingencyGroupDevice = 'Contingency Group'

    RemedialActionDevice = 'Remedial action'
    RemedialActionGroupDevice = 'Remedial action Group'

    ShortCircuitEvent = 'Short circuit event'

    InvestmentDevice = 'Investment'
    InvestmentsGroupDevice = 'Investments Group'

    FuelDevice = 'Fuel'
    EmissionGasDevice = 'Emission'

    GeneratorEmissionAssociation = 'Generator Emission'
    GeneratorFuelAssociation = 'Generator Fuel'
    GeneratorTechnologyAssociation = 'Generator Technology'

    DiagramDevice = 'Diagram'

    FluidInjectionDevice = 'Fluid Injection'
    FluidTurbineDevice = 'Fluid Turbine'
    FluidPumpDevice = 'Fluid Pump'
    FluidP2XDevice = 'Fluid P2X'
    FluidPathDevice = 'Fluid path'
    FluidNodeDevice = 'Fluid node'

    LineLocation = "Line Location"
    LineLocations = "Line Locations"

    ModellingAuthority = "Modelling Authority"

    FacilityDevice = "Facility"

    SimulationOptionsDevice = "SimulationOptionsDevice"

    InterAggregationInfo = "InterAggregationInfo"

    BusOrBranch = "BusOrBranch"

    DynamicModelHostDevice = "Dynamic Model Host"

    RmsModelTemplateDevice = "RMS template"
    RmsEventDevice = "Rms Event"
    RmsEventsGroupDevice = "Rms Events Group"

    VarFactory = "Var Factory"

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return DeviceType[s]
        except KeyError:
            return s

    @classmethod
    def list(cls):
        """

        :return:
        """
        return list(map(lambda c: c.value, cls))


class SubObjectType(Enum):
    """
    Types of objects that act as complicated variable types
    """
    Profile = "Profile"
    GeneratorQCurve = 'Generator Q curve'
    LineLocations = 'Line locations'
    TapChanger = 'Tap changer'
    Array = "Array"
    ObjectsList = "ObjectsList"
    Associations = "AssociationsList"
    ListOfWires = 'ListOfWires'
    AdmittanceMatrix = "Admittance Matrix"
    DynamicModelHostType = "DynamicModuleHost"
    DaeBlockType = "DaeBlock"
    VarType = "VarType"
    ConstType = "ConstType"

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return SubObjectType[s]
        except KeyError:
            return s

    @classmethod
    def list(cls):
        """

        :return:
        """
        return list(map(lambda c: c.value, cls))


class TapChangerTypes(Enum):
    """
    Types of objects that act as complicated variable types
    """
    NoRegulation = 'NoRegulation'
    VoltageRegulation = "VoltageRegulation"
    Asymmetrical = 'Asymmetrical'
    Symmetrical = 'Symmetrical'

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return TapChangerTypes[s]
        except KeyError:
            return s

    @classmethod
    def list(cls):
        """

        :return:
        """
        return list(map(lambda c: c.value, cls))


class BuildStatus(Enum):
    """
    Asset build status options
    """
    Commissioned = 'Commissioned'  # Already there, not planned for decommissioning
    Decommissioned = 'Decommissioned'  # Already retired (does not exist)
    Planned = 'Planned'  # Planned for commissioning some time, does not exist yet)
    Candidate = 'Candidate'  # Candidate for commissioning, does not exist yet, might be selected for commissioning
    PlannedDecommission = 'PlannedDecommission'  # Already there, but it has been selected for decommissioning

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return BuildStatus[s]
        except KeyError:
            return s

    @classmethod
    def list(cls):
        """

        :return:
        """
        return list(map(lambda c: c.value, cls))


class StudyResultsType(Enum):
    """
    Types of simulation results
    """
    PowerFlow = 'PowerFlow'
    PowerFlowTimeSeries = 'PowerFlowTimeSeries'
    OptimalPowerFlow = 'PowerFlow'
    OptimalPowerFlowTimeSeries = 'PowerFlowTimeSeries'
    ShortCircuit = 'ShortCircuit'
    ContinuationPowerFlow = 'ContinuationPowerFlow'
    ContingencyAnalysis = 'ContingencyAnalysis'
    ContingencyAnalysisTimeSeries = 'ContingencyAnalysisTimeSeries'
    SigmaAnalysis = 'SigmaAnalysis'
    LinearAnalysis = 'LinearAnalysis'
    LinearAnalysisTimeSeries = 'LinearAnalysisTimeSeries'
    AvailableTransferCapacity = 'AvailableTransferCapacity'
    AvailableTransferCapacityTimeSeries = 'AvailableTransferCapacityTimeSeries'
    Clustering = 'Clustering'
    StateEstimation = 'StateEstimation'
    InputsAnalysis = 'InputsAnalysis'
    InvestmentEvaluations = 'InvestmentEvaluations'
    NetTransferCapacity = 'NetTransferCapacity'
    NetTransferCapacityTimeSeries = 'NetTransferCapacityTimeSeries'
    StochasticPowerFlow = 'StochasticPowerFlow'
    RmsSimulation = "RmsSimulation"
    SmallSignalStability = "SmallSignalStability"

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return StudyResultsType[s]
        except KeyError:
            return s

    @classmethod
    def list(cls):
        """

        :return:
        """
        return list(map(lambda c: c.value, cls))


class AvailableTransferMode(Enum):
    """
    AvailableTransferMode
    """

    Generation = "Generation"
    InstalledPower = "InstalledPower"
    Load = "Load"
    GenerationAndLoad = "GenerationAndLoad"

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return AvailableTransferMode[s]
        except KeyError:
            return s

    @classmethod
    def list(cls):
        """

        :return:
        """
        return list(map(lambda c: c.value, cls))


class InvestmentsEvaluationObjectives(Enum):
    """
    Types of investment optimization objectives
    """
    PowerFlow = 'PowerFlow'
    TimeSeriesPowerFlow = 'TimeSeriesPowerFlow'
    # OptimalPowerFlow = 'OptimalPowerFlow'
    # TimeSeriesOptimalPowerFlow = 'TimeSeriesOptimalPowerFlow'
    GenerationAdequacy = "Adequacy"
    SimpleDispatch = "Simple dispatch"
    FromPlugin = 'From Plugin'

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return InvestmentsEvaluationObjectives[s]
        except KeyError:
            return s

    @classmethod
    def list(cls):
        """

        :return:
        """
        return list(map(lambda c: c.value, cls))


class LogSeverity(Enum):
    """
    Enumeration of logs severities
    """
    Error = 'Error'
    Warning = 'Warning'
    Information = 'Information'
    Divergence = 'Divergence'

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return LogSeverity[s]
        except KeyError:
            return s


class FileType(Enum):
    """
    Enumeration of logs severities
    """
    VeraGrid = "VeraGrid"
    VeraGrid_xlsx1 = "VeraGrid Excel 1"
    VeraGrid_xlsx2 = "VeraGrid Excel 2"
    VeraGrid_xlsx3 = "VeraGrid Excel 3"
    VeraGrid_xlsx4 = "VeraGrid Excel 4"
    VeraGrid_delta = "VeraGrid Delta"
    VeraGrid_sqlite = "VeraGrid SQLite"
    VeraGrid_h5 = "VeraGrid H5"
    VeraGrid_json = "VeraGrid Json"
    VeraGrid_ejson3 = "Ejson3"
    Matpower = "Matpower"
    DPX = "DPX"
    PWF = "PWF"
    EPC = "EPC"
    PyPsa_h5 = "PyPSA H5"
    PyPsa = "PyPsa"
    PandaPower = "Pandapower"
    Iidm = "Iidm"
    PSSE_raw = "PSS/e raw"
    PSSE_rawx = "PSS/e rawx"
    DGS = "DGS"
    CGMES = 'CGMES'
    CIM = "CIM"
    UCTE = 'UCTE'
    RTE_xml = "RTE_XML"
    IPA = "IPA"
    PGM = "Power grid models"
    generic_excel = "Generic Excel"

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return FileType[s]
        except KeyError:
            return s

class CGMESVersions(Enum):
    """
    Enumeration of logs severities
    """
    v2_4_15 = '2.4.15'
    v3_0_0 = '3.0.0'

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return CGMESVersions[s]
        except KeyError:
            return s


class CgmesTopologyMode(Enum):
    """
    Topology conversion mode for CGMES imports.
    """
    Auto = "Auto"
    ConnectivityNode = "ConnectivityNode"
    TopologicalNode = "TopologicalNode"

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return CgmesTopologyMode[s]
        except KeyError:
            return s


class SparseSolver(Enum):
    """
    Sparse solvers to use
    """
    ILU = 'ILU'
    KLU = 'KLU'
    SuperLU = 'SuperLU'
    Pardiso = 'Pardiso'
    GMRES = 'GMRES'
    UMFPACK = 'UmfPack'
    UMFPACKTriangular = 'UmfPackTriangular'

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return CGMESVersions[s]
        except KeyError:
            return s


class NodalCapacityMethod(Enum):
    """
    Sparse solvers to use
    """
    NonlinearOptimization = 'Nonlinear Optimization'
    LinearOptimization = 'Linear Optimization'
    CPF = "Continuation power flow"

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return NodalCapacityMethod[s]
        except KeyError:
            return s


class ResultTypes(Enum):
    """
    ResultTypes
    """
    # Power flow
    BusActivePower = 'P: Active power'

    BusActivePowerA = 'PA: Active power A'
    BusActivePowerB = 'PB: Active power B'
    BusActivePowerC = 'PC: Active power C'

    BusReactivePower = 'Q: Reactive power'

    BusReactivePowerA = 'QA: Reactive power A'
    BusReactivePowerB = 'QB: Reactive power B'
    BusReactivePowerC = 'QC: Reactive power C'

    BusActivePowerIncrement = "ΔP: Active power increment"

    BranchActivePowerFrom = 'Pf: Active power "from"'
    BranchActivePowerFromA = 'PfA: Active power "from" A'
    BranchActivePowerFromB = 'PfB: Active power "from" B'
    BranchActivePowerFromC = 'PfC: Active power "from" C'

    BranchReactivePowerFrom = 'Qf: Reactive power "from"'
    BranchReactivePowerFromA = 'QfA: Reactive power "from" A'
    BranchReactivePowerFromB = 'QfB: Reactive power "from" B'
    BranchReactivePowerFromC = 'QfC: Reactive power "from" C'

    BranchActivePowerTo = 'Pt: Active power "to"'
    BranchActivePowerToA = 'Pt: Active power "to" A'
    BranchActivePowerToB = 'Pt: Active power "to" B'
    BranchActivePowerToC = 'Pt: Active power "to" C'

    BranchReactivePowerTo = 'Qt: Reactive power "to"'
    BranchReactivePowerToA = 'Qt: Reactive power "to" A'
    BranchReactivePowerToB = 'Qt: Reactive power "to" B'
    BranchReactivePowerToC = 'Qt: Reactive power "to" C'

    BranchActiveCurrentFrom = 'Irf: Active current "from"'
    BranchActiveCurrentFromA = 'Irf: Active current "from" A'
    BranchActiveCurrentFromB = 'Irf: Active current "from" B'
    BranchActiveCurrentFromC = 'Irf: Active current "from" C'

    BranchReactiveCurrentFrom = 'Iif: Reactive current "from"'
    BranchReactiveCurrentFromA = 'Iif: Reactive current "from" A'
    BranchReactiveCurrentFromB = 'Iif: Reactive current "from" B'
    BranchReactiveCurrentFromC = 'Iif: Reactive current "from" C'

    BranchActiveCurrentTo = 'Irt: Active current "to"'
    BranchActiveCurrentToA = 'Irt: Active current "to" A'
    BranchActiveCurrentToB = 'Irt: Active current "to" B'
    BranchActiveCurrentToC = 'Irt: Active current "to" C'

    BranchReactiveCurrentTo = 'Iit: Reactive current "to"'
    BranchReactiveCurrentToA = 'Iit: Reactive current "to" A'
    BranchReactiveCurrentToB = 'Iit: Reactive current "to" B'
    BranchReactiveCurrentToC = 'Iit: Reactive current "to" C'

    BranchTapModule = 'm: Tap module'
    BranchTapAngle = '𝜏: Tap angle'
    BranchBeq = 'Beq: Equivalent susceptance'

    BranchLoading = 'Branch Loading'
    BranchLoadingA = 'Branch Loading A'
    BranchLoadingB = 'Branch Loading B'
    BranchLoadingC = 'Branch Loading C'

    BranchVoltage = 'ΔV: Voltage modules drop'
    BranchVoltageA = 'ΔV: Voltage modules drop A'
    BranchVoltageB = 'ΔV: Voltage modules drop B'
    BranchVoltageC = 'ΔV: Voltage modules drop C'

    BranchAngles = 'Δθ: Voltage angles drop'
    BranchAnglesA = 'Δθ: Voltage angles drop A'
    BranchAnglesB = 'Δθ: Voltage angles drop B'
    BranchAnglesC = 'Δθ: Voltage angles drop C'

    BranchLosses = 'Branch losses'

    BranchActiveLosses = 'Pl: Active losses'
    BranchActiveLossesA = 'Pl: Active losses A'
    BranchActiveLossesB = 'Pl: Active losses B'
    BranchActiveLossesC = 'Pl: Active losses C'

    BranchReactiveLosses = 'Ql: Reactive losses'
    BranchReactiveLossesA = 'Ql: Reactive losses A'
    BranchReactiveLossesB = 'Ql: Reactive losses B'
    BranchReactiveLossesC = 'Ql: Reactive losses C'

    BranchActiveLossesPercentage = 'Pl: Active losses (%)'
    BranchActiveLossesPercentageA = 'Pl: Active losses (%) A'
    BranchActiveLossesPercentageB = 'Pl: Active losses (%) B'
    BranchActiveLossesPercentageC = 'Pl: Active losses (%) C'

    BatteryPower = 'Battery power'
    BatteryEnergy = 'Battery energy'

    HvdcLosses = 'HVDC losses'
    HvdcLoading = 'HVDC loading'

    HvdcPowerFrom = 'HVDC power "from"'
    HvdcPowerFromA = 'HVDC power "from" A'
    HvdcPowerFromB = 'HVDC power "from" B'
    HvdcPowerFromC = 'HVDC power "from" C'

    HvdcPowerTo = 'HVDC power "to"'
    HvdcPowerToA = 'HVDC power "to" A'
    HvdcPowerToB = 'HVDC power "to" B'
    HvdcPowerToC = 'HVDC power "to" C'

    VscLosses = 'Vsc losses'
    VscPowerFromPositive = 'Vsc power "from" positive pole'
    VscPowerFromNegative = 'Vsc power "from" negative pole'
    VscLoading = 'Vsc loading'

    VscPowerTo = 'Vsc power "to"'
    VscPowerToA = 'Vsc power "to" A'
    VscPowerToB = 'Vsc power "to" B'
    VscPowerToC = 'Vsc power "to" C'

    # StochasticPowerFlowDriver
    BusVoltageAverage = 'Bus voltage avg'
    BusVoltageStd = 'Bus voltage std'
    BusVoltageCDF = 'Bus voltage CDF'
    BusPowerCDF = 'Bus power CDF'
    BranchPowerAverage = 'Branch power avg'
    BranchPowerStd = 'Branch power std'
    BranchPowerCDF = 'Branch power CDF'
    BranchLoadingAverage = 'loading avg'
    BranchLoadingStd = 'Loading std'
    BranchLoadingCDF = 'Loading CDF'
    BranchLossesAverage = 'Losses avg'
    BranchLossesStd = 'Losses std'
    BranchLossesCDF = 'Losses CDF'

    # PF
    BusVoltageModule = 'V: Voltage module'

    BusVoltageModuleA = 'VA: Voltage module A'
    BusVoltageModuleB = 'VB: Voltage module B'
    BusVoltageModuleC = 'VC: Voltage module C'

    BusVoltageAngle = 'θ: Voltage angle'

    BusVoltageAngleA = 'θA: Voltage angle A'
    BusVoltageAngleB = 'θB: Voltage angle B'
    BusVoltageAngleC = 'θC: Voltage angle C'

    BusPower = 'Bus power'
    BusShadowPrices = 'Nodal shadow prices'
    BranchOverloads = 'Branch overloads'
    BranchOverloadsCost = 'Branch overloads cost'

    LoadPower = 'Load power'
    LoadShedding = 'Load shedding'
    LoadSheddingCost = "Load shedding cost"
    LoadNeutralVoltage = 'Load neutral voltage'

    GeneratorShedding = 'Generator shedding'
    GeneratorPower = 'Generator power'

    GeneratorReactivePower = 'Generator reactive power'
    GeneratorReactivePowerA = 'Generator reactive power A'
    GeneratorReactivePowerB = 'Generator reactive power B'
    GeneratorReactivePowerC = 'Generator reactive power C'

    GeneratorCost = 'Generator cost'
    GeneratorFuels = 'Generator fuels'
    GeneratorEmissions = 'Generator emissions'
    GeneratorProducing = 'Generator producing'
    GeneratorStartingUp = 'Generator starting up'
    GeneratorShuttingDown = 'Generator shutting down'
    GeneratorInvested = 'Generator invested'

    BatteryReactivePower = 'Battery reactive power'
    BatteryReactivePowerA = 'Battery reactive power A'
    BatteryReactivePowerB = 'Battery reactive power B'
    BatteryReactivePowerC = 'Battery reactive power C'

    BatteryInvested = 'Battery invested'

    ShuntReactivePower = 'Shunt reactive power'
    ShuntReactivePowerA = 'Shunt reactive power A'
    ShuntReactivePowerB = 'Shunt reactive power B'
    ShuntReactivePowerC = 'Shunt reactive power C'
    ShuntNeutralVoltage = 'Shunt neutral voltage'

    BusVoltagePolarPlot = 'Voltage plot'
    BusNodalCapacity = "Nodal capacity"

    # OPF-NTC
    HvdcOverloads = 'HVDC overloads'
    NodeSlacks = 'Nodal slacks'
    GenerationDelta = 'Generation deltas'
    GenerationDeltaSlacks = 'Generation delta slacks'
    InterAreaExchange = 'Inter-Area exchange'
    LossesPercentPerArea = 'Losses % per area'
    LossesPerArea = 'Losses per area'
    ActivePowerFlowPerArea = 'Active power flow per area'
    LossesPerGenPerArea = 'Losses per generation unit in area'
    InterSpaceBranchPower = "Inter-space branch power"
    InterSpaceBranchLoading = "Inter-space branch loading"

    SystemFuel = 'System fuel consumption'
    SystemEmissions = 'System emissions'
    SystemEnergyCost = 'System energy cost'
    SystemEnergyTotalCost = "System energy total cost"
    PowerByTechnology = "Power by technology"

    # NTC TS
    OpfNtcTsContingencyReport = 'Contingency flow report'
    OpfNtcTsBaseReport = 'Base flow report'

    # Short-circuit
    BusShortCircuitActivePower = 'Short circuit active power'
    BusShortCircuitActivePowerA = 'Short circuit active power A'
    BusShortCircuitActivePowerB = 'Short circuit active power B'
    BusShortCircuitActivePowerC = 'Short circuit active power C'

    BusShortCircuitReactivePower = 'Short circuit reactive power'
    BusShortCircuitReactivePowerA = 'Short circuit reactive power A'
    BusShortCircuitReactivePowerB = 'Short circuit reactive power B'
    BusShortCircuitReactivePowerC = 'Short circuit reactive power C'

    BusShortCircuitActiveCurrent = 'Short circuit active current'
    BusShortCircuitActiveCurrentA = 'Short circuit active current A'
    BusShortCircuitActiveCurrentB = 'Short circuit active current B'
    BusShortCircuitActiveCurrentC = 'Short circuit active current C'

    BusShortCircuitReactiveCurrent = 'Short circuit reactive current'
    BusShortCircuitReactiveCurrentA = 'Short circuit reactive current A'
    BusShortCircuitReactiveCurrentB = 'Short circuit reactive current B'
    BusShortCircuitReactiveCurrentC = 'Short circuit reactive current C'

    # PTDF
    PTDF = 'PTDF'
    PTDFBusVoltageSensitivity = 'Bus voltage sensitivity'
    LODF = 'LODF'
    HvdcPTDF = "HVDC PTDF"
    HvdcODF = "HVDC ODF"
    VscPTDF = "Vsc PTDF"
    VscODF = "Vsc ODF"

    MaxOverloads = 'Maximum contingency flow'
    ContingencyFlows = 'Contingency flow'
    ContingencyLoading = 'Contingency loading'
    MaxContingencyFlows = 'Max contingency flow'
    MaxContingencyLoading = 'Max contingency loading'

    ContingencyOverloadSum = 'Contingency overload sum'
    MeanContingencyOverLoading = 'Mean contingency overloading'
    StdDevContingencyOverLoading = 'Std-dev contingency overloading'

    ContingencyFrequency = 'Contingency frequency'
    ContingencyRelativeFrequency = 'Contingency relative frequency'

    SimulationError = 'Error'

    OTDFSimulationError = 'Error'

    # contingency analysis
    ContingencyAnalysisReport = 'Contingencies report'
    ContingencyStatisticalAnalysisReport = 'Contingencies statistical report'

    # Srap
    SrapUsedPower = 'Srap used power'

    # Hydro OPF
    FluidCurrentLevel = 'Reservoir fluid level'
    FluidFlowIn = 'Flow entering the node'
    FluidFlowOut = 'Flow exiting the node'
    FluidP2XFlow = 'Flow from the P2X'
    FluidSpillage = 'Spillage flow leaving'

    FluidFlowPath = 'Flow in the river'
    FluidFlowInjection = 'Flow circulating in the device'

    # OPF plots
    OpfBalancePlot = "Balance plot"
    OpfTechnologyPlot = "Technology plot"

    # sigma
    SigmaReal = 'Sigma real'
    SigmaImag = 'Sigma imaginary'
    SigmaDistances = 'Sigma distances'
    SigmaPlusDistances = 'Sigma + distances'

    # ATC
    AvailableTransferCapacityMatrix = 'Available transfer capacity'
    AvailableTransferCapacity = 'Available transfer capacity (final)'
    AvailableTransferCapacityN = 'Available transfer capacity (N)'
    AvailableTransferCapacityAlpha = 'Sensitivity to the exchange'
    AvailableTransferCapacityAlphaN1 = 'Sensitivity to the exchange (N-1)'
    NetTransferCapacity = 'Net transfer capacity'
    AvailableTransferCapacityReport = 'ATC Report'

    BaseFlowReport = 'Ntc: Base flow report'
    ContingencyFlowsReport = 'Ntc: Contingency flow report'
    ContingencyFlowsBranchReport = 'Ntc: Contingency flow report. (Branch)'
    ContingencyFlowsGenerationReport = 'Ntc: Contingency flow report. (Generation)'
    ContingencyFlowsHvdcReport = 'Ntc: Contingency flow report. (Hvdc)'

    # Time series
    TsBaseFlowReport = 'Time series base flow report'
    TsContingencyFlowReport = 'Time series contingency flow report'
    TsContingencyFlowBranchReport = 'Time series Contingency flow report (Branches)'
    TsContingencyFlowGenerationReport = 'Time series contingency flow report. (Generation)'
    TsContingencyFlowHvdcReport = 'Time series contingency flow report. (Hvdc)'
    TsGenerationPowerReport = 'Time series generation power report'
    TsGenerationDeltaReport = 'Time series generation delta power report'
    TsAlphaReport = 'Time series sensitivity to the exchange report'
    TsWorstAlphaN1Report = 'Time series worst sensitivity to the exchange report (N-1)'
    TsBranchMonitoring = 'Time series branch monitoring logic report'
    TsCriticalBranches = 'Time series critical Branches report'
    TsContingencyBranches = 'Time series contingency Branches report'

    # Clustering
    ClusteringReport = 'Clustering time series report'

    # RMS Simulation

    RmsSimulationReport = 'Rms time series report'
    RmsPlotResults = 'Rms plot results'

    # RmsGeneratorResults = 'Rms Generator results'
    # RmsLineResults = 'Rms Line results'
    # RmsLoadResults = 'Rms load results'
    #
    #
    # RmsGeneratorOmegaResults = 'Rms Genqec omega results'
    # RmsGeneratorDeltaResults = 'Rms Genqec delta results'
    #
    # RmsLoadPResults = 'Rms Load P results'
    # RmsLoadQResults = 'Rms Load Q results'
    #
    # RmsLinePResults = 'Rms Simple Line P results'
    # RmsLineQResults = 'Rms Simple Line Q results'

    # Small Signal Stability
    ParticipationFactors = "Participation Factors"
    StateMatrix = "State Matrix"
    Modes = "Modes"
    SDomainPlot = "S-Domain Plot"
    SDomainPlotHz = "S-Domain Plot in Hz"

    # inputs analysis
    ZoneAnalysis = 'Zone analysis'
    CountryAnalysis = 'Country analysis'
    AreaAnalysis = 'Area analysis'

    AreaGenerationAnalysis = 'Area generation analysis'
    ZoneGenerationAnalysis = 'Zone generation analysis'
    CountryGenerationAnalysis = 'Country generation analysis'

    AreaLoadAnalysis = 'Area load analysis'
    ZoneLoadAnalysis = 'Zone load analysis'
    CountryLoadAnalysis = 'Country load analysis'

    AreaBalanceAnalysis = 'Area balance analysis'
    ZoneBalanceAnalysis = 'Zone balance analysis'
    CountryBalanceAnalysis = 'Country balance analysis'

    # Short circuit
    BusVoltageModule0 = 'Voltage module (0)'
    BusVoltageAngle0 = 'Voltage angle (0)'
    BranchActivePowerFrom0 = 'Branch active power "from" (0)'
    BranchReactivePowerFrom0 = 'Branch reactive power "from" (0)'
    BranchActiveCurrentFrom0 = 'Branch active current "from" (0)'
    BranchReactiveCurrentFrom0 = 'Branch reactive current "from" (0)'
    BranchLoading0 = 'Branch loading (0)'
    BranchActiveLosses0 = 'Branch active losses (0)'
    BranchReactiveLosses0 = 'Branch reactive losses (0)'

    BusVoltageModule1 = 'Voltage module (1)'
    BusVoltageAngle1 = 'Voltage angle (1)'
    BranchActivePowerFrom1 = 'Branch active power "from" (1)'
    BranchReactivePowerFrom1 = 'Branch reactive power "from" (1)'
    BranchActiveCurrentFrom1 = 'Branch active current "from" (1)'
    BranchReactiveCurrentFrom1 = 'Branch reactive current "from" (1)'
    BranchLoading1 = 'Branch loading (1)'
    BranchActiveLosses1 = 'Branch active losses (1)'
    BranchReactiveLosses1 = 'Branch reactive losses (1)'

    BusVoltageModule2 = 'Voltage module (2)'
    BusVoltageAngle2 = 'Voltage angle (2)'
    BranchActivePowerFrom2 = 'Branch active power "from" (2)'
    BranchReactivePowerFrom2 = 'Branch reactive power "from" (2)'
    BranchActiveCurrentFrom2 = 'Branch active current "from" (2)'
    BranchReactiveCurrentFrom2 = 'Branch reactive current "from" (2)'
    BranchLoading2 = 'Branch loading (2)'
    BranchActiveLosses2 = 'Branch active losses (2)'
    BranchReactiveLosses2 = 'Branch reactive losses (2)'
    BranchMonitoring = 'Branch monitoring logic'

    # BusVoltageModuleA = 'Voltage module (A)'
    # BusVoltageAngleA = 'Voltage angle (A)'
    # BranchActivePowerFromA = 'Branch active power "from" (A)'
    # BranchReactivePowerFromA = 'Branch reactive power "from" (A)'
    # BranchActiveCurrentFromA = 'Branch active current "from" (A)'
    # BranchReactiveCurrentFromA = 'Branch reactive current "from" (A)'
    # BranchLoadingA = 'Branch loading (A)'
    # BranchActiveLossesA = 'Branch active losses (A)'
    # BranchReactiveLossesA = 'Branch reactive losses (A)'
    #
    # BusVoltageModuleB = 'Voltage module (B)'
    # BusVoltageAngleB = 'Voltage angle (B)'
    # BranchActivePowerFromB = 'Branch active power "from" (B)'
    # BranchReactivePowerFromB = 'Branch reactive power "from" (B)'
    # BranchActiveCurrentFromB = 'Branch active current "from" (B)'
    # BranchReactiveCurrentFromB = 'Branch reactive current "from" (B)'
    # BranchLoadingB = 'Branch loading (B)'
    # BranchActiveLossesB = 'Branch active losses (B)'
    # BranchReactiveLossesB = 'Branch reactive losses (B)'
    #
    # BusVoltageModuleC = 'Voltage module (C)'
    # BusVoltageAngleC = 'Voltage angle (C)'
    # BranchActivePowerFromC = 'Branch active power "from" (C)'
    # BranchReactivePowerFromC = 'Branch reactive power "from" (C)'
    # BranchActiveCurrentFromC = 'Branch active current "from" (C)'
    # BranchReactiveCurrentFromC = 'Branch reactive current "from" (C)'
    # BranchLoadingC = 'Branch loading (C)'
    # BranchActiveLossesC = 'Branch active losses (C)'
    # BranchReactiveLossesC = 'Branch reactive losses (C)'

    ShortCircuitInfo = 'Short-circuit information'

    # classifiers
    SystemResults = 'System'
    BusResults = 'Bus'
    BranchResults = 'Branch'
    HvdcResults = 'Hvdc'
    VscResults = 'Vsc'
    AreaResults = 'Area'
    InfoResults = 'Information'
    ReportsResults = 'Reports'
    ParetoResults = 'Pareto'
    SlacksResults = 'Slacks'
    DispatchResults = 'Dispatch'
    FlowReports = 'Flow Reports'
    Sensibilities = 'Sensibilities'
    SeriesResults = 'Series'
    SnapshotResults = 'Snapshot'
    NTCResults = 'NTC'
    SpecialPlots = 'Special plots'
    GeneratorResults = 'Generators'
    LoadResults = 'Loads'
    BatteryResults = 'Batteries'
    ShuntResults = 'Shunt like devices'
    StatisticResults = 'Statistics'

    # fluid
    FluidNodeResults = 'Fluid nodes'
    FluidPathResults = 'Fluid paths'
    FluidInjectionResults = 'Fluid injections'
    FluidTurbineResults = 'Fluid turbines'
    FluidPumpResults = 'Fluid pumps'
    FluidP2XResults = 'Fluid P2Xs'

    # investments evaluation
    InvestmentsReportResults = 'Evaluation report'
    InvestmentsFrequencyResults = "Frequency"
    InvestmentsCombinationsResults = "Combinations"
    InvestmentsObjectivesResults = "Objectives"

    InvestmentsParetoReportResults = 'Pareto evaluation report'
    InvestmentsParetoFrequencyResults = "Pareto frequency"
    InvestmentsParetoCombinationsResults = "Pareto combinations"
    InvestmentsParetoObjectivesResults = "Pareto objectives"

    InvestmentsParetoPlot = 'Pareto plots'
    InvestmentsIterationsPlot = 'Iterations plot'
    InvestmentsParetoPlotNSGA2 = 'Pareto plot NSGA2'
    InvestmentsWhenToMakePlot = "When to make them plot"

    # reliability
    ReliabilityLOLEResults = "LOLE"
    ReliabilityENSResults = "ENS"
    ReliabilityLOLFResults = "LOLF"
    ReliabilityLOLETResults = "LOLET"
    ReliabilityLOLFTResults = "LOLFT"



    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self.value)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return ResultTypes[s]
        except KeyError:
            return s


class SimulationTypes(Enum):
    """
    Enumeration of simulation types
    """
    DesignView = 'Design View'
    TemplateDriver = 'Template'
    PowerFlow_run = 'Power flow'
    PowerFlow3ph_run = 'Power flow 3ph'
    StateEstimation_run = 'State estimation'
    ShortCircuit_run = 'Short circuit'
    MonteCarlo_run = 'Monte Carlo'
    PowerFlowTimeSeries_run = 'Power flow time series'
    ClusteringAnalysis_run = 'Clustering Analysis'
    CleanRoom_run = 'Clean room'
    ContinuationPowerFlow_run = 'Voltage collapse'
    LatinHypercube_run = 'Latin Hypercube'
    StochasticPowerFlow = 'Stochastic Power Flow'
    Cascade_run = 'Cascade'
    OPF_run = 'Optimal power flow'
    OPF_NTC_run = 'Optimal net transfer capacity'
    OPF_NTC_TS_run = 'Optimal net transfer capacity time series'
    OPFTimeSeries_run = 'Optimal power flow time series'
    TransientStability_run = 'Transient stability'
    TopologyReduction_run = 'Topology reduction'
    LinearAnalysis_run = 'Linear analysis'
    LinearAnalysis_TS_run = 'Linear analysis time series'
    NonLinearAnalysis_run = 'Nonlinear analysis'
    NonLinearAnalysis_TS_run = 'Nonlinear analysis time series'
    ContingencyAnalysis_run = 'Contingency analysis'
    ContingencyAnalysisTS_run = 'Contingency analysis time series'
    Delete_and_reduce_run = 'Delete and reduce'
    NetTransferCapacity_run = 'Available transfer capacity'
    NetTransferCapacityTS_run = 'Available transfer capacity time series'
    SigmaAnalysis_run = "Sigma Analysis"
    NodeGrouping_run = "Node groups"
    InputsAnalysis_run = 'Inputs Analysis'
    OptimalNetTransferCapacityTimeSeries_run = 'Optimal net transfer capacity time series'
    InvestmentsEvaluation_run = 'Investments evaluation'
    TopologyProcessor_run = 'Topology Processor'
    NodalCapacityTimeSeries_run = 'Nodal capacity time series'
    Reliability_run = "Reliability"
    RmsDynamic_run = "RMS Dynamic"
    SmallSignal_run = "Small Signal stability"
    EmtDynamic_run = "EMT Dynamic"

    FileOpen = "file open"
    FileSave = "file save"
    ExportAll = "export all"

    NoSim = "No simulation"

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return SimulationTypes[s]
        except KeyError:
            return s


class JobStatus(Enum):
    """
    Job status types
    """
    Done = 'Done'
    Running = 'Running'
    Failed = "Failed"
    Waiting = "Waiting"
    Cancelled = "Cancelled"

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return JobStatus[s]
        except KeyError:
            return s


class ContingencyFilteringMethods(Enum):
    """
    Contingency filtering methods
    """
    AllActive = "All active contingencies"
    Country = "Country"
    Community = "Community"
    Region = "Region"
    Municipality = "Municipality"
    Zone = "Zone"
    Area = "Area"
    SensitiveToMonitored = "Sensitive to monitored"

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return ContingencyFilteringMethods[s]
        except KeyError:
            return s


class Colormaps(Enum):
    """
    Available colormaps
    """
    VeraGrid = 'VeraGrid'
    TSO = 'TSO'  # -1, 1
    TSO2 = 'TSO 2'  # -1, 1
    SCADA = 'SCADA'  # -1, 1
    Heatmap = 'Heatmap'  # 0, 1
    Blues = 'Blue'  # 0, 1
    Greens = 'Green'  # 0, 1
    Blue2Gray = 'Blue to gray'  # 0, 1
    Green2Red = 'Green to red'  # -1, 1
    Red2Blue = 'Red to blue'  # -1, 1

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return Colormaps[s]
        except KeyError:
            return s


class VoltageLevelTypes(Enum):
    """
    Types of substation types
    """
    SingleBar = 'Single bar'
    SingleBarWithBypass = 'Single bar with bypass'
    SingleBarWithSplitter = 'Single bar with splitter'
    DoubleBar = "Double bar"
    DoubleBarWithBypass = "Double bar with bypass"
    DoubleBarWithTransference = "Double bar with transference bar"
    DoubleBarDuplex = "Double bar duplex"
    Ring = 'Ring'
    BreakerAndAHalf = 'Breaker and a half'

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return VoltageLevelTypes[s]
        except KeyError:
            return s

    @classmethod
    def list(cls):
        """

        :return:
        """
        return list(map(lambda c: c.value, cls))


class ContingencyOperationTypes(Enum):
    """
    Types of contingency operations
    """
    Active = 'active'
    PowerPercentage = '%'

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        if s == 'status':
            return ContingencyOperationTypes.Active

        try:
            return ContingencyOperationTypes[s]
        except KeyError:
            return s

    @classmethod
    def list(cls):
        """

        :return:
        """
        return list(map(lambda c: c.value, cls))


class BranchGroupTypes(Enum):
    """
    Branch group types
    """
    LineSegmentsGroup = 'Line segments group'
    TransformerGroup = 'Transformer group'
    GenericGroup = "Generic group"

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return BranchGroupTypes[s]
        except KeyError:
            return s

    @classmethod
    def list(cls):
        """

        :return:
        """
        return list(map(lambda c: c.value, cls))


class CascadeType(Enum):
    PowerFlow = "PowerFlow",
    LatinHypercube = "LHS"

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return CascadeType[s]
        except KeyError:
            return s

    @classmethod
    def list(cls):
        """

        :return:
        """
        return list(map(lambda c: c.value, cls))

class DynamicIntegrationMethod(Enum):
    """
    Dynamic integration methods.
    """
    # Implicit time-stepping (DAE form)
    DaeTrapezoidal = "DAE_Trapezoidal"
    DaeBackEuler = "DAE_BackEuler"
    DaeBDF2 = "DAE_bdf2"
    DaeContinuous = "DAE_Continuous"

    # Explicit time-stepping (ODE form)
    OdeRungeKutta4 = "ODE_Runge_Kutta 4"
    OdeEuler = "ODE_Euler"

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        try:
            return DynamicIntegrationMethod[s]
        except KeyError:
            return s

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class EmtSolverTypes(Enum):
    """
    Jacobian construction backends for implicit solvers.
    """
    Symbolic = "symbolic"  # Symbolic differentiation (SD)
    Automatic = "automatic"  # Sparse forward-mode AD + graph coloring
    StructuralAD = "structuralAD"  # Sparse structural automatic differentiation

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return EmtSolverTypes[s]
        except KeyError:
            return s

    @classmethod
    def list(cls):
        """

        :return:
        """
        return list(map(lambda c: c.value, cls))


class SmallSignalEmtBuildTypes(Enum):
    """
    Jacobian construction backends for implicit solvers.
    """
    Arnoldi = "Arnoldi"
    HybridArnoldi = "Hybrid Arnoldi"

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return SmallSignalEmtBuildTypes[s]
        except KeyError:
            return s

    @classmethod
    def list(cls):
        """

        :return:
        """
        return list(map(lambda c: c.value, cls))


class RmsInitializationMethod(Enum):
    Explicit = "Explicit"
    PseudoTransient = "PseudoTransient"

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return RmsInitializationMethod[s]
        except KeyError:
            return s

    @classmethod
    def list(cls):
        """

        :return:
        """
        return list(map(lambda c: c.value, cls))


class GridReductionMethod(Enum):
    """
    GridReductionMethod
    """
    Ward = "Ward"
    DiShi = "DiShi"
    WardLinear = "Ward linear"
    PTDF = "PTDF"
    PTDFProjected = "PTDF projected"

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return GridReductionMethod[s]
        except KeyError:
            return s


class BusReductionMethod(Enum):
    """
    GridReductionMethod
    """
    Reduce = "Reduce"
    Keep = "Keep"

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return BusReductionMethod[s]
        except KeyError:
            return s


class VarPowerFlowRefferenceType(Enum):
    """
    VarPowerFlowRefferenceType
    """
    NOTHING = "nothing"
    Vm = "Vm"  # Bus voltage module in p.u.
    Va = "Va"  # Bus voltage angle in rad
    Vmf = "Vmf"  # Bus voltage module in p.u.
    Vaf = "Vaf"  # Bus voltage angle in rad
    Vmt = "Vmt"  # Bus voltage module in p.u.
    Vat = "Vat"  # Bus voltage angle in rad
    P = "P"  # Bus active power in p.u.
    Q = "Q"  # Bus reactive power in p.u.
    Pf = "Pf"  # Branch active power from in p.u.
    Qf = "Qf"  # Branch reactive power from in p.u.
    Pt = "Pt"  # Branch active power to in p.u.
    Qt = "Qt"  # Branch reactive power to in p.u.
    Vdc = "Vdc"  # Bus voltage for DC voltage in p.u.
    Idc = "Idc"  # Bus current for DC Bus in p.u.

    # from Power Flow 3ph
    v_N = "v_N"  # Bus voltage at phase N.
    v_A = "v_A"  # Bus voltage at phase A.
    v_B = "v_B"  # Bus voltage at phase B.
    v_C = "v_C"  # Bus voltage at phase C.
    d_v_N = "d_v_N"  # Bus voltage derivative at phase N.
    d_v_A = "d_v_A"  # Bus voltage derivative at phase A.
    d_v_B = "d_v_B"  # Bus voltage derivative at phase B.
    d_v_C = "d_v_C"  # Bus voltage derivative at phase C.

    i_N = "i_N"  # Injection current at phase N in p.u.
    i_A = "i_A"  # Injection current at phase A in p.u.
    i_B = "i_B"  # Injection current at phase B in p.u.
    i_C = "i_C"  # Injection current at phase C in p.u.
    theta = "theta"  # Rotor angle in a synchronous generator in rad

    P_N = "P_N"  # Bus active power in phase N in p.u.
    P_A = "P_A"  # Bus active power in phase A in p.u.
    P_B = "P_B"  # Bus active power in phase B in p.u.
    P_C = "P_C"  # Bus active power in phase C in p.u.
    Q_N = "Q_N"  # Bus reactive power in phase N in p.u.
    Q_A = "Q_A"  # Bus reactive power in phase A in p.u.
    Q_B = "Q_B"  # Bus reactive power in phase B in p.u.
    Q_C = "Q_C"  # Bus reactive power in phase C in p.u.

    Sf_A = "Sf_A"  # Branch power from in phase A in p.u.
    Sf_B = "Sf_B"  # Branch power from in phase B in p.u.
    Sf_C = "Sf_C"  # Branch power from in phase C in p.u.
    St_A = "St_A"  # Branch power from in phase A in p.u.
    St_B = "St_B"  # Branch power from in phase B in p.u.
    St_C = "St_C"  # Branch power from in phase C in p.u.

    if_N = "if_N"  # Branch current from in phase N in p.u.
    if_A = "if_A"  # Branch current from in phase A in p.u.
    if_B = "if_B"  # Branch current from in phase B in p.u.
    if_C = "if_C"  # Branch current from in phase C in p.u.
    it_N = "it_N"  # Branch current to in phase N in p.u.
    it_A = "it_A"  # Branch current to in phase A in p.u.
    it_B = "it_B"  # Branch current to in phase B in p.u.
    it_C = "it_C"  # Branch current to in phase C in p.u.

    # Phasor representation (real/imaginary components)
    Vr = "Vr"  # Bus voltage real part in p.u.
    Vi = "Vi"  # Bus voltage imaginary part in p.u.
    Vrf = "Vrf"  # From-bus voltage real part in p.u.
    Vif = "Vif"  # From-bus voltage imaginary part in p.u.
    Vrt = "Vrt"  # To-bus voltage real part in p.u.
    Vit = "Vit"  # To-bus voltage imaginary part in p.u.

    # Complex phasor representation (single complex variable)
    V_complex = "V_complex"  # Complex voltage phasor V = Vr + j*Vi
    Vf_complex = "Vf_complex"  # Complex voltage at from bus
    Vt_complex = "Vt_complex"  # Complex voltage at to bus
    I_complex = "I_complex"  # Complex current phasor I = Ir + j*Ii
    If_complex = "If_complex"  # Complex current at from bus
    It_complex = "It_complex"  # Complex current at to bus
    S_complex = "S_complex"  # Complex power S = P + j*Q
    Sf_complex = "Sf_complex"  # Complex power at from bus
    St_complex = "St_complex"  # Complex power at to bus

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return VarPowerFlowRefferenceType[s]
        except KeyError:
            return s


class ParamPowerFlowRefferenceType(Enum):
    """
    ParamPowerFlowRefferenceType
    """
    NOTHING = "nothing"
    #General
    dt = "dt"  # time step for dynamic simulations
    
    # Branch / load parameters
    g = "g"  # Branch resistance in per unit
    b = "b"  # Branch reactance in per unit
    bsh = "bsh"  # Branch shunt susceptance in per unit
    Pl0 = "Pl0"  # Load active power
    Ql0 = "Ql0"  # Load reactive power

    # 3phase load power
    Pl0_A = "Pl0_A"  # Load active power phase A
    Ql0_A = "Ql0_A"  # Load reactive power phase A
    Pl0_B = "Pl0_B"  # Load active power phase B
    Ql0_B = "Ql0_B"  # Load reactive power phase B
    Pl0_C = "Pl0_C"  # Load active power phase C
    Ql0_C = "Ql0_C"  # Load reactive power phase C

    # Machine / power flow parameters
    fn = "fn"
    ws = "ws"
    M = "M"
    D = "D"
    Rs = "Rs"
    Ra = "Ra"

    # Reactances
    Xd = "Xd"
    Xq = "Xq"
    Xd_prime = "Xd_prime"
    Xq_prime = "Xq_prime"
    Xd_2prime = "Xd_2prime"
    Xq_2prime = "Xq_2prime"
    Xl = "Xl"

    # Time constants
    Td0_prime = "Td0_prime"
    Tq0_prime = "Tq0_prime"
    Td0_2prime = "Td0_2prime"
    Tq0_2prime = "Tq0_2prime"

    # Auxiliary parameters
    Xd_prime_minus_Xl = "Xd_prime_minus_Xl"
    Xq_prime_minus_Xl = "Xq_prime_minus_Xl"
    Xdaux = "Xdaux"
    Xdaux2 = "Xdaux2"
    Xdaux3 = "Xdaux3"
    Xqaux = "Xqaux"
    Xqaux2 = "Xqaux2"
    Xqaux3 = "Xqaux3"

    # Control / extra parameters
    A = "A"
    B = "B"

    # Governor / control gains and limits
    K = "K"  # governor gain (inverse droop)
    Pmax = "Pmax"  # max mechanical power (pu)
    Pmin = "Pmin"  # min mechanical power (pu)
    Uc = "Uc"  # max valve closing rate (pu/s)
    Uo = "Uo"  # max valve opening rate (pu/s)
    T_aux = "T_aux"

    # Control parameters
    Kp = "Kp"
    Ki = "Ki"
    omega_ref = "omega_ref"
    p0 = "p0"
    P0 = "P0"

    # Electrical / additional machine parameters
    R1 = "R1"
    X1 = "X1"
    freq = "freq"  # corresponds to Var("frequ")
    vf = "vf"
    tm0 = "tm0"



    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """

        :param s:
        :return:
        """
        try:
            return ParamPowerFlowRefferenceType[s]
        except KeyError:
            return s


class ReliabilityMode(Enum):
    """
    ReliabilityMode
    """
    GenerationAdequacy = "Generation Adequacy"
    GridMetrics = "Grid Metrics"

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """
        :param s:
        :return:
        """
        try:
            return ReliabilityMode[s]
        except KeyError:
            return s


class OpfDispatchMode(Enum):
    """
    OpfGenerationMode
    """
    Normal = "Normal"
    InterAreaRedispatch = "Inter-area redispatch"
    UnitCommitment = "Unit commitment"
    NodalCapacity = "Nodal capacity"
    GenerationExpansionPlanning = "Generation expansion planning"

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """
        :param s:
        :return:
        """
        try:
            return OpfDispatchMode[s]
        except KeyError:
            return s


class TimeSeriesSearchPoint(Enum):
    """
    TimeSeriesSearchPoint
    """
    HighestLoad = "Highest Load"
    LowestLoad = "Lowest load"

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """
        :param s:
        :return:
        """
        try:
            return TimeSeriesSearchPoint[s]
        except KeyError:
            return s


class EmtLineTypes(Enum):
    """
    EmtLineTypes
    """
    Bergeron = "Bergeron"
    J_Marti = "J_Marti"
    PI = "Pi"

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """
        :param s:
        :return:
        """
        try:
            return EmtLineTypes[s]
        except KeyError:
            return s


class BlockType(Enum):
    """
    this class contains the existing types of blocks
    """
    CONST = "CONST"
    GAIN = "GAIN"
    SUM = "SUM"
    SUBSTR = "SUBSTR"
    PRODUCT = "PRODUCT"
    DIVIDE = "Divide"
    ABS = "Abs"
    GENRAW = "GENRAW"
    GENQEC = "GENQEC"
    GOV = "Gov"
    STAB = "Stab"
    EXCITER = "Exciter"
    LINE = "Line"
    LOAD = "Load"
    GENERIC = "Generic"
    BUS_CONNECTION = "Bus Connection"
    EXTERNAL_MAPPING = "EXTERNAL_MAPPING"

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """
        :param s:
        :return:
        """
        try:
            return BlockType[s]
        except KeyError:
            return s



class ProceduralGridMethods(Enum):
    """
    this class contains the existing types of blocks
    """
    SteinerAlone = "Steiner tree"
    SteinerAndOptimization = "Steiner tree + optimization"

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        """
        :param s:
        :return:
        """
        try:
            return ProceduralGridMethods[s]
        except KeyError:
            return s