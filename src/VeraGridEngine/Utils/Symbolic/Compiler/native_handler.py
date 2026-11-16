# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.Utils.Symbolic.block import Block


class NativeBlockCompiler:
    __slots__ = ("hash_code",)

    def __init__(self, bl: Block, folder: str):
        pass
        self.hash_code = "000" # TODO : find out how to het the unique block hash

    def save(self):
        pass


class NativeBlockInterpreter:
    __slots__ = ()

    def __init__(self, hash_code: str, folder: str):
        pass

    def fn(self):
        pass

    def dfn(self):
        pass