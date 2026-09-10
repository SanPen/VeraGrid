from __future__ import annotations

import faulthandler
import multiprocessing
import queue
import random
import time
import traceback
from typing import Any, List

import shiboken6
from PySide6 import QtCore
from PySide6 import QtWidgets

from tests.GUI.test_dialog_smoke import DialogSmokeContext
from tests.GUI.test_dialog_smoke import DialogSmokeTarget
from tests.GUI.test_dialog_smoke import build_dialog_for_smoke
from tests.GUI.test_dialog_smoke import close_dialog_for_smoke


def build_stress_target_sequence(cycles: int, seed: int) -> List[DialogSmokeTarget]:
    """
    Build a deterministic dialog sequence for repeated GUI lifecycle stress.

    :param cycles: Number of dialog open/close operations to exercise.
    :param seed: Shuffle seed used to keep failures reproducible.
    :return: Ordered dialog targets.
    """
    random_generator: random.Random = random.Random(seed)
    all_targets: List[DialogSmokeTarget] = list(DialogSmokeTarget)
    sequence: List[DialogSmokeTarget] = list()

    while len(sequence) < cycles:
        shuffled_targets: List[DialogSmokeTarget] = list(all_targets)
        random_generator.shuffle(shuffled_targets)

        target: DialogSmokeTarget
        for target in shuffled_targets:
            if len(sequence) < cycles:
                sequence.append(target)
            else:
                pass

    return sequence


def drain_qt_events(app: QtWidgets.QApplication) -> None:
    """
    Let Qt finish deferred construction, repaint and delete work.

    :param app: Shared Qt application.
    :return: None.
    """
    event_index: int
    for event_index in range(3):
        app.processEvents()
        QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)


def run_gui_stress_smoke_in_child(message_queue: Any, cycles: int, seed: int) -> None:
    """
    Repeatedly open and close GUI dialogs in a disposable child process.

    :param message_queue: Parent-visible queue receiving progress and failures.
    :param cycles: Number of dialog lifecycle operations.
    :param seed: Deterministic target-order seed.
    :return: None.
    """
    faulthandler.enable()

    app: QtWidgets.QApplication | None = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(list(("gui-stress-smoke", "-platform", "offscreen")))
    else:
        pass

    sequence: List[DialogSmokeTarget] = build_stress_target_sequence(cycles=cycles, seed=seed)
    cycle: int
    target: DialogSmokeTarget
    for cycle, target in enumerate(sequence):
        context: DialogSmokeContext = DialogSmokeContext(app=app)
        dialog: QtWidgets.QWidget | None = None
        message: str = f"{cycle + 1}/{cycles}: {target.value}"
        message_queue.put(message)

        try:
            dialog = build_dialog_for_smoke(target=target, context=context)
            dialog.show()
            drain_qt_events(app=app)
            assert shiboken6.isValid(dialog)
        except Exception:
            message_queue.put(f"{message}\n{traceback.format_exc()}")
            raise
        finally:
            if dialog is None:
                pass
            else:
                close_dialog_for_smoke(dialog=dialog, app=app)

        active_modal_widget: QtWidgets.QWidget | None = app.activeModalWidget()
        if active_modal_widget is None:
            pass
        else:
            message_queue.put(f"{message}\nleft active modal widget: {active_modal_widget}")
            raise AssertionError(f"{target.value} left active modal widget")


def run_gui_stress_smoke_subprocess(cycles: int, timeout_s: float, seed: int) -> None:
    """
    Run repeated GUI lifecycle stress outside the parent pytest process.

    :param cycles: Number of dialog lifecycle operations.
    :param timeout_s: Maximum interval without child-process progress in seconds.
    :param seed: Deterministic target-order seed.
    :return: None.
    """
    process_context: multiprocessing.context.BaseContext = multiprocessing.get_context("spawn")
    message_queue: Any = process_context.Queue()
    process: multiprocessing.Process = process_context.Process(
        target=run_gui_stress_smoke_in_child,
        args=(message_queue, cycles, seed),
    )

    process.start()
    message: str = ""
    last_progress_time_s: float = time.monotonic()

    while process.is_alive() and time.monotonic() - last_progress_time_s <= timeout_s:
        try:
            queued_message: object = message_queue.get(timeout=1.0)
            if isinstance(queued_message, str):
                message = queued_message
            else:
                message = repr(queued_message)
            last_progress_time_s = time.monotonic()
        except queue.Empty:
            pass

    if process.is_alive():
        process.terminate()
        process.join(10.0)
        raise AssertionError(f"GUI stress subprocess made no progress for {timeout_s} seconds: {message}")
    else:
        process.join(10.0)

    try:
        while True:
            queued_message = message_queue.get_nowait()
            if isinstance(queued_message, str):
                message = queued_message
            else:
                message = repr(queued_message)
    except queue.Empty:
        pass

    assert process.exitcode == 0, message


def test_gui_repeated_dialog_lifecycle_stress() -> None:
    """
    Stress repeated dialog construction and teardown in a crash-contained process.

    :return: None.
    """
    cycles: int = 25
    seed: int = 20260907
    timeout_s: float = 120.0

    run_gui_stress_smoke_subprocess(cycles=cycles, timeout_s=timeout_s, seed=seed)
