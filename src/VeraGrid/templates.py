# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

from typing import List
import os
import pandas as pd
import json
from VeraGridEngine.Devices.Branches.line import SequenceLineType, UndergroundLineType
from VeraGridEngine.Devices.Branches.transformer import TransformerType
from VeraGridEngine.Devices.Branches.wire import Wire
from VeraGridEngine.Templates.Rms.bus_rms_template import BusRmsTemplate
from VeraGridEngine.Templates.Rms.generator_rms_template import get_generator_rms_template
from VeraGridEngine.Templates.Rms.line_rms_template import get_line_rms_template
from VeraGridEngine.Templates.Rms.load_rms_template import LoadRmsTemplate
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.IO.veragrid.catalogue import (parse_transformer_types, parse_cable_types, parse_wire_types,
                                                  parse_sequence_line_types)


def get_transformer_catalogue() -> List[TransformerType]:
    """

    :return:
    """
    here = os.path.dirname(os.path.abspath(__file__))
    fname = os.path.join(here, 'data', 'transformers.csv')

    if os.path.exists(fname):
        df = pd.read_csv(fname)

        return parse_transformer_types(df)
    else:
        return list()


def get_cables_catalogue() -> List[UndergroundLineType]:
    """

    :return:
    """
    here = os.path.dirname(os.path.abspath(__file__))
    fname = os.path.join(here, 'data', 'cables.csv')

    if os.path.exists(fname):
        df = pd.read_csv(fname)

        return parse_cable_types(df)
    else:
        return list()


def get_wires_catalogue() -> List[Wire]:
    """

    :return:
    """
    here = os.path.dirname(os.path.abspath(__file__))
    fname = os.path.join(here, 'data', 'wires.csv')

    if os.path.exists(fname):
        df = pd.read_csv(fname)

        return parse_wire_types(df)
    else:
        return list()


def get_sequence_lines_catalogue() -> List[SequenceLineType]:
    """

    :return:
    """
    here = os.path.dirname(os.path.abspath(__file__))
    fname = os.path.join(here, 'data', 'sequence_lines.csv')

    if os.path.exists(fname):
        df = pd.read_csv(fname)

        return parse_sequence_line_types(df)
    else:
        return list()


def get_rms_model_catalogue() -> List[RmsModelTemplate]:
    """
    Here the list of all rms templates must be returned in a list
    :return:
    """
    return [get_generator_rms_template(),
            get_line_rms_template(),
            LoadRmsTemplate()]
