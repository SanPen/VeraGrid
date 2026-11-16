# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""CGMES Dynamics classes generated from ENTSO-E 61970-600-2 DY RDFS 2020."""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Tuple

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.base import Base
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty

class UnitMultiplier(Enum):
    """RDF enumeration UnitMultiplier."""

    y = 'y'
    z = 'z'
    a = 'a'
    f = 'f'
    p = 'p'
    n = 'n'
    micro = 'micro'
    m = 'm'
    c = 'c'
    d = 'd'
    none = 'none'
    da = 'da'
    h = 'h'
    k = 'k'
    M = 'M'
    G = 'G'
    T = 'T'
    P = 'P'
    E = 'E'
    Z = 'Z'
    Y = 'Y'

class UnitSymbol(Enum):
    """RDF enumeration UnitSymbol."""

    none = 'none'
    m = 'm'
    kg = 'kg'
    s = 's'
    A = 'A'
    K = 'K'
    mol = 'mol'
    cd = 'cd'
    deg = 'deg'
    rad = 'rad'
    sr = 'sr'
    Gy = 'Gy'
    Bq = 'Bq'
    degC = 'degC'
    Sv = 'Sv'
    F = 'F'
    C = 'C'
    S = 'S'
    H = 'H'
    V = 'V'
    ohm = 'ohm'
    J = 'J'
    N = 'N'
    Hz = 'Hz'
    lx = 'lx'
    lm = 'lm'
    Wb = 'Wb'
    T = 'T'
    W = 'W'
    Pa = 'Pa'
    m2 = 'm2'
    m3 = 'm3'
    mPers = 'mPers'
    mPers2 = 'mPers2'
    m3Pers = 'm3Pers'
    mPerm3 = 'mPerm3'
    kgm = 'kgm'
    kgPerm3 = 'kgPerm3'
    m2Pers = 'm2Pers'
    WPermK = 'WPermK'
    JPerK = 'JPerK'
    ppm = 'ppm'
    rotPers = 'rotPers'
    radPers = 'radPers'
    WPerm2 = 'WPerm2'
    JPerm2 = 'JPerm2'
    SPerm = 'SPerm'
    KPers = 'KPers'
    PaPers = 'PaPers'
    JPerkgK = 'JPerkgK'
    VA = 'VA'
    VAr = 'VAr'
    cosPhi = 'cosPhi'
    Vs = 'Vs'
    V2 = 'V2'
    As = 'As'
    A2 = 'A2'
    A2s = 'A2s'
    VAh = 'VAh'
    Wh = 'Wh'
    VArh = 'VArh'
    VPerHz = 'VPerHz'
    HzPers = 'HzPers'
    character = 'character'
    charPers = 'charPers'
    kgm2 = 'kgm2'
    dB = 'dB'
    WPers = 'WPers'
    lPers = 'lPers'
    dBm = 'dBm'
    h = 'h'
    min = 'min'
    Q = 'Q'
    Qh = 'Qh'
    ohmm = 'ohmm'
    APerm = 'APerm'
    V2h = 'V2h'
    A2h = 'A2h'
    Ah = 'Ah'
    count = 'count'
    ft3 = 'ft3'
    m3Perh = 'm3Perh'
    gal = 'gal'
    Btu = 'Btu'
    l = 'l'
    lPerh = 'lPerh'
    lPerl = 'lPerl'
    gPerg = 'gPerg'
    molPerm3 = 'molPerm3'
    molPermol = 'molPermol'
    molPerkg = 'molPerkg'
    sPers = 'sPers'
    HzPerHz = 'HzPerHz'
    VPerV = 'VPerV'
    APerA = 'APerA'
    VPerVA = 'VPerVA'
    rev = 'rev'
    kat = 'kat'
    JPerkg = 'JPerkg'
    m3Uncompensated = 'm3Uncompensated'
    m3Compensated = 'm3Compensated'
    WPerW = 'WPerW'
    therm = 'therm'
    onePerm = 'onePerm'
    m3Perkg = 'm3Perkg'
    Pas = 'Pas'
    Nm = 'Nm'
    NPerm = 'NPerm'
    radPers2 = 'radPers2'
    JPerm3 = 'JPerm3'
    VPerm = 'VPerm'
    CPerm3 = 'CPerm3'
    CPerm2 = 'CPerm2'
    FPerm = 'FPerm'
    HPerm = 'HPerm'
    JPermol = 'JPermol'
    JPermolK = 'JPermolK'
    CPerkg = 'CPerkg'
    GyPers = 'GyPers'
    WPersr = 'WPersr'
    WPerm2sr = 'WPerm2sr'
    katPerm3 = 'katPerm3'
    d = 'd'
    anglemin = 'anglemin'
    anglesec = 'anglesec'
    ha = 'ha'
    tonne = 'tonne'
    bar = 'bar'
    mmHg = 'mmHg'
    M = 'M'
    kn = 'kn'
    Mx = 'Mx'
    G = 'G'
    Oe = 'Oe'
    Vh = 'Vh'
    WPerA = 'WPerA'
    onePerHz = 'onePerHz'
    VPerVAr = 'VPerVAr'
    ohmPerm = 'ohmPerm'
    kgPerJ = 'kgPerJ'
    JPers = 'JPers'

class DroopSignalFeedbackKind(Enum):
    """RDF enumeration DroopSignalFeedbackKind."""

    electricalPower = 'electricalPower'
    none = 'none'
    fuelValveStroke = 'fuelValveStroke'
    governorOutput = 'governorOutput'

class ExcIEEEST1AUELselectorKind(Enum):
    """RDF enumeration ExcIEEEST1AUELselectorKind."""

    ignoreUELsignal = 'ignoreUELsignal'
    inputHVgateVoltageOutput = 'inputHVgateVoltageOutput'
    inputHVgateErrorSignal = 'inputHVgateErrorSignal'
    inputAddedToErrorSignal = 'inputAddedToErrorSignal'

class ExcREXSFeedbackSignalKind(Enum):
    """RDF enumeration ExcREXSFeedbackSignalKind."""

    fieldVoltage = 'fieldVoltage'
    fieldCurrent = 'fieldCurrent'
    outputVoltage = 'outputVoltage'

class ExcST6BOELselectorKind(Enum):
    """RDF enumeration ExcST6BOELselectorKind."""

    noOELinput = 'noOELinput'
    beforeUEL = 'beforeUEL'
    afterUEL = 'afterUEL'

class ExcST7BOELselectorKind(Enum):
    """RDF enumeration ExcST7BOELselectorKind."""

    noOELinput = 'noOELinput'
    addVref = 'addVref'
    inputLVgate = 'inputLVgate'
    outputLVgate = 'outputLVgate'

class ExcST7BUELselectorKind(Enum):
    """RDF enumeration ExcST7BUELselectorKind."""

    noUELinput = 'noUELinput'
    addVref = 'addVref'
    inputHVgate = 'inputHVgate'
    outputHVgate = 'outputHVgate'

class FrancisGovernorControlKind(Enum):
    """RDF enumeration FrancisGovernorControlKind."""

    mechanicHydrolicTachoAccelerator = 'mechanicHydrolicTachoAccelerator'
    mechanicHydraulicTransientFeedback = 'mechanicHydraulicTransientFeedback'
    electromechanicalElectrohydraulic = 'electromechanicalElectrohydraulic'

class GenericNonLinearLoadModelKind(Enum):
    """RDF enumeration GenericNonLinearLoadModelKind."""

    exponentialRecovery = 'exponentialRecovery'
    loadAdaptive = 'loadAdaptive'

class GovHydro4ModelKind(Enum):
    """RDF enumeration GovHydro4ModelKind."""

    simple = 'simple'
    francisPelton = 'francisPelton'
    kaplan = 'kaplan'

class IfdBaseKind(Enum):
    """RDF enumeration IfdBaseKind."""

    ifag = 'ifag'
    ifnl = 'ifnl'
    iffl = 'iffl'
    other = 'other'

class InputSignalKind(Enum):
    """RDF enumeration InputSignalKind."""

    rotorSpeed = 'rotorSpeed'
    rotorAngularFrequencyDeviation = 'rotorAngularFrequencyDeviation'
    busFrequency = 'busFrequency'
    busFrequencyDeviation = 'busFrequencyDeviation'
    generatorElectricalPower = 'generatorElectricalPower'
    generatorAcceleratingPower = 'generatorAcceleratingPower'
    busVoltage = 'busVoltage'
    busVoltageDerivative = 'busVoltageDerivative'
    branchCurrent = 'branchCurrent'
    fieldCurrent = 'fieldCurrent'
    generatorMechanicalPower = 'generatorMechanicalPower'

class RemoteSignalKind(Enum):
    """RDF enumeration RemoteSignalKind."""

    remoteBusVoltageFrequency = 'remoteBusVoltageFrequency'
    remoteBusVoltageFrequencyDeviation = 'remoteBusVoltageFrequencyDeviation'
    remoteBusFrequency = 'remoteBusFrequency'
    remoteBusFrequencyDeviation = 'remoteBusFrequencyDeviation'
    remoteBusVoltageAmplitude = 'remoteBusVoltageAmplitude'
    remoteBusVoltage = 'remoteBusVoltage'
    remoteBranchCurrentAmplitude = 'remoteBranchCurrentAmplitude'
    remoteBusVoltageAmplitudeDerivative = 'remoteBusVoltageAmplitudeDerivative'
    remotePuBusVoltageDerivative = 'remotePuBusVoltageDerivative'

class RotorKind(Enum):
    """RDF enumeration RotorKind."""

    roundRotor = 'roundRotor'
    salientPole = 'salientPole'

class StaticLoadModelKind(Enum):
    """RDF enumeration StaticLoadModelKind."""

    exponential = 'exponential'
    zIP1 = 'zIP1'
    zIP2 = 'zIP2'
    constantZ = 'constantZ'

class SynchronousMachineModelKind(Enum):
    """RDF enumeration SynchronousMachineModelKind."""

    subtransient = 'subtransient'
    subtransientTypeF = 'subtransientTypeF'
    subtransientTypeJ = 'subtransientTypeJ'
    subtransientSimplified = 'subtransientSimplified'
    subtransientSimplifiedDirectAxis = 'subtransientSimplifiedDirectAxis'

class WindLookupTableFunctionKind(Enum):
    """RDF enumeration WindLookupTableFunctionKind."""

    prr = 'prr'
    omegap = 'omegap'
    ipmax = 'ipmax'
    iqmax = 'iqmax'
    pwp = 'pwp'
    tcwdu = 'tcwdu'
    tduwt = 'tduwt'
    qmaxp = 'qmaxp'
    qminp = 'qminp'
    qmaxu = 'qmaxu'
    qminu = 'qminu'
    tuover = 'tuover'
    tuunder = 'tuunder'
    tfover = 'tfover'
    tfunder = 'tfunder'
    qwp = 'qwp'

class WindPlantQcontrolModeKind(Enum):
    """RDF enumeration WindPlantQcontrolModeKind."""

    reactivePower = 'reactivePower'
    powerFactor = 'powerFactor'
    uqStatic = 'uqStatic'
    voltageControl = 'voltageControl'

class WindQcontrolModeKind(Enum):
    """RDF enumeration WindQcontrolModeKind."""

    voltage = 'voltage'
    reactivePower = 'reactivePower'
    openLoopReactivePower = 'openLoopReactivePower'
    powerFactor = 'powerFactor'
    openLooppowerFactor = 'openLooppowerFactor'

class WindUVRTQcontrolModeKind(Enum):
    """RDF enumeration WindUVRTQcontrolModeKind."""

    mode0 = 'mode0'
    mode1 = 'mode1'
    mode2 = 'mode2'

class ActivePower(Base):
    """RDF class ActivePower."""

    __slots__ = ('value', 'multiplier', 'unit')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ActivePower') -> None:
        """Initialize an RDF-defined CGMES object."""
        Base.__init__(self, rdfid=rdfid, tpe=tpe)
        self.value: float = None
        self.multiplier: UnitMultiplier = None
        self.unit: UnitSymbol = None

class AngleDegrees(Base):
    """RDF class AngleDegrees."""

    __slots__ = ('value', 'unit', 'multiplier')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'AngleDegrees') -> None:
        """Initialize an RDF-defined CGMES object."""
        Base.__init__(self, rdfid=rdfid, tpe=tpe)
        self.value: float = None
        self.unit: UnitSymbol = None
        self.multiplier: UnitMultiplier = None

class ApparentPower(Base):
    """RDF class ApparentPower."""

    __slots__ = ('value', 'multiplier', 'unit')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ApparentPower') -> None:
        """Initialize an RDF-defined CGMES object."""
        Base.__init__(self, rdfid=rdfid, tpe=tpe)
        self.value: float = None
        self.multiplier: UnitMultiplier = None
        self.unit: UnitSymbol = None

class Area(Base):
    """RDF class Area."""

    __slots__ = ('value', 'unit', 'multiplier')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'Area') -> None:
        """Initialize an RDF-defined CGMES object."""
        Base.__init__(self, rdfid=rdfid, tpe=tpe)
        self.value: float = None
        self.unit: UnitSymbol = None
        self.multiplier: UnitMultiplier = None

class Boolean(Base):
    """RDF class Boolean."""

    __slots__ = ()

    def __init__(self, rdfid: str = "", tpe: str = 'Boolean') -> None:
        """Initialize an RDF-defined CGMES object."""
        Base.__init__(self, rdfid=rdfid, tpe=tpe)
        pass

class Date(Base):
    """RDF class Date."""

    __slots__ = ()

    def __init__(self, rdfid: str = "", tpe: str = 'Date') -> None:
        """Initialize an RDF-defined CGMES object."""
        Base.__init__(self, rdfid=rdfid, tpe=tpe)
        pass

class Float(Base):
    """RDF class Float."""

    __slots__ = ()

    def __init__(self, rdfid: str = "", tpe: str = 'Float') -> None:
        """Initialize an RDF-defined CGMES object."""
        Base.__init__(self, rdfid=rdfid, tpe=tpe)
        pass

class Frequency(Base):
    """RDF class Frequency."""

    __slots__ = ('value', 'unit', 'multiplier')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'Frequency') -> None:
        """Initialize an RDF-defined CGMES object."""
        Base.__init__(self, rdfid=rdfid, tpe=tpe)
        self.value: float = None
        self.unit: UnitSymbol = None
        self.multiplier: UnitMultiplier = None

class IdentifiedObject(Base):
    """RDF class IdentifiedObject."""

    __slots__ = ('description', 'mRID', 'name')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'IdentifiedObject') -> None:
        """Initialize an RDF-defined CGMES object."""
        Base.__init__(self, rdfid=rdfid, tpe=tpe)
        self.description: str = None
        self.mRID: str = None
        self.name: str = None

class Integer(Base):
    """RDF class Integer."""

    __slots__ = ()

    def __init__(self, rdfid: str = "", tpe: str = 'Integer') -> None:
        """Initialize an RDF-defined CGMES object."""
        Base.__init__(self, rdfid=rdfid, tpe=tpe)
        pass

class Length(Base):
    """RDF class Length."""

    __slots__ = ('value', 'unit', 'multiplier')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'Length') -> None:
        """Initialize an RDF-defined CGMES object."""
        Base.__init__(self, rdfid=rdfid, tpe=tpe)
        self.value: float = None
        self.unit: UnitSymbol = None
        self.multiplier: UnitMultiplier = None

class PU(Base):
    """RDF class PU."""

    __slots__ = ('value', 'unit', 'multiplier')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'PU') -> None:
        """Initialize an RDF-defined CGMES object."""
        Base.__init__(self, rdfid=rdfid, tpe=tpe)
        self.value: float = None
        self.unit: UnitSymbol = None
        self.multiplier: UnitMultiplier = None

class ProprietaryParameterDynamics(Base):
    """RDF class ProprietaryParameterDynamics."""

    __slots__ = ('CSCUserDefined', 'SVCUserDefined', 'VSCUserDefined', 'WindPlantUserDefined', 'WindType1or2UserDefined', 'WindType3or4UserDefined', 'SynchronousMachineUserDefined', 'AsynchronousMachineUserDefined', 'TurbineGovernorUserDefined', 'TurbineLoadControllerUserDefined', 'MechanicalLoadUserDefined', 'ExcitationSystemUserDefined', 'OverexcitationLimiterUserDefined', 'UnderexcitationLimiterUserDefined', 'PowerSystemStabilizerUserDefined', 'DiscontinuousExcitationControlUserDefined', 'PFVArControllerType1UserDefined', 'VoltageAdjusterUserDefined', 'PFVArControllerType2UserDefined', 'VoltageCompensatorUserDefined', 'LoadUserDefined', 'parameterNumber', 'booleanParameterValue', 'integerParameterValue', 'floatParameterValue')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ProprietaryParameterDynamics') -> None:
        """Initialize an RDF-defined CGMES object."""
        Base.__init__(self, rdfid=rdfid, tpe=tpe)
        self.CSCUserDefined: CSCUserDefined = None
        self.SVCUserDefined: SVCUserDefined = None
        self.VSCUserDefined: VSCUserDefined = None
        self.WindPlantUserDefined: WindPlantUserDefined = None
        self.WindType1or2UserDefined: WindType1or2UserDefined = None
        self.WindType3or4UserDefined: WindType3or4UserDefined = None
        self.SynchronousMachineUserDefined: SynchronousMachineUserDefined = None
        self.AsynchronousMachineUserDefined: AsynchronousMachineUserDefined = None
        self.TurbineGovernorUserDefined: TurbineGovernorUserDefined = None
        self.TurbineLoadControllerUserDefined: TurbineLoadControllerUserDefined = None
        self.MechanicalLoadUserDefined: MechanicalLoadUserDefined = None
        self.ExcitationSystemUserDefined: ExcitationSystemUserDefined = None
        self.OverexcitationLimiterUserDefined: OverexcitationLimiterUserDefined = None
        self.UnderexcitationLimiterUserDefined: UnderexcitationLimiterUserDefined = None
        self.PowerSystemStabilizerUserDefined: PowerSystemStabilizerUserDefined = None
        self.DiscontinuousExcitationControlUserDefined: DiscontinuousExcitationControlUserDefined = None
        self.PFVArControllerType1UserDefined: PFVArControllerType1UserDefined = None
        self.VoltageAdjusterUserDefined: VoltageAdjusterUserDefined = None
        self.PFVArControllerType2UserDefined: PFVArControllerType2UserDefined = None
        self.VoltageCompensatorUserDefined: VoltageCompensatorUserDefined = None
        self.LoadUserDefined: LoadUserDefined = None
        self.parameterNumber: int = None
        self.booleanParameterValue: bool = None
        self.integerParameterValue: int = None
        self.floatParameterValue: float = None

class Seconds(Base):
    """RDF class Seconds."""

    __slots__ = ('value', 'unit', 'multiplier')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'Seconds') -> None:
        """Initialize an RDF-defined CGMES object."""
        Base.__init__(self, rdfid=rdfid, tpe=tpe)
        self.value: float = None
        self.unit: UnitSymbol = None
        self.multiplier: UnitMultiplier = None

class String(Base):
    """RDF class String."""

    __slots__ = ()

    def __init__(self, rdfid: str = "", tpe: str = 'String') -> None:
        """Initialize an RDF-defined CGMES object."""
        Base.__init__(self, rdfid=rdfid, tpe=tpe)
        pass

class Temperature(Base):
    """RDF class Temperature."""

    __slots__ = ('multiplier', 'unit', 'value')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'Temperature') -> None:
        """Initialize an RDF-defined CGMES object."""
        Base.__init__(self, rdfid=rdfid, tpe=tpe)
        self.multiplier: UnitMultiplier = None
        self.unit: UnitSymbol = None
        self.value: float = None

class VolumeFlowRate(Base):
    """RDF class VolumeFlowRate."""

    __slots__ = ('multiplier', 'unit', 'value')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'VolumeFlowRate') -> None:
        """Initialize an RDF-defined CGMES object."""
        Base.__init__(self, rdfid=rdfid, tpe=tpe)
        self.multiplier: UnitMultiplier = None
        self.unit: UnitSymbol = None
        self.value: float = None

class ACDCTerminal(IdentifiedObject):
    """RDF class ACDCTerminal."""

    __slots__ = ()

    def __init__(self, rdfid: str = "", tpe: str = 'ACDCTerminal') -> None:
        """Initialize an RDF-defined CGMES object."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        pass

class DynamicsFunctionBlock(IdentifiedObject):
    """RDF class DynamicsFunctionBlock."""

    __slots__ = ('enabled',)

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'DynamicsFunctionBlock') -> None:
        """Initialize an RDF-defined CGMES object."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.enabled: bool = None

class GenICompensationForGenJ(IdentifiedObject):
    """RDF class GenICompensationForGenJ."""

    __slots__ = ('SynchronousMachineDynamics', 'VcompIEEEType2', 'rcij', 'xcij')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GenICompensationForGenJ') -> None:
        """Initialize an RDF-defined CGMES object."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.SynchronousMachineDynamics: SynchronousMachineDynamics = None
        self.VcompIEEEType2: VCompIEEEType2 = None
        self.rcij: PU = None
        self.xcij: PU = None

class LoadDynamics(IdentifiedObject):
    """RDF class LoadDynamics."""

    __slots__ = ('EnergyConsumer',)

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'LoadDynamics') -> None:
        """Initialize an RDF-defined CGMES object."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.EnergyConsumer: List[EnergyConsumer] = list()

class LoadMotor(IdentifiedObject):
    """RDF class LoadMotor."""

    __slots__ = ('LoadAggregate', 'pfrac', 'lfac', 'ls', 'lp', 'lpp', 'ra', 'tpo', 'tppo', 'h', 'd', 'vt', 'tv', 'tbkr')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'LoadMotor') -> None:
        """Initialize an RDF-defined CGMES object."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.LoadAggregate: LoadAggregate = None
        self.pfrac: float = None
        self.lfac: float = None
        self.ls: PU = None
        self.lp: PU = None
        self.lpp: PU = None
        self.ra: PU = None
        self.tpo: Seconds = None
        self.tppo: Seconds = None
        self.h: Seconds = None
        self.d: float = None
        self.vt: PU = None
        self.tv: Seconds = None
        self.tbkr: Seconds = None

class LoadStatic(IdentifiedObject):
    """RDF class LoadStatic."""

    __slots__ = ('LoadAggregate', 'staticLoadModelType', 'kp1', 'kp2', 'kp3', 'kp4', 'ep1', 'ep2', 'ep3', 'kpf', 'kq1', 'kq2', 'kq3', 'kq4', 'eq1', 'eq2', 'eq3', 'kqf')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'LoadStatic') -> None:
        """Initialize an RDF-defined CGMES object."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.LoadAggregate: LoadAggregate = None
        self.staticLoadModelType: StaticLoadModelKind = None
        self.kp1: float = None
        self.kp2: float = None
        self.kp3: float = None
        self.kp4: float = None
        self.ep1: float = None
        self.ep2: float = None
        self.ep3: float = None
        self.kpf: float = None
        self.kq1: float = None
        self.kq2: float = None
        self.kq3: float = None
        self.kq4: float = None
        self.eq1: float = None
        self.eq2: float = None
        self.eq3: float = None
        self.kqf: float = None

class PowerSystemResource(IdentifiedObject):
    """RDF class PowerSystemResource."""

    __slots__ = ()

    def __init__(self, rdfid: str = "", tpe: str = 'PowerSystemResource') -> None:
        """Initialize an RDF-defined CGMES object."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        pass

class RemoteInputSignal(IdentifiedObject):
    """RDF class RemoteInputSignal."""

    __slots__ = ('Terminal', 'remoteSignalType', 'DiscontinuousExcitationControlDynamics', 'WindTurbineType1or2Dynamics', 'PowerSystemStabilizerDynamics', 'UnderexcitationLimiterDynamics', 'PFVArControllerType1Dynamics', 'VoltageCompensatorDynamics', 'WindPlantDynamics', 'WindTurbineType3or4Dynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'RemoteInputSignal') -> None:
        """Initialize an RDF-defined CGMES object."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.Terminal: Terminal = None
        self.remoteSignalType: RemoteSignalKind = None
        self.DiscontinuousExcitationControlDynamics: DiscontinuousExcitationControlDynamics = None
        self.WindTurbineType1or2Dynamics: WindTurbineType1or2Dynamics = None
        self.PowerSystemStabilizerDynamics: PowerSystemStabilizerDynamics = None
        self.UnderexcitationLimiterDynamics: UnderexcitationLimiterDynamics = None
        self.PFVArControllerType1Dynamics: PFVArControllerType1Dynamics = None
        self.VoltageCompensatorDynamics: VoltageCompensatorDynamics = None
        self.WindPlantDynamics: WindPlantDynamics = None
        self.WindTurbineType3or4Dynamics: WindTurbineType3or4Dynamics = None

class WindAeroConstIEC(IdentifiedObject):
    """RDF class WindAeroConstIEC."""

    __slots__ = ('WindGenTurbineType1aIEC',)

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindAeroConstIEC') -> None:
        """Initialize an RDF-defined CGMES object."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.WindGenTurbineType1aIEC: WindGenTurbineType1aIEC = None

class WindAeroOneDimIEC(IdentifiedObject):
    """RDF class WindAeroOneDimIEC."""

    __slots__ = ('ka', 'thetaomega', 'WindTurbineType3IEC')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindAeroOneDimIEC') -> None:
        """Initialize an RDF-defined CGMES object."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.ka: float = None
        self.thetaomega: AngleDegrees = None
        self.WindTurbineType3IEC: WindTurbineType3IEC = None

class WindAeroTwoDimIEC(IdentifiedObject):
    """RDF class WindAeroTwoDimIEC."""

    __slots__ = ('dpomega', 'dptheta', 'dpv1', 'omegazero', 'pavail', 'thetazero', 'thetav2', 'WindTurbineType3IEC')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindAeroTwoDimIEC') -> None:
        """Initialize an RDF-defined CGMES object."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.dpomega: PU = None
        self.dptheta: PU = None
        self.dpv1: PU = None
        self.omegazero: PU = None
        self.pavail: PU = None
        self.thetazero: AngleDegrees = None
        self.thetav2: AngleDegrees = None
        self.WindTurbineType3IEC: WindTurbineType3IEC = None

class WindContCurrLimIEC(IdentifiedObject):
    """RDF class WindContCurrLimIEC."""

    __slots__ = ('imax', 'imaxdip', 'kpqu', 'mdfslim', 'mqpri', 'tufiltcl', 'upqumax', 'WindTurbineType3or4IEC', 'WindDynamicsLookupTable')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindContCurrLimIEC') -> None:
        """Initialize an RDF-defined CGMES object."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.imax: PU = None
        self.imaxdip: PU = None
        self.kpqu: PU = None
        self.mdfslim: bool = None
        self.mqpri: bool = None
        self.tufiltcl: Seconds = None
        self.upqumax: PU = None
        self.WindTurbineType3or4IEC: WindTurbineType3or4IEC = None
        self.WindDynamicsLookupTable: List[WindDynamicsLookupTable] = list()

class WindContPType3IEC(IdentifiedObject):
    """RDF class WindContPType3IEC."""

    __slots__ = ('dpmax', 'dprefmax', 'dprefmin', 'dthetamax', 'dthetamaxuvrt', 'kdtd', 'kip', 'kpp', 'mpuvrt', 'omegaoffset', 'pdtdmax', 'tdvs', 'thetaemin', 'thetauscale', 'tomegafiltp3', 'tpfiltp3', 'tpord', 'tufiltp3', 'tomegaref', 'udvs', 'updip', 'omegadtd', 'zeta', 'WindTurbineType3IEC', 'WindDynamicsLookupTable')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindContPType3IEC') -> None:
        """Initialize an RDF-defined CGMES object."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.dpmax: PU = None
        self.dprefmax: PU = None
        self.dprefmin: PU = None
        self.dthetamax: PU = None
        self.dthetamaxuvrt: PU = None
        self.kdtd: PU = None
        self.kip: PU = None
        self.kpp: PU = None
        self.mpuvrt: bool = None
        self.omegaoffset: PU = None
        self.pdtdmax: PU = None
        self.tdvs: Seconds = None
        self.thetaemin: PU = None
        self.thetauscale: PU = None
        self.tomegafiltp3: Seconds = None
        self.tpfiltp3: Seconds = None
        self.tpord: PU = None
        self.tufiltp3: Seconds = None
        self.tomegaref: Seconds = None
        self.udvs: PU = None
        self.updip: PU = None
        self.omegadtd: PU = None
        self.zeta: float = None
        self.WindTurbineType3IEC: WindTurbineType3IEC = None
        self.WindDynamicsLookupTable: List[WindDynamicsLookupTable] = list()

class WindContPType4aIEC(IdentifiedObject):
    """RDF class WindContPType4aIEC."""

    __slots__ = ('dpmaxp4a', 'tpordp4a', 'tufiltp4a', 'WindTurbineType4aIEC')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindContPType4aIEC') -> None:
        """Initialize an RDF-defined CGMES object."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.dpmaxp4a: PU = None
        self.tpordp4a: Seconds = None
        self.tufiltp4a: Seconds = None
        self.WindTurbineType4aIEC: WindTurbineType4aIEC = None

class WindContPType4bIEC(IdentifiedObject):
    """RDF class WindContPType4bIEC."""

    __slots__ = ('dpmaxp4b', 'tpaero', 'tpordp4b', 'tufiltp4b', 'WindTurbineType4bIEC')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindContPType4bIEC') -> None:
        """Initialize an RDF-defined CGMES object."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.dpmaxp4b: PU = None
        self.tpaero: Seconds = None
        self.tpordp4b: Seconds = None
        self.tufiltp4b: Seconds = None
        self.WindTurbineType4bIEC: WindTurbineType4bIEC = None

class WindContPitchAngleIEC(IdentifiedObject):
    """RDF class WindContPitchAngleIEC."""

    __slots__ = ('dthetamax', 'dthetamin', 'kic', 'kiomega', 'kpc', 'kpomega', 'kpx', 'thetamax', 'thetamin', 'ttheta', 'WindTurbineType3IEC')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindContPitchAngleIEC') -> None:
        """Initialize an RDF-defined CGMES object."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.dthetamax: float = None
        self.dthetamin: float = None
        self.kic: PU = None
        self.kiomega: PU = None
        self.kpc: PU = None
        self.kpomega: PU = None
        self.kpx: PU = None
        self.thetamax: AngleDegrees = None
        self.thetamin: AngleDegrees = None
        self.ttheta: Seconds = None
        self.WindTurbineType3IEC: WindTurbineType3IEC = None

class WindContQIEC(IdentifiedObject):
    """RDF class WindContQIEC."""

    __slots__ = ('iqh1', 'iqmax', 'iqmin', 'iqpost', 'kiq', 'kiu', 'kpq', 'kpu', 'kqv', 'tpfiltq', 'rdroop', 'tufiltq', 'tpost', 'tqord', 'udb1', 'udb2', 'umax', 'umin', 'uqdip', 'uref0', 'windQcontrolModesType', 'windUVRTQcontrolModesType', 'xdroop', 'WindTurbineType3or4IEC')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindContQIEC') -> None:
        """Initialize an RDF-defined CGMES object."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.iqh1: PU = None
        self.iqmax: PU = None
        self.iqmin: PU = None
        self.iqpost: PU = None
        self.kiq: PU = None
        self.kiu: PU = None
        self.kpq: PU = None
        self.kpu: PU = None
        self.kqv: PU = None
        self.tpfiltq: Seconds = None
        self.rdroop: PU = None
        self.tufiltq: Seconds = None
        self.tpost: Seconds = None
        self.tqord: Seconds = None
        self.udb1: PU = None
        self.udb2: PU = None
        self.umax: PU = None
        self.umin: PU = None
        self.uqdip: PU = None
        self.uref0: PU = None
        self.windQcontrolModesType: WindQcontrolModeKind = None
        self.windUVRTQcontrolModesType: WindUVRTQcontrolModeKind = None
        self.xdroop: PU = None
        self.WindTurbineType3or4IEC: WindTurbineType3or4IEC = None

class WindContQLimIEC(IdentifiedObject):
    """RDF class WindContQLimIEC."""

    __slots__ = ('qmax', 'qmin', 'WindTurbineType3or4IEC')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindContQLimIEC') -> None:
        """Initialize an RDF-defined CGMES object."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.qmax: PU = None
        self.qmin: PU = None
        self.WindTurbineType3or4IEC: WindTurbineType3or4IEC = None

class WindContQPQULimIEC(IdentifiedObject):
    """RDF class WindContQPQULimIEC."""

    __slots__ = ('tpfiltql', 'tufiltql', 'WindTurbineType3or4IEC', 'WindDynamicsLookupTable')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindContQPQULimIEC') -> None:
        """Initialize an RDF-defined CGMES object."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.tpfiltql: Seconds = None
        self.tufiltql: Seconds = None
        self.WindTurbineType3or4IEC: WindTurbineType3or4IEC = None
        self.WindDynamicsLookupTable: List[WindDynamicsLookupTable] = list()

class WindContRotorRIEC(IdentifiedObject):
    """RDF class WindContRotorRIEC."""

    __slots__ = ('kirr', 'komegafilt', 'kpfilt', 'kprr', 'rmax', 'rmin', 'tomegafiltrr', 'tpfiltrr', 'WindDynamicsLookupTable', 'WindGenTurbineType2IEC')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindContRotorRIEC') -> None:
        """Initialize an RDF-defined CGMES object."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.kirr: PU = None
        self.komegafilt: float = None
        self.kpfilt: float = None
        self.kprr: PU = None
        self.rmax: PU = None
        self.rmin: PU = None
        self.tomegafiltrr: Seconds = None
        self.tpfiltrr: Seconds = None
        self.WindDynamicsLookupTable: List[WindDynamicsLookupTable] = list()
        self.WindGenTurbineType2IEC: WindGenTurbineType2IEC = None

class WindDynamicsLookupTable(IdentifiedObject):
    """RDF class WindDynamicsLookupTable."""

    __slots__ = ('WindContCurrLimIEC', 'WindContPType3IEC', 'WindContQPQULimIEC', 'WindContRotorRIEC', 'input', 'lookupTableFunctionType', 'output', 'sequence', 'WindPlantFreqPcontrolIEC', 'WindProtectionIEC', 'WindPlantReactiveControlIEC', 'WindGenType3bIEC', 'WindPitchContPowerIEC')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindDynamicsLookupTable') -> None:
        """Initialize an RDF-defined CGMES object."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.WindContCurrLimIEC: WindContCurrLimIEC = None
        self.WindContPType3IEC: WindContPType3IEC = None
        self.WindContQPQULimIEC: WindContQPQULimIEC = None
        self.WindContRotorRIEC: WindContRotorRIEC = None
        self.input: float = None
        self.lookupTableFunctionType: WindLookupTableFunctionKind = None
        self.output: float = None
        self.sequence: int = None
        self.WindPlantFreqPcontrolIEC: WindPlantFreqPcontrolIEC = None
        self.WindProtectionIEC: WindProtectionIEC = None
        self.WindPlantReactiveControlIEC: WindPlantReactiveControlIEC = None
        self.WindGenType3bIEC: WindGenType3bIEC = None
        self.WindPitchContPowerIEC: WindPitchContPowerIEC = None

class WindGenType3IEC(IdentifiedObject):
    """RDF class WindGenType3IEC."""

    __slots__ = ('dipmax', 'diqmax', 'xs', 'WindTurbineType3IEC')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindGenType3IEC') -> None:
        """Initialize an RDF-defined CGMES object."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.dipmax: PU = None
        self.diqmax: PU = None
        self.xs: PU = None
        self.WindTurbineType3IEC: WindTurbineType3IEC = None

class WindGenType4IEC(IdentifiedObject):
    """RDF class WindGenType4IEC."""

    __slots__ = ('dipmax', 'diqmin', 'diqmax', 'tg', 'WindTurbineType4aIEC', 'WindTurbineType4bIEC')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindGenType4IEC') -> None:
        """Initialize an RDF-defined CGMES object."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.dipmax: PU = None
        self.diqmin: PU = None
        self.diqmax: PU = None
        self.tg: Seconds = None
        self.WindTurbineType4aIEC: WindTurbineType4aIEC = None
        self.WindTurbineType4bIEC: WindTurbineType4bIEC = None

class WindMechIEC(IdentifiedObject):
    """RDF class WindMechIEC."""

    __slots__ = ('cdrt', 'hgen', 'hwtr', 'kdrt', 'WindTurbineType3IEC', 'WindTurbineType1or2IEC', 'WindTurbineType4bIEC')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindMechIEC') -> None:
        """Initialize an RDF-defined CGMES object."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.cdrt: PU = None
        self.hgen: Seconds = None
        self.hwtr: Seconds = None
        self.kdrt: PU = None
        self.WindTurbineType3IEC: WindTurbineType3IEC = None
        self.WindTurbineType1or2IEC: WindTurbineType1or2IEC = None
        self.WindTurbineType4bIEC: WindTurbineType4bIEC = None

class WindPitchContPowerIEC(IdentifiedObject):
    """RDF class WindPitchContPowerIEC."""

    __slots__ = ('WindDynamicsLookupTable', 'WindGenTurbineType1bIEC', 'WindGenTurbineType2IEC', 'dpmax', 'dpmin', 'pmin', 'pset', 't1', 'tr', 'uuvrt')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindPitchContPowerIEC') -> None:
        """Initialize an RDF-defined CGMES object."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.WindDynamicsLookupTable: List[WindDynamicsLookupTable] = list()
        self.WindGenTurbineType1bIEC: WindGenTurbineType1bIEC = None
        self.WindGenTurbineType2IEC: WindGenTurbineType2IEC = None
        self.dpmax: PU = None
        self.dpmin: PU = None
        self.pmin: PU = None
        self.pset: PU = None
        self.t1: Seconds = None
        self.tr: Seconds = None
        self.uuvrt: PU = None

class WindPlantFreqPcontrolIEC(IdentifiedObject):
    """RDF class WindPlantFreqPcontrolIEC."""

    __slots__ = ('WindDynamicsLookupTable', 'dprefmax', 'dprefmin', 'dpwprefmax', 'dpwprefmin', 'prefmax', 'prefmin', 'kiwpp', 'kiwppmax', 'kiwppmin', 'kpwpp', 'kwppref', 'tpft', 'tpfv', 'twpffiltp', 'twppfiltp', 'WindPlantIEC')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindPlantFreqPcontrolIEC') -> None:
        """Initialize an RDF-defined CGMES object."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.WindDynamicsLookupTable: List[WindDynamicsLookupTable] = list()
        self.dprefmax: PU = None
        self.dprefmin: PU = None
        self.dpwprefmax: PU = None
        self.dpwprefmin: PU = None
        self.prefmax: PU = None
        self.prefmin: PU = None
        self.kiwpp: float = None
        self.kiwppmax: PU = None
        self.kiwppmin: PU = None
        self.kpwpp: float = None
        self.kwppref: PU = None
        self.tpft: Seconds = None
        self.tpfv: Seconds = None
        self.twpffiltp: Seconds = None
        self.twppfiltp: Seconds = None
        self.WindPlantIEC: WindPlantIEC = None

class WindPlantReactiveControlIEC(IdentifiedObject):
    """RDF class WindPlantReactiveControlIEC."""

    __slots__ = ('WindDynamicsLookupTable', 'WindPlantIEC', 'dxrefmax', 'dxrefmin', 'kiwpx', 'kiwpxmax', 'kiwpxmin', 'kpwpx', 'kwpqref', 'kwpqu', 'tuqfilt', 'twppfiltq', 'twpqfiltq', 'twpufiltq', 'txft', 'txfv', 'uwpqdip', 'windPlantQcontrolModesType', 'xrefmax', 'xrefmin')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindPlantReactiveControlIEC') -> None:
        """Initialize an RDF-defined CGMES object."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.WindDynamicsLookupTable: List[WindDynamicsLookupTable] = list()
        self.WindPlantIEC: WindPlantIEC = None
        self.dxrefmax: PU = None
        self.dxrefmin: PU = None
        self.kiwpx: float = None
        self.kiwpxmax: PU = None
        self.kiwpxmin: PU = None
        self.kpwpx: float = None
        self.kwpqref: PU = None
        self.kwpqu: PU = None
        self.tuqfilt: Seconds = None
        self.twppfiltq: Seconds = None
        self.twpqfiltq: Seconds = None
        self.twpufiltq: Seconds = None
        self.txft: Seconds = None
        self.txfv: Seconds = None
        self.uwpqdip: PU = None
        self.windPlantQcontrolModesType: WindPlantQcontrolModeKind = None
        self.xrefmax: PU = None
        self.xrefmin: PU = None

class WindProtectionIEC(IdentifiedObject):
    """RDF class WindProtectionIEC."""

    __slots__ = ('WindDynamicsLookupTable', 'dfimax', 'fover', 'funder', 'mzc', 'tfma', 'uover', 'uunder', 'WindTurbineType3or4IEC', 'WindTurbineType1or2IEC')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindProtectionIEC') -> None:
        """Initialize an RDF-defined CGMES object."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.WindDynamicsLookupTable: List[WindDynamicsLookupTable] = list()
        self.dfimax: PU = None
        self.fover: PU = None
        self.funder: PU = None
        self.mzc: bool = None
        self.tfma: Seconds = None
        self.uover: PU = None
        self.uunder: PU = None
        self.WindTurbineType3or4IEC: WindTurbineType3or4IEC = None
        self.WindTurbineType1or2IEC: WindTurbineType1or2IEC = None

class WindRefFrameRotIEC(IdentifiedObject):
    """RDF class WindRefFrameRotIEC."""

    __slots__ = ('tpll', 'upll1', 'upll2', 'WindTurbineType3or4IEC')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindRefFrameRotIEC') -> None:
        """Initialize an RDF-defined CGMES object."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.tpll: Seconds = None
        self.upll1: PU = None
        self.upll2: PU = None
        self.WindTurbineType3or4IEC: WindTurbineType3or4IEC = None

class CrossCompoundTurbineGovernorDynamics(DynamicsFunctionBlock):
    """RDF class CrossCompoundTurbineGovernorDynamics."""

    __slots__ = ('HighPressureSynchronousMachineDynamics', 'LowPressureSynchronousMachineDynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'CrossCompoundTurbineGovernorDynamics') -> None:
        """Initialize an RDF-defined CGMES object."""
        DynamicsFunctionBlock.__init__(self, rdfid=rdfid, tpe=tpe)
        self.HighPressureSynchronousMachineDynamics: SynchronousMachineDynamics = None
        self.LowPressureSynchronousMachineDynamics: SynchronousMachineDynamics = None

class DiscontinuousExcitationControlDynamics(DynamicsFunctionBlock):
    """RDF class DiscontinuousExcitationControlDynamics."""

    __slots__ = ('RemoteInputSignal', 'ExcitationSystemDynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'DiscontinuousExcitationControlDynamics') -> None:
        """Initialize an RDF-defined CGMES object."""
        DynamicsFunctionBlock.__init__(self, rdfid=rdfid, tpe=tpe)
        self.RemoteInputSignal: RemoteInputSignal = None
        self.ExcitationSystemDynamics: ExcitationSystemDynamics = None

class Equipment(PowerSystemResource):
    """RDF class Equipment."""

    __slots__ = ()

    def __init__(self, rdfid: str = "", tpe: str = 'Equipment') -> None:
        """Initialize an RDF-defined CGMES object."""
        PowerSystemResource.__init__(self, rdfid=rdfid, tpe=tpe)
        pass

class ExcitationSystemDynamics(DynamicsFunctionBlock):
    """RDF class ExcitationSystemDynamics."""

    __slots__ = ('SynchronousMachineDynamics', 'VoltageCompensatorDynamics', 'OverexcitationLimiterDynamics', 'PFVArControllerType2Dynamics', 'DiscontinuousExcitationControlDynamics', 'PowerSystemStabilizerDynamics', 'UnderexcitationLimiterDynamics', 'PFVArControllerType1Dynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcitationSystemDynamics') -> None:
        """Initialize an RDF-defined CGMES object."""
        DynamicsFunctionBlock.__init__(self, rdfid=rdfid, tpe=tpe)
        self.SynchronousMachineDynamics: SynchronousMachineDynamics = None
        self.VoltageCompensatorDynamics: VoltageCompensatorDynamics = None
        self.OverexcitationLimiterDynamics: OverexcitationLimiterDynamics = None
        self.PFVArControllerType2Dynamics: PFVArControllerType2Dynamics = None
        self.DiscontinuousExcitationControlDynamics: DiscontinuousExcitationControlDynamics = None
        self.PowerSystemStabilizerDynamics: PowerSystemStabilizerDynamics = None
        self.UnderexcitationLimiterDynamics: UnderexcitationLimiterDynamics = None
        self.PFVArControllerType1Dynamics: PFVArControllerType1Dynamics = None

class HVDCDynamics(DynamicsFunctionBlock):
    """RDF class HVDCDynamics."""

    __slots__ = ()

    def __init__(self, rdfid: str = "", tpe: str = 'HVDCDynamics') -> None:
        """Initialize an RDF-defined CGMES object."""
        DynamicsFunctionBlock.__init__(self, rdfid=rdfid, tpe=tpe)
        pass

class LoadAggregate(LoadDynamics):
    """RDF class LoadAggregate."""

    __slots__ = ('LoadMotor', 'LoadStatic')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'LoadAggregate') -> None:
        """Initialize an RDF-defined CGMES object."""
        LoadDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.LoadMotor: LoadMotor = None
        self.LoadStatic: LoadStatic = None

class LoadComposite(LoadDynamics):
    """RDF class LoadComposite."""

    __slots__ = ('epvs', 'epfs', 'eqvs', 'eqfs', 'epvd', 'epfd', 'eqvd', 'eqfd', 'lfac', 'h', 'pfrac')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'LoadComposite') -> None:
        """Initialize an RDF-defined CGMES object."""
        LoadDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.epvs: float = None
        self.epfs: float = None
        self.eqvs: float = None
        self.eqfs: float = None
        self.epvd: float = None
        self.epfd: float = None
        self.eqvd: float = None
        self.eqfd: float = None
        self.lfac: float = None
        self.h: Seconds = None
        self.pfrac: float = None

class LoadGenericNonLinear(LoadDynamics):
    """RDF class LoadGenericNonLinear."""

    __slots__ = ('genericNonLinearLoadModelType', 'tp', 'tq', 'ls', 'lt', 'bs', 'bt')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'LoadGenericNonLinear') -> None:
        """Initialize an RDF-defined CGMES object."""
        LoadDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.genericNonLinearLoadModelType: GenericNonLinearLoadModelKind = None
        self.tp: Seconds = None
        self.tq: Seconds = None
        self.ls: float = None
        self.lt: float = None
        self.bs: float = None
        self.bt: float = None

class LoadUserDefined(LoadDynamics):
    """RDF class LoadUserDefined."""

    __slots__ = ('proprietary', 'ProprietaryParameterDynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'LoadUserDefined') -> None:
        """Initialize an RDF-defined CGMES object."""
        LoadDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.proprietary: bool = None
        self.ProprietaryParameterDynamics: List[ProprietaryParameterDynamics] = list()

class MechanicalLoadDynamics(DynamicsFunctionBlock):
    """RDF class MechanicalLoadDynamics."""

    __slots__ = ('SynchronousMachineDynamics', 'AsynchronousMachineDynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'MechanicalLoadDynamics') -> None:
        """Initialize an RDF-defined CGMES object."""
        DynamicsFunctionBlock.__init__(self, rdfid=rdfid, tpe=tpe)
        self.SynchronousMachineDynamics: SynchronousMachineDynamics = None
        self.AsynchronousMachineDynamics: AsynchronousMachineDynamics = None

class OverexcitationLimiterDynamics(DynamicsFunctionBlock):
    """RDF class OverexcitationLimiterDynamics."""

    __slots__ = ('ExcitationSystemDynamics',)

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'OverexcitationLimiterDynamics') -> None:
        """Initialize an RDF-defined CGMES object."""
        DynamicsFunctionBlock.__init__(self, rdfid=rdfid, tpe=tpe)
        self.ExcitationSystemDynamics: ExcitationSystemDynamics = None

class PFVArControllerType1Dynamics(DynamicsFunctionBlock):
    """RDF class PFVArControllerType1Dynamics."""

    __slots__ = ('RemoteInputSignal', 'ExcitationSystemDynamics', 'VoltageAdjusterDynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'PFVArControllerType1Dynamics') -> None:
        """Initialize an RDF-defined CGMES object."""
        DynamicsFunctionBlock.__init__(self, rdfid=rdfid, tpe=tpe)
        self.RemoteInputSignal: RemoteInputSignal = None
        self.ExcitationSystemDynamics: ExcitationSystemDynamics = None
        self.VoltageAdjusterDynamics: VoltageAdjusterDynamics = None

class PFVArControllerType2Dynamics(DynamicsFunctionBlock):
    """RDF class PFVArControllerType2Dynamics."""

    __slots__ = ('ExcitationSystemDynamics',)

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'PFVArControllerType2Dynamics') -> None:
        """Initialize an RDF-defined CGMES object."""
        DynamicsFunctionBlock.__init__(self, rdfid=rdfid, tpe=tpe)
        self.ExcitationSystemDynamics: ExcitationSystemDynamics = None

class PowerSystemStabilizerDynamics(DynamicsFunctionBlock):
    """RDF class PowerSystemStabilizerDynamics."""

    __slots__ = ('RemoteInputSignal', 'ExcitationSystemDynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'PowerSystemStabilizerDynamics') -> None:
        """Initialize an RDF-defined CGMES object."""
        DynamicsFunctionBlock.__init__(self, rdfid=rdfid, tpe=tpe)
        self.RemoteInputSignal: List[RemoteInputSignal] = list()
        self.ExcitationSystemDynamics: ExcitationSystemDynamics = None

class RotatingMachineDynamics(DynamicsFunctionBlock):
    """RDF class RotatingMachineDynamics."""

    __slots__ = ('damping', 'inertia', 'saturationFactor', 'saturationFactor120', 'statorLeakageReactance', 'statorResistance')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'RotatingMachineDynamics') -> None:
        """Initialize an RDF-defined CGMES object."""
        DynamicsFunctionBlock.__init__(self, rdfid=rdfid, tpe=tpe)
        self.damping: float = None
        self.inertia: Seconds = None
        self.saturationFactor: float = None
        self.saturationFactor120: float = None
        self.statorLeakageReactance: PU = None
        self.statorResistance: PU = None

class StaticVarCompensatorDynamics(DynamicsFunctionBlock):
    """RDF class StaticVarCompensatorDynamics."""

    __slots__ = ('StaticVarCompensator',)

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'StaticVarCompensatorDynamics') -> None:
        """Initialize an RDF-defined CGMES object."""
        DynamicsFunctionBlock.__init__(self, rdfid=rdfid, tpe=tpe)
        self.StaticVarCompensator: StaticVarCompensator = None

class Terminal(ACDCTerminal):
    """RDF class Terminal."""

    __slots__ = ('ConductingEquipment', 'RemoteInputSignal')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'Terminal') -> None:
        """Initialize an RDF-defined CGMES object."""
        ACDCTerminal.__init__(self, rdfid=rdfid, tpe=tpe)
        self.ConductingEquipment: ConductingEquipment = None
        self.RemoteInputSignal: List[RemoteInputSignal] = list()

class TurbineGovernorDynamics(DynamicsFunctionBlock):
    """RDF class TurbineGovernorDynamics."""

    __slots__ = ('SynchronousMachineDynamics', 'AsynchronousMachineDynamics', 'TurbineLoadControllerDynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'TurbineGovernorDynamics') -> None:
        """Initialize an RDF-defined CGMES object."""
        DynamicsFunctionBlock.__init__(self, rdfid=rdfid, tpe=tpe)
        self.SynchronousMachineDynamics: SynchronousMachineDynamics = None
        self.AsynchronousMachineDynamics: AsynchronousMachineDynamics = None
        self.TurbineLoadControllerDynamics: TurbineLoadControllerDynamics = None

class TurbineLoadControllerDynamics(DynamicsFunctionBlock):
    """RDF class TurbineLoadControllerDynamics."""

    __slots__ = ('TurbineGovernorDynamics',)

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'TurbineLoadControllerDynamics') -> None:
        """Initialize an RDF-defined CGMES object."""
        DynamicsFunctionBlock.__init__(self, rdfid=rdfid, tpe=tpe)
        self.TurbineGovernorDynamics: TurbineGovernorDynamics = None

class UnderexcitationLimiterDynamics(DynamicsFunctionBlock):
    """RDF class UnderexcitationLimiterDynamics."""

    __slots__ = ('RemoteInputSignal', 'ExcitationSystemDynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'UnderexcitationLimiterDynamics') -> None:
        """Initialize an RDF-defined CGMES object."""
        DynamicsFunctionBlock.__init__(self, rdfid=rdfid, tpe=tpe)
        self.RemoteInputSignal: RemoteInputSignal = None
        self.ExcitationSystemDynamics: ExcitationSystemDynamics = None

class VoltageAdjusterDynamics(DynamicsFunctionBlock):
    """RDF class VoltageAdjusterDynamics."""

    __slots__ = ('PFVArControllerType1Dynamics',)

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'VoltageAdjusterDynamics') -> None:
        """Initialize an RDF-defined CGMES object."""
        DynamicsFunctionBlock.__init__(self, rdfid=rdfid, tpe=tpe)
        self.PFVArControllerType1Dynamics: PFVArControllerType1Dynamics = None

class VoltageCompensatorDynamics(DynamicsFunctionBlock):
    """RDF class VoltageCompensatorDynamics."""

    __slots__ = ('RemoteInputSignal', 'ExcitationSystemDynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'VoltageCompensatorDynamics') -> None:
        """Initialize an RDF-defined CGMES object."""
        DynamicsFunctionBlock.__init__(self, rdfid=rdfid, tpe=tpe)
        self.RemoteInputSignal: RemoteInputSignal = None
        self.ExcitationSystemDynamics: ExcitationSystemDynamics = None

class WindGenType3aIEC(WindGenType3IEC):
    """RDF class WindGenType3aIEC."""

    __slots__ = ('kpc', 'tic', 'WindTurbineType4IEC')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindGenType3aIEC') -> None:
        """Initialize an RDF-defined CGMES object."""
        WindGenType3IEC.__init__(self, rdfid=rdfid, tpe=tpe)
        self.kpc: float = None
        self.tic: Seconds = None
        self.WindTurbineType4IEC: WindTurbineType4IEC = None

class WindGenType3bIEC(WindGenType3IEC):
    """RDF class WindGenType3bIEC."""

    __slots__ = ('WindDynamicsLookupTable', 'mwtcwp', 'tg', 'two')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindGenType3bIEC') -> None:
        """Initialize an RDF-defined CGMES object."""
        WindGenType3IEC.__init__(self, rdfid=rdfid, tpe=tpe)
        self.WindDynamicsLookupTable: List[WindDynamicsLookupTable] = list()
        self.mwtcwp: bool = None
        self.tg: Seconds = None
        self.two: Seconds = None

class WindPlantDynamics(DynamicsFunctionBlock):
    """RDF class WindPlantDynamics."""

    __slots__ = ('RemoteInputSignal', 'WindTurbineType3or4Dynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindPlantDynamics') -> None:
        """Initialize an RDF-defined CGMES object."""
        DynamicsFunctionBlock.__init__(self, rdfid=rdfid, tpe=tpe)
        self.RemoteInputSignal: RemoteInputSignal = None
        self.WindTurbineType3or4Dynamics: List[WindTurbineType3or4Dynamics] = list()

class WindTurbineType1or2Dynamics(DynamicsFunctionBlock):
    """RDF class WindTurbineType1or2Dynamics."""

    __slots__ = ('RemoteInputSignal', 'AsynchronousMachineDynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindTurbineType1or2Dynamics') -> None:
        """Initialize an RDF-defined CGMES object."""
        DynamicsFunctionBlock.__init__(self, rdfid=rdfid, tpe=tpe)
        self.RemoteInputSignal: RemoteInputSignal = None
        self.AsynchronousMachineDynamics: AsynchronousMachineDynamics = None

class WindTurbineType3or4Dynamics(DynamicsFunctionBlock):
    """RDF class WindTurbineType3or4Dynamics."""

    __slots__ = ('PowerElectronicsConnection', 'RemoteInputSignal', 'WindPlantDynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindTurbineType3or4Dynamics') -> None:
        """Initialize an RDF-defined CGMES object."""
        DynamicsFunctionBlock.__init__(self, rdfid=rdfid, tpe=tpe)
        self.PowerElectronicsConnection: PowerElectronicsConnection = None
        self.RemoteInputSignal: RemoteInputSignal = None
        self.WindPlantDynamics: WindPlantDynamics = None

class AsynchronousMachineDynamics(RotatingMachineDynamics):
    """RDF class AsynchronousMachineDynamics."""

    __slots__ = ('AsynchronousMachine', 'TurbineGovernorDynamics', 'MechanicalLoadDynamics', 'WindTurbineType1or2Dynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'AsynchronousMachineDynamics') -> None:
        """Initialize an RDF-defined CGMES object."""
        RotatingMachineDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.AsynchronousMachine: AsynchronousMachine = None
        self.TurbineGovernorDynamics: TurbineGovernorDynamics = None
        self.MechanicalLoadDynamics: MechanicalLoadDynamics = None
        self.WindTurbineType1or2Dynamics: WindTurbineType1or2Dynamics = None

class CSCDynamics(HVDCDynamics):
    """RDF class CSCDynamics."""

    __slots__ = ('CSConverter',)

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'CSCDynamics') -> None:
        """Initialize an RDF-defined CGMES object."""
        HVDCDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.CSConverter: CsConverter = None

class ConductingEquipment(Equipment):
    """RDF class ConductingEquipment."""

    __slots__ = ('Terminals',)

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ConductingEquipment') -> None:
        """Initialize an RDF-defined CGMES object."""
        Equipment.__init__(self, rdfid=rdfid, tpe=tpe)
        self.Terminals: List[Terminal] = list()

class DiscExcContIEEEDEC1A(DiscontinuousExcitationControlDynamics):
    """RDF class DiscExcContIEEEDEC1A."""

    __slots__ = ('vtlmt', 'vomax', 'vomin', 'ketl', 'vtc', 'val', 'esc', 'kan', 'tan', 'tw5', 'vsmax', 'vsmin', 'td', 'tl1', 'tl2', 'vtm', 'vtn', 'vanmax')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'DiscExcContIEEEDEC1A') -> None:
        """Initialize an RDF-defined CGMES object."""
        DiscontinuousExcitationControlDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.vtlmt: PU = None
        self.vomax: PU = None
        self.vomin: PU = None
        self.ketl: PU = None
        self.vtc: PU = None
        self.val: PU = None
        self.esc: PU = None
        self.kan: PU = None
        self.tan: Seconds = None
        self.tw5: Seconds = None
        self.vsmax: PU = None
        self.vsmin: PU = None
        self.td: Seconds = None
        self.tl1: Seconds = None
        self.tl2: Seconds = None
        self.vtm: PU = None
        self.vtn: PU = None
        self.vanmax: PU = None

class DiscExcContIEEEDEC2A(DiscontinuousExcitationControlDynamics):
    """RDF class DiscExcContIEEEDEC2A."""

    __slots__ = ('vk', 'td1', 'td2', 'vdmin', 'vdmax')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'DiscExcContIEEEDEC2A') -> None:
        """Initialize an RDF-defined CGMES object."""
        DiscontinuousExcitationControlDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.vk: PU = None
        self.td1: Seconds = None
        self.td2: Seconds = None
        self.vdmin: PU = None
        self.vdmax: PU = None

class DiscExcContIEEEDEC3A(DiscontinuousExcitationControlDynamics):
    """RDF class DiscExcContIEEEDEC3A."""

    __slots__ = ('vtmin', 'tdr')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'DiscExcContIEEEDEC3A') -> None:
        """Initialize an RDF-defined CGMES object."""
        DiscontinuousExcitationControlDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.vtmin: PU = None
        self.tdr: Seconds = None

class DiscontinuousExcitationControlUserDefined(DiscontinuousExcitationControlDynamics):
    """RDF class DiscontinuousExcitationControlUserDefined."""

    __slots__ = ('proprietary', 'ProprietaryParameterDynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'DiscontinuousExcitationControlUserDefined') -> None:
        """Initialize an RDF-defined CGMES object."""
        DiscontinuousExcitationControlDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.proprietary: bool = None
        self.ProprietaryParameterDynamics: List[ProprietaryParameterDynamics] = list()

class ExcAC1A(ExcitationSystemDynamics):
    """RDF class ExcAC1A."""

    __slots__ = ('tb', 'tc', 'ka', 'ta', 'vamax', 'vamin', 'te', 'kf', 'kf1', 'kf2', 'ks', 'tf', 'kc', 'kd', 'ke', 've1', 'seve1', 've2', 'seve2', 'vrmax', 'vrmin', 'hvlvgates')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcAC1A') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.tb: Seconds = None
        self.tc: Seconds = None
        self.ka: PU = None
        self.ta: Seconds = None
        self.vamax: PU = None
        self.vamin: PU = None
        self.te: Seconds = None
        self.kf: PU = None
        self.kf1: PU = None
        self.kf2: PU = None
        self.ks: PU = None
        self.tf: Seconds = None
        self.kc: PU = None
        self.kd: PU = None
        self.ke: PU = None
        self.ve1: PU = None
        self.seve1: float = None
        self.ve2: PU = None
        self.seve2: float = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.hvlvgates: bool = None

class ExcAC2A(ExcitationSystemDynamics):
    """RDF class ExcAC2A."""

    __slots__ = ('tb', 'tc', 'ka', 'ta', 'vamax', 'vamin', 'kb', 'kb1', 'vrmax', 'vrmin', 'te', 'vfemax', 'kh', 'kf', 'kl', 'vlr', 'kl1', 'ks', 'tf', 'kc', 'kd', 'ke', 've1', 'seve1', 've2', 'seve2', 'hvgate', 'lvgate')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcAC2A') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.tb: Seconds = None
        self.tc: Seconds = None
        self.ka: PU = None
        self.ta: Seconds = None
        self.vamax: PU = None
        self.vamin: PU = None
        self.kb: PU = None
        self.kb1: PU = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.te: Seconds = None
        self.vfemax: PU = None
        self.kh: PU = None
        self.kf: PU = None
        self.kl: PU = None
        self.vlr: PU = None
        self.kl1: PU = None
        self.ks: PU = None
        self.tf: Seconds = None
        self.kc: PU = None
        self.kd: PU = None
        self.ke: PU = None
        self.ve1: PU = None
        self.seve1: float = None
        self.ve2: PU = None
        self.seve2: float = None
        self.hvgate: bool = None
        self.lvgate: bool = None

class ExcAC3A(ExcitationSystemDynamics):
    """RDF class ExcAC3A."""

    __slots__ = ('tb', 'tc', 'ka', 'ta', 'vamax', 'vamin', 'te', 'vemin', 'kr', 'kf', 'tf', 'kn', 'efdn', 'kc', 'kd', 'ke', 'klv', 'kf1', 'kf2', 'ks', 'vfemax', 've1', 'seve1', 've2', 'seve2', 'vlv')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcAC3A') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.tb: Seconds = None
        self.tc: Seconds = None
        self.ka: Seconds = None
        self.ta: PU = None
        self.vamax: PU = None
        self.vamin: PU = None
        self.te: Seconds = None
        self.vemin: PU = None
        self.kr: PU = None
        self.kf: PU = None
        self.tf: Seconds = None
        self.kn: PU = None
        self.efdn: PU = None
        self.kc: PU = None
        self.kd: PU = None
        self.ke: PU = None
        self.klv: PU = None
        self.kf1: PU = None
        self.kf2: PU = None
        self.ks: PU = None
        self.vfemax: PU = None
        self.ve1: PU = None
        self.seve1: float = None
        self.ve2: PU = None
        self.seve2: float = None
        self.vlv: PU = None

class ExcAC4A(ExcitationSystemDynamics):
    """RDF class ExcAC4A."""

    __slots__ = ('vimax', 'vimin', 'tc', 'tb', 'ka', 'ta', 'vrmax', 'vrmin', 'kc')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcAC4A') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.vimax: PU = None
        self.vimin: PU = None
        self.tc: Seconds = None
        self.tb: Seconds = None
        self.ka: PU = None
        self.ta: Seconds = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.kc: PU = None

class ExcAC5A(ExcitationSystemDynamics):
    """RDF class ExcAC5A."""

    __slots__ = ('ka', 'ks', 'tb', 'tc', 'ta', 'vrmax', 'vrmin', 'ke', 'te', 'kf', 'tf1', 'tf2', 'tf3', 'efd1', 'seefd1', 'efd2', 'seefd2', 'a')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcAC5A') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.ka: PU = None
        self.ks: PU = None
        self.tb: Seconds = None
        self.tc: Seconds = None
        self.ta: Seconds = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.ke: PU = None
        self.te: Seconds = None
        self.kf: PU = None
        self.tf1: Seconds = None
        self.tf2: Seconds = None
        self.tf3: Seconds = None
        self.efd1: PU = None
        self.seefd1: float = None
        self.efd2: PU = None
        self.seefd2: float = None
        self.a: float = None

class ExcAC6A(ExcitationSystemDynamics):
    """RDF class ExcAC6A."""

    __slots__ = ('ka', 'ks', 'ta', 'tk', 'tb', 'tc', 'vamax', 'vamin', 'vrmax', 'vrmin', 'te', 'kh', 'tj', 'th', 'vfelim', 'vhmax', 'kc', 'kd', 'ke', 've1', 'seve1', 've2', 'seve2')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcAC6A') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.ka: PU = None
        self.ks: PU = None
        self.ta: Seconds = None
        self.tk: Seconds = None
        self.tb: Seconds = None
        self.tc: Seconds = None
        self.vamax: PU = None
        self.vamin: PU = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.te: Seconds = None
        self.kh: PU = None
        self.tj: Seconds = None
        self.th: Seconds = None
        self.vfelim: PU = None
        self.vhmax: PU = None
        self.kc: PU = None
        self.kd: PU = None
        self.ke: PU = None
        self.ve1: PU = None
        self.seve1: float = None
        self.ve2: PU = None
        self.seve2: float = None

class ExcAC8B(ExcitationSystemDynamics):
    """RDF class ExcAC8B."""

    __slots__ = ('inlim', 'ka', 'kc', 'kd', 'kdr', 'ke', 'kir', 'kpr', 'ks', 'pidlim', 'seve1', 'seve2', 'ta', 'tdr', 'te', 'telim', 've1', 've2', 'vemin', 'vfemax', 'vimax', 'vimin', 'vpidmax', 'vpidmin', 'vrmax', 'vrmin', 'vtmult')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcAC8B') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.inlim: bool = None
        self.ka: PU = None
        self.kc: PU = None
        self.kd: PU = None
        self.kdr: PU = None
        self.ke: PU = None
        self.kir: PU = None
        self.kpr: PU = None
        self.ks: PU = None
        self.pidlim: bool = None
        self.seve1: float = None
        self.seve2: float = None
        self.ta: Seconds = None
        self.tdr: Seconds = None
        self.te: Seconds = None
        self.telim: bool = None
        self.ve1: PU = None
        self.ve2: PU = None
        self.vemin: PU = None
        self.vfemax: PU = None
        self.vimax: PU = None
        self.vimin: PU = None
        self.vpidmax: PU = None
        self.vpidmin: PU = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.vtmult: bool = None

class ExcANS(ExcitationSystemDynamics):
    """RDF class ExcANS."""

    __slots__ = ('k3', 'k2', 'kce', 't3', 't2', 't1', 'blint', 'kvfif', 'ifmn', 'ifmx', 'vrmn', 'vrmx', 'krvecc', 'tb')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcANS') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.k3: float = None
        self.k2: float = None
        self.kce: float = None
        self.t3: Seconds = None
        self.t2: Seconds = None
        self.t1: Seconds = None
        self.blint: int = None
        self.kvfif: int = None
        self.ifmn: PU = None
        self.ifmx: PU = None
        self.vrmn: PU = None
        self.vrmx: PU = None
        self.krvecc: int = None
        self.tb: Seconds = None

class ExcAVR1(ExcitationSystemDynamics):
    """RDF class ExcAVR1."""

    __slots__ = ('ka', 'vrmn', 'vrmx', 'ta', 'tb', 'te', 'e1', 'se1', 'e2', 'se2', 'kf', 'tf')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcAVR1') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.ka: float = None
        self.vrmn: PU = None
        self.vrmx: PU = None
        self.ta: Seconds = None
        self.tb: Seconds = None
        self.te: Seconds = None
        self.e1: PU = None
        self.se1: float = None
        self.e2: PU = None
        self.se2: float = None
        self.kf: float = None
        self.tf: Seconds = None

class ExcAVR2(ExcitationSystemDynamics):
    """RDF class ExcAVR2."""

    __slots__ = ('ka', 'vrmn', 'vrmx', 'ta', 'tb', 'te', 'e1', 'se1', 'e2', 'se2', 'kf', 'tf1', 'tf2')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcAVR2') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.ka: float = None
        self.vrmn: PU = None
        self.vrmx: PU = None
        self.ta: Seconds = None
        self.tb: Seconds = None
        self.te: Seconds = None
        self.e1: PU = None
        self.se1: float = None
        self.e2: PU = None
        self.se2: float = None
        self.kf: float = None
        self.tf1: Seconds = None
        self.tf2: Seconds = None

class ExcAVR3(ExcitationSystemDynamics):
    """RDF class ExcAVR3."""

    __slots__ = ('ka', 'vrmn', 'vrmx', 't1', 't2', 't3', 't4', 'te', 'e1', 'se1', 'e2', 'se2')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcAVR3') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.ka: float = None
        self.vrmn: PU = None
        self.vrmx: PU = None
        self.t1: Seconds = None
        self.t2: Seconds = None
        self.t3: Seconds = None
        self.t4: Seconds = None
        self.te: Seconds = None
        self.e1: PU = None
        self.se1: float = None
        self.e2: PU = None
        self.se2: float = None

class ExcAVR4(ExcitationSystemDynamics):
    """RDF class ExcAVR4."""

    __slots__ = ('ka', 'vrmn', 'vrmx', 't1', 't2', 't3', 't4', 'ke', 'vfmx', 'vfmn', 'kif', 'tif', 't1if', 'imul')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcAVR4') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.ka: float = None
        self.vrmn: PU = None
        self.vrmx: PU = None
        self.t1: Seconds = None
        self.t2: Seconds = None
        self.t3: Seconds = None
        self.t4: Seconds = None
        self.ke: float = None
        self.vfmx: PU = None
        self.vfmn: PU = None
        self.kif: float = None
        self.tif: Seconds = None
        self.t1if: Seconds = None
        self.imul: bool = None

class ExcAVR5(ExcitationSystemDynamics):
    """RDF class ExcAVR5."""

    __slots__ = ('ka', 'ta', 'rex')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcAVR5') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.ka: PU = None
        self.ta: Seconds = None
        self.rex: PU = None

class ExcAVR7(ExcitationSystemDynamics):
    """RDF class ExcAVR7."""

    __slots__ = ('k1', 'a1', 'a2', 't1', 't2', 'vmax1', 'vmin1', 'k3', 'a3', 'a4', 't3', 't4', 'vmax3', 'vmin3', 'k5', 'a5', 'a6', 't5', 't6', 'vmax5', 'vmin5')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcAVR7') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.k1: PU = None
        self.a1: PU = None
        self.a2: PU = None
        self.t1: Seconds = None
        self.t2: Seconds = None
        self.vmax1: PU = None
        self.vmin1: PU = None
        self.k3: PU = None
        self.a3: PU = None
        self.a4: PU = None
        self.t3: Seconds = None
        self.t4: Seconds = None
        self.vmax3: PU = None
        self.vmin3: PU = None
        self.k5: PU = None
        self.a5: PU = None
        self.a6: PU = None
        self.t5: Seconds = None
        self.t6: Seconds = None
        self.vmax5: PU = None
        self.vmin5: PU = None

class ExcBBC(ExcitationSystemDynamics):
    """RDF class ExcBBC."""

    __slots__ = ('t1', 't2', 't3', 't4', 'k', 'vrmin', 'vrmax', 'efdmin', 'efdmax', 'xe', 'switch')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcBBC') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.t1: Seconds = None
        self.t2: Seconds = None
        self.t3: Seconds = None
        self.t4: Seconds = None
        self.k: PU = None
        self.vrmin: PU = None
        self.vrmax: PU = None
        self.efdmin: PU = None
        self.efdmax: PU = None
        self.xe: PU = None
        self.switch: bool = None

class ExcCZ(ExcitationSystemDynamics):
    """RDF class ExcCZ."""

    __slots__ = ('kp', 'tc', 'vrmax', 'vrmin', 'ka', 'ta', 'ke', 'te', 'efdmax', 'efdmin')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcCZ') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.kp: PU = None
        self.tc: Seconds = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.ka: PU = None
        self.ta: Seconds = None
        self.ke: PU = None
        self.te: Seconds = None
        self.efdmax: PU = None
        self.efdmin: PU = None

class ExcDC1A(ExcitationSystemDynamics):
    """RDF class ExcDC1A."""

    __slots__ = ('ka', 'ks', 'ta', 'tb', 'tc', 'vrmax', 'vrmin', 'ke', 'te', 'kf', 'tf', 'efd1', 'seefd1', 'efd2', 'seefd2', 'exclim', 'efdmin', 'efdmax')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcDC1A') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.ka: PU = None
        self.ks: PU = None
        self.ta: Seconds = None
        self.tb: Seconds = None
        self.tc: Seconds = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.ke: PU = None
        self.te: Seconds = None
        self.kf: PU = None
        self.tf: Seconds = None
        self.efd1: PU = None
        self.seefd1: float = None
        self.efd2: PU = None
        self.seefd2: float = None
        self.exclim: bool = None
        self.efdmin: PU = None
        self.efdmax: PU = None

class ExcDC2A(ExcitationSystemDynamics):
    """RDF class ExcDC2A."""

    __slots__ = ('ka', 'ks', 'ta', 'tb', 'tc', 'vrmax', 'vrmin', 'ke', 'te', 'kf', 'tf', 'tf1', 'efd1', 'seefd1', 'efd2', 'seefd2', 'exclim', 'vtlim')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcDC2A') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.ka: PU = None
        self.ks: PU = None
        self.ta: Seconds = None
        self.tb: Seconds = None
        self.tc: Seconds = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.ke: PU = None
        self.te: Seconds = None
        self.kf: PU = None
        self.tf: Seconds = None
        self.tf1: Seconds = None
        self.efd1: PU = None
        self.seefd1: float = None
        self.efd2: PU = None
        self.seefd2: float = None
        self.exclim: bool = None
        self.vtlim: bool = None

class ExcDC3A(ExcitationSystemDynamics):
    """RDF class ExcDC3A."""

    __slots__ = ('trh', 'ks', 'kr', 'kv', 'vrmax', 'vrmin', 'te', 'ke', 'efd1', 'seefd1', 'efd2', 'seefd2', 'exclim', 'efdmax', 'efdmin', 'efdlim')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcDC3A') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.trh: Seconds = None
        self.ks: PU = None
        self.kr: PU = None
        self.kv: PU = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.te: Seconds = None
        self.ke: PU = None
        self.efd1: PU = None
        self.seefd1: float = None
        self.efd2: PU = None
        self.seefd2: float = None
        self.exclim: bool = None
        self.efdmax: PU = None
        self.efdmin: PU = None
        self.efdlim: bool = None

class ExcDC3A1(ExcitationSystemDynamics):
    """RDF class ExcDC3A1."""

    __slots__ = ('ka', 'ta', 'vrmax', 'vrmin', 'te', 'kf', 'tf', 'kp', 'ki', 'vbmax', 'exclim', 'ke', 'vb1max', 'vblim')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcDC3A1') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.ka: PU = None
        self.ta: Seconds = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.te: Seconds = None
        self.kf: PU = None
        self.tf: Seconds = None
        self.kp: PU = None
        self.ki: PU = None
        self.vbmax: PU = None
        self.exclim: bool = None
        self.ke: PU = None
        self.vb1max: PU = None
        self.vblim: bool = None

class ExcELIN1(ExcitationSystemDynamics):
    """RDF class ExcELIN1."""

    __slots__ = ('tfi', 'tnu', 'vpu', 'vpi', 'vpnf', 'dpnf', 'tsw', 'efmin', 'efmax', 'xe', 'ks1', 'ks2', 'ts1', 'ts2', 'smax')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcELIN1') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.tfi: Seconds = None
        self.tnu: Seconds = None
        self.vpu: PU = None
        self.vpi: PU = None
        self.vpnf: PU = None
        self.dpnf: PU = None
        self.tsw: Seconds = None
        self.efmin: PU = None
        self.efmax: PU = None
        self.xe: PU = None
        self.ks1: PU = None
        self.ks2: PU = None
        self.ts1: Seconds = None
        self.ts2: Seconds = None
        self.smax: PU = None

class ExcELIN2(ExcitationSystemDynamics):
    """RDF class ExcELIN2."""

    __slots__ = ('k1', 'k1ec', 'kd1', 'tb1', 'pid1max', 'ti1', 'iefmax2', 'k2', 'ketb', 'upmax', 'upmin', 'te', 'xp', 'te2', 'ke2', 've1', 'seve1', 've2', 'seve2', 'tr4', 'k3', 'ti3', 'k4', 'ti4', 'iefmax', 'iefmin', 'efdbas')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcELIN2') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.k1: PU = None
        self.k1ec: PU = None
        self.kd1: PU = None
        self.tb1: Seconds = None
        self.pid1max: PU = None
        self.ti1: PU = None
        self.iefmax2: PU = None
        self.k2: PU = None
        self.ketb: PU = None
        self.upmax: PU = None
        self.upmin: PU = None
        self.te: Seconds = None
        self.xp: PU = None
        self.te2: Seconds = None
        self.ke2: PU = None
        self.ve1: PU = None
        self.seve1: PU = None
        self.ve2: PU = None
        self.seve2: PU = None
        self.tr4: Seconds = None
        self.k3: PU = None
        self.ti3: Seconds = None
        self.k4: PU = None
        self.ti4: Seconds = None
        self.iefmax: PU = None
        self.iefmin: PU = None
        self.efdbas: PU = None

class ExcHU(ExcitationSystemDynamics):
    """RDF class ExcHU."""

    __slots__ = ('tr', 'te', 'imin', 'imax', 'ae', 'emin', 'emax', 'ki', 'ai', 'ti', 'atr', 'ke')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcHU') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.tr: Seconds = None
        self.te: Seconds = None
        self.imin: PU = None
        self.imax: PU = None
        self.ae: PU = None
        self.emin: PU = None
        self.emax: PU = None
        self.ki: float = None
        self.ai: PU = None
        self.ti: Seconds = None
        self.atr: PU = None
        self.ke: float = None

class ExcIEEEAC1A(ExcitationSystemDynamics):
    """RDF class ExcIEEEAC1A."""

    __slots__ = ('tb', 'tc', 'ka', 'ta', 'vamax', 'vamin', 'te', 'kf', 'tf', 'kc', 'kd', 'ke', 've1', 'seve1', 've2', 'seve2', 'vrmax', 'vrmin')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcIEEEAC1A') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.tb: Seconds = None
        self.tc: Seconds = None
        self.ka: PU = None
        self.ta: Seconds = None
        self.vamax: PU = None
        self.vamin: PU = None
        self.te: Seconds = None
        self.kf: PU = None
        self.tf: Seconds = None
        self.kc: PU = None
        self.kd: PU = None
        self.ke: PU = None
        self.ve1: PU = None
        self.seve1: float = None
        self.ve2: PU = None
        self.seve2: float = None
        self.vrmax: PU = None
        self.vrmin: PU = None

class ExcIEEEAC2A(ExcitationSystemDynamics):
    """RDF class ExcIEEEAC2A."""

    __slots__ = ('tb', 'tc', 'ka', 'ta', 'vamax', 'vamin', 'kb', 'vrmax', 'vrmin', 'te', 'vfemax', 'kh', 'kf', 'tf', 'kc', 'kd', 'ke', 've1', 'seve1', 've2', 'seve2')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcIEEEAC2A') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.tb: Seconds = None
        self.tc: Seconds = None
        self.ka: PU = None
        self.ta: Seconds = None
        self.vamax: PU = None
        self.vamin: PU = None
        self.kb: PU = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.te: Seconds = None
        self.vfemax: PU = None
        self.kh: PU = None
        self.kf: PU = None
        self.tf: Seconds = None
        self.kc: PU = None
        self.kd: PU = None
        self.ke: PU = None
        self.ve1: PU = None
        self.seve1: float = None
        self.ve2: PU = None
        self.seve2: float = None

class ExcIEEEAC3A(ExcitationSystemDynamics):
    """RDF class ExcIEEEAC3A."""

    __slots__ = ('tb', 'tc', 'ka', 'ta', 'vamax', 'vamin', 'te', 'vemin', 'kr', 'kf', 'tf', 'kn', 'efdn', 'kc', 'kd', 'ke', 'vfemax', 've1', 'seve1', 've2', 'seve2')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcIEEEAC3A') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.tb: Seconds = None
        self.tc: Seconds = None
        self.ka: PU = None
        self.ta: Seconds = None
        self.vamax: PU = None
        self.vamin: PU = None
        self.te: Seconds = None
        self.vemin: PU = None
        self.kr: PU = None
        self.kf: PU = None
        self.tf: Seconds = None
        self.kn: PU = None
        self.efdn: PU = None
        self.kc: PU = None
        self.kd: PU = None
        self.ke: PU = None
        self.vfemax: PU = None
        self.ve1: PU = None
        self.seve1: float = None
        self.ve2: PU = None
        self.seve2: float = None

class ExcIEEEAC4A(ExcitationSystemDynamics):
    """RDF class ExcIEEEAC4A."""

    __slots__ = ('vimax', 'vimin', 'tc', 'tb', 'ka', 'ta', 'vrmax', 'vrmin', 'kc')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcIEEEAC4A') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.vimax: PU = None
        self.vimin: PU = None
        self.tc: Seconds = None
        self.tb: Seconds = None
        self.ka: PU = None
        self.ta: Seconds = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.kc: PU = None

class ExcIEEEAC5A(ExcitationSystemDynamics):
    """RDF class ExcIEEEAC5A."""

    __slots__ = ('ka', 'ta', 'vrmax', 'vrmin', 'ke', 'te', 'kf', 'tf1', 'tf2', 'tf3', 'efd1', 'seefd1', 'efd2', 'seefd2')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcIEEEAC5A') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.ka: PU = None
        self.ta: Seconds = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.ke: PU = None
        self.te: Seconds = None
        self.kf: PU = None
        self.tf1: Seconds = None
        self.tf2: Seconds = None
        self.tf3: Seconds = None
        self.efd1: PU = None
        self.seefd1: float = None
        self.efd2: PU = None
        self.seefd2: float = None

class ExcIEEEAC6A(ExcitationSystemDynamics):
    """RDF class ExcIEEEAC6A."""

    __slots__ = ('ka', 'ta', 'tk', 'tb', 'tc', 'vamax', 'vamin', 'vrmax', 'vrmin', 'te', 'kh', 'tj', 'th', 'vfelim', 'vhmax', 'kc', 'kd', 'ke', 've1', 'seve1', 've2', 'seve2')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcIEEEAC6A') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.ka: PU = None
        self.ta: Seconds = None
        self.tk: Seconds = None
        self.tb: Seconds = None
        self.tc: Seconds = None
        self.vamax: PU = None
        self.vamin: PU = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.te: Seconds = None
        self.kh: PU = None
        self.tj: Seconds = None
        self.th: Seconds = None
        self.vfelim: PU = None
        self.vhmax: PU = None
        self.kc: PU = None
        self.kd: PU = None
        self.ke: PU = None
        self.ve1: PU = None
        self.seve1: float = None
        self.ve2: PU = None
        self.seve2: float = None

class ExcIEEEAC7B(ExcitationSystemDynamics):
    """RDF class ExcIEEEAC7B."""

    __slots__ = ('kpr', 'kir', 'kdr', 'tdr', 'vrmax', 'vrmin', 'kpa', 'kia', 'vamax', 'vamin', 'kp', 'kl', 'te', 'vfemax', 'vemin', 'ke', 'kc', 'kd', 'kf1', 'kf2', 'kf3', 'tf', 've1', 'seve1', 've2', 'seve2')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcIEEEAC7B') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.kpr: PU = None
        self.kir: PU = None
        self.kdr: PU = None
        self.tdr: Seconds = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.kpa: PU = None
        self.kia: PU = None
        self.vamax: PU = None
        self.vamin: PU = None
        self.kp: PU = None
        self.kl: PU = None
        self.te: Seconds = None
        self.vfemax: PU = None
        self.vemin: PU = None
        self.ke: PU = None
        self.kc: PU = None
        self.kd: PU = None
        self.kf1: PU = None
        self.kf2: PU = None
        self.kf3: PU = None
        self.tf: Seconds = None
        self.ve1: PU = None
        self.seve1: float = None
        self.ve2: PU = None
        self.seve2: float = None

class ExcIEEEAC8B(ExcitationSystemDynamics):
    """RDF class ExcIEEEAC8B."""

    __slots__ = ('kpr', 'kir', 'kdr', 'tdr', 'vrmax', 'vrmin', 'ka', 'ta', 'te', 'vfemax', 'vemin', 'ke', 'kc', 'kd', 've1', 'seve1', 've2', 'seve2')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcIEEEAC8B') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.kpr: PU = None
        self.kir: PU = None
        self.kdr: PU = None
        self.tdr: Seconds = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.ka: PU = None
        self.ta: Seconds = None
        self.te: Seconds = None
        self.vfemax: PU = None
        self.vemin: PU = None
        self.ke: PU = None
        self.kc: PU = None
        self.kd: PU = None
        self.ve1: PU = None
        self.seve1: float = None
        self.ve2: PU = None
        self.seve2: float = None

class ExcIEEEDC1A(ExcitationSystemDynamics):
    """RDF class ExcIEEEDC1A."""

    __slots__ = ('ka', 'ta', 'tb', 'tc', 'vrmax', 'vrmin', 'ke', 'te', 'kf', 'tf', 'efd1', 'seefd1', 'efd2', 'seefd2', 'uelin', 'exclim')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcIEEEDC1A') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.ka: PU = None
        self.ta: Seconds = None
        self.tb: Seconds = None
        self.tc: Seconds = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.ke: PU = None
        self.te: Seconds = None
        self.kf: PU = None
        self.tf: Seconds = None
        self.efd1: PU = None
        self.seefd1: float = None
        self.efd2: PU = None
        self.seefd2: float = None
        self.uelin: bool = None
        self.exclim: bool = None

class ExcIEEEDC2A(ExcitationSystemDynamics):
    """RDF class ExcIEEEDC2A."""

    __slots__ = ('efd1', 'efd2', 'exclim', 'ka', 'ke', 'kf', 'seefd1', 'seefd2', 'ta', 'tb', 'tc', 'te', 'tf', 'uelin', 'vrmax', 'vrmin')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcIEEEDC2A') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.efd1: PU = None
        self.efd2: PU = None
        self.exclim: PU = None
        self.ka: PU = None
        self.ke: PU = None
        self.kf: PU = None
        self.seefd1: float = None
        self.seefd2: float = None
        self.ta: Seconds = None
        self.tb: Seconds = None
        self.tc: Seconds = None
        self.te: Seconds = None
        self.tf: Seconds = None
        self.uelin: bool = None
        self.vrmax: PU = None
        self.vrmin: PU = None

class ExcIEEEDC3A(ExcitationSystemDynamics):
    """RDF class ExcIEEEDC3A."""

    __slots__ = ('trh', 'kv', 'vrmax', 'vrmin', 'te', 'ke', 'efd1', 'seefd1', 'efd2', 'seefd2', 'exclim')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcIEEEDC3A') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.trh: Seconds = None
        self.kv: PU = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.te: Seconds = None
        self.ke: PU = None
        self.efd1: PU = None
        self.seefd1: float = None
        self.efd2: PU = None
        self.seefd2: float = None
        self.exclim: bool = None

class ExcIEEEDC4B(ExcitationSystemDynamics):
    """RDF class ExcIEEEDC4B."""

    __slots__ = ('ka', 'ta', 'kp', 'ki', 'kd', 'td', 'vrmax', 'vrmin', 'ke', 'te', 'kf', 'tf', 'efd1', 'seefd1', 'efd2', 'seefd2', 'vemin', 'oelin', 'uelin')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcIEEEDC4B') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.ka: PU = None
        self.ta: Seconds = None
        self.kp: PU = None
        self.ki: PU = None
        self.kd: PU = None
        self.td: Seconds = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.ke: PU = None
        self.te: Seconds = None
        self.kf: PU = None
        self.tf: Seconds = None
        self.efd1: PU = None
        self.seefd1: float = None
        self.efd2: PU = None
        self.seefd2: float = None
        self.vemin: PU = None
        self.oelin: bool = None
        self.uelin: bool = None

class ExcIEEEST1A(ExcitationSystemDynamics):
    """RDF class ExcIEEEST1A."""

    __slots__ = ('ilr', 'ka', 'kc', 'kf', 'klr', 'pssin', 'ta', 'tb', 'tb1', 'tc', 'tc1', 'tf', 'uelin', 'vamax', 'vamin', 'vimax', 'vimin', 'vrmax', 'vrmin')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcIEEEST1A') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.ilr: PU = None
        self.ka: PU = None
        self.kc: PU = None
        self.kf: PU = None
        self.klr: PU = None
        self.pssin: bool = None
        self.ta: Seconds = None
        self.tb: Seconds = None
        self.tb1: Seconds = None
        self.tc: Seconds = None
        self.tc1: Seconds = None
        self.tf: Seconds = None
        self.uelin: ExcIEEEST1AUELselectorKind = None
        self.vamax: PU = None
        self.vamin: PU = None
        self.vimax: PU = None
        self.vimin: PU = None
        self.vrmax: PU = None
        self.vrmin: PU = None

class ExcIEEEST2A(ExcitationSystemDynamics):
    """RDF class ExcIEEEST2A."""

    __slots__ = ('ka', 'ta', 'vrmax', 'vrmin', 'ke', 'te', 'kf', 'tf', 'kp', 'ki', 'kc', 'efdmax', 'uelin')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcIEEEST2A') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.ka: PU = None
        self.ta: Seconds = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.ke: PU = None
        self.te: Seconds = None
        self.kf: PU = None
        self.tf: Seconds = None
        self.kp: PU = None
        self.ki: PU = None
        self.kc: PU = None
        self.efdmax: PU = None
        self.uelin: bool = None

class ExcIEEEST3A(ExcitationSystemDynamics):
    """RDF class ExcIEEEST3A."""

    __slots__ = ('vimax', 'vimin', 'ka', 'ta', 'tb', 'tc', 'vrmax', 'vrmin', 'km', 'tm', 'vmmax', 'vmmin', 'kg', 'kp', 'thetap', 'ki', 'kc', 'xl', 'vbmax', 'vgmax')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcIEEEST3A') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.vimax: PU = None
        self.vimin: PU = None
        self.ka: PU = None
        self.ta: Seconds = None
        self.tb: Seconds = None
        self.tc: Seconds = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.km: PU = None
        self.tm: Seconds = None
        self.vmmax: PU = None
        self.vmmin: PU = None
        self.kg: PU = None
        self.kp: PU = None
        self.thetap: AngleDegrees = None
        self.ki: PU = None
        self.kc: PU = None
        self.xl: PU = None
        self.vbmax: PU = None
        self.vgmax: PU = None

class ExcIEEEST4B(ExcitationSystemDynamics):
    """RDF class ExcIEEEST4B."""

    __slots__ = ('kpr', 'kir', 'ta', 'vrmax', 'vrmin', 'kpm', 'kim', 'vmmax', 'vmmin', 'kg', 'kp', 'thetap', 'ki', 'kc', 'xl', 'vbmax')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcIEEEST4B') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.kpr: PU = None
        self.kir: PU = None
        self.ta: Seconds = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.kpm: PU = None
        self.kim: PU = None
        self.vmmax: PU = None
        self.vmmin: PU = None
        self.kg: PU = None
        self.kp: PU = None
        self.thetap: AngleDegrees = None
        self.ki: PU = None
        self.kc: PU = None
        self.xl: PU = None
        self.vbmax: PU = None

class ExcIEEEST5B(ExcitationSystemDynamics):
    """RDF class ExcIEEEST5B."""

    __slots__ = ('kr', 't1', 'kc', 'vrmax', 'vrmin', 'tc1', 'tb1', 'tc2', 'tb2', 'toc1', 'tob1', 'toc2', 'tob2', 'tuc1', 'tub1', 'tuc2', 'tub2')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcIEEEST5B') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.kr: PU = None
        self.t1: Seconds = None
        self.kc: PU = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.tc1: Seconds = None
        self.tb1: Seconds = None
        self.tc2: Seconds = None
        self.tb2: Seconds = None
        self.toc1: Seconds = None
        self.tob1: Seconds = None
        self.toc2: Seconds = None
        self.tob2: Seconds = None
        self.tuc1: Seconds = None
        self.tub1: Seconds = None
        self.tuc2: Seconds = None
        self.tub2: Seconds = None

class ExcIEEEST6B(ExcitationSystemDynamics):
    """RDF class ExcIEEEST6B."""

    __slots__ = ('ilr', 'kci', 'kff', 'kg', 'kia', 'klr', 'km', 'kpa', 'oelin', 'tg', 'vamax', 'vamin', 'vrmax', 'vrmin')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcIEEEST6B') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.ilr: PU = None
        self.kci: PU = None
        self.kff: PU = None
        self.kg: PU = None
        self.kia: PU = None
        self.klr: PU = None
        self.km: PU = None
        self.kpa: PU = None
        self.oelin: ExcST6BOELselectorKind = None
        self.tg: Seconds = None
        self.vamax: PU = None
        self.vamin: PU = None
        self.vrmax: PU = None
        self.vrmin: PU = None

class ExcIEEEST7B(ExcitationSystemDynamics):
    """RDF class ExcIEEEST7B."""

    __slots__ = ('kh', 'kia', 'kl', 'kpa', 'oelin', 'tb', 'tc', 'tf', 'tg', 'tia', 'uelin', 'vmax', 'vmin', 'vrmax', 'vrmin')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcIEEEST7B') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.kh: PU = None
        self.kia: PU = None
        self.kl: PU = None
        self.kpa: PU = None
        self.oelin: ExcST7BOELselectorKind = None
        self.tb: Seconds = None
        self.tc: Seconds = None
        self.tf: Seconds = None
        self.tg: Seconds = None
        self.tia: Seconds = None
        self.uelin: ExcST7BUELselectorKind = None
        self.vmax: PU = None
        self.vmin: PU = None
        self.vrmax: PU = None
        self.vrmin: PU = None

class ExcNI(ExcitationSystemDynamics):
    """RDF class ExcNI."""

    __slots__ = ('busFedSelector', 'tr', 'ka', 'ta', 'vrmax', 'vrmin', 'kf', 'tf2', 'tf1', 'r')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcNI') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.busFedSelector: bool = None
        self.tr: Seconds = None
        self.ka: PU = None
        self.ta: Seconds = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.kf: PU = None
        self.tf2: Seconds = None
        self.tf1: Seconds = None
        self.r: PU = None

class ExcOEX3T(ExcitationSystemDynamics):
    """RDF class ExcOEX3T."""

    __slots__ = ('t1', 't2', 't3', 't4', 'ka', 't5', 't6', 'vrmax', 'vrmin', 'te', 'kf', 'tf', 'kc', 'kd', 'ke', 'e1', 'see1', 'e2', 'see2')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcOEX3T') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.t1: Seconds = None
        self.t2: Seconds = None
        self.t3: Seconds = None
        self.t4: Seconds = None
        self.ka: PU = None
        self.t5: Seconds = None
        self.t6: Seconds = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.te: Seconds = None
        self.kf: PU = None
        self.tf: Seconds = None
        self.kc: PU = None
        self.kd: PU = None
        self.ke: PU = None
        self.e1: PU = None
        self.see1: PU = None
        self.e2: PU = None
        self.see2: PU = None

class ExcPIC(ExcitationSystemDynamics):
    """RDF class ExcPIC."""

    __slots__ = ('ka', 'ta1', 'vr1', 'vr2', 'ta2', 'ta3', 'ta4', 'vrmax', 'vrmin', 'kf', 'tf1', 'tf2', 'efdmax', 'efdmin', 'ke', 'te', 'e1', 'se1', 'e2', 'se2', 'kp', 'ki', 'kc')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcPIC') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.ka: PU = None
        self.ta1: Seconds = None
        self.vr1: PU = None
        self.vr2: PU = None
        self.ta2: Seconds = None
        self.ta3: Seconds = None
        self.ta4: Seconds = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.kf: PU = None
        self.tf1: Seconds = None
        self.tf2: Seconds = None
        self.efdmax: PU = None
        self.efdmin: PU = None
        self.ke: PU = None
        self.te: Seconds = None
        self.e1: PU = None
        self.se1: PU = None
        self.e2: PU = None
        self.se2: PU = None
        self.kp: PU = None
        self.ki: PU = None
        self.kc: PU = None

class ExcREXS(ExcitationSystemDynamics):
    """RDF class ExcREXS."""

    __slots__ = ('e1', 'e2', 'fbf', 'flimf', 'kc', 'kd', 'ke', 'kefd', 'kf', 'kh', 'kii', 'kip', 'ks', 'kvi', 'kvp', 'kvphz', 'nvphz', 'se1', 'se2', 'ta', 'tb1', 'tb2', 'tc1', 'tc2', 'te', 'tf', 'tf1', 'tf2', 'tp', 'vcmax', 'vfmax', 'vfmin', 'vimax', 'vrmax', 'vrmin', 'xc')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcREXS') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.e1: PU = None
        self.e2: PU = None
        self.fbf: ExcREXSFeedbackSignalKind = None
        self.flimf: PU = None
        self.kc: PU = None
        self.kd: PU = None
        self.ke: PU = None
        self.kefd: PU = None
        self.kf: Seconds = None
        self.kh: PU = None
        self.kii: PU = None
        self.kip: PU = None
        self.ks: PU = None
        self.kvi: PU = None
        self.kvp: PU = None
        self.kvphz: PU = None
        self.nvphz: PU = None
        self.se1: PU = None
        self.se2: PU = None
        self.ta: Seconds = None
        self.tb1: Seconds = None
        self.tb2: Seconds = None
        self.tc1: Seconds = None
        self.tc2: Seconds = None
        self.te: Seconds = None
        self.tf: Seconds = None
        self.tf1: Seconds = None
        self.tf2: Seconds = None
        self.tp: Seconds = None
        self.vcmax: PU = None
        self.vfmax: PU = None
        self.vfmin: PU = None
        self.vimax: PU = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.xc: PU = None

class ExcRQB(ExcitationSystemDynamics):
    """RDF class ExcRQB."""

    __slots__ = ('ki0', 'ki1', 'te', 'tc', 'klir', 'ucmin', 'ucmax', 'lus', 'klus', 'mesu', 't4m', 'lsat', 'tf')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcRQB') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.ki0: float = None
        self.ki1: float = None
        self.te: Seconds = None
        self.tc: Seconds = None
        self.klir: float = None
        self.ucmin: PU = None
        self.ucmax: PU = None
        self.lus: PU = None
        self.klus: float = None
        self.mesu: Seconds = None
        self.t4m: Seconds = None
        self.lsat: PU = None
        self.tf: Seconds = None

class ExcSCRX(ExcitationSystemDynamics):
    """RDF class ExcSCRX."""

    __slots__ = ('tatb', 'tb', 'k', 'te', 'emin', 'emax', 'cswitch', 'rcrfd')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcSCRX') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.tatb: float = None
        self.tb: Seconds = None
        self.k: PU = None
        self.te: Seconds = None
        self.emin: PU = None
        self.emax: PU = None
        self.cswitch: bool = None
        self.rcrfd: float = None

class ExcSEXS(ExcitationSystemDynamics):
    """RDF class ExcSEXS."""

    __slots__ = ('tatb', 'tb', 'k', 'te', 'emin', 'emax', 'kc', 'tc', 'efdmin', 'efdmax')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcSEXS') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.tatb: float = None
        self.tb: Seconds = None
        self.k: PU = None
        self.te: Seconds = None
        self.emin: PU = None
        self.emax: PU = None
        self.kc: PU = None
        self.tc: Seconds = None
        self.efdmin: PU = None
        self.efdmax: PU = None

class ExcSK(ExcitationSystemDynamics):
    """RDF class ExcSK."""

    __slots__ = ('efdmax', 'efdmin', 'emax', 'emin', 'k', 'k1', 'k2', 'kc', 'kce', 'kd', 'kgob', 'kp', 'kqi', 'kqob', 'kqp', 'nq', 'qconoff', 'qz', 'remote', 'sbase', 'tc', 'te', 'ti', 'tp', 'tr', 'uimax', 'uimin', 'urmax', 'urmin', 'vtmax', 'vtmin', 'yp')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcSK') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.efdmax: PU = None
        self.efdmin: PU = None
        self.emax: PU = None
        self.emin: PU = None
        self.k: PU = None
        self.k1: PU = None
        self.k2: PU = None
        self.kc: PU = None
        self.kce: PU = None
        self.kd: PU = None
        self.kgob: PU = None
        self.kp: PU = None
        self.kqi: PU = None
        self.kqob: PU = None
        self.kqp: PU = None
        self.nq: PU = None
        self.qconoff: bool = None
        self.qz: PU = None
        self.remote: bool = None
        self.sbase: ApparentPower = None
        self.tc: Seconds = None
        self.te: Seconds = None
        self.ti: Seconds = None
        self.tp: Seconds = None
        self.tr: Seconds = None
        self.uimax: PU = None
        self.uimin: PU = None
        self.urmax: PU = None
        self.urmin: PU = None
        self.vtmax: PU = None
        self.vtmin: PU = None
        self.yp: PU = None

class ExcST1A(ExcitationSystemDynamics):
    """RDF class ExcST1A."""

    __slots__ = ('vimax', 'vimin', 'tc', 'tb', 'ka', 'ta', 'vrmax', 'vrmin', 'kc', 'kf', 'tf', 'tc1', 'tb1', 'vamax', 'vamin', 'ilr', 'klr', 'xe')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcST1A') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.vimax: PU = None
        self.vimin: PU = None
        self.tc: Seconds = None
        self.tb: Seconds = None
        self.ka: PU = None
        self.ta: Seconds = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.kc: PU = None
        self.kf: PU = None
        self.tf: Seconds = None
        self.tc1: Seconds = None
        self.tb1: Seconds = None
        self.vamax: PU = None
        self.vamin: PU = None
        self.ilr: PU = None
        self.klr: PU = None
        self.xe: PU = None

class ExcST2A(ExcitationSystemDynamics):
    """RDF class ExcST2A."""

    __slots__ = ('ka', 'ta', 'vrmax', 'vrmin', 'ke', 'te', 'kf', 'tf', 'kp', 'ki', 'kc', 'efdmax', 'uelin', 'tb', 'tc')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcST2A') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.ka: PU = None
        self.ta: Seconds = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.ke: PU = None
        self.te: Seconds = None
        self.kf: PU = None
        self.tf: Seconds = None
        self.kp: PU = None
        self.ki: PU = None
        self.kc: PU = None
        self.efdmax: PU = None
        self.uelin: bool = None
        self.tb: Seconds = None
        self.tc: Seconds = None

class ExcST3A(ExcitationSystemDynamics):
    """RDF class ExcST3A."""

    __slots__ = ('vimax', 'vimin', 'kj', 'tb', 'tc', 'efdmax', 'km', 'tm', 'vrmax', 'vrmin', 'kg', 'kp', 'thetap', 'ki', 'kc', 'xl', 'vbmax', 'vgmax', 'ks', 'ks1')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcST3A') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.vimax: PU = None
        self.vimin: PU = None
        self.kj: PU = None
        self.tb: Seconds = None
        self.tc: Seconds = None
        self.efdmax: PU = None
        self.km: PU = None
        self.tm: Seconds = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.kg: PU = None
        self.kp: PU = None
        self.thetap: AngleDegrees = None
        self.ki: PU = None
        self.kc: PU = None
        self.xl: PU = None
        self.vbmax: PU = None
        self.vgmax: PU = None
        self.ks: PU = None
        self.ks1: PU = None

class ExcST4B(ExcitationSystemDynamics):
    """RDF class ExcST4B."""

    __slots__ = ('kpr', 'kir', 'ta', 'vrmax', 'vrmin', 'kpm', 'kim', 'vmmax', 'vmmin', 'kg', 'kp', 'thetap', 'ki', 'kc', 'xl', 'vbmax', 'vgmax', 'uel', 'lvgate')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcST4B') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.kpr: PU = None
        self.kir: PU = None
        self.ta: Seconds = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.kpm: PU = None
        self.kim: PU = None
        self.vmmax: PU = None
        self.vmmin: PU = None
        self.kg: PU = None
        self.kp: PU = None
        self.thetap: AngleDegrees = None
        self.ki: PU = None
        self.kc: PU = None
        self.xl: PU = None
        self.vbmax: PU = None
        self.vgmax: PU = None
        self.uel: bool = None
        self.lvgate: bool = None

class ExcST6B(ExcitationSystemDynamics):
    """RDF class ExcST6B."""

    __slots__ = ('ilr', 'k1', 'kcl', 'kff', 'kg', 'kia', 'klr', 'km', 'kpa', 'kvd', 'oelin', 'tg', 'ts', 'tvd', 'vamax', 'vamin', 'vilim', 'vimax', 'vimin', 'vmult', 'vrmax', 'vrmin', 'xc')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcST6B') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.ilr: PU = None
        self.k1: bool = None
        self.kcl: PU = None
        self.kff: PU = None
        self.kg: PU = None
        self.kia: PU = None
        self.klr: PU = None
        self.km: PU = None
        self.kpa: PU = None
        self.kvd: PU = None
        self.oelin: ExcST6BOELselectorKind = None
        self.tg: Seconds = None
        self.ts: Seconds = None
        self.tvd: Seconds = None
        self.vamax: PU = None
        self.vamin: PU = None
        self.vilim: bool = None
        self.vimax: PU = None
        self.vimin: PU = None
        self.vmult: bool = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.xc: PU = None

class ExcST7B(ExcitationSystemDynamics):
    """RDF class ExcST7B."""

    __slots__ = ('kh', 'kia', 'kl', 'kpa', 'oelin', 'tb', 'tc', 'tf', 'tg', 'tia', 'ts', 'uelin', 'vmax', 'vmin', 'vrmax', 'vrmin')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcST7B') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.kh: PU = None
        self.kia: PU = None
        self.kl: PU = None
        self.kpa: PU = None
        self.oelin: ExcST7BOELselectorKind = None
        self.tb: Seconds = None
        self.tc: Seconds = None
        self.tf: Seconds = None
        self.tg: Seconds = None
        self.tia: Seconds = None
        self.ts: Seconds = None
        self.uelin: ExcST7BUELselectorKind = None
        self.vmax: PU = None
        self.vmin: PU = None
        self.vrmax: PU = None
        self.vrmin: PU = None

class ExcitationSystemUserDefined(ExcitationSystemDynamics):
    """RDF class ExcitationSystemUserDefined."""

    __slots__ = ('proprietary', 'ProprietaryParameterDynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'ExcitationSystemUserDefined') -> None:
        """Initialize an RDF-defined CGMES object."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.proprietary: bool = None
        self.ProprietaryParameterDynamics: List[ProprietaryParameterDynamics] = list()

class GovCT1(TurbineGovernorDynamics):
    """RDF class GovCT1."""

    __slots__ = ('mwbase', 'r', 'rselect', 'tpelec', 'maxerr', 'minerr', 'kpgov', 'kigov', 'kdgov', 'tdgov', 'vmax', 'vmin', 'tact', 'kturb', 'wfnl', 'tb', 'tc', 'wfspd', 'teng', 'tfload', 'kpload', 'kiload', 'ldref', 'dm', 'ropen', 'rclose', 'kimw', 'aset', 'ka', 'ta', 'db', 'tsa', 'tsb', 'rup', 'rdown')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovCT1') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.mwbase: ActivePower = None
        self.r: PU = None
        self.rselect: DroopSignalFeedbackKind = None
        self.tpelec: Seconds = None
        self.maxerr: PU = None
        self.minerr: PU = None
        self.kpgov: PU = None
        self.kigov: PU = None
        self.kdgov: PU = None
        self.tdgov: Seconds = None
        self.vmax: PU = None
        self.vmin: PU = None
        self.tact: Seconds = None
        self.kturb: PU = None
        self.wfnl: PU = None
        self.tb: Seconds = None
        self.tc: Seconds = None
        self.wfspd: bool = None
        self.teng: Seconds = None
        self.tfload: Seconds = None
        self.kpload: PU = None
        self.kiload: PU = None
        self.ldref: PU = None
        self.dm: PU = None
        self.ropen: float = None
        self.rclose: float = None
        self.kimw: PU = None
        self.aset: float = None
        self.ka: PU = None
        self.ta: Seconds = None
        self.db: PU = None
        self.tsa: Seconds = None
        self.tsb: Seconds = None
        self.rup: PU = None
        self.rdown: PU = None

class GovCT2(TurbineGovernorDynamics):
    """RDF class GovCT2."""

    __slots__ = ('mwbase', 'r', 'rselect', 'tpelec', 'maxerr', 'minerr', 'kpgov', 'kigov', 'kdgov', 'tdgov', 'vmax', 'vmin', 'tact', 'kturb', 'wfnl', 'tb', 'tc', 'wfspd', 'teng', 'tfload', 'kpload', 'kiload', 'ldref', 'dm', 'ropen', 'rclose', 'kimw', 'aset', 'ka', 'ta', 'db', 'tsa', 'tsb', 'rup', 'rdown', 'prate', 'flim1', 'plim1', 'flim2', 'plim2', 'flim3', 'plim3', 'flim4', 'plim4', 'flim5', 'plim5', 'flim6', 'plim6', 'flim7', 'plim7', 'flim8', 'plim8', 'flim9', 'plim9', 'flim10', 'plim10')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovCT2') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.mwbase: ActivePower = None
        self.r: PU = None
        self.rselect: DroopSignalFeedbackKind = None
        self.tpelec: Seconds = None
        self.maxerr: PU = None
        self.minerr: PU = None
        self.kpgov: PU = None
        self.kigov: PU = None
        self.kdgov: PU = None
        self.tdgov: Seconds = None
        self.vmax: PU = None
        self.vmin: PU = None
        self.tact: Seconds = None
        self.kturb: PU = None
        self.wfnl: PU = None
        self.tb: Seconds = None
        self.tc: Seconds = None
        self.wfspd: bool = None
        self.teng: Seconds = None
        self.tfload: Seconds = None
        self.kpload: PU = None
        self.kiload: PU = None
        self.ldref: PU = None
        self.dm: PU = None
        self.ropen: float = None
        self.rclose: float = None
        self.kimw: PU = None
        self.aset: float = None
        self.ka: PU = None
        self.ta: Seconds = None
        self.db: PU = None
        self.tsa: Seconds = None
        self.tsb: Seconds = None
        self.rup: PU = None
        self.rdown: PU = None
        self.prate: PU = None
        self.flim1: Frequency = None
        self.plim1: PU = None
        self.flim2: Frequency = None
        self.plim2: PU = None
        self.flim3: Frequency = None
        self.plim3: PU = None
        self.flim4: Frequency = None
        self.plim4: PU = None
        self.flim5: Frequency = None
        self.plim5: PU = None
        self.flim6: Frequency = None
        self.plim6: PU = None
        self.flim7: Frequency = None
        self.plim7: PU = None
        self.flim8: Frequency = None
        self.plim8: PU = None
        self.flim9: Frequency = None
        self.plim9: PU = None
        self.flim10: Frequency = None
        self.plim10: PU = None

class GovGAST(TurbineGovernorDynamics):
    """RDF class GovGAST."""

    __slots__ = ('mwbase', 'r', 't1', 't2', 't3', 'at', 'kt', 'vmax', 'vmin', 'dturb')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovGAST') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.mwbase: ActivePower = None
        self.r: PU = None
        self.t1: Seconds = None
        self.t2: Seconds = None
        self.t3: Seconds = None
        self.at: PU = None
        self.kt: PU = None
        self.vmax: PU = None
        self.vmin: PU = None
        self.dturb: PU = None

class GovGAST1(TurbineGovernorDynamics):
    """RDF class GovGAST1."""

    __slots__ = ('mwbase', 'r', 't1', 't2', 't3', 'lmax', 'kt', 'vmax', 'vmin', 'fidle', 'rmax', 'loadinc', 'tltr', 'ltrate', 'a', 'b', 'db1', 'eps', 'db2', 'gv1', 'pgv1', 'gv2', 'pgv2', 'gv3', 'pgv3', 'gv4', 'pgv4', 'gv5', 'pgv5', 'gv6', 'pgv6', 'ka', 't4', 't5')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovGAST1') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.mwbase: ActivePower = None
        self.r: PU = None
        self.t1: Seconds = None
        self.t2: Seconds = None
        self.t3: Seconds = None
        self.lmax: PU = None
        self.kt: PU = None
        self.vmax: PU = None
        self.vmin: PU = None
        self.fidle: PU = None
        self.rmax: float = None
        self.loadinc: PU = None
        self.tltr: Seconds = None
        self.ltrate: float = None
        self.a: float = None
        self.b: float = None
        self.db1: Frequency = None
        self.eps: Frequency = None
        self.db2: ActivePower = None
        self.gv1: PU = None
        self.pgv1: PU = None
        self.gv2: PU = None
        self.pgv2: PU = None
        self.gv3: PU = None
        self.pgv3: PU = None
        self.gv4: PU = None
        self.pgv4: PU = None
        self.gv5: PU = None
        self.pgv5: PU = None
        self.gv6: PU = None
        self.pgv6: PU = None
        self.ka: PU = None
        self.t4: Seconds = None
        self.t5: Seconds = None

class GovGAST2(TurbineGovernorDynamics):
    """RDF class GovGAST2."""

    __slots__ = ('mwbase', 'w', 'x', 'y', 'z', 'etd', 'tcd', 'trate', 't', 'tmax', 'tmin', 'ecr', 'k3', 'a', 'b', 'c', 'tf', 'kf', 'k5', 'k4', 't3', 't4', 'tt', 't5', 'af1', 'bf1', 'af2', 'bf2', 'cf2', 'tr', 'k6', 'tc')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovGAST2') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.mwbase: ActivePower = None
        self.w: PU = None
        self.x: Seconds = None
        self.y: Seconds = None
        self.z: int = None
        self.etd: Seconds = None
        self.tcd: Seconds = None
        self.trate: ActivePower = None
        self.t: Seconds = None
        self.tmax: PU = None
        self.tmin: PU = None
        self.ecr: Seconds = None
        self.k3: PU = None
        self.a: float = None
        self.b: float = None
        self.c: float = None
        self.tf: Seconds = None
        self.kf: PU = None
        self.k5: PU = None
        self.k4: PU = None
        self.t3: Seconds = None
        self.t4: Seconds = None
        self.tt: Seconds = None
        self.t5: Seconds = None
        self.af1: PU = None
        self.bf1: PU = None
        self.af2: PU = None
        self.bf2: PU = None
        self.cf2: PU = None
        self.tr: Temperature = None
        self.k6: PU = None
        self.tc: Temperature = None

class GovGAST3(TurbineGovernorDynamics):
    """RDF class GovGAST3."""

    __slots__ = ('bp', 'tg', 'rcmx', 'rcmn', 'ky', 'ty', 'tac', 'kac', 'tc', 'bca', 'kca', 'dtc', 'ka', 'tsi', 'ksi', 'ttc', 'tfen', 'td', 'tt', 'mxef', 'mnef')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovGAST3') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.bp: PU = None
        self.tg: Seconds = None
        self.rcmx: PU = None
        self.rcmn: PU = None
        self.ky: float = None
        self.ty: Seconds = None
        self.tac: Seconds = None
        self.kac: float = None
        self.tc: Seconds = None
        self.bca: float = None
        self.kca: float = None
        self.dtc: Temperature = None
        self.ka: PU = None
        self.tsi: Seconds = None
        self.ksi: float = None
        self.ttc: Seconds = None
        self.tfen: Temperature = None
        self.td: Seconds = None
        self.tt: Temperature = None
        self.mxef: PU = None
        self.mnef: PU = None

class GovGAST4(TurbineGovernorDynamics):
    """RDF class GovGAST4."""

    __slots__ = ('bp', 'tv', 'ta', 'tc', 'tcm', 'ktm', 'tm', 'rymx', 'rymn', 'mxef', 'mnef')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovGAST4') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.bp: PU = None
        self.tv: Seconds = None
        self.ta: Seconds = None
        self.tc: Seconds = None
        self.tcm: Seconds = None
        self.ktm: PU = None
        self.tm: Seconds = None
        self.rymx: PU = None
        self.rymn: PU = None
        self.mxef: PU = None
        self.mnef: PU = None

class GovGASTWD(TurbineGovernorDynamics):
    """RDF class GovGASTWD."""

    __slots__ = ('mwbase', 'kdroop', 'kp', 'ki', 'kd', 'etd', 'tcd', 'trate', 't', 'tmax', 'tmin', 'ecr', 'k3', 'a', 'b', 'c', 'tf', 'kf', 'k5', 'k4', 't3', 't4', 'tt', 't5', 'af1', 'bf1', 'af2', 'bf2', 'cf2', 'tr', 'k6', 'tc', 'td')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovGASTWD') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.mwbase: ActivePower = None
        self.kdroop: PU = None
        self.kp: PU = None
        self.ki: PU = None
        self.kd: PU = None
        self.etd: Seconds = None
        self.tcd: Seconds = None
        self.trate: ActivePower = None
        self.t: Seconds = None
        self.tmax: PU = None
        self.tmin: PU = None
        self.ecr: Seconds = None
        self.k3: PU = None
        self.a: float = None
        self.b: float = None
        self.c: float = None
        self.tf: Seconds = None
        self.kf: PU = None
        self.k5: PU = None
        self.k4: PU = None
        self.t3: Seconds = None
        self.t4: Seconds = None
        self.tt: Seconds = None
        self.t5: Seconds = None
        self.af1: PU = None
        self.bf1: PU = None
        self.af2: PU = None
        self.bf2: PU = None
        self.cf2: PU = None
        self.tr: Temperature = None
        self.k6: PU = None
        self.tc: Temperature = None
        self.td: Seconds = None

class GovHydro1(TurbineGovernorDynamics):
    """RDF class GovHydro1."""

    __slots__ = ('mwbase', 'rperm', 'rtemp', 'tr', 'tf', 'tg', 'velm', 'gmax', 'gmin', 'tw', 'at', 'dturb', 'qnl', 'hdam')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovHydro1') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.mwbase: ActivePower = None
        self.rperm: PU = None
        self.rtemp: PU = None
        self.tr: Seconds = None
        self.tf: Seconds = None
        self.tg: Seconds = None
        self.velm: float = None
        self.gmax: PU = None
        self.gmin: PU = None
        self.tw: Seconds = None
        self.at: PU = None
        self.dturb: PU = None
        self.qnl: PU = None
        self.hdam: PU = None

class GovHydro2(TurbineGovernorDynamics):
    """RDF class GovHydro2."""

    __slots__ = ('mwbase', 'tg', 'tp', 'uo', 'uc', 'pmax', 'pmin', 'rperm', 'rtemp', 'tr', 'tw', 'kturb', 'aturb', 'bturb', 'db1', 'eps', 'db2', 'gv1', 'pgv1', 'gv2', 'pgv2', 'gv3', 'pgv3', 'gv4', 'pgv4', 'gv5', 'pgv5', 'gv6', 'pgv6')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovHydro2') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.mwbase: ActivePower = None
        self.tg: Seconds = None
        self.tp: Seconds = None
        self.uo: float = None
        self.uc: float = None
        self.pmax: PU = None
        self.pmin: PU = None
        self.rperm: PU = None
        self.rtemp: PU = None
        self.tr: Seconds = None
        self.tw: Seconds = None
        self.kturb: PU = None
        self.aturb: PU = None
        self.bturb: PU = None
        self.db1: Frequency = None
        self.eps: Frequency = None
        self.db2: ActivePower = None
        self.gv1: PU = None
        self.pgv1: PU = None
        self.gv2: PU = None
        self.pgv2: PU = None
        self.gv3: PU = None
        self.pgv3: PU = None
        self.gv4: PU = None
        self.pgv4: PU = None
        self.gv5: PU = None
        self.pgv5: PU = None
        self.gv6: PU = None
        self.pgv6: PU = None

class GovHydro3(TurbineGovernorDynamics):
    """RDF class GovHydro3."""

    __slots__ = ('mwbase', 'pmax', 'pmin', 'governorControl', 'rgate', 'relec', 'td', 'tf', 'tp', 'velop', 'velcl', 'k1', 'k2', 'ki', 'kg', 'tt', 'db1', 'eps', 'db2', 'tw', 'at', 'dturb', 'qnl', 'h0', 'gv1', 'pgv1', 'gv2', 'pgv2', 'gv3', 'pgv3', 'gv4', 'pgv4', 'gv5', 'pgv5', 'gv6', 'pgv6')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovHydro3') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.mwbase: ActivePower = None
        self.pmax: PU = None
        self.pmin: PU = None
        self.governorControl: bool = None
        self.rgate: PU = None
        self.relec: PU = None
        self.td: Seconds = None
        self.tf: Seconds = None
        self.tp: Seconds = None
        self.velop: float = None
        self.velcl: float = None
        self.k1: PU = None
        self.k2: PU = None
        self.ki: PU = None
        self.kg: PU = None
        self.tt: Seconds = None
        self.db1: Frequency = None
        self.eps: Frequency = None
        self.db2: ActivePower = None
        self.tw: Seconds = None
        self.at: PU = None
        self.dturb: PU = None
        self.qnl: PU = None
        self.h0: PU = None
        self.gv1: PU = None
        self.pgv1: PU = None
        self.gv2: PU = None
        self.pgv2: PU = None
        self.gv3: PU = None
        self.pgv3: PU = None
        self.gv4: PU = None
        self.pgv4: PU = None
        self.gv5: PU = None
        self.pgv5: PU = None
        self.gv6: PU = None
        self.pgv6: PU = None

class GovHydro4(TurbineGovernorDynamics):
    """RDF class GovHydro4."""

    __slots__ = ('mwbase', 'tg', 'tp', 'uo', 'uc', 'gmax', 'gmin', 'rperm', 'rtemp', 'tr', 'tw', 'at', 'dturb', 'hdam', 'qnl', 'db1', 'eps', 'db2', 'gv0', 'pgv0', 'gv1', 'pgv1', 'gv2', 'pgv2', 'gv3', 'pgv3', 'gv4', 'pgv4', 'gv5', 'pgv5', 'bgv0', 'bgv1', 'bgv2', 'bgv3', 'bgv4', 'bgv5', 'bmax', 'tblade', 'model')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovHydro4') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.mwbase: ActivePower = None
        self.tg: Seconds = None
        self.tp: Seconds = None
        self.uo: float = None
        self.uc: float = None
        self.gmax: PU = None
        self.gmin: PU = None
        self.rperm: Seconds = None
        self.rtemp: Seconds = None
        self.tr: Seconds = None
        self.tw: Seconds = None
        self.at: PU = None
        self.dturb: PU = None
        self.hdam: PU = None
        self.qnl: PU = None
        self.db1: Frequency = None
        self.eps: Frequency = None
        self.db2: ActivePower = None
        self.gv0: PU = None
        self.pgv0: PU = None
        self.gv1: PU = None
        self.pgv1: PU = None
        self.gv2: PU = None
        self.pgv2: PU = None
        self.gv3: PU = None
        self.pgv3: PU = None
        self.gv4: PU = None
        self.pgv4: PU = None
        self.gv5: PU = None
        self.pgv5: PU = None
        self.bgv0: PU = None
        self.bgv1: PU = None
        self.bgv2: PU = None
        self.bgv3: PU = None
        self.bgv4: PU = None
        self.bgv5: PU = None
        self.bmax: float = None
        self.tblade: Seconds = None
        self.model: GovHydro4ModelKind = None

class GovHydroDD(TurbineGovernorDynamics):
    """RDF class GovHydroDD."""

    __slots__ = ('mwbase', 'pmax', 'pmin', 'r', 'td', 'tf', 'tp', 'velop', 'velcl', 'k1', 'k2', 'ki', 'kg', 'tturb', 'aturb', 'bturb', 'tt', 'db1', 'eps', 'db2', 'gv1', 'pgv1', 'gv2', 'pgv2', 'gv3', 'pgv3', 'gv4', 'pgv4', 'gv5', 'pgv5', 'gv6', 'pgv6', 'gmax', 'gmin', 'inputSignal')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovHydroDD') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.mwbase: ActivePower = None
        self.pmax: PU = None
        self.pmin: PU = None
        self.r: PU = None
        self.td: Seconds = None
        self.tf: Seconds = None
        self.tp: Seconds = None
        self.velop: float = None
        self.velcl: float = None
        self.k1: PU = None
        self.k2: PU = None
        self.ki: PU = None
        self.kg: PU = None
        self.tturb: Seconds = None
        self.aturb: PU = None
        self.bturb: PU = None
        self.tt: Seconds = None
        self.db1: Frequency = None
        self.eps: Frequency = None
        self.db2: ActivePower = None
        self.gv1: PU = None
        self.pgv1: PU = None
        self.gv2: PU = None
        self.pgv2: PU = None
        self.gv3: PU = None
        self.pgv3: PU = None
        self.gv4: PU = None
        self.pgv4: PU = None
        self.gv5: PU = None
        self.pgv5: PU = None
        self.gv6: PU = None
        self.pgv6: PU = None
        self.gmax: PU = None
        self.gmin: PU = None
        self.inputSignal: bool = None

class GovHydroFrancis(TurbineGovernorDynamics):
    """RDF class GovHydroFrancis."""

    __slots__ = ('am', 'av0', 'av1', 'bp', 'db1', 'etamax', 'governorControl', 'h1', 'h2', 'hn', 'kc', 'kg', 'kt', 'qc0', 'qn', 'ta', 'td', 'ts', 'twnc', 'twng', 'tx', 'va', 'valvmax', 'valvmin', 'vc', 'waterTunnelSurgeChamberSimulation', 'zsfc')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovHydroFrancis') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.am: PU = None
        self.av0: Area = None
        self.av1: Area = None
        self.bp: PU = None
        self.db1: Frequency = None
        self.etamax: PU = None
        self.governorControl: FrancisGovernorControlKind = None
        self.h1: Length = None
        self.h2: Length = None
        self.hn: Length = None
        self.kc: PU = None
        self.kg: PU = None
        self.kt: PU = None
        self.qc0: PU = None
        self.qn: VolumeFlowRate = None
        self.ta: Seconds = None
        self.td: Seconds = None
        self.ts: Seconds = None
        self.twnc: Seconds = None
        self.twng: Seconds = None
        self.tx: Seconds = None
        self.va: float = None
        self.valvmax: PU = None
        self.valvmin: PU = None
        self.vc: float = None
        self.waterTunnelSurgeChamberSimulation: bool = None
        self.zsfc: Length = None

class GovHydroIEEE0(TurbineGovernorDynamics):
    """RDF class GovHydroIEEE0."""

    __slots__ = ('mwbase', 'k', 't1', 't2', 't3', 't4', 'pmax', 'pmin')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovHydroIEEE0') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.mwbase: ActivePower = None
        self.k: PU = None
        self.t1: Seconds = None
        self.t2: Seconds = None
        self.t3: Seconds = None
        self.t4: Seconds = None
        self.pmax: PU = None
        self.pmin: PU = None

class GovHydroIEEE2(TurbineGovernorDynamics):
    """RDF class GovHydroIEEE2."""

    __slots__ = ('mwbase', 'tg', 'tp', 'uo', 'uc', 'pmax', 'pmin', 'rperm', 'rtemp', 'tr', 'tw', 'kturb', 'aturb', 'bturb', 'gv1', 'pgv1', 'gv2', 'pgv2', 'gv3', 'pgv3', 'gv4', 'pgv4', 'gv5', 'pgv5', 'gv6', 'pgv6')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovHydroIEEE2') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.mwbase: ActivePower = None
        self.tg: Seconds = None
        self.tp: Seconds = None
        self.uo: float = None
        self.uc: float = None
        self.pmax: PU = None
        self.pmin: PU = None
        self.rperm: PU = None
        self.rtemp: PU = None
        self.tr: Seconds = None
        self.tw: Seconds = None
        self.kturb: PU = None
        self.aturb: PU = None
        self.bturb: PU = None
        self.gv1: PU = None
        self.pgv1: PU = None
        self.gv2: PU = None
        self.pgv2: PU = None
        self.gv3: PU = None
        self.pgv3: PU = None
        self.gv4: PU = None
        self.pgv4: PU = None
        self.gv5: PU = None
        self.pgv5: PU = None
        self.gv6: PU = None
        self.pgv6: PU = None

class GovHydroPID(TurbineGovernorDynamics):
    """RDF class GovHydroPID."""

    __slots__ = ('mwbase', 'pmax', 'pmin', 'r', 'td', 'tf', 'tp', 'velop', 'velcl', 'kd', 'kp', 'ki', 'kg', 'tturb', 'aturb', 'bturb', 'tt', 'db1', 'inputSignal', 'eps', 'db2', 'gv1', 'pgv1', 'gv2', 'pgv2', 'gv3', 'pgv3', 'gv4', 'pgv4', 'gv5', 'pgv5', 'gv6', 'pgv6')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovHydroPID') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.mwbase: ActivePower = None
        self.pmax: PU = None
        self.pmin: PU = None
        self.r: PU = None
        self.td: Seconds = None
        self.tf: Seconds = None
        self.tp: Seconds = None
        self.velop: float = None
        self.velcl: float = None
        self.kd: PU = None
        self.kp: PU = None
        self.ki: PU = None
        self.kg: PU = None
        self.tturb: Seconds = None
        self.aturb: PU = None
        self.bturb: PU = None
        self.tt: Seconds = None
        self.db1: Frequency = None
        self.inputSignal: bool = None
        self.eps: Frequency = None
        self.db2: ActivePower = None
        self.gv1: PU = None
        self.pgv1: PU = None
        self.gv2: PU = None
        self.pgv2: PU = None
        self.gv3: PU = None
        self.pgv3: PU = None
        self.gv4: PU = None
        self.pgv4: PU = None
        self.gv5: PU = None
        self.pgv5: PU = None
        self.gv6: PU = None
        self.pgv6: PU = None

class GovHydroPID2(TurbineGovernorDynamics):
    """RDF class GovHydroPID2."""

    __slots__ = ('mwbase', 'treg', 'rperm', 'kp', 'ki', 'kd', 'ta', 'tb', 'velmax', 'velmin', 'gmax', 'gmin', 'tw', 'd', 'g0', 'g1', 'p1', 'g2', 'p2', 'p3', 'atw', 'feedbackSignal')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovHydroPID2') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.mwbase: ActivePower = None
        self.treg: Seconds = None
        self.rperm: PU = None
        self.kp: PU = None
        self.ki: float = None
        self.kd: PU = None
        self.ta: Seconds = None
        self.tb: Seconds = None
        self.velmax: float = None
        self.velmin: float = None
        self.gmax: PU = None
        self.gmin: PU = None
        self.tw: Seconds = None
        self.d: PU = None
        self.g0: PU = None
        self.g1: PU = None
        self.p1: PU = None
        self.g2: PU = None
        self.p2: PU = None
        self.p3: PU = None
        self.atw: PU = None
        self.feedbackSignal: bool = None

class GovHydroPelton(TurbineGovernorDynamics):
    """RDF class GovHydroPelton."""

    __slots__ = ('av0', 'av1', 'bp', 'db1', 'db2', 'h1', 'h2', 'hn', 'kc', 'kg', 'qc0', 'qn', 'simplifiedPelton', 'staticCompensating', 'ta', 'ts', 'tv', 'twnc', 'twng', 'tx', 'va', 'valvmax', 'valvmin', 'vav', 'vc', 'vcv', 'waterTunnelSurgeChamberSimulation', 'zsfc')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovHydroPelton') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.av0: Area = None
        self.av1: Area = None
        self.bp: PU = None
        self.db1: Frequency = None
        self.db2: Frequency = None
        self.h1: Length = None
        self.h2: Length = None
        self.hn: Length = None
        self.kc: PU = None
        self.kg: PU = None
        self.qc0: PU = None
        self.qn: VolumeFlowRate = None
        self.simplifiedPelton: bool = None
        self.staticCompensating: bool = None
        self.ta: Seconds = None
        self.ts: Seconds = None
        self.tv: Seconds = None
        self.twnc: Seconds = None
        self.twng: Seconds = None
        self.tx: Seconds = None
        self.va: float = None
        self.valvmax: PU = None
        self.valvmin: PU = None
        self.vav: PU = None
        self.vc: float = None
        self.vcv: PU = None
        self.waterTunnelSurgeChamberSimulation: bool = None
        self.zsfc: Length = None

class GovHydroR(TurbineGovernorDynamics):
    """RDF class GovHydroR."""

    __slots__ = ('mwbase', 'pmax', 'pmin', 'r', 'td', 't1', 't2', 't3', 't4', 't5', 't6', 't7', 't8', 'tp', 'velop', 'velcl', 'ki', 'kg', 'gmax', 'gmin', 'tt', 'inputSignal', 'db1', 'eps', 'db2', 'tw', 'at', 'dturb', 'qnl', 'h0', 'gv1', 'pgv1', 'gv2', 'pgv2', 'gv3', 'pgv3', 'gv4', 'pgv4', 'gv5', 'pgv5', 'gv6', 'pgv6')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovHydroR') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.mwbase: ActivePower = None
        self.pmax: PU = None
        self.pmin: PU = None
        self.r: PU = None
        self.td: Seconds = None
        self.t1: Seconds = None
        self.t2: Seconds = None
        self.t3: Seconds = None
        self.t4: Seconds = None
        self.t5: Seconds = None
        self.t6: Seconds = None
        self.t7: Seconds = None
        self.t8: Seconds = None
        self.tp: Seconds = None
        self.velop: float = None
        self.velcl: float = None
        self.ki: PU = None
        self.kg: PU = None
        self.gmax: PU = None
        self.gmin: PU = None
        self.tt: Seconds = None
        self.inputSignal: bool = None
        self.db1: Frequency = None
        self.eps: Frequency = None
        self.db2: ActivePower = None
        self.tw: Seconds = None
        self.at: PU = None
        self.dturb: PU = None
        self.qnl: PU = None
        self.h0: PU = None
        self.gv1: PU = None
        self.pgv1: PU = None
        self.gv2: PU = None
        self.pgv2: PU = None
        self.gv3: PU = None
        self.pgv3: PU = None
        self.gv4: PU = None
        self.pgv4: PU = None
        self.gv5: PU = None
        self.pgv5: PU = None
        self.gv6: PU = None
        self.pgv6: PU = None

class GovHydroWEH(TurbineGovernorDynamics):
    """RDF class GovHydroWEH."""

    __slots__ = ('mwbase', 'rpg', 'rpp', 'tpe', 'kp', 'ki', 'kd', 'td', 'tp', 'tdv', 'tg', 'gtmxop', 'gtmxcl', 'gmax', 'gmin', 'dturb', 'tw', 'db', 'dpv', 'dicn', 'feedbackSignal', 'gv1', 'gv2', 'gv3', 'gv4', 'gv5', 'fl1', 'fl2', 'fl3', 'fl4', 'fl5', 'fp1', 'fp2', 'fp3', 'fp4', 'fp5', 'fp6', 'fp7', 'fp8', 'fp9', 'fp10', 'pmss1', 'pmss2', 'pmss3', 'pmss4', 'pmss5', 'pmss6', 'pmss7', 'pmss8', 'pmss9', 'pmss10')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovHydroWEH') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.mwbase: ActivePower = None
        self.rpg: float = None
        self.rpp: float = None
        self.tpe: Seconds = None
        self.kp: PU = None
        self.ki: PU = None
        self.kd: PU = None
        self.td: Seconds = None
        self.tp: Seconds = None
        self.tdv: Seconds = None
        self.tg: Seconds = None
        self.gtmxop: PU = None
        self.gtmxcl: PU = None
        self.gmax: PU = None
        self.gmin: PU = None
        self.dturb: PU = None
        self.tw: Seconds = None
        self.db: PU = None
        self.dpv: PU = None
        self.dicn: PU = None
        self.feedbackSignal: bool = None
        self.gv1: PU = None
        self.gv2: PU = None
        self.gv3: PU = None
        self.gv4: PU = None
        self.gv5: PU = None
        self.fl1: PU = None
        self.fl2: PU = None
        self.fl3: PU = None
        self.fl4: PU = None
        self.fl5: PU = None
        self.fp1: PU = None
        self.fp2: PU = None
        self.fp3: PU = None
        self.fp4: PU = None
        self.fp5: PU = None
        self.fp6: PU = None
        self.fp7: PU = None
        self.fp8: PU = None
        self.fp9: PU = None
        self.fp10: PU = None
        self.pmss1: PU = None
        self.pmss2: PU = None
        self.pmss3: PU = None
        self.pmss4: PU = None
        self.pmss5: PU = None
        self.pmss6: PU = None
        self.pmss7: PU = None
        self.pmss8: PU = None
        self.pmss9: PU = None
        self.pmss10: PU = None

class GovHydroWPID(TurbineGovernorDynamics):
    """RDF class GovHydroWPID."""

    __slots__ = ('mwbase', 'treg', 'reg', 'kp', 'ki', 'kd', 'ta', 'tb', 'velmax', 'velmin', 'gatmax', 'gatmin', 'tw', 'pmax', 'pmin', 'd', 'gv3', 'gv1', 'pgv1', 'gv2', 'pgv2', 'pgv3')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovHydroWPID') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.mwbase: ActivePower = None
        self.treg: Seconds = None
        self.reg: PU = None
        self.kp: PU = None
        self.ki: PU = None
        self.kd: PU = None
        self.ta: Seconds = None
        self.tb: Seconds = None
        self.velmax: PU = None
        self.velmin: PU = None
        self.gatmax: PU = None
        self.gatmin: PU = None
        self.tw: Seconds = None
        self.pmax: PU = None
        self.pmin: PU = None
        self.d: PU = None
        self.gv3: PU = None
        self.gv1: PU = None
        self.pgv1: PU = None
        self.gv2: PU = None
        self.pgv2: PU = None
        self.pgv3: PU = None

class GovSteam0(TurbineGovernorDynamics):
    """RDF class GovSteam0."""

    __slots__ = ('mwbase', 'r', 't1', 'vmax', 'vmin', 't2', 't3', 'dt')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovSteam0') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.mwbase: ActivePower = None
        self.r: PU = None
        self.t1: Seconds = None
        self.vmax: PU = None
        self.vmin: PU = None
        self.t2: Seconds = None
        self.t3: Seconds = None
        self.dt: PU = None

class GovSteam1(TurbineGovernorDynamics):
    """RDF class GovSteam1."""

    __slots__ = ('mwbase', 'k', 't1', 't2', 't3', 'uo', 'uc', 'pmax', 'pmin', 't4', 'k1', 'k2', 't5', 'k3', 'k4', 't6', 'k5', 'k6', 't7', 'k7', 'k8', 'db1', 'eps', 'sdb1', 'sdb2', 'db2', 'valve', 'gv1', 'pgv1', 'gv2', 'pgv2', 'gv3', 'pgv3', 'gv4', 'pgv4', 'gv5', 'pgv5', 'gv6', 'pgv6')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovSteam1') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.mwbase: ActivePower = None
        self.k: PU = None
        self.t1: Seconds = None
        self.t2: Seconds = None
        self.t3: Seconds = None
        self.uo: float = None
        self.uc: float = None
        self.pmax: PU = None
        self.pmin: PU = None
        self.t4: Seconds = None
        self.k1: float = None
        self.k2: float = None
        self.t5: Seconds = None
        self.k3: float = None
        self.k4: float = None
        self.t6: Seconds = None
        self.k5: float = None
        self.k6: float = None
        self.t7: Seconds = None
        self.k7: float = None
        self.k8: float = None
        self.db1: Frequency = None
        self.eps: Frequency = None
        self.sdb1: bool = None
        self.sdb2: bool = None
        self.db2: ActivePower = None
        self.valve: bool = None
        self.gv1: PU = None
        self.pgv1: PU = None
        self.gv2: PU = None
        self.pgv2: PU = None
        self.gv3: PU = None
        self.pgv3: PU = None
        self.gv4: PU = None
        self.pgv4: PU = None
        self.gv5: PU = None
        self.pgv5: PU = None
        self.gv6: PU = None
        self.pgv6: PU = None

class GovSteam2(TurbineGovernorDynamics):
    """RDF class GovSteam2."""

    __slots__ = ('k', 'dbf', 't1', 't2', 'pmax', 'pmin', 'mxef', 'mnef')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovSteam2') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.k: float = None
        self.dbf: PU = None
        self.t1: Seconds = None
        self.t2: Seconds = None
        self.pmax: PU = None
        self.pmin: PU = None
        self.mxef: PU = None
        self.mnef: PU = None

class GovSteamBB(TurbineGovernorDynamics):
    """RDF class GovSteamBB."""

    __slots__ = ('fcut', 'ks', 'kls', 'kg', 't1', 'kp', 'tn', 'kd', 'td', 'pmax', 'pmin', 't4', 'k2', 't5', 'k3', 't6', 'peflag')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovSteamBB') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.fcut: PU = None
        self.ks: PU = None
        self.kls: PU = None
        self.kg: PU = None
        self.t1: Seconds = None
        self.kp: PU = None
        self.tn: Seconds = None
        self.kd: PU = None
        self.td: Seconds = None
        self.pmax: PU = None
        self.pmin: PU = None
        self.t4: Seconds = None
        self.k2: PU = None
        self.t5: Seconds = None
        self.k3: PU = None
        self.t6: Seconds = None
        self.peflag: bool = None

class GovSteamCC(CrossCompoundTurbineGovernorDynamics):
    """RDF class GovSteamCC."""

    __slots__ = ('mwbase', 'pmaxhp', 'rhp', 't1hp', 't3hp', 't4hp', 't5hp', 'fhp', 'dhp', 'pmaxlp', 'rlp', 't1lp', 't3lp', 't4lp', 't5lp', 'flp', 'dlp')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovSteamCC') -> None:
        """Initialize an RDF-defined CGMES object."""
        CrossCompoundTurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.mwbase: ActivePower = None
        self.pmaxhp: PU = None
        self.rhp: PU = None
        self.t1hp: Seconds = None
        self.t3hp: Seconds = None
        self.t4hp: Seconds = None
        self.t5hp: Seconds = None
        self.fhp: PU = None
        self.dhp: PU = None
        self.pmaxlp: PU = None
        self.rlp: PU = None
        self.t1lp: Seconds = None
        self.t3lp: Seconds = None
        self.t4lp: Seconds = None
        self.t5lp: Seconds = None
        self.flp: PU = None
        self.dlp: PU = None

class GovSteamEU(TurbineGovernorDynamics):
    """RDF class GovSteamEU."""

    __slots__ = ('mwbase', 'tp', 'ke', 'tip', 'tdp', 'tfp', 'tf', 'kfcor', 'db1', 'wfmax', 'wfmin', 'pmax', 'ten', 'tw', 'komegacor', 'db2', 'wwmax', 'wwmin', 'wmax1', 'wmax2', 'tvhp', 'cho', 'chc', 'hhpmax', 'tvip', 'cio', 'cic', 'simx', 'thp', 'trh', 'tlp', 'prhmax', 'khp', 'klp', 'tb')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovSteamEU') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.mwbase: ActivePower = None
        self.tp: Seconds = None
        self.ke: PU = None
        self.tip: Seconds = None
        self.tdp: Seconds = None
        self.tfp: Seconds = None
        self.tf: Seconds = None
        self.kfcor: PU = None
        self.db1: PU = None
        self.wfmax: PU = None
        self.wfmin: PU = None
        self.pmax: PU = None
        self.ten: Seconds = None
        self.tw: Seconds = None
        self.komegacor: PU = None
        self.db2: PU = None
        self.wwmax: PU = None
        self.wwmin: PU = None
        self.wmax1: PU = None
        self.wmax2: PU = None
        self.tvhp: Seconds = None
        self.cho: float = None
        self.chc: float = None
        self.hhpmax: PU = None
        self.tvip: Seconds = None
        self.cio: PU = None
        self.cic: PU = None
        self.simx: PU = None
        self.thp: Seconds = None
        self.trh: Seconds = None
        self.tlp: Seconds = None
        self.prhmax: PU = None
        self.khp: PU = None
        self.klp: PU = None
        self.tb: Seconds = None

class GovSteamFV2(TurbineGovernorDynamics):
    """RDF class GovSteamFV2."""

    __slots__ = ('mwbase', 't1', 'vmax', 'vmin', 'k', 't3', 'dt', 'tt', 'r', 'ta', 'tb', 'tc', 'ti')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovSteamFV2') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.mwbase: ActivePower = None
        self.t1: Seconds = None
        self.vmax: PU = None
        self.vmin: PU = None
        self.k: PU = None
        self.t3: Seconds = None
        self.dt: PU = None
        self.tt: Seconds = None
        self.r: PU = None
        self.ta: Seconds = None
        self.tb: Seconds = None
        self.tc: Seconds = None
        self.ti: Seconds = None

class GovSteamFV3(TurbineGovernorDynamics):
    """RDF class GovSteamFV3."""

    __slots__ = ('mwbase', 'k', 't1', 't2', 't3', 'uo', 'uc', 'pmax', 'pmin', 't4', 'k1', 't5', 'k2', 't6', 'k3', 'ta', 'tb', 'tc', 'prmax', 'gv1', 'pgv1', 'gv2', 'pgv2', 'gv3', 'pgv3', 'gv4', 'pgv4', 'gv5', 'pgv5', 'gv6', 'pgv6')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovSteamFV3') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.mwbase: ActivePower = None
        self.k: PU = None
        self.t1: Seconds = None
        self.t2: Seconds = None
        self.t3: Seconds = None
        self.uo: float = None
        self.uc: float = None
        self.pmax: PU = None
        self.pmin: PU = None
        self.t4: Seconds = None
        self.k1: PU = None
        self.t5: Seconds = None
        self.k2: PU = None
        self.t6: Seconds = None
        self.k3: PU = None
        self.ta: Seconds = None
        self.tb: Seconds = None
        self.tc: Seconds = None
        self.prmax: PU = None
        self.gv1: PU = None
        self.pgv1: PU = None
        self.gv2: PU = None
        self.pgv2: PU = None
        self.gv3: PU = None
        self.pgv3: PU = None
        self.gv4: PU = None
        self.pgv4: PU = None
        self.gv5: PU = None
        self.pgv5: PU = None
        self.gv6: PU = None
        self.pgv6: PU = None

class GovSteamFV4(TurbineGovernorDynamics):
    """RDF class GovSteamFV4."""

    __slots__ = ('kf1', 'kf3', 'lps', 'lpi', 'mxef', 'mnef', 'crmx', 'crmn', 'kpt', 'kit', 'rvgmx', 'rvgmn', 'svmx', 'svmn', 'srmx', 'srmn', 'kpp', 'kip', 'rsmimx', 'rsmimn', 'kmp1', 'kmp2', 'srsmp', 'ta', 'tc', 'ty', 'yhpmx', 'yhpmn', 'tam', 'tcm', 'ympmx', 'ympmn', 'y', 'thp', 'trh', 'tmp', 'khp', 'pr1', 'pr2', 'psmn', 'kpc', 'kic', 'kdc', 'tdc', 'cpsmx', 'cpsmn', 'krc', 'tf1', 'tf2', 'tv', 'ksh')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovSteamFV4') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.kf1: PU = None
        self.kf3: PU = None
        self.lps: PU = None
        self.lpi: PU = None
        self.mxef: PU = None
        self.mnef: PU = None
        self.crmx: PU = None
        self.crmn: PU = None
        self.kpt: PU = None
        self.kit: PU = None
        self.rvgmx: PU = None
        self.rvgmn: PU = None
        self.svmx: float = None
        self.svmn: float = None
        self.srmx: PU = None
        self.srmn: PU = None
        self.kpp: PU = None
        self.kip: PU = None
        self.rsmimx: PU = None
        self.rsmimn: PU = None
        self.kmp1: PU = None
        self.kmp2: PU = None
        self.srsmp: PU = None
        self.ta: Seconds = None
        self.tc: Seconds = None
        self.ty: Seconds = None
        self.yhpmx: PU = None
        self.yhpmn: PU = None
        self.tam: Seconds = None
        self.tcm: Seconds = None
        self.ympmx: PU = None
        self.ympmn: PU = None
        self.y: PU = None
        self.thp: Seconds = None
        self.trh: Seconds = None
        self.tmp: Seconds = None
        self.khp: PU = None
        self.pr1: PU = None
        self.pr2: PU = None
        self.psmn: PU = None
        self.kpc: PU = None
        self.kic: PU = None
        self.kdc: PU = None
        self.tdc: Seconds = None
        self.cpsmx: PU = None
        self.cpsmn: PU = None
        self.krc: PU = None
        self.tf1: Seconds = None
        self.tf2: Seconds = None
        self.tv: Seconds = None
        self.ksh: PU = None

class GovSteamIEEE1(TurbineGovernorDynamics):
    """RDF class GovSteamIEEE1."""

    __slots__ = ('mwbase', 'k', 't1', 't2', 't3', 'uo', 'uc', 'pmax', 'pmin', 't4', 'k1', 'k2', 't5', 'k3', 'k4', 't6', 'k5', 'k6', 't7', 'k7', 'k8')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovSteamIEEE1') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.mwbase: ActivePower = None
        self.k: PU = None
        self.t1: Seconds = None
        self.t2: Seconds = None
        self.t3: Seconds = None
        self.uo: float = None
        self.uc: float = None
        self.pmax: PU = None
        self.pmin: PU = None
        self.t4: Seconds = None
        self.k1: float = None
        self.k2: float = None
        self.t5: Seconds = None
        self.k3: float = None
        self.k4: float = None
        self.t6: Seconds = None
        self.k5: float = None
        self.k6: float = None
        self.t7: Seconds = None
        self.k7: float = None
        self.k8: float = None

class GovSteamSGO(TurbineGovernorDynamics):
    """RDF class GovSteamSGO."""

    __slots__ = ('mwbase', 't1', 't2', 't3', 't4', 't5', 't6', 'k1', 'k2', 'k3', 'pmax', 'pmin')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'GovSteamSGO') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.mwbase: ActivePower = None
        self.t1: Seconds = None
        self.t2: Seconds = None
        self.t3: Seconds = None
        self.t4: Seconds = None
        self.t5: Seconds = None
        self.t6: Seconds = None
        self.k1: PU = None
        self.k2: PU = None
        self.k3: PU = None
        self.pmax: PU = None
        self.pmin: Seconds = None

class MechLoad1(MechanicalLoadDynamics):
    """RDF class MechLoad1."""

    __slots__ = ('a', 'b', 'd', 'e')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'MechLoad1') -> None:
        """Initialize an RDF-defined CGMES object."""
        MechanicalLoadDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.a: float = None
        self.b: float = None
        self.d: float = None
        self.e: float = None

class MechanicalLoadUserDefined(MechanicalLoadDynamics):
    """RDF class MechanicalLoadUserDefined."""

    __slots__ = ('proprietary', 'ProprietaryParameterDynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'MechanicalLoadUserDefined') -> None:
        """Initialize an RDF-defined CGMES object."""
        MechanicalLoadDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.proprietary: bool = None
        self.ProprietaryParameterDynamics: List[ProprietaryParameterDynamics] = list()

class OverexcLim2(OverexcitationLimiterDynamics):
    """RDF class OverexcLim2."""

    __slots__ = ('koi', 'voimax', 'voimin', 'ifdlim')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'OverexcLim2') -> None:
        """Initialize an RDF-defined CGMES object."""
        OverexcitationLimiterDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.koi: PU = None
        self.voimax: PU = None
        self.voimin: PU = None
        self.ifdlim: PU = None

class OverexcLimIEEE(OverexcitationLimiterDynamics):
    """RDF class OverexcLimIEEE."""

    __slots__ = ('itfpu', 'ifdmax', 'ifdlim', 'hyst', 'kcd', 'kramp')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'OverexcLimIEEE') -> None:
        """Initialize an RDF-defined CGMES object."""
        OverexcitationLimiterDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.itfpu: PU = None
        self.ifdmax: PU = None
        self.ifdlim: PU = None
        self.hyst: PU = None
        self.kcd: PU = None
        self.kramp: float = None

class OverexcLimX1(OverexcitationLimiterDynamics):
    """RDF class OverexcLimX1."""

    __slots__ = ('efdrated', 'efd1', 't1', 'efd2', 't2', 'efd3', 't3', 'efddes', 'kmx', 'vlow')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'OverexcLimX1') -> None:
        """Initialize an RDF-defined CGMES object."""
        OverexcitationLimiterDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.efdrated: PU = None
        self.efd1: PU = None
        self.t1: Seconds = None
        self.efd2: PU = None
        self.t2: Seconds = None
        self.efd3: PU = None
        self.t3: Seconds = None
        self.efddes: PU = None
        self.kmx: PU = None
        self.vlow: PU = None

class OverexcLimX2(OverexcitationLimiterDynamics):
    """RDF class OverexcLimX2."""

    __slots__ = ('m', 'efdrated', 'efd1', 't1', 'efd2', 't2', 'efd3', 't3', 'efddes', 'kmx', 'vlow')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'OverexcLimX2') -> None:
        """Initialize an RDF-defined CGMES object."""
        OverexcitationLimiterDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.m: bool = None
        self.efdrated: PU = None
        self.efd1: PU = None
        self.t1: Seconds = None
        self.efd2: PU = None
        self.t2: Seconds = None
        self.efd3: PU = None
        self.t3: Seconds = None
        self.efddes: PU = None
        self.kmx: PU = None
        self.vlow: PU = None

class OverexcitationLimiterUserDefined(OverexcitationLimiterDynamics):
    """RDF class OverexcitationLimiterUserDefined."""

    __slots__ = ('proprietary', 'ProprietaryParameterDynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'OverexcitationLimiterUserDefined') -> None:
        """Initialize an RDF-defined CGMES object."""
        OverexcitationLimiterDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.proprietary: bool = None
        self.ProprietaryParameterDynamics: List[ProprietaryParameterDynamics] = list()

class PFVArControllerType1UserDefined(PFVArControllerType1Dynamics):
    """RDF class PFVArControllerType1UserDefined."""

    __slots__ = ('proprietary', 'ProprietaryParameterDynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'PFVArControllerType1UserDefined') -> None:
        """Initialize an RDF-defined CGMES object."""
        PFVArControllerType1Dynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.proprietary: bool = None
        self.ProprietaryParameterDynamics: List[ProprietaryParameterDynamics] = list()

class PFVArControllerType2UserDefined(PFVArControllerType2Dynamics):
    """RDF class PFVArControllerType2UserDefined."""

    __slots__ = ('proprietary', 'ProprietaryParameterDynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'PFVArControllerType2UserDefined') -> None:
        """Initialize an RDF-defined CGMES object."""
        PFVArControllerType2Dynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.proprietary: bool = None
        self.ProprietaryParameterDynamics: List[ProprietaryParameterDynamics] = list()

class PFVArType1IEEEPFController(PFVArControllerType1Dynamics):
    """RDF class PFVArType1IEEEPFController."""

    __slots__ = ('ovex', 'tpfc', 'vitmin', 'vpf', 'vpfcbw', 'vpfref', 'vvtmax', 'vvtmin')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'PFVArType1IEEEPFController') -> None:
        """Initialize an RDF-defined CGMES object."""
        PFVArControllerType1Dynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.ovex: bool = None
        self.tpfc: Seconds = None
        self.vitmin: PU = None
        self.vpf: PU = None
        self.vpfcbw: float = None
        self.vpfref: PU = None
        self.vvtmax: PU = None
        self.vvtmin: PU = None

class PFVArType1IEEEVArController(PFVArControllerType1Dynamics):
    """RDF class PFVArType1IEEEVArController."""

    __slots__ = ('tvarc', 'vvar', 'vvarcbw', 'vvarref', 'vvtmax', 'vvtmin')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'PFVArType1IEEEVArController') -> None:
        """Initialize an RDF-defined CGMES object."""
        PFVArControllerType1Dynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.tvarc: Seconds = None
        self.vvar: PU = None
        self.vvarcbw: float = None
        self.vvarref: PU = None
        self.vvtmax: PU = None
        self.vvtmin: PU = None

class PFVArType2Common1(PFVArControllerType2Dynamics):
    """RDF class PFVArType2Common1."""

    __slots__ = ('j', 'kp', 'ki', 'max', 'ref')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'PFVArType2Common1') -> None:
        """Initialize an RDF-defined CGMES object."""
        PFVArControllerType2Dynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.j: bool = None
        self.kp: PU = None
        self.ki: PU = None
        self.max: PU = None
        self.ref: PU = None

class PFVArType2IEEEPFController(PFVArControllerType2Dynamics):
    """RDF class PFVArType2IEEEPFController."""

    __slots__ = ('pfref', 'vref', 'vclmt', 'kp', 'ki', 'vs', 'exlon')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'PFVArType2IEEEPFController') -> None:
        """Initialize an RDF-defined CGMES object."""
        PFVArControllerType2Dynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.pfref: PU = None
        self.vref: PU = None
        self.vclmt: PU = None
        self.kp: PU = None
        self.ki: PU = None
        self.vs: float = None
        self.exlon: bool = None

class PFVArType2IEEEVArController(PFVArControllerType2Dynamics):
    """RDF class PFVArType2IEEEVArController."""

    __slots__ = ('qref', 'vref', 'vclmt', 'kp', 'ki', 'vs', 'exlon')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'PFVArType2IEEEVArController') -> None:
        """Initialize an RDF-defined CGMES object."""
        PFVArControllerType2Dynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.qref: PU = None
        self.vref: PU = None
        self.vclmt: PU = None
        self.kp: PU = None
        self.ki: PU = None
        self.vs: float = None
        self.exlon: bool = None

class PowerSystemStabilizerUserDefined(PowerSystemStabilizerDynamics):
    """RDF class PowerSystemStabilizerUserDefined."""

    __slots__ = ('proprietary', 'ProprietaryParameterDynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'PowerSystemStabilizerUserDefined') -> None:
        """Initialize an RDF-defined CGMES object."""
        PowerSystemStabilizerDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.proprietary: bool = None
        self.ProprietaryParameterDynamics: List[ProprietaryParameterDynamics] = list()

class Pss1(PowerSystemStabilizerDynamics):
    """RDF class Pss1."""

    __slots__ = ('kw', 'kf', 'kpe', 'pmin', 'ks', 'vsmn', 'vsmx', 'tpe', 't5', 't6', 't7', 't8', 't9', 't10', 'vadat')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'Pss1') -> None:
        """Initialize an RDF-defined CGMES object."""
        PowerSystemStabilizerDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.kw: float = None
        self.kf: float = None
        self.kpe: float = None
        self.pmin: PU = None
        self.ks: float = None
        self.vsmn: PU = None
        self.vsmx: PU = None
        self.tpe: Seconds = None
        self.t5: Seconds = None
        self.t6: Seconds = None
        self.t7: Seconds = None
        self.t8: Seconds = None
        self.t9: Seconds = None
        self.t10: Seconds = None
        self.vadat: bool = None

class Pss1A(PowerSystemStabilizerDynamics):
    """RDF class Pss1A."""

    __slots__ = ('inputSignalType', 'a1', 'a2', 't1', 't2', 't3', 't4', 't5', 't6', 'ks', 'vrmax', 'vrmin', 'vcu', 'vcl', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8', 'kd', 'tdelay')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'Pss1A') -> None:
        """Initialize an RDF-defined CGMES object."""
        PowerSystemStabilizerDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.inputSignalType: InputSignalKind = None
        self.a1: PU = None
        self.a2: PU = None
        self.t1: Seconds = None
        self.t2: Seconds = None
        self.t3: Seconds = None
        self.t4: Seconds = None
        self.t5: Seconds = None
        self.t6: Seconds = None
        self.ks: PU = None
        self.vrmax: PU = None
        self.vrmin: PU = None
        self.vcu: PU = None
        self.vcl: PU = None
        self.a3: PU = None
        self.a4: PU = None
        self.a5: PU = None
        self.a6: PU = None
        self.a7: PU = None
        self.a8: PU = None
        self.kd: bool = None
        self.tdelay: Seconds = None

class Pss2B(PowerSystemStabilizerDynamics):
    """RDF class Pss2B."""

    __slots__ = ('inputSignal1Type', 'inputSignal2Type', 'vsi1max', 'vsi1min', 'tw1', 'tw2', 'vsi2max', 'vsi2min', 'tw3', 'tw4', 't1', 't2', 't3', 't4', 't6', 't7', 't8', 't9', 't10', 't11', 'ks1', 'ks2', 'ks3', 'ks4', 'n', 'm', 'vstmax', 'vstmin', 'a', 'ta', 'tb')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'Pss2B') -> None:
        """Initialize an RDF-defined CGMES object."""
        PowerSystemStabilizerDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.inputSignal1Type: InputSignalKind = None
        self.inputSignal2Type: InputSignalKind = None
        self.vsi1max: PU = None
        self.vsi1min: PU = None
        self.tw1: Seconds = None
        self.tw2: Seconds = None
        self.vsi2max: PU = None
        self.vsi2min: PU = None
        self.tw3: Seconds = None
        self.tw4: Seconds = None
        self.t1: Seconds = None
        self.t2: Seconds = None
        self.t3: Seconds = None
        self.t4: Seconds = None
        self.t6: Seconds = None
        self.t7: Seconds = None
        self.t8: Seconds = None
        self.t9: Seconds = None
        self.t10: Seconds = None
        self.t11: Seconds = None
        self.ks1: PU = None
        self.ks2: PU = None
        self.ks3: PU = None
        self.ks4: PU = None
        self.n: int = None
        self.m: int = None
        self.vstmax: PU = None
        self.vstmin: PU = None
        self.a: float = None
        self.ta: Seconds = None
        self.tb: Seconds = None

class Pss2ST(PowerSystemStabilizerDynamics):
    """RDF class Pss2ST."""

    __slots__ = ('inputSignal1Type', 'inputSignal2Type', 'k1', 'k2', 't1', 't2', 't3', 't4', 't5', 't6', 't7', 't8', 't9', 't10', 'lsmax', 'lsmin', 'vcu', 'vcl')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'Pss2ST') -> None:
        """Initialize an RDF-defined CGMES object."""
        PowerSystemStabilizerDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.inputSignal1Type: InputSignalKind = None
        self.inputSignal2Type: InputSignalKind = None
        self.k1: PU = None
        self.k2: PU = None
        self.t1: Seconds = None
        self.t2: Seconds = None
        self.t3: Seconds = None
        self.t4: Seconds = None
        self.t5: Seconds = None
        self.t6: Seconds = None
        self.t7: Seconds = None
        self.t8: Seconds = None
        self.t9: Seconds = None
        self.t10: Seconds = None
        self.lsmax: PU = None
        self.lsmin: PU = None
        self.vcu: PU = None
        self.vcl: PU = None

class Pss5(PowerSystemStabilizerDynamics):
    """RDF class Pss5."""

    __slots__ = ('kpe', 'kf', 'isfreq', 'kpss', 'ctw2', 'tw1', 'tw2', 'tl1', 'tl2', 'tl3', 'tl4', 'vsmn', 'vsmx', 'tpe', 'pmm', 'deadband', 'vadat')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'Pss5') -> None:
        """Initialize an RDF-defined CGMES object."""
        PowerSystemStabilizerDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.kpe: float = None
        self.kf: float = None
        self.isfreq: bool = None
        self.kpss: float = None
        self.ctw2: bool = None
        self.tw1: Seconds = None
        self.tw2: Seconds = None
        self.tl1: Seconds = None
        self.tl2: Seconds = None
        self.tl3: Seconds = None
        self.tl4: Seconds = None
        self.vsmn: PU = None
        self.vsmx: PU = None
        self.tpe: Seconds = None
        self.pmm: PU = None
        self.deadband: PU = None
        self.vadat: bool = None

class PssELIN2(PowerSystemStabilizerDynamics):
    """RDF class PssELIN2."""

    __slots__ = ('ts1', 'ts2', 'ts3', 'ts4', 'ts5', 'ts6', 'ks1', 'ks2', 'ppss', 'apss', 'psslim')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'PssELIN2') -> None:
        """Initialize an RDF-defined CGMES object."""
        PowerSystemStabilizerDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.ts1: Seconds = None
        self.ts2: Seconds = None
        self.ts3: Seconds = None
        self.ts4: Seconds = None
        self.ts5: Seconds = None
        self.ts6: Seconds = None
        self.ks1: PU = None
        self.ks2: PU = None
        self.ppss: PU = None
        self.apss: PU = None
        self.psslim: PU = None

class PssIEEE1A(PowerSystemStabilizerDynamics):
    """RDF class PssIEEE1A."""

    __slots__ = ('inputSignalType', 'a1', 'a2', 't1', 't2', 't3', 't4', 't5', 't6', 'ks', 'vrmax', 'vrmin')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'PssIEEE1A') -> None:
        """Initialize an RDF-defined CGMES object."""
        PowerSystemStabilizerDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.inputSignalType: InputSignalKind = None
        self.a1: PU = None
        self.a2: PU = None
        self.t1: Seconds = None
        self.t2: Seconds = None
        self.t3: Seconds = None
        self.t4: Seconds = None
        self.t5: Seconds = None
        self.t6: Seconds = None
        self.ks: PU = None
        self.vrmax: PU = None
        self.vrmin: PU = None

class PssIEEE2B(PowerSystemStabilizerDynamics):
    """RDF class PssIEEE2B."""

    __slots__ = ('inputSignal1Type', 'inputSignal2Type', 'vsi1max', 'vsi1min', 'tw1', 'tw2', 'vsi2max', 'vsi2min', 'tw3', 'tw4', 't1', 't2', 't3', 't4', 't6', 't7', 't8', 't9', 't10', 't11', 'ks1', 'ks2', 'ks3', 'n', 'm', 'vstmax', 'vstmin')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'PssIEEE2B') -> None:
        """Initialize an RDF-defined CGMES object."""
        PowerSystemStabilizerDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.inputSignal1Type: InputSignalKind = None
        self.inputSignal2Type: InputSignalKind = None
        self.vsi1max: PU = None
        self.vsi1min: PU = None
        self.tw1: Seconds = None
        self.tw2: Seconds = None
        self.vsi2max: PU = None
        self.vsi2min: PU = None
        self.tw3: Seconds = None
        self.tw4: Seconds = None
        self.t1: Seconds = None
        self.t2: Seconds = None
        self.t3: Seconds = None
        self.t4: Seconds = None
        self.t6: Seconds = None
        self.t7: Seconds = None
        self.t8: Seconds = None
        self.t9: Seconds = None
        self.t10: Seconds = None
        self.t11: Seconds = None
        self.ks1: PU = None
        self.ks2: PU = None
        self.ks3: PU = None
        self.n: int = None
        self.m: int = None
        self.vstmax: PU = None
        self.vstmin: PU = None

class PssIEEE3B(PowerSystemStabilizerDynamics):
    """RDF class PssIEEE3B."""

    __slots__ = ('inputSignal1Type', 'inputSignal2Type', 't1', 't2', 'tw1', 'tw2', 'tw3', 'ks1', 'ks2', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8', 'vstmax', 'vstmin')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'PssIEEE3B') -> None:
        """Initialize an RDF-defined CGMES object."""
        PowerSystemStabilizerDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.inputSignal1Type: InputSignalKind = None
        self.inputSignal2Type: InputSignalKind = None
        self.t1: Seconds = None
        self.t2: Seconds = None
        self.tw1: Seconds = None
        self.tw2: Seconds = None
        self.tw3: Seconds = None
        self.ks1: PU = None
        self.ks2: PU = None
        self.a1: PU = None
        self.a2: PU = None
        self.a3: PU = None
        self.a4: PU = None
        self.a5: PU = None
        self.a6: PU = None
        self.a7: PU = None
        self.a8: PU = None
        self.vstmax: PU = None
        self.vstmin: PU = None

class PssIEEE4B(PowerSystemStabilizerDynamics):
    """RDF class PssIEEE4B."""

    __slots__ = ('bwh1', 'bwh2', 'bwl1', 'bwl2', 'kh', 'kh1', 'kh11', 'kh17', 'kh2', 'ki', 'ki1', 'ki11', 'ki17', 'ki2', 'kl', 'kl1', 'kl11', 'kl17', 'kl2', 'omeganh1', 'omeganh2', 'omeganl1', 'omeganl2', 'th1', 'th10', 'th11', 'th12', 'th2', 'th3', 'th4', 'th5', 'th6', 'th7', 'th8', 'th9', 'ti1', 'ti10', 'ti11', 'ti12', 'ti2', 'ti3', 'ti4', 'ti5', 'ti6', 'ti7', 'ti8', 'ti9', 'tl1', 'tl10', 'tl11', 'tl12', 'tl2', 'tl3', 'tl4', 'tl5', 'tl6', 'tl7', 'tl8', 'tl9', 'vhmax', 'vhmin', 'vimax', 'vimin', 'vlmax', 'vlmin', 'vstmax', 'vstmin')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'PssIEEE4B') -> None:
        """Initialize an RDF-defined CGMES object."""
        PowerSystemStabilizerDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.bwh1: float = None
        self.bwh2: float = None
        self.bwl1: float = None
        self.bwl2: float = None
        self.kh: PU = None
        self.kh1: PU = None
        self.kh11: PU = None
        self.kh17: PU = None
        self.kh2: PU = None
        self.ki: PU = None
        self.ki1: PU = None
        self.ki11: PU = None
        self.ki17: PU = None
        self.ki2: PU = None
        self.kl: PU = None
        self.kl1: PU = None
        self.kl11: PU = None
        self.kl17: PU = None
        self.kl2: PU = None
        self.omeganh1: float = None
        self.omeganh2: float = None
        self.omeganl1: float = None
        self.omeganl2: float = None
        self.th1: Seconds = None
        self.th10: Seconds = None
        self.th11: Seconds = None
        self.th12: Seconds = None
        self.th2: Seconds = None
        self.th3: Seconds = None
        self.th4: Seconds = None
        self.th5: Seconds = None
        self.th6: Seconds = None
        self.th7: Seconds = None
        self.th8: Seconds = None
        self.th9: Seconds = None
        self.ti1: Seconds = None
        self.ti10: Seconds = None
        self.ti11: Seconds = None
        self.ti12: Seconds = None
        self.ti2: Seconds = None
        self.ti3: Seconds = None
        self.ti4: Seconds = None
        self.ti5: Seconds = None
        self.ti6: Seconds = None
        self.ti7: Seconds = None
        self.ti8: Seconds = None
        self.ti9: Seconds = None
        self.tl1: Seconds = None
        self.tl10: Seconds = None
        self.tl11: Seconds = None
        self.tl12: Seconds = None
        self.tl2: Seconds = None
        self.tl3: Seconds = None
        self.tl4: Seconds = None
        self.tl5: Seconds = None
        self.tl6: Seconds = None
        self.tl7: Seconds = None
        self.tl8: Seconds = None
        self.tl9: Seconds = None
        self.vhmax: PU = None
        self.vhmin: PU = None
        self.vimax: PU = None
        self.vimin: PU = None
        self.vlmax: PU = None
        self.vlmin: PU = None
        self.vstmax: PU = None
        self.vstmin: PU = None

class PssPTIST1(PowerSystemStabilizerDynamics):
    """RDF class PssPTIST1."""

    __slots__ = ('m', 'tf', 'tp', 't1', 't2', 't3', 't4', 'k', 'dtf', 'dtc', 'dtp')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'PssPTIST1') -> None:
        """Initialize an RDF-defined CGMES object."""
        PowerSystemStabilizerDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.m: PU = None
        self.tf: Seconds = None
        self.tp: Seconds = None
        self.t1: Seconds = None
        self.t2: Seconds = None
        self.t3: Seconds = None
        self.t4: Seconds = None
        self.k: PU = None
        self.dtf: Seconds = None
        self.dtc: Seconds = None
        self.dtp: Seconds = None

class PssPTIST3(PowerSystemStabilizerDynamics):
    """RDF class PssPTIST3."""

    __slots__ = ('m', 'tf', 'tp', 't1', 't2', 't3', 't4', 'k', 'dtf', 'dtc', 'dtp', 't5', 't6', 'a0', 'a1', 'a2', 'b0', 'b1', 'b2', 'a3', 'a4', 'a5', 'b3', 'b4', 'b5', 'athres', 'dl', 'al', 'lthres', 'pmin', 'isw', 'nav', 'ncl', 'ncr')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'PssPTIST3') -> None:
        """Initialize an RDF-defined CGMES object."""
        PowerSystemStabilizerDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.m: PU = None
        self.tf: Seconds = None
        self.tp: Seconds = None
        self.t1: Seconds = None
        self.t2: Seconds = None
        self.t3: Seconds = None
        self.t4: Seconds = None
        self.k: PU = None
        self.dtf: Seconds = None
        self.dtc: Seconds = None
        self.dtp: Seconds = None
        self.t5: Seconds = None
        self.t6: Seconds = None
        self.a0: PU = None
        self.a1: PU = None
        self.a2: PU = None
        self.b0: PU = None
        self.b1: PU = None
        self.b2: PU = None
        self.a3: PU = None
        self.a4: PU = None
        self.a5: PU = None
        self.b3: PU = None
        self.b4: PU = None
        self.b5: PU = None
        self.athres: PU = None
        self.dl: PU = None
        self.al: PU = None
        self.lthres: PU = None
        self.pmin: PU = None
        self.isw: bool = None
        self.nav: float = None
        self.ncl: float = None
        self.ncr: float = None

class PssRQB(PowerSystemStabilizerDynamics):
    """RDF class PssRQB."""

    __slots__ = ('ki2', 'ki3', 'ki4', 't4m', 'tomd', 'tomsl', 't4mom', 'sibv', 'kdpm', 't4f')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'PssRQB') -> None:
        """Initialize an RDF-defined CGMES object."""
        PowerSystemStabilizerDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.ki2: float = None
        self.ki3: float = None
        self.ki4: float = None
        self.t4m: Seconds = None
        self.tomd: Seconds = None
        self.tomsl: Seconds = None
        self.t4mom: Seconds = None
        self.sibv: PU = None
        self.kdpm: float = None
        self.t4f: Seconds = None

class PssSB4(PowerSystemStabilizerDynamics):
    """RDF class PssSB4."""

    __slots__ = ('tt', 'kx', 'tx2', 'ta', 'tx1', 'tb', 'tc', 'td', 'te', 'vsmax', 'vsmin')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'PssSB4') -> None:
        """Initialize an RDF-defined CGMES object."""
        PowerSystemStabilizerDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.tt: Seconds = None
        self.kx: PU = None
        self.tx2: Seconds = None
        self.ta: Seconds = None
        self.tx1: Seconds = None
        self.tb: Seconds = None
        self.tc: Seconds = None
        self.td: Seconds = None
        self.te: Seconds = None
        self.vsmax: PU = None
        self.vsmin: PU = None

class PssSH(PowerSystemStabilizerDynamics):
    """RDF class PssSH."""

    __slots__ = ('k', 'k0', 'k1', 'k2', 'k3', 'k4', 'td', 't1', 't2', 't3', 't4', 'vsmax', 'vsmin')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'PssSH') -> None:
        """Initialize an RDF-defined CGMES object."""
        PowerSystemStabilizerDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.k: PU = None
        self.k0: PU = None
        self.k1: PU = None
        self.k2: PU = None
        self.k3: PU = None
        self.k4: PU = None
        self.td: Seconds = None
        self.t1: Seconds = None
        self.t2: Seconds = None
        self.t3: Seconds = None
        self.t4: Seconds = None
        self.vsmax: PU = None
        self.vsmin: PU = None

class PssSK(PowerSystemStabilizerDynamics):
    """RDF class PssSK."""

    __slots__ = ('k1', 'k2', 'k3', 't1', 't2', 't3', 't4', 't5', 't6', 'vsmax', 'vsmin')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'PssSK') -> None:
        """Initialize an RDF-defined CGMES object."""
        PowerSystemStabilizerDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.k1: PU = None
        self.k2: PU = None
        self.k3: PU = None
        self.t1: Seconds = None
        self.t2: Seconds = None
        self.t3: Seconds = None
        self.t4: Seconds = None
        self.t5: Seconds = None
        self.t6: Seconds = None
        self.vsmax: PU = None
        self.vsmin: PU = None

class PssSTAB2A(PowerSystemStabilizerDynamics):
    """RDF class PssSTAB2A."""

    __slots__ = ('k2', 'k3', 'k4', 'k5', 't2', 't3', 't5', 'hlim')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'PssSTAB2A') -> None:
        """Initialize an RDF-defined CGMES object."""
        PowerSystemStabilizerDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.k2: PU = None
        self.k3: PU = None
        self.k4: PU = None
        self.k5: PU = None
        self.t2: Seconds = None
        self.t3: Seconds = None
        self.t5: Seconds = None
        self.hlim: PU = None

class PssWECC(PowerSystemStabilizerDynamics):
    """RDF class PssWECC."""

    __slots__ = ('inputSignal1Type', 'inputSignal2Type', 'k1', 't1', 'k2', 't2', 't3', 't4', 't5', 't6', 't7', 't8', 't10', 't9', 'vsmax', 'vsmin', 'vcu', 'vcl')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'PssWECC') -> None:
        """Initialize an RDF-defined CGMES object."""
        PowerSystemStabilizerDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.inputSignal1Type: InputSignalKind = None
        self.inputSignal2Type: InputSignalKind = None
        self.k1: PU = None
        self.t1: Seconds = None
        self.k2: PU = None
        self.t2: Seconds = None
        self.t3: Seconds = None
        self.t4: Seconds = None
        self.t5: Seconds = None
        self.t6: Seconds = None
        self.t7: Seconds = None
        self.t8: Seconds = None
        self.t10: Seconds = None
        self.t9: Seconds = None
        self.vsmax: PU = None
        self.vsmin: PU = None
        self.vcu: PU = None
        self.vcl: PU = None

class SVCUserDefined(StaticVarCompensatorDynamics):
    """RDF class SVCUserDefined."""

    __slots__ = ('proprietary', 'ProprietaryParameterDynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'SVCUserDefined') -> None:
        """Initialize an RDF-defined CGMES object."""
        StaticVarCompensatorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.proprietary: bool = None
        self.ProprietaryParameterDynamics: List[ProprietaryParameterDynamics] = list()

class SynchronousMachineDynamics(RotatingMachineDynamics):
    """RDF class SynchronousMachineDynamics."""

    __slots__ = ('SynchronousMachine', 'CrossCompoundTurbineGovernorDyanmics', 'CrossCompoundTurbineGovernorDynamics', 'MechanicalLoadDynamics', 'ExcitationSystemDynamics', 'TurbineGovernorDynamics', 'GenICompensationForGenJ')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'SynchronousMachineDynamics') -> None:
        """Initialize an RDF-defined CGMES object."""
        RotatingMachineDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.SynchronousMachine: SynchronousMachine = None
        self.CrossCompoundTurbineGovernorDyanmics: CrossCompoundTurbineGovernorDynamics = None
        self.CrossCompoundTurbineGovernorDynamics: CrossCompoundTurbineGovernorDynamics = None
        self.MechanicalLoadDynamics: MechanicalLoadDynamics = None
        self.ExcitationSystemDynamics: ExcitationSystemDynamics = None
        self.TurbineGovernorDynamics: List[TurbineGovernorDynamics] = list()
        self.GenICompensationForGenJ: List[GenICompensationForGenJ] = list()

class TurbLCFB1(TurbineLoadControllerDynamics):
    """RDF class TurbLCFB1."""

    __slots__ = ('mwbase', 'speedReferenceGovernor', 'db', 'emax', 'fb', 'kp', 'ki', 'fbf', 'pbf', 'tpelec', 'irmax', 'pmwset')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'TurbLCFB1') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineLoadControllerDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.mwbase: ActivePower = None
        self.speedReferenceGovernor: bool = None
        self.db: PU = None
        self.emax: PU = None
        self.fb: PU = None
        self.kp: PU = None
        self.ki: PU = None
        self.fbf: bool = None
        self.pbf: bool = None
        self.tpelec: Seconds = None
        self.irmax: PU = None
        self.pmwset: ActivePower = None

class TurbineGovernorUserDefined(TurbineGovernorDynamics):
    """RDF class TurbineGovernorUserDefined."""

    __slots__ = ('proprietary', 'ProprietaryParameterDynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'TurbineGovernorUserDefined') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.proprietary: bool = None
        self.ProprietaryParameterDynamics: List[ProprietaryParameterDynamics] = list()

class TurbineLoadControllerUserDefined(TurbineLoadControllerDynamics):
    """RDF class TurbineLoadControllerUserDefined."""

    __slots__ = ('proprietary', 'ProprietaryParameterDynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'TurbineLoadControllerUserDefined') -> None:
        """Initialize an RDF-defined CGMES object."""
        TurbineLoadControllerDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.proprietary: bool = None
        self.ProprietaryParameterDynamics: List[ProprietaryParameterDynamics] = list()

class UnderexcLim2Simplified(UnderexcitationLimiterDynamics):
    """RDF class UnderexcLim2Simplified."""

    __slots__ = ('q0', 'q1', 'p0', 'p1', 'kui', 'vuimin', 'vuimax')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'UnderexcLim2Simplified') -> None:
        """Initialize an RDF-defined CGMES object."""
        UnderexcitationLimiterDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.q0: PU = None
        self.q1: PU = None
        self.p0: PU = None
        self.p1: PU = None
        self.kui: PU = None
        self.vuimin: PU = None
        self.vuimax: PU = None

class UnderexcLimIEEE1(UnderexcitationLimiterDynamics):
    """RDF class UnderexcLimIEEE1."""

    __slots__ = ('kur', 'kuc', 'kuf', 'vurmax', 'vucmax', 'kui', 'kul', 'vuimax', 'vuimin', 'tu1', 'tu2', 'tu3', 'tu4', 'vulmax', 'vulmin')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'UnderexcLimIEEE1') -> None:
        """Initialize an RDF-defined CGMES object."""
        UnderexcitationLimiterDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.kur: PU = None
        self.kuc: PU = None
        self.kuf: PU = None
        self.vurmax: PU = None
        self.vucmax: PU = None
        self.kui: PU = None
        self.kul: PU = None
        self.vuimax: PU = None
        self.vuimin: PU = None
        self.tu1: Seconds = None
        self.tu2: Seconds = None
        self.tu3: Seconds = None
        self.tu4: Seconds = None
        self.vulmax: PU = None
        self.vulmin: PU = None

class UnderexcLimIEEE2(UnderexcitationLimiterDynamics):
    """RDF class UnderexcLimIEEE2."""

    __slots__ = ('tuv', 'tup', 'tuq', 'kui', 'kul', 'vuimax', 'vuimin', 'kuf', 'kfb', 'tul', 'tu1', 'tu2', 'tu3', 'tu4', 'vulmax', 'vulmin', 'p0', 'q0', 'p1', 'q1', 'p2', 'q2', 'p3', 'q3', 'p4', 'q4', 'p5', 'q5', 'p6', 'q6', 'p7', 'q7', 'p8', 'q8', 'p9', 'q9', 'p10', 'q10', 'k1', 'k2')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'UnderexcLimIEEE2') -> None:
        """Initialize an RDF-defined CGMES object."""
        UnderexcitationLimiterDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.tuv: Seconds = None
        self.tup: Seconds = None
        self.tuq: Seconds = None
        self.kui: PU = None
        self.kul: PU = None
        self.vuimax: PU = None
        self.vuimin: PU = None
        self.kuf: PU = None
        self.kfb: PU = None
        self.tul: Seconds = None
        self.tu1: Seconds = None
        self.tu2: Seconds = None
        self.tu3: Seconds = None
        self.tu4: Seconds = None
        self.vulmax: PU = None
        self.vulmin: PU = None
        self.p0: PU = None
        self.q0: PU = None
        self.p1: PU = None
        self.q1: PU = None
        self.p2: PU = None
        self.q2: PU = None
        self.p3: PU = None
        self.q3: PU = None
        self.p4: PU = None
        self.q4: PU = None
        self.p5: PU = None
        self.q5: PU = None
        self.p6: PU = None
        self.q6: PU = None
        self.p7: PU = None
        self.q7: PU = None
        self.p8: PU = None
        self.q8: PU = None
        self.p9: PU = None
        self.q9: PU = None
        self.p10: PU = None
        self.q10: PU = None
        self.k1: float = None
        self.k2: float = None

class UnderexcLimX1(UnderexcitationLimiterDynamics):
    """RDF class UnderexcLimX1."""

    __slots__ = ('kf2', 'tf2', 'km', 'tm', 'melmax', 'k')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'UnderexcLimX1') -> None:
        """Initialize an RDF-defined CGMES object."""
        UnderexcitationLimiterDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.kf2: PU = None
        self.tf2: Seconds = None
        self.km: PU = None
        self.tm: Seconds = None
        self.melmax: PU = None
        self.k: PU = None

class UnderexcLimX2(UnderexcitationLimiterDynamics):
    """RDF class UnderexcLimX2."""

    __slots__ = ('kf2', 'tf2', 'km', 'tm', 'melmax', 'qo', 'r')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'UnderexcLimX2') -> None:
        """Initialize an RDF-defined CGMES object."""
        UnderexcitationLimiterDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.kf2: PU = None
        self.tf2: Seconds = None
        self.km: PU = None
        self.tm: Seconds = None
        self.melmax: PU = None
        self.qo: PU = None
        self.r: PU = None

class UnderexcitationLimiterUserDefined(UnderexcitationLimiterDynamics):
    """RDF class UnderexcitationLimiterUserDefined."""

    __slots__ = ('proprietary', 'ProprietaryParameterDynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'UnderexcitationLimiterUserDefined') -> None:
        """Initialize an RDF-defined CGMES object."""
        UnderexcitationLimiterDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.proprietary: bool = None
        self.ProprietaryParameterDynamics: List[ProprietaryParameterDynamics] = list()

class VAdjIEEE(VoltageAdjusterDynamics):
    """RDF class VAdjIEEE."""

    __slots__ = ('vadjf', 'adjslew', 'vadjmax', 'vadjmin', 'taon', 'taoff')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'VAdjIEEE') -> None:
        """Initialize an RDF-defined CGMES object."""
        VoltageAdjusterDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.vadjf: float = None
        self.adjslew: float = None
        self.vadjmax: PU = None
        self.vadjmin: PU = None
        self.taon: Seconds = None
        self.taoff: Seconds = None

class VCompIEEEType1(VoltageCompensatorDynamics):
    """RDF class VCompIEEEType1."""

    __slots__ = ('rc', 'xc', 'tr')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'VCompIEEEType1') -> None:
        """Initialize an RDF-defined CGMES object."""
        VoltageCompensatorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.rc: PU = None
        self.xc: PU = None
        self.tr: Seconds = None

class VCompIEEEType2(VoltageCompensatorDynamics):
    """RDF class VCompIEEEType2."""

    __slots__ = ('tr', 'GenICompensationForGenJ')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'VCompIEEEType2') -> None:
        """Initialize an RDF-defined CGMES object."""
        VoltageCompensatorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.tr: Seconds = None
        self.GenICompensationForGenJ: List[GenICompensationForGenJ] = list()

class VSCDynamics(HVDCDynamics):
    """RDF class VSCDynamics."""

    __slots__ = ('VsConverter',)

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'VSCDynamics') -> None:
        """Initialize an RDF-defined CGMES object."""
        HVDCDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.VsConverter: VsConverter = None

class VoltageAdjusterUserDefined(VoltageAdjusterDynamics):
    """RDF class VoltageAdjusterUserDefined."""

    __slots__ = ('proprietary', 'ProprietaryParameterDynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'VoltageAdjusterUserDefined') -> None:
        """Initialize an RDF-defined CGMES object."""
        VoltageAdjusterDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.proprietary: bool = None
        self.ProprietaryParameterDynamics: List[ProprietaryParameterDynamics] = list()

class VoltageCompensatorUserDefined(VoltageCompensatorDynamics):
    """RDF class VoltageCompensatorUserDefined."""

    __slots__ = ('proprietary', 'ProprietaryParameterDynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'VoltageCompensatorUserDefined') -> None:
        """Initialize an RDF-defined CGMES object."""
        VoltageCompensatorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.proprietary: bool = None
        self.ProprietaryParameterDynamics: List[ProprietaryParameterDynamics] = list()

class WindPlantIEC(WindPlantDynamics):
    """RDF class WindPlantIEC."""

    __slots__ = ('WindPlantFreqPcontrolIEC', 'WindPlantReactiveControlIEC')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindPlantIEC') -> None:
        """Initialize an RDF-defined CGMES object."""
        WindPlantDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.WindPlantFreqPcontrolIEC: WindPlantFreqPcontrolIEC = None
        self.WindPlantReactiveControlIEC: WindPlantReactiveControlIEC = None

class WindPlantUserDefined(WindPlantDynamics):
    """RDF class WindPlantUserDefined."""

    __slots__ = ('proprietary', 'ProprietaryParameterDynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindPlantUserDefined') -> None:
        """Initialize an RDF-defined CGMES object."""
        WindPlantDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.proprietary: bool = None
        self.ProprietaryParameterDynamics: List[ProprietaryParameterDynamics] = list()

class WindTurbineType1or2IEC(WindTurbineType1or2Dynamics):
    """RDF class WindTurbineType1or2IEC."""

    __slots__ = ('WindMechIEC', 'WindProtectionIEC')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindTurbineType1or2IEC') -> None:
        """Initialize an RDF-defined CGMES object."""
        WindTurbineType1or2Dynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.WindMechIEC: WindMechIEC = None
        self.WindProtectionIEC: WindProtectionIEC = None

class WindTurbineType3or4IEC(WindTurbineType3or4Dynamics):
    """RDF class WindTurbineType3or4IEC."""

    __slots__ = ('WindContCurrLimIEC', 'WIndContQIEC', 'WindContQLimIEC', 'WindContQPQULimIEC', 'WindProtectionIEC', 'WindRefFrameRotIEC')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindTurbineType3or4IEC') -> None:
        """Initialize an RDF-defined CGMES object."""
        WindTurbineType3or4Dynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.WindContCurrLimIEC: WindContCurrLimIEC = None
        self.WIndContQIEC: WindContQIEC = None
        self.WindContQLimIEC: WindContQLimIEC = None
        self.WindContQPQULimIEC: WindContQPQULimIEC = None
        self.WindProtectionIEC: WindProtectionIEC = None
        self.WindRefFrameRotIEC: WindRefFrameRotIEC = None

class WindType1or2UserDefined(WindTurbineType1or2Dynamics):
    """RDF class WindType1or2UserDefined."""

    __slots__ = ('proprietary', 'ProprietaryParameterDynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindType1or2UserDefined') -> None:
        """Initialize an RDF-defined CGMES object."""
        WindTurbineType1or2Dynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.proprietary: bool = None
        self.ProprietaryParameterDynamics: List[ProprietaryParameterDynamics] = list()

class WindType3or4UserDefined(WindTurbineType3or4Dynamics):
    """RDF class WindType3or4UserDefined."""

    __slots__ = ('proprietary', 'ProprietaryParameterDynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindType3or4UserDefined') -> None:
        """Initialize an RDF-defined CGMES object."""
        WindTurbineType3or4Dynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.proprietary: bool = None
        self.ProprietaryParameterDynamics: List[ProprietaryParameterDynamics] = list()

class ACDCConverter(ConductingEquipment):
    """RDF class ACDCConverter."""

    __slots__ = ()

    def __init__(self, rdfid: str = "", tpe: str = 'ACDCConverter') -> None:
        """Initialize an RDF-defined CGMES object."""
        ConductingEquipment.__init__(self, rdfid=rdfid, tpe=tpe)
        pass

class AsynchronousMachineEquivalentCircuit(AsynchronousMachineDynamics):
    """RDF class AsynchronousMachineEquivalentCircuit."""

    __slots__ = ('xm', 'rr1', 'xlr1', 'rr2', 'xlr2')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'AsynchronousMachineEquivalentCircuit') -> None:
        """Initialize an RDF-defined CGMES object."""
        AsynchronousMachineDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.xm: PU = None
        self.rr1: PU = None
        self.xlr1: PU = None
        self.rr2: PU = None
        self.xlr2: PU = None

class AsynchronousMachineTimeConstantReactance(AsynchronousMachineDynamics):
    """RDF class AsynchronousMachineTimeConstantReactance."""

    __slots__ = ('xs', 'xp', 'xpp', 'tpo', 'tppo')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'AsynchronousMachineTimeConstantReactance') -> None:
        """Initialize an RDF-defined CGMES object."""
        AsynchronousMachineDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.xs: PU = None
        self.xp: PU = None
        self.xpp: PU = None
        self.tpo: Seconds = None
        self.tppo: Seconds = None

class AsynchronousMachineUserDefined(AsynchronousMachineDynamics):
    """RDF class AsynchronousMachineUserDefined."""

    __slots__ = ('proprietary', 'ProprietaryParameterDynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'AsynchronousMachineUserDefined') -> None:
        """Initialize an RDF-defined CGMES object."""
        AsynchronousMachineDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.proprietary: bool = None
        self.ProprietaryParameterDynamics: List[ProprietaryParameterDynamics] = list()

class CSCUserDefined(CSCDynamics):
    """RDF class CSCUserDefined."""

    __slots__ = ('proprietary', 'ProprietaryParameterDynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'CSCUserDefined') -> None:
        """Initialize an RDF-defined CGMES object."""
        CSCDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.proprietary: bool = None
        self.ProprietaryParameterDynamics: List[ProprietaryParameterDynamics] = list()

class EnergyConnection(ConductingEquipment):
    """RDF class EnergyConnection."""

    __slots__ = ()

    def __init__(self, rdfid: str = "", tpe: str = 'EnergyConnection') -> None:
        """Initialize an RDF-defined CGMES object."""
        ConductingEquipment.__init__(self, rdfid=rdfid, tpe=tpe)
        pass

class SynchronousMachineDetailed(SynchronousMachineDynamics):
    """RDF class SynchronousMachineDetailed."""

    __slots__ = ('saturationFactorQAxis', 'saturationFactor120QAxis', 'efdBaseRatio', 'ifdBaseType', 'ifdBaseValue')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'SynchronousMachineDetailed') -> None:
        """Initialize an RDF-defined CGMES object."""
        SynchronousMachineDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.saturationFactorQAxis: float = None
        self.saturationFactor120QAxis: float = None
        self.efdBaseRatio: float = None
        self.ifdBaseType: IfdBaseKind = None
        self.ifdBaseValue: float = None

class SynchronousMachineSimplified(SynchronousMachineDynamics):
    """RDF class SynchronousMachineSimplified."""

    __slots__ = ()

    def __init__(self, rdfid: str = "", tpe: str = 'SynchronousMachineSimplified') -> None:
        """Initialize an RDF-defined CGMES object."""
        SynchronousMachineDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        pass

class SynchronousMachineUserDefined(SynchronousMachineDynamics):
    """RDF class SynchronousMachineUserDefined."""

    __slots__ = ('proprietary', 'ProprietaryParameterDynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'SynchronousMachineUserDefined') -> None:
        """Initialize an RDF-defined CGMES object."""
        SynchronousMachineDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.proprietary: bool = None
        self.ProprietaryParameterDynamics: List[ProprietaryParameterDynamics] = list()

class VSCUserDefined(VSCDynamics):
    """RDF class VSCUserDefined."""

    __slots__ = ('proprietary', 'ProprietaryParameterDynamics')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'VSCUserDefined') -> None:
        """Initialize an RDF-defined CGMES object."""
        VSCDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.proprietary: bool = None
        self.ProprietaryParameterDynamics: List[ProprietaryParameterDynamics] = list()

class WindGenTurbineType1aIEC(WindTurbineType1or2IEC):
    """RDF class WindGenTurbineType1aIEC."""

    __slots__ = ('WindAeroConstIEC',)

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindGenTurbineType1aIEC') -> None:
        """Initialize an RDF-defined CGMES object."""
        WindTurbineType1or2IEC.__init__(self, rdfid=rdfid, tpe=tpe)
        self.WindAeroConstIEC: WindAeroConstIEC = None

class WindGenTurbineType1bIEC(WindTurbineType1or2IEC):
    """RDF class WindGenTurbineType1bIEC."""

    __slots__ = ('WindPitchContPowerIEC',)

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindGenTurbineType1bIEC') -> None:
        """Initialize an RDF-defined CGMES object."""
        WindTurbineType1or2IEC.__init__(self, rdfid=rdfid, tpe=tpe)
        self.WindPitchContPowerIEC: WindPitchContPowerIEC = None

class WindGenTurbineType2IEC(WindTurbineType1or2IEC):
    """RDF class WindGenTurbineType2IEC."""

    __slots__ = ('WindContRotorRIEC', 'WindPitchContPowerIEC')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindGenTurbineType2IEC') -> None:
        """Initialize an RDF-defined CGMES object."""
        WindTurbineType1or2IEC.__init__(self, rdfid=rdfid, tpe=tpe)
        self.WindContRotorRIEC: WindContRotorRIEC = None
        self.WindPitchContPowerIEC: WindPitchContPowerIEC = None

class WindTurbineType3IEC(WindTurbineType3or4IEC):
    """RDF class WindTurbineType3IEC."""

    __slots__ = ('WindAeroOneDimIEC', 'WindAeroTwoDimIEC', 'WindContPitchAngleIEC', 'WindContPType3IEC', 'WindGenType3IEC', 'WindMechIEC')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindTurbineType3IEC') -> None:
        """Initialize an RDF-defined CGMES object."""
        WindTurbineType3or4IEC.__init__(self, rdfid=rdfid, tpe=tpe)
        self.WindAeroOneDimIEC: WindAeroOneDimIEC = None
        self.WindAeroTwoDimIEC: WindAeroTwoDimIEC = None
        self.WindContPitchAngleIEC: WindContPitchAngleIEC = None
        self.WindContPType3IEC: WindContPType3IEC = None
        self.WindGenType3IEC: WindGenType3IEC = None
        self.WindMechIEC: WindMechIEC = None

class WindTurbineType4IEC(WindTurbineType3or4IEC):
    """RDF class WindTurbineType4IEC."""

    __slots__ = ('WindGenType3aIEC',)

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindTurbineType4IEC') -> None:
        """Initialize an RDF-defined CGMES object."""
        WindTurbineType3or4IEC.__init__(self, rdfid=rdfid, tpe=tpe)
        self.WindGenType3aIEC: WindGenType3aIEC = None

class CsConverter(ACDCConverter):
    """RDF class CsConverter."""

    __slots__ = ('CSCDynamics',)

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'CsConverter') -> None:
        """Initialize an RDF-defined CGMES object."""
        ACDCConverter.__init__(self, rdfid=rdfid, tpe=tpe)
        self.CSCDynamics: CSCDynamics = None

class EnergyConsumer(EnergyConnection):
    """RDF class EnergyConsumer."""

    __slots__ = ('LoadDynamics',)

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'EnergyConsumer') -> None:
        """Initialize an RDF-defined CGMES object."""
        EnergyConnection.__init__(self, rdfid=rdfid, tpe=tpe)
        self.LoadDynamics: LoadDynamics = None

class RegulatingCondEq(EnergyConnection):
    """RDF class RegulatingCondEq."""

    __slots__ = ()

    def __init__(self, rdfid: str = "", tpe: str = 'RegulatingCondEq') -> None:
        """Initialize an RDF-defined CGMES object."""
        EnergyConnection.__init__(self, rdfid=rdfid, tpe=tpe)
        pass

class SynchronousMachineEquivalentCircuit(SynchronousMachineDetailed):
    """RDF class SynchronousMachineEquivalentCircuit."""

    __slots__ = ('xad', 'rfd', 'xfd', 'r1d', 'x1d', 'xf1d', 'xaq', 'r1q', 'x1q', 'r2q', 'x2q')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'SynchronousMachineEquivalentCircuit') -> None:
        """Initialize an RDF-defined CGMES object."""
        SynchronousMachineDetailed.__init__(self, rdfid=rdfid, tpe=tpe)
        self.xad: PU = None
        self.rfd: PU = None
        self.xfd: PU = None
        self.r1d: PU = None
        self.x1d: PU = None
        self.xf1d: PU = None
        self.xaq: PU = None
        self.r1q: PU = None
        self.x1q: PU = None
        self.r2q: PU = None
        self.x2q: PU = None

class SynchronousMachineTimeConstantReactance(SynchronousMachineDetailed):
    """RDF class SynchronousMachineTimeConstantReactance."""

    __slots__ = ('rotorType', 'modelType', 'ks', 'xDirectSync', 'xDirectTrans', 'xDirectSubtrans', 'xQuadSync', 'xQuadTrans', 'xQuadSubtrans', 'tpdo', 'tppdo', 'tpqo', 'tppqo', 'tc')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'SynchronousMachineTimeConstantReactance') -> None:
        """Initialize an RDF-defined CGMES object."""
        SynchronousMachineDetailed.__init__(self, rdfid=rdfid, tpe=tpe)
        self.rotorType: RotorKind = None
        self.modelType: SynchronousMachineModelKind = None
        self.ks: float = None
        self.xDirectSync: PU = None
        self.xDirectTrans: PU = None
        self.xDirectSubtrans: PU = None
        self.xQuadSync: PU = None
        self.xQuadTrans: PU = None
        self.xQuadSubtrans: PU = None
        self.tpdo: Seconds = None
        self.tppdo: Seconds = None
        self.tpqo: Seconds = None
        self.tppqo: Seconds = None
        self.tc: Seconds = None

class VsConverter(ACDCConverter):
    """RDF class VsConverter."""

    __slots__ = ('VSCDynamics',)

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'VsConverter') -> None:
        """Initialize an RDF-defined CGMES object."""
        ACDCConverter.__init__(self, rdfid=rdfid, tpe=tpe)
        self.VSCDynamics: VSCDynamics = None

class WindTurbineType4aIEC(WindTurbineType4IEC):
    """RDF class WindTurbineType4aIEC."""

    __slots__ = ('WindContPType4aIEC', 'WindGenType4IEC')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindTurbineType4aIEC') -> None:
        """Initialize an RDF-defined CGMES object."""
        WindTurbineType4IEC.__init__(self, rdfid=rdfid, tpe=tpe)
        self.WindContPType4aIEC: WindContPType4aIEC = None
        self.WindGenType4IEC: WindGenType4IEC = None

class WindTurbineType4bIEC(WindTurbineType4IEC):
    """RDF class WindTurbineType4bIEC."""

    __slots__ = ('WindContPType4bIEC', 'WindGenType4IEC', 'WindMechIEC')

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'WindTurbineType4bIEC') -> None:
        """Initialize an RDF-defined CGMES object."""
        WindTurbineType4IEC.__init__(self, rdfid=rdfid, tpe=tpe)
        self.WindContPType4bIEC: WindContPType4bIEC = None
        self.WindGenType4IEC: WindGenType4IEC = None
        self.WindMechIEC: WindMechIEC = None

class PowerElectronicsConnection(RegulatingCondEq):
    """RDF class PowerElectronicsConnection."""

    __slots__ = ('WindTurbineType3or4Dynamics',)

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'PowerElectronicsConnection') -> None:
        """Initialize an RDF-defined CGMES object."""
        RegulatingCondEq.__init__(self, rdfid=rdfid, tpe=tpe)
        self.WindTurbineType3or4Dynamics: WindTurbineType3or4Dynamics = None

class RotatingMachine(RegulatingCondEq):
    """RDF class RotatingMachine."""

    __slots__ = ()

    def __init__(self, rdfid: str = "", tpe: str = 'RotatingMachine') -> None:
        """Initialize an RDF-defined CGMES object."""
        RegulatingCondEq.__init__(self, rdfid=rdfid, tpe=tpe)
        pass

class StaticVarCompensator(RegulatingCondEq):
    """RDF class StaticVarCompensator."""

    __slots__ = ('StaticVarCompensatorDynamics',)

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'StaticVarCompensator') -> None:
        """Initialize an RDF-defined CGMES object."""
        RegulatingCondEq.__init__(self, rdfid=rdfid, tpe=tpe)
        self.StaticVarCompensatorDynamics: StaticVarCompensatorDynamics = None

class AsynchronousMachine(RotatingMachine):
    """RDF class AsynchronousMachine."""

    __slots__ = ('AsynchronousMachineDynamics',)

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'AsynchronousMachine') -> None:
        """Initialize an RDF-defined CGMES object."""
        RotatingMachine.__init__(self, rdfid=rdfid, tpe=tpe)
        self.AsynchronousMachineDynamics: AsynchronousMachineDynamics = None

class SynchronousMachine(RotatingMachine):
    """RDF class SynchronousMachine."""

    __slots__ = ('SynchronousMachineDynamics',)

    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = "", tpe: str = 'SynchronousMachine') -> None:
        """Initialize an RDF-defined CGMES object."""
        RotatingMachine.__init__(self, rdfid=rdfid, tpe=tpe)
        self.SynchronousMachineDynamics: SynchronousMachineDynamics = None

ActivePower.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='value', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='multiplier', class_type=UnitMultiplier, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='unit', class_type=UnitSymbol, profiles=[CgmesProfileType.DY]),
)

AngleDegrees.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='value', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='unit', class_type=UnitSymbol, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='multiplier', class_type=UnitMultiplier, profiles=[CgmesProfileType.DY]),
)

ApparentPower.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='value', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='multiplier', class_type=UnitMultiplier, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='unit', class_type=UnitSymbol, profiles=[CgmesProfileType.DY]),
)

Area.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='value', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='unit', class_type=UnitSymbol, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='multiplier', class_type=UnitMultiplier, profiles=[CgmesProfileType.DY]),
)

Frequency.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='value', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='unit', class_type=UnitSymbol, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='multiplier', class_type=UnitMultiplier, profiles=[CgmesProfileType.DY]),
)

Length.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='value', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='unit', class_type=UnitSymbol, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='multiplier', class_type=UnitMultiplier, profiles=[CgmesProfileType.DY]),
)

PU.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='value', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='unit', class_type=UnitSymbol, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='multiplier', class_type=UnitMultiplier, profiles=[CgmesProfileType.DY]),
)

Seconds.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='value', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='unit', class_type=UnitSymbol, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='multiplier', class_type=UnitMultiplier, profiles=[CgmesProfileType.DY]),
)

Temperature.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='multiplier', class_type=UnitMultiplier, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='unit', class_type=UnitSymbol, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='value', class_type=float, profiles=[CgmesProfileType.DY]),
)

VolumeFlowRate.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='multiplier', class_type=UnitMultiplier, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='unit', class_type=UnitSymbol, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='value', class_type=float, profiles=[CgmesProfileType.DY]),
)

Terminal.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='ConductingEquipment', class_type=ConductingEquipment, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='RemoteInputSignal', class_type=RemoteInputSignal, profiles=[CgmesProfileType.DY]),
)

ConductingEquipment.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='Terminals', class_type=Terminal, profiles=[CgmesProfileType.DY]),
)

IdentifiedObject.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='description', class_type=str, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='mRID', class_type=str, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='name', class_type=str, profiles=[CgmesProfileType.DY]),
)

RemoteInputSignal.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='Terminal', class_type=Terminal, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='remoteSignalType', class_type=RemoteSignalKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='DiscontinuousExcitationControlDynamics', class_type=DiscontinuousExcitationControlDynamics, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindTurbineType1or2Dynamics', class_type=WindTurbineType1or2Dynamics, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='PowerSystemStabilizerDynamics', class_type=PowerSystemStabilizerDynamics, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='UnderexcitationLimiterDynamics', class_type=UnderexcitationLimiterDynamics, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='PFVArControllerType1Dynamics', class_type=PFVArControllerType1Dynamics, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='VoltageCompensatorDynamics', class_type=VoltageCompensatorDynamics, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindPlantDynamics', class_type=WindPlantDynamics, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindTurbineType3or4Dynamics', class_type=WindTurbineType3or4Dynamics, profiles=[CgmesProfileType.DY]),
)

AsynchronousMachineDynamics.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='AsynchronousMachine', class_type=AsynchronousMachine, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='TurbineGovernorDynamics', class_type=TurbineGovernorDynamics, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='MechanicalLoadDynamics', class_type=MechanicalLoadDynamics, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindTurbineType1or2Dynamics', class_type=WindTurbineType1or2Dynamics, profiles=[CgmesProfileType.DY]),
)

AsynchronousMachine.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='AsynchronousMachineDynamics', class_type=AsynchronousMachineDynamics, profiles=[CgmesProfileType.DY]),
)

LoadDynamics.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='EnergyConsumer', class_type=EnergyConsumer, profiles=[CgmesProfileType.DY]),
)

EnergyConsumer.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='LoadDynamics', class_type=LoadDynamics, profiles=[CgmesProfileType.DY]),
)

WindTurbineType3or4Dynamics.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='PowerElectronicsConnection', class_type=PowerElectronicsConnection, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='RemoteInputSignal', class_type=RemoteInputSignal, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindPlantDynamics', class_type=WindPlantDynamics, profiles=[CgmesProfileType.DY]),
)

PowerElectronicsConnection.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='WindTurbineType3or4Dynamics', class_type=WindTurbineType3or4Dynamics, profiles=[CgmesProfileType.DY]),
)

StaticVarCompensatorDynamics.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='StaticVarCompensator', class_type=StaticVarCompensator, profiles=[CgmesProfileType.DY]),
)

StaticVarCompensator.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='StaticVarCompensatorDynamics', class_type=StaticVarCompensatorDynamics, profiles=[CgmesProfileType.DY]),
)

SynchronousMachineDynamics.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='SynchronousMachine', class_type=SynchronousMachine, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='CrossCompoundTurbineGovernorDyanmics', class_type=CrossCompoundTurbineGovernorDynamics, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='CrossCompoundTurbineGovernorDynamics', class_type=CrossCompoundTurbineGovernorDynamics, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='MechanicalLoadDynamics', class_type=MechanicalLoadDynamics, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ExcitationSystemDynamics', class_type=ExcitationSystemDynamics, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='TurbineGovernorDynamics', class_type=TurbineGovernorDynamics, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='GenICompensationForGenJ', class_type=GenICompensationForGenJ, profiles=[CgmesProfileType.DY]),
)


SynchronousMachine.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='SynchronousMachineDynamics', class_type=SynchronousMachineDynamics, profiles=[CgmesProfileType.DY]),
)

CSCDynamics.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='CSConverter', class_type=CsConverter, profiles=[CgmesProfileType.DY]),
)

CsConverter.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='CSCDynamics', class_type=CSCDynamics, profiles=[CgmesProfileType.DY]),
)

VSCDynamics.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='VsConverter', class_type=VsConverter, profiles=[CgmesProfileType.DY]),
)

VsConverter.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='VSCDynamics', class_type=VSCDynamics, profiles=[CgmesProfileType.DY]),
)

DiscontinuousExcitationControlDynamics.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='RemoteInputSignal', class_type=RemoteInputSignal, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ExcitationSystemDynamics', class_type=ExcitationSystemDynamics, profiles=[CgmesProfileType.DY]),
)

WindTurbineType1or2Dynamics.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='RemoteInputSignal', class_type=RemoteInputSignal, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='AsynchronousMachineDynamics', class_type=AsynchronousMachineDynamics, profiles=[CgmesProfileType.DY]),
)

PowerSystemStabilizerDynamics.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='RemoteInputSignal', class_type=RemoteInputSignal, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ExcitationSystemDynamics', class_type=ExcitationSystemDynamics, profiles=[CgmesProfileType.DY]),
)

UnderexcitationLimiterDynamics.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='RemoteInputSignal', class_type=RemoteInputSignal, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ExcitationSystemDynamics', class_type=ExcitationSystemDynamics, profiles=[CgmesProfileType.DY]),
)

PFVArControllerType1Dynamics.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='RemoteInputSignal', class_type=RemoteInputSignal, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ExcitationSystemDynamics', class_type=ExcitationSystemDynamics, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='VoltageAdjusterDynamics', class_type=VoltageAdjusterDynamics, profiles=[CgmesProfileType.DY]),
)

VoltageCompensatorDynamics.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='RemoteInputSignal', class_type=RemoteInputSignal, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ExcitationSystemDynamics', class_type=ExcitationSystemDynamics, profiles=[CgmesProfileType.DY]),
)

WindPlantDynamics.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='RemoteInputSignal', class_type=RemoteInputSignal, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindTurbineType3or4Dynamics', class_type=WindTurbineType3or4Dynamics, profiles=[CgmesProfileType.DY]),
)

DynamicsFunctionBlock.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='enabled', class_type=bool, profiles=[CgmesProfileType.DY]),
)

RotatingMachineDynamics.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='damping', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='inertia', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='saturationFactor', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='saturationFactor120', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='statorLeakageReactance', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='statorResistance', class_type=PU, profiles=[CgmesProfileType.DY]),
)

CSCUserDefined.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='proprietary', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ProprietaryParameterDynamics', class_type=ProprietaryParameterDynamics, profiles=[CgmesProfileType.DY]),
)

ProprietaryParameterDynamics.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='CSCUserDefined', class_type=CSCUserDefined, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='SVCUserDefined', class_type=SVCUserDefined, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='VSCUserDefined', class_type=VSCUserDefined, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindPlantUserDefined', class_type=WindPlantUserDefined, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindType1or2UserDefined', class_type=WindType1or2UserDefined, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindType3or4UserDefined', class_type=WindType3or4UserDefined, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='SynchronousMachineUserDefined', class_type=SynchronousMachineUserDefined, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='AsynchronousMachineUserDefined', class_type=AsynchronousMachineUserDefined, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='TurbineGovernorUserDefined', class_type=TurbineGovernorUserDefined, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='TurbineLoadControllerUserDefined', class_type=TurbineLoadControllerUserDefined, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='MechanicalLoadUserDefined', class_type=MechanicalLoadUserDefined, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ExcitationSystemUserDefined', class_type=ExcitationSystemUserDefined, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='OverexcitationLimiterUserDefined', class_type=OverexcitationLimiterUserDefined, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='UnderexcitationLimiterUserDefined', class_type=UnderexcitationLimiterUserDefined, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='PowerSystemStabilizerUserDefined', class_type=PowerSystemStabilizerUserDefined, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='DiscontinuousExcitationControlUserDefined', class_type=DiscontinuousExcitationControlUserDefined, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='PFVArControllerType1UserDefined', class_type=PFVArControllerType1UserDefined, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='VoltageAdjusterUserDefined', class_type=VoltageAdjusterUserDefined, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='PFVArControllerType2UserDefined', class_type=PFVArControllerType2UserDefined, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='VoltageCompensatorUserDefined', class_type=VoltageCompensatorUserDefined, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='LoadUserDefined', class_type=LoadUserDefined, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='parameterNumber', class_type=int, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='booleanParameterValue', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='integerParameterValue', class_type=int, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='floatParameterValue', class_type=float, profiles=[CgmesProfileType.DY]),
)

SVCUserDefined.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='proprietary', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ProprietaryParameterDynamics', class_type=ProprietaryParameterDynamics, profiles=[CgmesProfileType.DY]),
)

VSCUserDefined.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='proprietary', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ProprietaryParameterDynamics', class_type=ProprietaryParameterDynamics, profiles=[CgmesProfileType.DY]),
)

WindPlantUserDefined.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='proprietary', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ProprietaryParameterDynamics', class_type=ProprietaryParameterDynamics, profiles=[CgmesProfileType.DY]),
)

WindType1or2UserDefined.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='proprietary', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ProprietaryParameterDynamics', class_type=ProprietaryParameterDynamics, profiles=[CgmesProfileType.DY]),
)

WindType3or4UserDefined.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='proprietary', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ProprietaryParameterDynamics', class_type=ProprietaryParameterDynamics, profiles=[CgmesProfileType.DY]),
)

SynchronousMachineUserDefined.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='proprietary', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ProprietaryParameterDynamics', class_type=ProprietaryParameterDynamics, profiles=[CgmesProfileType.DY]),
)

AsynchronousMachineUserDefined.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='proprietary', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ProprietaryParameterDynamics', class_type=ProprietaryParameterDynamics, profiles=[CgmesProfileType.DY]),
)

TurbineGovernorUserDefined.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='proprietary', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ProprietaryParameterDynamics', class_type=ProprietaryParameterDynamics, profiles=[CgmesProfileType.DY]),
)

TurbineLoadControllerUserDefined.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='proprietary', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ProprietaryParameterDynamics', class_type=ProprietaryParameterDynamics, profiles=[CgmesProfileType.DY]),
)

MechanicalLoadUserDefined.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='proprietary', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ProprietaryParameterDynamics', class_type=ProprietaryParameterDynamics, profiles=[CgmesProfileType.DY]),
)

ExcitationSystemUserDefined.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='proprietary', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ProprietaryParameterDynamics', class_type=ProprietaryParameterDynamics, profiles=[CgmesProfileType.DY]),
)

OverexcitationLimiterUserDefined.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='proprietary', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ProprietaryParameterDynamics', class_type=ProprietaryParameterDynamics, profiles=[CgmesProfileType.DY]),
)

UnderexcitationLimiterUserDefined.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='proprietary', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ProprietaryParameterDynamics', class_type=ProprietaryParameterDynamics, profiles=[CgmesProfileType.DY]),
)

PowerSystemStabilizerUserDefined.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='proprietary', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ProprietaryParameterDynamics', class_type=ProprietaryParameterDynamics, profiles=[CgmesProfileType.DY]),
)

DiscontinuousExcitationControlUserDefined.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='proprietary', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ProprietaryParameterDynamics', class_type=ProprietaryParameterDynamics, profiles=[CgmesProfileType.DY]),
)

PFVArControllerType1UserDefined.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='proprietary', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ProprietaryParameterDynamics', class_type=ProprietaryParameterDynamics, profiles=[CgmesProfileType.DY]),
)

VoltageAdjusterUserDefined.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='proprietary', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ProprietaryParameterDynamics', class_type=ProprietaryParameterDynamics, profiles=[CgmesProfileType.DY]),
)

PFVArControllerType2UserDefined.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='proprietary', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ProprietaryParameterDynamics', class_type=ProprietaryParameterDynamics, profiles=[CgmesProfileType.DY]),
)

VoltageCompensatorUserDefined.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='proprietary', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ProprietaryParameterDynamics', class_type=ProprietaryParameterDynamics, profiles=[CgmesProfileType.DY]),
)

LoadUserDefined.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='proprietary', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ProprietaryParameterDynamics', class_type=ProprietaryParameterDynamics, profiles=[CgmesProfileType.DY]),
)

CrossCompoundTurbineGovernorDynamics.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='HighPressureSynchronousMachineDynamics', class_type=SynchronousMachineDynamics, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='LowPressureSynchronousMachineDynamics', class_type=SynchronousMachineDynamics, profiles=[CgmesProfileType.DY]),
)

MechanicalLoadDynamics.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='SynchronousMachineDynamics', class_type=SynchronousMachineDynamics, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='AsynchronousMachineDynamics', class_type=AsynchronousMachineDynamics, profiles=[CgmesProfileType.DY]),
)

ExcitationSystemDynamics.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='SynchronousMachineDynamics', class_type=SynchronousMachineDynamics, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='VoltageCompensatorDynamics', class_type=VoltageCompensatorDynamics, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='OverexcitationLimiterDynamics', class_type=OverexcitationLimiterDynamics, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='PFVArControllerType2Dynamics', class_type=PFVArControllerType2Dynamics, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='DiscontinuousExcitationControlDynamics', class_type=DiscontinuousExcitationControlDynamics, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='PowerSystemStabilizerDynamics', class_type=PowerSystemStabilizerDynamics, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='UnderexcitationLimiterDynamics', class_type=UnderexcitationLimiterDynamics, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='PFVArControllerType1Dynamics', class_type=PFVArControllerType1Dynamics, profiles=[CgmesProfileType.DY]),
)

TurbineGovernorDynamics.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='SynchronousMachineDynamics', class_type=SynchronousMachineDynamics, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='AsynchronousMachineDynamics', class_type=AsynchronousMachineDynamics, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='TurbineLoadControllerDynamics', class_type=TurbineLoadControllerDynamics, profiles=[CgmesProfileType.DY]),
)

GenICompensationForGenJ.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='SynchronousMachineDynamics', class_type=SynchronousMachineDynamics, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='VcompIEEEType2', class_type=VCompIEEEType2, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rcij', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='xcij', class_type=PU, profiles=[CgmesProfileType.DY]),
)

SynchronousMachineDetailed.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='saturationFactorQAxis', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='saturationFactor120QAxis', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efdBaseRatio', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ifdBaseType', class_type=IfdBaseKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ifdBaseValue', class_type=float, profiles=[CgmesProfileType.DY]),
)

SynchronousMachineTimeConstantReactance.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='rotorType', class_type=RotorKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='modelType', class_type=SynchronousMachineModelKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ks', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='xDirectSync', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='xDirectTrans', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='xDirectSubtrans', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='xQuadSync', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='xQuadTrans', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='xQuadSubtrans', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpdo', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tppdo', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpqo', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tppqo', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
)

SynchronousMachineEquivalentCircuit.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='xad', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rfd', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='xfd', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='r1d', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='x1d', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='xf1d', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='xaq', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='r1q', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='x1q', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='r2q', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='x2q', class_type=PU, profiles=[CgmesProfileType.DY]),
)

AsynchronousMachineTimeConstantReactance.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='xs', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='xp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='xpp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpo', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tppo', class_type=Seconds, profiles=[CgmesProfileType.DY]),
)

AsynchronousMachineEquivalentCircuit.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='xm', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rr1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='xlr1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rr2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='xlr2', class_type=PU, profiles=[CgmesProfileType.DY]),
)

TurbineLoadControllerDynamics.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='TurbineGovernorDynamics', class_type=TurbineGovernorDynamics, profiles=[CgmesProfileType.DY]),
)

GovHydroIEEE0.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='mwbase', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmin', class_type=PU, profiles=[CgmesProfileType.DY]),
)

GovHydroIEEE2.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='mwbase', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tg', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uo', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uc', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rperm', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rtemp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tr', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tw', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kturb', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='aturb', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='bturb', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv6', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv6', class_type=PU, profiles=[CgmesProfileType.DY]),
)

GovSteamIEEE1.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='mwbase', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uo', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uc', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k2', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t5', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k3', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k4', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t6', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k5', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k6', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t7', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k7', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k8', class_type=float, profiles=[CgmesProfileType.DY]),
)

GovCT1.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='mwbase', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='r', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rselect', class_type=DroopSignalFeedbackKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpelec', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='maxerr', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='minerr', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kpgov', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kigov', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kdgov', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tdgov', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tact', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kturb', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='wfnl', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='wfspd', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='teng', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tfload', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kpload', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kiload', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ldref', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dm', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ropen', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rclose', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kimw', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='aset', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='db', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tsa', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tsb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rup', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rdown', class_type=PU, profiles=[CgmesProfileType.DY]),
)

GovCT2.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='mwbase', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='r', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rselect', class_type=DroopSignalFeedbackKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpelec', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='maxerr', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='minerr', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kpgov', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kigov', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kdgov', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tdgov', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tact', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kturb', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='wfnl', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='wfspd', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='teng', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tfload', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kpload', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kiload', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ldref', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dm', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ropen', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rclose', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kimw', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='aset', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='db', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tsa', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tsb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rup', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rdown', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='prate', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='flim1', class_type=Frequency, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='plim1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='flim2', class_type=Frequency, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='plim2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='flim3', class_type=Frequency, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='plim3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='flim4', class_type=Frequency, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='plim4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='flim5', class_type=Frequency, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='plim5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='flim6', class_type=Frequency, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='plim6', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='flim7', class_type=Frequency, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='plim7', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='flim8', class_type=Frequency, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='plim8', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='flim9', class_type=Frequency, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='plim9', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='flim10', class_type=Frequency, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='plim10', class_type=PU, profiles=[CgmesProfileType.DY]),
)

GovGAST.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='mwbase', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='r', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='at', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kt', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dturb', class_type=PU, profiles=[CgmesProfileType.DY]),
)

GovGAST1.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='mwbase', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='r', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='lmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kt', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='fidle', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rmax', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='loadinc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tltr', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ltrate', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='b', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='db1', class_type=Frequency, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='eps', class_type=Frequency, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='db2', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv6', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv6', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t5', class_type=Seconds, profiles=[CgmesProfileType.DY]),
)

GovGAST2.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='mwbase', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='w', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='x', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='y', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='z', class_type=int, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='etd', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tcd', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='trate', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ecr', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='b', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='c', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tt', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t5', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='af1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='bf1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='af2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='bf2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='cf2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tr', class_type=Temperature, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k6', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Temperature, profiles=[CgmesProfileType.DY]),
)

GovGAST3.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='bp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tg', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rcmx', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rcmn', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ky', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ty', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tac', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kac', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='bca', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kca', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dtc', class_type=Temperature, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tsi', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ksi', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ttc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tfen', class_type=Temperature, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='td', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tt', class_type=Temperature, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='mxef', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='mnef', class_type=PU, profiles=[CgmesProfileType.DY]),
)

GovGAST4.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='bp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tv', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tcm', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ktm', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tm', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rymx', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rymn', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='mxef', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='mnef', class_type=PU, profiles=[CgmesProfileType.DY]),
)

GovGASTWD.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='mwbase', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kdroop', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ki', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kd', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='etd', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tcd', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='trate', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ecr', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='b', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='c', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tt', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t5', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='af1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='bf1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='af2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='bf2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='cf2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tr', class_type=Temperature, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k6', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Temperature, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='td', class_type=Seconds, profiles=[CgmesProfileType.DY]),
)

GovHydro1.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='mwbase', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rperm', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rtemp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tr', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tg', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='velm', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tw', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='at', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dturb', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='qnl', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='hdam', class_type=PU, profiles=[CgmesProfileType.DY]),
)

GovHydro2.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='mwbase', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tg', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uo', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uc', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rperm', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rtemp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tr', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tw', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kturb', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='aturb', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='bturb', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='db1', class_type=Frequency, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='eps', class_type=Frequency, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='db2', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv6', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv6', class_type=PU, profiles=[CgmesProfileType.DY]),
)

GovHydro3.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='mwbase', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='governorControl', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rgate', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='relec', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='td', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='velop', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='velcl', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ki', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kg', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tt', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='db1', class_type=Frequency, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='eps', class_type=Frequency, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='db2', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tw', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='at', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dturb', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='qnl', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='h0', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv6', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv6', class_type=PU, profiles=[CgmesProfileType.DY]),
)

GovHydro4.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='mwbase', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tg', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uo', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uc', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rperm', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rtemp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tr', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tw', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='at', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dturb', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='hdam', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='qnl', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='db1', class_type=Frequency, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='eps', class_type=Frequency, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='db2', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv0', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv0', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='bgv0', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='bgv1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='bgv2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='bgv3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='bgv4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='bgv5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='bmax', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tblade', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='model', class_type=GovHydro4ModelKind, profiles=[CgmesProfileType.DY]),
)

GovHydroDD.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='mwbase', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='r', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='td', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='velop', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='velcl', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ki', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kg', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tturb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='aturb', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='bturb', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tt', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='db1', class_type=Frequency, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='eps', class_type=Frequency, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='db2', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv6', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv6', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='inputSignal', class_type=bool, profiles=[CgmesProfileType.DY]),
)

GovHydroFrancis.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='am', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='av0', class_type=Area, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='av1', class_type=Area, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='bp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='db1', class_type=Frequency, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='etamax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='governorControl', class_type=FrancisGovernorControlKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='h1', class_type=Length, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='h2', class_type=Length, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='hn', class_type=Length, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kg', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kt', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='qc0', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='qn', class_type=VolumeFlowRate, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='td', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ts', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='twnc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='twng', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tx', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='va', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='valvmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='valvmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vc', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='waterTunnelSurgeChamberSimulation', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='zsfc', class_type=Length, profiles=[CgmesProfileType.DY]),
)

GovHydroPelton.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='av0', class_type=Area, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='av1', class_type=Area, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='bp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='db1', class_type=Frequency, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='db2', class_type=Frequency, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='h1', class_type=Length, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='h2', class_type=Length, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='hn', class_type=Length, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kg', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='qc0', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='qn', class_type=VolumeFlowRate, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='simplifiedPelton', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='staticCompensating', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ts', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tv', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='twnc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='twng', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tx', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='va', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='valvmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='valvmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vav', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vc', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vcv', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='waterTunnelSurgeChamberSimulation', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='zsfc', class_type=Length, profiles=[CgmesProfileType.DY]),
)

GovHydroPID.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='mwbase', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='r', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='td', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='velop', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='velcl', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kd', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ki', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kg', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tturb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='aturb', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='bturb', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tt', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='db1', class_type=Frequency, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='inputSignal', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='eps', class_type=Frequency, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='db2', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv6', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv6', class_type=PU, profiles=[CgmesProfileType.DY]),
)

GovHydroPID2.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='mwbase', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='treg', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rperm', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ki', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kd', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='velmax', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='velmin', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tw', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='d', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='g0', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='g1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='p1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='g2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='p2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='p3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='atw', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='feedbackSignal', class_type=bool, profiles=[CgmesProfileType.DY]),
)

GovHydroR.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='mwbase', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='r', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='td', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t5', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t6', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t7', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t8', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='velop', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='velcl', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ki', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kg', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tt', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='inputSignal', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='db1', class_type=Frequency, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='eps', class_type=Frequency, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='db2', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tw', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='at', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dturb', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='qnl', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='h0', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv6', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv6', class_type=PU, profiles=[CgmesProfileType.DY]),
)

GovHydroWEH.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='mwbase', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rpg', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rpp', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpe', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ki', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kd', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='td', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tdv', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tg', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gtmxop', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gtmxcl', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dturb', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tw', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='db', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dpv', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dicn', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='feedbackSignal', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='fl1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='fl2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='fl3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='fl4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='fl5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='fp1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='fp2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='fp3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='fp4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='fp5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='fp6', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='fp7', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='fp8', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='fp9', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='fp10', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmss1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmss2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmss3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmss4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmss5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmss6', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmss7', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmss8', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmss9', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmss10', class_type=PU, profiles=[CgmesProfileType.DY]),
)

GovHydroWPID.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='mwbase', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='treg', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='reg', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ki', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kd', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='velmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='velmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gatmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gatmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tw', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='d', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv3', class_type=PU, profiles=[CgmesProfileType.DY]),
)

GovSteam0.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='mwbase', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='r', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dt', class_type=PU, profiles=[CgmesProfileType.DY]),
)

GovSteam1.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='mwbase', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uo', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uc', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k2', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t5', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k3', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k4', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t6', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k5', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k6', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t7', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k7', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k8', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='db1', class_type=Frequency, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='eps', class_type=Frequency, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='sdb1', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='sdb2', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='db2', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='valve', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv6', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv6', class_type=PU, profiles=[CgmesProfileType.DY]),
)

GovSteam2.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='k', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dbf', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='mxef', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='mnef', class_type=PU, profiles=[CgmesProfileType.DY]),
)

GovSteamBB.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='fcut', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ks', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kls', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kg', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tn', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kd', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='td', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t5', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t6', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='peflag', class_type=bool, profiles=[CgmesProfileType.DY]),
)

GovSteamCC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='mwbase', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmaxhp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rhp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1hp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3hp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t4hp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t5hp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='fhp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dhp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmaxlp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rlp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1lp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3lp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t4lp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t5lp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='flp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dlp', class_type=PU, profiles=[CgmesProfileType.DY]),
)

GovSteamEU.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='mwbase', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ke', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tip', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tdp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tfp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kfcor', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='db1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='wfmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='wfmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ten', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tw', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='komegacor', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='db2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='wwmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='wwmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='wmax1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='wmax2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tvhp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='cho', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='chc', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='hhpmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tvip', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='cio', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='cic', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='simx', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='thp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='trh', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tlp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='prhmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='khp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='klp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
)

GovSteamFV2.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='mwbase', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dt', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tt', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='r', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ti', class_type=Seconds, profiles=[CgmesProfileType.DY]),
)

GovSteamFV3.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='mwbase', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uo', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uc', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t5', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t6', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='prmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='gv6', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pgv6', class_type=PU, profiles=[CgmesProfileType.DY]),
)

GovSteamFV4.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='kf1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='lps', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='lpi', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='mxef', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='mnef', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='crmx', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='crmn', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kpt', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kit', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rvgmx', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rvgmn', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='svmx', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='svmn', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='srmx', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='srmn', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kpp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kip', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rsmimx', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rsmimn', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kmp1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kmp2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='srsmp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ty', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='yhpmx', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='yhpmn', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tam', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tcm', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ympmx', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ympmn', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='y', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='thp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='trh', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tmp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='khp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pr1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pr2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='psmn', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kpc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kic', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kdc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tdc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='cpsmx', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='cpsmn', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='krc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tv', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ksh', class_type=PU, profiles=[CgmesProfileType.DY]),
)

GovSteamSGO.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='mwbase', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t5', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t6', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmin', class_type=Seconds, profiles=[CgmesProfileType.DY]),
)

TurbLCFB1.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='mwbase', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='speedReferenceGovernor', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='db', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='emax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='fb', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ki', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='fbf', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pbf', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpelec', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='irmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmwset', class_type=ActivePower, profiles=[CgmesProfileType.DY]),
)

MechLoad1.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='a', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='b', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='d', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='e', class_type=float, profiles=[CgmesProfileType.DY]),
)

OverexcitationLimiterDynamics.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='ExcitationSystemDynamics', class_type=ExcitationSystemDynamics, profiles=[CgmesProfileType.DY]),
)

PFVArControllerType2Dynamics.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='ExcitationSystemDynamics', class_type=ExcitationSystemDynamics, profiles=[CgmesProfileType.DY]),
)

ExcIEEEAC1A.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vamax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vamin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kd', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ke', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ve1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seve1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ve2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seve2', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
)

ExcIEEEAC2A.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vamax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vamin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kb', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vfemax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kh', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kd', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ke', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ve1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seve1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ve2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seve2', class_type=float, profiles=[CgmesProfileType.DY]),
)

ExcIEEEAC3A.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vamax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vamin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vemin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kr', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kn', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efdn', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kd', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ke', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vfemax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ve1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seve1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ve2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seve2', class_type=float, profiles=[CgmesProfileType.DY]),
)

ExcIEEEAC4A.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='vimax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vimin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kc', class_type=PU, profiles=[CgmesProfileType.DY]),
)

ExcIEEEAC5A.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ke', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efd1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seefd1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efd2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seefd2', class_type=float, profiles=[CgmesProfileType.DY]),
)

ExcIEEEAC6A.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tk', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vamax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vamin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kh', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tj', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='th', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vfelim', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vhmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kd', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ke', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ve1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seve1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ve2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seve2', class_type=float, profiles=[CgmesProfileType.DY]),
)

ExcIEEEAC7B.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='kpr', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kir', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kdr', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tdr', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kpa', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kia', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vamax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vamin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kl', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vfemax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vemin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ke', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kd', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ve1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seve1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ve2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seve2', class_type=float, profiles=[CgmesProfileType.DY]),
)

ExcIEEEAC8B.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='kpr', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kir', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kdr', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tdr', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vfemax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vemin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ke', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kd', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ve1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seve1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ve2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seve2', class_type=float, profiles=[CgmesProfileType.DY]),
)

ExcIEEEDC1A.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ke', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efd1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seefd1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efd2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seefd2', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uelin', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='exclim', class_type=bool, profiles=[CgmesProfileType.DY]),
)

ExcIEEEDC2A.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='efd1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efd2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='exclim', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ke', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seefd1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seefd2', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uelin', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
)

ExcIEEEDC3A.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='trh', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kv', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ke', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efd1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seefd1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efd2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seefd2', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='exclim', class_type=bool, profiles=[CgmesProfileType.DY]),
)

ExcIEEEDC4B.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ki', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kd', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='td', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ke', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efd1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seefd1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efd2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seefd2', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vemin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='oelin', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uelin', class_type=bool, profiles=[CgmesProfileType.DY]),
)

ExcIEEEST1A.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='ilr', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='klr', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pssin', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uelin', class_type=ExcIEEEST1AUELselectorKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vamax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vamin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vimax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vimin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
)

ExcIEEEST2A.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ke', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ki', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efdmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uelin', class_type=bool, profiles=[CgmesProfileType.DY]),
)

ExcIEEEST3A.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='vimax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vimin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='km', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tm', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vmmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vmmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kg', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='thetap', class_type=AngleDegrees, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ki', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='xl', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vbmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vgmax', class_type=PU, profiles=[CgmesProfileType.DY]),
)

ExcIEEEST4B.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='kpr', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kir', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kpm', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kim', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vmmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vmmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kg', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='thetap', class_type=AngleDegrees, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ki', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='xl', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vbmax', class_type=PU, profiles=[CgmesProfileType.DY]),
)

ExcIEEEST5B.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='kr', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='toc1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tob1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='toc2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tob2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tuc1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tub1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tuc2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tub2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
)

ExcIEEEST6B.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='ilr', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kci', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kff', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kg', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kia', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='klr', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='km', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kpa', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='oelin', class_type=ExcST6BOELselectorKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tg', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vamax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vamin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
)

ExcIEEEST7B.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='kh', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kia', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kl', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kpa', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='oelin', class_type=ExcST7BOELselectorKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tg', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tia', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uelin', class_type=ExcST7BUELselectorKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
)

ExcAC1A.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vamax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vamin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ks', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kd', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ke', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ve1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seve1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ve2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seve2', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='hvlvgates', class_type=bool, profiles=[CgmesProfileType.DY]),
)

ExcAC2A.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vamax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vamin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kb', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kb1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vfemax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kh', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kl', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vlr', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kl1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ks', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kd', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ke', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ve1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seve1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ve2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seve2', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='hvgate', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='lvgate', class_type=bool, profiles=[CgmesProfileType.DY]),
)

ExcAC3A.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ka', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vamax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vamin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vemin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kr', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kn', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efdn', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kd', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ke', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='klv', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ks', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vfemax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ve1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seve1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ve2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seve2', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vlv', class_type=PU, profiles=[CgmesProfileType.DY]),
)

ExcAC4A.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='vimax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vimin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kc', class_type=PU, profiles=[CgmesProfileType.DY]),
)

ExcAC5A.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ks', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ke', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efd1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seefd1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efd2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seefd2', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a', class_type=float, profiles=[CgmesProfileType.DY]),
)

ExcAC6A.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ks', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tk', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vamax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vamin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kh', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tj', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='th', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vfelim', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vhmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kd', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ke', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ve1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seve1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ve2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seve2', class_type=float, profiles=[CgmesProfileType.DY]),
)

ExcAC8B.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='inlim', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kd', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kdr', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ke', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kir', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kpr', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ks', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pidlim', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seve1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seve2', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tdr', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='telim', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ve1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ve2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vemin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vfemax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vimax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vimin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vpidmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vpidmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vtmult', class_type=bool, profiles=[CgmesProfileType.DY]),
)

ExcANS.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='k3', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k2', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kce', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='blint', class_type=int, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kvfif', class_type=int, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ifmn', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ifmx', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmn', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmx', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='krvecc', class_type=int, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
)

ExcAVR1.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='ka', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmn', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmx', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='e1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='se1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='e2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='se2', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
)

ExcAVR2.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='ka', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmn', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmx', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='e1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='se1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='e2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='se2', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
)

ExcAVR3.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='ka', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmn', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmx', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='e1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='se1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='e2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='se2', class_type=float, profiles=[CgmesProfileType.DY]),
)

ExcAVR4.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='ka', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmn', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmx', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ke', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vfmx', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vfmn', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kif', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tif', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1if', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='imul', class_type=bool, profiles=[CgmesProfileType.DY]),
)

ExcAVR5.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rex', class_type=PU, profiles=[CgmesProfileType.DY]),
)

ExcAVR7.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='k1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vmax1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vmin1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vmax3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vmin3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a6', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t5', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t6', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vmax5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vmin5', class_type=PU, profiles=[CgmesProfileType.DY]),
)

ExcBBC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efdmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efdmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='xe', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='switch', class_type=bool, profiles=[CgmesProfileType.DY]),
)

ExcCZ.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='kp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ke', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efdmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efdmin', class_type=PU, profiles=[CgmesProfileType.DY]),
)

ExcDC1A.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ks', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ke', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efd1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seefd1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efd2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seefd2', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='exclim', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efdmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efdmax', class_type=PU, profiles=[CgmesProfileType.DY]),
)

ExcDC2A.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ks', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ke', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efd1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seefd1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efd2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seefd2', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='exclim', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vtlim', class_type=bool, profiles=[CgmesProfileType.DY]),
)

ExcDC3A.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='trh', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ks', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kr', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kv', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ke', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efd1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seefd1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efd2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seefd2', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='exclim', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efdmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efdmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efdlim', class_type=bool, profiles=[CgmesProfileType.DY]),
)

ExcDC3A1.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ki', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vbmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='exclim', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ke', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vb1max', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vblim', class_type=bool, profiles=[CgmesProfileType.DY]),
)

ExcELIN1.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='tfi', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tnu', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vpu', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vpi', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vpnf', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dpnf', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tsw', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='xe', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ks1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ks2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ts1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ts2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='smax', class_type=PU, profiles=[CgmesProfileType.DY]),
)

ExcELIN2.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='k1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k1ec', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kd1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pid1max', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ti1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='iefmax2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ketb', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='upmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='upmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='xp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ke2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ve1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seve1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ve2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='seve2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tr4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ti3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ti4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='iefmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='iefmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efdbas', class_type=PU, profiles=[CgmesProfileType.DY]),
)

ExcHU.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='tr', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='imin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='imax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ae', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='emin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='emax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ki', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ai', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ti', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='atr', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ke', class_type=float, profiles=[CgmesProfileType.DY]),
)

ExcNI.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='busFedSelector', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tr', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='r', class_type=PU, profiles=[CgmesProfileType.DY]),
)

ExcOEX3T.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t5', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t6', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kd', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ke', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='e1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='see1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='e2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='see2', class_type=PU, profiles=[CgmesProfileType.DY]),
)

ExcPIC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vr1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vr2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efdmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efdmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ke', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='e1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='se1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='e2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='se2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ki', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kc', class_type=PU, profiles=[CgmesProfileType.DY]),
)

ExcREXS.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='e1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='e2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='fbf', class_type=ExcREXSFeedbackSignalKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='flimf', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kd', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ke', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kefd', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kh', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kii', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kip', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ks', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kvi', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kvp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kvphz', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='nvphz', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='se1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='se2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vcmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vfmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vfmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vimax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='xc', class_type=PU, profiles=[CgmesProfileType.DY]),
)

ExcRQB.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='ki0', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ki1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='klir', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ucmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ucmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='lus', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='klus', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='mesu', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t4m', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='lsat', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
)

ExcSCRX.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='tatb', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='emin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='emax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='cswitch', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rcrfd', class_type=float, profiles=[CgmesProfileType.DY]),
)

ExcSEXS.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='tatb', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='emin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='emax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efdmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efdmax', class_type=PU, profiles=[CgmesProfileType.DY]),
)

ExcSK.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='efdmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efdmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='emax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='emin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kce', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kd', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kgob', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kqi', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kqob', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kqp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='nq', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='qconoff', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='qz', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='remote', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='sbase', class_type=ApparentPower, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ti', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tr', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uimax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uimin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='urmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='urmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vtmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vtmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='yp', class_type=PU, profiles=[CgmesProfileType.DY]),
)

ExcST1A.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='vimax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vimin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vamax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vamin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ilr', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='klr', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='xe', class_type=PU, profiles=[CgmesProfileType.DY]),
)

ExcST2A.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='ka', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ke', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ki', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efdmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uelin', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
)

ExcST3A.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='vimax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vimin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kj', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efdmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='km', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tm', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kg', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='thetap', class_type=AngleDegrees, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ki', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='xl', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vbmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vgmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ks', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ks1', class_type=PU, profiles=[CgmesProfileType.DY]),
)

ExcST4B.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='kpr', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kir', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kpm', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kim', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vmmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vmmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kg', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='thetap', class_type=AngleDegrees, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ki', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='xl', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vbmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vgmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uel', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='lvgate', class_type=bool, profiles=[CgmesProfileType.DY]),
)

ExcST6B.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='ilr', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k1', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kcl', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kff', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kg', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kia', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='klr', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='km', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kpa', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kvd', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='oelin', class_type=ExcST6BOELselectorKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tg', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ts', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tvd', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vamax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vamin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vilim', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vimax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vimin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vmult', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='xc', class_type=PU, profiles=[CgmesProfileType.DY]),
)

ExcST7B.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='kh', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kia', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kl', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kpa', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='oelin', class_type=ExcST7BOELselectorKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tg', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tia', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ts', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uelin', class_type=ExcST7BUELselectorKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
)

OverexcLimIEEE.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='itfpu', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ifdmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ifdlim', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='hyst', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kcd', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kramp', class_type=float, profiles=[CgmesProfileType.DY]),
)

OverexcLim2.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='koi', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='voimax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='voimin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ifdlim', class_type=PU, profiles=[CgmesProfileType.DY]),
)

OverexcLimX1.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='efdrated', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efd1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efd2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efd3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efddes', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kmx', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vlow', class_type=PU, profiles=[CgmesProfileType.DY]),
)

OverexcLimX2.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='m', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efdrated', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efd1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efd2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efd3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efddes', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kmx', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vlow', class_type=PU, profiles=[CgmesProfileType.DY]),
)

UnderexcLimIEEE1.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='kur', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kuc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kuf', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vurmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vucmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kui', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kul', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vuimax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vuimin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tu1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tu2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tu3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tu4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vulmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vulmin', class_type=PU, profiles=[CgmesProfileType.DY]),
)

UnderexcLimIEEE2.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='tuv', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tup', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tuq', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kui', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kul', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vuimax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vuimin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kuf', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kfb', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tul', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tu1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tu2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tu3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tu4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vulmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vulmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='p0', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='q0', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='p1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='q1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='p2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='q2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='p3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='q3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='p4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='q4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='p5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='q5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='p6', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='q6', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='p7', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='q7', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='p8', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='q8', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='p9', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='q9', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='p10', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='q10', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k2', class_type=float, profiles=[CgmesProfileType.DY]),
)

UnderexcLim2Simplified.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='q0', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='q1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='p0', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='p1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kui', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vuimin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vuimax', class_type=PU, profiles=[CgmesProfileType.DY]),
)

UnderexcLimX1.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='kf2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='km', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tm', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='melmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k', class_type=PU, profiles=[CgmesProfileType.DY]),
)

UnderexcLimX2.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='kf2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='km', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tm', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='melmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='qo', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='r', class_type=PU, profiles=[CgmesProfileType.DY]),
)

PssIEEE1A.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='inputSignalType', class_type=InputSignalKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t5', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t6', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ks', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
)

PssIEEE2B.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='inputSignal1Type', class_type=InputSignalKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='inputSignal2Type', class_type=InputSignalKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vsi1max', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vsi1min', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tw1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tw2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vsi2max', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vsi2min', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tw3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tw4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t6', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t7', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t8', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t9', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t10', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t11', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ks1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ks2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ks3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='n', class_type=int, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='m', class_type=int, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vstmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vstmin', class_type=PU, profiles=[CgmesProfileType.DY]),
)

PssIEEE3B.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='inputSignal1Type', class_type=InputSignalKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='inputSignal2Type', class_type=InputSignalKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tw1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tw2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tw3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ks1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ks2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a6', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a7', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a8', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vstmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vstmin', class_type=PU, profiles=[CgmesProfileType.DY]),
)

PssIEEE4B.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='bwh1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='bwh2', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='bwl1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='bwl2', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kh', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kh1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kh11', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kh17', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kh2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ki', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ki1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ki11', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ki17', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ki2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kl', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kl1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kl11', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kl17', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kl2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='omeganh1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='omeganh2', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='omeganl1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='omeganl2', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='th1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='th10', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='th11', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='th12', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='th2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='th3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='th4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='th5', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='th6', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='th7', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='th8', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='th9', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ti1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ti10', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ti11', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ti12', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ti2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ti3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ti4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ti5', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ti6', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ti7', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ti8', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ti9', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tl1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tl10', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tl11', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tl12', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tl2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tl3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tl4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tl5', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tl6', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tl7', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tl8', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tl9', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vhmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vhmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vimax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vimin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vlmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vlmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vstmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vstmin', class_type=PU, profiles=[CgmesProfileType.DY]),
)

Pss1.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='kw', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kpe', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ks', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vsmn', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vsmx', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpe', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t5', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t6', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t7', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t8', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t9', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t10', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vadat', class_type=bool, profiles=[CgmesProfileType.DY]),
)

Pss1A.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='inputSignalType', class_type=InputSignalKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t5', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t6', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ks', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vrmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vcu', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vcl', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a6', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a7', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a8', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kd', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tdelay', class_type=Seconds, profiles=[CgmesProfileType.DY]),
)

Pss2B.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='inputSignal1Type', class_type=InputSignalKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='inputSignal2Type', class_type=InputSignalKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vsi1max', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vsi1min', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tw1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tw2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vsi2max', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vsi2min', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tw3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tw4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t6', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t7', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t8', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t9', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t10', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t11', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ks1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ks2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ks3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ks4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='n', class_type=int, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='m', class_type=int, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vstmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vstmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
)

Pss2ST.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='inputSignal1Type', class_type=InputSignalKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='inputSignal2Type', class_type=InputSignalKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t5', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t6', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t7', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t8', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t9', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t10', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='lsmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='lsmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vcu', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vcl', class_type=PU, profiles=[CgmesProfileType.DY]),
)

Pss5.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='kpe', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kf', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='isfreq', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kpss', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ctw2', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tw1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tw2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tl1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tl2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tl3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tl4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vsmn', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vsmx', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpe', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmm', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='deadband', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vadat', class_type=bool, profiles=[CgmesProfileType.DY]),
)

PssELIN2.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='ts1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ts2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ts3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ts4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ts5', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ts6', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ks1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ks2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ppss', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='apss', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='psslim', class_type=PU, profiles=[CgmesProfileType.DY]),
)

PssPTIST1.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='m', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dtf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dtc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dtp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
)

PssPTIST3.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='m', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dtf', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dtc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dtp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t5', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t6', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a0', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='b0', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='b1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='b2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='a5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='b3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='b4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='b5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='athres', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dl', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='al', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='lthres', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='isw', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='nav', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ncl', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ncr', class_type=float, profiles=[CgmesProfileType.DY]),
)

PssRQB.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='ki2', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ki3', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ki4', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t4m', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tomd', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tomsl', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t4mom', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='sibv', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kdpm', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t4f', class_type=Seconds, profiles=[CgmesProfileType.DY]),
)

PssSB4.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='tt', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kx', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tx2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tx1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tb', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='td', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='te', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vsmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vsmin', class_type=PU, profiles=[CgmesProfileType.DY]),
)

PssSH.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='k', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k0', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='td', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vsmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vsmin', class_type=PU, profiles=[CgmesProfileType.DY]),
)

PssSK.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='k1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t5', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t6', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vsmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vsmin', class_type=PU, profiles=[CgmesProfileType.DY]),
)

PssSTAB2A.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='k2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k3', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k4', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k5', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t5', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='hlim', class_type=PU, profiles=[CgmesProfileType.DY]),
)

PssWECC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='inputSignal1Type', class_type=InputSignalKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='inputSignal2Type', class_type=InputSignalKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='k2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t4', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t5', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t6', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t7', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t8', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t10', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t9', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vsmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vsmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vcu', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vcl', class_type=PU, profiles=[CgmesProfileType.DY]),
)

DiscExcContIEEEDEC1A.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='vtlmt', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vomax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vomin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ketl', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vtc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='val', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='esc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kan', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tan', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tw5', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vsmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vsmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='td', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tl1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tl2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vtm', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vtn', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vanmax', class_type=PU, profiles=[CgmesProfileType.DY]),
)

DiscExcContIEEEDEC2A.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='vk', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='td1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='td2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vdmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vdmax', class_type=PU, profiles=[CgmesProfileType.DY]),
)

DiscExcContIEEEDEC3A.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='vtmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tdr', class_type=Seconds, profiles=[CgmesProfileType.DY]),
)

VoltageAdjusterDynamics.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='PFVArControllerType1Dynamics', class_type=PFVArControllerType1Dynamics, profiles=[CgmesProfileType.DY]),
)

PFVArType1IEEEPFController.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='ovex', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpfc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vitmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vpf', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vpfcbw', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vpfref', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vvtmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vvtmin', class_type=PU, profiles=[CgmesProfileType.DY]),
)

PFVArType1IEEEVArController.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='tvarc', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vvar', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vvarcbw', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vvarref', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vvtmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vvtmin', class_type=PU, profiles=[CgmesProfileType.DY]),
)

VAdjIEEE.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='vadjf', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='adjslew', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vadjmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vadjmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='taon', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='taoff', class_type=Seconds, profiles=[CgmesProfileType.DY]),
)

PFVArType2IEEEPFController.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='pfref', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vref', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vclmt', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ki', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vs', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='exlon', class_type=bool, profiles=[CgmesProfileType.DY]),
)

PFVArType2IEEEVArController.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='qref', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vref', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vclmt', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ki', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vs', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='exlon', class_type=bool, profiles=[CgmesProfileType.DY]),
)

PFVArType2Common1.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='j', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ki', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='max', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ref', class_type=PU, profiles=[CgmesProfileType.DY]),
)

VCompIEEEType1.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='rc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='xc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tr', class_type=Seconds, profiles=[CgmesProfileType.DY]),
)

VCompIEEEType2.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='tr', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(
        property_name='GenICompensationForGenJ',
        class_type=GenICompensationForGenJ,
        profiles=[CgmesProfileType.DY],
        multiplicity='2..n',
    ),
)

WindGenTurbineType1aIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='WindAeroConstIEC', class_type=WindAeroConstIEC, profiles=[CgmesProfileType.DY]),
)

WindAeroConstIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='WindGenTurbineType1aIEC', class_type=WindGenTurbineType1aIEC, profiles=[CgmesProfileType.DY]),
)

WindAeroOneDimIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='ka', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='thetaomega', class_type=AngleDegrees, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindTurbineType3IEC', class_type=WindTurbineType3IEC, profiles=[CgmesProfileType.DY]),
)

WindTurbineType3IEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='WindAeroOneDimIEC', class_type=WindAeroOneDimIEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindAeroTwoDimIEC', class_type=WindAeroTwoDimIEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindContPitchAngleIEC', class_type=WindContPitchAngleIEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindContPType3IEC', class_type=WindContPType3IEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindGenType3IEC', class_type=WindGenType3IEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindMechIEC', class_type=WindMechIEC, profiles=[CgmesProfileType.DY]),
)

WindAeroTwoDimIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='dpomega', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dptheta', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dpv1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='omegazero', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pavail', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='thetazero', class_type=AngleDegrees, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='thetav2', class_type=AngleDegrees, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindTurbineType3IEC', class_type=WindTurbineType3IEC, profiles=[CgmesProfileType.DY]),
)

WindContCurrLimIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='imax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='imaxdip', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kpqu', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='mdfslim', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='mqpri', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tufiltcl', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='upqumax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindTurbineType3or4IEC', class_type=WindTurbineType3or4IEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindDynamicsLookupTable', class_type=WindDynamicsLookupTable, profiles=[CgmesProfileType.DY]),
)

WindTurbineType3or4IEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='WindContCurrLimIEC', class_type=WindContCurrLimIEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WIndContQIEC', class_type=WindContQIEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindContQLimIEC', class_type=WindContQLimIEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindContQPQULimIEC', class_type=WindContQPQULimIEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindProtectionIEC', class_type=WindProtectionIEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindRefFrameRotIEC', class_type=WindRefFrameRotIEC, profiles=[CgmesProfileType.DY]),
)

WindDynamicsLookupTable.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='WindContCurrLimIEC', class_type=WindContCurrLimIEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindContPType3IEC', class_type=WindContPType3IEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindContQPQULimIEC', class_type=WindContQPQULimIEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindContRotorRIEC', class_type=WindContRotorRIEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='input', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='lookupTableFunctionType', class_type=WindLookupTableFunctionKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='output', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='sequence', class_type=int, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindPlantFreqPcontrolIEC', class_type=WindPlantFreqPcontrolIEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindProtectionIEC', class_type=WindProtectionIEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindPlantReactiveControlIEC', class_type=WindPlantReactiveControlIEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindGenType3bIEC', class_type=WindGenType3bIEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindPitchContPowerIEC', class_type=WindPitchContPowerIEC, profiles=[CgmesProfileType.DY]),
)

WindContPitchAngleIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='dthetamax', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dthetamin', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kic', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kiomega', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kpc', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kpomega', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kpx', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='thetamax', class_type=AngleDegrees, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='thetamin', class_type=AngleDegrees, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ttheta', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindTurbineType3IEC', class_type=WindTurbineType3IEC, profiles=[CgmesProfileType.DY]),
)

WindContPType3IEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='dpmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dprefmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dprefmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dthetamax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dthetamaxuvrt', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kdtd', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kip', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kpp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='mpuvrt', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='omegaoffset', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pdtdmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tdvs', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='thetaemin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='thetauscale', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tomegafiltp3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpfiltp3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpord', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tufiltp3', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tomegaref', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='udvs', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='updip', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='omegadtd', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='zeta', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindTurbineType3IEC', class_type=WindTurbineType3IEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindDynamicsLookupTable', class_type=WindDynamicsLookupTable, profiles=[CgmesProfileType.DY]),
)

WindContPType4aIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='dpmaxp4a', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpordp4a', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tufiltp4a', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindTurbineType4aIEC', class_type=WindTurbineType4aIEC, profiles=[CgmesProfileType.DY]),
)

WindTurbineType4aIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='WindContPType4aIEC', class_type=WindContPType4aIEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindGenType4IEC', class_type=WindGenType4IEC, profiles=[CgmesProfileType.DY]),
)

WindContPType4bIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='dpmaxp4b', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpaero', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpordp4b', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tufiltp4b', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindTurbineType4bIEC', class_type=WindTurbineType4bIEC, profiles=[CgmesProfileType.DY]),
)

WindTurbineType4bIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='WindContPType4bIEC', class_type=WindContPType4bIEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindGenType4IEC', class_type=WindGenType4IEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindMechIEC', class_type=WindMechIEC, profiles=[CgmesProfileType.DY]),
)

WindContQIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='iqh1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='iqmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='iqmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='iqpost', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kiq', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kiu', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kpq', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kpu', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kqv', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpfiltq', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rdroop', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tufiltq', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpost', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tqord', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='udb1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='udb2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='umax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='umin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uqdip', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uref0', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='windQcontrolModesType', class_type=WindQcontrolModeKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='windUVRTQcontrolModesType', class_type=WindUVRTQcontrolModeKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='xdroop', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindTurbineType3or4IEC', class_type=WindTurbineType3or4IEC, profiles=[CgmesProfileType.DY]),
)

WindContQLimIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='qmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='qmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindTurbineType3or4IEC', class_type=WindTurbineType3or4IEC, profiles=[CgmesProfileType.DY]),
)

WindContQPQULimIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='tpfiltql', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tufiltql', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindTurbineType3or4IEC', class_type=WindTurbineType3or4IEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindDynamicsLookupTable', class_type=WindDynamicsLookupTable, profiles=[CgmesProfileType.DY]),
)

WindContRotorRIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='kirr', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='komegafilt', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kpfilt', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kprr', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tomegafiltrr', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpfiltrr', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindDynamicsLookupTable', class_type=WindDynamicsLookupTable, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindGenTurbineType2IEC', class_type=WindGenTurbineType2IEC, profiles=[CgmesProfileType.DY]),
)

WindGenTurbineType2IEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='WindContRotorRIEC', class_type=WindContRotorRIEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindPitchContPowerIEC', class_type=WindPitchContPowerIEC, profiles=[CgmesProfileType.DY]),
)

WindPlantFreqPcontrolIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='WindDynamicsLookupTable', class_type=WindDynamicsLookupTable, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dprefmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dprefmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dpwprefmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dpwprefmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='prefmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='prefmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kiwpp', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kiwppmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kiwppmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kpwpp', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kwppref', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpft', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpfv', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='twpffiltp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='twppfiltp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindPlantIEC', class_type=WindPlantIEC, profiles=[CgmesProfileType.DY]),
)

WindProtectionIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='WindDynamicsLookupTable', class_type=WindDynamicsLookupTable, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dfimax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='fover', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='funder', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='mzc', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tfma', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uover', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uunder', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindTurbineType3or4IEC', class_type=WindTurbineType3or4IEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindTurbineType1or2IEC', class_type=WindTurbineType1or2IEC, profiles=[CgmesProfileType.DY]),
)

WindPlantReactiveControlIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='WindDynamicsLookupTable', class_type=WindDynamicsLookupTable, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindPlantIEC', class_type=WindPlantIEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dxrefmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dxrefmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kiwpx', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kiwpxmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kiwpxmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kpwpx', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kwpqref', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kwpqu', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tuqfilt', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='twppfiltq', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='twpqfiltq', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='twpufiltq', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='txft', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='txfv', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uwpqdip', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='windPlantQcontrolModesType', class_type=WindPlantQcontrolModeKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='xrefmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='xrefmin', class_type=PU, profiles=[CgmesProfileType.DY]),
)

WindGenType3bIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='WindDynamicsLookupTable', class_type=WindDynamicsLookupTable, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='mwtcwp', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tg', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='two', class_type=Seconds, profiles=[CgmesProfileType.DY]),
)

WindPitchContPowerIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='WindDynamicsLookupTable', class_type=WindDynamicsLookupTable, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindGenTurbineType1bIEC', class_type=WindGenTurbineType1bIEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindGenTurbineType2IEC', class_type=WindGenTurbineType2IEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dpmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dpmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pset', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tr', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uuvrt', class_type=PU, profiles=[CgmesProfileType.DY]),
)

WindGenTurbineType1bIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='WindPitchContPowerIEC', class_type=WindPitchContPowerIEC, profiles=[CgmesProfileType.DY]),
)

WindGenType3aIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='kpc', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tic', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindTurbineType4IEC', class_type=WindTurbineType4IEC, profiles=[CgmesProfileType.DY]),
)

WindTurbineType4IEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='WindGenType3aIEC', class_type=WindGenType3aIEC, profiles=[CgmesProfileType.DY]),
)

WindGenType3IEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='dipmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='diqmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='xs', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindTurbineType3IEC', class_type=WindTurbineType3IEC, profiles=[CgmesProfileType.DY]),
)

WindGenType4IEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='dipmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='diqmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='diqmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tg', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindTurbineType4aIEC', class_type=WindTurbineType4aIEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindTurbineType4bIEC', class_type=WindTurbineType4bIEC, profiles=[CgmesProfileType.DY]),
)

WindMechIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='cdrt', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='hgen', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='hwtr', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kdrt', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindTurbineType3IEC', class_type=WindTurbineType3IEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindTurbineType1or2IEC', class_type=WindTurbineType1or2IEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindTurbineType4bIEC', class_type=WindTurbineType4bIEC, profiles=[CgmesProfileType.DY]),
)

WindTurbineType1or2IEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='WindMechIEC', class_type=WindMechIEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindProtectionIEC', class_type=WindProtectionIEC, profiles=[CgmesProfileType.DY]),
)

WindPlantIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='WindPlantFreqPcontrolIEC', class_type=WindPlantFreqPcontrolIEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindPlantReactiveControlIEC', class_type=WindPlantReactiveControlIEC, profiles=[CgmesProfileType.DY]),
)

WindRefFrameRotIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='tpll', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='upll1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='upll2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindTurbineType3or4IEC', class_type=WindTurbineType3or4IEC, profiles=[CgmesProfileType.DY]),
)

LoadComposite.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='epvs', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='epfs', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='eqvs', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='eqfs', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='epvd', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='epfd', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='eqvd', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='eqfd', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='lfac', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='h', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pfrac', class_type=float, profiles=[CgmesProfileType.DY]),
)

LoadGenericNonLinear.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='genericNonLinearLoadModelType', class_type=GenericNonLinearLoadModelKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tq', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ls', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='lt', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='bs', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='bt', class_type=float, profiles=[CgmesProfileType.DY]),
)

LoadMotor.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='LoadAggregate', class_type=LoadAggregate, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pfrac', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='lfac', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ls', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='lp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='lpp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ra', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpo', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tppo', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='h', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='d', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='vt', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tv', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tbkr', class_type=Seconds, profiles=[CgmesProfileType.DY]),
)

LoadAggregate.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='LoadMotor', class_type=LoadMotor, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='LoadStatic', class_type=LoadStatic, profiles=[CgmesProfileType.DY]),
)

LoadStatic.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='LoadAggregate', class_type=LoadAggregate, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='staticLoadModelType', class_type=StaticLoadModelKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kp1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kp2', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kp3', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kp4', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ep1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ep2', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ep3', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kpf', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kq1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kq2', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kq3', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kq4', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='eq1', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='eq2', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='eq3', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kqf', class_type=float, profiles=[CgmesProfileType.DY]),
)

DY_CLASS_NAMES: Tuple[str, ...] = (
    'ProprietaryParameterDynamics',
    'DynamicsFunctionBlock',
    'GenICompensationForGenJ',
    'LoadDynamics',
    'LoadMotor',
    'LoadStatic',
    'RemoteInputSignal',
    'WindAeroConstIEC',
    'WindAeroOneDimIEC',
    'WindAeroTwoDimIEC',
    'WindContCurrLimIEC',
    'WindContPType3IEC',
    'WindContPType4aIEC',
    'WindContPType4bIEC',
    'WindContPitchAngleIEC',
    'WindContQIEC',
    'WindContQLimIEC',
    'WindContQPQULimIEC',
    'WindContRotorRIEC',
    'WindDynamicsLookupTable',
    'WindGenType3IEC',
    'WindGenType4IEC',
    'WindMechIEC',
    'WindPitchContPowerIEC',
    'WindPlantFreqPcontrolIEC',
    'WindPlantReactiveControlIEC',
    'WindProtectionIEC',
    'WindRefFrameRotIEC',
    'CrossCompoundTurbineGovernorDynamics',
    'DiscontinuousExcitationControlDynamics',
    'ExcitationSystemDynamics',
    'HVDCDynamics',
    'LoadAggregate',
    'LoadComposite',
    'LoadGenericNonLinear',
    'LoadUserDefined',
    'MechanicalLoadDynamics',
    'OverexcitationLimiterDynamics',
    'PFVArControllerType1Dynamics',
    'PFVArControllerType2Dynamics',
    'PowerSystemStabilizerDynamics',
    'RotatingMachineDynamics',
    'StaticVarCompensatorDynamics',
    'TurbineGovernorDynamics',
    'TurbineLoadControllerDynamics',
    'UnderexcitationLimiterDynamics',
    'VoltageAdjusterDynamics',
    'VoltageCompensatorDynamics',
    'WindGenType3aIEC',
    'WindGenType3bIEC',
    'WindPlantDynamics',
    'WindTurbineType1or2Dynamics',
    'WindTurbineType3or4Dynamics',
    'AsynchronousMachineDynamics',
    'CSCDynamics',
    'DiscExcContIEEEDEC1A',
    'DiscExcContIEEEDEC2A',
    'DiscExcContIEEEDEC3A',
    'DiscontinuousExcitationControlUserDefined',
    'ExcAC1A',
    'ExcAC2A',
    'ExcAC3A',
    'ExcAC4A',
    'ExcAC5A',
    'ExcAC6A',
    'ExcAC8B',
    'ExcANS',
    'ExcAVR1',
    'ExcAVR2',
    'ExcAVR3',
    'ExcAVR4',
    'ExcAVR5',
    'ExcAVR7',
    'ExcBBC',
    'ExcCZ',
    'ExcDC1A',
    'ExcDC2A',
    'ExcDC3A',
    'ExcDC3A1',
    'ExcELIN1',
    'ExcELIN2',
    'ExcHU',
    'ExcIEEEAC1A',
    'ExcIEEEAC2A',
    'ExcIEEEAC3A',
    'ExcIEEEAC4A',
    'ExcIEEEAC5A',
    'ExcIEEEAC6A',
    'ExcIEEEAC7B',
    'ExcIEEEAC8B',
    'ExcIEEEDC1A',
    'ExcIEEEDC2A',
    'ExcIEEEDC3A',
    'ExcIEEEDC4B',
    'ExcIEEEST1A',
    'ExcIEEEST2A',
    'ExcIEEEST3A',
    'ExcIEEEST4B',
    'ExcIEEEST5B',
    'ExcIEEEST6B',
    'ExcIEEEST7B',
    'ExcNI',
    'ExcOEX3T',
    'ExcPIC',
    'ExcREXS',
    'ExcRQB',
    'ExcSCRX',
    'ExcSEXS',
    'ExcSK',
    'ExcST1A',
    'ExcST2A',
    'ExcST3A',
    'ExcST4B',
    'ExcST6B',
    'ExcST7B',
    'ExcitationSystemUserDefined',
    'GovCT1',
    'GovCT2',
    'GovGAST',
    'GovGAST1',
    'GovGAST2',
    'GovGAST3',
    'GovGAST4',
    'GovGASTWD',
    'GovHydro1',
    'GovHydro2',
    'GovHydro3',
    'GovHydro4',
    'GovHydroDD',
    'GovHydroFrancis',
    'GovHydroIEEE0',
    'GovHydroIEEE2',
    'GovHydroPID',
    'GovHydroPID2',
    'GovHydroPelton',
    'GovHydroR',
    'GovHydroWEH',
    'GovHydroWPID',
    'GovSteam0',
    'GovSteam1',
    'GovSteam2',
    'GovSteamBB',
    'GovSteamCC',
    'GovSteamEU',
    'GovSteamFV2',
    'GovSteamFV3',
    'GovSteamFV4',
    'GovSteamIEEE1',
    'GovSteamSGO',
    'MechLoad1',
    'MechanicalLoadUserDefined',
    'OverexcLim2',
    'OverexcLimIEEE',
    'OverexcLimX1',
    'OverexcLimX2',
    'OverexcitationLimiterUserDefined',
    'PFVArControllerType1UserDefined',
    'PFVArControllerType2UserDefined',
    'PFVArType1IEEEPFController',
    'PFVArType1IEEEVArController',
    'PFVArType2Common1',
    'PFVArType2IEEEPFController',
    'PFVArType2IEEEVArController',
    'PowerSystemStabilizerUserDefined',
    'Pss1',
    'Pss1A',
    'Pss2B',
    'Pss2ST',
    'Pss5',
    'PssELIN2',
    'PssIEEE1A',
    'PssIEEE2B',
    'PssIEEE3B',
    'PssIEEE4B',
    'PssPTIST1',
    'PssPTIST3',
    'PssRQB',
    'PssSB4',
    'PssSH',
    'PssSK',
    'PssSTAB2A',
    'PssWECC',
    'SVCUserDefined',
    'SynchronousMachineDynamics',
    'TurbLCFB1',
    'TurbineGovernorUserDefined',
    'TurbineLoadControllerUserDefined',
    'UnderexcLim2Simplified',
    'UnderexcLimIEEE1',
    'UnderexcLimIEEE2',
    'UnderexcLimX1',
    'UnderexcLimX2',
    'UnderexcitationLimiterUserDefined',
    'VAdjIEEE',
    'VCompIEEEType1',
    'VCompIEEEType2',
    'VSCDynamics',
    'VoltageAdjusterUserDefined',
    'VoltageCompensatorUserDefined',
    'WindPlantIEC',
    'WindPlantUserDefined',
    'WindTurbineType1or2IEC',
    'WindTurbineType3or4IEC',
    'WindType1or2UserDefined',
    'WindType3or4UserDefined',
    'AsynchronousMachineEquivalentCircuit',
    'AsynchronousMachineTimeConstantReactance',
    'AsynchronousMachineUserDefined',
    'CSCUserDefined',
    'SynchronousMachineDetailed',
    'SynchronousMachineSimplified',
    'SynchronousMachineUserDefined',
    'VSCUserDefined',
    'WindGenTurbineType1aIEC',
    'WindGenTurbineType1bIEC',
    'WindGenTurbineType2IEC',
    'WindTurbineType3IEC',
    'WindTurbineType4IEC',
    'EnergyConsumer',
    'SynchronousMachineEquivalentCircuit',
    'SynchronousMachineTimeConstantReactance',
    'WindTurbineType4aIEC',
    'WindTurbineType4bIEC',
    'PowerElectronicsConnection',
)

DY_CLASS_DICT: Dict[str, type[Base]] = {
    'ProprietaryParameterDynamics': ProprietaryParameterDynamics,
    'DynamicsFunctionBlock': DynamicsFunctionBlock,
    'GenICompensationForGenJ': GenICompensationForGenJ,
    'LoadDynamics': LoadDynamics,
    'LoadMotor': LoadMotor,
    'LoadStatic': LoadStatic,
    'RemoteInputSignal': RemoteInputSignal,
    'WindAeroConstIEC': WindAeroConstIEC,
    'WindAeroOneDimIEC': WindAeroOneDimIEC,
    'WindAeroTwoDimIEC': WindAeroTwoDimIEC,
    'WindContCurrLimIEC': WindContCurrLimIEC,
    'WindContPType3IEC': WindContPType3IEC,
    'WindContPType4aIEC': WindContPType4aIEC,
    'WindContPType4bIEC': WindContPType4bIEC,
    'WindContPitchAngleIEC': WindContPitchAngleIEC,
    'WindContQIEC': WindContQIEC,
    'WindContQLimIEC': WindContQLimIEC,
    'WindContQPQULimIEC': WindContQPQULimIEC,
    'WindContRotorRIEC': WindContRotorRIEC,
    'WindDynamicsLookupTable': WindDynamicsLookupTable,
    'WindGenType3IEC': WindGenType3IEC,
    'WindGenType4IEC': WindGenType4IEC,
    'WindMechIEC': WindMechIEC,
    'WindPitchContPowerIEC': WindPitchContPowerIEC,
    'WindPlantFreqPcontrolIEC': WindPlantFreqPcontrolIEC,
    'WindPlantReactiveControlIEC': WindPlantReactiveControlIEC,
    'WindProtectionIEC': WindProtectionIEC,
    'WindRefFrameRotIEC': WindRefFrameRotIEC,
    'CrossCompoundTurbineGovernorDynamics': CrossCompoundTurbineGovernorDynamics,
    'DiscontinuousExcitationControlDynamics': DiscontinuousExcitationControlDynamics,
    'ExcitationSystemDynamics': ExcitationSystemDynamics,
    'HVDCDynamics': HVDCDynamics,
    'LoadAggregate': LoadAggregate,
    'LoadComposite': LoadComposite,
    'LoadGenericNonLinear': LoadGenericNonLinear,
    'LoadUserDefined': LoadUserDefined,
    'MechanicalLoadDynamics': MechanicalLoadDynamics,
    'OverexcitationLimiterDynamics': OverexcitationLimiterDynamics,
    'PFVArControllerType1Dynamics': PFVArControllerType1Dynamics,
    'PFVArControllerType2Dynamics': PFVArControllerType2Dynamics,
    'PowerSystemStabilizerDynamics': PowerSystemStabilizerDynamics,
    'RotatingMachineDynamics': RotatingMachineDynamics,
    'StaticVarCompensatorDynamics': StaticVarCompensatorDynamics,
    'TurbineGovernorDynamics': TurbineGovernorDynamics,
    'TurbineLoadControllerDynamics': TurbineLoadControllerDynamics,
    'UnderexcitationLimiterDynamics': UnderexcitationLimiterDynamics,
    'VoltageAdjusterDynamics': VoltageAdjusterDynamics,
    'VoltageCompensatorDynamics': VoltageCompensatorDynamics,
    'WindGenType3aIEC': WindGenType3aIEC,
    'WindGenType3bIEC': WindGenType3bIEC,
    'WindPlantDynamics': WindPlantDynamics,
    'WindTurbineType1or2Dynamics': WindTurbineType1or2Dynamics,
    'WindTurbineType3or4Dynamics': WindTurbineType3or4Dynamics,
    'AsynchronousMachineDynamics': AsynchronousMachineDynamics,
    'CSCDynamics': CSCDynamics,
    'DiscExcContIEEEDEC1A': DiscExcContIEEEDEC1A,
    'DiscExcContIEEEDEC2A': DiscExcContIEEEDEC2A,
    'DiscExcContIEEEDEC3A': DiscExcContIEEEDEC3A,
    'DiscontinuousExcitationControlUserDefined': DiscontinuousExcitationControlUserDefined,
    'ExcAC1A': ExcAC1A,
    'ExcAC2A': ExcAC2A,
    'ExcAC3A': ExcAC3A,
    'ExcAC4A': ExcAC4A,
    'ExcAC5A': ExcAC5A,
    'ExcAC6A': ExcAC6A,
    'ExcAC8B': ExcAC8B,
    'ExcANS': ExcANS,
    'ExcAVR1': ExcAVR1,
    'ExcAVR2': ExcAVR2,
    'ExcAVR3': ExcAVR3,
    'ExcAVR4': ExcAVR4,
    'ExcAVR5': ExcAVR5,
    'ExcAVR7': ExcAVR7,
    'ExcBBC': ExcBBC,
    'ExcCZ': ExcCZ,
    'ExcDC1A': ExcDC1A,
    'ExcDC2A': ExcDC2A,
    'ExcDC3A': ExcDC3A,
    'ExcDC3A1': ExcDC3A1,
    'ExcELIN1': ExcELIN1,
    'ExcELIN2': ExcELIN2,
    'ExcHU': ExcHU,
    'ExcIEEEAC1A': ExcIEEEAC1A,
    'ExcIEEEAC2A': ExcIEEEAC2A,
    'ExcIEEEAC3A': ExcIEEEAC3A,
    'ExcIEEEAC4A': ExcIEEEAC4A,
    'ExcIEEEAC5A': ExcIEEEAC5A,
    'ExcIEEEAC6A': ExcIEEEAC6A,
    'ExcIEEEAC7B': ExcIEEEAC7B,
    'ExcIEEEAC8B': ExcIEEEAC8B,
    'ExcIEEEDC1A': ExcIEEEDC1A,
    'ExcIEEEDC2A': ExcIEEEDC2A,
    'ExcIEEEDC3A': ExcIEEEDC3A,
    'ExcIEEEDC4B': ExcIEEEDC4B,
    'ExcIEEEST1A': ExcIEEEST1A,
    'ExcIEEEST2A': ExcIEEEST2A,
    'ExcIEEEST3A': ExcIEEEST3A,
    'ExcIEEEST4B': ExcIEEEST4B,
    'ExcIEEEST5B': ExcIEEEST5B,
    'ExcIEEEST6B': ExcIEEEST6B,
    'ExcIEEEST7B': ExcIEEEST7B,
    'ExcNI': ExcNI,
    'ExcOEX3T': ExcOEX3T,
    'ExcPIC': ExcPIC,
    'ExcREXS': ExcREXS,
    'ExcRQB': ExcRQB,
    'ExcSCRX': ExcSCRX,
    'ExcSEXS': ExcSEXS,
    'ExcSK': ExcSK,
    'ExcST1A': ExcST1A,
    'ExcST2A': ExcST2A,
    'ExcST3A': ExcST3A,
    'ExcST4B': ExcST4B,
    'ExcST6B': ExcST6B,
    'ExcST7B': ExcST7B,
    'ExcitationSystemUserDefined': ExcitationSystemUserDefined,
    'GovCT1': GovCT1,
    'GovCT2': GovCT2,
    'GovGAST': GovGAST,
    'GovGAST1': GovGAST1,
    'GovGAST2': GovGAST2,
    'GovGAST3': GovGAST3,
    'GovGAST4': GovGAST4,
    'GovGASTWD': GovGASTWD,
    'GovHydro1': GovHydro1,
    'GovHydro2': GovHydro2,
    'GovHydro3': GovHydro3,
    'GovHydro4': GovHydro4,
    'GovHydroDD': GovHydroDD,
    'GovHydroFrancis': GovHydroFrancis,
    'GovHydroIEEE0': GovHydroIEEE0,
    'GovHydroIEEE2': GovHydroIEEE2,
    'GovHydroPID': GovHydroPID,
    'GovHydroPID2': GovHydroPID2,
    'GovHydroPelton': GovHydroPelton,
    'GovHydroR': GovHydroR,
    'GovHydroWEH': GovHydroWEH,
    'GovHydroWPID': GovHydroWPID,
    'GovSteam0': GovSteam0,
    'GovSteam1': GovSteam1,
    'GovSteam2': GovSteam2,
    'GovSteamBB': GovSteamBB,
    'GovSteamCC': GovSteamCC,
    'GovSteamEU': GovSteamEU,
    'GovSteamFV2': GovSteamFV2,
    'GovSteamFV3': GovSteamFV3,
    'GovSteamFV4': GovSteamFV4,
    'GovSteamIEEE1': GovSteamIEEE1,
    'GovSteamSGO': GovSteamSGO,
    'MechLoad1': MechLoad1,
    'MechanicalLoadUserDefined': MechanicalLoadUserDefined,
    'OverexcLim2': OverexcLim2,
    'OverexcLimIEEE': OverexcLimIEEE,
    'OverexcLimX1': OverexcLimX1,
    'OverexcLimX2': OverexcLimX2,
    'OverexcitationLimiterUserDefined': OverexcitationLimiterUserDefined,
    'PFVArControllerType1UserDefined': PFVArControllerType1UserDefined,
    'PFVArControllerType2UserDefined': PFVArControllerType2UserDefined,
    'PFVArType1IEEEPFController': PFVArType1IEEEPFController,
    'PFVArType1IEEEVArController': PFVArType1IEEEVArController,
    'PFVArType2Common1': PFVArType2Common1,
    'PFVArType2IEEEPFController': PFVArType2IEEEPFController,
    'PFVArType2IEEEVArController': PFVArType2IEEEVArController,
    'PowerSystemStabilizerUserDefined': PowerSystemStabilizerUserDefined,
    'Pss1': Pss1,
    'Pss1A': Pss1A,
    'Pss2B': Pss2B,
    'Pss2ST': Pss2ST,
    'Pss5': Pss5,
    'PssELIN2': PssELIN2,
    'PssIEEE1A': PssIEEE1A,
    'PssIEEE2B': PssIEEE2B,
    'PssIEEE3B': PssIEEE3B,
    'PssIEEE4B': PssIEEE4B,
    'PssPTIST1': PssPTIST1,
    'PssPTIST3': PssPTIST3,
    'PssRQB': PssRQB,
    'PssSB4': PssSB4,
    'PssSH': PssSH,
    'PssSK': PssSK,
    'PssSTAB2A': PssSTAB2A,
    'PssWECC': PssWECC,
    'SVCUserDefined': SVCUserDefined,
    'SynchronousMachineDynamics': SynchronousMachineDynamics,
    'TurbLCFB1': TurbLCFB1,
    'TurbineGovernorUserDefined': TurbineGovernorUserDefined,
    'TurbineLoadControllerUserDefined': TurbineLoadControllerUserDefined,
    'UnderexcLim2Simplified': UnderexcLim2Simplified,
    'UnderexcLimIEEE1': UnderexcLimIEEE1,
    'UnderexcLimIEEE2': UnderexcLimIEEE2,
    'UnderexcLimX1': UnderexcLimX1,
    'UnderexcLimX2': UnderexcLimX2,
    'UnderexcitationLimiterUserDefined': UnderexcitationLimiterUserDefined,
    'VAdjIEEE': VAdjIEEE,
    'VCompIEEEType1': VCompIEEEType1,
    'VCompIEEEType2': VCompIEEEType2,
    'VSCDynamics': VSCDynamics,
    'VoltageAdjusterUserDefined': VoltageAdjusterUserDefined,
    'VoltageCompensatorUserDefined': VoltageCompensatorUserDefined,
    'WindPlantIEC': WindPlantIEC,
    'WindPlantUserDefined': WindPlantUserDefined,
    'WindTurbineType1or2IEC': WindTurbineType1or2IEC,
    'WindTurbineType3or4IEC': WindTurbineType3or4IEC,
    'WindType1or2UserDefined': WindType1or2UserDefined,
    'WindType3or4UserDefined': WindType3or4UserDefined,
    'AsynchronousMachineEquivalentCircuit': AsynchronousMachineEquivalentCircuit,
    'AsynchronousMachineTimeConstantReactance': AsynchronousMachineTimeConstantReactance,
    'AsynchronousMachineUserDefined': AsynchronousMachineUserDefined,
    'CSCUserDefined': CSCUserDefined,
    'SynchronousMachineDetailed': SynchronousMachineDetailed,
    'SynchronousMachineSimplified': SynchronousMachineSimplified,
    'SynchronousMachineTimeConstantReactance': SynchronousMachineTimeConstantReactance,
    'SynchronousMachineUserDefined': SynchronousMachineUserDefined,
    'VSCUserDefined': VSCUserDefined,
    'WindGenTurbineType1aIEC': WindGenTurbineType1aIEC,
    'WindGenTurbineType1bIEC': WindGenTurbineType1bIEC,
    'WindGenTurbineType2IEC': WindGenTurbineType2IEC,
    'WindTurbineType3IEC': WindTurbineType3IEC,
    'WindTurbineType4IEC': WindTurbineType4IEC,
    'EnergyConsumer': EnergyConsumer,
    'SynchronousMachineEquivalentCircuit': SynchronousMachineEquivalentCircuit,
    'SynchronousMachineTimeConstantReactance': SynchronousMachineTimeConstantReactance,
    'WindTurbineType4aIEC': WindTurbineType4aIEC,
    'WindTurbineType4bIEC': WindTurbineType4bIEC,
    'PowerElectronicsConnection': PowerElectronicsConnection,
}

DY_ASSOCIATION_INVERSES: Dict[Tuple[str, str], str] = {
    ('AsynchronousMachineDynamics', 'AsynchronousMachine'): 'AsynchronousMachineDynamics',
    ('CSCDynamics', 'CSConverter'): 'CSCDynamics',
    ('LoadDynamics', 'EnergyConsumer'): 'LoadDynamics',
    ('StaticVarCompensatorDynamics', 'StaticVarCompensator'): 'StaticVarCompensatorDynamics',
    ('SynchronousMachineDynamics', 'SynchronousMachine'): 'SynchronousMachineDynamics',
    ('VSCDynamics', 'VsConverter'): 'VSCDynamics',
    ('WindTurbineType3or4Dynamics', 'PowerElectronicsConnection'): 'WindTurbineType3or4Dynamics',
    ('WindTurbineType1or2Dynamics', 'AsynchronousMachineDynamics'): 'WindTurbineType1or2Dynamics',
}
