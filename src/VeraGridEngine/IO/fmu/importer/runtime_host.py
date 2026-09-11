# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from ctypes import c_double
import math
import os
from pathlib import Path
from typing import Any, Optional
import shutil

from VeraGridEngine.IO.fmu.importer.bindings import FmuImportConfig
from VeraGridEngine.IO.fmu.importer.errors import FmuArchiveError, FmuDependencyError, FmuModeError
from VeraGridEngine.IO.fmu.importer.model_description import (
    FmuInterfaceMode,
    FmuModelDescription,
    FmuVariableDescription,
    read_fmu_model_description,
)
from VeraGridEngine.IO.fmu.importer.native_binary import validate_native_binary
from VeraGridEngine.IO.fmu.importer.staging import (
    FmuStagingArea,
    revalidate_fmu_staging_area,
    stage_fmu_source,
)
from VeraGridEngine.enumerations import FmiVersion, FmuVariableType

try:
    import fmpy
    import fmpy.fmi2
except ModuleNotFoundError:
    fmpy = None


def _require_fmpy_module() -> Any:
    """Import the `fmpy` package used as FMI runtime host.

    :return: Imported `fmpy` module.
    """

    if fmpy is None:
        raise FmuDependencyError("FMPy is required to execute imported FMUs")
    else:
        return fmpy


def _construct_fmi_two_runtime(
    runtime_tpe: type,
    guid: str,
    model_identifier: str,
    extracted_dir: Path,
    instance_name: str,
) -> Any:
    """Construct an FMPy FMI 2 runtime while retaining partial native ownership.

    FMPy loads the shared library before resolving its FMI symbols. Allocating
    the Python object first preserves access to that library when ``__init__``
    fails during symbol resolution, which is required for deterministic cleanup
    on Windows.

    :param runtime_tpe: FMPy FMI 2 runtime class selected for the interface mode.
    :param guid: FMI model GUID read from the staged model description.
    :param model_identifier: Native model identifier selected for the interface.
    :param extracted_dir: Private staged FMU directory containing the binary.
    :param instance_name: FMI instance name used by the runtime wrapper.
    :return: Fully constructed FMPy FMI 2 runtime object.
    """

    # Retain the object before FMPy starts loading native state. A normal class
    # call assigns no caller-visible reference when ``__init__`` raises.
    runtime: Any = runtime_tpe.__new__(runtime_tpe)
    try:
        runtime_tpe.__init__(
            runtime,
            guid=guid,
            modelIdentifier=model_identifier,
            unzipDirectory=str(extracted_dir),
            instanceName=instance_name,
        )
    except Exception:
        # The DLL attribute exists only after LoadLibrary succeeds. Direct
        # access is intentional: AttributeError means that no library was
        # acquired, while any native cleanup error must not hide the load error.
        try:
            runtime.freeLibrary()
        except (AttributeError, OSError):
            pass
        raise
    return runtime


class FmiTwoEventUpdate:
    """Store one typed FMI 2 Event Mode iteration result.

    :param discrete_states_need_update: Whether another event iteration is required.
    :param terminate_simulation: Whether the FMU requested termination.
    :param nominals_changed: Whether continuous-state nominals changed.
    :param states_changed: Whether continuous state values changed.
    :param next_event_time: Validated raw next event time when defined.
    """

    __slots__ = (
        "discrete_states_need_update",
        "terminate_simulation",
        "nominals_changed",
        "states_changed",
        "next_event_time",
    )

    def __init__(
        self,
        discrete_states_need_update: bool,
        terminate_simulation: bool,
        nominals_changed: bool,
        states_changed: bool,
        next_event_time: float | None,
    ) -> None:
        """Store one normalized FMI 2 event update.

        :param discrete_states_need_update: Native newDiscreteStatesNeeded flag.
        :param terminate_simulation: Native terminateSimulation flag.
        :param nominals_changed: Native nominalsOfContinuousStatesChanged flag.
        :param states_changed: Native valuesOfContinuousStatesChanged flag.
        :param next_event_time: Raw nextEventTime when its defined flag is true.
        :return: None.
        """

        self.discrete_states_need_update: bool = bool(
            discrete_states_need_update
        )
        self.terminate_simulation: bool = bool(terminate_simulation)
        self.nominals_changed: bool = bool(nominals_changed)
        self.states_changed: bool = bool(states_changed)
        if next_event_time is None:
            self.next_event_time: float | None = None
        else:
            self.next_event_time = float(next_event_time)


class FmuRuntimeHost:
    """Wrap one instantiated FMI 2.0 runtime object hosted through FMPy.

    :param config: FMU runtime configuration.
    :param metadata: Parsed FMU metadata.
    :param mode: Selected FMI execution mode.
    :param extracted_dir: Runtime extraction directory.
    :param owns_extracted_dir: Whether the host must delete the extraction directory.
    :param model_description: FMPy model-description object.
    :param runtime: FMPy FMU runtime object.
    :param staging_area: Optional private staging owner used by the runtime factory.
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
        "staging_area",
        "runtime_released",
        "closed",
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
        staging_area: FmuStagingArea | None = None,
    ) -> None:
        """Store the instantiated FMU runtime wrapper.

        :param config: FMU runtime configuration.
        :param metadata: Metadata parsed from the original FMU source.
        :param mode: Selected FMI execution mode.
        :param extracted_dir: Private directory consumed by FMPy.
        :param owns_extracted_dir: Legacy ownership flag for direct construction.
        :param model_description: FMPy model-description object.
        :param runtime: Instantiated FMPy runtime object.
        :param staging_area: Private staging owner or ``None`` for legacy callers.
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
        self.staging_area: FmuStagingArea | None = staging_area
        self.runtime_released: bool = False
        self.closed: bool = False

    def initialize(
        self,
        start_time: float = 0.0,
        stop_time: float | None = None,
        start_values: dict[str, float] | None = None,
        integer_start_variable_names: tuple[str, ...] = tuple(),
        integer_start_values: tuple[int, ...] = tuple(),
    ) -> None:
        """Initialize the FMI runtime after instantiation.

        :param start_time: FMU start time.
        :param stop_time: Optional FMU stop time.
        :param start_values: Optional scalar-variable start values.
        :param integer_start_variable_names: Ordered FMI 2 Integer variables to
            initialize.
        :param integer_start_values: Ordered signed Int32 values paired with
            ``integer_start_variable_names``.
        :return: None.
        """

        tolerance: float | None = self.config.relative_tolerance
        integer_value_references: tuple[int, ...]
        validated_integer_values: tuple[int, ...]
        integer_value_references, validated_integer_values = (
            self._resolve_integer_initialization(
                variable_names=integer_start_variable_names,
                values=integer_start_values,
            )
        )

        # The FMI initialization phase is where initial parameters and inputs must be injected.
        try:
            self.runtime.setupExperiment(
                tolerance=tolerance,
                startTime=start_time,
                stopTime=stop_time,
            )
            self.runtime.enterInitializationMode()
            if start_values is not None:
                if len(start_values) > 0:
                    self.set_real(start_values)
                else:
                    pass
            else:
                pass
            if len(integer_value_references) > 0:
                self.runtime.setInteger(
                    list(integer_value_references),
                    list(validated_integer_values),
                )
            else:
                pass
            self.runtime.exitInitializationMode()
            self.initialized = True
        except Exception:
            # A partially initialized native instance cannot be reused safely.
            self.close()
            raise

    def _resolve_integer_initialization(
        self,
        variable_names: tuple[str, ...],
        values: tuple[int, ...],
    ) -> tuple[tuple[int, ...], tuple[int, ...]]:
        """Validate and resolve one complete FMI 2 Integer initialization batch.

        Validation is completed before ``setupExperiment`` so malformed input
        cannot leave the native lifecycle partially advanced.

        :param variable_names: Ordered FMI 2 Integer variable names.
        :param values: Ordered signed Int32 values.
        :return: Ordered value references and normalized integer values.
        :raises ValueError: If cardinality, uniqueness, or value typing is invalid.
        :raises FmuModeError: If metadata does not permit initialization writes.
        """

        if len(variable_names) == len(values):
            pass
        else:
            raise ValueError(
                "FMI 2 Integer initialization names and values must align"
            )
        value_references: list[int] = [0] * len(variable_names)
        normalized_values: list[int] = [0] * len(values)
        names_seen: set[str] = set()
        variable_index: int
        for variable_index in range(len(variable_names)):
            variable_name: str = variable_names[variable_index]
            if variable_name in names_seen:
                raise ValueError(
                    f"Duplicate FMI 2 Integer variable {variable_name!r}"
                )
            else:
                names_seen.add(variable_name)
            value: int = values[variable_index]
            if type(value) is int:
                if -2147483648 <= value <= 2147483647:
                    normalized_values[variable_index] = value
                else:
                    raise ValueError("FMI 2 Integer value is outside signed Int32")
            else:
                raise ValueError("FMI 2 Integer values must be Python int values")
            variable: FmuVariableDescription = self.metadata.get_variable(
                variable_name
            )
            if variable.variable_type == FmuVariableType.INTEGER:
                pass
            else:
                raise FmuModeError(
                    f"FMI 2 variable {variable_name!r} is not Integer"
                )
            initialization_writable: bool = (
                variable.causality == "input"
                or (
                    variable.causality == "parameter"
                    and variable.variability in (None, "fixed", "tunable")
                )
            )
            if initialization_writable:
                value_references[variable_index] = variable.value_reference
            else:
                raise FmuModeError(
                    f"FMI 2 Integer variable {variable_name!r} is not writable "
                    "during Initialization Mode"
                )
        return tuple(value_references), tuple(normalized_values)

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

    def set_integer(
        self,
        variable_names: tuple[str, ...],
        values: tuple[int, ...],
    ) -> None:
        """Write one ordered FMI 2 Integer batch during runtime execution.

        :param variable_names: Ordered input or tunable-parameter names.
        :param values: Ordered signed Int32 values.
        :return: None.
        :raises FmuModeError: If lifecycle or metadata forbids the write.
        :raises ValueError: If the batch is malformed.
        """

        access_is_live: bool = (
            self.initialized
            and not self.terminated
            and not self.runtime_released
            and not self.closed
        )
        if access_is_live:
            pass
        else:
            raise FmuModeError("FMI 2 Integer write requires a live initialized runtime")
        # Runtime execution has a narrower write matrix than Initialization
        # Mode. Check that matrix first so a rejected output or fixed parameter
        # is reported against the phase the caller is actually using.
        variable_index: int
        for variable_index in range(len(variable_names)):
            variable: FmuVariableDescription = self.metadata.get_variable(
                variable_names[variable_index]
            )
            operationally_writable: bool = (
                variable.causality == "input"
                or (
                    variable.causality == "parameter"
                    and variable.variability == "tunable"
                )
            )
            if operationally_writable:
                pass
            else:
                raise FmuModeError(
                    f"FMI 2 Integer variable {variable.name!r} is not writable "
                    "during runtime execution"
                )
        value_references: tuple[int, ...]
        normalized_values: tuple[int, ...]
        value_references, normalized_values = self._resolve_integer_initialization(
            variable_names=variable_names,
            values=values,
        )
        if len(value_references) > 0:
            try:
                self.runtime.setInteger(
                    list(value_references),
                    list(normalized_values),
                )
            except Exception:
                self.close()
                raise
        else:
            pass

    def get_integer(
        self,
        variable_names: tuple[str, ...],
    ) -> tuple[int, ...]:
        """Read one ordered FMI 2 Integer batch from a live runtime.

        :param variable_names: Ordered FMI 2 Integer variable names.
        :return: Integer values in the same order as ``variable_names``.
        :raises FmuModeError: If lifecycle or metadata forbids the read.
        :raises ValueError: If a variable name is duplicated.
        """

        access_is_live: bool = (
            self.initialized
            and not self.terminated
            and not self.runtime_released
            and not self.closed
        )
        if access_is_live:
            pass
        else:
            raise FmuModeError("FMI 2 Integer read requires a live initialized runtime")
        value_references: list[int] = [0] * len(variable_names)
        names_seen: set[str] = set()
        variable_index: int
        for variable_index in range(len(variable_names)):
            variable_name: str = variable_names[variable_index]
            if variable_name in names_seen:
                raise ValueError(
                    f"Duplicate FMI 2 Integer variable {variable_name!r}"
                )
            else:
                names_seen.add(variable_name)
            variable: FmuVariableDescription = self.metadata.get_variable(
                variable_name
            )
            if variable.variable_type == FmuVariableType.INTEGER:
                value_references[variable_index] = variable.value_reference
            else:
                raise FmuModeError(
                    f"FMI 2 variable {variable_name!r} is not Integer"
                )
        if len(value_references) > 0:
            try:
                runtime_values: list[int] = self.runtime.getInteger(
                    value_references
                )
            except Exception:
                self.close()
                raise
            if len(runtime_values) == len(value_references):
                normalized_values: list[int] = [0] * len(runtime_values)
                for variable_index in range(len(runtime_values)):
                    normalized_values[variable_index] = int(
                        runtime_values[variable_index]
                    )
                return tuple(normalized_values)
            else:
                self.close()
                raise FmuModeError(
                    "FMI 2 Integer runtime returned an invalid cardinality"
                )
        else:
            return tuple()

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

    def get_event_indicators(self) -> list[float]:
        """Read the complete finite FMI 2 event-indicator vector.

        :return: Indicators in model-description order.
        :raises FmuModeError: If cardinality or finiteness is invalid.
        """

        if self.mode == FmuInterfaceMode.MODEL_EXCHANGE:
            number_of_indicators: int = self.metadata.number_of_event_indicators
            if number_of_indicators > 0:
                indicator_buffer = (c_double * number_of_indicators)()
                self.runtime.getEventIndicators(
                    indicator_buffer,
                    number_of_indicators,
                )
                indicator_values: list[float] = [0.0] * number_of_indicators
                indicator_index: int
                for indicator_index in range(number_of_indicators):
                    indicator_value: float = float(
                        indicator_buffer[indicator_index]
                    )
                    if math.isfinite(indicator_value):
                        indicator_values[indicator_index] = indicator_value
                    else:
                        raise FmuModeError(
                            "FMI 2 event indicators must be finite"
                        )
                return indicator_values
            else:
                return list()
        else:
            raise FmuModeError(
                "get_event_indicators() is only valid for Model Exchange FMUs"
            )

    def needs_completed_integrator_step(self) -> bool:
        """Return whether the FMI 2 model requires completed-step notification.

        :return: Inverse of completedIntegratorStepNotNeeded.
        """

        if self.mode == FmuInterfaceMode.MODEL_EXCHANGE:
            completed_step_not_needed: bool = bool(
                self.model_description.modelExchange.completedIntegratorStepNotNeeded
            )
            return not completed_step_not_needed
        else:
            raise FmuModeError(
                "needs_completed_integrator_step() is only valid for Model Exchange FMUs"
            )

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

    def new_discrete_states(self) -> FmiTwoEventUpdate:
        """Advance the discrete-event iteration of a Model Exchange FMU.

        :return: Typed event information detached from the FMPy structure.
        """

        if self.mode == FmuInterfaceMode.MODEL_EXCHANGE:
            event_info: tuple[bool, bool, bool, bool, bool, float] = (
                self.runtime.newDiscreteStates()
            )
            if event_info[4]:
                next_event_time: float | None = float(event_info[5])
            else:
                next_event_time = None
            return FmiTwoEventUpdate(
                discrete_states_need_update=event_info[0],
                terminate_simulation=event_info[1],
                nominals_changed=event_info[2],
                states_changed=event_info[3],
                next_event_time=next_event_time,
            )
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
        """Release the FMI runtime and its private staging area exactly once.

        :return: None.
        """

        if self.closed:
            pass
        else:
            # Native resources are released once, before any DLL-containing
            # staging tree is removed. Uninitialized instances must not receive
            # the FMI terminate transition.
            if self.runtime_released:
                pass
            else:
                if self.initialized and not self.terminated:
                    try:
                        self.runtime.terminate()
                    except Exception:
                        pass
                    self.terminated = True
                else:
                    pass
                try:
                    self.runtime.freeInstance()
                except Exception:
                    pass
                self.runtime_released = True

            # The staging owner is authoritative for factory-created hosts. The
            # legacy boolean path remains only for compatible direct construction.
            if self.staging_area is None:
                if self.owns_extracted_dir:
                    shutil.rmtree(self.extracted_dir, ignore_errors=True)
                else:
                    pass
            else:
                self.staging_area.close()
            self.closed = True

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
    """Instantiate an FMI 2.0 runtime from a content-bound private snapshot.

    :param config: Runtime configuration for the FMU host.
    :return: Open runtime host.
    :raises FmuModeError: If the FMU is not an FMI 2 model.
    """

    metadata: FmuModelDescription = read_fmu_model_description(config.fmu_path)
    # This in-process FMPy owner is intentionally limited to FMI 2. FMI 3 is
    # executed only through the bounded worker session, so reject it before
    # dependency checks, native validation, or private staging side effects.
    if metadata.fmi_version_family == FmiVersion.FMI_2_0:
        pass
    else:
        raise FmuModeError(
            f"FmuRuntimeHost supports FMI 2 execution only, got FMI {metadata.fmi_version}"
        )
    mode: FmuInterfaceMode = config.resolve_execution_mode(metadata)
    fmpy_module: Any = _require_fmpy_module()
    if metadata.inspection_receipt is None:
        raise FmuArchiveError("FMU runtime metadata does not include an inspection receipt")
    else:
        pass
    model_identifier: str = metadata.get_model_identifier(mode)

    # Reject an incompatible or misplaced native library before allocating a
    # private staging tree. Inspection remains the authority for source paths.
    validate_native_binary(
        receipt=metadata.inspection_receipt,
        fmi_version_family=metadata.fmi_version_family,
        model_identifier=model_identifier,
    )
    staging_area: FmuStagingArea = stage_fmu_source(
        metadata.path,
        metadata.inspection_receipt,
        staging_parent=config.extraction_root,
    )
    extracted_dir: Path = staging_area.get_fmu_directory()
    runtime: Any | None = None
    runtime_instantiated: bool = False
    working_directory_before_load: Path = Path.cwd()

    try:
        fmi2_module: Any = fmpy_module.fmi2
        model_description: Any = fmpy_module.read_model_description(str(extracted_dir))

        # FMPy parses the staged XML independently. Both parsers must agree
        # before the native library selected by that metadata can be loaded.
        common_metadata_matches: bool = (
            model_description.fmiVersion == metadata.fmi_version
            and model_description.modelName == metadata.model_name
            and model_description.guid == metadata.guid
        )
        if common_metadata_matches:
            pass
        else:
            raise FmuArchiveError("FMPy metadata differs from the inspected FMU metadata")
        if mode == FmuInterfaceMode.CO_SIMULATION:
            if (
                model_description.coSimulation is not None
                and model_description.coSimulation.modelIdentifier == model_identifier
            ):
                pass
            else:
                raise FmuArchiveError("FMPy Co-Simulation metadata differs from the inspected FMU")
        else:
            if mode == FmuInterfaceMode.MODEL_EXCHANGE:
                if (
                    model_description.modelExchange is not None
                    and model_description.modelExchange.modelIdentifier == model_identifier
                ):
                    pass
                else:
                    raise FmuArchiveError("FMPy Model Exchange metadata differs from the inspected FMU")
            else:
                raise FmuModeError(f"Unsupported FMI mode {mode.value}")

        # The staged tree is revalidated after XML parsing and immediately
        # before the FMPy constructor can load its native library.
        revalidate_fmu_staging_area(staging_area)

        # The FMI runtime implementation depends on the selected execution mode.
        if mode == FmuInterfaceMode.CO_SIMULATION:
            runtime = _construct_fmi_two_runtime(
                runtime_tpe=fmi2_module.FMU2Slave,
                guid=model_description.guid,
                model_identifier=model_identifier,
                extracted_dir=extracted_dir,
                instance_name=model_description.modelName,
            )
        else:
            if mode == FmuInterfaceMode.MODEL_EXCHANGE:
                runtime = _construct_fmi_two_runtime(
                    runtime_tpe=fmi2_module.FMU2Model,
                    guid=model_description.guid,
                    model_identifier=model_identifier,
                    extracted_dir=extracted_dir,
                    instance_name=model_description.modelName,
                )
            else:
                raise FmuModeError(f"Unsupported FMI mode {mode.value}")

        # The FMU instance is created immediately so callers always receive a ready-to-init host.
        runtime.instantiate(visible=config.visible, loggingOn=config.debug_logging)
        runtime_instantiated = True
        return FmuRuntimeHost(
            config=config,
            metadata=metadata,
            mode=mode,
            extracted_dir=extracted_dir,
            owns_extracted_dir=True,
            model_description=model_description,
            runtime=runtime,
            staging_area=staging_area,
        )
    except Exception:
        # FMPy changes the process working directory while loading a DLL and
        # does not restore it when LoadLibrary raises. Restore that process
        # state before Windows cleanup attempts to remove the binary folder.
        current_working_directory: Path = Path.cwd()
        if current_working_directory == working_directory_before_load:
            pass
        else:
            os.chdir(working_directory_before_load)
        # A constructor can load the DLL before FMI instantiation. Release the
        # strongest state known, then remove the private staging child.
        if runtime is None:
            pass
        else:
            try:
                if runtime_instantiated:
                    runtime.freeInstance()
                else:
                    runtime.freeLibrary()
            except Exception:
                pass
        staging_area.close()
        raise
