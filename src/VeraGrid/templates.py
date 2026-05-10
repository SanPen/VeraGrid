# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

import copy
from functools import lru_cache
from typing import List
import os
import pandas as pd
from VeraGridEngine.Devices.Branches.line import SequenceLineType, UndergroundLineType
from VeraGridEngine.Devices.Branches.transformer import TransformerType
from VeraGridEngine.Devices.Branches.wire import Wire
from VeraGridEngine.IO.veragrid.catalogue import (parse_transformer_types, parse_cable_types, parse_wire_types,
                                                  parse_sequence_line_types)


@lru_cache(maxsize=1)
def _get_transformer_catalogue_cached() -> tuple[TransformerType, ...]:
    """
    Return the cached default transformer catalogue.

    :return: Immutable cached transformer tuple.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    fname = os.path.join(here, 'data', 'transformers.csv')

    if os.path.exists(fname):
        df = pd.read_csv(fname)
        return tuple(parse_transformer_types(df))
    else:
        return tuple()


@lru_cache(maxsize=1)
def _get_cables_catalogue_cached() -> tuple[UndergroundLineType, ...]:
    """
    Return the cached default cable catalogue.

    :return: Immutable cached cable tuple.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    fname = os.path.join(here, 'data', 'cables.csv')

    if os.path.exists(fname):
        df = pd.read_csv(fname)
        return tuple(parse_cable_types(df))
    else:
        return tuple()


@lru_cache(maxsize=1)
def _get_wires_catalogue_cached() -> tuple[Wire, ...]:
    """
    Return the cached default wire catalogue.

    :return: Immutable cached wire tuple.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    fname = os.path.join(here, 'data', 'wires.csv')

    if os.path.exists(fname):
        df = pd.read_csv(fname)
        return tuple(parse_wire_types(df))
    else:
        return tuple()


@lru_cache(maxsize=1)
def _get_sequence_lines_catalogue_cached() -> tuple[SequenceLineType, ...]:
    """
    Return the cached default sequence-line catalogue.

    :return: Immutable cached sequence-line tuple.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    fname = os.path.join(here, 'data', 'sequence_lines.csv')

    if os.path.exists(fname):
        df = pd.read_csv(fname)
        return tuple(parse_sequence_line_types(df))
    else:
        return tuple()


def get_transformer_catalogue() -> List[TransformerType]:
    """

    :return:
    """
    return copy.deepcopy(list(_get_transformer_catalogue_cached()))


def get_cables_catalogue() -> List[UndergroundLineType]:
    """

    :return:
    """
    return copy.deepcopy(list(_get_cables_catalogue_cached()))


def get_wires_catalogue() -> List[Wire]:
    """

    :return:
    """
    return copy.deepcopy(list(_get_wires_catalogue_cached()))


def get_sequence_lines_catalogue() -> List[SequenceLineType]:
    """

    :return:
    """
    return copy.deepcopy(list(_get_sequence_lines_catalogue_cached()))



