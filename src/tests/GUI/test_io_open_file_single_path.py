from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, List

from VeraGrid.Gui.Main.SubClasses.io import IoMain
from VeraGridEngine.enumerations import SimulationTypes


class FakeSignal:
    """
    Minimal Qt-like signal used to record signal connections in tests.
    """

    __slots__ = ("callbacks",)

    def __init__(self) -> None:
        """
        Build the fake signal.

        :return: None.
        """
        self.callbacks: List[Callable[..., Any]] = list()

    def connect(self, callback: Callable[..., Any]) -> None:
        """
        Record one connected callback.

        :param callback: Connected callable.
        :return: None.
        """
        self.callbacks.append(callback)


class FakeThreadObject:
    """
    Minimal file-open thread used to capture the normalized input path.
    """

    __slots__ = ("file_name", "options", "progress_signal", "progress_text", "done_signal", "started")

    def __init__(self, file_name: str | list[str], previous_circuit: Any, options: Any) -> None:
        """
        Build the fake thread object.

        :param file_name: Normalized file name payload passed by ``open_file_now``.
        :param previous_circuit: Unused previous circuit placeholder.
        :param options: File-open options.
        :return: None.
        """
        del previous_circuit
        self.file_name: str | list[str] = file_name
        self.options: Any = options
        self.progress_signal: FakeSignal = FakeSignal()
        self.progress_text: FakeSignal = FakeSignal()
        self.done_signal: FakeSignal = FakeSignal()
        self.started: bool = False

    def start(self) -> None:
        """
        Mark the fake thread as started.

        :return: None.
        """
        self.started = True


class FakeProgressBar:
    """
    Minimal progress bar sink used for signal connections.
    """

    __slots__ = ("values",)

    def __init__(self) -> None:
        """
        Build the fake progress bar.

        :return: None.
        """
        self.values: List[float] = list()

    def setValue(self, value: float) -> None:
        """
        Record one progress value.

        :param value: Progress value.
        :return: None.
        """
        self.values.append(value)


class FakeProgressLabel:
    """
    Minimal progress label sink used for signal connections.
    """

    __slots__ = ("texts",)

    def __init__(self) -> None:
        """
        Build the fake progress label.

        :return: None.
        """
        self.texts: List[str] = list()

    def setText(self, text: str) -> None:
        """
        Record one progress label update.

        :param text: Progress text.
        :return: None.
        """
        self.texts.append(text)


class FakeUi:
    """
    Minimal UI container required by ``open_file_now``.
    """

    __slots__ = ("progressBar", "progress_label")

    def __init__(self) -> None:
        """
        Build the fake UI.

        :return: None.
        """
        self.progressBar: FakeProgressBar = FakeProgressBar()
        self.progress_label: FakeProgressLabel = FakeProgressLabel()


class FakeIoHarness:
    """
    Minimal ``IoMain`` harness with only the state used by ``open_file_now``.
    """

    __slots__ = (
        "project_directory",
        "file_name",
        "circuit",
        "ui",
        "stuff_running_now",
        "open_file_thread_object",
        "last_file_driver",
        "LOCK",
        "UNLOCK",
        "post_open_file",
        "tr",
    )

    def __init__(self) -> None:
        """
        Build the fake harness.

        :return: None.
        """
        self.project_directory: str = ""
        self.file_name: str = ""
        self.circuit: Any = object()
        self.ui: FakeUi = FakeUi()
        self.stuff_running_now: List[SimulationTypes] = list()
        self.open_file_thread_object: FakeThreadObject | None = None
        self.last_file_driver: FakeThreadObject | None = None
        self.LOCK: Callable[[], None] = lambda: None
        self.UNLOCK: Callable[[], None] = lambda: None
        self.post_open_file: Callable[[], None] = lambda: None
        self.tr: Callable[[str], str] = lambda text: text


def test_open_file_now_accepts_one_string_path_without_iterating_characters(monkeypatch: Any,
                                                                             tmp_path: Path) -> None:
    """
    Verify ``open_file_now`` treats one string path as one file instead of a character sequence.

    :param monkeypatch: Pytest monkeypatch fixture.
    :param tmp_path: Temporary directory.
    :return: None.
    """
    file_path: Path = tmp_path / "single.veragrid"
    file_path.write_text("dummy", encoding="utf-8")

    captured_errors: List[dict[str, str]] = list()

    monkeypatch.setattr(
        "VeraGrid.Gui.Main.SubClasses.io.filedrv.FileOpenThread",
        FakeThreadObject,
    )
    monkeypatch.setattr(
        "VeraGrid.Gui.Main.SubClasses.io.error_msg",
        lambda text, title: captured_errors.append({"text": text, "title": title}),
    )

    harness: FakeIoHarness = FakeIoHarness()

    IoMain.open_file_now(harness, filenames=str(file_path))

    assert captured_errors == list()
    # The visible project identity changes only after the loaded circuit has
    # passed the project-replacement guards in ``post_open_file``.
    assert harness.file_name == ""
    assert harness.project_directory == str(file_path.parent)
    assert isinstance(harness.open_file_thread_object, FakeThreadObject)
    assert harness.open_file_thread_object.file_name == str(file_path)
    assert harness.open_file_thread_object.started is True
    assert harness.last_file_driver is harness.open_file_thread_object
    assert harness.stuff_running_now == [SimulationTypes.FileOpen]


def test_save_file_overwrites_only_native_veragrid_files() -> None:
    """
    Check that imported non-VeraGrid files are not treated as direct save targets.

    :return: None.
    """
    assert IoMain.is_direct_veragrid_save_path(file_name="/tmp/grid.veragrid")
    assert IoMain.is_direct_veragrid_save_path(file_name="/tmp/grid.gridcal")
    assert not IoMain.is_direct_veragrid_save_path(file_name="/tmp/grid.raw")
    assert not IoMain.is_direct_veragrid_save_path(file_name="/tmp/grid.xml")
