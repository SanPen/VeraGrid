# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os
from VeraGridEngine.IO.file_open import FileOpen
from VeraGridEngine.IO.file_save import FileSave


def test_all_grids():
    # get the directory of this file

    # navigate to the grids folder
    grids_path = os.path.join('data', 'grids')

    files = os.listdir(grids_path)
    failed = list()
    for file_name in files:

        path = os.path.join(grids_path, file_name)

        print('-' * 160)
        print('Loading', file_name, '...', end='')
        try:
            file_handler = FileOpen(path)
            circuit = file_handler.open()

            print('ok')
        except:
            print('Failed')
            failed.append(file_name)

    print('Failed:')
    for f in failed:
        print('\t', f)

    for f in failed:
        print('Attempting', f)
        path = os.path.join(grids_path, f)
        file_handler = FileOpen(path)
        circuit = file_handler.open()

    assert len(failed) == 0


def test_line_templates_finding(tmp_path):
    """
    Test that checks that a line assigned a line template that is not a Sequence line can open it
    :return:
    """
    # navigate to the grids folder
    fname = os.path.join('data', 'grids', 'test_line_templates.gridcal')


    opener = FileOpen(fname)
    grid = opener.open()

    # it it fails, it may be because the file structure changed and the input file needs updating
    # FileSave(grid, str(fname)).save()

    normalized_fname = tmp_path / 'test_line_templates_normalized.gridcal'
    FileSave(grid, str(normalized_fname)).save()

    reopened = FileOpen(str(normalized_fname))
    reopened.open()

    if reopened.logger.has_logs():
        reopened.logger.print()

    assert not reopened.logger.has_logs()


def test_issue_337():

    # navigate to the grids folder
    fname = os.path.join('data', 'grids', 'RAW', 'issue_337.raw')

    grid = FileOpen(fname).open()

    print()
