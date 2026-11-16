# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Check source-selected PWM construction and exact native command wiring."""

from pathlib import Path

import pytest

from VeraGridEngine.Devices.Branches.vsc import VSC
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
from VeraGridEngine.IO.dgs.dgs_objects import BlkSig, BlkSlot, ElmComp, ElmVsc, PowerFactoryVscType
from VeraGridEngine.IO.dgs.dgs_to_blocks import DgsDirectRootBuildResult, ElmCompInstanceEntry
from VeraGridEngine.IO.dgs.dgs_to_veragrid import _get_powerfactory_vsc_series_impedance, dgs_to_circuit
from VeraGridEngine.IO.dgs.dynamic_models.dgs_adapter_block_from_native_dgs import build_dgs_elmvsc_two_level_block
from VeraGridEngine.IO.dgs.dynamic_models.dgs_native_model_workflow import (
    NativeDgsEquipmentKind, NativeDgsEquipmentPlan, assemble_native_dgs_model,
    construct_native_dgs_equipment, detect_native_dgs_equipment,
)
from VeraGridEngine.IO.dgs.dynamic_models.dynamic_model_import import DynamicModelImport, DgsDynamicTemplateConversionResult
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import DeviceType, DynamicSimulationMode
from tests.FileFormats.PowerFactory.test_dgs_adapter_block_from_native_dgs import _assert_equilibrium, _initial_bindings


def _source_and_roots() -> tuple[DgsCircuit, ElmVsc, ElmComp, ElmComp]:
    """Create two source composites referring to the same converter.

    :return: Source circuit, converter, selected root and alternative root.
    """
    circuit: DgsCircuit = DgsCircuit()
    source: ElmVsc = ElmVsc()
    source.ID = 'vsc'
    source.c_pmod = 'selected'
    source.vsctype = int(PowerFactoryVscType.TwoLevel)
    circuit.elmvscs.append(source)
    slot: BlkSlot = BlkSlot()
    slot.ID = 'native'
    slot.filtmod = 'ElmVsc'
    circuit.blkslots.append(slot)
    selected: ElmComp = ElmComp()
    selected.ID = 'selected'
    selected.pblk = list(('native',))
    selected.pelm = list(('vsc',))
    other: ElmComp = ElmComp()
    other.ID = 'other'
    other.pblk = list(('native',))
    other.pelm = list(('vsc',))
    circuit.elmcomps.extend((selected, other))
    return circuit, source, selected, other


def test_source_pmod_survives_converter_parsing() -> None:
    """Read the source-selected model instead of losing its exported FID.

    :return: None.
    """
    header: dict[str, int] = dict(FID=0, OP=1, loc_name=2, c_pmod=3, vsctype=4)
    source: ElmVsc = ElmVsc.parse_line('1566;C;PWM Converter;1475;0', header)
    assert source.c_pmod == '1475'
    assert source.vsctype == int(PowerFactoryVscType.TwoLevel)


def test_selected_root_respects_service_and_has_no_alternative_fallback() -> None:
    """Do not activate an alternative when the selected root is disabled.

    :return: None.
    """
    circuit: DgsCircuit
    source: ElmVsc
    selected: ElmComp
    other: ElmComp
    circuit, source, selected, other = _source_and_roots()
    importer: DynamicModelImport = DynamicModelImport(circuit, MultiCircuit(), DynamicSimulationMode.RMS, Logger())
    identity: tuple[str, DeviceType, str, str | None] = ('vsc', DeviceType.VscDevice, 'ElmVsc', 'PWM')
    assert importer._is_selected_dgs_root_for_host(selected, identity)
    assert not importer._is_selected_dgs_root_for_host(other, identity)
    selected.outserv = 1
    assert not importer._is_selected_dgs_root_for_host(selected, identity)
    assert not importer._is_selected_dgs_root_for_host(other, identity)
    selected.outserv = 0
    source.outserv = 1
    assert not importer._is_selected_dgs_root_for_host(selected, identity)
    source.outserv = 0
    source.c_pmod = None
    assert not importer._is_selected_dgs_root_for_host(selected, identity)
    other.outserv = 1
    assert importer._is_selected_dgs_root_for_host(selected, identity)


@pytest.mark.parametrize('power', (-0.5, 0.5))
def test_two_level_bridge_balances_terminal_power_without_arm_states(power: float) -> None:
    """Preserve losses and modulation in both directions of active power.

    :param power: AC terminal power on the system base.
    :return: None.
    """
    block: Block = build_dgs_elmvsc_two_level_block(
        100.0, 50.0, 110.0, 320.0, 320.0, 0.01, 0.1, 0.001, 0.002, 0.003)
    bindings: dict[int, float] = _initial_bindings(
        block, dict(Vdc_positive=1.0, Vdc_negative=-1.0, Vm=1.0, Va=0.2, Pac=power, Qac=0.1))
    _assert_equilibrium(block, bindings)
    assert len(block.state_vars) == 0
    assert 'mdc' not in set(variable.name for variable in block.in_vars)
    variables: dict[str, Var] = dict((variable.name, variable) for variable in block.out_vars)
    # Copper loss uses the system-base resistance; switching losses use AC current.
    current: float = bindings[variables['Iac'].uid]
    expected_loss: float = 0.02 * (power * power + 0.01) + 0.001 + 0.002 * current + 0.003 * current * current
    assert bindings[variables['Pdc'].uid] + power == pytest.approx(expected_loss, abs=1e-8)


def test_two_level_selection_ignores_stale_mmc_arm_fields() -> None:
    """A source topology selector must take precedence over unused MMC data.

    :return: None.
    """
    source: ElmVsc = ElmVsc()
    source.ID = '1566'
    source.vsctype = int(PowerFactoryVscType.TwoLevel)
    source.Snom = 75.0
    source.Unom = 0.575
    source.Pcu = 75.0
    source.uk = 10.0
    source.Rarm = 0.006
    source.Larm = 60.0
    circuit: DgsCircuit = DgsCircuit()
    circuit.elmvscs.append(source)
    native: ElmCompInstanceEntry = ElmCompInstanceEntry(
        '1371', 'PWM', '1566', 'PWM', 'ElmVsc', 0, None, None,
        slot_inputs=list(('Pmr;Pmi',)), slot_reference_is_resolved=True, element_reference_is_resolved=True)
    result: DgsDirectRootBuildResult = DgsDirectRootBuildResult(Block(), dict(), dict(), list((native,)))
    plans: tuple[NativeDgsEquipmentPlan, ...] = detect_native_dgs_equipment(result, circuit)
    assert plans[0].converter_type == PowerFactoryVscType.TwoLevel
    resistance: float
    reactance: float
    resistance, reactance = _get_powerfactory_vsc_series_impedance(source, 50.0)
    assert resistance == pytest.approx(0.001)
    assert reactance == pytest.approx((0.1 ** 2 - 0.001 ** 2) ** 0.5)
    host: VSC = VSC(bus_from=Bus(Vnom=0.575, is_dc=True), bus_to=Bus(Vnom=0.575),
                    bus_dc_n=Bus(Vnom=0.575, is_dc=True), rate=75.0,
                    r_series=resistance, x_series=reactance, alpha1=0.0, alpha2=0.0, alpha3=resistance * 100.0 / 75.0,
                    mmc_arm_capacitance_uf=10000.0)
    block: Block = construct_native_dgs_equipment(plans[0], host, circuit, 100.0, 50.0)
    assert len(block.state_vars) == 0
    assert len(block.in_vars) == 6
    bindings: dict[int, float] = _initial_bindings(
        block, dict(Vdc_positive=1.0, Vdc_negative=-1.0, Vm=1.0, Va=0.0, Pac=-0.4, Qac=0.0))
    _assert_equilibrium(block, bindings)
    pdc: Var = next(variable for variable in block.out_vars if variable.name == 'Pdc')
    assert bindings[pdc.uid] - 0.4 == pytest.approx(resistance * 100.0 / 75.0 * 0.16, abs=1e-8)
    host.rate = 0.0
    with pytest.raises(ValueError, match='positive rating'):
        construct_native_dgs_equipment(plans[0], host, circuit, 100.0, 50.0)


def test_cable_725_connects_native_vector_commands_by_exact_endpoints() -> None:
    """Wire both modulation values without guessing a producer by signal name.

    :return: None.
    """
    pmr: Var = Var('modulation_real')
    pmi: Var = Var('modulation_imaginary')
    producer: Block = Block(out_vars=list((pmr, pmi)), event_dict=dict(((pmr, Const(1.0)), (pmi, Const(0.0)))))
    native: ElmCompInstanceEntry = ElmCompInstanceEntry(
        '1371', 'PWM', '1566', 'PWM', 'ElmVsc', 0, None, None,
        slot_inputs=list(('Pmr;Pmi',)), slot_reference_is_resolved=True, element_reference_is_resolved=True)
    control: ElmCompInstanceEntry = ElmCompInstanceEntry(
        '1369', 'Normalize', '1507', 'Normalize', 'ElmDsl', 0, None, None,
        slot_outputs=list(('Pmr;Pmi',)), slot_reference_is_resolved=True, element_reference_is_resolved=True)
    direct: DgsDirectRootBuildResult = DgsDirectRootBuildResult(
        Block(children=list((producer,))), dict((('1369', producer),)), dict(), list((native, control)))
    cable: BlkSig = BlkSig()
    cable.ID = '725'
    cable.loc_name = 'Pmr;Pmi'
    cable.pnodfrom = '1369'
    cable.pnodto = '1371'
    cable.inodfrom = 0
    cable.inodto = 0
    circuit: DgsCircuit = DgsCircuit()
    circuit.blksigs.append(cable)
    equipment: Block = build_dgs_elmvsc_two_level_block(100.0, 75.0, 0.575, 0.575, 0.575, 0.0, 0.0)
    original_pmr: Var = equipment.in_vars[4]
    assembled: Block = assemble_native_dgs_model(
        NativeDgsEquipmentPlan(NativeDgsEquipmentKind.BipolarVsc, native, PowerFactoryVscType.TwoLevel),
        equipment, direct, circuit, Logger())
    dependencies: set[int] = set(variable.uid for expression in assembled.algebraic_eqs for variable in expression.get_vars())
    assert pmr.uid in dependencies
    assert pmi.uid in dependencies
    assert original_pmr.uid not in dependencies


def test_native_assembly_failure_does_not_discard_an_independent_root() -> None:
    """Keep an unrelated valid converter template after a physical build fails.

    :return: None.
    """
    path: Path = Path(__file__).resolve().parents[2] / 'data' / 'grids' / 'DGS' / 'hvdc_vsc_v1_complete_static_dynamic.dgs'
    source: DgsCircuit = DgsCircuit()
    source.parse_dgs(str(path))
    grid: MultiCircuit = dgs_to_circuit(str(path))
    assert len(grid.vsc_devices) == 2
    grid.vsc_devices[0].rate = 0.0
    logger: Logger = Logger()
    importer: DynamicModelImport = DynamicModelImport(source, grid, DynamicSimulationMode.RMS, logger)
    result: DgsDynamicTemplateConversionResult = importer.convert_and_add_templates()
    assert any(entry.msg == 'DGS dynamic root could not be assembled' for entry in logger.entries)
    assert len(result.templates_by_root_dgs_id) == 1
