"""Construct the IEEE39 network and its benchmark RMS models."""

from __future__ import annotations

from pathlib import Path

import andes

from VeraGridEngine.enumerations import ParamPowerFlowReferenceType
from VeraGridEngine.enumerations import VarPowerFlowReferenceType
from VeraGridEngine.Templates.Rms.line.line_rms_template import get_line_rms_template
from VeraGridEngine.Templates.Rms.load_characteristics.load_rms_template import get_load_rms_template
from VeraGridEngine.Templates.Rms.buses.shunt_template import get_shunt_template
from VeraGridEngine.Templates.Rms.transformers.transformer_rms_template import get_transformer2w_rms
from VeraGridEngine.Templates.Rms.buses.bus_rms_template import initialize_bus_rms
from VeraGridEngine.Utils.Symbolic.templates_common_functions import set_rms_model
import VeraGridEngine.api as gce

from benchmarks.dynamics_andes.small_signal.IEEE39.ieee39_network_model import configure_ieee39_static_network
from benchmarks.dynamics_andes.small_signal.IEEE39.ieee39_dynamic_model import get_ieee39_genrou_rms_template


def _get_base_grid_path() -> Path:
    """Return the IEEE39 base-grid path.

    :return: Base-grid path.
    """
    grid_path: Path = Path(andes.get_case("ieee39/ieee39.raw"))
    return grid_path.resolve()


def _assign_ieee39_rms_models(grid: gce.MultiCircuit) -> None:
    """Assign standard GENROU RMS models to the IEEE39 grid.

    :param grid: VeraGrid network.
    :return: None.
    """
    bus_list: list[object] = list(grid.buses)
    for bus in bus_list:
        initialize_bus_rms(bus, vf=grid.var_factory)

    generator_count: int = len(grid.generators)
    generator_index: int = 0
    while generator_index < generator_count:
        generator = grid.generators[generator_index]
        set_rms_model(
            device=generator,
            model=get_ieee39_genrou_rms_template(
                vfactory=grid.var_factory,
                generator_index=generator_index,
                name=f"ieee39_gen_{generator_index + 1}",
            ).block,
            var_factory=grid.var_factory,
        )
        generator_index += 1

    line_count: int = len(grid.lines)
    line_index: int = 0
    while line_index < line_count:
        line = grid.lines[line_index]
        set_rms_model(device=line, model=get_line_rms_template(grid.var_factory, name=f"ieee39_line_{line_index + 1}").block, var_factory=grid.var_factory)
        line_index += 1

    transformer_count: int = len(grid.transformers2w)
    transformer_index: int = 0
    while transformer_index < transformer_count:
        transformer = grid.transformers2w[transformer_index]
        set_rms_model(
            device=transformer,
            model=get_transformer2w_rms(grid.var_factory).block,
            var_factory=grid.var_factory,
        )
        transformer_index += 1

    load_count: int = len(grid.loads)
    load_index: int = 0
    while load_index < load_count:
        load = grid.loads[load_index]
        set_rms_model(device=load, model=get_load_rms_template(grid.var_factory, name=f"ieee39_load_{load_index + 1}").block, var_factory=grid.var_factory)
        load_index += 1

    shunt_count: int = len(grid.shunts)
    shunt_index: int = 0
    while shunt_index < shunt_count:
        shunt = grid.shunts[shunt_index]
        shunt_model = get_shunt_template(
            grid.var_factory,
            name=f"ieee39_shunt_{shunt_index + 1}",
            phasor=False,
        ).block
        shunt_vm = shunt_model.E(VarPowerFlowReferenceType.Vm)
        shunt_p = shunt_model.E(VarPowerFlowReferenceType.P)
        shunt_q = shunt_model.E(VarPowerFlowReferenceType.Q)
        shunt_g = shunt_model.api_obj_mapping[ParamPowerFlowReferenceType.g]
        shunt_b = shunt_model.api_obj_mapping[ParamPowerFlowReferenceType.b]
        shunt_model.event_dict[shunt_g] = grid.var_factory.add_const(
            value=shunt.G / grid.Sbase,
            name="g",
        )
        shunt_model.event_dict[shunt_b] = grid.var_factory.add_const(
            value=shunt.B / grid.Sbase,
            name="b",
        )
        shunt_model.init_eqs[shunt_p] = -shunt_g * shunt_vm ** 2
        shunt_model.init_eqs[shunt_q] = shunt_b * shunt_vm ** 2
        set_rms_model(
            device=shunt,
            model=shunt_model,
            var_factory=grid.var_factory,
        )
        shunt_index += 1


def build_ieee39_rms_benchmark_grid() -> gce.MultiCircuit:
    """Build the IEEE39 RMS-ready benchmark grid.

    :return: RMS-ready grid.
    """
    grid_path: Path = _get_base_grid_path()
    grid: gce.MultiCircuit = gce.open_file(str(grid_path))
    configure_ieee39_static_network(grid)
    _assign_ieee39_rms_models(grid)
    return grid
