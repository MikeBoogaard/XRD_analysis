# RSM toolkit progress

Updated 2026-10-09. Resume the working package; do not restart the Phase 1 analysis.

## Application icon and example data consolidation

- Moved the supplied PNG unchanged into [package icons](src/rsm_toolkit/data/icons/rsm.png). The GUI loads it as its window icon at four sizes; installed wheels include the asset. Restart the GUI to see it.
- Adopted the user's renamed [example_data](example_data) directory, including S0154 and S0183. Moved the remaining supplementary measurement directory beneath it, retaining its internal folders and file bytes. Crystallographic references and generated outputs remain in their existing locations.
- Updated preset paths, example scripts, tests, current documentation and preservation-manifest paths. Original preservation hashes and Phase 1 analysis are unchanged. Historical output metadata retains original paths; reselect the measurement when loading saved settings that reference a former location.
- Validation: **113 passed in 36.55 s**, including Tk icon/preset smoke checks, GUI plot-to-preview execution, experimental plotting and data preservation checks. Wheel rebuilt; packaged PNG verified byte-for-byte. No remaining work for this adjustment.

## Current product update: direct directions and CIF materials

User reports expert confirmation that the asymmetric map is correct and requests normal production presentation. Treat the prior mismatch investigation as historical; do not apply its empirical omega correction.

- GUI now says **Presets**, uses direct crystal directions exclusively, and has no convention selector or provisional acknowledgement/status. The asymmetric preset uses [1-100], retaining the established opposite-Qy sense; symmetric uses [0001]. Both extra offsets remain zero. Checked the updated configurations against the previous maps: measured Q arrays are identical; theoretical markers agree within 1e-14 inverse angstrom.
- Added [material_library.py](src/rsm_toolkit/material_library.py), reading the five bundled CIF cell metrics for CdS, two ZnS references, cubic Ge and hexagonal Ge. Available for both substrate and film; CdZnS Vegard and custom cells remain supported. CIF copies are byte-identical to the preserved references and packaged as wheel resources.
- Removed provisional gating, figure/marker badges and new-export status flags. Existing API/configuration fields and older export reading remain accepted for compatibility; factual calibration metadata is not fabricated. Geometry, lattice, indexing, wavelength and off-plane validation remain active.
- GUI settings now use schema rsm-gui-2. Direct-direction v1 settings load safely. Reciprocal-reference v1 settings with overlays prompt the user to enter equivalent direct directions instead of silently reinterpreting the same indices.
- Rewrote [README.md](README.md) as normal user documentation with a simple tutorial, presets, materials and setup. Removed rebuild/history references from the GUI and README. Historical scientific analysis and original data are preserved.
- Regenerated [symmetric plot](outputs/RSM_11-20_theory.png) and [asymmetric plot](outputs/RSM_12-30_theory.png), plus metadata, without status badges. Asymmetric plot visually checked.
- Validation: **112 passed, 1 skipped in 40.35 s**. One withdrawn Tk end-to-end display test could not obtain a Tk display; core worker, material, coordinate, export and remaining GUI tests passed. Wheel build succeeded and all five materials loaded directly from the wheel.

The dated sections below record prior work; this section supersedes their user-interface and status-label descriptions.

## Latest: desktop GUI and beginner tutorial

- Launch by double-clicking [Start RSM GUI.cmd](<Start RSM GUI.cmd>) or running `.venv/Scripts/python -m rsm_toolkit gui` from the repository root. [gui.py](src/rsm_toolkit/gui.py) provides File/Sample/Advanced tabs, a PNG preview, open-output-folder button and load/save settings.
- [gui_workflow.py](src/rsm_toolkit/gui_workflow.py) translates validated form fields into the existing unified configuration and reuses readers, calculations, overlays and exports. Worker subprocess keeps Tk responsive. Every run creates a unique timestamped folder containing PNG, NPZ, metadata, GUI settings, CLI configuration and warnings; failures are explicit.
- Norm/RSM accept validated separated or compact four-index notation. Old-style InPlane is explicitly a reciprocal-plane reference projected onto the surface, unlike a direct crystal direction. A parallel reference or inconsistent indices are rejected. Earlier discussion established this equivalence for the current scans; no legacy filename parsing or silent correction restored.
- Material choices: CdS reference, explicit-percent CdZnS Vegard, custom general cell, or no film. Independent film orientation supported; aligned films share Cartesian crystal axes. No guessed Zn fraction or custom cell metric. Intensity-only maps need no material settings.
- GUI requires nominal coplanar acknowledgement and explicit along/opposite axis sense for theory. All GUI maps remain provisional; calibrated arbitrary vector geometry remains in the existing CLI/API. Geometry-only CLI behavior unchanged. Existing advanced JSON files are not silently simplified into GUI forms; load/save uses its own `rsm-gui-1` settings schema.
- Both supplied scan presets reproduce existing Q arrays and theoretical markers. Both offsets remain zero; **the unresolved asymmetric mismatch is deliberately unchanged**, per user instruction. No automatic fitting/alignment added.
- [README beginner tutorial](README.md#beginner-tutorial-plot-with-the-desktop-window) explains one-time setup, launching, examples, all required inputs, automatic saving and settings reuse. Pillow (already present via plotting dependencies) is now explicitly declared for GUI previews; Tk comes from Python's Tcl/Tk installation.
- Validation: **105 tests passed, zero skipped, in 30.85 s**. Includes 18 GUI/workflow tests, real-file worker output, synthetic and physical projection checks, preservation, prior CLI and analytical checks, and a withdrawn Tk end-to-end Plot-button/worker/preview test on Windows. Widget requested sizes fit the default window; no manual desktop usability review is claimed. See [test_results.xml](outputs/test_results.xml).

## Latest diagnostic: asymmetric mismatch

User authorized testing the alignment plan. [Alignment report](docs/asymmetric_alignment_check.md) records metadata checks and a local substrate Gaussian fit. No matching BRML is available; RAW type-60 Delta is not an established correction (older paired BRML separates Delta and offsets). Phi/Chi axis mapping remains unresolved.

A separate **empirical reference trial**, omega +0.777397 degrees, aligns the fitted substrate direction; Q error decreases from 0.062983 to 0.001752 inverse angstrom, with remaining 2theta residual -0.029928 degrees. This is reference-derived, not recovered Bruker calibration or proof of a phi cause. Original maps/configurations remain unchanged. See [comparison](outputs/alignment_check/comparison.png), [trial configuration](outputs/alignment_check/omega_reference_trial.json), [report](outputs/alignment_check/report.json). Reproduce with `.venv/Scripts/python examples/check_asymmetric_alignment.py`. Do not transfer the correction to other scans or set calibration_verified=true.

## Latest: new user-specified scans with provisional theory

User supplied substrate (11-20), Zn fraction 0.35 and aligned film, and authorized provisional [1-100] for the (12-30) scan; the other scan is (11-20) along [0001]. Generated both real-data overlays with [cdzns_12-30.json](examples/cdzns_12-30.json) and [cdzns_11-20.json](examples/cdzns_11-20.json). These supersede the missing-metadata blocker below **for these two new scans only**. Original S0159/S0155 assignments remain unconfirmed.

- Film model: explicit relaxed hexagonal linear Vegard interpolation of repository CdS/ZnS cells, x_Zn=0.35; no fitted strain or measured film metric.
- (12-30) positive measured Qy selects the provisional reversed azimuth: map +y opposite the supplied [1-100], sample_to_map=diag(-1,-1,1). This assumption is written in the configuration; neither angles nor markers were translated to force agreement. Substrate marker differs from the measured maximum, so orientation/zeroes need experimental checking.
- (11-20): provisional identity alignment with +y=[0001]. Both maps and all markers retain PROVISIONAL status.
- Independent formulas checked all four vectors: (12-30) Q=(0,2pi/(sqrt(3)a),6pi/a); (11-20) Q=(0,0,4pi/a). Substrate/film Qy,Qz respectively: (0.8770789962,4.5574361512)/(0.9022915069,4.6884441998) and (0,3.0382907675)/(0,3.1256294665), inverse angstrom.
- Outputs: [first plot](outputs/RSM_12-30_theory.png), [second plot](outputs/RSM_11-20_theory.png), matching NPZ and full JSON metadata. Original RAW files unchanged. Annotation offsets separate the two phase labels.

Reproduce (automatically saves PNG + NPZ + JSON):

```powershell
.venv/Scripts/python -m rsm_toolkit map "example_data/rsm(12-30)along10-10.raw" --config examples/cdzns_12-30.json --output outputs/RSM_12-30_theory.png
.venv/Scripts/python -m rsm_toolkit map "example_data/RSM(11-20)along0001.raw" --config examples/cdzns_11-20.json --output outputs/RSM_11-20_theory.png
```

## Completed and verified

- Installable `src/rsm_toolkit` package; editable install in `.venv` (Python 3.12.3). No runtime imports of legacy modules.
- Direct readers for the actual BRML 8.6.2.0 external Eiger profile and RAW4.00 PSD Fix Scan exports in `example_data`.
- Both measurements contain 1401×477 bins. All paired BRML/RAW counts match after float32 rounding; per-bin detector angles match to about 1.4e-14 degrees. No filename scientific parsing or count normalization.
- Explicit coplanar and general vector-rotation geometry; general reciprocal lattices, plane/direction indexing, independent phase/orientation objects, optional overlays.
- Point maps, explicit bin means/sums, PNG/PDF/SVG, NPZ+JSON round-trip, separate profile and empirical fitting utilities, CLI.
- Latest stored test run: **105 passed, zero skipped, in 30.85 s**, including xrayutilities reference comparison, real-file conversion/export tests, GUI workflow, configuration regressions and overlay/archive tests. See [test_results.xml](outputs/test_results.xml).
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
- Overlay rendering on actual S0159 RAW intensity was tested using **explicitly synthetic test lattices/orientations**, not assumed CdZnS composition. [Validation plot](outputs/validation/synthetic_overlay.png) was visually checked and labeled accordingly. It is NOT the requested experimental CdS/CdZnS prediction. Its [input](outputs/validation/synthetic_overlay_config.json) and output sidecar use different paths. Reproduce with `.venv/Scripts/python -m rsm_toolkit map example_data/22-40_RSM_S0159.raw --config outputs/validation/synthetic_overlay_config.json --output outputs/validation/synthetic_overlay.png`.
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
.venv/Scripts/python -m rsm_toolkit inspect example_data/22-40_RSM_S0159.brml
```

Obtain the mounting/azimuth and calibration-standard records. Configure the actual axis model, test against a known symmetric/asymmetric reference, then regenerate calibrated maps and optional overlays. Do not spend effort on S0154 or legacy compatibility. Keep `analysis_docs` and original measurements unchanged. The commands above are reproduction commands; the example and full tests have already passed, so do not rerun them just to rediscover the current state.
