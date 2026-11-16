# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import math
import uuid

from typing import Dict, List, Optional, Sequence

from PySide6 import QtCore, QtGui

from VeraGrid.Gui.Icons.icon_associations import device_type_icons
from VeraGridEngine.enumerations import DeviceType, DynamicSimulationMode
from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.fmu_template import FmuTemplate
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.template_catalogue import (
    BasicBlockTemplateDescriptor,
    ExactMathematicalBlockDescriptor,
    build_exact_mathematical_block_descriptors,
)
from VeraGridEngine.Templates.template_catalogue import (
    ProceduralBlockParameterSpec,
    ProceduralBlockTemplateDescriptor,
)
from VeraGridEngine.Templates.template_catalogue import (
    InternationalStandardTemplateDescriptor,
    load_international_standard_template,
)
from VeraGridEngine.Templates.Rms import (
    get_international_model_builders,
)
from VeraGridEngine.Templates.Rms.synchronous_machines.genqec_exc_gov_sat_template_v2 import (
    get_complete_generator_template_rms,
    get_genqec_rms,
)
from VeraGridEngine.Templates.Emt.line.bergeron_line_emt_template import get_bergeron_line_emt_template
from VeraGridEngine.Templates.Emt.battery_energy_storage.bess_avm_emt_template import get_bess_avm_grid_following_emt_template
from VeraGridEngine.Templates.Emt.line.constant_parameter_line_emt_template import get_constant_parameter_line_emt_template
from VeraGridEngine.Templates.Emt.converters.converter_emt_template import get_emt_ideal_converter, get_full_pseudo_emt_converter
from VeraGridEngine.Templates.Emt.converters.converter_switched_emt_template import get_switched_emt_converter
from VeraGridEngine.Templates.Emt.dc_line.dc_line_emt_template import get_dc_line_with_power_input_emt_template
from VeraGridEngine.Templates.Emt.dc_line.dc_load_emt_template import get_dc_load_emt_template
from VeraGridEngine.Templates.Emt.synchronous_machines.generator_emt_type_template import get_complete_generator_template_emt
from VeraGridEngine.Templates.Emt.line.frequency_dependent_line_emt_template import get_frequency_dependent_line_emt_template
from VeraGridEngine.Templates.Emt.induction_machines.induction_motor_emt_template import get_induction_motor_double_cage_emt_template, get_induction_motor_single_cage_emt_template
from VeraGridEngine.Templates.Emt.load_characteristics.load_RLC_emt_template import get_shunt_c_emt_template, get_shunt_l_emt_template, get_shunt_r_emt_template
from VeraGridEngine.Templates.Emt.load_characteristics.load_exponential_emt_template import get_exponential_load_emt
from VeraGridEngine.Templates.Emt.load_characteristics.load_zip_emt_template import get_load_ZIP_emt_template
from VeraGridEngine.Templates.Emt.line.pi_line_emt_template import get_pi_line_emt_template
from VeraGridEngine.Templates.Emt.solar_pv_generation.pv_emt_template import get_pv_avm_grid_following_emt_template
from VeraGridEngine.Templates.Emt.synchronous_machines.sm1_emt_template import get_sm1_emt_template
from VeraGridEngine.Templates.Emt.converters.statcom_gfl_emt_template import get_statcom_gfl_emt_template
from VeraGridEngine.Templates.Emt.synchronous_machines.thevenin_equivalent_emt_generator_template import get_generator_thevenin_rl_emt_template_with_ref
from VeraGridEngine.Templates.Emt.transformers.transformer_emt_template import get_transformer_emt_template
from VeraGridEngine.Templates.Emt.converters.upc_gfl_emt_template import get_upc_gfl_emt_template
from VeraGridEngine.Templates.Emt.converters.upc_point_to_point_hvdc_emt_template import get_upc_point_to_point_hvdc_emt_template
from VeraGridEngine.Templates.Emt.converters.vsc_gfm_emt import get_gfm_emt_template
from VeraGridEngine.Templates.Emt.transformers.xfmr_emt_template import get_xfmr_emt_template
from VeraGridEngine.Templates.Rms.common.basic_devices import get_gfl_converter_rms
from VeraGridEngine.Templates.Rms.transformers.cantilever_transformer_rms_template import get_cantilever_transformer_rms_template
from VeraGridEngine.Templates.Rms.renewable_controls.colib_gfm_rms_templates import get_epri_gfm_rms_template, get_upc_gfm_rms_template
from VeraGridEngine.Templates.Rms.dc_line.dc_line_rms_template_v2 import build_dc_line_rms_v2
from VeraGridEngine.Templates.Rms.battery_energy_storage.esd1_rms_template import get_esd1_rms_template
from VeraGridEngine.Templates.Rms.synchronous_machines.flywheel_rms_template import get_flywheel_rms_template
from VeraGridEngine.Templates.Rms.synchronous_machines.gencls_rms_template import get_gencls_rms_template
from VeraGridEngine.Templates.Rms.synchronous_machines.genrow_rms_template import get_genrow_rms_template
from VeraGridEngine.Templates.Rms.converters.hvdc_vsc_gfl_rms_template_v2 import build_hvdc_vsc_gfl_rms
from VeraGridEngine.Templates.Rms.wind_generation.iec_type3_wind_turbine_rms_template import get_iec_type3_wind_turbine_rms_template
from VeraGridEngine.Templates.Rms.renewable_controls.l2ep_rms_gfl_template import get_l2ep_rms_gfl_template
from VeraGridEngine.Templates.Rms.line.line_rms_template import get_line_rms_template
from VeraGridEngine.Templates.Rms.load_characteristics.load_rms_template import get_load_rms_template
from VeraGridEngine.Templates.Rms.line.pi_equivalent_line_rms_template import get_pi_equivalent_line_rms_template
from VeraGridEngine.Templates.Rms.solar_pv_generation.pvd1_rms_template import get_pvd1_complete_rms_template, get_pvd1_dc_link_bess_rms_template, get_pvd1_dc_link_mppt_rms_template, get_pvd1_dc_mppt_rms_template, get_pvd1_rms_template
from VeraGridEngine.Templates.Rms.buses.shunt_template import get_shunt_template
from VeraGridEngine.Templates.Rms.dc_line.rte_average_vsc_hvdc_rms_template import get_rte_average_vsc_hvdc_rms_template
from VeraGridEngine.Templates.Rms.protection_relays.sfrm_ufls_rms_template import get_sfrm_ufls_rms_template
from VeraGridEngine.Templates.Rms.induction_machines.single_cage_induction_motor_rms_template import get_single_cage_induction_motor_rms_template
from VeraGridEngine.Templates.Rms.voltage_compensators.static_compensator_rms_template import get_static_compensator_rms_template
from VeraGridEngine.Templates.Rms.transformers.transformer_rms_template import get_transformer2w_rms
from VeraGridEngine.Templates.Rms.renewable_controls.upc_full_phasor_gfl_rms_template import get_upc_full_phasor_gfl_rms_template
from VeraGridEngine.Templates.Rms.renewable_controls.upc_phasor_gfl_rms_templates import (
    get_upc_phasor_i0_gfl_rms_template,
    get_upc_phasor_i1_gfl_rms_template,
    get_upc_phasor_pq1_gfl_rms_template,
)
from VeraGridEngine.Templates.Rms.common.voltage_source_template import VoltageSourceBuild
from VeraGridEngine.Templates.Rms.induction_machines.wecc_rotor_flux_induction_motor_rms_template import get_wecc_rotor_flux_induction_motor_rms_template
from VeraGridEngine.enumerations import (
    BlockType,
    DerivativeInactiveBehavior,
    DerivativeOrder,
    DerivativeScalingMode,
    DynamicDeviceTemplateType,
    ExactMathematicalBlockOperation,
    IntegratorBoundSource,
    IntegratorHoldMode,
    IntegratorResetMode,
    IntegratorSaturationMode,
    IntegratorScalingMode,
    InternationalStandardModel,
    ProceduralLogicType,
)
from VeraGridEngine.Templates.device_template_materialization import (
    create_block_of_type,
    create_default_template_builder,
)
from VeraGridEngine.Templates.template_catalogue import TemplateDefinition
from VeraGridEngine.Templates.template_catalogue import BASIC_BLOCK_CATALOGUE, get_template_catalogue_entries
from VeraGridEngine.Templates.device_template_materialization import build_dynamic_library_device_template
from VeraGridEngine.Utils.Symbolic.block import Block


def _new_uid() -> int:
    """
    Generate a fresh integer identifier.

    :return: Fresh uid.
    """
    return uuid.uuid4().int


class LibraryLeafSpec:
    """Describe one draggable leaf entry in the library tree."""

    __slots__ = ("label", "payload", "search_text")

    def __init__(self, label: str, payload: object, search_text: str = "") -> None:
        """Create an immutable-by-convention library leaf description.

        :param label: Text displayed in the library tree.
        :param payload: Typed object materialized when the leaf is dropped.
        :param search_text: Optional text used by the recursive filter.
        :return: None.
        """
        self.label: str = label
        self.payload: object = payload
        self.search_text: str = search_text


class IntegratorPresetDescriptor:
    """Describe one preconfigured view of the canonical integrator builder."""

    __slots__ = (
        "_block_type",
        "_scaling_mode",
        "_hold_mode",
        "_reset_mode",
        "_saturation_mode",
        "_bound_source",
        "_scale_bounds_by_gain",
        "_description",
    )

    def __init__(
            self,
            block_type: BlockType,
            scaling_mode: IntegratorScalingMode,
            hold_mode: IntegratorHoldMode,
            reset_mode: IntegratorResetMode,
            saturation_mode: IntegratorSaturationMode,
            bound_source: IntegratorBoundSource,
            scale_bounds_by_gain: bool,
            description: str,
    ) -> None:
        """Store the structural defaults represented by one Library leaf.

        Every preset materializes the same normal configurable integrator. The
        descriptor only avoids repetitive clicks for common initial layouts.

        :param block_type: Canonical integrator builder type.
        :param scaling_mode: Input scaling selected by the preset.
        :param hold_mode: External hold structure selected by the preset.
        :param reset_mode: Reset structure selected by the preset.
        :param saturation_mode: Output saturation selected by the preset.
        :param bound_source: Source of enabled saturation bounds.
        :param scale_bounds_by_gain: Whether one parameter scales the bounds.
        :param description: Human-facing explanation shown in the Library.
        :return: None.
        """
        self._block_type: BlockType = block_type
        self._scaling_mode: IntegratorScalingMode = scaling_mode
        self._hold_mode: IntegratorHoldMode = hold_mode
        self._reset_mode: IntegratorResetMode = reset_mode
        self._saturation_mode: IntegratorSaturationMode = saturation_mode
        self._bound_source: IntegratorBoundSource = bound_source
        self._scale_bounds_by_gain: bool = scale_bounds_by_gain
        self._description: str = description

    def get_block_type(self) -> BlockType:
        """Return the canonical builder type.

        :return: Integrator block type used to materialize the preset.
        """
        return self._block_type

    def get_scaling_mode(self) -> IntegratorScalingMode:
        """Return the preset input-scaling mode.

        :return: Configured integrator scaling mode.
        """
        return self._scaling_mode

    def get_hold_mode(self) -> IntegratorHoldMode:
        """Return the preset hold mode.

        :return: Configured integrator hold mode.
        """
        return self._hold_mode

    def get_reset_mode(self) -> IntegratorResetMode:
        """Return the preset reset mode.

        :return: Configured integrator reset mode.
        """
        return self._reset_mode

    def get_saturation_mode(self) -> IntegratorSaturationMode:
        """Return the preset output-saturation mode.

        :return: Configured integrator saturation mode.
        """
        return self._saturation_mode

    def get_bound_source(self) -> IntegratorBoundSource:
        """Return the source of enabled saturation bounds.

        :return: Configured bound source.
        """
        return self._bound_source

    def get_scale_bounds_by_gain(self) -> bool:
        """Return whether the preset scales its bounds by a gain.

        :return: ``True`` when enabled bounds share an extra gain parameter.
        """
        return self._scale_bounds_by_gain

    def get_description(self) -> str:
        """Return the Library explanation of the preset.

        :return: Human-facing preset description.
        """
        return self._description

    def apply_to_template_builder(self, builder: TemplateDefinition) -> None:
        """Apply this preset to a canonical integrator template builder.

        :param builder: Integrator builder whose initial structural values are
            replaced by this preset.
        :return: None.
        """
        builder.params_dict["scaling"].value = self._scaling_mode
        builder.params_dict["hold_input"].value = self._hold_mode
        builder.params_dict["reset"].value = self._reset_mode
        builder.params_dict["output_saturation"].value = self._saturation_mode
        builder.params_dict["bound_source"].value = self._bound_source
        builder.params_dict["scale_bounds_by_gain"].value = self._scale_bounds_by_gain


class DerivativePresetDescriptor:
    """Describe one preconfigured view of the canonical derivative builder."""

    __slots__ = (
        "_derivative_order",
        "_scaling_mode",
        "_inactive_behavior",
        "_description",
    )

    def __init__(
            self,
            derivative_order: DerivativeOrder,
            scaling_mode: DerivativeScalingMode,
            inactive_behavior: DerivativeInactiveBehavior,
            description: str,
    ) -> None:
        """Store the structural defaults represented by one Library leaf.

        :param derivative_order: First- or second-order filtered derivative.
        :param scaling_mode: Numerator scaling selected by the preset.
        :param inactive_behavior: Response to a non-positive denominator time.
        :param description: Human-facing explanation shown in the Library.
        :return: None.
        """
        self._derivative_order: DerivativeOrder = derivative_order
        self._scaling_mode: DerivativeScalingMode = scaling_mode
        self._inactive_behavior: DerivativeInactiveBehavior = inactive_behavior
        self._description: str = description

    def get_block_type(self) -> BlockType:
        """Return the canonical builder type.

        :return: Derivative block type used to materialize the preset.
        """
        return BlockType.DERIVATIVE

    def get_derivative_order(self) -> DerivativeOrder:
        """Return the preset derivative order.

        :return: Configured first- or second-order selection.
        """
        return self._derivative_order

    def get_scaling_mode(self) -> DerivativeScalingMode:
        """Return the preset numerator-scaling mode.

        :return: Configured derivative scaling mode.
        """
        return self._scaling_mode

    def get_inactive_behavior(self) -> DerivativeInactiveBehavior:
        """Return the preset non-positive-time behavior.

        :return: Configured derivative inactive behavior.
        """
        return self._inactive_behavior

    def get_description(self) -> str:
        """Return the Library explanation of the preset.

        :return: Human-facing preset description.
        """
        return self._description

    def apply_to_template_builder(self, builder: TemplateDefinition) -> None:
        """Apply this preset to a canonical derivative template builder.

        :param builder: Derivative builder receiving the initial selections.
        :return: None.
        """
        builder.params_dict["order"].value = self._derivative_order
        builder.params_dict["scaling"].value = self._scaling_mode
        builder.params_dict["non_positive_time"].value = self._inactive_behavior


def build_integrator_preset_descriptors() -> tuple[tuple[str, IntegratorPresetDescriptor], ...]:
    """Build the curated Library views of the configurable integrator.

    The set intentionally covers independent common structures instead of the
    full Cartesian product. Users can combine every option later in General
    Structure without multiplying Library entries indefinitely.

    :return: Ordered label and preset-descriptor pairs.
    """
    default_bound_source: IntegratorBoundSource = IntegratorBoundSource.PARAMETER
    presets: tuple[tuple[str, IntegratorPresetDescriptor], ...] = (
        ("Integrator", IntegratorPresetDescriptor(
            block_type=BlockType.INTEGRATOR,
            scaling_mode=IntegratorScalingMode.UNIT,
            hold_mode=IntegratorHoldMode.NONE,
            reset_mode=IntegratorResetMode.NONE,
            saturation_mode=IntegratorSaturationMode.NONE,
            bound_source=default_bound_source,
            scale_bounds_by_gain=False,
            description="Integrates the input as y = integral(u dt).",
        )),
        ("Gain integrator (K/s)", IntegratorPresetDescriptor(
            block_type=BlockType.INTEGRATOR,
            scaling_mode=IntegratorScalingMode.GAIN,
            hold_mode=IntegratorHoldMode.NONE,
            reset_mode=IntegratorResetMode.NONE,
            saturation_mode=IntegratorSaturationMode.NONE,
            bound_source=default_bound_source,
            scale_bounds_by_gain=False,
            description="Integrates the input with a configurable gain K: dy/dt = K u.",
        )),
        ("Time-constant integrator (1/(sT))", IntegratorPresetDescriptor(
            block_type=BlockType.INTEGRATOR,
            scaling_mode=IntegratorScalingMode.TIME_CONSTANT,
            hold_mode=IntegratorHoldMode.NONE,
            reset_mode=IntegratorResetMode.NONE,
            saturation_mode=IntegratorSaturationMode.NONE,
            bound_source=default_bound_source,
            scale_bounds_by_gain=False,
            description="Integrates the input through a configurable time constant T: dy/dt = u/T.",
        )),
        ("Upper-limited integrator", IntegratorPresetDescriptor(
            block_type=BlockType.INTEGRATOR,
            scaling_mode=IntegratorScalingMode.UNIT,
            hold_mode=IntegratorHoldMode.NONE,
            reset_mode=IntegratorResetMode.NONE,
            saturation_mode=IntegratorSaturationMode.UPPER,
            bound_source=default_bound_source,
            scale_bounds_by_gain=False,
            description="Integrates the input and clamps the exposed output at a configurable upper limit.",
        )),
        ("Lower-limited integrator", IntegratorPresetDescriptor(
            block_type=BlockType.INTEGRATOR,
            scaling_mode=IntegratorScalingMode.UNIT,
            hold_mode=IntegratorHoldMode.NONE,
            reset_mode=IntegratorResetMode.NONE,
            saturation_mode=IntegratorSaturationMode.LOWER,
            bound_source=default_bound_source,
            scale_bounds_by_gain=False,
            description="Integrates the input and clamps the exposed output at a configurable lower limit.",
        )),
        ("Limited integrator", IntegratorPresetDescriptor(
            block_type=BlockType.INTEGRATOR,
            scaling_mode=IntegratorScalingMode.UNIT,
            hold_mode=IntegratorHoldMode.NONE,
            reset_mode=IntegratorResetMode.NONE,
            saturation_mode=IntegratorSaturationMode.BOTH,
            bound_source=default_bound_source,
            scale_bounds_by_gain=False,
            description=(
                "Integrates the input and clamps the exposed output between configurable lower and upper limits."
            ),
        )),
        ("Holdable integrator", IntegratorPresetDescriptor(
            block_type=BlockType.INTEGRATOR,
            scaling_mode=IntegratorScalingMode.UNIT,
            hold_mode=IntegratorHoldMode.SIGNAL,
            reset_mode=IntegratorResetMode.NONE,
            saturation_mode=IntegratorSaturationMode.NONE,
            bound_source=default_bound_source,
            scale_bounds_by_gain=False,
            description="Integrates the input and freezes its state while the external hold signal is active.",
        )),
        ("Resettable integrator", IntegratorPresetDescriptor(
            block_type=BlockType.INTEGRATOR,
            scaling_mode=IntegratorScalingMode.UNIT,
            hold_mode=IntegratorHoldMode.NONE,
            reset_mode=IntegratorResetMode.INITIAL_STATE,
            saturation_mode=IntegratorSaturationMode.NONE,
            bound_source=default_bound_source,
            scale_bounds_by_gain=False,
            description="Integrates the input and resets the state to its initialized value on a rising reset edge.",
        )),
        ("Integrator with startup freeze", IntegratorPresetDescriptor(
            block_type=BlockType.STARTUP_FREEZE_INTEGRATOR,
            scaling_mode=IntegratorScalingMode.UNIT,
            hold_mode=IntegratorHoldMode.NONE,
            reset_mode=IntegratorResetMode.NONE,
            saturation_mode=IntegratorSaturationMode.NONE,
            bound_source=default_bound_source,
            scale_bounds_by_gain=False,
            description=(
                "Keeps the state frozen for a configurable interval after startup and then integrates normally."
            ),
        )),
    )
    return presets


def build_derivative_preset_descriptors() -> tuple[tuple[str, DerivativePresetDescriptor], ...]:
    """Build the curated Library views of the configurable derivative.

    The presets cover common transfer functions without exposing the full
    Cartesian product. Every created block remains completely configurable in
    General Structure.

    :return: Ordered label and preset-descriptor pairs.
    """
    strict_behavior: DerivativeInactiveBehavior = DerivativeInactiveBehavior.STRICT
    presets: tuple[tuple[str, DerivativePresetDescriptor], ...] = (
        ("Filtered derivative s/(1+Ts)", DerivativePresetDescriptor(
            derivative_order=DerivativeOrder.FIRST,
            scaling_mode=DerivativeScalingMode.UNIT,
            inactive_behavior=strict_behavior,
            description="Applies the first-order filtered derivative s/(1 + T s).",
        )),
        ("Gain filtered derivative", DerivativePresetDescriptor(
            derivative_order=DerivativeOrder.FIRST,
            scaling_mode=DerivativeScalingMode.GAIN,
            inactive_behavior=strict_behavior,
            description="Applies the gain-scaled filtered derivative K s/(1 + T s).",
        )),
        ("Washout", DerivativePresetDescriptor(
            derivative_order=DerivativeOrder.FIRST,
            scaling_mode=DerivativeScalingMode.TIME_CONSTANT,
            inactive_behavior=strict_behavior,
            description="Applies the washout transfer function T s/(1 + T s).",
        )),
        ("Gain washout", DerivativePresetDescriptor(
            derivative_order=DerivativeOrder.FIRST,
            scaling_mode=DerivativeScalingMode.GAIN_TIME_CONSTANT,
            inactive_behavior=strict_behavior,
            description="Applies the gain-scaled washout K T s/(1 + T s).",
        )),
        ("Bypassable washout", DerivativePresetDescriptor(
            derivative_order=DerivativeOrder.FIRST,
            scaling_mode=DerivativeScalingMode.TIME_CONSTANT,
            inactive_behavior=DerivativeInactiveBehavior.BYPASS_INPUT,
            description="Applies T s/(1 + T s), or passes the input through when T is non-positive.",
        )),
        ("Second-order filtered derivative", DerivativePresetDescriptor(
            derivative_order=DerivativeOrder.SECOND,
            scaling_mode=DerivativeScalingMode.GAIN,
            inactive_behavior=strict_behavior,
            description="Applies the second-order filtered derivative K s²/(1 + T s)².",
        )),
    )
    return presets


class LibraryDeviceTemplateSpec:
    """Describe one complete reusable device model owned by the Library."""

    __slots__ = (
        "label",
        "source",
        "mode",
        "device_type",
        "category_path",
        "description",
        "search_text",
        "compatible_device_types",
    )

    def __init__(
            self,
            label: str,
            source: DynamicDeviceTemplateType | BlockType | InternationalStandardTemplateDescriptor,
            mode: DynamicSimulationMode,
            device_type: DeviceType,
            category_path: tuple[str, ...],
            description: str,
            search_text: str = "",
            compatible_device_types: tuple[DeviceType, ...] | None = None,
    ) -> None:
        """Store one canonical device-template registration.

        :param label: Human-facing Library and catalogue label.
        :param source: Typed materialization identifier.
        :param mode: Dynamic simulation domain.
        :param device_type: Physical device type accepting the template.
        :param category_path: Path below the ``Devices`` branch.
        :param description: Human-facing explanation of the model behavior.
        :param search_text: Optional additional filter terms.
        :param compatible_device_types: Physical device types that may use the
            same registered drawing without duplicating the Library entry.
        :return: None.
        """
        self.label: str = label
        self.source: DynamicDeviceTemplateType | BlockType | InternationalStandardTemplateDescriptor = source
        self.mode: DynamicSimulationMode = mode
        self.device_type: DeviceType = device_type
        self.category_path: tuple[str, ...] = category_path
        self.description: str = description
        self.search_text: str = search_text
        if compatible_device_types is None:
            self.compatible_device_types: tuple[DeviceType, ...] = (device_type,)
        else:
            self.compatible_device_types = compatible_device_types

    def is_compatible_with(self, device_type: DeviceType) -> bool:
        """Check whether this drawing can model one physical device type.

        :param device_type: Physical editor host under consideration.
        :return: ``True`` when the registered drawing is compatible.
        """
        return device_type in self.compatible_device_types


class DynamicsLibraryTreeModel(QtGui.QStandardItemModel):
    __slots__ = ("_block_role", "_mime_type", "_drag_token_role", "_drag_payloads")

    def __init__(self, block_role: int, mime_type: str) -> None:
        """Create a source model that owns drag payloads explicitly.

        :param block_role: Qt item-data role containing the typed payload.
        :param mime_type: MIME type used for internal drag operations.
        :return: None.
        """
        super().__init__()
        self._block_role: int = block_role
        self._mime_type: str = mime_type
        self._drag_token_role: int = block_role + 1
        self._drag_payloads: Dict[str, object] = dict()

        self.setHorizontalHeaderLabels(list(("Name", "Description")))

    def register_drag_payload(self, item: QtGui.QStandardItem, payload: object) -> None:
        """Register one payload and expose its opaque drag token on an item.

        :param item: Tree item that starts the drag.
        :param payload: Typed editor object represented by the item.
        :return: None.
        """
        token: str = str(_new_uid())
        self._drag_payloads[token] = payload
        item.setData(payload, self._block_role)
        item.setData(token, self._drag_token_role)

    def get_drag_payload(self, token: str) -> object | None:
        """Return the payload associated with one drag token.

        :param token: Opaque token serialized in the MIME data.
        :return: Registered payload or ``None`` when the token is unknown.
        """
        return self._drag_payloads.get(token, None)

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlag:
        """Return drag-enabled flags only for supported leaf payloads.

        :param index: Source-model index being queried by Qt.
        :return: Flags appropriate for a category or draggable leaf.
        """
        if index.isValid():
            if index.column() != 0:
                return QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable
            else:
                pass
            item: QtGui.QStandardItem | None = self.itemFromIndex(index)
            if item is not None:
                item_data: object = item.data(self._block_role)
                if is_supported_library_payload(item_data):
                    return (QtCore.Qt.ItemFlag.ItemIsEnabled
                            | QtCore.Qt.ItemFlag.ItemIsSelectable
                            | QtCore.Qt.ItemFlag.ItemIsDragEnabled)
                else:
                    return QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable
            else:
                return QtCore.Qt.ItemFlag.ItemIsEnabled
        else:
            return QtCore.Qt.ItemFlag.ItemIsEnabled

    def mimeTypes(self) -> List[str]:
        """Return the MIME types produced by this model.

        :return: Single internal dynamic-editor MIME type.
        """
        return list((self._mime_type,))

    def supportedDragActions(self) -> QtCore.Qt.DropAction:
        """Return the copy action used for library drags.

        :return: Qt copy action.
        """
        return QtCore.Qt.DropAction.CopyAction

    def mimeData(self, indexes: List[QtCore.QModelIndex]) -> QtCore.QMimeData:
        """Serialize the first supported selected leaf as an opaque token.

        :param indexes: Selected source-model indexes supplied by Qt.
        :return: MIME data containing a registered payload token when possible.
        """
        mime_data: QtCore.QMimeData = QtCore.QMimeData()

        index: QtCore.QModelIndex
        for index in indexes:
            if index.isValid():
                source_index: QtCore.QModelIndex = index.siblingAtColumn(0)
                item: QtGui.QStandardItem | None = self.itemFromIndex(source_index)
                if item is not None:
                    item_token: object = item.data(self._drag_token_role)
                    item_data: object = item.data(self._block_role)
                    if isinstance(item_token, str) and is_supported_library_payload(item_data):
                        mime_data.setData(self._mime_type, QtCore.QByteArray(item_token.encode("utf-8")))
                        return mime_data
                    else:
                        pass
                else:
                    pass
            else:
                pass

        return mime_data


class LibraryTreeFilterProxyModel(QtCore.QSortFilterProxyModel):
    __slots__ = ("_search_role",)

    def __init__(self, search_role: int, parent: QtCore.QObject | None = None) -> None:
        """Create a recursive proxy filtering one dedicated search role.

        :param search_role: Source-model role containing normalized search text.
        :param parent: Optional Qt owner.
        :return: None.
        """
        super().__init__(parent)
        self._search_role: int = search_role
        self.setRecursiveFilteringEnabled(True)
        self.setAutoAcceptChildRows(True)
        self.setFilterCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.setFilterRole(search_role)
        self.setFilterKeyColumn(0)

    def mimeData(self, indexes: List[QtCore.QModelIndex]) -> QtCore.QMimeData:
        """Map proxy indexes to the source model before serializing a drag.

        :param indexes: Selected proxy-model indexes.
        :return: MIME data produced by the typed source model.
        """
        source_model: QtCore.QAbstractItemModel | None = self.sourceModel()
        if isinstance(source_model, DynamicsLibraryTreeModel):
            source_indexes: List[QtCore.QModelIndex] = [self.mapToSource(index) for index in indexes if index.isValid()]
            return source_model.mimeData(source_indexes)
        else:
            return super().mimeData(indexes)

    def supportedDragActions(self) -> QtCore.Qt.DropAction:
        """Delegate supported drag actions to the source model.

        :return: Drag actions supported by the active source model.
        """
        source_model: QtCore.QAbstractItemModel | None = self.sourceModel()
        if isinstance(source_model, DynamicsLibraryTreeModel):
            return source_model.supportedDragActions()
        else:
            return super().supportedDragActions()


class DynamicEditorLibrary:
    """Build the mode- and device-specific dynamic block library."""

    __slots__ = (
        "api_object",
        "mode",
        "templates_list",
        "block_role",
        "mime_type",
        "LIBRARY_SEARCH_TEXT_ROLE",
        "tree_structure",
        "library_model",
    )

    def __init__(self,
                 api_object: ALL_DEV_TYPES,
                 mode: DynamicSimulationMode = DynamicSimulationMode.RMS,
                 templates_list: Optional[List[RmsModelTemplate | EmtModelTemplate | FmuTemplate]] = None) -> None:
        """Create a library definition for one device and simulation mode.

        :param api_object: Static device associated with the editor.
        :param mode: RMS or EMT editor mode.
        :param templates_list: Optional catalogue templates exposed as leaves.
        :return: None.
        """

        self.api_object: ALL_DEV_TYPES = api_object
        self.mode: DynamicSimulationMode = mode
        self.templates_list: Optional[List[RmsModelTemplate | EmtModelTemplate | FmuTemplate]] = templates_list
        self.block_role: int = int(QtCore.Qt.ItemDataRole.UserRole) + 300
        self.mime_type: str = "application/x-veragrid-dynamics-block"
        self.LIBRARY_SEARCH_TEXT_ROLE: int = int(QtCore.Qt.ItemDataRole.UserRole) + 502

        # Build one projection of the canonical mode library for the active
        # physical device. The catalogue uses the same builders without this
        # device filter, so availability cannot drift between the two views.
        active_device_type: DeviceType = (
            self.api_object.device_type if self.api_object is not None else DeviceType.NoDevice
        )
        self.tree_structure: Dict[str, object] = build_dynamic_library_structure(
            mode=mode,
            device_type=active_device_type,
        )

        self.tree_structure["Tools"] = list((
            LibraryLeafSpec("Signal pair", BlockType.FROM_GOTO),
            LibraryLeafSpec("Measurements", BlockType.INPUT_CONN),
            LibraryLeafSpec("Generic device", BlockType.GENERIC),
        ))

        if mode == DynamicSimulationMode.RMS:
            self.tree_structure["Tools"].append(LibraryLeafSpec("Interconnection", BlockType.INTERCONNECTION))
        else:
            pass

        if self.templates_list:
            self.tree_structure["Templates"] = dict((("Available", [LibraryLeafSpec(template.name, template, template.name) for template in
                              self.templates_list]),))
        else:
            pass

        # build and add library model
        self.library_model: DynamicsLibraryTreeModel = self.build_library_tree_model()

    def build_library_tree_model(self) -> DynamicsLibraryTreeModel:
        """
        Build the source tree-view model for dynamic library.

        :return: Populated source model owned by the editor library.
        """

        model: DynamicsLibraryTreeModel = DynamicsLibraryTreeModel(self.block_role, self.mime_type)
        root_item: QtGui.QStandardItem = model.invisibleRootItem()

        category: str
        branch_data: object
        for category, branch_data in self.tree_structure.items():
            self._append_library_branch(model, root_item, category, branch_data)

        return model

    def _append_library_branch(self,
                               model: DynamicsLibraryTreeModel,
                               parent_item: QtGui.QStandardItem,
                               branch_label: str,
                               branch_data: object,
                               path_tokens: tuple[str, ...] = tuple()) -> None:
        """
        Append one recursive library branch into the tree model.

        :param model: Source model receiving the branch.
        :param parent_item: Parent item under which the branch is inserted.
        :param branch_label: Visible branch label.
        :param branch_data: Validated nested branch dictionary or leaf list.
        :param path_tokens: Ancestor labels used to build searchable text.
        :return: None.
        """

        branch_item: QtGui.QStandardItem = QtGui.QStandardItem(branch_label)
        description_item: QtGui.QStandardItem = QtGui.QStandardItem("")
        branch_item.setEditable(False)
        description_item.setEditable(False)
        branch_item.setData(" ".join((*path_tokens, branch_label)).strip(), self.LIBRARY_SEARCH_TEXT_ROLE)
        set_library_branch_icon(item=branch_item, branch_label=branch_label)
        parent_item.appendRow(list((branch_item, description_item)))

        if isinstance(branch_data, dict):
            child_label: str
            child_data: object
            for child_label, child_data in branch_data.items():
                self._append_library_branch(model, branch_item, child_label, child_data, (*path_tokens, branch_label))
        else:
            if isinstance(branch_data, list):
                leaf: LibraryLeafSpec
                for leaf in sorted(branch_data, key=_library_leaf_label_sort_key):
                    item: QtGui.QStandardItem = QtGui.QStandardItem(leaf.label)
                    leaf_description: str = build_library_item_description(payload=leaf.payload)
                    leaf_description_item: QtGui.QStandardItem = QtGui.QStandardItem(leaf_description)
                    item.setEditable(False)
                    leaf_description_item.setEditable(False)
                    if len(leaf.search_text) > 0:
                        search_text: str = f"{leaf.search_text} {leaf_description}".strip()
                    else:
                        search_text = f"{leaf.label} {leaf_description}".strip()
                    item.setData(search_text, self.LIBRARY_SEARCH_TEXT_ROLE)
                    item.setToolTip(leaf_description)
                    leaf_description_item.setToolTip(leaf_description)
                    if isinstance(leaf.payload, ProceduralBlockTemplateDescriptor):
                        procedural_tooltip: str = (
                            f"{leaf.payload.display_label} — {leaf.payload.logic_tpe.value}. "
                            "Drag onto the canvas or double-click to insert."
                        )
                        if leaf.payload.requires_configuration:
                            procedural_tooltip += " Complete the external target identifiers in Python code."
                        else:
                            pass
                        item.setToolTip(procedural_tooltip)
                    elif isinstance(leaf.payload, InternationalStandardTemplateDescriptor):
                        item.setToolTip(
                            f"{leaf.payload.display_label} — {leaf_description}. "
                            "Drag onto the canvas or double-click to insert."
                        )
                    else:
                        pass
                    set_library_item_icon(item, leaf.payload)
                    model.register_drag_payload(item, leaf.payload)
                    branch_item.appendRow(list((item, leaf_description_item)))
            else:
                raise TypeError(f"Unsupported library branch data type {type(branch_data)!r}")



def get_generator_technology_category(label: str) -> tuple[str, ...]:
    """Classify one generator or source model by its known technology.

    :param label: Registered user-facing device-model label.
    :return: Technology category path for the shared Devices branch.
    """
    label_text: str = label.lower()
    if "pvd" in label_text or "pv" in label_text:
        return ("PV generators",)
    elif "wind" in label_text or "turbine" in label_text:
        return ("Wind turbines",)
    elif "source" in label_text:
        return ("Sources",)
    else:
        return ("Synchronous and other generators",)


def _international_standard_label(model: InternationalStandardModel) -> str:
    """Return the established visible label for one standard model.

    :param model: International-standard model identifier.
    :return: Human-facing Library label.
    """
    if model == InternationalStandardModel.PSS1AOMEGA:
        label: str = "PSS1A (omega input)"
    elif model == InternationalStandardModel.PSS1APGEN:
        label = "PSS1A (Pgen input)"
    elif model == InternationalStandardModel.IEEEVC_1981:
        label = "IEEEVC 1981"
    elif model == InternationalStandardModel.PSSKUNDUR:
        label = "PSS Kundur"
    elif model == InternationalStandardModel.REGCBCS:
        label = "REGCbCS"
    elif model == InternationalStandardModel.WT4ACURRENTSOURCE:
        label = "WT4A current source"
    elif model == InternationalStandardModel.WT4ACURRENTSOURCE2020:
        label = "WT4A current source 2020"
    elif model == InternationalStandardModel.WT4BCURRENTSOURCE:
        label = "WT4B current source"
    elif model == InternationalStandardModel.WT4BCURRENTSOURCE2020:
        label = "WT4B current source 2020"
    elif model == InternationalStandardModel.WT4INJECTOR:
        label = "WT4 injector"
    elif model == InternationalStandardModel.WTG4ACURRENTSOURCE:
        label = "WTG4A current source"
    elif model == InternationalStandardModel.WTG4BCURRENTSOURCE:
        label = "WTG4B current source"
    elif model == InternationalStandardModel.WPP4BCURRENTSOURCE2020:
        label = "WPP4B current source 2020"
    elif model == InternationalStandardModel.PVCURRENTSOURCEBNOPLANTCONTROL:
        label = "PV current source B (no plant control)"
    elif model == InternationalStandardModel.PVVOLTAGESOURCEANOPLANTCONTROL:
        label = "PV voltage source A (no plant control)"
    elif model == InternationalStandardModel.PVVOLTAGESOURCEBNOPLANTCONTROL:
        label = "PV voltage source B (no plant control)"
    elif model == InternationalStandardModel.BESSCBCURRENTSOURCENOPLANTCONTROL:
        label = "BESSCB current source (no plant control)"
    else:
        label = model.name
    return label


def build_international_standard_description(model: InternationalStandardModel) -> str:
    """Return the functional description of an international-standard model.

    The descriptor registry is intentionally lightweight and does not build
    every symbolic template merely to read its comment. This function mirrors
    the model-level meaning needed by the Library while keeping tree creation
    fast and deterministic.

    :param model: International-standard model identifier.
    :return: Functional description shown in the Library and its tooltips.
    """
    label: str = _international_standard_label(model=model)
    if model == InternationalStandardModel.GENSAL:
        description: str = "GENSAL salient-pole synchronous-machine RMS model"
    elif model == InternationalStandardModel.GENROU:
        description = "GENROU round-rotor synchronous-machine RMS model"
    elif model == InternationalStandardModel.GENTRA:
        description = "Field-transient salient-pole synchronous machine without damper windings"
    elif model == InternationalStandardModel.GENSAE:
        description = "Salient-pole synchronous machine with five states and two-axis power-law saturation"
    elif model == InternationalStandardModel.GENROE:
        description = "Round-rotor synchronous machine with power-law magnetic saturation"
    elif model == InternationalStandardModel.CIMTR1:
        description = "CIMTR1 induction-generator RMS model"
    elif model == InternationalStandardModel.CIMTR2:
        description = "CIMTR2 induction-motor RMS model with speed-dependent torque"
    elif model == InternationalStandardModel.CIMTR3:
        description = "CIMTR3 induction-generator RMS model with rotor-angle deviation"
    elif model == InternationalStandardModel.CIMTR4:
        description = "CIMTR4 induction-motor RMS model with rotor-angle deviation and speed-dependent torque"
    elif model == InternationalStandardModel.CIM5:
        description = "PSS/E CIM5 saturated induction-motor load RMS model"
    elif model == InternationalStandardModel.CIM6:
        description = "PSS/E CIM6 induction-motor load RMS model with polynomial torque"
    elif model == InternationalStandardModel.CIMW:
        description = "PSS/E CIMW induction-motor load RMS model with initialized-speed torque"
    elif model == InternationalStandardModel.GGOV1D:
        description = "Tracked fuel-valve governor with asymmetric speed deadband and turbine dynamics"
    elif model == InternationalStandardModel.GASTD:
        description = "GASTD turbine-governor with asymmetric speed pickup and explicit turbine dynamics"
    elif model == InternationalStandardModel.IEESGOD:
        description = "IEESGOD turbine-governor with asymmetric speed pickup and explicit turbine dynamics"
    elif model == InternationalStandardModel.HYGOV2:
        description = 'Cascaded PI hydraulic governor with gate motion limits and inverse-response water dynamics.'
    elif model == InternationalStandardModel.PIDGOV:
        description = 'Hydraulic PID regulation with selectable droop feedback and calibrated gate/power characteristic.'
    elif model == InternationalStandardModel.PIDGOVD:
        description = 'Deadbanded hydraulic PID regulation with raw-speed mechanical damping.'
    elif model == InternationalStandardModel.HYGOV2D:
        description = 'Cascaded PI hydraulic governor with asymmetric excess-speed deadband.'
    elif model == InternationalStandardModel.HYGOVD:
        description = "HYGOVD turbine-governor with asymmetric speed pickup and explicit turbine dynamics"
    elif model == InternationalStandardModel.TGOV1D:
        description = "TGOV1D turbine-governor with asymmetric speed pickup and explicit turbine dynamics"
    elif model == InternationalStandardModel.GGOV1:
        description = "GGOV1 general-purpose turbine-governor model for synchronous generation"
    elif model == InternationalStandardModel.BBGOV1:
        description = "Brown-Boveri governor with step-gradient limiter and three steam turbine paths"
    elif model == InternationalStandardModel.IEEEG3:
        description = "Hydraulic governor with pilot-valve dynamics, transient droop and inverse water-column response"
    elif model == InternationalStandardModel.IEEEG3D:
        description = "Hydraulic governor with asymmetric speed deadband, pilot-valve dynamics and inverse water-column response"
    elif model == InternationalStandardModel.GAST:
        description = "Gas-turbine speed governor with fuel-valve dynamics and exhaust-temperature limiting"
    elif model == InternationalStandardModel.GAST2A:
        description = "Detailed gas-turbine governor with fuel-system, exhaust-temperature, and turbine dynamics"
    elif model == InternationalStandardModel.IEESGO:
        description = "Steam-turbine speed governor with chest, reheat and crossover power stages"
    elif model in tuple((InternationalStandardModel.GOVHYDRO4, InternationalStandardModel.HYGOV)):
        description = f"{label} hydro-turbine governor model for synchronous generation"
    elif model in tuple((InternationalStandardModel.GOVSTEAM1, InternationalStandardModel.GOVSTEAMEU)):
        description = f"{label} steam-turbine governor model for synchronous generation"
    elif model in (InternationalStandardModel.DEGOV, InternationalStandardModel.DEGOV1, InternationalStandardModel.DEGOV1D):
        description = 'Electronic engine-speed governor with bounded fuel throttle and combustion transport delay'
    elif model == InternationalStandardModel.IVOGO:
        description = 'Three-stage rational speed governor with balanced integral load memories and separate power/torque outputs.'
    elif model == InternationalStandardModel.LCFB1:
        description = "Outer measured-power control with frequency bias and bounded governor-reference correction"
    elif model == InternationalStandardModel.IEEEG1D:
        description = "Steam governor with asymmetric deadband, valve travel limits and four turbine stages"
    elif model in tuple((InternationalStandardModel.IEEEG1, InternationalStandardModel.IEEEG2)):
        description = f"{label} IEEE turbine-governor model for synchronous generation"
    elif model == InternationalStandardModel.TGOV2:
        description = "Steam turbine governor with reheat stages, damping and TI-relative fast valving"
    elif model == InternationalStandardModel.TGOV4:
        description = "Steam turbine governor with multivalve steam stages and boiler pressure dynamics"
    elif model in tuple((InternationalStandardModel.TGOV1, InternationalStandardModel.TGOV3)):
        description = f"{label} turbine-governor model for synchronous generation"
    elif model == InternationalStandardModel.IEEEVC_1981:
        description = "IEEEVC 1981 terminal-voltage compensation model for a synchronous generator"
    elif model == InternationalStandardModel.COMP:
        description = "Voltage sensing behind a signed reactive impedance using rectangular terminal phasors"
    elif model == InternationalStandardModel.COMPCC:
        description = "Cross-compound voltage sensing with shared and individual two-machine current corrections"
    elif model == InternationalStandardModel.CCOMP4A:
        description = "Four-unit reactive-current sharing with a bounded correction to terminal voltage"
    elif model == InternationalStandardModel.CPAAUT:
        description = "Bus-frequency washout and lag producing a bounded auxiliary power signal in MW"
    elif model == InternationalStandardModel.WT12T1:
        description = "Type 1/2 wind turbine one- or two-mass shaft driven by mechanical and electrical torque"
    elif model == InternationalStandardModel.REMCMP:
        description = "Remote bus voltage sensing without an artificial measurement delay"
    elif model == InternationalStandardModel.VRKUNDUR:
        description = "Kundur automatic voltage regulator model for a synchronous generator"
    elif model == InternationalStandardModel.AC11C:
        description = "IEEE AC11C filtered-PI excitation control with dual rectifier supplies and boost logic"
    elif model == InternationalStandardModel.AC9C:
        description = "IEEE AC9C PID excitation control with limiter routing, dual source and chopper selection"
    elif model in tuple((
            InternationalStandardModel.AC1A,
            InternationalStandardModel.AC6A,
            InternationalStandardModel.AC6C,
            InternationalStandardModel.AC6C2,
            InternationalStandardModel.AC7B,
            InternationalStandardModel.AC7C,
            InternationalStandardModel.AC8C,
            InternationalStandardModel.DC1A,
            InternationalStandardModel.DC1C,
            InternationalStandardModel.ESDC2A,
            InternationalStandardModel.EXAC1,
            InternationalStandardModel.IEEET1,
            InternationalStandardModel.IEEEX2,
            InternationalStandardModel.IEEX2A,
            InternationalStandardModel.SCRX,
            InternationalStandardModel.SEXS,
            InternationalStandardModel.ST1A,
            InternationalStandardModel.ST5C,
            InternationalStandardModel.ST6B,
            InternationalStandardModel.ST6C,
            InternationalStandardModel.ST8C,
            InternationalStandardModel.ST9C,
            InternationalStandardModel.ST10C,
    )):
        description = f"{label} automatic voltage regulator and excitation-system model for a synchronous generator"
    elif model == InternationalStandardModel.IEEL:
        description = "IEEL excitation limiter model for a synchronous generator"
    elif model == InternationalStandardModel.MAXEX2:
        description = "MAXEX2 maximum-excitation limiter model for a synchronous generator"
    elif model in tuple((InternationalStandardModel.OEL2C, InternationalStandardModel.OEL3C,
                         InternationalStandardModel.OEL4C, InternationalStandardModel.OEL5C)):
        description = f"{label} over-excitation limiter model protecting a synchronous generator field winding"
    elif model in tuple((InternationalStandardModel.SCL1C, InternationalStandardModel.SCL2C)):
        description = f"{label} stator-current limiter model for a synchronous generator"
    elif model in tuple((InternationalStandardModel.UEL1, InternationalStandardModel.UEL2C)):
        description = f"{label} under-excitation limiter model for a synchronous generator"
    elif model == InternationalStandardModel.PSS1AOMEGA:
        description = "PSS1A power-system stabilizer using rotor-speed deviation as its input"
    elif model == InternationalStandardModel.PSS1APGEN:
        description = "PSS1A power-system stabilizer using generator active power as its input"
    elif model == InternationalStandardModel.PSS2C:
        description = 'Continuously enabled four-phase dual-input ramp tracking with limited measurements.'
    elif model == InternationalStandardModel.PSS3B:
        description = 'Dual-input damping with optional washouts and two quadratic phase compensators.'
    elif model in tuple((InternationalStandardModel.PSS2A, InternationalStandardModel.PSS2B,
                         InternationalStandardModel.PSS2C)):
        description = f"{label} dual-input power-system stabilizer for damping electromechanical oscillations"
    elif model in tuple((InternationalStandardModel.PSS3B, InternationalStandardModel.PSS3C,
                         InternationalStandardModel.PSS6C)):
        description = f"{label} power-system stabilizer for damping generator electromechanical oscillations"
    elif model == InternationalStandardModel.PSSKUNDUR:
        description = "Kundur power-system stabilizer for damping generator electromechanical oscillations"
    elif model == InternationalStandardModel.STAB1:
        description = "Speed-sensitive stabilizer with washout and two phase-compensation stages"
    elif model == InternationalStandardModel.STAB2A:
        description = "Electrical-power stabilizer with triple washout and parallel-path filtering"
    elif model == InternationalStandardModel.STAB3:
        description = "Reference-subtracted power stabilizer with filtered derivative feedback"
    elif model == InternationalStandardModel.STAB4:
        description = "Power stabilizer with derivative reset, phase compensation and asymmetric voltage limits"
    elif model == InternationalStandardModel.IVOST:
        description = 'Electrical-power damping through three rational filters with distinct tracking and external output limits.'
    elif model == InternationalStandardModel.STABNI:
        description = "Power stabilizer with double reset and fourth-order shaping"
    elif model == InternationalStandardModel.IEEEST:
        description = "Single-input stabilizer with polynomial filtering and terminal-voltage supervision"
    elif model == InternationalStandardModel.PSS1A:
        description = "IEEE PSS1A single-input stabilizer using the documented IEEEST coefficient map"
    elif model == InternationalStandardModel.PSS4B:
        description = "IEEE dual-input stabilizer with independently limited low, intermediate and high frequency bands"
    elif model == InternationalStandardModel.IEE2ST:
        description = "Dual-input stabilizer with independent transducers and three phase-compensation stages"
    elif model == InternationalStandardModel.BBSEX1:
        description = 'Static excitation with bounded regulator feedback and voltage-dependent field capability.'
    elif model == InternationalStandardModel.BUDCZT:
        description = 'Parallel PI excitation with bounded integral memory and separate actuator/exciter dynamics.'
    elif model == InternationalStandardModel.EXPIC1:
        description = 'PI excitation with separate regulator/field limits, shaped rate feedback and compound supply.'
    elif model == InternationalStandardModel.EXNI:
        description = 'Bidirectional controlled-bridge excitation with external clipping and two-stage rate feedback.'
    elif model == InternationalStandardModel.IEET1B:
        description = 'Biased rotating excitation with clipped voltage error, two regulator stages and selectable rate feedback.'
    elif model == InternationalStandardModel.ST4B:
        description = 'Cascaded bounded voltage/field PI regulators with loaded compound-transformer supply.'
    elif model == InternationalStandardModel.AC8B:
        description = 'Bounded PID excitation with a saturated rotating winding, current-dependent ceiling and loaded diode bridge.'
    elif model == InternationalStandardModel.ST4C:
        description = 'Cascaded bounded PI excitation with selectable take-over gates, firing lag and filtered bridge feedback.'
    elif model == InternationalStandardModel.ST5B:
        description = 'Three live bounded lead-lag channels with take-over selection and terminal-dependent field capability.'
    elif model in (InternationalStandardModel.ST7B,InternationalStandardModel.ST7C):
        description = 'Static excitation with reference takeover, independent capability feedback and optional firing lag.'
    elif model == InternationalStandardModel.ST1C:
        description = 'Terminal-fed static excitation with three minimum/maximum limiter locations and two stabilizer summations.'
    elif model == InternationalStandardModel.ESST1A:
        description = 'Terminal-fed static excitation with selectable limiter/stabilizer routing and field-current limiting.'
    elif model == InternationalStandardModel.IEEET3:
        description = 'Compound-transformer excitation with capability on total field forcing.'
    elif model == InternationalStandardModel.IEEEX3:
        description = 'Compound-transformer excitation with capability on rectified transformer supply.'
    elif model in (InternationalStandardModel.AC6C,InternationalStandardModel.AC6C2):
        description = 'Two-stage brushless excitation with bounded regulator, clipped field-current feedback and selectable forcing limits.'
    elif model == InternationalStandardModel.AC7C:
        description = 'Cascaded PID/PI excitation with explicit takeover gates and compound or self-derived field power.'
    elif model == InternationalStandardModel.AC7B:
        description = 'Cascaded voltage PID and field PI with mixed field feedback, terminal supply and negative forcing capability.'
    elif model == InternationalStandardModel.ST6C:
        description = 'Current-limited PID field regulation with inner feedforward, bridge-command feedback and compound supply.'
    elif model == InternationalStandardModel.ST8C:
        description = 'Static excitation with voltage and field-current PI regulators, field-current feedback, and dual rectifier supplies.'
    elif model == InternationalStandardModel.DC4C:
        description = 'Compound-fed bounded PID regulation of a commutator exciter with loaded supply and field-rate feedback.'
    elif model == InternationalStandardModel.DC4B:
        description = 'Terminal-fed bounded PID excitation with selectable limiter routing and field-rate feedback.'
    elif model == InternationalStandardModel.DC3A:
        description = 'Rheostat excitation with range-normalized motor travel, fast contacts and lower field stop.'
    elif model == InternationalStandardModel.DC2C:
        description = 'Bounded rotating excitation with terminal-fed regulation and selectable limiter takeover.'
    elif model == InternationalStandardModel.ESAC8B:
        description = 'PID voltage regulator with saturated rotating excitation and nonnegative field output.'
    elif model == InternationalStandardModel.ESAC5A:
        description = "Brushless exciter with independent regulator supply and shaped exciter-field feedback"
    elif model == InternationalStandardModel.EXAC4:
        description = "Alternator-fed controlled bridge with external current-dependent output clipping"
    elif model == InternationalStandardModel.AC5C:
        description = 'Brushless excitation with shaped field-loss feedback and selectable excitation limiters.'
    elif model in (InternationalStandardModel.AC1C,InternationalStandardModel.AC2C):
        description = 'Brushless rotating excitation with selectable limiter insertion and a field-current ceiling.'
    elif model == InternationalStandardModel.AC3C:
        description = 'PID brushless excitation with independent over/under-excitation routing.'
    elif model == InternationalStandardModel.AC4C:
        description = 'Controlled bridge with selectable excitation gates and current-dependent capability'
    elif model == InternationalStandardModel.ESAC4A:
        description = "Alternator-fed controlled bridge with non-windup regulation and a minimum-excitation gate"
    elif model == InternationalStandardModel.EXAC1A:
        description = "Brushless exciter with rate feedback from rectified field voltage"
    elif model == InternationalStandardModel.ESAC1A:
        description = "Brushless exciter with separate amplifier/forcing limits and cascaded capability gates"
    elif model == InternationalStandardModel.EXAC2:
        description = "High-response brushless exciter with inner field-current feedback and a finite-gain current override"
    elif model == InternationalStandardModel.EXAC3:
        description = "Self-excited brushless exciter with nonlinear field-voltage rate feedback and minimum-voltage protection"
    elif model == InternationalStandardModel.EXBAS:
        description = "PI brushless excitation with shaped exciter-current rate feedback"
    elif model == InternationalStandardModel.IEET1A:
        description = "Field-controlled excitation with external output-voltage clipping and internal-memory rate feedback"
    elif model == InternationalStandardModel.IEEET4:
        description = "Deadband relay reset with parallel rapid forcing"
    elif model == InternationalStandardModel.IEEET5:
        description = "Continuous error reset with parallel rapid forcing"
    elif model == InternationalStandardModel.IEEEX4:
        description = "Range-normalized reset with parallel rapid forcing"
    elif model == InternationalStandardModel.IEET5A:
        description = "Lag or integral regulation with rapid forcing and an external field clip"
    elif model == InternationalStandardModel.ESAC2A:
        description = "High-response brushless excitation with takeover gates and an internal field-current stop"
    elif model == InternationalStandardModel.ESAC3A:
        description = "Self-excited brushless excitation with minimum-excitation takeover and internal field stops"
    elif model == InternationalStandardModel.MNLEX1:
        description = "Minimum-excitation limiter using active-current and field-current balance"
    elif model == InternationalStandardModel.MNLEX2:
        description = "Circular power-capability limiter with voltage scaling and internal rate feedback"
    elif model == InternationalStandardModel.MNLEX3:
        description = "Linear reactive-current capability limiter with field-voltage feedback"
    elif model == InternationalStandardModel.EXST2A:
        description = 'Multiplicative compound-source static exciter with field-voltage feedback.'
    elif model == InternationalStandardModel.ESST2A:
        description = 'Multiplicative compound-source static exciter with a minimum-excitation gate.'
    elif model == InternationalStandardModel.EXST2:
        description = "Static exciter with compound rectifier supply, commutation loading and bounded field voltage"
    elif model == InternationalStandardModel.REECB:
        description = "WECC REECB renewable-energy electrical control model"
    elif model == InternationalStandardModel.REECC:
        description = "WECC REECC renewable-energy electrical control model"
    elif model == InternationalStandardModel.REGCBCS:
        description = "WECC REGCbCS current-source converter control model for renewable generation"
    elif model == InternationalStandardModel.REPCA:
        description = "WECC REPCA plant-level active- and reactive-power controller for renewable generation"
    elif model == InternationalStandardModel.WT4ACURRENTSOURCE:
        description = "WECC type-4A wind-turbine generator RMS current-source model"
    elif model == InternationalStandardModel.WT4ACURRENTSOURCE2020:
        description = "2020 WECC type-4A wind-turbine generator RMS current-source model"
    elif model == InternationalStandardModel.WT4BCURRENTSOURCE:
        description = "WECC type-4B wind-turbine generator RMS current-source model"
    elif model == InternationalStandardModel.WT4BCURRENTSOURCE2020:
        description = "2020 WECC type-4B wind-turbine generator RMS current-source model"
    elif model == InternationalStandardModel.WT4INJECTOR:
        description = "WECC type-4 wind-turbine RMS current-injection model"
    elif model == InternationalStandardModel.WTG4ACURRENTSOURCE:
        description = "WECC WTG4A type-4 wind-turbine generator RMS current-source model"
    elif model == InternationalStandardModel.WTG4BCURRENTSOURCE:
        description = "WECC WTG4B type-4 wind-turbine generator RMS current-source model"
    elif model == InternationalStandardModel.WPP4BCURRENTSOURCE2020:
        description = "2020 WECC type-4B wind-power-plant RMS current-source model"
    elif model == InternationalStandardModel.PVCURRENTSOURCEBNOPLANTCONTROL:
        description = "Photovoltaic generator RMS current-source B model without plant-level control"
    elif model == InternationalStandardModel.PVVOLTAGESOURCEANOPLANTCONTROL:
        description = "Photovoltaic generator RMS voltage-source A model without plant-level control"
    elif model == InternationalStandardModel.PVVOLTAGESOURCEBNOPLANTCONTROL:
        description = "Photovoltaic generator RMS voltage-source B model without plant-level control"
    elif model == InternationalStandardModel.BESSCBCURRENTSOURCENOPLANTCONTROL:
        description = "WECC BESSCB battery energy-storage RMS current-source model without plant-level control"
    elif model == InternationalStandardModel.FRQTPA:
        description = "FRQTPA frequency trip relay model for generator protection"
    elif model == InternationalStandardModel.VTGTPA:
        description = "VTGTPA voltage trip relay model for generator protection"
    elif model == InternationalStandardModel.FRQTPAT:
        description = "PSS/E FRQTPAT frequency pickup and generator trip relay stages"
    elif model == InternationalStandardModel.VTGTPAT:
        description = "PSS/E VTGTPAT voltage pickup and generator trip relay stages"
    else:
        description = f"{label} international-standard RMS dynamic model"

    return description


def _append_international_standard_group(
        descriptors: List[InternationalStandardTemplateDescriptor],
        models: tuple[InternationalStandardModel, ...],
        category_name: str,
        module_folder: str,
        device_type: DeviceType | None,
) -> None:
    """Append one ordered international-standard family to the local registry.

    :param descriptors: Destination descriptor list.
    :param models: Ordered model identifiers in the family.
    :param category_name: Canonical standard family name.
    :param module_folder: Engine implementation subpackage.
    :param device_type: Complete device type, or ``None`` for controls.
    :return: None.
    """
    model: InternationalStandardModel
    for model in models:
        descriptors.append(InternationalStandardTemplateDescriptor(
            model=model,
            display_label=_international_standard_label(model=model),
            category_path=(category_name,),
            module_folder=module_folder,
            device_type=device_type,
        ))


def get_dynamic_library_international_standard_descriptors() -> Sequence[InternationalStandardTemplateDescriptor]:
    """Return the international-standard inventory owned by the GUI Library.

    :return: Immutable descriptors in canonical family order.
    """
    descriptors: List[InternationalStandardTemplateDescriptor] = list()
    _append_international_standard_group(
        descriptors, (InternationalStandardModel.GENSAL, InternationalStandardModel.GENROU,
                      InternationalStandardModel.GENTRA, InternationalStandardModel.GENROE,
                      InternationalStandardModel.GENSAE),
        "Synchronous machines", "synchronous_machines", DeviceType.GeneratorDevice)

    # Induction models have different physical hosts and are registered
    # explicitly so the editor projection can filter them correctly.
    descriptors.append(InternationalStandardTemplateDescriptor(
        InternationalStandardModel.CIMTR1, "CIMTR1", ("Induction machines",),
        "induction_machines", DeviceType.GeneratorDevice))
    descriptors.append(InternationalStandardTemplateDescriptor(
        InternationalStandardModel.CIMTR2, "CIMTR2", ("Induction machines",),
        "induction_machines", DeviceType.GeneratorDevice))
    descriptors.append(InternationalStandardTemplateDescriptor(
        InternationalStandardModel.CIMTR3, "CIMTR3", ("Induction machines",),
        "induction_machines", DeviceType.GeneratorDevice))
    descriptors.append(InternationalStandardTemplateDescriptor(
        InternationalStandardModel.CIMTR4, "CIMTR4", ("Induction machines",),
        "induction_machines", DeviceType.GeneratorDevice))
    descriptors.append(InternationalStandardTemplateDescriptor(
        InternationalStandardModel.CIMW, "CIMW", ("Induction machines",),
        "induction_machines", DeviceType.LoadDevice))
    descriptors.append(InternationalStandardTemplateDescriptor(
        InternationalStandardModel.CIM5, "CIM5", ("Induction machines",),
        "induction_machines", DeviceType.LoadDevice))
    descriptors.append(InternationalStandardTemplateDescriptor(
        InternationalStandardModel.CIM6, "CIM6", ("Induction machines",),
        "induction_machines", DeviceType.LoadDevice))

    _append_international_standard_group(
        descriptors,
        (InternationalStandardModel.GASTD, InternationalStandardModel.IEESGOD, InternationalStandardModel.HYGOVD,
         InternationalStandardModel.HYGOVR1, InternationalStandardModel.HYGOV2,
         InternationalStandardModel.HYGOV2D,
         InternationalStandardModel.PIDGOV, InternationalStandardModel.PIDGOVD,
         InternationalStandardModel.BBGOV1,
         InternationalStandardModel.TGOV1D, InternationalStandardModel.GGOV1, InternationalStandardModel.GGOV1D, InternationalStandardModel.GOVHYDRO4,
         InternationalStandardModel.GOVSTEAM1, InternationalStandardModel.GOVSTEAMEU,
         InternationalStandardModel.IVOGO, InternationalStandardModel.DEGOV, InternationalStandardModel.DEGOV1, InternationalStandardModel.DEGOV1D,
         InternationalStandardModel.HYGOV, InternationalStandardModel.IEEEG1, InternationalStandardModel.IEEEG1D, InternationalStandardModel.LCFB1,
         InternationalStandardModel.IEEEG2, InternationalStandardModel.TGOV1, InternationalStandardModel.TGOV2,
         InternationalStandardModel.TGOV3, InternationalStandardModel.TGOV4, InternationalStandardModel.GAST, InternationalStandardModel.GAST2A, InternationalStandardModel.IEEEG3, InternationalStandardModel.IEEEG3D,
         InternationalStandardModel.IEESGO),
        "Governors", "governors", None)
    _append_international_standard_group(
        descriptors,
        (InternationalStandardModel.COMP, InternationalStandardModel.COMPCC,
         InternationalStandardModel.CCOMP4A, InternationalStandardModel.REMCMP),
        "Voltage compensators", "voltage_compensators", None)
    _append_international_standard_group(
        descriptors,
        (InternationalStandardModel.CPAAUT,),
        "Auxiliary signals", "auxiliary_signals", None)
    _append_international_standard_group(
        descriptors,
        (InternationalStandardModel.AC1A, InternationalStandardModel.AC1C,
         InternationalStandardModel.AC3C,
         InternationalStandardModel.AC6A, InternationalStandardModel.ESAC6A,
         InternationalStandardModel.AC6C, InternationalStandardModel.AC6C2,
         InternationalStandardModel.AC7B, InternationalStandardModel.AC7C,
         InternationalStandardModel.AC8B, InternationalStandardModel.AC8C,
         InternationalStandardModel.AC9C, InternationalStandardModel.AC11C,
         InternationalStandardModel.BBSEX1, InternationalStandardModel.DC1A,
         InternationalStandardModel.DC1C, InternationalStandardModel.ESDC2A,
         InternationalStandardModel.EXAC1, InternationalStandardModel.EXST2,
         InternationalStandardModel.EXST2A, InternationalStandardModel.ESST2A, InternationalStandardModel.IEEET1,
         InternationalStandardModel.IEEEX1, InternationalStandardModel.ESDC1A, InternationalStandardModel.EXDC2,
         InternationalStandardModel.ESAC5A,
         InternationalStandardModel.ESAC8B,
         InternationalStandardModel.DC2C, InternationalStandardModel.DC3A, InternationalStandardModel.DC4B, InternationalStandardModel.DC4C,
         InternationalStandardModel.IEEET3, InternationalStandardModel.IEEEX3,
         InternationalStandardModel.ESST1A,
         InternationalStandardModel.BUDCZT,
         InternationalStandardModel.EXAC4, InternationalStandardModel.ESAC4A, InternationalStandardModel.AC4C,
         InternationalStandardModel.AC2C, InternationalStandardModel.AC5C,
         InternationalStandardModel.EXAC1A,
         InternationalStandardModel.ESAC1A,
         InternationalStandardModel.EXAC2,
         InternationalStandardModel.EXAC3,
         InternationalStandardModel.EXBAS,
         InternationalStandardModel.IEET1A, InternationalStandardModel.IEET1B, InternationalStandardModel.EXNI, InternationalStandardModel.EXPIC1,
         InternationalStandardModel.IEEET4,
         InternationalStandardModel.IEEET5,
         InternationalStandardModel.IEEEX4,
         InternationalStandardModel.IEET5A,
         InternationalStandardModel.ESAC2A,
         InternationalStandardModel.ESAC3A,
         InternationalStandardModel.IEEET2,
         InternationalStandardModel.IEEEX2, InternationalStandardModel.IEEX2A,
         InternationalStandardModel.SCRX, InternationalStandardModel.SEXS,
         InternationalStandardModel.ST1A, InternationalStandardModel.ST1C,
         InternationalStandardModel.ST4B, InternationalStandardModel.ST4C,
         InternationalStandardModel.ST5B, InternationalStandardModel.ST5C,
         InternationalStandardModel.ST6B, InternationalStandardModel.ST6C,
         InternationalStandardModel.ST7B, InternationalStandardModel.ST7C,
         InternationalStandardModel.ST8C, InternationalStandardModel.ST9C,
         InternationalStandardModel.ST10C, InternationalStandardModel.VRKUNDUR,
         InternationalStandardModel.IEEEVC_1981),
        "Excitation systems", "excitation_systems", None)
    _append_international_standard_group(
        descriptors,
        (InternationalStandardModel.IEEL, InternationalStandardModel.MAXEX2,
         InternationalStandardModel.MNLEX1, InternationalStandardModel.MNLEX2, InternationalStandardModel.MNLEX3,
         InternationalStandardModel.OEL2C, InternationalStandardModel.OEL3C,
         InternationalStandardModel.OEL4C, InternationalStandardModel.OEL5C,
         InternationalStandardModel.SCL1C, InternationalStandardModel.SCL2C,
         InternationalStandardModel.UEL1, InternationalStandardModel.UEL2C),
        "Excitation limiters", "excitation_limiters", None)
    _append_international_standard_group(
        descriptors,
        (InternationalStandardModel.PSS1AOMEGA, InternationalStandardModel.PSS1APGEN,
         InternationalStandardModel.PSS2A, InternationalStandardModel.PSS2B,
         InternationalStandardModel.PSS2C, InternationalStandardModel.PSS3B,
         InternationalStandardModel.PSS4B,
         InternationalStandardModel.PSS3C, InternationalStandardModel.PSS6C,
         InternationalStandardModel.PSS7C,
         InternationalStandardModel.PSSKUNDUR, InternationalStandardModel.STAB1,
         InternationalStandardModel.STAB2A, InternationalStandardModel.STAB3,
         InternationalStandardModel.STAB4, InternationalStandardModel.STABNI, InternationalStandardModel.IVOST,
         InternationalStandardModel.IEEEST, InternationalStandardModel.PSS1A,
         InternationalStandardModel.IEE2ST, InternationalStandardModel.BEPSST,
         InternationalStandardModel.OSTB2T, InternationalStandardModel.OSTB5T),
        "Power system stabilizers", "power_system_stabilizers", None)
    _append_international_standard_group(
        descriptors,
        (InternationalStandardModel.REECB, InternationalStandardModel.REECC,
         InternationalStandardModel.REGCBCS, InternationalStandardModel.REPCA,
         InternationalStandardModel.WT12T1),
        "Renewable controls", "renewable_controls", None)
    _append_international_standard_group(
        descriptors,
        (InternationalStandardModel.WT4ACURRENTSOURCE, InternationalStandardModel.WT4ACURRENTSOURCE2020,
         InternationalStandardModel.WT4BCURRENTSOURCE, InternationalStandardModel.WT4BCURRENTSOURCE2020,
         InternationalStandardModel.WT4INJECTOR, InternationalStandardModel.WTG4ACURRENTSOURCE,
         InternationalStandardModel.WTG4BCURRENTSOURCE, InternationalStandardModel.WPP4BCURRENTSOURCE2020),
        "Wind generation", "wind_generation", DeviceType.GeneratorDevice)
    _append_international_standard_group(
        descriptors,
        (InternationalStandardModel.PVCURRENTSOURCEBNOPLANTCONTROL,
         InternationalStandardModel.PVVOLTAGESOURCEANOPLANTCONTROL,
         InternationalStandardModel.PVVOLTAGESOURCEBNOPLANTCONTROL),
        "Solar PV generation", "solar_pv_generation", DeviceType.GeneratorDevice)
    _append_international_standard_group(
        descriptors, (InternationalStandardModel.BESSCBCURRENTSOURCENOPLANTCONTROL,),
        "Battery energy storage", "battery_energy_storage", DeviceType.BatteryDevice)
    _append_international_standard_group(
        descriptors, (InternationalStandardModel.FRQTPA, InternationalStandardModel.VTGTPA,
                      InternationalStandardModel.FRQTPAT, InternationalStandardModel.VTGTPAT),
        "Protection relays", "protection_relays", None)
    international_builders: dict[str, object] = get_international_model_builders()
    family_labels: dict[str, str] = dict()
    family_labels["common"] = "Common"
    family_labels["excitation_limiters"] = "Excitation limiters"
    family_labels["excitation_systems"] = "Excitation systems"
    family_labels["governors"] = "Governors"
    family_labels["induction_machines"] = "Induction machines"
    family_labels["load_characteristics"] = "Load characteristics"
    family_labels["power_system_stabilizers"] = "Power system stabilizers"
    family_labels["synchronous_machines"] = "Synchronous machines"
    family_labels["voltage_compensators"] = "Voltage compensators"
    family_labels["wind_generation"] = "Wind generation"
    model_key: str
    for model_key in sorted(international_builders):
        builder: object = international_builders[model_key]
        module_parts: list[str] = builder.__module__.split(".")
        family_label: str | None = family_labels.get(module_parts[-2], None)
        if family_label is None:
            raise ValueError(f"Unsupported international model family: {module_parts[-2]}")
        else:
            descriptors.append(InternationalStandardTemplateDescriptor(
                model=InternationalStandardModel[model_key],
                display_label=model_key,
                category_path=(family_label,),
                module_folder=module_parts[-2],
                module_name=module_parts[-1],
            ))
    return tuple(descriptors)


def get_dynamic_library_procedural_descriptors() -> Sequence[ProceduralBlockTemplateDescriptor]:
    """Return the procedural inventory and ordering owned by the GUI Library.

    :return: Immutable procedural descriptors in canonical category order.
    """
    return tuple((
        ProceduralBlockTemplateDescriptor(ProceduralLogicType.FixedSample, "Fixed sample",
                                          ("Sampling and history",), ("condition",), ("y",), tuple()),
        ProceduralBlockTemplateDescriptor(ProceduralLogicType.SampledValue, "Sampled value",
                                          ("Sampling and history",), ("u",), ("y",), tuple()),
        ProceduralBlockTemplateDescriptor(ProceduralLogicType.TimeDelay, "Time delay",
                                          ("Sampling and history",), ("u",), ("y",),
                                          (ProceduralBlockParameterSpec("delay", 0.0),)),
        ProceduralBlockTemplateDescriptor(ProceduralLogicType.MovingAverage, "Moving average",
                                          ("Sampling and history",), ("u",), ("y",),
                                          (ProceduralBlockParameterSpec("delay", 0.0),
                                           ProceduralBlockParameterSpec("window", 0.01))),
        ProceduralBlockTemplateDescriptor(ProceduralLogicType.WrappedDerivative, "Wrapped derivative",
                                          ("Measurements and Units", "Frequency measurement"),
                                          ("angle_rad",), ("rate_rad_per_s",),
                                          (ProceduralBlockParameterSpec("maximum_rate", 5.0),)),
        ProceduralBlockTemplateDescriptor(ProceduralLogicType.HardSaturation, "Hard saturation",
                                          ("Limits and latches",), ("u",), ("y",),
                                          (ProceduralBlockParameterSpec("minimum", -1.0),
                                           ProceduralBlockParameterSpec("maximum", 1.0))),
        ProceduralBlockTemplateDescriptor(ProceduralLogicType.GradientLimiter, "Gradient limiter",
                                          ("Limits and latches",), ("u",), ("y",),
                                          (ProceduralBlockParameterSpec("lower_rate", -1.0),
                                           ProceduralBlockParameterSpec("upper_rate", 1.0))),
        ProceduralBlockTemplateDescriptor(ProceduralLogicType.FlipFlop, "Flip-flop",
                                          ("Limits and latches",), ("set", "reset"), ("y",), tuple()),
        ProceduralBlockTemplateDescriptor(ProceduralLogicType.AnalogFlipFlop, "Analog flip-flop",
                                          ("Limits and latches",), ("u", "set", "reset"), ("y",), tuple()),
        ProceduralBlockTemplateDescriptor(ProceduralLogicType.PickupDropoff, "Pickup/dropoff",
                                          ("Limits and latches",), ("condition",), ("y",),
                                          (ProceduralBlockParameterSpec("pickup_delay", 0.0),
                                           ProceduralBlockParameterSpec("dropoff_delay", 0.0))),
        ProceduralBlockTemplateDescriptor(ProceduralLogicType.TimedPulse, "Timed pulse",
                                          ("Limits and latches",), ("condition",), ("y",),
                                          (ProceduralBlockParameterSpec("duration", 1.0),)),
        ProceduralBlockTemplateDescriptor(ProceduralLogicType.DelayedThresholdLatch,
                                          "Delayed threshold latch", ("Limits and latches",),
                                          ("monitored",), ("y",), tuple()),
        ProceduralBlockTemplateDescriptor(ProceduralLogicType.ConditionalDiagnostic,
                                          "Conditional diagnostic", ("Events and diagnostics",),
                                          ("condition",), tuple(), tuple()),
        ProceduralBlockTemplateDescriptor(ProceduralLogicType.DelayedSwitchEvent,
                                          "Delayed switch event", ("Events and diagnostics",),
                                          ("guard", "trigger"), ("closed",),
                                          (ProceduralBlockParameterSpec("delay", 0.0),), True),
        ProceduralBlockTemplateDescriptor(ProceduralLogicType.ResetOnRisingEdge,
                                          "Reset on rising edge", ("Events and diagnostics",),
                                          ("condition", "value"), ("y",), tuple()),
        ProceduralBlockTemplateDescriptor(ProceduralLogicType.StartupHandover,
                                          "Startup handover", ("Events and diagnostics",),
                                          tuple(), ("enabled",),
                                          (ProceduralBlockParameterSpec("enable_time", 0.0),)),
        ProceduralBlockTemplateDescriptor(ProceduralLogicType.ValveState, "Valve state",
                                          ("Switching and modulation",),
                                          ("valve_voltage", "valve_current"), ("state",),
                                          (ProceduralBlockParameterSpec("valve_type", 0.0),
                                           ProceduralBlockParameterSpec("gate", 0.0),
                                           ProceduralBlockParameterSpec("antiparallel", 1.0),
                                           ProceduralBlockParameterSpec("voltage_epsilon", 1.0e-9),
                                           ProceduralBlockParameterSpec("current_epsilon", 1.0e-9))),
        ProceduralBlockTemplateDescriptor(ProceduralLogicType.ThreePhaseCarrierPwm,
                                          "Three-phase carrier PWM", ("Switching and modulation",),
                                          ("modulation_a", "modulation_b", "modulation_c"),
                                          ("gate_a", "gate_b", "gate_c"),
                                          (ProceduralBlockParameterSpec("switching_frequency", 2.0 * math.pi * 1000.0),
                                           ProceduralBlockParameterSpec("carrier_phase", 0.0))),
        ProceduralBlockTemplateDescriptor(ProceduralLogicType.ThreePhaseCarrierSampledModulation,
                                          "Three-phase sampled modulation", ("Switching and modulation",),
                                          ("modulation_a", "modulation_b", "modulation_c"),
                                          ("sample_a", "sample_b", "sample_c"),
                                          (ProceduralBlockParameterSpec("switching_frequency", 2.0 * math.pi * 1000.0),
                                           ProceduralBlockParameterSpec("carrier_phase", 0.0))),
    ))


def build_rms_control_library_branch() -> Dict[str, object]:
    """Build the categorized RMS control branch, including standards.

    :return: Nested RMS control branch.
    """
    branch: Dict[str, object] = dict()
    native_controls: tuple[tuple[tuple[str, ...], LibraryLeafSpec], ...] = (
        (("PLL", "Native"), LibraryLeafSpec("PLL transformer", BlockType.PLL_TRANSFORM_RMS)),
        (("PLL", "Native"), LibraryLeafSpec("PLL explicit PI", BlockType.VSC_PLL_RMS)),
        (("Governors", "Native"), LibraryLeafSpec("Governor", BlockType.GOV_RMS)),
        (("Exciters", "Native"), LibraryLeafSpec("Exciter", BlockType.EXCITER_RMS)),
        (("Stabilizers", "Native"), LibraryLeafSpec("Stabilizer", BlockType.STAB_RMS)),
        (("Active power and Vdc", "Native"), LibraryLeafSpec("PI power controller", BlockType.PI_POWER_CONTROLLER)),
        (("Active power and Vdc", "Native"), LibraryLeafSpec("Vdc / P control", BlockType.VSC_ACTIVE_CONTROL_RMS)),
        (("Reactive power and voltage", "Native"), LibraryLeafSpec("Qac / Vac control", BlockType.VSC_REACTIVE_CONTROL_RMS)),
        (("Current control", "Native"), LibraryLeafSpec("PI current controller", BlockType.PI_CURRENT_CONTROLLER)),
        (("Current control", "Native"), LibraryLeafSpec("d-axis current PI controller", BlockType.VSC_VD_HAT_RMS,
                                                         "d-axis current PI controller vd hat vd_hat y_vd_hat")),
        (("Current control", "Native"), LibraryLeafSpec("q-axis current PI controller", BlockType.VSC_VQ_HAT_RMS,
                                                         "q-axis current PI controller vq hat vq_hat y_vq_hat")),
        (("Current control", "Native"), LibraryLeafSpec("Converter electrical equations", BlockType.VSC_ELECTRICAL_RMS)),
        (("Current control", "Native"), LibraryLeafSpec("DC-link capacitor", BlockType.VSC_DC_LINK_RMS)),
        (("Limiters", "Native"), LibraryLeafSpec("Current limiter", BlockType.VSC_CURRENT_LIMITER_RMS)),
    )
    native_entry: tuple[tuple[str, ...], LibraryLeafSpec]
    for native_entry in native_controls:
        insert_library_leaf(branch, native_entry[0], native_entry[1])

    standard_category_map: tuple[tuple[str, str], ...] = (
        ("Governors", "Governors"),
        ("Voltage compensators", "Reactive power and voltage"),
        ("Auxiliary signals", "Auxiliary signals"),
        ("Excitation systems", "Exciters"),
        ("Excitation limiters", "Limiters"),
        ("Power system stabilizers", "Stabilizers"),
        ("Renewable controls", "Renewable controls"),
        ("Protection relays", "Protection"),
        ("Common", "Auxiliary signals"),
        ("Induction machines", "Machines and loads"),
        ("Load characteristics", "Machines and loads"),
        ("Synchronous machines", "Machines and loads"),
        ("Wind generation", "Renewable controls"),
    )
    descriptor: InternationalStandardTemplateDescriptor
    for descriptor in get_dynamic_library_international_standard_descriptors():
        if descriptor.device_type is None:
            destination_name: str | None = None
            mapping_entry: tuple[str, str]
            for mapping_entry in standard_category_map:
                if descriptor.category_path[0] == mapping_entry[0]:
                    destination_name = mapping_entry[1]
                else:
                    pass
            if destination_name is not None:
                insert_library_leaf(
                    branch, (destination_name, "International standards"),
                    LibraryLeafSpec(descriptor.display_label, descriptor, descriptor.search_text))
            else:
                pass
        else:
            pass
    return branch


def build_emt_control_library_branch() -> Dict[str, object]:
    """Build the categorized EMT control branch.

    :return: Nested EMT control branch.
    """
    return dict((
        ("Governors", dict((("Native", list((LibraryLeafSpec("Governor", BlockType.GOV_EMT),))),))),
        ("Exciters", dict((("Native", list((LibraryLeafSpec("Exciter", BlockType.EXCITER_EMT),))),))),
        ("Stabilizers", dict((("Native", list((LibraryLeafSpec("Stabilizer", BlockType.STAB_EMT),))),))),
    ))


def get_international_standard_device_category(
        descriptor: InternationalStandardTemplateDescriptor,
) -> tuple[str, ...]:
    """Map a complete international model to the shared device categories.

    :param descriptor: International-standard model registration.
    :return: Device branch category shared with native models.
    """
    if descriptor.category_path[0] == "Induction machines":
        return ("Induction machines",)
    elif descriptor.device_type == DeviceType.GeneratorDevice:
        if descriptor.category_path[0] == "Wind generation":
            return ("Wind turbines",)
        elif descriptor.category_path[0] == "Solar PV generation":
            return ("PV generators",)
        else:
            return get_generator_technology_category(label=descriptor.display_label)
    elif descriptor.device_type == DeviceType.BatteryDevice:
        return ("Batteries",)
    elif descriptor.device_type == DeviceType.LoadDevice:
        return ("Loads",)
    else:
        return ("Other devices",)


def build_device_library_branch(
        mode: DynamicSimulationMode,
        device_type: DeviceType | None,
) -> Dict[str, object]:
    """Build the complete or device-filtered canonical ``Devices`` branch.

    :param mode: Dynamic simulation domain.
    :param device_type: Physical device filter, or ``None`` for all devices.
    :return: Nested device branch used by both editor and catalogue.
    """
    branch: Dict[str, object] = dict()
    entry: object
    for entry in get_template_catalogue_entries(mode=mode):
        spec: LibraryDeviceTemplateSpec = LibraryDeviceTemplateSpec(
            label=entry.label,
            source=entry.source,
            mode=entry.mode,
            device_type=entry.device_type,
            category_path=entry.category_path,
            description=entry.description,
            search_text=entry.search_text,
            compatible_device_types=entry.compatible_device_types,
        )
        if device_type is None or spec.is_compatible_with(device_type=device_type):
            insert_library_leaf(branch, spec.category_path, LibraryLeafSpec(spec.label, spec, spec.search_text))
        else:
            pass
    return branch


def build_dynamic_library_structure(
        mode: DynamicSimulationMode,
        device_type: DeviceType,
) -> Dict[str, object]:
    """Build one editor projection from the canonical Library registrations.

    :param mode: Dynamic simulation domain.
    :param device_type: Physical device whose internal model is edited.
    :return: Ordered top-level Library tree structure.
    """
    structure: Dict[str, object] = dict()
    structure["Basic"] = build_basic_library_branch()
    if mode == DynamicSimulationMode.EMT:
        # Fault insertion is a mode-wide composition tool rather than a full
        # network-device drawing. Keep it near the top of the visible Library
        # so the large device and control trees cannot obscure its presence.
        structure["Faults"] = list((LibraryLeafSpec(
            label="Fault EMT",
            payload=BlockType.FAULT_EMT,
            search_text="EMT fault short circuit LG LL LLG LLL LLLG ground",
        ),))
    else:
        pass
    structure["Devices"] = build_device_library_branch(mode=mode, device_type=device_type)
    if mode == DynamicSimulationMode.RMS:
        structure["Controls"] = build_rms_control_library_branch()
    elif mode == DynamicSimulationMode.EMT:
        structure["Controls"] = build_emt_control_library_branch()
    else:
        pass
    structure["Procedural logic"] = build_procedural_library_branch()
    return structure


def _collect_device_specs_from_branch(
        branch_data: object,
        specs: List[LibraryDeviceTemplateSpec],
) -> None:
    """Collect canonical device specifications from one recursive branch.

    :param branch_data: Nested branch or leaf list.
    :param specs: Destination device specification list.
    :return: None.
    """
    if isinstance(branch_data, dict):
        child_data: object
        for child_data in branch_data.values():
            _collect_device_specs_from_branch(child_data, specs)
    elif isinstance(branch_data, list):
        leaf: LibraryLeafSpec
        for leaf in sorted(branch_data, key=_library_leaf_label_sort_key):
            if isinstance(leaf.payload, LibraryDeviceTemplateSpec):
                specs.append(leaf.payload)
            else:
                pass
    else:
        raise TypeError(f"Unsupported device branch data type {type(branch_data)!r}")


def get_dynamic_library_device_specs(mode: DynamicSimulationMode) -> List[LibraryDeviceTemplateSpec]:
    """Return every descendant of the canonical mode ``Devices`` branch.

    :param mode: Dynamic simulation domain.
    :return: Device-template specifications in Library branch order.
    """
    specs: List[LibraryDeviceTemplateSpec] = list()
    entry: object
    for entry in get_template_catalogue_entries(mode=mode):
        specs.append(LibraryDeviceTemplateSpec(
            label=entry.label,
            source=entry.source,
            mode=entry.mode,
            device_type=entry.device_type,
            category_path=entry.category_path,
            description=entry.description,
            search_text=entry.search_text,
            compatible_device_types=entry.compatible_device_types,
        ))
    return specs


def build_basic_branch_skeleton() -> Dict[str, object]:
    """Return an empty Basic branch populated exclusively by engine catalogues.

    :return: Empty branch.
    """
    return dict()


def get_basic_procedural_category_path(
        descriptor: ProceduralBlockTemplateDescriptor,
) -> tuple[str, ...] | None:
    """Return the Basic path for a reusable procedural primitive.

    Common sampling, memory, limit, latch, edge, and timer behaviors belong in
    the semantic Basic taxonomy. Device-oriented switching and diagnostic
    behaviors remain under the dedicated ``Procedural logic`` branch.

    :param descriptor: Procedural descriptor being projected into the Library.
    :return: Basic category path, or ``None`` for an advanced procedural block.
    """
    logic_tpe: ProceduralLogicType = descriptor.logic_tpe
    if logic_tpe == ProceduralLogicType.FixedSample:
        category_path: tuple[str, ...] | None = ("Memory and discrete-time", "Sample and hold")
    elif logic_tpe == ProceduralLogicType.SampledValue:
        category_path = ("Memory and discrete-time", "Previous value")
    elif logic_tpe == ProceduralLogicType.TimeDelay:
        category_path = ("Memory and discrete-time", "Exact time delay")
    elif logic_tpe == ProceduralLogicType.MovingAverage:
        category_path = ("Memory and discrete-time", "Moving average")
    elif logic_tpe == ProceduralLogicType.WrappedDerivative:
        category_path = ("Measurements and conversions", "Electrical measurements")
    elif logic_tpe == ProceduralLogicType.HardSaturation:
        category_path = ("Limits and nonlinearities", "Saturation")
    elif logic_tpe == ProceduralLogicType.GradientLimiter:
        category_path = ("Limits and nonlinearities", "Rate limiter")
    elif logic_tpe in (ProceduralLogicType.FlipFlop, ProceduralLogicType.AnalogFlipFlop):
        category_path = ("Logic and events", "Latches and flip-flops")
    elif logic_tpe in (ProceduralLogicType.PickupDropoff, ProceduralLogicType.TimedPulse,
                      ProceduralLogicType.DelayedThresholdLatch):
        category_path = ("Logic and events", "Timed comparator")
    elif logic_tpe == ProceduralLogicType.ResetOnRisingEdge:
        category_path = ("Logic and events", "Edge detector")
    elif logic_tpe == ProceduralLogicType.StartupHandover:
        category_path = ("Logic and events", "Timers")
    elif logic_tpe in (
            ProceduralLogicType.ConditionalDiagnostic,
            ProceduralLogicType.DelayedSwitchEvent,
            ProceduralLogicType.ValveState,
            ProceduralLogicType.ThreePhaseCarrierPwm,
            ProceduralLogicType.ThreePhaseCarrierSampledModulation,
    ):
        category_path = None
    else:
        raise ValueError(f"Unclassified procedural Library type '{logic_tpe.name}'")
    return category_path


def build_non_empty_library_branch(branch: Dict[str, object]) -> Dict[str, object]:
    """Copy a Library branch while removing empty categories recursively.

    :param branch: Fully populated branch built from the canonical skeleton.
    :return: Branch containing only categories with at least one visible leaf.
    """
    result: Dict[str, object] = dict()
    label: str
    child_data: object
    for label, child_data in branch.items():
        if isinstance(child_data, dict):
            filtered_child: Dict[str, object] = build_non_empty_library_branch(branch=child_data)
            if len(filtered_child) > 0:
                result[label] = filtered_child
            else:
                pass
        elif isinstance(child_data, list):
            if len(child_data) > 0:
                result[label] = child_data
            else:
                pass
        else:
            raise TypeError(f"Unsupported Library branch data type {type(child_data)!r}")
    return result


def build_basic_library_branch() -> Dict[str, object]:
    """Build the complete categorized ``Basic`` library branch.

    Structural blocks, canonical procedural primitives, and non-duplicate
    catalog descriptors are inserted into one semantic hierarchy. Legacy
    wrapper templates remain loadable even when their duplicate leaf is hidden.

    :return: Nested branch data consumed by :class:`DynamicEditorLibrary`.
    """
    basic_branch: Dict[str, object] = build_basic_branch_skeleton()
    structural_blocks: tuple[tuple[tuple[str, ...], LibraryLeafSpec], ...] = (
        (("Mathematical functions", "Constants"), LibraryLeafSpec("Configurable constant", BlockType.CONST)),
        (("Mathematical functions", "Gain"), LibraryLeafSpec("Gain", BlockType.GAIN)),
        (("Mathematical functions", "Sum"), LibraryLeafSpec("Sum", BlockType.SUM)),
        (("Mathematical functions", "Product"), LibraryLeafSpec("Product", BlockType.PRODUCT)),
        (("Mathematical functions", "Minimum/Maximum"), LibraryLeafSpec("MIN", BlockType.MIN)),
        (("Mathematical functions", "Minimum/Maximum"), LibraryLeafSpec("MAX", BlockType.MAX)),
        (("Mathematical functions", "Absolute value"), LibraryLeafSpec("Absolute value", BlockType.ABS)),
        (("Lookup tables", "Inverse 1D lookup table"),
         LibraryLeafSpec("Inverse linear lookup table", BlockType.INVERSE_LOOKUP_ARRAY)),
        (("Lookup tables", "1D lookup table"),
         LibraryLeafSpec("Linear lookup table", BlockType.LOOKUP_ARRAY_LINEAR)),
        (("Lookup tables", "1D lookup table"),
         LibraryLeafSpec("Spline lookup table", BlockType.LOOKUP_ARRAY_SPLINE)),
        (("Lookup tables", "1D lookup table"),
         LibraryLeafSpec("Dynamic linear lookup table", BlockType.LOOKUP_ARRAY_LINEAR_VARIABLE)),
        (("Lookup tables", "2D lookup table"),
         LibraryLeafSpec("Bilinear lookup table", BlockType.LOOKUP_MATRIX_LINEAR)),
        (("Lookup tables", "2D lookup table"),
         LibraryLeafSpec("2D spline lookup table", BlockType.LOOKUP_MATRIX_SPLINE)),
    )
    structural_entry: tuple[tuple[str, ...], LibraryLeafSpec]
    for structural_entry in structural_blocks:
        insert_library_leaf(
            branch=basic_branch,
            category_path=structural_entry[0],
            leaf=structural_entry[1],
        )

    # Presets are convenient initial views of one canonical configurable
    # integrator, not separate block implementations. General Structure can
    # still transform any created instance into every supported combination.
    integrator_preset_entry: tuple[str, IntegratorPresetDescriptor]
    for integrator_preset_entry in build_integrator_preset_descriptors():
        insert_library_leaf(
            branch=basic_branch,
            category_path=("Continuous dynamics", "Integrators"),
            leaf=LibraryLeafSpec(
                label=integrator_preset_entry[0],
                payload=integrator_preset_entry[1],
            ),
        )

    # Derivative presets are common starting configurations of one canonical
    # builder. Less common combinations remain available through General
    # Structure without expanding the Library with legacy duplicates.
    derivative_preset_entry: tuple[str, DerivativePresetDescriptor]
    for derivative_preset_entry in build_derivative_preset_descriptors():
        insert_library_leaf(
            branch=basic_branch,
            category_path=("Continuous dynamics", "Derivatives"),
            leaf=LibraryLeafSpec(
                label=derivative_preset_entry[0],
                payload=derivative_preset_entry[1],
            ),
        )

    # Exact named values are registered as two parallel normal block families:
    # sources under Constants and multipliers under Gain. Imported equivalents
    # remain available for legacy files but their duplicate leaves are hidden.
    exact_descriptor: ExactMathematicalBlockDescriptor
    for exact_descriptor in build_exact_mathematical_block_descriptors():
        if exact_descriptor.operation == ExactMathematicalBlockOperation.CONSTANT:
            exact_category_path: tuple[str, ...] = ("Mathematical functions", "Constants")
        else:
            exact_category_path = ("Mathematical functions", "Gain")
        insert_library_leaf(
            branch=basic_branch,
            category_path=exact_category_path,
            leaf=LibraryLeafSpec(
                label=exact_descriptor.display_label,
                payload=exact_descriptor,
                search_text=exact_descriptor.search_text,
            ),
        )

    # Reusable procedural primitives are shown in their semantic Basic category
    # instead of being duplicated under the top-level procedural branch.
    procedural_descriptor: ProceduralBlockTemplateDescriptor
    for procedural_descriptor in get_dynamic_library_procedural_descriptors():
        procedural_category_path: tuple[str, ...] | None = get_basic_procedural_category_path(
            descriptor=procedural_descriptor,
        )
        if procedural_category_path is not None:
            insert_library_leaf(
                branch=basic_branch,
                category_path=procedural_category_path,
                leaf=LibraryLeafSpec(
                    label=procedural_descriptor.display_label,
                    payload=procedural_descriptor,
                    search_text=procedural_descriptor.search_text,
                ),
            )
        else:
            pass

    # The engine catalogue owns every Basic category and leaf placement.
    descriptors: list[BasicBlockTemplateDescriptor]
    descriptor: BasicBlockTemplateDescriptor
    for descriptors in BASIC_BLOCK_CATALOGUE.values():
        for descriptor in descriptors:
            insert_library_leaf(
                branch=basic_branch,
                category_path=tuple(descriptor.category_path),
                leaf=LibraryLeafSpec(
                    label=descriptor.display_label,
                    payload=descriptor,
                    search_text=descriptor.search_text,
                ),
            )

    # Planned categories without an implementation are intentionally omitted
    # until a real block is available, avoiding dead ends in the visible tree.
    return build_non_empty_library_branch(branch=basic_branch)


def build_procedural_library_branch() -> Dict[str, object]:
    """Build the advanced procedural-logic branch.

    The descriptor inventory and its ordering are owned locally by this
    Library module. Engine code remains responsible only for materializing the
    selected typed behavior.

    :return: Nested branch data shared by RMS and EMT editors.
    """
    branch: Dict[str, object] = dict()
    descriptor: ProceduralBlockTemplateDescriptor
    for descriptor in get_dynamic_library_procedural_descriptors():
        if get_basic_procedural_category_path(descriptor=descriptor) is None:
            insert_library_leaf(
                branch=branch,
                category_path=tuple(descriptor.category_path),
                leaf=LibraryLeafSpec(
                    label=descriptor.display_label,
                    payload=descriptor,
                    search_text=descriptor.search_text,
                ),
            )
        else:
            pass
    return branch


def _library_leaf_label_sort_key(leaf: "LibraryLeafSpec") -> str:
    """
    Return the case-insensitive sort key for one library leaf.

    :param leaf: Library leaf specification.
    :return: Lower-case label.
    """
    return leaf.label.lower()


def is_supported_library_payload(item_data: object) -> bool:
    """
    Check whether a tree item payload can be dragged into the editor scene.

    :param item_data: Candidate payload object.
    :return: ``True`` when the payload can be materialized in the editor.
    """
    if isinstance(item_data, (IntegratorPresetDescriptor, DerivativePresetDescriptor)):
        return True
    elif isinstance(item_data, BlockType):
        return True
    elif isinstance(item_data, ExactMathematicalBlockDescriptor):
        return True
    elif isinstance(item_data, BasicBlockTemplateDescriptor):
        return True
    elif isinstance(item_data, ProceduralBlockTemplateDescriptor):
        return True
    elif isinstance(item_data, InternationalStandardTemplateDescriptor):
        return True
    elif isinstance(item_data, LibraryDeviceTemplateSpec):
        return True
    elif isinstance(item_data, (RmsModelTemplate, EmtModelTemplate, FmuTemplate)):
        return True
    else:
        return False


def insert_library_leaf(branch: Dict[str, object], category_path: tuple[str, ...], leaf: LibraryLeafSpec) -> None:
    """
    Insert one library leaf into a nested dictionary branch.

    :param branch: Mutable catalogue branch being populated.
    :param category_path: Remaining category path for the leaf.
    :param leaf: Typed leaf to insert.
    :return: None.
    """

    head: str = category_path[0]
    if len(category_path) == 1:
        leaves: object = branch.setdefault(head, list())
        if isinstance(leaves, list):
            leaves.append(leaf)
        else:
            raise TypeError(f"Category '{head}' is already used as a branch node")
    else:
        child_branch: object = branch.setdefault(head, dict())
        if isinstance(child_branch, dict):
            insert_library_leaf(child_branch, category_path[1:], leaf)
        else:
            raise TypeError(f"Category '{head}' is already used as a leaf collection")


def build_library_item_description(payload: object) -> str:
    """Return the description shown in the library tree second column.

    :param payload: Typed payload represented by one library leaf.
    :return: Human-readable description derived from existing block metadata.
    """
    if isinstance(payload, IntegratorPresetDescriptor):
        description: str = payload.get_description()
    elif isinstance(payload, DerivativePresetDescriptor):
        description = payload.get_description()
    elif isinstance(payload, BasicBlockTemplateDescriptor):
        if len(payload.description) > 0:
            description: str = payload.description
        else:
            description = build_library_interface_description(
                inputs=payload.inputs,
                outputs=payload.outputs,
                states=payload.states,
                params=payload.params,
            )
    elif isinstance(payload, ExactMathematicalBlockDescriptor):
        description = payload.description
    elif isinstance(payload, ProceduralBlockTemplateDescriptor):
        if len(payload.description) > 0:
            description = payload.description
        else:
            description = build_library_interface_description(
                inputs=payload.input_names,
                outputs=payload.output_names,
                states=tuple(),
                params=tuple(parameter_spec.name for parameter_spec in payload.parameter_specs),
            )
        if payload.requires_configuration:
            description = f"{description.rstrip('.')}. Requires external configuration"
        else:
            pass
    elif isinstance(payload, InternationalStandardTemplateDescriptor):
        if isinstance(payload.model, InternationalStandardModel):
            description = build_international_standard_description(model=payload.model)
        else:
            description = f"{payload.display_label} international-standard RMS equation block"
    elif isinstance(payload, LibraryDeviceTemplateSpec):
        description = payload.description
    elif isinstance(payload, RmsModelTemplate):
        if len(payload.comment) > 0:
            description = payload.comment
        else:
            description = "RMS model template"
    elif isinstance(payload, EmtModelTemplate):
        if len(payload.comment) > 0:
            description = payload.comment
        else:
            description = "EMT model template"
    elif isinstance(payload, FmuTemplate):
        if len(payload.comment) > 0:
            description = payload.comment
        else:
            description = "FMU model template"
    elif isinstance(payload, BlockType):
        description = build_block_type_description(block_type=payload)
    else:
        description = ""

    return description


def build_library_interface_description(
        inputs: Sequence[str],
        outputs: Sequence[str],
        states: Sequence[str],
        params: Sequence[str],
) -> str:
    """Build a compact interface summary from descriptor metadata.

    :param inputs: Input port names.
    :param outputs: Output port names.
    :param states: State variable names.
    :param params: Runtime parameter names.
    :return: Compact description text.
    """
    parts: list[str] = list()
    input_part: str = build_library_name_list(label="Inputs", names=inputs)
    output_part: str = build_library_name_list(label="Outputs", names=outputs)
    state_part: str = build_library_name_list(label="States", names=states)
    param_part: str = build_library_name_list(label="Parameters", names=params)

    if len(input_part) > 0:
        parts.append(input_part)
    else:
        pass
    if len(output_part) > 0:
        parts.append(output_part)
    else:
        pass
    if len(state_part) > 0:
        parts.append(state_part)
    else:
        pass
    if len(param_part) > 0:
        parts.append(param_part)
    else:
        pass

    if len(parts) > 0:
        description: str = "; ".join(parts)
    else:
        description = "No exposed ports"

    return description


def build_library_name_list(label: str, names: Sequence[str]) -> str:
    """Build one bounded comma-separated description segment.

    :param label: Segment label.
    :param names: Names to display.
    :return: Description segment, or an empty string when no names exist.
    """
    if len(names) == 0:
        text: str = ""
    else:
        visible_names: list[str] = list()
        name_index: int
        for name_index in range(min(6, len(names))):
            visible_names.append(str(names[name_index]))
        if len(names) > len(visible_names):
            visible_names.append(f"+{len(names) - len(visible_names)} more")
        else:
            pass
        text = f"{label}: {', '.join(visible_names)}"

    return text


def build_block_type_description(block_type: BlockType) -> str:
    """Return the functional description of a native enum-backed block.

    :param block_type: Native block type.
    :return: Human-readable explanation of the block behavior.
    """
    if block_type == BlockType.FROM_GOTO:
        description: str = "Routes a signal between paired From and Goto connectors without a visible wire"
    elif block_type == BlockType.INPUT_CONN:
        description = "Connects bus measurements or external device variables to the dynamic model"
    elif block_type == BlockType.OUTPUT_CONN:
        description = "Maps a dynamic-model signal to an external device variable"
    elif block_type == BlockType.GENERIC:
        description = "Empty dynamic-model template for building a custom device or control"
    elif block_type == BlockType.PLL_TRANSFORM_RMS:
        description = "Phase-locked loop and reference-frame transform that derives d-q voltage and frequency"
    elif block_type == BlockType.VSC_PLL_RMS:
        description = "Explicit-state PI phase-locked loop that tracks AC-grid angle and frequency"
    elif block_type == BlockType.GOV_RMS:
        description = "Generator turbine-governor RMS control that regulates mechanical power from speed error"
    elif block_type == BlockType.EXCITER_RMS:
        description = "Generator excitation-system RMS control that regulates terminal voltage"
    elif block_type == BlockType.STAB_RMS:
        description = "Generator power-system stabilizer RMS control for damping electromechanical oscillations"
    elif block_type == BlockType.PI_POWER_CONTROLLER:
        description = "VSC outer-loop PI controller that converts active and reactive power errors to current references"
    elif block_type == BlockType.VSC_ACTIVE_CONTROL_RMS:
        description = "VSC outer-loop PI control of DC voltage or active power, producing a q-axis current reference"
    elif block_type == BlockType.VSC_REACTIVE_CONTROL_RMS:
        description = "VSC outer-loop PI control of AC voltage or reactive power, producing a d-axis current reference"
    elif block_type == BlockType.PI_CURRENT_CONTROLLER:
        description = "VSC inner-loop PI controller that converts current error to a converter voltage command"
    elif block_type == BlockType.VSC_VD_HAT_RMS:
        description = "VSC d-axis inner current PI controller producing the d-axis voltage correction"
    elif block_type == BlockType.VSC_VQ_HAT_RMS:
        description = "VSC q-axis inner current PI controller producing the q-axis voltage correction"
    elif block_type == BlockType.VSC_ELECTRICAL_RMS:
        description = "VSC electrical RMS equations for d-q current dynamics and AC-terminal power"
    elif block_type == BlockType.VSC_DC_LINK_RMS:
        description = "VSC DC-link capacitor dynamics with DC voltage and terminal-power constraints"
    elif block_type == BlockType.VSC_CURRENT_LIMITER_RMS:
        description = "VSC current-reference magnitude limiter with q-axis priority"
    elif block_type == BlockType.GOV_EMT:
        description = "Generator turbine-governor EMT control that regulates mechanical power from speed error"
    elif block_type == BlockType.EXCITER_EMT:
        description = "Generator excitation-system EMT control that regulates field voltage"
    elif block_type == BlockType.STAB_EMT:
        description = "Generator stabilizer EMT control for damping electromechanical oscillations"
    elif block_type == BlockType.RLC_COMBO_EMT:
        description = "Configurable three-phase resistor-inductor-capacitor branch for an EMT network"
    elif block_type == BlockType.FAULT_EMT:
        description = "Configurable EMT short-circuit fault with selectable phases and ground connection"
    elif block_type == BlockType.SWITCH_EMT:
        description = "Controlled ideal electrical switch for opening or closing an EMT branch"
    elif block_type == BlockType.INTERCONNECTION:
        description = "Exposes selected variables from another device dynamic model"
    elif block_type.name.startswith("MEASUREMENTS_"):
        description = f"Exposes the {block_type.value} network measurement as a dynamic-model signal"
    elif block_type == BlockType.CONST:
        description = "Produces a configurable constant signal"
    elif block_type == BlockType.GAIN:
        description = "Multiplies an input signal by a configurable gain"
    elif block_type == BlockType.MIN:
        description = "Outputs the smallest input signal; the number of inputs is configurable"
    elif block_type == BlockType.MAX:
        description = "Outputs the largest input signal; the number of inputs is configurable"
    elif block_type == BlockType.SUM:
        description = "Adds or subtracts a configurable set of input signals"
    elif block_type == BlockType.DIVIDE:
        description = "Divides one input signal by another"
    elif block_type == BlockType.PRODUCT:
        description = "Multiplies a configurable set of input signals"
    elif block_type == BlockType.ABS:
        description = "Returns the absolute value or magnitude of the input signal"
    elif block_type == BlockType.INTEGRATOR:
        description = (
            "Integrates the input with configurable scaling, hold, reset, "
            "and output-saturation structure"
        )
    elif block_type == BlockType.STARTUP_FREEZE_INTEGRATOR:
        description = (
            "Integrates the input after a configurable startup freeze interval, "
            "with optional scaling, hold, reset, and output saturation"
        )
    elif block_type == BlockType.DERIVATIVE:
        description = (
            "Applies a configurable first- or second-order filtered derivative "
            "with selectable numerator scaling and non-positive-time behavior"
        )
    elif block_type == BlockType.POWER:
        description = "Raises the input signal to a configurable power"
    elif block_type in tuple((BlockType.SIN, BlockType.COS, BlockType.TAN)):
        description = f"Applies the {block_type.value} trigonometric function to the input signal"
    elif block_type == BlockType.EXP:
        description = "Applies the natural exponential function to the input signal"
    elif block_type == BlockType.LOG:
        description = "Applies the natural logarithm to the input signal"
    elif block_type == BlockType.LOG10:
        description = "Applies the base-10 logarithm to the input signal"
    elif block_type == BlockType.SQRT:
        description = "Returns the square root of the input signal"
    elif block_type in tuple((BlockType.ASIN, BlockType.ACOS, BlockType.ATAN)):
        description = f"Applies the inverse {block_type.value} trigonometric function to the input signal"
    elif block_type in tuple((BlockType.SINH, BlockType.COSH, BlockType.TANH)):
        description = f"Applies the {block_type.value} hyperbolic function to the input signal"
    elif block_type == BlockType.REAL:
        description = "Extracts the real component of a complex input signal"
    elif block_type == BlockType.IMAG:
        description = "Extracts the imaginary component of a complex input signal"
    elif block_type == BlockType.CONJ:
        description = "Returns the complex conjugate of the input signal"
    elif block_type == BlockType.ANGLE:
        description = "Returns the phase angle of a complex input signal"
    elif block_type == BlockType.INVERSE_LOOKUP_ARRAY:
        description = "Computes the input corresponding to a tabulated output using linear interpolation"
    elif block_type == BlockType.LOOKUP_ARRAY_LINEAR:
        description = "Interpolates a configurable one-dimensional table linearly, with clipping or extrapolation"
    elif block_type == BlockType.LOOKUP_ARRAY_LINEAR_VARIABLE:
        description = (
            "Linearly interpolates a table whose ordered x/y points are signal inputs; "
            "the point count and clipping rule are configurable"
        )
    elif block_type == BlockType.LOOKUP_ARRAY_SPLINE:
        description = "Interpolates a configurable one-dimensional table with a clipped natural cubic spline"
    elif block_type == BlockType.LOOKUP_MATRIX_LINEAR:
        description = "Interpolates a configurable two-dimensional table bilinearly"
    elif block_type == BlockType.LOOKUP_MATRIX_SPLINE:
        description = "Interpolates a configurable two-dimensional table with a clipped natural cubic spline"
    elif block_type.name.endswith("_RMS"):
        description = f"RMS dynamic-model component implementing {block_type.value} behavior"
    elif block_type.name.endswith("_EMT"):
        description = f"EMT dynamic-model component implementing {block_type.value} behavior"
    else:
        description = f"Dynamic-model component implementing {block_type.value} behavior"

    return description


def set_library_branch_icon(item: QtGui.QStandardItem, branch_label: str) -> None:
    """Apply the best matching icon for one library branch row.

    :param item: Branch item whose icon is updated.
    :param branch_label: Branch text shown in the library tree.
    :return: None.
    """
    icon_path: str | None = device_type_icons.get(branch_label, None)
    if icon_path is None:
        if branch_label == "Basic":
            icon_path = ":/Icons/icons/Catalogue.png"
        elif branch_label == "Tools":
            icon_path = ":/Icons/icons/gear.png"
        elif branch_label == "Procedural logic":
            icon_path = ":/Icons/icons/dyn_edit.png"
        elif branch_label == "International standards":
            icon_path = ":/Icons/icons/dyn.png"
        elif branch_label == "Native":
            icon_path = ":/Icons/icons/dyn_gray.png"
        elif branch_label == "Faults":
            icon_path = ":/Icons/icons/short_circuit_plus.png"
        elif branch_label == "Devices":
            icon_path = ":/Icons/icons/dyn_gray.png"
        elif branch_label == "Controls":
            icon_path = ":/Icons/icons/control_pc.png"
        else:
            icon_path = ":/Icons/icons/tree.png"
    else:
        pass
    item.setIcon(QtGui.QIcon(icon_path))


def set_library_item_icon(item: QtGui.QStandardItem, payload: object) -> None:
    """
    Apply the best matching icon for one draggable library leaf.

    :param item: Tree item whose icon is updated.
    :param payload: Typed payload represented by the item.
    :return: None.
    """

    if isinstance(payload, IntegratorPresetDescriptor):
        # Every configurable-integrator preset belongs to the same Library
        # family, so all variants intentionally share the user-provided base
        # integrator artwork.
        integrator_icon: QtGui.QIcon = QtGui.QIcon(":/Icons/icons/integrator.svg")
        if integrator_icon.isNull():
            item.setIcon(QtGui.QIcon(":/Icons/icons/dyn_gray.png"))
        else:
            item.setIcon(integrator_icon)
    elif isinstance(payload, DerivativePresetDescriptor):
        # All derivative presets intentionally share one family icon, just as
        # the integrator presets do. The generic dynamic-block icon remains a
        # defensive fallback if the compiled Qt resource is unavailable.
        derivative_icon: QtGui.QIcon = QtGui.QIcon(":/Icons/icons/derivative.svg")
        if derivative_icon.isNull():
            item.setIcon(QtGui.QIcon(":/Icons/icons/dyn_gray.png"))
        else:
            item.setIcon(derivative_icon)
    elif isinstance(payload, FmuTemplate):
        item.setIcon(QtGui.QIcon(device_type_icons[DeviceType.FmuTemplateDevice.value]))
    elif isinstance(payload, RmsModelTemplate):
        item.setIcon(QtGui.QIcon(device_type_icons[DeviceType.RmsModelTemplateDevice.value]))
    elif isinstance(payload, InternationalStandardTemplateDescriptor):
        item.setIcon(QtGui.QIcon(device_type_icons[DeviceType.RmsModelTemplateDevice.value]))
    elif isinstance(payload, LibraryDeviceTemplateSpec):
        icon_path: str | None = device_type_icons.get(payload.device_type.value, None)
        if icon_path is not None:
            item.setIcon(QtGui.QIcon(icon_path))
        elif payload.mode == DynamicSimulationMode.RMS:
            item.setIcon(QtGui.QIcon(device_type_icons[DeviceType.RmsModelTemplateDevice.value]))
        else:
            item.setIcon(QtGui.QIcon(device_type_icons[DeviceType.EmtModelTemplateDevice.value]))
    elif isinstance(
            payload,
            (
                EmtModelTemplate,
                BasicBlockTemplateDescriptor,
                ExactMathematicalBlockDescriptor,
                ProceduralBlockTemplateDescriptor,
            ),
    ):
        item.setIcon(QtGui.QIcon(device_type_icons[DeviceType.EmtModelTemplateDevice.value]))
    elif isinstance(payload, BlockType):
        if payload == BlockType.FROM_GOTO:
            item.setIcon(QtGui.QIcon(":/Icons/icons/tree.png"))
        elif payload in (BlockType.INPUT_CONN, BlockType.INTERCONNECTION) or payload.name.startswith("MEASUREMENTS_"):
            item.setIcon(QtGui.QIcon(":/Icons/icons/measurement.png"))
        elif payload == BlockType.SUM:
            item.setIcon(QtGui.QIcon(":/Icons/icons/plus.png"))
        elif payload == BlockType.PRODUCT:
            item.setIcon(QtGui.QIcon(":/Icons/icons/multiply.png"))
        elif payload == BlockType.DIVIDE:
            item.setIcon(QtGui.QIcon(":/Icons/icons/divide.png"))
        elif payload.name.endswith("_EMT"):
            item.setIcon(QtGui.QIcon(":/Icons/icons/dyn_emt.png"))
        elif payload.name.endswith("_RMS"):
            item.setIcon(QtGui.QIcon(":/Icons/icons/dyn.png"))
        else:
            item.setIcon(QtGui.QIcon(":/Icons/icons/dyn_gray.png"))
    else:
        pass
