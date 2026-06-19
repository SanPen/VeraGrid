# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can see it at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Sequence


from VeraGridEngine.Devices.Branches.transformer import Transformer2W
from VeraGridEngine.Devices.Branches.winding import Winding
from VeraGridEngine.enumerations import BlockType, WindingType
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Templates.predefined_blocks import (
    constant,
    gain,
    adder,
    substract,
    product,
    divide,
    absolut,
    generic
)

import VeraGridEngine.Templates as tem
from VeraGridEngine.Devices.types import ALL_DEV_TYPES



def _get_transformer_connection_types(api_object: Transformer2W | Winding | None) -> tuple[WindingType | None, WindingType | None]:
    """
    Return the explicit from/to winding connections for transformer-like objects.

    :param api_object: Transformer-like API object.
    :return: Pair ``(conn_f, conn_t)`` or ``(None, None)`` when unavailable.
    """
    if api_object is None:
        return None, None
    else:
        return api_object.conn_f, api_object.conn_t


def create_block_of_type(var_factory: VarFactory,
                         block_type: BlockType,
                         item_name: str = "",
                         api_object: ALL_DEV_TYPES | None = None) -> Block | None:
    """
    Create a Block appropriate for block_type.
    """
    # CONST (single output)
    if block_type == BlockType.CONST:
        blk = constant(var_factory, item_name)
        blk.name = item_name
        return blk

    # GAIN (single input -> single output)
    elif block_type == BlockType.GAIN:
        blk = gain(var_factory, item_name)
        blk.name = item_name
        return blk

    # SUM / ADDER (2 inputs)
    elif block_type == BlockType.SUM:
        blk = adder(var_factory, item_name)
        blk.name = item_name
        return blk

    # SUBSTRACT (2 inputs)
    elif block_type == BlockType.SUBSTR:
        blk = substract(var_factory, item_name)
        blk.name = item_name
        return blk

    # PRODUCT (2 inputs)
    elif block_type == BlockType.PRODUCT:
        blk = product(var_factory, item_name)
        blk.name = item_name
        return blk

    # DIVIDE (2 inputs)
    elif block_type == BlockType.DIVIDE:
        blk = divide(var_factory, item_name)
        blk.name = item_name
        return blk

    # ABSOLUT (single input -> single output)
    elif block_type == BlockType.ABS:
        blk = absolut(var_factory, item_name)
        blk.name = item_name
        return blk

    # ---------- RMS BLOCKS ----------

    # GENRAW (simple model)
    elif block_type == BlockType.GENRAW:
        blk = tem.get_genrow_rms_template(var_factory).block
        blk.name = item_name
        return blk

    # GENQEC (generator with saturation)
    elif block_type == BlockType.GENQEC:
        blk = tem.get_genqec_rms(var_factory, item_name).block
        blk.name = item_name
        return blk

    # GOVERNOR (governor with control)
    elif block_type == BlockType.GOV_RMS:
        blk = tem.get_governor_rms(var_factory, item_name).block
        blk.name = item_name
        return blk

    # STABILIZER (stabilizer)
    elif block_type == BlockType.STAB_RMS:
        blk = tem.get_stabilizer_rms(var_factory, item_name).block
        blk.name = item_name
        return blk

    # EXCITER (exciter)
    elif block_type == BlockType.EXCITER_RMS:
        blk = tem.get_exciter_rms(var_factory, item_name).block
        blk.name = item_name
        return blk

    # LINE (line)
    elif block_type == BlockType.LINE_RMS:
        blk = tem.get_line_rms_template(var_factory).block
        blk.name = item_name
        return blk

    # LOAD (line)
    elif block_type == BlockType.LOAD_RMS:
        blk = tem.get_load_rms_template(var_factory).block
        blk.name = item_name
        return blk

    # GRID FORMING CONVERTER
    elif block_type == BlockType.GFL_VSC_RMS:
        blk = tem.build_vsc_rms(var_factory).block
        blk.name = item_name
        return blk

    elif block_type == BlockType.PLL_TRANSFORM_RMS:
        blk = tem.get_pll_transform_rms(var_factory).block
        blk.name = item_name
        return blk

    elif block_type == BlockType.PI_CURRENT_CONTROLLER:
        blk = tem.get_pi_current_controller(var_factory).block
        blk.name = item_name
        return blk

    elif block_type == BlockType.PI_POWER_CONTROLLER:
        blk = tem.get_pi_power_controller(var_factory).block
        blk.name = item_name
        return blk

    elif block_type == BlockType.GFL_CONVERTER_RMS:
        blk = tem.get_gfl_converter_rms(var_factory).block
        blk.name = item_name
        return blk



    # DC PV source averaged
    # elif block_type == BlockType.DC_PV_SOURCE_RMS:
    #     blk = tem.DCPVSourceAveraged(var_factory).block
    #     blk.name = item_name
    #     return blk

    # ---------- EMT BLOCKS ----------
    # EMT type GENERATOR
    elif block_type == BlockType.EMT_GENERATOR:
        blk = tem.get_simple_generator_emt_template(var_factory).block
        blk.name = item_name
        return blk

    # Thevenin equivalent generator
    elif block_type == BlockType.EMT_THEVENIN:
        blk = tem.get_generator_thevenin_rl_emt_template_with_ref(var_factory).block
        blk.name = item_name
        return blk

    # GOVERNOR (governor with control)
    elif block_type == BlockType.GOV_EMT:
        blk = tem.get_governor_emt(var_factory, item_name).block
        blk.name = item_name
        return blk

    # STABILIZER (stabilizer)
    elif block_type == BlockType.STAB_EMT:
        blk = tem.get_stabilizer_emt(var_factory, item_name).block
        blk.name = item_name
        return blk

    # EXCITER (exciter)
    elif block_type == BlockType.EXCITER_EMT:
        blk = tem.get_exciter_emt(var_factory, item_name).block
        blk.name = item_name
        return blk

    # DC LOAD
    elif block_type == BlockType.DC_LOAD_EMT:
        blk = tem.get_dc_load_emt_template(var_factory).block
        blk.name = item_name
        return blk

    # #
    # elif block_type == BlockType.INDUCTION_MOTOR_EMT:
    #     blk = tem.get_induction_motor_emt_template(vf=var_factory, name=item_name).block
    #     blk.name = item_name
    #     return blk

    elif block_type == BlockType.TRAFO_EMT:
        conn_f, conn_t = _get_transformer_connection_types(api_object)
        blk = tem.get_transformer_emt_template(var_factory, conn_f=conn_f, conn_t=conn_t).block
        blk.name = item_name
        return blk

    elif block_type == BlockType.XFMR_TRANSFORMER:
        conn_f, conn_t = _get_transformer_connection_types(api_object)
        blk = tem.get_xfmr_emt_template(var_factory, conn_f=conn_f, conn_t=conn_t).block
        blk.name = item_name
        return blk

    elif block_type == BlockType.GROUND_EMT:
        blk = tem.get_ground_emt_template(var_factory, item_name).block
        blk.name = item_name
        return blk

    # TODO: create function for the PV template alone
    # elif block_type == BlockType.PV_EMT:
    #     blk = get_pv_avm_grid_following_emt_template(var_factory, item_name).block
    #     blk.name = item_name
    #     return blk

    elif block_type == BlockType.BATTERY_EMT:
        blk = tem.get_battery_avm_emt_template(var_factory, item_name).block
        blk.name = item_name
        return blk

    elif block_type == BlockType.BESS_EMT:
        blk = tem.get_bess_avm_grid_following_emt_template(var_factory, item_name).block
        blk.name = item_name
        return blk

    # DC LINE
    elif block_type == BlockType.EMT_DC_LINE:
        blk = tem.get_dc_line_with_power_input_emt_template(var_factory).block
        blk.name = item_name
        return blk

    # COMPLETE PSEUDO EMT VSC
    elif block_type == BlockType.COMPLETE_PSEUDO_VSC_EMT:
        blk = tem.get_full_pseudo_emt_converter(var_factory).block
        blk.name = item_name
        return blk

    else:
        raise ValueError(f"Unknown block type: {block_type}")


def create_emt_wizard_block(phase_n: bool,
                            phase_a: bool,
                            phase_b: bool,
                            phase_c: bool,
                            var_factory: VarFactory,
                            block_type: BlockType,
                            item_name: str) -> Block | None:
    """
    :param phase_n:
    :type phase_n:
    :param phase_a:
    :type phase_a:
    :param phase_b:
    :type phase_b:
    :param phase_c:
    :type phase_c:
    :param var_factory:
    :type var_factory:
    :param block_type:
    :type block_type:
    :param item_name:
    :type item_name:
    :return: Requested EMT wizard block or ``None``.
    """
    # PI LINE (line)
    if block_type == BlockType.EMT_PI_LINE:
        blk = tem.get_pi_line_emt_template(vf=var_factory,
                                       phN=phase_n,
                                       phA=phase_a,
                                       phB=phase_b,
                                       phC=phase_c,
                                       name=item_name).block
        blk.name = item_name
        return blk

    # BERGERON LINE (line)
    elif block_type == BlockType.EMT_BERGERON_LINE:
        blk = tem.get_bergeron_line_emt_template(vf=var_factory,
                                        phN=phase_n,
                                        phA=phase_a,
                                        phB=phase_b,
                                        phC=phase_c,
                                        name=item_name).block
        blk.name = item_name
        return blk

    # JMARTI LINE (line)
    elif block_type == BlockType.EMT_JMARTI_LINE:
        blk = tem.get_jmarti_line_emt_template(vf=var_factory,
                                           phN=phase_n,
                                           phA=phase_a,
                                           phB=phase_b,
                                           phC=phase_c,
                                           name=item_name).block
        blk.name = item_name
        return blk


    elif block_type == BlockType.VOLTAGE_SOURCE_EMT:
        blk = tem.get_voltage_source_emt_template(vf=var_factory,
                                              phN=phase_n,
                                              phA=phase_a,
                                              phB=phase_b,
                                              phC=phase_c,
                                              name=item_name).block
        blk.name = item_name
        return blk

    elif block_type == BlockType.CURRENT_SOURCE_EMT:
        blk = tem.get_current_source_emt_template(vf=var_factory,
                                              phN=phase_n,
                                              phA=phase_a,
                                              phB=phase_b,
                                              phC=phase_c,
                                              name=item_name).block
        blk.name = item_name
        return blk

    elif block_type == BlockType.CONTROLLED_VOLTAGE_SOURCE_EMT:
        blk = tem.get_controlled_voltage_source_emt_template(vf=var_factory,
                                                         phN=phase_n,
                                                         phA=phase_a,
                                                         phB=phase_b,
                                                         phC=phase_c,
                                                         name=item_name).block
        blk.name = item_name
        return blk

    elif block_type == BlockType.CONTROLLED_CURRENT_SOURCE_EMT:
        blk = tem.get_controlled_current_source_emt_template(vf=var_factory,
                                                         phN=phase_n,
                                                         phA=phase_a,
                                                         phB=phase_b,
                                                         phC=phase_c,
                                                         name=item_name).block
        blk.name = item_name
        return blk

    elif block_type == BlockType.DC_VOLTAGE_SOURCE_EMT:
        blk = tem.get_dc_voltage_source_emt_template(vf=var_factory, name=item_name).block
        blk.name = item_name
        return blk

    elif block_type == BlockType.DC_CURRENT_SOURCE_EMT:
        blk = tem.get_dc_current_source_emt_template(vf=var_factory, name=item_name).block
        blk.name = item_name
        return blk

    elif block_type == BlockType.CONTROLLED_DC_VOLTAGE_SOURCE_EMT:
        blk = tem.get_controlled_dc_voltage_source_emt_template(vf=var_factory, name=item_name).block
        blk.name = item_name
        return blk

    elif block_type == BlockType.CONTROLLED_DC_CURRENT_SOURCE_EMT:
        blk = tem.get_controlled_dc_current_source_emt_template(vf=var_factory, name=item_name).block
        blk.name = item_name
        return blk

    # LOAD
    elif block_type == BlockType.R_LOAD_EMT:
        blk = tem.get_shunt_r_emt_template(vf=var_factory,
                                       phA=phase_a,
                                       phB=phase_b,
                                       phC=phase_c,
                                       name=item_name).block
        blk.name = item_name
        return blk

    elif block_type == BlockType.L_LOAD_EMT:
        blk = tem.get_shunt_l_emt_template(vf=var_factory,
                                       phA=phase_a,
                                       phB=phase_b,
                                       phC=phase_c,
                                       name=item_name).block
        blk.name = item_name
        return blk
    elif block_type == BlockType.C_LOAD_EMT:
        blk = tem.get_shunt_c_emt_template(vf=var_factory,
                                       phA=phase_a,
                                       phB=phase_b,
                                       phC=phase_c,
                                       name=item_name).block
        blk.name = item_name
        return blk

    elif block_type == BlockType.EXP_LOAD_EMT:
        blk = tem.get_exponential_load_emt(vf=var_factory,
                                       phA=phase_a,
                                       phB=phase_b,
                                       phC=phase_c,
                                       name=item_name).block
        blk.name = item_name
        return blk

    elif block_type == BlockType.ZIP_LOAD_EMT:
        blk = tem.get_load_ZIP_emt_template(vf=var_factory,
                                       phA=phase_a,
                                       phB=phase_b,
                                       phC=phase_c,
                                       name=item_name).block
        blk.name = item_name
        return blk

    else:
        return None

def create_generic_block(var_factory: VarFactory,
                         inputs: int,
                         outputs: int,
                         name: str = "generic"
                         ) -> Block:
    """

    :param var_factory:
    :param inputs:
    :param outputs:
    :param name:
    :return:
    """
    blk = generic(var_factory, inputs, outputs)
    blk.name = name
    return blk
