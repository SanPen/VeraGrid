from __future__ import annotations

from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.enumerations import GeneratorControlMode


def test_generator_control_mode_accepts_legacy_string_values() -> None:
    gen = Generator()

    gen.control_mode = "V"
    assert gen.control_mode == GeneratorControlMode.V

    gen.control_mode = "Q"
    assert gen.control_mode == GeneratorControlMode.Q

    gen.control_mode = "Q-V"
    assert gen.control_mode == GeneratorControlMode.QVDroop


def test_generator_control_mode_accepts_legacy_bool_values() -> None:
    gen = Generator()

    gen.control_mode = True
    assert gen.control_mode == GeneratorControlMode.V

    gen.control_mode = False
    assert gen.control_mode == GeneratorControlMode.Q
