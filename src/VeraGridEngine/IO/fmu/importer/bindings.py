# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from enum import Enum
from pathlib import Path

from VeraGridEngine.IO.fmu.importer.errors import FmuBindingError
from VeraGridEngine.IO.fmu.importer.model_description import FmuInterfaceMode, FmuModelDescription


class FmuBindingDirection(str, Enum):
    """Declare how a VeraGrid signal is connected to an FMU scalar variable."""

    INPUT = "input"
    OUTPUT = "output"
    PARAMETER = "parameter"


class FmuVariableBinding:
    """Describe one logical binding between VeraGrid and an FMU variable."""

    __slots__ = ("signal_name", "variable_name", "direction", "scale", "offset")

    def __init__(
        self,
        signal_name: str,
        variable_name: str,
        direction: FmuBindingDirection,
        scale: float = 1.0,
        offset: float = 0.0,
    ) -> None:
        """Store the FMU binding metadata for one signal."""

        self.signal_name: str = signal_name
        self.variable_name: str = variable_name
        self.direction: FmuBindingDirection = direction
        self.scale: float = float(scale)
        self.offset: float = float(offset)


class FmuImportConfig:
    """Store the runtime configuration required to execute an imported FMU."""

    __slots__ = (
        "fmu_path",
        "preferred_mode",
        "bindings",
        "communication_step",
        "relative_tolerance",
        "extraction_root",
        "visible",
        "debug_logging",
    )

    def __init__(
        self,
        fmu_path: str | Path,
        preferred_mode: FmuInterfaceMode | None = None,
        bindings: tuple[FmuVariableBinding, ...] = tuple(),
        communication_step: float | None = None,
        relative_tolerance: float | None = None,
        extraction_root: str | Path | None = None,
        visible: bool = False,
        debug_logging: bool = False,
    ) -> None:
        """Store the runtime options for the imported FMU host."""

        self.fmu_path: Path = Path(fmu_path).expanduser()
        self.preferred_mode: FmuInterfaceMode | None = preferred_mode
        self.bindings: tuple[FmuVariableBinding, ...] = bindings
        if communication_step is None:
            self.communication_step = None
        else:
            if communication_step > 0.0:
                self.communication_step = float(communication_step)
            else:
                raise ValueError("communication_step must be positive when provided")
        if relative_tolerance is None:
            self.relative_tolerance = None
        else:
            if relative_tolerance > 0.0:
                self.relative_tolerance = float(relative_tolerance)
            else:
                raise ValueError("relative_tolerance must be positive when provided")
        if extraction_root is None:
            self.extraction_root = None
        else:
            self.extraction_root = Path(extraction_root).expanduser()
        self.visible: bool = bool(visible)
        self.debug_logging: bool = bool(debug_logging)

    def resolve_mode(self, metadata: FmuModelDescription) -> FmuInterfaceMode:
        """Resolve the FMU execution mode to use with the provided metadata."""

        return metadata.resolve_mode(self.preferred_mode)


def validate_bindings(metadata: FmuModelDescription, bindings: tuple[FmuVariableBinding, ...]) -> None:
    """Validate that the VeraGrid bindings respect the FMU variable causalities."""

    seen_signal_names: set[tuple[str, FmuBindingDirection]] = set()
    binding: FmuVariableBinding
    for binding in bindings:
        key: tuple[str, FmuBindingDirection] = (binding.signal_name, binding.direction)
        if key in seen_signal_names:
            raise FmuBindingError(
                f"Duplicate FMU binding for signal {binding.signal_name!r} and direction {binding.direction.value!r}"
            )
        else:
            seen_signal_names.add(key)

        variable = metadata.get_variable(binding.variable_name)
        causality: str = variable.causality or "local"
        if binding.direction == FmuBindingDirection.INPUT:
            if causality not in {"input", "parameter"}:
                raise FmuBindingError(
                    f"Variable {binding.variable_name!r} is not bindable as FMU input (causality={causality!r})"
                )
            else:
                pass
        else:
            if binding.direction == FmuBindingDirection.OUTPUT:
                if causality not in {"output", "local"}:
                    raise FmuBindingError(
                        f"Variable {binding.variable_name!r} is not bindable as FMU output (causality={causality!r})"
                    )
                else:
                    pass
            else:
                if binding.direction == FmuBindingDirection.PARAMETER:
                    if causality != "parameter":
                        raise FmuBindingError(
                            f"Variable {binding.variable_name!r} is not bindable as FMU parameter (causality={causality!r})"
                        )
                    else:
                        pass
                else:
                    raise FmuBindingError(f"Unsupported FMU binding direction {binding.direction!r}")
