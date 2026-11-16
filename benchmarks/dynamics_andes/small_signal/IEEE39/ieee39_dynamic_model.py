# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""IEEE39 parameterization of reusable standard VeraGrid RMS models."""

from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import configure_genrou_block
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import configure_tgov1_block
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import GenrouRmsParameters
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import GenrouSaturationMode
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import Tgov1RmsParameters
from VeraGridEngine.Templates.Rms.excitation_systems.ieeex1_ieeest_rms_template import configure_ieeex1_block
from VeraGridEngine.Templates.Rms.excitation_systems.ieeex1_ieeest_rms_template import configure_ieeest_block
from VeraGridEngine.Templates.Rms.excitation_systems.ieeex1_ieeest_rms_template import get_complete_genrou_ieeex1_ieeest_rms_template
from VeraGridEngine.Templates.Rms.excitation_systems.ieeex1_ieeest_rms_template import Ieeex1RmsParameters
from VeraGridEngine.Templates.Rms.excitation_systems.ieeex1_ieeest_rms_template import IeeestInputMode
from VeraGridEngine.Templates.Rms.excitation_systems.ieeex1_ieeest_rms_template import IeeestRmsParameters
from VeraGridEngine.Utils.Symbolic.block import Block


def _get_machine_ratings() -> tuple[float, ...]:
    """Return IEEE39 generator ratings in MVA.

    :return: Ten machine ratings in generator order.
    """
    return (1040.0, 836.0, 843.7, 1174.8, 1080.2, 1085.7, 1025.2, 970.2, 1684.1, 1199.0)


def _scaled_genrou_parameters(
    rating: float,
    inertia: float,
    ra: float,
    xl: float,
    xd1: float,
    xd: float,
    xq: float,
    xd2: float,
    xq1: float,
    xq2: float,
    td10: float,
    tq10: float,
) -> GenrouRmsParameters:
    """Convert one native machine-base GENROU record to the 100-MVA base.

    :param rating: Native machine rating in MVA.
    :param inertia: Native machine inertia coefficient.
    :param ra: Native armature resistance.
    :param xl: Native leakage reactance.
    :param xd1: Native d-axis transient reactance.
    :param xd: Native d-axis synchronous reactance.
    :param xq: Native q-axis synchronous reactance.
    :param xd2: Native d-axis subtransient reactance.
    :param xq1: Native q-axis transient reactance.
    :param xq2: Native q-axis subtransient reactance.
    :param td10: D-axis transient open-circuit time constant.
    :param tq10: Q-axis transient open-circuit time constant.
    :return: System-base GENROU parameters.
    """
    impedance_scale: float = 100.0 / rating
    power_scale: float = rating / 100.0
    parameters: GenrouRmsParameters = GenrouRmsParameters(
        60.0,
        0.0,
        inertia * power_scale,
        ra * impedance_scale,
        xl * impedance_scale,
        xd1 * impedance_scale,
        0.0,
        0.0,
        xd * impedance_scale,
        xq * impedance_scale,
        xd2 * impedance_scale,
        xq1 * impedance_scale,
        xq2 * impedance_scale,
        td10,
        0.03,
        tq10,
        0.04,
    )
    return parameters


def _get_genrou_parameters() -> tuple[GenrouRmsParameters, ...]:
    """Return converted IEEE39 GENROU parameters.

    :return: Ten system-base parameter sets.
    """
    return (
        _scaled_genrou_parameters(1040.0, 8.4, 0.0014, 0.125, 0.31, 1.0, 0.69, 0.00792, 0.31, 0.00792, 10.2, 1.5),
        _scaled_genrou_parameters(836.0, 6.06, 0.027, 0.35, 0.697, 2.95, 2.82, 0.29779, 0.697, 0.29779, 6.56, 1.5),
        _scaled_genrou_parameters(843.7, 7.16, 0.00386, 0.304, 0.531, 2.495, 2.37, 0.02566, 0.531, 0.02566, 5.7, 1.5),
        _scaled_genrou_parameters(1174.8, 5.72, 0.00222, 0.295, 0.436, 2.62, 2.58, 0.00803, 0.436, 0.00803, 5.69, 1.5),
        _scaled_genrou_parameters(1080.2, 5.2, 0.0014, 0.54, 1.32, 6.7, 6.2, 0.00571, 1.32, 0.00571, 5.4, 0.44),
        _scaled_genrou_parameters(1085.7, 6.96, 0.0615, 0.224, 0.5, 2.54, 2.41, 0.46538, 0.5, 0.46538, 7.3, 0.4),
        _scaled_genrou_parameters(1025.2, 5.28, 0.00268, 0.322, 0.49, 2.95, 2.92, 0.02141, 0.49, 0.02141, 5.66, 1.5),
        _scaled_genrou_parameters(970.2, 4.86, 0.00686, 0.28, 0.57, 2.9, 2.8, 0.06076, 0.57, 0.06076, 6.7, 0.41),
        _scaled_genrou_parameters(1684.1, 6.9, 0.003, 0.298, 0.57, 2.106, 2.05, 0.01174, 0.57, 0.01174, 4.79, 1.96),
        _scaled_genrou_parameters(1199.0, 100.0, 0.001, 0.03, 0.06, 0.2, 0.19, 0.0026, 0.06, 0.0026, 7.0, 0.7),
    )


def _scaled_tgov1_parameters(rating: float, native_vmax: float) -> Tgov1RmsParameters:
    """Convert one native TGOV1N record to the system power base.

    :param rating: Native machine rating in MVA.
    :param native_vmax: Native upper valve limit.
    :return: System-base TGOV1 parameters.
    """
    power_scale: float = rating / 100.0
    inverse_power_scale: float = 100.0 / rating
    parameters: Tgov1RmsParameters = Tgov1RmsParameters(
        1.0,
        0.05 * inverse_power_scale,
        native_vmax * power_scale,
        0.1 * power_scale,
        0.05,
        1.0,
        2.1,
        0.0,
    )
    return parameters


def _get_tgov1_parameters() -> tuple[Tgov1RmsParameters, ...]:
    """Return converted IEEE39 TGOV1N parameters.

    :return: Ten system-base governor parameter sets.
    """
    ratings: tuple[float, ...] = _get_machine_ratings()
    return (
        _scaled_tgov1_parameters(ratings[0], 1.01),
        _scaled_tgov1_parameters(ratings[1], 1.05),
        _scaled_tgov1_parameters(ratings[2], 1.05),
        _scaled_tgov1_parameters(ratings[3], 1.05),
        _scaled_tgov1_parameters(ratings[4], 1.05),
        _scaled_tgov1_parameters(ratings[5], 1.05),
        _scaled_tgov1_parameters(ratings[6], 1.05),
        _scaled_tgov1_parameters(ratings[7], 1.05),
        _scaled_tgov1_parameters(ratings[8], 1.05),
        _scaled_tgov1_parameters(ratings[9], 1.05),
    )


def _get_ieeex1_parameters() -> tuple[Ieeex1RmsParameters, ...]:
    """Return IEEE39 IEEEX1 parameters in generator order.

    :return: Ten excitation-system parameter sets.
    """
    return (
        Ieeex1RmsParameters(0.06, 0.25, 1.3, 0.23, 10.1, -0.05, 8.0, -8.0, 1.7, 0.5, 3.0, 2.0),
        Ieeex1RmsParameters(0.05, 0.41, 1.3, 0.23, 10.1, -0.05, 5.2, -5.0, 3.0, 0.66, 4.0, 0.88),
        Ieeex1RmsParameters(0.06, 0.5, 1.3, 0.23, 10.1, -0.02, 5.0, -5.0, 3.0, 0.13, 4.0, 0.34),
        Ieeex1RmsParameters(0.06, 0.5, 1.3, 0.23, 10.1, -0.05, 5.0, -5.0, 3.0, 0.08, 4.0, 0.31),
        Ieeex1RmsParameters(0.02, 0.785, 1.3, 0.23, 40.0, -0.04, 9.9, -9.9, 3.0, 0.03, 4.0, 0.91),
        Ieeex1RmsParameters(0.02, 0.471, 1.3, 0.23, 10.1, 1.0, 5.0, -5.0, 3.0, 0.08, 4.0, 0.25),
        Ieeex1RmsParameters(0.02, 0.73, 1.3, 0.23, 40.0, 1.0, 6.5, -6.5, 3.0, 0.03, 4.0, 0.74),
        Ieeex1RmsParameters(0.02, 0.528, 1.3, 0.23, 10.1, -0.05, 5.0, -5.0, 3.0, 0.09, 4.0, 0.28),
        Ieeex1RmsParameters(0.02, 0.95, 1.3, 0.23, 40.0, 1.0, 9.9, -9.9, 3.0, 0.03, 4.0, 0.85),
        Ieeex1RmsParameters(0.02, 0.95, 1.3, 0.23, 10.1, 1.0, 9.9, -9.9, 3.0, 0.03, 4.0, 0.85),
    )


def _get_ieeest_parameters() -> tuple[IeeestRmsParameters, ...]:
    """Return IEEE39 mode-3 IEEEST parameters.

    :return: Ten stabilizer parameter sets.
    """
    ratings: tuple[float, ...] = _get_machine_ratings()
    return (
        IeeestRmsParameters(0.0, 0.75, 1.0, 4.2, -2.0, 0.1, -0.1, 999.0, -999.0, ratings[0] / 100.0),
        IeeestRmsParameters(0.0, 0.75, 1.0, 4.2, -2.0, 0.1, -0.1, 999.0, -999.0, ratings[1] / 100.0),
        IeeestRmsParameters(0.0, 0.75, 1.0, 4.2, -2.0, 0.1, -0.1, 999.0, -999.0, ratings[2] / 100.0),
        IeeestRmsParameters(0.0, 0.75, 1.0, 4.2, -2.0, 0.1, -0.1, 999.0, -999.0, ratings[3] / 100.0),
        IeeestRmsParameters(0.0, 0.75, 1.0, 4.2, -2.0, 0.1, -0.1, 999.0, -999.0, ratings[4] / 100.0),
        IeeestRmsParameters(0.0, 0.75, 1.0, 4.2, -2.0, 0.1, -0.1, 999.0, -999.0, ratings[5] / 100.0),
        IeeestRmsParameters(0.0, 0.75, 1.0, 4.2, -2.0, 0.1, -0.1, 999.0, -999.0, ratings[6] / 100.0),
        IeeestRmsParameters(0.0, 0.75, 1.0, 4.2, -2.0, 0.1, -0.1, 999.0, -999.0, ratings[7] / 100.0),
        IeeestRmsParameters(0.0, 0.75, 1.0, 4.2, -2.0, 0.1, -0.1, 999.0, -999.0, ratings[8] / 100.0),
        IeeestRmsParameters(0.0, 0.75, 1.0, 4.2, -2.0, 0.1, -0.1, 999.0, -999.0, ratings[9] / 100.0),
    )


def get_ieee39_genrou_rms_template(
    vfactory: VarFactory,
    generator_index: int,
    name: str | None = None,
) -> RmsModelTemplate:
    """Build and configure one IEEE39 generator assembly.

    :param vfactory: Shared symbolic variable factory.
    :param generator_index: Zero-based generator index in bus order 30..39.
    :param name: Optional composite-template name.
    :return: Configured GENROU, TGOV1N, IEEEX1 and IEEEST assembly.
    :raises IndexError: If the generator index is outside 0..9.
    """
    machine_parameters: tuple[GenrouRmsParameters, ...] = _get_genrou_parameters()
    governor_parameters: tuple[Tgov1RmsParameters, ...] = _get_tgov1_parameters()
    exciter_parameters: tuple[Ieeex1RmsParameters, ...] = _get_ieeex1_parameters()
    stabilizer_parameters: tuple[IeeestRmsParameters, ...] = _get_ieeest_parameters()
    if generator_index < 0 or generator_index >= len(machine_parameters):
        raise IndexError(
            f"IEEE39 generator_index must be in 0..{len(machine_parameters) - 1}; "
            f"received {generator_index}."
        )
    else:
        pass

    if name is None:
        model_name: str = f"ieee39_GENROU_{generator_index + 1}"
    else:
        model_name = name
    template: RmsModelTemplate = get_complete_genrou_ieeex1_ieeest_rms_template(
        vfactory=vfactory,
        input_mode=IeeestInputMode.ELECTRICAL_POWER,
        saturation_mode=GenrouSaturationMode.DISABLED,
        name=model_name,
    )
    machine_block: Block = template.block.children[0]
    governor_block: Block = template.block.children[1]
    exciter_block: Block = template.block.children[2]
    stabilizer_block: Block = template.block.children[3]
    configure_genrou_block(machine_block, machine_parameters[generator_index], vfactory)
    configure_tgov1_block(governor_block, governor_parameters[generator_index], vfactory)
    configure_ieeex1_block(exciter_block, exciter_parameters[generator_index], vfactory)
    configure_ieeest_block(stabilizer_block, stabilizer_parameters[generator_index], vfactory)
    return template


def get_ieee39_andes_style_state_labels() -> list[str]:
    """Return the IEEE39 physical states in VeraGrid compiled order.

    :return: ANDES-style labels aligned with the 130 VeraGrid states.
    """
    labels: list[str] = list()
    generator_ordinal: int
    for generator_ordinal in range(1, 11):
        state_name: str
        for state_name in ("delta", "omega", "e1q", "e1d", "e2d", "e2q"):
            labels.append(f"{state_name} GENROU {generator_ordinal}")
        labels.append(f"LAG_y TGOV1N TGOV1 {generator_ordinal}")
        labels.append(f"LL_x TGOV1N TGOV1 {generator_ordinal}")
        for state_name in ("vp", "LA_y", "W_x"):
            labels.append(f"{state_name} IEEEX1 {generator_ordinal}")
        labels.append(f"LL2_x IEEEST {generator_ordinal}")
        labels.append(f"WO_x IEEEST {generator_ordinal}")
    return labels


