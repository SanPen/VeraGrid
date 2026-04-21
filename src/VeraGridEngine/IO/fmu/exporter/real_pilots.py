# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Callable
import math

import numpy as np

from . import compat  # noqa: F401  # bootstrap VeraGrid imports
from .compat import Const, Var

import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.thevenin_equivalent_emt_generator_template import get_generator_thevenin_rl_emt_template
from VeraGridEngine.Templates.Rms.load_frequency_dependent import FrequencyLoadBuild

from .snapshot import build_model_snapshot, reconstruct_block


@dataclass(frozen=True, slots=True)
class PilotModel:
    name: str
    model: object
    outputs: tuple[str, ...]
    stop_time: float
    fmpy_start_values: dict[str, float]
    smoke_set_values: dict[str, float]
    input_builder: Callable[[float], np.ndarray | None]


def _constant_input_signal(stop_time: float, values: dict[str, float], samples: int = 101) -> np.ndarray:
    dtype = [("time", np.float64)] + [(name, np.float64) for name in values]
    result = np.zeros(samples, dtype=dtype)
    result["time"] = np.linspace(0.0, stop_time, samples)
    for name, value in values.items():
        result[name] = float(value)
    return result


def _three_phase_input_signal(stop_time: float, amplitude: float, frequency_hz: float, name_prefix: str) -> np.ndarray:
    samples = 201
    omega = 2.0 * math.pi * frequency_hz
    times = np.linspace(0.0, stop_time, samples)
    dtype = [
        ("time", np.float64),
        (f"v_A_{name_prefix}", np.float64),
        (f"v_B_{name_prefix}", np.float64),
        (f"v_C_{name_prefix}", np.float64),
    ]
    result = np.zeros(samples, dtype=dtype)
    result["time"] = times
    result[f"v_A_{name_prefix}"] = amplitude * np.sin(omega * times)
    result[f"v_B_{name_prefix}"] = amplitude * np.sin(omega * times - 2.0 * math.pi / 3.0)
    result[f"v_C_{name_prefix}"] = amplitude * np.sin(omega * times + 2.0 * math.pi / 3.0)
    return result


def _set_event_const_by_name(block: object, var_name: str, value: float) -> None:
    event_dict = getattr(block, "event_dict")
    for variable in list(event_dict.keys()):
        if getattr(variable, "name", None) == var_name:
            event_dict[variable] = Const(float(value))
            return
    raise KeyError(var_name)


def _set_init_const_by_name(block: object, var_name: str, value: float) -> None:
    init_values = getattr(block, "init_values")
    for variable in list(getattr(block, "state_vars", [])) + list(getattr(block, "algebraic_vars", [])):
        if getattr(variable, "name", None) == var_name:
            init_values[variable] = Const(float(value))
            return
    raise KeyError(var_name)


def _safe_block_copy(block: object):
    return reconstruct_block(build_model_snapshot(block))


def build_frequency_load_rms_pilot() -> PilotModel:
    var_factory = VarFactory(name="FMU RMS Pilot VarFactory")
    template = FrequencyLoadBuild(var_factory, name="fmu_rms_pilot", Pl0=1.0, Ql0=0.1)
    return PilotModel(
        name="FrequencyLoadPilot",
        model=template.block,
        outputs=("P", "Q"),
        stop_time=1e-2,
        fmpy_start_values={},
        smoke_set_values={"Vm_": 1.0, "Va_": 0.0},
        input_builder=lambda stop_time: _constant_input_signal(stop_time, {"Vm_": 1.0, "Va_": 0.0}),
    )


def build_thevenin_generator_emt_pilot() -> PilotModel:
    grid = SimpleNamespace(var_factory=VarFactory(name="FMU EMT Pilot VarFactory"), fBase=50.0)
    generator = SimpleNamespace(R1=0.01, X1=0.2)
    pilot_name = "emt_thevenin_eq_generator_template"
    template = get_generator_thevenin_rl_emt_template(grid, generator, name=pilot_name)
    block = template.block

    _set_event_const_by_name(block, f"phi_v_{pilot_name}", 0.0)
    _set_event_const_by_name(block, f"phi_{pilot_name}", 0.0)
    _set_event_const_by_name(block, f"Vpk_{pilot_name}", 1.0)
    _set_event_const_by_name(block, f"Ipk_{pilot_name}", 0.2)

    _set_init_const_by_name(block, f"i_A_{pilot_name}", 0.0)
    _set_init_const_by_name(block, f"i_B_{pilot_name}", -0.2 * math.sin(2.0 * math.pi / 3.0))
    _set_init_const_by_name(block, f"i_C_{pilot_name}", 0.2 * math.sin(2.0 * math.pi / 3.0))

    return PilotModel(
        name="TheveninGeneratorEMTPilot",
        model=block,
        outputs=(
            f"i_A_{pilot_name}",
            f"i_B_{pilot_name}",
            f"i_C_{pilot_name}",
        ),
        stop_time=1e-3,
        fmpy_start_values={},
        smoke_set_values={},
        input_builder=lambda stop_time: _three_phase_input_signal(stop_time, amplitude=1.0, frequency_hz=50.0, name_prefix=pilot_name),
    )


def build_frequency_load_rms_powerfactory_pilot() -> PilotModel:
    pilot = build_frequency_load_rms_pilot()
    block = _safe_block_copy(pilot.model)
    for variable in list(block.in_vars):
        if variable.name == "Vm_":
            block.event_dict[variable] = Const(1.0)
        elif variable.name == "Va_":
            block.event_dict[variable] = Const(0.0)
        else:
            raise KeyError(f"Unexpected RMS pilot input {variable.name!r}")
    block.in_vars = []
    return PilotModel(
        name="FrequencyLoadPilotPF",
        model=block,
        outputs=pilot.outputs,
        stop_time=pilot.stop_time,
        fmpy_start_values={},
        smoke_set_values={},
        input_builder=lambda stop_time: None,
    )


def build_thevenin_generator_emt_powerfactory_pilot() -> PilotModel:
    pilot = build_thevenin_generator_emt_pilot()
    block = _safe_block_copy(pilot.model)
    if len(block.in_vars) != 3:
        raise ValueError("Expected three EMT voltage inputs for the PowerFactory pilot")

    v_a, v_b, v_c = block.in_vars
    t = Var("glob_time")
    omega = Const(2.0 * math.pi * 50.0)
    phase = Const(2.0 * math.pi / 3.0)

    block.algebraic_vars.extend([v_a, v_b, v_c])
    block.algebraic_eqs.extend(
        [
            v_a - sym.sin(omega * t),
            v_b - sym.sin(omega * t - phase),
            v_c - sym.sin(omega * t + phase),
        ]
    )
    block.init_eqs[v_a] = Const(0.0)
    block.init_eqs[v_b] = Const(-math.sin(2.0 * math.pi / 3.0))
    block.init_eqs[v_c] = Const(math.sin(2.0 * math.pi / 3.0))
    block.in_vars = []

    return PilotModel(
        name="TheveninGeneratorEMTPilotPF",
        model=block,
        outputs=pilot.outputs,
        stop_time=pilot.stop_time,
        fmpy_start_values={},
        smoke_set_values={},
        input_builder=lambda stop_time: None,
    )


def get_pilot_model(name: str) -> PilotModel:
    pilots = {
        "rms": build_frequency_load_rms_pilot,
        "emt": build_thevenin_generator_emt_pilot,
    }
    try:
        return pilots[name.lower()]()
    except KeyError as exc:
        raise KeyError(f"Unknown pilot model {name!r}. Available pilots: {', '.join(sorted(pilots))}") from exc


def get_powerfactory_pilot_model(name: str) -> PilotModel:
    pilots = {
        "rms": build_frequency_load_rms_powerfactory_pilot,
        "emt": build_thevenin_generator_emt_powerfactory_pilot,
    }
    try:
        return pilots[name.lower()]()
    except KeyError as exc:
        raise KeyError(f"Unknown PowerFactory pilot model {name!r}. Available pilots: {', '.join(sorted(pilots))}") from exc


def pilot_output_path(base_dir: str | Path, pilot: PilotModel) -> Path:
    return Path(base_dir) / f"{pilot.name}.fmu"
