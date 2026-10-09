# Experimental validation report

Updated 2026-10-08. The package imports and reconstructs both supplied CdZnS-on-CdS measurements from their actual BRML and RAW exports. The calculations are verified for the **declared nominal coplanar convention**. The experimental sample frame remains **provisional**, pending mounting and calibration records.

## Per-file outcome

| File | Import | Conversion | Result |
|---|---|---|---|
| [22-40_RSM_S0159.brml](../example_data/22-40_RSM_S0159.brml) | Pass: DIFFRAC 8.6.2.0, external Eiger 1D count profile | Pass, nominal coplanar | 1401×477 bins; maximum recorded intensity 1272.08 |
| [22-40_RSM_S0159.raw](../example_data/22-40_RSM_S0159.raw) | Pass: RAW4.00 PSD Fix Scan | Pass; agrees with paired BRML | 1401 ranges ×477 bins |
| [2200_RSM_S0155.brml](../example_data/2200_RSM_S0155.brml) | Pass: same BRML codec profile | Pass, nominal coplanar | 1401×477 bins; maximum recorded intensity 1587.1501 |
| [2200_RSM_S0155.raw](../example_data/2200_RSM_S0155.raw) | Pass: RAW4.00 PSD Fix Scan | Pass; agrees with paired BRML | 1401 ranges ×477 bins |

No supplied new file failed. No S0154 input was used. No reflection index or sample group was inferred from the source names. The user's stated film/substrate identities are attached as context, not used in the angle conversion.

Both records explicitly specify OmegaTwoThetaScan, UltraFastRSM, Coplanar and 0.5 s per step. Omega spans 17.5–24.5°; detector-arm angle spans 95–109°. The calibrated per-channel offsets expand the full 2theta range to 91.6150547296–112.3812767337°. The used method wavelength is 1.5406 Å. Both scans have the same angular ranges despite their different names.

## Checks on the actual data

- All **668,277 intensities in each pair** match exactly when BRML float64 values are rounded to the RAW float32 representation. Maximum absolute rounding differences are 4.3945312427e-5 and 4.9218750064e-5 recorded counts. These are export-precision differences, not count normalization.
- Theta, per-bin TwoTheta, TwoThetaArm, Chi and Phi arrays agree between paired exports within 2e-12°; largest observed per-bin angle difference is approximately 1.42e-14°.
- Counting-time arrays agree exactly; used wavelengths agree exactly.
- Converted Q arrays agree within a maximum component difference of **3.10862446895e-15 Å⁻¹**.
- Every reconstructed vector satisfies the elastic magnitude identity to the test tolerances (`atol=5e-14 Å⁻¹`, `rtol=1e-13`). This checks arithmetic, not sample alignment.
- NPZ/JSON exports round-trip the full Q, intensities and motor arrays exactly.
- Source data and Phase 1 analysis hashes are checked by the automated preservation test against [preserved_files.json](preserved_files.json).

The two file formats are independent encodings of the same acquisition, not independent physical experiments. Their agreement establishes parsing consistency; it does not establish correct instrument alignment or crystal orientation.

## Delivered outputs

The executed [example](../examples/cdzns_on_cds_rsm.py) saves:

| Measurement | Map | Numerical data | Metadata |
|---|---|---|---|
| First pair | [PNG](../outputs/cdzns_on_cds_rsm.png), [PDF](../outputs/cdzns_on_cds_rsm.pdf), [SVG](../outputs/cdzns_on_cds_rsm.svg) | [NPZ](../outputs/cdzns_on_cds_rsm.npz) | [JSON](../outputs/cdzns_on_cds_rsm.json) |
| Second pair | [PNG](../outputs/cdzns_on_cds_rsm_02.png), [PDF](../outputs/cdzns_on_cds_rsm_02.pdf), [SVG](../outputs/cdzns_on_cds_rsm_02.svg) | [NPZ](../outputs/cdzns_on_cds_rsm_02.npz) | [JSON](../outputs/cdzns_on_cds_rsm_02.json) |

[experimental_results.json](../outputs/experimental_results.json) records the source hashes, configurations, comparison errors, plotting settings, warnings and brightest measured bins. Both PNGs were visually inspected: axes and intensity units are legible; provisional status is prominent; no clipped labels or missing plots were observed. The primary views are raw-point displays, not interpolated fields. The fixed four-decade display range affects color only. It masks 580,180 and 567,056 zero values respectively, retains them unchanged in the numeric exports, and reports the masking on each figure. White areas can include masked zeros or space outside the measured footprint; they must not be interpreted as proof of no scattering.

## Brightest measured bins (no phase assignment)

| Measurement | Omega (°) | Bin 2theta (°) | Qy (Å⁻¹) | Qz (Å⁻¹) | Recorded intensity |
|---|---:|---:|---:|---:|---:|
| First pair | 18.145 | 96.33080998796 | −3.04058271936 | 5.26211500098 | 1272.08 |
| Second pair | 18.160 | 96.30395097952 | −3.03733382534 | 5.26251848243 | 1587.1501 |

These are discrete brightest-bin coordinates, not fitted centers, confidence intervals, phase identification, film composition or strain. Broader features are visible in both maps, but no film/substrate assignment is inferred solely from their appearance.

## Scientifically checked transformations

Analytical tests cover elastic Q magnitude, wavelength scaling, symmetric/asymmetric signs, rocking arcs, rotation order, right-handedness, dimensional units, general reciprocal metrics, hexagonal d spacings and direct-versus-reciprocal indexing. A separate Rodrigues-vector implementation agrees with the coplanar formula. xrayutilities **1.8.0** QConversion, configured with explicitly matching axes, agrees within 1e-12 Å⁻¹. Structure-factor cancellation is checked on an explicit full-cell motif. These are mathematically independent checks of the specified conventions.

The original working snapshot had 57 passing tests with no skips; continuation added strict boolean/configuration regressions so malformed JSON cannot promote provisional geometry to verified. The authoritative current count and failures are in [test_results.xml](../outputs/test_results.xml) and the latest [PROGRESS.md](../PROGRESS.md). Test tolerances for analytical identities are near floating-point precision; they are **not** instrument uncertainty estimates.

## Unresolved experimental interpretation

1. The surface plane and in-plane crystal direction have not been supplied. The files report UB usage Off; crystal orientation is not recovered from a filename.
2. Chi/Psi-H is 0.3° for the first measurement and 0.44° for the second. Phi-H is 0.51° and 90°. Their motor-axis ordering, zero references and relationship to the mounted sample remain unverified. The example preserves those values but does not invent a rotation correction.
3. Qy/Qz therefore refer to the explicitly labeled **nominal coplanar frame**, not a certified surface-parallel/surface-normal frame. Qx=0 is a model projection; the Eiger 1D profile integrates a finite transverse ROI.
4. Angular calibration, detector calibration uncertainty, and source wavelength uncertainty need experimental standards/logs. Recorded target coordinates do not prove encoder accuracy.
5. Film composition, lattice parameters and strain state are unknown. No CdS/ZnS interpolation or crystal overlay is selected automatically. A geometric reciprocal vector also does not establish a permitted observable reflection.
6. Fractional counts reflect upstream detector ROI/rebinning operations. No raw-Poisson uncertainty, dead-time/absorption correction, or physical linewidth interpretation is assumed.

To obtain a scientifically calibrated sample-frame RSM: provide mounting/azimuth information, a documented motor sequence/sign/offset definition, and a known symmetric/asymmetric calibration scan. Then configure the validated frame, check expected reflection positions and regenerate the maps. The existing code accepts explicit geometry and material/orientation objects; this step requires evidence rather than another speculative implementation.

## Unsupported features and reproducibility

Only the tested RAW4 PSD and external BRML codec profiles are claimed. Unknown RAW versions, different external memory layouts, unsupported scan modes and uncalibrated arbitrary area-detector frames raise errors. Full space-group/CIF symmetry expansion and atomic form-factor databases are not implemented. See [format support](file_formats.md) and [coordinate conventions](coordinates.md).

The environment uses Python 3.12.3 on Windows, NumPy 2.2.5, SciPy 1.15.2, Matplotlib 3.10.1, pytest 9.1.1 and xrayutilities 1.8.0. [requirements-tested.txt](../requirements-tested.txt) pins the complete selected runtime/test/reference dependency set. The development virtual environment reuses preinstalled core numerical packages through `--system-site-packages`; the pins allow recreation in a clean environment. No claim is made that such a clean environment was downloaded and tested on another operating system.
