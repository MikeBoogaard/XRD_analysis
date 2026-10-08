# RSM toolkit progress

Updated 2026-10-08. Resume the working package; do not restart the Phase 1 analysis.

## Latest: new user-specified scans with provisional theory

User supplied substrate (11-20), Zn fraction 0.35 and aligned film, and authorized provisional [1-100] for the (12-30) scan; the other scan is (11-20) along [0001]. Generated both real-data overlays with [cdzns_12-30.json](examples/cdzns_12-30.json) and [cdzns_11-20.json](examples/cdzns_11-20.json). These supersede the missing-metadata blocker below **for these two new scans only**. Original S0159/S0155 assignments remain unconfirmed.

- Film model: explicit relaxed hexagonal linear Vegard interpolation of repository CdS/ZnS cells, x_Zn=0.35; no fitted strain or measured film metric.
- (12-30) positive measured Qy selects the provisional reversed azimuth: map +y opposite the supplied [1-100], sample_to_map=diag(-1,-1,1). This assumption is written in the configuration; neither angles nor markers were translated to force agreement. Substrate marker differs from the measured maximum, so orientation/zeroes need experimental checking.
- (11-20): provisional identity alignment with +y=[0001]. Both maps and all markers retain PROVISIONAL status.
- Independent formulas checked all four vectors: (12-30) Q=(0,2pi/(sqrt(3)a),6pi/a); (11-20) Q=(0,0,4pi/a). Substrate/film Qy,Qz respectively: (0.8770789962,4.5574361512)/(0.9022915069,4.6884441998) and (0,3.0382907675)/(0,3.1256294665), inverse angstrom.
- Outputs: [first plot](outputs/RSM_12-30_theory.png), [second plot](outputs/RSM_11-20_theory.png), matching NPZ and full JSON metadata. Original RAW files unchanged. Annotation offsets separate the two phase labels.

Reproduce (automatically saves PNG + NPZ + JSON):

```powershell
.venv/Scripts/python -m rsm_toolkit map "new_data/rsm(12-30)along10-10.raw" --config examples/cdzns_12-30.json --output outputs/RSM_12-30_theory.png
.venv/Scripts/python -m rsm_toolkit map "new_data/RSM(11-20)along0001.raw" --config examples/cdzns_11-20.json --output outputs/RSM_11-20_theory.png
```

## Completed and verified

- Installable `src/rsm_toolkit` package; editable install in `.venv` (Python 3.12.3). No runtime imports of legacy modules.
- Direct readers for the actual BRML 8.6.2.0 external Eiger profile and RAW4.00 PSD Fix Scan exports in `new_data`.
- Both measurements contain 1401×477 bins. All paired BRML/RAW counts match after float32 rounding; per-bin detector angles match to about 1.4e-14 degrees. No filename scientific parsing or count normalization.
- Explicit coplanar and general vector-rotation geometry; general reciprocal lattices, plane/direction indexing, independent phase/orientation objects, optional overlays.
- Point maps, explicit bin means/sums, PNG/PDF/SVG, NPZ+JSON round-trip, separate profile and empirical fitting utilities, CLI.
- Latest stored test run: **86 passed, zero skipped, in 25.62 s**, including xrayutilities reference comparison, all four real-file conversion/export tests, configuration regressions and 18 new overlay/archive tests. See [test_results.xml](outputs/test_results.xml).
- `examples/cdzns_on_cds_rsm.py` ran successfully for both pairs; outputs exist as `outputs/cdzns_on_cds_rsm.*` and `outputs/cdzns_on_cds_rsm_02.*`, plus `experimental_results.json`.
- Both PNGs visually inspected: axes, counts colorbar and provisional status are readable; measured features and sampling footprint visible. No crystal/phase assignments claimed.
- Original measurements and Phase 1 files are hash-protected by `docs/preserved_files.json`.

## Continuation milestone completed: validation closeout and handoff

- Inspected existing implementation and saved results; retained working parsers and coordinate equations without rebuilding them.
- Fixed configuration validation: strings such as `"false"` cannot be used as calibration/provisional boolean flags. Malformed JSON and invalid configuration roots now raise toolkit errors. Added 11 regression cases; targeted configuration/geometry suite passed 22 tests before the full 68-test run.
- Wrote [experimental_report.md](docs/experimental_report.md) with per-file results, numerical comparisons, outputs and scientific limitations.
- Recorded [requirements-tested.txt](requirements-tested.txt) and updated README recreation instructions. A fresh independent environment has not been tested.
- Installed CLI inspection passed on actual BRML and RAW files; RAW-to-grid CLI map/export passed: [cli_smoke.png](outputs/cli_smoke.png), NPZ and JSON alongside it.
- Built [rsm_toolkit-0.1.0-py3-none-any.whl](outputs/wheels/rsm_toolkit-0.1.0-py3-none-any.whl); inspected its 19 entries and imported directly from the wheel with Python isolated mode. No legacy modules are packaged.
- Original inputs and Phase 1 analysis remain unchanged; preservation tests passed.

## Overlay/configuration/cleanup continuation (2026-10-08)

- Reused existing reciprocal lattice and RAW/BRML conversion; added [overlays.py](src/rsm_toolkit/overlays.py) and unified JSON support. Film and substrate have independent cell/orientation/reflection lists. Explicit lattice or user-fraction Vegard interpolation; no Zn default.
- Theory requires an explicit proper sample-to-map rotation, matching frame, reference, and provisional opt-in where necessary. Missing metadata, off-plane and wavelength-inaccessible reflections fail before output. Substrate circles/film diamonds and labels are distinct; exports record numerical theory and full settings.
- [cdzns_on_cds.json](examples/cdzns_on_cds.json) is an editable **incomplete specimen template**, with unknowns null and overlays disabled. [Configuration guide](docs/run_configuration.md) gives the command and convention. Its measured-only CLI run passed and saved [cdzns_configured.png](outputs/cdzns_configured.png), NPZ and JSON.
- Overlay rendering on actual S0159 RAW intensity was tested using **explicitly synthetic test lattices/orientations**, not assumed CdZnS composition. [Validation plot](outputs/validation/synthetic_overlay.png) was visually checked and labeled accordingly. It is NOT the requested experimental CdS/CdZnS prediction. Its [input](outputs/validation/synthetic_overlay_config.json) and output sidecar use different paths. Reproduce with `.venv/Scripts/python -m rsm_toolkit map new_data/22-40_RSM_S0159.raw --config outputs/validation/synthetic_overlay_config.json --output outputs/validation/synthetic_overlay.png`.
- Archived retired source/notebooks and old root bytecode with verified hashes; extracted notebook content before removing 8 Modules sources and 2 root notebooks. Removed generated legacy caches/build. All experimental/reference/Phase 1 preservation tests passed. See [cleanup record](docs/legacy_cleanup.md). Source paths in Phase 1 now correspond to ZIP entry paths.
- Prior wheel in outputs/wheels predates these overlay changes; use the current editable package or rebuild a wheel. No new runtime dependency was added.

## First unfinished milestone: actual CdS/CdZnS overlay

**Blocked by missing specimen metadata, not by the overlay implementation.** User was asked for scan choice, Zn fraction or film a/c, substrate surface plane, direct +in-plane direction, film orientation and reflection indices. No answer was available during implementation. Do not label the synthetic validation figure as a fulfilled experimental overlay. Once supplied, update the unified file with evidence-backed sample-to-map alignment, enable overlays, run its documented command, inspect/save the real theory report and plot. Instrument calibration remains a separate requirement for verified rather than provisional coordinates.

## Calibrated experimental sample frame

The software can already load all four supplied files and produce nominal coplanar maps. The next milestone depends on the experimental metadata below. Do not add guessed Chi/Phi rotations or promote the existing maps to verified. Obtain the evidence, configure the existing geometry API, validate against a standard, then regenerate the outputs. No further parser rewrite or legacy compatibility work is needed for these inputs.

## Scientific blockers — do not guess

- Actual surface plane, in-plane direction, film orientation, and calibrated meanings/order/zeroes of Chi/Phi are unavailable. Chi=0.3°/0.44°, Phi=0.51°/90° are recorded but are not automatically applied by the nominal coplanar model.
- Thus existing maps are **provisional in the nominal coplanar frame**, not certified sample-normal maps. Qx=0 is the declared projection; the original detector integrated a transverse ROI.
- Composition and film lattice parameters remain unspecified. No lattice-based overlay is enabled in the real-data example.
- External BRML binary codec is narrowly validated against these paired RAW exports, not a general vendor specification. Unknown variants must continue to fail explicitly.

## Commands and next scientifically useful work

```powershell
.venv/Scripts/python -m pytest -q --junitxml=outputs/test_results.xml
.venv/Scripts/python examples/cdzns_on_cds_rsm.py
.venv/Scripts/python -m rsm_toolkit inspect new_data/22-40_RSM_S0159.brml
```

Obtain the mounting/azimuth and calibration-standard records. Configure the actual axis model, test against a known symmetric/asymmetric reference, then regenerate calibrated maps and optional overlays. Do not spend effort on S0154 or legacy compatibility. Keep `analysis_docs` and original measurements unchanged. The commands above are reproduction commands; the example and full tests have already passed, so do not rerun them just to rediscover the current state.
