# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import Tuple
import os.path
import shutil
import packaging.version as pkg
import warnings
from pathlib import Path
from VeraGridEngine.enumerations import (
    TapModuleControl,
    TapPhaseControl,
    BusMode,
    ShuntConnectionType,
    WindingType,
    WindingsConnection,
    HvdcControlType,
    ContingencyMethod,
    ContingencyOperationTypes,
    BuildStatus,
    BranchGroupTypes,
    ConverterControlType
)
GSLV_RECOMMENDED_VERSION: str = "0.7.15"
GSLV_VERSION: str = ''
GSLV_AVAILABLE: bool = False
try:
    import pygslv as pg
    # The wrapper owns the license discovery logic, so activation is centralized here.
    pg.search_license_and_activate(verbose=False)

    # The API exposes license state after activation. The rest of the code only
    # needs one explicit availability flag to decide whether to dispatch to GSLV.
    if not pg.isLicensed():
        GSLV_AVAILABLE = False
    else:
        GSLV_AVAILABLE = True
        GSLV_VERSION = pg.get_version()

    if GSLV_AVAILABLE:
        if pkg.parse(GSLV_VERSION) < pkg.parse(GSLV_RECOMMENDED_VERSION):
            warnings.warn(f"Recommended version for GSLV is {GSLV_RECOMMENDED_VERSION} "
                          f"instead of {GSLV_VERSION}")

    build_status_dict = {
        BuildStatus.Planned: pg.BuildStatus.Planned,
        BuildStatus.Commissioned: pg.BuildStatus.Commissioned,
        BuildStatus.Candidate: pg.BuildStatus.Candidate,
        BuildStatus.Decommissioned: pg.BuildStatus.Decommissioned,
        BuildStatus.PlannedDecommission: pg.BuildStatus.PlannedDecommission,
    }

    tap_module_control_mode_dict = {
        TapModuleControl.fixed: pg.TapModuleControl.fixed,
        TapModuleControl.Qf: pg.TapModuleControl.Qf,
        TapModuleControl.Qt: pg.TapModuleControl.Qt,
        TapModuleControl.Vm: pg.TapModuleControl.Vm,
    }

    tap_phase_control_mode_dict = {
        TapPhaseControl.fixed: pg.TapPhaseControl.fixed,
        TapPhaseControl.Pf: pg.TapPhaseControl.Pf,
        TapPhaseControl.Pt: pg.TapPhaseControl.Pt,
    }

    hvdc_control_mode_dict = {
        HvdcControlType.type_0_free: pg.HvdcControlType.type_0_free,
        HvdcControlType.type_1_Pset: pg.HvdcControlType.type_1_Pset,
    }

    group_type_dict = {
        BranchGroupTypes.GenericGroup: pg.BranchGroupTypes.GenericGroup,
        BranchGroupTypes.TransformerGroup: pg.BranchGroupTypes.TransformerGroup,
        BranchGroupTypes.LineSegmentsGroup: pg.BranchGroupTypes.LineSegmentsGroup,
    }

    contingency_ops_type_dict = {
        ContingencyOperationTypes.Active: pg.ContingencyOperationTypes.Active,
        ContingencyOperationTypes.PowerPercentage: pg.ContingencyOperationTypes.PowerPercentage,
    }

    contingency_method_dict = {
        ContingencyMethod.Linear: pg.ContingencyMethod.PTDF,
        ContingencyMethod.PowerFlow: pg.ContingencyMethod.PowerFlow,
        ContingencyMethod.HELM: pg.ContingencyMethod.HELM,
    }

    converter_control_type_dict = {
        ConverterControlType.Vm_dc: pg.ConverterControlType.Vm_dc,
        ConverterControlType.Vm_ac: pg.ConverterControlType.Vm_ac,
        ConverterControlType.Va_ac: pg.ConverterControlType.Va_ac,
        ConverterControlType.Qac: pg.ConverterControlType.Q_ac,
        ConverterControlType.Pdc: pg.ConverterControlType.P_dc,
        ConverterControlType.Pac: pg.ConverterControlType.P_ac,
    }

    bus_type_dict = {
        BusMode.PQ_tpe.value: pg.BusMode.PQ,
        BusMode.PV_tpe.value: pg.BusMode.PV,
        BusMode.Slack_tpe.value: pg.BusMode.Slack,
        BusMode.P_tpe.value: pg.BusMode.P,
        BusMode.PQV_tpe.value: pg.BusMode.PQV,
    }

    shunt_connection_type_dict = {
        ShuntConnectionType.GroundedStar: pg.ShuntConnectionType.GroundedStar,
        ShuntConnectionType.FloatingStar: pg.ShuntConnectionType.FloatingStar,
        ShuntConnectionType.NeutralStar: pg.ShuntConnectionType.NeutralStar,
        ShuntConnectionType.Delta: pg.ShuntConnectionType.Delta,
    }

    winding_type_dict = {
        WindingType.GroundedStar: pg.WindingType.GroundedStar,
        WindingType.NeutralStar: pg.WindingType.NeutralStar,
        WindingType.Delta: pg.WindingType.Delta,
        WindingType.ZigZag: pg.WindingType.ZigZag,
    }

    windings_connection_dict = {
        WindingsConnection.GG: pg.WindingsConnection.GG,
        WindingsConnection.GS: pg.WindingsConnection.GS,
        WindingsConnection.GD: pg.WindingsConnection.GD,
        WindingsConnection.SS: pg.WindingsConnection.SS,
        WindingsConnection.SD: pg.WindingsConnection.SD,
        WindingsConnection.DD: pg.WindingsConnection.DD,
    }

except ImportError:
    pg = None
    GSLV_AVAILABLE = False
    GSLV_VERSION = ''

    build_status_dict = dict()
    tap_module_control_mode_dict = dict()
    tap_phase_control_mode_dict = dict()
    hvdc_control_mode_dict = dict()
    group_type_dict = dict()
    contingency_ops_type_dict = dict()
    contingency_method_dict = dict()
    converter_control_type_dict = dict()
    bus_type_dict = dict()
    shunt_connection_type_dict = dict()
    winding_type_dict = dict()
    windings_connection_dict = dict()


def install_gslv_license(fname: str) -> Tuple[bool, str]:
    """
    Copy one GSLV license file into VeraGrid's managed folder.

    :param fname: Source license file path.
    :return: Success flag and status message.
    """

    if os.path.exists(fname):
        # The license must live inside VeraGrid's managed folder so the wrapper
        # can discover it consistently on later runs.
        folder: str = os.path.join(str(Path.home()), '.VeraGrid')
        if os.path.exists(folder):
            pass
        else:
            os.makedirs(folder)

        name = os.path.basename(fname)
        dst = os.path.join(folder, name)
        shutil.copyfile(fname, dst)
        return True, "License installed!"
    else:
        return False, "The file does not exists :("
