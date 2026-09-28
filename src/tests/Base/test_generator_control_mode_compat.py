from __future__ import annotations

import numpy as np

from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.enumerations import BusMode, GeneratorControlMode


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


def test_generator_control_mode_profile_returns_profile_and_snapshot_values() -> None:
    gen: Generator = Generator(control_mode=GeneratorControlMode.Q)
    gen.control_mode_prof = np.array(
        [GeneratorControlMode.V, GeneratorControlMode.QVDroop],
        dtype=object,
    )

    assert gen.get_control_mode_prof_at(0) == GeneratorControlMode.V
    assert gen.get_control_mode_prof_at(1) == GeneratorControlMode.QVDroop
    assert gen.get_control_mode_prof_at(None) == GeneratorControlMode.Q


def test_generator_control_mode_profile_is_used_by_compiler() -> None:
    grid: MultiCircuit = MultiCircuit()
    bus: Bus = grid.add_bus(Bus(name="Bus"))
    generator: Generator = Generator(control_mode=GeneratorControlMode.Q)
    generator.control_mode_prof = np.array(
        [GeneratorControlMode.V, GeneratorControlMode.QVDroop],
        dtype=object,
    )
    grid.add_generator(bus=bus, api_obj=generator)

    numerical_circuit_t0 = compile_numerical_circuit_at(circuit=grid, t_idx=0)
    numerical_circuit_t1 = compile_numerical_circuit_at(circuit=grid, t_idx=1)

    assert numerical_circuit_t0.generator_data.control_mode_int[0] == GeneratorControlMode.V.idx()
    assert numerical_circuit_t1.generator_data.control_mode_int[0] == GeneratorControlMode.QVDroop.idx()
    assert numerical_circuit_t0.bus_data.bus_types[0] == BusMode.PV_tpe.value
    assert numerical_circuit_t1.bus_data.bus_types[0] == BusMode.PQ_tpe.value
