# Repository map and evidence guide

Audit date: 2026-10-08. Scope: all files present in the supplied workspace. No replacement implementation or changes to original files were made. This directory contains analysis and a read-only evidence collector only.

## Evidence conventions

- **Observed source:** behavior follows directly from the supplied source. Line numbers are one-based physical file lines; notebook references point to JSON lines and identify the relevant cell.
- **Observed execution:** executed in the audit environment, or explicitly identified as a saved historical notebook output.
- **Derived physics:** independently derived under stated assumptions; this does not establish the instrument's actual convention.
- **Unverified:** depends on missing instrument records, dependency versions, experimental calibration, or material provenance.

The complete file-by-file size and SHA-256 inventory, including every bytecode file, is in [baseline_evidence.json](./baseline_evidence.json). This is a supplied folder snapshot: no Git metadata, dependency manifest, tests, README, packaging configuration, or AGENTS.md was found.

## Structure

| Location | Contents and role |
|---|---|
| [RSM_main.ipynb](../RSM_main.ipynb) | Only populated entry point: interactive loading, conversion, mapping, rocking-curve fit, theoretical overlay |
| [Theoretical_RSM_main.ipynb](../Theoretical_RSM_main.ipynb) | One empty code cell; no executable workflow |
| [Modules/](../Modules/) | Eight Python source modules, inventoried below; no `__init__.py`, so imports rely on namespace-package behavior and repository root on Python's import path |
| [S0154/](../S0154/) | One measurement: CdS S0154, Temp300, Norm10-10, RSM30-32, InPlane000-1 |
| [S0183/](../S0183/) | One measurement: CdS S0183, Temp200, Norm10-10, RSM22-40, InPlane1-120; notebook default |
| [XRD data txt - for suplementary/](<../XRD data txt - for suplementary/>) | One nested measurement under `10-10/K0203 -T_275deg`: Temp275, Norm10-10, RSM20-20, InPlane11-20 |
| [Literature data for analysis/CIF/](<../Literature data for analysis/CIF/>) | Five structures: CdS, ZnS, alternative ZnS, cubic Ge, hexagonal Ge |
| [Reflections.xlsx](<../Literature data for analysis/Reflections.xlsx>) | Standalone reference workbook; no source code reads it |
| [__pycache__/](../__pycache__/) | Four historical caches: plotting, functions, fitting, data_procesing (CPython 3.11) |
| [Modules/__pycache__/](../Modules/__pycache__/) | Fifteen historical caches, including geometry for 3.10 and 3.11; several correspond to absent source |

The absent historical source names represented by caches include `functions`, `crystal_defenitions`, `findCOM`, `fitting_models`, `spot_analysis`, and `linetrace`. Their names are evidence of earlier development, not proof of current functionality. Caches were inventoried and hashed, not executed or reverse-decompiled. Current source and saved notebook outputs are the behavioral evidence used here.

## Entry point and dependencies

[RSM_main.ipynb](../RSM_main.ipynb:9), cell 1, resets the IPython namespace, enables autoreload, imports six modules, suppresses warnings, and requests the Tk Matplotlib backend. Cell 2 sets 8047.8 as the X-ray energy, selects S0183, discovers `.dat` recursively, and loads the crystal collection ([lines 45–52](../RSM_main.ipynb:45)). Subsequent cells initialize data, plot maps, fit curves, and call the theoretical-plane helper. Execution counts are out of order, so the saved notebook is not evidence of a clean sequential successful run.

Runtime requirements inferred from imports:

| Dependency | Role | Evidence |
|---|---|---|
| Python / IPython / Jupyter | Namespace packages, notebook magics, interactive state | [notebook cell 1](../RSM_main.ipynb:9); metadata reports Python 3.11.4 at line 162 |
| NumPy | Arrays, trigonometric profile model, reductions, trapezoidal integral | [fitting](../Modules/fitting.py:127); `np.trapezoid` at line 137 requires a sufficiently recent NumPy (introduced in 2.0) |
| pandas | Whitespace and decimal-comma numeric input | [parser](../Modules/data_procesing.py:103) |
| xrayutilities | CIF interpretation, reciprocal vectors, alloys, HXRD transforms, gridding, cuts, reciprocal-plane plotting | [geometry](../Modules/geometry.py:23), [plotting](../Modules/plotting.py:43), [cuts](../Modules/data_procesing.py:154) |
| SciPy | Center of mass; bounded nonlinear least squares | [data_analysis](../Modules/data_analysis.py:2), [fitting](../Modules/fitting.py:3) |
| Matplotlib / Tk | Figures, logarithmic colors, notebook GUI backend | [plotting](../Modules/plotting.py:3), [notebook](../RSM_main.ipynb:25) |
| lmfit | Imported Gaussian2dModel but never used; still an import-time requirement for theory | [theory](../Modules/theory.py:9) |
| Standard library | Paths, file discovery, filename regex | [data_procesing](../Modules/data_procesing.py:1) |

No package versions are pinned. CIF comments mention pymatgen as a generator; pymatgen is not a runtime import. Excel libraries are not runtime requirements of the repository.

## Function inventory

| Module / function (definition line) | Actual responsibility and significant constraints |
|---|---|
| [geometry.crystal_defenitions](../Modules/geometry.py:6) | Load three fixed CIFs; nested `create_CdZnS` at line 16 creates a 0.35 alloy; return four fixed material keys. Cubic Ge path is assigned but not used. |
| [geometry.make_geometry](../Modules/geometry.py:40) | Convert both orientation index triples through `crystal.Q`; convert energy with `lam2en`; construct HXRD with `lo_hi` default. |
| [geometry.experiment_defenitions](../Modules/geometry.py:46) | Construct CdS, Ge, ZnS, alloy experiments, even when only CdS and Ge are needed. |
| [geometry.theoretical_om_tt](../Modules/geometry.py:66) | Q2Ang of a crystal reflection; discard two returned angles. |
| [geometry.theoretical_Qy_Qz](../Modules/geometry.py:71) | Transform a reciprocal vector; discard Qx. |
| [geometry.hkil_to_hkl](../Modules/geometry.py:76) | Warn if redundant index is inconsistent, then drop i regardless. |
| [data_procesing.string_to_hkil](../Modules/data_procesing.py:10) | Parse four signed single digits. No general multi-digit indexing. |
| [data_procesing.list_datafolders](../Modules/data_procesing.py:20) | Select immediate subdirectories by substring; unused by notebook's recursive glob. |
| [data_procesing.exp_paramameters](../Modules/data_procesing.py:32) | Array-valued parameter container for energy, dwell time, offsets, reflection and orientations. No validation. |
| [data_procesing.extract_token](../Modules/data_procesing.py:45) | Slice filename between prefix and delimiter; missing prefix raises, missing delimiter truncates last character. |
| [data_procesing.exp_data_from_file_title](../Modules/data_procesing.py:57) | Extract naming metadata, parse optional dwell/omega offset; material token unused; all orientation tokens use plane-index conversion. |
| [data_procesing.initialize_data](../Modules/data_procesing.py:93) | Read files; normalize by dwell; construct CdS geometry; calculate q; return three basename-keyed dictionaries. |
| [data_procesing.cut_range](../Modules/data_procesing.py:127) | Nearest endpoint slicing, upper endpoint excluded. Not used by main workflow. |
| [data_procesing.get_cut_indices](../Modules/data_procesing.py:137) | Find nearest indices around a selected component of a position vector; documented scalar input is not actually supported. |
| [data_procesing.get_cut_data](../Modules/data_procesing.py:141) | Half-open slice of coordinates and intensity. |
| [data_procesing.get_qmax_pos](../Modules/data_procesing.py:145) | Discrete argmax, not a fitted center; unused concatenation allocated. |
| [data_procesing.find_fixed_position](../Modules/data_procesing.py:152) | Alternating library line cuts near a predicted peak, 500 samples per cut; contains reused-index defect. |
| [data_analysis.read_key_reflection](../Modules/data_analysis.py:6), [read_sampleID](../Modules/data_analysis.py:10), [read_inplane_direction](../Modules/data_analysis.py:14), [read_Temp](../Modules/data_analysis.py:18), [read_Norm](../Modules/data_analysis.py:22) | Unvalidated substring extractors for plot grouping/labels. Sample ID requires MatCdS. |
| [data_analysis.find_max_tt_om](../Modules/data_analysis.py:31) | Aggregate onto angle-index matrix; threshold at 30% of max; rounded index centroid; return (2theta, omega). Unused in active workflow. |
| [line_scan.omega](../Modules/line_scan.py:5) | Mean intensity at each omega in a fixed 2theta band; draw strip boundaries in reciprocal or angular coordinates. |
| [line_scan.background_correction](../Modules/line_scan.py:28) | Returns input unchanged; subtraction is commented out. |
| [line_scan.average_psd_over_axis](../Modules/line_scan.py:41) | Inclusive band mask, exact grouping, arithmetic mean. |
| [plotting.plot_RSM](../Modules/plotting.py:37) | Grid, normalize, color map, predict peaks, choose extraction center, extract curve, create/close figures; return curve dictionaries, figure count, final vmax. |
| [plotting.plot_fwhm](../Modules/plotting.py:167) | Three fixed reflection/orientation groups; plot widths versus filename temperature, fixed limits/exclusions. Not called in notebook. |
| [fitting.remove_spikes](../Modules/fitting.py:10) | Remove points based on adjacent raw intensity jumps; always retain first. |
| [fitting.plot_analysis](../Modules/fitting.py:24) | Rebuild material geometries and theory angles, fit each curve, return FWHM and bounds only. Figure count and predicted 2theta unused. |
| [fitting.fitting](../Modules/fitting.py:59) | Filter, select ±2° around second-highest surviving point, fit one pseudo-Voigt, calculate approximate interval and descriptive metrics, optionally annotate. |
| [fitting.pseudo_voigt](../Modules/fitting.py:127) | Common-height/common-FWHM Gaussian–Lorentzian mixture. |
| [fitting.get_integral_breadth](../Modules/fitting.py:135) | Trapezoidal area divided by maximum on supplied finite interval. |
| [theory.plot_full_theoretical_RSM](../Modules/theory.py:16) | Fixed orientation, three-material reciprocal-plane display, print (300) predictions once per key; ignores supplied per-sample geometry. |
| [Colorsheme.thesis_colormap](../Modules/Colorsheme.py:10) | Four-color gradient, swatches, decorative preview, return hex colors; separate from duplicated colors in map routine. |

## Reading order

[Pipeline](./02_data_pipeline.md) → [equations](./03_physics_and_equations.md) → [coordinates](./04_coordinate_systems.md) → [assumptions](./05_hardcoded_assumptions.md) → [baseline behavior](./06_existing_behavior.md) → [errors](./07_potential_physics_errors.md) → [questions](./08_open_questions.md) → [rebuild requirements and executive summary](./09_rebuild_requirements.md).
