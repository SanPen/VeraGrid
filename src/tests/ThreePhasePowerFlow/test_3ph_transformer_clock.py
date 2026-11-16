# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import numpy as np
import pytest
import VeraGridEngine.api as vge

from VeraGridEngine.basic_structures import Logger, CxMat, CxVec
from VeraGridEngine.Devices.Branches.transformer import Transformer2W
from VeraGridEngine.Devices.Branches.transformer_type import TransformerType
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.enumerations import WindingType


@pytest.mark.parametrize('connections', (
    (WindingType.GroundedStar, WindingType.GroundedStar),
    (WindingType.NeutralStar, WindingType.NeutralStar),
    (WindingType.GroundedStar, WindingType.Delta),
    (WindingType.Delta, WindingType.GroundedStar),
    (WindingType.NeutralStar, WindingType.Delta),
    (WindingType.Delta, WindingType.NeutralStar),
    (WindingType.Delta, WindingType.Delta),
))
@pytest.mark.parametrize('clock', range(12))
@pytest.mark.parametrize('reverse', (False, True))
def test_clock_no_load_sequences(connections: tuple[WindingType, WindingType],
                                 clock: int, reverse: bool) -> None:
    """Check both port currents for the specified no-load voltage ratio.

    :param connections: HV and LV winding connections
    :param clock: HV-to-LV displacement in units of 30 degrees
    :param reverse: Connect the LV winding at the from terminal
    :return: None
    """
    bus_hv: Bus = Bus(Vnom=132.0)
    bus_lv: Bus = Bus(Vnom=33.0)
    tr: Transformer2W = Transformer2W(
        bus_from=bus_lv if reverse else bus_hv,
        bus_to=bus_hv if reverse else bus_lv,
        HV=132.0, LV=33.0, r=0.01, x=0.1, tap_module=1.07, tap_phase=0.08)
    tr.conn_f, tr.conn_t = connections[::-1] if reverse else connections
    tr.vector_group_number = clock
    logger: Logger = Logger()
    yff, yft, ytf, ytt = tr.transformer_admittance(1.1, 0.97, logger)
    assert not logger.has_logs()

    # The clock rotates positive and negative sequences in opposite directions;
    # the existing tap phase and virtual tap ratio remain independent of it.
    phase: float = np.deg2rad(30.0 * clock) * (-1 if reverse else 1)
    a: complex = np.exp(2j * np.pi / 3)
    sequences: CxMat = np.array(((0, 1, a * a, a), (0, 1, a, a * a)))
    for sequence, sign in zip(sequences, (1, -1)):
        target: CxVec = sequence * (0.97 / (1.07 * 1.1)) * np.exp(-1j * (0.08 + sign * phase))
        np.testing.assert_allclose(yff @ sequence + yft @ target, 0.0, atol=1e-13)
        np.testing.assert_allclose(ytf @ sequence + ytt @ target, 0.0, atol=1e-13)

    # A clock change must neither open nor create a homopolar/neutral path.
    tr.vector_group_number = 0
    zero_clock: tuple = tr.transformer_admittance(1.1, 0.97, logger)
    homopolar: CxVec = np.array((0, 1, 1, 1), dtype=complex)
    for actual, original in zip((yff, yft, ytf, ytt), zero_clock):
        np.testing.assert_allclose(actual @ homopolar, original @ homopolar, atol=1e-13)
        np.testing.assert_array_equal(actual[0, :], original[0, :])
        np.testing.assert_array_equal(actual[:, 0], original[:, 0])
    np.testing.assert_array_equal(yff, zero_clock[0])
    np.testing.assert_array_equal(ytt, zero_clock[3])


@pytest.mark.parametrize('reverse', (False, True))
def test_transformer_template_copies_clock(reverse: bool) -> None:
    """Apply the catalogue clock alongside its winding connections.

    :param reverse: Connect LV at the from terminal
    :return: None
    """
    hv: Bus = Bus(Vnom=132.0)
    lv: Bus = Bus(Vnom=33.0)
    tr: Transformer2W = Transformer2W(bus_from=lv if reverse else hv, bus_to=hv if reverse else lv)
    template: TransformerType = TransformerType(hv_nominal_voltage=132.0, lv_nominal_voltage=33.0)
    template.conn_hv = WindingType.Delta
    template.conn_lv = WindingType.GroundedStar
    template.vector_group_number = 11
    tr.apply_template(template, Sbase=100.0)
    assert tr.vector_group_number == 11
    assert (tr.conn_f, tr.conn_t) == ((template.conn_lv, template.conn_hv) if reverse
                                    else (template.conn_hv, template.conn_lv))


def test_fortescue_existing_import_is_preserved() -> None:
    """Keep the historical numerical-method import available to existing callers.

    :return: None
    """
    from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions import fortescue_012_to_abc
    from VeraGridEngine.Utils.NumericalMethods.common import fortescue_012_to_abc as shared_fortescue
    assert fortescue_012_to_abc is shared_fortescue


@pytest.mark.parametrize('clock', (1, 11))
def test_clock_loaded_power_flow(clock: int) -> None:
    """A balanced load keeps its powers and magnitudes when the clock rotates it.

    :param clock: Lagging or leading clock
    :return: None
    """
    grid: vge.MultiCircuit = vge.MultiCircuit()
    source: Bus = grid.add_bus(Bus(Vnom=132.0, is_slack=True))
    target: Bus = grid.add_bus(Bus(Vnom=33.0))
    grid.add_generator(source, vge.Generator())
    grid.add_load(target, vge.Load(P=12.0, Q=3.0, P1=4.0, P2=4.0, P3=4.0,
                                   Q1=1.0, Q2=1.0, Q3=1.0))
    tr: Transformer2W = Transformer2W(bus_from=source, bus_to=target, HV=132.0, LV=33.0,
                                      r=0.01, x=0.1)
    tr.conn_f = WindingType.Delta
    tr.conn_t = WindingType.GroundedStar
    grid.add_transformer2w(tr)
    options: vge.PowerFlowOptions = vge.PowerFlowOptions(tolerance=1e-10, max_iter=100,
                                                         control_taps_modules=False,
                                                         control_taps_phase=False)
    reference: vge.PowerFlowResults3Ph = vge.power_flow3ph(grid, options)
    tr.vector_group_number = clock
    shifted: vge.PowerFlowResults3Ph = vge.power_flow3ph(grid, options)
    assert reference.converged and shifted.converged
    v_reference: CxVec = np.array((reference.voltage_A[1], reference.voltage_B[1], reference.voltage_C[1]))
    v_shifted: CxVec = np.array((shifted.voltage_A[1], shifted.voltage_B[1], shifted.voltage_C[1]))
    np.testing.assert_allclose(v_shifted, v_reference * np.exp(-1j * np.deg2rad(30.0 * clock)), atol=1e-9)
