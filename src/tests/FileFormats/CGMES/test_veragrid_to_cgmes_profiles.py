# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Profile-aware CGMES export tests."""

import numpy as np
import pytest

import VeraGridEngine.Devices as dev
from VeraGridEngine.Devices.Branches.tap_changer import TapChanger
from VeraGridEngine.IO.cim.cgmes.cgmes_circuit import CgmesCircuit
from VeraGridEngine.IO.cim.cgmes.veragrid_to_cgmes import get_transformer_tap_values_for_cgmes_export, veragrid_to_cgmes
from VeraGridEngine.data_logger import DataLogger
from VeraGridEngine.enumerations import CGMESVersions, TapChangerTypes


def test_veragrid_to_cgmes_uses_profile_values_when_t_idx_is_provided() -> None:
    """CGMES export must use profile values when ``t_idx`` is provided."""

    grid: dev.MultiCircuit = dev.MultiCircuit(name="cgmes-profile-export")

    bus_1: dev.Bus = dev.Bus(name="B1", Vnom=110.0)
    bus_2: dev.Bus = dev.Bus(name="B2", Vnom=110.0)
    grid.add_bus(bus_1)
    grid.add_bus(bus_2)

    load: dev.Load = dev.Load(name="LD1", P=10.0, Q=5.0, Ir=1.0, Ii=2.0, G=3.0, B=4.0, active=True)
    load.P_prof = np.array([10.0, 20.0])
    load.Q_prof = np.array([5.0, 6.0])
    load.Ir_prof = np.array([1.0, 2.0])
    load.Ii_prof = np.array([2.0, 3.0])
    load.G_prof = np.array([3.0, 4.0])
    load.B_prof = np.array([4.0, 5.0])
    grid.add_load(bus=bus_1, api_obj=load)

    external_grid: dev.ExternalGrid = dev.ExternalGrid(name="EG1", P=30.0, Q=7.0, active=True)
    external_grid.P_prof = np.array([30.0, 40.0])
    external_grid.Q_prof = np.array([7.0, 9.0])
    grid.add_external_grid(bus=bus_1, api_obj=external_grid)

    line: dev.Line = dev.Line(bus_from=bus_1, bus_to=bus_2, name="L12", r=0.01, x=0.05, b=0.001, rate=100.0)
    line.rate_prof = np.array([100.0, 200.0])
    line.contingency_factor_prof = np.array([1.1, 1.2])
    line.protection_rating_factor_prof = np.array([1.3, 1.4])
    grid.add_line(line)

    switch: dev.Switch = dev.Switch(bus_from=bus_1, bus_to=bus_2, name="SW12", active=True)
    switch.active_prof = np.array([True, False])
    grid.add_switch(switch)

    cgmes_model: CgmesCircuit = CgmesCircuit(cgmes_version=CGMESVersions.v2_4_15)
    logger: DataLogger = DataLogger()

    exported = veragrid_to_cgmes(
        gc_model=grid,
        num_circ=None,
        pf_results=None,
        cgmes_model=cgmes_model,
        logger=logger,
        t_idx=1,
    )

    exported_load = exported.cgmes_assets.ConformLoad_list[0]
    exported_external_grid = exported.cgmes_assets.ExternalNetworkInjection_list[0]
    exported_breaker = exported.cgmes_assets.Breaker_list[0]

    assert exported_load.p == 26.0
    assert exported_load.q == 14.0
    assert exported_load.LoadResponse.pConstantPower == np.round(20.0 / 26.0, 4)
    assert exported_load.LoadResponse.pConstantCurrent == np.round(2.0 / 26.0, 4)
    assert exported_load.LoadResponse.pConstantImpedance == np.round(4.0 / 26.0, 4)
    assert exported_load.LoadResponse.qConstantPower == np.round(6.0 / 14.0, 4)
    assert exported_load.LoadResponse.qConstantCurrent == np.round(3.0 / 14.0, 4)
    assert exported_load.LoadResponse.qConstantImpedance == np.round(5.0 / 14.0, 4)

    assert exported_external_grid.p == 40.0
    assert exported_external_grid.q == 9.0

    assert exported_breaker.open is True

    current_limits = exported.cgmes_assets.CurrentLimit_list
    current_limit_values = sorted({round(current_limit.value, 4) for current_limit in current_limits})
    expected_values = sorted({
        round(200.0 * 1e3 / (110.0 * np.sqrt(3.0)), 4),
        round(240.0 * 1e3 / (110.0 * np.sqrt(3.0)), 4),
        round(280.0 * 1e3 / (110.0 * np.sqrt(3.0)), 4),
    })

    assert len(current_limits) == 6
    assert current_limit_values == expected_values


@pytest.mark.parametrize("tc_type", [TapChangerTypes.NoRegulation, TapChangerTypes.VoltageRegulation])
def test_exporting_the_tap_values_leaves_the_tap_changer_as_it_was(tc_type: TapChangerTypes) -> None:
    """Export an off-nominal fixed tap without touching the table or the position of the device."""

    transformer: dev.Transformer2W = dev.Transformer2W(name="T1")
    tap_changer: TapChanger = transformer.tap_changer
    tap_changer.total_positions = 11
    tap_changer.neutral_position = 5
    tap_changer.dV = 0.01
    tap_changer.tc_type = tc_type
    table: np.ndarray = 1.0 + 0.01 * (np.arange(11) - 5)
    assert tap_changer.set_tap_module_phase_values(tap_modules=table, tap_phases=np.zeros(11))
    tap_changer.tap_position = 7
    transformer.tap_module = table[8]

    get_transformer_tap_values_for_cgmes_export(mc_elm=transformer, logger=DataLogger())

    assert tap_changer.tc_type == tc_type
    assert tap_changer.tap_position == 7
    assert tap_changer.uses_explicit_table
    assert np.array_equal(tap_changer.tap_modules_array, table)


TAP_TABLES: dict[str, np.ndarray] = {
    "rising": 1.0 + 0.0125 * (np.arange(17) - 8),
    "falling": 1.0 - 0.0125 * (np.arange(17) - 8),
    "falling_on_the_to_bus": 1.0 / (1.0 + 0.0125 * (np.arange(17) - 8)),
}


def _transformer_on_a_table(table: np.ndarray, position: int, dv: float = 0.0125, neutral: int = 8,
                            tc_type: TapChangerTypes = TapChangerTypes.VoltageRegulation) -> dev.Transformer2W:
    """A transformer on an exact 17 position table, whose generic step is dv."""

    transformer: dev.Transformer2W = dev.Transformer2W(name="T1")
    tap_changer: TapChanger = transformer.tap_changer
    tap_changer.total_positions = 17
    tap_changer.neutral_position = neutral
    tap_changer.dV = dv
    tap_changer.tc_type = tc_type
    assert tap_changer.set_tap_module_phase_values(tap_modules=table, tap_phases=np.zeros(17))
    tap_changer.tap_position = position
    transformer.tap_module = table[position]
    return transformer


@pytest.mark.parametrize("shape", TAP_TABLES)
@pytest.mark.parametrize("position", [0, 3, 8, 12, 16])
def test_exported_tap_values_read_back_as_the_same_module(shape: str, position: int) -> None:
    """The way back lands on the module and the step of the exact table, and the increment has the sign of the table."""

    table: np.ndarray = TAP_TABLES[shape]
    transformer: dev.Transformer2W = _transformer_on_a_table(table=table, position=position)

    low, high, normal, neutral, increment, step = get_transformer_tap_values_for_cgmes_export(mc_elm=transformer,
                                                                                               logger=DataLogger())

    imported: TapChanger = TapChanger()
    imported.init_from_cgmes(low=low, high=high, normal=normal, neutral=neutral, stepVoltageIncrement=increment,
                             step=step, tc_type=TapChangerTypes.VoltageRegulation)
    assert step == position
    assert (increment < 0.0) == (shape != "rising")
    assert imported.get_tap_module() == pytest.approx(table[position], abs=1e-6)


@pytest.mark.parametrize("module", [1.0, 1.0 + 1e-9])
def test_a_module_of_one_exports_the_neutral_step(module: float) -> None:
    """A profile at 1.0 leaves on the neutral step, whatever position the snapshot holds."""

    transformer: dev.Transformer2W = _transformer_on_a_table(table=TAP_TABLES["rising"], position=3)
    transformer.tap_module = module

    values: tuple[int, int, int, int, float, int] = get_transformer_tap_values_for_cgmes_export(mc_elm=transformer,
                                                                                               logger=DataLogger())

    assert values[5] == 8
    assert values[4] == 1.25


@pytest.mark.parametrize("shape", TAP_TABLES)
@pytest.mark.parametrize("module", [1.0 + 1e-3, 1.0 + 1e-4, 1.0 - 1e-4])
def test_a_module_off_one_at_the_neutral_leaves_it_with_the_sign_of_the_table(shape: str, module: float) -> None:
    """A module close to 1 but off it is not the neutral step, and the step beside carries it with the sign of
    the table."""

    transformer: dev.Transformer2W = _transformer_on_a_table(table=TAP_TABLES[shape], position=8)
    transformer.tap_module = module

    low, high, normal, neutral, increment, step = get_transformer_tap_values_for_cgmes_export(mc_elm=transformer,
                                                                                               logger=DataLogger())

    imported: TapChanger = TapChanger()
    imported.init_from_cgmes(low=low, high=high, normal=normal, neutral=neutral, stepVoltageIncrement=increment,
                             step=step, tc_type=TapChangerTypes.VoltageRegulation)
    assert abs(step - neutral) == 1
    assert (increment < 0.0) == (shape != "rising")
    assert imported.get_tap_module() == pytest.approx(module, abs=1e-6)


@pytest.mark.parametrize("neutral", [0, 16])
@pytest.mark.parametrize("slope", [0.0125, -0.0125])
@pytest.mark.parametrize("module", [1.0 + 1e-3, 1.0 - 1e-3])
def test_a_module_off_one_at_a_neutral_on_an_end_leaves_on_the_only_step_beside(neutral: int, slope: float,
                                                                                module: float) -> None:
    """At a neutral on an end of the range only one step is beside it, so the increment takes the sign that step
    needs, which reverses the table when the table would have gone the other way."""

    table: np.ndarray = 1.0 + slope * (np.arange(17) - neutral)
    transformer: dev.Transformer2W = _transformer_on_a_table(table=table, position=neutral, neutral=neutral)
    transformer.tap_module = module

    low, high, normal, neutral_step, increment, step = get_transformer_tap_values_for_cgmes_export(
        mc_elm=transformer, logger=DataLogger())

    imported: TapChanger = TapChanger()
    imported.init_from_cgmes(low=low, high=high, normal=normal, neutral=neutral_step, stepVoltageIncrement=increment,
                             step=step, tc_type=TapChangerTypes.VoltageRegulation)
    step_up: bool = (module > 1.0) != (slope < 0.0)
    assert low <= step <= high
    assert step - neutral_step == (1 if neutral == 0 else -1)
    assert ((increment < 0.0) == (slope < 0.0)) == (step_up == (neutral == 0))
    assert imported.get_tap_module() == pytest.approx(module, abs=1e-6)


@pytest.mark.parametrize("dv", [0.0125, -0.0125])
def test_a_fixed_changer_of_module_one_keeps_the_generic_sign(dv: float) -> None:
    """A fixed changer leaves on the neutral step and the generic law at a module of 1, as it does off 1, whatever
    its table and its snapshot position do."""

    transformer: dev.Transformer2W = _transformer_on_a_table(table=TAP_TABLES["falling"], position=3, dv=dv,
                                                             tc_type=TapChangerTypes.NoRegulation)
    transformer.tap_module = 1.0

    values: tuple[int, int, int, int, float, int] = get_transformer_tap_values_for_cgmes_export(mc_elm=transformer,
                                                                                               logger=DataLogger())

    assert values[5] == 8
    assert values[4] == np.sign(dv) * 1.25


def test_a_module_of_one_on_a_flat_table_exports_the_neutral_step() -> None:
    """Every position of a flat table holds a module of 1, and the neutral step is still the one that leaves."""

    transformer: dev.Transformer2W = _transformer_on_a_table(table=np.ones(17), position=8)
    transformer.tap_module = 1.0

    values: tuple[int, int, int, int, float, int] = get_transformer_tap_values_for_cgmes_export(mc_elm=transformer,
                                                                                               logger=DataLogger())

    assert values[5] == 8
    assert values[4] == 1.25


@pytest.mark.parametrize("shape, sign", [("rising", 1.0), ("falling", -1.0)])
@pytest.mark.parametrize("dv", [0.0125, -0.0125])
def test_a_module_of_one_takes_the_sign_of_the_table(shape: str, sign: float, dv: float) -> None:
    """At a module of 1 the table, not the generic step, says where the voltage goes."""

    transformer: dev.Transformer2W = _transformer_on_a_table(table=TAP_TABLES[shape], position=8, dv=dv)
    transformer.tap_module = 1.0

    values: tuple[int, int, int, int, float, int] = get_transformer_tap_values_for_cgmes_export(mc_elm=transformer,
                                                                                               logger=DataLogger())

    assert values[4] == sign * 1.25


def test_a_module_of_one_exports_the_neutral_step_below_zero() -> None:
    """A changer whose steps start below zero leaves on its neutral step, not on the position of it."""

    transformer: dev.Transformer2W = dev.Transformer2W(name="T1")
    transformer.tap_changer.init_from_cgmes(low=-8, high=8, normal=0, neutral=0, stepVoltageIncrement=1.25, step=-3,
                                            tc_type=TapChangerTypes.VoltageRegulation)
    transformer.tap_module = 1.0

    values: tuple[int, int, int, int, float, int] = get_transformer_tap_values_for_cgmes_export(mc_elm=transformer,
                                                                                               logger=DataLogger())

    assert values[3] == 0
    assert values[5] == 0
