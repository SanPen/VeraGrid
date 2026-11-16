# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Check connected DERA1 current-control assembly and persistence."""

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.renewable_controls.dera1_controller import (
    build_dera1_controller_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.dera1_protection import (
    Dera1ProtectionSettings,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from tests.symbolic_block_roundtrip import roundtrip_block
from VeraGridEngine.Utils.procedural_logic import (
    DelayedThresholdLatchLogic,
    ProceduralLogicCodec,
    ResetOnRisingEdgeLogic,
)


def test_dera1_controller_assembles_ten_source_states_and_id_iq_outputs() -> None:
    """Connect measurement, controls, relays, current priority, and Tg loops."""
    template = build_dera1_controller_template(
        VarFactory(),
        protection_settings=Dera1ProtectionSettings(
            voltage_trip_enabled=True, frequency_trip_enabled=True,
            vl0=0.5, vl1=0.9, vh1=1.1, vh0=1.5,
            initial_voltage=1.0, initial_frequency_hz=60.0,
        ),
    )
    block: Block = template.block
    assert len(block.in_vars) == 5
    assert len(block.state_vars) == 10
    assert len(block.out_vars) == 2
    assert block.out_vars[0].name.startswith('ActiveCurrentPu_')
    assert block.out_vars[1].name.startswith('ReactiveCurrentPu_')
    assert sum(isinstance(logic, DelayedThresholdLatchLogic)
               for logic in block.procedural_logic) == 6
    assert sum(isinstance(logic, ResetOnRisingEdgeLogic)
               for logic in block.procedural_logic) == 2


def test_dera1_controller_procedural_logic_roundtrips_with_host_remaps() -> None:
    """Preserve all timers and capture logic in a composed native block."""
    template = build_dera1_controller_template(
        VarFactory(),
        protection_settings=Dera1ProtectionSettings(
            voltage_trip_enabled=True, frequency_trip_enabled=True,
            vl0=0.5, vl1=0.9, vh1=1.1, vh0=1.5,
            initial_voltage=1.0, initial_frequency_hz=60.0,
        ),
    )
    restored: Block = roundtrip_block(template.block, ProceduralLogicCodec())
    assert len(restored.procedural_logic) == 8
    assert sum(isinstance(logic, DelayedThresholdLatchLogic)
               for logic in restored.procedural_logic) == 6
    assert sum(isinstance(logic, ResetOnRisingEdgeLogic)
               for logic in restored.procedural_logic) == 2
