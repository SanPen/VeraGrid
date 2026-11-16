# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""IEEE14 parameterization of the reusable VeraGrid RMS standard models."""

from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import configure_esst3a_block
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import configure_exst1_block
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import configure_genrou_block
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import configure_tgov1_block
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import Esst3aRmsParameters
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import Exst1RmsParameters
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import GenrouExciterType
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import GenrouRmsParameters
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import get_complete_genrou_rms_template
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import Tgov1RmsParameters
from VeraGridEngine.Utils.Symbolic.block import Block


def _get_genrou_parameters() -> tuple[GenrouRmsParameters, ...]:
    """Return GENROU parameters in IEEE14 generator order.

    :return: Five IEEE14 GENROU parameter sets.
    """
    return (
        GenrouRmsParameters(60.0, 0.0, 8.0, 0.0, 0.15, 0.6, 0.09, 0.38, 1.8, 1.75, 0.23, 0.8, 0.23, 6.5, 0.06, 0.2, 0.05),
        GenrouRmsParameters(60.0, 0.0, 13.0, 0.0, 0.15, 0.6, 0.09, 0.38, 1.8, 1.75, 0.28, 0.8, 0.28, 6.5, 0.06, 0.2, 0.05),
        GenrouRmsParameters(60.0, 0.0, 10.0, 0.0, 0.15, 0.6, 0.09, 0.38, 1.8, 1.75, 0.34, 0.8, 0.34, 6.5, 0.06, 0.2, 0.05),
        GenrouRmsParameters(60.0, 0.0, 10.0, 0.0, 0.15, 0.6, 0.09, 0.38, 1.8, 1.75, 0.28, 0.8, 0.28, 6.5, 0.06, 0.2, 0.05),
        GenrouRmsParameters(60.0, 0.0, 10.0, 0.0, 0.15, 0.6, 0.09, 0.38, 1.8, 1.75, 0.34, 0.8, 0.34, 6.5, 0.06, 0.2, 0.05),
    )


def _get_tgov1_parameters() -> tuple[Tgov1RmsParameters, ...]:
    """Return TGOV1 parameters in IEEE14 generator order.

    :return: Five IEEE14 TGOV1 parameter sets.
    """
    return (
        Tgov1RmsParameters(1.0, 0.05, 1.05, 0.3, 0.05, 1.0, 2.1, 0.0),
        Tgov1RmsParameters(1.0, 0.05, 1.2, 0.0, 0.1, 1.0, 2.1, 0.0),
        Tgov1RmsParameters(1.0, 0.05, 1.2, 0.0, 0.1, 1.0, 2.1, 0.0),
        Tgov1RmsParameters(1.0, 0.05, 1.05, 0.3, 0.05, 1.0, 2.1, 0.0),
        Tgov1RmsParameters(1.0, 0.05, 1.05, 0.3, 0.05, 1.0, 2.1, 0.0),
    )


def _get_exst1_parameters() -> Exst1RmsParameters:
    """Return the IEEE14 EXST1 parameter set.

    :return: EXST1 parameters for generator two.
    """
    return Exst1RmsParameters(
        0.02, 99.0, -99.0, 0.0, 0.02, 50.0, 0.02, 9999.0, -9999.0, 0.0, 0.01, 1.0
    )


def _get_esst3a_parameters() -> Esst3aRmsParameters:
    """Return the IEEE14 zero-TA ESST3A parameter set.

    :return: Shared ESST3A parameters for four generators.
    """
    return Esst3aRmsParameters(
        0.02, 0.2, -0.2, 8.0, 1.0, 5.0, 20.0, 0.0, 99.0, -99.0,
        1.0, 3.67, 0.435, 5.48, 0.01, 0.0098, 3.86, 3.33, 0.4, 99.0, 0.0
    )


def _get_exciter_types() -> tuple[GenrouExciterType, ...]:
    """Return excitation-system selections in IEEE14 generator order.

    :return: Five excitation-system selections.
    """
    return (
        GenrouExciterType.ESST3A,
        GenrouExciterType.EXST1,
        GenrouExciterType.ESST3A,
        GenrouExciterType.ESST3A,
        GenrouExciterType.ESST3A,
    )


def get_ieee14_andes_style_state_labels() -> list[str]:
    """Return IEEE14 physical state labels in VeraGrid compiled order.

    :return: ANDES-style labels aligned with the 56-state VeraGrid trajectory.
    """
    labels: list[str] = list()
    esst3a_ordinal_by_generator: dict[int, int] = dict(((1, 2), (3, 3), (4, 4), (5, 5)))
    generator_ordinal: int
    for generator_ordinal in range(1, 6):
        state_name: str
        for state_name in ("delta", "omega", "e1q", "e1d", "e2d", "e2q"):
            labels.append(f"{state_name} GENROU {generator_ordinal}")
        labels.append(f"LAG_y TGOV1 {generator_ordinal}")
        labels.append(f"LL_x TGOV1 {generator_ordinal}")
        if generator_ordinal == 2:
            for state_name in ("LG_y", "LL_x", "LR_y", "WF_x"):
                labels.append(f"{state_name} EXST1 1")
        else:
            exciter_ordinal: int = esst3a_ordinal_by_generator[generator_ordinal]
            for state_name in ("LG_y", "LL_x", "LAW2_y"):
                labels.append(f"{state_name} ESST3A {exciter_ordinal}")
    return labels


def get_ieee14_genrou_rms_template(
    vfactory: VarFactory,
    generator_index: int,
    name: str | None = None,
) -> RmsModelTemplate:
    """Build and configure one IEEE14 GENROU generator assembly.

    :param vfactory: Shared symbolic variable factory.
    :param generator_index: Zero-based generator index in the IEEE14 inventory.
    :param name: Optional wrapper name.
    :return: Configured GENROU, TGOV1 and excitation-system assembly.
    :raises IndexError: If ``generator_index`` is outside 0..4.
    """
    genrou_parameters: tuple[GenrouRmsParameters, ...] = _get_genrou_parameters()
    tgov1_parameters: tuple[Tgov1RmsParameters, ...] = _get_tgov1_parameters()
    exciter_types: tuple[GenrouExciterType, ...] = _get_exciter_types()
    if generator_index < 0 or generator_index >= len(genrou_parameters):
        raise IndexError(
            f"IEEE14 generator_index must be in 0..{len(genrou_parameters) - 1}; "
            f"received {generator_index}."
        )
    else:
        pass

    if name is None:
        model_name: str = f"ieee14_GENROU_{generator_index + 1}"
    else:
        model_name = name
    exciter_type: GenrouExciterType = exciter_types[generator_index]
    template: RmsModelTemplate = get_complete_genrou_rms_template(
        vfactory=vfactory,
        exciter_type=exciter_type,
        name=model_name,
    )
    machine_block: Block = template.block.children[0]
    governor_block: Block = template.block.children[1]
    exciter_block: Block = template.block.children[2]

    configure_genrou_block(machine_block, genrou_parameters[generator_index], vfactory)
    configure_tgov1_block(governor_block, tgov1_parameters[generator_index], vfactory)
    if exciter_type is GenrouExciterType.ESST3A:
        configure_esst3a_block(exciter_block, _get_esst3a_parameters(), vfactory)
    else:
        configure_exst1_block(exciter_block, _get_exst1_parameters(), vfactory)
    return template
