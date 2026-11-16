# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""PowerFactory BESS current-reference behavior with the controller disabled."""
from pathlib import Path

import pytest

from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
from VeraGridEngine.IO.dgs.dgs_objects import ElmVscmono
from VeraGridEngine.IO.dgs.dgs_to_blocks import ElmCompInstanceEntry
from VeraGridEngine.IO.dgs.dgs_to_veragrid import dgs_to_circuit
from VeraGridEngine.IO.dgs.dynamic_models.dgs_native_model_workflow import (
    NativeDgsEquipmentKind, NativeDgsEquipmentPlan, _native_vsc_holds_initial_modulation,
)
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import DynamicSimulationMode

DATA = Path(__file__).resolve().parents[2] / 'data/grids/DGS/native_options_pf2024'


@pytest.mark.parametrize('selector,inputs,expected', [
    (0, ['id_ref', 'iq_ref', 'cosref', 'sinref'], True),
    (1, ['id_ref', 'iq_ref'], False),
    (None, ['id_ref', 'iq_ref'], False),
    (0, ['id_ref'], False),
    (0, ['id_ref', 'iq_ref', 'Pmd'], False),
])
def test_modulation_hold_requires_explicit_source_and_current_pair(selector, inputs, expected):
    circuit = DgsCircuit()
    source = ElmVscmono()
    source.ID = 'converter'
    source.i_ctrl = selector
    circuit.elmvscmonos.append(source)
    entry = ElmCompInstanceEntry('slot', 'VSC', 'converter', 'VSC', 'ElmVscmono', 0,
                                None, None, connected_inputs=inputs)
    plan = NativeDgsEquipmentPlan(NativeDgsEquipmentKind.MonopolarVsc, entry)
    assert _native_vsc_holds_initial_modulation(plan, circuit) is expected
    circuit.elmvscmonos.append(source)
    assert not _native_vsc_holds_initial_modulation(plan, circuit)


def test_coupled_bess_resolves_routed_reference_and_holds_initial_modulation():
    logger = Logger()
    grid = dgs_to_circuit(str(DATA / 'bess_coupled_converter.dgs'),
                          use_dynamic_information=True,
                          dynamic_simulation_mode=DynamicSimulationMode.RMS, logger_=logger)
    assert not any(entry.msg == 'DGS dynamic root could not be assembled'
                   and entry.device == 'Grid Forming Converter' for entry in logger.entries)
    held = [entry for entry in logger.entries
            if entry.msg == 'Native VSC modulation held at initialized value (integrated controller disabled)']
    assert {entry.value for entry in held} == {'Pmd', 'Pmq'}
    assert any(entry.msg == 'DGS native equipment constructed and assembled'
               and entry.device == 'Onduleur NIDEC GF' for entry in logger.entries)
    assert len(grid.vsc_devices) == 1
