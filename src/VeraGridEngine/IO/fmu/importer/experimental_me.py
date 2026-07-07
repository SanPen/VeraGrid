# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

import numpy as np

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Parents.branch_parent import BranchParent
from VeraGridEngine.Devices.Parents.injection_parent import InjectionParent
from VeraGridEngine.enumerations import DeviceType, ParamPowerFlowRefferenceType, VarPowerFlowRefferenceType
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var

from VeraGridEngine.IO.fmu.importer.bindings import FmuImportConfig
from VeraGridEngine.IO.fmu.importer.device_config import load_fmu_me_device_config, restore_fmu_me_spec_from_record
from VeraGridEngine.IO.fmu.importer.experimental_cs import FmuRefBinding, _ensure_emt_external_mapping_keys
from VeraGridEngine.IO.fmu.importer.model_description import FmuInterfaceMode, FmuModelDescription, FmuVariableDescription, read_fmu_model_description
from VeraGridEngine.IO.fmu.importer.runtime_host import FmuRuntimeHost, open_fmu_runtime_host


class FmuMeDomain(str, Enum):
    """Enumerate the VeraGrid domains that may host FMU ME devices.

    :return: None.
    """

    RMS = "rms"
    EMT = "emt"


class FmuMeIntegrationMethod(str, Enum):
    """Enumerate the internal predictor methods available for FMU ME devices.

    :return: None.
    """

    EXPLICIT_EULER = "explicit_euler"


class FmuMeDeviceSpec:
    """Store the runtime metadata required to execute one FMU ME device.

    :param domain: VeraGrid domain that will consume the FMU.
    :param config: FMU runtime configuration.
    :param device_tpe: VeraGrid device type.
    :param input_variable_names: Ordered FMU input names.
    :param output_variable_names: Ordered FMU output names.
    :param state_variable_names: Ordered FMU continuous-state names.
    :param derivative_variable_names: Ordered FMU derivative names.
    :param integration_method: Internal predictor used by the adapter.
    """

    __slots__ = (
        "domain",
        "config",
        "device_tpe",
        "input_variable_names",
        "output_variable_names",
        "state_variable_names",
        "derivative_variable_names",
        "integration_method",
        "input_bindings",
        "output_bindings",
        "output_defaults",
        "output_param_uids",
    )

    def __init__(
        self,
        domain: FmuMeDomain,
        config: FmuImportConfig,
        device_tpe: DeviceType,
        input_variable_names: tuple[str, ...],
        output_variable_names: tuple[str, ...],
        state_variable_names: tuple[str, ...],
        derivative_variable_names: tuple[str, ...],
        integration_method: FmuMeIntegrationMethod,
        input_bindings: tuple[FmuRefBinding, ...],
        output_bindings: tuple[FmuRefBinding, ...],
        output_defaults: dict[VarPowerFlowRefferenceType, float],
        output_param_uids: dict[VarPowerFlowRefferenceType, int],
    ) -> None:
        """Store the runtime FMU ME specification.

        :return: None.
        """

        self.domain: FmuMeDomain = domain
        self.config: FmuImportConfig = config
        self.device_tpe: DeviceType = device_tpe
        self.input_variable_names: tuple[str, ...] = input_variable_names
        self.output_variable_names: tuple[str, ...] = output_variable_names
        self.state_variable_names: tuple[str, ...] = state_variable_names
        self.derivative_variable_names: tuple[str, ...] = derivative_variable_names
        self.integration_method: FmuMeIntegrationMethod = integration_method
        self.input_bindings: tuple[FmuRefBinding, ...] = input_bindings
        self.output_bindings: tuple[FmuRefBinding, ...] = output_bindings
        self.output_defaults: dict[VarPowerFlowRefferenceType, float] = output_defaults
        self.output_param_uids: dict[VarPowerFlowRefferenceType, int] = output_param_uids


class FmuMeDeviceAdapter:
    """Execute one FMU ME device with a light internal predictor.

    :param spec: Runtime specification of the FMU ME device.
    """

    __slots__ = ("spec", "runtime_host", "state_vector", "initialized")

    def __init__(self, spec: FmuMeDeviceSpec) -> None:
        """Store the FMU ME runtime adapter.

        :return: None.
        """

        self.spec: FmuMeDeviceSpec = spec
        self.runtime_host: Optional[FmuRuntimeHost] = None
        self.state_vector: Optional[np.ndarray] = None
        self.initialized: bool = False

    def initialize(
        self,
        start_time: float,
        input_values: dict[str, float] | None = None,
        start_values: dict[str, float] | None = None,
    ) -> None:
        """Open and initialize the FMU ME runtime.

        :param start_time: Initial simulation time.
        :param input_values: FMU input values applied during initialization.
        :param start_values: Additional FMU start values.
        :return: None.
        """

        start_values_payload: dict[str, float] = dict()
        if start_values is not None:
            start_values_payload.update(start_values)
        else:
            pass
        if input_values is not None:
            start_values_payload.update(input_values)
        else:
            pass

        # The runtime host is opened lazily so the adapter carries no external state before use.
        self.runtime_host = open_fmu_runtime_host(self.spec.config)
        self.runtime_host.initialize(start_time=start_time, start_values=start_values_payload)
        self.state_vector = np.array(self.runtime_host.get_continuous_states(), dtype=float)
        self.initialized = True

    def get_state_vector(self) -> np.ndarray:
        """Return a copy of the current continuous-state vector.

        :return: Copy of the current state vector.
        """

        if self.state_vector is None:
            return np.zeros(0, dtype=float)
        else:
            return np.array(self.state_vector, dtype=float)

    def set_state_vector(self, values: np.ndarray) -> None:
        """Replace the adapter continuous-state vector and propagate it to the FMU.

        :param values: New continuous-state vector.
        :return: None.
        """

        if self.runtime_host is None:
            raise RuntimeError("FMU ME adapter must be initialized before setting states")
        else:
            state_values: np.ndarray = np.array(values, dtype=float)
            self.runtime_host.set_continuous_states(state_values.tolist())
            self.state_vector = state_values

    def _apply_inputs(self, input_values: dict[str, float]) -> None:
        """Apply one input vector to the FMU runtime.

        :param input_values: FMU input values.
        :return: None.
        """

        if self.runtime_host is None:
            raise RuntimeError("FMU ME adapter must be initialized before applying inputs")
        else:
            if len(input_values) > 0:
                self.runtime_host.set_real(input_values)
            else:
                pass

    def evaluate_derivatives(self, time_value: float, input_values: dict[str, float]) -> np.ndarray:
        """Evaluate the FMU derivative vector at the provided time and inputs.

        :param time_value: Current evaluation time.
        :param input_values: FMU input values.
        :return: Derivative vector.
        """

        if self.runtime_host is None:
            raise RuntimeError("FMU ME adapter must be initialized before derivative evaluation")
        else:
            self.runtime_host.set_time(time_value)
            self._apply_inputs(input_values)
            if self.state_vector is not None:
                self.runtime_host.set_continuous_states(self.state_vector.tolist())
            else:
                pass
            derivative_values: list[float] = self.runtime_host.get_derivatives()
            return np.array(derivative_values, dtype=float)

    def evaluate_outputs(self, time_value: float, input_values: dict[str, float]) -> dict[str, float]:
        """Evaluate the FMU output vector at the provided time and inputs.

        :param time_value: Current evaluation time.
        :param input_values: FMU input values.
        :return: Output values indexed by FMU variable name.
        """

        if self.runtime_host is None:
            raise RuntimeError("FMU ME adapter must be initialized before output evaluation")
        else:
            self.runtime_host.set_time(time_value)
            self._apply_inputs(input_values)
            if self.state_vector is not None:
                self.runtime_host.set_continuous_states(self.state_vector.tolist())
            else:
                pass
            return self.runtime_host.get_real(list(self.spec.output_variable_names))

    def explicit_euler_step(self, current_time: float, step_size: float, input_values: dict[str, float]) -> dict[str, float]:
        """Advance the FMU one explicit-Euler predictor step.

        :param current_time: Current integration time.
        :param step_size: Step length.
        :param input_values: FMU input values.
        :return: Output values after the step.
        """

        if self.spec.integration_method == FmuMeIntegrationMethod.EXPLICIT_EULER:
            derivatives: np.ndarray = self.evaluate_derivatives(current_time, input_values)
            state_vector: np.ndarray = self.get_state_vector()
            if state_vector.size > 0:
                state_vector = state_vector + step_size * derivatives
                self.set_state_vector(state_vector)
            else:
                pass
            return self.evaluate_outputs(current_time + step_size, input_values)
        else:
            raise ValueError(f"Unsupported FMU ME integration method {self.spec.integration_method.value}")

    def close(self) -> None:
        """Release the FMU runtime used by the adapter.

        :return: None.
        """

        if self.runtime_host is not None:
            self.runtime_host.close()
            self.runtime_host = None
        else:
            pass


def _build_state_variable_names(metadata: FmuModelDescription) -> tuple[str, ...]:
    """Recover the ordered continuous-state variable names from derivative metadata.

    :param metadata: Parsed FMU metadata.
    :return: Ordered continuous-state variable names.
    """

    state_variable_names: list[str] = list()
    derivative_variable: FmuVariableDescription
    for derivative_variable in metadata.get_derivative_variables():
        derivative_index: int | None = derivative_variable.derivative_index
        if derivative_index is not None:
            # FMI derivative indices are 1-based and point to the associated state variable.
            state_variable_names.append(metadata.variables[derivative_index - 1].name)
        else:
            pass
    return tuple(state_variable_names)


def build_fmu_me_device_spec(
    domain: FmuMeDomain,
    config: FmuImportConfig,
    device_tpe: DeviceType,
    input_variable_names: tuple[str, ...],
    output_variable_names: tuple[str, ...],
    integration_method: FmuMeIntegrationMethod = FmuMeIntegrationMethod.EXPLICIT_EULER,
) -> FmuMeDeviceSpec:
    """Build the clean runtime specification required by a future FMU ME device adapter.

    :param domain: VeraGrid domain that will consume the FMU.
    :param config: FMU runtime configuration.
    :param device_tpe: VeraGrid device type.
    :param input_variable_names: Ordered FMU input names.
    :param output_variable_names: Ordered FMU output names.
    :param integration_method: Predictor used by the adapter.
    :return: Runtime FMU ME device specification.
    """

    metadata: FmuModelDescription = read_fmu_model_description(config.fmu_path)
    resolved_mode: FmuInterfaceMode = metadata.resolve_mode(config.preferred_mode)
    if resolved_mode == FmuInterfaceMode.MODEL_EXCHANGE:
        available_variables: set[str] = set(metadata.get_variable_names())
        input_variable_name: str
        for input_variable_name in input_variable_names:
            if input_variable_name in available_variables:
                pass
            else:
                raise KeyError(f"FMU variable {input_variable_name!r} was not found in {config.fmu_path}")
        output_variable_name: str
        for output_variable_name in output_variable_names:
            if output_variable_name in available_variables:
                pass
            else:
                raise KeyError(f"FMU variable {output_variable_name!r} was not found in {config.fmu_path}")

        state_variable_names: tuple[str, ...] = _build_state_variable_names(metadata)
        derivative_variable_names: tuple[str, ...] = tuple(variable.name for variable in metadata.get_derivative_variables())
        return FmuMeDeviceSpec(
            domain=domain,
            config=config,
            device_tpe=device_tpe,
            input_variable_names=input_variable_names,
            output_variable_names=output_variable_names,
            state_variable_names=state_variable_names,
            derivative_variable_names=derivative_variable_names,
            integration_method=integration_method,
            input_bindings=tuple(),
            output_bindings=tuple(),
            output_defaults=dict(),
            output_param_uids=dict(),
        )
    else:
        raise ValueError(f"FMU ME device specs require a Model Exchange FMU, got {resolved_mode.value}")


def _build_rms_me_output_shell_block(
    vfactory: VarFactory,
    name: str,
    output_bindings: tuple[FmuRefBinding, ...],
    output_defaults: dict[VarPowerFlowRefferenceType, float] | None,
) -> Block:
    """Build the symbolic RMS shell used to expose FMU ME outputs to VeraGrid.

    :param vfactory: Variable factory used by the owning grid.
    :param name: Template name.
    :param output_bindings: FMU-to-VeraGrid bindings.
    :param output_defaults: Default output values before the first FMU step.
    :return: Symbolic shell block.
    """

    defaults: dict[VarPowerFlowRefferenceType, float]
    if output_defaults is None:
        defaults = dict()
    else:
        defaults = dict(output_defaults)

    algebraic_vars: list[Var] = list()
    algebraic_eqs: list[Any] = list()
    event_dict: dict[Var, Const] = dict()
    external_mapping: dict[VarPowerFlowRefferenceType, Var] = dict()

    binding: FmuRefBinding
    for binding in output_bindings:
        reference_name: str = binding.reference.value.replace("-", "_")
        output_var: Var = vfactory.add_var(name=f"fmu_{reference_name}_{name}", reference=binding.reference)
        parameter_var: Var = vfactory.add_var(name=f"fmu_param_{reference_name}_{name}")
        default_value: float = float(defaults.get(binding.reference, 0.0))

        # The FMU outputs are projected into runtime parameters so the RMS DAE sees a normal block.
        event_dict[parameter_var] = vfactory.add_const(default_value)
        algebraic_vars.append(output_var)
        algebraic_eqs.append(output_var - parameter_var)
        external_mapping[binding.reference] = output_var

    return Block(
        algebraic_vars=algebraic_vars,
        algebraic_eqs=algebraic_eqs,
        out_vars=list(algebraic_vars),
        event_dict=event_dict,
        external_mapping=external_mapping,
        name=name,
    )


def build_rms_fmu_me_injection_template(
    vfactory: VarFactory,
    config: FmuImportConfig,
    input_bindings: tuple[FmuRefBinding, ...],
    output_bindings: tuple[FmuRefBinding, ...],
    name: str,
    device_tpe: DeviceType = DeviceType.LoadDevice,
    output_defaults: dict[VarPowerFlowRefferenceType, float] | None = None,
    integration_method: FmuMeIntegrationMethod = FmuMeIntegrationMethod.EXPLICIT_EULER,
) -> RmsModelTemplate:
    """Build the symbolic RMS shell for an imported FMU ME device.

    :param vfactory: Variable factory used by the owning grid.
    :param config: FMU runtime configuration.
    :param input_bindings: VeraGrid-to-FMU bindings.
    :param output_bindings: FMU-to-VeraGrid bindings.
    :param name: Template name.
    :param device_tpe: VeraGrid device type.
    :param output_defaults: Default output values before the first FMU step.
    :param integration_method: Internal ME predictor method.
    :return: RMS template wrapping the FMU shell block.
    """

    input_variable_names: list[str] = list()
    output_variable_names: list[str] = list()
    binding: FmuRefBinding
    for binding in input_bindings:
        input_variable_names.append(binding.fmu_variable_name)
    for binding in output_bindings:
        output_variable_names.append(binding.fmu_variable_name)

    # The FMU metadata is validated before the symbolic shell block is created.
    build_fmu_me_device_spec(
        domain=FmuMeDomain.RMS,
        config=config,
        device_tpe=device_tpe,
        input_variable_names=tuple(input_variable_names),
        output_variable_names=tuple(output_variable_names),
        integration_method=integration_method,
    )

    template: RmsModelTemplate = RmsModelTemplate(name=name)
    template.tpe = device_tpe
    template.block = _build_rms_me_output_shell_block(vfactory, name, output_bindings, output_defaults)
    return template


def build_emt_fmu_me_injection_template(
    vfactory: VarFactory,
    config: FmuImportConfig,
    input_bindings: tuple[FmuRefBinding, ...],
    output_bindings: tuple[FmuRefBinding, ...],
    name: str,
    device_tpe: DeviceType = DeviceType.LoadDevice,
    output_defaults: dict[VarPowerFlowRefferenceType, float] | None = None,
    integration_method: FmuMeIntegrationMethod = FmuMeIntegrationMethod.EXPLICIT_EULER,
) -> EmtModelTemplate:
    """Build the symbolic EMT shell for an imported FMU ME device.

    :param vfactory: Variable factory used by the owning grid.
    :param config: FMU runtime configuration.
    :param input_bindings: VeraGrid-to-FMU bindings.
    :param output_bindings: FMU-to-VeraGrid bindings.
    :param name: Template name.
    :param device_tpe: VeraGrid device type.
    :param output_defaults: Default output values before the first FMU step.
    :param integration_method: Internal ME predictor method.
    :return: EMT template wrapping the FMU shell block.
    """

    input_variable_names: list[str] = list()
    output_variable_names: list[str] = list()
    binding: FmuRefBinding
    for binding in input_bindings:
        input_variable_names.append(binding.fmu_variable_name)
    for binding in output_bindings:
        output_variable_names.append(binding.fmu_variable_name)

    build_fmu_me_device_spec(
        domain=FmuMeDomain.EMT,
        config=config,
        device_tpe=device_tpe,
        input_variable_names=tuple(input_variable_names),
        output_variable_names=tuple(output_variable_names),
        integration_method=integration_method,
    )

    template: EmtModelTemplate = EmtModelTemplate(name=name)
    template.tpe = device_tpe
    template.block = _build_rms_me_output_shell_block(vfactory, name, output_bindings, output_defaults)
    _ensure_emt_external_mapping_keys(template.block)
    template.block.api_obj_mapping = dict()
    template.block.api_obj_mapping[ParamPowerFlowRefferenceType.Pl0_A] = None
    template.block.api_obj_mapping[ParamPowerFlowRefferenceType.Pl0_B] = None
    template.block.api_obj_mapping[ParamPowerFlowRefferenceType.Pl0_C] = None
    template.block.api_obj_mapping[ParamPowerFlowRefferenceType.Ql0_A] = None
    template.block.api_obj_mapping[ParamPowerFlowRefferenceType.Ql0_B] = None
    template.block.api_obj_mapping[ParamPowerFlowRefferenceType.Ql0_C] = None
    template.block.api_obj_mapping[ParamPowerFlowRefferenceType.omega_base] = None
    return template


def _read_rms_me_device_config(device: Any) -> Any | None:
    """Read the serialized FMU ME configuration stored on one device.

    :param device: VeraGrid device instance.
    :return: Parsed device configuration when available.
    """

    try:
        config_text: str = device.rms_fmu_me_import_config
    except AttributeError:
        if isinstance(device, InjectionParent) or isinstance(device, BranchParent):
            raise
        else:
            return None
    return load_fmu_me_device_config(config_text)


def _read_emt_me_device_config(device: Any) -> Any | None:
    """Read the serialized FMU ME configuration stored on one EMT device.

    :param device: VeraGrid device instance.
    :return: Parsed device configuration when available.
    """

    try:
        config_text: str = device.emt_fmu_me_import_config
    except AttributeError:
        if isinstance(device, InjectionParent) or isinstance(device, BranchParent):
            raise
        else:
            return None
    return load_fmu_me_device_config(config_text)


def _build_rms_me_runtime_spec(device: Any, block: Block) -> Any | None:
    """Rebuild the FMU ME runtime specification from the stored device config.

    :param device: VeraGrid device instance.
    :param block: Device block used in the active RMS problem.
    :return: Runtime FMU ME specification when available.
    """

    record = _read_rms_me_device_config(device)
    if record is None:
        return None
    else:
        if record.domain == FmuMeDomain.RMS:
            return restore_fmu_me_spec_from_record(record, block, device.device_type)
        else:
            return None


def _build_emt_me_runtime_spec(device: Any, block: Block) -> Any | None:
    """Rebuild the FMU ME runtime specification from the stored EMT device config.

    :param device: VeraGrid device instance.
    :param block: Device block used in the active EMT problem.
    :return: Runtime FMU ME specification when available.
    """

    record = _read_emt_me_device_config(device)
    if record is None:
        return None
    else:
        if record.domain == FmuMeDomain.EMT:
            return restore_fmu_me_spec_from_record(record, block, device.device_type)
        else:
            return None


def _get_event_param_index_map(problem: Any) -> dict[int, int]:
    """
    Return the runtime event-parameter index map exposed by the active problem.

    :param problem: Runtime problem wrapper.
    :return: UID-to-index event-parameter map.
    """

    try:
        return problem._uid2idx_event_params
    except AttributeError:
        return problem.uid2idx_event_params


def _get_rms_me_input_value(problem: Any, device: Any, reference: VarPowerFlowRefferenceType, x_snapshot: np.ndarray) -> float:
    """Read one RMS FMU ME input from the current network snapshot.

    :param problem: RMS problem instance.
    :param device: VeraGrid device instance.
    :param reference: Requested VeraGrid external reference.
    :param x_snapshot: Current accepted state snapshot.
    :return: Numeric input value.
    """

    if reference in {VarPowerFlowRefferenceType.Vm, VarPowerFlowRefferenceType.Va, VarPowerFlowRefferenceType.Vdc}:
        bus_model: Block = device.bus.rms_model
        variable: Var = bus_model.external_mapping[reference]
        return float(x_snapshot[problem.uid2idx_vars[variable.uid]])
    else:
        raise KeyError(f"Unsupported RMS FMU ME input reference {reference.value!r}")


def _get_emt_me_input_value(problem: Any, device: Any, reference: VarPowerFlowRefferenceType, x_snapshot: np.ndarray) -> float:
    """Read one EMT FMU ME input from the current network snapshot.

    :param problem: EMT problem instance.
    :param device: VeraGrid device instance.
    :param reference: Requested VeraGrid external reference.
    :param x_snapshot: Current accepted state snapshot.
    :return: Numeric input value.
    """

    if reference in {
        VarPowerFlowRefferenceType.v_N,
        VarPowerFlowRefferenceType.v_A,
        VarPowerFlowRefferenceType.v_B,
        VarPowerFlowRefferenceType.v_C,
        VarPowerFlowRefferenceType.Vdc,
    }:
        bus_model: Block = device.bus.emt_model
        variable: Var = bus_model.external_mapping[reference]
        return float(x_snapshot[problem.uid2idx_vars[variable.uid]])
    else:
        raise KeyError(f"Unsupported EMT FMU ME input reference {reference.value!r}")


class RmsFmuMeDeviceAdapter:
    """Adapt one imported FMU ME device to the RMS communication-step loop.

    :param problem: RMS problem instance.
    :param device: VeraGrid device instance.
    :param spec: Runtime FMU ME specification.
    :param output_param_indices: Runtime-parameter indices receiving FMU outputs.
    """

    __slots__ = ("problem", "device", "spec", "output_param_indices", "runtime_adapter", "last_outputs")

    def __init__(
        self,
        problem: Any,
        device: Any,
        spec: FmuMeDeviceSpec,
        output_param_indices: dict[VarPowerFlowRefferenceType, int],
    ) -> None:
        """Store the RMS FMU ME runtime adapter.

        :return: None.
        """

        self.problem: Any = problem
        self.device: Any = device
        self.spec: FmuMeDeviceSpec = spec
        self.output_param_indices: dict[VarPowerFlowRefferenceType, int] = output_param_indices
        self.runtime_adapter: FmuMeDeviceAdapter = FmuMeDeviceAdapter(spec)
        self.last_outputs: dict[VarPowerFlowRefferenceType, float] = dict()

    def _build_input_values(self, x_snapshot: np.ndarray) -> dict[str, float]:
        """Collect the FMU ME input values from the current RMS snapshot.

        :param x_snapshot: Current accepted state snapshot.
        :return: FMU input values.
        """

        input_values: dict[str, float] = dict()
        binding: FmuRefBinding
        for binding in self.spec.input_bindings:
            input_values[binding.fmu_variable_name] = _get_rms_me_input_value(self.problem, self.device, binding.reference, x_snapshot)
        return input_values

    def _map_outputs(self, runtime_outputs: dict[str, float]) -> dict[VarPowerFlowRefferenceType, float]:
        """Map runtime FMU outputs back to VeraGrid references.

        :param runtime_outputs: FMU outputs indexed by FMU variable name.
        :return: FMU outputs indexed by VeraGrid reference.
        """

        mapped_outputs: dict[VarPowerFlowRefferenceType, float] = dict()
        binding: FmuRefBinding
        for binding in self.spec.output_bindings:
            mapped_outputs[binding.reference] = float(runtime_outputs[binding.fmu_variable_name])
        return mapped_outputs

    def initialize_outputs(self, time_value: float, x_snapshot: np.ndarray) -> dict[VarPowerFlowRefferenceType, float]:
        """Initialize the FMU ME runtime and return its first output sample.

        :param time_value: Current simulation time.
        :param x_snapshot: Current accepted state snapshot.
        :return: FMU outputs indexed by VeraGrid reference.
        """

        self.runtime_adapter.initialize(start_time=time_value, input_values=self._build_input_values(x_snapshot))
        outputs: dict[VarPowerFlowRefferenceType, float] = self._map_outputs(
            self.runtime_adapter.evaluate_outputs(time_value, self._build_input_values(x_snapshot))
        )
        self.last_outputs = dict(outputs)
        return outputs

    def advance(self, current_time: float, step_size: float, x_snapshot: np.ndarray) -> dict[VarPowerFlowRefferenceType, float]:
        """Advance the FMU ME runtime for one RMS communication step.

        :param current_time: Current simulation time.
        :param step_size: RMS communication step.
        :param x_snapshot: Current accepted state snapshot.
        :return: FMU outputs indexed by VeraGrid reference.
        """

        outputs: dict[VarPowerFlowRefferenceType, float] = self._map_outputs(
            self.runtime_adapter.explicit_euler_step(current_time=current_time, step_size=step_size, input_values=self._build_input_values(x_snapshot))
        )
        self.last_outputs = dict(outputs)
        return outputs

    def apply_outputs(self, target: np.ndarray, outputs: dict[VarPowerFlowRefferenceType, float]) -> None:
        """Write the FMU ME outputs into VeraGrid runtime-parameter storage.

        :param target: Runtime-parameter array.
        :param outputs: FMU outputs indexed by VeraGrid reference.
        :return: None.
        """

        reference: VarPowerFlowRefferenceType
        for reference, value in outputs.items():
            target[self.output_param_indices[reference]] = float(value)

    def close(self) -> None:
        """Release the FMU ME runtime used by the adapter.

        :return: None.
        """

        if len(self.last_outputs) == 0:
            if self.runtime_adapter.initialized:
                self.last_outputs = dict(self.runtime_adapter.evaluate_outputs(0.0, dict()))
            else:
                pass
        else:
            pass
        self.runtime_adapter.close()


class EmtFmuMeDeviceAdapter:
    """Adapt one imported FMU ME device to the EMT boundary-update loop.

    :param problem: EMT problem instance.
    :param device: VeraGrid device instance.
    :param spec: Runtime FMU ME specification.
    :param output_param_indices: Runtime-parameter indices receiving FMU outputs.
    """

    __slots__ = ("problem", "device", "spec", "output_param_indices", "runtime_adapter", "last_time", "initialized")

    def __init__(
        self,
        problem: Any,
        device: Any,
        spec: FmuMeDeviceSpec,
        output_param_indices: dict[VarPowerFlowRefferenceType, int],
    ) -> None:
        """Store the EMT FMU ME runtime adapter.

        :return: None.
        """

        self.problem: Any = problem
        self.device: Any = device
        self.spec: FmuMeDeviceSpec = spec
        self.output_param_indices: dict[VarPowerFlowRefferenceType, int] = output_param_indices
        self.runtime_adapter: FmuMeDeviceAdapter = FmuMeDeviceAdapter(spec)
        self.last_time: float = 0.0
        self.initialized: bool = False

    def _build_input_values(self, x_snapshot: np.ndarray) -> dict[str, float]:
        """Collect the FMU ME input values from the current EMT snapshot.

        :param x_snapshot: Current accepted state snapshot.
        :return: FMU input values.
        """

        input_values: dict[str, float] = dict()
        binding: FmuRefBinding
        for binding in self.spec.input_bindings:
            input_values[binding.fmu_variable_name] = _get_emt_me_input_value(self.problem, self.device, binding.reference, x_snapshot)
        return input_values

    def _map_outputs(self, runtime_outputs: dict[str, float]) -> dict[VarPowerFlowRefferenceType, float]:
        """Map runtime FMU outputs back to VeraGrid references.

        :param runtime_outputs: FMU outputs indexed by FMU variable name.
        :return: FMU outputs indexed by VeraGrid reference.
        """

        mapped_outputs: dict[VarPowerFlowRefferenceType, float] = dict()
        binding: FmuRefBinding
        for binding in self.spec.output_bindings:
            mapped_outputs[binding.reference] = float(runtime_outputs[binding.fmu_variable_name])
        return mapped_outputs

    def initialize_outputs(self, time_value: float, x_snapshot: np.ndarray) -> dict[VarPowerFlowRefferenceType, float]:
        """Initialize the FMU ME runtime and return its first output sample.

        :param time_value: Current simulation time.
        :param x_snapshot: Current accepted state snapshot.
        :return: FMU outputs indexed by VeraGrid reference.
        """

        self.runtime_adapter.initialize(start_time=time_value, input_values=self._build_input_values(x_snapshot))
        self.initialized = True
        self.last_time = time_value
        return self._map_outputs(self.runtime_adapter.evaluate_outputs(time_value, self._build_input_values(x_snapshot)))

    def advance(self, current_time: float, step_size: float, x_snapshot: np.ndarray) -> dict[VarPowerFlowRefferenceType, float]:
        """Advance the FMU ME runtime for one EMT communication step.

        :param current_time: Current simulation time.
        :param step_size: EMT communication step.
        :param x_snapshot: Current accepted state snapshot.
        :return: FMU outputs indexed by VeraGrid reference.
        """

        outputs: dict[VarPowerFlowRefferenceType, float] = self._map_outputs(
            self.runtime_adapter.explicit_euler_step(current_time=current_time, step_size=step_size, input_values=self._build_input_values(x_snapshot))
        )
        self.last_time = current_time + step_size
        return outputs

    def apply_outputs(self, target: np.ndarray, outputs: dict[VarPowerFlowRefferenceType, float]) -> None:
        """Write the FMU ME outputs into VeraGrid runtime-parameter storage.

        :param target: Runtime-parameter array.
        :param outputs: FMU outputs indexed by VeraGrid reference.
        :return: None.
        """

        reference: VarPowerFlowRefferenceType
        for reference, value in outputs.items():
            target[self.output_param_indices[reference]] = float(value)

    def close(self) -> None:
        """Release the FMU ME runtime used by the adapter.

        :return: None.
        """

        self.runtime_adapter.close()


def register_rms_fmu_me_device(problem: Any, device: Any, block: Block) -> None:
    """Register one imported FMU ME device in the active RMS problem.

    :param problem: RMS problem instance.
    :param device: VeraGrid device instance.
    :param block: Device RMS block used in the active problem.
    :return: None.
    """

    spec: Optional[FmuMeDeviceSpec] = _build_rms_me_runtime_spec(device, block)
    if spec is None:
        return
    else:
        adapter: RmsFmuMeDeviceAdapter
        for adapter in problem._fmu_me_adapters:
            if adapter.device.idtag == device.idtag:
                return
            else:
                pass

        output_param_indices: dict[VarPowerFlowRefferenceType, int] = dict()
        uid_to_index = _get_event_param_index_map(problem)
        reference: VarPowerFlowRefferenceType
        for reference, uid in spec.output_param_uids.items():
            output_param_indices[reference] = uid_to_index[uid]

        problem._fmu_me_adapters.append(
            RmsFmuMeDeviceAdapter(problem=problem, device=device, spec=spec, output_param_indices=output_param_indices)
        )
        problem._fmu_me_initialized = False


def initialize_rms_fmu_me_devices(problem: Any, x_snapshot: np.ndarray, time_value: float = 0.0) -> None:
    """Initialize all imported FMU ME devices before the RMS loop starts.

    :param problem: RMS problem instance.
    :param x_snapshot: Initial accepted state snapshot.
    :param time_value: Initial simulation time.
    :return: None.
    """

    if len(problem._fmu_me_adapters) > 0:
        adapter: RmsFmuMeDeviceAdapter
        for adapter in problem._fmu_me_adapters:
            outputs = adapter.initialize_outputs(time_value, x_snapshot)
            adapter.apply_outputs(problem._variable_parameters_values, outputs)
            if problem._variable_parameters_values is None:
                problem._last_variable_parameters_values = None
            else:
                problem._last_variable_parameters_values = np.array(problem._variable_parameters_values, copy=True)
        problem._fmu_me_initialized = True
    else:
        problem._fmu_me_initialized = True


def advance_rms_fmu_me_devices(problem: Any, time_value: float, x_snapshot: np.ndarray, step_size: float) -> None:
    """Advance all imported FMU ME devices for one RMS communication step.

    :param problem: RMS problem instance.
    :param time_value: Current simulation time.
    :param x_snapshot: Current accepted state snapshot.
    :param step_size: RMS communication step.
    :return: None.
    """

    if len(problem._fmu_me_adapters) > 0:
        if problem._fmu_me_initialized:
            pass
        else:
            initialize_rms_fmu_me_devices(problem=problem, x_snapshot=x_snapshot, time_value=time_value)

        adapter: RmsFmuMeDeviceAdapter
        for adapter in problem._fmu_me_adapters:
            outputs = adapter.advance(current_time=time_value, step_size=step_size, x_snapshot=x_snapshot)
            adapter.apply_outputs(problem._variable_parameters_values, outputs)
            if problem._variable_parameters_values is None:
                problem._last_variable_parameters_values = None
            else:
                problem._last_variable_parameters_values = np.array(problem._variable_parameters_values, copy=True)
    else:
        pass


def close_rms_fmu_me_devices(problem: Any) -> None:
    """Close all imported FMU ME devices.

    :param problem: RMS problem instance.
    :return: None.
    """

    adapter: RmsFmuMeDeviceAdapter
    for adapter in problem._fmu_me_adapters:
        adapter.close()


def register_emt_fmu_me_device(problem: Any, device: Any, block: Block) -> None:
    """Register one imported FMU ME device in the active EMT problem.

    :param problem: EMT problem instance.
    :param device: VeraGrid device instance.
    :param block: Device EMT block used in the active problem.
    :return: None.
    """

    spec: Optional[FmuMeDeviceSpec] = _build_emt_me_runtime_spec(device, block)
    if spec is None:
        return
    else:
        adapter: EmtFmuMeDeviceAdapter
        for adapter in problem._fmu_me_adapters:
            if adapter.device.idtag == device.idtag:
                return
            else:
                pass

        output_param_indices: dict[VarPowerFlowRefferenceType, int] = dict()
        uid_to_index = _get_event_param_index_map(problem)
        reference: VarPowerFlowRefferenceType
        for reference, uid in spec.output_param_uids.items():
            output_param_indices[reference] = uid_to_index[uid]

        problem._fmu_me_adapters.append(
            EmtFmuMeDeviceAdapter(problem=problem, device=device, spec=spec, output_param_indices=output_param_indices)
        )


def queue_emt_fmu_me_device(problem: Any, device: Any, block: Block) -> None:
    """Queue one EMT device for FMU ME restoration after problem repartitioning.

    :param problem: EMT problem instance.
    :param device: VeraGrid device instance.
    :param block: Device EMT block used in the active problem.
    :return: None.
    """

    record = _read_emt_me_device_config(device)
    if record is None:
        return
    else:
        problem._pending_fmu_me_devices.append((device, block))


def finalize_emt_fmu_me_devices(problem: Any) -> None:
    """Restore all queued EMT FMU ME devices after the EMT problem is assembled.

    :param problem: EMT problem instance.
    :return: None.
    """

    pending_device: tuple[Any, Block]
    for pending_device in problem._pending_fmu_me_devices:
        register_emt_fmu_me_device(problem, pending_device[0], pending_device[1])
