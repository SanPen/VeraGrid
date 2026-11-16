# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Event parameters are evaluated once in dependency order."""

import numpy as np
import pytest

from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.Utils.Symbolic.jit_compiler import RMSCompiler, RMSCompilerVec
from VeraGridEngine.Utils.Symbolic.jit_compiler_rms_numba_comp import (
    RMSCompiler as NumbaRMSCompiler,
    RMSCompilerVec as NumbaRMSCompilerVec,
)


@pytest.mark.parametrize("compiler_type", [RMSCompiler, RMSCompilerVec,
                                             NumbaRMSCompiler, NumbaRMSCompilerVec])
def test_event_parameter_chain_in_reverse_declaration_order(compiler_type):
    a, b, c = Var("a"), Var("b"), Var("c")
    params = [c, b, a]
    names = {parameter.uid: f"vprms[{i}]" for i, parameter in enumerate(params)}
    compiler = compiler_type([], [], params, [], names)
    aliases = {parameter.uid: f"vprms_{i}" for i, parameter in enumerate(params)}
    fn = compiler.compile_event_params_fn(
        [b + 1, a + 1, a + 1], aliases, "vprms", "glob_time")
    np.testing.assert_allclose(fn(np.ones(3), 0.0), [4, 3, 2])


@pytest.mark.parametrize("compiler_type", [RMSCompiler, RMSCompilerVec,
                                             NumbaRMSCompiler, NumbaRMSCompilerVec])
def test_event_parameter_cycle_is_rejected(compiler_type):
    a, b = Var("a"), Var("b")
    names = {a.uid: "vprms[0]", b.uid: "vprms[1]"}
    compiler = compiler_type([], [], [a, b], [], names)
    with pytest.raises(ValueError, match="Cyclic event-parameter dependencies"):
        compiler.compile_event_params_fn([b + 1, a + 1], {}, "vprms", "glob_time")


@pytest.mark.parametrize("compiler_type", [RMSCompiler, RMSCompilerVec,
                                             NumbaRMSCompiler, NumbaRMSCompilerVec])
def test_self_reference_reads_incoming_parameter_value(compiler_type):
    a = Var("a")
    compiler = compiler_type([], [], [a], [], {a.uid: "vprms[0]"})
    fn = compiler.compile_event_params_fn([a + 1], {}, "vprms", "glob_time")
    np.testing.assert_allclose(fn(np.array([5.0]), 0.0), [6.0])
