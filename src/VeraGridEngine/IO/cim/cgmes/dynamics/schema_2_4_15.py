# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""CGMES 2.4.15 Dynamics classes missing or different in the 2020 RDFS."""

from __future__ import annotations

from typing import Dict, List, Tuple

from VeraGridEngine.IO.cim.cgmes.base import Base
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import (
    CgmesProfileType,
    WindLVRTQcontrolModesKind,
    WindQcontrolModesKind,
)
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.energy_source import EnergySource
from VeraGridEngine.IO.cim.cgmes.dynamics.schema import (
    ActivePower,
    AsynchronousMachineDynamics,
    AngleDegrees,
    ExcitationSystemDynamics,
    DynamicsFunctionBlock,
    Frequency,
    GenericNonLinearLoadModelKind,
    GovSteamCC as GovSteamCC2020,
    GovSteamEU as GovSteamEU2020,
    GovSteamFV3 as GovSteamFV32020,
    IdentifiedObject,
    ProprietaryParameterDynamics as ProprietaryParameterDynamics2020,
    LoadDynamics,
    PU,
    RemoteInputSignal,
    RotatingMachineDynamics,
    Seconds,
    SynchronousMachine as SynchronousMachineEquipment,
    SynchronousMachineDetailed as SynchronousMachineDetailed2020,
    SynchronousMachineDynamics as SynchronousMachineDynamics2020,
    SynchronousMachineEquivalentCircuit as SynchronousMachineEquivalentCircuit2020,
    SynchronousMachineSimplified as SynchronousMachineSimplified2020,
    SynchronousMachineTimeConstantReactance as SynchronousMachineTimeConstantReactance2020,
    SynchronousMachineUserDefined as SynchronousMachineUserDefined2020,
    TurbineGovernorDynamics,
    WindContPitchAngleIEC as WindContPitchAngleIEC2020,
    WindContPType3IEC,
    WindDynamicsLookupTable,
    WindContCurrLimIEC,
    WindContQIEC,
    WindContRotorRIEC,
    WindPlantFreqPcontrolIEC,
    WindLookupTableFunctionKind,
    WindMechIEC,
    WindPlantIEC,
    WindPlantDynamics,
    WindProtectionIEC,
    WindTurbineType1or2IEC,
    WindTurbineType4aIEC,
    WindTurbineType4bIEC,
    WindType3or4UserDefined as WindType3or4UserDefined2020,
)


class SynchronousMachineDynamics(RotatingMachineDynamics):
    """Canonical 2.4.15 synchronous-machine associations, without later cross-compound links."""

    __slots__ = (
        'SynchronousMachine', 'MechanicalLoadDynamics', 'ExcitationSystemDynamics',
        'TurbineGovernorDynamics', 'GenICompensationForGenJ',
    )
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple(
        prop for prop in SynchronousMachineDynamics2020.LOCAL_CGMES_PROPERTIES
        if prop.property_name not in (
            'CrossCompoundTurbineGovernorDyanmics', 'CrossCompoundTurbineGovernorDynamics',
        )
    )

    def __init__(self, rdfid: str = '', tpe: str = 'SynchronousMachineDynamics') -> None:
        """Initialize only associations declared by the 2.4.15 RDF."""
        RotatingMachineDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.SynchronousMachine: SynchronousMachineEquipment | None = None
        self.MechanicalLoadDynamics: object | None = None
        self.ExcitationSystemDynamics: object | None = None
        self.TurbineGovernorDynamics: List[object] = list()
        self.GenICompensationForGenJ: List[object] = list()


class SynchronousMachineDetailed(SynchronousMachineDynamics):
    """Canonical 2.4.15 detailed synchronous-machine parameter carrier."""

    __slots__ = (
        'saturationFactorQAxis', 'saturationFactor120QAxis', 'efdBaseRatio',
        'ifdBaseType', 'ifdBaseValue',
    )
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = (
        SynchronousMachineDetailed2020.LOCAL_CGMES_PROPERTIES
    )

    def __init__(self, rdfid: str = '', tpe: str = 'SynchronousMachineDetailed') -> None:
        """Initialize the canonical detailed-machine scalar fields."""
        SynchronousMachineDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.saturationFactorQAxis: float | None = None
        self.saturationFactor120QAxis: float | None = None
        self.efdBaseRatio: float | None = None
        self.ifdBaseType: object | None = None
        self.ifdBaseValue: float | None = None


class SynchronousMachineSimplified(SynchronousMachineDynamics):
    """Canonical 2.4.15 simplified synchronous-machine model association."""

    __slots__ = tuple()
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = '', tpe: str = 'SynchronousMachineSimplified') -> None:
        """Initialize the inherited machine associations only."""
        SynchronousMachineDynamics.__init__(self, rdfid=rdfid, tpe=tpe)


class SynchronousMachineUserDefined(SynchronousMachineDynamics):
    """Canonical 2.4.15 proprietary synchronous-machine model record."""

    __slots__ = ('proprietary', 'ProprietaryParameterDynamics')
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = (
        SynchronousMachineUserDefined2020.LOCAL_CGMES_PROPERTIES
    )

    def __init__(self, rdfid: str = '', tpe: str = 'SynchronousMachineUserDefined') -> None:
        """Initialize the exact proprietary fields declared by the legacy RDF."""
        SynchronousMachineDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.proprietary: bool | None = None
        self.ProprietaryParameterDynamics: List[object] = list()


class SynchronousMachineEquivalentCircuit(SynchronousMachineDetailed):
    """Canonical 2.4.15 equivalent-circuit parameter record."""

    __slots__ = (
        'xad', 'rfd', 'xfd', 'r1d', 'x1d', 'xf1d', 'xaq', 'r1q', 'x1q', 'r2q', 'x2q',
    )
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = (
        SynchronousMachineEquivalentCircuit2020.LOCAL_CGMES_PROPERTIES
    )

    def __init__(self, rdfid: str = '', tpe: str = 'SynchronousMachineEquivalentCircuit') -> None:
        """Initialize the eleven canonical circuit coefficients."""
        SynchronousMachineDetailed.__init__(self, rdfid=rdfid, tpe=tpe)
        self.xad: PU | None = None
        self.rfd: PU | None = None
        self.xfd: PU | None = None
        self.r1d: PU | None = None
        self.x1d: PU | None = None
        self.xf1d: PU | None = None
        self.xaq: PU | None = None
        self.r1q: PU | None = None
        self.x1q: PU | None = None
        self.r2q: PU | None = None
        self.x2q: PU | None = None


class SynchronousMachineTimeConstantReactance(SynchronousMachineDetailed):
    """Canonical 2.4.15 time-constant/reactance parameter record."""

    __slots__ = (
        'rotorType', 'modelType', 'ks', 'xDirectSync', 'xDirectTrans', 'xDirectSubtrans',
        'xQuadSync', 'xQuadTrans', 'xQuadSubtrans', 'tpdo', 'tppdo', 'tpqo', 'tppqo', 'tc',
    )
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = (
        SynchronousMachineTimeConstantReactance2020.LOCAL_CGMES_PROPERTIES
    )

    def __init__(
            self,
            rdfid: str = '',
            tpe: str = 'SynchronousMachineTimeConstantReactance',
    ) -> None:
        """Initialize the exact legacy machine selector and parameter surface."""
        SynchronousMachineDetailed.__init__(self, rdfid=rdfid, tpe=tpe)
        self.rotorType: object | None = None
        self.modelType: object | None = None
        self.ks: float | None = None
        self.xDirectSync: PU | None = None
        self.xDirectTrans: PU | None = None
        self.xDirectSubtrans: PU | None = None
        self.xQuadSync: PU | None = None
        self.xQuadTrans: PU | None = None
        self.xQuadSubtrans: PU | None = None
        self.tpdo: Seconds | None = None
        self.tppdo: Seconds | None = None
        self.tpqo: Seconds | None = None
        self.tppqo: Seconds | None = None
        self.tc: Seconds | None = None


class GovSteamCC(TurbineGovernorDynamics):
    """Canonical 2.4.15 GovSteamCC with inherited RDF association fields."""

    __slots__ = (
        'mwbase', 'pmaxhp', 'rhp', 't1hp', 't3hp', 't4hp', 't5hp', 'fhp', 'dhp',
        'pmaxlp', 'rlp', 't1lp', 't3lp', 't4lp', 't5lp', 'flp', 'dlp',
    )
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = GovSteamCC2020.LOCAL_CGMES_PROPERTIES

    def __init__(self, rdfid: str = '', tpe: str = 'GovSteamCC') -> None:
        """Initialize scalar parameters without 2020-only high/low machine links."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.mwbase: ActivePower | None = None
        self.pmaxhp: PU | None = None
        self.rhp: PU | None = None
        self.t1hp: Seconds | None = None
        self.t3hp: Seconds | None = None
        self.t4hp: Seconds | None = None
        self.t5hp: Seconds | None = None
        self.fhp: PU | None = None
        self.dhp: PU | None = None
        self.pmaxlp: PU | None = None
        self.rlp: PU | None = None
        self.t1lp: Seconds | None = None
        self.t3lp: Seconds | None = None
        self.t4lp: Seconds | None = None
        self.t5lp: Seconds | None = None
        self.flp: PU | None = None
        self.dlp: PU | None = None


class ProprietaryParameterDynamics(Base):
    """Canonical 2.4.15 proprietary-parameter links without later converter types."""

    __slots__ = (
        'WindPlantUserDefined', 'WindType1or2UserDefined', 'WindType3or4UserDefined',
        'SynchronousMachineUserDefined', 'AsynchronousMachineUserDefined',
        'TurbineGovernorUserDefined', 'TurbineLoadControllerUserDefined',
        'MechanicalLoadUserDefined', 'ExcitationSystemUserDefined',
        'OverexcitationLimiterUserDefined', 'UnderexcitationLimiterUserDefined',
        'PowerSystemStabilizerUserDefined', 'DiscontinuousExcitationControlUserDefined',
        'PFVArControllerType1UserDefined', 'VoltageAdjusterUserDefined',
        'PFVArControllerType2UserDefined', 'VoltageCompensatorUserDefined',
        'LoadUserDefined', 'parameterNumber', 'booleanParameterValue',
        'integerParameterValue', 'floatParameterValue',
    )
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple(
        prop for prop in ProprietaryParameterDynamics2020.LOCAL_CGMES_PROPERTIES
        if prop.property_name not in ('CSCUserDefined', 'SVCUserDefined', 'VSCUserDefined')
    )

    def __init__(self, rdfid: str = '', tpe: str = 'ProprietaryParameterDynamics') -> None:
        """Initialize only user-defined model classes present in the 2.4.15 RDF."""
        Base.__init__(self, rdfid=rdfid, tpe=tpe)
        self.WindPlantUserDefined: object | None = None
        self.WindType1or2UserDefined: object | None = None
        self.WindType3or4UserDefined: object | None = None
        self.SynchronousMachineUserDefined: object | None = None
        self.AsynchronousMachineUserDefined: object | None = None
        self.TurbineGovernorUserDefined: object | None = None
        self.TurbineLoadControllerUserDefined: object | None = None
        self.MechanicalLoadUserDefined: object | None = None
        self.ExcitationSystemUserDefined: object | None = None
        self.OverexcitationLimiterUserDefined: object | None = None
        self.UnderexcitationLimiterUserDefined: object | None = None
        self.PowerSystemStabilizerUserDefined: object | None = None
        self.DiscontinuousExcitationControlUserDefined: object | None = None
        self.PFVArControllerType1UserDefined: object | None = None
        self.VoltageAdjusterUserDefined: object | None = None
        self.PFVArControllerType2UserDefined: object | None = None
        self.VoltageCompensatorUserDefined: object | None = None
        self.LoadUserDefined: object | None = None
        self.parameterNumber: int | None = None
        self.booleanParameterValue: bool | None = None
        self.integerParameterValue: int | None = None
        self.floatParameterValue: float | None = None


class GovHydro4(TurbineGovernorDynamics):
    """Canonical 2.4.15 GovHydro4 fields, including RDF property ``qn1``."""

    __slots__ = (
        'mwbase', 'tg', 'tp', 'uo', 'uc', 'gmax', 'gmin', 'rperm', 'rtemp',
        'tr', 'tw', 'at', 'dturb', 'hdam', 'qn1', 'db1', 'eps', 'db2',
        'gv0', 'pgv0', 'gv1', 'pgv1', 'gv2', 'pgv2', 'gv3', 'pgv3',
        'gv4', 'pgv4', 'gv5', 'pgv5', 'bgv0', 'bgv1', 'bgv2', 'bgv3',
        'bgv4', 'bgv5', 'bmax', 'tblade',
    )
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = '', tpe: str = 'GovHydro4') -> None:
        """Initialize the exact 2.4.15 class surface without 2020-only fields."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.mwbase: ActivePower | None = None
        self.tg: Seconds | None = None
        self.tp: Seconds | None = None
        self.uo: float | None = None
        self.uc: float | None = None
        self.gmax: PU | None = None
        self.gmin: PU | None = None
        self.rperm: Seconds | None = None
        self.rtemp: Seconds | None = None
        self.tr: Seconds | None = None
        self.tw: Seconds | None = None
        self.at: PU | None = None
        self.dturb: PU | None = None
        self.hdam: PU | None = None
        self.qn1: PU | None = None
        self.db1: Frequency | None = None
        self.eps: Frequency | None = None
        self.db2: ActivePower | None = None
        self.gv0: PU | None = None
        self.pgv0: PU | None = None
        self.gv1: PU | None = None
        self.pgv1: PU | None = None
        self.gv2: PU | None = None
        self.pgv2: PU | None = None
        self.gv3: PU | None = None
        self.pgv3: PU | None = None
        self.gv4: PU | None = None
        self.pgv4: PU | None = None
        self.gv5: PU | None = None
        self.pgv5: PU | None = None
        self.bgv0: PU | None = None
        self.bgv1: PU | None = None
        self.bgv2: PU | None = None
        self.bgv3: PU | None = None
        self.bgv4: PU | None = None
        self.bgv5: PU | None = None
        self.bmax: float | None = None
        self.tblade: Seconds | None = None


class LoadComposite(LoadDynamics):
    """Canonical 2.4.15 LoadComposite fields, including RDF property ``lfrac``."""

    __slots__ = (
        'epvs', 'epfs', 'eqvs', 'eqfs', 'epvd', 'epfd', 'eqvd', 'eqfd',
        'lfrac', 'h', 'pfrac',
    )
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = '', tpe: str = 'LoadComposite') -> None:
        """Initialize the exact 2.4.15 load-composite property surface."""
        LoadDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.epvs: float | None = None
        self.epfs: float | None = None
        self.eqvs: float | None = None
        self.eqfs: float | None = None
        self.epvd: float | None = None
        self.epfd: float | None = None
        self.eqvd: float | None = None
        self.eqfd: float | None = None
        self.lfrac: float | None = None
        self.h: Seconds | None = None
        self.pfrac: float | None = None


class LoadGenericNonLinear(LoadDynamics):
    """Canonical 2.4.15 GNLD fields, including legacy ``pt`` and ``qt``."""

    __slots__ = (
        'genericNonLinearLoadModelType', 'pt', 'qt', 'tp', 'tq', 'ls', 'lt', 'bs', 'bt',
    )
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = '', tpe: str = 'LoadGenericNonLinear') -> None:
        """Initialize the exact 2.4.15 generic nonlinear load property surface."""
        LoadDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.genericNonLinearLoadModelType: GenericNonLinearLoadModelKind | None = None
        self.pt: float | None = None
        self.qt: float | None = None
        self.tp: Seconds | None = None
        self.tq: Seconds | None = None
        self.ls: float | None = None
        self.lt: float | None = None
        self.bs: float | None = None
        self.bt: float | None = None


class GovSteamEU(TurbineGovernorDynamics):
    """Canonical 2.4.15 GovSteamEU fields, including ``kwcor``."""

    __slots__ = (
        'mwbase', 'tp', 'ke', 'tip', 'tdp', 'tfp', 'tf', 'kfcor', 'db1', 'wfmax',
        'wfmin', 'pmax', 'ten', 'tw', 'kwcor', 'db2', 'wwmax', 'wwmin', 'wmax1',
        'wmax2', 'tvhp', 'cho', 'chc', 'hhpmax', 'tvip', 'cio', 'cic', 'simx',
        'thp', 'trh', 'tlp', 'prhmax', 'khp', 'klp', 'tb',
    )
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = '', tpe: str = 'GovSteamEU') -> None:
        """Initialize the exact 2.4.15 turbine-governor parameter surface."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.mwbase: ActivePower | None = None
        self.tp: Seconds | None = None
        self.ke: PU | None = None
        self.tip: Seconds | None = None
        self.tdp: Seconds | None = None
        self.tfp: Seconds | None = None
        self.tf: Seconds | None = None
        self.kfcor: PU | None = None
        self.db1: PU | None = None
        self.wfmax: PU | None = None
        self.wfmin: PU | None = None
        self.pmax: PU | None = None
        self.ten: Seconds | None = None
        self.tw: Seconds | None = None
        self.kwcor: PU | None = None
        self.db2: PU | None = None
        self.wwmax: PU | None = None
        self.wwmin: PU | None = None
        self.wmax1: PU | None = None
        self.wmax2: PU | None = None
        self.tvhp: Seconds | None = None
        self.cho: float | None = None
        self.chc: float | None = None
        self.hhpmax: PU | None = None
        self.tvip: Seconds | None = None
        self.cio: PU | None = None
        self.cic: PU | None = None
        self.simx: PU | None = None
        self.thp: Seconds | None = None
        self.trh: Seconds | None = None
        self.tlp: Seconds | None = None
        self.prhmax: PU | None = None
        self.khp: PU | None = None
        self.klp: PU | None = None
        self.tb: Seconds | None = None


class GovSteamFV3(TurbineGovernorDynamics):
    """Canonical 2.4.15 GovSteamFV3 fields, without later curve parameters."""

    __slots__ = (
        'mwbase', 'k', 't1', 't2', 't3', 'uo', 'uc', 'pmax', 'pmin', 't4', 'k1',
        't5', 'k2', 't6', 'k3', 'ta', 'tb', 'tc', 'prmax',
    )
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = '', tpe: str = 'GovSteamFV3') -> None:
        """Initialize the exact 2.4.15 governor and fast-valving parameters."""
        TurbineGovernorDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.mwbase: ActivePower | None = None
        self.k: PU | None = None
        self.t1: Seconds | None = None
        self.t2: Seconds | None = None
        self.t3: Seconds | None = None
        self.uo: float | None = None
        self.uc: float | None = None
        self.pmax: PU | None = None
        self.pmin: PU | None = None
        self.t4: Seconds | None = None
        self.k1: PU | None = None
        self.t5: Seconds | None = None
        self.k2: PU | None = None
        self.t6: Seconds | None = None
        self.k3: PU | None = None
        self.ta: Seconds | None = None
        self.tb: Seconds | None = None
        self.tc: Seconds | None = None
        self.prmax: PU | None = None


LoadComposite.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='epvs', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='epfs', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='eqvs', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='eqfs', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='epvd', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='epfd', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='eqvd', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='eqfd', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='lfrac', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='h', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pfrac', class_type=float, profiles=[CgmesProfileType.DY]),
)

LoadGenericNonLinear.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='genericNonLinearLoadModelType', class_type=GenericNonLinearLoadModelKind, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pt', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='qt', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tp', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tq', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='ls', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='lt', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='bs', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='bt', class_type=float, profiles=[CgmesProfileType.DY]),
)

GovSteamEU.LOCAL_CGMES_PROPERTIES = tuple(
    CgmesProperty(
        property_name=(
            'kwcor' if cgmes_property.property_name == 'komegacor'
            else cgmes_property.property_name
        ),
        class_type=cgmes_property.class_type,
        profiles=cgmes_property.profiles,
    )
    for cgmes_property in GovSteamEU2020.LOCAL_CGMES_PROPERTIES
)

GovSteamFV3.LOCAL_CGMES_PROPERTIES = tuple(
    cgmes_property
    for cgmes_property in GovSteamFV32020.LOCAL_CGMES_PROPERTIES
    if not cgmes_property.property_name.startswith(('gv', 'pgv'))
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
    CgmesProperty(property_name='qn1', class_type=PU, profiles=[CgmesProfileType.DY]),
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
)


class ExcDC1A(ExcitationSystemDynamics):
    """Canonical 2.4.15 ExcDC1A fields, including the RDF spelling ``edfmax``."""

    __slots__ = (
        'ka', 'ks', 'ta', 'tb', 'tc', 'vrmax', 'vrmin', 'ke', 'te', 'kf', 'tf',
        'efd1', 'seefd1', 'efd2', 'seefd2', 'exclim', 'efdmin', 'edfmax',
    )
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = '', tpe: str = 'ExcDC1A') -> None:
        """Initialize only properties declared by the selected RDF edition."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.ka: PU | None = None
        self.ks: PU | None = None
        self.ta: Seconds | None = None
        self.tb: Seconds | None = None
        self.tc: Seconds | None = None
        self.vrmax: PU | None = None
        self.vrmin: PU | None = None
        self.ke: PU | None = None
        self.te: Seconds | None = None
        self.kf: PU | None = None
        self.tf: Seconds | None = None
        self.efd1: PU | None = None
        self.seefd1: float | None = None
        self.efd2: PU | None = None
        self.seefd2: float | None = None
        self.exclim: bool | None = None
        self.efdmin: PU | None = None
        self.edfmax: PU | None = None


class ExcDC3A(ExcitationSystemDynamics):
    """Canonical 2.4.15 ExcDC3A fields, including the RDF spelling ``edfmax``."""

    __slots__ = (
        'trh', 'ks', 'kr', 'kv', 'vrmax', 'vrmin', 'te', 'ke', 'efd1', 'seefd1',
        'efd2', 'seefd2', 'exclim', 'edfmax', 'efdmin', 'efdlim',
    )
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = '', tpe: str = 'ExcDC3A') -> None:
        """Initialize only properties declared by the selected RDF edition."""
        ExcitationSystemDynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.trh: Seconds | None = None
        self.ks: PU | None = None
        self.kr: PU | None = None
        self.kv: PU | None = None
        self.vrmax: PU | None = None
        self.vrmin: PU | None = None
        self.te: Seconds | None = None
        self.ke: PU | None = None
        self.efd1: PU | None = None
        self.seefd1: float | None = None
        self.efd2: PU | None = None
        self.seefd2: float | None = None
        self.exclim: bool | None = None
        self.edfmax: PU | None = None
        self.efdmin: PU | None = None
        self.efdlim: bool | None = None


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
    CgmesProperty(property_name='edfmax', class_type=PU, profiles=[CgmesProfileType.DY]),
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
    CgmesProperty(property_name='edfmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efdmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='efdlim', class_type=bool, profiles=[CgmesProfileType.DY]),
)


class WindGenTurbineType1IEC(WindTurbineType1or2IEC):
    """Canonical 2.4.15 Type 1 turbine root and aerodynamic association."""

    __slots__ = ('WindAeroConstIEC',)
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = '', tpe: str = 'WindGenTurbineType1IEC') -> None:
        """Initialize the exact Type 1 RDF class shape."""
        WindTurbineType1or2IEC.__init__(self, rdfid=rdfid, tpe=tpe)
        self.WindAeroConstIEC: WindAeroConstIEC | None = None


class WindAeroConstIEC(IdentifiedObject):
    """Canonical 2.4.15 constant-aerodynamic marker association."""

    __slots__ = ('WindGenTurbineType1IEC',)
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = '', tpe: str = 'WindAeroConstIEC') -> None:
        """Initialize the 2.4.15 RDF association to its Type 1 turbine root."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.WindGenTurbineType1IEC: WindGenTurbineType1IEC | None = None



class WindPitchContEmulIEC(IdentifiedObject):
    """Canonical Type 2 pitch-control emulator parameters and association."""

    __slots__ = (
        'kdroop', 'kipce', 'komegaaero', 'kppce', 'omegaref', 'pimax',
        'pimin', 't1', 't2', 'tpe', 'WindGenTurbineType2IEC',
    )
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = '', tpe: str = 'WindPitchContEmulIEC') -> None:
        """Initialize all fields declared by the 2.4.15 Dynamics RDF."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.kdroop: float | None = None
        self.kipce: float | None = None
        self.komegaaero: PU | None = None
        self.kppce: float | None = None
        self.omegaref: PU | None = None
        self.pimax: PU | None = None
        self.pimin: PU | None = None
        self.t1: Seconds | None = None
        self.t2: Seconds | None = None
        self.tpe: Seconds | None = None
        self.WindGenTurbineType2IEC: WindGenTurbineType2IEC | None = None


class WindGenTurbineType2IEC(WindTurbineType1or2IEC):
    """Canonical 2.4.15 Type 2 associations, excluding later profile fields."""

    __slots__ = ('WindContRotorRIEC', 'WindPitchContEmulIEC')
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = '', tpe: str = 'WindGenTurbineType2IEC') -> None:
        """Initialize Type 2 with its 2.4.15 association surface."""
        WindTurbineType1or2IEC.__init__(self, rdfid=rdfid, tpe=tpe)
        self.WindContRotorRIEC: WindContRotorRIEC | None = None
        self.WindPitchContEmulIEC: WindPitchContEmulIEC | None = None



WindGenTurbineType1IEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='WindAeroConstIEC', class_type=WindAeroConstIEC, profiles=[CgmesProfileType.DY]),
)
WindAeroConstIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(
        property_name='WindGenTurbineType1IEC',
        class_type=WindGenTurbineType1IEC,
        profiles=[CgmesProfileType.DY],
    ),
)
WindTurbineType1or2IEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='WindMechIEC', class_type=WindMechIEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(
        property_name='WindProtectionIEC',
        class_type=WindProtectionIEC,
        profiles=[CgmesProfileType.DY],
    ),
)
WindPitchContEmulIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='kdroop', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kipce', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='komegaaero', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kppce', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='omegaref', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pimax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pimin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t1', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='t2', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpe', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindGenTurbineType2IEC', class_type=WindGenTurbineType2IEC, profiles=[CgmesProfileType.DY]),
)
WindGenTurbineType2IEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='WindContRotorRIEC', class_type=WindContRotorRIEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindPitchContEmulIEC', class_type=WindPitchContEmulIEC, profiles=[CgmesProfileType.DY]),
)


class WindTurbineType3or4Dynamics(DynamicsFunctionBlock):
    """Canonical 2.4.15 Type 3/4 root and its exact three associations."""

    __slots__ = ('EnergySource', 'RemoteInputSignal', 'WindPlantDynamics')
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = '', tpe: str = 'WindTurbineType3or4Dynamics') -> None:
        """Initialize the legacy physical-energy-source and model links."""
        DynamicsFunctionBlock.__init__(self, rdfid=rdfid, tpe=tpe)
        self.EnergySource: EnergySource | None = None
        self.RemoteInputSignal: RemoteInputSignal | None = None
        self.WindPlantDynamics: WindPlantDynamics | None = None


class WindType3or4UserDefined(WindTurbineType3or4Dynamics):
    """Canonical 2.4.15 proprietary Type 3/4 record linked through EnergySource."""

    __slots__ = ('proprietary', 'ProprietaryParameterDynamics')
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = (
        WindType3or4UserDefined2020.LOCAL_CGMES_PROPERTIES
    )

    def __init__(self, rdfid: str = '', tpe: str = 'WindType3or4UserDefined') -> None:
        """Initialize the legacy root associations and proprietary parameter link."""
        WindTurbineType3or4Dynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.proprietary: bool | None = None
        self.ProprietaryParameterDynamics: List[object] = list()


class WindTurbineType3or4IEC(WindTurbineType3or4Dynamics):
    """Canonical 2.4.15 base containing only the declared Type 3/4 associations."""

    __slots__ = ('WindContCurrLimIEC', 'WIndContQIEC', 'WindProtectionIEC')
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = '', tpe: str = 'WindTurbineType3or4IEC') -> None:
        """Initialize the canonical 2.4.15 common Type 3/4 associations."""
        WindTurbineType3or4Dynamics.__init__(self, rdfid=rdfid, tpe=tpe)
        self.WindContCurrLimIEC: WindContCurrLimIEC | None = None
        self.WIndContQIEC: WindContQIEC | None = None
        self.WindProtectionIEC: WindProtectionIEC | None = None


class WindContQIEC(IdentifiedObject):
    """Canonical 2.4.15 Q-controller fields, including legacy ``tiq`` and Q limits."""

    __slots__ = (
        'iqh1', 'iqmax', 'iqmin', 'iqpost', 'kiq', 'kiu', 'kpq', 'kpu', 'kqv',
        'qmax', 'qmin', 'rdroop', 'tiq', 'tpfilt', 'tpost', 'tqord', 'tufilt',
        'udb1', 'udb2', 'umax', 'umin', 'uqdip', 'uref0',
        'windLVRTQcontrolModesType', 'windQcontrolModesType', 'xdroop',
        'WindTurbineType3or4IEC',
    )
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = '', tpe: str = 'WindContQIEC') -> None:
        """Initialize exactly the WindContQIEC fields declared by the 2.4.15 RDF."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.iqh1: PU | None = None
        self.iqmax: PU | None = None
        self.iqmin: PU | None = None
        self.iqpost: PU | None = None
        self.kiq: PU | None = None
        self.kiu: PU | None = None
        self.kpq: PU | None = None
        self.kpu: PU | None = None
        self.kqv: PU | None = None
        self.qmax: PU | None = None
        self.qmin: PU | None = None
        self.rdroop: PU | None = None
        self.tiq: Seconds | None = None
        self.tpfilt: Seconds | None = None
        self.tpost: Seconds | None = None
        self.tqord: Seconds | None = None
        self.tufilt: Seconds | None = None
        self.udb1: PU | None = None
        self.udb2: PU | None = None
        self.umax: PU | None = None
        self.umin: PU | None = None
        self.uqdip: PU | None = None
        self.uref0: PU | None = None
        self.windLVRTQcontrolModesType: WindLVRTQcontrolModesKind | None = None
        self.windQcontrolModesType: WindQcontrolModesKind | None = None
        self.xdroop: PU | None = None
        self.WindTurbineType3or4IEC: WindTurbineType3or4IEC | None = None


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
    CgmesProperty(property_name='qmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='qmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rdroop', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tiq', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpfilt', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpost', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tqord', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tufilt', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='udb1', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='udb2', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='umax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='umin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uqdip', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uref0', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(
        property_name='windLVRTQcontrolModesType',
        class_type=WindLVRTQcontrolModesKind,
        profiles=[CgmesProfileType.DY],
    ),
    CgmesProperty(
        property_name='windQcontrolModesType',
        class_type=WindQcontrolModesKind,
        profiles=[CgmesProfileType.DY],
    ),
    CgmesProperty(property_name='xdroop', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(
        property_name='WindTurbineType3or4IEC',
        class_type=WindTurbineType3or4IEC,
        profiles=[CgmesProfileType.DY],
    ),
)

WindTurbineType3or4IEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='WindContCurrLimIEC', class_type=WindContCurrLimIEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WIndContQIEC', class_type=WindContQIEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindProtectionIEC', class_type=WindProtectionIEC, profiles=[CgmesProfileType.DY]),
)

WindTurbineType3or4Dynamics.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(
        property_name='EnergySource',
        class_type=EnergySource,
        profiles=[CgmesProfileType.DY],
    ),
    CgmesProperty(
        property_name='RemoteInputSignal',
        class_type=RemoteInputSignal,
        profiles=[CgmesProfileType.DY],
    ),
    CgmesProperty(
        property_name='WindPlantDynamics',
        class_type=WindPlantDynamics,
        profiles=[CgmesProfileType.DY],
    ),
)

RemoteInputSignal.LOCAL_CGMES_PROPERTIES = tuple(
    CgmesProperty(
        property_name=cgmes_property.property_name,
        class_type=(
            WindTurbineType3or4Dynamics
            if cgmes_property.property_name == 'WindTurbineType3or4Dynamics'
            else cgmes_property.class_type
        ),
        profiles=list(cgmes_property.profiles),
        multiplicity=cgmes_property.multiplicity,
    )
    for cgmes_property in RemoteInputSignal.LOCAL_CGMES_PROPERTIES
)

WindPlantDynamics.LOCAL_CGMES_PROPERTIES = tuple(
    CgmesProperty(
        property_name=cgmes_property.property_name,
        class_type=(
            WindTurbineType3or4Dynamics
            if cgmes_property.property_name == 'WindTurbineType3or4Dynamics'
            else cgmes_property.class_type
        ),
        profiles=list(cgmes_property.profiles),
        multiplicity=cgmes_property.multiplicity,
    )
    for cgmes_property in WindPlantDynamics.LOCAL_CGMES_PROPERTIES
)


class WindContPType4aIEC(IdentifiedObject):
    """Canonical 2.4.15 Type 4A P-controller fields."""

    __slots__ = ('dpmax', 'tpord', 'tufilt', 'WindTurbineType4aIEC')
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = '', tpe: str = 'WindContPType4aIEC') -> None:
        """Initialize the exact Type 4A P-controller RDF surface."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.dpmax: PU | None = None
        self.tpord: Seconds | None = None
        self.tufilt: Seconds | None = None
        self.WindTurbineType4aIEC: WindTurbineType4aIEC | None = None


WindContPType4aIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='dpmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpord', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tufilt', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(
        property_name='WindTurbineType4aIEC',
        class_type=WindTurbineType4aIEC,
        profiles=[CgmesProfileType.DY],
    ),
)


class WindContPType4bIEC(IdentifiedObject):
    """Canonical 2.4.15 Type 4B P-controller fields."""

    __slots__ = ('dpmax', 'tpaero', 'tpord', 'tufilt', 'WindTurbineType4bIEC')
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = '', tpe: str = 'WindContPType4bIEC') -> None:
        """Initialize the exact Type 4B P-controller RDF surface."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.dpmax: PU | None = None
        self.tpaero: Seconds | None = None
        self.tpord: Seconds | None = None
        self.tufilt: Seconds | None = None
        self.WindTurbineType4bIEC: WindTurbineType4bIEC | None = None


WindContPType4bIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='dpmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpaero', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpord', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tufilt', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(
        property_name='WindTurbineType4bIEC',
        class_type=WindTurbineType4bIEC,
        profiles=[CgmesProfileType.DY],
    ),
)
WindMechIEC.LOCAL_CGMES_PROPERTIES = tuple(
    CgmesProperty(
        property_name=cgmes_property.property_name,
        class_type=(
            WindTurbineType4bIEC
            if cgmes_property.property_name == 'WindTurbineType4bIEC'
            else cgmes_property.class_type
        ),
        profiles=list(cgmes_property.profiles),
        multiplicity=cgmes_property.multiplicity,
    )
    for cgmes_property in WindMechIEC.LOCAL_CGMES_PROPERTIES
)


class WindGenType4IEC(WindTurbineType3or4IEC):
    """Canonical 2.4.15 abstract Type 4 generator parameter class."""

    __slots__ = ('dipmax', 'diqmin', 'diqmax', 'tg')
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = '', tpe: str = 'WindGenType4IEC') -> None:
        """Initialize the Type 4 parameters declared directly by the 2016 RDF."""
        WindTurbineType3or4IEC.__init__(self, rdfid=rdfid, tpe=tpe)
        self.dipmax: PU | None = None
        self.diqmin: PU | None = None
        self.diqmax: PU | None = None
        self.tg: Seconds | None = None


WindGenType4IEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='dipmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='diqmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='diqmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tg', class_type=Seconds, profiles=[CgmesProfileType.DY]),
)


class WindTurbineType4aIEC(WindGenType4IEC):
    """Canonical 2.4.15 Type 4A turbine composite."""

    __slots__ = ('WindContPType4aIEC',)
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = '', tpe: str = 'WindTurbineType4aIEC') -> None:
        """Initialize the 2.4.15 Type 4A direct association."""
        WindGenType4IEC.__init__(self, rdfid=rdfid, tpe=tpe)
        self.WindContPType4aIEC: WindContPType4aIEC | None = None


WindTurbineType4aIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(
        property_name='WindContPType4aIEC',
        class_type=WindContPType4aIEC,
        profiles=[CgmesProfileType.DY],
    ),
)


class WindTurbineType4bIEC(WindGenType4IEC):
    """Canonical 2.4.15 Type 4B turbine composite."""

    __slots__ = ('WindContPType4bIEC', 'WindMechIEC')
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = '', tpe: str = 'WindTurbineType4bIEC') -> None:
        """Initialize the 2.4.15 Type 4B direct associations."""
        WindGenType4IEC.__init__(self, rdfid=rdfid, tpe=tpe)
        self.WindContPType4bIEC: WindContPType4bIEC | None = None
        self.WindMechIEC: WindMechIEC | None = None


WindTurbineType4bIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(
        property_name='WindContPType4bIEC',
        class_type=WindContPType4bIEC,
        profiles=[CgmesProfileType.DY],
    ),
    CgmesProperty(
        property_name='WindMechIEC',
        class_type=WindMechIEC,
        profiles=[CgmesProfileType.DY],
    ),
)

WindContPType4aIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='dpmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpord', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tufilt', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(
        property_name='WindTurbineType4aIEC',
        class_type=WindTurbineType4aIEC,
        profiles=[CgmesProfileType.DY],
    ),
)
WindContPType4bIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='dpmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpaero', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpord', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tufilt', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(
        property_name='WindTurbineType4bIEC',
        class_type=WindTurbineType4bIEC,
        profiles=[CgmesProfileType.DY],
    ),
)


class WindGenTurbineType3IEC(WindTurbineType3or4IEC):
    """Canonical 2.4.15 abstract generator base for Type 3A and Type 3B."""

    __slots__ = (
        'WindAeroLinearIEC', 'WindContPitchAngleIEC', 'WindContPType3IEC',
        'dipmax', 'diqmax', 'WindMechIEC',
    )
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = '', tpe: str = 'WindGenTurbineType3IEC') -> None:
        """Initialize canonical 2.4.15 Type 3 generator properties."""
        WindTurbineType3or4IEC.__init__(self, rdfid=rdfid, tpe=tpe)
        self.WindAeroLinearIEC: WindAeroLinearIEC | None = None
        self.WindContPitchAngleIEC: WindContPitchAngleIEC | None = None
        self.WindContPType3IEC: WindContPType3IEC | None = None
        self.dipmax: PU | None = None
        self.diqmax: PU | None = None
        self.WindMechIEC: WindMechIEC | None = None


class WindMechIEC(IdentifiedObject):
    """Canonical 2.4.15 two-mass drivetrain and turbine associations."""

    __slots__ = (
        'cdrt', 'hgen', 'hwtr', 'kdrt', 'WindGenTurbineType3IEC',
        'WindTurbineType1or2IEC', 'WindTurbineType4bIEC',
    )
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = '', tpe: str = 'WindMechIEC') -> None:
        """Initialize canonical mechanical fields and the 2016 Type 3 root link."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.cdrt: PU | None = None
        self.hgen: Seconds | None = None
        self.hwtr: Seconds | None = None
        self.kdrt: PU | None = None
        self.WindGenTurbineType3IEC: WindGenTurbineType3IEC | None = None
        self.WindTurbineType1or2IEC: WindTurbineType1or2IEC | None = None
        self.WindTurbineType4bIEC: WindTurbineType4bIEC | None = None


class WindContPType3IEC(IdentifiedObject):
    """Canonical 2.4.15 Type 3 active-power controller RDF class."""

    __slots__ = (
        'dpmax', 'dtrisemaxlvrt', 'kdtd', 'kip', 'kpp', 'mplvrt',
        'omegaoffset', 'pdtdmax', 'rramp', 'tdvs', 'temin', 'tomegafilt',
        'tpfilt', 'tpord', 'tufilt', 'tuscale', 'twref', 'udvs', 'updip',
        'wdtd', 'zeta', 'WindGenTurbineType3IEC', 'WindDynamicsLookupTable',
    )
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = '', tpe: str = 'WindContPType3IEC') -> None:
        """Initialize the exact 2016 RDF names and lookup association shape."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.dpmax: PU | None = None
        self.dtrisemaxlvrt: PU | None = None
        self.kdtd: PU | None = None
        self.kip: PU | None = None
        self.kpp: PU | None = None
        self.mplvrt: bool | None = None
        self.omegaoffset: PU | None = None
        self.pdtdmax: PU | None = None
        self.rramp: PU | None = None
        self.tdvs: Seconds | None = None
        self.temin: PU | None = None
        self.tomegafilt: Seconds | None = None
        self.tpfilt: Seconds | None = None
        self.tpord: PU | None = None
        self.tufilt: Seconds | None = None
        self.tuscale: PU | None = None
        self.twref: Seconds | None = None
        self.udvs: PU | None = None
        self.updip: PU | None = None
        self.wdtd: PU | None = None
        self.zeta: float | None = None
        self.WindGenTurbineType3IEC: WindGenTurbineType3IEC | None = None
        self.WindDynamicsLookupTable: List[WindDynamicsLookupTable] = list()


class WindDynamicsLookupTable(IdentifiedObject):
    """Canonical 2.4.15 lookup point and its supported owner associations."""

    __slots__ = (
        'input', 'lookupTableFunctionType', 'output', 'sequence',
        'WindContCurrLimIEC', 'WindContPType3IEC', 'WindContRotorRIEC',
        'WindPlantFreqPcontrolIEC',
    )
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = '', tpe: str = 'WindDynamicsLookupTable') -> None:
        """Initialize the four lookup values and four 2.4.15 owner links."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.input: float | None = None
        self.lookupTableFunctionType: WindLookupTableFunctionKind | None = None
        self.output: float | None = None
        self.sequence: int | None = None
        self.WindContCurrLimIEC: WindContCurrLimIEC | None = None
        self.WindContPType3IEC: WindContPType3IEC | None = None
        self.WindContRotorRIEC: WindContRotorRIEC | None = None
        self.WindPlantFreqPcontrolIEC: WindPlantFreqPcontrolIEC | None = None


class WindContRotorRIEC(IdentifiedObject):
    """Canonical 2.4.15 rotor-resistance controller class."""

    __slots__ = (
        'kirr', 'komegafilt', 'kpfilt', 'kprr', 'rmax', 'rmin',
        'tomegafilt', 'tpfilt', 'WindDynamicsLookupTable',
        'WindGenTurbineType2IEC',
    )
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = '', tpe: str = 'WindContRotorRIEC') -> None:
        """Initialize the legacy filter names and canonical Type 2 relation."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.kirr: PU | None = None
        self.komegafilt: float | None = None
        self.kpfilt: float | None = None
        self.kprr: PU | None = None
        self.rmax: PU | None = None
        self.rmin: PU | None = None
        self.tomegafilt: Seconds | None = None
        self.tpfilt: Seconds | None = None
        self.WindDynamicsLookupTable: List[WindDynamicsLookupTable] = list()
        self.WindGenTurbineType2IEC: WindGenTurbineType2IEC | None = None


class WindContCurrLimIEC(IdentifiedObject):
    """Canonical 2.4.15 current limiter with its exact seven RDF properties."""

    __slots__ = (
        'imax', 'imaxdip', 'mdfslim', 'mqpri', 'tufilt',
        'WindTurbineType3or4IEC', 'WindDynamicsLookupTable',
    )
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = '', tpe: str = 'WindContCurrLimIEC') -> None:
        """Initialize legacy current-limit parameters and lookup data links."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.imax: PU | None = None
        self.imaxdip: PU | None = None
        self.mdfslim: bool | None = None
        self.mqpri: bool | None = None
        self.tufilt: Seconds | None = None
        self.WindTurbineType3or4IEC: WindTurbineType3or4IEC | None = None
        self.WindDynamicsLookupTable: List[WindDynamicsLookupTable] = list()


class WindPlantFreqPcontrolIEC(IdentifiedObject):
    """Canonical 2.4.15 plant frequency and active-power controller."""

    __slots__ = (
        'dprefmax', 'dprefmin', 'kiwpp', 'kpwpp', 'prefmax', 'prefmin',
        'tpft', 'tpfv', 'twpffilt', 'twppfilt', 'WindDynamicsLookupTable',
        'WindPlantIEC',
    )
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = '', tpe: str = 'WindPlantFreqPcontrolIEC') -> None:
        """Initialize the exact 2016 controller parameters and associations."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.dprefmax: PU | None = None
        self.dprefmin: PU | None = None
        self.kiwpp: float | None = None
        self.kpwpp: float | None = None
        self.prefmax: PU | None = None
        self.prefmin: PU | None = None
        self.tpft: Seconds | None = None
        self.tpfv: Seconds | None = None
        self.twpffilt: Seconds | None = None
        self.twppfilt: Seconds | None = None
        self.WindDynamicsLookupTable: List[WindDynamicsLookupTable] = list()
        self.WindPlantIEC: WindPlantIEC | None = None


class WindProtectionIEC(IdentifiedObject):
    """Canonical 2.4.15 relay thresholds and turbine-root associations."""

    __slots__ = (
        'fover', 'funder', 'tfover', 'tfunder', 'tuover', 'tuunder',
        'uover', 'uunder', 'WindTurbineType3or4IEC', 'WindTurbineType1or2IEC',
    )
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = '', tpe: str = 'WindProtectionIEC') -> None:
        """Initialize the exact scalar relay settings and equipment roots."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.fover: PU | None = None
        self.funder: PU | None = None
        self.tfover: Seconds | None = None
        self.tfunder: Seconds | None = None
        self.tuover: Seconds | None = None
        self.tuunder: Seconds | None = None
        self.uover: PU | None = None
        self.uunder: PU | None = None
        self.WindTurbineType3or4IEC: WindTurbineType3or4IEC | None = None
        self.WindTurbineType1or2IEC: WindTurbineType1or2IEC | None = None


class WindPlantReactiveControlIEC(IdentifiedObject):
    """Canonical 2.4.15 plant reactive controller properties."""

    __slots__ = (
        'WindPlantIEC', 'kiwpx', 'kpwpx', 'kwpqu', 'mwppf', 'mwpu',
        'twppfilt', 'twpqfilt', 'twpufilt', 'txft', 'txfv', 'uwpqdip',
        'xrefmax', 'xrefmin',
    )
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = '', tpe: str = 'WindPlantReactiveControlIEC') -> None:
        """Initialize the exact legacy fields and plant association."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.WindPlantIEC: WindPlantIEC | None = None
        self.kiwpx: float | None = None
        self.kpwpx: float | None = None
        self.kwpqu: PU | None = None
        self.mwppf: bool | None = None
        self.mwpu: bool | None = None
        self.twppfilt: Seconds | None = None
        self.twpqfilt: Seconds | None = None
        self.twpufilt: Seconds | None = None
        self.txft: Seconds | None = None
        self.txfv: Seconds | None = None
        self.uwpqdip: PU | None = None
        self.xrefmax: PU | None = None
        self.xrefmin: PU | None = None


class WindContPitchAngleIEC(IdentifiedObject):
    """Canonical 2.4.15 pitch controller with its RDF Type 3 association name."""

    __slots__ = (
        'dthetamax', 'dthetamin', 'kic', 'kiomega', 'kpc', 'kpomega', 'kpx',
        'thetamax', 'thetamin', 'ttheta', 'WindGenTurbineType3IEC',
    )
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = tuple()

    def __init__(self, rdfid: str = '', tpe: str = 'WindContPitchAngleIEC') -> None:
        """Initialize the exact pitch-control parameter and association surface."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.dthetamax: float | None = None
        self.dthetamin: float | None = None
        self.kic: PU | None = None
        self.kiomega: PU | None = None
        self.kpc: PU | None = None
        self.kpomega: PU | None = None
        self.kpx: PU | None = None
        self.thetamax: AngleDegrees | None = None
        self.thetamin: AngleDegrees | None = None
        self.ttheta: Seconds | None = None
        self.WindGenTurbineType3IEC: WindGenTurbineType3IEC | None = None


WindContPitchAngleIEC.LOCAL_CGMES_PROPERTIES = tuple(
    cgmes_property
    for cgmes_property in WindContPitchAngleIEC2020.LOCAL_CGMES_PROPERTIES
    if cgmes_property.property_name != 'WindTurbineType3IEC'
) + (
    CgmesProperty(
        property_name='WindGenTurbineType3IEC',
        class_type=WindGenTurbineType3IEC,
        profiles=[CgmesProfileType.DY],
    ),
)


class WindGenTurbineType3aIEC(WindGenTurbineType3IEC):
    """Canonical 2.4.15 Type 3A generator realization parameters."""

    __slots__ = ('kpc', 'xs', 'tic')
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='kpc', class_type=float, profiles=[CgmesProfileType.DY]),
        CgmesProperty(property_name='xs', class_type=PU, profiles=[CgmesProfileType.DY]),
        CgmesProperty(property_name='tic', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    )

    def __init__(self, rdfid: str = '', tpe: str = 'WindGenTurbineType3aIEC') -> None:
        """Initialize canonical Type 3A local parameters."""
        WindGenTurbineType3IEC.__init__(self, rdfid=rdfid, tpe=tpe)
        self.kpc: float | None = None
        self.xs: PU | None = None
        self.tic: Seconds | None = None


class WindGenTurbineType3bIEC(WindGenTurbineType3IEC):
    """Canonical 2.4.15 Type 3B generator realization parameters."""

    # TODO: The RDF/EA defines fducw as a scalar but describes an fduCW() curve; 2.4.15 has no lookup-table association, so enabled crowbar timing cannot be reconstructed until the canonical data surface supplies curve points.
    __slots__ = ('fducw', 'tg', 'two', 'mwtcwp', 'xs')
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='fducw', class_type=float, profiles=[CgmesProfileType.DY]),
        CgmesProperty(property_name='tg', class_type=Seconds, profiles=[CgmesProfileType.DY]),
        CgmesProperty(property_name='two', class_type=Seconds, profiles=[CgmesProfileType.DY]),
        CgmesProperty(property_name='mwtcwp', class_type=bool, profiles=[CgmesProfileType.DY]),
        CgmesProperty(property_name='xs', class_type=PU, profiles=[CgmesProfileType.DY]),
    )

    def __init__(self, rdfid: str = '', tpe: str = 'WindGenTurbineType3bIEC') -> None:
        """Initialize canonical Type 3B local parameters."""
        WindGenTurbineType3IEC.__init__(self, rdfid=rdfid, tpe=tpe)
        self.fducw: float | None = None
        self.tg: Seconds | None = None
        self.two: Seconds | None = None
        self.mwtcwp: bool | None = None
        self.xs: PU | None = None


class WindAeroLinearIEC(IdentifiedObject):
    """Canonical 2.4.15 linear aerodynamic block and parameter record."""

    __slots__ = ('dpomega', 'dptheta', 'omegazero', 'pavail', 'thetazero', 'WindGenTurbineType3IEC')
    LOCAL_CGMES_PROPERTIES: Tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='dpomega', class_type=PU, profiles=[CgmesProfileType.DY]),
        CgmesProperty(property_name='dptheta', class_type=PU, profiles=[CgmesProfileType.DY]),
        CgmesProperty(property_name='omegazero', class_type=PU, profiles=[CgmesProfileType.DY]),
        CgmesProperty(property_name='pavail', class_type=PU, profiles=[CgmesProfileType.DY]),
        CgmesProperty(property_name='thetazero', class_type=AngleDegrees, profiles=[CgmesProfileType.DY]),
        CgmesProperty(property_name='WindGenTurbineType3IEC', class_type=WindGenTurbineType3IEC, profiles=[CgmesProfileType.DY]),
    )

    def __init__(self, rdfid: str = '', tpe: str = 'WindAeroLinearIEC') -> None:
        """Initialize canonical 2.4.15 aerodynamic parameters."""
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
        self.dpomega: PU | None = None
        self.dptheta: PU | None = None
        self.omegazero: PU | None = None
        self.pavail: PU | None = None
        self.thetazero: AngleDegrees | None = None
        self.WindGenTurbineType3IEC: WindGenTurbineType3IEC | None = None


WindGenTurbineType3IEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='WindAeroLinearIEC', class_type=WindAeroLinearIEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindContPitchAngleIEC', class_type=WindContPitchAngleIEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindContPType3IEC', class_type=WindContPType3IEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dipmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='diqmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindMechIEC', class_type=WindMechIEC, profiles=[CgmesProfileType.DY]),
)

WindMechIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='cdrt', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='hgen', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='hwtr', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kdrt', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(
        property_name='WindGenTurbineType3IEC',
        class_type=WindGenTurbineType3IEC,
        profiles=[CgmesProfileType.DY],
    ),
    CgmesProperty(
        property_name='WindTurbineType1or2IEC',
        class_type=WindTurbineType1or2IEC,
        profiles=[CgmesProfileType.DY],
    ),
    CgmesProperty(
        property_name='WindTurbineType4bIEC',
        class_type=WindTurbineType4bIEC,
        profiles=[CgmesProfileType.DY],
    ),
)

WindContPType3IEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='dpmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dtrisemaxlvrt', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kdtd', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kip', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kpp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='mplvrt', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='omegaoffset', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='pdtdmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rramp', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tdvs', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='temin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tomegafilt', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpfilt', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpord', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tufilt', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tuscale', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='twref', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='udvs', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='updip', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='wdtd', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='zeta', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='WindGenTurbineType3IEC', class_type=WindGenTurbineType3IEC, profiles=[CgmesProfileType.DY]),
    CgmesProperty(
        property_name='WindDynamicsLookupTable',
        class_type=WindDynamicsLookupTable,
        profiles=[CgmesProfileType.DY],
        multiplicity='2..n',
    ),
)

WindDynamicsLookupTable.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='input', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(
        property_name='lookupTableFunctionType',
        class_type=WindLookupTableFunctionKind,
        profiles=[CgmesProfileType.DY],
    ),
    CgmesProperty(property_name='output', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='sequence', class_type=int, profiles=[CgmesProfileType.DY]),
    CgmesProperty(
        property_name='WindContCurrLimIEC',
        class_type=WindContCurrLimIEC,
        profiles=[CgmesProfileType.DY],
        multiplicity='0..1',
    ),
    CgmesProperty(
        property_name='WindContPType3IEC',
        class_type=WindContPType3IEC,
        profiles=[CgmesProfileType.DY],
        multiplicity='0..1',
    ),
    CgmesProperty(
        property_name='WindContRotorRIEC',
        class_type=WindContRotorRIEC,
        profiles=[CgmesProfileType.DY],
        multiplicity='0..1',
    ),
    CgmesProperty(
        property_name='WindPlantFreqPcontrolIEC',
        class_type=WindPlantFreqPcontrolIEC,
        profiles=[CgmesProfileType.DY],
        multiplicity='0..1',
    ),
)

WindContRotorRIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='kirr', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='komegafilt', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kpfilt', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kprr', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='rmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tomegafilt', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpfilt', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(
        property_name='WindDynamicsLookupTable',
        class_type=WindDynamicsLookupTable,
        profiles=[CgmesProfileType.DY],
        multiplicity='2..n',
    ),
    CgmesProperty(
        property_name='WindGenTurbineType2IEC',
        class_type=WindGenTurbineType2IEC,
        profiles=[CgmesProfileType.DY],
    ),
)

WindContCurrLimIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='imax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='imaxdip', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='mdfslim', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='mqpri', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tufilt', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(
        property_name='WindTurbineType3or4IEC',
        class_type=WindTurbineType3or4IEC,
        profiles=[CgmesProfileType.DY],
    ),
    CgmesProperty(
        property_name='WindDynamicsLookupTable',
        class_type=WindDynamicsLookupTable,
        profiles=[CgmesProfileType.DY],
        multiplicity='2..n',
    ),
)

WindPlantFreqPcontrolIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='dprefmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='dprefmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kiwpp', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kpwpp', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='prefmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='prefmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpft', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tpfv', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='twpffilt', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='twppfilt', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(
        property_name='WindDynamicsLookupTable',
        class_type=WindDynamicsLookupTable,
        profiles=[CgmesProfileType.DY],
        multiplicity='1..n',
    ),
    CgmesProperty(
        property_name='WindPlantIEC',
        class_type=WindPlantIEC,
        profiles=[CgmesProfileType.DY],
    ),
)

WindProtectionIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='fover', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='funder', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tfover', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tfunder', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tuover', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='tuunder', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uover', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uunder', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(
        property_name='WindTurbineType3or4IEC',
        class_type=WindTurbineType3or4IEC,
        profiles=[CgmesProfileType.DY],
    ),
    CgmesProperty(
        property_name='WindTurbineType1or2IEC',
        class_type=WindTurbineType1or2IEC,
        profiles=[CgmesProfileType.DY],
    ),
)

WindPlantReactiveControlIEC.LOCAL_CGMES_PROPERTIES = (
    CgmesProperty(property_name='kiwpx', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kpwpx', class_type=float, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='kwpqu', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='mwppf', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='mwpu', class_type=bool, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='twppfilt', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='twpqfilt', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='twpufilt', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='txft', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='txfv', class_type=Seconds, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='uwpqdip', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='xrefmax', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(property_name='xrefmin', class_type=PU, profiles=[CgmesProfileType.DY]),
    CgmesProperty(
        property_name='WindPlantIEC',
        class_type=WindPlantIEC,
        profiles=[CgmesProfileType.DY],
    ),
)


def get_cgmes_24_15_dynamics_schema() -> tuple[Dict[str, type], Dict[Tuple[str, str], str]]:
    """Return versioned 2.4.15 Dynamics classes and inverse associations.

    :return: Class constructors and the inverse-association map entries.
    """
    class_dict: Dict[str, type] = {
        'GovSteamCC': GovSteamCC,
        'GovHydro4': GovHydro4,
        'GovSteamEU': GovSteamEU,
        'GovSteamFV3': GovSteamFV3,
        'LoadComposite': LoadComposite,
        'LoadGenericNonLinear': LoadGenericNonLinear,
        'ExcDC1A': ExcDC1A,
        'ExcDC3A': ExcDC3A,
        'WindGenTurbineType1IEC': WindGenTurbineType1IEC,
        'WindGenTurbineType2IEC': WindGenTurbineType2IEC,
        'WindPitchContEmulIEC': WindPitchContEmulIEC,
        'WindTurbineType3or4IEC': WindTurbineType3or4IEC,
        'WindContQIEC': WindContQIEC,
        'WindContPType4aIEC': WindContPType4aIEC,
        'WindContPType4bIEC': WindContPType4bIEC,
        'WindGenType4IEC': WindGenType4IEC,
        'WindTurbineType4aIEC': WindTurbineType4aIEC,
        'WindTurbineType4bIEC': WindTurbineType4bIEC,
        'WindGenTurbineType3IEC': WindGenTurbineType3IEC,
        'WindMechIEC': WindMechIEC,
        'WindContPType3IEC': WindContPType3IEC,
        'WindDynamicsLookupTable': WindDynamicsLookupTable,
        'WindContRotorRIEC': WindContRotorRIEC,
        'WindContCurrLimIEC': WindContCurrLimIEC,
        'WindPlantFreqPcontrolIEC': WindPlantFreqPcontrolIEC,
        'WindPlantReactiveControlIEC': WindPlantReactiveControlIEC,
        'WindProtectionIEC': WindProtectionIEC,
        'WindTurbineType3or4Dynamics': WindTurbineType3or4Dynamics,
        'WindType3or4UserDefined': WindType3or4UserDefined,
        'ProprietaryParameterDynamics': ProprietaryParameterDynamics,
        'SynchronousMachineDynamics': SynchronousMachineDynamics,
        'SynchronousMachineDetailed': SynchronousMachineDetailed,
        'SynchronousMachineSimplified': SynchronousMachineSimplified,
        'SynchronousMachineUserDefined': SynchronousMachineUserDefined,
        'SynchronousMachineEquivalentCircuit': SynchronousMachineEquivalentCircuit,
        'SynchronousMachineTimeConstantReactance': SynchronousMachineTimeConstantReactance,
        'WindContPitchAngleIEC': WindContPitchAngleIEC,
        'WindGenTurbineType3aIEC': WindGenTurbineType3aIEC,
        'WindGenTurbineType3bIEC': WindGenTurbineType3bIEC,
        'WindAeroLinearIEC': WindAeroLinearIEC,
        'WindAeroConstIEC': WindAeroConstIEC,
    }
    inverse_associations: Dict[Tuple[str, str], str] = {
        ('EnergySource', 'WindTurbineType3or4Dynamics'): 'WindTurbineType3or4Dynamics.EnergySource',
        ('WindTurbineType3or4Dynamics', 'EnergySource'): 'EnergySource.WindTurbineType3or4Dynamics',
        ('RemoteInputSignal', 'WindTurbineType3or4Dynamics'): 'WindTurbineType3or4Dynamics.RemoteInputSignal',
        ('WindTurbineType3or4Dynamics', 'RemoteInputSignal'): 'RemoteInputSignal.WindTurbineType3or4Dynamics',
        ('WindPlantDynamics', 'WindTurbineType3or4Dynamics'): 'WindTurbineType3or4Dynamics.WindPlantDynamics',
        ('WindTurbineType3or4Dynamics', 'WindPlantDynamics'): 'WindPlantDynamics.WindTurbineType3or4Dynamics',
        ('WindGenTurbineType1IEC', 'WindAeroConstIEC'): 'WindAeroConstIEC.WindGenTurbineType1IEC',
        ('WindAeroConstIEC', 'WindGenTurbineType1IEC'): 'WindGenTurbineType1IEC.WindAeroConstIEC',
        ('WindGenTurbineType2IEC', 'WindContRotorRIEC'): 'WindContRotorRIEC.WindGenTurbineType2IEC',
        ('WindContRotorRIEC', 'WindGenTurbineType2IEC'): 'WindGenTurbineType2IEC.WindContRotorRIEC',
        ('WindGenTurbineType2IEC', 'WindPitchContEmulIEC'): 'WindPitchContEmulIEC.WindGenTurbineType2IEC',
        ('WindPitchContEmulIEC', 'WindGenTurbineType2IEC'): 'WindGenTurbineType2IEC.WindPitchContEmulIEC',
        ('WindTurbineType3or4IEC', 'WindContCurrLimIEC'): 'WindContCurrLimIEC.WindTurbineType3or4IEC',
        ('WindContCurrLimIEC', 'WindTurbineType3or4IEC'): 'WindTurbineType3or4IEC.WindContCurrLimIEC',
        ('WindTurbineType3or4IEC', 'WIndContQIEC'): 'WindContQIEC.WindTurbineType3or4IEC',
        ('WindContQIEC', 'WindTurbineType3or4IEC'): 'WindTurbineType3or4IEC.WIndContQIEC',
        ('WindTurbineType4aIEC', 'WindContPType4aIEC'): 'WindContPType4aIEC.WindTurbineType4aIEC',
        ('WindContPType4aIEC', 'WindTurbineType4aIEC'): 'WindTurbineType4aIEC.WindContPType4aIEC',
        ('WindTurbineType4bIEC', 'WindContPType4bIEC'): 'WindContPType4bIEC.WindTurbineType4bIEC',
        ('WindContPType4bIEC', 'WindTurbineType4bIEC'): 'WindTurbineType4bIEC.WindContPType4bIEC',
        ('WindMechIEC', 'WindTurbineType4bIEC'): 'WindTurbineType4bIEC.WindMechIEC',
        ('WindTurbineType4bIEC', 'WindMechIEC'): 'WindMechIEC.WindTurbineType4bIEC',
        ('WindTurbineType3or4IEC', 'WindProtectionIEC'): 'WindProtectionIEC.WindTurbineType3or4IEC',
        ('WindProtectionIEC', 'WindTurbineType3or4IEC'): 'WindTurbineType3or4IEC.WindProtectionIEC',
        ('WindGenTurbineType3IEC', 'WindAeroLinearIEC'): 'WindAeroLinearIEC.WindGenTurbineType3IEC',
        ('WindAeroLinearIEC', 'WindGenTurbineType3IEC'): 'WindGenTurbineType3IEC.WindAeroLinearIEC',
        ('WindGenTurbineType3IEC', 'WindContPitchAngleIEC'): 'WindContPitchAngleIEC.WindGenTurbineType3IEC',
        ('WindContPitchAngleIEC', 'WindGenTurbineType3IEC'): 'WindGenTurbineType3IEC.WindContPitchAngleIEC',
        ('WindGenTurbineType3IEC', 'WindContPType3IEC'): 'WindContPType3IEC.WindGenTurbineType3IEC',
        ('WindContPType3IEC', 'WindGenTurbineType3IEC'): 'WindGenTurbineType3IEC.WindContPType3IEC',
        ('WindDynamicsLookupTable', 'WindContCurrLimIEC'): 'WindContCurrLimIEC.WindDynamicsLookupTable',
        ('WindContCurrLimIEC', 'WindDynamicsLookupTable'): 'WindDynamicsLookupTable.WindContCurrLimIEC',
        ('WindDynamicsLookupTable', 'WindContPType3IEC'): 'WindContPType3IEC.WindDynamicsLookupTable',
        ('WindContPType3IEC', 'WindDynamicsLookupTable'): 'WindDynamicsLookupTable.WindContPType3IEC',
        ('WindDynamicsLookupTable', 'WindContRotorRIEC'): 'WindContRotorRIEC.WindDynamicsLookupTable',
        ('WindContRotorRIEC', 'WindDynamicsLookupTable'): 'WindDynamicsLookupTable.WindContRotorRIEC',
        ('WindDynamicsLookupTable', 'WindPlantFreqPcontrolIEC'): 'WindPlantFreqPcontrolIEC.WindDynamicsLookupTable',
        ('WindPlantFreqPcontrolIEC', 'WindDynamicsLookupTable'): 'WindDynamicsLookupTable.WindPlantFreqPcontrolIEC',
        ('WindPlantIEC', 'WindPlantFreqPcontrolIEC'): 'WindPlantFreqPcontrolIEC.WindPlantIEC',
        ('WindPlantFreqPcontrolIEC', 'WindPlantIEC'): 'WindPlantIEC.WindPlantFreqPcontrolIEC',
        ('WindPlantIEC', 'WindPlantReactiveControlIEC'): 'WindPlantReactiveControlIEC.WindPlantIEC',
        ('WindPlantReactiveControlIEC', 'WindPlantIEC'): 'WindPlantIEC.WindPlantReactiveControlIEC',
        ('WindTurbineType3or4Dynamics', 'EnergySource'): 'EnergySource.WindTurbineType3or4Dynamics',
        ('WindTurbineType1or2IEC', 'WindProtectionIEC'): 'WindProtectionIEC.WindTurbineType1or2IEC',
        ('WindProtectionIEC', 'WindTurbineType1or2IEC'): 'WindTurbineType1or2IEC.WindProtectionIEC',
        ('WindGenTurbineType3IEC', 'WindMechIEC'): 'WindMechIEC.WindGenTurbineType3IEC',
        ('WindMechIEC', 'WindGenTurbineType3IEC'): 'WindGenTurbineType3IEC.WindMechIEC',
    }
    return class_dict, inverse_associations
