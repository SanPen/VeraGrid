# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from VeraGridEngine.basic_structures import Logger


def try_float(val: str, device: str, prop_name: str, logger: Logger, fallback_value: float = 0):
    """

    :param val:
    :param device:
    :param prop_name:
    :param logger:
    :param fallback_value:
    :return:
    """
    try:
        return float(val)
    except ValueError as e:
        logger.add_error(msg=str(e),
                         device=device,
                         device_property=prop_name,
                         value=val)
        return fallback_value


def sub_float(line: str, a: int, b: int, device: str, prop_name: str, logger: Logger,
              fallback_value: float = 0.0) -> float:
    """
    Try to get a value from a substring
    :param line: string
    :param a: start point
    :param b: end+1 point
    :param device: device type name
    :param prop_name: property name
    :param logger: Logger to record issues
    :param fallback_value: Value to set on error
    :return: float
    """
    if len(line) > b:
        chunk = line[a:b].strip()

        try:
            return float(chunk)
        except ValueError as e:
            logger.add_error(msg=str(e),
                             device=device,
                             device_property=prop_name,
                             value=chunk)
            return fallback_value
    else:
        logger.add_error(msg=f"Could not parse {prop_name} because the file row is too short",
                         device=device,
                         device_property=prop_name,
                         value=line,
                         expected_value=b)
        return fallback_value


def try_int(val: str, device: str, prop_name: str, logger: Logger, fallback_value: int = 0):
    """

    :param val:
    :param device:
    :param prop_name:
    :param logger:
    :param fallback_value:
    :return:
    """
    try:
        return int(val)
    except ValueError as e:
        logger.add_error(msg=str(e),
                         device=device,
                         device_property=prop_name,
                         value=val)
        return fallback_value


def sub_int(line: str, a: int, b: int, device: str, prop_name: str, logger: Logger,
            fallback_value: int = 0) -> int:
    """
    Try to get a value from a substring
    :param line: string
    :param a: start point
    :param b: end+1 point
    :param device: device type name
    :param prop_name: property name
    :param logger: Logger to record issues
    :param fallback_value: Value to set on error
    :return: int
    """
    if len(line) > b:
        chunk = line[a:b].strip()

        try:
            return int(chunk)
        except ValueError as e:
            logger.add_error(msg=str(e),
                             device=device,
                             device_property=prop_name,
                             value=chunk)
            return fallback_value
    else:
        logger.add_error(msg=f"Could not parse {prop_name} because the file row is too short",
                         device=device,
                         device_property=prop_name,
                         value=line,
                         expected_value=b)
        return fallback_value


def sub_str(line: str, a: int, b: int, device: str, prop_name: str, logger: Logger,
            fallback_value: str = "") -> str:
    """
    Try to get a value from a substring
    :param line: string
    :param a: start point
    :param b: end+1 point
    :param device: device type name
    :param prop_name: property name
    :param logger: Logger to record issues
    :param fallback_value: Value to set on error
    :return: string
    """

    if len(line) > b:
        chunk = line[a:b].strip()
        return chunk
    else:
        logger.add_error(msg=f"Could not parse {prop_name} because the file row is too short",
                         device=device,
                         device_property=prop_name,
                         value=line,
                         expected_value=b)
        return fallback_value
