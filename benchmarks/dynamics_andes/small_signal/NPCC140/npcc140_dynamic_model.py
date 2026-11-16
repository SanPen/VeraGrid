# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""NPCC 140 parameterization of reusable standard RMS generator models."""

from __future__ import annotations

from typing import Any

import andes
import pandas as pd

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.enumerations import VarPowerFlowReferenceType
from VeraGridEngine.Templates.Rms.synchronous_machines.gencls_rms_template import configure_gencls_tgov1_block
from VeraGridEngine.Templates.Rms.synchronous_machines.gencls_rms_template import GenclsMechanicalInput
from VeraGridEngine.Templates.Rms.synchronous_machines.gencls_rms_template import GenclsRmsParameters
from VeraGridEngine.Templates.Rms.synchronous_machines.gencls_rms_template import get_complete_gencls_rms_template
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import configure_genrou_block
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import configure_tgov1_block
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import GenrouRmsParameters
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import GenrouSaturationMode
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import get_genrou_rms_template
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import get_tgov1_rms_template
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import Tgov1RmsParameters
from VeraGridEngine.Templates.Rms.excitation_systems.ieeex1_ieeest_rms_template import configure_ieeex1_block
from VeraGridEngine.Templates.Rms.excitation_systems.ieeex1_ieeest_rms_template import get_ieeex1_rms_template
from VeraGridEngine.Templates.Rms.excitation_systems.ieeex1_ieeest_rms_template import Ieeex1RmsParameters
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


Npcc140DynamicTables = tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]


def load_npcc140_dynamic_tables() -> Npcc140DynamicTables:
    """Load the four NPCC dynamic tables from the ANDES case workbook.

    :return: GENCLS, GENROU, TGOV1 and IEEEX1 tables in that order.
    """
    workbook_path: str = str(andes.get_case("npcc/npcc.xlsx"))
    gencls_table: pd.DataFrame = pd.read_excel(workbook_path, sheet_name="GENCLS")
    genrou_table: pd.DataFrame = pd.read_excel(workbook_path, sheet_name="GENROU")
    tgov1_table: pd.DataFrame = pd.read_excel(workbook_path, sheet_name="TGOV1")
    ieeex1_table: pd.DataFrame = pd.read_excel(workbook_path, sheet_name="IEEEX1")
    return gencls_table, genrou_table, tgov1_table, ieeex1_table


def _single_row(frame: pd.DataFrame, column: str, value: Any) -> pd.Series | None:
    """Return a unique matching model row, allowing no match.

    :param frame: Source dynamic-model table.
    :param column: Linkage-column name.
    :param value: Linkage value.
    :return: Unique row or ``None``.
    :raises ValueError: If duplicate matches exist.
    """
    matches: pd.DataFrame = frame.loc[frame[column] == value]
    if len(matches) == 0:
        return None
    elif len(matches) == 1:
        return matches.iloc[0]
    else:
        raise ValueError(f"Expected at most one {column}={value!r} row; found {len(matches)}.")


def _scaled_genrou_parameters(row: pd.Series, system_base: float) -> GenrouRmsParameters:
    """Convert one native-machine-base NPCC GENROU row to system base.

    :param row: GENROU workbook row.
    :param system_base: VeraGrid system power base in MVA.
    :return: System-base GENROU parameters.
    """
    rating: float = float(row["Sn"])
    impedance_scale: float = system_base / rating
    power_scale: float = rating / system_base
    return GenrouRmsParameters(
        fn=float(row["fn"]),
        d=float(row["D"]) * power_scale,
        m=float(row["M"]) * power_scale,
        ra=float(row["ra"]) * impedance_scale,
        xl=float(row["xl"]) * impedance_scale,
        xd1=float(row["xd1"]) * impedance_scale,
        s10=float(row["S10"]),
        s12=float(row["S12"]),
        xd=float(row["xd"]) * impedance_scale,
        xq=float(row["xq"]) * impedance_scale,
        xd2=float(row["xd2"]) * impedance_scale,
        xq1=float(row["xq1"]) * impedance_scale,
        xq2=float(row["xq2"]) * impedance_scale,
        td10=float(row["Td10"]),
        td20=float(row["Td20"]),
        tq10=float(row["Tq10"]),
        tq20=float(row["Tq20"]),
    )


def _scaled_gencls_parameters(row: pd.Series, system_base: float) -> GenclsRmsParameters:
    """Convert one native-machine-base NPCC GENCLS row to system base.

    :param row: GENCLS workbook row.
    :param system_base: VeraGrid system power base in MVA.
    :return: System-base GENCLS parameters.
    """
    rating: float = float(row["Sn"])
    return GenclsRmsParameters(
        fn=float(row["fn"]),
        d=float(row["D"]) * rating / system_base,
        m=float(row["M"]) * rating / system_base,
        ra=float(row["ra"]) * system_base / rating,
        xd1=float(row["xd1"]) * system_base / rating,
    )


def _scaled_tgov1_parameters(
    row: pd.Series,
    machine_rating: float,
    system_base: float,
) -> Tgov1RmsParameters:
    """Convert one native-machine-base TGOV1 row to system base.

    :param row: TGOV1 workbook row.
    :param machine_rating: Connected machine rating in MVA.
    :param system_base: VeraGrid system power base in MVA.
    :return: System-base TGOV1 parameters.
    """
    power_scale: float = machine_rating / system_base
    return Tgov1RmsParameters(
        wref0=float(row["wref0"]),
        r=float(row["R"]) / power_scale,
        vmax=float(row["VMAX"]) * power_scale,
        vmin=float(row["VMIN"]) * power_scale,
        t1=float(row["T1"]),
        t2=float(row["T2"]),
        t3=float(row["T3"]),
        dt=float(row["Dt"]) * power_scale,
    )


def _ieeex1_parameters(row: pd.Series) -> Ieeex1RmsParameters:
    """Convert one NPCC IEEEX1 workbook row.

    :param row: IEEEX1 workbook row.
    :return: IEEEX1 parameters.
    """
    return Ieeex1RmsParameters(
        ta=float(row["TA"]),
        te=float(row["TE"]),
        tf1=float(row["TF1"]),
        kf1=float(row["KF1"]),
        ka=float(row["KA"]),
        ke=float(row["KE"]),
        vrmax=float(row["VRMAX"]),
        vrmin=float(row["VRMIN"]),
        e1=float(row["E1"]),
        se1=float(row["SE1"]),
        e2=float(row["E2"]),
        se2=float(row["SE2"]),
    )


def _add_initialized_hold(
    block: Block,
    input_var: Var,
    initial_var: Var,
    hold_name: str,
    vfactory: VarFactory,
) -> None:
    """Close one unconnected machine input with an initialized constant.

    :param block: Machine block.
    :param input_var: Otherwise-unconnected input variable.
    :param initial_var: Variable defining the equilibrium hold value.
    :param hold_name: Stable hold-parameter name.
    :param vfactory: Shared variable factory.
    :return: None.
    """
    hold_var: Var = vfactory.add_var(hold_name)
    block.event_dict[hold_var] = vfactory.add_const(value=None, name=hold_name)
    block.init_eqs[hold_var] = initial_var
    block.init_eqs[input_var] = initial_var
    block.algebraic_vars.append(input_var)
    block.algebraic_eqs.append(hold_var - input_var)


def _add_zero_input(block: Block, input_var: Var) -> None:
    """Close one unconnected controller input at zero.

    :param block: Controller block.
    :param input_var: Otherwise-unconnected input.
    :return: None.
    """
    block.init_eqs[input_var] = sym.Const(0.0)
    block.algebraic_vars.append(input_var)
    block.algebraic_eqs.append(-input_var)


def _build_genrou_assembly(
    vfactory: VarFactory,
    machine_row: pd.Series,
    governor_row: pd.Series | None,
    exciter_row: pd.Series | None,
    system_base: float,
) -> RmsModelTemplate:
    """Build one NPCC GENROU with its available controllers.

    :param vfactory: Shared symbolic variable factory.
    :param machine_row: GENROU workbook row.
    :param governor_row: Optional TGOV1 row.
    :param exciter_row: Optional IEEEX1 row.
    :param system_base: VeraGrid system power base in MVA.
    :return: Connected and configured generator assembly.
    """
    model_name: str = str(machine_row["idx"])
    template: RmsModelTemplate = RmsModelTemplate(name=model_name)
    template.tpe = DeviceType.GeneratorDevice
    machine_block: Block = get_genrou_rms_template(
        vfactory=vfactory,
        name=f"{model_name} GENROU",
        saturation_mode=GenrouSaturationMode.DISABLED,
    ).block.children[0]
    configure_genrou_block(
        machine_block,
        _scaled_genrou_parameters(machine_row, system_base),
        vfactory,
    )
    template.block.children.append(machine_block)

    if governor_row is None:
        _add_initialized_hold(
            block=machine_block,
            input_var=machine_block.in_vars[2],
            initial_var=machine_block.out_vars[4],
            hold_name="Tm_hold",
            vfactory=vfactory,
        )
    else:
        governor_block: Block = get_tgov1_rms_template(
            vfactory=vfactory,
            name=f"{model_name} TGOV1",
        ).block.children[0]
        configure_tgov1_block(
            governor_block,
            _scaled_tgov1_parameters(
                governor_row,
                float(machine_row["Sn"]),
                system_base,
            ),
            vfactory,
        )
        vfactory.add_connection(machine_block.in_vars[2], governor_block.out_vars[0])
        vfactory.add_connection(governor_block.in_vars[0], machine_block.out_vars[2])
        vfactory.add_connection(governor_block.in_vars[1], machine_block.out_vars[4])
        template.block.children.append(governor_block)

    if exciter_row is None:
        _add_initialized_hold(
            block=machine_block,
            input_var=machine_block.in_vars[3],
            initial_var=machine_block.out_vars[3],
            hold_name="Vf_hold",
            vfactory=vfactory,
        )
    else:
        exciter_block: Block = get_ieeex1_rms_template(
            vfactory=vfactory,
            name=f"{model_name} IEEEX1",
        ).block.children[0]
        configure_ieeex1_block(exciter_block, _ieeex1_parameters(exciter_row), vfactory)
        vfactory.add_connection(machine_block.in_vars[3], exciter_block.out_vars[0])
        vfactory.add_connection(exciter_block.in_vars[0], machine_block.in_vars[0])
        vfactory.add_connection(exciter_block.in_vars[1], machine_block.out_vars[2])
        _add_zero_input(exciter_block, exciter_block.in_vars[2])
        template.block.children.append(exciter_block)

    template.block.external_mapping = dict()
    template.block.external_mapping[VarPowerFlowReferenceType.Vm] = machine_block.in_vars[0]
    template.block.external_mapping[VarPowerFlowReferenceType.Va] = machine_block.in_vars[1]
    template.block.external_mapping[VarPowerFlowReferenceType.P] = machine_block.out_vars[0]
    template.block.external_mapping[VarPowerFlowReferenceType.Q] = machine_block.out_vars[1]
    template.block.in_vars = list((machine_block.in_vars[0], machine_block.in_vars[1]))
    template.block.out_vars = list((machine_block.out_vars[0], machine_block.out_vars[1]))
    template.block.name = model_name
    return template


def get_npcc140_generator_rms_template(
    vfactory: VarFactory,
    generator_index: int,
    system_base: float,
    tables: Npcc140DynamicTables,
) -> RmsModelTemplate:
    """Build one NPCC generator in RAW static-generator order.

    :param vfactory: Shared symbolic variable factory.
    :param generator_index: Zero-based static-generator index.
    :param system_base: VeraGrid system power base in MVA.
    :param tables: Loaded NPCC dynamic tables.
    :return: Configured GENCLS or GENROU assembly.
    """
    gencls_table, genrou_table, tgov1_table, ieeex1_table = tables
    static_generator_index: int = generator_index + 1
    gencls_row: pd.Series | None = _single_row(
        gencls_table,
        "gen",
        static_generator_index,
    )
    genrou_row: pd.Series | None = _single_row(
        genrou_table,
        "gen",
        static_generator_index,
    )
    if gencls_row is None and genrou_row is None:
        raise ValueError(f"No NPCC dynamic machine links to static generator {static_generator_index}.")
    elif gencls_row is not None and genrou_row is not None:
        raise ValueError(f"Two NPCC dynamic machines link to static generator {static_generator_index}.")
    elif genrou_row is not None:
        machine_name: str = str(genrou_row["idx"])
        return _build_genrou_assembly(
            vfactory=vfactory,
            machine_row=genrou_row,
            governor_row=_single_row(tgov1_table, "syn", machine_name),
            exciter_row=_single_row(ieeex1_table, "syn", machine_name),
            system_base=system_base,
        )
    else:
        machine_name = str(gencls_row["idx"])
        governor_row: pd.Series | None = _single_row(tgov1_table, "syn", machine_name)
        if governor_row is None:
            mechanical_input: GenclsMechanicalInput = GenclsMechanicalInput.CONSTANT
        else:
            mechanical_input = GenclsMechanicalInput.TGOV1
        template: RmsModelTemplate = get_complete_gencls_rms_template(
            vfactory=vfactory,
            mechanical_input=mechanical_input,
            name=machine_name,
        )
        governor_parameters: Tgov1RmsParameters | None
        if governor_row is None:
            governor_parameters = None
        else:
            governor_parameters = _scaled_tgov1_parameters(
                governor_row,
                float(gencls_row["Sn"]),
                system_base,
            )
        configure_gencls_tgov1_block(
            template=template,
            machine_parameters=_scaled_gencls_parameters(gencls_row, system_base),
            governor_parameters=governor_parameters,
            vfactory=vfactory,
        )
        return template


def _model_ordinal(model_index: Any) -> int:
    """Extract the ANDES model ordinal from an ``idx`` value.

    :param model_index: Workbook model index such as ``GENROU_22``.
    :return: Integer suffix.
    """
    parts: list[str] = str(model_index).rsplit("_", maxsplit=1)
    if len(parts) == 2 and parts[1].isdigit():
        return int(parts[1])
    else:
        raise ValueError(f"Cannot extract a model ordinal from {model_index!r}.")


def get_npcc140_andes_style_state_labels(tables: Npcc140DynamicTables) -> list[str]:
    """Return physical state labels in VeraGrid compiled device order.

    :param tables: Loaded NPCC dynamic-model tables.
    :return: ANDES-style labels aligned with VeraGrid state rows.
    """
    gencls_table, genrou_table, tgov1_table, ieeex1_table = tables
    labels: list[str] = list()
    static_generator_index: int
    for static_generator_index in range(1, 49):
        gencls_row: pd.Series | None = _single_row(
            gencls_table,
            "gen",
            static_generator_index,
        )
        genrou_row: pd.Series | None = _single_row(
            genrou_table,
            "gen",
            static_generator_index,
        )
        if genrou_row is not None:
            machine_type: str = "GENROU"
            machine_ordinal: int = _model_ordinal(genrou_row["idx"])
            machine_states: tuple[str, ...] = (
                "delta", "omega", "e1q", "e1d", "e2d", "e2q",
            )
            machine_name: str = str(genrou_row["idx"])
        elif gencls_row is not None:
            machine_type = "GENCLS"
            machine_ordinal = _model_ordinal(gencls_row["idx"])
            machine_states = ("delta", "omega")
            machine_name = str(gencls_row["idx"])
        else:
            raise ValueError(
                f"No NPCC dynamic machine links to static generator {static_generator_index}."
            )
        state_name: str
        for state_name in machine_states:
            labels.append(f"{state_name} {machine_type} {machine_ordinal}")

        governor_row: pd.Series | None = _single_row(tgov1_table, "syn", machine_name)
        if governor_row is None:
            pass
        else:
            governor_ordinal: int = _model_ordinal(governor_row["idx"])
            labels.append(f"LAG_y TGOV1 {governor_ordinal}")
            labels.append(f"LL_x TGOV1 {governor_ordinal}")

        exciter_row: pd.Series | None = _single_row(ieeex1_table, "syn", machine_name)
        if exciter_row is None:
            pass
        else:
            exciter_ordinal: int = _model_ordinal(exciter_row["idx"])
            labels.append(f"vp IEEEX1 {exciter_ordinal}")
            labels.append(f"LA_y IEEEX1 {exciter_ordinal}")
            labels.append(f"W_x IEEEX1 {exciter_ordinal}")
    return labels
