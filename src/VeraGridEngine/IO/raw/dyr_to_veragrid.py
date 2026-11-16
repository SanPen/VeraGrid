# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""PSS/E DYR bindings to existing native RMS templates.

Machine-base impedances/inertia are converted explicitly. Controllers are
assembled by reviewed ports, never attached as complete physical devices merely
because their catalogue name matches a DYR record.
"""
from __future__ import annotations
from enum import Enum
from typing import TYPE_CHECKING
import math
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.IO.raw.raw_types import RawGeneratorLike, RawLoadLike
from VeraGridEngine.IO.raw.psse_file_type import PsseFileType
from VeraGridEngine.IO.raw.psse_conversion_report import PsseConversionStatus
from VeraGridEngine.IO.raw.psse_auxiliary import PsseVersion
from VeraGridEngine.IO.raw.versioned.base.dyr import DyrRecord, UserModelType
from VeraGridEngine.IO.raw.versioned.base.auxiliary import RecordStatus, BusIdentifier, EquipmentKind
from VeraGridEngine.Templates.Rms.synchronous_machines.gencls_rms_template import (
    get_complete_gencls_rms_template, GenclsMechanicalInput, GenclsRmsParameters,
    configure_gencls_block,
)
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import (
    get_genrou_rms_template, get_tgov1_rms_template, get_exst1_rms_template,
    get_esst3a_rms_template, GenrouRmsParameters, Tgov1RmsParameters,
    configure_genrou_block, configure_tgov1_block, set_rms_model_parameter, GenrouSaturationMode,
    _anti_windup_state_derivative, _esst3a_fex,
)
from VeraGridEngine.Templates.Rms import (
    build_international_standard_template, _normalize_imported_variable_names,
)
from VeraGridEngine.Templates.Rms.governors.ivogo import build_ivogo_template
from VeraGridEngine.Templates.Rms.governors.degov1 import DieselGovernorParameters, EngineDroopFeedback, build_degov1_template
from VeraGridEngine.Templates.Rms.governors.ggov1 import (
    TrackedGovernorParameters, GovernorDroopFeedback, FuelFlowCharacteristic, build_ggov1_template)
from VeraGridEngine.Templates.Rms.governors.hygov2 import CascadedHydroGovernorParameters, build_hygov2_template
from VeraGridEngine.Templates.Rms.governors.pidgov import HydroDroopFeedback, PidHydroGovernorParameters, build_pidgov_template
from VeraGridEngine.Templates.Rms.governors.hygov import NonlinearHydroGovernorParameters, build_hygov_template
from VeraGridEngine.Templates.Rms.governors.hygovr1 import Hygovr1Parameters, build_hygovr1_template
from VeraGridEngine.Templates.Rms.governors.tgov1d import build_tgov1d_template
from VeraGridEngine.Templates.Rms.governors.gast import GasGovernorParameters, build_gast_template
from VeraGridEngine.Templates.Rms.governors.ieesgo import SteamGovernorParameters, build_ieesgo_template
from VeraGridEngine.Templates.Rms.governors.tgov2 import TGOV2Parameters, build_tgov2_template
from VeraGridEngine.Templates.Rms.governors.bbgov1 import (
    Bbgov1Parameters, build_bbgov1_template,
)
from VeraGridEngine.Templates.Rms.governors.tgov3 import (
    Tgov3Parameters, build_tgov3_template,
)
from VeraGridEngine.Templates.Rms.governors.wesgov import (
    WesgovSettings, build_wesgov_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.regca1_low_voltage import (
    Regca1LowVoltageSettings,
)
from VeraGridEngine.Templates.Rms.renewable_controls.dera1_active_power import (
    Dera1ActivePowerSettings,
)
from VeraGridEngine.Templates.Rms.renewable_controls.dera1_generator import (
    build_dera1_generator_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.dera1_inner_current_loop import (
    Dera1InnerCurrentLoopSettings,
)
from VeraGridEngine.Templates.Rms.renewable_controls.dera1_protection import (
    Dera1ProtectionSettings,
)
from VeraGridEngine.Templates.Rms.renewable_controls.dera1_reactive_current import (
    Dera1ReactiveCurrentSettings,
)
from VeraGridEngine.Templates.Rms.renewable_controls.dera1_voltage_measurement import (
    Dera1VoltageMeasurementSettings,
)
from VeraGridEngine.Templates.Rms.induction_machines.psse_cim_motor import (
    PsseCimMotorModel,
    PsseCimMotorParameters,
    PsseCimMotorType,
    build_psse_cim_motor_template,
    calculate_cimw_c0,
    solve_psse_cim_motor_operating_point,
)
from VeraGridEngine.Templates.Rms.induction_machines.cimtr1 import (
    Cimtr1Parameters, build_cimtr1_template,
)
from VeraGridEngine.Templates.Rms.induction_machines.cimtr2 import (
    Cimtr2Parameters, build_cimtr2_template,
)
from VeraGridEngine.Templates.Rms.induction_machines.cimtr3 import (
    Cimtr3Parameters, build_cimtr3_template,
)
from VeraGridEngine.Templates.Rms.induction_machines.cimtr4 import (
    Cimtr4Parameters, build_cimtr4_template,
)
from VeraGridEngine.Templates.Rms.induction_machines.cimtr_operating_point import (
    CimtrOperatingPoint, solve_cimtr_operating_point,
)
from VeraGridEngine.Templates.Rms.load_characteristics.cmld_static import (
    CmldStaticLoadParameters, build_cmld_static_load_component,
)
from VeraGridEngine.Templates.Rms.renewable_controls.reeca1_current_limit import (
    Reeca1CurrentLimitSettings, Reeca1CurrentPriority, reeca1_curve_from_source_pairs,
)
from VeraGridEngine.Templates.Rms.renewable_controls.reeca1_active_power import (
    Reeca1ActivePowerMode, Reeca1ActivePowerSettings,
)
from VeraGridEngine.Templates.Rms.renewable_controls.reeca1_voltage_support import (
    Reeca1VoltageSupportSettings,
)
from VeraGridEngine.Templates.Rms.renewable_controls.reeca1_constant_q import (
    Reeca1ConstantQSettings,
)
from VeraGridEngine.Templates.Rms.renewable_controls.reeca1_constant_pf import (
    Reeca1ConstantPfSettings,
)
from VeraGridEngine.Templates.Rms.renewable_controls.reeca1_coordinated_qv import (
    Reeca1CoordinatedQvSettings,
)
from VeraGridEngine.Templates.Rms.renewable_controls.reeca1_local_voltage import (
    Reeca1LocalVoltageSettings,
)
from VeraGridEngine.Templates.Rms.renewable_controls.reecc1_battery import (
    Reecc1BatterySettings,
)
from VeraGridEngine.Templates.Rms.renewable_controls.wtdta1_drive_train import (
    Wtdta1DriveTrainSettings,
)
from VeraGridEngine.Templates.Rms.renewable_controls.wtara1_aerodynamic import (
    Wtara1AerodynamicSettings,
)
from VeraGridEngine.Templates.Rms.renewable_controls.wttqa1_torque import (
    Wttqa1TorqueMode, Wttqa1TorqueSettings,
)
from VeraGridEngine.Templates.Rms.renewable_controls.wtpta1_pitch import (
    Wtpta1PitchSettings,
)
from VeraGridEngine.Templates.Rms.renewable_controls.renewable_partial_chain import (
    build_renewable_partial_chain,
)
from VeraGridEngine.Templates.Rms.renewable_controls.repca1_active_plant import (
    Repca1ActivePlantSettings,
)
from VeraGridEngine.Templates.Rms.renewable_controls.repca1_reactive_plant import (
    Repca1ReactiveMode, Repca1ReactivePlantSettings,
)
from VeraGridEngine.Templates.Rms.power_system_stabilizers.ivost import build_ivost_template
from VeraGridEngine.Templates.Rms.common.rational_controller import RationalStageParameters
from VeraGridEngine.Templates.Rms.power_system_stabilizers.stab1 import build_stab1_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.stab2a import build_stab2a_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.stab3 import build_stab3_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.stab4 import build_stab4_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.stabni import build_stabni_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.ieeest import IeeestParameters, build_ieeest_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.iee2st import Iee2stParameters, build_iee2st_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss4b import (
    Pss4bParameters, build_pss4b_template,
)
from VeraGridEngine.Templates.Rms.voltage_compensators.comp import build_comp_template
from VeraGridEngine.Templates.Rms.excitation_limiters.mnlex1 import build_mnlex1_template
from VeraGridEngine.Templates.Rms.excitation_limiters.mnlex2 import build_mnlex2_template
from VeraGridEngine.Templates.Rms.excitation_limiters.mnlex3 import build_mnlex3_template
from VeraGridEngine.Templates.Rms.excitation_limiters.maxex2 import (
    Maxex2Measurement, Maxex2Parameters, build_maxex2_template,
)
from VeraGridEngine.Templates.Rms.excitation_limiters.oel2c import build_oel2c_template
from VeraGridEngine.Templates.Rms.excitation_limiters.uel1 import (
    Uel1Settings, build_uel1_template,
)
from VeraGridEngine.Templates.Rms.excitation_limiters.uel2c import (
    Uel2cGainReductionMode, Uel2cParameters, Uel2cThirdQuadrantMode, build_uel2c_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exst2 import CompoundExciterKind, build_exst2_template
from VeraGridEngine.Templates.Rms.synchronous_machines.gentra import build_gentra_template
from VeraGridEngine.Templates.Rms.synchronous_machines.gensae import build_gensae_template
from VeraGridEngine.Templates.Rms.excitation_systems.scrx import build_scrx_template
from VeraGridEngine.Templates.Rms.governors.ieeeg3 import (
    HydraulicGovernorParameters, build_ieeeg3_template)
from VeraGridEngine.Templates.Rms.power_system_stabilizers.ramp_tracking_stabilizer import RampStabilizerParameters, StabilizerInterface
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss2a import build_pss2a_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss2b import build_pss2b_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss2c import build_pss2c_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss3b import QuadraticDualStabilizerParameters, build_pss3b_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss7c import build_pss7c_template
from VeraGridEngine.Templates.Rms.governors.ieeeg1 import (
    MultiStageSteamGovernorParameters, build_ieeeg1_template)
from VeraGridEngine.Templates.Rms.governors.lcfb1 import (
    TurbineLoadControllerParameters, build_lcfb1_template)
from VeraGridEngine.Templates.Rms.excitation_systems.esac8b import build_esac8b_template
from VeraGridEngine.Templates.Rms.excitation_systems.compound_excitation_supply import CompoundSupplyParameters
from VeraGridEngine.Templates.Rms.excitation_systems.dc4c import build_dc4c_template
from VeraGridEngine.Templates.Rms.excitation_systems.dc4b import build_dc4b_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac1c import build_ac1c_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac2c import build_ac2c_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac5c import build_ac5c_template
from VeraGridEngine.Templates.Rms.excitation_systems.expic1 import PiCompoundFieldParameters, build_expic1_template
from VeraGridEngine.Templates.Rms.excitation_systems.exni import BridgeExcitationSupply, build_exni_template
from VeraGridEngine.Templates.Rms.excitation_systems.ieet1b import RotatingRateFeedbackSignal, build_ieet1b_template
from VeraGridEngine.Templates.Rms.excitation_systems.st6c import CurrentLimitedFieldParameters, FieldRegulatorLimiterLocation, build_st6c_template
from VeraGridEngine.Templates.Rms.excitation_systems.st9c import (
    St9cParameters, build_st9c_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.st10c import (
    St10cParameters, build_st10c_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.st8c import (
    St8cLimiterLocation, St8cParameters, build_st8c_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_rectifier_sources import (
    Ac9cPotentialSourceSelection,
)
from VeraGridEngine.Templates.Rms.excitation_systems.st5c import build_st5c_template
from VeraGridEngine.Templates.Rms.excitation_systems.st5b import ParallelChannelExciterParameters, build_st5b_template
from VeraGridEngine.Templates.Rms.excitation_systems.cascaded_brushless_circuit import CascadedBrushlessCircuit, CascadedLimiterLocation, CascadedPowerSupply
from VeraGridEngine.Templates.Rms.excitation_systems.ac7c import build_ac7c_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac7b import CascadedBrushlessParameters, build_ac7b_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac6c import Ac6cParameters, Ac6cLimiterLocation, FieldLimitVoltage, build_ac6c_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac6c2 import build_ac6c2_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac8c import build_ac8c_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac8b import PidBrushlessExciterParameters, CompoundPidPowerCircuit, build_ac8b_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c import (
    Ac9cLimiterLocation, build_ac9c_controller_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_current_regulator import (
    Ac9cCurrentRegulatorSettings,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_field_feedback import (
    Ac9cFieldFeedbackSettings,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_freewheel_voltage import (
    Ac9cFreewheelVoltageSettings,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_pid import (
    Ac9cPidSettings,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_potential_source import (
    Ac9cPotentialSourceSettings,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_power_stage import (
    ac9c_power_stage_type_from_psse,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_rectifier_bridge import (
    Ac9cRectifierBridgeSettings,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_rectifier_sources import (
    ac9c_potential_source_selection_from_psse,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_rectifier_supply import (
    Ac9cRectifierSupplySettings,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_rotating_exciter import (
    Ac9cRotatingExciterSettings,
)
from VeraGridEngine.Templates.Rms.excitation_systems.ac11c import (
    Ac11cLimiterLocation, Ac11cParameters, Ac11cPowerSource, Ac11cPssLocation,
    build_ac11c_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.st4c import FilteredCompoundPiParameters, CompoundExcitationSource, CompoundSupplementLocation, build_st4c_template
from VeraGridEngine.Templates.Rms.excitation_systems.st4b import CompoundPiExciterParameters, build_st4b_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac6a import (
    Ac6aParameters, build_ac6a_template, build_esac6a_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.self_feedback_exciter import ExcitationBridgeDynamics, ExcitationLimiterLocation, SelfFeedbackExciterParameters, build_self_feedback_exciter
from VeraGridEngine.Templates.Rms.excitation_systems.esst1a import StaticMinimumExcitationLocation, StaticMaximumExcitationLocation, StaticStabilizerLocation, TerminalFedExciterParameters, build_esst1a_template
from VeraGridEngine.Templates.Rms.excitation_systems.budczt import LimitedPiExciterParameters, build_budczt_template
from VeraGridEngine.Templates.Rms.excitation_systems.bbsex1 import AuxiliaryVoltageLocation, FeedbackStaticExciterParameters, build_bbsex1_template
from VeraGridEngine.Templates.Rms.excitation_systems.thevenin_exciter import CompoundCapabilityLocation, TheveninExciterParameters, build_thevenin_exciter
from VeraGridEngine.Templates.Rms.excitation_systems.dc_exciter import DcExciterKind, DcExciterParameters, RotatingLimiterLocation, build_dc_exciter
from VeraGridEngine.Templates.Rms.excitation_systems.electromechanical_exciter import (
    ElectromechanicalExciterKind, ElectromechanicalExciterParameters, build_electromechanical_exciter)
from VeraGridEngine.Templates.Rms.excitation_systems.alternator_rectifier import (
    AlternatorRectifierKind, AlternatorRectifierParameters, RectifierLimiterLocation, build_alternator_rectifier,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Templates.Rms.buses.bus_rms_template import initialize_bus_rms
from VeraGridEngine.Utils.Symbolic.symbolic import Var, Expr, Const
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.enumerations import InternationalStandardModel, DeviceType, VarPowerFlowReferenceType
from VeraGridEngine.enumerations import InductionMachineRole
if TYPE_CHECKING:
    from VeraGridEngine.IO.raw.auxiliary_to_veragrid import PsseAuxiliaryConverter


class PsseDynamicRole(Enum):
    """Distinct physical and controller attachment roles."""
    MACHINE = 'machine'
    GOVERNOR = 'governor'
    TURBINE_LOAD_CONTROLLER = 'turbine_load_controller'
    EXCITER = 'exciter'
    STABILIZER = 'stabilizer'
    COMPENSATOR = 'compensator'
    UNDEREXCITATION = 'underexcitation'
    OVEREXCITATION = 'overexcitation'
    RENEWABLE_CONVERTER = 'renewable_converter'
    DERA_CONVERTER = 'dera_converter'
    RENEWABLE_ELECTRICAL_CONTROL = 'renewable_electrical_control'
    RENEWABLE_PLANT_CONTROL = 'renewable_plant_control'
    RENEWABLE_MECHANICAL_CONTROL = 'renewable_mechanical_control'
    LOAD_MOTOR = 'load_motor'


class PsseStabilizerInput(Enum):
    """Documented integer selectors, owned exclusively by the source adapter."""

    BLOCKED = 0
    ROTOR_SPEED = 1
    BUS_FREQUENCY = 2
    ELECTRICAL_POWER = 3
    ACCELERATING_POWER = 4
    BUS_VOLTAGE = 5
    VOLTAGE_DERIVATIVE = 6


class PsseDynamicBinding:
    """Explicit source model, role and native parameter-name correspondence."""
    __slots__ = ('role', 'standard', 'parameters', 'dc_kind', 'electromechanical_kind')

    def __init__(self, role: PsseDynamicRole, standard: InternationalStandardModel | None,
                 parameters: tuple[tuple[str, str], ...] = (),
                 dc_kind: DcExciterKind | None = None,
                 electromechanical_kind: ElectromechanicalExciterKind | None = None) -> None:
        """Store a reviewed mapping, not a name-based inference.

        :param role: Physical/controller role.
        :param standard: Existing catalogue builder, or None for network-ready templates.
        :param parameters: Exact CON-name to symbolic-parameter pairs.
        :param dc_kind: Reviewed DC-exciter equation structure, when applicable.
        :param electromechanical_kind: Reviewed reset and rapid-forcing structure, when applicable.
        """
        self.role: PsseDynamicRole = role
        self.standard: InternationalStandardModel | None = standard
        self.parameters: tuple[tuple[str, str], ...] = parameters
        self.dc_kind: DcExciterKind | None = dc_kind
        self.electromechanical_kind: ElectromechanicalExciterKind | None = electromechanical_kind


def dynamic_record_name(record: DyrRecord) -> str:
    """Select reviewed source identity without renaming a user-model assignment.

    Generic user headers never resolve by arbitrary subroutine name alone.
    Only a release-owned schema with a matching complete calling contract may
    select a user-model binding. Original keyword, header and tokens stay intact.

    :param record: Source record retaining its parser-selected schema.
    :return: Reviewed source subroutine or original assignment keyword.
    """
    if (record.user_schema is not None and record.user_header is not None
            and record.user_schema.matches(record.user_header)):
        return record.user_schema.layout.name
    else:
        return record.model.upper()


def dynamic_binding(model: str) -> PsseDynamicBinding | None:
    """Get the explicit standard-library binding.

    :param model: PSS/E model name.
    :return: Reviewed binding or None; no reflection or plugin execution.
    """
    ac1_parameters: tuple[tuple[str, str], ...] = (('TR','avr_tR'),('TB','avr_tB'),('TC','avr_tC'),('KA','avr_Ka'),('TA','avr_tA'),('VRMAX','avr_VrMaxPu'),('VRMIN','avr_VrMinPu'),('TE','avr_tE'),('KF','avr_Kf'),('TF','avr_tF'),('KC','avr_Kc'),('KD','avr_Kd'),('KE','avr_Ke'),('E1','avr_VExcLowPu'),('SE1','avr_VExcSatLowPu'),('E2','avr_VExcHighPu'),('SE2','avr_VExcSatHighPu'))
    amplifier_ac1_parameters: tuple[tuple[str, str], ...] = tuple(
        ('VAMAX' if source == 'VRMAX' else ('VAMIN' if source == 'VRMIN' else source), target)
        for source, target in ac1_parameters)
    gated_ac1_parameters: tuple[tuple[str, str], ...] = amplifier_ac1_parameters + (('VRMAX','BridgeVRMAX'),('VRMIN','BridgeVRMIN'))
    shaped_ac5_parameters: tuple[tuple[str,str],...] = tuple(('TF1' if source == 'TF' else source,target) for source,target in ac1_parameters if source not in ('TB','TC')) + (('TF2','avr_tB'),('TF3','avr_tC'),('VFEMAX','VFEMAX'),('VEMIN','VEMIN'))
    bindings: dict[str, PsseDynamicBinding] = dict(
        GENCLS=PsseDynamicBinding(PsseDynamicRole.MACHINE, None),
        CIMTR1=PsseDynamicBinding(PsseDynamicRole.MACHINE, InternationalStandardModel.CIMTR1),
        CIMTR2=PsseDynamicBinding(PsseDynamicRole.MACHINE, InternationalStandardModel.CIMTR2),
        CIMTR3=PsseDynamicBinding(PsseDynamicRole.MACHINE, InternationalStandardModel.CIMTR3),
        CIMTR4=PsseDynamicBinding(PsseDynamicRole.MACHINE, InternationalStandardModel.CIMTR4),
        CIM5AL=PsseDynamicBinding(PsseDynamicRole.LOAD_MOTOR, InternationalStandardModel.CIM5),
        CIM5AR=PsseDynamicBinding(PsseDynamicRole.LOAD_MOTOR, InternationalStandardModel.CIM5),
        CIM5BL=PsseDynamicBinding(PsseDynamicRole.LOAD_MOTOR, InternationalStandardModel.CIM5),
        CIM5OW=PsseDynamicBinding(PsseDynamicRole.LOAD_MOTOR, InternationalStandardModel.CIM5),
        CIM5ZN=PsseDynamicBinding(PsseDynamicRole.LOAD_MOTOR, InternationalStandardModel.CIM5),
        CIM6AL=PsseDynamicBinding(PsseDynamicRole.LOAD_MOTOR, InternationalStandardModel.CIM6),
        CIM6AR=PsseDynamicBinding(PsseDynamicRole.LOAD_MOTOR, InternationalStandardModel.CIM6),
        CIM6BL=PsseDynamicBinding(PsseDynamicRole.LOAD_MOTOR, InternationalStandardModel.CIM6),
        CIM6OW=PsseDynamicBinding(PsseDynamicRole.LOAD_MOTOR, InternationalStandardModel.CIM6),
        CIM6ZN=PsseDynamicBinding(PsseDynamicRole.LOAD_MOTOR, InternationalStandardModel.CIM6),
        CIMWAL=PsseDynamicBinding(PsseDynamicRole.LOAD_MOTOR, InternationalStandardModel.CIMW),
        CIMWAR=PsseDynamicBinding(PsseDynamicRole.LOAD_MOTOR, InternationalStandardModel.CIMW),
        CIMWBL=PsseDynamicBinding(PsseDynamicRole.LOAD_MOTOR, InternationalStandardModel.CIMW),
        CIMWOW=PsseDynamicBinding(PsseDynamicRole.LOAD_MOTOR, InternationalStandardModel.CIMW),
        CIMWZN=PsseDynamicBinding(PsseDynamicRole.LOAD_MOTOR, InternationalStandardModel.CIMW),
        CMLDBLU2=PsseDynamicBinding(PsseDynamicRole.LOAD_MOTOR, None),
        CMLDOWU2=PsseDynamicBinding(PsseDynamicRole.LOAD_MOTOR, None),
        CMLDZNU2=PsseDynamicBinding(PsseDynamicRole.LOAD_MOTOR, None),
        CMLDARU2=PsseDynamicBinding(PsseDynamicRole.LOAD_MOTOR, None),
        CMLDALU2=PsseDynamicBinding(PsseDynamicRole.LOAD_MOTOR, None),
        GENROU=PsseDynamicBinding(PsseDynamicRole.MACHINE, None),
        GENROE=PsseDynamicBinding(PsseDynamicRole.MACHINE, InternationalStandardModel.GENROE),
        GENTRA=PsseDynamicBinding(PsseDynamicRole.MACHINE, InternationalStandardModel.GENTRA),
        GENSAL=PsseDynamicBinding(PsseDynamicRole.MACHINE, InternationalStandardModel.GENSAL),
        GENSAE=PsseDynamicBinding(PsseDynamicRole.MACHINE, InternationalStandardModel.GENSAE),
        REGCA1=PsseDynamicBinding(PsseDynamicRole.RENEWABLE_CONVERTER, None),
        REGCAU1=PsseDynamicBinding(PsseDynamicRole.RENEWABLE_CONVERTER, None),
        DERA1=PsseDynamicBinding(PsseDynamicRole.DERA_CONVERTER, None),
        REECA1=PsseDynamicBinding(PsseDynamicRole.RENEWABLE_ELECTRICAL_CONTROL, None),
        REECAU1=PsseDynamicBinding(PsseDynamicRole.RENEWABLE_ELECTRICAL_CONTROL, None),
        REECC1=PsseDynamicBinding(PsseDynamicRole.RENEWABLE_ELECTRICAL_CONTROL, None),
        REPCA1=PsseDynamicBinding(PsseDynamicRole.RENEWABLE_PLANT_CONTROL, None),
        REPCTA1=PsseDynamicBinding(PsseDynamicRole.RENEWABLE_PLANT_CONTROL, None),
        REPCAU1=PsseDynamicBinding(PsseDynamicRole.RENEWABLE_PLANT_CONTROL, None),
        REPCTAU1=PsseDynamicBinding(PsseDynamicRole.RENEWABLE_PLANT_CONTROL, None),
        WTDTA1=PsseDynamicBinding(PsseDynamicRole.RENEWABLE_MECHANICAL_CONTROL, None),
        WTDTAU1=PsseDynamicBinding(PsseDynamicRole.RENEWABLE_MECHANICAL_CONTROL, None),
        WTARA1=PsseDynamicBinding(PsseDynamicRole.RENEWABLE_MECHANICAL_CONTROL, None),
        WTARAU1=PsseDynamicBinding(PsseDynamicRole.RENEWABLE_MECHANICAL_CONTROL, None),
        WTTQA1=PsseDynamicBinding(PsseDynamicRole.RENEWABLE_MECHANICAL_CONTROL, None),
        WTTQAU1=PsseDynamicBinding(PsseDynamicRole.RENEWABLE_MECHANICAL_CONTROL, None),
        WTPTA1=PsseDynamicBinding(PsseDynamicRole.RENEWABLE_MECHANICAL_CONTROL, None),
        WTPTAU1=PsseDynamicBinding(PsseDynamicRole.RENEWABLE_MECHANICAL_CONTROL, None),
        GGOV1=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.GGOV1),
        GGOV1D=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.GGOV1D),
        GGOV1DU=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.GGOV1D),
        DEGOV=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.DEGOV),
        DEGOV1D=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.DEGOV1D),
        DEGOV1DU=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.DEGOV1D),
        DEGOV1=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.DEGOV1),
        IEEEG1=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.IEEEG1),
        IEEEG1D=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.IEEEG1D),
        IEEEG1SDU=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.IEEEG1D),
        LCFB1=PsseDynamicBinding(PsseDynamicRole.TURBINE_LOAD_CONTROLLER, InternationalStandardModel.LCFB1),
        GASTD=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.GASTD),
        GASTDU=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.GASTD),
        IEESGOD=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.IEESGOD),
        IEESGODU=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.IEESGOD),
        PIDGOV=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.PIDGOV),
        PIDGOVD=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.PIDGOVD),
        PIDGOVDU=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.PIDGOVD),
        HYGOV2=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.HYGOV2),
        HYGOV2D=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.HYGOV2D),
        HYGOV2DU=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.HYGOV2D),
        HYGOVD=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.HYGOVD),
        HYGOVDU=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.HYGOVD),
        HYGOVR1=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.HYGOVR1),
        BBGOV1=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.BBGOV1),
        TGOV1D=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.TGOV1D),
        TGOV1DU=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.TGOV1D),
        TGOV1=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, None),
        TGOV2=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.TGOV2),
        TGOV3=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.TGOV3),
        TGOV3D=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.TGOV3),
        TGOV3DU=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.TGOV3),
        WESGOV=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, None),
        WESGOVD=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, None),
        WESGOVDU=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, None),
        IEEEG3=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.IEEEG3),
        IEEEG3D=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.IEEEG3D),
        IEEEG3DU=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.IEEEG3D),
        GAST=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.GAST),
        IEESGO=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.IEESGO),
        IEEEG2=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.IEEEG2,
            (('K','gov_K'),('T1','gov_t1'),('T2','gov_t2'),('T3','gov_t3'),
             ('PMAX','gov_PMaxPu'),('PMIN','gov_PMinPu'),('T4','gov_t4'))),
        IVOGO=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.IVOGO),
        IVOST=PsseDynamicBinding(PsseDynamicRole.STABILIZER, InternationalStandardModel.IVOST),
        STAB1=PsseDynamicBinding(PsseDynamicRole.STABILIZER, InternationalStandardModel.STAB1),
        STAB2A=PsseDynamicBinding(PsseDynamicRole.STABILIZER, InternationalStandardModel.STAB2A),
        STAB3=PsseDynamicBinding(PsseDynamicRole.STABILIZER, InternationalStandardModel.STAB3),
        STAB4=PsseDynamicBinding(PsseDynamicRole.STABILIZER, InternationalStandardModel.STAB4),
        STABNI=PsseDynamicBinding(PsseDynamicRole.STABILIZER, InternationalStandardModel.STABNI),
        IEEEST=PsseDynamicBinding(PsseDynamicRole.STABILIZER, InternationalStandardModel.IEEEST),
        BEPSST=PsseDynamicBinding(PsseDynamicRole.STABILIZER, InternationalStandardModel.BEPSST, (
            ('K1','K1'),('K2','K2'),('T1','T1'),('T2','T2'),('T3','T3'),('T4','T4'),
            ('T5','T5'),('T6','T6'),('T7','T7'),('T8','T8'),('T9','T9'),('T10','T10'),
            ('LSMAX','LSMAX'),('LSMIN','LSMIN'),('VCU','VCU'),('VCL','VCL'),
        )),
        OSTB2T=PsseDynamicBinding(PsseDynamicRole.STABILIZER, InternationalStandardModel.OSTB2T, (
            ('K','K'),('TS','TS'),('T1_T3','T1_T3'),('T3','T3'),('T2_T4','T2_T4'),
            ('T4','T4'),('HLIM','HLIM'),('LLIM','LLIM'),('KANG','KANG'),('TANG','TANG'),
            ('VNGMX','VNGMX'),('VMGMX','VMGMX'),('T_ON','T_ON'),('T_OFF','T_OFF'),
            ('VSMX','VSMX'),('VSMN','VSMN'),('DWTHR','DWTHR'),('ETHR','ETHR'),
            ('EFDTHR','EFDTHR'),('TSEAL','TSEAL'),
        )),
        OSTB5T=PsseDynamicBinding(PsseDynamicRole.STABILIZER, InternationalStandardModel.OSTB5T, (
            ('K','K'),('TS','TS'),('T1','T1_T3'),('T2','T2_T4'),('T3_T4','T3'),('T4','T4'),
            ('HLIM','HLIM'),('LLIM','LLIM'),('KANG','KANG'),('TANG','TANG'),
            ('VNGMX','VNGMX'),('VMGMX','VMGMX'),('T_ON','T_ON'),('T_OFF','T_OFF'),
            ('VSMX','VSMX'),('VSMN','VSMN'),('DWTHR','DWTHR'),('ETHR','ETHR'),
            ('EFDTHR','EFDTHR'),('TSEAL','TSEAL'),
        )),
        PSS2A=PsseDynamicBinding(PsseDynamicRole.STABILIZER, InternationalStandardModel.PSS2A),
        PSS3B=PsseDynamicBinding(PsseDynamicRole.STABILIZER, InternationalStandardModel.PSS3B),
        PSS2C=PsseDynamicBinding(PsseDynamicRole.STABILIZER, InternationalStandardModel.PSS2C),
        PSS6C=PsseDynamicBinding(PsseDynamicRole.STABILIZER, InternationalStandardModel.PSS6C, (
            ('T1','pss_t1'),('KS2','pss_Ks2'),('T2','pss_t2'),('KS1','pss_Ks1'),
            ('T3','pss_t3'),('MACC','pss_MAcc'),('T4','pss_t4'),('TD','pss_tD'),
            ('K0','pss_K0'),('K1','pss_K1'),('K2','pss_K2'),('K3','pss_K3'),('K4','pss_K4'),
            ('TI1','pss_tI1'),('TI2','pss_tI2'),('KI3','pss_Ki3'),('TI3','pss_tI3'),
            ('KI4','pss_Ki4'),('TI4','pss_tI4'),('KS','pss_Ks'),
            ('VSL1MAX','pss_PGenMaxPu'),('VSL1MIN','pss_PGenMinPu'),
            ('VSL2MAX','pss_OmegaMaxPu'),('VSL2MIN','pss_OmegaMinPu'),
            ('VSTMAX','pss_VPssMaxPu'),('VSTMIN','pss_VPssMinPu'),
            ('PSSON','pss_PPssOnPu'),('PSSOFF','pss_PPssOffPu'),
            ('XCOMP','pss_Xcomp'),('TCOMP','pss_Tcomp'),
        )),
        PSS7C=PsseDynamicBinding(PsseDynamicRole.STABILIZER, InternationalStandardModel.PSS7C, (
            ('TW1','TW1'),('KW2','KW2'),('T6','T6'),('TW3','TW3'),('TW4','TW4'),('T7','T7'),
            ('KS2','KS2'),('KS3','KS3'),('T8','T8'),('T9','T9'),('KS1','KS1'),
            ('K0','K0'),('K1','K1'),('K2','K2'),('K3','K3'),('K4','K4'),
            ('TI1','TI1'),('TI2','TI2'),('KI3','KI3'),('TI3','TI3'),('KI4','KI4'),('TI4','TI4'),
            ('VSL1MAX','VSL1MAX'),('VSL1MIN','VSL1MIN'),('VSL2MAX','VSL2MAX'),('VSL2MIN','VSL2MIN'),
            ('VSTMAX','VSTMAX'),('VSTMIN','VSTMIN'),('PSSON','PSSON'),('PSSOFF','PSSOFF'),
            ('XCOMP','XCOMP'),('TCOMP','TCOMP'),
        )),
        PSS2B=PsseDynamicBinding(PsseDynamicRole.STABILIZER, InternationalStandardModel.PSS2B),
        PSS4B=PsseDynamicBinding(PsseDynamicRole.STABILIZER, InternationalStandardModel.PSS4B),
        IEE2ST=PsseDynamicBinding(PsseDynamicRole.STABILIZER, InternationalStandardModel.IEE2ST),
        COMP=PsseDynamicBinding(PsseDynamicRole.COMPENSATOR, InternationalStandardModel.COMP),
        COMPCC=PsseDynamicBinding(PsseDynamicRole.COMPENSATOR, InternationalStandardModel.COMPCC, (
            ('R1','R1'),('X1','X1'),('R2','R2'),('X2','X2'),
        )),
        IEEEVC=PsseDynamicBinding(PsseDynamicRole.COMPENSATOR, InternationalStandardModel.IEEEVC_1981,
            (('RC','RcPu'),('XC','XcPu'))),
        CCOMP4A=PsseDynamicBinding(PsseDynamicRole.COMPENSATOR, InternationalStandardModel.CCOMP4A, (
            ('K1','K1'),('K2','K2'),('K3','K3'),('K4','K4'),
            ('KC','Kc'),('VMAX','Vmax'),('VMIN','Vmin'),
        )),
        CCOMP4U1=PsseDynamicBinding(PsseDynamicRole.COMPENSATOR, InternationalStandardModel.CCOMP4A, (
            ('K1','K1'),('K2','K2'),('K3','K3'),('K4','K4'),
            ('KC','Kc'),('VMAX','Vmax'),('VMIN','Vmin'),
        )),
        REMCMP=PsseDynamicBinding(PsseDynamicRole.COMPENSATOR, InternationalStandardModel.REMCMP),
        MNLEX1=PsseDynamicBinding(PsseDynamicRole.UNDEREXCITATION, InternationalStandardModel.MNLEX1),
        MNLEX2=PsseDynamicBinding(PsseDynamicRole.UNDEREXCITATION, InternationalStandardModel.MNLEX2),
        MNLEX3=PsseDynamicBinding(PsseDynamicRole.UNDEREXCITATION, InternationalStandardModel.MNLEX3),
        UEL1=PsseDynamicBinding(PsseDynamicRole.UNDEREXCITATION, InternationalStandardModel.UEL1, (
            ('KUR','KUR'),('KUC','KUC'),('KUF','KUF'),('VURMAX','VURMAX'),
            ('VUCMAX','VUCMAX'),('KUI','KUI'),('KUL','KUL'),('VUIMAX','VUIMAX'),
            ('VUIMIN','VUIMIN'),('TU1','TU1'),('TU2','TU2'),('TU3','TU3'),
            ('TU4','TU4'),('VULMAX','VULMAX'),('VULMIN','VULMIN'),
        )),
        UEL2C=PsseDynamicBinding(PsseDynamicRole.UNDEREXCITATION, InternationalStandardModel.UEL2C, (
            ('TUV','uel_tUV'),('TUP','uel_tUP'),('TUQ','uel_tUQ'),
            ('KUI','uel_Kui'),('KUL','uel_Kul'),('VUIMAX','uel_VUiMaxPu'),('VUIMIN','uel_VUiMinPu'),
            ('KUF','uel_Kuf'),('KFB','uel_KFb'),('TUL','uel_tUl'),('TU1','uel_tU1'),('TU2','uel_tU2'),
            ('TU3','uel_tU3'),('TU4','uel_tU4'),('VULMAX','uel_VULMaxPu'),('VULMIN','uel_VULMinPu'),
            ('KFIX','uel_KFix'),('TADJ','uel_tAdj'),('TQREF','uel_tQRef'),
            ('VUELMAX2','uel_VUel2MaxPu'),('VUELMIN2','uel_VUel2MinPu'),
            ('VUELMAX1','uel_VUel1MaxPu'),('VUELMIN1','uel_VUel1MinPu'),('XQ','uel_XqPu'),
        )),
        OEL2C=PsseDynamicBinding(PsseDynamicRole.OVEREXCITATION, InternationalStandardModel.OEL2C, (
            ('TC1OEL','oel_tC1Oel'),('TB1OEL','oel_tB1Oel'),('TC2OEL','oel_tC2Oel'),('TB2OEL','oel_tB2Oel'),
            ('KPOEL','oel_KpOel'),('KIOEL','oel_KiOel'),('KDOEL','oel_KdOel'),('TDOEL','oel_tDOel'),
            ('VOELMAX3','oel_VOel3MaxPu'),('VOELMIN3','oel_VOel3MinPu'),('VOELMAX2','oel_VOel2MaxPu'),
            ('VOELMIN2','oel_VOel2MinPu'),('VOELMAX1','oel_VOel1MaxPu'),('VOELMIN1','oel_VOel1MinPu'),
            ('IRESET','oel_IResetPu'),('TEN','oel_tEn'),('TOFF','oel_tOff'),('ITHOFF','oel_IThOffPu'),
            ('KSCALE','oel_KScale'),('TROEL','oel_tROel'),('KACT','oel_KAct'),('ITFPU','oel_ITfPu'),
            ('IINST','oel_IInstPu'),('ILIM','oel_ILimPu'),('TAOEL','oel_tAOel'),('C1','oel_C1'),('K1','oel_K1'),
            ('C2','oel_C2'),('K2','oel_K2'),('VINVMAX','oel_VInvMaxPu'),('VINVMIN','oel_VInvMinPu'),
            ('FixedRU','oel_FixedRu'),('FixedRD','oel_FixedRd'),('TFCL','oel_tFcl'),('TMAX','oel_tMax'),
            ('TMIN','oel_tMin'),('KFB','oel_KFb'),('KRD','oel_Krd'),('KRU','oel_Kru'),
            ('KZRU','oel_Kzru'),('IFDRATED','oel_IfdRatedPu'),
        )),
        MAXEX1=PsseDynamicBinding(PsseDynamicRole.OVEREXCITATION, InternationalStandardModel.MAXEX2),
        MAXEX2=PsseDynamicBinding(PsseDynamicRole.OVEREXCITATION, InternationalStandardModel.MAXEX2),
        HYGOV=PsseDynamicBinding(PsseDynamicRole.GOVERNOR, InternationalStandardModel.HYGOV,
            (('R','Rperm'),('r','Rtemp'),('Tr','Tr'),('Tf','Tf'),('Tg','Tg'),('VELM','Velm'),('GMAX','Gmax'),('GMIN','Gmin'),('Tw','Tw'),('At','At'),('Dturb','Dturb'),('qNL','Qnl'))),
        EXST1=PsseDynamicBinding(PsseDynamicRole.EXCITER, None),
        EXST2A=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.EXST2A),
        ESST2A=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.ESST2A),
        EXST2=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.EXST2),
        IEEET1=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.IEEET1,dc_kind=DcExciterKind.TYPE1),
        EXPIC1=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.EXPIC1),
        EXNI=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.EXNI),
        IEET1B=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.IEET1B),
        IEET1A=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.IEET1A,dc_kind=DcExciterKind.LIMITED_TYPE1),
        IEEET4=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.IEEET4,
            electromechanical_kind=ElectromechanicalExciterKind.DEADBAND_RESET),
        IEEET5=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.IEEET5,
            electromechanical_kind=ElectromechanicalExciterKind.INTEGRAL_RESET),
        DC4C=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.DC4C),
        DC4B=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.DC4B),
        DC3A=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.DC3A,
            electromechanical_kind=ElectromechanicalExciterKind.BOUNDED_NORMALIZED_RESET),
        IEEEX4=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.IEEEX4,
            electromechanical_kind=ElectromechanicalExciterKind.NORMALIZED_RESET),
        IEET5A=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.IEET5A,
            electromechanical_kind=ElectromechanicalExciterKind.LAG_OR_INTEGRAL),
        IEEEX1=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.IEEEX1,dc_kind=DcExciterKind.COMPENSATED_TYPE1),
        ESDC1A=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.ESDC1A,dc_kind=DcExciterKind.DC1A),
        ESDC2A=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.ESDC2A,dc_kind=DcExciterKind.DC2A),
        EXDC2=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.EXDC2,dc_kind=DcExciterKind.DC2),
        IEEET2=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.IEEET2,dc_kind=DcExciterKind.TYPE2),
        IEEEX2=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.IEEEX2,dc_kind=DcExciterKind.COMPENSATED_TYPE2),
        IEEX2A=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.IEEX2A,dc_kind=DcExciterKind.TYPE2A),
        BBSEX1=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.BBSEX1),
        BUDCZT=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.BUDCZT),
        ST6C=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.ST6C),
        ST6B=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.ST6B, (
            ('TR','avr_tR'),('KPA','avr_Kpa'),('KIA','avr_Kia'),('KDA','avr_Kda'),
            ('TDA','avr_tDa'),('VAMAX','avr_VaMaxPu'),('VAMIN','avr_VaMinPu'),
            ('KFF','avr_Kff'),('KM','avr_Km'),('KCI','avr_Kcl'),('KLR','avr_Klr'),
            ('ILR','avr_IlrPu'),('VRMAX','avr_VrMaxPu'),('VRMIN','avr_VrMinPu'),
            ('KG','avr_Kg'),('TG','avr_tG'),
        )),
        ST9C=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.ST9C),
        ST10C=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.ST10C),
        ST8C=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.ST8C),
        ST5C=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.ST5C),
        ST5B=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.ST5B),
        AC7C=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.AC7C),
        AC6C=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.AC6C),
        AC6C2=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.AC6C2),
        AC6A=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.AC6A,
            (('TR','TR'),('KA','KA'),('TA','TA'),('TK','TK'),('TB','TB'),('TC','TC'),
             ('VAMAX','VAMAX'),('VAMIN','VAMIN'),('VRMAX','VRMAX'),('VRMIN','VRMIN'),
             ('TE','TE'),('VFELIM','VFELIM'),('KH','KH'),('VHMAX','VHMAX'),('TH','TH'),
             ('TJ','TJ'),('KC','KC'),('KD','KD'),('KE','KE'),('E1','E1'),('SE1','SE1'),
             ('E2','E2'),('SE2','SE2'))),
        ESAC6A=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.ESAC6A,
            (('TR','TR'),('KA','KA'),('TA','TA'),('TK','TK'),('TB','TB'),('TC','TC'),
             ('VAMAX','VAMAX'),('VAMIN','VAMIN'),('VRMAX','VRMAX'),('VRMIN','VRMIN'),
             ('TE','TE'),('VFELIM','VFELIM'),('KH','KH'),('VHMAX','VHMAX'),('TH','TH'),
             ('TJ','TJ'),('KC','KC'),('KD','KD'),('KE','KE'),('E1','E1'),('SE1','SE1'),
             ('E2','E2'),('SE2','SE2'))),
        AC7B=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.AC7B),
        AC8C=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.AC8C),
        AC9C=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.AC9C),
        AC11C=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.AC11C),
        AC8B=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.AC8B),
        ST4C=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.ST4C),
        ESST4B=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.ST4B),
        ST7B=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.ST7B),
        ST7C=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.ST7C),
        ST1C=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.ST1C),
        ESST1A=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.ESST1A),
        IEEET3=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.IEEET3),
        IEEEX3=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.IEEEX3),
        DC1C=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.DC1C,dc_kind=DcExciterKind.BOUNDED_FIXED_SUPPLY),
        DC2C=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.DC2C,dc_kind=DcExciterKind.BOUNDED_TERMINAL_SUPPLY),
        ESAC8B=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.ESAC8B),
        ESAC5A=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.ESAC5A,dc_kind=DcExciterKind.BRUSHLESS),
        EXAC4=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.EXAC4),
        AC4C=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.AC4C),
        ESAC4A=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.ESAC4A),
        ESST3A=PsseDynamicBinding(PsseDynamicRole.EXCITER, None),
        SEXS=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.SEXS,
            (('TB','Tb'),('K','K'),('TE','Te'),('EMIN','EMin'),('EMAX','EMax'))),
        SCRX=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.SCRX,
            (('TB','avr_tB'),('K','avr_K'),('TE','avr_tE'),('EMIN','avr_VrMinPu'),
             ('EMAX','avr_VrMaxPu'),('CSWITCH','avr_CSwitch'),('RC_RFD','avr_RcToRfd'))),
        EXBAS=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.EXBAS,
            ac1_parameters+(('KP','KP'),('KI','KI'),('TF1','TF1'),('TF2','TF2'))),
        EXAC1=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.EXAC1,
            ac1_parameters),
        EXAC1A=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.EXAC1A,ac1_parameters),
        AC5C=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.AC5C,shaped_ac5_parameters),
        AC1C=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.AC1C,gated_ac1_parameters+(('VFEMAX','VFEMAX'),('VEMIN','VEMIN'))),
        AC2C=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.AC2C,gated_ac1_parameters+(('KB','KB'),('KH','KH'),('VFEMAX','VFEMAX'),('VEMIN','VEMIN'))),
        ESAC1A=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.ESAC1A,gated_ac1_parameters),
        ESAC2A=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.ESAC2A,
            gated_ac1_parameters+(('KB','KB'),('KH','KH'),('VFEMAX','VFEMAX'))),
        ESAC3A=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.ESAC3A,
            amplifier_ac1_parameters+(('KR','KR'),('KN','KN'),('EFDN','EFDN'),('VEMIN','VEMIN'),('VFEMAX','VFEMAX'))),
        EXAC2=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.EXAC2,
            gated_ac1_parameters+(('KB','KB'),('KL','KL'),('KH','KH'),('VLR','VLR'))),
        EXAC3=PsseDynamicBinding(PsseDynamicRole.EXCITER, InternationalStandardModel.EXAC3,
            amplifier_ac1_parameters+(('KLV','KLV'),('KR','KR'),('KN','KN'),('EFDN','EFDN'),('VLV','VLV'))),
    )
    return bindings.get(model.upper(), None)


def named_parameter(record: DyrRecord, name: str) -> float:
    """Read a required constant from the already validated source schema.

    :param record: Valid DYR record.
    :param name: Exact schema parameter name (case-sensitive, including HYGOV R/r).
    :return: Parsed constant.
    :raises ValueError: Schema/binding mismatch, handled at the record boundary.
    """
    for parameter in record.parameters:
        if parameter.name == name:
            return parameter.value
        else:
            pass
    raise ValueError('DYR binding parameter absent: ' + name)


def convert_psse_cim_load_record(
        context: PsseAuxiliaryConverter,
        source: str,
        record: DyrRecord,
        occupied_loads: set[tuple[int, str]],
) -> None:
    """Bind one reviewed 35.2 CIM record to its exact RAW load scope.

    Each selected load receives a separately initialized motor on its resolved
    motor base. The load's RMS model is replaced only after all selected loads
    have a valid electrical operating point and a complete native template.

    :param context: Native network, source RAW data and conversion ledger.
    :param source: DYR source filename.
    :param record: Valid CIM5, CIM6 or CIMW record.
    :param occupied_loads: Load identities already claimed by another DYR record.
    :return: None.
    """
    if record.status != RecordStatus.VALID:
        context.record(
            source, record.line_number, PsseFileType.DYR,
            PsseConversionStatus.INVALID, (), 'Invalid PSS/E CIM load model record',
        )
    elif not isinstance(record.identifier, int):
        context.record(
            source, record.line_number, PsseFileType.DYR,
            PsseConversionStatus.INVALID, (), 'PSS/E CIM scope identifier must be an integer',
        )
    else:
        model_name: str = record.model.upper()
        scope: str = model_name[-2:]
        scope_identifier: int = record.identifier
        if scope == 'BL':
            scope_valid: bool = scope_identifier > 0
        elif scope == 'AR' or scope == 'OW' or scope == 'ZN':
            scope_valid = scope_identifier > 0
        elif scope == 'AL':
            scope_valid = scope_identifier == 0
        else:
            scope_valid = False
        if not scope_valid:
            context.record(
                source, record.line_number, PsseFileType.DYR,
                PsseConversionStatus.INVALID, (), 'Invalid PSS/E CIM load scope: ' + scope,
            )
        elif len(record.icons) != 1 or record.icons[0] not in (1, 2):
            context.record(
                source, record.line_number, PsseFileType.DYR,
                PsseConversionStatus.INVALID, (), 'PSS/E CIM motor type IT must be 1 or 2',
            )
        else:
            model: PsseCimMotorModel
            if model_name.startswith('CIM5'):
                model = PsseCimMotorModel.CIM5
            elif model_name.startswith('CIM6'):
                model = PsseCimMotorModel.CIM6
            elif model_name.startswith('CIMW'):
                model = PsseCimMotorModel.CIMW
            else:
                model = PsseCimMotorModel.CIM5
            motor_type: PsseCimMotorType = PsseCimMotorType(record.icons[0])
            selected_raw_loads: list[RawLoadLike] = list()
            raw_load: RawLoadLike
            for raw_load in context.source.loads:
                load_id: str = str(raw_load.ID).replace("'", '').strip()
                id_matches: bool = record.equipment_id == '*' or load_id == record.equipment_id
                scope_matches: bool
                if scope == 'BL':
                    scope_matches = raw_load.I == scope_identifier
                elif scope == 'AR':
                    scope_matches = raw_load.AREA == scope_identifier
                elif scope == 'OW':
                    scope_matches = raw_load.OWNER == scope_identifier
                elif scope == 'ZN':
                    scope_matches = raw_load.ZONE == scope_identifier
                else:
                    scope_matches = True
                if raw_load.STATUS == 1 and id_matches and scope_matches:
                    selected_raw_loads.append(raw_load)
                else:
                    pass
            if len(selected_raw_loads) == 0:
                context.record(
                    source, record.line_number, PsseFileType.DYR,
                    PsseConversionStatus.UNRESOLVED, (), 'PSS/E CIM scope matched no active RAW loads',
                )
            else:
                staged: list[tuple[tuple[int, str], Load, RmsModelTemplate, Block]] = list()
                failure_message: str | None = None
                for raw_load in selected_raw_loads:
                    load_key: tuple[int, str] = (
                        raw_load.I, str(raw_load.ID).replace("'", '').strip(),
                    )
                    native_code: str = str(raw_load.I) + '_' + load_key[1]
                    native_loads: list[Load] = list(
                        native_load for native_load in context.grid.loads
                        if native_load.code == native_code
                    )
                    if load_key in occupied_loads:
                        failure_message = 'PSS/E CIM load scopes overlap at ' + native_code
                    elif len(native_loads) != 1:
                        failure_message = 'PSS/E CIM load identity is missing or ambiguous: ' + native_code
                    elif (
                        native_loads[0].rms_template is not None
                        or native_loads[0].rms_fmu_template is not None
                        or not native_loads[0].rms_model.empty()
                    ):
                        failure_message = 'PSS/E CIM cannot replace an existing load RMS model: ' + native_code
                    else:
                        raw_buses = list(bus for bus in context.source.buses if bus.I == raw_load.I)
                        if len(raw_buses) != 1:
                            failure_message = 'PSS/E CIM load bus is missing or ambiguous: ' + native_code
                        else:
                            motor_base_mva: float
                            if named_parameter(record, 'MBASE') > 0.0:
                                motor_base_mva = named_parameter(record, 'MBASE')
                            else:
                                motor_base_mva = named_parameter(record, 'PMULT') * raw_load.PL
                            parameters: PsseCimMotorParameters = PsseCimMotorParameters(
                                ra=named_parameter(record, 'RA'),
                                xa=named_parameter(record, 'XA'),
                                xm=named_parameter(record, 'XM'),
                                r1=named_parameter(record, 'R1'),
                                x1=named_parameter(record, 'X1'),
                                r2=named_parameter(record, 'R2'),
                                x2=named_parameter(record, 'X2'),
                                e1=named_parameter(record, 'E1'),
                                se1=named_parameter(record, 'SE1'),
                                e2=named_parameter(record, 'E2'),
                                se2=named_parameter(record, 'SE2'),
                                mbase=named_parameter(record, 'MBASE'),
                                pmult=named_parameter(record, 'PMULT'),
                                load_mw=raw_load.PL,
                                system_base_mva=context.source.SBASE,
                                inertia=named_parameter(record, 'H'),
                                vi=named_parameter(record, 'VI'),
                                ti=named_parameter(record, 'TI'),
                                tb=named_parameter(record, 'TB'),
                                damping=named_parameter(record, 'D') if model == PsseCimMotorModel.CIM5 else 0.0,
                                tnom=named_parameter(record, 'TNOM') if model != PsseCimMotorModel.CIMW else 0.0,
                                a=named_parameter(record, 'A') if model != PsseCimMotorModel.CIM5 else 0.0,
                                b=named_parameter(record, 'B') if model != PsseCimMotorModel.CIM5 else 0.0,
                                d=named_parameter(record, 'D') if model != PsseCimMotorModel.CIM5 else 0.0,
                                exponent=named_parameter(record, 'E') if model != PsseCimMotorModel.CIM5 else 1.0,
                                c0=named_parameter(record, 'C0') if model == PsseCimMotorModel.CIM6 else None,
                            )
                            operating_point = solve_psse_cim_motor_operating_point(
                                model=model,
                                motor_type=motor_type,
                                parameters=parameters,
                                voltage_magnitude=raw_buses[0].VM,
                                voltage_angle=math.radians(raw_buses[0].VA),
                                active_power_target=raw_load.PL / motor_base_mva,
                                reactive_power_target=raw_load.QL / motor_base_mva,
                                nominal_frequency_hz=context.source.BASFRQ,
                            )
                            if operating_point is None:
                                failure_message = 'PSS/E CIM steady-state operating point did not converge: ' + native_code
                            else:
                                parameters.operating_point = operating_point
                                parameters.torque_reference = operating_point[7]
                                parameters.q_adjustment = operating_point[8]
                                if model == PsseCimMotorModel.CIMW:
                                    parameters.c0 = calculate_cimw_c0(
                                        coefficient_a=parameters.a,
                                        coefficient_b=parameters.b,
                                        coefficient_d=parameters.d,
                                        exponent=parameters.exponent,
                                        initialized_speed=operating_point[0],
                                    )
                                else:
                                    pass
                                template: RmsModelTemplate = build_psse_cim_motor_template(
                                    vf=context.grid.var_factory,
                                    model=model,
                                    motor_type=motor_type,
                                    parameters=parameters,
                                    name='PSSE_' + native_code + '_' + model.value,
                                    nominal_frequency_hz=context.source.BASFRQ,
                                )
                                staged.append((
                                    load_key, native_loads[0], template,
                                    native_loads[0].rms_model,
                                ))
                    if failure_message is not None:
                        break
                    else:
                        pass
                if failure_message is not None:
                    context.record(
                        source, record.line_number, PsseFileType.DYR,
                        PsseConversionStatus.UNRESOLVED, (), failure_message,
                    )
                else:
                    targets: list[Load] = list()
                    staged_entry: tuple[tuple[int, str], Load, RmsModelTemplate, Block]
                    try:
                        for staged_entry in staged:
                            staged_entry[1].rms_template = staged_entry[2]
                    except (ValueError, TypeError, RuntimeError) as error:
                        for staged_entry in staged:
                            staged_entry[1].rms_template = None
                            staged_entry[1].rms_model = staged_entry[3]
                        raise ValueError('PSS/E CIM load installation rolled back') from error
                    else:
                        for staged_entry in staged:
                            context.grid.add_rms_model(staged_entry[2])
                            occupied_loads.add(staged_entry[0])
                            targets.append(staged_entry[1])
                    context.record(
                        source, record.line_number, PsseFileType.DYR,
                        PsseConversionStatus.CONVERTED, tuple(targets),
                        'Applied PSS/E 35.2 ' + model.value + ' motor to '
                        + str(len(targets)) + ' scoped load(s)',
                    )


def convert_psse_cmld_static_record(
        context: PsseAuxiliaryConverter,
        source: str,
        record: DyrRecord,
        occupied_loads: set[tuple[int, str]],
) -> None:
    """Bind the documented static-only subset of a PSS/E CMLD record.

    Motor, electronic, feeder, transformer and frequency terms outside this
    subset are rejected so the native load never silently loses dynamics.

    :param context: Native network, source RAW data and conversion ledger.
    :param source: DYR source filename.
    :param record: Valid 35.2 CMLD record.
    :param occupied_loads: Load identities already claimed by another DYR record.
    :return: None.
    """
    model_name: str = dynamic_record_name(record)
    if record.status != RecordStatus.VALID:
        context.record(source, record.line_number, PsseFileType.DYR,
                       PsseConversionStatus.INVALID, (), 'Invalid PSS/E CMLD record')
    elif record.icons != (0, 0):
        context.record(source, record.line_number, PsseFileType.DYR,
                       PsseConversionStatus.INVALID, (),
                       'PSS/E CMLD internal-storage ICONs must both be zero')
    elif not isinstance(record.identifier, int):
        context.record(source, record.line_number, PsseFileType.DYR,
                       PsseConversionStatus.INVALID, (), 'PSS/E CMLD scope identifier must be an integer')
    elif context.source.REV != 35:
        context.record(source, record.line_number, PsseFileType.DYR,
                       PsseConversionStatus.UNSUPPORTED, (), 'PSS/E CMLD binding is reviewed only for release 35.2')
    else:
        scope: str = model_name[-4:-2]
        scope_identifier: int = record.identifier
        scope_valid: bool = (scope in ('BL', 'OW', 'ZN', 'AR') and scope_identifier > 0)
        if scope == 'AL':
            scope_valid = scope_identifier == 0
        else:
            pass
        if not scope_valid:
            context.record(source, record.line_number, PsseFileType.DYR,
                           PsseConversionStatus.INVALID, (), 'Invalid PSS/E CMLD load scope: ' + scope)
        else:
            unsupported_values: tuple[tuple[str, float], ...] = (
                ('BSHUNT', 0.0), ('RFDR', 0.0), ('XFDR', 0.0), ('XXF', 0.0),
                ('TFIXHS', 1.0), ('TFIXLS', 1.0), ('LTC', 0.0),
                ('FMA', 0.0), ('FMB', 0.0), ('FMC', 0.0), ('FMD', 0.0),
                ('FEL', 0.0), ('PFRQ', 0.0), ('QFRQ', 0.0),
            )
            unsupported_parameter: str | None = None
            for parameter_name, required_value in unsupported_values:
                if not math.isclose(named_parameter(record, parameter_name), required_value, abs_tol=1e-12):
                    unsupported_parameter = parameter_name
                    break
                else:
                    pass
            if unsupported_parameter is not None:
                context.record(source, record.line_number, PsseFileType.DYR,
                               PsseConversionStatus.UNSUPPORTED, (),
                               'PSS/E CMLD static-only binding rejects non-default ' + unsupported_parameter)
            else:
                selected_raw_loads: list[RawLoadLike] = list()
                for raw_load in context.source.loads:
                    raw_load_id: str = str(raw_load.ID).replace("'", '').strip()
                    matches_id: bool = record.equipment_id == '*' or record.equipment_id == raw_load_id
                    if scope == 'BL':
                        matches_scope: bool = raw_load.I == scope_identifier
                    elif scope == 'OW':
                        matches_scope = raw_load.OWNER == scope_identifier
                    elif scope == 'ZN':
                        matches_scope = raw_load.ZONE == scope_identifier
                    elif scope == 'AR':
                        matches_scope = raw_load.AREA == scope_identifier
                    else:
                        matches_scope = True
                    if raw_load.STATUS == 1 and matches_id and matches_scope:
                        selected_raw_loads.append(raw_load)
                    else:
                        pass
                if len(selected_raw_loads) == 0:
                    context.record(source, record.line_number, PsseFileType.DYR,
                                   PsseConversionStatus.UNRESOLVED, (), 'PSS/E CMLD scope matched no active RAW loads')
                else:
                    staged: list[tuple[tuple[int, str], Load, RmsModelTemplate, Block]] = list()
                    failure_message: str | None = None
                    for raw_load in selected_raw_loads:
                        load_id: str = str(raw_load.ID).replace("'", '').strip()
                        load_key: tuple[int, str] = (raw_load.I, load_id)
                        native_code: str = str(raw_load.I) + '_' + load_id
                        native_loads: list[Load] = list(
                            native_load for native_load in context.grid.loads if native_load.code == native_code
                        )
                        raw_buses = list(bus for bus in context.source.buses if bus.I == raw_load.I)
                        raw_pf: float = raw_load.PL / math.hypot(raw_load.PL, raw_load.QL) if raw_load.PL > 0.0 else 0.0
                        source_pf: float = named_parameter(record, 'PFS')
                        valid_operating_point: bool = (
                            raw_load.PL > 0.0 and raw_load.QL >= 0.0
                            and math.isclose(raw_pf, source_pf, rel_tol=0.0, abs_tol=1e-6)
                        )
                        if load_key in occupied_loads:
                            failure_message = 'PSS/E CMLD scopes overlap at ' + native_code
                        elif len(native_loads) != 1:
                            failure_message = 'PSS/E CMLD load identity is missing or ambiguous: ' + native_code
                        elif (native_loads[0].rms_template is not None
                              or native_loads[0].rms_fmu_template is not None
                              or not native_loads[0].rms_model.empty()):
                            failure_message = 'PSS/E CMLD cannot replace an existing load RMS model: ' + native_code
                        elif len(raw_buses) != 1 or raw_buses[0].VM <= 0.0:
                            failure_message = 'PSS/E CMLD load bus voltage is missing or invalid: ' + native_code
                        elif not valid_operating_point:
                            failure_message = 'PSS/E CMLD PFS must match the positive-P, lagging RAW load power factor: ' + native_code
                        else:
                            parameters: CmldStaticLoadParameters = CmldStaticLoadParameters(
                                active_power_pu=raw_load.PL / context.source.SBASE,
                                static_power_factor=source_pf,
                                motor_a_fraction=named_parameter(record, 'FMA'),
                                motor_b_fraction=named_parameter(record, 'FMB'),
                                motor_c_fraction=named_parameter(record, 'FMC'),
                                motor_d_fraction=named_parameter(record, 'FMD'),
                                electronic_fraction=named_parameter(record, 'FEL'),
                                p1_exponent=named_parameter(record, 'P1E'),
                                p1_coefficient=named_parameter(record, 'P1C'),
                                p2_exponent=named_parameter(record, 'P2E'),
                                p2_coefficient=named_parameter(record, 'P2C'),
                                p_frequency_coefficient=named_parameter(record, 'PFRQ'),
                                q1_exponent=named_parameter(record, 'Q1E'),
                                q1_coefficient=named_parameter(record, 'Q1C'),
                                q2_exponent=named_parameter(record, 'Q2E'),
                                q2_coefficient=named_parameter(record, 'Q2C'),
                                q_frequency_coefficient=named_parameter(record, 'QFRQ'),
                                initial_voltage_pu=raw_buses[0].VM,
                            )
                            template: RmsModelTemplate = build_cmld_static_load_component(
                                vf=context.grid.var_factory,
                                name='PSSE_' + native_code + '_CMLD_STATIC',
                                parameters=parameters,
                            )
                            staged.append((load_key, native_loads[0], template, native_loads[0].rms_model))
                        if failure_message is not None:
                            break
                        else:
                            pass
                    if failure_message is not None:
                        context.record(source, record.line_number, PsseFileType.DYR,
                                       PsseConversionStatus.UNRESOLVED, (), failure_message)
                    else:
                        targets: list[Load] = list()
                        for staged_entry in staged:
                            staged_entry[1].rms_template = staged_entry[2]
                            context.grid.add_rms_model(staged_entry[2])
                            occupied_loads.add(staged_entry[0])
                            targets.append(staged_entry[1])
                        context.record(
                            source, record.line_number, PsseFileType.DYR,
                            PsseConversionStatus.CONVERTED, tuple(targets),
                            'Applied restricted PSS/E 35.2 static-only CMLD branch to '
                            + str(len(targets)) + ' scoped load(s); all motor, feeder/transformer and frequency terms were zero/default',
                        )


def freeze_input(block: Block, port: Var, vf: VarFactory, initial: Expr | Const | None = None) -> None:
    """Hold an unconnected physical input at its power-flow initialized value.

    :param block: Owning block.
    :param port: Input to close algebraically.
    :param vf: Circuit symbol factory.
    :param initial: Optional explicit initialization expression.
    """
    hold: Var = vf.add_var(port.name + '_DYR_hold')
    block.event_dict[hold] = vf.add_const(value=None, name=hold.name)
    block.init_eqs[hold] = initial if initial is not None else block.init_eqs[port]
    if initial is not None:
        block.init_eqs[port] = initial
    else:
        pass
    block.algebraic_vars.append(port)
    block.algebraic_eqs.append(port - hold)


def bind_parameters(block: Block, record: DyrRecord, binding: PsseDynamicBinding,
                    vf: VarFactory, suffix: str) -> None:
    """Apply every declared source-to-template parameter mapping.

    :param block: Fresh native component block.
    :param record: Valid source record.
    :param binding: Reviewed exact parameter names.
    :param vf: Circuit factory.
    :param suffix: Builder's deterministic instance suffix.
    """
    if record.model.upper() == 'OSTB5T':
        t4: float = named_parameter(record, 'T4')
        t3: float = named_parameter(record, 'T3_T4') * t4
        set_rms_model_parameter(block, 'T1_T3_' + suffix, named_parameter(record, 'T1') / t3, vf)
        set_rms_model_parameter(block, 'T3_' + suffix, t3, vf)
        set_rms_model_parameter(block, 'T2_T4_' + suffix, named_parameter(record, 'T2') / t4, vf)
    else:
        pass
    for source_name, target_name in binding.parameters:
        if record.model.upper() == 'OSTB5T' and source_name in ('T1', 'T2', 'T3_T4', 'T4'):
            pass
        else:
            set_rms_model_parameter(block, target_name + '_' + suffix, named_parameter(record, source_name), vf)


def build_gensal_network(vf: VarFactory, record: DyrRecord, name: str,
                         base_ratio: float, ra: float, frequency: float) -> RmsModelTemplate:
    """Connect the existing five-state GENSAL equations to native P/Q bus ports.

    No GENROU substitution is used. Initial states follow the GENSAL steady-state
    stator and damper equations; the original machine saturation stays intact.

    :param vf: Circuit variable factory.
    :param record: Valid GENSAL constants on machine base.
    :param name: Fresh instance label.
    :param base_ratio: Machine MVA divided by system MVA.
    :param ra: Armature resistance on machine base.
    :param frequency: Network frequency in Hz.
    :return: Network-ready RMS wrapper around the existing standard machine.
    """
    template: RmsModelTemplate = build_international_standard_template(InternationalStandardModel.GENSAL, vf, name)
    machine: Block = template.block
    values: dict[str, float] = dict(FNomHz=frequency, H=named_parameter(record,'H')*base_ratio,
        D=named_parameter(record,'D')*base_ratio, RaPu=ra/base_ratio,
        XdPu=named_parameter(record,'Xd')/base_ratio, XqPu=named_parameter(record,'Xq')/base_ratio,
        XpdPu=named_parameter(record,'Xd1')/base_ratio, XppdPu=named_parameter(record,'Xd2')/base_ratio,
        XppqPu=named_parameter(record,'Xd2')/base_ratio, XlPu=named_parameter(record,'Xl')/base_ratio,
        Tpd0=named_parameter(record,'Tdo1'), Tppd0=named_parameter(record,'Tdo2'),
        Tppq0=named_parameter(record,'Tqo2'), S10=named_parameter(record,'S10'), S12=named_parameter(record,'S12'))
    for label, value in values.items():
        set_rms_model_parameter(machine, label + '_' + name, value, vf)
    vm: Var = vf.add_var('Vm', reference=VarPowerFlowReferenceType.Vm)
    va: Var = vf.add_var('Va', reference=VarPowerFlowReferenceType.Va)
    pg: Var = vf.add_var('Pg', reference=VarPowerFlowReferenceType.P)
    qg: Var = vf.add_var('Qg', reference=VarPowerFlowReferenceType.Q)
    id_var, iq_var, efd, pm = machine.in_vars
    ud, uq, pe, omega = machine.out_vars
    delta, _, epq, psikd, psippq = machine.state_vars
    voltage: Expr = vm * sym.exp(sym.Const(1j) * va)
    current: Expr = sym.conj((pg + sym.Const(1j) * qg) / voltage)
    internal: Expr = voltage + (sym.Const(values['RaPu']) + sym.Const(1j * values['XqPu'])) * current
    machine.init_eqs[delta] = sym.imag(sym.log(internal / sym.abs(internal)))
    rotation: Expr = sym.exp(-sym.Const(1j) * (delta - sym.Const(math.pi/2)))
    vd_init: Expr = sym.real(voltage * rotation)
    vq_init: Expr = sym.imag(voltage * rotation)
    machine.init_eqs[id_var] = sym.real(current * rotation)
    machine.init_eqs[iq_var] = sym.imag(current * rotation)
    machine.init_eqs[epq] = vq_init + values['RaPu']*iq_var + values['XpdPu']*id_var
    machine.init_eqs[psikd] = epq - (values['XpdPu']-values['XlPu'])*id_var
    machine.init_eqs[psippq] = (values['XqPu']-values['XppqPu'])*iq_var
    # The source algebraic initialization already defines XadIfd and Te exactly.
    variables: dict[str, Var] = dict((var.name, var) for var in machine.algebraic_vars)
    xad: Var = variables['XadIfdPu_' + name]
    torque: Var = variables['TePu_' + name]
    machine.init_eqs[efd] = xad
    machine.init_eqs[pm] = torque
    bridge: Block = Block(name=name+'_network')
    bridge.algebraic_vars = [id_var, iq_var, pg, qg]
    bridge.algebraic_eqs = [ud-vm*sym.sin(delta-va), uq-vm*sym.cos(delta-va), pg-ud*id_var-uq*iq_var, qg-uq*id_var+ud*iq_var]
    bridge.init_eqs[id_var] = machine.init_eqs[id_var]
    bridge.init_eqs[iq_var] = machine.init_eqs[iq_var]
    # These boundary inputs are now owned by the network bridge.
    machine.in_vars = [efd, pm]
    machine.init_eqs.pop(id_var, None)
    machine.init_eqs.pop(iq_var, None)
    root: Block = Block(name=name)
    root.children = [machine, bridge]
    root.in_vars = [vm, va]
    root.out_vars = [pg, qg, omega, xad, torque, ud, uq, id_var, iq_var]
    root.external_mapping = dict([(VarPowerFlowReferenceType.Vm,vm),(VarPowerFlowReferenceType.Va,va),(VarPowerFlowReferenceType.P,pg),(VarPowerFlowReferenceType.Q,qg)])
    # Ports use the same order as the network-ready GENROU wrapper's child.
    root.in_vars = [vm, va, pm, efd]
    root.init_eqs[pm] = torque
    root.init_eqs[efd] = xad
    template.block = Block(name=name+'_wrapper')
    template.block.children = [root]
    template.block.in_vars = [vm,va]
    template.block.out_vars = [pg,qg]
    template.block.external_mapping = dict(root.external_mapping)
    template.tpe = DeviceType.GeneratorDevice
    return template


def build_cimtr_network(
        vf: VarFactory,
        template: RmsModelTemplate,
        name: str,
        base_ratio: float,
        role: InductionMachineRole,
        operating_point: CimtrOperatingPoint,
) -> RmsModelTemplate:
    """Connect a solved CIMTR machine point to native generator P/Q ports.

    :param vf: Circuit variable factory.
    :param template: Parameterized source-role CIMTR machine.
    :param name: Fresh dynamic model identity.
    :param base_ratio: Machine MVA divided by system MVA.
    :param role: Source generator or motor convention.
    :param operating_point: Solved flux, speed, torque and Q correction.
    :return: Network-connected RMS template with system-base generator outputs.
    """
    if base_ratio <= 0.0:
        raise ValueError('CIMTR requires a positive machine-to-system base ratio')
    else:
        pass

    machine: Block = template.block
    voltage_d: Var = machine.in_vars[0]
    voltage_q: Var = machine.in_vars[1]
    torque_input: Var = machine.in_vars[2]
    machine_power: Var = machine.out_vars[0]
    machine_reactive: Var = machine.out_vars[1]
    terminal_voltage: Var = vf.add_var('Vm', reference=VarPowerFlowReferenceType.Vm)
    terminal_angle: Var = vf.add_var('Va', reference=VarPowerFlowReferenceType.Va)
    active_power: Var = vf.add_var('Pg', reference=VarPowerFlowReferenceType.P)
    reactive_power: Var = vf.add_var('Qg', reference=VarPowerFlowReferenceType.Q)
    network_sign: float
    if role == InductionMachineRole.GENERATOR:
        network_sign = 1.0
    else:
        network_sign = -1.0

    # The algebraic bridge rotates polar bus voltage into the source d/q frame;
    # only network P/Q are converted to system base and generator sign.
    bridge: Block = Block(name=name + '_network')
    bridge.algebraic_vars = [voltage_d, voltage_q, active_power, reactive_power]
    bridge.algebraic_eqs = [
        voltage_d + terminal_voltage * sym.sin(terminal_angle),
        voltage_q - terminal_voltage * sym.cos(terminal_angle),
        active_power - network_sign * base_ratio * machine_power,
        reactive_power - network_sign * base_ratio * (
            machine_reactive + operating_point.q_adjustment * terminal_voltage ** 2
        ),
    ]
    bridge.init_eqs[voltage_d] = -terminal_voltage * sym.sin(terminal_angle)
    bridge.init_eqs[voltage_q] = terminal_voltage * sym.cos(terminal_angle)
    # The source power-flow sheet initializes flux and speed from the solved
    # electrical point, not from the shared kernel's generic synchronous seed.
    state_values: tuple[float, ...] = (
        operating_point.epr, operating_point.epi, operating_point.eppr,
        operating_point.eppi, operating_point.omega,
    )
    state_index: int
    state_value: float
    for state_index, state_value in enumerate(state_values):
        machine.init_eqs[machine.state_vars[state_index]] = vf.add_const(value=state_value)
    machine.init_eqs[machine.algebraic_vars[0]] = vf.add_const(value=operating_point.ir)
    machine.init_eqs[machine.algebraic_vars[1]] = vf.add_const(value=operating_point.ii)
    machine.init_eqs[torque_input] = vf.add_const(value=operating_point.torque_reference)
    machine.init_eqs[voltage_d] = -terminal_voltage * sym.sin(terminal_angle)
    machine.init_eqs[voltage_q] = terminal_voltage * sym.cos(terminal_angle)

    # The wrapper preserves the nested-machine convention used by other RAW
    # machine builders while exposing only the device's network terminals.
    root: Block = Block(name=name)
    root.children = [machine, bridge]
    root.in_vars = [terminal_voltage, terminal_angle]
    root.out_vars = [active_power, reactive_power]
    root.external_mapping = dict((
        (VarPowerFlowReferenceType.Vm, terminal_voltage),
        (VarPowerFlowReferenceType.Va, terminal_angle),
        (VarPowerFlowReferenceType.P, active_power),
        (VarPowerFlowReferenceType.Q, reactive_power),
    ))
    template.block = Block(name=name + '_wrapper')
    template.block.children = [root]
    template.block.in_vars = [terminal_voltage, terminal_angle]
    template.block.out_vars = [active_power, reactive_power]
    template.block.external_mapping = dict(root.external_mapping)
    template.tpe = DeviceType.GeneratorDevice
    return template


def build_cimtr_source_template(
        context: PsseAuxiliaryConverter,
        record: DyrRecord,
        raw: RawGeneratorLike,
        name: str,
        base_ratio: float,
) -> RmsModelTemplate:
    """Build an in-service, solved-point CIMTR RAW binding.

    :param context: RAW/native network identity and base information.
    :param record: Valid CIMTR1, CIMTR2, CIMTR3 or CIMTR4 record.
    :param raw: Exact matching PSS/E machine record.
    :param name: Fresh dynamic component identity.
    :param base_ratio: Machine MVA divided by system MVA.
    :return: Connected machine template on native system P/Q ports.
    :raises ValueError: Source mode or initial condition is outside the reviewed subset.
    """
    model: str = dynamic_record_name(record)
    role: InductionMachineRole
    if raw.STAT != 1:
        raise ValueError('CIMTR dynamic initialization requires an in-service RAW machine')
    else:
        pass
    if model in ('CIMTR1', 'CIMTR3'):
        role = InductionMachineRole.GENERATOR
        if raw.PG <= 0.0:
            raise ValueError(model + ' requires positive generator active power')
        elif named_parameter(record, 'SWITCH') not in (0.0, 1.0):
            raise ValueError(model + ' SWITCH must be binary')
        else:
            pass
        torque_exponent: float = 1.0
    elif model in ('CIMTR2', 'CIMTR4'):
        role = InductionMachineRole.MOTOR
        if raw.PG >= 0.0:
            raise ValueError(model + ' requires negative generator active power')
        else:
            pass
        torque_exponent = named_parameter(record, 'D')
    else:
        raise ValueError('No reviewed source binding exists for ' + model)

    t_prime: float = named_parameter(record, 'TP')
    t_double_prime: float = named_parameter(record, 'TPP')
    inertia: float = named_parameter(record, 'H')
    x: float = named_parameter(record, 'X')
    x_prime: float = named_parameter(record, 'XP')
    x_double_prime: float = named_parameter(record, 'XPP')
    x_leakage: float = named_parameter(record, 'XL')
    e1: float = named_parameter(record, 'E1')
    se1: float = named_parameter(record, 'SE1')
    e2: float = named_parameter(record, 'E2')
    se2: float = named_parameter(record, 'SE2')
    if se1 != 0.0 or se2 != 0.0:
        raise ValueError('CIMTR saturation is not represented by the native flux kernel')
    elif t_double_prime <= 0.0 or x_double_prime <= 0.0:
        raise ValueError('CIMTR single-cage source mode is not represented by the native flux kernel')
    elif not math.isclose(raw.ZX, x_double_prime, rel_tol=1.0e-3, abs_tol=1.0e-5):
        raise ValueError('CIMTR RAW ZSOURCE must match XPP for the double-cage source mode')
    elif raw.RT != 0.0 or raw.XT != 0.0:
        raise ValueError('CIMTR source binding requires zero generator step-up impedance')
    else:
        pass

    bus: Bus | None = context.buses.get(raw.I, None)
    if bus is None:
        raise ValueError('CIMTR terminal bus is missing')
    else:
        pass
    if role == InductionMachineRole.GENERATOR:
        active_power_target: float = raw.PG / raw.MBASE
        reactive_power_target: float = raw.QG / raw.MBASE
    else:
        active_power_target = -raw.PG / raw.MBASE
        reactive_power_target = -raw.QG / raw.MBASE
    operating_point: CimtrOperatingPoint | None = solve_cimtr_operating_point(
        role=role,
        voltage_magnitude=bus.Vm0,
        voltage_angle=bus.Va0,
        active_power_target=active_power_target,
        reactive_power_target=reactive_power_target,
        nominal_frequency_hz=context.grid.fBase,
        resistance=raw.ZR,
        x=x,
        x_prime=x_prime,
        x_double_prime=x_double_prime,
        t_prime=t_prime,
        t_double_prime=t_double_prime,
        torque_exponent=torque_exponent,
    )
    if operating_point is None:
        raise ValueError('CIMTR solved operating point did not converge')
    else:
        pass

    if model == 'CIMTR1':
        template: RmsModelTemplate = build_cimtr1_template(
            vf=context.grid.var_factory,
            name=name,
            parameters=Cimtr1Parameters(
                t_prime=t_prime, t_double_prime=t_double_prime,
                inertia=inertia, x=x, x_prime=x_prime,
                x_double_prime=x_double_prime, x_leakage=x_leakage,
                e1=e1, se1=se1, e2=e2, se2=se2, ra=raw.ZR,
            ),
        )
    elif model == 'CIMTR2':
        template = build_cimtr2_template(
            vf=context.grid.var_factory,
            name=name,
            parameters=Cimtr2Parameters(
                t_prime=t_prime, t_double_prime=t_double_prime,
                inertia=inertia, x=x, x_prime=x_prime,
                x_double_prime=x_double_prime, x_leakage=x_leakage,
                e1=e1, se1=se1, e2=e2, se2=se2,
                load_torque_exponent=torque_exponent, ra=raw.ZR,
            ),
        )
    elif model == 'CIMTR3':
        template = build_cimtr3_template(
            vf=context.grid.var_factory,
            name=name,
            parameters=Cimtr3Parameters(
                t_prime=t_prime, t_double_prime=t_double_prime,
                inertia=inertia, x=x, x_prime=x_prime,
                x_double_prime=x_double_prime, x_leakage=x_leakage,
                e1=e1, se1=se1, e2=e2, se2=se2,
                switch=int(named_parameter(record, 'SWITCH')),
                synchronous_power=named_parameter(record, 'SYNPOW'),
                ra=raw.ZR,
            ),
        )
    else:
        template = build_cimtr4_template(
            vf=context.grid.var_factory,
            name=name,
            parameters=Cimtr4Parameters(
                t_prime=t_prime, t_double_prime=t_double_prime,
                inertia=inertia, x=x, x_prime=x_prime,
                x_double_prime=x_double_prime, x_leakage=x_leakage,
                e1=e1, se1=se1, e2=e2, se2=se2,
                load_torque_exponent=torque_exponent,
                synchronous_torque=named_parameter(record, 'SYNTOR'),
                ra=raw.ZR,
            ),
        )
    return build_cimtr_network(
        vf=context.grid.var_factory, template=template, name=name,
        base_ratio=base_ratio, role=role, operating_point=operating_point,
    )


def build_controller(record: DyrRecord, binding: PsseDynamicBinding, vf: VarFactory,
                     name: str, base_ratio: float, system_base: float = 100.0,
                     nominal_frequency: float = 50.0) -> RmsModelTemplate:
    """Materialize a fresh existing controller with explicit parameter conversion.

    :param record: Valid controller constants.
    :param binding: Reviewed role and parameter map.
    :param vf: Circuit symbol factory.
    :param name: Unique component instance label.
    :param base_ratio: Machine MVA divided by system MVA.
    :param system_base: Network MVA base for source turbine ratings.
    :param nominal_frequency: Network frequency in Hz for source deadbands.
    :return: Parameterized component, still awaiting physical signal connections.
    """
    template: RmsModelTemplate
    model: str = dynamic_record_name(record)
    if model == 'BBGOV1':
        template = build_bbgov1_template(vf, name, Bbgov1Parameters(
            fcut=named_parameter(record,'FCUT'), ks=named_parameter(record,'KS'),
            kls=named_parameter(record,'KLS'), kg=named_parameter(record,'KG'),
            kp=named_parameter(record,'KP'), tn=named_parameter(record,'TN'),
            kd=named_parameter(record,'KD'), td=named_parameter(record,'TD'),
            t4=named_parameter(record,'T4'), k2=named_parameter(record,'K2'),
            t5=named_parameter(record,'T5'), k3=named_parameter(record,'K3'),
            t6=named_parameter(record,'T6'), t1=named_parameter(record,'T1'),
            switch=named_parameter(record,'SWITCH'), pmax=named_parameter(record,'PMAX'),
            pmin=named_parameter(record,'PMIN'),
        ))
    elif model == 'PSS4B':
        template = build_pss4b_template(vf, name, Pss4bParameters(record.constants))
    elif model in ('WESGOV', 'WESGOVD', 'WESGOVDU'):
        is_deadband: bool = model in ('WESGOVD', 'WESGOVDU')
        settings: WesgovSettings = WesgovSettings(
            delta_tc=named_parameter(record, 'DTC'),
            delta_tp=named_parameter(record, 'DTP'),
            droop=named_parameter(record, 'DROOP'),
            kp=named_parameter(record, 'KP'),
            ti=named_parameter(record, 'TI'),
            t1=named_parameter(record, 'T1'),
            t2=named_parameter(record, 'T2'),
            alim=named_parameter(record, 'ALIM'),
            tpe=named_parameter(record, 'TPE'),
            deadband_high=named_parameter(record, 'DBH') if is_deadband else 0.0,
            deadband_low=named_parameter(record, 'DBL') if is_deadband else 0.0,
        )
        template = build_wesgov_template(vf, settings, name)
    elif model == 'TGOV2':
        template = build_tgov2_template(
            vf, name, TGOV2Parameters(
                r=named_parameter(record,'R'), t1=named_parameter(record,'T1'),
                vmax=named_parameter(record,'VMAX'), vmin=named_parameter(record,'VMIN'),
                k=named_parameter(record,'K'), t3=named_parameter(record,'T3'),
                dt=named_parameter(record,'DT'), tt=named_parameter(record,'TT'),
                ta=named_parameter(record,'TA'), tb=named_parameter(record,'TB'),
                tc=named_parameter(record,'TC'),
            ),
        )
    elif model in ('TGOV3', 'TGOV3D', 'TGOV3DU'):
        is_deadband: bool = model in ('TGOV3D', 'TGOV3DU')
        fraction_sum: float = (named_parameter(record, 'K1')
                               + named_parameter(record, 'K2')
                               + named_parameter(record, 'K3'))
        feasible_stage_maximum: float = min(
            named_parameter(record, 'PMAX'), named_parameter(record, 'PRMAX'),
        )
        feasible_stage_minimum: float = max(0.0, named_parameter(record, 'PMIN'))
        if fraction_sum <= 0.0 or feasible_stage_maximum < feasible_stage_minimum:
            raise ValueError('TGOV3 source limits have no feasible initial power')
        else:
            pass
        seed_power: float = (
            (feasible_stage_minimum + feasible_stage_maximum) / 2.0
            * fraction_sum
        )
        template = build_tgov3_template(
            vf=vf,
            name=name,
            parameters=Tgov3Parameters(
                k=named_parameter(record, 'K'),
                t1=named_parameter(record, 'T1'),
                t2=named_parameter(record, 'T2'),
                t3=named_parameter(record, 'T3'),
                uo=named_parameter(record, 'UO'),
                uc=named_parameter(record, 'UC'),
                pmax=named_parameter(record, 'PMAX'),
                pmin=named_parameter(record, 'PMIN'),
                t4=named_parameter(record, 'T4'),
                k1=named_parameter(record, 'K1'),
                t5=named_parameter(record, 'T5'),
                k2=named_parameter(record, 'K2'),
                t6=named_parameter(record, 'T6'),
                k3=named_parameter(record, 'K3'),
                ta=named_parameter(record, 'TA'),
                tb=named_parameter(record, 'TB'),
                tc=named_parameter(record, 'TC'),
                prmax=named_parameter(record, 'PRMAX'),
                pm0=seed_power,
                deadband_high=named_parameter(record, 'DBH') if is_deadband else 0.0,
                deadband_low=named_parameter(record, 'DBL') if is_deadband else 0.0,
            ),
        )
    elif record.model.upper() == 'TGOV1':
        template = get_tgov1_rms_template(vf, name)
        parameters: Tgov1RmsParameters = Tgov1RmsParameters(1.0, named_parameter(record,'R')/base_ratio,
            named_parameter(record,'VMAX')*base_ratio,named_parameter(record,'VMIN')*base_ratio,
            named_parameter(record,'T1'),named_parameter(record,'T2'),named_parameter(record,'T3'),named_parameter(record,'Dt')*base_ratio)
        configure_tgov1_block(template.block.children[0], parameters, vf)
    elif dynamic_record_name(record) in ('GGOV1','GGOV1D','GGOV1DU'):
        tracked: TrackedGovernorParameters = TrackedGovernorParameters(
            feedback=GovernorDroopFeedback(record.icons[0]), fuel_characteristic=FuelFlowCharacteristic(record.icons[1]),
            droop=named_parameter(record,'R'), power_time=named_parameter(record,'TPELEC'),
            error_limits=(named_parameter(record,'MINERR'), named_parameter(record,'MAXERR')),
            governor_gains=(named_parameter(record,'KPGOV'), named_parameter(record,'KIGOV'), named_parameter(record,'KDGOV')),
            derivative_time=named_parameter(record,'TDGOV'), valve_limits=(named_parameter(record,'VMIN'), named_parameter(record,'VMAX')),
            actuator_time=named_parameter(record,'TACT'), valve_rates=(named_parameter(record,'RCLOSE'), named_parameter(record,'ROPEN')),
            turbine_gain=named_parameter(record,'KTURB'), no_load_fuel=named_parameter(record,'WFNL'),
            turbine_times=(named_parameter(record,'TC'), named_parameter(record,'TB')),
            load_time=named_parameter(record,'TFLOAD'), load_gains=(named_parameter(record,'KPLOAD'), named_parameter(record,'KILOAD')),
            load_reference=named_parameter(record,'LDREF'), damping=named_parameter(record,'DM'),
            reset_gain=named_parameter(record,'KIMW'), deadband=named_parameter(record,'DB'),
            temperature_times=(named_parameter(record,'TSA'), named_parameter(record,'TSB')),
            speed_deadband=(named_parameter(record,'DBL'), named_parameter(record,'DBH')) if dynamic_record_name(record) in ('GGOV1D','GGOV1DU') else (0.,0.),
            load_rates=(named_parameter(record,'RDOWN'),named_parameter(record,'RUP')))
        template = build_ggov1_template(vf,name,tracked)
    elif dynamic_record_name(record) in ('DEGOV','DEGOV1','DEGOV1D','DEGOV1DU'):
        engine: DieselGovernorParameters = DieselGovernorParameters(
            t1=named_parameter(record,'T1'),t2=named_parameter(record,'T2'),t3=named_parameter(record,'T3'),
            gain=named_parameter(record,'K'),t4=named_parameter(record,'T4'),t5=named_parameter(record,'T5'),t6=named_parameter(record,'T6'),
            combustion_delay=named_parameter(record,'TD'),maximum=named_parameter(record,'TMAX'),minimum=named_parameter(record,'TMIN'),
            droop=named_parameter(record,'DROOP') if dynamic_record_name(record) != 'DEGOV' else 0.,
            power_time=named_parameter(record,'TE') if dynamic_record_name(record) != 'DEGOV' else 0.,
            feedback=EngineDroopFeedback(record.icons[0]) if dynamic_record_name(record) != 'DEGOV' else EngineDroopFeedback.THROTTLE,
            deadband_high=named_parameter(record,'DBH') if dynamic_record_name(record) in ('DEGOV1D','DEGOV1DU') else 0.,
            deadband_low=named_parameter(record,'DBL') if dynamic_record_name(record) in ('DEGOV1D','DEGOV1DU') else 0.)
        template = build_degov1_template(vf,name,engine)
    elif record.model.upper() == 'LCFB1':
        load_settings: TurbineLoadControllerParameters = TurbineLoadControllerParameters(
            frequency_bias=named_parameter(record,'FB') if record.icons[0] == 1 else 0.0,
            power_time=named_parameter(record,'TPELEC'),deadband=named_parameter(record,'DB'),
            error_limit=named_parameter(record,'EMAX'),proportional_gain=named_parameter(record,'KP'),
            integral_gain=named_parameter(record,'KI'),correction_limit=named_parameter(record,'LRMAX'))
        template = build_lcfb1_template(vf,name,load_settings)
    elif record.model.upper() == 'UEL1':
        settings: Uel1Settings = Uel1Settings(
            kur=named_parameter(record,'KUR'), kuc=named_parameter(record,'KUC'),
            kuf=named_parameter(record,'KUF'), vurmax=named_parameter(record,'VURMAX'),
            vucmax=named_parameter(record,'VUCMAX'), kui=named_parameter(record,'KUI'),
            kul=named_parameter(record,'KUL'), vuimax=named_parameter(record,'VUIMAX'),
            vuimin=named_parameter(record,'VUIMIN'), tu1=named_parameter(record,'TU1'),
            tu2=named_parameter(record,'TU2'), tu3=named_parameter(record,'TU3'),
            tu4=named_parameter(record,'TU4'), vulmax=named_parameter(record,'VULMAX'),
            vulmin=named_parameter(record,'VULMIN'),
        )
        template = build_uel1_template(vf,name,settings)
    elif record.model.upper() == 'UEL2C':
        existing_uids: set[int] = set(vf.get_vars_dict()) | set(vf.get_diff_var_dict())
        uel2c_parameters: Uel2cParameters = Uel2cParameters(
            k1=record.icons[0],k2=record.icons[1],tuv=named_parameter(record,'TUV'),
            tup=named_parameter(record,'TUP'),tuq=named_parameter(record,'TUQ'),
            kui=named_parameter(record,'KUI'),kul=named_parameter(record,'KUL'),
            vuimax=named_parameter(record,'VUIMAX'),vuimin=named_parameter(record,'VUIMIN'),
            kuf=named_parameter(record,'KUF'),kfb=named_parameter(record,'KFB'),
            tul=named_parameter(record,'TUL'),tu1=named_parameter(record,'TU1'),
            tu2=named_parameter(record,'TU2'),tu3=named_parameter(record,'TU3'),
            tu4=named_parameter(record,'TU4'),vulmax=named_parameter(record,'VULMAX'),
            vulmin=named_parameter(record,'VULMIN'),vbias=named_parameter(record,'VBIAS'),
            kfix=named_parameter(record,'KFIX'),tadj=named_parameter(record,'TADJ'),
            tqref=named_parameter(record,'TQREF'),vuelmax2=named_parameter(record,'VUELMAX2'),
            vuelmin2=named_parameter(record,'VUELMIN2'),vuelmax1=named_parameter(record,'VUELMAX1'),
            vuelmin1=named_parameter(record,'VUELMIN1'),xq=named_parameter(record,'XQ'))
        curve_points: tuple[tuple[float,float],...] = tuple(
            (named_parameter(record,'P'+str(index)),named_parameter(record,'Q'+str(index)))
            for index in range(11) if named_parameter(record,'P'+str(index)) != 0.0)
        template = build_uel2c_template(vf,name,curve_points,
            Uel2cThirdQuadrantMode(record.icons[2]),
            Uel2cGainReductionMode.FIXED if record.icons[3] == 1 else Uel2cGainReductionMode.ADJUSTABLE,
            uel2c_parameters)
        block: Block = template.block
        block.name = name
        for variable_uid, variable in list(vf.get_vars_dict().items()) + list(vf.get_diff_var_dict().items()):
            if variable_uid not in existing_uids and variable.name.endswith('_Uel2c'):
                variable.set_name(variable.name[:-len('_Uel2c')] + '_' + name)
            else:
                pass
        _normalize_imported_variable_names(vf,existing_uids)
        bind_parameters(block,record,binding,vf,name)
    elif record.model.upper() in ('MAXEX1','MAXEX2'):
        measurement: Maxex2Measurement
        if record.model.upper() == 'MAXEX1':
            measurement = Maxex2Measurement.FIELD_VOLTAGE
            rated_name: str = 'EFDRATED'
            level1_name: str = 'EFD1'
            level2_name: str = 'EFD2'
            level3_name: str = 'EFD3'
            desired_name: str = 'EFDDES'
        else:
            measurement = Maxex2Measurement(record.icons[0])
            rated_name = 'RATED'
            level1_name = 'LEVEL1'
            level2_name = 'LEVEL2'
            level3_name = 'LEVEL3'
            desired_name = 'DESIRED_LEVEL'
        parameters: Maxex2Parameters = Maxex2Parameters(
            measurement=measurement,
            rated=named_parameter(record,rated_name),
            level1=named_parameter(record,level1_name),
            time1=named_parameter(record,'TIME1'),
            level2=named_parameter(record,level2_name),
            time2=named_parameter(record,'TIME2'),
            level3=named_parameter(record,level3_name),
            time3=named_parameter(record,'TIME3'),
            desired_level=named_parameter(record,desired_name),
            kmx=named_parameter(record,'KMX'),
            vlow=named_parameter(record,'VLOW'),
        )
        template = build_maxex2_template(vf,name,parameters)
    elif record.model.upper() == 'OEL2C':
        existing_uids: set[int] = set(vf.get_vars_dict()) | set(vf.get_diff_var_dict())
        template = build_oel2c_template(vf, name)
        block: Block = template.block
        block.name = name
        # The generated OEL2C builder has a fixed suffix; rename every fresh
        # symbol so separate generator instances remain UID-distinct by name.
        for variable_uid, variable in list(vf.get_vars_dict().items()) + list(vf.get_diff_var_dict().items()):
            if variable_uid not in existing_uids and variable.name.endswith('_Oel2c'):
                variable.set_name(variable.name[:-len('_Oel2c')] + '_' + name)
            else:
                pass
        _normalize_imported_variable_names(vf, existing_uids)
        bind_parameters(block, record, binding, vf, name)
        set_rms_model_parameter(block, 'oel_Sw1_' + name, float(record.icons[1] - 1), vf)
    elif dynamic_record_name(record) in ('IEEEG1','IEEEG1D','IEEEG1SDU'):
        steam: MultiStageSteamGovernorParameters = MultiStageSteamGovernorParameters(
            gain=named_parameter(record,'K'),speed_lag=named_parameter(record,'T1'),speed_lead=named_parameter(record,'T2'),
            servo_time=named_parameter(record,'T3'),opening_rate=named_parameter(record,'UO'),closing_rate=named_parameter(record,'UC'),
            maximum=named_parameter(record,'PMAX'),minimum=named_parameter(record,'PMIN'),
            turbine_times=(named_parameter(record,'T4'),named_parameter(record,'T5'),named_parameter(record,'T6'),named_parameter(record,'T7')),
            fractions=tuple(named_parameter(record,'K'+str(index)) for index in range(1,9)),
            deadband_high=named_parameter(record,'DBH') if dynamic_record_name(record) in ('IEEEG1D','IEEEG1SDU') else 0.0,
            deadband_low=named_parameter(record,'DBL') if dynamic_record_name(record) in ('IEEEG1D','IEEEG1SDU') else 0.0)
        template = build_ieeeg1_template(vf,name,steam)
    elif dynamic_record_name(record) in ('IEEEG3','IEEEG3D','IEEEG3DU'):
        hydraulics: HydraulicGovernorParameters = HydraulicGovernorParameters(
            gate_time=named_parameter(record,'TG'), pilot_time=named_parameter(record,'TP'),
            opening_rate=named_parameter(record,'UO'), closing_rate=named_parameter(record,'UC'),
            gate_max=named_parameter(record,'PMAX'), gate_min=named_parameter(record,'PMIN'),
            permanent_droop=named_parameter(record,'SIGMA'), transient_droop=named_parameter(record,'DELTA'),
            reset_time=named_parameter(record,'TR'), water_time=named_parameter(record,'TW'),
            a11=named_parameter(record,'A11'), a13=named_parameter(record,'A13'),
            a21=named_parameter(record,'A21'), a23=named_parameter(record,'A23'),
            deadband_high=named_parameter(record,'DBH') if dynamic_record_name(record) in ('IEEEG3D','IEEEG3DU') else 0.0,
            deadband_low=named_parameter(record,'DBL') if dynamic_record_name(record) in ('IEEEG3D','IEEEG3DU') else 0.0)
        template = build_ieeeg3_template(vf,name,hydraulics)
    elif record.model.upper() in ('EXST1','ESST3A'):
        template = get_exst1_rms_template(vf,name) if record.model.upper() == 'EXST1' else get_esst3a_rms_template(vf,name)
        for parameter in record.parameters:
            value: float = parameter.value
            # Both the data sheet and native THETAP parameter use degrees.
            set_rms_model_parameter(template.block.children[0], parameter.name, value, vf)
        block: Block = template.block.children[0]
        if record.model.upper() == 'EXST1':
            configure_exst1_algebraic_lags(block,record)
        else:
            parameters_by_name: dict[str, Var] = dict((var.name,var) for var in block.event_dict)
            # Preserve PSS/E regulator and exciter limits absent from this
            # catalogue's zero-TA realization, using its existing anti-windup helper.
            block.algebraic_eqs[5] = sym.hard_sat(parameters_by_name['KA']*block.algebraic_vars[4],
                parameters_by_name['VRMIN'],parameters_by_name['VRMAX'])-block.algebraic_vars[5]
            block.state_eqs[2] = _anti_windup_state_derivative(block.state_vars[2],block.state_eqs[2],
                parameters_by_name['VMMIN'],parameters_by_name['VMMAX'])
            if named_parameter(record,'TR') == 0:
                state: Var = block.state_vars.pop(0)
                block.state_eqs.pop(0)
                if block.diff_vars:
                    block.diff_vars.pop(0)
                else:
                    pass
                block.algebraic_vars.append(state)
                block.algebraic_eqs.append(block.in_vars[1]-state)
            else:
                pass
    elif dynamic_record_name(record) in ('TGOV1D','TGOV1DU'):
        template = build_tgov1d_template(vf,name,Tgov1RmsParameters(1.,named_parameter(record,'R'),
            named_parameter(record,'VMAX'),named_parameter(record,'VMIN'),named_parameter(record,'T1'),
            named_parameter(record,'T2'),named_parameter(record,'T3'),named_parameter(record,'Dt')),
            named_parameter(record,'DBL'),named_parameter(record,'DBH'))
    elif dynamic_record_name(record) in ('HYGOV','HYGOVD','HYGOVDU'):
        hydro_parameters: NonlinearHydroGovernorParameters = NonlinearHydroGovernorParameters(
            permanent_droop=named_parameter(record,'R'),temporary_droop=named_parameter(record,'r'),
            reset_time=named_parameter(record,'Tr'),filter_time=named_parameter(record,'Tf'),gate_time=named_parameter(record,'Tg'),
            velocity=named_parameter(record,'VELM'),maximum=named_parameter(record,'GMAX'),minimum=named_parameter(record,'GMIN'),
            water_time=named_parameter(record,'Tw'),gain=named_parameter(record,'At'),damping=named_parameter(record,'Dturb'),
            no_load_flow=named_parameter(record,'qNL'),
            deadband_low=named_parameter(record,'DBL') if dynamic_record_name(record) != 'HYGOV' else 0.,
            deadband_high=named_parameter(record,'DBH') if dynamic_record_name(record) != 'HYGOV' else 0.)
        template = build_hygov_template(vf,name,hydro_parameters)
    elif dynamic_record_name(record) == 'HYGOVR1':
        turbine_rating: float = named_parameter(record, 'TRATE')
        turbine_base: float = turbine_rating if turbine_rating > 0.0 else base_ratio * system_base
        settings: Hygovr1Parameters = Hygovr1Parameters(
            db1_hz=named_parameter(record, 'DB1'),
            err_pu=named_parameter(record, 'ERR'),
            td=named_parameter(record, 'TD'),
            lead_lag_times=(
                named_parameter(record, 'T1'), named_parameter(record, 'T2'),
                named_parameter(record, 'T3'), named_parameter(record, 'T4'),
                named_parameter(record, 'T5'), named_parameter(record, 'T6'),
                named_parameter(record, 'T7'), named_parameter(record, 'T8'),
            ),
            kp=named_parameter(record, 'KP'),
            droop=named_parameter(record, 'R'),
            tt=named_parameter(record, 'TT'),
            kg=named_parameter(record, 'KG'),
            tp=named_parameter(record, 'TP'),
            velocity_open=named_parameter(record, 'VELOPEN'),
            velocity_close=named_parameter(record, 'VELCLOSE'),
            gate_max=named_parameter(record, 'PMAX'),
            gate_min=named_parameter(record, 'PMIN'),
            db2_mw=named_parameter(record, 'DB2'),
            tw=named_parameter(record, 'TW'),
            at=named_parameter(record, 'AT'),
            damping=named_parameter(record, 'DTURB'),
            no_load_flow=named_parameter(record, 'QNL'),
            turbine_base_mw=turbine_base,
            nominal_frequency=nominal_frequency,
        )
        template = build_hygovr1_template(vf, name, settings)
    elif dynamic_record_name(record) in ('GAST','GASTD','GASTDU'):
        template = build_gast_template(vf, name, GasGovernorParameters(
            r=named_parameter(record,'R'), t1=named_parameter(record,'T1'),
            t2=named_parameter(record,'T2'), t3=named_parameter(record,'T3'),
            ambient_limit=named_parameter(record,'AT'), temperature_gain=named_parameter(record,'KT'),
            valve_max=named_parameter(record,'VMAX'), valve_min=named_parameter(record,'VMIN'),
            damping=named_parameter(record,'Dturb'),
            deadband_low=named_parameter(record,'DBL') if dynamic_record_name(record) != 'GAST' else 0.,
            deadband_high=named_parameter(record,'DBH') if dynamic_record_name(record) != 'GAST' else 0.))
    elif dynamic_record_name(record) in ('IEESGO','IEESGOD','IEESGODU'):
        template = build_ieesgo_template(vf, name, SteamGovernorParameters(
            t1=named_parameter(record,'T1'), t2=named_parameter(record,'T2'),
            t3=named_parameter(record,'T3'), t4=named_parameter(record,'T4'),
            t5=named_parameter(record,'T5'), t6=named_parameter(record,'T6'),
            gain=named_parameter(record,'K1'), reheat_fraction=named_parameter(record,'K2'),
            low_pressure_fraction=named_parameter(record,'K3'), power_max=named_parameter(record,'PMAX'),
            power_min=named_parameter(record,'PMIN'),
            deadband_low=named_parameter(record,'DBL') if dynamic_record_name(record) != 'IEESGO' else 0.,
            deadband_high=named_parameter(record,'DBH') if dynamic_record_name(record) != 'IEESGO' else 0.))
    elif dynamic_record_name(record) == 'PSS7C':
        ramp_settings: RampStabilizerParameters = RampStabilizerParameters(
            washout_times=(named_parameter(record,'TW1'),named_parameter(record,'KW2'),
                named_parameter(record,'TW3'),named_parameter(record,'TW4')),
            transducer_times=(named_parameter(record,'T6'),named_parameter(record,'T7')),
            ks1=named_parameter(record,'KS1'),ks2=named_parameter(record,'KS2'),
            ks3=named_parameter(record,'KS3'),t8=named_parameter(record,'T8'),
            t9=named_parameter(record,'T9'),ramp_m=record.icons[4],ramp_n=record.icons[5],
            upper=named_parameter(record,'VSTMAX'),lower=named_parameter(record,'VSTMIN'),
            input_limits=((named_parameter(record,'VSL1MIN'),named_parameter(record,'VSL1MAX')),
                (named_parameter(record,'VSL2MIN'),named_parameter(record,'VSL2MAX'))))
        template = build_pss7c_template(vf,name,ramp_settings,
            (named_parameter(record,'K0'),named_parameter(record,'K1'),named_parameter(record,'K2'),
             named_parameter(record,'K3'),named_parameter(record,'K4')),
            (named_parameter(record,'TI1'),named_parameter(record,'TI2'),
             named_parameter(record,'TI3'),named_parameter(record,'TI4')),
            (named_parameter(record,'KI3'),named_parameter(record,'KI4')),
            named_parameter(record,'PSSON'),named_parameter(record,'PSSOFF'),
            named_parameter(record,'XCOMP'),named_parameter(record,'TCOMP'))
    elif record.model.upper() in ('PSS2A','PSS2B','PSS2C'):
        limited: bool = record.model.upper() != 'PSS2A'
        ramp: RampStabilizerParameters = RampStabilizerParameters(
            washout_times=(named_parameter(record,'TW1'),named_parameter(record,'TW2'),
                           named_parameter(record,'TW3'),named_parameter(record,'TW4')),
            transducer_times=(named_parameter(record,'T6'),named_parameter(record,'T7')),
            ks1=named_parameter(record,'KS1'),ks2=named_parameter(record,'KS2'),ks3=named_parameter(record,'KS3'),
            t8=named_parameter(record,'T8'),t9=named_parameter(record,'T9'),
            ramp_m=record.icons[4],ramp_n=record.icons[5],
            phase_times=((named_parameter(record,'T1'),named_parameter(record,'T2')),
                         (named_parameter(record,'T3'),named_parameter(record,'T4')),
                         (named_parameter(record,'T10'),named_parameter(record,'T11')) if limited else (0.0,0.0)),
            upper=named_parameter(record,'VSTMAX'),lower=named_parameter(record,'VSTMIN'),
            input_limits=((named_parameter(record,'VS1MIN'),named_parameter(record,'VS1MAX')),
                          (named_parameter(record,'VS2MIN'),named_parameter(record,'VS2MAX'))) if limited else ((-10.0,10.0),(-10.0,10.0)),
            fourth_phase=(named_parameter(record,'T12'),named_parameter(record,'T13')) if record.model.upper() == 'PSS2C' else (0.,0.))
        template = build_pss2c_template(vf,name,ramp,StabilizerInterface.SELECTED_SIGNALS,
            named_parameter(record,'PSSON'),named_parameter(record,'PSSOFF')) if record.model.upper() == 'PSS2C' else (build_pss2b_template(vf,name,ramp,StabilizerInterface.SELECTED_SIGNALS) if limited else
                    build_pss2a_template(vf,name,ramp,StabilizerInterface.SELECTED_SIGNALS))
    elif record.model.upper() == 'PSS3B':
        template = build_pss3b_template(vf,name,QuadraticDualStabilizerParameters(
            gains=(named_parameter(record,'KS1'),named_parameter(record,'KS2')),
            transducer_times=(named_parameter(record,'T1'),named_parameter(record,'T2')),
            washout_times=(named_parameter(record,'TW1'),named_parameter(record,'TW2'),named_parameter(record,'TW3')),
            coefficients=(named_parameter(record,'A1'),named_parameter(record,'A2'),named_parameter(record,'A3'),named_parameter(record,'A4'),
                named_parameter(record,'A5'),named_parameter(record,'A6'),named_parameter(record,'A7'),named_parameter(record,'A8')),
            upper=named_parameter(record,'VSTMAX'),lower=named_parameter(record,'VSTMIN')))
    elif record.model.upper() == 'IEE2ST':
        template = build_iee2st_template(vf, name, Iee2stParameters(
            gains=(named_parameter(record,'K1'), named_parameter(record,'K2')),
            transducer_times=(named_parameter(record,'T1'), named_parameter(record,'T2')),
            reset_numerator=named_parameter(record,'T3'), reset_denominator=named_parameter(record,'T4'),
            phase_times=((named_parameter(record,'T5'), named_parameter(record,'T6')),
                (named_parameter(record,'T7'), named_parameter(record,'T8')),
                (named_parameter(record,'T9'), named_parameter(record,'T10'))),
            upper=named_parameter(record,'LSMAX'), lower=named_parameter(record,'LSMIN'),
            voltage_upper=named_parameter(record,'VCU'), voltage_lower=named_parameter(record,'VCL')))
    elif record.model.upper() == 'IEEEST':
        template = build_ieeest_template(vf, name, IeeestParameters(
            filter_coefficients=(named_parameter(record,'A1'), named_parameter(record,'A2'),
                named_parameter(record,'A3'), named_parameter(record,'A4'),
                named_parameter(record,'A5'), named_parameter(record,'A6')),
            lead1=named_parameter(record,'T1'), lag1=named_parameter(record,'T2'),
            lead2=named_parameter(record,'T3'), lag2=named_parameter(record,'T4'),
            reset_numerator=named_parameter(record,'T5'), reset_denominator=named_parameter(record,'T6'),
            gain=named_parameter(record,'KS'), upper=named_parameter(record,'LSMAX'),
            lower=named_parameter(record,'LSMIN'), voltage_upper=named_parameter(record,'VCU'),
            voltage_lower=named_parameter(record,'VCL')))
    elif record.model.upper() == 'STAB1':
        template = build_stab1_template(vf, name, gain_over_time=named_parameter(record,'KoverT'),
            washout_time=named_parameter(record,'T'), lead1_ratio=named_parameter(record,'T1overT3'),
            lag1_time=named_parameter(record,'T3'), lead2_ratio=named_parameter(record,'T2overT4'),
            lag2_time=named_parameter(record,'T4'), output_limit=named_parameter(record,'HLIM'))
    elif record.model.upper() == 'STAB2A':
        template = build_stab2a_template(vf, name, k2=named_parameter(record,'K2'), t2=named_parameter(record,'T2'),
            k3=named_parameter(record,'K3'), t3=named_parameter(record,'T3'), k4=named_parameter(record,'K4'),
            k5=named_parameter(record,'K5'), t5=named_parameter(record,'T5'), output_limit=named_parameter(record,'HLIM'))
    elif record.model.upper() == 'STAB3':
        template = build_stab3_template(vf, name, transducer_time=named_parameter(record,'Tt'),
            first_lag_time=named_parameter(record,'TX1'), reset_time=named_parameter(record,'TX2'),
            gain=named_parameter(record,'KX'), output_limit=named_parameter(record,'VLIM'))
    elif record.model.upper() == 'STAB4':
        template = build_stab4_template(vf, name, gain=named_parameter(record,'KX'),
            transducer_time=named_parameter(record,'TT'), first_lag_time=named_parameter(record,'TX1'),
            reset_time=named_parameter(record,'TX2'), lead1_time=named_parameter(record,'Ta'),
            lead2_time=named_parameter(record,'Tb'), second_lag_time=named_parameter(record,'Tc'),
            output_lag1_time=named_parameter(record,'Td'), output_lag2_time=named_parameter(record,'Te'),
            lower_limit=named_parameter(record,'L1'), upper_limit=named_parameter(record,'L2'))
    elif record.model.upper() == 'STABNI':
        template = build_stabni_template(vf,name,gain=named_parameter(record,'K'),lead_time=named_parameter(record,'T1'),
            transducer_time=named_parameter(record,'T2'),reset_time=named_parameter(record,'T0'),
            output_limit=named_parameter(record,'LIMIT'))
    elif record.model.upper() == 'MNLEX1':
        template = build_mnlex1_template(vf,name,feedback_gain=named_parameter(record,'KF2'),
            feedback_time=named_parameter(record,'TF2'),limiter_gain=named_parameter(record,'KM'),
            limiter_time=named_parameter(record,'TM'),maximum=named_parameter(record,'MELMAX'),
            slope=named_parameter(record,'K'))
    elif record.model.upper() == 'MNLEX2':
        template = build_mnlex2_template(vf,name,feedback_gain=named_parameter(record,'KF2'),
            feedback_time=named_parameter(record,'TF2'),limiter_gain=named_parameter(record,'KM'),
            limiter_time=named_parameter(record,'TM'),maximum=named_parameter(record,'MELMAX'),
            reactive_center=named_parameter(record,'Q0'),radius=named_parameter(record,'Radius'))
    elif record.model.upper() == 'MNLEX3':
        template = build_mnlex3_template(vf,name,feedback_gain=named_parameter(record,'KF2'),
            feedback_time=named_parameter(record,'TF2'),limiter_gain=named_parameter(record,'KM'),
            limiter_time=named_parameter(record,'TM'),maximum=named_parameter(record,'MELMAX'),
            reactive_intercept=named_parameter(record,'Q0'),slope=named_parameter(record,'B'))
    elif record.model.upper() == 'DC4C':
        if named_parameter(record,'KE') == 0:
            raise ValueError('Compound commutator automatic field-resistance calibration is unreviewed')
        else:
            pass
        template = build_dc4c_template(vf,name,DcExciterParameters(
            tr=named_parameter(record,'TR'),ka=named_parameter(record,'KA'),ta=named_parameter(record,'TA'),
            vrmax=named_parameter(record,'VRMAX'),vrmin=named_parameter(record,'VRMIN'),
            ke=named_parameter(record,'KE'),te=named_parameter(record,'TE'),kf=named_parameter(record,'KF'),tf=named_parameter(record,'TF'),
            field_min=named_parameter(record,'VEMIN'),e1=named_parameter(record,'E1'),se1=named_parameter(record,'SE1'),
            e2=named_parameter(record,'E2'),se2=named_parameter(record,'SE2')),
            named_parameter(record,'KPR'),named_parameter(record,'KJR'),named_parameter(record,'KDR'),named_parameter(record,'TDR'),
            RotatingLimiterLocation(record.icons[1]),RotatingLimiterLocation(record.icons[0]),
            CompoundSupplyParameters(kp=named_parameter(record,'KP'),ki=named_parameter(record,'KI'),
                xl=named_parameter(record,'XL'),theta=named_parameter(record,'THETAP'),kc=named_parameter(record,'KC1'),
                vbmax=named_parameter(record,'VBMAX'),source=CompoundExcitationSource(record.icons[3])))
    elif record.model.upper() == 'DC4B':
        template = build_dc4b_template(vf,name,DcExciterParameters(
            tr=named_parameter(record,'TR'),ka=named_parameter(record,'KA'),ta=named_parameter(record,'TA'),
            vrmax=named_parameter(record,'VRMAX'),vrmin=named_parameter(record,'VRMIN'),
            ke=named_parameter(record,'KE'),te=named_parameter(record,'TE'),kf=named_parameter(record,'KF'),tf=named_parameter(record,'TF'),
            field_min=named_parameter(record,'VEMIN'),e1=named_parameter(record,'E1'),se1=named_parameter(record,'SE1'),
            e2=named_parameter(record,'E2'),se2=named_parameter(record,'SE2')),
            named_parameter(record,'KP'),named_parameter(record,'KI'),named_parameter(record,'KD'),named_parameter(record,'TD'),
            RotatingLimiterLocation(record.icons[1]),RotatingLimiterLocation(record.icons[0]))
    elif record.model.upper() in ('EXAC4','ESAC4A','AC4C'):
        template = build_alternator_rectifier(vf,name,
            AlternatorRectifierKind.OUTPUT_CLIP if record.model.upper() == 'EXAC4' else (AlternatorRectifierKind.SELECTABLE_GATES if record.model.upper() == 'AC4C' else AlternatorRectifierKind.NONWINDUP_GATE),
            AlternatorRectifierParameters(tr=named_parameter(record,'TR'),
                vi_max=named_parameter(record,'VIMAX'), vi_min=named_parameter(record,'VIMIN'),
                tc=named_parameter(record,'TC'), tb=named_parameter(record,'TB'),
                ka=named_parameter(record,'KA'), ta=named_parameter(record,'TA'),
                vr_max=named_parameter(record,'VRMAX'), vr_min=named_parameter(record,'VRMIN'),
                kc=named_parameter(record,'KC')),
            RectifierLimiterLocation(record.icons[1]) if record.model.upper() == 'AC4C' else RectifierLimiterLocation.SUMMATION,
            RectifierLimiterLocation(record.icons[0]) if record.model.upper() == 'AC4C' else RectifierLimiterLocation.SUMMATION)
    elif binding.electromechanical_kind is not None:
        mechanism: ElectromechanicalExciterKind = binding.electromechanical_kind
        source_upper: float = named_parameter(record,'VRMAX')
        source_ke: float = named_parameter(record,'KE')
        mechanics: ElectromechanicalExciterParameters = ElectromechanicalExciterParameters(
            tr=named_parameter(record,'TR') if mechanism in (ElectromechanicalExciterKind.NORMALIZED_RESET,ElectromechanicalExciterKind.BOUNDED_NORMALIZED_RESET) else 0.0,
            reset_time=named_parameter(record,'TRH'),
            reset_deadband=named_parameter(record,'KR') if mechanism == ElectromechanicalExciterKind.DEADBAND_RESET else 0.0,
            fast_band=named_parameter(record,'KV'), regulator_max=None if source_upper == 0 and mechanism != ElectromechanicalExciterKind.BOUNDED_NORMALIZED_RESET else source_upper,
            regulator_min=named_parameter(record,'VRMIN'), field_gain=None if source_ke == 0 and mechanism != ElectromechanicalExciterKind.BOUNDED_NORMALIZED_RESET else source_ke,
            field_time=named_parameter(record,'TE'), e1=named_parameter(record,'E1'), se1=named_parameter(record,'SE1'),
            e2=named_parameter(record,'E2'), se2=named_parameter(record,'SE2'),
            gain=named_parameter(record,'KA') if mechanism == ElectromechanicalExciterKind.LAG_OR_INTEGRAL else 1.0,
            field_min=named_parameter(record,'EFDMIN') if mechanism == ElectromechanicalExciterKind.LAG_OR_INTEGRAL else (named_parameter(record,'VEMIN') if mechanism == ElectromechanicalExciterKind.BOUNDED_NORMALIZED_RESET else 0.0),
            field_max=named_parameter(record,'EFDMAX') if mechanism == ElectromechanicalExciterKind.LAG_OR_INTEGRAL else 5.0)
        template = build_electromechanical_exciter(vf,name,mechanism,mechanics)
    elif dynamic_record_name(record) in ('PIDGOV','PIDGOVD','PIDGOVDU'):
        pid_deadband: bool = dynamic_record_name(record) != 'PIDGOV'
        if len(record.icons) != 1:
            raise ValueError('Hydraulic PID feedback selection is missing')
        else:
            pass
        template = build_pidgov_template(vf,name,PidHydroGovernorParameters(
            droop=named_parameter(record,'RPERM'),detector_time=named_parameter(record,'TREG'),
            kp=named_parameter(record,'KP'),ki=named_parameter(record,'KI'),kd=named_parameter(record,'KD'),
            controller_time=named_parameter(record,'TA'),servo_time=named_parameter(record,'TB'),damping=named_parameter(record,'DTURB'),
            g0=named_parameter(record,'G0'),g1=named_parameter(record,'G1'),p1=named_parameter(record,'P1'),
            g2=named_parameter(record,'G2'),p2=named_parameter(record,'P2'),p3=named_parameter(record,'P3'),
            gate_max=named_parameter(record,'GMAX'),gate_min=named_parameter(record,'GMIN'),
            water_factor=named_parameter(record,'ATW'),water_time=named_parameter(record,'TW'),
            opening_rate=named_parameter(record,'VELMAX'),closing_rate=named_parameter(record,'VELMIN'),feedback=HydroDroopFeedback(record.icons[0]),
            deadband_low=named_parameter(record,'DBL') if pid_deadband else 0.,
            deadband_high=named_parameter(record,'DBH') if pid_deadband else 0.))
    elif dynamic_record_name(record) in ('HYGOV2','HYGOV2D','HYGOV2DU'):
        cascaded_deadband: bool = dynamic_record_name(record) != 'HYGOV2'
        template = build_hygov2_template(vf,name,CascadedHydroGovernorParameters(
            kp=named_parameter(record,'KP'),ki=named_parameter(record,'KI'),ka=named_parameter(record,'KA'),
            t1=named_parameter(record,'T1'),t2=named_parameter(record,'T2'),t3=named_parameter(record,'T3'),
            t4=named_parameter(record,'T4'),t5=named_parameter(record,'T5'),t6=named_parameter(record,'T6'),
            reset_time=named_parameter(record,'TR'),temporary_droop=named_parameter(record,'r'),
            permanent_droop=named_parameter(record,'R'),gate_velocity=named_parameter(record,'VGMAX'),
            gate_max=named_parameter(record,'GMAX'),gate_min=named_parameter(record,'GMIN'),power_gain=named_parameter(record,'PMAX'),
            deadband_low=named_parameter(record,'DBL') if cascaded_deadband else 0.,
            deadband_high=named_parameter(record,'DBH') if cascaded_deadband else 0.))
    elif record.model.upper() == 'BUDCZT':
        template = build_budczt_template(vf,name,LimitedPiExciterParameters(
            kp=named_parameter(record,'KP'),ka=named_parameter(record,'KA'),ke=named_parameter(record,'KE'),
            tr=named_parameter(record,'TR'),ti=named_parameter(record,'TI'),
            ta=named_parameter(record,'TA'),te=named_parameter(record,'TE'),
            regulator_max=named_parameter(record,'URMAX'),regulator_min=named_parameter(record,'URMIN'),
            field_max=named_parameter(record,'EFDMAX'),field_min=named_parameter(record,'EFDMIN')))
    elif record.model.upper() == 'EXPIC1':
        template = build_expic1_template(vf,name,PiCompoundFieldParameters(
            tr=named_parameter(record,'TR'),ka=named_parameter(record,'KA'),ta1=named_parameter(record,'TA1'),
            vr1=named_parameter(record,'VR1'),vr2=named_parameter(record,'VR2'),ta2=named_parameter(record,'TA2'),ta3=named_parameter(record,'TA3'),ta4=named_parameter(record,'TA4'),
            vrmax=named_parameter(record,'VRMAX'),vrmin=named_parameter(record,'VRMIN'),kf=named_parameter(record,'KF'),tf1=named_parameter(record,'TF1'),tf2=named_parameter(record,'TF2'),
            efdmax=named_parameter(record,'EFDMAX'),efdmin=named_parameter(record,'EFDMIN'),ke=named_parameter(record,'KE'),te=named_parameter(record,'TE'),
            e1=named_parameter(record,'E1'),se1=named_parameter(record,'SE1'),e2=named_parameter(record,'E2'),se2=named_parameter(record,'SE2'),
            kp=named_parameter(record,'KP'),ki=named_parameter(record,'KI'),kc=named_parameter(record,'KC')))
    elif record.model.upper() == 'EXNI':
        if named_parameter(record,'R') != 0:
            raise ValueError('Controlled-bridge reverse-current logic requires separate review; only bidirectional R=0 is supported')
        else:
            pass
        template = build_exni_template(vf,name,tr=named_parameter(record,'TR'),ka=named_parameter(record,'KA'),ta=named_parameter(record,'TA'),
            vrmax=named_parameter(record,'VRMAX'),vrmin=named_parameter(record,'VRMIN'),kf=named_parameter(record,'KF'),
            tf1=named_parameter(record,'TF1'),tf2=named_parameter(record,'TF2'),supply=BridgeExcitationSupply(named_parameter(record,'SWITCH')))
    elif record.model.upper() == 'IEET1B':
        if named_parameter(record,'KE') == 0 or named_parameter(record,'VRMAX') == 0:
            raise ValueError('Biased rotating exciter automatic coefficient/capability calibration has not been reviewed')
        else:
            pass
        template = build_ieet1b_template(vf,name,DcExciterParameters(
            tr=named_parameter(record,'TR'),ka=named_parameter(record,'KA'),ta=named_parameter(record,'TA1'),
            vrmax=named_parameter(record,'VRMAX'),vrmin=named_parameter(record,'VRMIN'),ke=named_parameter(record,'KE'),te=named_parameter(record,'TE'),
            kf=named_parameter(record,'KF1'),tf=named_parameter(record,'TF1'),e1=named_parameter(record,'E1'),se1=named_parameter(record,'SE1'),
            e2=named_parameter(record,'E2'),se2=named_parameter(record,'SE2')),
            second_time=named_parameter(record,'TA2'),error_max=named_parameter(record,'VSMAX'),error_min=named_parameter(record,'VSMIN'),
            compensation=named_parameter(record,'Xe'),feedback_signal=RotatingRateFeedbackSignal(named_parameter(record,'Switch')))
    elif record.model.upper() == 'ST6C':
        template = build_st6c_template(vf,name,CurrentLimitedFieldParameters(
            tr=named_parameter(record,'TR'),kpa=named_parameter(record,'KPA'),kia=named_parameter(record,'KIA'),
            kda=named_parameter(record,'KDA'),tda=named_parameter(record,'TDA'),vamax=named_parameter(record,'VAMAX'),
            vamin=named_parameter(record,'VAMIN'),kff=named_parameter(record,'KFF'),km=named_parameter(record,'KM'),
            kci=named_parameter(record,'KCI'),klr=named_parameter(record,'KLR'),ilr=named_parameter(record,'ILR'),
            vrmax=named_parameter(record,'VRMAX'),vrmin=named_parameter(record,'VRMIN'),kg=named_parameter(record,'KG'),
            tg=named_parameter(record,'TG'),vmmax=named_parameter(record,'VMMAX'),vmmin=named_parameter(record,'VMMIN'),
            ta=named_parameter(record,'TA'),supply=CompoundSupplyParameters(kp=named_parameter(record,'KP'),
                ki=named_parameter(record,'KI'),xl=named_parameter(record,'XL'),theta=named_parameter(record,'THETAP'),
                kc=named_parameter(record,'KC'),vbmax=named_parameter(record,'VBMAX'),source=CompoundExcitationSource(record.icons[3])),
            minimum_location=FieldRegulatorLimiterLocation(record.icons[1]),maximum_location=FieldRegulatorLimiterLocation(record.icons[0])))
    elif model == 'ST8C':
        if (len(record.icons) != 4 or record.icons[0] not in (1, 2)
                or record.icons[1] not in (1, 2) or record.icons[2] not in (1, 2, 3)
                or record.icons[3] not in (1, 2)):
            raise ValueError('ST8C requires OEL/UEL positions 1–2, unused SCL 1–3, and SW1 1–2')
        else:
            pass
        template = build_st8c_template(
            vf, name,
            St8cParameters(
                tr=named_parameter(record, 'TR'),
                kpr=named_parameter(record, 'KPR'),
                kir=named_parameter(record, 'KIR'),
                vpimax=named_parameter(record, 'VPIMAX'),
                vpimin=named_parameter(record, 'VPIMIN'),
                kpa=named_parameter(record, 'KPA'),
                kia=named_parameter(record, 'KIA'),
                vamax=named_parameter(record, 'VAMAX'),
                vamin=named_parameter(record, 'VAMIN'),
                ka=named_parameter(record, 'KA'),
                ta=named_parameter(record, 'TA'),
                vrmax=named_parameter(record, 'VRMAX'),
                vrmin=named_parameter(record, 'VRMIN'),
                kf=named_parameter(record, 'KF'),
                tf=named_parameter(record, 'TF'),
                kc1=named_parameter(record, 'KC1'),
                kp=named_parameter(record, 'KP'),
                ki1=named_parameter(record, 'KI1'),
                xl=named_parameter(record, 'XL'),
                thetap=named_parameter(record, 'THETAP'),
                vb1max=named_parameter(record, 'VB1MAX'),
                kc2=named_parameter(record, 'KC2'),
                ki2=named_parameter(record, 'KI2'),
                vb2max=named_parameter(record, 'VB2MAX'),
            ),
            source_selection=(
                Ac9cPotentialSourceSelection.TERMINAL_FED
                if record.icons[3] == 1
                else Ac9cPotentialSourceSelection.INDEPENDENT
            ),
            oel_location=(
                St8cLimiterLocation.SUMMATION
                if record.icons[0] == 1
                else St8cLimiterLocation.TAKEOVER_GATE
            ),
            uel_location=(
                St8cLimiterLocation.SUMMATION
                if record.icons[1] == 1
                else St8cLimiterLocation.TAKEOVER_GATE
            ),
        )
    elif model == 'ST10C':
        if len(record.icons) != 5 or record.icons != (1, 1, 1, 1, 1):
            raise ValueError('ST10C currently requires summation-point selectors and terminal-fed supply')
        else:
            pass
        template = build_st10c_template(vf, name, St10cParameters(
            tr=named_parameter(record, 'TR'),
            kr=named_parameter(record, 'KR'),
            tc1=named_parameter(record, 'TC1'),
            tb1=named_parameter(record, 'TB1'),
            tc2=named_parameter(record, 'TC2'),
            tb2=named_parameter(record, 'TB2'),
            vrsmax=named_parameter(record, 'VRSMAX'),
            vrsmin=named_parameter(record, 'VRSMIN'),
            vrmax=named_parameter(record, 'VRMAX'),
            vrmin=named_parameter(record, 'VRMIN'),
            t1=named_parameter(record, 'T1'),
            kp=named_parameter(record, 'KP'),
            kc=named_parameter(record, 'KC'),
            ki=named_parameter(record, 'KI'),
            xl=named_parameter(record, 'XL'),
            thetap_rad=math.radians(named_parameter(record, 'THETAP')),
            vbmax=named_parameter(record, 'VBMAX'),
        ))
    elif model == 'ST9C':
        if len(record.icons) != 4 or record.icons[0] not in (1, 2, 3) \
                or record.icons[1] not in (1, 2, 3) or record.icons[2] not in (1, 2, 3) \
                or record.icons[3] not in (1, 2):
            raise ValueError('ST9C requires OEL/UEL/SCL positions 1–3 and power-source position 1–2')
        else:
            pass
        template = build_st9c_template(vf, name, St9cParameters(
            tr=named_parameter(record, 'TR'),
            tcd=named_parameter(record, 'TCD'),
            tbd=named_parameter(record, 'TBD'),
            za=named_parameter(record, 'ZA'),
            ka=named_parameter(record, 'KA'),
            ku=named_parameter(record, 'KU'),
            ta=named_parameter(record, 'TA'),
            tauel=named_parameter(record, 'TAUEL'),
            vrmax=named_parameter(record, 'VRMAX'),
            vrmin=named_parameter(record, 'VRMIN'),
            kas=named_parameter(record, 'KAS'),
            tas=named_parameter(record, 'TAS'),
            kp=named_parameter(record, 'KP'),
            thetap_rad=math.radians(named_parameter(record, 'THETAP')),
            ki=named_parameter(record, 'KI'),
            xl=named_parameter(record, 'XL'),
            kc=named_parameter(record, 'KC'),
            vbmax=named_parameter(record, 'VBMAX'),
        ))
        # Position A uses the terminal compound source; position B selects fixed KP.
        freeze_named_parameter(template.block, 'avr.Sw1_' + name,
                                Const(1.0 if record.icons[3] == 1 else 0.0), vf)
        freeze_named_parameter(template.block, 'avr.PositionOel_' + name,
                                Const(float(record.icons[0])), vf)
        freeze_named_parameter(template.block, 'avr.PositionUel_' + name,
                                Const(float(record.icons[1])), vf)
        freeze_named_parameter(template.block, 'avr.PositionScl_' + name,
                                Const(float(record.icons[2])), vf)
        switch_output: Var | None = next(
            (variable for variable in template.block.algebraic_vars
             if variable.name == 'avr.switch.y_' + name),
            None,
        )
        potential_supply: Var | None = next(
            (variable for variable in template.block.algebraic_vars
             if variable.name == 'avr.potentialCircuit.vE_' + name),
            None,
        )
        if switch_output is None or potential_supply is None:
            raise ValueError('ST9C selected-source initialization variables are missing')
        elif record.icons[3] == 1:
            template.block.init_eqs[switch_output] = potential_supply
        else:
            template.block.init_eqs[switch_output] = Const(named_parameter(record, 'KP'))
    elif record.model.upper() in ('ST5B','ST5C'):
        parallel_parameters: ParallelChannelExciterParameters = ParallelChannelExciterParameters(
            tr=named_parameter(record,'TR'),
            tc1=named_parameter(record,'TC1'),
            tb1=named_parameter(record,'TB1'),
            tc2=named_parameter(record,'TC2'),
            tb2=named_parameter(record,'TB2'),
            kr=named_parameter(record,'KR'),
            vrmax=named_parameter(record,'VRMAX'),
            vrmin=named_parameter(record,'VRMIN'),
            t1=named_parameter(record,'T1'),
            kc=named_parameter(record,'KC'),
            tuc1=named_parameter(record,'TUC1'),
            tub1=named_parameter(record,'TUB1'),
            tuc2=named_parameter(record,'TUC2'),
            tub2=named_parameter(record,'TUB2'),
            toc1=named_parameter(record,'TOC1'),
            tob1=named_parameter(record,'TOB1'),
            toc2=named_parameter(record,'TOC2'),
            tob2=named_parameter(record,'TOB2'),
            minimum_location=ExcitationLimiterLocation(record.icons[1]) if record.model.upper() == 'ST5C' else ExcitationLimiterLocation.REFERENCE_GATE,
            maximum_location=ExcitationLimiterLocation(record.icons[0]) if record.model.upper() == 'ST5C' else ExcitationLimiterLocation.REFERENCE_GATE)
        template = build_st5c_template(vf,name,parallel_parameters) if record.model.upper() == 'ST5C' else build_st5b_template(vf,name,parallel_parameters)
    elif record.model.upper() == 'AC11C':
        ac11c_parameters: Ac11cParameters = Ac11cParameters(
            tr=named_parameter(record, 'TR'),
            kpa=named_parameter(record, 'KPA'),
            tia=named_parameter(record, 'TIA'),
            kpu=named_parameter(record, 'KPU'),
            tiu=named_parameter(record, 'TIU'),
            kb=named_parameter(record, 'KB'),
            tb=named_parameter(record, 'TB'),
            kpo=named_parameter(record, 'KPO'),
            tio=named_parameter(record, 'TIO'),
            vrsmx=named_parameter(record, 'VRSMAX'),
            vrsmn=named_parameter(record, 'VRSMIN'),
            vrmax=named_parameter(record, 'VRMAX'),
            vrmin=named_parameter(record, 'VRMIN'),
            vamax=named_parameter(record, 'VAMAX'),
            vamin=named_parameter(record, 'VAMIN'),
            te=named_parameter(record, 'TE'),
            kc=named_parameter(record, 'KC'),
            kd=named_parameter(record, 'KD'),
            ke=named_parameter(record, 'KE'),
            vfemax=named_parameter(record, 'VFEMAX'),
            vemin=named_parameter(record, 'VEMIN'),
            e1=named_parameter(record, 'E1'),
            se1=named_parameter(record, 'SE1'),
            e2=named_parameter(record, 'E2'),
            se2=named_parameter(record, 'SE2'),
            kp=named_parameter(record, 'KP'),
            ki1=named_parameter(record, 'KI1'),
            xl=named_parameter(record, 'XL'),
            theta_p=named_parameter(record, 'THETAP'),
            kc1=named_parameter(record, 'KC1'),
            vb1max=named_parameter(record, 'VB1MAX'),
            ki2=named_parameter(record, 'KI2'),
            kc2=named_parameter(record, 'KC2'),
            vb2max=named_parameter(record, 'VB2MAX'),
            kboost=named_parameter(record, 'KBOOST'),
            vboost=named_parameter(record, 'VBOOST'),
            pss_location=Ac11cPssLocation(record.icons[0]),
            oel_location=Ac11cLimiterLocation(record.icons[1]),
            uel_location=Ac11cLimiterLocation(record.icons[2]),
            scl_location=Ac11cLimiterLocation(record.icons[3]),
            power_source=Ac11cPowerSource(record.icons[4]),
        )
        template = build_ac11c_template(vf, name, ac11c_parameters)
    elif record.model.upper() == 'AC9C':
        if (len(record.icons) != 4 or record.icons[0] not in (1, 2)
                or record.icons[1] not in (1, 2) or record.icons[2] not in (1, 2, 3)):
            raise ValueError('AC9C supports documented OEL/UEL positions 1–2 and SCL 1–3 only')
        else:
            pass
        vfwmin: float = named_parameter(record, 'VFWMIN')
        vfwmax: float = named_parameter(record, 'VFWMAX')
        initial_freewheel: float = min(max(0.0, vfwmin), vfwmax)
        template = build_ac9c_controller_template(
            vf=vf,
            name=name,
            tr=named_parameter(record, 'TR'),
            pid_settings=Ac9cPidSettings(
                kpr=named_parameter(record, 'KPR'),
                kir=named_parameter(record, 'KIR'),
                kdr=named_parameter(record, 'KDR'),
                tdr=named_parameter(record, 'TDR'),
                vpidmax=named_parameter(record, 'VPIDMAX'),
                vpidmin=named_parameter(record, 'VPIDMIN'),
            ),
            current_settings=Ac9cCurrentRegulatorSettings(
                kpa=named_parameter(record, 'KPA'),
                kia=named_parameter(record, 'KIA'),
                vamax=named_parameter(record, 'VAMAX'),
                vamin=named_parameter(record, 'VAMIN'),
            ),
            bridge_settings=Ac9cRectifierBridgeSettings(
                ka=named_parameter(record, 'KA'),
                ta=named_parameter(record, 'TA'),
                vrmax=named_parameter(record, 'VRMAX'),
                vrmin=named_parameter(record, 'VRMIN'),
            ),
            field_feedback_settings=Ac9cFieldFeedbackSettings(
                kf=named_parameter(record, 'KF'),
                tf=named_parameter(record, 'TF'),
            ),
            freewheel_settings=Ac9cFreewheelVoltageSettings(
                kfw=named_parameter(record, 'KFW'),
                vfwmax=vfwmax,
                vfwmin=vfwmin,
                vfw0=initial_freewheel,
            ),
            exciter_settings=Ac9cRotatingExciterSettings(
                kc=named_parameter(record, 'KC'),
                kd=named_parameter(record, 'KD'),
                ke=named_parameter(record, 'KE'),
                te=named_parameter(record, 'TE'),
                vfemax=named_parameter(record, 'VFEMAX'),
                vemin=named_parameter(record, 'VEMIN'),
                e1=named_parameter(record, 'E1'),
                se1=named_parameter(record, 'SE1'),
                e2=named_parameter(record, 'E2'),
                se2=named_parameter(record, 'SE2'),
            ),
            potential_source_settings=Ac9cPotentialSourceSettings(
                kp=named_parameter(record, 'KP'),
                ki1=named_parameter(record, 'KI1'),
                ki2=named_parameter(record, 'KI2'),
                xl=named_parameter(record, 'XL'),
                theta_p=named_parameter(record, 'THETAP'),
            ),
            channel1_settings=Ac9cRectifierSupplySettings(
                kc=named_parameter(record, 'KC1'),
                vbmax=named_parameter(record, 'VB1MAX'),
                source0=abs(named_parameter(record, 'KP')),
            ),
            channel2_settings=Ac9cRectifierSupplySettings(
                kc=named_parameter(record, 'KC2'),
                vbmax=named_parameter(record, 'VB2MAX'),
                source0=0.001,
            ),
            source_selection=ac9c_potential_source_selection_from_psse(record.icons[3]),
            stage_type=ac9c_power_stage_type_from_psse(named_parameter(record, 'SCT')),
            oel_location=Ac9cLimiterLocation(record.icons[0]),
            uel_location=Ac9cLimiterLocation(record.icons[1]),
            vlim1=named_parameter(record, 'VLIM1'),
            vlim2=named_parameter(record, 'VLIM2'),
        )
    elif record.model.upper() in ('AC6C','AC6C2'):
        ac6c_parameters: Ac6cParameters = Ac6cParameters(
            tr=named_parameter(record,'TR'),ka=named_parameter(record,'KA'),
            ta=named_parameter(record,'TA'),tk=named_parameter(record,'TK'),
            tb=named_parameter(record,'TB'),tc=named_parameter(record,'TC'),
            vamax=named_parameter(record,'VAMAX'),vamin=named_parameter(record,'VAMIN'),
            vrmax=named_parameter(record,'VRMAX'),vrmin=named_parameter(record,'VRMIN'),
            te=named_parameter(record,'TE'),vfelim=named_parameter(record,'VFELIM'),
            kh=named_parameter(record,'KH'),vhmax=named_parameter(record,'VHMAX'),
            th=named_parameter(record,'TH'),tj=named_parameter(record,'TJ'),
            kc=named_parameter(record,'KC'),kd=named_parameter(record,'KD'),
            ke=named_parameter(record,'KE'),e1=named_parameter(record,'E1'),
            se1=named_parameter(record,'SE1'),e2=named_parameter(record,'E2'),
            se2=named_parameter(record,'SE2'),vfemax=named_parameter(record,'VFEMAX'),
            vemin=named_parameter(record,'VEMIN'),
            minimum_location=Ac6cLimiterLocation(record.icons[1]),
            maximum_location=Ac6cLimiterLocation(record.icons[0]),
            limit_voltage=FieldLimitVoltage(record.icons[2]) if record.model.upper() == 'AC6C2' else FieldLimitVoltage.TERMINAL)
        template = build_ac6c2_template(vf,name,ac6c_parameters) if record.model.upper() == 'AC6C2' else build_ac6c_template(vf,name,ac6c_parameters)
    elif record.model.upper() in ('AC7B','AC7C'):
        cascaded_parameters: CascadedBrushlessParameters = CascadedBrushlessParameters(
            tr=named_parameter(record,'TR'),
            kpr=named_parameter(record,'KPR'),
            kir=named_parameter(record,'KIR'),
            kdr=named_parameter(record,'KDR'),
            tdr=named_parameter(record,'TDR'),
            vrmax=named_parameter(record,'VRMAX'),
            vrmin=named_parameter(record,'VRMIN'),
            kpa=named_parameter(record,'KPA'),
            kia=named_parameter(record,'KIA'),
            vamax=named_parameter(record,'VAMAX'),
            vamin=named_parameter(record,'VAMIN'),
            kp=named_parameter(record,'KP'),
            kl=named_parameter(record,'KL'),
            kf1=named_parameter(record,'KF1'),
            kf2=named_parameter(record,'KF2'),
            kf3=named_parameter(record,'KF3'),
            tf3=named_parameter(record,'TF3'),
            kc=named_parameter(record,'KC'),
            kd=named_parameter(record,'KD'),
            ke=named_parameter(record,'KE'),
            te=named_parameter(record,'TE'),
            vfemax=named_parameter(record,'VFEMAX'),
            vemin=named_parameter(record,'VEMIN'),
            e1=named_parameter(record,'E1'),
            se1=named_parameter(record,'SE1'),
            e2=named_parameter(record,'E2'),
            se2=named_parameter(record,'SE2'))
        if record.model.upper() == 'AC7C':
            if record.icons[5] == 1 and named_parameter(record,'KP') == 0:
                raise ValueError('Modern cascaded KP=0 potential-supply bypass requires separate source review')
            else:
                pass
            template = build_ac7c_template(vf,name,cascaded_parameters,CascadedBrushlessCircuit(
                ki=named_parameter(record,'KI'),xl=named_parameter(record,'XL'),theta=named_parameter(record,'THETAP'),
                kc1=named_parameter(record,'KC1'),vbmax=named_parameter(record,'VBMAX'),kr=named_parameter(record,'KR'),
                source=CompoundExcitationSource(record.icons[4]),power_supply=CascadedPowerSupply(record.icons[5]),
                minimum_location=CascadedLimiterLocation(record.icons[1]),maximum_location=CascadedLimiterLocation(record.icons[0]),
                supplement_location=CompoundSupplementLocation(record.icons[3])))
        else:
            template = build_ac7b_template(vf,name,cascaded_parameters)
    elif record.model.upper() in ('AC8B','AC8C'):
        pid_brushless_parameters: PidBrushlessExciterParameters = PidBrushlessExciterParameters(
            tr=named_parameter(record,'TR'),
            kpr=named_parameter(record,'KPR'),
            kir=named_parameter(record,'KIR'),
            kdr=named_parameter(record,'KDR'),
            tdr=named_parameter(record,'TDR'),
            vpidmax=named_parameter(record,'VPIDMAX'),
            vpidmin=named_parameter(record,'VPIDMIN'),
            ka=named_parameter(record,'KA'),
            ta=named_parameter(record,'TA'),
            vrmax=named_parameter(record,'VRMAX'),
            vrmin=named_parameter(record,'VRMIN'),
            kc=named_parameter(record,'KC'),
            kd=named_parameter(record,'KD'),
            ke=named_parameter(record,'KE'),
            te=named_parameter(record,'TE'),
            vfemax=named_parameter(record,'VFEMAX'),
            vemin=named_parameter(record,'VEMIN'),
            e1=named_parameter(record,'E1'),
            se1=named_parameter(record,'SE1'),
            e2=named_parameter(record,'E2'),
            se2=named_parameter(record,'SE2'))
        if record.model.upper() == 'AC8C':
            template = build_ac8c_template(vf,name,pid_brushless_parameters,CompoundPidPowerCircuit(
                kp=named_parameter(record,'KP'),ki=named_parameter(record,'KI'),xl=named_parameter(record,'XL'),
                theta=named_parameter(record,'THETAP'),kc1=named_parameter(record,'KC1'),vbmax=named_parameter(record,'VBMAX'),
                source=CompoundExcitationSource(record.icons[4]),minimum_location=ExcitationLimiterLocation(record.icons[1]),
                maximum_location=ExcitationLimiterLocation(record.icons[0]),supplement_location=CompoundSupplementLocation(record.icons[3])))
        else:
            template = build_ac8b_template(vf,name,pid_brushless_parameters)
    elif record.model.upper() == 'ST4C':
        template = build_st4c_template(vf,name,FilteredCompoundPiParameters(
            tr=named_parameter(record,'TR'),
            kpr=named_parameter(record,'KPR'),
            kir=named_parameter(record,'KIR'),
            vrmax=named_parameter(record,'VRMAX'),
            vrmin=named_parameter(record,'VRMIN'),
            kpm=named_parameter(record,'KPM'),
            kim=named_parameter(record,'KIM'),
            vmmax=named_parameter(record,'VMMAX'),
            vmmin=named_parameter(record,'VMMIN'),
            ta=named_parameter(record,'TA'),
            vamax=named_parameter(record,'VAMAX'),
            vamin=named_parameter(record,'VAMIN'),
            kg=named_parameter(record,'KG'),
            tg=named_parameter(record,'TG'),
            vgmax=named_parameter(record,'VGMAX'),
            kp=named_parameter(record,'KP'),
            ki=named_parameter(record,'KI'),
            xl=named_parameter(record,'XL'),
            thetap=named_parameter(record,'THETAP'),
            kc=named_parameter(record,'KC'),
            vbmax=named_parameter(record,'VBMAX'),
            minimum_location=ExcitationLimiterLocation(record.icons[2]),maximum_location=ExcitationLimiterLocation(record.icons[1]),
            supplement_location=CompoundSupplementLocation(record.icons[0]),source=CompoundExcitationSource(record.icons[4])))
    elif record.model.upper() == 'ESST4B':
        template = build_st4b_template(vf,name,CompoundPiExciterParameters(
            tr=named_parameter(record,'TR'),kpr=named_parameter(record,'KPR'),kir=named_parameter(record,'KIR'),
            vrmax=named_parameter(record,'VRMAX'),vrmin=named_parameter(record,'VRMIN'),ta=named_parameter(record,'TA'),
            kpm=named_parameter(record,'KPM'),kim=named_parameter(record,'KIM'),vmmax=named_parameter(record,'VMMAX'),vmmin=named_parameter(record,'VMMIN'),
            kg=named_parameter(record,'KG'),kp=named_parameter(record,'KP'),ki=named_parameter(record,'KI'),vbmax=named_parameter(record,'VBMAX'),
            kc=named_parameter(record,'KC'),xl=named_parameter(record,'Xl'),thetap=named_parameter(record,'THETAP')))
    elif record.model.upper() in ('ST7B','ST7C'):
        if len(record.icons) != 2:
            raise ValueError('Self-feedback excitation requires explicit OEL/UEL selectors')
        else:
            pass
        template = build_self_feedback_exciter(vf,name,
            ExcitationBridgeDynamics.FIRING_LAG if record.model.upper() == 'ST7C' else ExcitationBridgeDynamics.INSTANTANEOUS,
            SelfFeedbackExciterParameters(tr=named_parameter(record,'TR'),tg=named_parameter(record,'TG'),tf=named_parameter(record,'TF'),
                vmax=named_parameter(record,'VMAX'),vmin=named_parameter(record,'VMIN'),kpa=named_parameter(record,'KPA'),
                vrmax=named_parameter(record,'VRMAX'),vrmin=named_parameter(record,'VRMIN'),kh=named_parameter(record,'KH'),kl=named_parameter(record,'KL'),
                tc=named_parameter(record,'TC'),tb=named_parameter(record,'TB'),kia=named_parameter(record,'KIA'),tia=named_parameter(record,'TIA'),
                ta=named_parameter(record,'TA') if record.model.upper() == 'ST7C' else .02,
                minimum_location=ExcitationLimiterLocation(record.icons[1]),maximum_location=ExcitationLimiterLocation(record.icons[0])),
            record.model.upper() == 'ST7C')
    elif record.model.upper() in ('ESST1A','ST1C'):
        if len(record.icons) != (3 if record.model.upper() == 'ST1C' else 2):
            raise ValueError('Terminal-fed static excitation requires UEL and stabilizer insertion flags')
        else:
            pass
        template = build_esst1a_template(vf,name,TerminalFedExciterParameters(
            tr=named_parameter(record,'TR'),vi_max=named_parameter(record,'VIMAX'),vi_min=named_parameter(record,'VIMIN'),
            tc=named_parameter(record,'TC'),tb=named_parameter(record,'TB'),tc1=named_parameter(record,'TC1'),tb1=named_parameter(record,'TB1'),
            ka=named_parameter(record,'KA'),ta=named_parameter(record,'TA'),va_max=named_parameter(record,'VAMAX'),va_min=named_parameter(record,'VAMIN'),
            vr_max=named_parameter(record,'VRMAX'),vr_min=named_parameter(record,'VRMIN'),kc=named_parameter(record,'KC'),
            kf=named_parameter(record,'KF'),tf=named_parameter(record,'TF'),klr=named_parameter(record,'KLR'),ilr=named_parameter(record,'ILR'),
            minimum_location=StaticMinimumExcitationLocation(record.icons[0]),stabilizer_location=StaticStabilizerLocation(record.icons[1])),
            StaticMaximumExcitationLocation(record.icons[2]) if record.model.upper() == 'ST1C' else None)
    elif record.model.upper() == 'BBSEX1':
        template = build_bbsex1_template(vf,name,FeedbackStaticExciterParameters(
            tr=named_parameter(record,'TF'),gain=named_parameter(record,'K'),
            t1=named_parameter(record,'T1'),t2=named_parameter(record,'T2'),
            t3=named_parameter(record,'T3'),t4=named_parameter(record,'T4'),
            regulator_max=named_parameter(record,'VRMAX'),regulator_min=named_parameter(record,'VRMIN'),
            field_max=named_parameter(record,'EFDMAX'),field_min=named_parameter(record,'EFDMIN'),
            auxiliary_location=AuxiliaryVoltageLocation.FIELD_OUTPUT if named_parameter(record,'Switch') == 0 else AuxiliaryVoltageLocation.VOLTAGE_ERROR))
    elif record.model.upper() == 'ESAC8B':
        if named_parameter(record,'KE') == 0 or named_parameter(record,'VRMAX') == 0:
            raise ValueError('ESAC8B automatic field/capability calibration has not been reviewed')
        else:
            pass
        template = build_esac8b_template(vf,name,DcExciterParameters(
            tr=named_parameter(record,'TR'),ka=named_parameter(record,'KA'),ta=named_parameter(record,'TA'),
            vrmax=named_parameter(record,'VRMAX'),vrmin=named_parameter(record,'VRMIN'),
            te=named_parameter(record,'TE'),ke=named_parameter(record,'KE'),
            e1=named_parameter(record,'E1'),se1=named_parameter(record,'SE1'),
            e2=named_parameter(record,'E2'),se2=named_parameter(record,'SE2')),
            named_parameter(record,'KP'),named_parameter(record,'KI'),
            named_parameter(record,'KD'),named_parameter(record,'TD'))
    elif binding.dc_kind is not None:
        kind: DcExciterKind = binding.dc_kind
        bounded_rotating: bool = kind in (DcExciterKind.BOUNDED_FIXED_SUPPLY,DcExciterKind.BOUNDED_TERMINAL_SUPPLY)
        field_coefficient: float = named_parameter(record,'KE')
        upper_capability: float = named_parameter(record,'VRMAX')
        p: DcExciterParameters = DcExciterParameters(tr=0.0 if kind == DcExciterKind.LIMITED_TYPE1 else named_parameter(record,'TR'),
            ka=named_parameter(record,'KA'),ta=named_parameter(record,'TA'),
            tb=0.0 if kind in (DcExciterKind.TYPE1,DcExciterKind.TYPE2,DcExciterKind.BRUSHLESS,DcExciterKind.LIMITED_TYPE1) else named_parameter(record,'TB'),
            tc=0.0 if kind in (DcExciterKind.TYPE1,DcExciterKind.TYPE2,DcExciterKind.BRUSHLESS,DcExciterKind.LIMITED_TYPE1) else named_parameter(record,'TC'),
            vrmax=None if upper_capability == 0 else upper_capability,vrmin=named_parameter(record,'VRMIN'),
            ke=None if field_coefficient == 0 else field_coefficient,te=named_parameter(record,'TE'),
            kf=named_parameter(record,'KF1' if record.model.upper() == 'IEEEX1' else 'KF'),
            tf=named_parameter(record,'TF' if kind in (DcExciterKind.TYPE1,DcExciterKind.LIMITED_TYPE1,DcExciterKind.BOUNDED_FIXED_SUPPLY,DcExciterKind.BOUNDED_TERMINAL_SUPPLY) else 'TF1'),
            e1=named_parameter(record,'E1'),se1=named_parameter(record,'SE1'),
            e2=named_parameter(record,'EFDMAX' if kind == DcExciterKind.LIMITED_TYPE1 else 'E2'),
            se2=named_parameter(record,'SEMAX' if kind == DcExciterKind.LIMITED_TYPE1 else 'SE2'),
            tf2=named_parameter(record,'TF2') if kind in (DcExciterKind.TYPE2,DcExciterKind.COMPENSATED_TYPE2,DcExciterKind.BRUSHLESS) else 1.0,
            tf3=named_parameter(record,'TF3') if kind == DcExciterKind.BRUSHLESS else 0.0,
            field_min=named_parameter(record,'VEMIN') if bounded_rotating else (named_parameter(record,'EFDMIN') if kind == DcExciterKind.LIMITED_TYPE1 else 0.0),
            field_max=named_parameter(record,'VEMAX') if bounded_rotating else 999.)
        template = build_dc_exciter(vf,name,kind,p,
            RotatingLimiterLocation(record.icons[1]) if bounded_rotating else RotatingLimiterLocation.SUMMATION,
            RotatingLimiterLocation(record.icons[0]) if bounded_rotating else RotatingLimiterLocation.SUMMATION)
    elif record.model.upper() in ('IEEET3','IEEEX3'):
        template = build_thevenin_exciter(vf,name,
            CompoundCapabilityLocation.TOTAL_FORCING if record.model.upper() == 'IEEET3' else CompoundCapabilityLocation.COMPOUND_SUPPLY,
            TheveninExciterParameters(tr=named_parameter(record,'TR'),ka=named_parameter(record,'KA'),ta=named_parameter(record,'TA'),
                regulator_max=named_parameter(record,'VRMAX'),regulator_min=named_parameter(record,'VRMIN'),
                te=named_parameter(record,'TE'),kf=named_parameter(record,'KF'),tf=named_parameter(record,'TF'),
                kp=named_parameter(record,'KP'),ki=named_parameter(record,'KI'),supply_max=named_parameter(record,'VBMAX'),ke=named_parameter(record,'KE')))
    elif record.model.upper() in ('EXST2','EXST2A','ESST2A'):
        template = build_exst2_template(vf,name,transducer_time=named_parameter(record,'TR'),
            regulator_gain=named_parameter(record,'KA'),regulator_time=named_parameter(record,'TA'),
            regulator_max=named_parameter(record,'VRMAX'),regulator_min=named_parameter(record,'VRMIN'),
            field_feedback=named_parameter(record,'KE'),exciter_time=named_parameter(record,'TE'),
            rate_gain=named_parameter(record,'KF'),rate_time=named_parameter(record,'TF'),
            potential_gain=named_parameter(record,'KP'),current_gain=named_parameter(record,'KI'),
            commutation_gain=named_parameter(record,'KC'),field_max=named_parameter(record,'EFDMAX'),
            initial_field_voltage=0.0,
            kind=CompoundExciterKind.ADDITIVE_BRIDGE if record.model.upper() == 'EXST2' else (
                CompoundExciterKind.GATED_MULTIPLICATIVE_BRIDGE if record.model.upper() == 'ESST2A' else CompoundExciterKind.MULTIPLICATIVE_BRIDGE))
    elif record.model.upper() in ('IVOST','IVOGO'):
        rational_stages: tuple[RationalStageParameters,RationalStageParameters,RationalStageParameters] = (
            RationalStageParameters(gain=named_parameter(record,'K1'),numerator=named_parameter(record,'A1'),
                denominator=named_parameter(record,'A2'),lead=named_parameter(record,'T1'),lag=named_parameter(record,'T2'),
                maximum=named_parameter(record,'MAX1'),minimum=named_parameter(record,'MIN1')),
            RationalStageParameters(gain=named_parameter(record,'K3'),numerator=named_parameter(record,'A3'),
                denominator=named_parameter(record,'A4'),lead=named_parameter(record,'T3'),lag=named_parameter(record,'T4'),
                maximum=named_parameter(record,'MAX3'),minimum=named_parameter(record,'MIN3')),
            RationalStageParameters(gain=named_parameter(record,'K5'),numerator=named_parameter(record,'A5'),
                denominator=named_parameter(record,'A6'),lead=named_parameter(record,'T5'),lag=named_parameter(record,'T6'),
                maximum=named_parameter(record,'MAX5'),minimum=named_parameter(record,'MIN5')),
        )
        if record.model.upper() == 'IVOST':
            template = build_ivost_template(vf,name,rational_stages)
        else:
            template = build_ivogo_template(vf,name,rational_stages)
    elif record.model.upper() == 'COMP':
        template = build_comp_template(vf, name, reactance=named_parameter(record,'Xe'))
    elif binding.standard is not None:
        if record.model.upper() in ('AC6A','ESAC6A'):
            parameters: Ac6aParameters = Ac6aParameters(
                tr=named_parameter(record,'TR'),ka=named_parameter(record,'KA'),
                ta=named_parameter(record,'TA'),tk=named_parameter(record,'TK'),
                tb=named_parameter(record,'TB'),tc=named_parameter(record,'TC'),
                vamax=named_parameter(record,'VAMAX'),vamin=named_parameter(record,'VAMIN'),
                vrmax=named_parameter(record,'VRMAX'),vrmin=named_parameter(record,'VRMIN'),
                te=named_parameter(record,'TE'),vfelim=named_parameter(record,'VFELIM'),
                kh=named_parameter(record,'KH'),vhmax=named_parameter(record,'VHMAX'),
                th=named_parameter(record,'TH'),tj=named_parameter(record,'TJ'),
                kc=named_parameter(record,'KC'),kd=named_parameter(record,'KD'),
                ke=named_parameter(record,'KE'),e1=named_parameter(record,'E1'),
                se1=named_parameter(record,'SE1'),e2=named_parameter(record,'E2'),
                se2=named_parameter(record,'SE2'))
            if record.model.upper() == 'AC6A':
                template = build_ac6a_template(vf,name,parameters)
            else:
                template = build_esac6a_template(vf,name,parameters)
        elif record.model.upper() in ('AC1C','AC2C','AC5C'):
            existing_uids: set[int] = set(vf.get_vars_dict().keys())
            existing_uids.update(vf.get_diff_var_dict().keys())
            if record.model.upper() == 'AC1C':
                template = build_ac1c_template(vf,name,RotatingLimiterLocation(record.icons[1]),RotatingLimiterLocation(record.icons[0]))
            elif record.model.upper() == 'AC2C':
                template = build_ac2c_template(vf,name,RotatingLimiterLocation(record.icons[1]),RotatingLimiterLocation(record.icons[0]))
            else:
                template = build_ac5c_template(vf,name,RotatingLimiterLocation(record.icons[1]),RotatingLimiterLocation(record.icons[0]))
            _normalize_imported_variable_names(vf,existing_uids)
        elif record.model.upper() == 'SCRX':
            existing_uids: set[int] = set(vf.get_vars_dict().keys())
            existing_uids.update(vf.get_diff_var_dict().keys())
            template = build_scrx_template(vf,name,exciter_time=named_parameter(record,'TE'))
            _normalize_imported_variable_names(vf,existing_uids)
        else:
            template = build_international_standard_template(binding.standard, vf, name)
        bind_parameters(template.block,record,binding,vf,name)
        if record.model.upper() == 'PSS6C':
            set_rms_model_parameter(template.block,'pss_Ics1_'+name,float(record.icons[0]),vf)
            set_rms_model_parameter(template.block,'pss_Ics2_'+name,float(record.icons[2]),vf)
        else:
            pass
        if record.model.upper() == 'SEXS':
            set_rms_model_parameter(template.block,'Ta_'+name,named_parameter(record,'TATB')*named_parameter(record,'TB'),vf)
        elif record.model.upper() == 'SCRX':
            set_rms_model_parameter(template.block,'avr_tA_'+name,named_parameter(record,'TATB')*named_parameter(record,'TB'),vf)
        else:
            pass
        if record.model.upper() in ('EXAC1','EXAC1A','ESAC1A','EXAC2','EXAC3','ESAC2A','ESAC3A','EXBAS','AC1C','AC2C','AC5C'):
            variables: dict[str, Var] = dict((var.name, var) for var in template.block.event_dict)
            lead_state: Var = next(var for var in template.block.state_vars if var.name == 'avr_leadLag_x_scaled_1_'+name)
            template.block.init_eqs[lead_state] = variables['avr_leadLag_a_end_'+name] * variables['avr_leadLag_x_start_1_'+name]
            if named_parameter(record,'SE1') == 0 and named_parameter(record,'SE2') == 0:
                # Remove the disabled curve structurally rather than evaluate
                # a gated zero multiplied by an undefined saturation fit.
                for coefficient in ('avr_Sq','avr_Bsq','avr_VExcThresholdPu'):
                    set_rms_model_parameter(template.block,coefficient+'_'+name,0.0,vf)
            else:
                pass
        else:
            pass
        if record.model.upper() == 'IEEEG2' and named_parameter(record,'T1') == 0:
            # A zero speed-filter lag is an exact measurement identity. The
            # following positive T3 compensator still makes the transfer proper.
            filter_name: str = 'gov_firstOrder_y_'+name
            filter_index: int = next(index for index,variable in enumerate(template.block.state_vars) if variable.name == filter_name)
            filter_state: Var = template.block.state_vars.pop(filter_index)
            template.block.state_eqs.pop(filter_index)
            template.block.diff_vars.pop(filter_index)
            template.block.algebraic_vars.append(filter_state)
            template.block.algebraic_eqs.append(filter_state-(template.block.in_vars[0]-template.block.in_vars[1]))
        else:
            pass
        # Generated catalogue components include stand-alone input declarations
        # and unused Modelica diagnostic/$START variables. Inputs are owned by
        # the host once wired; dead declarations must not make its DAE singular.
        used: set[int] = set()
        for equations in (template.block.state_eqs, template.block.algebraic_eqs):
            for equation in equations:
                used.update(var.uid for var in equation.get_vars())
        inputs: set[int] = set(var.uid for var in template.block.in_vars)
        retained: list[Var] = list()
        for variable in template.block.algebraic_vars:
            if variable.uid in inputs:
                pass
            elif variable.uid in used:
                retained.append(variable)
            else:
                template.block.init_eqs.pop(variable, None)
        template.block.algebraic_vars = retained
    else:
        raise ValueError('No reviewed native controller builder')
    return template


def configure_exst1_algebraic_lags(block: Block, record: DyrRecord) -> None:
    """Lower documented zero-time-constant EXST1 lags to exact algebraic equations.

    :param block: Fresh native EXST1 block, with reviewed original state/port order.
    :param record: Source constants; no epsilon replaces zero lags.
    """
    states: list[Var] = list()
    equations: list[Expr] = list()
    derivatives: list[Var] = list()
    gain: Var = next(var for var in block.event_dict if var.name == 'KA')
    for index, parameter in enumerate(('TR','TB','TA','TF')):
        state: Var = block.state_vars[index]
        if named_parameter(record,parameter) != 0:
            states.append(state)
            equations.append(block.state_eqs[index])
            if index < len(block.diff_vars):
                derivatives.append(block.diff_vars[index])
            else:
                pass
        else:
            block.algebraic_vars.append(state)
            if index == 0:
                block.algebraic_eqs.append(block.in_vars[1]-state)
            elif index == 1:
                block.algebraic_eqs.append(block.algebraic_vars[2]-state)
                block.algebraic_eqs[3] = block.algebraic_vars[3]-block.algebraic_vars[2]
            elif index == 2:
                block.algebraic_eqs.append(gain*block.algebraic_vars[3]-state)
            else:
                block.algebraic_eqs.append(block.state_vars[2]-state)
                block.algebraic_eqs[4] = block.algebraic_vars[4]
    block.state_vars = states
    block.state_eqs = equations
    block.diff_vars = derivatives


def freeze_named_parameter(block: Block, name: str, initial: Expr | Const, vf: VarFactory) -> None:
    """Initialize a native service parameter from the host's power-flow state.

    :param block: Controller block.
    :param name: Exact native parameter name.
    :param initial: Initialization expression.
    :param vf: Circuit symbol factory.
    :raises ValueError: Missing or ambiguous parameter mapping.
    """
    matches: list[Var] = [var for var in block.event_dict if var.name == name]
    if len(matches) != 1:
        raise ValueError('Native service parameter not unique: ' + name)
    else:
        parameter: Var = matches[0]
        block.event_dict[parameter] = vf.add_const(value=None, name=name)
        block.init_eqs[parameter] = initial


def connect_scaled(root: Block, target: Var, source: Var, factor: float, vf: VarFactory) -> None:
    """Connect a controller port with an explicit machine/system base conversion.

    :param root: Owning composite block for a required scaling equation.
    :param target: Consuming port.
    :param source: Producing signal.
    :param factor: Target units divided by source units.
    :param vf: Shared symbol factory.
    """
    if factor == 1.0:
        vf.add_connection(target, source)
    else:
        root.algebraic_vars.append(target)
        root.algebraic_eqs.append(target - source * sym.Const(factor))
        root.init_eqs[target] = source * sym.Const(factor)


def bind_supplementary_voltage(root: Block, block: Block, port: Var, vf: VarFactory,
                                stabilizer: Block | None, underexcitation: Block | None,
                                overexcitation: Block | None = None) -> None:
    """Connect additive voltage controls to an exciter's common summation port.

    :param root: Assembly owning a required signal-summing equation.
    :param block: Exciter owning the open input port.
    :param port: Common supplementary voltage input.
    :param vf: Shared circuit variable factory.
    :param stabilizer: Optional supplementary damping controller.
    :param underexcitation: Optional additive minimum-excitation controller.
    """
    if stabilizer is None and underexcitation is None and overexcitation is None:
        freeze_input(block,port,vf,sym.Const(0.0))
    else:
        signal: Expr = sym.Const(0.0)
        if stabilizer is not None:
            signal = signal+stabilizer.out_vars[0]
        else:
            pass
        if underexcitation is not None:
            signal = signal+underexcitation.out_vars[0]
        else:
            pass
        if overexcitation is not None:
            signal = signal+overexcitation.out_vars[0]
        else:
            pass
        root.algebraic_vars.append(port)
        root.algebraic_eqs.append(port-signal)
        root.init_eqs[port] = signal


def attach_controller(template: RmsModelTemplate, machine: Block, controller: RmsModelTemplate,
                      record: DyrRecord, vf: VarFactory, base_ratio: float, system_base: float,
                      stabilizer: Block | None = None, compensator: Block | None = None,
                      underexcitation: Block | None = None, load_controller: Block | None = None,
                      overexcitation: Block | None = None,
                      overexcitation_record: DyrRecord | None = None) -> None:
    """Wire a reviewed governor/exciter to one complete generator model.

    :param template: Composite generator template.
    :param machine: Network-facing machine block with reviewed port order.
    :param controller: Parameterized native component.
    :param record: Source controller record.
    :param vf: Circuit symbol factory.
    :param base_ratio: Machine MVA divided by system MVA.
    :param system_base: Network power base in MVA for an explicitly rated turbine.
    :param stabilizer: Optional already-connected supplementary-voltage controller.
    :param compensator: Optional already-connected voltage measurement component.
    :param underexcitation: Optional already-connected additive minimum-excitation limiter.
    :param load_controller: Optional reviewed outer load controller, consumed by its compatible governor.
    """
    model: str = dynamic_record_name(record)
    if model == 'ST8C':
        block: Block = controller.block
    else:
        block = controller.block.children[0] if controller.block.children else controller.block
    binding: PsseDynamicBinding | None = dynamic_binding(model)
    dc_kind: DcExciterKind | None = None if binding is None else binding.dc_kind
    electromechanical_kind: ElectromechanicalExciterKind | None = None if binding is None else binding.electromechanical_kind
    sensed_voltage: Var = machine.in_vars[0] if compensator is None else compensator.out_vars[0]
    stabilizer_bias: Expr = Const(0.0) if stabilizer is None else stabilizer.out_vars[0]
    # Connections replace port references; capture the machine's operating-point
    # expression before the field port is rebound to the controller output.
    field_initial: Expr | Const | None = machine.init_eqs.get(machine.in_vars[3], None) if len(machine.in_vars) > 3 else None
    controller_reference_index: int = 0 if model == 'AC11C' else (4 if model == 'ST6B' else 1)
    controller_reference_initial: Expr | Const | None = (
        block.init_eqs.get(block.in_vars[controller_reference_index], None)
        if model in ('AC6A','ESAC6A','EXST2','EXST2A','ESST2A','IEEET3','IEEEX3','EXAC4','ESAC4A','AC4C','ESAC8B','BBSEX1','BUDCZT','ESST1A','ST1C','ST7B','ST7C','ST5B','ST5C','ST6B','ST6C','ST8C','AC6C','AC6C2','AC7B','AC7C','AC8B','AC8C','AC11C','ST4C','ESST4B','IEET1B','EXNI','EXPIC1','DC4B','DC4C')
        or dc_kind is not None or electromechanical_kind is not None else None
    )
    pid_reference_initial: Expr | Const | None = block.init_eqs.get(block.in_vars[1],None) if model in ('PIDGOV','PIDGOVD','PIDGOVDU') else None
    fuel_reference_initial: Expr | Const | None = block.init_eqs.get(block.in_vars[2],None) if model in ('GGOV1','GGOV1D','GGOV1DU') else None
    rational_reference: Expr | Const | None = block.init_eqs.get(block.in_vars[1],None) if model == 'IVOGO' else None
    engine_reference: Expr | Const | None = block.init_eqs.get(block.in_vars[2],None) if model in ('DEGOV','DEGOV1','DEGOV1D','DEGOV1DU') else None
    # OpenIPSL components carry stand-alone input guesses. They must not
    # overwrite the producing machine/bus initializer after port rebinding.
    for input_port in block.in_vars:
        block.init_eqs.pop(input_port, None)
    if (binding is not None and binding.role == PsseDynamicRole.EXCITER
            and field_initial is not None and model != 'AC9C'):
        block.init_eqs[block.out_vars[0]] = field_initial
    else:
        pass
    if model in ('WESGOV', 'WESGOVD', 'WESGOVDU'):
        is_deadband: bool = model in ('WESGOVD', 'WESGOVDU')
        turbine_rating: float = named_parameter(record, 'TRATE') if is_deadband else 0.0
        turbine_ratio: float = (
            turbine_rating / system_base if turbine_rating > 0.0 else base_ratio
        )
        if turbine_ratio <= 0.0:
            raise ValueError('WESGOV requires a positive machine or turbine power base')
        else:
            pass
        speed: Var = machine.out_vars[2]
        electrical_power: Var = machine.out_vars[0]
        machine_torque: Var = machine.out_vars[3] if len(machine.out_vars) == 4 else machine.out_vars[4]
        initial_mechanical_power: Expr = machine_torque * Const(base_ratio / turbine_ratio)
        vf.add_connection(block.in_vars[0], speed)
        connect_scaled(template.block, block.in_vars[1], electrical_power,
                       1.0 / turbine_ratio, vf)
        freeze_input(block, block.in_vars[2], vf, initial_mechanical_power)
        command_parameters: list[Var] = [
            parameter for parameter in block.event_dict
            if parameter.name == 'ValveCommandPu_' + block.name
        ]
        if len(command_parameters) != 1:
            raise ValueError('WESGOV sampled command parameter is not unique')
        else:
            block.event_dict[command_parameters[0]] = initial_mechanical_power
        for variable in block.state_vars + block.algebraic_vars:
            if variable.name.startswith(('ValvePositionPu_', 'MechanicalPowerPu_')):
                block.init_eqs[variable] = initial_mechanical_power
            else:
                pass
        connect_scaled(template.block, machine.in_vars[2], block.out_vars[0],
                       turbine_ratio, vf)
    elif model == 'BBGOV1':
        if base_ratio <= 0.0:
            raise ValueError('BBGOV1 requires a positive generator/system MVA ratio')
        elif named_parameter(record, 'KP') <= 0.0 or named_parameter(record, 'KD') <= 0.0:
            raise ValueError('BBGOV1 equilibrium requires positive PI and valve gains')
        else:
            pass
        machine_torque: Var = machine.out_vars[3] if len(machine.out_vars) == 4 else machine.out_vars[4]
        initial_power: Expr = machine_torque / Const(base_ratio)
        selected_feedback: Expr = (
            machine.out_vars[0] / Const(base_ratio)
            if named_parameter(record, 'SWITCH') == 0.0 else initial_power
        )
        vf.add_connection(block.in_vars[0], machine.out_vars[2])
        freeze_input(block, block.in_vars[1], vf, selected_feedback)
        connect_scaled(template.block, block.in_vars[2], machine.out_vars[0], 1.0 / base_ratio, vf)
        connect_scaled(template.block, machine.in_vars[2], block.out_vars[0], base_ratio, vf)
        for state in block.state_vars:
            if state.name.startswith(('ValveOutputPu_', 'SteamOutputPu_',
                                      'IntermediateTurbinePowerPu_', 'LowPressureTurbinePowerPu_')):
                block.init_eqs[state] = initial_power
            elif state.name.startswith('StepGradientLimiterPu_'):
                block.init_eqs[state] = Const(0.0)
            elif state.name.startswith('PIControllerIntegralPu_'):
                block.init_eqs[state] = initial_power / Const(
                    named_parameter(record, 'KP') * named_parameter(record, 'KD'),
                )
            elif state.name.startswith('PowerFeedbackPu_'):
                block.init_eqs[state] = selected_feedback
            else:
                raise ValueError('BBGOV1 contains an unreviewed native state')
        for variable in block.algebraic_vars:
            if variable.name.startswith('PIControllerOutputPu_'):
                block.init_eqs[variable] = initial_power / Const(named_parameter(record, 'KD'))
            elif variable.name.startswith('PowerFeedbackPu_'):
                block.init_eqs[variable] = selected_feedback
            elif variable.name.startswith('StepGradientLimiterFeedbackPu_'):
                block.init_eqs[variable] = Const(0.0)
            elif variable.name.startswith('MechanicalPowerPu_'):
                block.init_eqs[variable] = initial_power
            else:
                pass
        block.init_eqs[block.out_vars[0]] = initial_power
    elif model == 'TGOV2':
        if base_ratio <= 0.0:
            raise ValueError('TGOV2 requires a positive generator/system MVA ratio')
        else:
            pass
        machine_speed: Var = machine.out_vars[2]
        machine_torque: Var = machine.out_vars[3] if len(machine.out_vars) == 4 else machine.out_vars[4]
        initial_mechanical_power: Expr = machine_torque / Const(base_ratio)
        if len(block.state_vars) != 4 or len(block.in_vars) != 2 or len(block.out_vars) != 1:
            raise ValueError('TGOV2 native state and port layout is inconsistent')
        else:
            pass
        controller_reference: Expr = Const(named_parameter(record,'R')) * initial_mechanical_power
        freeze_input(block,block.in_vars[0],vf,controller_reference)
        template.block.algebraic_vars.append(block.in_vars[1])
        template.block.algebraic_eqs.append(block.in_vars[1]-(machine_speed-Const(1.0)))
        template.block.init_eqs[block.in_vars[1]] = machine_speed-Const(1.0)
        connect_scaled(template.block,machine.in_vars[2],block.out_vars[0],base_ratio,vf)
        block.init_eqs[block.state_vars[0]] = initial_mechanical_power
        block.init_eqs[block.state_vars[1]] = initial_mechanical_power*Const(1.0-named_parameter(record,'K'))
        block.init_eqs[block.state_vars[2]] = initial_mechanical_power*Const(1.0-named_parameter(record,'K'))
        block.init_eqs[block.state_vars[3]] = Const(1.0)
        block.init_eqs[block.out_vars[0]] = initial_mechanical_power
    elif model in ('TGOV3', 'TGOV3D', 'TGOV3DU'):
        if base_ratio <= 0.0:
            raise ValueError('TGOV3 requires a positive generator/system MVA ratio')
        else:
            pass
        turbine_rating_ratio: float = 1.0
        if model in ('TGOV3D', 'TGOV3DU') and named_parameter(record, 'TRATE') > 0.0:
            machine_rating: float = base_ratio * system_base
            turbine_rating_ratio = named_parameter(record, 'TRATE') / machine_rating
        else:
            pass
        machine_speed: Var = machine.out_vars[2]
        machine_torque: Var = machine.out_vars[3] if len(machine.out_vars) == 4 else machine.out_vars[4]
        initial_mechanical_power: Expr = machine_torque / Const(
            base_ratio * turbine_rating_ratio,
        )
        fraction_sum: float = (named_parameter(record, 'K1')
                               + named_parameter(record, 'K2')
                               + named_parameter(record, 'K3'))
        initial_stage_power: Expr = initial_mechanical_power / Const(fraction_sum)
        expected_state_count: int = 6 if named_parameter(record, 'T1') > 0.0 else 5
        if (len(block.state_vars) != expected_state_count
                or len(block.in_vars) != 2 or len(block.out_vars) != 1):
            raise ValueError('TGOV3 native state and port layout is inconsistent')
        else:
            pass
        freeze_input(block, block.in_vars[1], vf, initial_stage_power)
        speed_input: Var = block.in_vars[0]
        template.block.algebraic_vars.append(speed_input)
        template.block.algebraic_eqs.append(speed_input - (machine_speed - Const(1.0)))
        template.block.init_eqs[speed_input] = machine_speed - Const(1.0)
        connect_scaled(
            template.block, machine.in_vars[2], block.out_vars[0],
            base_ratio * turbine_rating_ratio, vf,
        )
        for state in block.state_vars:
            if state.name.startswith('TGOV3SpeedFilterPu_'):
                block.init_eqs[state] = Const(0.0)
            elif state.name.startswith('TGOV3InterceptValvePositionPu_'):
                block.init_eqs[state] = Const(1.0)
            elif state.name.startswith((
                    'TGOV3GovernorOutputPu_', 'TGOV3TurbineT4Pu_',
                    'TGOV3ReheatIntegratorPu_', 'TGOV3TurbineT6Pu_')):
                block.init_eqs[state] = initial_stage_power
            else:
                raise ValueError('TGOV3 family contains an unreviewed native state')
        for variable in block.algebraic_vars:
            if variable.name.startswith(('TGOV3ReheatPowerPu_', 'TGOV3FlowPu_')):
                block.init_eqs[variable] = initial_stage_power
            elif variable.name.startswith('TGOV3ValveFlowPu_'):
                block.init_eqs[variable] = Const(1.0)
            else:
                pass
        block.init_eqs[block.out_vars[0]] = initial_mechanical_power
    elif model == 'ST6B':
        if field_initial is None or controller_reference_initial is None:
            raise ValueError('ST6B field and voltage-reference initialization is missing')
        elif len(block.in_vars) != 7 or len(record.icons) != 1 or record.icons[0] not in (1, 2):
            raise ValueError('ST6B requires its seven reviewed inputs and OEL selector')
        elif overexcitation is not None:
            raise ValueError('ST6B OEL injection is not yet reviewed')
        elif underexcitation is not None:
            raise ValueError('ST6B UEL injection requires the unmodeled high/low-value gate paths')
        else:
            pass
        vf.add_connection(machine.in_vars[3], block.out_vars[0])
        vf.add_connection(block.in_vars[0], machine.out_vars[3])
        vf.add_connection(block.in_vars[3], sensed_voltage)
        freeze_input(block, block.in_vars[1], vf, Const(0.0))
        bind_supplementary_voltage(template.block, block, block.in_vars[2], vf, stabilizer, None)
        freeze_input(block, block.in_vars[4], vf, controller_reference_initial)
        freeze_input(block, block.in_vars[5], vf, Const(0.0))
        vf.add_connection(block.in_vars[6], machine.in_vars[0])
        freeze_named_parameter(block, 'avr_Efd0Pu_' + controller.name, field_initial, vf)
        freeze_named_parameter(block, 'avr_Us0Pu_' + controller.name, sensed_voltage, vf)
        template.block.children.append(block)
    elif model in ('AC6A','ESAC6A'):
        if field_initial is None or controller_reference_initial is None:
            raise ValueError('AC6A requires field and voltage-reference initializations')
        else:
            pass
        vf.add_connection(machine.in_vars[3],block.out_vars[0])
        vf.add_connection(block.in_vars[0],sensed_voltage)
        freeze_input(block,block.in_vars[1],vf,controller_reference_initial)
        bind_supplementary_voltage(template.block,block,block.in_vars[2],vf,stabilizer,None,overexcitation)
        uel_signal: Expr = Const(0.0) if underexcitation is None else underexcitation.out_vars[0]
        signals: tuple[tuple[Var,Expr],...] = (
            (block.in_vars[3],uel_signal),
            (block.in_vars[4],machine.out_vars[3]),
            (block.in_vars[5],machine.in_vars[0]),
        )
        for port,signal in signals:
            template.block.algebraic_vars.append(port)
            template.block.algebraic_eqs.append(port-signal)
            template.block.init_eqs[port] = signal
        freeze_named_parameter(block,'Efd0Pu_'+controller.name,field_initial,vf)
        freeze_named_parameter(block,'Ifd0Pu_'+controller.name,machine.out_vars[3],vf)
        freeze_named_parameter(block,'Vt0Pu_'+controller.name,sensed_voltage,vf)
        freeze_named_parameter(block,'Vs0Pu_'+controller.name,stabilizer_bias,vf)
        freeze_named_parameter(block,'Uel0Pu_'+controller.name,uel_signal,vf)
        if overexcitation is not None and overexcitation_record is not None:
            if model not in ('AC6A', 'ESAC6A'):
                raise ValueError('Over-excitation limiters currently require the reviewed AC6A/ESAC6A feedback ports')
            else:
                pass
            selection: int = 0
            if dynamic_record_name(overexcitation_record) != 'MAXEX1':
                selection = int(overexcitation_record.icons[0])
            else:
                pass
            if dynamic_record_name(overexcitation_record) == 'MAXEX1':
                measurement: Expr = block.out_vars[0]
            elif dynamic_record_name(overexcitation_record) == 'MAXEX2' and selection == 0:
                measurement = block.out_vars[0]
            elif dynamic_record_name(overexcitation_record) == 'MAXEX2' and selection == 1:
                measurement = machine.out_vars[3]
            elif dynamic_record_name(overexcitation_record) == 'OEL2C' and selection == 1:
                measurement = block.out_vars[0]
            elif dynamic_record_name(overexcitation_record) == 'OEL2C' and selection == 2:
                measurement = machine.out_vars[3]
            elif dynamic_record_name(overexcitation_record) == 'OEL2C':
                measurement = block.out_vars[2]
            else:
                raise ValueError('Over-excitation measurement selector is unsupported')
            oel_input: Var = overexcitation.in_vars[0]
            template.block.algebraic_vars.append(oel_input)
            template.block.algebraic_eqs.append(oel_input-measurement)
            template.block.init_eqs[oel_input] = measurement
            if dynamic_record_name(overexcitation_record) == 'OEL2C':
                input_parameter: Var = next(parameter for parameter in overexcitation.event_dict
                                            if parameter.name == 'oel_Input0Pu_' + overexcitation.name)
                overexcitation.event_dict[input_parameter] = measurement
            else:
                pass
            template.block.children.append(overexcitation)
        else:
            pass
        template.block.children.append(block)
    elif model == 'TGOV1':
        vf.add_connection(machine.in_vars[2], block.out_vars[0])
        vf.add_connection(block.in_vars[0], machine.out_vars[2])
        torque: Var = machine.out_vars[3] if len(machine.out_vars) == 4 else machine.out_vars[4]
        vf.add_connection(block.in_vars[1], torque)
    elif model in ('GGOV1','GGOV1D','GGOV1DU'):
        fuel_rating: float = named_parameter(record,'TRATE')
        fuel_ratio: float = fuel_rating/system_base if fuel_rating > 0 else base_ratio
        fuel_initial: Var = machine.out_vars[3] if len(machine.out_vars) == 4 else machine.out_vars[4]
        if fuel_reference_initial is None:
            raise ValueError('Fuel-governor speed/load reference initialization is missing')
        else:
            pass
        vf.add_connection(block.in_vars[0],machine.out_vars[2])
        connect_scaled(template.block,block.in_vars[1],machine.out_vars[0],1/fuel_ratio,vf)
        connect_scaled(template.block,machine.in_vars[2],block.out_vars[0],fuel_ratio,vf)
        freeze_named_parameter(block,'InitialMechanicalPowerPu_'+controller.name,fuel_initial/Const(fuel_ratio),vf)
        freeze_input(block,block.in_vars[2],vf,fuel_reference_initial)
        freeze_input(block,block.in_vars[3],vf,machine.out_vars[0]/Const(fuel_ratio))
    elif model == 'IVOGO':
        if rational_reference is None:
            raise ValueError('Rational governor operating-point reference is missing')
        else:
            pass
        rational_torque0: Var = machine.out_vars[3] if len(machine.out_vars) == 4 else machine.out_vars[4]
        vf.add_connection(block.in_vars[0],machine.out_vars[2])
        connect_scaled(template.block,machine.in_vars[2],block.out_vars[1],base_ratio,vf)
        freeze_named_parameter(block,'InitialMechanicalPowerPu_'+controller.name,rational_torque0*machine.out_vars[2]/Const(base_ratio),vf)
        freeze_input(block,block.in_vars[1],vf,rational_reference)
    elif model in ('DEGOV','DEGOV1','DEGOV1D','DEGOV1DU'):
        engine_rating: float = named_parameter(record,'TRATE') if model in ('DEGOV1D','DEGOV1DU') else 0.
        engine_ratio: float = engine_rating/system_base if engine_rating > 0 else base_ratio
        engine_initial: Var = machine.out_vars[3] if len(machine.out_vars) == 4 else machine.out_vars[4]
        if engine_reference is None:
            raise ValueError('Engine governor reference initialization is missing')
        else:
            pass
        vf.add_connection(block.in_vars[0],machine.out_vars[2])
        connect_scaled(template.block,block.in_vars[1],machine.out_vars[0],1/engine_ratio,vf)
        connect_scaled(template.block,machine.in_vars[2],block.out_vars[1],engine_ratio,vf)
        freeze_named_parameter(block,'InitialMechanicalTorquePu_'+controller.name,engine_initial/Const(engine_ratio),vf)
        freeze_named_parameter(block,'InitialElectricalPowerPu_'+controller.name,machine.out_vars[0]/Const(engine_ratio),vf)
        freeze_input(block,block.in_vars[2],vf,engine_reference)
    elif model in ('IEEEG1','IEEEG1D','IEEEG1SDU'):
        steam_rating: float = named_parameter(record,'TRATE') if model in ('IEEEG1D','IEEEG1SDU') else 0.0
        steam_ratio: float = steam_rating/system_base if steam_rating > 0 else base_ratio
        vf.add_connection(block.in_vars[0],machine.out_vars[2])
        connect_scaled(template.block,machine.in_vars[2],block.out_vars[2],steam_ratio,vf)
        steam_initial: Var = machine.out_vars[3] if len(machine.out_vars) == 4 else machine.out_vars[4]
        freeze_input(block,block.in_vars[1],vf,Const(1.0))
        if load_controller is None:
            freeze_input(block,block.in_vars[2],vf,steam_initial/Const(steam_ratio))
        else:
            fraction_sum: float = sum(named_parameter(record,'K'+str(index)) for index in range(1,9))
            freeze_input(load_controller,load_controller.in_vars[2],vf,steam_initial/Const(steam_ratio*fraction_sum))
            connect_scaled(template.block,block.in_vars[2],load_controller.out_vars[0],fraction_sum,vf)
    elif model in ('IEEEG3','IEEEG3D','IEEEG3DU'):
        turbine_rating: float = named_parameter(record,'TRATE') if model in ('IEEEG3D','IEEEG3DU') else 0.0
        turbine_ratio: float = turbine_rating/system_base if turbine_rating > 0 else base_ratio
        vf.add_connection(block.in_vars[0],machine.out_vars[2])
        connect_scaled(template.block,machine.in_vars[2],block.out_vars[0],turbine_ratio,vf)
        initial_power: Var = machine.out_vars[3] if len(machine.out_vars) == 4 else machine.out_vars[4]
        freeze_input(block,block.in_vars[1],vf,initial_power/Const(turbine_ratio))
    elif model == 'IEEEG2':
        vf.add_connection(block.in_vars[0],machine.out_vars[2])
        connect_scaled(template.block,machine.in_vars[2],block.out_vars[0],base_ratio,vf)
        torque: Var = machine.out_vars[3] if len(machine.out_vars) == 4 else machine.out_vars[4]
        initial: Expr = torque/sym.Const(base_ratio)
        freeze_input(block,block.in_vars[1],vf,sym.Const(1.0))
        freeze_input(block,block.in_vars[2],vf,initial)
        freeze_named_parameter(block,'gov_Pm0Pu_'+controller.name,initial,vf)
    elif model in ('GAST','GASTD','GASTDU','IEESGO','IEESGOD','IEESGODU','TGOV1D','TGOV1DU'):
        family_ratio: float = base_ratio if model in ('GAST','IEESGO') else (named_parameter(record,'TRATE')/system_base if named_parameter(record,'TRATE') > 0 else base_ratio)
        vf.add_connection(block.in_vars[0], machine.out_vars[2])
        connect_scaled(template.block, machine.in_vars[2], block.out_vars[0], family_ratio, vf)
        torque: Var = machine.out_vars[3] if len(machine.out_vars) == 4 else machine.out_vars[4]
        freeze_input(block, block.in_vars[1], vf, torque / sym.Const(family_ratio))
    elif model in ('PIDGOV','PIDGOVD','PIDGOVDU'):
        pid_ratio: float = base_ratio if model == 'PIDGOV' else (named_parameter(record,'TRATE')/system_base if named_parameter(record,'TRATE') > 0 else base_ratio)
        if pid_reference_initial is None:
            raise ValueError('Hydraulic PID reference initialization is missing')
        else:
            pass
        vf.add_connection(block.in_vars[0],machine.out_vars[2])
        connect_scaled(template.block,block.in_vars[2],machine.out_vars[0],1./pid_ratio,vf)
        connect_scaled(template.block,machine.in_vars[2],block.out_vars[0],pid_ratio,vf)
        pid_torque: Var = machine.out_vars[3] if len(machine.out_vars) == 4 else machine.out_vars[4]
        freeze_named_parameter(block,'Pm0Pu_'+controller.name,pid_torque/Const(pid_ratio),vf)
        freeze_named_parameter(block,'Pe0Pu_'+controller.name,machine.out_vars[0]/Const(pid_ratio),vf)
        freeze_input(block,block.in_vars[1],vf,pid_reference_initial)
    elif model in ('HYGOV2','HYGOV2D','HYGOV2DU'):
        cascade_ratio: float = base_ratio if model == 'HYGOV2' else (named_parameter(record,'TRATE')/system_base if named_parameter(record,'TRATE') > 0 else base_ratio)
        vf.add_connection(block.in_vars[0],machine.out_vars[2])
        connect_scaled(template.block,machine.in_vars[2],block.out_vars[0],cascade_ratio,vf)
        cascade_torque: Var = machine.out_vars[3] if len(machine.out_vars) == 4 else machine.out_vars[4]
        initial_cascade_power: Expr = cascade_torque/Const(cascade_ratio)
        freeze_named_parameter(block,'Pm0Pu_'+controller.name,initial_cascade_power,vf)
        freeze_input(block,block.in_vars[1],vf,Const(named_parameter(record,'R')/named_parameter(record,'PMAX'))*initial_cascade_power)
    elif model in ('HYGOV','HYGOVD','HYGOVDU'):
        hydro_ratio: float = base_ratio if model == 'HYGOV' else (named_parameter(record,'TRATE')/system_base if named_parameter(record,'TRATE') > 0 else base_ratio)
        vf.add_connection(block.in_vars[0],machine.out_vars[2])
        connect_scaled(template.block,machine.in_vars[2],block.out_vars[0],hydro_ratio,vf)
        hydro_torque: Var = machine.out_vars[3] if len(machine.out_vars) == 4 else machine.out_vars[4]
        hydro_gate: Expr = hydro_torque/Const(hydro_ratio*named_parameter(record,'At'))+Const(named_parameter(record,'qNL'))
        freeze_input(block,block.in_vars[1],vf,Const(named_parameter(record,'R'))*hydro_gate)
    elif model == 'HYGOVR1':
        turbine_rating: float = named_parameter(record, 'TRATE')
        turbine_ratio: float = turbine_rating / system_base if turbine_rating > 0.0 else base_ratio
        if turbine_ratio <= 0.0:
            raise ValueError('HYGOVR1 requires a positive machine or turbine power base')
        else:
            pass
        vf.add_connection(block.in_vars[0], machine.out_vars[2])
        connect_scaled(template.block, block.in_vars[2], machine.out_vars[0],
                       1.0 / turbine_ratio, vf)
        connect_scaled(template.block, machine.in_vars[2], block.out_vars[0],
                       turbine_ratio, vf)
        machine_torque: Var = machine.out_vars[3] if len(machine.out_vars) == 4 else machine.out_vars[4]
        initial_power: Expr = machine_torque / Const(turbine_ratio)
        freeze_named_parameter(block, 'Pm0Pu_' + controller.name, initial_power, vf)
        for state in block.state_vars:
            if state.name == 'GeneratorPowerPu_' + controller.name:
                block.init_eqs[state] = machine.out_vars[0] / Const(turbine_ratio)
            else:
                pass
        if named_parameter(record, 'TT') > 0.0:
            feedback_initial: Expr = machine.out_vars[0] / Const(turbine_ratio)
        else:
            feedback_initial = (
                initial_power / named_parameter(record, 'AT')
                + Const(named_parameter(record, 'QNL'))
            )
        freeze_input(
            block, block.in_vars[1], vf,
            Const(named_parameter(record, 'R')) * feedback_initial,
        )
    elif model == 'ST8C':
        if field_initial is None or len(block.in_vars) != 10 or len(machine.out_vars) < 4:
            raise ValueError('ST8C requires a field-dynamic machine and its ten-port interface')
        elif len(block.state_vars) != 5 or len(block.out_vars) != 6:
            raise ValueError('ST8C native state and output contract is inconsistent')
        elif record.icons[0] not in (1, 2) or record.icons[1] not in (1, 2):
            raise ValueError('ST8C OEL/UEL takeover positions 1–2 are the only reviewed paths')
        else:
            pass
        vf.add_connection(machine.in_vars[3], block.out_vars[0])
        vf.add_connection(block.in_vars[0], sensed_voltage)
        vf.add_connection(block.in_vars[5], machine.out_vars[3])
        freeze_input(block, block.in_vars[1], vf, sensed_voltage - stabilizer_bias)
        bind_supplementary_voltage(
            template.block, block, block.in_vars[2], vf, stabilizer, None,
        )
        if overexcitation is None:
            freeze_input(block, block.in_vars[3], vf, Const(0.0))
        else:
            vf.add_connection(block.in_vars[3], overexcitation.out_vars[0])
        if underexcitation is None:
            freeze_input(block, block.in_vars[4], vf, Const(0.0))
        else:
            vf.add_connection(block.in_vars[4], underexcitation.out_vars[0])

        phasors: tuple[Expr, ...] = terminal_phasor_signals(machine, base_ratio)
        for port, signal in zip(block.in_vars[6:10], phasors, strict=True):
            template.block.algebraic_vars.append(port)
            template.block.algebraic_eqs.append(port - signal)
            template.block.init_eqs[port] = signal
            block.init_eqs[port] = signal
        else:
            pass

        field_current0: Expr = machine.out_vars[3]
        feedback0: Expr = field_current0 * Const(named_parameter(record, 'KF'))
        ifd_reference0: Expr = field_current0 + feedback0
        first_channel: Var = block.out_vars[4]
        second_channel: Var = block.out_vars[5]
        bridge_initial: Expr = sym.safe_divide(
            field_initial - second_channel, first_channel, Const(1.0),
        )
        block.init_eqs[block.in_vars[6]] = phasors[0]
        block.init_eqs[block.in_vars[7]] = phasors[1]
        block.init_eqs[block.in_vars[8]] = phasors[2]
        block.init_eqs[block.in_vars[9]] = phasors[3]
        block.init_eqs[block.state_vars[0]] = sensed_voltage
        block.init_eqs[block.state_vars[1]] = ifd_reference0
        block.init_eqs[block.state_vars[2]] = bridge_initial / Const(
            named_parameter(record, 'KA'),
        )
        block.init_eqs[block.state_vars[3]] = bridge_initial
        block.init_eqs[block.state_vars[4]] = feedback0
        block.init_eqs[block.out_vars[1]] = ifd_reference0
        block.init_eqs[block.out_vars[2]] = bridge_initial
    elif model == 'ST10C':
        if field_initial is None or len(block.in_vars) != 11:
            raise ValueError('ST10C requires a field-dynamic machine and its eleven-port interface')
        else:
            pass
        phasors: tuple[Expr, ...] = terminal_phasor_signals(machine, base_ratio)
        vf.add_connection(block.in_vars[0], sensed_voltage)
        block.init_eqs[block.in_vars[0]] = sensed_voltage
        for port, signal in zip(block.in_vars[7:11], phasors, strict=True):
            template.block.algebraic_vars.append(port)
            template.block.algebraic_eqs.append(port - signal)
            template.block.init_eqs[port] = signal
            block.init_eqs[port] = signal
        else:
            pass
        sensed_state: Var | None = next(
            (variable for variable in block.init_eqs
             if variable.name == 'SensedVoltage_' + controller.name),
            None,
        )
        source_supply: Var | None = next(
            (variable for variable in block.algebraic_vars
             if variable.name == 'AvailableFieldSupply_' + controller.name),
            None,
        )
        regulator_gain: Var | None = next(
            (variable for variable in block.event_dict
             if variable.name == 'KR_' + controller.name),
            None,
        )
        if sensed_state is None or source_supply is None or regulator_gain is None:
            raise ValueError('ST10C operating-point symbols are missing')
        else:
            pass
        block.init_eqs[sensed_state] = sensed_voltage
        potential_gain: Var | None = next(
            (variable for variable in block.event_dict
             if variable.name == 'KP_' + controller.name), None,
        )
        loading_gain: Var | None = next(
            (variable for variable in block.event_dict
             if variable.name == 'KC_' + controller.name), None,
        )
        current_gain: Var | None = next(
            (variable for variable in block.event_dict
             if variable.name == 'KI_' + controller.name), None,
        )
        source_reactance: Var | None = next(
            (variable for variable in block.event_dict
             if variable.name == 'XL_' + controller.name), None,
        )
        source_phase: Var | None = next(
            (variable for variable in block.event_dict
             if variable.name == 'THETAP_' + controller.name), None,
        )
        supply_limit: Var | None = next(
            (variable for variable in block.event_dict
             if variable.name == 'VBMAX_' + controller.name), None,
        )
        if (potential_gain is None or loading_gain is None or current_gain is None
                or source_reactance is None or source_phase is None or supply_limit is None):
            raise ValueError('ST10C source parameters are missing')
        else:
            pass
        terminal_voltage_re: Expr = phasors[0]
        terminal_voltage_im: Expr = phasors[1]
        terminal_current_re: Expr = phasors[2]
        terminal_current_im: Expr = phasors[3]
        source_gain_re: Expr = potential_gain * sym.cos(source_phase)
        source_gain_im: Expr = potential_gain * sym.sin(source_phase)
        compound_gain_re: Expr = current_gain + source_gain_re * source_reactance
        compound_gain_im: Expr = source_gain_im * source_reactance
        potential_source_re: Expr = (
            source_gain_re * terminal_voltage_re - source_gain_im * terminal_voltage_im
            - compound_gain_re * terminal_current_im - compound_gain_im * terminal_current_re
        )
        potential_source_im: Expr = (
            source_gain_im * terminal_voltage_re + source_gain_re * terminal_voltage_im
            + compound_gain_re * terminal_current_re - compound_gain_im * terminal_current_im
        )
        potential_source_magnitude: Expr = sym.sqrt(
            potential_source_re * potential_source_re
            + potential_source_im * potential_source_im,
        )
        supply_initial: Expr = sym.min(
            supply_limit,
            potential_source_magnitude * _esst3a_fex(
                sym.safe_divide(
                    loading_gain * machine.out_vars[3], potential_source_magnitude,
                    Const(1.0),
                ),
            ),
        )
        regulator_initial: Expr = field_initial / (supply_initial * regulator_gain)
        block.init_eqs[source_supply] = supply_initial
        block.init_eqs[block.in_vars[1]] = sensed_voltage + regulator_initial
        for state in block.state_vars:
            if state.name == 'AvrFirstLeadLagState_' + controller.name:
                block.init_eqs[state] = regulator_initial
            elif state.name == 'AvrSecondLeadLagState_' + controller.name:
                block.init_eqs[state] = regulator_initial
            elif state.name == 'RegulatorBridgeOutput_' + controller.name:
                block.init_eqs[state] = field_initial / supply_initial
            else:
                pass
        else:
            pass
        command: Var | None = next(
            (variable for variable in block.algebraic_vars
             if variable.name == 'RegulatorCommand_' + controller.name), None,
        )
        if command is None:
            raise ValueError('ST10C regulator command initializer is missing')
        else:
            block.init_eqs[command] = field_initial / supply_initial
        if stabilizer is None:
            freeze_input(block, block.in_vars[2], vf, Const(0.0))
        else:
            vf.add_connection(block.in_vars[2], stabilizer.out_vars[0])
        if underexcitation is None:
            freeze_input(block, block.in_vars[3], vf, Const(0.0))
        else:
            vf.add_connection(block.in_vars[3], underexcitation.out_vars[0])
        if overexcitation is None:
            freeze_input(block, block.in_vars[4], vf, Const(0.0))
        else:
            vf.add_connection(block.in_vars[4], overexcitation.out_vars[0])
        freeze_input(block, block.in_vars[5], vf, Const(0.0))
        vf.add_connection(block.in_vars[6], machine.out_vars[3])
        vf.add_connection(machine.in_vars[3], block.out_vars[0])
    elif model == 'ST9C':
        if field_initial is None or len(block.in_vars) != 11:
            raise ValueError('ST9C requires a field-dynamic machine and its complete eleven-port interface')
        elif underexcitation is not None or overexcitation is not None or overexcitation_record is not None:
            raise ValueError('ST9C limiter takeover ports are not represented by the native exciter template')
        else:
            pass
        # The compound supply uses live rectangular terminal voltage and current.
        phasors: tuple[Expr, ...] = terminal_phasor_signals(machine, base_ratio)
        for port, signal in zip(block.in_vars[:4], phasors, strict=True):
            template.block.algebraic_vars.append(port)
            template.block.algebraic_eqs.append(port - signal)
            template.block.init_eqs[port] = signal
        # PSS remains additive; limiter signal ports stay closed at zero until their gates exist.
        if stabilizer is None:
            freeze_input(block, block.in_vars[5], vf, Const(0.0))
        else:
            vf.add_connection(block.in_vars[5], stabilizer.out_vars[0])
        freeze_input(block, block.in_vars[4], vf, Const(0.0))
        freeze_input(block, block.in_vars[6], vf, Const(0.0))
        freeze_input(block, block.in_vars[7], vf, Const(0.0))
        freeze_input(block, block.in_vars[10], vf, Const(0.0))
        # Track the live sensed voltage and seed the reference at the solved point.
        vf.add_connection(block.in_vars[8], sensed_voltage)
        freeze_input(block, block.in_vars[9], vf, sensed_voltage - stabilizer_bias)
        freeze_named_parameter(block, 'avr.Efd0Pu_' + controller.name, field_initial, vf)
        freeze_named_parameter(block, 'avr.Us0Pu_' + controller.name, sensed_voltage, vf)
        loaded_supply: Var | None = next(
            (variable for variable in block.algebraic_vars
             if variable.name == 'avr.min2.y_' + controller.name),
            None,
        )
        if loaded_supply is None:
            raise ValueError('ST9C loaded source initializer is missing')
        else:
            freeze_named_parameter(block, 'avr.Vb0Pu_' + controller.name, loaded_supply, vf)
        vf.add_connection(machine.in_vars[3], block.out_vars[0])
    elif model in ('EXST1','ESST3A'):
        vf.add_connection(machine.in_vars[3], block.out_vars[0])
        vf.add_connection(block.in_vars[0], machine.out_vars[3])
        vf.add_connection(block.in_vars[1], sensed_voltage)
        if model == 'ESST3A':
            vf.add_connection(block.in_vars[2], machine.out_vars[5])
            vf.add_connection(block.in_vars[3], machine.out_vars[6])
            connect_scaled(template.block, block.in_vars[4], machine.out_vars[7], 1.0/base_ratio, vf)
            connect_scaled(template.block, block.in_vars[5], machine.out_vars[8], 1.0/base_ratio, vf)
            pss: Var = block.in_vars[6]
        else:
            pss = block.in_vars[2]
        bind_supplementary_voltage(template.block,block,pss,vf,stabilizer,underexcitation)
        if underexcitation is not None or stabilizer is not None:
            # Template normalization may already have moved an initialized
            # reference parameter from init_eqs into event_dict.
            for registry in (block.init_eqs,block.event_dict):
                for variable in tuple(registry):
                    if variable.name in ('vref0','vref'):
                        registry[variable] = registry[variable]-stabilizer_bias
                        if underexcitation is not None:
                            registry[variable] = registry[variable]-underexcitation.out_vars[0]
                        else:
                            pass
                    else:
                        pass
        else:
            pass
    elif model in ('EXAC4','ESAC4A','AC4C'):
        if field_initial is None or controller_reference_initial is None:
            raise ValueError('Alternator-fed rectifier field/reference initialization is missing')
        else:
            pass
        vf.add_connection(machine.in_vars[3],block.out_vars[0])
        vf.add_connection(block.in_vars[0],sensed_voltage)
        vf.add_connection(block.in_vars[4],machine.out_vars[3])
        freeze_named_parameter(block,'Efd0Pu_'+controller.name,field_initial,vf)
        freeze_named_parameter(block,'Us0Pu_'+controller.name,sensed_voltage,vf)
        if stabilizer is None:
            freeze_input(block,block.in_vars[2],vf,Const(0.0))
        else:
            vf.add_connection(block.in_vars[2],stabilizer.out_vars[0])
        gated: bool = model == 'ESAC4A' or (model == 'AC4C' and record.icons[1] == 2)
        if model == 'AC4C':
            if record.icons[0] == 2:
                vf.add_connection(block.in_vars[5],block.out_vars[2])
            else:
                freeze_input(block,block.in_vars[5],vf,Const(0.0))
        else:
            pass
        if underexcitation is not None:
            vf.add_connection(block.in_vars[3],underexcitation.out_vars[0])
        elif gated:
            vf.add_connection(block.in_vars[3],block.out_vars[1])
        else:
            freeze_input(block,block.in_vars[3],vf,Const(0.0))
        freeze_input(block,block.in_vars[1],vf,controller_reference_initial-stabilizer_bias
            if gated or underexcitation is None else controller_reference_initial-stabilizer_bias-underexcitation.out_vars[0])
    elif model == 'EXNI':
        if field_initial is None or controller_reference_initial is None:
            raise ValueError('Bidirectional bridge operating-point initialization is missing')
        else:
            pass
        vf.add_connection(machine.in_vars[3],block.out_vars[0])
        vf.add_connection(block.in_vars[0],sensed_voltage)
        vf.add_connection(block.in_vars[4],machine.in_vars[0])
        freeze_named_parameter(block,'Efd0Pu_'+controller.name,field_initial,vf)
        freeze_named_parameter(block,'Us0Pu_'+controller.name,sensed_voltage,vf)
        freeze_named_parameter(block,'Vt0Pu_'+controller.name,machine.in_vars[0],vf)
        freeze_named_parameter(block,'Aux0Pu_'+controller.name,stabilizer_bias if underexcitation is None else stabilizer_bias+underexcitation.out_vars[0],vf)
        bind_supplementary_voltage(template.block,block,block.in_vars[2],vf,stabilizer,None)
        if underexcitation is None:
            freeze_input(block,block.in_vars[3],vf,Const(0.))
        else:
            vf.add_connection(block.in_vars[3],underexcitation.out_vars[0])
        freeze_input(block,block.in_vars[1],vf,controller_reference_initial)
    elif model == 'IEET1B':
        if field_initial is None or controller_reference_initial is None:
            raise ValueError('Biased rotating exciter operating-point initialization is missing')
        else:
            pass
        vf.add_connection(machine.in_vars[3],block.out_vars[0])
        vf.add_connection(block.in_vars[0],sensed_voltage)
        vf.add_connection(block.in_vars[4],machine.in_vars[0])
        magnitude: Expr = sym.sqrt(machine.out_vars[7]**2+machine.out_vars[8]**2)/Const(base_ratio)
        template.block.algebraic_vars.append(block.in_vars[5])
        template.block.algebraic_eqs.append(block.in_vars[5]-magnitude)
        template.block.init_eqs[block.in_vars[5]] = magnitude
        freeze_named_parameter(block,'Efd0Pu_'+controller.name,field_initial,vf)
        freeze_named_parameter(block,'Us0Pu_'+controller.name,sensed_voltage,vf)
        freeze_named_parameter(block,'Imag0Pu_'+controller.name,magnitude,vf)
        freeze_named_parameter(block,'Aux0Pu_'+controller.name,stabilizer_bias if underexcitation is None else stabilizer_bias+underexcitation.out_vars[0],vf)
        bind_supplementary_voltage(template.block,block,block.in_vars[2],vf,stabilizer,None)
        if underexcitation is None:
            freeze_input(block,block.in_vars[3],vf,Const(0.))
        else:
            vf.add_connection(block.in_vars[3],underexcitation.out_vars[0])
        freeze_input(block,block.in_vars[1],vf,controller_reference_initial)
    elif model in ('ST5B','ST5C'):
        if field_initial is None or controller_reference_initial is None:
            raise ValueError('Parallel-channel field/reference initialization is missing')
        else:
            pass
        vf.add_connection(machine.in_vars[3],block.out_vars[0])
        vf.add_connection(block.in_vars[0],sensed_voltage)
        vf.add_connection(block.in_vars[3],machine.out_vars[3])
        vf.add_connection(block.in_vars[4],machine.in_vars[0])
        freeze_named_parameter(block,'Efd0Pu_'+controller.name,field_initial,vf)
        freeze_named_parameter(block,'Ifd0Pu_'+controller.name,machine.out_vars[3],vf)
        freeze_named_parameter(block,'Us0Pu_'+controller.name,sensed_voltage,vf)
        freeze_named_parameter(block,'Vt0Pu_'+controller.name,machine.in_vars[0],vf)
        freeze_named_parameter(block,'Vs0Pu_'+controller.name,stabilizer_bias,vf)
        bind_supplementary_voltage(template.block,block,block.in_vars[2],vf,stabilizer,None)
        if model == 'ST5C' and record.icons[1] == 1:
            freeze_named_parameter(block,'Uel0Pu_'+controller.name,Const(0.) if underexcitation is None else underexcitation.out_vars[0],vf)
            if underexcitation is None:
                freeze_input(block,block.in_vars[5],vf,Const(0.))
            else:
                vf.add_connection(block.in_vars[5],underexcitation.out_vars[0])
        else:
            vf.add_connection(block.in_vars[5],block.out_vars[1] if underexcitation is None else underexcitation.out_vars[0])
        if model == 'ST5C' and record.icons[0] == 1:
            freeze_named_parameter(block,'Oel0Pu_'+controller.name,Const(0.),vf)
            freeze_input(block,block.in_vars[6],vf,Const(0.))
        else:
            vf.add_connection(block.in_vars[6],block.out_vars[2])
        freeze_input(block,block.in_vars[1],vf,controller_reference_initial)
    elif model == 'AC9C':
        if field_initial is None or len(block.in_vars) != 10 or len(machine.out_vars) < 4:
            raise ValueError('AC9C requires a field-dynamic machine and its complete ten-port interface')
        elif underexcitation is not None or overexcitation is not None or overexcitation_record is not None:
            raise ValueError('AC9C external OEL/UEL records need active-limit initialization review')
        else:
            pass
        chopper_selected: bool = named_parameter(record, 'SCT') == 0.0
        vct_voltage: Var | None = next(
            (variable for variable in block.algebraic_vars if variable.name.startswith('VCTPu_')),
            None,
        )
        if chopper_selected and vct_voltage is None:
            raise ValueError('AC9C chopper initialization is missing its terminal-source voltage')
        else:
            pass
        # The machine field output and AC phasors close AC9C's physical source paths.
        vf.add_connection(machine.in_vars[3], block.out_vars[2])
        vf.add_connection(block.in_vars[0], sensed_voltage)
        vf.add_connection(block.in_vars[9], machine.out_vars[3])
        phasors: tuple[Expr, ...] = terminal_phasor_signals(machine, base_ratio)
        for port, signal in zip(block.in_vars[5:9], phasors, strict=True):
            template.block.algebraic_vars.append(port)
            template.block.algebraic_eqs.append(port - signal)
            template.block.init_eqs[port] = signal
        bind_supplementary_voltage(template.block, block, block.in_vars[2], vf, stabilizer, None)
        freeze_input(block, block.in_vars[1], vf, sensed_voltage - stabilizer_bias)
        freeze_input(block, block.in_vars[3], vf, Const(0.0))
        freeze_input(block, block.in_vars[4], vf, Const(0.0))
        block.init_eqs[block.out_vars[2]] = field_initial

        # Invert the source rectifier curve to seed VE from machine EFD and field current.
        loading0: Expr = Const(named_parameter(record, 'KC')) * machine.out_vars[3]
        first_internal: Expr = field_initial + Const(0.577) * loading0
        middle_internal: Expr = sym.sqrt(
            (field_initial * field_initial + loading0 * loading0) / Const(0.75),
        )
        last_internal: Expr = field_initial / Const(1.732) + loading0
        first_region: Expr = sym.heaviside(first_internal - loading0 / Const(0.433))
        second_region: Expr = sym.heaviside(middle_internal - loading0 / Const(0.75))
        internal_initial: Expr = (
            first_region * first_internal
            + (Const(1.0) - first_region) * (
                second_region * middle_internal
                + (Const(1.0) - second_region) * last_internal
            )
        )
        for state in block.state_vars:
            if state.name.startswith('SensedVoltagePu_'):
                block.init_eqs[state] = sensed_voltage
            elif state.name.startswith('PIDIntegratorPu_'):
                block.init_eqs[state] = block.out_vars[4]
            elif state.name.startswith('PIDDerivativeMemoryPu_'):
                block.init_eqs[state] = Const(0.0)
            elif state.name.startswith('CurrentRegulatorIntegratorPu_'):
                if chopper_selected and vct_voltage is not None:
                    block.init_eqs[state] = (
                        block.out_vars[3] - vct_voltage
                    ) / Const(named_parameter(record, 'KA'))
                else:
                    block.init_eqs[state] = (
                        block.out_vars[3] - block.out_vars[7]
                    ) / Const(named_parameter(record, 'KA'))
            elif state.name.startswith('VAPu_'):
                block.init_eqs[state] = block.out_vars[3] - block.out_vars[7]
            elif state.name.startswith('ExciterFieldVoltagePu_'):
                block.init_eqs[state] = internal_initial
            elif state.name.startswith('FilteredFeedbackPu_'):
                block.init_eqs[state] = (
                    block.out_vars[3] * Const(named_parameter(record, 'KF'))
                )
            else:
                raise ValueError('AC9C contains an unreviewed native state')
        else:
            pass
        # Seed source outputs from their own equations so machine phasors and loaded supplies agree at t=0.
        for variable, equation in zip(block.algebraic_vars, block.algebraic_eqs, strict=True):
            block.init_eqs[variable] = equation.right
        if chopper_selected and vct_voltage is not None:
            # Test each threshold region against the VAVR implied by its own VR value.
            regulator_error: Expr = block.out_vars[0] - block.out_vars[4]
            ka: Const = Const(named_parameter(record, 'KA'))
            current_proportional: Expr = (
                Const(named_parameter(record, 'KPA')) * regulator_error
            )
            minimum: Const = Const(named_parameter(record, 'VAMIN'))
            maximum: Const = Const(named_parameter(record, 'VAMAX'))
            upper_vavr: Expr = sym.hard_sat(
                current_proportional + (block.out_vars[3] - vct_voltage) / ka,
                minimum, maximum,
            )
            middle_vavr: Expr = sym.hard_sat(
                current_proportional + block.out_vars[3] / ka, minimum, maximum,
            )
            lower_vavr: Expr = sym.hard_sat(
                current_proportional + (block.out_vars[3] + block.out_vars[5]) / ka,
                minimum, maximum,
            )
            threshold1: Const = Const(named_parameter(record, 'VLIM1'))
            threshold2: Const = Const(named_parameter(record, 'VLIM2'))
            upper_branch: Expr = sym.heaviside(upper_vavr - threshold1)
            middle_branch: Expr = (
                (Const(1.0) - upper_branch)
                * sym.heaviside(middle_vavr - threshold2)
                * (Const(1.0) - sym.heaviside(middle_vavr - threshold1))
            )
            lower_branch: Expr = (
                (Const(1.0) - upper_branch)
                * (Const(1.0) - middle_branch)
                * (Const(1.0) - sym.heaviside(lower_vavr - threshold2))
            )
            chopper_voltage: Expr = (
                upper_branch * vct_voltage
                - lower_branch * block.out_vars[5]
            )
            for state in block.state_vars:
                if state.name.startswith('CurrentRegulatorIntegratorPu_'):
                    block.init_eqs[state] = (
                        block.out_vars[3] - chopper_voltage
                    ) / ka
                else:
                    pass
            block.init_eqs[block.out_vars[7]] = chopper_voltage
        else:
            pass
    elif model == 'AC11C':
        if field_initial is None or controller_reference_initial is None:
            raise ValueError('AC11C field/reference operating-point initialization is missing')
        else:
            pass
        vf.add_connection(machine.in_vars[3], block.out_vars[0])
        phasors: tuple[Expr, ...] = terminal_phasor_signals(machine, base_ratio)
        for index, signal in enumerate(phasors):
            port: Var = block.in_vars[5 + index]
            template.block.algebraic_vars.append(port)
            template.block.algebraic_eqs.append(port - signal)
            template.block.init_eqs[port] = signal
        vf.add_connection(block.in_vars[9], machine.out_vars[3])
        freeze_named_parameter(block, 'Efd0Pu_' + controller.name, field_initial, vf)
        freeze_named_parameter(block, 'Ifd0Pu_' + controller.name, machine.out_vars[3], vf)
        freeze_named_parameter(block, 'Vt0Pu_' + controller.name, machine.in_vars[0], vf)
        kc_parameters: list[Var] = [
            parameter for parameter in block.event_dict
            if parameter.name == 'KC_' + controller.name
        ]
        if len(kc_parameters) != 1:
            raise ValueError('AC11C rectifier coefficient initialization is missing')
        else:
            pass
        loading0: Expr = block.event_dict[kc_parameters[0]] * machine.out_vars[3]
        first_internal: Expr = field_initial + Const(0.577) * loading0
        middle_internal: Expr = sym.sqrt(
            (field_initial * field_initial + loading0 * loading0) / Const(0.75),
        )
        last_internal: Expr = field_initial / Const(1.732) + loading0
        first_region: Expr = sym.heaviside(first_internal - loading0 / Const(0.433))
        second_region: Expr = sym.heaviside(middle_internal - loading0 / Const(0.75))
        internal_initial: Expr = (
            first_region * first_internal
            + (Const(1.0) - first_region) * (
                second_region * middle_internal
                + (Const(1.0) - second_region) * last_internal
            )
        )
        freeze_named_parameter(block, 'Ve0Pu_' + controller.name, internal_initial, vf)
        bind_supplementary_voltage(template.block, block, block.in_vars[1], vf, stabilizer, None)
        if underexcitation is None:
            freeze_input(block, block.in_vars[3], vf, Const(0.0))
        else:
            vf.add_connection(block.in_vars[3], underexcitation.out_vars[0])
        if overexcitation is None:
            freeze_input(block, block.in_vars[2], vf, Const(0.0))
        else:
            vf.add_connection(block.in_vars[2], overexcitation.out_vars[0])
        freeze_input(block, block.in_vars[4], vf, Const(0.0))
        freeze_input(block, block.in_vars[0], vf, controller_reference_initial)
    elif model in ('AC6C','AC6C2'):
        if field_initial is None or controller_reference_initial is None:
            raise ValueError('Two-stage brushless field/reference initialization is missing')
        else:
            pass
        vf.add_connection(machine.in_vars[3],block.out_vars[0])
        vf.add_connection(block.in_vars[0],sensed_voltage)
        vf.add_connection(block.in_vars[3],machine.out_vars[3])
        vf.add_connection(block.in_vars[4],machine.in_vars[0])
        freeze_named_parameter(block,'Efd0Pu_'+controller.name,field_initial,vf)
        freeze_named_parameter(block,'Ifd0Pu_'+controller.name,machine.out_vars[3],vf)
        freeze_named_parameter(block,'Us0Pu_'+controller.name,sensed_voltage,vf)
        freeze_named_parameter(block,'Vt0Pu_'+controller.name,machine.in_vars[0],vf)
        freeze_named_parameter(block,'Vs0Pu_'+controller.name,stabilizer_bias,vf)
        freeze_named_parameter(block,'Uel0Pu_'+controller.name,Const(0.) if underexcitation is None else underexcitation.out_vars[0],vf)
        freeze_named_parameter(block,'Oel0Pu_'+controller.name,Const(0.),vf)
        bind_supplementary_voltage(template.block,block,block.in_vars[2],vf,stabilizer,None)
        if underexcitation is not None:
            vf.add_connection(block.in_vars[5],underexcitation.out_vars[0])
        elif record.icons[1] == 2:
            vf.add_connection(block.in_vars[5],block.out_vars[1])
        else:
            freeze_input(block,block.in_vars[5],vf,Const(0.))
        if record.icons[0] == 2:
            vf.add_connection(block.in_vars[6],block.out_vars[2])
        else:
            freeze_input(block,block.in_vars[6],vf,Const(0.))
        freeze_input(block,block.in_vars[1],vf,controller_reference_initial)
    elif model == 'AC7B':
        if field_initial is None or controller_reference_initial is None:
            raise ValueError('Cascaded brushless field/reference initialization is missing')
        else:
            pass
        vf.add_connection(machine.in_vars[3],block.out_vars[0])
        vf.add_connection(block.in_vars[0],sensed_voltage)
        vf.add_connection(block.in_vars[3],machine.out_vars[3])
        vf.add_connection(block.in_vars[4],machine.in_vars[0])
        freeze_named_parameter(block,'Efd0Pu_'+controller.name,field_initial,vf)
        freeze_named_parameter(block,'Ifd0Pu_'+controller.name,machine.out_vars[3],vf)
        freeze_named_parameter(block,'Us0Pu_'+controller.name,sensed_voltage,vf)
        freeze_named_parameter(block,'Vt0Pu_'+controller.name,machine.in_vars[0],vf)
        freeze_named_parameter(block,'Aux0Pu_'+controller.name,stabilizer_bias if underexcitation is None else stabilizer_bias+underexcitation.out_vars[0],vf)
        bind_supplementary_voltage(template.block,block,block.in_vars[2],vf,stabilizer,None)
        if underexcitation is None:
            freeze_input(block,block.in_vars[5],vf,Const(0.))
        else:
            vf.add_connection(block.in_vars[5],underexcitation.out_vars[0])
        freeze_input(block,block.in_vars[6],vf,Const(0.))
        freeze_input(block,block.in_vars[1],vf,controller_reference_initial)
    elif model == 'AC8B':
        if field_initial is None or controller_reference_initial is None:
            raise ValueError('PID brushless field/reference initialization is missing')
        else:
            pass
        vf.add_connection(machine.in_vars[3],block.out_vars[0])
        vf.add_connection(block.in_vars[0],sensed_voltage)
        vf.add_connection(block.in_vars[3],machine.out_vars[3])
        freeze_named_parameter(block,'Efd0Pu_'+controller.name,field_initial,vf)
        freeze_named_parameter(block,'Ifd0Pu_'+controller.name,machine.out_vars[3],vf)
        freeze_named_parameter(block,'Us0Pu_'+controller.name,sensed_voltage,vf)
        freeze_named_parameter(block,'Aux0Pu_'+controller.name,stabilizer_bias if underexcitation is None else stabilizer_bias+underexcitation.out_vars[0],vf)
        bind_supplementary_voltage(template.block,block,block.in_vars[2],vf,stabilizer,None)
        if underexcitation is None:
            freeze_input(block,block.in_vars[4],vf,Const(0.))
        else:
            vf.add_connection(block.in_vars[4],underexcitation.out_vars[0])
        freeze_input(block,block.in_vars[5],vf,Const(0.))
        freeze_input(block,block.in_vars[1],vf,controller_reference_initial)
    elif model in ('ESST4B','EXPIC1','ST4C','AC8C','ST6C','AC7C'):
        if field_initial is None or controller_reference_initial is None:
            raise ValueError('Compound PI exciter operating-point initialization is missing')
        else:
            pass
        vf.add_connection(machine.in_vars[3],block.out_vars[0])
        vf.add_connection(block.in_vars[0],sensed_voltage)
        vf.add_connection(block.in_vars[7],machine.out_vars[3])
        freeze_named_parameter(block,'Efd0Pu_'+controller.name,field_initial,vf)
        freeze_named_parameter(block,'Us0Pu_'+controller.name,sensed_voltage,vf)
        freeze_named_parameter(block,'Vs0Pu_'+controller.name,stabilizer_bias,vf)
        freeze_named_parameter(block,'Uel0Pu_'+controller.name,Const(0.) if underexcitation is None else underexcitation.out_vars[0],vf)
        phasors: tuple[Expr,...] = terminal_phasor_signals(machine,base_ratio)
        for port,expression in zip(block.in_vars[3:7],phasors):
            template.block.algebraic_vars.append(port)
            template.block.algebraic_eqs.append(port-expression)
            template.block.init_eqs[port] = expression
        bind_supplementary_voltage(template.block,block,block.in_vars[2],vf,stabilizer,None)
        minimum_flag: int = record.icons[1] if model in ('AC8C','ST6C','AC7C') else record.icons[2] if model == 'ST4C' else 1
        if underexcitation is None and model in ('ST4C','AC8C','ST6C','AC7C') and minimum_flag in ((2,4) if model == 'ST6C' else (2,3)):
            vf.add_connection(block.in_vars[8],block.out_vars[1 if minimum_flag == 2 else 3])
        elif underexcitation is None:
            freeze_input(block,block.in_vars[8],vf,Const(0.))
        else:
            vf.add_connection(block.in_vars[8],underexcitation.out_vars[0])
        if model in ('ST4C','AC8C','ST6C','AC7C'):
            if model in ('AC8C','ST6C','AC7C'):
                freeze_named_parameter(block,'Ifd0Pu_'+controller.name,machine.out_vars[3],vf)
            else:
                pass
            maximum_flag: int = record.icons[0] if model in ('AC8C','ST6C','AC7C') else record.icons[1]
            freeze_named_parameter(block,'Oel0Pu_'+controller.name,Const(0.),vf)
            if maximum_flag in ((1,3) if model == 'ST6C' else (1,)):
                freeze_input(block,block.in_vars[9],vf,Const(0.))
            else:
                vf.add_connection(block.in_vars[9],block.out_vars[2 if maximum_flag == 2 else 5 if model == 'AC7C' and maximum_flag == 4 else 4])
        elif model == 'ESST4B':
            vf.add_connection(block.in_vars[9],block.out_vars[1])
        else:
            pass
        freeze_input(block,block.in_vars[1],vf,controller_reference_initial)
    elif model in ('ST7B','ST7C'):
        if field_initial is None or controller_reference_initial is None:
            raise ValueError('Self-feedback exciter operating-point initialization is missing')
        else:
            pass
        vf.add_connection(machine.in_vars[3],block.out_vars[0])
        vf.add_connection(block.in_vars[0],sensed_voltage)
        vf.add_connection(block.in_vars[4],machine.in_vars[0])
        freeze_named_parameter(block,'Efd0Pu_'+controller.name,field_initial,vf)
        freeze_named_parameter(block,'Us0Pu_'+controller.name,sensed_voltage,vf)
        freeze_named_parameter(block,'Vs0Pu_'+controller.name,stabilizer_bias,vf)
        freeze_named_parameter(block,'Uel0Pu_'+controller.name,Const(0.) if underexcitation is None else underexcitation.out_vars[0],vf)
        freeze_named_parameter(block,'Oel0Pu_'+controller.name,Const(0.),vf)
        bind_supplementary_voltage(template.block,block,block.in_vars[2],vf,stabilizer,None)
        if underexcitation is not None:
            vf.add_connection(block.in_vars[3],underexcitation.out_vars[0])
            if (model == 'ST7C' and len(underexcitation.in_vars) == 6
                    and underexcitation.in_vars[2].name.startswith('uel_VFbPu_')):
                vf.add_connection(underexcitation.in_vars[2],block.out_vars[5])
                freeze_named_parameter(underexcitation,
                    'uel_UsRef0Pu_'+underexcitation.name,block.out_vars[5],vf)
            else:
                pass
        elif record.icons[1] == 1:
            freeze_input(block,block.in_vars[3],vf,Const(0.))
        else:
            vf.add_connection(block.in_vars[3],block.out_vars[2 if record.icons[1] == 2 else 4])
        if record.icons[0] == 1:
            freeze_input(block,block.in_vars[5],vf,Const(0.))
        else:
            vf.add_connection(block.in_vars[5],block.out_vars[1 if record.icons[0] == 2 else 3])
        freeze_input(block,block.in_vars[1],vf,controller_reference_initial)
    elif model in ('ESST1A','ST1C'):
        if field_initial is None or controller_reference_initial is None:
            raise ValueError('Terminal-fed static exciter initialization is missing')
        else:
            pass
        vf.add_connection(machine.in_vars[3],block.out_vars[0])
        vf.add_connection(block.in_vars[0],sensed_voltage)
        vf.add_connection(block.in_vars[4],machine.in_vars[0])
        vf.add_connection(block.in_vars[5],machine.out_vars[3])
        freeze_named_parameter(block,'Efd0Pu_'+controller.name,field_initial,vf)
        freeze_named_parameter(block,'Us0Pu_'+controller.name,sensed_voltage,vf)
        freeze_named_parameter(block,'Ifd0Pu_'+controller.name,machine.out_vars[3],vf)
        freeze_named_parameter(block,'Vs0Pu_'+controller.name,stabilizer_bias,vf)
        freeze_named_parameter(block,'Uel0Pu_'+controller.name,Const(0.) if underexcitation is None else underexcitation.out_vars[0],vf)
        bind_supplementary_voltage(template.block,block,block.in_vars[2],vf,stabilizer,None)
        if underexcitation is not None:
            vf.add_connection(block.in_vars[3],underexcitation.out_vars[0])
        elif record.icons[0] == 1:
            freeze_input(block,block.in_vars[3],vf,Const(0.))
        else:
            vf.add_connection(block.in_vars[3],block.out_vars[1 if record.icons[0] == 2 else 2])
        if model == 'ST1C':
            freeze_named_parameter(block,'Oel0Pu_'+controller.name,Const(0.),vf)
            if record.icons[2] == 1:
                freeze_input(block,block.in_vars[6],vf,Const(0.))
            else:
                vf.add_connection(block.in_vars[6],block.out_vars[4 if record.icons[2] == 2 else 3])
        else:
            vf.add_connection(block.in_vars[6],block.out_vars[3])
        freeze_input(block,block.in_vars[1],vf,controller_reference_initial)
    elif model == 'BBSEX1':
        if field_initial is None or controller_reference_initial is None:
            raise ValueError('Static feedback exciter operating-point initialization is missing')
        else:
            pass
        vf.add_connection(machine.in_vars[3],block.out_vars[0])
        vf.add_connection(block.in_vars[0],sensed_voltage)
        vf.add_connection(block.in_vars[4],machine.in_vars[0])
        freeze_named_parameter(block,'Efd0Pu_'+controller.name,field_initial,vf)
        freeze_named_parameter(block,'Us0Pu_'+controller.name,sensed_voltage,vf)
        bind_supplementary_voltage(template.block,block,block.in_vars[2],vf,stabilizer,None)
        if underexcitation is None:
            freeze_input(block,block.in_vars[3],vf,Const(0.))
        else:
            vf.add_connection(block.in_vars[3],underexcitation.out_vars[0])
        auxiliary_initial: Expr = stabilizer_bias if underexcitation is None else stabilizer_bias+underexcitation.out_vars[0]
        freeze_named_parameter(block,'Aux0Pu_'+controller.name,auxiliary_initial,vf)
        freeze_input(block,block.in_vars[1],vf,controller_reference_initial)
    elif model == 'DC4C':
        if field_initial is None or controller_reference_initial is None:
            raise ValueError('Compound commutator field/reference initialization is missing')
        else:
            pass
        vf.add_connection(machine.in_vars[3],block.out_vars[0])
        vf.add_connection(block.in_vars[0],sensed_voltage)
        freeze_named_parameter(block,'Efd0Pu_'+controller.name,field_initial,vf)
        freeze_named_parameter(block,'Us0Pu_'+controller.name,sensed_voltage,vf)
        compound_phasors: tuple[Expr,...] = terminal_phasor_signals(machine,base_ratio)
        for port,expression in zip(block.in_vars[3:7],compound_phasors):
            template.block.algebraic_vars.append(port)
            template.block.algebraic_eqs.append(port-expression)
            template.block.init_eqs[port] = expression
        bind_supplementary_voltage(template.block,block,block.in_vars[2],vf,stabilizer,None)
        if underexcitation is not None:
            vf.add_connection(block.in_vars[7],underexcitation.out_vars[0])
        elif record.icons[1] == 2:
            vf.add_connection(block.in_vars[7],block.out_vars[1])
        else:
            freeze_input(block,block.in_vars[7],vf,Const(0.))
        if record.icons[0] == 2:
            vf.add_connection(block.in_vars[8],block.out_vars[2])
        else:
            freeze_input(block,block.in_vars[8],vf,Const(0.))
        freeze_input(block,block.in_vars[1],vf,controller_reference_initial-stabilizer_bias-
            (underexcitation.out_vars[0] if underexcitation is not None and record.icons[1] == 1 else Const(0.)))
    elif dc_kind is not None or electromechanical_kind is not None or model in ('ESAC8B','BUDCZT','DC4B'):
        if field_initial is None or controller_reference_initial is None:
            raise ValueError('Rotating exciter operating-point initialization is missing')
        else:
            pass
        vf.add_connection(machine.in_vars[3],block.out_vars[0])
        vf.add_connection(block.in_vars[0],sensed_voltage)
        vf.add_connection(block.in_vars[4],machine.in_vars[0])
        freeze_named_parameter(block,'Efd0Pu_'+controller.name,field_initial,vf)
        freeze_named_parameter(block,'Us0Pu_'+controller.name,sensed_voltage,vf)
        if stabilizer is None:
            freeze_input(block,block.in_vars[2],vf,sym.Const(0.0))
        else:
            vf.add_connection(block.in_vars[2],stabilizer.out_vars[0])
        if model == 'DC4B':
            freeze_named_parameter(block,'Vt0Pu_'+controller.name,machine.in_vars[0],vf)
        else:
            pass
        bounded_rotating_host: bool = model == 'DC4B' or dc_kind in (DcExciterKind.BOUNDED_FIXED_SUPPLY,DcExciterKind.BOUNDED_TERMINAL_SUPPLY)
        gated: bool = dc_kind in (DcExciterKind.DC1A,DcExciterKind.DC2A) or (bounded_rotating_host and record.icons[1] == 2)
        if underexcitation is not None:
            vf.add_connection(block.in_vars[3],underexcitation.out_vars[0])
        elif gated:
            # max(demand,demand) bypasses an absent limiter at every time step.
            vf.add_connection(block.in_vars[3],block.out_vars[1])
        else:
            freeze_input(block,block.in_vars[3],vf,sym.Const(0.0))
        if bounded_rotating_host:
            if record.icons[0] == 2:
                vf.add_connection(block.in_vars[5],block.out_vars[2])
            else:
                freeze_input(block,block.in_vars[5],vf,Const(0.))
        else:
            pass
        freeze_input(block,block.in_vars[1],vf,controller_reference_initial-stabilizer_bias
            if gated or underexcitation is None else controller_reference_initial-stabilizer_bias-underexcitation.out_vars[0])
    elif model in ('EXST2','EXST2A','ESST2A','IEEET3','IEEEX3'):
        if field_initial is None or controller_reference_initial is None:
            raise ValueError('Static exciter field/reference initialization is missing')
        else:
            pass
        vf.add_connection(machine.in_vars[3],block.out_vars[0])
        vf.add_connection(block.in_vars[0],sensed_voltage)
        vf.add_connection(block.in_vars[7],machine.out_vars[3])
        freeze_named_parameter(block,'Efd0Pu_'+controller.name,field_initial,vf)
        expressions: tuple[Expr,...] = terminal_phasor_signals(machine,base_ratio)
        for port,expression in zip(block.in_vars[3:7],expressions):
            template.block.algebraic_vars.append(port)
            template.block.algebraic_eqs.append(port-expression)
            template.block.init_eqs[port] = expression
        if model == 'ESST2A':
            bind_supplementary_voltage(template.block,block,block.in_vars[2],vf,stabilizer,None)
            if underexcitation is None:
                vf.add_connection(block.in_vars[8],block.out_vars[1])
            else:
                vf.add_connection(block.in_vars[8],underexcitation.out_vars[0])
            freeze_input(block,block.in_vars[1],vf,controller_reference_initial-stabilizer_bias)
        else:
            bind_supplementary_voltage(template.block,block,block.in_vars[2],vf,stabilizer,underexcitation)
            freeze_input(block,block.in_vars[1],vf,controller_reference_initial-stabilizer_bias if underexcitation is None
                else controller_reference_initial-stabilizer_bias-underexcitation.out_vars[0])
    elif model == 'SCRX':
        if field_initial is None:
            raise ValueError('Static-exciter field initialization is missing')
        else:
            pass
        vf.add_connection(machine.in_vars[3],block.out_vars[0])
        vf.add_connection(block.in_vars[0],machine.out_vars[3])
        vf.add_connection(block.in_vars[4],sensed_voltage)
        vf.add_connection(block.in_vars[6],machine.in_vars[0])
        freeze_input(block,block.in_vars[1],vf,sym.Const(0.0))
        if stabilizer is None:
            freeze_input(block,block.in_vars[2],vf,sym.Const(0.0))
        else:
            vf.add_connection(block.in_vars[2],stabilizer.out_vars[0])
        if underexcitation is None:
            freeze_input(block,block.in_vars[5],vf,sym.Const(0.0))
        else:
            vf.add_connection(block.in_vars[5],underexcitation.out_vars[0])
        freeze_named_parameter(block,'avr_Efd0Pu_'+controller.name,field_initial,vf)
        freeze_named_parameter(block,'avr_UStator0Pu_'+controller.name,sensed_voltage,vf)
        freeze_named_parameter(block,'avr_Ut0Pu_'+controller.name,machine.in_vars[0],vf)
        freeze_named_parameter(block,'avr_IRotor0Pu_'+controller.name,machine.out_vars[3],vf)
        reference: Var = next(var for var in block.event_dict if var.name == 'avr_URef0Pu_'+controller.name)
        freeze_input(block,block.in_vars[3],vf,block.event_dict[reference]-stabilizer_bias if underexcitation is None
            else block.event_dict[reference]-stabilizer_bias-underexcitation.out_vars[0])
    elif model == 'SEXS':
        if field_initial is None:
            raise ValueError('Machine field initialization is missing')
        else:
            pass
        vf.add_connection(machine.in_vars[3],block.out_vars[0])
        vf.add_connection(block.in_vars[1],sensed_voltage)
        bind_supplementary_voltage(template.block,block,block.in_vars[0],vf,stabilizer,underexcitation)
        freeze_named_parameter(block,'Efd0Pu_'+controller.name,field_initial,vf)
        freeze_named_parameter(block,'Us0Pu_'+controller.name,sensed_voltage,vf)
        reference_initial: Expr = block.event_dict[next(var for var in block.event_dict if var.name == 'UsRef0Pu_'+controller.name)]
        freeze_input(block,block.in_vars[2],vf,reference_initial-stabilizer_bias if underexcitation is None
            else reference_initial-stabilizer_bias-underexcitation.out_vars[0])
    elif model in ('EXAC1','EXAC1A','ESAC1A','EXAC2','EXAC3','ESAC2A','ESAC3A','EXBAS','AC1C','AC2C','AC5C'):
        if field_initial is None:
            raise ValueError('Machine field initialization is missing')
        else:
            pass
        set_rms_model_parameter(block,'avr_ULow_'+controller.name,math.sqrt(3.0)/4.0,vf)
        vf.add_connection(machine.in_vars[3],block.out_vars[0])
        vf.add_connection(block.in_vars[0],machine.out_vars[3])
        vf.add_connection(block.in_vars[3],sensed_voltage)
        if model in ('ESAC1A','ESAC2A') or model in ('AC1C','AC2C','AC5C') and record.icons[0] == 2:
            vf.add_connection(block.in_vars[1],block.out_vars[2])
        else:
            freeze_input(block,block.in_vars[1],vf,sym.Const(0.0))
        if stabilizer is None:
            freeze_input(block,block.in_vars[2],vf,sym.Const(0.0))
        else:
            vf.add_connection(block.in_vars[2],stabilizer.out_vars[0])
        if underexcitation is None:
            if model in ('ESAC1A','ESAC2A','ESAC3A') or model in ('AC1C','AC2C','AC5C') and record.icons[1] == 2:
                vf.add_connection(block.in_vars[5],block.out_vars[1])
            else:
                freeze_input(block,block.in_vars[5],vf,sym.Const(0.0))
        else:
            vf.add_connection(block.in_vars[5],underexcitation.out_vars[0])
        freeze_named_parameter(block,'avr_Efd0Pu_'+controller.name,field_initial,vf)
        freeze_named_parameter(block,'avr_Us0Pu_'+controller.name,sensed_voltage,vf)
        freeze_named_parameter(block,'avr_Ir0Pu_'+controller.name,machine.out_vars[3],vf)
        # The template derives its reference from Efd0/Ir0 and saturation data.
        reference: Var = next(var for var in block.event_dict if var.name == 'avr_UsRef0Pu_'+controller.name)
        freeze_input(block,block.in_vars[4],vf,block.event_dict[reference]-stabilizer_bias if underexcitation is None or model in ('ESAC1A','ESAC2A','ESAC3A') or model in ('AC1C','AC2C','AC5C') and record.icons[1] == 2
            else block.event_dict[reference]-stabilizer_bias-underexcitation.out_vars[0])
    else:
        raise ValueError('No reviewed native signal connection for '+model)
    template.block.children.append(block)


def terminal_phasor_signals(machine: Block, base_ratio: float) -> tuple[Expr,...]:
    """Expose terminal voltage and machine-base current without dividing by voltage.

    :param machine: Machine with rotor-frame stator-current outputs.
    :param base_ratio: Machine MVA divided by system MVA.
    :return: Rectangular voltage/current signals in Vr,Vi,Ir,Ii order.
    """
    rotor: Block = machine.children[0] if machine.children else machine
    angle: Var = rotor.state_vars[0]
    voltage: Var = machine.in_vars[0]
    terminal_angle: Var = machine.in_vars[1]
    current_d: Var = machine.out_vars[7]
    current_q: Var = machine.out_vars[8]
    return (voltage*sym.cos(terminal_angle),voltage*sym.sin(terminal_angle),
        (current_d*sym.sin(angle)+current_q*sym.cos(angle))/sym.Const(base_ratio),
        (-current_d*sym.cos(angle)+current_q*sym.sin(angle))/sym.Const(base_ratio))


def add_terminal_current_signals(template: RmsModelTemplate, machine: Block,
                                 vf: VarFactory, key: tuple[int, str]) -> None:
    """Expose outgoing terminal current on a generator's system-base RMS block.

    :param template: Native generator model receiving the algebraic current signals.
    :param machine: Network-facing machine with voltage and P/Q ports.
    :param vf: Circuit symbol factory owning both signals.
    :param key: Exact PSS/E bus and machine identity used to name the signals.
    :return: None.
    """
    voltage: Expr = machine.in_vars[0] * sym.exp(Const(1j) * machine.in_vars[1])
    current: Expr = sym.conj((machine.out_vars[0] + Const(1j) * machine.out_vars[1]) / voltage)
    current_real: Var = vf.add_var('PsseTerminalCurrentRealPu_' + str(key[0]) + '_' + key[1])
    current_imag: Var = vf.add_var('PsseTerminalCurrentImagPu_' + str(key[0]) + '_' + key[1])
    real_expression: Expr = current_real - sym.real(current)
    imag_expression: Expr = current_imag - sym.imag(current)
    template.block.algebraic_vars.extend((current_real, current_imag))
    template.block.algebraic_eqs.extend((real_expression, imag_expression))
    template.block.init_eqs[current_real] = sym.real(current)
    template.block.init_eqs[current_imag] = sym.imag(current)


def _find_child_block(root: Block, name: str) -> Block | None:
    """Resolve one direct dynamic child by its deterministic source name.

    :param root: Composite generator model root.
    :param name: Exact child block name.
    :return: Unique child or None when absent/ambiguous.
    """
    matches: list[Block] = [child for child in root.children if child.name == name]
    if len(matches) == 1:
        return matches[0]
    else:
        return None


def _find_terminal_current(root: Block, key: tuple[int, str], imaginary: bool) -> Var | None:
    """Resolve one generator-owned terminal-current algebraic variable.

    :param root: Native generator model root.
    :param key: Exact PSS/E bus and machine identity.
    :param imaginary: Select reactive-axis current when true, real-axis current otherwise.
    :return: Current signal or None when absent/ambiguous.
    """
    axis: str = 'Imag' if imaginary else 'Real'
    expected_name: str = 'PsseTerminalCurrent' + axis + 'Pu_' + str(key[0]) + '_' + key[1]
    matches: list[Var] = [variable for variable in root.algebraic_vars if variable.name == expected_name]
    if len(matches) == 1:
        return matches[0]
    else:
        return None


def attach_compensator(context: PsseAuxiliaryConverter, template: RmsModelTemplate,
                        machine: Block, controller: RmsModelTemplate, record: DyrRecord,
                        base_ratio: float) -> Block:
    """Connect local phasor or remote voltage sensing without changing the network.

    :param context: Native bus lookup and source conversion diagnostics.
    :param template: Complete host machine assembly.
    :param machine: Network-facing generator block with P/Q output ports.
    :param controller: Fresh native voltage-measurement component.
    :param record: Checked source voltage-compensation assignment.
    :param base_ratio: Machine MVA divided by system MVA.
    :return: Connected component whose output feeds the exciter measurement.
    :raises ValueError: Missing or invalid remote bus reference.
    """
    block: Block = controller.block
    vf: VarFactory = context.grid.var_factory
    for port in block.in_vars:
        block.init_eqs.pop(port,None)
    if dynamic_record_name(record) in ('CCOMP4A', 'CCOMP4U1'):
        if len(record.icons) != 6:
            raise ValueError('CCOMP4A requires three complete linked bus and machine identities')
        else:
            pass
        linked_keys: tuple[tuple[int, str], ...] = tuple(
            (int(record.icons[index]), str(record.icons[index + 1]).strip())
            for index in (0, 2, 4)
        )
        host_key: tuple[int, str] = (int(record.identifier), (record.equipment_id or '1').strip())
        machine_keys: tuple[tuple[int, str], ...] = (host_key,) + linked_keys
        host_raw: RawGeneratorLike | None = context.raw_generators.get(host_key, None)
        if len(set(machine_keys)) != 4:
            raise ValueError('CCOMP4A requires four distinct generator identities')
        elif host_raw is None or host_raw.RT != 0.0 or host_raw.XT != 0.0:
            raise ValueError('CCOMP4A requires zero host GSU impedance')
        else:
            pass
        if _find_terminal_current(template.block, host_key, True) is None:
            raise ValueError('CCOMP4A host terminal-current signal is missing')
        else:
            host_current: Var | None = _find_terminal_current(template.block, host_key, True)
            if host_current is None:
                raise ValueError('CCOMP4A host terminal-current signal disappeared')
            else:
                host_input: Var = vf.add_var(
                    'CCOMP4AIqPu_' + str(host_key[0]) + '_' + host_key[1] + '_Unit1'
                )
                template.block.algebraic_vars.append(host_input)
                template.block.algebraic_eqs.append(host_input - host_current / Const(base_ratio))
                template.block.init_eqs[host_input] = host_current / Const(base_ratio)
                vf.add_connection(block.in_vars[1], host_input)
        for key in linked_keys:
            linked: Generator | None = context.generators.get(key, None)
            linked_raw: RawGeneratorLike | None = context.raw_generators.get(key, None)
            if (linked is None or linked_raw is None or linked_raw.MBASE <= 0.0
                    or linked_raw.RT != 0.0 or linked_raw.XT != 0.0
                    or linked.rms_template is None or not linked.rms_template.block.children):
                raise ValueError('CCOMP4A linked generators require exact identities, zero GSU impedance and active DYR machine templates')
            else:
                if _find_terminal_current(linked.rms_template.block, key, True) is None:
                    raise ValueError('CCOMP4A linked terminal-current signal is missing')
                else:
                    pass
            current_input: Var = vf.add_var(
                'CCOMP4AIqPu_' + str(host_key[0]) + '_' + host_key[1] + '_Unit' + str(linked_keys.index(key) + 2)
            )
            template.block.algebraic_vars.append(current_input)
            current_signal: Var | None = _find_terminal_current(linked.rms_template.block, key, True)
            if current_signal is None:
                raise ValueError('CCOMP4A linked terminal-current signal disappeared')
            else:
                template.block.algebraic_eqs.append(current_input - current_signal / Const(base_ratio))
                template.block.init_eqs[current_input] = current_signal / Const(base_ratio)
                vf.add_connection(block.in_vars[linked_keys.index(key) + 2], current_input)
        vf.add_connection(block.in_vars[0], machine.in_vars[0])
    elif record.model.upper() == 'COMPCC':
        if len(record.icons) != 1:
            raise ValueError('COMPCC requires the second machine identifier')
        else:
            pass
        host_bus: int | None = context.bus_number(record.bus)
        host_key: tuple[int, str] | None = (
            (host_bus, (record.equipment_id or '1').strip()) if host_bus is not None else None
        )
        linked_key: tuple[int, str] | None = (
            (host_bus, str(record.icons[0]).strip()) if host_bus is not None else None
        )
        if host_key is None or linked_key is None or host_key == linked_key:
            raise ValueError('COMPCC requires a distinct second machine at the same bus')
        else:
            linked: Generator | None = context.generators.get(linked_key, None)
            if linked is None or linked.rms_template is None or not linked.rms_template.block.children:
                raise ValueError('COMPCC requires an already-built second machine at the host bus')
            else:
                linked_machine: Block = linked.rms_template.block.children[0]
        host_real_current: Var | None = _find_terminal_current(template.block, host_key, False)
        host_imag_current: Var | None = _find_terminal_current(template.block, host_key, True)
        peer_real_current: Var | None = _find_terminal_current(linked.rms_template.block, linked_key, False)
        peer_imag_current: Var | None = _find_terminal_current(linked.rms_template.block, linked_key, True)
        if (host_real_current is None or host_imag_current is None
                or peer_real_current is None or peer_imag_current is None):
            raise ValueError('COMPCC requires live current signals on both machine templates')
        else:
            voltage: Expr = machine.in_vars[0] * sym.exp(Const(1j) * machine.in_vars[1])
            voltage_real_port: Var = block.in_vars[0]
            voltage_imag_port: Var = block.in_vars[1]
            template.block.algebraic_vars.extend((voltage_real_port, voltage_imag_port))
            template.block.algebraic_eqs.extend((
                voltage_real_port - sym.real(voltage), voltage_imag_port - sym.imag(voltage),
            ))
            template.block.init_eqs[voltage_real_port] = sym.real(voltage)
            template.block.init_eqs[voltage_imag_port] = sym.imag(voltage)
        peer_exciters: list[DyrRecord] = list()
        for document in context.source.dyr_files:
            for candidate in document.records:
                candidate_binding: PsseDynamicBinding | None = dynamic_binding(dynamic_record_name(candidate))
                if (context.bus_number(candidate.bus) == host_bus
                        and (candidate.equipment_id or '1').strip() == linked_key[1]
                        and candidate_binding is not None
                        and candidate_binding.role == PsseDynamicRole.EXCITER):
                    peer_exciters.append(candidate)
                else:
                    pass
        if len(peer_exciters) != 1 or dynamic_record_name(peer_exciters[0]) != 'SEXS':
            raise ValueError('COMPCC currently requires one explicit SEXS exciter on the second machine')
        else:
            peer_exciter_name: str = linked.rms_template.name + '_SEXS'
            peer_exciter_blocks: list[Block] = [
                child for child in linked.rms_template.block.children if child.name == peer_exciter_name
            ]
            if len(peer_exciter_blocks) != 1:
                raise ValueError('COMPCC second-machine SEXS block is missing or ambiguous')
            else:
                peer_exciter: Block = peer_exciter_blocks[0]
            peer_voltage_initials: list[Var] = [variable for variable in peer_exciter.event_dict
                if variable.name == 'Us0Pu_' + peer_exciter.name]
            if len(peer_voltage_initials) != 1 or len(peer_exciter.in_vars) < 2:
                raise ValueError('COMPCC second-machine SEXS voltage initializer is missing or ambiguous')
            else:
                pass
    elif record.model.upper() == 'REMCMP':
        remote_number: float = named_parameter(record,'JBUS')
        if remote_number <= 0 or not remote_number.is_integer():
            raise ValueError('Remote sensing requires a positive integer bus number')
        else:
            remote_bus: Bus | None = context.buses.get(int(remote_number),None)
            if remote_bus is None or remote_bus.is_dc:
                raise ValueError('Remote sensing requires an existing native AC bus')
            else:
                if remote_bus.rms_model.empty():
                    initialize_bus_rms(remote_bus,vf)
                else:
                    pass
                remote_voltage: Var | None = remote_bus.rms_model.external_mapping.get(VarPowerFlowReferenceType.Vm,None)
                if remote_voltage is None:
                    raise ValueError('Remote sensing bus has no polar RMS voltage mapping')
                else:
                    vf.add_network_connection(block.in_vars[0],remote_voltage)
    else:
        expressions: tuple[Expr,...] = terminal_phasor_signals(machine,base_ratio)
        for port,expression in zip(block.in_vars,expressions):
            template.block.algebraic_vars.append(port)
            template.block.algebraic_eqs.append(port-expression)
            template.block.init_eqs[port] = expression
    template.block.children.append(block)
    return block


def wire_cross_machine_compensators(context: PsseAuxiliaryConverter) -> None:
    """Connect deferred cross-machine signals after all device runtime copies exist.

    :param context: Shared network, exact machine lookups and dynamic source documents.
    :return: None.
    """
    vf: VarFactory = context.grid.var_factory
    for document in context.source.dyr_files:
        for record in document.records:
            model: str = dynamic_record_name(record)
            host_bus: int | None = context.bus_number(record.bus)
            host_key: tuple[int, str] | None = (
                (host_bus, (record.equipment_id or '1').strip()) if host_bus is not None else None
            )
            was_converted: bool = False
            for entry in context.entries:
                if (entry.source == document.source and entry.line == record.line_number
                        and entry.file_type == PsseFileType.DYR
                        and entry.status == PsseConversionStatus.CONVERTED):
                    was_converted = True
                else:
                    pass
            if was_converted and model in ('CCOMP4A', 'CCOMP4U1') and host_key is not None and len(record.icons) == 6:
                host: Generator | None = context.generators.get(host_key, None)
                linked_keys: tuple[tuple[int, str], ...] = tuple(
                    (int(record.icons[index]), str(record.icons[index + 1]).strip())
                    for index in (0, 2, 4)
                )
                if host is None or host.rms_template is None or not host.rms_model.children:
                    raise ValueError('CCOMP4A host runtime assembly is unavailable for cross-machine wiring')
                else:
                    host_template: RmsModelTemplate = host.rms_template
                    host_runtime: Block = host.rms_model
                    host_compensator: Block | None = _find_child_block(
                        host_template.block, host_template.name + '_CCOMP4A'
                    )
                    runtime_compensator: Block | None = _find_child_block(
                        host_runtime, host_template.name + '_CCOMP4A'
                    )
                    if host_compensator is None or runtime_compensator is None:
                        raise ValueError('CCOMP4A template/runtime component pairing is incomplete')
                    else:
                        pass
                    host_ratio: float = context.raw_generators[host_key].MBASE / context.grid.Sbase
                    for unit_index, linked_key in enumerate((host_key,) + linked_keys):
                        linked: Generator | None = context.generators.get(linked_key, None)
                        if linked is None or linked.rms_template is None or not linked.rms_model.children:
                            raise ValueError('CCOMP4A linked runtime generator is unavailable')
                        else:
                            pass
                        template_input: Var = host_compensator.in_vars[unit_index + 1]
                        wrapper_name: str = (
                            'CCOMP4AIqPu_' + str(host_key[0]) + '_' + host_key[1]
                            + '_Unit' + str(unit_index + 1)
                        )
                        template_wrapper: list[Var] = [
                            variable for variable in host_template.block.algebraic_vars
                            if variable.name == wrapper_name
                        ]
                        runtime_wrapper: list[Var] = [
                            variable for variable in host_runtime.algebraic_vars
                            if variable.name == wrapper_name
                        ]
                        template_current: Var | None = _find_terminal_current(
                            linked.rms_template.block, linked_key, True
                        )
                        runtime_current: Var | None = _find_terminal_current(
                            linked.rms_model, linked_key, True
                        )
                        if (len(template_wrapper) != 1 or len(runtime_wrapper) != 1
                                or template_current is None or runtime_current is None):
                            raise ValueError('CCOMP4A terminal-current cross-link is missing or ambiguous')
                        else:
                            vf.add_connection(template_input, template_wrapper[0])
                            runtime_input: Var = runtime_compensator.in_vars[unit_index + 1]
                            vf.add_connection(runtime_input, runtime_wrapper[0])
                            equation_index: int | None = None
                            for variable_index, variable in enumerate(host_runtime.algebraic_vars):
                                if variable.non_mutable_uid == runtime_wrapper[0].non_mutable_uid:
                                    equation_index = variable_index
                                else:
                                    pass
                            if equation_index is None or equation_index >= len(host_runtime.algebraic_eqs):
                                raise ValueError('CCOMP4A runtime current-base equation cannot be located')
                            else:
                                expression: Expr = runtime_current / Const(host_ratio)
                                host_runtime.algebraic_eqs[equation_index] = runtime_wrapper[0] - expression
                                host_runtime.init_eqs[runtime_wrapper[0]] = expression
            elif was_converted and model == 'COMPCC' and host_key is not None and len(record.icons) == 1:
                host: Generator | None = context.generators.get(host_key, None)
                linked_key: tuple[int, str] = (host_key[0], str(record.icons[0]).strip())
                linked: Generator | None = context.generators.get(linked_key, None)
                if (host is None or linked is None or host.rms_template is None or linked.rms_template is None
                        or not host.rms_model.children or not linked.rms_model.children):
                    raise ValueError('COMPCC paired runtime assemblies are unavailable')
                else:
                    pass
                host_template: RmsModelTemplate = host.rms_template
                linked_template: RmsModelTemplate = linked.rms_template
                template_compensator: Block | None = _find_child_block(
                    host_template.block, host_template.name + '_COMPCC'
                )
                runtime_compensator: Block | None = _find_child_block(
                    host.rms_model, host_template.name + '_COMPCC'
                )
                template_peer_exciter: Block | None = _find_child_block(
                    linked_template.block, linked_template.name + '_SEXS'
                )
                runtime_peer_exciter: Block | None = _find_child_block(
                    linked.rms_model, linked_template.name + '_SEXS'
                )
                if (template_compensator is None or runtime_compensator is None
                        or template_peer_exciter is None or runtime_peer_exciter is None):
                    raise ValueError('COMPCC compensator or peer SEXS block is missing')
                else:
                    pass
                template_host_real: Var | None = _find_terminal_current(host_template.block, host_key, False)
                template_host_imag: Var | None = _find_terminal_current(host_template.block, host_key, True)
                template_peer_real: Var | None = _find_terminal_current(linked_template.block, linked_key, False)
                template_peer_imag: Var | None = _find_terminal_current(linked_template.block, linked_key, True)
                runtime_host_real: Var | None = _find_terminal_current(host.rms_model, host_key, False)
                runtime_host_imag: Var | None = _find_terminal_current(host.rms_model, host_key, True)
                runtime_peer_real: Var | None = _find_terminal_current(linked.rms_model, linked_key, False)
                runtime_peer_imag: Var | None = _find_terminal_current(linked.rms_model, linked_key, True)
                current_signals: tuple[Var | None, ...] = (
                    template_host_real, template_host_imag, template_peer_real, template_peer_imag,
                    runtime_host_real, runtime_host_imag, runtime_peer_real, runtime_peer_imag,
                )
                if any(signal is None for signal in current_signals):
                    raise ValueError('COMPCC terminal-current cross-link is missing')
                else:
                    template_signals: tuple[Var, ...] = (
                        template_host_real, template_host_imag, template_peer_real, template_peer_imag,
                    )
                    runtime_signals: tuple[Var, ...] = (
                        runtime_host_real, runtime_host_imag, runtime_peer_real, runtime_peer_imag,
                    )
                    for index, signal in enumerate(template_signals):
                        vf.add_connection(template_compensator.in_vars[index + 2], signal)
                    else:
                        pass
                    for index, signal in enumerate(runtime_signals):
                        vf.add_connection(runtime_compensator.in_vars[index + 2], signal)
                    else:
                        pass
                    template_peer_machine: Block = linked_template.block.children[0]
                    runtime_peer_machine: Block = linked.rms_model.children[0]
                    vf.remove_connection(template_peer_exciter.in_vars[1], template_peer_machine.in_vars[0])
                    vf.add_connection(template_peer_exciter.in_vars[1], template_compensator.out_vars[1])
                    vf.remove_connection(runtime_peer_exciter.in_vars[1], runtime_peer_machine.in_vars[0])
                    vf.add_connection(runtime_peer_exciter.in_vars[1], runtime_compensator.out_vars[1])
                    for exciter, source_output in (
                            (template_peer_exciter, template_compensator.out_vars[1]),
                            (runtime_peer_exciter, runtime_compensator.out_vars[1])):
                        sensed_parameters: list[Var] = [variable for variable in exciter.event_dict
                            if variable.name == 'Us0Pu_' + exciter.name]
                        reference_parameters: list[Var] = [variable for variable in exciter.event_dict
                            if variable.name == 'UsRef0Pu_' + exciter.name]
                        if len(sensed_parameters) != 1 or len(reference_parameters) != 1:
                            raise ValueError('COMPCC second-machine SEXS reference initialization is missing or ambiguous')
                        else:
                            reference: Expr | Const | None = exciter.event_dict.get(reference_parameters[0], None)
                            if not isinstance(reference, Expr):
                                raise ValueError('COMPCC second-machine SEXS reference is not symbolic')
                            else:
                                exciter.event_dict[reference_parameters[0]] = reference.subs(
                                    {sensed_parameters[0]: source_output}
                                )
            else:
                pass


def attach_underexcitation(template: RmsModelTemplate, machine: Block, controller: RmsModelTemplate,
                            record: DyrRecord, vf: VarFactory, base_ratio: float) -> Block:
    """Connect capability and field signals to a native minimum-excitation controller.

    :param template: Complete host machine assembly.
    :param machine: Network-facing machine with rotor-frame current outputs.
    :param controller: Fresh native minimum-excitation controller.
    :param record: Source assignment selecting the capability characteristic.
    :param base_ratio: Machine MVA divided by system MVA.
    :return: Connected limiter whose output feeds the exciter summation.
    """
    block: Block = controller.block
    for port in block.in_vars:
        block.init_eqs.pop(port,None)
    if record.model.upper() == 'UEL1':
        phasors: tuple[Expr,...] = terminal_phasor_signals(machine,base_ratio)
        signals: tuple[Expr,...] = phasors + (machine.out_vars[3],Const(0.0))
    elif record.model.upper() == 'UEL2C':
        if base_ratio <= 0.0:
            raise ValueError('UEL2C requires a positive machine/system MVA ratio')
        else:
            pass
        phasors: tuple[Expr,...] = terminal_phasor_signals(machine,base_ratio)
        signals = (machine.out_vars[0]/Const(base_ratio),machine.out_vars[1]/Const(base_ratio),
                   Const(0.0),machine.in_vars[0],phasors[1],phasors[0])
    elif record.model.upper() == 'MNLEX2':
        signals: tuple[Expr,...] = (machine.out_vars[0]/sym.Const(base_ratio),
            machine.out_vars[1]/sym.Const(base_ratio),machine.in_vars[0])
    else:
        rotor: Block = machine.children[0] if machine.children else machine
        angle: Expr = rotor.state_vars[0]-machine.in_vars[1]
        # Rotate live stator currents, rather than divide P/Q by a possibly
        # collapsed voltage during a fault. Both currents use machine MVA base.
        active: Expr = (machine.out_vars[7]*sym.sin(angle)+machine.out_vars[8]*sym.cos(angle))/sym.Const(base_ratio)
        reactive: Expr = (machine.out_vars[7]*sym.cos(angle)-machine.out_vars[8]*sym.sin(angle))/sym.Const(base_ratio)
        signals = (active,machine.out_vars[3],machine.in_vars[3]) if record.model.upper() == 'MNLEX1' else (active,reactive,machine.in_vars[3])
    for index, (port,signal) in enumerate(zip(block.in_vars,signals)):
        if record.model.upper() == 'UEL2C' and index == 2:
            pass
        else:
            template.block.algebraic_vars.append(port)
            template.block.algebraic_eqs.append(port-signal)
            template.block.init_eqs[port] = signal
    if record.model.upper() == 'UEL2C':
        voltage_bias_parameters: list[Var] = [
            variable for variable in block.event_dict
            if variable.name == 'uel_VBiasPu_'+block.name
        ]
        if len(voltage_bias_parameters) != 1:
            raise ValueError('UEL2C voltage-bias parameter is not unique')
        else:
            pass
        voltage_bias_parameter: Var = voltage_bias_parameters[0]
        voltage_high: Expr = sym.heaviside(signals[3]-Const(1.0)-Const(1e-6))
        voltage_above_bias: Expr = sym.heaviside(
            signals[3]-voltage_bias_parameter-Const(1e-6))
        voltage_bias_signal: Expr = (
            voltage_high*signals[3]
            + (Const(1.0)-voltage_high)
            * (voltage_above_bias+(Const(1.0)-voltage_above_bias)
               * (signals[3]/voltage_bias_parameter))
        )
        freeze_named_parameter(block,'uel_PGen0Pu_'+block.name,signals[0],vf)
        freeze_named_parameter(block,'uel_QGen0Pu_'+block.name,signals[1],vf)
        freeze_named_parameter(block,'uel_U0Pu_'+block.name,signals[3],vf)
        freeze_named_parameter(block,'uel_QRef0Pu_'+block.name,signals[1],vf)
        freeze_named_parameter(block,'uel_VBias0Pu_'+block.name,voltage_bias_signal,vf)
        for variable in block.algebraic_vars:
            if variable.name == 'uel_multiSwitch1_y_'+block.name:
                block.init_eqs[variable] = voltage_bias_signal
            else:
                pass
        for parameter in block.event_dict:
            if parameter.name == 'uel_firstOrder_k_'+block.name:
                block.event_dict[parameter] = signals[3]
            elif parameter.name == 'uel_firstOrder3_k_'+block.name:
                block.event_dict[parameter] = signals[1]
            elif parameter.name == 'uel_firstOrder4_k_'+block.name:
                block.event_dict[parameter] = block.event_dict[
                    next(variable for variable in block.event_dict
                         if variable.name == 'uel_KFb_'+block.name)
                ] * block.in_vars[2]
            else:
                pass
    else:
        pass
    if record.model.upper() == 'UEL1':
        parameters: dict[str,Var] = dict(
            (variable.name.split('_')[0],variable)
            for variable in block.event_dict
        )
        terminal_voltage_re: Var = block.in_vars[0]
        terminal_voltage_im: Var = block.in_vars[1]
        terminal_current_re: Var = block.in_vars[2]
        terminal_current_im: Var = block.in_vars[3]
        field_voltage: Var = block.in_vars[4]
        radius: Expr = parameters['KUR'] * sym.sqrt(
            terminal_current_re * terminal_current_re
            + terminal_current_im * terminal_current_im
        )
        center_re: Expr = parameters['KUC'] * terminal_voltage_re + terminal_current_im
        center_im: Expr = parameters['KUC'] * terminal_voltage_im - terminal_current_re
        center: Expr = sym.sqrt(center_re * center_re + center_im * center_im)
        error: Expr = (
            sym.hard_sat(center,Const(0.0),parameters['VUCMAX'])
            - sym.hard_sat(radius,Const(0.0),parameters['VURMAX'])
            - parameters['KUF'] * field_voltage
        )
        block.init_eqs[block.algebraic_vars[2]] = error
        integrator: Var = block.state_vars[0]
        integrator_initial: Expr = sym.hard_sat(
            Const(0.0),
            parameters['VUIMIN'],parameters['VUIMAX'],
        )
        pi_initial: Expr = sym.hard_sat(
            parameters['KUL'] * error + integrator_initial,
            parameters['VUIMIN'],parameters['VUIMAX'],
        )
        block.init_eqs[integrator] = integrator_initial
        if len(block.state_vars) > 1:
            block.init_eqs[block.state_vars[1]] = pi_initial
        else:
            pass
        if len(block.state_vars) > 2:
            block.init_eqs[block.state_vars[2]] = pi_initial
        else:
            pass
    else:
        pass
    template.block.children.append(block)
    return block


def stabilizer_measurement(context: PsseAuxiliaryConverter, machine: Block,
                             selection: PsseStabilizerInput, remote: int | str,
                             base_ratio: float) -> Expr:
    """Resolve one reviewed stabilizer measurement without changing its physical base.

    :param context: Native bus lookup and shared symbol factory.
    :param machine: Network-facing host machine.
    :param selection: Explicit source input selector.
    :param remote: Zero for the terminal or a positive remote bus number.
    :param base_ratio: Machine MVA divided by system MVA.
    :return: Live measurement expression or explicit remote network variable.
    :raises ValueError: Unsupported measurement or missing native AC bus mapping.
    """
    if selection == PsseStabilizerInput.BLOCKED:
        return Const(0.0)
    elif selection == PsseStabilizerInput.ROTOR_SPEED:
        return machine.out_vars[2]-Const(1.0)
    elif selection == PsseStabilizerInput.ELECTRICAL_POWER:
        return machine.out_vars[0]/Const(base_ratio)
    elif selection == PsseStabilizerInput.BUS_VOLTAGE and remote == 0:
        return machine.in_vars[0]
    elif selection == PsseStabilizerInput.BUS_VOLTAGE and isinstance(remote, int):
        remote_bus: Bus | None = context.buses.get(remote, None)
        if remote_bus is None or remote_bus.is_dc:
            raise ValueError('Stabilizer remote voltage requires an existing native AC bus')
        else:
            if remote_bus.rms_model.empty():
                initialize_bus_rms(remote_bus, context.grid.var_factory)
            else:
                pass
            remote_voltage: Var | None = remote_bus.rms_model.external_mapping.get(VarPowerFlowReferenceType.Vm, None)
            if remote_voltage is None:
                raise ValueError('Stabilizer remote bus has no polar RMS voltage mapping')
            else:
                return remote_voltage
    else:
        raise ValueError('Stabilizer input measurement has no reviewed native realization')


def attach_stabilizer(context: PsseAuxiliaryConverter, template: RmsModelTemplate, machine: Block, controller: RmsModelTemplate,
                       record: DyrRecord, vf: VarFactory, base_ratio: float,
                       compensator: Block | None) -> Block:
    """Connect a supplementary-voltage controller to live machine measurements.

    :param context: Native bus lookup for explicitly selected remote voltage sensing.
    :param template: Complete host generator assembly.
    :param machine: Network-facing synchronous machine block.
    :param controller: Fresh native stabilizer instance.
    :param record: Source record determining the measured signal.
    :param vf: Shared circuit symbol factory.
    :param base_ratio: Machine MVA divided by system MVA.
    :param compensator: Reviewed compensated-voltage measurement used by supervision.
    :return: Connected block consumed by the exciter attachment.
    """
    block: Block = controller.block
    for port in block.in_vars:
        block.init_eqs.pop(port,None)
    if record.model.upper() == 'BEPSST':
        if len(block.in_vars) != 4 or len(machine.out_vars) < 3 or len(machine.in_vars) < 1:
            raise ValueError('BEPSST requires two measured signals and terminal-voltage host signals')
        else:
            pass
        for signal_index in (0, 1):
            selector_index: int = 2 * signal_index
            selection: PsseStabilizerInput = PsseStabilizerInput(record.icons[selector_index])
            remote: int | str = record.icons[selector_index + 1]
            signal: Expr = stabilizer_measurement(context, machine, selection, remote, base_ratio)
            port: Var = block.in_vars[signal_index]
            if remote != 0 and isinstance(signal, Var):
                vf.add_network_connection(port, signal)
            else:
                template.block.algebraic_vars.append(port)
                template.block.algebraic_eqs.append(port - signal)
                template.block.init_eqs[port] = signal
        terminal_port: Var = block.in_vars[2]
        template.block.algebraic_vars.append(terminal_port)
        template.block.algebraic_eqs.append(terminal_port - machine.in_vars[0])
        template.block.init_eqs[terminal_port] = machine.in_vars[0]
        freeze_input(block, block.in_vars[3], vf, machine.in_vars[0])
    elif record.model.upper() in ('OSTB2T', 'OSTB5T'):
        if len(block.in_vars) != 3 or len(machine.out_vars) < 3 or len(machine.in_vars) < 4:
            raise ValueError('Ontario Hydro stabilizers require speed, terminal-voltage and field-voltage host signals')
        else:
            pass
        signals: tuple[Expr, Expr, Expr] = (
            machine.out_vars[2] - Const(1.0), machine.in_vars[0], machine.in_vars[3],
        )
        for port, signal in zip(block.in_vars, signals, strict=True):
            template.block.algebraic_vars.append(port)
            template.block.algebraic_eqs.append(port - signal)
            template.block.init_eqs[port] = signal
    elif record.model.upper() == 'PSS4B':
        if len(block.in_vars) != 2 or len(machine.out_vars) < 3:
            raise ValueError('PSS4B requires speed-deviation and electrical-power host signals')
        else:
            pass
        signals: tuple[Expr, Expr] = (
            machine.out_vars[2] - Const(1.0), machine.out_vars[0],
        )
        for port, signal in zip(block.in_vars, signals, strict=True):
            template.block.algebraic_vars.append(port)
            template.block.algebraic_eqs.append(port - signal)
            template.block.init_eqs[port] = signal
    elif record.model.upper() in ('IEEEST', 'IEE2ST', 'PSS2A', 'PSS2B', 'PSS2C', 'PSS3B', 'PSS7C') or dynamic_record_name(record) == 'PSS7C':
        for index in range(1 if record.model.upper() == 'IEEEST' else 2):
            selection: PsseStabilizerInput = PsseStabilizerInput(record.icons[2*index])
            remote: int | str = record.icons[2*index+1]
            signal: Expr = stabilizer_measurement(context, machine, selection, remote, base_ratio)
            if remote != 0 and isinstance(signal, Var):
                vf.add_network_connection(block.in_vars[index], signal)
            else:
                template.block.algebraic_vars.append(block.in_vars[index])
                template.block.algebraic_eqs.append(block.in_vars[index]-signal)
                template.block.init_eqs[block.in_vars[index]] = signal
        if (record.model.upper() in ('PSS2C', 'PSS7C') or dynamic_record_name(record) == 'PSS7C') and len(block.in_vars) == 3:
            power_signal: Expr = machine.out_vars[0] / Const(base_ratio)
            template.block.algebraic_vars.append(block.in_vars[2])
            template.block.algebraic_eqs.append(block.in_vars[2] - power_signal)
            template.block.init_eqs[block.in_vars[2]] = power_signal
        else:
            pass
        # The application guide defines VCT as compensated voltage, independently
        # of where the stabilizer's selected input signal is measured.
        if record.model.upper() in ('IEEEST','IEE2ST'):
            voltage_port: Var = block.in_vars[-1]
            supervisory_voltage: Var = machine.in_vars[0] if compensator is None else compensator.out_vars[0]
            template.block.algebraic_vars.append(voltage_port)
            template.block.algebraic_eqs.append(voltage_port-supervisory_voltage)
            template.block.init_eqs[voltage_port] = supervisory_voltage
        else:
            pass
    elif record.model.upper() == 'PSS6C':
        if len(block.in_vars) != 7:
            raise ValueError('PSS6C native interface must expose seven signal ports')
        else:
            pass
        power_machine_pu: Expr = machine.out_vars[0] / Const(base_ratio)
        signals: tuple[Expr, ...] = (
            power_machine_pu, machine.out_vars[2] - Const(1.0), Const(1.0), Const(0.0),
            machine.in_vars[0], Const(0.0), Const(0.0),
        )
        for port, signal in zip(block.in_vars, signals):
            block.init_eqs.pop(port, None)
            template.block.algebraic_vars.append(port)
            template.block.algebraic_eqs.append(port - signal)
            template.block.init_eqs[port] = signal
        freeze_named_parameter(block, 'pss_PGen0Pu_' + controller.name, power_machine_pu, vf)
        pss_variables: dict[str, Var] = dict(
            (variable.name, variable)
            for variable in block.state_vars + block.algebraic_vars + list(block.event_dict)
        )
        first_transducer: Var = pss_variables['pss_firstOrder_y_' + controller.name]
        first_limiter: Var = pss_variables['pss_limiter_y_' + controller.name]
        first_gain_stage: Var = pss_variables['pss_firstOrder1_y_' + controller.name]
        first_gain: Var = pss_variables['pss_Ks1_' + controller.name]
        second_transducer: Var = pss_variables['pss_firstOrder2_y_' + controller.name]
        second_limiter: Var = pss_variables['pss_limiter1_y_' + controller.name]
        second_gain: Var = pss_variables['pss_Ks2_' + controller.name]
        derivative_memory: Var = pss_variables['pss_derivative_x_' + controller.name]
        block.init_eqs[first_transducer] = first_limiter
        block.init_eqs[first_gain_stage] = first_transducer * first_gain
        block.init_eqs[second_transducer] = second_limiter * second_gain
        block.init_eqs[derivative_memory] = second_transducer
    elif record.model.upper() == 'IVOST':
        # The source diagram consumes PELEC directly, without a machine-base conversion.
        vf.add_connection(block.in_vars[0],machine.out_vars[0])
        freeze_named_parameter(block,'InitialElectricalPowerPu_'+controller.name,machine.out_vars[0],vf)
    elif record.model.upper() == 'STAB1':
        vf.add_connection(block.in_vars[0],machine.out_vars[2])
    else:
        connect_scaled(template.block,block.in_vars[0],machine.out_vars[0],1.0/base_ratio,vf)
        if len(block.in_vars) == 2:
            freeze_input(block,block.in_vars[1],vf,machine.out_vars[0]/sym.Const(base_ratio))
        else:
            pass
    template.block.children.append(block)
    return block


def validate_dynamic_parameters(record: DyrRecord) -> None:
    """Reject physical domains or template structural variants that cannot run exactly.

    :param record: Parsed numeric source record.
    :raises ValueError: Unsupported domain/structural variant.
    """
    model: str = dynamic_record_name(record)
    binding: PsseDynamicBinding | None = dynamic_binding(model)
    positive: tuple[str, ...] = ()
    if model in ('BEPSST', 'IEEEST', 'IEE2ST', 'PSS2A', 'PSS2B', 'PSS2C', 'PSS3B', 'PSS7C'):
        expected_icons: int = (
            5 if model == 'BEPSST' else
            (2 if model == 'IEEEST' else (4 if model in ('IEE2ST','PSS3B') else 6))
        )
        if model == 'PSS7C':
            expected_icons = 6
        else:
            pass
        if len(record.icons) != expected_icons:
            raise ValueError('Stabilizer has an incorrect integer signal-selection header')
        else:
            pass
        for index in range(0, 2 if model == 'IEEEST' else 4, 2):
            selection: PsseStabilizerInput = PsseStabilizerInput(record.icons[index])
            if selection == PsseStabilizerInput.BLOCKED and model != 'IEE2ST':
                raise ValueError('Only the dual-input stabilizer documents a disabled input selector')
            elif model == 'PSS7C' and selection not in (PsseStabilizerInput.ROTOR_SPEED,
                    PsseStabilizerInput.ELECTRICAL_POWER, PsseStabilizerInput.BUS_VOLTAGE):
                raise ValueError('PSS7C currently supports local/remote speed, machine power or bus-voltage selectors only')
            elif selection not in (PsseStabilizerInput.BLOCKED, PsseStabilizerInput.ROTOR_SPEED, PsseStabilizerInput.ELECTRICAL_POWER,
                                 PsseStabilizerInput.BUS_VOLTAGE):
                raise ValueError('Stabilizer frequency, accelerating-power and voltage-derivative measurements remain unreviewed')
            elif record.icons[index+1] != 0 and selection != PsseStabilizerInput.BUS_VOLTAGE:
                raise ValueError('Remote bus is not allowed for this stabilizer input')
            else:
                pass
        if model == 'BEPSST' and record.icons[4] != 0:
            raise ValueError('BEPSST TEB trip input remains unrepresented; ITS must be zero')
        else:
            pass
        if model == 'BEPSST':
            constants: tuple[str, ...] = (
                'T1','T2','T3','T4','T5','T6','T7','T8','T9','T10',
            )
            if (any(named_parameter(record, parameter_name) < 0.0 for parameter_name in constants)
                    or named_parameter(record, 'T4') <= 0.0
                    or any(named_parameter(record, numerator) != 0.0
                           and named_parameter(record, denominator) == 0.0
                           for numerator, denominator in (('T5','T6'),('T7','T8'),('T9','T10')))
                    or named_parameter(record, 'LSMIN') > named_parameter(record, 'LSMAX')
                    or (named_parameter(record, 'VCU') != 0.0
                        and named_parameter(record, 'VCL') != 0.0
                        and named_parameter(record, 'VCL') >= named_parameter(record, 'VCU'))):
                raise ValueError('BEPSST source constants violate the represented PSS path domains')
            else:
                pass
    elif model == 'PSS6C':
        if (len(record.icons) != 4 or record.icons[0] not in (1, 3)
                or record.icons[2] not in (1, 3) or record.icons[1] != 0 or record.icons[3] != 0):
            raise ValueError('PSS6C currently supports local rotor-speed or machine-power inputs only')
        else:
            pass
    elif model in ('OSTB2T', 'OSTB5T'):
        if model == 'OSTB5T' and (named_parameter(record, 'T4') <= 0.0
                or named_parameter(record, 'T3_T4') <= 0.0
                or named_parameter(record, 'T1') < 0.0 or named_parameter(record, 'T2') < 0.0):
            raise ValueError('OSTB5T source lead-lag constants violate their documented domains')
        else:
            pass
        if (named_parameter(record, 'TS') <= 0.0
                or (model == 'OSTB2T' and (named_parameter(record, 'T3') <= 0.0
                or named_parameter(record, 'T4') <= 0.0 or named_parameter(record, 'KANG') <= 0.0
                ))
                or (model == 'OSTB5T' and named_parameter(record, 'KANG') <= 0.0)
                or named_parameter(record, 'TANG') < 0.0 or named_parameter(record, 'TSEAL') < 0.0
                or named_parameter(record, 'T_ON') < 0.0
                or named_parameter(record, 'T_OFF') < named_parameter(record, 'T_ON')
                or named_parameter(record, 'LLIM') > named_parameter(record, 'HLIM')
                or named_parameter(record, 'VSMN') > named_parameter(record, 'VSMX')
                or min(named_parameter(record, 'VNGMX'), named_parameter(record, 'VMGMX')) < 0.0):
            raise ValueError('Ontario Hydro stabilizer parameters violate filter, switching or limiter domains')
        else:
            pass
    elif model == 'WTTQA1':
        if len(record.icons) != 1 or record.icons[0] not in (0, 1):
            raise ValueError('WTTQA1 TFLAG must select speed error or power error')
        else:
            pass
    elif model in ('IVOST','IVOGO'):
        for stage_index in (1,3,5):
            if named_parameter(record,'A'+str(stage_index+1)) == 0 and named_parameter(record,'A'+str(stage_index)) == 0:
                raise ValueError('Source zero-origin rational-stage cancellation requires a reviewed initialization convention')
            elif named_parameter(record,'A'+str(stage_index+1)) == 0 and named_parameter(record,'K'+str(stage_index)) == 0:
                raise ValueError('Source zero-gain free-integral initialization requires separate review')
            elif stage_index != 5 and named_parameter(record,'A'+str(stage_index+1)) == 0 and named_parameter(record,'T'+str(stage_index)) > 0:
                raise ValueError('Source bounded PI degeneration requires a reviewed anti-windup convention')
            else:
                pass
    elif model == 'DC4C':
        positive = ('KPR','KA','TA','TE','VBMAX')
        if len(record.icons) != 4 or any(flag not in (1,2) for flag in record.icons):
            raise ValueError('Compound commutator selectors must each be one or two')
        else:
            pass
    elif model in ('AC4C','DC4B'):
        if len(record.icons) != 2 or any(flag not in (1,2) for flag in record.icons):
            raise ValueError('Exciter OEL/UEL selectors must each be one or two')
        else:
            pass
    elif model == 'OEL2C':
        if len(record.icons) != 2 or record.icons[0] not in (1, 2, 3) or record.icons[1] not in (1, 2):
            raise ValueError('OEL2C INPUT must select Efd, Ifd, or VFE and SW1 must select fixed or inverse rate')
        else:
            pass
    elif model == 'UEL2C':
        if (len(record.icons) != 4 or record.icons[0] not in (0, 1, 2)
                or record.icons[1] not in (0, 1, 2)
                or record.icons[2] not in (0, 1)
                or record.icons[3] not in (1, 2)):
            raise ValueError('UEL2C exponent, third-quadrant and gain-reduction selectors are invalid')
        elif named_parameter(record,'XQ') <= 0.0:
            raise ValueError('UEL2C requires positive generator q-axis reactance XQ')
        elif any(named_parameter(record,name) <= 0.0 for name in
                 ('TUV','TUP','TUQ','TUL','TU1','TU2','TU3','TU4','TADJ','TQREF')):
            raise ValueError('UEL2C zero filter and lead-lag times are unsupported by the current native realization')
        elif named_parameter(record,'VBIAS') == 0.0:
            raise ValueError('UEL2C zero VBIAS makes the source voltage-bias division undefined')
        else:
            previous_power: float | None = None
            active_pairs: int = 0
            terminated: bool = False
            for index in range(11):
                power: float = named_parameter(record,'P'+str(index))
                reactive_power: float = named_parameter(record,'Q'+str(index))
                if power == 0.0:
                    if reactive_power != 0.0 or active_pairs < 2:
                        raise ValueError('UEL2C P-Q characteristic needs two points and a zero terminator pair')
                    else:
                        terminated = True
                elif terminated:
                    raise ValueError('UEL2C P-Q pairs after the zero terminator must be zero')
                elif previous_power is not None and power <= previous_power:
                    raise ValueError('UEL2C P-Q characteristic active-power points must increase')
                else:
                    active_pairs += 1
                    previous_power = power
            if active_pairs < 2:
                raise ValueError('UEL2C P-Q characteristic requires at least two active points')
            else:
                pass
    elif model == 'DERA1':
        if len(record.icons) != 6 or any(flag not in (0, 1) for flag in record.icons):
            raise ValueError('DERA1 requires six binary selector flags')
        elif named_parameter(record, 'TG') <= 0.0:
            raise ValueError('DERA1 requires positive Tg')
        elif named_parameter(record, 'DPMAX') <= 0.0 or named_parameter(record, 'DPMIN') >= 0.0:
            raise ValueError('DERA1 active-power ramp limits must straddle zero')
        elif named_parameter(record, 'PMIN') > named_parameter(record, 'PMAX'):
            raise ValueError('DERA1 active-power limits are reversed')
        elif named_parameter(record, 'VL0') > named_parameter(record, 'VL1'):
            raise ValueError('DERA1 low-voltage thresholds are reversed')
        elif named_parameter(record, 'VH1') > named_parameter(record, 'VH0'):
            raise ValueError('DERA1 high-voltage thresholds are reversed')
        elif not 0.0 <= named_parameter(record, 'VRFRAC') <= 1.0:
            raise ValueError('DERA1 Vrfrac must be in [0, 1]')
        else:
            pass
    elif model == 'GENCLS':
        if named_parameter(record,'H') < 0:
            raise ValueError('Classical machine inertia cannot be negative')
        else:
            pass
    elif model in ('GENROU','GENROE'):
        positive = ('H','Tdo1','Tdo2','Tqo1','Tqo2','Xd','Xq','Xd1','Xq1','Xd2')
    elif model in ('GENSAL','GENSAE'):
        positive = ('H','Tdo1','Tdo2','Tqo2','Xd','Xq','Xd1','Xd2')
    elif model == 'GENTRA':
        positive = ('H','Tdo1','Xd','Xq','Xd1')
        if named_parameter(record,'AF') <= 0:
            raise ValueError('Source network-iteration acceleration factor must be positive')
        else:
            pass
    elif model in ('GGOV1','GGOV1D','GGOV1DU'):
        if len(record.icons) != 2 or record.icons[0] not in (-2,-1,0,1) or record.icons[1] not in (0,1):
            raise ValueError('Unreviewed fuel-governor droop or fuel-characteristic selector')
        elif named_parameter(record,'TENG') != 0 or named_parameter(record,'KA') != 0:
            raise ValueError('Fuel transport delay and time-step acceleration limiting need dedicated native realizations')
        elif named_parameter(record,'KPLOAD') <= 0 or named_parameter(record,'TFLOAD') <= 0 or named_parameter(record,'KILOAD') < 0:
            raise ValueError('Reviewed fuel-load limiting requires positive P gain and measurement time, with nonnegative I gain')
        elif named_parameter(record,'TRATE') < 0 or named_parameter(record,'ASET') < 0 or named_parameter(record,'TA') < 0:
            raise ValueError('Fuel-governor rating and disabled acceleration settings must be nonnegative')
        elif named_parameter(record,'RUP') <= 0 or named_parameter(record,'RDOWN') >= 0:
            raise ValueError('Source load-limit slew bounds must straddle zero even when the limiter is inactive')
        else:
            pass
    elif model in ('DEGOV','DEGOV1','DEGOV1D','DEGOV1DU'):
        positive = ('T1','T2','K','T5','T6','TD')
        if model != 'DEGOV' and (len(record.icons) != 1 or record.icons[0] not in (0,1)):
            raise ValueError('Engine governor droop control must select throttle or electrical power')
        elif min(named_parameter(record,'T3'),named_parameter(record,'T4')) < 0 or named_parameter(record,'TMAX') <= named_parameter(record,'TMIN'):
            raise ValueError('Engine governor requires nonnegative numerator times and ordered throttle limits')
        elif model in ('DEGOV1D','DEGOV1DU') and (named_parameter(record,'TRATE') < 0 or named_parameter(record,'DBH') < 0 or named_parameter(record,'DBL') > 0):
            raise ValueError('Engine governor rating/deadband signs are invalid')
        elif model != 'DEGOV' and min(named_parameter(record,'DROOP'),named_parameter(record,'TE')) < 0:
            raise ValueError('Engine governor droop and power measurement time must be nonnegative')
        else:
            pass
    elif model == 'LCFB1':
        if len(record.icons) != 2 or record.icons[0] not in (0,1) or record.icons[1] != 1:
            raise ValueError('Reviewed outer load control requires power control enabled and a binary frequency-bias flag')
        else:
            pass
    elif model in ('IEEEG1','IEEEG1D','IEEEG1SDU'):
        single_shaft_header: bool = record.icons == () if model == 'IEEEG1SDU' else len(record.icons) == 2 and record.icons[0] == 0
        if not single_shaft_header or any(named_parameter(record,'K'+str(index)) != 0 for index in (2,4,6,8)):
            raise ValueError('Cross-compound steam governor targets and second-shaft fractions require a reviewed multi-machine assembly')
        elif model in ('IEEEG1D','IEEEG1SDU') and named_parameter(record,'TRATE') < 0:
            raise ValueError('Steam turbine rating must be nonnegative; zero selects machine MBASE')
        else:
            pass
    elif model in ('IEEEG3D','IEEEG3DU'):
        if named_parameter(record,'TRATE') < 0:
            raise ValueError('Hydraulic turbine rating must be nonnegative; zero selects the machine base')
        else:
            pass
    elif model in ('TGOV1','TGOV1D','TGOV1DU'):
        positive = ('R','T1','T3')
    elif model == 'TGOV2':
        positive = ('R','T1','T3','TT')
        if named_parameter(record,'VMIN') >= named_parameter(record,'VMAX'):
            raise ValueError('TGOV2 throttle limits must be ordered')
        elif not 0.0 <= named_parameter(record,'K') <= 1.0:
            raise ValueError('TGOV2 direct turbine fraction must lie in [0, 1]')
        elif not (0.0 < named_parameter(record,'TA') < named_parameter(record,'TB')
                  < named_parameter(record,'TC')):
            raise ValueError('TGOV2 fast-valving schedule requires 0 < TA < TB < TC')
        else:
            pass
    elif model in ('TGOV3', 'TGOV3D', 'TGOV3DU'):
        positive = ('K','T3','T5')
        if named_parameter(record,'PMAX') <= named_parameter(record,'PMIN'):
            raise ValueError('TGOV3 governor power limits must be ordered')
        elif named_parameter(record,'UO') <= 0.0 or named_parameter(record,'UC') >= 0.0:
            raise ValueError('TGOV3 opening and closing rates must straddle zero')
        elif min(named_parameter(record,'T1'), named_parameter(record,'T2'),
                 named_parameter(record,'T4'), named_parameter(record,'T6')) < 0.0:
            raise ValueError('TGOV3 lag times must be nonnegative')
        elif named_parameter(record,'TA') <= 0.0 or named_parameter(record,'TB') < named_parameter(record,'TA') or named_parameter(record,'TC') <= named_parameter(record,'TB'):
            raise ValueError('TGOV3 fast-valving times must satisfy 0 < TA <= TB < TC')
        elif named_parameter(record,'K1') + named_parameter(record,'K2') + named_parameter(record,'K3') <= 0.0:
            raise ValueError('TGOV3 turbine power fractions must have positive total gain')
        elif model in ('TGOV3D', 'TGOV3DU') and (
                named_parameter(record, 'DBH') < 0.0
                or named_parameter(record, 'DBL') > 0.0
                or named_parameter(record, 'TRATE') < 0.0):
            raise ValueError('TGOV3D deadbands or turbine rating violate source limits')
        elif model == 'TGOV3' and (
                named_parameter(record, 'PMIN') < 0.0
                or named_parameter(record, 'PRMAX') <= 0.0):
            raise ValueError('TGOV3 source power and reheat limits are invalid')
        else:
            pass
    elif model in ('HYGOV','HYGOVD','HYGOVDU'):
        positive = ('R','r','Tr','Tf','Tg','Tw','At')
    elif model == 'HYGOVR1':
        positive = ('R','TW','AT')
        if min(named_parameter(record, name) for name in ('DB1','ERR','KP','TT','KG','TP','DB2','DTURB','QNL','TRATE')) < 0.0:
            raise ValueError('HYGOVR1 gains, deadbands, damping and rating must be nonnegative')
        elif named_parameter(record, 'VELOPEN') < 0.0 or named_parameter(record, 'VELCLOSE') > 0.0:
            raise ValueError('HYGOVR1 gate rates must open positively and close negatively')
        elif named_parameter(record, 'PMAX') <= named_parameter(record, 'PMIN') or named_parameter(record, 'PMIN') < 0.0:
            raise ValueError('HYGOVR1 gate limits must be ordered and nonnegative')
        elif min(named_parameter(record, 'TD'), *(named_parameter(record, 'T' + str(index)) for index in range(1, 9))) < 0.0:
            raise ValueError('HYGOVR1 filter and lead-lag times must be nonnegative')
        else:
            for stage_index in range(4):
                lead_time: float = named_parameter(record, 'T' + str(stage_index * 2 + 1))
                lag_time: float = named_parameter(record, 'T' + str(stage_index * 2 + 2))
                if lag_time == 0.0 and lead_time != 0.0:
                    raise ValueError('HYGOVR1 zero lag requires zero lead in each stage')
                else:
                    pass
    elif model == 'IEEEG2':
        positive = ('T3','T4')
        if named_parameter(record,'T1') < 0 or named_parameter(record,'T2') < 0 or named_parameter(record,'K') < 0:
            raise ValueError('Hydro governor gain/filter times must be nonnegative')
        elif named_parameter(record,'PMAX') <= named_parameter(record,'PMIN'):
            raise ValueError('Hydro governor upper power limit must exceed lower limit')
        else:
            pass
    elif model == 'SEXS':
        positive = ('TB','K','TE')
    elif model == 'SCRX':
        positive = ('TB','K')
        if named_parameter(record,'TATB') < 0 or named_parameter(record,'RC_RFD') < 0 or named_parameter(record,'TE') < 0:
            raise ValueError('Static-exciter lead ratio and crowbar resistance must be nonnegative')
        elif named_parameter(record,'CSWITCH') not in (0,1):
            raise ValueError('Static-exciter source switch must be 0 or 1')
        elif named_parameter(record,'EMAX') <= named_parameter(record,'EMIN'):
            raise ValueError('Static-exciter maximum must exceed minimum')
        else:
            pass
    elif model == 'EXST1':
        positive = ('KA',)
        if any(named_parameter(record,name) < 0 for name in ('TR','TB','TA','TF')):
            raise ValueError('EXST1 time constants cannot be negative')
        elif named_parameter(record,'TB') == 0 and named_parameter(record,'TC') != 0:
            raise ValueError('Zero-TB EXST1 needs TC=0 for an exact algebraic lead-lag')
        elif named_parameter(record,'TF') == 0 and named_parameter(record,'KF') != 0:
            raise ValueError('Zero-TF EXST1 needs KF=0 for disabled rate feedback')
        else:
            pass
    elif model == 'ST6C':
        positive = ('KPA','TG','VBMAX')
        if len(record.icons) != 4 or any(flag not in (1,2,3,4) for flag in record.icons[:3]) or record.icons[3] not in (1,2):
            raise ValueError('Current-limited field excitation selectors are invalid')
        else:
            pass
    elif model == 'ST6B':
        positive = ('TR','KPA','KIA','TDA','TG')
        if named_parameter(record,'KDA') < 0.0:
            raise ValueError('ST6B derivative gain must be nonnegative')
        elif named_parameter(record,'KM') <= 0.0 or named_parameter(record,'KFF') < 0.0:
            raise ValueError('ST6B forward path requires KM positive and KFF nonnegative')
        elif named_parameter(record,'VAMAX') <= named_parameter(record,'VAMIN'):
            raise ValueError('ST6B regulator upper limit must exceed its lower limit')
        elif named_parameter(record,'VRMAX') <= named_parameter(record,'VRMIN'):
            raise ValueError('ST6B field regulator upper limit must exceed its lower limit')
        else:
            pass
    elif model in ('ST5B','ST5C'):
        positive = ('KR',)
        if model == 'ST5C' and (len(record.icons) != 2 or any(flag not in (1,2) for flag in record.icons)):
            raise ValueError('Selectable parallel excitation requires OEL/UEL selectors one or two')
        else:
            pass
    elif model == 'AC11C':
        positive = ('KPA','TIA','KPU','TIU','KPO','TIO','TE','KE','VFEMAX','KP')
        if (len(record.icons) != 5 or record.icons[0] not in (1,2,3)
                or any(flag not in (1,2,3) for flag in record.icons[1:4])
                or record.icons[4] not in (1,2)):
            raise ValueError('AC11C stabilizer, limiter or power-source selectors are invalid')
        else:
            pass
    elif model in ('AC6C','AC6C2'):
        positive = ('KA','KE','TE','VFEMAX')
        if len(record.icons) != (3 if model == 'AC6C2' else 2) or any(flag not in (1,2) for flag in record.icons[:2]) or (model == 'AC6C2' and record.icons[2] not in (0,1)):
            raise ValueError('Two-stage brushless limiter selection is invalid')
        else:
            pass
    elif model in ('AC7B','AC7C'):
        positive = ('KE','TE','VFEMAX')
        if model == 'AC7C' and (len(record.icons) != 6 or record.icons[0] not in (1,2,3,4) or any(flag not in (1,2,3) for flag in record.icons[1:3]) or any(flag not in (1,2) for flag in record.icons[3:])):
            raise ValueError('Modern cascaded excitation source/signal selections are invalid')
        else:
            pass
    elif model in ('AC8B','AC8C'):
        positive = ('KA','KE','TE','VFEMAX')
        if model == 'AC8C' and (len(record.icons) != 5 or any(flag not in (1,2,3) for flag in record.icons[:3]) or any(flag not in (1,2) for flag in record.icons[3:])):
            raise ValueError('Compound PID excitation signal/source selectors are invalid')
        else:
            pass
    elif model == 'ST4C':
        positive = ('KPR','TG','VBMAX')
        if len(record.icons) != 5 or record.icons[0] not in (1,2) or any(flag not in (1,2,3) for flag in record.icons[1:4]) or record.icons[4] not in (1,2):
            raise ValueError('Filtered compound excitation signal/source selections are invalid')
        else:
            pass
    elif model == 'ESST3A':
        positive = ('TB','TM','KA')
        if named_parameter(record,'TA') != 0:
            raise ValueError('Native ESST3A template implements the TA=0 structural variant only')
        elif named_parameter(record,'TR') < 0:
            raise ValueError('ESST3A transducer time constant cannot be negative')
        else:
            pass
    elif model in ('EXAC1','EXAC1A','ESAC1A','EXAC2','EXAC3','ESAC2A','ESAC3A','EXBAS','AC1C','AC2C','AC5C'):
        positive = ('TR','TF2','KA','TA','TE','TF1') if model == 'AC5C' else ('TR','TB','KA','TA','TE','TF')
        if model in ('AC1C','AC2C','AC5C') and (len(record.icons) != 2 or any(flag not in (1,2) for flag in record.icons) or named_parameter(record,'VEMIN') != 0 or min(named_parameter(record,'KC'),named_parameter(record,'KD')) <= 0):
            raise ValueError('Reviewed brushless source requires OEL/UEL flags one or two, VEMIN=0 and positive KC/KD')
        else:
            pass
        if model == 'AC5C' and named_parameter(record,'TF3') < 0:
            raise ValueError('Brushless feedback-shaper lead time must be nonnegative')
        else:
            pass
        upper_name: str = 'VAMAX' if model in ('EXAC3','ESAC3A') else 'VRMAX'
        lower_name: str = 'VAMIN' if model in ('EXAC3','ESAC3A') else 'VRMIN'
        if named_parameter(record,upper_name) <= named_parameter(record,lower_name):
            raise ValueError('Exciter upper limit must exceed lower limit')
        elif model in ('ESAC1A','EXAC2','ESAC2A','AC1C','AC2C') and named_parameter(record,'VAMAX') <= named_parameter(record,'VAMIN'):
            raise ValueError('Exciter amplifier upper limit must exceed lower limit')
        elif min(named_parameter(record,'E1'),named_parameter(record,'SE1'),
                 named_parameter(record,'E2'),named_parameter(record,'SE2')) < 0:
            raise ValueError('Exciter saturation samples must be nonnegative')
        elif (named_parameter(record,'SE1') != 0 or named_parameter(record,'SE2') != 0) and (
                named_parameter(record,'E2') <= named_parameter(record,'E1') or
                named_parameter(record,'E2')*named_parameter(record,'SE2') <= named_parameter(record,'E1')*named_parameter(record,'SE1')):
            raise ValueError('Enabled saturation requires increasing voltage and excess-field samples')
        else:
            pass
        if model == 'EXBAS' and (min(named_parameter(record,'KI'),named_parameter(record,'TF2'),named_parameter(record,'KE')) <= 0 or
                min(named_parameter(record,'KP'),named_parameter(record,'TF1'),named_parameter(record,'KF'),named_parameter(record,'VRMIN')) < 0):
            raise ValueError('Reviewed PI brushless excitation requires positive integral/feedback-lag/resistance and nonnegative proportional/feedback/forcing settings')
        else:
            pass
        if model in ('ESAC2A','ESAC3A','AC1C','AC2C','AC5C') and (min(named_parameter(record,'KE'),named_parameter(record,'VFEMAX')) <= 0 or
                min(named_parameter(record,'KD'),named_parameter(record,'KC'),named_parameter(record,'KF')) < 0):
            raise ValueError('Reviewed field-current stops require positive resistance/current ceiling and nonnegative loading/feedback')
        elif model in ('ESAC2A','AC2C') and (named_parameter(record,'KB') <= 0 or named_parameter(record,'KH') < 0):
            raise ValueError('High-response excitation requires positive inner gain and nonnegative direct feedback')
        elif model == 'ESAC3A' and (min(named_parameter(record,'KR'),named_parameter(record,'EFDN')) <= 0 or
                min(named_parameter(record,'KN'),named_parameter(record,'VEMIN')) < 0):
            raise ValueError('Self-excited excitation requires positive supply gain/knee and nonnegative lower voltage/feedback')
        else:
            pass
        if model == 'EXAC2' and (min(named_parameter(record,'KB'),named_parameter(record,'KL'),
                                    named_parameter(record,'VLR')) <= 0 or named_parameter(record,'KH') < 0):
            raise ValueError('High-response excitation requires positive inner/limiter gain and reference, and nonnegative direct feedback')
        else:
            pass
        if model == 'EXAC3' and (min(named_parameter(record,'KR'),named_parameter(record,'EFDN')) <= 0 or
                min(named_parameter(record,'KLV'),named_parameter(record,'KN'),named_parameter(record,'VLV'),named_parameter(record,'KF')) < 0):
            raise ValueError('Self-excited excitation requires positive supply gain/knee and nonnegative feedback/limiter settings')
        else:
            pass
    elif model in ('EXST2','EXST2A','ESST2A','IEEET3','IEEEX3'):
        if named_parameter(record,'KI') == 0 and named_parameter(record,'KP') != 0:
            raise ValueError('Automatic compound current-source gain calibration has not been reviewed')
        else:
            pass
    elif model == 'IEEET4':
        if named_parameter(record,'KR') <= 0 or named_parameter(record,'KV') <= named_parameter(record,'KR'):
            raise ValueError('Reviewed relay reset requires 0 < KR < KV; zero-deadband substitutions are not inferred')
        else:
            pass
    elif binding is not None and binding.dc_kind is not None:
        if binding.dc_kind in (DcExciterKind.BOUNDED_FIXED_SUPPLY,DcExciterKind.BOUNDED_TERMINAL_SUPPLY):
            if len(record.icons) != 2 or any(selection not in (1,2) for selection in record.icons):
                raise ValueError('Bounded rotating excitation requires explicit OEL/UEL flags one or two')
            elif named_parameter(record,'KE') == 0 or named_parameter(record,'VRMAX') <= 0:
                raise ValueError('Bounded rotating exciter automatic coefficient/capability calibration has not been reviewed')
            else:
                pass
        else:
            pass
        reserved_switch: float = next((parameter.value for parameter in record.parameters if parameter.name == 'Switch'),0.0)
        if reserved_switch != 0:
            raise ValueError('Only the documented zero reserved DC-exciter switch is reviewed')
        else:
            pass
    else:
        pass
    if model == 'PSS2C':
        pss_on: float = named_parameter(record,'PSSON')
        pss_off: float = named_parameter(record,'PSSOFF')
        if pss_on == 0.0 and pss_off == 0.0:
            pass
        elif pss_on < 0.0:
            pass
        elif pss_on <= 0.0 or pss_off >= pss_on:
            raise ValueError('Enabled PSS2C output hysteresis requires PSSON > 0 and PSSOFF < PSSON')
        else:
            pass
    else:
        pass
    if model in ('TGOV1D','TGOV1DU','GASTD','GASTDU','IEESGOD','IEESGODU','HYGOVD','HYGOVDU','HYGOV2D','HYGOV2DU','PIDGOVD','PIDGOVDU'):
        if named_parameter(record,'TRATE') < 0:
            raise ValueError('Turbine rating must be nonnegative; zero selects machine MVA')
        else:
            pass
    else:
        pass
    if model in ('GENROU','GENROE','GENSAL','GENSAE'):
        if named_parameter(record,'Xd1') == named_parameter(record,'Xl'):
            raise ValueError('Transient and leakage reactances must differ')
        elif model in ('GENROU','GENROE') and named_parameter(record,'Xq1') == named_parameter(record,'Xl'):
            raise ValueError('Quadrature transient and leakage reactances must differ')
        elif named_parameter(record,'S10') < 0 or named_parameter(record,'S12') < 0 or (named_parameter(record,'S10') > 0 and named_parameter(record,'S12') <= named_parameter(record,'S10')):
            raise ValueError('Machine saturation points must be nonnegative and increasing')
        elif model in ('GENROE','GENSAE') and (named_parameter(record,'S10') == 0) != (named_parameter(record,'S12') == 0):
            raise ValueError('Power-law saturation needs two positive samples or two zeros')
        else:
            pass
    else:
        pass
    for name in positive:
        if named_parameter(record,name) <= 0:
            raise ValueError('Native '+model+' requires positive '+name+'; algebraic/zero-inertia variants are not substituted')
        else:
            pass


def _convert_renewable_assembly(
        context: PsseAuxiliaryConverter,
        key: tuple[int, str],
        records: list[tuple[str, DyrRecord]],
        unresolved_buses: set[int],
        unresolved_machines: set[tuple[int, str]],
) -> None:
    """Convert reviewed local REGCA1 renewable assemblies as one unit.

    The native current-source chain supports polar RMS, KHV=0, local REECA1
    direct-power constant-Q, constant-power-factor, local-voltage or
    coordinated Q/V control, and optional local REPCA1 power/Q control.
    Other selectors and neighboring models block the complete assignment.

    :param context: Shared grid, identity lookups and conversion ledger.
    :param key: Exact PSS/E bus and machine identifier.
    :param records: Valid, bound DYR records for the machine.
    :param unresolved_buses: Bus identities with unsupported or malformed records.
    :param unresolved_machines: Machine identities with unsupported or malformed records.
    :return: None.
    """
    generator: Generator | None = context.generators.get(key, None)
    raw: RawGeneratorLike | None = context.raw_generators.get(key, None)
    role_records: dict[PsseDynamicRole, list[tuple[str, DyrRecord]]] = dict()
    for source, record in records:
        binding: PsseDynamicBinding | None = dynamic_binding(dynamic_record_name(record))
        if binding is not None:
            role_records.setdefault(binding.role, list()).append((source, record))
        else:
            pass
    converter_records: list[tuple[str, DyrRecord]] = role_records.get(
        PsseDynamicRole.RENEWABLE_CONVERTER, list())
    electrical_records: list[tuple[str, DyrRecord]] = role_records.get(
        PsseDynamicRole.RENEWABLE_ELECTRICAL_CONTROL, list())
    plant_records: list[tuple[str, DyrRecord]] = role_records.get(
        PsseDynamicRole.RENEWABLE_PLANT_CONTROL, list())
    mechanical_records: list[tuple[str, DyrRecord]] = role_records.get(
        PsseDynamicRole.RENEWABLE_MECHANICAL_CONTROL, list())
    source_records: list[tuple[str, DyrRecord]] = list()
    source_records.extend(converter_records)
    source_records.extend(electrical_records)
    source_records.extend(plant_records)
    source_records.extend(mechanical_records)
    supported_roles: bool = len(source_records) == len(records)
    complete: bool = (
        generator is not None and raw is not None and raw.MBASE > 0
        and context.grid.Sbase > 0 and len(converter_records) == 1
        and len(electrical_records) == 1 and len(plant_records) <= 1
        and len(mechanical_records) <= 4
        and supported_roles and key[0] not in unresolved_buses
        and key not in unresolved_machines
    )
    if not complete:
        for source, record in records:
            context.record(source, record.line_number, PsseFileType.DYR,
                           PsseConversionStatus.UNRESOLVED, (),
                           'Renewable DYR assembly has missing, duplicate, unsupported, or ambiguous source records')
    else:
        assignment_attempted: bool = False
        original_runtime: Block = generator.rms_model
        converter_record: DyrRecord = converter_records[0][1]
        electrical_record: DyrRecord = electrical_records[0][1]
        battery_mode: bool = dynamic_record_name(electrical_record) == 'REECC1'
        power_factor_flag: int = int(electrical_record.icons[1])
        voltage_flag: int = int(electrical_record.icons[2])
        reactive_control_flag: int = int(electrical_record.icons[3])
        speed_power_flag: int = 0 if battery_mode else int(electrical_record.icons[4])
        priority_flag: int = int(electrical_record.icons[4] if battery_mode else electrical_record.icons[5])
        plant_record: DyrRecord | None = plant_records[0][1] if plant_records else None
        mechanical_by_model: dict[str, DyrRecord] = dict()
        try:
            for _, source_record in records:
                validate_dynamic_parameters(source_record)

            for _, mechanical_record in mechanical_records:
                mechanical_name: str = dynamic_record_name(mechanical_record)
                if mechanical_name == 'WTDTAU1':
                    mechanical_name = 'WTDTA1'
                elif mechanical_name == 'WTARAU1':
                    mechanical_name = 'WTARA1'
                elif mechanical_name == 'WTTQAU1':
                    mechanical_name = 'WTTQA1'
                elif mechanical_name == 'WTPTAU1':
                    mechanical_name = 'WTPTA1'
                else:
                    pass
                if mechanical_name in mechanical_by_model:
                    raise ValueError('Duplicate ' + mechanical_name + ' wind control record')
                else:
                    mechanical_by_model[mechanical_name] = mechanical_record

            if dynamic_record_name(converter_record) not in ('REGCA1', 'REGCAU1'):
                raise ValueError('Unexpected renewable converter source model')
            elif dynamic_record_name(electrical_record) not in ('REECA1', 'REECAU1', 'REECC1'):
                raise ValueError('Unexpected renewable electrical source model')
            elif plant_record is not None and dynamic_record_name(plant_record) not in ('REPCA1', 'REPCAU1', 'REPCTA1', 'REPCTAU1'):
                raise ValueError('Only local REPCA1/REPCTA1 plant control is supported in this assembly')
            else:
                pass

            if len(converter_record.icons) != 1 or converter_record.icons[0] not in (0, 1):
                raise ValueError('REGCA1 LVPLSW must be zero or one')
            elif len(electrical_record.icons) != (5 if battery_mode else 6):
                raise ValueError('Renewable electrical model has an incorrect ICON count')
            elif battery_mode and (electrical_record.icons[0] != 0
                                   or any(flag not in (0, 1) for flag in electrical_record.icons[1:])):
                raise ValueError('REECC1 currently requires local voltage and binary control selectors')
            elif battery_mode and electrical_record.icons[1] == 1 and electrical_record.icons[3] == 1:
                raise ValueError('REECC1 PFFLAG=1 with QFLAG=1 selects conflicting reactive controls')
            elif not battery_mode and (electrical_record.icons[0] != 0
                    or any(flag not in (0, 1) for flag in electrical_record.icons[1:])):
                raise ValueError('REECA1 requires local bus and supported selector flags')
            elif not battery_mode and electrical_record.icons[1] == 1 and electrical_record.icons[3] == 1:
                raise ValueError('REECA1 PFFLAG=1 with QFLAG=1 is not source-resolved')
            elif battery_mode and mechanical_records:
                raise ValueError('REECC1 battery cannot be combined with wind mechanical models')
            else:
                pass

            has_drive_train: bool = 'WTDTA1' in mechanical_by_model
            has_aerodynamics: bool = 'WTARA1' in mechanical_by_model
            has_torque_control: bool = 'WTTQA1' in mechanical_by_model
            has_pitch_control: bool = 'WTPTA1' in mechanical_by_model
            if has_aerodynamics and not has_drive_train:
                raise ValueError('WTARA1 requires the WTDTA1 shaft host')
            elif has_torque_control and (not has_drive_train or speed_power_flag != 0):
                raise ValueError('WTTQA1 requires WTDTA1 and REECA1 PFLAG=0')
            elif has_pitch_control and not (has_drive_train and has_aerodynamics and has_torque_control):
                raise ValueError('WTPTA1 requires WTDTA1, WTARA1 and WTTQA1')
            elif has_drive_train and not has_torque_control and speed_power_flag != 1:
                raise ValueError('WTDTA1 without WTTQA1 requires REECA1 PFLAG=1')
            elif speed_power_flag == 1 and not has_drive_train:
                raise ValueError('REECA1 PFLAG=1 requires the reviewed WTDTA1 speed signal')
            elif (plant_record is not None
                  and dynamic_record_name(plant_record) in ('REPCTA1', 'REPCTAU1')
                  and not has_torque_control):
                raise ValueError('REPCTA1 requires the WTTQA1 Type 3 torque-control path')
            else:
                pass

            khv: float = named_parameter(converter_record, 'KHV')
            if khv != 0.:
                raise ValueError('REGCA1 KHV requires the source network-iteration path')
            else:
                pass
            converter_settings: Regca1LowVoltageSettings = Regca1LowVoltageSettings(
                tg=named_parameter(converter_record, 'TG'),
                rrpwr=named_parameter(converter_record, 'RRPWR'),
                brkpt=named_parameter(converter_record, 'BRKPT'),
                zerox=named_parameter(converter_record, 'ZEROX'),
                lvpl1=named_parameter(converter_record, 'LVPL1'),
                volim=named_parameter(converter_record, 'VOLIM'),
                lvpnt1=named_parameter(converter_record, 'LVPNT1'),
                lvpnt0=named_parameter(converter_record, 'LVPNT0'),
                iolim=named_parameter(converter_record, 'IOLIM'),
                tfltr=named_parameter(converter_record, 'TFLTR'),
                khv=khv,
                iqrmax=named_parameter(converter_record, 'IQRMAX'),
                iqrmin=named_parameter(converter_record, 'IQRMIN'),
                accel=named_parameter(converter_record, 'ACCEL'),
                lvplsw=bool(converter_record.icons[0]),
            )

            reactive_curve: tuple[tuple[float, float], ...] = reeca1_curve_from_source_pairs((
                (named_parameter(electrical_record, 'VQ1'), named_parameter(electrical_record, 'IQ1')),
                (named_parameter(electrical_record, 'VQ2'), named_parameter(electrical_record, 'IQ2')),
                (named_parameter(electrical_record, 'VQ3'), named_parameter(electrical_record, 'IQ3')),
                (named_parameter(electrical_record, 'VQ4'), named_parameter(electrical_record, 'IQ4')),
            ))
            active_curve: tuple[tuple[float, float], ...] = reeca1_curve_from_source_pairs((
                (named_parameter(electrical_record, 'VP1'), named_parameter(electrical_record, 'IP1')),
                (named_parameter(electrical_record, 'VP2'), named_parameter(electrical_record, 'IP2')),
                (named_parameter(electrical_record, 'VP3'), named_parameter(electrical_record, 'IP3')),
                (named_parameter(electrical_record, 'VP4'), named_parameter(electrical_record, 'IP4')),
            ))
            current_limits: Reeca1CurrentLimitSettings = Reeca1CurrentLimitSettings(
                imax=named_parameter(electrical_record, 'IMAX'),
                reactive_curve=reactive_curve,
                active_curve=active_curve,
                priority=(Reeca1CurrentPriority.REACTIVE if priority_flag == 0
                          else Reeca1CurrentPriority.ACTIVE),
                trv=named_parameter(electrical_record, 'TRV'),
                thld2=(0.0 if battery_mode else named_parameter(electrical_record, 'THLD2')),
                bidirectional_active_current=battery_mode,
            )
            dpmax: float = named_parameter(electrical_record, 'DPMAX')
            dpmin: float = named_parameter(electrical_record, 'DPMIN')
            if dpmax == 0. and dpmin == 0.:
                pref_rates: tuple[float | None, float | None] = (None, None)
            else:
                pref_rates = (dpmax, dpmin)
            active_settings: Reeca1ActivePowerSettings = Reeca1ActivePowerSettings(
                tpord=named_parameter(electrical_record, 'TPORD'),
                pmin=named_parameter(electrical_record, 'PMIN'),
                pmax=named_parameter(electrical_record, 'PMAX'),
                mode=(Reeca1ActivePowerMode.TORQUE_TIMES_SPEED
                      if speed_power_flag == 1 else Reeca1ActivePowerMode.POWER),
                dpmax=pref_rates[0], dpmin=pref_rates[1],
                bidirectional=battery_mode,
            )
            voltage_support: Reeca1VoltageSupportSettings = Reeca1VoltageSupportSettings(
                vdip=named_parameter(electrical_record, 'VDIP'),
                vup=named_parameter(electrical_record, 'VUP'),
                dbd1=named_parameter(electrical_record, 'DBD1'),
                dbd2=named_parameter(electrical_record, 'DBD2'),
                kqv=named_parameter(electrical_record, 'KQV'),
                iqh1=named_parameter(electrical_record, 'IQH1'),
                iql1=named_parameter(electrical_record, 'IQL1'),
                vref0=named_parameter(electrical_record, 'VREF0'),
                iqfrz=(0.0 if battery_mode else named_parameter(electrical_record, 'IQFRZ')),
                thld=(0.0 if battery_mode else named_parameter(electrical_record, 'THLD')),
            )
            drive_train_settings: Wtdta1DriveTrainSettings | None = None
            if has_drive_train:
                drive_record: DyrRecord = mechanical_by_model['WTDTA1']
                drive_train_settings = Wtdta1DriveTrainSettings(
                    h=named_parameter(drive_record, 'H'),
                    damp=named_parameter(drive_record, 'DAMP'),
                    htfrac=named_parameter(drive_record, 'HTFRAC'),
                    freq1=named_parameter(drive_record, 'FREQ1'),
                    dshaft=named_parameter(drive_record, 'DSHAFT'),
                    nominal_frequency_hz=context.grid.fBase,
                )
            else:
                pass
            aerodynamic_settings: Wtara1AerodynamicSettings | None = None
            if has_aerodynamics:
                aerodynamic_record: DyrRecord = mechanical_by_model['WTARA1']
                aerodynamic_settings = Wtara1AerodynamicSettings(
                    ka=named_parameter(aerodynamic_record, 'KA'),
                    theta0=named_parameter(aerodynamic_record, 'THETA0'),
                )
            else:
                pass
            torque_settings: Wttqa1TorqueSettings | None = None
            if has_torque_control:
                torque_record: DyrRecord = mechanical_by_model['WTTQA1']
                torque_settings = Wttqa1TorqueSettings(
                    kpp=named_parameter(torque_record, 'KPP'),
                    kip=named_parameter(torque_record, 'KIP'),
                    tp=named_parameter(torque_record, 'TP'),
                    twref=named_parameter(torque_record, 'TWREF'),
                    temax=named_parameter(torque_record, 'TEMAX'),
                    temin=named_parameter(torque_record, 'TEMIN'),
                    curve=((named_parameter(torque_record, 'P1'), named_parameter(torque_record, 'SPD1')),
                           (named_parameter(torque_record, 'P2'), named_parameter(torque_record, 'SPD2')),
                           (named_parameter(torque_record, 'P3'), named_parameter(torque_record, 'SPD3')),
                           (named_parameter(torque_record, 'P4'), named_parameter(torque_record, 'SPD4'))),
                    trate=named_parameter(torque_record, 'TRATE'),
                    mode=Wttqa1TorqueMode(torque_record.icons[0]),
                )
            else:
                pass
            pitch_settings: Wtpta1PitchSettings | None = None
            if has_pitch_control:
                pitch_record: DyrRecord = mechanical_by_model['WTPTA1']
                pitch_settings = Wtpta1PitchSettings(
                    kiw=named_parameter(pitch_record, 'KIW'),
                    kpw=named_parameter(pitch_record, 'KPW'),
                    kic=named_parameter(pitch_record, 'KIC'),
                    kpc=named_parameter(pitch_record, 'KPC'),
                    kcc=named_parameter(pitch_record, 'KCC'),
                    tp=named_parameter(pitch_record, 'TP'),
                    theta_max=named_parameter(pitch_record, 'TETAMAX'),
                    theta_min=named_parameter(pitch_record, 'TETAMIN'),
                    rate_max=named_parameter(pitch_record, 'RTETAMAX'),
                    rate_min=named_parameter(pitch_record, 'RTETAMIN'),
                )
            else:
                pass
            reactive_settings: Reeca1ConstantQSettings | None
            if reactive_control_flag == 0 or (battery_mode and voltage_flag == 1):
                reactive_settings = Reeca1ConstantQSettings(
                    tiq=named_parameter(electrical_record, 'TIQ'),
                    qmin=named_parameter(electrical_record, 'QMIN'),
                    qmax=named_parameter(electrical_record, 'QMAX'),
                )
            else:
                reactive_settings = None
            power_factor_settings: Reeca1ConstantPfSettings | None = None
            coordinated_qv_settings: Reeca1CoordinatedQvSettings | None = None
            local_voltage_settings: Reeca1LocalVoltageSettings | None = None
            if power_factor_flag == 1:
                power_factor_settings = Reeca1ConstantPfSettings(
                    tp=named_parameter(electrical_record, 'TP'),
                )
            elif not battery_mode and reactive_control_flag == 1 and voltage_flag == 1:
                coordinated_qv_settings = Reeca1CoordinatedQvSettings(
                    qmin=named_parameter(electrical_record, 'QMIN'),
                    qmax=named_parameter(electrical_record, 'QMAX'),
                    vmin=named_parameter(electrical_record, 'VMIN'),
                    vmax=named_parameter(electrical_record, 'VMAX'),
                    kqp=named_parameter(electrical_record, 'KQP'),
                    kqi=named_parameter(electrical_record, 'KQI'),
                    kvp=named_parameter(electrical_record, 'KVP'),
                    kvi=named_parameter(electrical_record, 'KVI'),
                    tiq=named_parameter(electrical_record, 'TIQ'),
                )
            elif reactive_control_flag == 1:
                local_voltage_settings = Reeca1LocalVoltageSettings(
                    kvp=named_parameter(electrical_record, 'KVP'),
                    kvi=named_parameter(electrical_record, 'KVI'),
                    vbias=(0.0 if battery_mode else named_parameter(electrical_record, 'VBIAS')),
                    tiq=named_parameter(electrical_record, 'TIQ'),
                )
            else:
                pass
            battery_settings: Reecc1BatterySettings | None = None
            if battery_mode:
                battery_settings = Reecc1BatterySettings(
                    time_seconds=named_parameter(electrical_record, 'T'),
                    soc_initial=named_parameter(electrical_record, 'SOCINI'),
                    soc_maximum=named_parameter(electrical_record, 'SOCMAX'),
                    soc_minimum=named_parameter(electrical_record, 'SOCMIN'),
                )
            else:
                pass
            plant_active: Repca1ActivePlantSettings | None = None
            plant_reactive: Repca1ReactivePlantSettings | None = None
            if plant_record is not None:
                if (len(plant_record.icons) != 7 or plant_record.icons[0] != 0
                        or plant_record.icons[1] != 0 or plant_record.icons[2] != 0
                        or plant_record.icons[4] != 0 or plant_record.icons[5] != 0
                        or plant_record.icons[6] != 0):
                    raise ValueError('REPCA1 supports only local plant measurements without frequency response')
                else:
                    pass
                plant_active = Repca1ActivePlantSettings(
                    kpg=named_parameter(plant_record, 'KPG'),
                    kig=named_parameter(plant_record, 'KIG'),
                    tp=named_parameter(plant_record, 'TP'),
                    fdbd1=named_parameter(plant_record, 'FDBD1'),
                    fdbd2=named_parameter(plant_record, 'FDBD2'),
                    femax=named_parameter(plant_record, 'FEMAX'),
                    femin=named_parameter(plant_record, 'FEMIN'),
                    pmax=named_parameter(plant_record, 'PMAX'),
                    pmin=named_parameter(plant_record, 'PMIN'),
                    tg=named_parameter(plant_record, 'TG'),
                    ddn=named_parameter(plant_record, 'DDN'),
                    dup=named_parameter(plant_record, 'DUP'),
                    frequency_enabled=False,
                )
                plant_reactive = Repca1ReactivePlantSettings(
                    tfltr=named_parameter(plant_record, 'TFLTR'),
                    kp=named_parameter(plant_record, 'KP'),
                    ki=named_parameter(plant_record, 'KI'),
                    tft=named_parameter(plant_record, 'TFT'),
                    tfv=named_parameter(plant_record, 'TFV'),
                    vfrz=named_parameter(plant_record, 'VFRZ'),
                    rc=named_parameter(plant_record, 'RC'),
                    xc=named_parameter(plant_record, 'XC'),
                    kc=named_parameter(plant_record, 'KC'),
                    emax=named_parameter(plant_record, 'EMAX'),
                    emin=named_parameter(plant_record, 'EMIN'),
                    dbd1=named_parameter(plant_record, 'DBD1'),
                    dbd2=named_parameter(plant_record, 'DBD2'),
                    qmax=named_parameter(plant_record, 'QMAX'),
                    qmin=named_parameter(plant_record, 'QMIN'),
                    mode=Repca1ReactiveMode.Q_CONTROL,
                )
            else:
                pass

            template: RmsModelTemplate = build_renewable_partial_chain(
                vf=context.grid.var_factory,
                name='PSSE_' + str(key[0]) + '_' + key[1] + '_REGCA1',
                converter_settings=converter_settings,
                current_limit_settings=current_limits,
                active_power_settings=active_settings,
                drive_train_settings=drive_train_settings,
                aerodynamic_settings=aerodynamic_settings,
                torque_settings=torque_settings,
                pitch_settings=pitch_settings,
                plant_settings=plant_active,
                plant_reactive_settings=plant_reactive,
                reactive_power_settings=reactive_settings,
                power_factor_settings=power_factor_settings,
                coordinated_qv_settings=coordinated_qv_settings,
                local_voltage_settings=local_voltage_settings,
                voltage_support_settings=voltage_support,
                battery_settings=battery_settings,
            )
            if generator.rms_template is not None or generator.rms_fmu_template is not None:
                raise ValueError('Generator already has an RMS model assignment')
            else:
                pass
            assignment_attempted = True
            generator.rms_template = template
            context.grid.add_rms_model(template)
            for source, record in records:
                context.record(source, record.line_number, PsseFileType.DYR,
                               PsseConversionStatus.CONVERTED, (generator, template),
                               'Applied ' + dynamic_record_name(record)
                               + ' through the reviewed local renewable current-source assembly')
        except (ValueError, KeyError, IndexError) as error:
            if assignment_attempted:
                generator.rms_template = None
                generator.rms_model = original_runtime
            else:
                pass
            for source, record in records:
                context.record(source, record.line_number, PsseFileType.DYR,
                               PsseConversionStatus.UNRESOLVED, (),
                               'Renewable DYR assembly rejected: ' + str(error))


def _convert_dera1_assembly(
        context: PsseAuxiliaryConverter,
        key: tuple[int, str],
        records: list[tuple[str, DyrRecord]],
        unresolved_buses: set[int],
        unresolved_machines: set[tuple[int, str]],
) -> None:
    """Convert a single reviewed DERA1 record to its physical generator host.

    :param context: Source/native identity maps and conversion report owner.
    :param key: Exact PSS/E bus and machine identity.
    :param records: Records assigned to the same machine.
    :param unresolved_buses: Buses with ambiguous unsupported records.
    :param unresolved_machines: Machines with ambiguous unsupported records.
    :return: None.
    """
    generator: Generator | None = context.generators.get(key, None)
    raw: RawGeneratorLike | None = context.raw_generators.get(key, None)
    complete: bool = (
        len(records) == 1 and generator is not None and raw is not None
        and raw.MBASE > 0.0 and context.grid.Sbase > 0.0
        and raw.XT == 0.0
        and key[0] not in unresolved_buses and key not in unresolved_machines
    )
    if not complete:
        for source, record in records:
            context.record(
                source, record.line_number, PsseFileType.DYR,
                PsseConversionStatus.UNRESOLVED, (),
                'DERA1 requires one unambiguous renewable generator with zero implicit transformer impedance',
            )
    else:
        source: str
        record: DyrRecord
        source, record = records[0]
        original_runtime: Block = generator.rms_model
        assignment_attempted: bool = False
        try:
            validate_dynamic_parameters(record)
            if dynamic_record_name(record) != 'DERA1':
                raise ValueError('Unexpected model in DERA1 assembly')
            else:
                pass

            machine_base: float = float(raw.MBASE)
            system_base: float = float(context.grid.Sbase)
            machine_ratio: float = machine_base / system_base
            initial_voltage: float = float(context.buses[key[0]].Vm0)
            initial_angle: float = float(context.buses[key[0]].Va0)
            initial_p: float = float(generator.P) / machine_base
            initial_q: float = float(generator.Q) / machine_base
            initial_frequency: float = float(context.grid.fBase)
            if initial_voltage <= 0.0 or machine_ratio <= 0.0:
                raise ValueError('DERA1 operating point requires positive voltage and machine base')
            else:
                pass

            if initial_p == 0.0 and initial_q == 0.0:
                pf_angle = 0.0
            else:
                pf_angle = math.atan2(initial_q, initial_p)
            active: Dera1ActivePowerSettings = Dera1ActivePowerSettings(
                trf=named_parameter(record, 'TRF'),
                tp=named_parameter(record, 'TP'),
                ddn=named_parameter(record, 'DDN'),
                dup=named_parameter(record, 'DUP'),
                fdbd1=named_parameter(record, 'FDBD1'),
                fdbd2=named_parameter(record, 'FDBD2'),
                femax=named_parameter(record, 'FEMAX'),
                femin=named_parameter(record, 'FEMIN'),
                pmax=named_parameter(record, 'PMAX'),
                pmin=named_parameter(record, 'PMIN'),
                dpmax=named_parameter(record, 'DPMAX'),
                dpmin=named_parameter(record, 'DPMIN'),
                tpord=named_parameter(record, 'TPORD'),
                kpg=named_parameter(record, 'KPG'),
                kig=named_parameter(record, 'KIG'),
                initial_frequency_deviation=0.0,
                initial_active_power=initial_p,
            )
            reactive: Dera1ReactiveCurrentSettings = Dera1ReactiveCurrentSettings(
                pf_control=bool(record.icons[0]),
                dbd1=named_parameter(record, 'DBD1'),
                dbd2=named_parameter(record, 'DBD2'),
                kqv=named_parameter(record, 'KQV'),
                vref0=named_parameter(record, 'VREF0'),
                tiq=named_parameter(record, 'TIQ'),
                iqhl=named_parameter(record, 'IQHL'),
                iqll=named_parameter(record, 'IQLL'),
                initial_voltage=initial_voltage,
                initial_active_power=initial_p,
                initial_reactive_power=initial_q,
                pf_angle=pf_angle,
            )
            protection: Dera1ProtectionSettings = Dera1ProtectionSettings(
                voltage_trip_enabled=bool(record.icons[4]),
                frequency_trip_enabled=bool(record.icons[5]),
                vl0=named_parameter(record, 'VL0'),
                vl1=named_parameter(record, 'VL1'),
                vh0=named_parameter(record, 'VH0'),
                vh1=named_parameter(record, 'VH1'),
                tvl0=named_parameter(record, 'TVL0'),
                tvl1=named_parameter(record, 'TVL1'),
                tvh0=named_parameter(record, 'TVH0'),
                tvh1=named_parameter(record, 'TVH1'),
                vrfrac=named_parameter(record, 'VRFRAC'),
                fl=named_parameter(record, 'FL'),
                fh=named_parameter(record, 'FH'),
                tfl=named_parameter(record, 'TFL'),
                tfh=named_parameter(record, 'TFH'),
                tv=named_parameter(record, 'TV'),
                vpr=named_parameter(record, 'VPR'),
                initial_voltage=initial_voltage,
                initial_frequency_hz=initial_frequency,
            )
            inner: Dera1InnerCurrentLoopSettings = Dera1InnerCurrentLoopSettings(
                tg=named_parameter(record, 'TG'),
                rrpwr=named_parameter(record, 'RRPWR'),
                initial_active_current=initial_p / initial_voltage,
                initial_reactive_current=initial_q / initial_voltage,
            )
            voltage_settings: Dera1VoltageMeasurementSettings = Dera1VoltageMeasurementSettings(
                trv=named_parameter(record, 'TRV'),
                initial_voltage=initial_voltage,
            )
            template: RmsModelTemplate = build_dera1_generator_template(
                vf=context.grid.var_factory,
                name='PSSE_' + str(key[0]) + '_' + key[1] + '_DERA1',
                active_settings=active,
                reactive_settings=reactive,
                inner_current_settings=inner,
                protection_settings=protection,
                voltage_settings=voltage_settings,
                imax=named_parameter(record, 'IMAX'),
                active_current_priority=bool(record.icons[2]),
                generator=bool(record.icons[3]),
            )
            host: Block = template.block
            assignment_attempted = True
            generator.rms_template = template
            context.grid.add_rms_model(template)
            context.record(
                source, record.line_number, PsseFileType.DYR,
                PsseConversionStatus.CONVERTED, (generator, template),
                'Applied PSS/E 35.2 DERA1 current-source control and protection model',
            )
        except (ValueError, KeyError, IndexError, StopIteration) as error:
            if assignment_attempted:
                generator.rms_template = None
                generator.rms_model = original_runtime
            else:
                pass
            context.record(
                source, record.line_number, PsseFileType.DYR,
                PsseConversionStatus.UNRESOLVED, (),
                'DERA1 source binding rejected: ' + str(error),
            )


def convert_dynamics(context: PsseAuxiliaryConverter) -> None:
    """Build one connected native RMS model per exact PSS/E machine identity.

    A bad or unsupported controller blocks activation of its machine assembly.
    No partially connected model is installed as if it were ready to simulate.

    :param context: Shared native identity lookups, diagnostics and conversion ledger.
    """
    assignments: dict[tuple[int,str], list[tuple[str,DyrRecord]]] = dict()
    unresolved_buses: set[int] = set()
    unresolved_machines: set[tuple[int,str]] = set()
    cross_machine_keys: set[tuple[int, str]] = set()
    rejected_sources: set[str] = set()
    occupied_loads: set[tuple[int, str]] = set()
    for document in context.source.dyr_files:
        for record in document.records:
            number: int | None = context.bus_number(record.bus)
            binding: PsseDynamicBinding | None = dynamic_binding(dynamic_record_name(record))
            if dynamic_record_name(record) in ('WTDTA1', 'WTARA1', 'WTTQA1', 'WTPTA1', 'REPCTA1') and document.version is not PsseVersion.V35:
                binding = None
            elif dynamic_record_name(record) in ('WTDTAU1', 'WTARAU1', 'WTTQAU1', 'WTPTAU1', 'REPCTAU1') and document.version is not PsseVersion.V33:
                binding = None
            elif dynamic_record_name(record) == 'ST8C' and document.version is not PsseVersion.V35:
                binding = None
            elif dynamic_record_name(record) == 'ST10C' and document.version is not PsseVersion.V35:
                binding = None
            elif dynamic_record_name(record) == 'REECC1' and document.version is not PsseVersion.V35:
                binding = None
            elif dynamic_record_name(record) == 'HYGOVR1' and document.version is not PsseVersion.V35:
                binding = None
            elif dynamic_record_name(record) in ('CIMTR1', 'CIMTR2', 'CIMTR3', 'CIMTR4') and document.version is not PsseVersion.V35:
                binding = None
            else:
                pass
            # An unreviewed two-shaft governor must not leave its other named
            # machine running as if that mechanical coupling did not exist.
            if record.model.upper() in ('IEEEG1','IEEEG1D') and record.status == RecordStatus.VALID and len(record.icons) == 2 and isinstance(record.icons[0],int) and record.icons[0] > 0:
                unresolved_machines.add((record.icons[0],str(record.icons[1]).strip()))
                if number is not None:
                    unresolved_machines.add((number,(record.equipment_id or '1').strip()))
                else:
                    pass
            elif (record.user_header is not None and record.user_header.model_type == UserModelType.CROSS_COMPOUND_GOVERNOR
                  and len(record.remote_buses) == 1 and len(record.user_header.references) == 2):
                secondary_number: int | None = context.bus_number(record.remote_buses[0])
                if secondary_number is not None:
                    unresolved_machines.add((secondary_number,str(record.user_header.references[1]).strip()))
                else:
                    pass
                if number is not None:
                    unresolved_machines.add((number,(record.equipment_id or '1').strip()))
                else:
                    pass
            else:
                pass
            if record.target_kind == EquipmentKind.LOAD:
                load_model_name: str = dynamic_record_name(record)
                if record.status == RecordStatus.INVALID:
                    context.record(
                        document.source, record.line_number, PsseFileType.DYR,
                        PsseConversionStatus.INVALID, (), 'Invalid PSS/E load model record',
                    )
                elif load_model_name.startswith('CMLD') and document.version is not PsseVersion.V35:
                    context.record(
                        document.source, record.line_number, PsseFileType.DYR,
                        PsseConversionStatus.UNSUPPORTED, (),
                        'PSS/E CMLD binding is reviewed only for release 35.2',
                    )
                elif load_model_name.startswith('CMLD'):
                    try:
                        convert_psse_cmld_static_record(
                            context=context,
                            source=document.source,
                            record=record,
                            occupied_loads=occupied_loads,
                        )
                    except (ValueError, KeyError, IndexError, StopIteration) as error:
                        context.record(
                            document.source, record.line_number, PsseFileType.DYR,
                            PsseConversionStatus.UNRESOLVED, (),
                            'PSS/E CMLD source binding rejected: ' + str(error),
                        )
                elif load_model_name.startswith(('CIM5','CIM6','CIMW')) and document.version is not PsseVersion.V35:
                    context.record(
                        document.source, record.line_number, PsseFileType.DYR,
                        PsseConversionStatus.UNSUPPORTED, (),
                        'PSS/E CIM load binding is reviewed only for release 35.2',
                    )
                elif load_model_name.startswith(('CIM5','CIM6','CIMW')):
                    try:
                        convert_psse_cim_load_record(
                            context=context,
                            source=document.source,
                            record=record,
                            occupied_loads=occupied_loads,
                        )
                    except (ValueError, KeyError, IndexError, StopIteration) as error:
                        context.record(
                            document.source, record.line_number, PsseFileType.DYR,
                            PsseConversionStatus.UNRESOLVED, (),
                            'PSS/E CIM source binding rejected: ' + str(error),
                        )
                else:
                    context.record(
                        document.source, record.line_number, PsseFileType.DYR,
                        PsseConversionStatus.UNSUPPORTED, (),
                        'PSS/E load model has no reviewed native binding: ' + load_model_name,
                    )
            elif record.status != RecordStatus.VALID or number is None or binding is None:
                context.record(document.source,record.line_number,PsseFileType.DYR,
                    PsseConversionStatus.INVALID if record.status == RecordStatus.INVALID else PsseConversionStatus.UNSUPPORTED,
                    (), 'DYR record has no complete reviewed native model binding: '+record.model)
                if record.target_kind == EquipmentKind.MACHINE and number is not None and record.equipment_id is not None:
                    unresolved_machines.add((number,record.equipment_id.strip()))
                elif isinstance(record.identifier,int):
                    unresolved_buses.add(record.identifier)
                else:
                    pass
            else:
                key: tuple[int,str] = (number,(record.equipment_id or '1').strip())
                assignments.setdefault(key,list()).append((document.source,record))
                if dynamic_record_name(record) in ('CCOMP4A', 'CCOMP4U1') and len(record.icons) == 6:
                    cross_machine_keys.add(key)
                    for icon_index in (0, 2, 4):
                        cross_machine_keys.add((int(record.icons[icon_index]), str(record.icons[icon_index + 1]).strip()))
                elif dynamic_record_name(record) == 'COMPCC' and len(record.icons) == 1:
                    cross_machine_keys.add(key)
                    cross_machine_keys.add((number, str(record.icons[0]).strip()))
                else:
                    pass
        for tokens in document.rejected:
            context.record(document.source,0,PsseFileType.DYR,PsseConversionStatus.INVALID,(), 'Malformed DYR record retained in source document')
            if tokens:
                try:
                    rejected_bus: int | None = context.bus_number(BusIdentifier(None,tokens[0].text)) if tokens[0].quoted else int(tokens[0].text)
                except ValueError:
                    rejected_bus = None
                if rejected_bus is not None:
                    unresolved_buses.add(rejected_bus)
                else:
                    rejected_sources.add(document.source)
            else:
                rejected_sources.add(document.source)
    renewable_keys: list[tuple[int, str]] = list()
    dera_keys: list[tuple[int, str]] = list()
    ordinary_keys: list[tuple[int, str]] = list()
    cross_current_keys: list[tuple[int, str]] = list()
    for assignment_key, assignment_records in assignments.items():
        has_cross_current: bool = any(
            dynamic_record_name(assignment_record) in ('CCOMP4A', 'CCOMP4U1', 'COMPCC')
            for _, assignment_record in assignment_records
        )
        if has_cross_current:
            cross_current_keys.append(assignment_key)
        else:
            ordinary_keys.append(assignment_key)
        if any(
                dynamic_record_name(assignment_record) == 'DERA1'
                for _, assignment_record in assignment_records):
            dera_keys.append(assignment_key)
        else:
            pass
    ordered_keys: list[tuple[int, str]] = ordinary_keys + cross_current_keys
    for key in ordered_keys:
        records: list[tuple[str, DyrRecord]] = assignments[key]
        contains_converter: bool = False
        for _, record in records:
            candidate_binding: PsseDynamicBinding | None = dynamic_binding(dynamic_record_name(record))
            if candidate_binding is not None and candidate_binding.role == PsseDynamicRole.RENEWABLE_CONVERTER:
                contains_converter = True
            else:
                pass
        if contains_converter:
            renewable_keys.append(key)
        else:
            pass
    for key in renewable_keys:
        renewable_records: list[tuple[str, DyrRecord]] = assignments.pop(key)
        _convert_renewable_assembly(
            context, key, renewable_records, unresolved_buses, unresolved_machines,
        )
    for key in dera_keys:
        dera_records: list[tuple[str, DyrRecord]] = assignments.pop(key)
        _convert_dera1_assembly(
            context, key, dera_records, unresolved_buses, unresolved_machines,
        )
    ordinary_keys = list()
    cross_current_keys = list()
    for assignment_key, assignment_records in assignments.items():
        has_cross_current = any(
            dynamic_record_name(assignment_record) in ('CCOMP4A', 'CCOMP4U1', 'COMPCC')
            for _, assignment_record in assignment_records
        )
        if has_cross_current:
            cross_current_keys.append(assignment_key)
        else:
            ordinary_keys.append(assignment_key)
    ordered_keys = ordinary_keys + cross_current_keys
    for key in ordered_keys:
        records: list[tuple[str, DyrRecord]] = assignments[key]
        generator: Generator | None = context.generators.get(key,None)
        raw: RawGeneratorLike | None = context.raw_generators.get(key,None)
        roles: dict[PsseDynamicRole,list[tuple[str,DyrRecord]]] = dict()
        for source, record in records:
            binding = dynamic_binding(dynamic_record_name(record))
            if binding is not None:
                roles.setdefault(binding.role,list()).append((source,record))
            else:
                pass
        machines: list[tuple[str,DyrRecord]] = roles.get(PsseDynamicRole.MACHINE,list())
        complete: bool = generator is not None and raw is not None and raw.MBASE > 0 and not raw.XT and context.grid.Sbase > 0 and len(machines) == 1 and key[0] not in unresolved_buses and key not in unresolved_machines and all(len(items)==1 for items in roles.values()) and all(source not in rejected_sources for source, _ in records)
        if not complete:
            for source, record in records:
                context.record(source,record.line_number,PsseFileType.DYR,PsseConversionStatus.UNRESOLVED,(), 'DYR assembly has missing/ambiguous host, competing models, unsupported neighboring records, or invalid MBASE')
        else:
            source, record = machines[0]
            vf: VarFactory = context.grid.var_factory
            ratio: float = raw.MBASE/context.grid.Sbase
            name: str = 'PSSE_'+str(key[0])+'_'+key[1]+'_'+record.model.upper()
            assignment_attempted: bool = False
            original_runtime: Block = generator.rms_model
            try:
                for _, candidate in records:
                    validate_dynamic_parameters(candidate)
                model: str = dynamic_record_name(record)
                template: RmsModelTemplate
                if model in ('CIMTR1', 'CIMTR2', 'CIMTR3', 'CIMTR4'):
                    if len(records) != 1:
                        raise ValueError('CIMTR models cannot be combined with standard governor or controller records')
                    else:
                        pass
                    template = build_cimtr_source_template(
                        context=context, record=record, raw=raw, name=name,
                        base_ratio=ratio,
                    )
                elif model == 'GENCLS':
                    governor_records: list[tuple[str,DyrRecord]] = roles.get(PsseDynamicRole.GOVERNOR,list())
                    tgov: bool = bool(governor_records) and governor_records[0][1].model.upper() == 'TGOV1'
                    if governor_records and not tgov:
                        raise ValueError('GENCLS currently supports only the TGOV1 governor assembly')
                    else:
                        pass
                    template = get_complete_gencls_rms_template(vf, GenclsMechanicalInput.TGOV1 if tgov else GenclsMechanicalInput.CONSTANT, name)
                    configure_gencls_block(template.block.children[0], GenclsRmsParameters(context.grid.fBase,
                        named_parameter(record,'D')*ratio,2*named_parameter(record,'H')*ratio,
                        raw.ZR/ratio,raw.ZX/ratio),vf)
                elif model in ('GENROU','GENROE'):
                    saturation: GenrouSaturationMode
                    if named_parameter(record,'S10') == 0 and named_parameter(record,'S12') == 0:
                        saturation = GenrouSaturationMode.DISABLED
                    elif model == 'GENROE':
                        saturation = GenrouSaturationMode.POWER_LAW
                    else:
                        saturation = GenrouSaturationMode.QUADRATIC
                    template = get_genrou_rms_template(vf,name,saturation)
                    configure_genrou_block(template.block.children[0],GenrouRmsParameters(context.grid.fBase,
                        named_parameter(record,'D')*ratio,2*named_parameter(record,'H')*ratio,raw.ZR/ratio,
                        named_parameter(record,'Xl')/ratio,named_parameter(record,'Xd1')/ratio,
                        named_parameter(record,'S10'),named_parameter(record,'S12'),named_parameter(record,'Xd')/ratio,
                        named_parameter(record,'Xq')/ratio,named_parameter(record,'Xd2')/ratio,named_parameter(record,'Xq1')/ratio,
                        named_parameter(record,'Xd2')/ratio,named_parameter(record,'Tdo1'),named_parameter(record,'Tdo2'),
                        named_parameter(record,'Tqo1'),named_parameter(record,'Tqo2')),vf)
                elif model == 'GENSAE':
                    template = build_gensae_template(vf,name,frequency=context.grid.fBase,
                        damping=named_parameter(record,'D')*ratio, inertia=2*named_parameter(record,'H')*ratio,
                        resistance=raw.ZR/ratio, leakage=named_parameter(record,'Xl')/ratio,
                        xd_transient=named_parameter(record,'Xd1')/ratio,
                        saturation1=named_parameter(record,'S10'), saturation12=named_parameter(record,'S12'),
                        xd=named_parameter(record,'Xd')/ratio, xq=named_parameter(record,'Xq')/ratio,
                        x_subtransient=named_parameter(record,'Xd2')/ratio,
                        td_transient=named_parameter(record,'Tdo1'), td_subtransient=named_parameter(record,'Tdo2'),
                        tq_subtransient=named_parameter(record,'Tqo2'))
                elif model == 'GENTRA':
                    # AF relaxes the source network iteration; the native coupled DAE
                    # has no corresponding physical parameter to alter.
                    template = build_gentra_template(vf,name,context.grid.fBase,
                        named_parameter(record,'H')*ratio,named_parameter(record,'D')*ratio,
                        raw.ZR/ratio,named_parameter(record,'Xd')/ratio,
                        named_parameter(record,'Xq')/ratio,named_parameter(record,'Xd1')/ratio,
                        named_parameter(record,'Tdo1'),named_parameter(record,'S10'),named_parameter(record,'S12'))
                else:
                    template = build_gensal_network(vf,record,name,ratio,raw.ZR,context.grid.fBase)
                machine: Block = template.block.children[0]
                if key in cross_machine_keys:
                    add_terminal_current_signals(template, machine, vf, key)
                else:
                    pass
                compensator_records: list[tuple[str,DyrRecord]] = roles.get(PsseDynamicRole.COMPENSATOR,list())
                compensator_block: Block | None = None
                if compensator_records:
                    if model == 'GENCLS' or not roles.get(PsseDynamicRole.EXCITER,list()):
                        raise ValueError('Voltage compensation requires a machine with an explicit exciter')
                    else:
                        compensator_record: DyrRecord = compensator_records[0][1]
                        compensator_binding: PsseDynamicBinding | None = dynamic_binding(
                            dynamic_record_name(compensator_record)
                        )
                        if compensator_binding is not None:
                            compensator_name: str = (
                                name + '_CCOMP4A' if dynamic_record_name(compensator_record) == 'CCOMP4U1'
                                else name + '_' + dynamic_record_name(compensator_record)
                            )
                            compensator_template: RmsModelTemplate = build_controller(compensator_record,compensator_binding,vf,
                                compensator_name,ratio)
                            compensator_block = attach_compensator(context,template,machine,compensator_template,compensator_record,ratio)
                        else:
                            raise ValueError('Voltage compensator binding disappeared')
                else:
                    pass
                stabilizer_records: list[tuple[str,DyrRecord]] = roles.get(PsseDynamicRole.STABILIZER,list())
                stabilizer_block: Block | None = None
                if stabilizer_records:
                    if model == 'GENCLS' or not roles.get(PsseDynamicRole.EXCITER,list()):
                        raise ValueError('Supplementary voltage control requires a machine with an explicit exciter')
                    else:
                        stabilizer_record: DyrRecord = stabilizer_records[0][1]
                        stabilizer_binding: PsseDynamicBinding | None = dynamic_binding(
                            dynamic_record_name(stabilizer_record))
                        if stabilizer_binding is not None:
                            stabilizer_template: RmsModelTemplate = build_controller(stabilizer_record,stabilizer_binding,vf,
                                name+'_'+stabilizer_record.model.upper(),ratio)
                            stabilizer_block = attach_stabilizer(context,template,machine,stabilizer_template,
                                stabilizer_record,vf,ratio,compensator_block)
                        else:
                            raise ValueError('Stabilizer binding disappeared')
                else:
                    pass
                underexcitation_records: list[tuple[str,DyrRecord]] = roles.get(PsseDynamicRole.UNDEREXCITATION,list())
                underexcitation_block: Block | None = None
                if underexcitation_records:
                    if model == 'GENCLS' or not roles.get(PsseDynamicRole.EXCITER,list()):
                        raise ValueError('Minimum-excitation limiting requires a machine with an explicit exciter')
                    else:
                        underexcitation_record: DyrRecord = underexcitation_records[0][1]
                        if dynamic_record_name(underexcitation_record) == 'UEL2C':
                            exciter_records: list[tuple[str,DyrRecord]] = roles.get(PsseDynamicRole.EXCITER,list())
                            if len(exciter_records) != 1 or dynamic_record_name(exciter_records[0][1]) != 'ST7C':
                                raise ValueError('PSS/E UEL2C requires the documented ST7C feedback host')
                            else:
                                pass
                        else:
                            pass
                        underexcitation_binding: PsseDynamicBinding | None = dynamic_binding(underexcitation_record.model)
                        if underexcitation_binding is not None:
                            underexcitation_template: RmsModelTemplate = build_controller(underexcitation_record,underexcitation_binding,vf,
                                name+'_'+underexcitation_record.model.upper(),ratio)
                            underexcitation_block = attach_underexcitation(template,machine,underexcitation_template,
                                underexcitation_record,vf,ratio)
                        else:
                            raise ValueError('Minimum-excitation binding disappeared')
                else:
                    pass
                overexcitation_records: list[tuple[str,DyrRecord]] = roles.get(PsseDynamicRole.OVEREXCITATION,list())
                overexcitation_block: Block | None = None
                overexcitation_record: DyrRecord | None = None
                if overexcitation_records:
                    exciters: list[tuple[str,DyrRecord]] = roles.get(PsseDynamicRole.EXCITER,list())
                    if (model == 'GENCLS' or len(exciters) != 1
                            or dynamic_record_name(exciters[0][1]) not in ('AC6A','ESAC6A')
                            or dynamic_record_name(overexcitation_records[0][1]) not in ('OEL2C','MAXEX1','MAXEX2')):
                        raise ValueError('OEL2C, MAXEX1 and MAXEX2 currently require an explicit AC6A or ESAC6A exciter')
                    else:
                        overexcitation_record = overexcitation_records[0][1]
                        overexcitation_binding: PsseDynamicBinding | None = dynamic_binding(overexcitation_record.model)
                        if overexcitation_binding is not None:
                            overexcitation_template: RmsModelTemplate = build_controller(
                                overexcitation_record, overexcitation_binding, vf,
                                name + '_OEL2C', ratio)
                            overexcitation_block = overexcitation_template.block
                        else:
                            raise ValueError('Over-excitation binding disappeared')
                else:
                    pass
                # GENCLS's optional governor was precomposed; configure it exactly once.
                load_records: list[tuple[str,DyrRecord]] = roles.get(PsseDynamicRole.TURBINE_LOAD_CONTROLLER,list())
                load_block: Block | None = None
                if load_records:
                    governed: list[tuple[str,DyrRecord]] = roles.get(PsseDynamicRole.GOVERNOR,list())
                    if model == 'GENCLS' or len(governed) != 1 or governed[0][1].model.upper() != 'IEEEG1':
                        raise ValueError('Reviewed outer load control currently requires a field-dynamic machine and a single-shaft IEEEG1 governor')
                    else:
                        load_record: DyrRecord = load_records[0][1]
                        load_binding: PsseDynamicBinding | None = dynamic_binding(load_record.model)
                        if load_binding is None:
                            raise ValueError('Turbine load-controller binding disappeared')
                        else:
                            load_template: RmsModelTemplate = build_controller(load_record,load_binding,vf,name+'_LCFB1',ratio)
                            load_block = load_template.block
                            for port in load_block.in_vars:
                                load_block.init_eqs.pop(port,None)
                            vf.add_connection(load_block.in_vars[0],machine.out_vars[2])
                            connect_scaled(template.block,load_block.in_vars[1],machine.out_vars[0],1.0/ratio,vf)
                            freeze_input(load_block,load_block.in_vars[3],vf,machine.out_vars[0]/Const(ratio))
                            template.block.children.append(load_block)
                else:
                    pass
                for role in (PsseDynamicRole.GOVERNOR,PsseDynamicRole.EXCITER):
                    controllers: list[tuple[str,DyrRecord]] = roles.get(role,list())
                    if controllers:
                        controller_record: DyrRecord = controllers[0][1]
                        binding = dynamic_binding(dynamic_record_name(controller_record))
                        if model == 'GENCLS' and role == PsseDynamicRole.EXCITER:
                            raise ValueError('GENCLS has a constant internal emf and cannot host an exciter')
                        else:
                            pass
                        if model == 'GENCLS' and controller_record.model.upper() == 'TGOV1':
                            governor: Block = template.block.children[1]
                            configure_tgov1_block(governor,Tgov1RmsParameters(1.0,named_parameter(controller_record,'R')/ratio,
                                named_parameter(controller_record,'VMAX')*ratio,named_parameter(controller_record,'VMIN')*ratio,
                                named_parameter(controller_record,'T1'),named_parameter(controller_record,'T2'),named_parameter(controller_record,'T3'),named_parameter(controller_record,'Dt')*ratio),vf)
                        elif binding is not None:
                            controller: RmsModelTemplate = build_controller(
                                controller_record, binding, vf,
                                name + '_' + dynamic_record_name(controller_record), ratio,
                                context.grid.Sbase, context.grid.fBase,
                            )
                            attach_controller(template,machine,controller,controller_record,vf,ratio,context.grid.Sbase,
                                stabilizer_block,compensator_block,underexcitation_block,load_block,
                                overexcitation_block,overexcitation_record)
                        else:
                            raise ValueError('Controller binding disappeared')
                    elif model not in ('GENCLS', 'CIMTR1', 'CIMTR2', 'CIMTR3', 'CIMTR4'):
                        port: Var = machine.in_vars[2] if role == PsseDynamicRole.GOVERNOR else machine.in_vars[3]
                        freeze_input(machine,port,vf)
                    else:
                        pass
                # No implicit replacement of a pre-existing user/native dynamic model.
                if generator.rms_template is not None or generator.rms_fmu_template is not None:
                    raise ValueError('Generator already has an RMS model assignment')
                else:
                    pass
                assignment_attempted = True
                generator.rms_template = template
                context.grid.add_rms_model(template)
                for source, applied in records:
                    context.record(source,applied.line_number,PsseFileType.DYR,PsseConversionStatus.CONVERTED,
                        (generator,template),'Applied '+applied.model+' through a parameterized native RMS assembly')
            except (ValueError,KeyError,IndexError) as error:
                if assignment_attempted:
                    generator.rms_template = None
                    generator.rms_model = original_runtime
                else:
                    pass
                for source, failed in records:
                    context.record(source,failed.line_number,PsseFileType.DYR,PsseConversionStatus.UNSUPPORTED,
                        (generator,),'DYR assembly not activated: '+str(error))
    wire_cross_machine_compensators(context)
