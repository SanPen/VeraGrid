# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from ctypes import c_double
from pathlib import Path
from typing import Any, Optional
import importlib
import shutil
import tempfile

from VeraGridEngine.IO.fmu.importer.bindings import FmuImportConfig
from VeraGridEngine.IO.fmu.importer.errors import FmuDependencyError, FmuModeError
from VeraGridEngine.IO.fmu.importer.model_description import FmuInterfaceMode, FmuModelDescription, read_fmu_model_description


def _require_fmpy_module() -> Any:
    """Import the `fmpy` package used as FMI runtime host.

    :return: Imported `fmpy` module.
    """

    try:
        return importlib.import_module("fmpy")
    except ModuleNotFoundError as exc:
        raise FmuDependencyError("FMPy is required to execute imported FMUs") from exc


def _prepare_runtime_directory(fmu_path: Path, extraction_root: Path | None) -> tuple[Path, bool]:
    """Prepare the extracted directory used by the FMI runtime.

    :param fmu_path: FMU archive path or extracted directory.
    :param extraction_root: Optional trusted extraction root.
    :return: Runtime directory and ownership flag.
    """

    if fmu_path.is_dir():
        model_description_path: Path = fmu_path / "modelDescription.xml"
        if model_description_path.exists():
            return fmu_path.resolve(), False
        else:
            raise FileNotFoundError(f"FMU directory {fmu_path} does not contain modelDescription.xml")
    else:
        fmpy_module: Any = _require_fmpy_module()
        effective_root: Path
        if extraction_root is None:
            effective_root = fmu_path.parent.resolve()
        else:
            effective_root = extraction_root.expanduser().resolve()
        effective_root.mkdir(parents=True, exist_ok=True)
        runtime_dir: Path = Path(tempfile.mkdtemp(prefix=f"{fmu_path.stem}_runtime_", dir=str(effective_root)))

        # The extraction happens in a trusted location to avoid Windows DLL loading policies.
        fmpy_module.extract(str(fmu_path), unzipdir=str(runtime_dir))
        return runtime_dir, True


class FmuRuntimeHost:
    """Wrap one instantiated FMI 2.0 runtime object hosted through FMPy.

    :param config: FMU runtime configuration.
    :param metadata: Parsed FMU metadata.
    :param mode: Selected FMI execution mode.
    :param extracted_dir: Runtime extraction directory.
    :param owns_extracted_dir: Whether the host must delete the extraction directory.
    :param model_description: FMPy model-description object.
    :param runtime: FMPy FMU runtime object.
    """

    __slots__ = (
        "config",
        "metadata",
        "mode",
        "extracted_dir",
        "owns_extracted_dir",
        "model_description",
        "runtime",
        "initialized",
        "terminated",
    )

    def __init__(
        self,
        config: FmuImportConfig,
        metadata: FmuModelDescription,
        mode: FmuInterfaceMode,
        extracted_dir: Path,
        owns_extracted_dir: bool,
        model_description: Any,
        runtime: Any,
    ) -> None:
        """Store the instantiated FMU runtime wrapper.

        :return: None.
        """

        self.config: FmuImportConfig = config
        self.metadata: FmuModelDescription = metadata
        self.mode: FmuInterfaceMode = mode
        self.extracted_dir: Path = extracted_dir
        self.owns_extracted_dir: bool = owns_extracted_dir
        self.model_description: Any = model_description
        self.runtime: Any = runtime
        self.initialized: bool = False
        self.terminated: bool = False

    def initialize(
        self,
        start_time: float = 0.0,
        stop_time: float | None = None,
        start_values: dict[str, float] | None = None,
    ) -> None:
        """Initialize the FMI runtime after instantiation.

        :param start_time: FMU start time.
        :param stop_time: Optional FMU stop time.
        :param start_values: Optional scalar-variable start values.
        :return: None.
        """

        tolerance: float | None = self.config.relative_tolerance

        # The FMI initialization phase is where initial parameters and inputs must be injected.
        self.runtime.setupExperiment(tolerance=tolerance, startTime=start_time, stopTime=stop_time)
        self.runtime.enterInitializationMode()
        if start_values is not None:
            if len(start_values) > 0:
                self.set_real(start_values)
            else:
                pass
        else:
            pass
        self.runtime.exitInitializationMode()
        self.initialized = True

    def _get_value_references(self, names: list[str]) -> list[int]:
        """Resolve the FMI value references for the requested variable names.

        :param names: Ordered FMI variable names.
        :return: Matching FMI value references.
        """

        value_references: list[int] = list()
        name: str
        for name in names:
            variable = self.metadata.get_variable(name)
            value_references.append(variable.value_reference)
        return value_references

    def set_real(self, values: dict[str, float]) -> None:
        """Set one or more FMI real variables.

        :param values: Mapping from variable name to numeric value.
        :return: None.
        """

        if len(values) > 0:
            variable_names: list[str] = list(values.keys())
            value_references: list[int] = self._get_value_references(variable_names)
            numeric_values: list[float] = list()
            variable_name: str
            for variable_name in variable_names:
                numeric_values.append(float(values[variable_name]))
            self.runtime.setReal(value_references, numeric_values)
        else:
            pass

    def get_real(self, names: list[str]) -> dict[str, float]:
        """Read one or more FMI real variables.

        :param names: Ordered FMI variable names.
        :return: Mapping from variable name to numeric value.
        """

        value_references: list[int] = self._get_value_references(names)
        runtime_values: list[float] = self.runtime.getReal(value_references)
        result: dict[str, float] = dict()
        index: int
        for index, variable_name in enumerate(names):
            result[variable_name] = float(runtime_values[index])
        return result

    def do_step(self, current_time: float, step_size: float) -> None:
        """Advance a Co-Simulation FMU by one communication step.

        :param current_time: Current communication time.
        :param step_size: Requested communication step.
        :return: None.
        """

        if self.mode == FmuInterfaceMode.CO_SIMULATION:
            self.runtime.doStep(currentCommunicationPoint=current_time, communicationStepSize=step_size)
        else:
            raise FmuModeError("do_step() is only valid for Co-Simulation FMUs")

    def set_time(self, time_value: float) -> None:
        """Set the current time of a Model Exchange FMU.

        :param time_value: Time value seen by the FMI runtime.
        :return: None.
        """

        if self.mode == FmuInterfaceMode.MODEL_EXCHANGE:
            self.runtime.setTime(time_value)
        else:
            raise FmuModeError("set_time() is only valid for Model Exchange FMUs")

    def set_continuous_states(self, values: list[float]) -> None:
        """Set the continuous states of a Model Exchange FMU.

        :param values: Ordered state values.
        :return: None.
        """

        if self.mode == FmuInterfaceMode.MODEL_EXCHANGE:
            state_buffer = (c_double * len(values))(*[float(value) for value in values])
            self.runtime.setContinuousStates(state_buffer, len(values))
        else:
            raise FmuModeError("set_continuous_states() is only valid for Model Exchange FMUs")

    def get_continuous_state_count(self) -> int:
        """Return the number of continuous states declared by the FMU.

        :return: Number of continuous states.
        """

        if self.mode == FmuInterfaceMode.MODEL_EXCHANGE:
            return int(self.model_description.numberOfContinuousStates)
        else:
            raise FmuModeError("get_continuous_state_count() is only valid for Model Exchange FMUs")

    def get_continuous_states(self) -> list[float]:
        """Read the continuous-state vector of a Model Exchange FMU.

        :return: Ordered continuous-state vector.
        """

        if self.mode == FmuInterfaceMode.MODEL_EXCHANGE:
            number_of_states: int = int(self.model_description.numberOfContinuousStates)
            if number_of_states > 0:
                state_buffer = (c_double * number_of_states)()
                self.runtime.getContinuousStates(state_buffer, number_of_states)
                values: list[float] = list()
                index: int
                for index in range(number_of_states):
                    values.append(float(state_buffer[index]))
                return values
            else:
                return list()
        else:
            raise FmuModeError("get_continuous_states() is only valid for Model Exchange FMUs")

    def get_derivatives(self) -> list[float]:
        """Read the continuous derivatives of a Model Exchange FMU.

        :return: Ordered derivative vector.
        """

        if self.mode == FmuInterfaceMode.MODEL_EXCHANGE:
            number_of_states: int = int(self.model_description.numberOfContinuousStates)
            if number_of_states > 0:
                derivative_buffer = (c_double * number_of_states)()
                self.runtime.getDerivatives(derivative_buffer, number_of_states)
                values: list[float] = list()
                index: int
                for index in range(number_of_states):
                    values.append(float(derivative_buffer[index]))
                return values
            else:
                return list()
        else:
            raise FmuModeError("get_derivatives() is only valid for Model Exchange FMUs")

    def completed_integrator_step(self) -> tuple[bool, bool]:
        """Notify a Model Exchange FMU that one host integrator step completed.

        :return: Pair with `(enter_event_mode, terminate)` flags.
        """

        if self.mode == FmuInterfaceMode.MODEL_EXCHANGE:
            enter_event_mode: bool
            terminate_simulation: bool
            enter_event_mode, terminate_simulation = self.runtime.completedIntegratorStep()
            return bool(enter_event_mode), bool(terminate_simulation)
        else:
            raise FmuModeError("completed_integrator_step() is only valid for Model Exchange FMUs")

    def enter_event_mode(self) -> None:
        """Enter FMI Event Mode for a Model Exchange FMU.

        :return: None.
        """

        if self.mode == FmuInterfaceMode.MODEL_EXCHANGE:
            self.runtime.enterEventMode()
        else:
            raise FmuModeError("enter_event_mode() is only valid for Model Exchange FMUs")

    def new_discrete_states(self) -> Any:
        """Advance the discrete-event iteration of a Model Exchange FMU.

        :return: Native FMPy event-info structure.
        """

        if self.mode == FmuInterfaceMode.MODEL_EXCHANGE:
            return self.runtime.newDiscreteStates()
        else:
            raise FmuModeError("new_discrete_states() is only valid for Model Exchange FMUs")

    def enter_continuous_time_mode(self) -> None:
        """Return a Model Exchange FMU to continuous-time mode.

        :return: None.
        """

        if self.mode == FmuInterfaceMode.MODEL_EXCHANGE:
            self.runtime.enterContinuousTimeMode()
        else:
            raise FmuModeError("enter_continuous_time_mode() is only valid for Model Exchange FMUs")

    def close(self) -> None:
        """Release the FMI runtime and the temporary extraction directory.

        :return: None.
        """

        # The FMU termination must happen before the extraction directory is deleted.
        if self.terminated:
            pass
        else:
            try:
                self.runtime.terminate()
            except Exception:
                pass
            self.terminated = True

        # The instance must always be released, even when terminate() failed.
        try:
            self.runtime.freeInstance()
        except Exception:
            pass

        # Temporary directories are owned only when we extracted the FMU ourselves.
        if self.owns_extracted_dir:
            shutil.rmtree(self.extracted_dir, ignore_errors=True)
        else:
            pass

    def __enter__(self) -> "FmuRuntimeHost":
        """Return the runtime host for context-manager use.

        :return: The runtime host itself.
        """

        return self

    def __exit__(self, exc_tpe: Any, exc_value: Any, traceback_value: Any) -> None:
        """Release the runtime when exiting a context-manager scope.

        :param exc_tpe: Exception type.
        :param exc_value: Exception value.
        :param traceback_value: Exception traceback.
        :return: None.
        """

        self.close()


def open_fmu_runtime_host(config: FmuImportConfig) -> FmuRuntimeHost:
    """Instantiate a runtime host around an imported FMU.

    :param config: Runtime configuration for the FMU host.
    :return: Open runtime host.
    """

    metadata: FmuModelDescription = read_fmu_model_description(config.fmu_path)
    mode: FmuInterfaceMode = config.resolve_mode(metadata)
    extracted_dir: Path
    owns_extracted_dir: bool
    extracted_dir, owns_extracted_dir = _prepare_runtime_directory(metadata.path, config.extraction_root)

    try:
        fmpy_module: Any = _require_fmpy_module()
        fmi2_module: Any = importlib.import_module("fmpy.fmi2")
        model_description: Any = fmpy_module.read_model_description(str(extracted_dir))
        model_identifier: str = metadata.get_model_identifier(mode)

        # The FMI runtime implementation depends on the selected execution mode.
        runtime: Any
        if mode == FmuInterfaceMode.CO_SIMULATION:
            runtime = fmi2_module.FMU2Slave(
                guid=model_description.guid,
                modelIdentifier=model_identifier,
                unzipDirectory=str(extracted_dir),
                instanceName=model_description.modelName,
            )
        else:
            if mode == FmuInterfaceMode.MODEL_EXCHANGE:
                runtime = fmi2_module.FMU2Model(
                    guid=model_description.guid,
                    modelIdentifier=model_identifier,
                    unzipDirectory=str(extracted_dir),
                    instanceName=model_description.modelName,
                )
            else:
                raise FmuModeError(f"Unsupported FMI mode {mode.value}")

        # The FMU instance is created immediately so callers always receive a ready-to-init host.
        runtime.instantiate(visible=config.visible, loggingOn=config.debug_logging)
        return FmuRuntimeHost(
            config=config,
            metadata=metadata,
            mode=mode,
            extracted_dir=extracted_dir,
            owns_extracted_dir=owns_extracted_dir,
            model_description=model_description,
            runtime=runtime,
        )
    except Exception:
        if owns_extracted_dir:
            shutil.rmtree(extracted_dir, ignore_errors=True)
        else:
            pass
        raise
