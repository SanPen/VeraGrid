# CGMES Conversion Implementation Review Spec (Codex)

This document is a **review checklist + rulebook** for assessing a CGMES conversion implementation (exporter and/or importer).
It focuses on what Codex should verify: **format correctness, semantics, dependency integrity, profile coherence, boundary handling, and validation gates**.

> Assumption: Your implementation produces or consumes CGMES CIMXML (RDF/XML) instance files (FullModel and, where applicable, DifferenceModel)
> across the standard ENTSO-E/IEC CGMES profile families (EQ/SSH/TP/SV/GL/DL/DY…).

---

## 0) Definitions used in this spec

- **File**: a single RDF/XML document containing CIM instances and an `md:Model` header.
- **Dataset / Exchange**: a set of files intended to be assembled together for a given `scenarioTime` and `modelingAuthoritySet`.
- **IGM**: individual grid model (single modelling authority).
- **CGM**: common grid model (assembly/merge output).
- **Boundary set**: versioned bundle of boundary/reference datasets used consistently during assembly.
- **Profile**: a constrained view of CIM used for exchange (e.g., EQ, SSH, TP, SV).

---

## 1) Hard requirements: identifiers and object identity

### 1.1 IdentifiedObject.mRID
Codex checks:
- Every CIM object derived from `IdentifiedObject` has **exactly one** `mRID`.
- `mRID` is **globally unique** within an assembled model.
- `mRID` is **persistent** across exports of the *same* real-world equipment.
- `mRID` follows **UUID** format (RFC 4122).

Failure mode: unstable or non-unique mRIDs makes assembly, diff application, and traceability unreliable.

### 1.2 RDF subject IDs normalisation
Codex checks:
- The exporter uses stable RDF subjects (prefer `rdf:about="urn:uuid:<uuid>"`).
- If legacy `rdf:ID` forms appear, the converter:
  - parses them correctly,
  - normalises internally to a canonical form,
  - preserves identity mapping to `mRID`.

---

## 2) File header and metadata correctness (md:Model)

Your converter MUST produce/consume valid header metadata and dependency semantics.

### 2.1 Required md:Model fields (minimum)
Codex checks the presence and parseability of:

- `md:Model.scenarioTime` (the “as-of” model time)
- `md:Model.created` (serialization time)
- `md:Model.version` (integer; changes only if content changes)
- `md:Model.profile` (one-to-many profile URIs)
- `md:Model.modelingAuthoritySet` (MAS identifier)
- `md:Model.DependentOn` (when the profile/file requires other files)
- `md:Model.Supersedes` (when file replaces another file)

### 2.2 Header ↔ filename / packaging consistency
Codex checks:
- Filename metadata (if used by your process) is consistent with header: scenario time, MAS, profile.
- `version` increments when content changes, not when only filenames change.
- `created` changes on regeneration, even if `scenarioTime` is the same.

### 2.3 Dependency closure and resolvability
Codex checks:
- All `DependentOn` references resolve within the dataset (or within an explicitly supplied dependency bundle such as a boundary/reference package).
- The dependency graph is acyclic for a single assembled model (cycles indicate malformed assembly semantics).
- Assembly can be performed deterministically starting from SV (see §6).

Failure mode: dangling dependencies => model cannot be assembled.

---

## 3) Namespace and profile coherence

### 3.1 Namespace consistency rule
Codex checks:
- All files in a single assembly use **compatible CIM namespaces** (no mixing of different CIM major versions in one assembly).
- Prefixes can vary, but namespace URIs must be coherent.

### 3.2 Profile URIs and profile membership
Codex checks:
- Every file advertises its profile URI(s) in the header.
- The content is consistent with that profile (class/attribute membership + required elements).
- Your converter does not silently “leak” objects from one profile into another in a way that violates exchange conventions.

---

## 4) Representation support: node-breaker, bus-branch, hybrid

Your implementation MUST handle these representations at import and export.

### 4.1 ConnectivityNode and TopologicalNode expectations
Codex checks:
- **Core EQ includes ConnectivityNode** objects (node-breaker foundation).
- **Topology (TP)** represents computed or designed topology via TopologicalNodes.

### 4.2 Terminal connectivity semantics (critical)
Codex checks:
- Terminals connect consistently to:
  - ConnectivityNode and/or
  - TopologicalNode
  depending on the dataset’s representation and included profiles.
- When a `RegulatingControl` is associated with a `Terminal`, `Terminal.TopologicalNode` is present (required in that case).

Failure mode: PF and SV linkage becomes inconsistent; regulators can’t be resolved to buses.

---

## 5) Topology (TP) and State Variables (SV) semantics

### 5.1 TP exchange constraints
Codex checks:
- TP is exchanged **only as FullModel** (never as DifferenceModel).
- TP is treated as output of topology processing; do not attempt to “merge TP by ID” across models.

### 5.2 SV exchange constraints
Codex checks:
- SV values refer to the correct equipment/terminals/topological nodes.
- SV dependency chain is valid (see §6).
- SV is consistent with SSH/EQ (e.g., states align with switched device statuses and injections).

---

## 6) Deterministic assembly procedure (what your implementation must support)

Codex assembles a model as follows; your conversion must make this possible.

### 6.1 Assembly starting point
Rule: **Assembly starts from the SV file** for a given scenarioTime+MAS.

Codex checks:
- An SV file exists for each assembled IGM/CGM snapshot (unless your process explicitly excludes SV).
- From SV, `DependentOn` resolves the minimal closure of required EQ/SSH/TP and auxiliary files.

### 6.2 Dependency traversal
Codex checks:
- `DependentOn` provides a complete closure for required files.
- Boundary/reference dependencies are either:
  - included in the dependency closure, or
  - provided as explicit “always available” packages with versioning.

---

## 7) Boundary + reference data handling (assembly-critical)

### 7.1 One boundary set per CGM creation
Codex checks:
- CGM assembly uses **exactly one** boundary set version (official/latest per your process).
- Your implementation does not mix objects from multiple boundary versions in one assembled CGM.

### 7.2 Bilateral boundary logic
Codex checks:
- Boundary datasets are treated as **bilateral** agreements (per border/per neighbour).
- Import supports multiple boundary files grouped into a versioned package.

### 7.3 Duplicate handling rules
Codex checks:
- No single instance file contains duplicates.
- During assembly, duplicates are permitted **only** when originating from boundary/reference datasets as defined by the boundary process.
- Post-merge output does not contain unintended duplicates.
- BoundaryPoints are preserved in merged output to support disassembly.

Failure mode: naive deduplication breaks border equivalences; naive “reject duplicates” breaks assembly.

### 7.4 Boundary “minimalism”
Codex checks:
- Boundary model is minimal (ideally just the ConnectivityNode + necessary containers), and
- model parts intended for assembly (IGMs) do not overlap boundary objects incorrectly.

---

## 8) HVDC / AC-DC boundary rules (if your converter supports DC)

Codex checks the following (common interoperability breaker):

### 8.1 HVDC boundary modelling (strict)
Rule:
- HVDC boundary shall be represented as **one cim:Line** that contains the **two boundary points** (one per side of an HVDC Pole).
- Modelling DC boundary as **two cim:Line** objects each with a single boundary point is **not allowed**.

### 8.2 HVDC modelling level compatibility
Codex checks:
- If a modelling option that explicitly “cannot be combined with DC IGM” is used, your tool blocks that assembly path or flags it clearly.
- Shunts/filters (if modelled for voltage control) are placed as required by the chosen modelling level (process guidance prefers AC IGM placement in common cases).

---

## 9) PST modelling checks (Phase Shifting Transformers)

Codex checks:
- PST types are mapped to the correct CIM tap changer class:
  - general case: PhaseTapChangerTabular (preferred)
  - symmetrical: PhaseTapChangerSymmetrical or PhaseTapChangerLinear
  - asymmetrical: PhaseTapChangerAsymmetrical
  - in-phase + phase-shift: RatioTapChanger + PhaseTapChangerSymmetrical

Codex warnings (not necessarily fatal):
- If non-tabular PST exchange is used, validate that your implementation’s per-tap recalculation is consistent and documented.

---

## 10) Validation gates: QoCDC-style levels and blocking behaviour

Codex evaluates your converter against an 8-level validation pipeline.
Your implementation should support producing outputs that pass levels 1–6.

### 10.1 Levels (what Codex runs)
1. Filename metadata (if applicable in your process)
2. XML/RDF syntax + header/metadata correctness
3. Intra-file CIM constraints (required attributes/cardinalities, consistent references)
4. Model assembly viability (dependency closure; consistent packaging)
5. Cross-profile consistency (EQ/SSH/TP/SV coherence)
6. Plausibility after PF (optional if your pipeline includes PF; otherwise structural plausibility)
7. Coordination (cross-IGM, market coordination) — non-blocking
8. Convergence behaviour — non-blocking

### 10.2 Blocking policy
Codex default policy:
- **Levels 1–6**: ERROR = block / fail review
- **Levels 7–8**: never blocking by default (report only)

---

## 11) Conversion implementation review: what Codex expects to see

This section is a “code review checklist” for your CGMES conversion implementation.

### 11.1 Importer requirements
- Robust RDF/XML parser supporting large files (streaming preferred).
- Namespace-aware parsing (prefix changes tolerated).
- Identity mapping strategy:
  - stable `mRID` extraction,
  - stable subject ID handling,
  - collision detection and reporting.
- Dependency resolver for `DependentOn` and boundary packages.
- Profile-aware validation hooks (so errors are attributed to profile constraints).

### 11.2 Exporter requirements
- Deterministic serialisation:
  - stable ordering where possible,
  - stable IDs,
  - stable container structure.
- Correct header synthesis for:
  - FullModel exports,
  - DifferenceModel exports (where used),
  - Supersedes / DependentOn semantics.
- Profile separation rules:
  - objects appear in the right file(s),
  - no illegal cross-profile leakage.

### 11.3 Assembly / merge requirements
- Assembly procedure is explicit and testable:
  - start from SV,
  - traverse dependencies,
  - apply boundary/reference consistently.
- Duplicate policy is correct (boundary duplicates allowed, others rejected).
- Topology processing:
  - if you recompute TP, accept that TopologicalNode mRIDs can change,
  - do not attempt to merge TP by reusing old topological IDs.

### 11.4 Diagnostics requirements
Codex expects:
- Clear error categories aligned to validation levels.
- Exact object references in diagnostics (mRID + class + file).
- A “minimal reproduction” mode:
  - ability to export dependency closure for a failing SV.

---

## 12) Minimal test suite Codex will use (you should have these)

1) **Single IGM**: EQ+SSH(+TP+SV), passes levels 1–6.
2) **IGM with boundary**: import boundary set + IGM; assemble without duplicates beyond allowed boundary duplicates.
3) **Multi-IGM CGM assembly**: 2+ IGMs + same boundary set; ensure deterministic assembly.
4) **Topology recomputation case**: show TP regenerated; ensure semantics remain consistent even if TopologicalNode mRIDs change.
5) **PST case**: at least one PST using tabular tap changer; validate exported attributes.
6) **HVDC case (if supported)**:
   - boundary as one line with two boundary points,
   - reject two-line single-boundarypoint form.

---

## 13) Severity rubric (Codex default)

**ERROR (fail review)**
- Unresolvable header dependencies
- Mixed incompatible namespaces in one assembly
- Missing required md:Model fields
- Missing ConnectivityNodes in Core EQ
- TP exported as diff
- Illegal HVDC boundary modelling (two lines with single boundarypoint each)
- Duplicate objects not attributable to boundary/reference rules
- Non-unique or unstable mRIDs within assembled model

**WARN (review notes)**
- Non-UUID mRID formats that can be normalised
- Non-tabular PST exchange without documented recalculation
- Boundary overlap beyond minimalism guidance
- Missing optional profiles (GL/DL) when expected by your process, but not required

---

## 14) What Codex needs from you during review (inputs)

To review your implementation, Codex expects:
- A sample dataset bundle (or fixture generator) containing:
  - at least one valid IGM closure,
  - boundary/reference package,
  - optional HVDC + PST fixtures.
- A description of:
  - how you generate mRIDs,
  - how you build headers (DependentOn/Supersedes),
  - your profile mapping rules,
  - your boundary versioning mechanism.
- A log output example of a failed validation with:
  - level,
  - severity,
  - object mRID/class,
  - source file.

---

End of spec.
