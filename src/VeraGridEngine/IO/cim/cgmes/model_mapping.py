# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""CGMES equation-source crosswalk to existing RMS international models."""

from typing import Dict


def get_cgmes_rms_equation_sources() -> Dict[str, str]:
    """Return the proven RMS equation sources adapted by CGMES template builders.

    :return: CGMES class names mapped to RMS model paths or reusable equation modules.
    """
    return {
        'AsynchronousMachineTimeConstantReactance': 'common.auxiliary_functions.build_induction_machine',
        'AsynchronousMachineEquivalentCircuit': 'common.auxiliary_functions.build_induction_machine (EA912 parameter conversion)',
        'ExcNI': 'excitation_systems.exni',
        'ExcSCRX': 'excitation_systems.scrx',
        'ExcIEEEST4B': 'excitation_systems.st4b',
        'ExcIEEEST5B': 'excitation_systems.st5b',
        'ExcIEEEST7B': 'excitation_systems.st7b',
        'ExcIEEEST2A': 'excitation_systems.exst2',
        'GovCT1': 'governors.ggov1',
        'GovCT2': 'governors.ggov1',
        'GovGAST': 'governors.gast',
        'GovHydroPID2': 'governors.pidgov',
        'GovSteam1': 'governors.govsteam1',
        'GovSteamEU': 'governors.govsteameu',
        'GovSteamIEEE1': 'governors.ieeeg1',
        'LoadMotor': 'international_standards.induction_machines.load_motor.build_load_motor_template (shared induction equations)',
        'WindPitchContEmulIEC': 'IEC 61400-27-1:2015 §6.6.5.1 Figure 7.11',
        'PssIEEE1A': 'power_system_stabilizers.ieeest (shared stages)',
        'PssIEEE2B': 'power_system_stabilizers.pss2b (shared equation builder)',
        'PssIEEE3B': 'power_system_stabilizers.ieeest (shared stages)',
        'PssPTIST3': 'power_system_stabilizers.ieeest (shared filters)',
        'PssSTAB2A': 'power_system_stabilizers.stab2a (shared equation builder)',
    }
