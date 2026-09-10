# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
import math
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

import VeraGridEngine.Devices as dev
from VeraGridEngine.basic_structures import Vec, IntVec
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.enumerations import ShuntControlMode, GeneratorControlMode, CandidateKind
from VeraGridEngine.Simulations.driver_template import DriverTemplate
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowDriver
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions
from VeraGridEngine.Simulations.PowerFlow.power_flow_ts_driver import PowerFlowTimeSeriesDriver
from VeraGridEngine.Simulations.LinearFactors.linear_analysis import LinearAnalysis
from VeraGridEngine.Utils.GeographicalMethods.haversine_distance import haversine_distance
from VeraGridEngine.Simulations.InvestmentsEvaluation.CandidateGeneration.candidate_generation_options import (
    CandidateGenerationOptions,
)
from VeraGridEngine.Simulations.InvestmentsEvaluation.CandidateGeneration.candidate_generation_results import (
    CandidateGenerationResults, ViolationRecord, VoltageViolationRecord, ReinforcementCandidate,
)


class CandidateGenerationDriver(DriverTemplate):
    """
    Candidate-investment generator for transmission expansion planning.

    Pipeline:
      1. Fresh AC power flow (base case): per-branch loading and bus voltage, base-case feasibility.
      2. LODF N-1 screening (branches) + base-case voltage screening (buses): flag branches
         overloaded under each single branch outage, and buses outside their voltage limits.
         Voltage screening is base case only - no linear voltage-sensitivity ("QTDF") utility
         exists in this codebase to make an N-1 pass cheap, and over-voltage is predominantly a
         light-load/base-case phenomenon, so an N solve per contingency would be disproportionate.
      3. PTDF-ranked reinforcements, kept as three independently ranked tracks (see ``run()``):
         new-line corridors and rating upgrades (line/branch-scale MW relief), static generators
         and batteries (injection-scale MW relief, capped by ``max_injection_mw`` - orders of
         magnitude below a transmission line's implicit capacity, so mixing them into one ranked
         list would starve the smaller-scale kinds of verification slots), and shunt reactors
         (p.u. of voltage excess, an entirely different unit).
      4. Shortlist: each track's candidates ranked by its own relief score, annotated with the
         violations they relieve.
      5. Fresh AC power flow verification of the top candidate(s) of each track, re-checking both
         branch and voltage violations regardless of which kind is being verified.

    With ``options.use_time_series`` set, step 0 first scans the grid's time series for the
    hour with the most combined branch overloads and bus voltage violations, and the whole
    pipeline above then runs at that single hour instead of the grid's current snapshot values.
    """
    __slots__ = ("options", "pf_options")

    name = 'Candidate investment generator'

    def __init__(self,
                 grid: MultiCircuit,
                 options: Optional[CandidateGenerationOptions] = None,
                 pf_options: Optional[PowerFlowOptions] = None):
        """
        :param grid: MultiCircuit to analyse.
        :param options: Candidate-generation options.
        :param pf_options: Power-flow options for the base case and verification.
        """
        DriverTemplate.__init__(self, grid=grid)
        self.options: CandidateGenerationOptions = options if options is not None else CandidateGenerationOptions()
        self.pf_options: PowerFlowOptions = pf_options if pf_options is not None else PowerFlowOptions()
        self.results: CandidateGenerationResults = CandidateGenerationResults()

    # ----------------------------------------------------------------------------------------------
    # Low-level helpers
    # ----------------------------------------------------------------------------------------------
    def _run_ac_pf(self, grid: MultiCircuit, t_idx: Optional[int] = None) -> Tuple[bool, Vec, Vec]:
        """
        Run a fresh AC power flow and return (converged, active-power branch flows in MW, bus
        voltage magnitudes in p.u.).

        :param grid: The grid to solve.
        :param t_idx: Time index to solve at, or None for the grid's snapshot values.
        :return: (converged, Sf.real, |voltage|), Sf and voltage in compiled branch/bus order.
        """
        pf = PowerFlowDriver(grid=grid, options=self.pf_options, t_idx=t_idx)
        pf.run()
        return (bool(pf.results.converged),
               np.asarray(pf.results.Sf.real, dtype=float),
               np.asarray(np.abs(pf.results.voltage), dtype=float))

    def _find_critical_snapshot(self, time_indices: IntVec) -> Tuple[int, int, int, List[str]]:
        """
        Scan a base-case-only (N-0) AC power-flow time series and locate the single most critical
        hour: the one with the most combined branch overloads and bus voltage violations.

        :param time_indices: Time steps to scan.
        :return: (critical time index (global axis), overloaded-branch count at that hour,
                 voltage-violated-bus count at that hour, per-bus voltage violation report).
        """
        ts_driver = PowerFlowTimeSeriesDriver(grid=self.grid, options=self.pf_options,
                                              time_indices=time_indices)
        ts_driver.run()

        # Topology/limits are assumed static across the scanned window, so one structural
        # compilation is enough to get rates, monitorable branches and bus voltage limits.
        nc = compile_numerical_circuit_at(self.grid, t_idx=int(time_indices[0]))
        pbd = nc.passive_branch_data
        monitorable = np.array([pbd.active[i] and pbd.rates[i] > 0.0 for i in range(nc.nbr)], dtype=bool)

        loading = np.abs(ts_driver.results.loading)
        n_overload = np.sum((loading > self.options.base_overload_threshold) & monitorable[None, :], axis=1)

        vm = np.abs(ts_driver.results.voltage)
        vmin = nc.bus_data.Vmin
        vmax = nc.bus_data.Vmax
        voltage_violated = (vm < vmin[None, :]) | (vm > vmax[None, :])
        n_voltage = np.sum(voltage_violated, axis=1)

        criticality = n_overload + n_voltage
        local_idx = int(np.argmax(criticality))
        t_critical = int(time_indices[local_idx])

        voltage_report: List[str] = list()
        bus_names = nc.bus_data.names
        for i in range(nc.nbus):
            if voltage_violated[local_idx, i]:
                bound = "Vmax" if vm[local_idx, i] > vmax[i] else "Vmin"
                limit = vmax[i] if bound == "Vmax" else vmin[i]
                voltage_report.append(f"{str(bus_names[i])}: {vm[local_idx, i]:.3f} pu "
                                     f"({'>' if bound == 'Vmax' else '<'} {bound} {limit:.3f} pu)")

        return t_critical, int(n_overload[local_idx]), int(n_voltage[local_idx]), voltage_report

    @staticmethod
    def _screen(nc: NumericalCircuit,
                lodf: np.ndarray,
                base_flow: Vec,
                base_threshold: float,
                n1_threshold: float) -> List[ViolationRecord]:
        """
        Base-case + N-1 (LODF) overload screening.

        :param nc: Numerical circuit (source of names, rates, contingency rates, active flags).
        :param lodf: LODF matrix (branches x branches), LODF[m, c] = effect on m of outaging c.
        :param base_flow: Base-case active-power flows in MW (compiled branch order).
        :param base_threshold: Base-case loading fraction that flags a branch.
        :param n1_threshold: N-1 loading fraction that flags a branch.
        :return: List of violations.
        """
        pbd = nc.passive_branch_data
        names = pbd.names
        rates = pbd.rates
        cont_rates = pbd.contingency_rates
        active = pbd.active

        n_br = nc.nbr
        violations: List[ViolationRecord] = list()

        # Branches worth monitoring / outaging: active with a positive rating.
        monitorable = np.array([active[i] and rates[i] > 0.0 for i in range(n_br)], dtype=bool)

        # --- base case ---
        for m in range(n_br):
            if monitorable[m] and abs(base_flow[m]) > rates[m] * base_threshold:
                violations.append(ViolationRecord(monitored_idx=m,
                                                  monitored_name=str(names[m]),
                                                  flow=float(base_flow[m]),
                                                  limit=float(rates[m])))

        # --- N-1 ---
        for c in range(n_br):
            # Outaging a branch that carries ~no flow redistributes nothing.
            if not monitorable[c] or abs(base_flow[c]) < 1e-9:
                continue
            for m in range(n_br):
                if not monitorable[m] or m == c:
                    continue
                flow_after = base_flow[m] + lodf[m, c] * base_flow[c]
                limit = cont_rates[m] * n1_threshold
                if limit > 0.0 and abs(flow_after) > limit:
                    violations.append(ViolationRecord(monitored_idx=m,
                                                      monitored_name=str(names[m]),
                                                      flow=float(flow_after),
                                                      limit=float(cont_rates[m]),
                                                      outage_idx=c,
                                                      outage_name=str(names[c])))
        return violations

    @staticmethod
    def _violation_key(v: ViolationRecord) -> Tuple[str, str]:
        """Identity of a violation independent of branch indexing (survives adding a line)."""
        return (v.outage_name if not v.is_base_case else "__base__", v.monitored_name)

    @staticmethod
    def _screen_voltage(nc: NumericalCircuit, vm: Vec) -> List[VoltageViolationRecord]:
        """
        Base-case bus-voltage screening: flag every active bus whose voltage magnitude falls
        outside its own [Vmin, Vmax]. No N-1 (post-contingency) pass is performed - see the class
        docstring for why.

        :param nc: Numerical circuit (source of bus names, active flags, Vmin/Vmax).
        :param vm: Bus voltage magnitudes in p.u. (compiled bus order), from a converged AC PF.
        :return: List of voltage violations.
        """
        bus_data = nc.bus_data
        violations: List[VoltageViolationRecord] = list()

        for i in range(nc.nbus):
            if not bus_data.active[i]:
                pass
            else:
                v = float(vm[i])
                vmin_i = float(bus_data.Vmin[i])
                vmax_i = float(bus_data.Vmax[i])
                if v < vmin_i or v > vmax_i:
                    violations.append(VoltageViolationRecord(bus_idx=i, bus_name=str(bus_data.names[i]),
                                                              vm=v, vmin=vmin_i, vmax=vmax_i))
                else:
                    pass

        return violations

    @staticmethod
    def _voltage_violation_key(v: VoltageViolationRecord) -> str:
        """Identity of a voltage violation independent of bus indexing (survives adding a device)."""
        return v.bus_name

    def _nearest_buses(self, buses: List, bus_idx: int, k: int) -> List[int]:
        """
        Indices of the k nearest buses to ``bus_idx`` by haversine distance. Buses without
        coordinates (0, 0) are skipped, as is the bus itself.

        :param buses: List of Bus devices (compiled bus order).
        :param bus_idx: Reference bus index.
        :param k: How many neighbours to return.
        :return: List of bus indices.
        """
        ref = buses[bus_idx]
        if ref.latitude == 0.0 and ref.longitude == 0.0:
            return list()

        dists: List[Tuple[float, int]] = list()
        for j, b in enumerate(buses):
            if j == bus_idx:
                continue
            if b.latitude == 0.0 and b.longitude == 0.0:
                continue
            d = haversine_distance(lat1=ref.latitude, lon1=ref.longitude,
                                   lat2=b.latitude, lon2=b.longitude)
            dists.append((d, j))

        dists.sort(key=lambda t: t[0])
        return [j for _, j in dists[:k]]

    # ----------------------------------------------------------------------------------------------
    # Candidate generation
    # ----------------------------------------------------------------------------------------------
    def _make_upgrade_candidates(self,
                                 nc: NumericalCircuit,
                                 branch_by_idtag: Dict[str, object],
                                 violations: List[ViolationRecord]) -> List[ReinforcementCandidate]:
        """
        One upgrade candidate per overloaded branch: raise its rate to the smallest value that
        clears every violation on that branch (base and N-1).
        """
        pbd = nc.passive_branch_data
        rates = pbd.rates
        cont_rates = pbd.contingency_rates
        idtags = pbd.idtag

        # Group violations by the monitored branch.
        by_branch: Dict[int, List[ViolationRecord]] = dict()
        for v in violations:
            by_branch.setdefault(v.monitored_idx, list()).append(v)

        candidates: List[ReinforcementCandidate] = list()
        for m, vlist in by_branch.items():
            old_rate = float(rates[m])
            if old_rate <= 0.0:
                continue
            factor = cont_rates[m] / old_rate if old_rate > 0.0 else 1.0

            # Rate needed to clear each violation on this branch.
            needed = 0.0
            for v in vlist:
                if v.is_base_case:
                    needed = max(needed, abs(v.flow))
                else:
                    needed = max(needed, abs(v.flow) / factor if factor > 0.0 else abs(v.flow))

            new_rate = math.ceil(needed)
            if new_rate <= old_rate:
                continue

            cand = ReinforcementCandidate(kind=CandidateKind.Upgrade)
            cand.target_branch = branch_by_idtag[str(idtags[m])]
            cand.branch_idx = m
            cand.old_rate = old_rate
            cand.new_rate = float(new_rate)
            cand.relieved_violations = list(vlist)
            cand.score = float(sum(v.excess for v in vlist))
            # Priced as replacing the branch with one built to the new rating (see
            # CandidateGenerationOptions.line_cost_per_mva), not the incremental capacity added.
            cand.capex = self.options.line_cost_per_mva * cand.new_rate
            candidates.append(cand)

        return candidates

    def _make_new_line_candidates(self,
                                  nc: NumericalCircuit,
                                  buses: List,
                                  branch_by_idtag: Dict[str, object],
                                  ptdf: np.ndarray,
                                  violations: List[ViolationRecord]) -> List[ReinforcementCandidate]:
        """
        Enumerate new-line corridors (parallel duplicate of each overloaded branch, plus corridors
        to nearby buses) and score each by the PTDF-estimated relief it provides across violations.
        """
        pbd = nc.passive_branch_data
        F = pbd.F
        T = pbd.T
        idtags = pbd.idtag
        thr = self.options.ptdf_threshold

        # Enumerate candidate corridors, keyed by unordered bus pair. Each carries a reference
        # branch (for impedance/rate/naming) taken from the overloaded branch that spawned it.
        corridors: Dict[frozenset, Tuple[int, int, object]] = dict()

        monitored_branches = sorted({v.monitored_idx for v in violations})
        for m in monitored_branches:
            f, t = int(F[m]), int(T[m])
            ref = branch_by_idtag[str(idtags[m])]

            def register(a: int, b: int) -> None:
                if a == b:
                    return
                # A new AC line must connect buses of the same nominal voltage; otherwise the
                # circuit would turn it into a transformer (leaving the investment pointing at an
                # orphan line). Cross-voltage branches are covered by upgrade candidates instead.
                va, vb = buses[a].Vnom, buses[b].Vnom
                if abs(va - vb) > 0.1 * max(va, vb, 1e-9):
                    return
                key = frozenset((a, b))
                if key not in corridors:
                    corridors[key] = (a, b, ref)

            # Parallel duplicate of the overloaded corridor.
            register(f, t)

            # Corridors from each endpoint to nearby buses.
            for n in self._nearest_buses(buses, f, self.options.top_n_corridors):
                register(f, n)
            for n in self._nearest_buses(buses, t, self.options.top_n_corridors):
                register(t, n)

        candidates: List[ReinforcementCandidate] = list()
        for (a, b, ref) in corridors.values():
            rate = float(ref.rate)
            if rate <= 0.0:
                continue

            relieved: List[ViolationRecord] = list()
            score = 0.0
            for v in violations:
                mm = v.monitored_idx
                sens = ptdf[mm, a] - ptdf[mm, b]
                if abs(sens) < thr:
                    continue
                # Max achievable flow change on the monitored branch if the new line carries
                # up to its rating (first-order PTDF estimate).
                delta = abs(sens) * rate
                relief_v = min(delta, v.excess)
                if relief_v <= 0.0:
                    continue
                score += relief_v
                if delta >= v.excess:  # estimated to fully clear this violation
                    relieved.append(v)

            if score <= 0.0 or len(relieved) == 0:
                continue

            cand = ReinforcementCandidate(kind=CandidateKind.NewLine)
            cand.bus_from = buses[a]
            cand.bus_to = buses[b]
            cand.bus_from_idx = a
            cand.bus_to_idx = b
            cand.r = float(ref.R)
            cand.x = float(ref.X)
            cand.b = float(ref.B)
            cand.rate = rate
            cand.name = f"{buses[a].name} - {buses[b].name}"
            cand.relieved_violations = relieved
            cand.score = float(score)
            cand.capex = self.options.line_cost_per_mva * cand.rate
            candidates.append(cand)

        return candidates

    def _make_shunt_reactor_candidates(self,
                                       nc: NumericalCircuit,
                                       buses: List,
                                       voltage_violations: List[VoltageViolationRecord]
                                       ) -> List[ReinforcementCandidate]:
        """
        One shunt-reactor candidate per over-voltage bus. Under-voltage buses are left unaddressed:
        a reactor only absorbs reactive power (Bmin=0), so it cannot relieve Vm < Vmin.

        Sizing avoids hand-building a full Ybus/Thevenin voltage sensitivity: ``Bmax`` is bounded
        by a network-strength proxy (total MVA rating of active, monitorable branches incident to
        the bus, standing in for short-circuit stiffness) and the standard decoupled
        ``dQ ~= Sk * dV`` approximation, margined for headroom. The actual required B is sized by
        the AC power flow's own continuous shunt-control logic during verification (step 5), within
        [0, Bmax] - this estimate only bounds that search and seeds the CAPEX proxy used for ranking.

        :param nc: Numerical circuit (source of branch endpoints/ratings and bus data).
        :param buses: List of Bus devices (compiled bus order).
        :param voltage_violations: Base-case voltage violations from ``_screen_voltage``.
        :return: List of shunt-reactor candidates.
        """
        pbd = nc.passive_branch_data
        candidates: List[ReinforcementCandidate] = list()

        for v in voltage_violations:
            if not v.is_overvoltage:
                pass
            else:
                i = v.bus_idx

                # Local network-strength proxy standing in for short-circuit stiffness (Sk).
                sk_proxy = 0.0
                for m in range(nc.nbr):
                    if pbd.active[m] and pbd.rates[m] > 0.0 and (int(pbd.F[m]) == i or int(pbd.T[m]) == i):
                        sk_proxy += float(pbd.rates[m])
                if sk_proxy <= 0.0:
                    sk_proxy = float(nc.Sbase)
                else:
                    pass

                # Classic decoupled sizing estimate: dQ ~= Sk * dV, margined for solver headroom.
                q_needed = v.excess * sk_proxy
                bmax = self.options.shunt_bmax_margin * q_needed

                cand = ReinforcementCandidate(kind=CandidateKind.ShuntReactor)
                cand.target_bus = buses[i]
                cand.target_bus_idx = i
                cand.shunt_vset = v.vmax
                cand.shunt_bmax = bmax
                cand.relieved_voltage_violations = [v]
                cand.score = float(v.excess)
                cand.capex = self.options.shunt_cost_per_mvar * bmax
                candidates.append(cand)

        return candidates

    def _find_injection_sites(self,
                              nc: NumericalCircuit,
                              buses: List,
                              violations: List[ViolationRecord]) -> List[int]:
        """
        Candidate bus indices for a real-power injection device: the endpoints of every overloaded
        branch plus their nearest neighbours, mirroring the corridor enumeration in
        ``_make_new_line_candidates`` (single buses here, not bus pairs).

        :param nc: Numerical circuit (source of branch endpoints).
        :param buses: List of Bus devices (compiled bus order).
        :param violations: Branch-overload violations.
        :return: Sorted, de-duplicated bus indices.
        """
        pbd = nc.passive_branch_data
        sites: Set[int] = set()

        monitored_branches = sorted({v.monitored_idx for v in violations})
        for m in monitored_branches:
            f, t = int(pbd.F[m]), int(pbd.T[m])
            sites.add(f)
            sites.add(t)
            for n in self._nearest_buses(buses, f, self.options.top_n_corridors):
                sites.add(n)
            for n in self._nearest_buses(buses, t, self.options.top_n_corridors):
                sites.add(n)

        return sorted(sites)

    def _size_injection_candidate(self,
                                  site: int,
                                  ptdf: np.ndarray,
                                  violations: List[ViolationRecord]
                                  ) -> Tuple[float, float, List[ViolationRecord]]:
        """
        Size a real-power injection at ``site`` against every branch-overload violation it can
        validly relieve, capped by ``options.max_injection_mw``.

        Unlike a new line, a single-direction injection cannot reroute flow both ways: a site only
        validly helps a violation when its PTDF sensitivity has the sign that makes positive
        generation reduce, not worsen, |flow| there (``sens * flow < 0``); the wrong-sign case is
        excluded rather than mis-scored.

        :param site: Candidate bus index.
        :param ptdf: PTDF matrix (branches x buses).
        :param violations: Branch-overload violations.
        :return: (sized P in MW, total relief score in MW, violations estimated fully relieved).
        """
        thr = self.options.ptdf_threshold

        # Pass 1: size P to fully clear the worst violation this site can validly help with.
        p_needed = 0.0
        for v in violations:
            sens = ptdf[v.monitored_idx, site]
            if abs(sens) < thr or sens * v.flow >= 0.0:
                pass
            else:
                p_needed = max(p_needed, v.excess / abs(sens))

        if p_needed <= 0.0:
            return 0.0, 0.0, list()
        else:
            p_size = min(p_needed, self.options.max_injection_mw)

            # Pass 2: score exactly like the new-line corridor scoring - capped partial relief per
            # violation, full credit only when the sized injection is estimated to fully clear it.
            relieved: List[ViolationRecord] = list()
            score = 0.0
            for v in violations:
                sens = ptdf[v.monitored_idx, site]
                if abs(sens) < thr or sens * v.flow >= 0.0:
                    pass
                else:
                    delta = abs(sens) * p_size
                    relief_v = min(delta, v.excess)
                    if relief_v > 0.0:
                        score += relief_v
                        if delta >= v.excess:
                            relieved.append(v)
                        else:
                            pass
                    else:
                        pass

            return p_size, score, relieved

    def _make_static_generator_candidates(self,
                                          nc: NumericalCircuit,
                                          buses: List,
                                          ptdf: np.ndarray,
                                          violations: List[ViolationRecord]
                                          ) -> List[ReinforcementCandidate]:
        """
        One static-generator candidate per viable injection site: real-power overload relief only,
        a non-wires alternative to a new line or upgrade.

        :param nc: Numerical circuit.
        :param buses: List of Bus devices (compiled bus order).
        :param ptdf: PTDF matrix (branches x buses).
        :param violations: Branch-overload violations.
        :return: List of static-generator candidates.
        """
        candidates: List[ReinforcementCandidate] = list()

        for site in self._find_injection_sites(nc=nc, buses=buses, violations=violations):
            p_size, score, relieved = self._size_injection_candidate(site, ptdf, violations)
            if score <= 0.0 or len(relieved) == 0:
                pass
            else:
                cand = ReinforcementCandidate(kind=CandidateKind.StaticGenerator)
                cand.injection_bus = buses[site]
                cand.injection_bus_idx = site
                cand.injection_p = p_size
                cand.injection_snom = p_size
                cand.relieved_violations = relieved
                cand.score = float(score)
                cand.capex = self.options.static_gen_cost_per_mw * p_size
                candidates.append(cand)

        return candidates

    def _make_battery_candidates(self,
                                 nc: NumericalCircuit,
                                 buses: List,
                                 ptdf: np.ndarray,
                                 violations: List[ViolationRecord],
                                 voltage_violations: List[VoltageViolationRecord]
                                 ) -> List[ReinforcementCandidate]:
        """
        One battery candidate per viable injection site, sized identically to the static generator
        for real-power relief (single-snapshot sizing, no multi-period dispatch in v1). Voltage
        support is a free side effect of the default voltage-controlled behaviour applied in
        ``ReinforcementCandidate.apply()`` - not separately sized here; if a site happens to
        coincide with a screened over-voltage bus, that violation is attached purely for reporting
        and does not affect targeting/score.

        :param nc: Numerical circuit.
        :param buses: List of Bus devices (compiled bus order).
        :param ptdf: PTDF matrix (branches x buses).
        :param violations: Branch-overload violations.
        :param voltage_violations: Base-case voltage violations, for informational attachment only.
        :return: List of battery candidates.
        """
        voltage_by_bus: Dict[int, VoltageViolationRecord] = {v.bus_idx: v for v in voltage_violations}
        candidates: List[ReinforcementCandidate] = list()

        for site in self._find_injection_sites(nc=nc, buses=buses, violations=violations):
            p_size, score, relieved = self._size_injection_candidate(site, ptdf, violations)
            if score <= 0.0 or len(relieved) == 0:
                pass
            else:
                cand = ReinforcementCandidate(kind=CandidateKind.Battery)
                cand.injection_bus = buses[site]
                cand.injection_bus_idx = site
                cand.injection_p = p_size
                cand.battery_pmax = p_size
                cand.battery_enom = p_size * self.options.battery_duration_hours
                cand.injection_snom = p_size
                cand.relieved_violations = relieved
                if site in voltage_by_bus:
                    cand.relieved_voltage_violations = [voltage_by_bus[site]]
                else:
                    pass
                cand.score = float(score)
                # Priced by Enom (which already encodes Pmax x duration), not by P alone - matches
                # the bundled power+energy costing convention the source figure uses (see options).
                cand.capex = self.options.battery_cost_per_mwh * cand.battery_enom
                candidates.append(cand)

        return candidates

    # ----------------------------------------------------------------------------------------------
    # Verification (step 5)
    # ----------------------------------------------------------------------------------------------
    def _verify(self,
                candidate: ReinforcementCandidate,
                original_keys: Set[Tuple[str, str]],
                original_voltage_keys: Set[str],
                t_idx: Optional[int] = None) -> str:
        """
        Apply the candidate to a copy of the grid, re-run AC PF + N-1 + voltage screening, and
        report whether its targeted violations are cleared and whether any new violations appeared.
        Both the branch and voltage checks run for every kind: a static-generator/battery injection
        could in principle nudge a nearby bus's voltage via network coupling, and a shunt reactor's
        Bmax cap could saturate without fully correcting voltage - either direction is caught here.

        :param candidate: Candidate to verify.
        :param original_keys: Identities of all branch violations found in the original screening.
        :param original_voltage_keys: Identities of all voltage violations found in the original
                                      screening.
        :param t_idx: Time index to verify at, or None for the grid's snapshot values.
        :return: One-line verification report.
        """
        candidate.verified = True
        candidate.n_targeted = len(candidate.relieved_violations)
        candidate.n_voltage_targeted = len(candidate.relieved_voltage_violations)

        cpy = self.grid.copy()
        cpy_buses = cpy.get_buses()

        if candidate.kind == CandidateKind.NewLine:
            line = dev.Line(bus_from=cpy_buses[candidate.bus_from_idx],
                            bus_to=cpy_buses[candidate.bus_to_idx],
                            name=candidate.name,
                            r=candidate.r, x=candidate.x, b=candidate.b,
                            rate=candidate.rate)
            cpy.add_line(line)
        elif candidate.kind == CandidateKind.Upgrade:
            target_idtag = candidate.target_branch.idtag
            for br in cpy.get_branches(add_switch=True):
                if br.idtag == target_idtag:
                    br.rate = candidate.new_rate
                    # A t_idx-based compile (time-series mode) resolves rate through rate_prof,
                    # not the scalar - without this the verification PF would still see old_rate.
                    br_rate_prof = br.get_profile('rate')
                    if br_rate_prof is not None:
                        br_rate_prof.fill(candidate.new_rate)
                    break
                else:
                    pass
        elif candidate.kind == CandidateKind.ShuntReactor:
            # Added directly active (no Investment wrapper) - testing "what if this existed",
            # mirroring how a new-line candidate's verification copy adds an active Line.
            shunt = dev.ControllableShunt(name="verify-shunt",
                                          Bmin=0.0, Bmax=candidate.shunt_bmax,
                                          Gmin=0.0, Gmax=0.0,
                                          number_of_steps=1,
                                          vset=candidate.shunt_vset,
                                          control_mode=ShuntControlMode.Continuous,
                                          active=True)
            cpy.add_controllable_shunt(cpy_buses[candidate.target_bus_idx], shunt)
        elif candidate.kind == CandidateKind.StaticGenerator:
            static_gen = dev.StaticGenerator(name="verify-staticgen",
                                             P=candidate.injection_p, Q=0.0,
                                             Snom=candidate.injection_snom, active=True)
            cpy.add_static_generator(cpy_buses[candidate.injection_bus_idx], static_gen)
        elif candidate.kind == CandidateKind.Battery:
            battery = dev.Battery(name="verify-battery",
                                  P=candidate.injection_p, Pmin=0.0, Pmax=candidate.battery_pmax,
                                  Enom=candidate.battery_enom,
                                  control_mode=GeneratorControlMode.V, vset=1.0, active=True)
            cpy.add_battery(cpy_buses[candidate.injection_bus_idx], battery)
        else:
            raise ValueError(f"Unhandled candidate kind: {candidate.kind}")

        converged, base_flow, vm = self._run_ac_pf(cpy, t_idx=t_idx)
        if not converged:
            candidate.verification_converged = False
            return f"{candidate.label()}: verification power flow did NOT converge."
        else:
            candidate.verification_converged = True

        nc = compile_numerical_circuit_at(cpy, t_idx=t_idx)
        if len(base_flow) != nc.nbr:
            # Cannot map flows onto branches reliably; treat as not verifiable.
            candidate.verification_converged = False
            return f"{candidate.label()}: verification skipped (branch count changed)."
        else:
            pass

        lin = LinearAnalysis(nc=nc)
        new_violations = self._screen(nc=nc, lodf=lin.LODF, base_flow=base_flow,
                                      base_threshold=self.options.base_overload_threshold,
                                      n1_threshold=self.options.n1_overload_threshold)
        new_voltage_violations = self._screen_voltage(nc=nc, vm=vm)

        new_keys = {self._violation_key(v) for v in new_violations}
        new_voltage_keys = {self._voltage_violation_key(v) for v in new_voltage_violations}

        targeted = {self._violation_key(v) for v in candidate.relieved_violations}
        resolved = targeted - new_keys
        introduced = new_keys - original_keys

        targeted_v = {self._voltage_violation_key(v) for v in candidate.relieved_voltage_violations}
        resolved_v = targeted_v - new_voltage_keys
        introduced_v = new_voltage_keys - original_voltage_keys

        candidate.n_resolved = len(resolved)
        candidate.n_new_violations = len(introduced)
        candidate.n_voltage_resolved = len(resolved_v)
        candidate.n_new_voltage_violations = len(introduced_v)

        msg = (f"{candidate.label()}: resolved {len(resolved)}/{len(targeted)} targeted violation(s); "
              f"{len(introduced)} new violation(s).")
        if len(targeted_v) > 0 or len(introduced_v) > 0:
            msg += (f" Voltage: resolved {len(resolved_v)}/{len(targeted_v)} targeted; "
                   f"{len(introduced_v)} new.")
        else:
            pass

        return msg

    # ----------------------------------------------------------------------------------------------
    # Main pipeline
    # ----------------------------------------------------------------------------------------------
    def run(self) -> None:
        """
        Execute the full candidate-generation pipeline and populate ``self.results``.
        """
        self.tic()
        results = CandidateGenerationResults()

        # --- Step 0: locate the critical snapshot (time-series mode only) ---
        t_idx: Optional[int] = None
        if self.options.use_time_series:
            if not self.grid.has_time_series:
                self.logger.add_error("Time-series mode requested but the grid has no time series; "
                                      "aborting.")
                self.results = results
                self.toc()
                return

            time_indices = (self.options.time_indices if self.options.time_indices is not None
                            else self.grid.get_all_time_indices())

            self.report_text("Scanning time series for the critical snapshot...")
            t_critical, n_overload, n_voltage, voltage_report = self._find_critical_snapshot(time_indices)

            t_idx = t_critical
            results.critical_time_idx = t_critical
            time_array = self.grid.get_time_array()
            results.critical_time_label = str(time_array[t_critical]) if time_array is not None else ""
            results.n_overloaded_at_critical = n_overload
            results.n_voltage_violated_at_critical = n_voltage
            results.voltage_violation_report = voltage_report

        # --- Step 1: base case AC power flow ---
        self.report_text("Base case AC power flow...")
        converged, base_flow, vm = self._run_ac_pf(self.grid, t_idx=t_idx)
        results.base_case_converged = converged

        if not converged:
            self.logger.add_error("Base case power flow did not converge; aborting.")
            self.results = results
            self.toc()
            return

        # Compile once for screening + linear factors (own bus ordering == circuit.get_buses()).
        buses = self.grid.get_buses()
        bus_dict = {bus: i for i, bus in enumerate(buses)}
        nc = compile_numerical_circuit_at(self.grid, bus_dict=bus_dict, t_idx=t_idx)

        if len(base_flow) != nc.nbr:
            self.logger.add_error("Branch count mismatch between power flow and compilation; aborting.",
                                  value=f"pf={len(base_flow)} nc={nc.nbr}")
            self.results = results
            self.toc()
            return

        branch_by_idtag: Dict[str, object] = {
            br.idtag: br for br in self.grid.get_branches(add_switch=True)
        }

        # Per-branch base-case loading report.
        pbd = nc.passive_branch_data
        for m in range(nc.nbr):
            if pbd.active[m] and pbd.rates[m] > 0.0:
                loading = abs(base_flow[m]) / (pbd.rates[m] + 1e-9) * 100.0
                results.base_loading_report.append(f"{str(pbd.names[m])}: {loading:.1f}%")

        # --- Step 2: LODF N-1 screening + base-case voltage screening ---
        self.report_text("LODF N-1 screening...")
        lin = LinearAnalysis(nc=nc)
        violations = self._screen(nc=nc, lodf=lin.LODF, base_flow=base_flow,
                                  base_threshold=self.options.base_overload_threshold,
                                  n1_threshold=self.options.n1_overload_threshold)
        results.violations = violations
        results.base_case_feasible = (len(results.base_violations) == 0)

        self.report_text("Voltage screening...")
        voltage_violations = self._screen_voltage(nc=nc, vm=vm)
        results.voltage_violations = voltage_violations

        for v in violations:
            self.logger.add_info(v.describe())
        for v in voltage_violations:
            self.logger.add_info(v.describe())

        if len(violations) == 0 and len(voltage_violations) == 0:
            self.logger.add_info("No base-case or N-1 violations, and no voltage violations found; "
                                 "no candidates needed.")
            self.results = results
            self.toc()
            return
        else:
            pass

        # --- Steps 3-4: line/branch-scale overload-relief candidates (new line, upgrade) ---
        self.report_text("Ranking reinforcements (PTDF)...")
        candidates: List[ReinforcementCandidate] = list()
        candidates += self._make_upgrade_candidates(nc=nc, branch_by_idtag=branch_by_idtag,
                                                    violations=violations)
        candidates += self._make_new_line_candidates(nc=nc, buses=buses,
                                                     branch_by_idtag=branch_by_idtag,
                                                     ptdf=lin.PTDF, violations=violations)
        candidates.sort(key=lambda c: c.score, reverse=True)
        results.candidates = candidates

        # --- Steps 3-4: injection-scale overload-relief candidates (static generator, battery) -
        # own track, separate from the line/branch-scale one above: capped at max_injection_mw
        # (tens of MW), these always score far below a transmission line's implicit capacity
        # (hundreds-thousands of MW), so sharing one ranked list would starve them of verification
        # slots regardless of how good a fit they are (see CandidateGenerationResults docstring) ---
        self.report_text("Ranking injection-relief reinforcements (static generator, battery)...")
        injection_candidates: List[ReinforcementCandidate] = list()
        injection_candidates += self._make_static_generator_candidates(nc=nc, buses=buses,
                                                                        ptdf=lin.PTDF,
                                                                        violations=violations)
        injection_candidates += self._make_battery_candidates(nc=nc, buses=buses, ptdf=lin.PTDF,
                                                               violations=violations,
                                                               voltage_violations=voltage_violations)
        injection_candidates.sort(key=lambda c: c.score, reverse=True)
        results.injection_candidates = injection_candidates

        # --- Steps 3-4: voltage-relief candidate generation + ranking (own track, see
        # CandidateGenerationResults.voltage_candidates docstring for why it's kept separate) ---
        self.report_text("Ranking voltage-relief reinforcements...")
        voltage_candidates = self._make_shunt_reactor_candidates(nc=nc, buses=buses,
                                                                  voltage_violations=voltage_violations)
        voltage_candidates.sort(key=lambda c: c.score, reverse=True)
        results.voltage_candidates = voltage_candidates

        # --- Step 5: verify top-k candidates of each of the three tracks ---
        original_keys = {self._violation_key(v) for v in violations}
        original_voltage_keys = {self._voltage_violation_key(v) for v in voltage_violations}
        for cand in candidates[:max(0, self.options.verify_top_k)]:
            self.report_text("Verifying top overload-relief candidate(s)...")
            results.verification_report.append(
                self._verify(cand, original_keys, original_voltage_keys, t_idx=t_idx))
        for cand in injection_candidates[:max(0, self.options.verify_top_k)]:
            self.report_text("Verifying top injection-relief candidate(s)...")
            results.verification_report.append(
                self._verify(cand, original_keys, original_voltage_keys, t_idx=t_idx))
        for cand in voltage_candidates[:max(0, self.options.verify_top_k)]:
            self.report_text("Verifying top voltage-relief candidate(s)...")
            results.verification_report.append(
                self._verify(cand, original_keys, original_voltage_keys, t_idx=t_idx))

        self.results = results
        self.toc()
