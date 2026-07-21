import numpy as np

from VeraGridEngine.Simulations.PowerFlow.Formulations.pf_formulation_template import PfFormulationTemplate
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.levenberg_marquadt_fx import levenberg_marquardt_fx
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.newton_raphson_fx import newton_raphson_fx
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.powell_fx import powell_fx
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions
from VeraGridEngine.Simulations.PowerFlow.power_flow_results import NumericPowerFlowResults
from VeraGridEngine.Utils.Sparse.csc2 import CSC


class ThresholdTrackingProblem(PfFormulationTemplate):
    """
    Minimal formulation used to verify when the iterative solvers enable control updates.
    """
    __slots__ = (
        "_x",
        "_initial_error",
        "_trial_error",
        "_update_controls_history",
    )

    def __init__(self,
                 options: PowerFlowOptions,
                 initial_error: float,
                 trial_error: float) -> None:
        """
        Build a one-variable formulation with deterministic residuals.

        :param options: Power flow options under test
        :param initial_error: Residual reported before the first solver step
        :param trial_error: Residual reported by the trial step used to decide control activation
        """
        super().__init__(V0=np.ones(1, dtype=complex), options=options)
        self._x: np.ndarray = np.zeros(1, dtype=float)
        self._initial_error: float = initial_error
        self._trial_error: float = trial_error
        self._update_controls_history: list[bool] = list()

    @property
    def update_controls_history(self) -> list[bool]:
        """
        Return the sequence of control-update decisions observed by the formulation.

        :return: List of booleans passed by the solvers into ``update()``
        """
        return self._update_controls_history

    def x2var(self, x: np.ndarray) -> None:
        """
        Copy the solver vector into the internal state.

        :param x: State vector
        """
        self._x = x.copy()

    def var2x(self) -> np.ndarray:
        """
        Return the current one-variable state.

        :return: State vector
        """
        return self._x.copy()

    def check_error(self, x: np.ndarray) -> tuple[float, np.ndarray]:
        """
        Return a deterministic trial residual so the solver threshold can be asserted.

        :param x: Trial state vector
        :return: Trial residual and state vector
        """
        return self._trial_error, x.copy()

    def update(self, x: np.ndarray, update_controls: bool = False) -> tuple[float, bool, np.ndarray, np.ndarray]:
        """
        Record the control-update flag and emulate a converging nonlinear problem.

        :param x: State vector
        :param update_controls: Whether the solver decided to activate controls
        :return: Residual, convergence flag, state vector and residual vector
        """
        self.x2var(x)
        self._update_controls_history.append(update_controls)

        if len(self._update_controls_history) == 1:
            self._error = self._initial_error
            self._converged = False
            self._f = np.array([0.1], dtype=float)
        else:
            self._error = self._trial_error
            self._converged = True
            self._f = np.array([0.0], dtype=float)

        return self._error, self._converged, self.var2x(), self._f.copy()

    def size(self) -> int:
        """
        Return the Jacobian size.

        :return: Number of variables
        """
        return 1

    def fx(self) -> np.ndarray:
        """
        Return the current residual vector.

        :return: Residual vector
        """
        return self._f.copy()

    def Jacobian(self) -> CSC:
        """
        Return the constant 1x1 Jacobian needed by the toy problem.

        :return: Sparse Jacobian
        """
        matrix: CSC = CSC(1, 1, 1, True)
        matrix.set(np.array([0], dtype=np.int32),
                   np.array([0, 1], dtype=np.int32),
                   np.array([1.0], dtype=float))
        return matrix

    def get_solution(self, elapsed: float, iterations: int) -> NumericPowerFlowResults:
        """
        Return a minimal numeric solution object compatible with the solver APIs.

        :param elapsed: Solver elapsed time
        :param iterations: Solver iteration count
        :return: Numeric power flow result
        """
        zeros_real: np.ndarray = np.zeros(0, dtype=float)
        zeros_complex: np.ndarray = np.zeros(0, dtype=complex)
        return NumericPowerFlowResults(
            V=self.V.copy(),
            Scalc=self.Scalc.copy(),
            m=zeros_real.copy(),
            tau=zeros_real.copy(),
            Sf=zeros_complex.copy(),
            St=zeros_complex.copy(),
            If=zeros_complex.copy(),
            It=zeros_complex.copy(),
            loading=zeros_complex.copy(),
            losses=zeros_complex.copy(),
            Pfp_vsc=zeros_real.copy(),
            Pfn_vsc=zeros_real.copy(),
            St_vsc=zeros_complex.copy(),
            If_vsc=zeros_real.copy(),
            It_vsc=zeros_complex.copy(),
            losses_vsc=zeros_real.copy(),
            loading_vsc=zeros_real.copy(),
            Sf_hvdc=zeros_complex.copy(),
            St_hvdc=zeros_complex.copy(),
            losses_hvdc=zeros_complex.copy(),
            loading_hvdc=zeros_real.copy(),
            norm_f=self._error,
            converged=self._converged,
            iterations=iterations,
            elapsed=elapsed,
        )


def test_power_flow_options_default_controls_start_tolerance() -> None:
    """
    The formulation should inherit the default control-activation threshold from the options.
    """
    options: PowerFlowOptions = PowerFlowOptions()
    problem: ThresholdTrackingProblem = ThresholdTrackingProblem(
        options=options,
        initial_error=1.0,
        trial_error=1e-3,
    )

    assert np.isclose(options.controls_start_tolerance, 1e-2)
    assert np.isclose(problem._controls_tol, options.controls_start_tolerance)


def test_newton_raphson_uses_controls_start_tolerance() -> None:
    """
    Newton-Raphson should use ``controls_start_tolerance`` instead of the old hardcoded threshold.
    """
    options: PowerFlowOptions = PowerFlowOptions(controls_start_tolerance=1e-2)
    problem: ThresholdTrackingProblem = ThresholdTrackingProblem(
        options=options,
        initial_error=1.0,
        trial_error=5e-3,
    )

    newton_raphson_fx(problem=problem, tol=1e-6, max_iter=1)

    assert problem.update_controls_history == [False, True]


def test_levenberg_marquardt_uses_controls_start_tolerance() -> None:
    """
    Levenberg-Marquardt should use ``controls_start_tolerance`` instead of ``tol * 100``.
    """
    options: PowerFlowOptions = PowerFlowOptions(controls_start_tolerance=1e-2)
    problem: ThresholdTrackingProblem = ThresholdTrackingProblem(
        options=options,
        initial_error=5e-3,
        trial_error=1e-8,
    )

    levenberg_marquardt_fx(problem=problem, tol=1e-6, max_iter=1)

    assert problem.update_controls_history == [False, True]


def test_powell_uses_controls_start_tolerance() -> None:
    """
    Powell Dog Leg should use ``controls_start_tolerance`` instead of ``tol * 100``.
    """
    options: PowerFlowOptions = PowerFlowOptions(controls_start_tolerance=1e-2)
    problem: ThresholdTrackingProblem = ThresholdTrackingProblem(
        options=options,
        initial_error=5e-3,
        trial_error=1e-8,
    )

    powell_fx(problem=problem, tol=1e-6, max_iter=1)

    assert problem.update_controls_history == [False, True]
