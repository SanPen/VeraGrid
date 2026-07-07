from __future__ import annotations

from pathlib import Path

import pytest

from VeraGridEngine.IO.fmu.importer.bindings import FmuBindingDirection, FmuVariableBinding, validate_bindings
from VeraGridEngine.IO.fmu.importer.model_description import FmuInterfaceMode, read_fmu_model_description


def _artifacts_root() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "fmi" / "artifacts"


def _known_fmi_platforms() -> set[str]:
    known_platforms: set[str] = set()
    known_platforms.add("win64")
    known_platforms.add("linux64")
    known_platforms.add("darwin64")
    return known_platforms


def test_read_existing_co_simulation_fmu_metadata() -> None:
    fmu_path = _artifacts_root() / "FrequencyLoadPilot.fmu"
    metadata = read_fmu_model_description(fmu_path)

    assert metadata.fmi_version == "2.0"
    assert metadata.get_supports_co_simulation() is True
    assert metadata.get_supports_model_exchange() is False
    assert metadata.resolve_mode() == FmuInterfaceMode.CO_SIMULATION
    assert metadata.get_model_identifier(FmuInterfaceMode.CO_SIMULATION) != ""
    assert len(metadata.platforms) > 0
    assert set(metadata.platforms).issubset(_known_fmi_platforms())
    assert any(variable.causality == "input" for variable in metadata.variables)
    assert any(variable.causality == "output" for variable in metadata.variables)


def test_validate_bindings_uses_fmu_causality() -> None:
    fmu_path = _artifacts_root() / "FrequencyLoadPilot.fmu"
    metadata = read_fmu_model_description(fmu_path)
    input_var = next(variable for variable in metadata.variables if variable.causality == "input")
    output_var = next(variable for variable in metadata.variables if variable.causality == "output")

    validate_bindings(
        metadata,
        (
            FmuVariableBinding(signal_name="bus_voltage", variable_name=input_var.name, direction=FmuBindingDirection.INPUT),
            FmuVariableBinding(signal_name="active_power", variable_name=output_var.name, direction=FmuBindingDirection.OUTPUT),
        ),
    )

    with pytest.raises(Exception):
        validate_bindings(
            metadata,
            (FmuVariableBinding(signal_name="bad", variable_name=input_var.name, direction=FmuBindingDirection.OUTPUT),),
        )
