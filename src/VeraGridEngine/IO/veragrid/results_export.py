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
import re
import numpy as np
import pandas as pd
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.Simulations.Rms.rms_results import RmsResults
from VeraGridEngine.Simulations.EMT.emt_results import EmtResults

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


def _build_dynamic_group_identity(group_idx: int,
                                  group_names: np.ndarray,
                                  group_idtags: np.ndarray) -> str:
    """
    Build one stable archive label for one dynamic event group.

    :param group_idx: Event-group positional index.
    :param group_names: Event-group display names.
    :param group_idtags: Event-group stable identifiers.
    :return: Archive-safe group identity string.
    """
    group_name: str = ""
    group_idtag: str = ""

    if group_idx >= 0 and group_idx < len(group_names):
        group_name = str(group_names[group_idx])
    else:
        group_name = ""

    if group_idx >= 0 and group_idx < len(group_idtags):
        group_idtag = str(group_idtags[group_idx])
    else:
        group_idtag = ""

    # The exported filename should reflect the visible event-group name because
    # that is the label the user recognizes in the GUI. The numeric prefix
    # preserves ordering, and the fallback keeps unnamed groups exportable.
    if group_name != "":
        identity_text: str = f"{group_idx:03d}_{group_name}"
    else:
        if group_idtag != "":
            identity_text = f"{group_idx:03d}_group"
        else:
            identity_text = f"{group_idx:03d}_group"

    # sanitize zip name part
    raw_text: str = str(identity_text)

    # Event-group names are user-provided labels, therefore they may contain
    # path separators or punctuation that would create ambiguous zip paths.
    # Normalizing them up front keeps the archive structure deterministic.
    sanitized_text: str = re.sub(r'[\\/:*?"<>|]+', '_', raw_text)
    sanitized_text = re.sub(r'\s+', ' ', sanitized_text).strip()

    if sanitized_text == "":
        return "unnamed_group"
    else:
        return sanitized_text

def _write_dataframe_to_zip(dataframe: pd.DataFrame,
                            filename: str,
                            myzip: zipfile.ZipFile,
                            logger: Logger) -> None:
    """
    Serialize one DataFrame into the destination zip archive.

    :param dataframe: Table to serialize.
    :param filename: Destination zip member path.
    :param myzip: Open zip archive.
    :param logger: Logger used to record serialization problems.
    :return: None.
    """
    with StringIO() as buffer:
        try:
            dataframe.to_csv(buffer)
            myzip.writestr(filename, buffer.getvalue())
        except ValueError:
            logger.add_error('Value error', filename)


def _export_rms_results_to_zip(results: RmsResults,
                               myzip: zipfile.ZipFile,
                               text_func: Union[Callable[[str], None], None],
                               logger: Logger) -> None:
    """
    Export RMS dynamic results as one CSV per simulated event group.

    :param results: RMS results object.
    :param myzip: Open zip archive.
    :param text_func: Optional progress text callback.
    :param logger: Logger used to record serialization problems.
    :return: None.
    """
    n_vars: int = len(results.variables)
    variable_labels: np.ndarray = np.empty(n_vars, dtype=object)
    var_index: int
    for var_index in range(n_vars):
        variable_labels[var_index] = str(results.uid2vars_glob_name[results.variables[var_index].uid])

    group_idx: int

    # The RMS payload is three-dimensional: time, variable, event-group.
    # Exporting one group at a time preserves the natural simulation structure
    # expected by downstream post-processing scripts.
    for group_idx in range(results.ng):
        has_group_results: bool = bool(results.has_event_group_results[group_idx])

        if has_group_results:
            group_identity: str = _build_dynamic_group_identity(group_idx=group_idx,
                                                                group_names=results.rms_events_group_names,
                                                                group_idtags=results.rms_events_group_idtags)
            filename: str = f"RMS simulation/{group_identity}.csv"

            if text_func is not None:
                text_func(f"flushing {results.name} {filename}")
            else:
                pass

            # Slicing the third axis isolates the one simulation case that the
            # user wants to post-process independently.
            group_values: np.ndarray = results.values[:, :, group_idx]
            dataframe: pd.DataFrame = pd.DataFrame(data=group_values,
                                                   index=results.time_array,
                                                   columns=variable_labels)
            _write_dataframe_to_zip(dataframe=dataframe,
                                    filename=filename,
                                    myzip=myzip,
                                    logger=logger)
        else:
            logger.add_info('Skipping RMS event group without runtime results',
                            device=str(results.rms_events_group_names[group_idx]))


def _export_emt_results_to_zip(results: EmtResults,
                               myzip: zipfile.ZipFile,
                               text_func: Union[Callable[[str], None], None],
                               logger: Logger) -> None:
    """
    Export EMT dynamic results as one CSV per simulated event group and payload kind.

    :param results: EMT results object.
    :param myzip: Open zip archive.
    :param text_func: Optional progress text callback.
    :param logger: Logger used to record serialization problems.
    :return: None.
    """
    n_vars: int = len(results.variables)
    value_labels: np.ndarray = np.empty(n_vars, dtype=object)
    var_index: int
    for var_index in range(n_vars):
        value_labels[var_index] = str(results.uid2vars_glob_name[results.variables[var_index].uid])

    n_vars: int = len(results.diff_variables)
    diff_value_labels: np.ndarray = np.empty(n_vars, dtype=object)
    var_index: int
    for var_index in range(n_vars):
        diff_value_labels[var_index] = str(results.uid2vars_glob_name[results.diff_variables[var_index].uid])

    group_idx: int

    # EMT carries two runtime namespaces: algebraic/state values and their
    # differential-variable payload. Both are needed for faithful external
    # post-processing, therefore both tables are exported for each active group.
    for group_idx in range(results.ng):
        has_group_results: bool = bool(results.has_event_group_results[group_idx])

        if has_group_results:
            group_identity: str = _build_dynamic_group_identity(group_idx=group_idx,
                                                                group_names=results.emt_events_group_names,
                                                                group_idtags=results.emt_events_group_idtags)

            values_filename: str = f"EMT simulation/{group_identity}.csv"
            diff_values_filename: str = f"EMT simulation/{group_identity}_diff_values.csv"

            if text_func is not None:
                text_func(f"flushing {results.name} {values_filename}")
            else:
                pass

            values_payload: np.ndarray = results.values[:, :, group_idx]
            values_dataframe: pd.DataFrame = pd.DataFrame(data=values_payload,
                                                          index=results.time_array,
                                                          columns=value_labels)
            _write_dataframe_to_zip(dataframe=values_dataframe,
                                    filename=values_filename,
                                    myzip=myzip,
                                    logger=logger)

            if text_func is not None:
                text_func(f"flushing {results.name} {diff_values_filename}")
            else:
                pass

            diff_values_payload: np.ndarray = results.diff_values[:, :, group_idx]
            diff_values_dataframe: pd.DataFrame = pd.DataFrame(data=diff_values_payload,
                                                               index=results.time_array,
                                                               columns=diff_value_labels)
            _write_dataframe_to_zip(dataframe=diff_values_dataframe,
                                    filename=diff_values_filename,
                                    myzip=myzip,
                                    logger=logger)
        else:
            logger.add_info('Skipping EMT event group without runtime results',
                            device=str(results.emt_events_group_names[group_idx]))


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
                try:
                    if progress_func is not None:
                        progress_func((k + 1) / n * 100.0)
                    else:
                        pass

                    # Dynamic RMS results are stored as a 3D tensor, therefore
                    # they cannot be exported through the generic ResultsTable
                    # path that assumes a single 2D table per result type.
                    if isinstance(results, RmsResults):
                        _export_rms_results_to_zip(results=results,
                                                   myzip=myzip,
                                                   text_func=text_func,
                                                   logger=logger)
                    else:
                        # EMT follows the same per-group export strategy, but it
                        # carries two runtime payload namespaces that must both
                        # be exported for complete external post-processing.
                        if isinstance(results, EmtResults):
                            _export_emt_results_to_zip(results=results,
                                                       myzip=myzip,
                                                       text_func=text_func,
                                                       logger=logger)
                        else:
                            if isinstance(results.available_results, dict):
                                available_res = [e for tpe, lst in results.available_results.items() for e in lst]
                            else:
                                available_res = results.available_results

                            for available_result in available_res:

                                # The generic branch keeps the historical export
                                # behavior for studies that already describe
                                # themselves as 2D ResultsTable objects.
                                result_name = str(available_result.value)

                                if text_func is not None:
                                    text_func('flushing ' + results.name + ' ' + result_name)
                                else:
                                    pass

                                mdl = results.mdl(result_type=available_result)

                                if mdl is not None:
                                    with StringIO() as buffer:
                                        raw_text: str = str(results.name + ' ' + result_name + '.csv')

                                        # Windows extraction rejects path segments containing reserved filename
                                        # characters such as ``:``. Removing those characters keeps the archive
                                        # portable while preserving the original wording as closely as possible.
                                        filename: str = re.sub(r'[\\:*?"<>|]+', '', raw_text)
                                        filename = re.sub(r'/+', '/', filename)
                                        filename = re.sub(r'\s+', ' ', filename).strip()
                                        if filename == "":
                                            filename = "unnamed_result.csv"

                                        try:
                                            mdl.save_to_csv(buffer)
                                            myzip.writestr(filename, buffer.getvalue())
                                        except ValueError:
                                            logger.add_error('Value error', filename)
                                else:
                                    logger.add_info('No results for ' + results.name + ' - ' + result_name)
                finally:
                    # Plotting is re-enabled unconditionally so any later GUI
                    # visualization behaves exactly as before the archive export.
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
