# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.versioned.base.impedance_correction_table import RawImpedanceCorrectionTable


class RawImpedanceCorrectionTableV29(RawImpedanceCorrectionTable):
    """PSSE v29 typed object."""

    def parse(self, data, version, logger: Logger):
        self.version = version
        self.I = -1
        all_data = []
        for row in data:
            all_data += row

        if len(all_data) == 0:
            logger.add_error('No impedance table data', str(version))
            return

        self.I = int(all_data.pop(0))

        if len(all_data) % 3 == 0:
            k = 0
            while k < len(all_data):
                if not (all_data[k] == 0 and all_data[k + 1] == 0 and all_data[k + 2] == 0):
                    self.T.append(all_data[k])
                    self.F_re.append(all_data[k + 1])
                    self.F_im.append(all_data[k + 2])
                k += 3
        elif len(all_data) % 2 == 0:
            k = 0
            while k < len(all_data) - 1:
                if not (all_data[k] == 0 and all_data[k + 1] == 0 and all_data[k + 2] == 0):
                    self.T.append(all_data[k])
                    self.F_re.append(all_data[k + 1])
                    self.F_im.append(0.0)
                k += 3
        else:
            logger.add_error('Impedance correction values not divisible by 3 nor 4, hence they are wrong :(',
                             str(version))

    def get_raw_line(self, version):
        data = [self.I]
        for k in range(12):
            data.append(self.T[k])
            data.append(self.F_re[k])
            data.append(self.F_im[k])
        return ", ".join(data)
