# Rebuild requirements and executive summary

This document specifies behavior and scientific acceptance criteria for a later rebuild. It does not prescribe the current modules as the future architecture, and no replacement has been implemented.

## Scientific and functional requirements

| ID | Requirement | Acceptance evidence |
|---|---|---|
| R01 | Preserve raw observations, original files, units, source identity and processing provenance | Immutable source hashes; unique path/run identity; every output traces to configuration and input |
| R02 | Read the supplied whitespace decimal-comma/point tables with explicit schema; allow future parsers without encoding physics in filenames | All three supplied row counts/ranges reproduced; missing/malformed fields reported; additional columns retained or explicitly handled |
| R03 | Represent energy/wavelength, angle definitions, dwell, monitor normalization, corrections and uncertainties explicitly | Dimensional validation, positive-time checks, energy/wavelength consistency and recoverable metadata |
| R04 | Separate instrument angle-to-q kinematics from material reference calculations | The same calibrated measurement maps identically regardless of which overlay material is selected |
| R05 | Define laboratory, sample, direct-crystal and reciprocal-crystal frames, handedness, axis order, degrees/radians and 2π convention | Written convention, basis/unit tests and asymmetric reference measurements |
| R06 | Distinguish direct directions [uvw]/[uvtw] from plane normals (hkl)/(hkil); validate redundant indices | General multi-digit signed indices, metric-aware conversion, rejection of ambiguous/invalid orientation metadata |
| R07 | Support arbitrary physically valid cell metrics and user-selected phases, reference structures and orientation relationships | Cubic, hexagonal and nonorthogonal test cells; independent reciprocal-metric checks; no required CdS/Ge keys |
| R08 | Define supported scan/detector modes explicitly | Coplanar omega/2theta maps first; correctly interpret supplied fixed and shifting detector windows; future detector images require actual calibration models, not inferred pixels |
| R09 | Preserve full 3D q and accessibility information even when displaying a 2D plane | qx retained and checked; off-plane reflections flagged; full motor solution available where needed |
| R10 | Validate reference structures and record composition/strain/temperature assumptions | Provenance and uncertainties; independent d-spacing and extinction checks; alloy model/fraction explicit |
| R11 | Keep intensity transformations scientifically distinct from display scaling | Counts/rate/monitor corrections recorded; masks separate from zero; negatives and sentinels not silently hidden; logarithmic display does not change fit data |
| R12 | Offer documented gridding and reduction definitions with coverage and uncertainty | Test density, bin width, duplicates and empty cells; specify whether output is mean, sum or integrated intensity; no accidental cross-map state |
| R13 | Define peak selection independently for each map and reflection | Arbitrary reflection support; explicit target phase and search bounds; missing/overlapping peak statuses; file-order invariance |
| R14 | Support scientifically specified angle or q cuts without requiring plotting | Units and half/full widths explicit; irregular sampling and finite detector coverage handled; outputs numerical and inspectable |
| R15 | Make fitting model, baseline, bounds, weighting, masks and fit range explicit | Retain parameters/covariance/residuals/selection; synthetic recovery and repeated-measurement validation; fit failure remains visible |
| R16 | Report empirical widths separately from derived physical properties | No mosaicity/size/strain inference without a justified resolution and broadening model |
| R17 | Export reproducible numeric results and figures with accurate labels and explicit exclusions | User-selected formats (to be agreed); per-map normalization scale, configuration, uncertainty and fit status included |
| R18 | Run deterministically in batch/headless mode and optionally interactively | Pinned environment, no global warning suppression, no GUI object required for numerical analysis |
| R19 | Preserve legacy fixtures without enshrining defects as correctness | Historical errors/anomalies recorded; explicit distinction between behavioral regression and validated physical expectations |

## Independent validation matrix

| Layer | Check | Expected property |
|---|---|---|
| Units | Convert 8047.8 eV independently | λ≈1.5405974109 Å |
| Crystal metric | AᵀB and known cubic/hexagonal spacings | 2πI and analytical d values |
| Orientation | Direct direction versus plane normal; arbitrary rotations | Correct distinct mappings, norm preservation, right-handed frame |
| Coplanar transform | Symmetric reflection, zero detector deflection, fixed-2theta rocking scan | qy=0 at omega=theta; q=0 at 2theta=0; constant q magnitude along rocking arc |
| Signed geometry | Opposite asymmetric reflections on calibrated specimen | Experimentally correct qy sign and axis orientation |
| Theory | CdS/Ge (300) values in saved notebook | Reproduce metric/branch numbers while retaining any extra required motor angles |
| Detector/scan | Original motor/pixel records versus table rows | Correct calibration and scan coupling for each supplied measurement type |
| Intensity | Synthetic counts, varied dwell, missing bins, negative sentinel cases | Traceable units/variance; no silently invented measurements |
| Gridding | Uniform field, impulse, varied density and successive extents | Documented averaging/integration, explicit coverage, no stale state |
| Cuts | Constant/known 2D field and irregular sampling | Correct mean versus integral and coordinate units |
| Fits | Analytic Gaussian/Lorentzian limits, mixed profiles, overlap/background/noise | Recover expected width within justified tolerance; expose model failure |
| Uncertainty | Repeat scans or simulated known noise ensembles | Interval coverage assessed independently of covariance assumptions |
| Robustness | Missing metadata, duplicate basename, unsupported reflection, empty/singular input | Explicit status/error; no stale center or overwritten results |

Tolerances should follow floating-point precision for algebraic identities and calibration/resolution uncertainty for experiments. Matching a legacy number is not sufficient when the legacy result conflicts with verified geometry.

## Reuse, replace, and defer decisions

**Reusable physical principles:** elastic scattering q=kf−ki, energy–wavelength conversion, lattice duality, Bragg law, explicit frame transformations and the algebraically correct common-FWHM pseudo-Voigt. Reuse the principles after validating conventions, not necessarily their current API wrappers. The independent (300) check provides a useful narrow reference.

**Useful historical behavior to preserve as fixtures:** three input datasets and metadata spellings; scalar dwell normalization; angle-band arithmetic means; map color choices if desired; empirical FWHM definitions; actual error messages and anomalous inputs. Preserving a fixture does not require reproducing a scientific error in the validated path.

**Unnecessary specialization to remove:** fixed CdS/Ge/ZnS keys, mandatory alloy construction, filename-only metadata, single-digit indices, reflection-specific extraction branches, hardcoded orientation in theory, fixed plot groups/limits, GUI-dependent fit flow and embedded specimen/temperature labels.

**Decisions that require evidence:** instrument signs and offsets, direct versus reciprocal orientation intent, raw intensity meaning, detector calibration, material reference provenance, S0154 anomaly handling and physical interpretation of widths. Do not choose plausible defaults and present them as established experiment facts.

## Executive summary

Scientifically, this repository is an exploratory notebook workflow for converting exported omega–2theta intensity tables into two-dimensional qy–qz reciprocal-space maps, overlaying selected hexagonal material reflections, extracting angle-band rocking curves and fitting empirical widths. It is not a general diffractometer reconstruction, a structure refinement system or a validated strain/mosaicity analysis.

The reusable physics consists of elastic-scattering kinematics, reciprocal-lattice geometry, Bragg peak prediction and standard profile mathematics. Independent calculation reproduces the saved CdS and Ge (300) angle predictions. That validates one metric/energy/branch example; it does not validate the measured maps' orientation or instrument conventions.

The software is unnecessarily specialized to fixed CdS/hex-Ge/ZnS structures, filename conventions, a 35%-argument alloy, selected reflections and temperature groups. Data parsing, phase assumptions, peak selection, fitting and figure state are tightly coupled. The default S0183 notebook already records a plotting failure, and current source contains normalization and peak-search-index defects.

The missing historical dependency environment prevents a fresh complete baseline run. Instrument signs, absolute angle semantics, orientation labels, intensity units/corrections and material provenance remain unvalidated. S0154 additionally contains large signed intensity anomalies, and the CdS/hex-Ge CIFs contain inconsistent volume metadata. All 38 original files were preserved unchanged, including these inputs and saved notebook outputs.

A general-purpose replacement must make instrument geometry, crystal/sample orientation, units, metadata and uncertainty explicit; support configurable materials and reflections; preserve full reciprocal vectors and raw data; separate numerical reductions from display; validate peak/fit models and failure states; and provide reproducible numerical and graphical exports. Its acceptance criteria must include independent physical standards, not only agreement with this repository.

Analysis is complete and ready for review. Implementation is deferred until the scientific questions and intended scope are reviewed.
