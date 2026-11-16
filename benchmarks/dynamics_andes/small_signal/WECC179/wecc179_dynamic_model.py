# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""WECC 179 parameterization of reusable standard RMS generator models."""

from __future__ import annotations

from typing import Any

import andes
import pandas as pd

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.enumerations import VarPowerFlowReferenceType
from VeraGridEngine.Templates.Rms.excitation_systems.esdc2a_exciter_rms_template import configure_esdc2a_block
from VeraGridEngine.Templates.Rms.excitation_systems.esdc2a_exciter_rms_template import Esdc2aRmsParameters
from VeraGridEngine.Templates.Rms.excitation_systems.esdc2a_exciter_rms_template import get_esdc2a_exciter_rms_template
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import configure_esst3a_block
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import configure_exst1_block
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import configure_genrou_block
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import Esst3aRmsParameters
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import Exst1RmsParameters
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import GenrouRmsParameters
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import get_esst3a_rms_template
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import get_exst1_rms_template
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import get_genrou_rms_template
from VeraGridEngine.Templates.Rms.governors.ieeeg1_governor_rms_template import configure_ieeeg1_block
from VeraGridEngine.Templates.Rms.governors.ieeeg1_governor_rms_template import get_ieeeg1_governor_rms_template
from VeraGridEngine.Templates.Rms.governors.ieeeg1_governor_rms_template import Ieeeg1RmsParameters
from VeraGridEngine.Templates.Rms.excitation_systems.ieeex1_ieeest_rms_template import configure_ieeest_block
from VeraGridEngine.Templates.Rms.excitation_systems.ieeex1_ieeest_rms_template import get_ieeest_rms_template
from VeraGridEngine.Templates.Rms.excitation_systems.ieeex1_ieeest_rms_template import IeeestInputMode
from VeraGridEngine.Templates.Rms.excitation_systems.ieeex1_ieeest_rms_template import IeeestRmsParameters
from VeraGridEngine.Templates.Rms.power_system_stabilizers.st2cut_stabilizer_rms_template import configure_st2cut_block
from VeraGridEngine.Templates.Rms.power_system_stabilizers.st2cut_stabilizer_rms_template import get_st2cut_stabilizer_rms_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.st2cut_stabilizer_rms_template import St2cutInputMode
from VeraGridEngine.Templates.Rms.power_system_stabilizers.st2cut_stabilizer_rms_template import St2cutRmsParameters
from VeraGridEngine.Utils.Symbolic.block import Block


Wecc179DynamicTables = tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]


def load_wecc179_dynamic_tables() -> Wecc179DynamicTables:
    """Load all dynamic-device sheets from the WECC full workbook.

    :return: GENROU, IEEEG1, ESDC2A, EXST1, ESST3A, IEEEST and ST2CUT tables.
    """
    workbook_path: str = str(andes.get_case("wecc/wecc_full.xlsx"))
    genrou_table: pd.DataFrame = pd.read_excel(workbook_path, sheet_name="GENROU")
    ieeeg1_table: pd.DataFrame = pd.read_excel(workbook_path, sheet_name="IEEEG1")
    esdc2a_table: pd.DataFrame = pd.read_excel(workbook_path, sheet_name="ESDC2A")
    exst1_table: pd.DataFrame = pd.read_excel(workbook_path, sheet_name="EXST1")
    esst3a_table: pd.DataFrame = pd.read_excel(workbook_path, sheet_name="ESST3A")
    ieeest_table: pd.DataFrame = pd.read_excel(workbook_path, sheet_name="IEEEST")
    st2cut_table: pd.DataFrame = pd.read_excel(workbook_path, sheet_name="ST2CUT")
    return (
        genrou_table,
        ieeeg1_table,
        esdc2a_table,
        exst1_table,
        esst3a_table,
        ieeest_table,
        st2cut_table,
    )


def _single_row(frame: pd.DataFrame, column: str, value: Any) -> pd.Series | None:
    """Return a unique matching row, allowing no match.

    :param frame: Source model table.
    :param column: Linkage column.
    :param value: Linkage value.
    :return: Unique row or ``None``.
    """
    matches: pd.DataFrame = frame.loc[frame[column] == value]
    if len(matches) == 0:
        return None
    elif len(matches) == 1:
        return matches.iloc[0]
    else:
        raise ValueError(f"Expected at most one {column}={value!r} row; found {len(matches)}.")


def _model_ordinal(model_index: Any) -> int:
    """Extract an integer model ordinal from an ANDES index.

    :param model_index: Index such as ``GENROU_1``.
    :return: Integer suffix.
    """
    parts: list[str] = str(model_index).rsplit("_", maxsplit=1)
    if len(parts) == 2 and parts[1].isdigit():
        return int(parts[1])
    else:
        raise ValueError(f"Cannot extract a model ordinal from {model_index!r}.")


def _genrou_parameters(row: pd.Series, system_base: float) -> GenrouRmsParameters:
    """Convert one WECC GENROU row to system base.

    :param row: GENROU row.
    :param system_base: System MVA base.
    :return: GENROU parameters.
    """
    rating: float = float(row["Sn"])
    impedance_scale: float = system_base / rating
    power_scale: float = rating / system_base
    return GenrouRmsParameters(
        float(row["fn"]), float(row["D"]) * power_scale,
        float(row["M"]) * power_scale, float(row["ra"]) * impedance_scale,
        float(row["xl"]) * impedance_scale, float(row["xd1"]) * impedance_scale,
        float(row["S10"]), float(row["S12"]), float(row["xd"]) * impedance_scale,
        float(row["xq"]) * impedance_scale, float(row["xd2"]) * impedance_scale,
        float(row["xq1"]) * impedance_scale, float(row["xq2"]) * impedance_scale,
        float(row["Td10"]), float(row["Td20"]), float(row["Tq10"]), float(row["Tq20"]),
    )


def _ieeeg1_parameters(row: pd.Series, power_scale: float) -> Ieeeg1RmsParameters:
    """Convert one IEEEG1 row to system base.

    :param row: IEEEG1 row.
    :param power_scale: Machine rating divided by system base.
    :return: IEEEG1 parameters.
    """
    return Ieeeg1RmsParameters((
        float(row["K"]) * power_scale, float(row["T1"]), float(row["T2"]),
        float(row["T3"]), float(row["UO"]), float(row["UC"]),
        float(row["PMAX"]) * power_scale, float(row["PMIN"]) * power_scale,
        float(row["T4"]), float(row["K1"]), float(row["K2"]),
        float(row["T5"]), float(row["K3"]), float(row["K4"]),
        float(row["T6"]), float(row["K5"]), float(row["K6"]),
        float(row["T7"]), float(row["K7"]), float(row["K8"]),
    ))


def _esdc2a_parameters(row: pd.Series) -> Esdc2aRmsParameters:
    """Return one ESDC2A parameter record.

    :param row: ESDC2A row.
    :return: ESDC2A parameters.
    """
    return Esdc2aRmsParameters((
        float(row["TR"]), float(row["KA"]), float(row["TA"]), float(row["TB"]),
        float(row["TC"]), float(row["VRMAX"]), float(row["VRMIN"]),
        float(row["KE"]), float(row["TE"]), float(row["KF"]), float(row["TF1"]),
        float(row["E1"]), float(row["SE1"]), float(row["E2"]), float(row["SE2"]),
    ))


def _exst1_parameters(row: pd.Series) -> Exst1RmsParameters:
    """Return one EXST1 parameter record.

    :param row: EXST1 row.
    :return: EXST1 parameters.
    """
    return Exst1RmsParameters(
        float(row["TR"]), float(row["VIMAX"]), float(row["VIMIN"]),
        float(row["TC"]), float(row["TB"]), float(row["KA"]), float(row["TA"]),
        float(row["VRMAX"]), float(row["VRMIN"]), float(row["KC"]),
        float(row["KF"]), float(row["TF"]),
    )


def _esst3a_parameters(row: pd.Series) -> Esst3aRmsParameters:
    """Return one zero-TA ESST3A parameter record.

    :param row: ESST3A row.
    :return: ESST3A parameters.
    """
    return Esst3aRmsParameters(
        float(row["TR"]), float(row["VIMAX"]), float(row["VIMIN"]),
        float(row["KM"]), float(row["TC"]), float(row["TB"]), float(row["KA"]),
        float(row["TA"]), float(row["VRMAX"]), float(row["VRMIN"]),
        float(row["KG"]), float(row["KP"]), float(row["KI"]), float(row["VBMAX"]),
        float(row["KC"]), float(row["XL"]), float(row["VGMAX"]),
        float(row["THETAP"]), float(row["TM"]), float(row["VMMAX"]), float(row["VMMIN"]),
    )


def _ieeest_parameters(row: pd.Series, power_scale: float) -> IeeestRmsParameters:
    """Return one zero-input-filter IEEEST record.

    :param row: IEEEST row.
    :param power_scale: Machine rating divided by system base.
    :return: IEEEST parameters.
    """
    upper_voltage_cutoff: float = float(row["VCU"])
    lower_voltage_cutoff: float = float(row["VCL"])
    if upper_voltage_cutoff == 0.0:
        upper_voltage_cutoff = 999.0
    else:
        pass
    if lower_voltage_cutoff == 0.0:
        lower_voltage_cutoff = -999.0
    else:
        pass
    return IeeestRmsParameters(
        float(row["T3"]), float(row["T4"]), float(row["T5"]), float(row["T6"]),
        float(row["KS"]), float(row["LSMAX"]), float(row["LSMIN"]),
        upper_voltage_cutoff, lower_voltage_cutoff, power_scale,
    )


def _st2cut_parameters(row: pd.Series, power_scale: float) -> St2cutRmsParameters:
    """Return one WECC ST2CUT record.

    :param row: ST2CUT row.
    :param power_scale: Machine rating divided by system base.
    :return: ST2CUT parameters.
    """
    mode_number: int = int(row["MODE"])
    if mode_number == 1:
        mode: St2cutInputMode = St2cutInputMode.ROTOR_SPEED
    elif mode_number == 3:
        mode = St2cutInputMode.ELECTRICAL_POWER
    else:
        raise ValueError(f"WECC ST2CUT MODE {mode_number} is unsupported.")
    return St2cutRmsParameters(
        mode=mode,
        values=(
            float(row["K1"]), float(row["T1"]), float(row["T3"]), float(row["T4"]),
            float(row["T5"]), float(row["T6"]), float(row["T7"]), float(row["T8"]),
            float(row["T9"]), float(row["T10"]), float(row["LSMAX"]), float(row["LSMIN"]),
        ),
        power_scale=power_scale,
    )


def _build_exciter(
    vfactory: VarFactory,
    model_name: str,
    tables: Wecc179DynamicTables,
) -> tuple[Block, str]:
    """Build and configure the exciter connected to one machine.

    :param vfactory: Shared symbolic variable factory.
    :param model_name: GENROU model index.
    :param tables: WECC dynamic tables.
    :return: Exciter block and exciter index.
    """
    esdc2a_table: pd.DataFrame = tables[2]
    exst1_table: pd.DataFrame = tables[3]
    esst3a_table: pd.DataFrame = tables[4]
    esdc_row: pd.Series | None = _single_row(esdc2a_table, "syn", model_name)
    exst_row: pd.Series | None = _single_row(exst1_table, "syn", model_name)
    esst_row: pd.Series | None = _single_row(esst3a_table, "syn", model_name)
    row_count: int = sum(row is not None for row in (esdc_row, exst_row, esst_row))
    if row_count == 1:
        pass
    else:
        raise ValueError(f"Expected one exciter for {model_name}; found {row_count}.")
    if esdc_row is not None:
        block: Block = get_esdc2a_exciter_rms_template(
            vfactory=vfactory,
            name=f"{model_name} ESDC2A",
        ).block.children[0]
        configure_esdc2a_block(block, _esdc2a_parameters(esdc_row), vfactory)
        exciter_name: str = str(esdc_row["idx"])
    elif exst_row is not None:
        block = get_exst1_rms_template(
            vfactory=vfactory,
            name=f"{model_name} EXST1",
        ).block.children[0]
        configure_exst1_block(block, _exst1_parameters(exst_row), vfactory)
        exciter_name = str(exst_row["idx"])
    else:
        block = get_esst3a_rms_template(
            vfactory=vfactory,
            name=f"{model_name} ESST3A",
        ).block.children[0]
        configure_esst3a_block(block, _esst3a_parameters(esst_row), vfactory)
        exciter_name = str(esst_row["idx"])
    return block, exciter_name


def _build_stabilizer(
    vfactory: VarFactory,
    exciter_name: str,
    power_scale: float,
    tables: Wecc179DynamicTables,
) -> Block:
    """Build and configure the stabilizer linked to one exciter.

    :param vfactory: Shared symbolic variable factory.
    :param exciter_name: Exciter model index.
    :param power_scale: Machine rating divided by system base.
    :param tables: WECC dynamic tables.
    :return: Configured PSS block.
    """
    ieeest_table: pd.DataFrame = tables[5]
    st2cut_table: pd.DataFrame = tables[6]
    ieeest_row: pd.Series | None = _single_row(ieeest_table, "avr", exciter_name)
    st2cut_row: pd.Series | None = _single_row(st2cut_table, "avr", exciter_name)
    if ieeest_row is not None and st2cut_row is None:
        block: Block = get_ieeest_rms_template(
            vfactory=vfactory,
            input_mode=IeeestInputMode.ELECTRICAL_POWER,
            name=f"{exciter_name} IEEEST",
        ).block.children[0]
        configure_ieeest_block(block, _ieeest_parameters(ieeest_row, power_scale), vfactory)
    elif ieeest_row is None and st2cut_row is not None:
        parameters: St2cutRmsParameters = _st2cut_parameters(st2cut_row, power_scale)
        block = get_st2cut_stabilizer_rms_template(
            vfactory=vfactory,
            input_mode=parameters.mode,
            include_input_lag=parameters.t1 > 0.0,
            include_second_lead_lag=parameters.t8 > 0.0,
            include_third_lead_lag=parameters.t10 > 0.0,
            name=f"{exciter_name} ST2CUT",
        ).block.children[0]
        configure_st2cut_block(block, parameters, vfactory)
    else:
        raise ValueError(f"Expected one stabilizer for {exciter_name}.")
    return block


def get_wecc179_generator_rms_template(
    vfactory: VarFactory,
    generator_index: int,
    system_base: float,
    tables: Wecc179DynamicTables,
) -> RmsModelTemplate:
    """Build one complete WECC generator assembly in static-generator order.

    :param vfactory: Shared symbolic variable factory.
    :param generator_index: Zero-based generator index.
    :param system_base: VeraGrid system MVA base.
    :param tables: Loaded WECC dynamic tables.
    :return: Connected GENROU--IEEEG1--exciter--PSS template.
    """
    genrou_table: pd.DataFrame = tables[0]
    ieeeg1_table: pd.DataFrame = tables[1]
    machine_row: pd.Series | None = _single_row(genrou_table, "gen", generator_index + 1)
    if machine_row is None:
        raise ValueError(f"No WECC GENROU links to static generator {generator_index + 1}.")
    else:
        pass
    model_name: str = str(machine_row["idx"])
    power_scale: float = float(machine_row["Sn"]) / system_base
    governor_row: pd.Series | None = _single_row(ieeeg1_table, "syn", model_name)
    if governor_row is None:
        raise ValueError(f"No WECC IEEEG1 links to {model_name}.")
    else:
        pass
    template: RmsModelTemplate = RmsModelTemplate(name=model_name)
    template.tpe = DeviceType.GeneratorDevice
    machine_block: Block = get_genrou_rms_template(
        vfactory=vfactory,
        name=f"{model_name} GENROU",
    ).block.children[0]
    configure_genrou_block(machine_block, _genrou_parameters(machine_row, system_base), vfactory)
    governor_block: Block = get_ieeeg1_governor_rms_template(
        vfactory=vfactory,
        include_t7_state=float(governor_row["T7"]) > 0.0,
        name=f"{model_name} IEEEG1",
    ).block.children[0]
    configure_ieeeg1_block(governor_block, _ieeeg1_parameters(governor_row, power_scale), vfactory)
    exciter_block, exciter_name = _build_exciter(vfactory, model_name, tables)
    stabilizer_block: Block = _build_stabilizer(vfactory, exciter_name, power_scale, tables)

    vfactory.add_connection(machine_block.in_vars[2], governor_block.out_vars[0])
    vfactory.add_connection(governor_block.in_vars[0], machine_block.out_vars[2])
    vfactory.add_connection(governor_block.in_vars[1], machine_block.out_vars[4])
    vfactory.add_connection(machine_block.in_vars[3], exciter_block.out_vars[0])
    if len(exciter_block.in_vars) == 2:
        vfactory.add_connection(exciter_block.in_vars[0], machine_block.in_vars[0])
        pss_input_index: int = 1
    elif len(exciter_block.in_vars) == 3:
        vfactory.add_connection(exciter_block.in_vars[0], machine_block.out_vars[3])
        vfactory.add_connection(exciter_block.in_vars[1], machine_block.in_vars[0])
        pss_input_index = 2
    else:
        vfactory.add_connection(exciter_block.in_vars[0], machine_block.out_vars[3])
        vfactory.add_connection(exciter_block.in_vars[1], machine_block.in_vars[0])
        vfactory.add_connection(exciter_block.in_vars[2], machine_block.out_vars[5])
        vfactory.add_connection(exciter_block.in_vars[3], machine_block.out_vars[6])
        vfactory.add_connection(exciter_block.in_vars[4], machine_block.out_vars[7])
        vfactory.add_connection(exciter_block.in_vars[5], machine_block.out_vars[8])
        pss_input_index = 6
    vfactory.add_connection(exciter_block.in_vars[pss_input_index], stabilizer_block.out_vars[0])
    if len(stabilizer_block.in_vars) == 2:
        vfactory.add_connection(stabilizer_block.in_vars[0], machine_block.out_vars[2])
        vfactory.add_connection(stabilizer_block.in_vars[1], machine_block.out_vars[4])
    else:
        vfactory.add_connection(stabilizer_block.in_vars[0], machine_block.in_vars[0])
        vfactory.add_connection(stabilizer_block.in_vars[1], machine_block.out_vars[2])
        vfactory.add_connection(stabilizer_block.in_vars[2], machine_block.out_vars[4])
        vfactory.add_connection(stabilizer_block.in_vars[3], governor_block.out_vars[0])
    template.block.children.extend((machine_block, governor_block, exciter_block, stabilizer_block))
    template.block.external_mapping = dict()
    template.block.external_mapping[VarPowerFlowReferenceType.Vm] = machine_block.in_vars[0]
    template.block.external_mapping[VarPowerFlowReferenceType.Va] = machine_block.in_vars[1]
    template.block.external_mapping[VarPowerFlowReferenceType.P] = machine_block.out_vars[0]
    template.block.external_mapping[VarPowerFlowReferenceType.Q] = machine_block.out_vars[1]
    template.block.in_vars = list((machine_block.in_vars[0], machine_block.in_vars[1]))
    template.block.out_vars = list((machine_block.out_vars[0], machine_block.out_vars[1]))
    return template


def get_wecc179_andes_style_state_labels(tables: Wecc179DynamicTables) -> list[str]:
    """Return physical WECC state labels in VeraGrid compiled order.

    :param tables: Loaded WECC tables.
    :return: ANDES-style labels excluding unused BusFreq states.
    """
    genrou_table: pd.DataFrame = tables[0]
    ieeeg1_table: pd.DataFrame = tables[1]
    ieeest_table: pd.DataFrame = tables[5]
    st2cut_table: pd.DataFrame = tables[6]
    labels: list[str] = list()
    generator_index: int
    for generator_index in range(29):
        machine_row: pd.Series = genrou_table.loc[
            genrou_table["gen"] == generator_index + 1
        ].iloc[0]
        machine_ordinal: int = _model_ordinal(machine_row["idx"])
        state_name: str
        for state_name in ("delta", "omega", "e1q", "e1d", "e2d", "e2q"):
            labels.append(f"{state_name} GENROU {machine_ordinal}")
        governor_row: pd.Series = ieeeg1_table.loc[
            ieeeg1_table["syn"] == machine_row["idx"]
        ].iloc[0]
        governor_ordinal: int = _model_ordinal(governor_row["idx"])
        for state_name in ("LL_x", "IAW_y", "L4_y"):
            labels.append(f"{state_name} IEEEG1 {governor_ordinal}")
        if float(governor_row["T7"]) > 0.0:
            labels.append(f"L7_y IEEEG1 {governor_ordinal}")
        else:
            pass
        exciter_block, exciter_name = _build_exciter(VarFactory(), str(machine_row["idx"]), tables)
        exciter_type: str = exciter_name.rsplit("_", maxsplit=1)[0]
        exciter_ordinal: int = _model_ordinal(exciter_name)
        for variable in exciter_block.state_vars:
            labels.append(f"{variable.name} {exciter_type} {exciter_ordinal}")
        pss_row: pd.Series | None = _single_row(ieeest_table, "avr", exciter_name)
        if pss_row is not None:
            pss_ordinal: int = _model_ordinal(pss_row["idx"])
            labels.append(f"LL2_x IEEEST {pss_ordinal}")
            labels.append(f"WO_x IEEEST {pss_ordinal}")
        else:
            st2cut_row: pd.Series = st2cut_table.loc[
                st2cut_table["avr"] == exciter_name
            ].iloc[0]
            pss_ordinal = _model_ordinal(st2cut_row["idx"])
            if float(st2cut_row["T1"]) > 0.0:
                labels.append(f"L1_y ST2CUT {pss_ordinal}")
            else:
                pass
            labels.append(f"WO_x ST2CUT {pss_ordinal}")
            labels.append(f"LL1_x ST2CUT {pss_ordinal}")
            if float(st2cut_row["T8"]) > 0.0:
                labels.append(f"LL2_x ST2CUT {pss_ordinal}")
            else:
                pass
            if float(st2cut_row["T10"]) > 0.0:
                labels.append(f"LL3_x ST2CUT {pss_ordinal}")
            else:
                pass
    return labels
