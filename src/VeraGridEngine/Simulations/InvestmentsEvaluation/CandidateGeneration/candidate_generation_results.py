# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING

import VeraGridEngine.Devices as dev
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import ShuntControlMode, GeneratorControlMode, CandidateKind

if TYPE_CHECKING:
    from VeraGridEngine.Devices.multi_circuit import MultiCircuit


class ViolationRecord:
    """
    A single overloaded branch, either in the base case or under a branch outage.
    """

    def __init__(self,
                 monitored_idx: int,
                 monitored_name: str,
                 flow: float,
                 limit: float,
                 outage_idx: int = -1,
                 outage_name: str = ""):
        """
        :param monitored_idx: Branch index (compiled order) of the overloaded branch.
        :param monitored_name: Name of the overloaded branch.
        :param flow: Signed active-power flow on the monitored branch (MW).
        :param limit: Rating the flow is compared against (MW).
        :param outage_idx: Branch index of the outaged branch, or -1 for a base-case violation.
        :param outage_name: Name of the outaged branch ("" for base case).
        """
        self.monitored_idx = monitored_idx
        self.monitored_name = monitored_name
        self.flow = flow
        self.limit = limit
        self.outage_idx = outage_idx
        self.outage_name = outage_name

    @property
    def is_base_case(self) -> bool:
        """Whether this is a base-case (N) violation rather than an N-1 one."""
        return self.outage_idx < 0

    @property
    def loading(self) -> float:
        """Loading fraction (|flow| / limit)."""
        return abs(self.flow) / (self.limit + 1e-9)

    @property
    def excess(self) -> float:
        """MW by which |flow| exceeds the limit (>= 0)."""
        return max(abs(self.flow) - self.limit, 0.0)

    def describe(self) -> str:
        """One-line description in the requested 'outage X -> branch Y overloaded (Z%)' form."""
        pct = self.loading * 100.0
        if self.is_base_case:
            return f"base case -> branch {self.monitored_name} overloaded ({pct:.1f}%)"
        return f"outage {self.outage_name} -> branch {self.monitored_name} overloaded ({pct:.1f}%)"


class VoltageViolationRecord:
    """
    A single bus voltage-magnitude violation, base case only (see ``CandidateGenerationDriver``
    docstring for why N-1 voltage screening is out of scope).
    """

    def __init__(self,
                 bus_idx: int,
                 bus_name: str,
                 vm: float,
                 vmin: float,
                 vmax: float):
        """
        :param bus_idx: Bus index (compiled order) of the violated bus.
        :param bus_name: Name of the violated bus.
        :param vm: Voltage magnitude at the bus (p.u.).
        :param vmin: Lower voltage limit (p.u.).
        :param vmax: Upper voltage limit (p.u.).
        """
        self.bus_idx = bus_idx
        self.bus_name = bus_name
        self.vm = vm
        self.vmin = vmin
        self.vmax = vmax

    @property
    def is_overvoltage(self) -> bool:
        """Whether this violation is an over-voltage (Vm > Vmax)."""
        return self.vm > self.vmax

    @property
    def is_undervoltage(self) -> bool:
        """Whether this violation is an under-voltage (Vm < Vmin)."""
        return self.vm < self.vmin

    @property
    def excess(self) -> float:
        """P.u. by which the voltage exceeds its violated bound (>= 0)."""
        if self.is_overvoltage:
            return max(self.vm - self.vmax, 0.0)
        elif self.is_undervoltage:
            return max(self.vmin - self.vm, 0.0)
        else:
            return 0.0

    def describe(self) -> str:
        """One-line description in the 'bus X: Vm pu (> Vmax limit pu)' form."""
        if self.is_overvoltage:
            bound, limit, rel = "Vmax", self.vmax, ">"
        else:
            bound, limit, rel = "Vmin", self.vmin, "<"
        return f"bus {self.bus_name}: {self.vm:.3f} pu ({rel} {bound} {limit:.3f} pu)"


class ReinforcementCandidate:
    """
    A candidate reinforcement: a new line on a corridor, a rating upgrade of an existing branch, a
    shunt reactor, a static generator, or a battery. Carries enough to be scored, annotated with the
    violations it relieves, and materialised as an ``Investment``.
    """

    def __init__(self, kind: CandidateKind):
        """
        :param kind: Which reinforcement this candidate represents (see ``CandidateKind``).
        """
        self.kind: CandidateKind = kind

        # New-line fields
        self.bus_from: Optional[dev.Bus] = None
        self.bus_to: Optional[dev.Bus] = None
        self.bus_from_idx: int = -1
        self.bus_to_idx: int = -1
        self.r: float = 0.0
        self.x: float = 1e-5
        self.b: float = 0.0
        self.rate: float = 0.0
        self.name: str = ""

        # Upgrade fields
        self.target_branch: Optional[dev.EditableDevice] = None
        self.branch_idx: int = -1
        self.old_rate: float = 0.0
        self.new_rate: float = 0.0

        # Shunt-reactor fields
        self.target_bus: Optional[dev.Bus] = None
        self.target_bus_idx: int = -1
        self.shunt_vset: float = 1.0
        self.shunt_bmax: float = 0.0

        # Static-generator / battery shared placement fields
        self.injection_bus: Optional[dev.Bus] = None
        self.injection_bus_idx: int = -1
        self.injection_p: float = 0.0
        self.injection_snom: float = 0.0

        # Battery-only fields
        self.battery_pmax: float = 0.0
        self.battery_enom: float = 0.0

        # Scoring / annotation
        self.relieved_violations: List[ViolationRecord] = list()
        self.relieved_voltage_violations: List[VoltageViolationRecord] = list()
        self.score: float = 0.0
        self.capex: float = 0.0

        # Verification outcome (populated only for the top-k candidates that are verified in step 5)
        self.verified: bool = False
        self.verification_converged: bool = False
        self.n_targeted: int = 0
        self.n_resolved: int = 0
        self.n_new_violations: int = 0
        self.n_voltage_targeted: int = 0
        self.n_voltage_resolved: int = 0
        self.n_new_voltage_violations: int = 0

    @property
    def verified_ok(self) -> bool:
        """
        Whether this candidate was verified with a converged AC power flow and introduced no new
        branch or voltage violations. This is the gate for displaying a candidate in the GUI
        shortlist.
        """
        return (self.verified and self.verification_converged
               and self.n_new_violations == 0 and self.n_new_voltage_violations == 0)

    def group_name(self) -> str:
        """Name of the investments group this candidate goes into: the asset it represents."""
        if self.kind == CandidateKind.NewLine:
            return f"New line {self.bus_from.name} - {self.bus_to.name}"
        elif self.kind == CandidateKind.Upgrade:
            return f"Upgrade {self.target_branch.name} rate {self.new_rate:.0f}"
        elif self.kind == CandidateKind.ShuntReactor:
            return f"Shunt reactor @ {self.target_bus.name}"
        elif self.kind == CandidateKind.StaticGenerator:
            return f"Static generator @ {self.injection_bus.name}"
        elif self.kind == CandidateKind.Battery:
            return f"Battery @ {self.injection_bus.name}"
        else:
            raise ValueError(f"Unhandled candidate kind: {self.kind}")

    def label(self) -> str:
        """Human-readable one-line label for the candidate list in the GUI."""
        if self.kind == CandidateKind.NewLine:
            what = f"New line {self.bus_from.name} - {self.bus_to.name} (rate {self.rate:.0f} MVA)"
            n = len(self.relieved_violations)
            return f"{what} | relieves {n} violation(s) | score {self.score:.1f} MW"
        elif self.kind == CandidateKind.Upgrade:
            what = f"Upgrade {self.target_branch.name} rate {self.old_rate:.0f} -> {self.new_rate:.0f} MVA"
            n = len(self.relieved_violations)
            return f"{what} | relieves {n} violation(s) | score {self.score:.1f} MW"
        elif self.kind == CandidateKind.ShuntReactor:
            what = f"Shunt reactor @ {self.target_bus.name} (Bmax {self.shunt_bmax:.1f} MVAr, Vset {self.shunt_vset:.3f} pu)"
            n = len(self.relieved_voltage_violations)
            return f"{what} | relieves {n} voltage violation(s) | score {self.score:.3f} pu"
        elif self.kind == CandidateKind.StaticGenerator:
            what = f"Static generator @ {self.injection_bus.name} ({self.injection_p:.1f} MW)"
            n = len(self.relieved_violations)
            return f"{what} | relieves {n} violation(s) | score {self.score:.1f} MW"
        elif self.kind == CandidateKind.Battery:
            what = f"Battery @ {self.injection_bus.name} ({self.injection_p:.1f} MW, {self.battery_enom:.1f} MWh)"
            n = len(self.relieved_violations)
            if len(self.relieved_voltage_violations) > 0:
                extra = f" (+voltage support @ {len(self.relieved_voltage_violations)} bus(es))"
            else:
                extra = ""
            return f"{what} | relieves {n} violation(s){extra} | score {self.score:.1f} MW"
        else:
            raise ValueError(f"Unhandled candidate kind: {self.kind}")

    def apply(self, circuit: "MultiCircuit", group: dev.InvestmentsGroup,
             logger: Logger) -> Optional[dev.EditableDevice]:
        """
        Materialise this candidate on the given circuit as ``Investment`` object(s) in ``group``.

        For a new-line candidate a new ``Line`` device is added to the circuit (inactive) and one
        investment activates it.

        For an upgrade the branch is *copied*, the copy's rate is set to the new value and it is
        added inactive; two investments are added to the group: one activates the uprated copy and
        one deactivates the original branch. This keeps the corridor's topology while raising its
        rating, and — unlike a ``prop``/``value`` investment — works through the activation-only
        investments framework (optimizer and Variations panel), which never applies ``prop``/
        ``value``. The base grid is left untouched until the investments are applied.

        Shunt reactor, static generator and battery candidates are all brand-new devices with
        nothing existing to deactivate, so they follow the same single-device/single-investment
        pattern as the new-line candidate: built inactive, added to the circuit, and wrapped in one
        investment that activates them.

        :param circuit: The circuit to add to (the same one the generator ran on).
        :param group: The investments group to attach to.
        :param logger: Logger for messages.
        :return: The newly created device (for drawing), or ``None`` if nothing new is drawable.
        """
        if self.kind == CandidateKind.NewLine:
            # The line is a candidate investment: add it inactive so it shows as disabled on the
            # diagram until its investment is applied.
            line = dev.Line(bus_from=self.bus_from,
                            bus_to=self.bus_to,
                            name=self.name,
                            r=self.r,
                            x=self.x,
                            b=self.b,
                            rate=self.rate,
                            active=False)
            circuit.add_line(line)
            circuit.add_investment(dev.Investment(device=line,
                                                  code=line.code,
                                                  name="New line: " + line.name,
                                                  CAPEX=self.capex,
                                                  group=group))
            return line
        elif self.kind == CandidateKind.Upgrade:
            # Upgrade: copy the branch, raise the copy's rate, add it inactive. The forced new
            # idtag keeps the copy distinct from the original in the grid's element dictionary.
            upgraded = self.target_branch.copy(forced_new_idtag=True)
            upgraded.rate = self.new_rate
            upgraded.active = False
            upgraded.name = self.target_branch.name + " (upgraded)"
            # copy() inherits the source branch's time profiles (all-active rate=old_rate); the
            # scalar assignments above don't touch them, and any t_idx-based compile (time-series
            # mode) resolves active/rate through the profile, not the scalar - so without this the
            # copy would read as active at every hour, at the OLD rate, until fixed here.
            upgraded_active_prof = upgraded.get_profile('active')
            if upgraded_active_prof is not None:
                upgraded_active_prof.fill(False)
            upgraded_rate_prof = upgraded.get_profile('rate')
            if upgraded_rate_prof is not None:
                upgraded_rate_prof.fill(self.new_rate)
            circuit.add_branch(upgraded)

            # One investment activates the uprated copy...
            circuit.add_investment(dev.Investment(device=upgraded,
                                                  code=upgraded.code,
                                                  name="Upgrade: " + self.target_branch.name,
                                                  CAPEX=self.capex,
                                                  status=True,
                                                  group=group))
            # ...and one deactivates the original branch, so the corridor runs at the new rating.
            circuit.add_investment(dev.Investment(device=self.target_branch,
                                                  code=self.target_branch.code,
                                                  name="Deactivate original: " + self.target_branch.name,
                                                  CAPEX=0.0,
                                                  status=False,
                                                  group=group))
            return upgraded
        elif self.kind == CandidateKind.ShuntReactor:
            # A reactor only absorbs (Bmin=0); the continuous shunt control sizes the actual B
            # within [0, Bmax] during a power flow to hit Vset, so only the cap needs to be built
            # here - see CandidateGenerationDriver._make_shunt_reactor_candidates for the sizing.
            shunt = dev.ControllableShunt(name=f"Shunt reactor @ {self.target_bus.name}",
                                          Bmin=0.0,
                                          Bmax=self.shunt_bmax,
                                          Gmin=0.0,
                                          Gmax=0.0,
                                          number_of_steps=1,
                                          vset=self.shunt_vset,
                                          control_mode=ShuntControlMode.Continuous,
                                          active=False)
            circuit.add_controllable_shunt(self.target_bus, shunt)
            circuit.add_investment(dev.Investment(device=shunt,
                                                  code=shunt.code,
                                                  name="Shunt reactor: " + shunt.name,
                                                  CAPEX=self.capex,
                                                  group=group))
            return shunt
        elif self.kind == CandidateKind.StaticGenerator:
            static_gen = dev.StaticGenerator(name=f"Static generator @ {self.injection_bus.name}",
                                             P=self.injection_p,
                                             Q=0.0,
                                             Snom=self.injection_snom,
                                             active=False)
            circuit.add_static_generator(self.injection_bus, static_gen)
            circuit.add_investment(dev.Investment(device=static_gen,
                                                  code=static_gen.code,
                                                  name="Static generator: " + static_gen.name,
                                                  CAPEX=self.capex,
                                                  group=group))
            return static_gen
        elif self.kind == CandidateKind.Battery:
            # control_mode defaults to V (voltage-controlled, like a PV bus), so voltage support at
            # this bus comes for free - no separate sizing is done for it, per the design decision.
            battery = dev.Battery(name=f"Battery @ {self.injection_bus.name}",
                                  P=self.injection_p,
                                  Pmin=0.0,
                                  Pmax=self.battery_pmax,
                                  Enom=self.battery_enom,
                                  control_mode=GeneratorControlMode.V,
                                  vset=1.0,
                                  active=False)
            circuit.add_battery(self.injection_bus, battery)
            circuit.add_investment(dev.Investment(device=battery,
                                                  code=battery.code,
                                                  name="Battery: " + battery.name,
                                                  CAPEX=self.capex,
                                                  group=group))
            return battery
        else:
            raise ValueError(f"Unhandled candidate kind: {self.kind}")


class CandidateGenerationResults:
    """
    Results of the candidate-investment generator pipeline.
    """

    def __init__(self):
        self.base_case_converged: bool = False
        self.base_case_feasible: bool = False
        self.base_loading_report: List[str] = list()
        self.violations: List[ViolationRecord] = list()
        self.candidates: List[ReinforcementCandidate] = list()
        self.verification_report: List[str] = list()

        # Static-generator/battery candidates: kept as their own list/track rather than merged into
        # ``candidates``. They score in the same unit (MW of overload relief) as new-line/upgrade,
        # but are capped at ``options.max_injection_mw`` (tens of MW) while a transmission line's
        # implicit capacity is hundreds to thousands of MW - sharing one ranked list would starve
        # them of verification slots regardless of how good a fit they are for their site.
        self.injection_candidates: List[ReinforcementCandidate] = list()

        # Voltage screening (base case, always on) and the shunt-reactor candidates it drives.
        # Kept as its own list/track rather than merged into ``candidates``: shunt-reactor scores
        # are in p.u. (voltage excess) while every other kind scores in MW (overload relief), so a
        # single sorted list would let unit scale silently starve one kind of verification slots.
        self.voltage_violations: List[VoltageViolationRecord] = list()
        self.voltage_candidates: List[ReinforcementCandidate] = list()

        # Populated only when the generator ran in time-series critical-snapshot mode.
        self.critical_time_idx: Optional[int] = None
        self.critical_time_label: str = ""
        self.n_overloaded_at_critical: int = 0
        self.n_voltage_violated_at_critical: int = 0
        self.voltage_violation_report: List[str] = list()

    @property
    def base_violations(self) -> List[ViolationRecord]:
        """Base-case (N) violations."""
        return [v for v in self.violations if v.is_base_case]

    @property
    def n1_violations(self) -> List[ViolationRecord]:
        """N-1 violations."""
        return [v for v in self.violations if not v.is_base_case]

    @property
    def verified_candidates(self) -> List[ReinforcementCandidate]:
        """
        Overload-relief candidates that passed verification: verified with a converged AC power
        flow and no new violations introduced. This is the shortlist offered to the user in the GUI.
        """
        return [c for c in self.candidates if c.verified_ok]

    @property
    def verified_injection_candidates(self) -> List[ReinforcementCandidate]:
        """
        Injection-relief (static generator/battery) candidates that passed verification: verified
        with a converged AC power flow and no new violations introduced.
        """
        return [c for c in self.injection_candidates if c.verified_ok]

    @property
    def verified_voltage_candidates(self) -> List[ReinforcementCandidate]:
        """
        Voltage-relief (shunt reactor) candidates that passed verification: verified with a
        converged AC power flow and no new violations introduced.
        """
        return [c for c in self.voltage_candidates if c.verified_ok]

    def summary_text(self) -> str:
        """
        Assemble the textual report shown in the GUI: base-case status, per-branch loading extract,
        the N-1 violation list, and the verification outcome for the top candidate(s).
        """
        lines: List[str] = list()

        # Critical snapshot (only present in time-series mode)
        if self.critical_time_idx is not None:
            lines.append("=== Critical snapshot (time series) ===")
            lines.append(f"Time index: {self.critical_time_idx}" +
                        (f" ({self.critical_time_label})" if self.critical_time_label else ""))
            lines.append(f"Overloaded branches: {self.n_overloaded_at_critical}")
            lines.append(f"Voltage-violated buses: {self.n_voltage_violated_at_critical}")
            if len(self.voltage_violation_report):
                lines.append("Voltage violations at the critical snapshot (see 'Voltage screening' "
                             "section below for shunt-reactor candidates):")
                for line in self.voltage_violation_report:
                    lines.append("  " + line)
            lines.append("")

        # Step 1: base case
        lines.append("=== Base case AC power flow ===")
        lines.append("Converged: " + ("yes" if self.base_case_converged else "no"))
        lines.append("Feasible (no base-case overloads): " + ("yes" if self.base_case_feasible else "no"))
        if len(self.base_violations):
            lines.append("Base-case overloads:")
            for v in self.base_violations:
                lines.append("  " + v.describe())
        lines.append("")

        # Step 2: N-1 screening
        lines.append("=== N-1 screening (LODF) ===")
        if len(self.n1_violations):
            for v in self.n1_violations:
                lines.append("  " + v.describe())
        else:
            lines.append("  No N-1 overloads found.")
        lines.append("")

        # Step 2: voltage screening (base case, always on)
        lines.append("=== Voltage screening (base case) ===")
        if len(self.voltage_violations):
            for v in self.voltage_violations:
                lines.append("  " + v.describe())
        else:
            lines.append("  No base-case voltage violations found.")
        lines.append("")

        # Steps 3-4: line/branch-scale overload-relief candidates (new line, upgrade)
        lines.append(f"=== Ranked candidates ({len(self.candidates)}) ===")
        if len(self.candidates) == 0:
            lines.append("  No candidates generated.")
        lines.append("")

        # Steps 3-4: injection-scale overload-relief candidates (static generator, battery)
        lines.append(f"=== Ranked injection-relief candidates (static generator/battery) "
                     f"({len(self.injection_candidates)}) ===")
        if len(self.injection_candidates) == 0:
            lines.append("  No injection-relief candidates generated.")
        lines.append("")

        # Steps 3-4: voltage-relief (shunt reactor) candidates
        lines.append(f"=== Ranked voltage-relief candidates (shunt reactors) ({len(self.voltage_candidates)}) ===")
        if len(self.voltage_candidates) == 0:
            lines.append("  No shunt-reactor candidates generated.")
        lines.append("")

        # Step 5: verification
        if len(self.verification_report):
            lines.append("=== Verification (AC PF + N-1 + voltage) ===")
            lines.extend("  " + r for r in self.verification_report)

        return "\n".join(lines)
