# Open questions and required evidence

These questions identify decisions needed before a scientifically validated rebuild. They do not block completion of this repository audit. Priority A affects coordinate or intensity correctness; B affects quantitative analysis; C affects scope and reproducibility.

| ID | Priority | Question | Evidence needed / acceptance criterion | Current evidence |
|---|---|---|---|---|
| Q01 | A | What instrument, motor axes, detector and acquisition/export software produced each file? | Instrument geometry diagram, axis order/signs, detector model, representative original export header | No configuration beyond default HXRD ([geometry](../Modules/geometry.py:40)) |
| Q02 | A | Is column 0 absolute incidence omega, an encoder value, or an offset such as omega−theta? Is column 1 absolute beam deflection for each pixel? | Match several table rows to motor and detector-channel logs, including first/last scan positions | Direct use of columns; `omscan=abs` ignored ([parser](../Modules/data_procesing.py:108)) |
| Q03 | A | Why do S0154/S0183 detector windows move by 2Δomega while K0203's is fixed? | Original scan programs, coupling settings and upstream angle-conversion equations | [Measured endpoint differences](./06_existing_behavior.md) |
| Q04 | A | Does InPlane denote a direct crystallographic direction or reciprocal plane normal? | Mounting drawing, crystal indexing convention and known azimuth | Both normal and in-plane use Q ([geometry](../Modules/geometry.py:41)) |
| Q05 | A | What was intended by S0183 `InPlane1-120`, whose redundant index is inconsistent? | Original sample orientation record; corrected label approved by experiment owner | Historical warning ([notebook](../RSM_main.ipynb:65)); do not infer correction |
| Q06 | A | What creates S0154's signed billion-scale intensity values? | Raw instrument files, overflow/sentinel rules, detector status and export conversion history | [Baseline extrema](./06_existing_behavior.md); no local filtering |
| Q07 | A | Which angular offsets/calibrations should apply, with what sign? | Calibration standard scans, motor zeroes, alignment procedure, meaning of omoff | Stored offset unused ([parser](../Modules/data_procesing.py:64)) |
| Q08 | A | What wavelength spectrum was used? | Source/anode, monochromator/analyzer, Kα1/Kα2 selection, energy uncertainty | One scalar 8047.8 ([notebook](../RSM_main.ipynb:47)) |
| Q09 | A | Are intensity values counts, counts/s, corrected counts, interpolated values or another detector quantity? | Exposure/monitor metadata and upstream corrections with units | Fractional values, dwell defaults 1 ([parser](../Modules/data_procesing.py:65)) |
| Q10 | B | Which phases and orientation relationships are physically present? Is hex-Ge film, substrate or reference? | Specimen stack, phase characterization and epitaxial orientation matrix | Fixed CdS/Ge labels and substrate comments ([plotting](../Modules/plotting.py:106)) |
| Q11 | B | What sources, temperatures and uncertainties support each CIF metric and site list? | DOI/database entry/version; distinguish measured and computed structures; explain metric/volume discrepancies | Pymatgen comments, ambiguous hex-Ge block, alternate ZnS files, inconsistent CdS/Ge volume fields |
| Q12 | B | Is 0.35 alloy fraction Zn or Cd, and is linear lattice interpolation justified? | Composition measurement and historical xrayutilities Alloy semantics | [Alloy call](../Modules/geometry.py:17) only |
| Q13 | B | What constitutes the desired line curve: mean count rate, integrated intensity, rocking curve at fixed 2theta, or a reciprocal-space cut? | Scientific objective plus units and weighting definition | Mean within angle strip ([line_scan](../Modules/line_scan.py:41)) |
| Q14 | B | Which phase/peak should center the cut for every reflection? | Expected peak identity, overlap rules, search bounds and allowed missing-peak outcome | Only two branches ([plotting](../Modules/plotting.py:110)) |
| Q15 | B | What is the monochromator streak, and how is it distinguishable from sharp real features? | Example raw map, detector/background controls and validated mask model | Adjacent jump rule ([fitting](../Modules/fitting.py:63)) |
| Q16 | B | What is the physical interpretation of the fitted FWHM? | Instrument resolution, relevant broadening model, fit range/background/overlap decisions | Empirical omega pseudo-Voigt only ([fitting](../Modules/fitting.py:127)) |
| Q17 | B | What noise/uncertainty model supports fit intervals and temperature error bars? | Repeat scans, counting statistics after corrections, temperature calibration | Covariance×1.96 and xerr=1 hardcoded |
| Q18 | B | Should theory show projected off-plane reflections or only experimentally accessible peaks? | Plane tolerance, angular acceptance and all required motor coordinates | Qx and inverse angles discarded; ttmax=900 |
| Q19 | B | Which reference workbook rows are authoritative? | Energy/orientation provenance, explanation of zero/missing 2theta and 0002 row | [Workbook audit](./06_existing_behavior.md) |
| Q20 | C | Which Python/xrayutilities/NumPy versions produced accepted historical results? | Environment export, package lock and an original successful run with inputs | Notebook says Python 3.11.4; no dependency versions |
| Q21 | C | Are historical caches or absent modules scientifically important? | Recover source history and original output figures, if available | Cache names only; no reconstruction from bytecode attempted |
| Q22 | C | What output artifacts and interaction modes are required? | Required numeric tables, image formats, metadata, batch/headless needs | In-memory figures/dicts only |
| Q23 | C | What legacy behavior must be reproducible even if physically questionable? | Explicit compatibility versus validated-mode policy; approve frozen baseline cases | Existing default fails, so screenshot mimicry is not a sufficient target |
| Q24 | C | What future measurement families must be covered? | Prioritized coplanar/noncoplanar, point/line/area detector, material and file-format examples | Current source assumes two angle columns and fixed materials |

## Minimal validation evidence package

Request at review: one complete instrument/export description; one certified symmetric and one asymmetric reference scan with motor metadata; representative clean measurements of each scan type; exposure/intensity provenance; specimen orientation/phase records; reference-structure citations; a historical working environment and accepted outputs if available. These would settle more than additional internal round-trip tests.

No existing file should be relabeled or corrected until its provenance is established. Anomalous inputs remain useful preservation fixtures, but cannot be treated as validated physical standards.
