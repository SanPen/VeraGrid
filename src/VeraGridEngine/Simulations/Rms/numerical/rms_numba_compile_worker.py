# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Compile small scalar RMS kernel groups outside the numerical process."""

import importlib.util
import multiprocessing
import sys
import traceback
from multiprocessing.connection import Connection
from pathlib import Path
from time import perf_counter
from types import FunctionType
from typing import Any

from numba import njit
from numba.core.event import Event, Listener, TimingListener, install_listener
from numba.core.registry import CPUDispatcher


class KernelCompileJob:
    """Describe one generated function without retaining its symbolic graph."""

    __slots__ = ("module_name", "module_path", "function_name", "signature")

    def __init__(self, module_name: str, module_path: str, function_name: str, signature: Any) -> None:
        """Record only the import location, function name and eager signature.

        :param module_name: Stable generated or engine module name.
        :param module_path: Absolute Python source location.
        :param function_name: Function inside that module.
        :param signature: Numba eager signature.
        :return: None.
        """
        self.module_name: str = module_name
        self.module_path: str = module_path
        self.function_name: str = function_name
        self.signature: Any = signature


class LoadedKernel:
    """Keep a cache-loaded dispatcher and independently measured worker time."""

    __slots__ = ("dispatcher", "compile_seconds", "load_seconds")

    def __init__(self, dispatcher: Any, compile_seconds: float, load_seconds: float) -> None:
        """Capture one successfully loaded native function.

        :param dispatcher: Verified cache-hit dispatcher in the numerical process.
        :param compile_seconds: Actual compilation seconds reported by the worker.
        :param load_seconds: Time loading the cached specialization.
        :return: None.
        """
        self.dispatcher: Any = dispatcher
        self.compile_seconds: float = compile_seconds
        self.load_seconds: float = load_seconds


class KernelCompileReport:
    """Return bounded timing/error data across the process boundary."""

    __slots__ = ("seconds", "error")

    def __init__(self, seconds: tuple[float, ...], error: str | None) -> None:
        """Store actual event times and an optional compilation traceback.

        :param seconds: One exclusive Numba event duration per submitted function.
        :param error: Traceback on failure; None after success.
        :return: None.
        """
        self.seconds: tuple[float, ...] = seconds
        self.error: str | None = error


class CacheOnlyListener(Listener):
    """Refuse a cache miss before Numba starts compiling in the numerical process."""

    __slots__ = ()

    def on_start(self, event: Event) -> None:
        """Abort immediately when a dispatcher would enter its compiler.

        :param event: Numba compilation-start notification.
        :return: None.
        :raises RuntimeError: Always; numerical-process compilation is forbidden.
        """
        raise RuntimeError("RMS cache entry disappeared or is incompatible; numerical-process compilation is forbidden")

    def on_end(self, event: Event) -> None:
        """Accept an end notification without changing the refusal marker.

        :param event: Numba compilation-end notification.
        :return: None.
        """
        pass


def kernel_compile_job(function: Any, signature: Any) -> KernelCompileJob:
    """Extract a small importable descriptor from a Python or native function.

    :param function: Generated Python function or an existing lazy dispatcher.
    :param signature: Required eager specialization.
    :return: Graph-free compiler job.
    """
    python_function: FunctionType
    if isinstance(function, CPUDispatcher):
        python_function = function.py_func
    else:
        assert isinstance(function, FunctionType)
        python_function = function
    return KernelCompileJob(python_function.__module__, str(Path(python_function.__code__.co_filename).resolve()),
                            python_function.__name__, signature)


def resolve_kernel(job: KernelCompileJob) -> FunctionType:
    """Import exactly the module whose source identity defines Numba's cache key.

    :param job: Function location and eager signature.
    :return: Undecorated Python function with its original module identity.
    """
    if job.module_name not in sys.modules:
        specification = importlib.util.spec_from_file_location(job.module_name, job.module_path)
        assert specification is not None and specification.loader is not None
        module = importlib.util.module_from_spec(specification)
        sys.modules[job.module_name] = module
        specification.loader.exec_module(module)
    else:
        pass
    function: Any = sys.modules[job.module_name].__dict__[job.function_name]
    if isinstance(function, CPUDispatcher):
        return function.py_func
    else:
        assert isinstance(function, FunctionType)
        return function


def load_cached_kernel(job: KernelCompileJob, allow_miss: bool = False) -> LoadedKernel | None:
    """Load a specialization while prohibiting fallback compilation.

    :param job: Exact source, signature and common RMS compilation options.
    :param allow_miss: Return None on a missing cache entry during preflight.
    :return: Verified cache-hit kernel, or None for an allowed miss.
    :raises LookupError: Missing cache entry during mandatory loading.
    :raises RuntimeError: Numba did not confirm a cache hit.
    """
    function: FunctionType = resolve_kernel(job)
    started: float = perf_counter()
    dispatcher: Any = njit(cache=True, fastmath=False, error_model="numpy")(function)
    # Check the exact installed Numba cache key before invoking compile(). A
    # normal miss must not emit a START event without END and poison surrounding
    # compilation timers. The listener below is a fail-closed race/corruption guard.
    key: Any = dispatcher._cache._index_key(job.signature, dispatcher.targetctx.codegen())
    cached_name: str | None = dispatcher._cache._cache_file._load_index().get(key, None)
    if cached_name is None:
        if allow_miss:
            return None
        else:
            raise LookupError(f"RMS kernel cache miss: {job.function_name}")
    else:
        pass
    listener: CacheOnlyListener = CacheOnlyListener()
    with install_listener("numba:compile", listener):
        dispatcher.compile(job.signature)
    # A fresh dispatcher must obtain its eager specialization from disk, never
    # from an unobserved in-memory overload or a silent compiler fallback.
    if sum(dispatcher._cache_hits.values()) < 1:
        raise RuntimeError(f"Numba did not confirm a cache hit for {job.function_name}")
    else:
        pass
    dispatcher.disable_compile()
    return LoadedKernel(dispatcher, 0.0, perf_counter() - started)


def compile_kernel_group(jobs: tuple[KernelCompileJob, ...], connection: Connection) -> None:
    """Compile a small group, publish its cache entries and exit with no grid data.

    :param jobs: Importable function descriptors; no equations or network objects.
    :param connection: One-way report channel owned by this temporary worker.
    :return: None.
    """
    seconds: list[float] = list(0.0 for _ in jobs)
    report: KernelCompileReport
    try:
        index: int
        job: KernelCompileJob
        for index, job in enumerate(jobs):
            function: FunctionType = resolve_kernel(job)
            timer: TimingListener = TimingListener()
            with install_listener("numba:compile", timer):
                dispatcher: Any = njit(job.signature, cache=True, fastmath=False, error_model="numpy")(function)
            seconds[index] = timer.duration if timer.done else 0.0
        report = KernelCompileReport(tuple(seconds), None)
    except BaseException:
        report = KernelCompileReport(tuple(seconds), traceback.format_exc())
    try:
        connection.send(report)
    finally:
        connection.close()


def prepare_kernel_group(jobs: tuple[KernelCompileJob, ...]) -> tuple[LoadedKernel, ...]:
    """Compile only misses in one disposable process, then require cache-only loads.

    :param jobs: Small group of residual/JVP or helper function descriptors.
    :return: Loaded kernels in input order, including actual child compilation time.
    :raises RuntimeError: Worker failure or missing/incompatible cache output.
    """
    loaded: list[LoadedKernel | None] = list(load_cached_kernel(job, allow_miss=True) for job in jobs)
    missing: list[int] = list(index for index, kernel in enumerate(loaded) if kernel is None)
    if missing:
        context: multiprocessing.context.BaseContext = multiprocessing.get_context("spawn")
        receive: Connection
        send: Connection
        receive, send = context.Pipe(duplex=False)
        worker: multiprocessing.Process = context.Process(
            target=compile_kernel_group, args=(tuple(jobs[index] for index in missing), send),
        )
        report: KernelCompileReport
        worker.start()
        send.close()
        try:
            # No compilation timeout: poll only to detect a dead worker and to
            # keep interruption/cleanup responsive while the compiler runs.
            while not receive.poll(0.1) and worker.is_alive():
                pass
            if receive.poll():
                report = receive.recv()
            else:
                raise RuntimeError(f"RMS compiler worker exited without a report: {worker.exitcode}")
            worker.join()
        except EOFError as worker_error:
            raise RuntimeError("RMS compiler worker closed its report channel unexpectedly") from worker_error
        finally:
            receive.close()
            if worker.is_alive():
                worker.terminate()
                worker.join(timeout=2.0)
                if worker.is_alive():
                    worker.kill()
                    worker.join()
                else:
                    pass
            else:
                pass
        if report.error is not None:
            raise RuntimeError("RMS compiler worker failed:\n" + report.error)
        elif worker.exitcode != 0:
            raise RuntimeError(f"RMS compiler worker failed with exit code {worker.exitcode}")
        else:
            pass
        # Join before loading: all compiler scratch and metadata have now been
        # released by the OS. Missing output is an error, never a recompilation.
        index: int
        for index, source_index in enumerate(missing):
            kernel: LoadedKernel | None = load_cached_kernel(jobs[source_index])
            assert kernel is not None
            kernel.compile_seconds = report.seconds[index]
            loaded[source_index] = kernel
    else:
        pass
    assert all(kernel is not None for kernel in loaded)
    return tuple(kernel for kernel in loaded if kernel is not None)
