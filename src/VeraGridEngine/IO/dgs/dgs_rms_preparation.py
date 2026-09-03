# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Dict, List, Set

from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.Devices.Branches.dc_line import DcLine
from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Devices.Branches.series_reactance import SeriesReactance
from VeraGridEngine.Devices.Branches.switch import Switch
from VeraGridEngine.Devices.Branches.transformer import Transformer2W
from VeraGridEngine.Devices.Branches.vsc import VSC
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Injections.battery import Battery
from VeraGridEngine.Devices.Injections.controllable_shunt import ControllableShunt
from VeraGridEngine.Devices.Injections.current_injection import CurrentInjection
from VeraGridEngine.Devices.Injections.external_grid import ExternalGrid
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.Devices.Injections.shunt import Shunt
from VeraGridEngine.Devices.Injections.static_generator import StaticGenerator
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.Parents.dynamic_parent import DynamicDevice
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.enumerations import (
    ConverterControlType,
    DeviceType,
    ParamPowerFlowReferenceType,
    VarPowerFlowReferenceType,
)
from VeraGridEngine.Templates.Rms.genrow_rms_template import get_genrow_rms_template
from VeraGridEngine.Templates.Rms.line_rms_template import (
    get_dc_line_rms_template,
    get_ideal_ac_connector_rms_template,
    get_line_rms_template,
)
from VeraGridEngine.Templates.Rms.load_rms_template import (
    get_load_rms_template,
    get_voltage_dependent_power_rms_template,
)
from VeraGridEngine.enumerations import VoltageDependentPowerModel
from VeraGridEngine.Templates.Rms.shunt_template import get_shunt_template
from VeraGridEngine.Templates.Rms.transformer_rms_template import (
    get_ideal_transformer2w_rms,
    get_transformer2w_rms,
)
from VeraGridEngine.Templates.Rms.voltage_source_template import (
    VoltageSourceBuild,
    build_thevenin_voltage_source,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.bus_rms_template import (
    initialize_bus_rms,
    promote_dc_bus_voltage_to_capacitive_state,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.Utils.procedural_logic import DelayedSwitchEventLogic
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class DgsRmsPreparationReport:
    """
    Store the deterministic outcome of DGS RMS-shell preparation.

    This report distinguishes newly prepared physical devices from devices that
    already carried an imported model and unsupported physical classes that were
    left untouched.
    """

    __slots__ = (
        "_prepared_bus_count",
        "_prepared_device_count",
        "_preserved_device_count",
        "_unsupported_device_count",
        "_failed_device_count",
    )

    def __init__(self) -> None:
        """Initialize all preparation counters to zero."""
        self._prepared_bus_count: int = 0
        self._prepared_device_count: int = 0
        self._preserved_device_count: int = 0
        self._unsupported_device_count: int = 0
        self._failed_device_count: int = 0

    def record_prepared_bus(self) -> None:
        """Record one bus shell created by the preparation stage."""
        self._prepared_bus_count += 1

    def record_prepared_device(self) -> None:
        """Record one physical-device shell created by the preparation stage."""
        self._prepared_device_count += 1

    def record_preserved_device(self) -> None:
        """Record one pre-existing physical-device model left unchanged."""
        self._preserved_device_count += 1

    def record_unsupported_device(self) -> None:
        """Record one unsupported physical class left unchanged."""
        self._unsupported_device_count += 1

    def record_failed_device(self) -> None:
        """Record one handled per-device preparation failure."""
        self._failed_device_count += 1

    def get_prepared_bus_count(self) -> int:
        """Return the number of newly initialized bus shells."""
        return self._prepared_bus_count

    def get_prepared_device_count(self) -> int:
        """Return the number of newly initialized device shells."""
        return self._prepared_device_count

    def get_preserved_device_count(self) -> int:
        """Return the number of imported models preserved unchanged."""
        return self._preserved_device_count

    def get_unsupported_device_count(self) -> int:
        """Return the number of unsupported device classes."""
        return self._unsupported_device_count

    def get_failed_device_count(self) -> int:
        """Return the number of handled device preparation failures."""
        return self._failed_device_count


class _BusUnionFind:
    """Track deterministic AC-bus components during ideal-link contraction."""

    __slots__ = ("_parent", "_rank")

    def __init__(self, buses: List[Bus]) -> None:
        """Initialize one singleton component per imported bus.

        :param buses: Imported buses in stable circuit order.
        :return: None.
        """
        self._parent: Dict[Bus, Bus] = dict()
        self._rank: Dict[Bus, int] = dict()
        bus: Bus
        for bus in buses:
            self._parent[bus] = bus
            self._rank[bus] = 0
        else:
            pass

    def find(self, bus: Bus) -> Bus:
        """Return and compress the representative of one bus component.

        :param bus: Bus whose topology representative is required.
        :return: Deterministic representative bus.
        """
        root: Bus = bus
        while self._parent[root] is not root:
            root = self._parent[root]
        else:
            pass
        cursor: Bus = bus
        next_bus: Bus
        while self._parent[cursor] is not cursor:
            next_bus = self._parent[cursor]
            self._parent[cursor] = root
            cursor = next_bus
        else:
            pass
        return root

    def union(self, bus_from: Bus, bus_to: Bus) -> bool:
        """Join components and report whether the link enters the forest.

        :param bus_from: First terminal bus.
        :param bus_to: Second terminal bus.
        :return: ``True`` when the connector joins distinct components.
        """
        root_from: Bus = self.find(bus=bus_from)
        root_to: Bus = self.find(bus=bus_to)
        if root_from is root_to:
            return False
        else:
            rank_from: int = self._rank[root_from]
            rank_to: int = self._rank[root_to]
            if rank_from < rank_to:
                self._parent[root_from] = root_to
            else:
                self._parent[root_to] = root_from
                if rank_from == rank_to:
                    self._rank[root_from] = rank_from + 1
                else:
                    pass
            return True


def _select_ideal_ac_connector_constraint_ids(
        circuit: MultiCircuit,
        branch_devices: List[DynamicDevice],
) -> Set[str]:
    """Select an acyclic basis of closed ideal AC connectors.

    PowerFactory contracts closed switches and zero-impedance lines before
    solving the network. Imposing every equality in a meshed busbar creates
    redundant multipliers and undefined cycle flows in a fixed-size DAE. A
    deterministic spanning forest retains the same voltage topology while the
    remaining ideal chords carry exact zero transfer flow.

    :param circuit: Imported circuit owning the AC buses.
    :param branch_devices: Physical branches in stable preparation order.
    :return: Device IDs whose templates impose voltage equality.
    """
    union_find: _BusUnionFind = _BusUnionFind(buses=list(circuit.buses))
    constraint_ids: Set[str] = set()
    device: DynamicDevice
    for device in branch_devices:
        is_ideal_ac_connector: bool = False
        if isinstance(device, Switch):
            is_ideal_ac_connector = True
        else:
            if isinstance(device, (Line, SeriesReactance)):
                impedance_square: float = (
                    float(device.R_corrected) ** 2 + float(device.X) ** 2
                )
                is_ideal_ac_connector = impedance_square <= 1.0e-24
            else:
                pass
        is_active_ac_connector: bool = (
            is_ideal_ac_connector
            and bool(device.active)
            and not bool(device.bus_from.is_dc)
            and not bool(device.bus_to.is_dc)
        )
        if is_active_ac_connector:
            joins_components: bool = union_find.union(
                bus_from=device.bus_from,
                bus_to=device.bus_to,
            )
            if joins_components:
                constraint_ids.add(str(device.idtag))
            else:
                pass
        else:
            pass
    else:
        pass
    return constraint_ids


def _get_source_dgs_id_from_runtime_idtag(api_idtag: str | None) -> str | None:
    """Recover the source DGS FID from one expanded runtime identifier.

    DGS rows with ``ngnum > 1`` are expanded into individual VeraGrid devices
    whose identifiers end in ``:<parallel number>``. Reference-machine flags
    belong to the source row, so topology binding must compare the original FID.

    :param api_idtag: Runtime device identifier.
    :return: Source DGS identifier, or ``None`` when it is unavailable.
    """
    if api_idtag is None or api_idtag == "":
        source_dgs_id: str | None = None
    else:
        identifier_parts: List[str] = api_idtag.rsplit(":", maxsplit=1)
        if len(identifier_parts) == 2 and identifier_parts[1].isdigit():
            source_dgs_id = identifier_parts[0]
        else:
            source_dgs_id = api_idtag
    return source_dgs_id


def _find_root_var_by_uid(block: Block, variable_uid: int) -> Var | None:
    """Find one root-block variable through its stable symbolic identity.

    :param block: Configured ElmSym wrapper block.
    :param variable_uid: Exact symbolic variable UID retained by the adapter.
    :return: Matching variable, or ``None`` for an incomplete block contract.
    """
    variable_collections: List[List[Var]] = list([
        block.state_vars,
        block.algebraic_vars,
        block.in_vars,
        block.out_vars,
        list(block.parameters.keys()),
    ])
    matching_variable: Var | None = None
    variable_collection: List[Var]
    candidate: Var
    for variable_collection in variable_collections:
        for candidate in variable_collection:
            if matching_variable is None and candidate.uid == variable_uid:
                matching_variable = candidate
            else:
                pass
        else:
            pass
    else:
        pass
    return matching_variable


def _build_active_ac_bus_components(
        circuit: MultiCircuit,
        branch_devices: List[DynamicDevice],
) -> _BusUnionFind:
    """Build active AC synchronous areas without crossing DC equipment.

    :param circuit: Imported circuit owning the buses.
    :param branch_devices: Imported non-HVDC branch devices.
    :return: Union-find containing every active AC connected component.
    """
    components: _BusUnionFind = _BusUnionFind(buses=list(circuit.buses))
    branch: DynamicDevice
    for branch in branch_devices:
        connects_active_ac_buses: bool = (
            bool(branch.active)
            and branch.bus_from is not None
            and branch.bus_to is not None
            and not bool(branch.bus_from.is_dc)
            and not bool(branch.bus_to.is_dc)
        )
        if connects_active_ac_buses:
            components.union(
                bus_from=branch.bus_from,
                bus_to=branch.bus_to,
            )
        else:
            pass
    else:
        pass
    return components


def _bind_dgs_elmsym_reference_frequencies(
        circuit: MultiCircuit,
        branch_devices: List[DynamicDevice],
        elmsym_reference_source_ids: Set[str],
        logger: Logger,
) -> int:
    """Bind each adapted ElmSym angle to its DGS reference-machine speed.

    PowerFactory evaluates ``d(phi)/dt = omega_base * (speed - fref)``. For a
    reference machine exported with ``ip_ctrl=1``, ``fref`` is that machine's
    own speed; every other synchronous machine in the same connected AC area
    uses the same frame. The binding is resolved exclusively from DGS FIDs and
    active topology, so disconnected islands cannot leak a frequency signal.

    :param circuit: Prepared imported circuit.
    :param branch_devices: Imported non-HVDC branch devices.
    :param elmsym_reference_source_ids: Active ``ElmSym.ip_ctrl=1`` source FIDs.
    :param logger: Diagnostic sink for ambiguous or incomplete source data.
    :return: Number of adapted machines bound to an explicit reference frame.
    """
    components: _BusUnionFind = _build_active_ac_bus_components(
        circuit=circuit,
        branch_devices=branch_devices,
    )
    reference_generator_by_component: Dict[Bus, Generator] = dict()
    reference_source_by_component: Dict[Bus, str] = dict()
    ambiguous_components: Set[Bus] = set()
    generator: Generator
    for generator in circuit.get_generators():
        source_id: str | None = _get_source_dgs_id_from_runtime_idtag(
            api_idtag=generator.idtag,
        )
        is_reference_candidate: bool = (
            bool(generator.active)
            and generator.bus is not None
            and source_id is not None
            and source_id in elmsym_reference_source_ids
        )
        if is_reference_candidate and generator.bus is not None and source_id is not None:
            component: Bus = components.find(bus=generator.bus)
            existing_source_id: str | None = reference_source_by_component.get(
                component,
                None,
            )
            if existing_source_id is None:
                reference_generator_by_component[component] = generator
                reference_source_by_component[component] = source_id
            else:
                if existing_source_id == source_id:
                    # Parallel units expanded from one reference row share one
                    # physical frequency frame; the first stable unit suffices.
                    pass
                else:
                    ambiguous_components.add(component)
        else:
            pass
    else:
        pass

    ambiguous_component: Bus
    for ambiguous_component in ambiguous_components:
        logger.add_warning(
            msg="Multiple DGS reference machines occupy one connected AC area",
            value=reference_source_by_component.get(ambiguous_component, ""),
            expected_value="One ElmSym.ip_ctrl=1 source per connected AC area",
            device_class="ElmSym",
        )
    else:
        pass

    reference_speed_by_component: Dict[Bus, Var] = dict()
    component: Bus
    reference_generator: Generator
    for component, reference_generator in reference_generator_by_component.items():
        if component in ambiguous_components:
            pass
        else:
            reference_block: Block = reference_generator.rms_model
            reference_speed_uid_raw: int | None = (
                reference_block.dynamic_model_contract.dgs_elmsym_speed_var_uid
            )
            if reference_speed_uid_raw is not None:
                reference_speed: Var | None = _find_root_var_by_uid(
                    block=reference_block,
                    variable_uid=reference_speed_uid_raw,
                )
            else:
                reference_speed = None
            if reference_speed is None:
                logger.add_warning(
                    msg="DGS reference machine lacks an adapted RMS speed state",
                    device=reference_generator.name,
                    value=reference_source_by_component.get(component, ""),
                    device_class="ElmSym",
                )
            else:
                reference_speed_by_component[component] = reference_speed
                # A PowerFactory reference machine fixes the rotating dq frame,
                # not its terminal-bus voltage angle.  Retain that distinction
                # for DAE assembly so the bus active-power balance remains and
                # the reference rotor supplies the absolute angular coordinate.
                reference_block.dynamic_model_contract.dgs_elmsym_network_angle_anchor = True
    else:
        pass

    bound_machine_count: int = 0
    for generator in circuit.get_generators():
        machine_block: Block = generator.rms_model
        is_adapted_machine: bool = (
            machine_block.dynamic_model_contract.dgs_elmsym_runtime_adapter
        )
        if is_adapted_machine and bool(generator.active) and generator.bus is not None:
            component = components.find(bus=generator.bus)
            reference_speed = reference_speed_by_component.get(component, None)
            rotor_angle_uid_raw: int | None = (
                machine_block.dynamic_model_contract.dgs_elmsym_rotor_angle_var_uid
            )
            local_speed_uid_raw: int | None = (
                machine_block.dynamic_model_contract.dgs_elmsym_speed_var_uid
            )
            angular_frequency_uid_raw: int | None = (
                machine_block.dynamic_model_contract.dgs_elmsym_angular_frequency_var_uid
            )
            metadata_is_complete: bool = (
                reference_speed is not None
                and rotor_angle_uid_raw is not None
                and local_speed_uid_raw is not None
                and angular_frequency_uid_raw is not None
            )
            if metadata_is_complete:
                rotor_angle: Var | None = _find_root_var_by_uid(
                    block=machine_block,
                    variable_uid=rotor_angle_uid_raw,
                )
                local_speed: Var | None = _find_root_var_by_uid(
                    block=machine_block,
                    variable_uid=local_speed_uid_raw,
                )
                angular_frequency: Var | None = _find_root_var_by_uid(
                    block=machine_block,
                    variable_uid=angular_frequency_uid_raw,
                )
            else:
                rotor_angle = None
                local_speed = None
                angular_frequency = None
            variables_are_complete: bool = (
                rotor_angle is not None
                and local_speed is not None
                and angular_frequency is not None
                and reference_speed is not None
            )
            if variables_are_complete:
                rotor_angle_index: int = machine_block.state_vars.index(rotor_angle)
                machine_block.state_eqs[rotor_angle_index] = (
                    angular_frequency * (local_speed - reference_speed)
                )
                machine_block.dynamic_model_contract.dgs_elmsym_reference_speed_var_uid = (
                    reference_speed.uid
                )
                bound_machine_count += 1
            else:
                pass
        else:
            pass
    else:
        pass
    return bound_machine_count


def _build_dgs_standard_vsc_rms_template(
        circuit: MultiCircuit,
        device: VSC,
) -> RmsModelTemplate:
    """
    Build the standard loss-balanced RMS shell for one imported VSC.

    The shell supports native monopolar and bipolar topologies. It deliberately
    contains no controller dynamics: an exact exported composite is activated
    before this preparation stage and therefore takes precedence.

    :param circuit: Circuit supplying the symbolic factory and system base.
    :param device: Imported converter carrying loss and control properties.
    :return: Assignable standard RMS converter template.
    """
    dc_voltage: Var = circuit.var_factory.add_var(
        "Vdc",
        VarPowerFlowReferenceType.Vf_dc,
    )
    ac_voltage_magnitude: Var = circuit.var_factory.add_var(
        "Vm",
        VarPowerFlowReferenceType.Vmt,
    )
    ac_voltage_angle: Var = circuit.var_factory.add_var(
        "Va",
        VarPowerFlowReferenceType.Vat,
    )
    dc_power: Var = circuit.var_factory.add_var(
        "Pf",
        VarPowerFlowReferenceType.Pf,
    )
    ac_active_power: Var = circuit.var_factory.add_var(
        "Pt",
        VarPowerFlowReferenceType.Pt,
    )
    ac_reactive_power: Var = circuit.var_factory.add_var(
        "Qt",
        VarPowerFlowReferenceType.Qt,
    )
    idle_loss: Var = circuit.var_factory.add_var("alpha1")
    linear_loss: Var = circuit.var_factory.add_var("alpha2")
    quadratic_loss: Var = circuit.var_factory.add_var("alpha3")
    epsilon: Const = circuit.var_factory.add_const(1.0e-9)

    # Retain a physical fixed-Q contract only when the imported DGS explicitly
    # selected Q control. Other modes remain neutral until their exact exported
    # controller replaces this fallback.
    if device.control2 == ConverterControlType.Qac:
        reactive_power_target_pu: float = float(device.control2_val) / float(circuit.Sbase)
    else:
        reactive_power_target_pu = 0.0

    ac_current_magnitude: Expr = sym.sqrt(
        ac_active_power * ac_active_power
        + ac_reactive_power * ac_reactive_power
        + epsilon
    ) / (ac_voltage_magnitude + epsilon)
    converter_loss: Expr = (
        idle_loss
        + linear_loss * ac_current_magnitude
        + quadratic_loss * ac_current_magnitude * ac_current_magnitude
    )

    # One converter control closes the independent DC/AC active-power degree of
    # freedom. The target already carries the sign convention established by
    # the static DGS converter mapping, so no case-specific sign is introduced.
    if device.control1 == ConverterControlType.Vm_dc:
        active_control_equation: Expr = (
            dc_voltage - Const(float(device.control1_val))
        )
    else:
        if device.control1 == ConverterControlType.Pdc:
            active_control_equation = (
                dc_power
                - Const(float(device.control1_val) / float(circuit.Sbase))
            )
        else:
            # ``Pac`` is the regular remaining contract. More elaborate droop
            # modes are supplied by their exported composite; the fallback
            # retains their configured active-power operating target.
            active_control_equation = (
                ac_active_power
                - Const(float(device.control1_val) / float(circuit.Sbase))
            )

    block: Block = Block(
        name="DGS VSC RMS shell",
        in_vars=list([
            dc_voltage,
            ac_voltage_magnitude,
            ac_voltage_angle,
        ]),
        algebraic_vars=list([
            dc_power,
            ac_active_power,
        ]),
        algebraic_eqs=list([
            dc_power + ac_active_power - converter_loss,
            active_control_equation,
        ]),
        parameters={
            idle_loss: Const(float(device.alpha1)),
            linear_loss: Const(float(device.alpha2)),
            quadratic_loss: Const(float(device.alpha3)),
            ac_reactive_power: Const(reactive_power_target_pu),
        },
        init_eqs={
            dc_power: converter_loss - ac_active_power,
        },
        external_mapping={
            VarPowerFlowReferenceType.Vf_dc: dc_voltage,
            VarPowerFlowReferenceType.Vmt: ac_voltage_magnitude,
            VarPowerFlowReferenceType.Vat: ac_voltage_angle,
            VarPowerFlowReferenceType.Pf: dc_power,
            VarPowerFlowReferenceType.Pt: ac_active_power,
            VarPowerFlowReferenceType.Qt: ac_reactive_power,
        },
        api_obj_mapping={
            ParamPowerFlowReferenceType.alpha1: idle_loss,
            ParamPowerFlowReferenceType.alpha2: linear_loss,
            ParamPowerFlowReferenceType.alpha3: quadratic_loss,
        },
    )
    template: RmsModelTemplate = RmsModelTemplate(name="DGS VSC RMS shell")
    template.tpe = DeviceType.VscDevice
    template.block = block
    return template


def _build_dgs_elmgenstat_rms_template(
        circuit: MultiCircuit,
        device_tpe: DeviceType,
) -> RmsModelTemplate:
    """Build the supported ElmGenstat current-source RMS shell.

    Current DGS rows do not declare ``iSimModel``. The importer therefore
    materializes only PowerFactory's documented legacy current-source default
    instead of inventing an unavailable selector.

    :param circuit: Circuit owning the shared variable factory.
    :param device_tpe: Exact VeraGrid presentation type of the imported host.
    :return: Standard constant-current RMS template.
    """
    template: RmsModelTemplate = get_voltage_dependent_power_rms_template(
        vfactory=circuit.var_factory,
        voltage_model=VoltageDependentPowerModel.ConstantCurrent,
        name="DGS ElmGenstat constant current RMS model",
    )
    template.tpe = device_tpe
    return template


def _find_registered_thevenin_template(
        circuit: MultiCircuit,
        resistance_pu: float,
        reactance_pu: float,
) -> RmsModelTemplate | None:
    """Find one reusable external-grid template with the same impedance.

    DGS projects commonly contain several ``ElmXnet`` devices backed by the
    same positive-sequence source declaration. The circuit catalogue should
    expose that declaration once while each device keeps an independent block
    copied by the normal template setter.

    :param circuit: Circuit whose public RMS catalogue is searched.
    :param resistance_pu: Required positive-sequence resistance.
    :param reactance_pu: Required positive-sequence reactance.
    :return: Matching registered template, or ``None`` when none exists.
    """
    registered_template: RmsModelTemplate
    for registered_template in circuit.rms_models:
        is_thevenin_template: bool = (
            registered_template.tpe is DeviceType.GeneratorDevice
            and registered_template.name
            == "DGS external grid Thevenin RMS shell"
        )
        if is_thevenin_template:
            registered_resistance: float | None = None
            registered_reactance: float | None = None
            parameter: Var
            parameter_value: Const | Expr
            for parameter, parameter_value in registered_template.block.parameters.items():
                if parameter.name == "R1" and isinstance(parameter_value, Const):
                    registered_resistance = float(parameter_value.value)
                elif parameter.name == "X1" and isinstance(parameter_value, Const):
                    registered_reactance = float(parameter_value.value)
                else:
                    pass
            if (
                    registered_resistance == resistance_pu
                    and registered_reactance == reactance_pu
            ):
                return registered_template
            else:
                pass
        else:
            pass
    return None


def _build_dgs_default_rms_template(
        circuit: MultiCircuit,
        device: DynamicDevice,
        external_grid_source_ids: Set[str],
        elmgenstat_source_ids: Set[str],
        elmsym_source_ids: Set[str],
        typeless_elmlod_source_ids: Set[str],
        ideal_ac_connector_constraint_ids: Set[str],
) -> RmsModelTemplate | None:
    """
    Build the standard RMS shell appropriate for one imported physical device.

    The exact DGS source identity is used to distinguish an ``ElmXnet`` that the
    static importer represents as a ``Generator`` for short-circuit studies from
    a real synchronous generator. No names or project-specific labels are used.

    :param circuit: Circuit owning the shared variable factory.
    :param device: Physical device whose RMS model is missing.
    :param external_grid_source_ids: Exact FIDs exported from ``ElmXnet``.
    :param elmgenstat_source_ids: Exact FIDs exported from ``ElmGenstat``.
    :param elmsym_source_ids: Exact FIDs exported from ``ElmSym``.
    :param typeless_elmlod_source_ids: Exact FIDs of ``ElmLod`` objects whose
        DGS type reference is empty.
    :param ideal_ac_connector_constraint_ids: Ideal links selected for the
        acyclic voltage-constraint basis.
    :return: Standard RMS template, or ``None`` for an unsupported class.
    """
    template: RmsModelTemplate | None

    # Branch shells reproduce the static network equations around the solved
    # operating point. DC lines retain their current state, while AC passive
    # branches use the standard polar power-balance model.
    is_two_terminal_dc_branch: bool = (
        isinstance(device, (Line, SeriesReactance, Switch))
        and device.bus_from.is_dc
        and device.bus_to.is_dc
    )
    if isinstance(device, DcLine) or is_two_terminal_dc_branch:
        # Only a native Line exported with a positive DC series inductance owns
        # an RL energy state. DcLine, switch, and series-reactance objects do
        # not expose that physical parameter and therefore use exact Ohm law.
        use_dynamic_inductance: bool = (
            isinstance(device, Line)
            and float(device.dc_series_inductance_pu_seconds) > 0.0
        )
        template = get_dc_line_rms_template(
            vfactory=circuit.var_factory,
            name="DGS DC line RMS shell",
            use_dynamic_inductance=use_dynamic_inductance,
        )
    else:
        if isinstance(device, VSC):
            # A native converter without an assignable exported composite still
            # needs its standard AC/DC loss balance.  When an exact DGS dynamic
            # adapter exists, activation runs first and this fallback is never
            # installed, so imported controls always retain precedence.
            template = _build_dgs_standard_vsc_rms_template(
                circuit=circuit,
                device=device,
            )
        else:
            if isinstance(device, Transformer2W):
                transformer_impedance_square: float = (
                    float(device.R_corrected) ** 2 + float(device.X) ** 2
                )
                if transformer_impedance_square <= 1.0e-24:
                    # PowerFactory permits ideal transformers and contracts
                    # them in the static network. The exact constraint model
                    # preserves that topology without a numerically arbitrary
                    # large series admittance in the dynamic DAE.
                    existing_ideal_template: RmsModelTemplate | None = None
                    registered_template: RmsModelTemplate
                    for registered_template in circuit.rms_models:
                        if (
                                registered_template.tpe
                                is DeviceType.Transformer2WDevice
                                and registered_template.name
                                == "rms_ideal_trafo_template"
                        ):
                            existing_ideal_template = registered_template
                            break
                        else:
                            pass
                    if existing_ideal_template is None:
                        template = get_ideal_transformer2w_rms(
                            vf=circuit.var_factory,
                        )
                    else:
                        template = existing_ideal_template
                else:
                    template = get_transformer2w_rms(
                        vf=circuit.var_factory,
                        use_phasor_template=False,
                    )
            else:
                if isinstance(device, Switch):
                    enforce_constraint: bool = (
                        str(device.idtag)
                        in ideal_ac_connector_constraint_ids
                    )
                    switch_template_name: str = (
                        "DGS ideal AC connector RMS shell"
                        if enforce_constraint
                        else "DGS redundant ideal AC connector RMS shell"
                    )
                    template = get_ideal_ac_connector_rms_template(
                        vfactory=circuit.var_factory,
                        name=switch_template_name,
                        enforce_voltage_constraint=enforce_constraint,
                    )
                else:
                    if isinstance(device, (Line, SeriesReactance)):
                        passive_resistance: float = float(device.R_corrected)
                        passive_impedance_square: float = (
                            passive_resistance ** 2 + float(device.X) ** 2
                        )
                        if passive_impedance_square <= 1.0e-24:
                            # PowerFactory contracts zero-impedance AC lines.
                            # The exact ideal constraint keeps transfer P/Q as
                            # nodal unknowns and enforces equal voltage phasors;
                            # zero regular-line admittance opens the connector.
                            enforce_constraint = (
                                str(device.idtag)
                                in ideal_ac_connector_constraint_ids
                            )
                            connector_template_name: str = (
                                "DGS ideal AC connector RMS shell"
                                if enforce_constraint
                                else "DGS redundant ideal AC connector RMS shell"
                            )
                            template = get_ideal_ac_connector_rms_template(
                                vfactory=circuit.var_factory,
                                name=connector_template_name,
                                enforce_voltage_constraint=enforce_constraint,
                            )
                        else:
                            template = get_line_rms_template(
                                vfactory=circuit.var_factory,
                                name="DGS passive branch RMS shell",
                            )
                    else:
                        # ``ElmXnet`` is deliberately represented as a Generator by the
                        # static DGS importer. Its exact FID retains the voltage-source
                        # semantics without relying on a display name or slack heuristic.
                        if isinstance(device, ExternalGrid) or (
                                isinstance(device, Generator)
                                and str(device.idtag) in external_grid_source_ids
                        ):
                            if (
                                    isinstance(device, Generator)
                                    and str(device.idtag) in external_grid_source_ids
                                    and (
                                        abs(float(device.R1)) > 0.0
                                        or abs(float(device.X1)) > 0.0
                                    )
                            ):
                                # The static importer derives R1/X1 exclusively from
                                # ElmXnet snss/rntxn. Preserve that finite source
                                # impedance instead of clamping its terminal.
                                source_resistance: float = float(device.R1)
                                source_reactance: float = float(device.X1)
                                existing_thevenin_template: RmsModelTemplate | None = (
                                    _find_registered_thevenin_template(
                                        circuit=circuit,
                                        resistance_pu=source_resistance,
                                        reactance_pu=source_reactance,
                                    )
                                )
                                if existing_thevenin_template is None:
                                    template = build_thevenin_voltage_source(
                                        vfactory=circuit.var_factory,
                                        resistance_pu=source_resistance,
                                        reactance_pu=source_reactance,
                                        name="DGS external grid Thevenin RMS shell",
                                    )
                                else:
                                    template = existing_thevenin_template
                            else:
                                # Native ideal ExternalGrid devices and DGS
                                # sources without usable impedance retain the
                                # established ideal-voltage boundary condition.
                                template = VoltageSourceBuild(
                                    vfactory=circuit.var_factory,
                                    name="DGS external grid RMS shell",
                                )
                        else:
                            source_id: str = str(device.idtag)
                            is_elmgenstat_injection: bool = (
                                isinstance(
                                    device,
                                    (
                                        Generator,
                                        Battery,
                                        StaticGenerator,
                                        CurrentInjection,
                                    ),
                                )
                                and source_id in elmgenstat_source_ids
                            )
                            if is_elmgenstat_injection:
                                # ElmGenstat can map to Generator, Battery or
                                # StaticGenerator according to technology. Its
                                # exact source identity, not that presentation
                                # class, owns the native RMS source law.
                                template = _build_dgs_elmgenstat_rms_template(
                                    circuit=circuit,
                                    device_tpe=device.device_type,
                                )
                            else:
                                if (
                                    isinstance(device, (Generator, Battery))
                                    and source_id in elmsym_source_ids
                                ):
                                    # Do not fabricate dynamics for an
                                    # unresolved exported synchronous source.
                                    template = get_load_rms_template(
                                        vfactory=circuit.var_factory,
                                        name="DGS unresolved ElmSym fixed injection RMS shell",
                                    )
                                elif isinstance(device, (Generator, Battery)):
                                    template = get_genrow_rms_template(
                                        vfactory=circuit.var_factory,
                                        name="DGS synchronous machine RMS shell",
                                    )
                                else:
                                    # Fixed injections share algebraic shells
                                    # initialized from the solved operating point.
                                    if isinstance(device, Load):
                                        if source_id in typeless_elmlod_source_ids:
                                            # A typeless ElmLod is a static
                                            # admittance initialized from its
                                            # load-flow result.
                                            template = get_voltage_dependent_power_rms_template(
                                                vfactory=circuit.var_factory,
                                                voltage_model=(
                                                    VoltageDependentPowerModel.
                                                    ConstantImpedance
                                                ),
                                                name=(
                                                    "DGS typeless ElmLod constant impedance RMS model"
                                                ),
                                            )
                                        else:
                                            template = get_load_rms_template(
                                                vfactory=circuit.var_factory,
                                                name="DGS fixed load RMS shell",
                                            )
                                    else:
                                        if isinstance(device, (StaticGenerator, CurrentInjection)):
                                            template = get_load_rms_template(
                                                vfactory=circuit.var_factory,
                                                name="DGS fixed injection RMS shell",
                                            )
                                        else:
                                            if isinstance(device, (Shunt, ControllableShunt)):
                                                template = get_shunt_template(
                                                    vfactory=circuit.var_factory,
                                                    name="DGS shunt RMS shell",
                                                    phasor=False,
                                                )
                                            else:
                                                template = None

    return template


def _find_unique_rms_conduction_parameter(
        block: Block,
) -> tuple[Block | None, Var | None]:
    """Find the single retained ``u`` parameter in a standard RMS shell.

    :param block: Root block of one prepared physical device.
    :return: Owning block and parameter, or two ``None`` values if ambiguous.
    """
    parameter_owner: Block | None = None
    conduction_parameter: Var | None = None
    candidate_block: Block
    candidate_parameter: Var
    for candidate_block in block.get_all_blocks():
        for candidate_parameter in candidate_block.event_dict.keys():
            if candidate_parameter.name == "u":
                if conduction_parameter is None:
                    parameter_owner = candidate_block
                    conduction_parameter = candidate_parameter
                else:
                    return None, None
            else:
                pass
    return parameter_owner, conduction_parameter


def _seed_rms_conduction_status_from_device(device: DynamicDevice) -> bool:
    """Seed a retained RMS conduction parameter from physical service state.

    Static power flow excludes an out-of-service branch. Its fixed-size RMS
    template must start with the same status; otherwise dynamic initialization
    silently reconnects equipment that the solved operating point excluded.

    :param device: Physical device owning the connected RMS block.
    :return: ``True`` when a retained conduction parameter was initialized.
    """
    status_owner: Block | None
    status_parameter: Var | None
    status_owner, status_parameter = _find_unique_rms_conduction_parameter(
        block=device.rms_model,
    )
    seeded: bool = False
    if status_owner is not None and status_parameter is not None:
        status_value: float = 1.0 if bool(device.active) else 0.0
        status_owner.event_dict[status_parameter] = Const(status_value)
        seeded = True
    else:
        pass
    return seeded


def bind_dgs_switch_event_runtime(
        circuit: MultiCircuit,
        templates_by_root_dgs_id: Dict[
            str,
            RmsModelTemplate | EmtModelTemplate,
        ],
        logger: Logger,
) -> int:
    """Connect imported guarded switch modes to physical RMS conduction states.

    Multiple physical switches can sit in series on one equipment object. Their
    exported binary positions are multiplied so opening either terminal removes
    that equipment from the fixed-size RMS equations.

    :param circuit: Prepared circuit containing physical RMS shells.
    :param templates_by_root_dgs_id: Imported composite templates keyed by root FID.
    :param logger: Import diagnostic sink.
    :return: Number of physical RMS shells connected to switch-event modes.
    """
    device_by_idtag: Dict[str, DynamicDevice] = dict()
    physical_device: DynamicDevice
    for physical_device in circuit.get_branches_iter(
            add_vsc=False,
            add_hvdc=False,
            add_switch=True,
    ):
        device_by_idtag[physical_device.idtag] = physical_device

    modes_by_device_idtag: Dict[str, List[Var]] = dict()
    root_template: RmsModelTemplate | EmtModelTemplate
    root_block: Block
    logic_entry: object
    mode_block: Block
    mode_parameter: Var
    for root_template in templates_by_root_dgs_id.values():
        if isinstance(root_template, RmsModelTemplate):
            pass
        else:
            raise ValueError(
                "DGS RMS switch-event binding received a non-RMS template"
            )
        for root_block in root_template.block.get_all_blocks():
            for logic_entry in root_block.procedural_logic:
                if isinstance(logic_entry, DelayedSwitchEventLogic):
                    if logic_entry.command_closed:
                        logger.add_warning(
                            msg="DGS close-switch event binding is not supported",
                            device=logic_entry.name,
                            value=logic_entry.target_switch_idtag,
                        )
                    else:
                        matching_modes: List[Var] = list()
                        matching_mode_uids: Set[int] = set()
                        for mode_block in root_template.block.get_all_blocks():
                            for mode_parameter in mode_block.mode_dict.keys():
                                if mode_parameter.name == logic_entry.output_var_name:
                                    if mode_parameter.uid not in matching_mode_uids:
                                        matching_modes.append(mode_parameter)
                                        matching_mode_uids.add(mode_parameter.uid)
                                    else:
                                        pass
                                else:
                                    pass
                        if len(matching_modes) == 1:
                            device_modes: List[Var] | None = modes_by_device_idtag.get(
                                logic_entry.target_device_idtag,
                                None,
                            )
                            if device_modes is None:
                                device_modes = list()
                                device_modes.append(matching_modes[0])
                                modes_by_device_idtag[
                                    logic_entry.target_device_idtag
                                ] = device_modes
                            else:
                                mode_is_new: bool = True
                                existing_device_mode: Var
                                for existing_device_mode in device_modes:
                                    if existing_device_mode.uid == matching_modes[0].uid:
                                        mode_is_new = False
                                    else:
                                        pass
                                if mode_is_new:
                                    device_modes.append(matching_modes[0])
                                else:
                                    pass
                        else:
                            logger.add_warning(
                                msg="DGS switch event mode is missing or ambiguous",
                                device=logic_entry.name,
                                value=(
                                    f"{logic_entry.output_var_name}; "
                                    f"matches={len(matching_modes)}"
                                ),
                            )
                else:
                    pass

    bound_count: int = 0
    device_idtag: str
    switch_modes: List[Var]
    for device_idtag, switch_modes in modes_by_device_idtag.items():
        physical_device = device_by_idtag.get(device_idtag, None)
        if physical_device is None or physical_device.rms_model.empty():
            logger.add_warning(
                msg="DGS switch event physical target is unavailable",
                device=device_idtag,
            )
        else:
            conduction_owner: Block | None
            conduction_parameter: Var | None
            conduction_owner, conduction_parameter = (
                _find_unique_rms_conduction_parameter(
                    block=physical_device.rms_model,
                )
            )
            if conduction_owner is None or conduction_parameter is None:
                logger.add_warning(
                    msg="DGS switch event target has no unique RMS conduction state",
                    device=device_idtag,
                )
            else:
                conduction_expression: Expr | Const = conduction_owner.event_dict[
                    conduction_parameter
                ]
                switch_mode: Var
                for switch_mode in switch_modes:
                    conduction_expression = conduction_expression * switch_mode
                conduction_owner.event_dict[conduction_parameter] = (
                    conduction_expression
                )
                bound_count += 1
    return bound_count


def _prepare_dgs_rms_device(
        circuit: MultiCircuit,
        device: DynamicDevice,
        external_grid_source_ids: Set[str],
        elmgenstat_source_ids: Set[str],
        elmsym_source_ids: Set[str],
        typeless_elmlod_source_ids: Set[str],
        ideal_ac_connector_constraint_ids: Set[str],
        logger: Logger,
        report: DgsRmsPreparationReport,
) -> None:
    """
    Preserve or prepare the RMS model of one DGS physical device.

    :param circuit: Circuit owning the shared variable factory.
    :param device: Physical device to inspect.
    :param external_grid_source_ids: Exact FIDs exported from ``ElmXnet``.
    :param elmgenstat_source_ids: Exact FIDs exported from ``ElmGenstat``.
    :param elmsym_source_ids: Exact FIDs exported from ``ElmSym``.
    :param typeless_elmlod_source_ids: Exact FIDs of typeless ``ElmLod``.
    :param ideal_ac_connector_constraint_ids: Ideal links selected for the
        acyclic voltage-constraint basis.
    :param logger: Diagnostic sink for partial failures.
    :param report: Mutable preparation report.
    :return: None.
    """
    if device.rms_model.empty():
        template: RmsModelTemplate | None = _build_dgs_default_rms_template(
            circuit=circuit,
            device=device,
            external_grid_source_ids=external_grid_source_ids,
            elmgenstat_source_ids=elmgenstat_source_ids,
            elmsym_source_ids=elmsym_source_ids,
            typeless_elmlod_source_ids=typeless_elmlod_source_ids,
            ideal_ac_connector_constraint_ids=ideal_ac_connector_constraint_ids,
        )
        if template is None:
            report.record_unsupported_device()
            logger.add_warning(
                msg="DGS device has no standard RMS shell",
                device=device.name,
                device_class=device.device_type.value,
            )
        else:
            try:
                # The regular template setter duplicates and connects the model
                # through the same path used by VeraGrid's Dynamic Editor.
                device.rms_template = template
                # The device keeps a typed reference to its reusable template.
                # Register that public object in the circuit so VeraGrid
                # persistence writes the referenced declaration before devices
                # are reconstructed on reopen.
                if template in circuit.rms_models:
                    pass
                else:
                    circuit.add_rms_model(template)
            except (TypeError, ValueError, KeyError) as exc:
                report.record_failed_device()
                logger.add_warning(
                    msg="DGS standard RMS shell could not be assigned",
                    device=device.name,
                    device_class=device.device_type.value,
                    value=str(exc),
                )
            else:
                report.record_prepared_device()
    else:
        # Imported DGS controllers have priority over generic electrical shells.
        report.record_preserved_device()

    # Apply the physical in/out-of-service state after either assignment path.
    # Imported and standard branch models therefore share the same startup
    # contract without relying on template-specific default constants.
    _seed_rms_conduction_status_from_device(device=device)


def _get_monopolar_vsc_dc_capacitance_pu_seconds(
        converter: VSC,
        system_base_mva: float,
) -> float:
    """
    Return the native ``ElmVscmono`` DC-link energy coefficient.

    PowerFactory two-level converters own ``Cdc`` directly. For legacy MMC
    imports without a terminal coefficient, the three phase-leg submodule
    banks retain their established ``Ceq = 3 * Cmod / (2 * Nsm)`` reduction.
    The returned coefficient converts the selected physical capacitance to the bus RMS equation
    ``dVpu/dt = Ppu / (Cpu_seconds * Vpu)``.  Invalid or inapplicable device
    data produce zero so a partially exported DGS remains usable.

    :param converter: DGS-converted VSC connected to the DC bus.
    :param system_base_mva: Circuit power base in MVA.
    :return: Equivalent DC-link capacitance in per-unit seconds.
    """
    is_monopolar_dc_converter: bool = (
        converter.active
        and converter.bus_dc_n is None
        and converter.bus_from.is_dc
        and not converter.bus_from.is_grounded
    )
    dc_link_capacitance_uf: float = float(converter.dc_link_capacitance_uf)
    arm_capacitance_uf: float = float(converter.mmc_arm_capacitance_uf)
    dc_bus_base_kv: float = float(converter.bus_from.Vnom)
    physical_data_ready: bool = (
        is_monopolar_dc_converter
        and (dc_link_capacitance_uf > 0.0 or arm_capacitance_uf > 0.0)
        and dc_bus_base_kv > 0.0
        and system_base_mva > 0.0
    )
    if physical_data_ready:
        # A two-level converter owns Cdc directly. Legacy MMC imports retain
        # the existing arm-energy reduction when no terminal capacitor exists.
        if dc_link_capacitance_uf > 0.0:
            equivalent_capacitance_f: float = dc_link_capacitance_uf * 1.0e-6
        else:
            equivalent_capacitance_f = 1.5 * arm_capacitance_uf * 1.0e-6
        dc_bus_base_volts: float = dc_bus_base_kv * 1.0e3
        system_base_watts: float = system_base_mva * 1.0e6
        capacitance_pu_seconds: float = (
            equivalent_capacitance_f
            * dc_bus_base_volts
            * dc_bus_base_volts
            / system_base_watts
        )
    else:
        capacitance_pu_seconds = 0.0
    return capacitance_pu_seconds


def prepare_dgs_circuit_for_rms(
        circuit: MultiCircuit,
        external_grid_source_ids: Set[str],
        logger: Logger,
        elmgenstat_source_ids: Set[str] | None = None,
        elmsym_source_ids: Set[str] | None = None,
        elmsym_reference_source_ids: Set[str] | None = None,
        typeless_elmlod_source_ids: Set[str] | None = None,
) -> DgsRmsPreparationReport:
    """
    Complete missing standard RMS shells after one massive DGS import.

    The function is deterministic, idempotent and independent of PowerFactory.
    It does not replace imported dynamic models: only empty runtime slots receive
    standard electrical shells so the circuit can enter the normal RMS workflow.

    :param circuit: Imported circuit to prepare.
    :param external_grid_source_ids: Exact FIDs exported from ``ElmXnet``.
    :param logger: Diagnostic sink for unsupported classes and partial failures.
    :param elmgenstat_source_ids: Optional exact FIDs exported from ``ElmGenstat``.
    :param elmsym_source_ids: Optional exact FIDs exported from ``ElmSym``.
    :param elmsym_reference_source_ids: Optional active ``ElmSym.ip_ctrl=1``
        FIDs defining the frequency frame of each connected AC area.
    :param typeless_elmlod_source_ids: Optional exact FIDs exported from
        ``ElmLod`` without a ``TypLod`` reference.
    :return: Structured preparation report.
    """
    report: DgsRmsPreparationReport = DgsRmsPreparationReport()
    effective_elmgenstat_source_ids: Set[str]
    if elmgenstat_source_ids is None:
        effective_elmgenstat_source_ids = set()
    else:
        effective_elmgenstat_source_ids = elmgenstat_source_ids
    effective_elmsym_source_ids: Set[str]
    if elmsym_source_ids is None:
        effective_elmsym_source_ids = set()
    else:
        effective_elmsym_source_ids = elmsym_source_ids
    effective_elmsym_reference_source_ids: Set[str]
    if elmsym_reference_source_ids is None:
        effective_elmsym_reference_source_ids = set()
    else:
        effective_elmsym_reference_source_ids = elmsym_reference_source_ids
    effective_typeless_elmlod_source_ids: Set[str]
    if typeless_elmlod_source_ids is None:
        effective_typeless_elmlod_source_ids = set()
    else:
        effective_typeless_elmlod_source_ids = typeless_elmlod_source_ids
    bus: Bus
    branch_devices: List[DynamicDevice] = list(
        circuit.get_branches_iter(
            add_vsc=False,
            add_hvdc=False,
            add_switch=True,
        )
    )
    ideal_ac_connector_constraint_ids: Set[str] = (
        _select_ideal_ac_connector_constraint_ids(
            circuit=circuit,
            branch_devices=branch_devices,
        )
    )
    injection_devices: List[DynamicDevice] = list(circuit.get_injection_devices_iter())
    device: DynamicDevice
    dc_bus_capacitance: Dict[Bus, float] = dict()

    # A DGS DC cable exports total shunt capacitance through TypLne.bline.
    # Split each active cable equally between its terminal nodes, which is the
    # standard lumped pi representation used by PowerFactory RMS simulation.
    for bus in circuit.buses:
        dc_bus_capacitance[bus] = 0.0
    for line in circuit.lines:
        is_dc_cable: bool = line.bus_from.is_dc and line.bus_to.is_dc
        if is_dc_cable:
            if not line.dc_cable_dynamic_parameters_complete:
                raise ValueError(
                    f"DGS DC cable {line.idtag} lacks complete RMS energy parameters."
                )
            else:
                pass
            if line.active:
                terminal_capacitance: float = (
                    0.5 * float(line.dc_shunt_capacitance_pu_seconds)
                )
                dc_bus_capacitance[line.bus_from] += terminal_capacitance
                dc_bus_capacitance[line.bus_to] += terminal_capacitance
            else:
                pass
        else:
            pass

    # A native monopolar converter places its exported cell energy directly at
    # its single DC terminal.  Add it to the same nodal coefficient as cable
    # shunts so the solver advances one physical voltage state rather than two
    # constrained copies of the same DC-link voltage.
    converter: VSC
    for converter in circuit.get_vsc():
        converter_capacitance: float = (
            _get_monopolar_vsc_dc_capacitance_pu_seconds(
                converter=converter,
                system_base_mva=float(circuit.Sbase),
            )
        )
        if converter_capacitance > 0.0:
            dc_bus_capacitance[converter.bus_from] += converter_capacitance
        else:
            pass

    # Every device template connects against an existing bus shell, so buses are
    # initialized first and only when an imported model has not already done it.
    for bus in circuit.buses:
        if bus.is_dc and not bus.is_grounded:
            bus_capacitance: float = dc_bus_capacitance.get(bus, 0.0)
        else:
            bus_capacitance = 0.0
        vdc_shell_var: Var | None = bus.rms_model.external_mapping.get(
            VarPowerFlowReferenceType.Vdc,
            None,
        )
        is_replaceable_dc_shell: bool = (
            bus_capacitance > 0.0
            and vdc_shell_var is not None
            and len(bus.rms_model.state_vars) == 0
            and len(bus.rms_model.algebraic_vars) == 1
            and len(bus.rms_model.algebraic_eqs) == 0
            and len(bus.rms_model.children) == 0
        )
        if bus.rms_model.empty():
            initialize_bus_rms(
                bus=bus,
                vf=circuit.var_factory,
                dc_shunt_capacitance_pu_seconds=bus_capacitance,
            )
            report.record_prepared_bus()
        elif is_replaceable_dc_shell and vdc_shell_var is not None:
            # Dynamic association has already connected controller inputs to
            # this exact Vdc UID. Promote the existing variable in place so no
            # imported symbolic connection is invalidated by a replacement.
            promote_dc_bus_voltage_to_capacitive_state(
                bus_rms_model=bus.rms_model,
                vf=circuit.var_factory,
                dc_shunt_capacitance_pu_seconds=bus_capacitance,
            )
            report.record_prepared_bus()
        else:
            pass

    # Branches are connected before injections so all passive network equations
    # are available when the RMS problem compiles its nodal balances.
    for device in branch_devices:
        _prepare_dgs_rms_device(
            circuit=circuit,
            device=device,
            external_grid_source_ids=external_grid_source_ids,
            elmgenstat_source_ids=effective_elmgenstat_source_ids,
            elmsym_source_ids=effective_elmsym_source_ids,
            typeless_elmlod_source_ids=effective_typeless_elmlod_source_ids,
            ideal_ac_connector_constraint_ids=ideal_ac_connector_constraint_ids,
            logger=logger,
            report=report,
        )

    for device in circuit.get_vsc():
        _prepare_dgs_rms_device(
            circuit=circuit,
            device=device,
            external_grid_source_ids=external_grid_source_ids,
            elmgenstat_source_ids=effective_elmgenstat_source_ids,
            elmsym_source_ids=effective_elmsym_source_ids,
            typeless_elmlod_source_ids=effective_typeless_elmlod_source_ids,
            ideal_ac_connector_constraint_ids=ideal_ac_connector_constraint_ids,
            logger=logger,
            report=report,
        )

    for device in injection_devices:
        _prepare_dgs_rms_device(
            circuit=circuit,
            device=device,
            external_grid_source_ids=external_grid_source_ids,
            elmgenstat_source_ids=effective_elmgenstat_source_ids,
            elmsym_source_ids=effective_elmsym_source_ids,
            typeless_elmlod_source_ids=effective_typeless_elmlod_source_ids,
            ideal_ac_connector_constraint_ids=ideal_ac_connector_constraint_ids,
            logger=logger,
            report=report,
        )

    # PowerFactory evaluates every synchronous-machine angle in its connected
    # area's exported reference frame. This second pass must happen after all
    # generator wrappers exist because the equation references another device's
    # speed state through its globally stable symbolic UID.
    _bind_dgs_elmsym_reference_frequencies(
        circuit=circuit,
        branch_devices=branch_devices,
        elmsym_reference_source_ids=effective_elmsym_reference_source_ids,
        logger=logger,
    )

    return report
