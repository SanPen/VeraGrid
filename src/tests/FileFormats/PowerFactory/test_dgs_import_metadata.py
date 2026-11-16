# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Check import-owned metadata without runtime contract synchronization."""

from pathlib import Path

import pytest

from VeraGridEngine.Utils.Symbolic.symbolic_io import duplicate_block
from VeraGridEngine.Devices.Branches.transformer import Transformer2W
from VeraGridEngine.Templates.Rms.transformers.transformer_rms_template import get_ideal_transformer2w_rms
from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Templates.Rms.line.line_rms_template import get_line_rms_template
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.IO.dgs.dgs_complete_injection import build_complete_injection_template
from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
from VeraGridEngine.IO.dgs.dgs_objects import ElmSind
from VeraGridEngine.IO.dgs.dgs_import_metadata import (
    DgsImportMetadata,
    assign_import_template,
    get_import_field,
    set_import_field,
)
from VeraGridEngine.IO.dgs.dgs_to_veragrid import dgs_to_circuit
from VeraGridEngine.IO.dgs.dyn_dgs_parser import DynDgsParser
from VeraGridEngine.IO.dgs.dynamic_models.dynamic_model_import import DynamicModelImport
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import (
    DynamicSimulationMode,
    DeviceType,
    VarPowerFlowReferenceType,
    ParamPowerFlowReferenceType,
    DgsImportField,
)


def test_import_metadata_contains_only_fields_consumed_by_parser() -> None:
    """Keep the scalar schema limited to live parser consumers.

    :return: None.
    """
    importer: DynamicModelImport = DynamicModelImport(DgsCircuit(), MultiCircuit(), DynamicSimulationMode.RMS, Logger())
    metadata: DgsImportMetadata = importer.get_import_metadata()
    block: Block = Block()
    expected: dict[str, bool | int | float | str | None] = dict(
        dgs_elmsym_runtime_adapter=False,
        dgs_elmsym_rotor_angle_var_uid=None,
        dgs_elmsym_speed_var_uid=None,
        dgs_logical_actuator_root_id=None,
        dgs_open_resistance_ohm=None,
    )
    assert set(field.value for field in DgsImportField) == set(expected)
    with pytest.raises(KeyError):
        get_import_field(block, DgsImportField.DGS_ELMSYM_SPEED_VAR_UID, metadata)
    assert importer.block_metadata == dict()
    set_import_field(block, DgsImportField.DGS_ELMSYM_RUNTIME_ADAPTER, True, metadata)
    with pytest.raises(KeyError, match="dgs_elmsym_speed_var_uid"):
        get_import_field(block, DgsImportField.DGS_ELMSYM_SPEED_VAR_UID, metadata)
    set_import_field(block, DgsImportField.DGS_ELMSYM_RUNTIME_ADAPTER, True, metadata)
    set_import_field(block, DgsImportField.DGS_ELMSYM_ROTOR_ANGLE_VAR_UID, 123, metadata)
    set_import_field(block, DgsImportField.DGS_ELMSYM_SPEED_VAR_UID, 456, metadata)
    set_import_field(block, DgsImportField.DGS_LOGICAL_ACTUATOR_ROOT_ID, "root-fid", metadata)
    set_import_field(block, DgsImportField.DGS_OPEN_RESISTANCE_OHM, 123.0, metadata)
    assert metadata.blocks is importer.block_metadata
    assert set(importer.block_metadata) == set((block.uid,))
    assert set(importer.block_metadata[block.uid]) == set(expected)
    set_import_field(block, DgsImportField.DGS_LOGICAL_ACTUATOR_ROOT_ID, None, metadata)
    assert "dgs_logical_actuator_root_id" in importer.block_metadata[block.uid]
    assert get_import_field(block, DgsImportField.DGS_LOGICAL_ACTUATOR_ROOT_ID, metadata) is None


def test_duplication_leaves_import_metadata_unchanged() -> None:
    """Duplicate symbolic variables without copying or remapping import metadata.

    :return: None.
    """
    factory: VarFactory = VarFactory()
    x: Var = factory.add_var("metadata_state")
    u: Var = factory.add_var("metadata_u")
    child: Block = Block(state_vars=list((x,)), state_eqs=list((-x,)), out_vars=list((x,)),
                         event_dict=dict(((u, Const(1.0)),)))
    root: Block = Block(children=list((child,)))
    metadata: DgsImportMetadata = DgsImportMetadata(dict())
    set_import_field(root, DgsImportField.DGS_LOGICAL_ACTUATOR_ROOT_ID, "source-fid", metadata)
    set_import_field(root, DgsImportField.DGS_ELMSYM_SPEED_VAR_UID, x.uid, metadata)
    original_record: dict[str, bool | int | float | str | None] = dict(metadata.blocks[root.uid])
    original_keys: set[int] = set(metadata.blocks)
    copied: Block = duplicate_block(root, factory)
    target: Block = copied.children[0]
    assert target.uid != child.uid and copied.uid != root.uid
    assert target.state_vars[0].uid != x.uid
    assert next(iter(target.event_dict)).uid != u.uid
    assert set(metadata.blocks) == original_keys
    assert metadata.blocks[root.uid] == original_record
    assert target.uid not in metadata.blocks
    assert copied.uid not in metadata.blocks


def test_template_assignment_leaves_import_metadata_unchanged() -> None:
    """Keep template metadata unchanged when a physical device receives its clone.

    :return: None.
    """
    grid: MultiCircuit = MultiCircuit()
    bus: Bus = Bus(name="Metadata bus")
    grid.add_bus(bus)
    generator: Generator = Generator(name="Metadata host")
    grid.add_generator(bus=bus, api_obj=generator)
    source_var: Var = grid.var_factory.add_var("state")
    template: RmsModelTemplate = RmsModelTemplate(name="Metadata template")
    template.block = Block(state_vars=list((source_var,)), state_eqs=list((-source_var,)))
    metadata: DgsImportMetadata = DgsImportMetadata(dict())
    set_import_field(template.block, DgsImportField.DGS_ELMSYM_SPEED_VAR_UID,
                     source_var.uid, metadata)
    original_record: dict[str, object] = dict(metadata.blocks[template.block.uid])
    assign_import_template(generator, template)
    assert generator.rms_model.uid != template.block.uid
    assert generator.rms_model.state_vars[0].uid != source_var.uid
    assert set(metadata.blocks) == set((template.block.uid,))
    assert metadata.blocks[template.block.uid] == original_record


def test_generic_templates_without_metadata_do_not_register_empty_owners() -> None:
    """Leave metadata absent when a generic model has no import declarations.

    :return: None.
    """
    source: DgsCircuit = DgsCircuit()
    source.parse_dgs(str(Path(__file__).resolve().parents[2] / "data/grids/DGS/dynamic_gain_block.dgs"))
    destination: MultiCircuit = MultiCircuit()
    parser: DynDgsParser = DynDgsParser(source, destination, DynamicSimulationMode.RMS, Logger())
    parser.dynamic_model_import.convert_and_add_templates()
    assert len(destination.rms_models) == 1
    assert parser.dynamic_model_import.block_metadata == dict()


def test_reference_completion_uses_installed_models_and_their_metadata() -> None:
    """Connect machine frames using definitive installed variables and model UIDs.

    :return: None.
    """
    grid: MultiCircuit = MultiCircuit()
    bus: Bus = Bus(name="Machine bus")
    grid.add_bus(bus)
    parser: DynDgsParser = DynDgsParser(DgsCircuit(), grid, DynamicSimulationMode.RMS, Logger())
    generators: list[Generator] = list()
    templates: list[RmsModelTemplate] = list()
    speeds: list[Var] = list()
    index: int
    for index in range(2):
        generator: Generator = Generator(name=f"Machine {index}")
        grid.add_generator(bus=bus, api_obj=generator)
        angle: Var = grid.var_factory.add_var("phi")
        speed: Var = grid.var_factory.add_var("speed")
        omega: Var = grid.var_factory.add_var("renamed_base_frequency")
        template: RmsModelTemplate = RmsModelTemplate(name=generator.name)
        template.block = Block(state_vars=list((angle, speed)),
                               state_eqs=list((omega * (speed - Const(1.0)), -speed)),
                               parameters=dict(((omega, Const(314.0)),)),
                               api_obj_mapping=dict(((ParamPowerFlowReferenceType.omega_base, omega),)))
        metadata: DgsImportMetadata = parser.dynamic_model_import.get_import_metadata()
        generator.rms_template = template
        assert generator.rms_model.uid not in parser.dynamic_model_import.block_metadata
        parser.dynamic_model_import.register_imported_rms_model_metadata(generator, "ElmSym")
        assert generator.rms_model.uid in parser.dynamic_model_import.block_metadata
        assert generator.rms_model is not template.block
        generators.append(generator)
        templates.append(template)
        speeds.append(generator.rms_model.state_vars[1])
        assert generator.rms_model.state_vars[1].uid != speed.uid
    parser.elm_sym_reference_source_ids.add(generators[0].idtag)
    parser.complete_model_references()
    assert all(generator.rms_template is not None and not generator.rms_model.empty() for generator in generators)
    assert any(variable is speeds[0] for variable in generators[1].rms_model.state_eqs[0].get_vars())
    original_metadata: dict[int, dict[str, object]] = dict(
        (uid, dict(record)) for uid, record in parser.dynamic_model_import.block_metadata.items()
    )
    reference_speed: Var = generators[0].rms_model.state_vars[1]
    assert reference_speed is speeds[0]
    assert any(variable is reference_speed for variable in generators[1].rms_model.state_eqs[0].get_vars())
    assert parser.dynamic_model_import.block_metadata == original_metadata


@pytest.mark.parametrize("export_resistance", (True, False))
def test_logical_actuators_modify_installed_models_with_one_shared_controller(export_resistance: bool) -> None:
    """Bind a real two-pole DGS actuator to its definitive device-owned models.

    :param export_resistance: Whether the source explicitly exports the open resistance.
    :return: None.
    """
    fixture: Path = Path(__file__).resolve().parents[2] / "data/grids/DGS/hvdc_vsc_v3_complete_static_dynamic.dgs"
    source: DgsCircuit = DgsCircuit()
    source.parse_dgs(str(fixture))
    if not export_resistance:
        source_branch: ElmSind
        for source_branch in source.elmsinds:
            source_branch.initial_resistance_column_declared = False
    else:
        pass
    grid: MultiCircuit = dgs_to_circuit(path=str(fixture), use_dynamic_information=False)
    parser: DynDgsParser = DynDgsParser(source, grid, DynamicSimulationMode.RMS, Logger())
    parser.classify_static_dev_and_build_missing_models()
    prepared: int = parser.prepare_dgs_logical_actuator_topology()
    parser.dynamic_model_import.convert_and_add_templates()
    parser.dynamic_model_import.apply_templates_to_devices()
    parser.prepare_dgs_circuit_for_rms()
    parser.complete_model_references()
    if not export_resistance:
        for device in parser.actuator_topology:
            assert "dgs_open_resistance_ohm" in parser.dynamic_model_import.block_metadata[device.rms_model.uid]
            assert get_import_field(device.rms_model, DgsImportField.DGS_OPEN_RESISTANCE_OHM,
                                    parser.dynamic_model_import.get_import_metadata()) is None
    else:
        pass
    bound: int = parser.bind_dgs_logical_actuator_runtime()
    assert prepared == bound == 2
    assert all(device.rms_template is not None for device in parser.actuator_topology)
    assert all(device.rms_model.uid in parser.dynamic_model_import.block_metadata
               for device in parser.actuator_topology)
    root_ids: set[str] = set(root_id for root_id, resistance in parser.actuator_topology.values())
    controller: Block = parser.conversion_result.templates_by_root_dgs_id[next(iter(root_ids))].block
    assert sum(
        block.name == controller.name
        for device in parser.actuator_topology
        for block in device.rms_model.get_all_blocks()
    ) == 1
    gate_uids_by_pole: list[set[int]] = list()
    for device in parser.actuator_topology:
        gate_uids_by_pole.append(set(
            variable.uid
            for block in device.rms_model.get_all_blocks()
            for parameter, expression in block.event_dict.items()
            if parameter.name == "u"
            for variable in expression.get_vars()
            if variable.name == "gate"
        ))
    assert len(gate_uids_by_pole[0]) == 1
    assert gate_uids_by_pole[0] == gate_uids_by_pole[1]
    assert gate_uids_by_pole[0].isdisjoint(set(
        variable.uid for block in controller.get_all_blocks()
        for variable in block.algebraic_vars if variable.name == "gate"
    ))


def test_shared_standard_template_registers_each_installed_model_uid() -> None:
    """Reuse one template without sharing model parameters or metadata identities.

    :return: None.
    """
    grid: MultiCircuit = MultiCircuit()
    bus_from: Bus = Bus(name="From")
    bus_to: Bus = Bus(name="To")
    grid.add_bus(bus_from)
    grid.add_bus(bus_to)
    parser: DynDgsParser = DynDgsParser(DgsCircuit(), grid, DynamicSimulationMode.RMS, Logger())
    template: RmsModelTemplate = get_line_rms_template(grid.var_factory)
    models: list[Block] = list()
    index: int
    for index in range(2):
        line: Line = Line(bus_from=bus_from, bus_to=bus_to, name=f"Line {index}", r=0.01, x=0.1)
        grid.add_line(line)
        assign_import_template(line, template)
        assert line.rms_template is template
        assert line.rms_model is not template.block
        assert line.rms_model.uid not in parser.dynamic_model_import.block_metadata
        assert parser.dynamic_model_import.block_metadata == dict()
        models.append(line.rms_model)
    assert models[0].uid != models[1].uid
    assert template.block.uid not in parser.dynamic_model_import.block_metadata
    first_parameter_uids: set[int] = set(
        parameter.uid for block in models[0].get_all_blocks() for parameter in block.parameters
    )
    second_parameter_uids: set[int] = set(
        parameter.uid for block in models[1].get_all_blocks() for parameter in block.parameters
    )
    assert first_parameter_uids.isdisjoint(second_parameter_uids)


def test_ideal_transformer_instantiation_does_not_register_unused_metadata() -> None:
    """Keep metadata absent when a standard model has no parser declarations.

    :return: None.
    """
    grid: MultiCircuit = MultiCircuit()
    bus_from: Bus = Bus(name="From", Vnom=110.0)
    bus_to: Bus = Bus(name="To", Vnom=10.0)
    grid.add_bus(bus_from)
    grid.add_bus(bus_to)
    transformer: Transformer2W = Transformer2W(bus_from=bus_from, bus_to=bus_to, name="Ideal")
    grid.add_transformer2w(transformer)
    parser: DynDgsParser = DynDgsParser(DgsCircuit(), grid, DynamicSimulationMode.RMS, Logger())
    template: RmsModelTemplate = get_ideal_transformer2w_rms(grid.var_factory)
    assert parser.dynamic_model_import.block_metadata == dict()
    assign_import_template(transformer, template)
    assert parser.dynamic_model_import.block_metadata == dict()
    assert parser.dynamic_model_import.block_metadata == dict()


def test_complete_injection_normal_assignment_preserves_internal_connections() -> None:
    """Duplicate a complete declaration with one coherent internal controller.

    :return: None.
    """
    grid: MultiCircuit = MultiCircuit()
    bus: Bus = Bus(name="Injection bus")
    grid.add_bus(bus)
    host: Generator = Generator(name="Complete injection")
    grid.add_generator(bus=bus, api_obj=host)
    active: Var = grid.var_factory.add_var("P", reference=VarPowerFlowReferenceType.P)
    reactive: Var = grid.var_factory.add_var("Q", reference=VarPowerFlowReferenceType.Q)
    voltage: Var = grid.var_factory.add_var("Vm", reference=VarPowerFlowReferenceType.Vm)
    angle: Var = grid.var_factory.add_var("Va", reference=VarPowerFlowReferenceType.Va)
    base: RmsModelTemplate = RmsModelTemplate(name="Controller")
    base.tpe = DeviceType.GeneratorDevice
    base.block = Block(
        in_vars=list((voltage, angle)), out_vars=list((active, reactive)),
        algebraic_vars=list((active, reactive)), algebraic_eqs=list((active - Const(1.0), reactive)),
        external_mapping=dict(((VarPowerFlowReferenceType.P, active), (VarPowerFlowReferenceType.Q, reactive),
                               (VarPowerFlowReferenceType.Vm, voltage), (VarPowerFlowReferenceType.Va, angle))),
    )
    host.rms_template = base
    previous_model: Block = host.rms_model
    complete: RmsModelTemplate = build_complete_injection_template(grid.var_factory, base, "Complete")
    host.rms_template = complete
    model: Block = host.rms_model
    dc_model: Block = model.children[1]
    assert model is not complete.block
    assert model.children[0] is not base.block
    assert model.children[0].uid != previous_model.uid
    assert complete.block.children[0] is base.block
    assert dc_model.in_vars[0] is model.external_mapping[VarPowerFlowReferenceType.P]
    assert dc_model.in_vars[1] is model.external_mapping[VarPowerFlowReferenceType.Q]
    assert dc_model.in_vars[2].uid == model.external_mapping[VarPowerFlowReferenceType.Vm].uid
    assert dc_model.in_vars[0].uid != previous_model.external_mapping[VarPowerFlowReferenceType.P].uid
