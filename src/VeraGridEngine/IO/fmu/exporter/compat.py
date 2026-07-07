# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import Any
import sys
import types


_ENGINE_ROOT = Path(__file__).resolve().parents[3]
_SRC_ROOT = _ENGINE_ROOT.parent
_REPO_ROOT = _SRC_ROOT.parent


def _ensure_package(name: str, path: Path) -> ModuleType:
    module = sys.modules.get(name)
    if module is None:
        module = types.ModuleType(name)
        module.__path__ = [str(path)]
        sys.modules[name] = module
    return module


def _load_module(name: str, path: Path) -> ModuleType:
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module {name!r} from {path}")
    module = module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _install_matplotlib_stub() -> None:
    matplotlib_module = sys.modules.get("matplotlib")
    if matplotlib_module is None:
        matplotlib_module = types.ModuleType("matplotlib")
        matplotlib_module.__path__ = []
        sys.modules["matplotlib"] = matplotlib_module
    for submodule_name in ("pyplot", "colors", "cm"):
        full_name = f"matplotlib.{submodule_name}"
        if full_name not in sys.modules:
            submodule = types.ModuleType(full_name)
            sys.modules[full_name] = submodule
            setattr(matplotlib_module, submodule_name, submodule)
    pyplot_module = sys.modules["matplotlib.pyplot"]
    if not hasattr(pyplot_module, "axis"):
        setattr(pyplot_module, "axis", object)


def _install_procedural_logic_stub() -> None:
    module_name = "VeraGridEngine.Utils.procedural_logic"
    stub = sys.modules.get(module_name)
    if stub is None:
        stub = types.ModuleType(module_name)
        sys.modules[module_name] = stub

    def _entry_to_dict(entry: Any) -> dict[str, Any]:
        if isinstance(entry, dict):
            return dict(entry)
        if hasattr(entry, "to_dict") and callable(entry.to_dict):
            return dict(entry.to_dict())

        logic_type = getattr(getattr(entry, "logic_tpe", None), "value", None)
        data: dict[str, Any] = {
            "logic_type": logic_type or type(entry).__name__.lower(),
            "name": getattr(entry, "name", ""),
        }

        for field_name in (
            "output_var_name",
            "condition_expr",
            "source_expr",
            "set_expr",
            "reset_expr",
            "bool_expr",
            "pickup_delay_expr",
            "drop_delay_expr",
            "target_var_name",
            "value_expr",
            "monitored_var_name",
            "mode_var_name",
            "threshold",
            "delay",
            "reset_delay",
        ):
            if hasattr(entry, field_name):
                value = getattr(entry, field_name)
                data[field_name] = value if isinstance(value, (int, float, str, dict)) else value.to_dict() if hasattr(value, "to_dict") else value
        return data

    def procedural_logic_to_dict(entries: list[Any]) -> list[dict[str, Any]]:
        return [_entry_to_dict(entry) for entry in entries]

    def procedural_logic_from_dict(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [dict(entry) for entry in entries]

    stub.procedural_logic_to_dict = procedural_logic_to_dict
    stub.procedural_logic_from_dict = procedural_logic_from_dict


def _install_generator_stub() -> None:
    package_name = "VeraGridEngine.Devices.Injections"
    module_name = f"{package_name}.generator"
    _ensure_package(package_name, _ENGINE_ROOT / "Devices" / "Injections")
    if module_name in sys.modules:
        return

    stub = types.ModuleType(module_name)

    class Generator:
        def __init__(self, **kwargs: Any):
            for key, value in kwargs.items():
                setattr(self, key, value)

    stub.Generator = Generator
    sys.modules[module_name] = stub


if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

_install_matplotlib_stub()

_ensure_package("VeraGridEngine", _ENGINE_ROOT)
_ensure_package("VeraGridEngine.Utils", _ENGINE_ROOT / "Utils")
_ensure_package("VeraGridEngine.Utils.Symbolic", _ENGINE_ROOT / "Utils" / "Symbolic")
_ensure_package("VeraGridEngine.Utils.Sparse", _ENGINE_ROOT / "Utils" / "Sparse")
_ensure_package("VeraGridEngine.Devices", _ENGINE_ROOT / "Devices")
_ensure_package("VeraGridEngine.Devices.Parents", _ENGINE_ROOT / "Devices" / "Parents")
_ensure_package("VeraGridEngine.Devices.Dynamic", _ENGINE_ROOT / "Devices" / "Dynamic")
_ensure_package("VeraGridEngine.Devices.Diagrams", _ENGINE_ROOT / "Devices" / "Diagrams")
_ensure_package("VeraGridEngine.Templates", _ENGINE_ROOT / "Templates")
_ensure_package("VeraGridEngine.Templates.Emt", _ENGINE_ROOT / "Templates" / "Emt")
_ensure_package("VeraGridEngine.Templates.Rms", _ENGINE_ROOT / "Templates" / "Rms")

_install_procedural_logic_stub()
_install_generator_stub()

enumerations = _load_module("VeraGridEngine.enumerations", _ENGINE_ROOT / "enumerations.py")
engine_package = sys.modules["VeraGridEngine"]
for attr_name in dir(enumerations):
    if attr_name.startswith("_"):
        continue
    setattr(engine_package, attr_name, getattr(enumerations, attr_name))
setattr(engine_package, "MultiCircuit", object)

_load_module("VeraGridEngine.Devices.Diagrams.block_diagram", _ENGINE_ROOT / "Devices" / "Diagrams" / "block_diagram.py")
symbolic = _load_module("VeraGridEngine.Utils.Symbolic.symbolic", _ENGINE_ROOT / "Utils" / "Symbolic" / "symbolic.py")
block_module = _load_module("VeraGridEngine.Utils.Symbolic.block", _ENGINE_ROOT / "Utils" / "Symbolic" / "block.py")
procedural_logic_module = sys.modules["VeraGridEngine.Utils.procedural_logic"]

Block = block_module.Block
BinOp = symbolic.BinOp
CmpOp = symbolic.CmpOp
Comparison = symbolic.Comparison
Const = symbolic.Const
Expr = symbolic.Expr
Func = symbolic.Func
Func2 = symbolic.Func2
UnOp = symbolic.UnOp
Var = symbolic.Var
_dict_to_expr = symbolic._dict_to_expr
_expr_to_dict = symbolic._expr_to_dict
procedural_logic_to_dict = procedural_logic_module.procedural_logic_to_dict
DynamicIntegrationMethod = enumerations.DynamicIntegrationMethod
ProceduralLogicType = enumerations.ProceduralLogicType

__all__ = [
    "BinOp",
    "Block",
    "CmpOp",
    "Comparison",
    "Const",
    "DynamicIntegrationMethod",
    "Expr",
    "Func",
    "Func2",
    "ProceduralLogicType",
    "UnOp",
    "Var",
    "_dict_to_expr",
    "_expr_to_dict",
    "procedural_logic_to_dict",
]
