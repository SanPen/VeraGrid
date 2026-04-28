# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.001--.0-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Static EMT API-object parameter mapping.

This module contains the static-device to EMT-parameter assignment layer used
by ``EmtProblemDae``. The contract is intentionally narrow:

* ``Block.api_obj_mapping`` maps ``ParamPowerFlowRefferenceType`` keys to
  constant symbolic EMT parameters.
* Only values that come from the static grid device, or from static network
  bases such as ``Sbase`` and ``fBase``, are assigned here.
* ``Block.event_dict`` is never written by this module. Runtime/event
  parameters belong to explicit/native initialization and runtime event logic.

The EMT problem parser should call ``assign_static_api_object_mapping_for_device``
after processing each device block. The EMT model template chooses which static
values it consumes by exposing only the desired enum keys in ``api_obj_mapping``.
"""

from __future__ import annotations

from typing import Any, List, Tuple

import numpy as np

from VeraGridEngine.Devices import MultiCircuit
from VeraGridEngine.Devices.Branches.dc_line import DcLine
from VeraGridEngine.Devices.Branches.transformer import Transformer2W
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import (
    ConverterControlType,
    DeviceType,
    ParamPowerFlowRefferenceType,
    WindingType,
)


def to_static_mapping_const(value: Any) -> Const:
    """
    Convert a static numerical mapping value into a symbolic constant.

    :param value: Numerical value or an already-created ``Const``.
    :return: Constant symbolic expression used by EMT parameters.
    """
    out: Const

    if isinstance(value, Const):
        # Existing constants are preserved so callers can pre-build symbolic
        # constants without being wrapped a second time.
        out = value
    else:
        # Static API-object values are scalar real constants. The explicit float
        # conversion keeps parameter values homogeneous in the EMT parameter map.
        out = Const(float(value))

    return out


def add_static_mapping_warning(
        logger: Logger | None,
        device_name: str,
        message: str,
        value: str,
        expected_value: str,
        device_property: str,
) -> None:
    """
    Add one diagnostic warning for a static mapping issue.

    :param logger: Optional EMT logger.
    :param device_name: Device name used in diagnostics.
    :param message: Warning message.
    :param value: Actual problematic value.
    :param expected_value: Expected value or condition.
    :param device_property: Device property involved in the warning.
    :return: None.
    """
    if logger is None:
        # The mapper can be used in small unit tests without a full EMT logger.
        # In that case, invalid optional mappings are skipped silently.
        pass
    else:
        logger.add_warning(
            msg=message,
            device=device_name,
            value=value,
            expected_value=expected_value,
            device_class="EMT",
            device_property=device_property,
        )


def assign_api_mapping_value_if_present(
        mdl: Block,
        key: ParamPowerFlowRefferenceType,
        value: Any,
        logger: Logger | None,
        device_name: str,
) -> bool:
    """
    Assign one static API-object value to ``mdl.parameters`` if exposed.

    This function is the only low-level writer used by this module. It never
    writes into ``mdl.event_dict`` because event parameters are model-dynamic
    or runtime parameters initialized by the explicit/native initialization path.

    :param mdl: EMT symbolic block receiving the static parameter.
    :param key: Static API-object reference key.
    :param value: Static numerical value to assign.
    :param logger: Optional logger used to report invalid mapping contracts.
    :param device_name: Device name used in diagnostics.
    :return: ``True`` if the value was assigned, ``False`` otherwise.
    """
    assigned: bool = False
    api_obj_mapping: Any = mdl.api_obj_mapping

    if isinstance(api_obj_mapping, dict):
        # The mapping is optional: a model receives only the static parameters it
        # explicitly requests by exposing the enum key.
        target: Any | None = api_obj_mapping.get(key, None)

        if target is None:
            assigned = False
        else:
            event_dict: Any = mdl.event_dict

            if isinstance(event_dict, dict):
                if target in event_dict:
                    # A target present in event_dict means the model declared a
                    # runtime parameter as a static API-object parameter. That is
                    # a contract error, so this path refuses to assign it.
                    add_static_mapping_warning(
                        logger=logger,
                        device_name=device_name,
                        message="Static api_obj_mapping points to an event_dict parameter.",
                        value=str(key),
                        expected_value="api_obj_mapping target must be a constant parameter",
                        device_property="api_obj_mapping",
                    )
                    assigned = False
                else:
                    # The static mapping declares the symbolic parameter target.
                    # The target does not need to pre-exist in mdl.parameters.
                    mdl.parameters[target] = to_static_mapping_const(value)
                    assigned = True
            else:
                # Blocks normally expose event_dict as a dictionary. If they do
                # not, the static parameter assignment can still proceed because
                # there is no runtime container to conflict with.
                mdl.parameters[target] = to_static_mapping_const(value)
                assigned = True
    else:
        assigned = False

    return assigned


def api_mapping_has_any_key(
        mdl: Block,
        keys: List[ParamPowerFlowRefferenceType],
) -> bool:
    """
    Return whether the block exposes at least one of the provided static keys.

    :param mdl: EMT symbolic block.
    :param keys: API-object enum keys to test.
    :return: ``True`` if any key is present in ``mdl.api_obj_mapping``.
    """
    has_key: bool = False
    api_obj_mapping: Any = mdl.api_obj_mapping

    if isinstance(api_obj_mapping, dict):
        key_index: int = 0

        while key_index < len(keys):
            key: ParamPowerFlowRefferenceType = keys[key_index]

            if key in api_obj_mapping:
                # Do not break the loop: keeping the loop explicit avoids control
                # flow surprises and follows the local style constraints.
                has_key = True
            else:
                pass

            key_index += 1
    else:
        has_key = False

    return has_key


def assign_static_api_object_mapping_for_device(
        grid: MultiCircuit,
        device: Any,
        mdl: Block,
        logger: Logger | None,
) -> None:
    """
    Assign static API-object parameters for one EMT device block.

    The dispatcher is generic with respect to EMT templates. A template receives
    values only for the ``ParamPowerFlowRefferenceType`` keys it exposes in
    ``mdl.api_obj_mapping``. Adding a new EMT model for an already-supported
    ``DeviceType`` should not require modifying ``EmtProblemDae``.

    :param grid: Static network model containing base values.
    :param device: Static grid device owning the EMT model.
    :param mdl: EMT block receiving static parameter constants.
    :param logger: Optional logger used for diagnostics.
    :return: None.
    """
    api_obj_mapping: Any = mdl.api_obj_mapping

    if isinstance(api_obj_mapping, dict):
        if len(api_obj_mapping) == 0:
            pass
        else:
            # The dispatch is based on the static device type, not on the EMT
            # template name. The template only selects a subset of keys.
            device_type: DeviceType = device.device_type

            if device_type == DeviceType.LoadDevice:
                assign_load_static_api_mapping(
                    grid=grid,
                    load=device,
                    mdl=mdl,
                    logger=logger,
                )
            elif device_type == DeviceType.GeneratorDevice:
                assign_generator_static_api_mapping(
                    grid=grid,
                    generator=device,
                    mdl=mdl,
                    logger=logger,
                )
            elif device_type == DeviceType.VscDevice:
                assign_vsc_static_api_mapping(
                    grid=grid,
                    vsc=device,
                    mdl=mdl,
                    logger=logger,
                )
            elif device_type == DeviceType.DCLineDevice:
                if isinstance(device, DcLine):
                    assign_dc_line_static_api_mapping(
                        dc_line=device,
                        mdl=mdl,
                        logger=logger,
                    )
                else:
                    add_static_mapping_warning(
                        logger=logger,
                        device_name=str(device.name),
                        message="DCLineDevice static mapping skipped because the object type is not DcLine.",
                        value=str(device_type),
                        expected_value="DcLine instance",
                        device_property="device_type",
                    )
            elif device_type == DeviceType.Transformer2WDevice:
                if isinstance(device, Transformer2W):
                    assign_transformer2w_static_api_mapping(
                        grid=grid,
                        transformer=device,
                        mdl=mdl,
                        logger=logger,
                    )
                else:
                    add_static_mapping_warning(
                        logger=logger,
                        device_name=str(device.name),
                        message="Transformer2WDevice static mapping skipped because the object type is not Transformer2W.",
                        value=str(device_type),
                        expected_value="Transformer2W instance",
                        device_property="device_type",
                    )
            elif device_type == DeviceType.LineDevice:
                assign_line_static_api_mapping_if_needed(
                    grid=grid,
                    line=device,
                    mdl=mdl,
                    logger=logger,
                )
            else:
                # Compatibility fallback: older branch-like models may expose
                # line matrix keys even if their device_type is more generic.
                # The fallback activates only when the EMT template explicitly
                # requests line-matrix keys.
                if api_mapping_has_any_key(mdl=mdl, keys=get_all_line_matrix_keys()):
                    assign_line_static_api_mapping_if_needed(
                        grid=grid,
                        line=device,
                        mdl=mdl,
                        logger=logger,
                    )
                else:
                    pass
    else:
        pass


def assign_load_static_api_mapping(
        grid: MultiCircuit,
        load: Any,
        mdl: Block,
        logger: Logger | None,
) -> None:
    """
    Assign static load parameters exposed by ``mdl.api_obj_mapping``.

    :param grid: Static network model.
    :param load: Load device.
    :param mdl: Load EMT block.
    :param logger: Optional logger.
    :return: None.
    """
    device_name: str = str(load.name)
    sbase: float = float(grid.Sbase)

    if load.bus.is_dc:
        # DC loads use the historical EMT convention: explicit conductance is
        # used when available; otherwise active power is represented as an
        # equivalent conductance on the DC base.
        dc_p_value: float = float(load.P) / sbase
        dc_g_value: float = float(load.G) / sbase

        if dc_g_value == 0.0:
            dc_p_value = 0.0
            dc_g_value = float(load.P) / sbase
        else:
            pass

        assign_api_mapping_value_if_present(
            mdl=mdl,
            key=ParamPowerFlowRefferenceType.Pl0,
            value=dc_p_value,
            logger=logger,
            device_name=device_name,
        )
        assign_api_mapping_value_if_present(
            mdl=mdl,
            key=ParamPowerFlowRefferenceType.g,
            value=dc_g_value,
            logger=logger,
            device_name=device_name,
        )
    else:
        omega_base: float = 2.0 * np.pi * float(grid.fBase)
        p_values: np.ndarray = np.zeros(3, dtype=np.float64)
        q_values: np.ndarray = np.zeros(3, dtype=np.float64)

        # The static load stores phase values in ABC order; the EMT load
        # parameter contract exposes the same ABC order without a neutral power.
        p_values[0] = float(load.Pa) / sbase
        p_values[1] = float(load.Pb) / sbase
        p_values[2] = float(load.Pc) / sbase
        q_values[0] = float(load.Qa) / sbase
        q_values[1] = float(load.Qb) / sbase
        q_values[2] = float(load.Qc) / sbase

        p_keys: List[ParamPowerFlowRefferenceType] = list([
            ParamPowerFlowRefferenceType.Pl0_A,
            ParamPowerFlowRefferenceType.Pl0_B,
            ParamPowerFlowRefferenceType.Pl0_C,
        ])
        q_keys: List[ParamPowerFlowRefferenceType] = list([
            ParamPowerFlowRefferenceType.Ql0_A,
            ParamPowerFlowRefferenceType.Ql0_B,
            ParamPowerFlowRefferenceType.Ql0_C,
        ])

        phase_index: int = 0
        while phase_index < 3:
            assign_api_mapping_value_if_present(
                mdl=mdl,
                key=p_keys[phase_index],
                value=float(p_values[phase_index]),
                logger=logger,
                device_name=device_name,
            )
            assign_api_mapping_value_if_present(
                mdl=mdl,
                key=q_keys[phase_index],
                value=float(q_values[phase_index]),
                logger=logger,
                device_name=device_name,
            )
            phase_index += 1

        assign_api_mapping_value_if_present(
            mdl=mdl,
            key=ParamPowerFlowRefferenceType.omega_base,
            value=omega_base,
            logger=logger,
            device_name=device_name,
        )


def assign_generator_static_api_mapping(
        grid: MultiCircuit,
        generator: Any,
        mdl: Block,
        logger: Logger | None,
) -> None:
    """
    Assign static generator parameters exposed by ``mdl.api_obj_mapping``.

    :param grid: Static network model.
    :param generator: Generator device.
    :param mdl: Generator EMT block.
    :param logger: Optional logger.
    :return: None.
    """
    device_name: str = str(generator.name)
    omega_base: float = 2.0 * np.pi * float(grid.fBase)

    # These quantities are static generator object data or system base data.
    # PF-derived sharing targets are intentionally handled outside this module.
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.omega_base,
        value=omega_base,
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.R1,
        value=float(generator.R1),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.X1,
        value=float(generator.X1),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.X0,
        value=float(generator.X0),
        logger=logger,
        device_name=device_name,
    )


def converter_control_code(control_tpe: ConverterControlType | None) -> float:
    """
    Convert a static VSC control enum to the EMT template numerical code.

    :param control_tpe: Converter control enum or ``None``.
    :return: Numerical control code used by existing EMT templates.
    """
    code: float

    if control_tpe is None:
        code = 0.0
    elif control_tpe == ConverterControlType.Vm_dc:
        code = 1.0
    elif control_tpe == ConverterControlType.Vm_ac:
        code = 2.0
    elif control_tpe == ConverterControlType.Va_ac:
        code = 3.0
    elif control_tpe == ConverterControlType.Qac:
        code = 4.0
    elif control_tpe == ConverterControlType.Pdc:
        code = 5.0
    elif control_tpe == ConverterControlType.Pac:
        code = 6.0
    elif control_tpe == ConverterControlType.Pdc_angle_droop:
        code = 7.0
    elif control_tpe == ConverterControlType.Imax:
        code = 8.0
    else:
        code = 0.0

    return code


def assign_vsc_static_api_mapping(
        grid: MultiCircuit,
        vsc: Any,
        mdl: Block,
        logger: Logger | None,
) -> None:
    """
    Assign static VSC parameters exposed by ``mdl.api_obj_mapping``.

    PF-derived quantities such as converter initial active power or converter
    losses are intentionally not assigned here. They are initialization data, not
    static API-object data.

    :param grid: Static network model.
    :param vsc: VSC device.
    :param mdl: VSC EMT block.
    :param logger: Optional logger.
    :return: None.
    """
    device_name: str = str(vsc.name)
    omega_base: float = 2.0 * np.pi * float(grid.fBase)

    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.Sbase,
        value=float(grid.Sbase),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.omega_base,
        value=omega_base,
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.converter_control_mode_1,
        value=converter_control_code(vsc.control1),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.converter_control_mode_2,
        value=converter_control_code(vsc.control2),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.converter_control_target_1,
        value=float(vsc.control1_val),
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.converter_control_target_2,
        value=float(vsc.control2_val),
        logger=logger,
        device_name=device_name,
    )


def assign_dc_line_static_api_mapping(
        dc_line: DcLine,
        mdl: Block,
        logger: Logger | None,
) -> None:
    """
    Assign static DC-line parameters exposed by ``mdl.api_obj_mapping``.

    :param dc_line: DC line device.
    :param mdl: DC line EMT block.
    :param logger: Optional logger.
    :return: None.
    """
    device_name: str = str(dc_line.name)
    eps_value: float = 1.0e-12
    resistance_value: float = float(dc_line.R_corrected)
    conductance_value: float = 1.0 / max(abs(resistance_value), eps_value)

    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.g,
        value=conductance_value,
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.b,
        value=0.0,
        logger=logger,
        device_name=device_name,
    )
    assign_api_mapping_value_if_present(
        mdl=mdl,
        key=ParamPowerFlowRefferenceType.bsh,
        value=0.0,
        logger=logger,
        device_name=device_name,
    )


def xfmr_connection_matrix(winding_tpe: WindingType) -> np.ndarray:
    """
    Return the 3x3 transformer winding connection matrix.

    :param winding_tpe: Transformer winding connection type.
    :return: 3x3 winding connection matrix.
    """
    matrix: np.ndarray

    if winding_tpe in (
            WindingType.GroundedStar,
            WindingType.NeutralStar,
            WindingType.FloatingStar,
    ):
        matrix = np.eye(3, dtype=float)
    else:
        if winding_tpe == WindingType.Delta:
            matrix = np.array(
                [
                    [1.0, 0.0, -1.0],
                    [-1.0, 1.0, 0.0],
                    [0.0, -1.0, 1.0],
                ],
                dtype=float,
            ) / np.sqrt(3.0)
        else:
            matrix = np.eye(3, dtype=float)

    return matrix


def xfmr_phase_permutation_matrix(clock: int) -> np.ndarray:
    """
    Return the transformer phase permutation matrix from vector-group clock.

    :param clock: Transformer vector-group clock number.
    :return: 3x3 phase permutation matrix.
    """
    matrix: np.ndarray
    shift: int = (int(clock) // 4) % 3

    if shift == 0:
        matrix = np.eye(3, dtype=float)
    else:
        if shift == 1:
            matrix = np.array(
                [
                    [0.0, 1.0, 0.0],
                    [0.0, 0.0, 1.0],
                    [1.0, 0.0, 0.0],
                ],
                dtype=float,
            )
        else:
            matrix = np.array(
                [
                    [0.0, 0.0, 1.0],
                    [1.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0],
                ],
                dtype=float,
            )

    return matrix


def assign_transformer2w_static_api_mapping(
        grid: MultiCircuit,
        transformer: Transformer2W,
        mdl: Block,
        logger: Logger | None,
) -> None:
    """
    Assign static Transformer2W parameters exposed by ``mdl.api_obj_mapping``.

    :param grid: Static network model.
    :param transformer: Two-winding transformer device.
    :param mdl: Transformer EMT block.
    :param logger: Optional logger.
    :return: None.
    """
    classical_specific_keys: List[ParamPowerFlowRefferenceType] = get_transformer_classical_specific_keys()
    has_classical_specific_mapping: bool = api_mapping_has_any_key(mdl=mdl, keys=classical_specific_keys)

    # Direct/static transformer data are assigned first. If the classical model
    # is detected, the shared tap-ratio key is left for the classical path because
    # its current historical semantics are total nominal ratio times tap ratio.
    assign_transformer2w_direct_static_api_mapping(
        grid=grid,
        transformer=transformer,
        mdl=mdl,
        logger=logger,
        assign_tap_ratio=not has_classical_specific_mapping,
    )
    assign_transformer2w_classical_compatibility_api_mapping(
        grid=grid,
        transformer=transformer,
        mdl=mdl,
        logger=logger,
        has_classical_specific_mapping=has_classical_specific_mapping,
    )


def get_transformer_direct_static_keys() -> List[ParamPowerFlowRefferenceType]:
    """
    Return direct/static Transformer2W API-object keys.

    :return: Direct/static transformer mapping keys.
    """
    keys: List[ParamPowerFlowRefferenceType] = list([
        ParamPowerFlowRefferenceType.omega_base,
        ParamPowerFlowRefferenceType.transformer_rated_power_mva,
        ParamPowerFlowRefferenceType.transformer_open_circuit_current_pct,
        ParamPowerFlowRefferenceType.transformer_open_circuit_loss_kw,
        ParamPowerFlowRefferenceType.transformer_short_circuit_voltage_pct,
        ParamPowerFlowRefferenceType.transformer_short_circuit_loss_kw,
        ParamPowerFlowRefferenceType.transformer_tap_ratio,
        ParamPowerFlowRefferenceType.transformer_from_connection_aa,
        ParamPowerFlowRefferenceType.transformer_from_connection_ab,
        ParamPowerFlowRefferenceType.transformer_from_connection_ac,
        ParamPowerFlowRefferenceType.transformer_from_connection_ba,
        ParamPowerFlowRefferenceType.transformer_from_connection_bb,
        ParamPowerFlowRefferenceType.transformer_from_connection_bc,
        ParamPowerFlowRefferenceType.transformer_from_connection_ca,
        ParamPowerFlowRefferenceType.transformer_from_connection_cb,
        ParamPowerFlowRefferenceType.transformer_from_connection_cc,
        ParamPowerFlowRefferenceType.transformer_to_connection_aa,
        ParamPowerFlowRefferenceType.transformer_to_connection_ab,
        ParamPowerFlowRefferenceType.transformer_to_connection_ac,
        ParamPowerFlowRefferenceType.transformer_to_connection_ba,
        ParamPowerFlowRefferenceType.transformer_to_connection_bb,
        ParamPowerFlowRefferenceType.transformer_to_connection_bc,
        ParamPowerFlowRefferenceType.transformer_to_connection_ca,
        ParamPowerFlowRefferenceType.transformer_to_connection_cb,
        ParamPowerFlowRefferenceType.transformer_to_connection_cc,
    ])

    return keys


def assign_transformer2w_direct_static_api_mapping(
        grid: MultiCircuit,
        transformer: Transformer2W,
        mdl: Block,
        logger: Logger | None,
        assign_tap_ratio: bool,
) -> None:
    """
    Assign direct/static Transformer2W API-object parameters.

    :param grid: Static network model.
    :param transformer: Two-winding transformer device.
    :param mdl: Transformer EMT block.
    :param logger: Optional logger.
    :param assign_tap_ratio: Whether the shared tap-ratio key belongs to this path.
    :return: None.
    """
    direct_keys: List[ParamPowerFlowRefferenceType] = get_transformer_direct_static_keys()

    if api_mapping_has_any_key(mdl=mdl, keys=direct_keys):
        device_name: str = str(transformer.name)
        eps_value: float = 1.0e-12
        omega_base: float = 2.0 * np.pi * float(grid.fBase)

        sn_value: float = max(float(transformer.Sn), 1.0e-9)
        pcu_kw_value: float = max(float(transformer.Pcu), 0.0)
        pfe_kw_value: float = max(float(transformer.Pfe), 0.0)
        i0_pct_value: float = max(float(transformer.I0), 0.0)

        tap_module_value: float = float(transformer.tap_module)
        if abs(tap_module_value) <= eps_value:
            tap_module_value = 1.0
        else:
            pass

        if float(transformer.Vsc) > 0.0:
            vsc_pct_value: float = float(transformer.Vsc)
        else:
            vsc_pct_value = 100.0 * np.sqrt(
                max(
                    float(transformer.R) * float(transformer.R)
                    + float(transformer.X) * float(transformer.X),
                    0.0,
                )
            )

        from_connection_matrix: np.ndarray = xfmr_connection_matrix(transformer.conn_f)
        to_connection_matrix: np.ndarray = xfmr_connection_matrix(transformer.conn_t)
        permutation_matrix: np.ndarray = xfmr_phase_permutation_matrix(int(transformer.vector_group_number))
        to_effective_connection_matrix: np.ndarray = permutation_matrix @ to_connection_matrix

        assign_api_mapping_value_if_present(
            mdl=mdl,
            key=ParamPowerFlowRefferenceType.omega_base,
            value=omega_base,
            logger=logger,
            device_name=device_name,
        )
        assign_api_mapping_value_if_present(
            mdl=mdl,
            key=ParamPowerFlowRefferenceType.transformer_rated_power_mva,
            value=sn_value,
            logger=logger,
            device_name=device_name,
        )
        assign_api_mapping_value_if_present(
            mdl=mdl,
            key=ParamPowerFlowRefferenceType.transformer_open_circuit_current_pct,
            value=i0_pct_value,
            logger=logger,
            device_name=device_name,
        )
        assign_api_mapping_value_if_present(
            mdl=mdl,
            key=ParamPowerFlowRefferenceType.transformer_open_circuit_loss_kw,
            value=pfe_kw_value,
            logger=logger,
            device_name=device_name,
        )
        assign_api_mapping_value_if_present(
            mdl=mdl,
            key=ParamPowerFlowRefferenceType.transformer_short_circuit_voltage_pct,
            value=vsc_pct_value,
            logger=logger,
            device_name=device_name,
        )
        assign_api_mapping_value_if_present(
            mdl=mdl,
            key=ParamPowerFlowRefferenceType.transformer_short_circuit_loss_kw,
            value=pcu_kw_value,
            logger=logger,
            device_name=device_name,
        )

        if assign_tap_ratio:
            assign_api_mapping_value_if_present(
                mdl=mdl,
                key=ParamPowerFlowRefferenceType.transformer_tap_ratio,
                value=tap_module_value,
                logger=logger,
                device_name=device_name,
            )
        else:
            pass

        assign_3x3_static_matrix(
            mdl=mdl,
            matrix=from_connection_matrix,
            keys=get_transformer_from_connection_keys(),
            logger=logger,
            device_name=device_name,
        )
        assign_3x3_static_matrix(
            mdl=mdl,
            matrix=to_effective_connection_matrix,
            keys=get_transformer_to_connection_keys(),
            logger=logger,
            device_name=device_name,
        )
    else:
        pass


def get_transformer_from_connection_keys() -> List[List[ParamPowerFlowRefferenceType]]:
    """
    Return 3x3 from-side transformer connection mapping keys.

    :return: Matrix of from-side API-object keys.
    """
    keys: List[List[ParamPowerFlowRefferenceType]] = list([
        list([
            ParamPowerFlowRefferenceType.transformer_from_connection_aa,
            ParamPowerFlowRefferenceType.transformer_from_connection_ab,
            ParamPowerFlowRefferenceType.transformer_from_connection_ac,
        ]),
        list([
            ParamPowerFlowRefferenceType.transformer_from_connection_ba,
            ParamPowerFlowRefferenceType.transformer_from_connection_bb,
            ParamPowerFlowRefferenceType.transformer_from_connection_bc,
        ]),
        list([
            ParamPowerFlowRefferenceType.transformer_from_connection_ca,
            ParamPowerFlowRefferenceType.transformer_from_connection_cb,
            ParamPowerFlowRefferenceType.transformer_from_connection_cc,
        ]),
    ])

    return keys


def get_transformer_to_connection_keys() -> List[List[ParamPowerFlowRefferenceType]]:
    """
    Return 3x3 to-side transformer connection mapping keys.

    :return: Matrix of to-side API-object keys.
    """
    keys: List[List[ParamPowerFlowRefferenceType]] = list([
        list([
            ParamPowerFlowRefferenceType.transformer_to_connection_aa,
            ParamPowerFlowRefferenceType.transformer_to_connection_ab,
            ParamPowerFlowRefferenceType.transformer_to_connection_ac,
        ]),
        list([
            ParamPowerFlowRefferenceType.transformer_to_connection_ba,
            ParamPowerFlowRefferenceType.transformer_to_connection_bb,
            ParamPowerFlowRefferenceType.transformer_to_connection_bc,
        ]),
        list([
            ParamPowerFlowRefferenceType.transformer_to_connection_ca,
            ParamPowerFlowRefferenceType.transformer_to_connection_cb,
            ParamPowerFlowRefferenceType.transformer_to_connection_cc,
        ]),
    ])

    return keys


def assign_3x3_static_matrix(
        mdl: Block,
        matrix: np.ndarray,
        keys: List[List[ParamPowerFlowRefferenceType]],
        logger: Logger | None,
        device_name: str,
) -> None:
    """
    Assign a 3x3 static matrix through a 3x3 API-object key matrix.

    :param mdl: EMT block.
    :param matrix: Numerical 3x3 matrix.
    :param keys: API-object key matrix.
    :param logger: Optional logger.
    :param device_name: Device name used in diagnostics.
    :return: None.
    """
    row_index: int = 0

    while row_index < 3:
        col_index: int = 0

        while col_index < 3:
            assign_api_mapping_value_if_present(
                mdl=mdl,
                key=keys[row_index][col_index],
                value=float(matrix[row_index, col_index]),
                logger=logger,
                device_name=device_name,
            )
            col_index += 1

        row_index += 1


def get_transformer_classical_specific_keys() -> List[ParamPowerFlowRefferenceType]:
    """
    Return classical transformer keys that identify the classical mapping path.

    :return: Classical transformer-specific API-object keys.
    """
    keys: List[ParamPowerFlowRefferenceType] = list([
        ParamPowerFlowRefferenceType.transformer_winding1_resistance_pu,
        ParamPowerFlowRefferenceType.transformer_winding2_resistance_pu,
        ParamPowerFlowRefferenceType.transformer_winding1_inductance_pu_s,
        ParamPowerFlowRefferenceType.transformer_winding2_inductance_pu_s,
        ParamPowerFlowRefferenceType.transformer_mutual_inductance_pu_s,
        ParamPowerFlowRefferenceType.transformer_magnetizing_conductance_pu,
    ])

    return keys


def assign_transformer2w_classical_compatibility_api_mapping(
        grid: MultiCircuit,
        transformer: Transformer2W,
        mdl: Block,
        logger: Logger | None,
        has_classical_specific_mapping: bool,
) -> None:
    """
    Assign compatibility parameters for the classical coupled-winding model.

    These values are derived from static ``Transformer2W`` data, but the
    derivation is tied to the historical coupled-winding EMT equivalent. They are
    kept here to preserve existing model compatibility while removing this logic
    from ``EmtProblemDae``.

    :param grid: Static network model.
    :param transformer: Two-winding transformer device.
    :param mdl: Transformer EMT block.
    :param logger: Optional logger.
    :param has_classical_specific_mapping: Whether the EMT model exposes classical keys.
    :return: None.
    """
    if has_classical_specific_mapping:
        device_name: str = str(transformer.name)
        eps_value: float = 1.0e-12
        omega_base: float = 2.0 * np.pi * float(grid.fBase)

        if transformer.HV is not None and float(transformer.HV) > eps_value:
            hv_nominal_kv: float = float(transformer.HV)
        else:
            hv_nominal_kv = float(transformer.bus_from.Vnom)

        if transformer.LV is not None and float(transformer.LV) > eps_value:
            lv_nominal_kv: float = float(transformer.LV)
        else:
            lv_nominal_kv = float(transformer.bus_to.Vnom)

        if abs(lv_nominal_kv) > eps_value:
            nominal_ratio: float = hv_nominal_kv / lv_nominal_kv
        else:
            nominal_ratio = 1.0

        tap_module_value: float = float(transformer.tap_module)
        if abs(tap_module_value) <= eps_value:
            tap_module_value = 1.0
        else:
            pass

        total_ratio: float = nominal_ratio * tap_module_value
        total_ratio_square: float = total_ratio * total_ratio

        tap_phase_value: float = float(transformer.tap_phase)
        if abs(tap_phase_value) > eps_value:
            add_static_mapping_warning(
                logger=logger,
                device_name=device_name,
                message="Classical transformer static mapping skipped because tap_phase is non-zero.",
                value=str(tap_phase_value),
                expected_value="tap_phase close to zero",
                device_property="tap_phase",
            )
        else:
            r_total: float = float(transformer.R)
            x_total: float = float(transformer.X)
            g_core: float = float(transformer.G)
            b_magnetizing: float = float(transformer.B)

            # The historical coupled-winding model splits short-circuit
            # resistance and leakage inductance equally between windings.
            r1_value: float = 0.5 * r_total
            r2_value: float = 0.5 * r_total / (total_ratio_square + eps_value)

            leakage_l_primary: float = 0.5 * x_total / (omega_base + eps_value)
            leakage_l_secondary: float = leakage_l_primary / (total_ratio_square + eps_value)

            # The magnetizing branch is approximated from the static shunt
            # susceptance when available. Otherwise a large finite inductance is
            # used to keep the inductance matrix well-conditioned.
            if abs(b_magnetizing) > eps_value:
                x_magnetizing: float = 1.0 / abs(b_magnetizing)
            else:
                x_magnetizing = max(1000.0, 100.0 * max(abs(x_total), 1.0))

            magnetizing_l_primary: float = x_magnetizing / (omega_base + eps_value)
            magnetizing_l_secondary: float = magnetizing_l_primary / (total_ratio_square + eps_value)
            mutual_inductance: float = magnetizing_l_primary / (total_ratio + eps_value)

            l1_value: float = leakage_l_primary + magnetizing_l_primary
            l2_value: float = leakage_l_secondary + magnetizing_l_secondary
            determinant_value: float = l1_value * l2_value - mutual_inductance * mutual_inductance

            if determinant_value <= eps_value:
                add_static_mapping_warning(
                    logger=logger,
                    device_name=device_name,
                    message="Classical transformer static mapping skipped because inductance matrix is non-physical.",
                    value=str(determinant_value),
                    expected_value="positive inductance matrix determinant",
                    device_property="classical_transformer_mapping",
                )
            else:
                assign_api_mapping_value_if_present(
                    mdl=mdl,
                    key=ParamPowerFlowRefferenceType.transformer_winding1_resistance_pu,
                    value=r1_value,
                    logger=logger,
                    device_name=device_name,
                )
                assign_api_mapping_value_if_present(
                    mdl=mdl,
                    key=ParamPowerFlowRefferenceType.transformer_winding2_resistance_pu,
                    value=r2_value,
                    logger=logger,
                    device_name=device_name,
                )
                assign_api_mapping_value_if_present(
                    mdl=mdl,
                    key=ParamPowerFlowRefferenceType.transformer_winding1_inductance_pu_s,
                    value=l1_value,
                    logger=logger,
                    device_name=device_name,
                )
                assign_api_mapping_value_if_present(
                    mdl=mdl,
                    key=ParamPowerFlowRefferenceType.transformer_winding2_inductance_pu_s,
                    value=l2_value,
                    logger=logger,
                    device_name=device_name,
                )
                assign_api_mapping_value_if_present(
                    mdl=mdl,
                    key=ParamPowerFlowRefferenceType.transformer_mutual_inductance_pu_s,
                    value=mutual_inductance,
                    logger=logger,
                    device_name=device_name,
                )
                assign_api_mapping_value_if_present(
                    mdl=mdl,
                    key=ParamPowerFlowRefferenceType.transformer_magnetizing_conductance_pu,
                    value=g_core,
                    logger=logger,
                    device_name=device_name,
                )
                assign_api_mapping_value_if_present(
                    mdl=mdl,
                    key=ParamPowerFlowRefferenceType.transformer_tap_ratio,
                    value=total_ratio,
                    logger=logger,
                    device_name=device_name,
                )
    else:
        pass


def get_line_r_keys() -> List[List[ParamPowerFlowRefferenceType]]:
    """
    Return the fixed 4x4 NABC resistance mapping keys.

    :return: Matrix of resistance API-object keys.
    """
    keys: List[List[ParamPowerFlowRefferenceType]] = list([
        list([
            ParamPowerFlowRefferenceType.Rnn,
            ParamPowerFlowRefferenceType.Rna,
            ParamPowerFlowRefferenceType.Rnb,
            ParamPowerFlowRefferenceType.Rnc,
        ]),
        list([
            ParamPowerFlowRefferenceType.Ran,
            ParamPowerFlowRefferenceType.Raa,
            ParamPowerFlowRefferenceType.Rab,
            ParamPowerFlowRefferenceType.Rac,
        ]),
        list([
            ParamPowerFlowRefferenceType.Rbn,
            ParamPowerFlowRefferenceType.Rba,
            ParamPowerFlowRefferenceType.Rbb,
            ParamPowerFlowRefferenceType.Rbc,
        ]),
        list([
            ParamPowerFlowRefferenceType.Rcn,
            ParamPowerFlowRefferenceType.Rca,
            ParamPowerFlowRefferenceType.Rcb,
            ParamPowerFlowRefferenceType.Rcc,
        ]),
    ])

    return keys


def get_line_linv_keys() -> List[List[ParamPowerFlowRefferenceType]]:
    """
    Return the fixed 4x4 NABC inverse-inductance mapping keys.

    :return: Matrix of inverse-inductance API-object keys.
    """
    keys: List[List[ParamPowerFlowRefferenceType]] = list([
        list([
            ParamPowerFlowRefferenceType.Linv_nn,
            ParamPowerFlowRefferenceType.Linv_na,
            ParamPowerFlowRefferenceType.Linv_nb,
            ParamPowerFlowRefferenceType.Linv_nc,
        ]),
        list([
            ParamPowerFlowRefferenceType.Linv_an,
            ParamPowerFlowRefferenceType.Linv_aa,
            ParamPowerFlowRefferenceType.Linv_ab,
            ParamPowerFlowRefferenceType.Linv_ac,
        ]),
        list([
            ParamPowerFlowRefferenceType.Linv_bn,
            ParamPowerFlowRefferenceType.Linv_ba,
            ParamPowerFlowRefferenceType.Linv_bb,
            ParamPowerFlowRefferenceType.Linv_bc,
        ]),
        list([
            ParamPowerFlowRefferenceType.Linv_cn,
            ParamPowerFlowRefferenceType.Linv_ca,
            ParamPowerFlowRefferenceType.Linv_cb,
            ParamPowerFlowRefferenceType.Linv_cc,
        ]),
    ])

    return keys


def get_line_c_keys() -> List[List[ParamPowerFlowRefferenceType]]:
    """
    Return the fixed 4x4 NABC capacitance mapping keys.

    :return: Matrix of capacitance API-object keys.
    """
    keys: List[List[ParamPowerFlowRefferenceType]] = list([
        list([
            ParamPowerFlowRefferenceType.Cnn,
            ParamPowerFlowRefferenceType.Cna,
            ParamPowerFlowRefferenceType.Cnb,
            ParamPowerFlowRefferenceType.Cnc,
        ]),
        list([
            ParamPowerFlowRefferenceType.Can,
            ParamPowerFlowRefferenceType.Caa,
            ParamPowerFlowRefferenceType.Cab,
            ParamPowerFlowRefferenceType.Cac,
        ]),
        list([
            ParamPowerFlowRefferenceType.Cbn,
            ParamPowerFlowRefferenceType.Cba,
            ParamPowerFlowRefferenceType.Cbb,
            ParamPowerFlowRefferenceType.Cbc,
        ]),
        list([
            ParamPowerFlowRefferenceType.Ccn,
            ParamPowerFlowRefferenceType.Cca,
            ParamPowerFlowRefferenceType.Ccb,
            ParamPowerFlowRefferenceType.Ccc,
        ]),
    ])

    return keys


def flatten_matrix_keys(
        matrix_keys: List[List[ParamPowerFlowRefferenceType]],
) -> List[ParamPowerFlowRefferenceType]:
    """
    Flatten a matrix of API-object enum keys.

    :param matrix_keys: Matrix of API-object keys.
    :return: Flat list of keys.
    """
    flat_keys: List[ParamPowerFlowRefferenceType] = list()
    row_index: int = 0

    while row_index < len(matrix_keys):
        col_index: int = 0

        while col_index < len(matrix_keys[row_index]):
            flat_keys.append(matrix_keys[row_index][col_index])
            col_index += 1

        row_index += 1

    return flat_keys


def get_all_line_matrix_keys() -> List[ParamPowerFlowRefferenceType]:
    """
    Return every line R, Linv and C API-object key.

    :return: Flat list of all line matrix mapping keys.
    """
    all_keys: List[ParamPowerFlowRefferenceType] = list()
    key_matrices: List[List[List[ParamPowerFlowRefferenceType]]] = list([
        get_line_r_keys(),
        get_line_linv_keys(),
        get_line_c_keys(),
    ])
    matrix_index: int = 0

    while matrix_index < len(key_matrices):
        flat_keys: List[ParamPowerFlowRefferenceType] = flatten_matrix_keys(key_matrices[matrix_index])
        key_index: int = 0

        while key_index < len(flat_keys):
            all_keys.append(flat_keys[key_index])
            key_index += 1

        matrix_index += 1

    return all_keys


def assign_line_static_api_mapping_if_needed(
        grid: MultiCircuit,
        line: Any,
        mdl: Block,
        logger: Logger | None,
) -> None:
    """
    Assign static line matrices if the EMT model exposes line matrix keys.

    :param grid: Static network model.
    :param line: Line-like branch device.
    :param mdl: Line EMT block.
    :param logger: Optional logger.
    :return: None.
    """
    line_keys: List[ParamPowerFlowRefferenceType] = get_all_line_matrix_keys()

    if api_mapping_has_any_key(mdl=mdl, keys=line_keys):
        assign_line_static_api_mapping(
            grid=grid,
            line=line,
            mdl=mdl,
            logger=logger,
        )
    else:
        pass


def get_line_active_global_indices(line: Any) -> List[int]:
    """
    Return active NABC phase indices for a line-like device.

    :param line: Line-like branch device.
    :return: Active indices in fixed NABC order.
    """
    phase_mask: List[bool] = list([
        bool(line.ys.phN),
        bool(line.ys.phA),
        bool(line.ys.phB),
        bool(line.ys.phC),
    ])
    active_indices: List[int] = list()
    phase_index: int = 0

    while phase_index < len(phase_mask):
        if phase_mask[phase_index]:
            active_indices.append(phase_index)
        else:
            pass

        phase_index += 1

    return active_indices


def build_uncoupled_line_static_matrices(
        line: Any,
        omega_base: float,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Build uncoupled fallback line matrices.

    This preserves the historical fallback used when no tower/template matrix is
    available. The historical code uses ``X = line.B`` and ``B = line.X`` in
    this fallback; that convention is preserved here to avoid a hidden numerical
    behavior change in the mapping refactor.

    :param line: Line-like branch device.
    :param omega_base: Base angular frequency.
    :return: Tuple ``(R, L, C)`` in EMT per-unit form.
    """
    r_value: float = float(line.R)

    # Historical fallback naming intentionally preserved. Review this separately
    # with numerical regression tests before changing it.
    x_value: float = float(line.B)
    b_value: float = float(line.X)

    r_full: np.ndarray = np.zeros((3, 3), dtype=np.float64)
    x_full: np.ndarray = np.zeros((3, 3), dtype=np.float64)
    bsh_full: np.ndarray = np.zeros((3, 3), dtype=np.float64)
    phase_index: int = 0

    while phase_index < 3:
        r_full[phase_index, phase_index] = r_value
        x_full[phase_index, phase_index] = x_value
        bsh_full[phase_index, phase_index] = b_value
        phase_index += 1

    l_full: np.ndarray = x_full / (omega_base + 1.0e-20)
    c_full: np.ndarray = (bsh_full / (omega_base + 1.0e-20)) / 2.0

    return r_full, l_full, c_full


def build_line_static_matrices(
        grid: MultiCircuit,
        line: Any,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Build line R, L and C matrices in EMT per-unit form.

    :param grid: Static network model.
    :param line: Line-like branch device.
    :return: Tuple ``(R, L, C)`` in reduced active-phase coordinates.
    """
    frequency_base: float = float(grid.fBase)
    omega_base: float = 2.0 * np.pi * frequency_base
    voltage_base: float = float(line.bus_from.Vnom) * 1.0e3
    sbase_va: float = float(grid.Sbase) * 1.0e6
    zbase: float = (voltage_base * voltage_base) / sbase_va
    ybase: float = 1.0 / zbase
    line_template: Any = line.template

    if line_template is None:
        r_full: np.ndarray
        l_full: np.ndarray
        c_full: np.ndarray
        r_full, l_full, c_full = build_uncoupled_line_static_matrices(
            line=line,
            omega_base=omega_base,
        )
    else:
        # Tower/template matrices are physical line matrices. They are first
        # length-scaled and then converted to the system EMT per-unit base.
        z_phys: np.ndarray = line_template.z_nabc * float(line.length)
        y_phys: np.ndarray = line_template.y_nabc * float(line.length)

        z_pu: np.ndarray = z_phys / zbase
        y_pu: np.ndarray = y_phys / ybase

        r_full = np.real(z_pu)
        x_full: np.ndarray = np.imag(z_pu)
        l_full = x_full / (omega_base + 1.0e-20)

        bsh_full: np.ndarray = np.imag(y_pu)
        c_full = (bsh_full / (omega_base + 1.0e-20)) / 2.0

    return r_full, l_full, c_full


def validate_line_static_matrices(
        line: Any,
        r_full: np.ndarray,
        l_full: np.ndarray,
        c_full: np.ndarray,
        n_active: int,
        logger: Logger | None,
) -> bool:
    """
    Validate reduced line matrix dimensions before assignment.

    :param line: Line-like branch device.
    :param r_full: Reduced resistance matrix.
    :param l_full: Reduced inductance matrix.
    :param c_full: Reduced capacitance matrix.
    :param n_active: Number of active physical phases.
    :param logger: Optional logger.
    :return: ``True`` if all matrices match the active-phase shape.
    """
    valid: bool = True
    expected_shape: Tuple[int, int] = (n_active, n_active)
    device_name: str = str(line.name)

    if r_full.shape != expected_shape:
        add_static_mapping_warning(
            logger=logger,
            device_name=device_name,
            message="Line static mapping skipped because R matrix shape is inconsistent.",
            value=str(r_full.shape),
            expected_value=str(expected_shape),
            device_property="line_static_matrix_shape",
        )
        valid = False
    else:
        pass

    if l_full.shape != expected_shape:
        add_static_mapping_warning(
            logger=logger,
            device_name=device_name,
            message="Line static mapping skipped because L matrix shape is inconsistent.",
            value=str(l_full.shape),
            expected_value=str(expected_shape),
            device_property="line_static_matrix_shape",
        )
        valid = False
    else:
        pass

    if c_full.shape != expected_shape:
        add_static_mapping_warning(
            logger=logger,
            device_name=device_name,
            message="Line static mapping skipped because C matrix shape is inconsistent.",
            value=str(c_full.shape),
            expected_value=str(expected_shape),
            device_property="line_static_matrix_shape",
        )
        valid = False
    else:
        pass

    return valid


def assign_line_static_api_mapping(
        grid: MultiCircuit,
        line: Any,
        mdl: Block,
        logger: Logger | None,
) -> None:
    """
    Assign static line R, Linv and C parameters exposed by ``api_obj_mapping``.

    The physical reduced matrix is projected into the fixed 4x4 NABC API-object
    contract. Exposed inactive-phase entries are explicitly zeroed, preserving the
    previous template semantics while allowing partial key subsets.

    :param grid: Static network model.
    :param line: Line-like branch device.
    :param mdl: Line EMT block.
    :param logger: Optional logger.
    :return: None.
    """
    device_name: str = str(line.name)
    active_indices: List[int] = get_line_active_global_indices(line)
    n_active: int = len(active_indices)

    if n_active == 0:
        add_static_mapping_warning(
            logger=logger,
            device_name=device_name,
            message="Line static mapping skipped because no physical phases are active.",
            value="0 active phases",
            expected_value="at least one active phase",
            device_property="line_phases",
        )
    else:
        r_full: np.ndarray
        l_full: np.ndarray
        c_full: np.ndarray
        r_full, l_full, c_full = build_line_static_matrices(
            grid=grid,
            line=line,
        )

        matrices_are_valid: bool = validate_line_static_matrices(
            line=line,
            r_full=r_full,
            l_full=l_full,
            c_full=c_full,
            n_active=n_active,
            logger=logger,
        )

        if matrices_are_valid:
            determinant_value: float = float(np.linalg.det(l_full))

            if abs(determinant_value) <= 1.0e-20:
                add_static_mapping_warning(
                    logger=logger,
                    device_name=device_name,
                    message="Line static mapping skipped because inductance matrix is singular.",
                    value=str(determinant_value),
                    expected_value="non-zero determinant",
                    device_property="line_inductance_matrix",
                )
            else:
                linv_full: np.ndarray = np.linalg.inv(l_full)
                r_keys: List[List[ParamPowerFlowRefferenceType]] = get_line_r_keys()
                linv_keys: List[List[ParamPowerFlowRefferenceType]] = get_line_linv_keys()
                c_keys: List[List[ParamPowerFlowRefferenceType]] = get_line_c_keys()

                # First zero every exposed slot of the fixed NABC map. This is
                # important for templates that expose inactive neutral/phase keys.
                global_row: int = 0
                while global_row < 4:
                    global_col: int = 0

                    while global_col < 4:
                        assign_api_mapping_value_if_present(
                            mdl=mdl,
                            key=r_keys[global_row][global_col],
                            value=0.0,
                            logger=logger,
                            device_name=device_name,
                        )
                        assign_api_mapping_value_if_present(
                            mdl=mdl,
                            key=linv_keys[global_row][global_col],
                            value=0.0,
                            logger=logger,
                            device_name=device_name,
                        )
                        assign_api_mapping_value_if_present(
                            mdl=mdl,
                            key=c_keys[global_row][global_col],
                            value=0.0,
                            logger=logger,
                            device_name=device_name,
                        )
                        global_col += 1

                    global_row += 1

                # Then project reduced active-phase values into the fixed NABC
                # contract. Only keys requested by the EMT model are written.
                reduced_row: int = 0
                while reduced_row < n_active:
                    mapped_global_row: int = active_indices[reduced_row]
                    reduced_col: int = 0

                    while reduced_col < n_active:
                        mapped_global_col: int = active_indices[reduced_col]

                        assign_api_mapping_value_if_present(
                            mdl=mdl,
                            key=r_keys[mapped_global_row][mapped_global_col],
                            value=float(r_full[reduced_row, reduced_col]),
                            logger=logger,
                            device_name=device_name,
                        )
                        assign_api_mapping_value_if_present(
                            mdl=mdl,
                            key=linv_keys[mapped_global_row][mapped_global_col],
                            value=float(linv_full[reduced_row, reduced_col]),
                            logger=logger,
                            device_name=device_name,
                        )
                        assign_api_mapping_value_if_present(
                            mdl=mdl,
                            key=c_keys[mapped_global_row][mapped_global_col],
                            value=float(c_full[reduced_row, reduced_col]),
                            logger=logger,
                            device_name=device_name,
                        )
                        reduced_col += 1

                    reduced_row += 1
        else:
            pass
