# Hardcoded assumptions register

Categories: **(a)** general physical requirement; **(b)** instrument/measurement configuration; **(c)** material/sample configuration; **(d)** plotting preference; **(e)** unnecessary restriction; **(f)** potential bug. Multiple categories distinguish a legitimate configurable choice from how it is currently imposed. Search covered all eight source modules, both notebooks, all CIFs, filenames, reference workbook cells and measured-column ranges; caches were inventoried only.

## Physics, materials and instrument

| Assumption | Category | Evidence / assessment |
|---|---|---|
| Elastic monochromatic scattering via HXRD | a,b | [geometry:44](../Modules/geometry.py:44); valid model only within its experimental domain |
| Energy 8047.8, implicitly eV | b | [notebook:47](../RSM_main.ipynb:47); source spectrum and calibration not recorded |
| `lam2en` used to produce wavelength | f | [geometry:43](../Modules/geometry.py:43); dimensional naming problem, numerical reciprocity may preserve correct value |
| Default HXRD and `lo_hi` branch | b,e | [geometry:40](../Modules/geometry.py:40); no motor axes, handedness or detector parameters exposed |
| All files use CdS geometry | c,e,f | [data_procesing:112](../Modules/data_procesing.py:112); material token ignored |
| Fixed CdS, ZnS, hex-Ge and alloy keys | c,e | [geometry:23](../Modules/geometry.py:23), [experiments:48](../Modules/geometry.py:48); all four required even where two suffice |
| CdS a=b=4.136 Å, c=6.716 Å, γ=120°, P6₃mc/186 | c | [CdS.cif:3](<../Literature data for analysis/CIF/CdS.cif:3>); no uncertainty, strain or temperature dependence |
| ZnS a=b=3.80579647 Å, c=6.23798163 Å, γ=120°, P6₃mc/186 | c | [ZnS.cif:3](<../Literature data for analysis/CIF/ZnS.cif:3>) |
| Hex-Ge a=b=3.9855 Å, c=6.5772 Å, γ=120°, P1 | c,f | [Hex_Ge_100_paper.cif:2](<../Literature data for analysis/CIF/Hex_Ge_100_paper.cif:2>); block says GaAs, formula says Ge, four Ge sites; provenance unresolved |
| Alloy fraction 0.35 | c,e | [geometry:26](../Modules/geometry.py:26); component convention and interpolation unverified |
| Cubic Ge path assigned but unused | c,e | [geometry:12](../Modules/geometry.py:12); supplied cubic metric 5.762862 Å, P1 with eight sites ([CIF:3](<../Literature data for analysis/CIF/Ge_mp-32_conventional_standard.cif:3>)) |
| Alternative ZnS unused, different metric | c | [alternative CIF:4](<../Literature data for analysis/CIF/ZnS_WZ_mp-560588_conventional_standard.cif:4>): a=3.84827778, c=6.317452 Å; not equivalent to loaded metric |
| Fixed atomic positions, occupancy=1, ionic labels in CdS/ZnS | c | [CdS sites:44](<../Literature data for analysis/CIF/CdS.cif:44>), [ZnS sites:44](<../Literature data for analysis/CIF/ZnS.cif:44>); library warns S replaces S2− in saved output |
| CdS and hex-Ge declared volumes differ from their metrics | c,f | [CdS volume:13](<../Literature data for analysis/CIF/CdS.cif:13>), [Ge volume:13](<../Literature data for analysis/CIF/Hex_Ge_100_paper.cif:13>); independent determinant check in [equations](./03_physics_and_equations.md) |
| Same reflection indices and orientations for different phases | c,f | [plotting:59](../Modules/plotting.py:59); no verified phase orientation relation |
| Plane-index conversion used for in-plane direction | e,f | [data_procesing:75](../Modules/data_procesing.py:75); reciprocal/direct distinction unresolved |
| Invalid i gives warning, still accepted | e,f | [geometry:76](../Modules/geometry.py:76); actual S0183 warning stored in notebook |
| Predicted Ge peak anchors extraction | c,e,f | [plotting:106](../Modules/plotting.py:106); assumes phase identity and proximity to unstrained reference |
| `20-20` measured maximum search; `12-30` theoretical center | c,e,f | [plotting:110](../Modules/plotting.py:110); only these branches; no fallback |
| Theory overrides normal=(110), in-plane=(001) | c,e,f | [theory:21](../Modules/theory.py:21); ignores provided exp_geometry |
| Theory prints only (300), three fixed phases | c,e | [theory:30](../Modules/theory.py:30), [line 36](../Modules/theory.py:36) |
| `ttmax=900` | b,f | [theory:30](../Modules/theory.py:30); outside physical 0–180° scattering-angle domain; library response unresolved |
| Discard Qx and two inverse-geometry angles | b,e,f | [geometry:67](../Modules/geometry.py:67), [line 72](../Modules/geometry.py:72); silently loses off-plane/accessibility information |

## Input and numerical analysis

| Assumption | Category | Evidence / assessment |
|---|---|---|
| Current working directory is repository root; S0183 selected | b,e | [notebook:48](../RSM_main.ipynb:48) |
| Only `.dat` discovered; whitespace/no header, decimal comma | b,e | [notebook:50](../RSM_main.ipynb:50), [parser:103](../Modules/data_procesing.py:103); point decimals also occur and parse in supplied S0154 |
| Columns fixed to omega, 2theta, intensity | b,e | [parser:108](../Modules/data_procesing.py:108); no schema/units metadata |
| Four signed single digits in index tokens | e,f | [regex:11](../Modules/data_procesing.py:11); general Miller indices need separators/multi-digit support |
| MatCdS prefix used for sample ID | c,e | [data_analysis:11](../Modules/data_analysis.py:11) |
| Dwell defaults to 1; single scalar for all points | b,f | [parser:65](../Modules/data_procesing.py:65); counts versus count rate unknown; no positive-time check |
| `omoff` stored but unused; other offsets zero | b,f | [parser:87](../Modules/data_procesing.py:87), [line 108](../Modules/data_procesing.py:108) |
| `omscan=abs` and possible 90deg token do nothing | b,f | [parser:84](../Modules/data_procesing.py:84); no scan-type handling elsewhere |
| Basename uniquely identifies measurements | e,f | [parser:118](../Modules/data_procesing.py:118); collisions overwrite |
| Cut endpoints nearest sample, upper excluded | b,f | [cut_range:127](../Modules/data_procesing.py:127), [get_cut_data:141](../Modules/data_procesing.py:141); can produce empty windows |
| Peak cuts: 500 points, ±0.1 search, 0.1/0.01 integration ranges, two refinement passes | b,c,e,f | [find_fixed_position:152](../Modules/data_procesing.py:152); fixed numerical values, units follow passed coordinates; fine qy uses wrong axis's slice |
| Threshold centroid rounds 2theta to 4 decimals and keeps ≥30% max | b,c,e | [data_analysis:35](../Modules/data_analysis.py:35), [line 47](../Modules/data_analysis.py:47); inactive, index centroid assumes spacing |
| Omega strip half-width 0.2° in notebook | b,c | [notebook:101](../RSM_main.ipynb:101); configurable but no resolution rationale |
| Exact float equality groups omega; unweighted arithmetic mean | b,f | [line_scan:47](../Modules/line_scan.py:47); sensible for repeated nominal setpoints, fragile with jitter |
| No background correction | b,c,f | [line_scan:28](../Modules/line_scan.py:28); tails of ten points are read but subtraction disabled |
| Adjacent jump rejection default 2, actual fit threshold 0.5 | b,c,e,f | [remove_spikes:10](../Modules/fitting.py:10), [fit:63](../Modules/fitting.py:63); no detector-artifact model; scale dependent |
| Second-highest point, despite variable name index_10th | e,f | [fit:65](../Modules/fitting.py:65) |
| Fit window ±2°, initial width 0.1°, initial A=1 and η=0.5 | b,c,e | [fit:71](../Modules/fitting.py:71), [line 77](../Modules/fitting.py:77); may truncate broad peaks |
| Only exact fittype `pseudo voigt` | e,f | [fit:76](../Modules/fitting.py:76); other strings leave variables undefined |
| One peak, no baseline, unweighted residuals | c,e,f | [fit:78](../Modules/fitting.py:78), [model:127](../Modules/fitting.py:127) |
| Gaussian 1.96 covariance interval | a,f | [fit:92](../Modules/fitting.py:92); standard approximation with unmet/unchecked assumptions |

## Presentation choices that can affect interpretation

| Assumption | Category | Evidence / assessment |
|---|---|---|
| Grid 500×300, no accumulation | d,b | [plotting:43](../Modules/plotting.py:43); sampling/resolution sensitivity unchecked |
| Normalize each map by global grid max | d,f | [plotting:70](../Modules/plotting.py:70); not necessarily substrate max; prevents direct absolute intensity comparison |
| Floor 0.1 input units, LogNorm floor 10× higher, 100 levels | d,f | [plotting:70](../Modules/plotting.py:70); low counts/negatives concealed; threshold depends on input scaling |
| Curve divided by already normalized vmax=1 | f | [plotting:140](../Modules/plotting.py:140); contradicts substrate normalization label; affects jump rejection |
| Last file's vmax returned, empty selection undefined | f | [plotting:163](../Modules/plotting.py:163) |
| Reciprocal plot even for `Real` mode | d,f | [plotting:68](../Modules/plotting.py:68), [line_scan:15](../Modules/line_scan.py:15) |
| Four gradient colors, fixed fonts/figure sizes/ticks/annotation offsets | d | [styles:13](../Modules/plotting.py:13), [colors:79](../Modules/plotting.py:79), [annotation:122](../Modules/plotting.py:122); not physics |
| RSM and line figures closed by default; notebook keeps only map open | d | [plotting:38](../Modules/plotting.py:38), [notebook:103](../RSM_main.ipynb:103) |
| Temperature groups only 20-20/0001, 20-20/11-20, 12-30 | c,d,e | [plot_fwhm:171](../Modules/plotting.py:171); other results silently omitted |
| Width >12° omitted; y range 1–11°, temperature 180–300°C | d,e,f | [plot_fwhm:193](../Modules/plotting.py:193), [line 265](../Modules/plotting.py:265); valid results can disappear |
| x-error=1°C, shaded 180–195/285–300 regions labeled No fit | c,d,f | [plot_fwhm:242](../Modules/plotting.py:242), [line 269](../Modules/plotting.py:269); no measured uncertainty/status supports them |
| Legend substitutes 2-200 for 20-20 and 1-100 for missing direction | d,f | [plot_fwhm:254](../Modules/plotting.py:254); can misstate actual indices |
| Tk backend, global warnings suppressed | d,e,f | [notebook:23](../RSM_main.ipynb:23); headless portability and hidden scientific warnings |
| Case mismatch Hex_Ge_100_Paper versus actual lowercase paper | e,f | [geometry:13](../Modules/geometry.py:13); Windows tolerates, case-sensitive systems may fail |
| Colormap preview default n=10, division by n−1 | d,f | [Colorsheme:21](../Modules/Colorsheme.py:21); n=1 divides by zero |

No local code applies polarization, Lorentz, absorption, footprint, solid-angle, dead-time, incident-monitor, refraction, fluorescence, detector-flat-field, resolution or thermal-expansion corrections. This is a statement about absence of those operations from the inspected source, not proof they were absent from upstream data export.
