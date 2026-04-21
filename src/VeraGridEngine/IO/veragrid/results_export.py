# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import os
import time
from typing import List, Callable, Union, TYPE_CHECKING
from io import StringIO
import zipfile
from VeraGridEngine.basic_structures import Logger

if TYPE_CHECKING:
    from VeraGridEngine.Simulations.types import DRIVER_OBJECTS, RESULTS_OBJECTS


def _wait_until_file_is_releasable(file_name: str, timeout_s: float = 2.0) -> None:
    """
    Wait until a freshly written archive can be reopened.

    :param file_name: Output archive path.
    :param timeout_s: Maximum wait time in seconds.
    :return: None.
    """
    deadline: float = time.perf_counter() + timeout_s

    while True:
        try:
            with open(file_name, "rb"):
                return
        except PermissionError:
            if time.perf_counter() >= deadline:
                return
            time.sleep(0.05)


def export_results(results_list: List[RESULTS_OBJECTS],
                   file_name: str,
                   text_func: Union[Callable[[str], None], None] = None,
                   progress_func: Union[Callable[[float], None], None] = None,
                   logger: Logger = Logger()):
    """
    Constructor
    :param results_list: list of VeraGrid simulation results
    :param file_name: name of the file where to save (.zip)
    :param text_func: text function
    :param progress_func: progress function
    :param logger: logging object
    """

    # try:
    path, fname = os.path.split(file_name)

    if text_func is not None:
        text_func('Flushing ' + fname + ' into ' + fname + '...')

    # open zip file for writing
    try:
        with zipfile.ZipFile(file_name, 'w', zipfile.ZIP_DEFLATED) as myzip:

            n = len(results_list)

            for k, results in enumerate(results_list):

                # deactivate plotting
                results.deactivate_plotting()

                if progress_func is not None:
                    progress_func((k + 1) / n * 100.0)

                if isinstance(results.available_results, dict):
                    available_res = [e for tpe, lst in results.available_results.items() for e in lst]
                else:
                    available_res = results.available_results

                for available_result in available_res:

                    # ge the result type definition
                    result_name = str(available_result.value)

                    if text_func is not None:
                        text_func('flushing ' + results.name + ' ' + result_name)

                    # save the DataFrame to the buffer
                    mdl = results.mdl(result_type=available_result)

                    if mdl is not None:
                        with StringIO() as buffer:
                            filename = results.name + ' ' + result_name + '.csv'
                            try:
                                mdl.save_to_csv(buffer)
                                myzip.writestr(filename, buffer.getvalue())
                            except ValueError:
                                logger.add_error('Value error', filename)
                    else:
                        logger.add_info('No results for ' + results.name + ' - ' + result_name)

                # reactivate plotting
                results.activate_plotting()

    except PermissionError:
        logger.add('Permission error.\nDo you have the file open?')

    if os.path.exists(file_name):
        _wait_until_file_is_releasable(file_name=file_name)
    else:
        pass

    # post events
    if text_func is not None:
        text_func('Done!')


def export_drivers(drivers_list: List[DRIVER_OBJECTS],
                   file_name: str,
                   text_func: Union[Callable[[str], None], None] = None,
                   progress_func: Union[Callable[[float], None], None] = None,
                   logger: Logger = Logger()):
    """
    Constructor
    :param drivers_list: list of VeraGrid simulation drivers
    :param file_name: name of the file where to save (.zip)
    :param text_func: text function
    :param progress_func: progress function
    :param logger: logging object
    """

    results_list = [drv.results for drv in drivers_list]

    export_results(results_list=results_list,
                   file_name=file_name,
                   text_func=text_func,
                   progress_func=progress_func,
                   logger=logger)
