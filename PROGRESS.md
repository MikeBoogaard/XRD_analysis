# RSM toolkit progress

Updated 2026-10-08. Resume the working package; do not restart the Phase 1 analysis.

## Completed and verified

- Installable `src/rsm_toolkit` package; editable install in `.venv` (Python 3.12.3). No runtime imports of legacy modules.
- Direct readers for the actual BRML 8.6.2.0 external Eiger profile and RAW4.00 PSD Fix Scan exports in `new_data`.
- Both measurements contain 1401×477 bins. All paired BRML/RAW counts match after float32 rounding; per-bin detector angles match to about 1.4e-14 degrees. No filename scientific parsing or count normalization.
- Explicit coplanar and general vector-rotation geometry; general reciprocal lattices, plane/direction indexing, independent phase/orientation objects, optional overlays.
- Point maps, explicit bin means/sums, PNG/PDF/SVG, NPZ+JSON round-trip, separate profile and empirical fitting utilities, CLI.
- Latest stored test run: **68 passed, zero skipped, in 17.33 s**, including xrayutilities reference comparison, all four real-file conversion/export tests, and configuration regressions. See [test_results.xml](outputs/test_results.xml).
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

## First unfinished milestone: calibrated experimental sample frame

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
