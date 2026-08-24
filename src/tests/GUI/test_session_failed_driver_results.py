from __future__ import annotations

from VeraGrid.Session.session import GcThread, SimulationSession
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Simulations.driver_template import DriverTemplate
from VeraGridEngine.enumerations import ResultTypes, SimulationTypes


class FailingResultsDriver(DriverTemplate):
    """
    Minimal driver that fails after exposing a constructor-time result shell.
    """

    __slots__ = tuple()

    name = "Failing results driver"
    tpe = SimulationTypes.RmsSmallSignal_run

    def __init__(self, grid: MultiCircuit) -> None:
        """
        Initialize the driver with a result placeholder.

        :param grid: Empty test grid.
        :return: None.
        """
        DriverTemplate.__init__(self, grid=grid)
        self.results = object()

    def run(self) -> None:
        """
        Simulate a numerical failure after driver registration.

        :return: None.
        """
        raise RuntimeError("intentional numerical failure")


def test_failed_worker_discards_placeholder_and_blocks_result_access() -> None:
    """
    Verify a failed asynchronous study cannot publish its initial result shell.

    :return: None.
    """
    session: SimulationSession = SimulationSession()
    driver: FailingResultsDriver = FailingResultsDriver(grid=MultiCircuit())
    thread: GcThread = GcThread(driver=driver)
    session.drivers[driver.tpe] = driver
    session.threads[driver.tpe] = thread

    thread.run()

    assert thread.has_failed()
    assert driver.results is None
    assert driver.logger.has_errors()
    assert thread.logger.has_errors()
    assert session.get_results_model(
        driver_type=driver.tpe,
        result_type=ResultTypes.Modes,
    ) is None
    assert session.get_results_model_by_name(
        study_name=driver.name,
        study_type=ResultTypes.Modes,
    ) is None
