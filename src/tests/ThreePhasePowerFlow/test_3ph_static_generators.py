import numpy as np
import pytest

from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.Devices.Injections.static_generator import StaticGenerator
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.basic_structures import CxVec
from VeraGridEngine.enumerations import ShuntConnectionType


@pytest.mark.parametrize("connection", (ShuntConnectionType.GroundedStar, ShuntConnectionType.Delta))
@pytest.mark.parametrize("t_idx", (None, 0))
@pytest.mark.parametrize(
    "phase_powers, expected_snapshot, expected_profile",
    (
        ((0j, 0j, 0j), (4 + 2j, 4 + 2j, 4 + 2j), (6 + 3j, 6 + 3j, 6 + 3j)),
        ((1j, 0j, -1j), (4 + 1j, 4 + 0j, 4 - 1j), (6 + 2j, 6 + 0j, 6 - 2j)),
        ((1 + 0j, 0j, -1 + 0j), (1 + 2j, 2j, -1 + 2j), (2 + 3j, 3j, -2 + 3j)),
        ((1 + 1j, 0j, -1 - 1j), (1 + 1j, 0j, -1 - 1j), (2 + 2j, 0j, -2 - 2j)),
    ),
)
def test_static_generator_phase_power_compilation(
    connection: ShuntConnectionType,
    t_idx: int | None,
    phase_powers: tuple[complex, complex, complex],
    expected_snapshot: tuple[complex, complex, complex],
    expected_profile: tuple[complex, complex, complex],
) -> None:
    """
    Preserve explicit phases and distribute missing P/Q without crossing device slots.

    :param connection: Supported static-generator connection.
    :param t_idx: Snapshot or profile index to compile.
    :param phase_powers: Snapshot phase powers, including missing or cancelling components.
    :param expected_snapshot: Expected snapshot phase powers after fallback.
    :param expected_profile: Expected profile phase powers after fallback.
    :return: None.
    """
    grid: MultiCircuit = MultiCircuit()
    bus: Bus = Bus(name="Slack", Vnom=10.0, is_slack=True)
    grid.add_bus(bus)

    # A preceding load and another generator expose writes into neighbouring NABC blocks.
    load: Load = Load(P=9.0, Q=3.0)
    grid.add_load(bus=bus, api_obj=load)
    generator: StaticGenerator = StaticGenerator(
        P=12.0, Q=6.0,
        P1=phase_powers[0].real, P2=phase_powers[1].real, P3=phase_powers[2].real,
        Q1=phase_powers[0].imag, Q2=phase_powers[1].imag, Q3=phase_powers[2].imag,
    )
    generator.conn = connection
    grid.add_static_generator(bus=bus, api_obj=generator)
    other_generator: StaticGenerator = StaticGenerator(
        P=6.0, Q=12.0, P1=1.0, P2=2.0, P3=3.0, Q1=2.0, Q2=4.0, Q3=6.0,
    )
    other_generator.conn = connection
    grid.add_static_generator(bus=bus, api_obj=other_generator)

    # Different profile totals and phase values detect accidental snapshot reads.
    profile_phases: CxVec = 2.0 * np.array(phase_powers, dtype=complex)
    generator.P_prof = np.array((18.0,))
    generator.Q_prof = np.array((9.0,))
    generator.Pa_prof = np.array((profile_phases[0].real,))
    generator.Pb_prof = np.array((profile_phases[1].real,))
    generator.Pc_prof = np.array((profile_phases[2].real,))
    generator.Qa_prof = np.array((profile_phases[0].imag,))
    generator.Qb_prof = np.array((profile_phases[1].imag,))
    generator.Qc_prof = np.array((profile_phases[2].imag,))

    expected_phases: tuple[complex, complex, complex] = expected_snapshot if t_idx is None else expected_profile
    expected_total: complex = 12 + 6j if t_idx is None else 18 + 9j
    expected_star: CxVec = np.array((0j, 3 + 1j, 3 + 1j, 3 + 1j, 0j, 0j, 0j, 0j, 0j, 0j, 0j, 0j))
    expected_delta: CxVec = np.zeros(12, dtype=complex)
    expected_generators: CxVec = np.array((
        0j, -expected_phases[0], -expected_phases[1], -expected_phases[2],
        0j, -1 - 2j, -2 - 4j, -3 - 6j,
    ))
    if connection == ShuntConnectionType.GroundedStar:
        expected_star[4:] = expected_generators
    else:
        expected_delta[4:] = expected_generators

    numerical: NumericalCircuit = compile_numerical_circuit_at(
        circuit=grid, t_idx=t_idx, fill_three_phase=True,
    )

    # Check every slot, including neutral, the other connection and the normal totals.
    np.testing.assert_allclose(numerical.load_data.S3_star, expected_star)
    np.testing.assert_allclose(numerical.load_data.S3_delta, expected_delta)
    np.testing.assert_allclose(numerical.load_data.S, (9 + 3j, -expected_total, -6 - 12j))

    # Compilation must leave both the snapshot and the stored profiles untouched.
    np.testing.assert_allclose(
        (generator.get_Sa_at(None), generator.get_Sb_at(None), generator.get_Sc_at(None)), phase_powers,
    )
    np.testing.assert_allclose(
        (generator.get_Sa_at(0), generator.get_Sb_at(0), generator.get_Sc_at(0)), profile_phases,
    )
    np.testing.assert_allclose(
        (other_generator.Pa, other_generator.Pb, other_generator.Pc), (1.0, 2.0, 3.0),
    )
    np.testing.assert_allclose(
        (other_generator.Qa, other_generator.Qb, other_generator.Qc), (2.0, 4.0, 6.0),
    )
