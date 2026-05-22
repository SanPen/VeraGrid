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
from VeraGridEngine.IO.fmu.importer.device_config import load_fmu_cs_device_config, restore_fmu_cs_spec_from_record
from VeraGridEngine.IO.fmu.importer.model_description import FmuInterfaceMode, FmuModelDescription, read_fmu_model_description
from VeraGridEngine.IO.fmu.importer.runtime_host import FmuRuntimeHost, open_fmu_runtime_host


class FmuCsDomain(str, Enum):
    """Enumerate the VeraGrid domains that can consume an imported FMU CS device.

    :return: None.
    """

    RMS = "rms"
    EMT = "emt"


class FmuRefBinding:
    """Bind one VeraGrid reference variable to one FMU variable name.

    :param reference: VeraGrid external mapping reference.
    :param fmu_variable_name: FMU scalar-variable name.
    """

    __slots__ = ("reference", "fmu_variable_name")

    def __init__(self, reference: VarPowerFlowRefferenceType, fmu_variable_name: str) -> None:
        """Store the external-reference to FMU-variable binding.

        :return: None.
        """

        self.reference: VarPowerFlowRefferenceType = reference
        self.fmu_variable_name: str = fmu_variable_name


class FmuCsDeviceSpec:
    """Store the runtime data required to execute one FMU CS device.

    :param domain: VeraGrid domain using the FMU.
    :param config: Runtime configuration for the FMU.
    :param device_tpe: VeraGrid device type.
    :param input_bindings: VeraGrid-to-FMU bindings.
    :param output_bindings: FMU-to-VeraGrid bindings.
    :param output_defaults: Default output values before the FMU is stepped.
    :param output_param_uids: Event-parameter UIDs backing the FMU outputs.
    """

    __slots__ = (
        "domain",
        "config",
        "device_tpe",
        "input_bindings",
        "output_bindings",
        "output_defaults",
        "output_param_uids",
    )

    def __init__(
        self,
        domain: FmuCsDomain,
        config: FmuImportConfig,
        device_tpe: DeviceType,
        input_bindings: tuple[FmuRefBinding, ...],
        output_bindings: tuple[FmuRefBinding, ...],
        output_defaults: dict[VarPowerFlowRefferenceType, float],
        output_param_uids: dict[VarPowerFlowRefferenceType, int],
    ) -> None:
        """Store the runtime FMU device specification.

        :return: None.
        """

        self.domain: FmuCsDomain = domain
        self.config: FmuImportConfig = config
        self.device_tpe: DeviceType = device_tpe
        self.input_bindings: tuple[FmuRefBinding, ...] = input_bindings
        self.output_bindings: tuple[FmuRefBinding, ...] = output_bindings
        self.output_defaults: dict[VarPowerFlowRefferenceType, float] = output_defaults
        self.output_param_uids: dict[VarPowerFlowRefferenceType, int] = output_param_uids


class FmuCsDeviceAdapter:
    """Execute one FMU CS device inside a VeraGrid simulation step loop.

    :param problem: Owning simulation problem.
    :param device: VeraGrid device using the FMU.
    :param spec: Runtime FMU device specification.
    :param output_param_indices: Runtime-parameter indices receiving FMU outputs.
    """

    __slots__ = ("problem", "device", "spec", "output_param_indices", "runtime_host", "last_time", "initialized", "last_outputs")

    def __init__(
        self,
        problem: Any,
        device: Any,
        spec: FmuCsDeviceSpec,
        output_param_indices: dict[VarPowerFlowRefferenceType, int],
    ) -> None:
        """Store the FMU CS runtime adapter.

        :return: None.
        """

        self.problem: Any = problem
        self.device: Any = device
        self.spec: FmuCsDeviceSpec = spec
        self.output_param_indices: dict[VarPowerFlowRefferenceType, int] = output_param_indices
        self.runtime_host: FmuRuntimeHost | None = None
        self.last_time: float = 0.0
        self.initialized: bool = False
        self.last_outputs: dict[VarPowerFlowRefferenceType, float] = dict()

    def _build_input_values(self, x_snapshot: np.ndarray) -> dict[str, float]:
        """Collect the FMU input values from the current VeraGrid snapshot.

        :param x_snapshot: Current accepted state snapshot.
        :return: FMU input values.
        """

        input_values: dict[str, float] = dict()
        binding: FmuRefBinding
        for binding in self.spec.input_bindings:
            if self.spec.domain == FmuCsDomain.RMS:
                value: float = _get_rms_input_value(self.problem, self.device, binding.reference, x_snapshot)
            else:
                value = _get_emt_input_value(self.problem, self.device, binding.reference, x_snapshot)
            input_values[binding.fmu_variable_name] = value
        return input_values

    def _ensure_runtime(self, x_snapshot: np.ndarray, start_time: float) -> None:
        """Instantiate and initialize the FMU runtime the first time it is needed.

        :param x_snapshot: Current accepted state snapshot.
        :param start_time: Current simulation time.
        :return: None.
        """

        if self.runtime_host is None:
            # The FMU runtime is created lazily so static projects do not pay startup cost.
            self.runtime_host = open_fmu_runtime_host(self.spec.config)
            self.runtime_host.initialize(start_time=start_time, start_values=self._build_input_values(x_snapshot))
            self.initialized = True
            self.last_time = start_time
        else:
            pass

    def _read_outputs(self) -> dict[VarPowerFlowRefferenceType, float]:
        """Read the FMU outputs or fall back to the configured defaults.

        :return: Output values indexed by VeraGrid reference.
        """

        if self.runtime_host is None:
            return dict(self.spec.output_defaults)
        else:
            variable_names: list[str] = list()
            binding: FmuRefBinding
            for binding in self.spec.output_bindings:
                variable_names.append(binding.fmu_variable_name)
            runtime_values: dict[str, float] = self.runtime_host.get_real(variable_names)

            output_values: dict[VarPowerFlowRefferenceType, float] = dict()
            for binding in self.spec.output_bindings:
                output_values[binding.reference] = float(runtime_values[binding.fmu_variable_name])
            return output_values

    def initialize_outputs(self, time_value: float, x_snapshot: np.ndarray) -> dict[VarPowerFlowRefferenceType, float]:
        """Initialize the FMU and return its first output sample.

        :param time_value: Current simulation time.
        :param x_snapshot: Current accepted state snapshot.
        :return: Output values indexed by VeraGrid reference.
        """

        self._ensure_runtime(x_snapshot, time_value)
        outputs: dict[VarPowerFlowRefferenceType, float] = self._read_outputs()
        self.last_outputs = dict(outputs)
        return outputs

    def advance(self, current_time: float, step_size: float, x_snapshot: np.ndarray) -> dict[VarPowerFlowRefferenceType, float]:
        """Advance the FMU one communication step and read the outputs.

        :param current_time: Current communication time.
        :param step_size: Requested communication step.
        :param x_snapshot: Current accepted state snapshot.
        :return: Output values indexed by VeraGrid reference.
        """

        self._ensure_runtime(x_snapshot, current_time)
        if self.runtime_host is None:
            return dict(self.spec.output_defaults)
        else:
            # Inputs are refreshed from the accepted network state before stepping the FMU.
            self.runtime_host.set_real(self._build_input_values(x_snapshot))
            if current_time > self.last_time + 1e-15:
                self.last_time = current_time
            else:
                pass
            self.runtime_host.do_step(current_time=current_time, step_size=step_size)
            self.last_time = current_time + step_size
            outputs = self._read_outputs()
            self.last_outputs = dict(outputs)
            return outputs

    def apply_outputs(self, target: np.ndarray, outputs: dict[VarPowerFlowRefferenceType, float]) -> None:
        """Write the FMU outputs into VeraGrid runtime-parameter storage.

        :param target: Runtime-parameter array.
        :param outputs: FMU outputs indexed by VeraGrid reference.
        :return: None.
        """

        reference: VarPowerFlowRefferenceType
        for reference, value in outputs.items():
            target[self.output_param_indices[reference]] = float(value)

    def close(self) -> None:
        """Release the FMU runtime used by the adapter.

        :return: None.
        """

        if self.runtime_host is not None:
            if len(self.last_outputs) == 0:
                self.last_outputs = self._read_outputs()
            else:
                pass
            self.runtime_host.close()
            self.runtime_host = None
        else:
            pass


class CompositeEmtBoundaryUpdater:
    """Compose VeraGrid EMT boundary updates with imported FMU CS devices.

    :param problem: Owning EMT problem.
    :param adapters: FMU CS device adapters.
    """

    __slots__ = ("problem", "adapters", "initialized")

    def __init__(self, problem: Any, adapters: list[FmuCsDeviceAdapter]) -> None:
        """Store the boundary updater wrapper.

        :return: None.
        """

        self.problem: Any = problem
        self.adapters: list[FmuCsDeviceAdapter] = adapters
        self.initialized: bool = False

    def update(self, time_value: float, x_snapshot: np.ndarray, full_params: np.ndarray) -> None:
        """Execute the native boundary update and then step imported FMUs.

        :param time_value: Current simulation time.
        :param x_snapshot: Previous accepted solution.
        :param full_params: Runtime-parameter vector.
        :return: None.
        """

        # The native EMT boundary logic always runs first because it keeps internal line histories consistent.
        self.problem.emt_boundary_update(time_value, x_snapshot, full_params)
        if len(self.adapters) > 0:
            if self.initialized:
                adapter: FmuCsDeviceAdapter
                for adapter in self.adapters:
                    step_size: float = max(float(time_value - adapter.last_time), 0.0)
                    if step_size > 0.0:
                        outputs = adapter.advance(current_time=adapter.last_time, step_size=step_size, x_snapshot=x_snapshot)
                    else:
                        outputs = adapter._read_outputs()
                    adapter.apply_outputs(full_params, outputs)
            else:
                adapter = self.adapters[0]
                for adapter in self.adapters:
                    outputs = adapter.initialize_outputs(time_value, x_snapshot)
                    adapter.apply_outputs(full_params, outputs)
                self.initialized = True
        else:
            pass

    def get_next_forced_event_time(self, t_prev: float, t_target: float) -> float | None:
        """Forward the next forced event query to the native EMT problem.

        :param t_prev: Previous accepted time.
        :param t_target: Candidate target time.
        :return: Next forced event time if any.
        """

        return self.problem.get_next_forced_event_time(t_prev=t_prev, t_target=t_target)

    def close(self) -> None:
        """Release all FMU runtimes owned by the boundary updater.

        :return: None.
        """

        adapter: FmuCsDeviceAdapter
        for adapter in self.adapters:
            adapter.close()


def _validate_cs_spec(config: FmuImportConfig, input_bindings: tuple[FmuRefBinding, ...], output_bindings: tuple[FmuRefBinding, ...]) -> None:
    """Validate that an FMU is usable as a Co-Simulation device block.

    :param config: FMU runtime configuration.
    :param input_bindings: VeraGrid-to-FMU bindings.
    :param output_bindings: FMU-to-VeraGrid bindings.
    :return: None.
    """

    metadata: FmuModelDescription = read_fmu_model_description(config.fmu_path)
    resolved_mode: FmuInterfaceMode = metadata.resolve_mode(config.preferred_mode)
    if resolved_mode == FmuInterfaceMode.CO_SIMULATION:
        available_variables: set[str] = set(metadata.get_variable_names())
        binding: FmuRefBinding
        for binding in input_bindings:
            if binding.fmu_variable_name in available_variables:
                pass
            else:
                raise KeyError(f"FMU variable {binding.fmu_variable_name!r} was not found in {config.fmu_path}")
        for binding in output_bindings:
            if binding.fmu_variable_name in available_variables:
                pass
            else:
                raise KeyError(f"FMU variable {binding.fmu_variable_name!r} was not found in {config.fmu_path}")
    else:
        raise ValueError(f"Experimental CS device blocks require a Co-Simulation FMU, got {resolved_mode.value}")


def _build_output_binding_block_data(
    vfactory: VarFactory,
    name: str,
    output_bindings: tuple[FmuRefBinding, ...],
    output_defaults: dict[VarPowerFlowRefferenceType, float] | None,
) -> tuple[list[Var], list[Any], dict[VarPowerFlowRefferenceType, Var], dict[Var, Const]]:
    """Build the symbolic output shell used to host an imported FMU device.

    :param vfactory: Variable factory used by the owning grid.
    :param name: Template name.
    :param output_bindings: FMU-to-VeraGrid bindings.
    :param output_defaults: Default values for each output reference.
    :return: Algebraic vars, equations, external mapping and event params.
    """

    defaults: dict[VarPowerFlowRefferenceType, float]
    if output_defaults is None:
        defaults = dict()
    else:
        defaults = dict(output_defaults)

    algebraic_vars: list[Var] = list()
    algebraic_eqs: list[Any] = list()
    external_mapping: dict[VarPowerFlowRefferenceType, Var] = dict()
    event_dict: dict[Var, Const] = dict()

    binding: FmuRefBinding
    for binding in output_bindings:
        reference_name: str = binding.reference.value.replace("-", "_")
        output_var: Var = vfactory.add_var(name=f"fmu_{reference_name}_{name}", reference=binding.reference)
        parameter_var: Var = vfactory.add_var(name=f"fmu_param_{reference_name}_{name}")
        default_value: float = float(defaults.get(binding.reference, 0.0))

        # The FMU output is injected through an event parameter so the native solver sees a normal symbolic variable.
        event_dict[parameter_var] = vfactory.add_const(default_value)
        algebraic_vars.append(output_var)
        algebraic_eqs.append(output_var - parameter_var)
        external_mapping[binding.reference] = output_var

    return algebraic_vars, algebraic_eqs, external_mapping, event_dict


def _build_template_block(
    vfactory: VarFactory,
    name: str,
    output_bindings: tuple[FmuRefBinding, ...],
    output_defaults: dict[VarPowerFlowRefferenceType, float] | None,
) -> Block:
    """Build the symbolic shell block for an imported FMU device.

    :param vfactory: Variable factory used by the owning grid.
    :param name: Template name.
    :param output_bindings: FMU-to-VeraGrid bindings.
    :param output_defaults: Default values for each output reference.
    :return: Symbolic shell block.
    """

    algebraic_vars: list[Var]
    algebraic_eqs: list[Any]
    external_mapping: dict[VarPowerFlowRefferenceType, Var]
    event_dict: dict[Var, Const]
    algebraic_vars, algebraic_eqs, external_mapping, event_dict = _build_output_binding_block_data(
        vfactory=vfactory,
        name=name,
        output_bindings=output_bindings,
        output_defaults=output_defaults,
    )
    return Block(
        algebraic_vars=algebraic_vars,
        algebraic_eqs=algebraic_eqs,
        out_vars=list(algebraic_vars),
        event_dict=event_dict,
        external_mapping=external_mapping,
        name=name,
    )


def build_rms_fmu_cs_injection_template(
    vfactory: VarFactory,
    config: FmuImportConfig,
    input_bindings: tuple[FmuRefBinding, ...],
    output_bindings: tuple[FmuRefBinding, ...],
    name: str,
    device_tpe: DeviceType = DeviceType.LoadDevice,
    output_defaults: dict[VarPowerFlowRefferenceType, float] | None = None,
) -> RmsModelTemplate:
    """Build the symbolic RMS shell for one imported FMU CS device.

    :param vfactory: Variable factory used by the owning grid.
    :param config: FMU runtime configuration.
    :param input_bindings: VeraGrid-to-FMU bindings.
    :param output_bindings: FMU-to-VeraGrid bindings.
    :param name: Template name.
    :param device_tpe: VeraGrid device type.
    :param output_defaults: Default output values.
    :return: RMS template wrapping the FMU shell block.
    """

    _validate_cs_spec(config, input_bindings, output_bindings)
    template: RmsModelTemplate = RmsModelTemplate(name=name)
    template.tpe = device_tpe
    template.block = _build_template_block(vfactory, name, output_bindings, output_defaults)
    return template


def build_emt_fmu_cs_injection_template(
    vfactory: VarFactory,
    config: FmuImportConfig,
    input_bindings: tuple[FmuRefBinding, ...],
    output_bindings: tuple[FmuRefBinding, ...],
    name: str,
    device_tpe: DeviceType = DeviceType.LoadDevice,
    output_defaults: dict[VarPowerFlowRefferenceType, float] | None = None,
) -> EmtModelTemplate:
    """Build the symbolic EMT shell for one imported FMU CS device.

    :param vfactory: Variable factory used by the owning grid.
    :param config: FMU runtime configuration.
    :param input_bindings: VeraGrid-to-FMU bindings.
    :param output_bindings: FMU-to-VeraGrid bindings.
    :param name: Template name.
    :param device_tpe: VeraGrid device type.
    :param output_defaults: Default output values.
    :return: EMT template wrapping the FMU shell block.
    """

    _validate_cs_spec(config, input_bindings, output_bindings)
    template: EmtModelTemplate = EmtModelTemplate(name=name)
    template.tpe = device_tpe
    template.block = _build_template_block(vfactory, name, output_bindings, output_defaults)
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


def _ensure_emt_external_mapping_keys(block: Block) -> None:
    """Populate the EMT shell external mapping with the phase keys expected by the EMT parser.

    :param block: EMT shell block used by an imported FMU device.
    :return: None.
    """

    for reference in (
        VarPowerFlowRefferenceType.Vdc,
        VarPowerFlowRefferenceType.i_N,
        VarPowerFlowRefferenceType.i_A,
        VarPowerFlowRefferenceType.i_B,
        VarPowerFlowRefferenceType.i_C,
        VarPowerFlowRefferenceType.P,
        VarPowerFlowRefferenceType.Q,
        VarPowerFlowRefferenceType.P_N,
        VarPowerFlowRefferenceType.P_A,
        VarPowerFlowRefferenceType.P_B,
        VarPowerFlowRefferenceType.P_C,
        VarPowerFlowRefferenceType.Q_N,
        VarPowerFlowRefferenceType.Q_A,
        VarPowerFlowRefferenceType.Q_B,
        VarPowerFlowRefferenceType.Q_C,
        VarPowerFlowRefferenceType.phi,
        VarPowerFlowRefferenceType.phi_v,
        VarPowerFlowRefferenceType.Vpk,
        VarPowerFlowRefferenceType.Ipk,
        VarPowerFlowRefferenceType.d_v_N,
        VarPowerFlowRefferenceType.d_v_A,
        VarPowerFlowRefferenceType.d_v_B,
        VarPowerFlowRefferenceType.d_v_C,
    ):
        if reference in block.external_mapping:
            pass
        else:
            block.external_mapping[reference] = None


def _get_rms_input_value(problem: Any, device: Any, reference: VarPowerFlowRefferenceType, x_snapshot: np.ndarray) -> float:
    """Read one RMS FMU input from the current network snapshot.

    :param problem: RMS problem instance.
    :param device: Device using the FMU.
    :param reference: Requested VeraGrid external reference.
    :param x_snapshot: Current accepted state snapshot.
    :return: Numeric input value.
    """

    if reference in {VarPowerFlowRefferenceType.Vm, VarPowerFlowRefferenceType.Va, VarPowerFlowRefferenceType.Vdc}:
        bus_model: Block = device.bus.rms_model
        variable: Var = bus_model.external_mapping[reference]
        return float(x_snapshot[problem.uid2idx_vars[variable.uid]])
    else:
        raise KeyError(f"Unsupported RMS FMU input reference {reference.value!r}")


def _get_emt_input_value(problem: Any, device: Any, reference: VarPowerFlowRefferenceType, x_snapshot: np.ndarray) -> float:
    """Read one EMT FMU input from the current network snapshot.

    :param problem: EMT problem instance.
    :param device: Device using the FMU.
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
        raise KeyError(f"Unsupported EMT FMU input reference {reference.value!r}")


def _read_device_config(device: Any, domain: FmuCsDomain) -> Any | None:
    """Read the serialized FMU device configuration from one VeraGrid device.

    :param device: VeraGrid device instance.
    :param domain: Runtime domain using the FMU.
    :return: Parsed device configuration when available.
    """

    if domain == FmuCsDomain.RMS:
        try:
            config_text: str = device.rms_fmu_import_config
        except AttributeError:
            if isinstance(device, InjectionParent) or isinstance(device, BranchParent):
                raise
            else:
                return None
    else:
        try:
            config_text = device.emt_fmu_import_config
        except AttributeError:
            if isinstance(device, InjectionParent) or isinstance(device, BranchParent):
                raise
            else:
                return None

    return load_fmu_cs_device_config(config_text)


def _build_runtime_spec(device: Any, block: Block, domain: FmuCsDomain) -> FmuCsDeviceSpec | None:
    """Rebuild the runtime specification from the device stored configuration.

    :param device: VeraGrid device instance.
    :param block: Device block used in the active problem.
    :param domain: Runtime domain using the FMU.
    :return: Runtime device specification when available.
    """

    record = _read_device_config(device, domain)
    if record is None:
        return None
    else:
        if record.domain == domain:
            return restore_fmu_cs_spec_from_record(record, block, device.device_type)
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


def register_rms_fmu_cs_device(problem: Any, device: Any, block: Block) -> None:
    """Register one imported FMU CS RMS device in the active RMS problem.

    :param problem: RMS problem instance.
    :param device: VeraGrid device instance.
    :param block: Device RMS block used in the active problem.
    :return: None.
    """

    spec: Optional[FmuCsDeviceSpec] = _build_runtime_spec(device, block, FmuCsDomain.RMS)
    if spec is None:
        return
    else:
        adapter: FmuCsDeviceAdapter
        for adapter in problem._fmu_cs_adapters:
            if adapter.device.idtag == device.idtag:
                return
            else:
                pass

        output_param_indices: dict[VarPowerFlowRefferenceType, int] = dict()
        uid_to_index = _get_event_param_index_map(problem)
        reference: VarPowerFlowRefferenceType
        for reference, uid in spec.output_param_uids.items():
            output_param_indices[reference] = uid_to_index[uid]
        problem._fmu_cs_adapters.append(
            FmuCsDeviceAdapter(problem=problem, device=device, spec=spec, output_param_indices=output_param_indices)
        )
        problem._fmu_cs_initialized = False


def initialize_rms_fmu_cs_devices(problem: Any, x_snapshot: np.ndarray, time_value: float = 0.0) -> None:
    """Initialize all imported FMU CS RMS devices before the time loop starts.

    :param problem: RMS problem instance.
    :param x_snapshot: Initial accepted state snapshot.
    :param time_value: Initial simulation time.
    :return: None.
    """

    if len(problem._fmu_cs_adapters) > 0:
        adapter: FmuCsDeviceAdapter
        for adapter in problem._fmu_cs_adapters:
            outputs: dict[VarPowerFlowRefferenceType, float] = adapter.initialize_outputs(time_value, x_snapshot)
            adapter.apply_outputs(problem._variable_parameters_values, outputs)
            if problem._variable_parameters_values is None:
                problem._last_variable_parameters_values = None
            else:
                problem._last_variable_parameters_values = np.array(problem._variable_parameters_values, copy=True)
        problem._fmu_cs_initialized = True
    else:
        problem._fmu_cs_initialized = True


def align_rms_fmu_cs_device_output_parameters(problem: Any, x_snapshot: np.ndarray, time_value: float = 0.0) -> None:
    """
    Align RMS FMU CS output parameters with the current FMU outputs.

    The imported RMS FMU shell represents each FMU output with one algebraic
    equation of the form ``output_var - parameter_var = 0``. The parameter is
    seeded from the power-flow operating point before the FMU has had a chance to
    report its own initial outputs. A small FMU/default mismatch then appears as
    a DAE residual during the first RMS initialization check. Re-reading the FMU
    outputs and writing them back into the runtime parameter buffer removes that
    artificial mismatch before the solver judges the initial residual.

    :param problem: RMS problem instance.
    :param x_snapshot: Initial accepted state snapshot.
    :param time_value: Initial simulation time.
    :return: None.
    """

    if len(problem._fmu_cs_adapters) > 0:
        if problem._fmu_cs_initialized:
            adapter: FmuCsDeviceAdapter
            for adapter in problem._fmu_cs_adapters:
                outputs: dict[VarPowerFlowRefferenceType, float] = adapter.get_outputs(time_value, x_snapshot)
                adapter.apply_outputs(problem._variable_parameters_values, outputs)
                if problem._variable_parameters_values is None:
                    problem._last_variable_parameters_values = None
                else:
                    problem._last_variable_parameters_values = np.array(problem._variable_parameters_values, copy=True)
        else:
            initialize_rms_fmu_cs_devices(problem=problem, x_snapshot=x_snapshot, time_value=time_value)
    else:
        pass


def advance_rms_fmu_cs_devices(problem: Any, time_value: float, x_snapshot: np.ndarray, step_size: float) -> None:
    """Advance all imported FMU CS RMS devices for one solver step.

    :param problem: RMS problem instance.
    :param time_value: Current simulation time.
    :param x_snapshot: Current accepted state snapshot.
    :param step_size: RMS communication step.
    :return: None.
    """

    if len(problem._fmu_cs_adapters) > 0:
        if problem._fmu_cs_initialized:
            pass
        else:
            initialize_rms_fmu_cs_devices(problem=problem, x_snapshot=x_snapshot, time_value=time_value)

        adapter: FmuCsDeviceAdapter
        for adapter in problem._fmu_cs_adapters:
            outputs = adapter.advance(current_time=time_value, step_size=step_size, x_snapshot=x_snapshot)
            adapter.apply_outputs(problem._variable_parameters_values, outputs)
            if problem._variable_parameters_values is None:
                problem._last_variable_parameters_values = None
            else:
                problem._last_variable_parameters_values = np.array(problem._variable_parameters_values, copy=True)
    else:
        pass


def close_rms_fmu_cs_devices(problem: Any) -> None:
    """Close all imported FMU CS RMS devices.

    :param problem: RMS problem instance.
    :return: None.
    """

    adapter: FmuCsDeviceAdapter
    for adapter in problem._fmu_cs_adapters:
        adapter.close()


def register_emt_fmu_cs_device(problem: Any, device: Any, block: Block) -> None:
    """Register one imported FMU CS EMT device in the active EMT problem.

    :param problem: EMT problem instance.
    :param device: VeraGrid device instance.
    :param block: Device EMT block used in the active problem.
    :return: None.
    """

    spec: Optional[FmuCsDeviceSpec] = _build_runtime_spec(device, block, FmuCsDomain.EMT)
    if spec is None:
        return
    else:
        adapter: FmuCsDeviceAdapter
        for adapter in problem._fmu_cs_adapters:
            if adapter.device.idtag == device.idtag:
                return
            else:
                pass

        output_param_indices: dict[VarPowerFlowRefferenceType, int] = dict()
        uid_to_index = _get_event_param_index_map(problem)
        reference: VarPowerFlowRefferenceType
        for reference, uid in spec.output_param_uids.items():
            output_param_indices[reference] = uid_to_index[uid]
        problem._fmu_cs_adapters.append(
            FmuCsDeviceAdapter(problem=problem, device=device, spec=spec, output_param_indices=output_param_indices)
        )


def queue_emt_fmu_cs_device(problem: Any, device: Any, block: Block) -> None:
    """Queue one EMT device for FMU CS restoration after problem repartitioning.

    :param problem: EMT problem instance.
    :param device: VeraGrid device instance.
    :param block: Device EMT block used in the active problem.
    :return: None.
    """

    record = _read_device_config(device, FmuCsDomain.EMT)
    if record is None:
        return
    else:
        problem._pending_fmu_cs_devices.append((device, block))


def finalize_emt_fmu_cs_devices(problem: Any) -> None:
    """Restore all queued EMT FMU CS devices after the EMT problem is assembled.

    :param problem: EMT problem instance.
    :return: None.
    """

    pending_device: tuple[Any, Block]
    for pending_device in problem._pending_fmu_cs_devices:
        register_emt_fmu_cs_device(problem, pending_device[0], pending_device[1])


def build_emt_boundary_updater(problem: Any) -> Any:
    """Build the effective EMT boundary updater for the active problem.

    :param problem: EMT problem instance.
    :return: Native EMT problem or FMU-aware boundary wrapper.
    """

    if len(problem._fmu_cs_adapters) > 0:
        return CompositeEmtBoundaryUpdater(problem, list(problem._fmu_cs_adapters))
    else:
        return problem
