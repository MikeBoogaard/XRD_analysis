# Existing behavior and preserved baseline

## Execution scope and provenance

[audit_baseline.py](./audit_baseline.py) ran from the repository root with `python -B analysis_docs/audit_baseline.py`. It disables bytecode writes, uses the Agg backend for imports, and puts Matplotlib cache files inside this analysis directory. It hashes originals, imports modules without mocks, parses all three datasets with the repository's exact pandas call, inspects workbook OOXML without recalculation, runs available helper checks and independent Bragg calculations, then compares hashes. It does not execute notebook magics, install packages, change code, or replace missing dependencies.

Evidence is recorded in [baseline_evidence.json](./baseline_evidence.json). A second run added scan-range/extrema details and redirected streams to [baseline_stdout.txt](./baseline_stdout.txt) and [baseline_stderr.txt](./baseline_stderr.txt). The first run exited 0. The redirected invocation reported shell exit 1 with PowerShell NativeCommandError formatting around the expected SciPy zero-centroid RuntimeWarning; it nevertheless completed the evidence JSON and stdout. This wrapper result is retained rather than reported as a clean run. There is no traceback indicating failure to write the evidence.

All **38 original files**, including inputs, source, notebooks, workbook, CIFs and historical caches, matched their pre-execution SHA-256 hashes. No original reference outputs were regenerated or overwritten.

| Environment | Observed version / result |
|---|---|
| Python | 3.12.3, conda-forge, Windows |
| NumPy | 2.2.5 |
| pandas | 2.2.3 |
| SciPy | 1.15.2 |
| Matplotlib | 3.10.1 |
| xrayutilities | ModuleNotFoundError |
| lmfit | ModuleNotFoundError |

Imports of geometry, data_procesing, plotting, fitting and theory all stop at missing xrayutilities; the lmfit absence is independently confirmed, though masked by the earlier import failure in theory. line_scan, data_analysis and Colorsheme import successfully. Full angle conversion, map rendering and real-data fitting were **not freshly executed**. Installing an arbitrary modern dependency would not reproduce the undocumented historical environment, so no such substitution was made. The unmodified notebook also requires IPython and a Tk GUI backend; the audit's import-only Agg setting is explicitly not a faithful GUI replay.

## Input baseline

Source files are linked below; numbers come from parsing every row, not sampling. Three float64 columns, finite values and no duplicate (omega,2theta) pairs were observed in all files.

| Data | Rows | Omega range / step (°) | 2theta range (°) | Intensity min / max | Zero / negative values |
|---|---:|---|---|---|---|
| [S0154](../S0154/MatCdSS0154_Temp300_Norm10-10_RSM30-32_InPlane000-1_omscan=abs.dat) | 572,877 | 23–29 / 0.005 | 81.615055–100.381277 | −2,144,047,674 / +2,144,047,674 | 469,382 / 24,684 |
| [S0183](../S0183/MatCdSS0183_Temp200_Norm10-10_RSM22-40_InPlane1-120_omscan=abs.dat) | 527,379 | 17.5–23 / 0.005 | 91.6008731861–109.3954581065 | 0 / 41,848.7890625 | 223,918 / 0 |
| [K0203](<../XRD data txt - for suplementary/10-10/K0203 -T_275deg/MatCdSK0203_Temp275_Norm10-10_RSM20-20_InPlane11-20_omscan=abs.dat>) | 335,779 | 22.5–29.5 / 0.01 | 48.6008731861–55.3954581065 | 0 / 482,172.90625 | 2 / 0 |

S0154 has 1,201 omega settings with 477 rows each; S0183 has 1,101 with 479; K0203 has 701 with 479. S0154 uses decimal-point text, while the other two use decimal commas; all parsed successfully under the existing pandas configuration.

S0154's first/last omega detector windows are 81.615055–88.381277° and 93.615055–100.381277°: a 12° shift for 6° omega change. S0183's are 91.6008731861–98.3954581065° and 102.6008731861–109.3954581065°: an 11° shift for 5.5° omega change. K0203's window is unchanged between endpoints. This is consistent with differing coupled versus fixed detector scans, but the acquisition definitions and intermediate scan law require instrument records. Merely seeing `omscan=abs` on all three files does not resolve this difference.

The S0154 maximum is on [line 1323](../S0154/MatCdSS0154_Temp300_Norm10-10_RSM30-32_InPlane000-1_omscan=abs.dat:1323) and minimum on [line 7019](../S0154/MatCdSS0154_Temp300_Norm10-10_RSM30-32_InPlane000-1_omscan=abs.dat:7019). Billion-scale signed values are anomalous for ordinary count-like intensities. They could reflect upstream corruption, overflow, sentinels or another encoding; this audit cannot identify the cause. They must not be silently clipped into a trusted map. The existing parser accepts them without warning.

The inactive centroid would allocate a dense float matrix of 1,645,763,928 bytes for S0154 and 1,421,514,312 bytes for S0183 after rounding t to four decimals, before SciPy temporaries. K0203 needs only 2,686,232 bytes. These sizes follow directly from unique-axis counts and [allocation at line 44](../Modules/data_analysis.py:44); the large centroid calls were not run.

## Historical outputs retained in the notebook

- Cell 2 stores sulfur-charge substitution warnings ([notebook line 39](../RSM_main.ipynb:39)).
- Cell 3 stores invalid S0183 in-plane-index warning, then its filename ([line 65](../RSM_main.ipynb:65)).
- Cell 4 stores `UnboundLocalError: cannot access local variable 'com_tt_data' where it is not associated with a value` ([line 81](../RSM_main.ipynb:81)). This matches the missing `22-40` branch in current source; the historical traceback uses `<string>` and cannot prove identical source revision.
- Final cell stores CdS (ω,2θ)=(10.177876384327154,80.35575276865431) and Ge (12.03043598681558,84.0608719736312) ([line 136](../RSM_main.ipynb:136)). Independent metric/Bragg calculation agrees.
- No image payloads or serialized FWHM outputs are stored. The fitting cell has execution count 14 but no output; this does not prove it succeeded in a clean sequential run after the displayed exception.

## Reference workbook

[Reflections.xlsx](<../Literature data for analysis/Reflections.xlsx>) has one sheet, Sheet1, populated A1:D14: Material, Reflection, Omega, 2 theta. The inspected populated cells are literal values, with no formulas. Thirteen reference rows include twelve CdS and one LiNbO3 reflection. Code never reads this workbook, so it is supplementary historical intent, not runtime configuration.

Examples: row 7 gives CdS 20-20, omega 25.4744°, 2theta 50.9488°; row 8 gives CdS 30-30, 40.1778° / 80.3557°, consistent with the supplied CdS metric for symmetric incidence. Row 4 gives 2-1-10, omega 23.785° but 2theta 0; row 5 gives CdS 03-30, omega 12.0304° and missing 2theta. Row 14 gives CdS 0002, 18° / 36°, inconsistent with the loaded c=6.716 Å at λ≈1.5406 Å (which predicts 2theta≈26.5°). These could be placeholders, mislabeled materials or different measurement configurations. No orientation/energy/provenance metadata resolves them. Exact cell values are retained in the evidence JSON; the workbook was neither recalculated nor edited.

## Executed helper checks

| Check | Observed result |
|---|---|
| Mean strip with two intensities 2,4 at omega 0 and a third excluded point | omega=[0], intensity=[3]; confirms arithmetic mean |
| Thresholded centroid with one positive occupied point | Returns (tt,omega)=(4,2), preserving documented return order |
| All-zero centroid | SciPy RuntimeWarning then ValueError: cannot convert float NaN to integer |
| Label parsers on `other.dat` | Return fragments such as `her.da`, `.da`, `er.da` rather than validation errors |
| Independent (300) Bragg/metric calculation | Agrees with saved CdS/Ge outputs to floating-point precision |

## Malformed/different-input behavior inferred from source

The following are **static predictions**, not all experimentally executed, because affected modules cannot import without xrayutilities.

| Condition | Existing behavior and evidence |
|---|---|
| Missing file / empty file | pandas exception; no recovery ([parser:103](../Modules/data_procesing.py:103)) |
| Fewer than three columns | Array indexing fails; extra columns ignored ([parser:108](../Modules/data_procesing.py:108)) |
| Header/non-numeric/ragged rows | Parser or later numeric operations fail, or NaNs propagate; no schema validation |
| Missing Mat/RSM/Norm/InPlane prefix | extract_token raises ValueError ([line 48](../Modules/data_procesing.py:48)) |
| Missing delimiter after token | end=-1 slices off the last character ([line 51](../Modules/data_procesing.py:51)) |
| Multi-digit or differently encoded indices | Regex parses single digits; wrong count raises, four accidental digits can be misinterpreted ([line 11](../Modules/data_procesing.py:11)) |
| Invalid redundant index | Warning only; wrong value discarded ([geometry:77](../Modules/geometry.py:77)) |
| Zero/negative dwell | Divide by zero or sign reversal; no validation ([parser:110](../Modules/data_procesing.py:110)) |
| No discovered files | Initialize returns empty dictionaries; plot_RSM returns undefined vmax ([plotting:163](../Modules/plotting.py:163)) |
| Unsupported reflection first in plot call | Undefined com_tt_data; S0183 historical instance confirms it ([plotting:110](../Modules/plotting.py:110)) |
| Unsupported reflection after supported one | May reuse previous iteration's center, making results order-dependent |
| Empty cut / peak outside window | Empty argmax/reduction or empty line trace; no explicit missing-peak status ([cuts:145](../Modules/data_procesing.py:145)) |
| All-zero/negative/nonfinite map | Invalid normalization/log scaling; no guards ([plotting:70](../Modules/plotting.py:70)) |
| Single-point/empty fit curve | First-element or second-highest indexing fails ([fitting:11](../Modules/fitting.py:11), [line 66](../Modules/fitting.py:66)) |
| Fit mode other than pseudo voigt | y_fit and width variables undefined ([fitting:76](../Modules/fitting.py:76)) |
| Constant curve / singular fit | Undefined R², covariance warning or optimizer failure, no handling |
| Crystal files absent / case-sensitive system | CIF loading fails; uppercase/lowercase paper discrepancy matters ([geometry:13](../Modules/geometry.py:13)) |
| Different material | Still converted/annotated as fixed CdS/Ge phases; no material registry |
| Off-plane scan / pixel channel rather than 2theta input | No explicit interpretation or validation; not supported by local data contract |

## What is supported today

The source provides an interactive, specialized path for already angle-calibrated three-column maps, fixed hexagonal materials, qy–qz gridding, two reflection-specific rocking-curve extraction cases, and a single empirical width model. Arbitrary filenames, materials, detector images, 3D scans, general orientation conventions and robust batch analysis are not demonstrated. The supplied default workflow has a saved failure; the one supplied file using an implemented extraction branch (K0203) has not been fully replayed in the audit environment. There is no validated end-to-end baseline image or width result to use as a scientific gold standard.
