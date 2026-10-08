# Numerical output contract

`export_data(measurement_or_rsm, "name.npz")` writes:

- `name.npz`: NumPy compressed arrays, readable with `numpy.load(..., allow_pickle=False)`.
- `name.json`: schema `rsm-toolkit-1`, source path/SHA-256/format/reader, units, original shape, motor-key mapping, metadata and warnings. For RSM results it also contains geometry configuration, frame, wavelength, provisional status and reconstruction warnings.

Arrays:

| Key | Meaning |
|---|---|
| intensity | Original recorded values, original shape; no normalization/clipping/interpolation |
| motor_N | Full same-shaped motor coordinates; names and units are in JSON `motor_keys`/`motor_units` |
| counting_time_s | Same-shaped counting time when available; importer does not divide intensity by it |
| q | RSM only: `intensity.shape + (3,)`, Cartesian Q in Å⁻¹, including 2π |

For supplied files the intensity shape is `(1401,477)`: scan step first, rebinned detector channel second. `Theta` varies by row; `TwoThetaArm` is the detector motor; `TwoTheta` varies across both row and channel. Fixed drives are broadcast without loss. BRML's original per-step Datum table and XML descriptors remain in metadata. RAW unknown metadata blocks retain source byte offsets; the original file/hash is needed for future interpretation.

`load_export` checks schema and dimensions and restores either Measurement or RSM without using pickle. Numerical arrays are exact round-trip copies; outputs are derived artifacts, not replacements for original instrument files. Keep NPZ and JSON together. A JSON metadata field may deliberately be null (e.g. unknown sample orientation); that is not zero.

`Grid` is a separate result: edges, bin mean or sum, and sample occupancy. Empty cells are NaN, not zero counts. Plot limits, color normalization and log masks never alter the NPZ values. The supplied example additionally records plot settings, per-file summaries, cross-format comparison errors and the brightest measured bin in `experimental_results.json`.
