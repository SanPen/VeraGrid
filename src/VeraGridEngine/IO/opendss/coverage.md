# OpenDSS import coverage

`opendss_to_veragrid()` imports an OpenDSS circuit through the optional
`OpenDSSDirect.py` package and returns a VeraGrid `MultiCircuit`. The importer
maps supported network elements into VeraGrid devices and sends warnings and
import information to the supplied VeraGrid `Logger`. OpenDSSDirect is imported optionally; installing
VeraGrid does not require it. Calling the importer without the package raises
an `ImportError` with installation guidance.

```python
from VeraGridEngine.IO.opendss import opendss_to_veragrid

grid = opendss_to_veragrid("path/to/Master.dss")
```

The current importer targets a **balanced positive-sequence** network. It does
not reproduce OpenDSS's full unbalanced distribution model or run OpenDSS
controls inside VeraGrid.

## Device coverage

| OpenDSS element | VeraGrid representation | Coverage and limits |
| --- | --- | --- |
| Bus | `Bus` | Imports bus names and voltage bases. OpenDSS line-to-neutral base voltage is converted to VeraGrid line-to-line `Vnom`. A missing base is imported as 0 kV and logged as a warning. |
| `Vsource` | `ExternalGrid` | Imports all sources. The first successfully mapped source is voltage-controlled and marked slack; later sources are imported in PQ mode. |
| `Line` | `Line` or `Switch` | Zero-length and switch lines become switches, preserving open/closed state. Other lines use their R/X/C conductor matrices, line length and units, normal current rating, and sequence R0/X0 fields. Neutral conductors are Kron-reduced when present. The positive-sequence model cannot preserve single-phase or two-phase topology; those lines are represented by a balanced equivalent and warned. The imported ABC series and shunt matrices are stored in VeraGrid's `ys` and `ysh` fields. |
| `WireData` | `Wire` | Imports resistance, GMR, diameter, and normal ampacity with unit conversion. OpenDSS material/stranding metadata not exposed by the API is not inferred. |
| `CNData`, `TSData` | `UndergroundCableType` | Imports cable dimensions and conductor resistance. The VeraGrid core/sheath cable model approximates OpenDSS concentric-neutral and tape-shield construction; TSData tape-layer details are not retained and are warned. |
| `LineCode` | `SequenceLineType` | Imports sequence-defined and matrix-defined resistance, reactance, capacitance, and normal current rating. Lines that reference a LineCode link to the reusable template; the complete compiled matrices remain stored in the line's `ys` and `ysh`. |
| `LineGeometry` | `OverheadLineType` or `UndergroundLineType` | Imports conductor/cable references, phase positions, and earth resistivity into VeraGrid physical line systems. Lines that reference a geometry are linked to that template while retaining the compiled line matrices in `ys` and `ysh`. Cable neutrals and mixed bare conductors in cable geometry are logged and omitted because VeraGrid's cable system has no separate neutral-conductor relationship. |
| `LineSpacing` | `OverheadLineType` | Imports direct `Spacing` + `Wires` line definitions using the OpenDSSDirect active-class JSON interface. It creates a per-line physical template. If the installed OpenDSSDirect version does not expose the needed JSON properties, the importer logs the limitation and leaves the electrical line import intact. |
| Series `Reactor` | `SeriesReactance` | Imports R and X in per-unit on the VeraGrid system base. |
| Shunt `Reactor` | `Shunt` | Approximates the reactor as fixed susceptance from bus voltage and X. Losses and phase detail are omitted and a warning is emitted. |
| Two-winding `Transformer` | `Transformer2W` | Imports nominal rating, leakage R/X, bus voltage ratings, and the solved tap ratio. Regulator controls are not recreated; solved taps are baked into a fixed ratio and logged. Winding connection, phase shift, core-loss, and detailed phase data are not represented by this mapping. |
| Three-winding `Transformer` | `Transformer3W` | Imports the first three winding buses and pairwise leakage data as a three-winding equivalent. The conversion uses a common-base approximation. Per-winding tap/control details and winding connection/phase behavior are not reproduced. Other winding counts or invalid bus references are skipped with a warning. |
| `Load` | `Load` | Imports total kW/kvar as MW/MVAr. Load model/ZIP composition, profiles, and unbalanced phase allocation are not retained. One- and two-phase loads are converted to balanced total P/Q and warned. |
| `Capacitor` | `Shunt` | Imports kvar as fixed shunt susceptance. Capacitor control logic, switching behavior, and per-phase state are not recreated. |
| `Generator` | `Generator` | Imports operating kW/kvar and kVA. OpenDSS model 3 maps to voltage control; other models map to `control_mode=Q` with the imported kvar held fixed. Models 2, 5, and 6 are operating-point P/Q approximations and are warned. Model 3 uses a 1.0 pu voltage setpoint because OpenDSS Vpu and reactive limits are not transferred. Dispatch controls, profiles, dynamic behavior, and detailed phase data are not imported. |
| `PVSystem` | `StaticGenerator` | Imports operating kW/kvar and kVA. Inverter controls, irradiance/temperature profiles, and detailed phase data are not imported. |
| `Storage` | `Battery` | Imports operating kW/kvar, kVA, rated energy, and state of charge. OpenDSS dispatch mode, time profiles, efficiency settings, and detailed phase behavior are not mapped. |
| `Isource` | `CurrentInjection` | Converts solved terminal P/Q to an equivalent constant injection. This preserves the operating point, not the current-source law, and emits a warning. |
| `Sensor` | State-estimation measurements | Maps available branch P/Q to from- or to-end measurements, voltage to bus `VmMeasurement`, and current to a positive-sequence branch current measurement. Values are aggregated across measured phases; percent error is used to derive uncertainty. Per-phase measurements and voltage angles are not represented. |

## Not mapped

OpenDSS circuit elements that have no mapping in the table are not converted.
Their names are logged as warnings when OpenDSSDirect exposes them through
`Circuit.AllElementNames()`. Known element types that fail conversion because
of invalid topology or missing buses are also logged as warnings.

Examples of behavior not imported as executable VeraGrid controls include
`RegControl`, `CapControl`, `Relay`, `Recloser`, `Fuse`, and `SwtControl`.
`Monitor` and `EnergyMeter` reporting/zone behavior is also not reproduced.
OpenDSS curves, spectra, and load shapes are not imported as reusable VeraGrid
profiles. OpenDSS wire and cable construction models remain approximate where
their geometry does not match VeraGrid's physical asset models.

## Import diagnostics

Pass a VeraGrid `Logger` through the `logger` argument to receive warnings for
approximations, skipped elements, unsupported objects, and missing optional
dependencies. An informational entry confirms the number of buses imported.

`solve=True` (the default) solves the source circuit before converting device
operating points. Set `solve=False` to import without that solve; any element
conversion that relies on solved values will then use the values OpenDSS
currently exposes for the compiled circuit.
