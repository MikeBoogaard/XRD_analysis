# Rebuild specification

The new `src/rsm_toolkit` package has no dependency on legacy modules. Those files stay in place to keep Phase 1 source links useful, but are not installed or imported. Raw data and Phase 1 documents are protected by the SHA-256 manifest in `preserved_files.json`.

Layers: immutable measurement arrays and provenance; strict format readers; explicitly selected instrument geometry; independent crystal metrics/orientations; optional numerical reductions; plotting; command-line and executable examples. Scientific context is supplied through objects/configuration, never inferred from filenames. NumPy, SciPy and Matplotlib suffice for the core; xrayutilities is an optional independent geometry check. xarray/pymatgen are not required to reconstruct calibrated angle tables.

Primary acceptance inputs are the four files in `new_data`, two paired exports of 1401×477 UltraFastRSM observations. BRML is DIFFRAC 8.6.2.0 XML with an external memory-mapped count array, not a table of inline counts. RAW is RAW4.00 PSD Fix Scan, not a generic powder RAW. Read the actual format descriptors, bound every binary read, reject unknown variants, and compare all paired values.

Default reconstruction requires an explicit geometry choice. The real-data example selects an explicitly provisional nominal coplanar frame because crystal mounting and Chi/Phi zero conventions remain unverified. Used wavelength comes from the file's method setting, not tube-average guessing. Q is in 2π/Å convention. No assumed film lattice, composition, surface plane or reflection is needed for the measured map. No unverified crystal overlays will be drawn.

Deliverables include direct readers, general cell/orientation mathematics, configurable vector rotations, point plots and optional count-aware gridding, numerical exports, separate profile/fit helpers, a CLI, analytical and paired-export tests, both experimental examples, and a per-file report. Experimental conclusions remain provisional until calibration/orientation are supplied. S0154 is excluded from acceptance tests.
