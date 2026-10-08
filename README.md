# RSM Toolkit

A Python package for provenance-preserving XRD maps. It reads the supplied Bruker **RAW4.00 PSD Fix Scan** and **BRML DIFFRAC 8.6.2.0 Eiger2R_250K** measurements directly. No scientific parameters are parsed from filenames. Raw values remain unchanged; material models are optional and separate from instrument kinematics.

## Install and run

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[test]"
.venv/Scripts/python -m pytest
.venv/Scripts/python examples/cdzns_on_cds_rsm.py
```

On POSIX use `.venv/bin/python`. Python 3.10+ is supported. Core dependencies: NumPy, SciPy, Matplotlib. See `requirements-tested.txt` for the tested dependency versions. The optional `[reference]` extra enables comparison against xrayutilities.

To reproduce the tested dependency set, install `-r requirements-tested.txt` in a fresh environment, then install `-e . --no-deps --no-build-isolation`. The recorded environment is Windows/Python 3.12.3; other platforms have not been experimentally checked. For continuation status and the remaining calibration work, read [PROGRESS.md](PROGRESS.md).

The example processes **both actual paired measurements** in [new_data](new_data), checks BRML against RAW, and writes plots, full numerical arrays and metadata to [outputs](outputs). It deliberately produces **provisional nominal-coplanar maps**: the wavelength and angle tables are recorded, but sample mounting, surface orientation and Chi/Phi calibration have not been established. No composition, lattice constants or reflection indices are invented. Original data and [Phase 1 analysis](analysis_docs) are preserved; legacy notebooks/modules are not part of the installed package.

## Python API

For one editable run file, use [examples/cdzns_on_cds.json](examples/cdzns_on_cds.json) and the [configuration guide](docs/run_configuration.md). It includes both phases, lattice/composition, orientations, reflection lists, frame alignment, instrument and plot settings. Unknown specimen values are null. Theoretical markers are disabled until those values are supplied; no Zn concentration or mounting is guessed.

```powershell
.venv/Scripts/python -m rsm_toolkit map "new_data/22-40_RSM_S0159.raw" --config "examples/cdzns_on_cds.json" --output "outputs/cdzns_configured.png"
```

Enable `plot.theoretical_overlays` after completing the metadata. The command saves distinguishable substrate/film markers and their numerical predictions in the JSON sidecar. Missing alignment or off-plane reflections produce an explicit error. Geometry-only configuration files remain supported.

```python
from rsm_toolkit import (
    Material, Sample, RSMConfiguration, CoplanarGeometry,
    load_xrd, calculate_rsm, plot_rsm, save_figure, export_data,
)

sample = Sample(substrate=Material("CdS"), film=Material("CdZnS"))
measurement = load_xrd("new_data/22-40_RSM_S0159.brml")
config = RSMConfiguration(
    sample=sample,
    geometry=CoplanarGeometry(frame="nominal coplanar"),
    allow_provisional=True,  # explicit; not experimental calibration
)
rsm = calculate_rsm(measurement, config)
fig, ax = plot_rsm(rsm, intensity_scale="log", mode="points")
save_figure(fig, "outputs/my_map.png")
export_data(rsm, "outputs/my_map.npz")
```

Do not set `calibration_verified=True` solely because a plot looks plausible. Supply a calibration reference and correct motor conventions. For calibrated noncoplanar geometry use `VectorGeometry` with explicit Cartesian axes, rotations and zero beam directions. Geometry defaults are never chosen from a filename or material.

## Command line

```powershell
rsm-toolkit inspect new_data/22-40_RSM_S0159.brml new_data/22-40_RSM_S0159.raw
rsm-toolkit map new_data/22-40_RSM_S0159.brml --config examples/coplanar_provisional.json --output outputs/cli_map.png
```

The second command also writes NPZ + JSON. `--mode grid` performs a documented bin mean with coverage; `--scale linear` includes nonpositive intensities. Log plots mask nonpositive values and report how many; they do not clip or rewrite the data. PNG/PDF/SVG are supported. [calibrated_required.json](examples/calibrated_required.json) is intentionally incomplete and fails until geometry is supplied.

## Capabilities and boundaries

- Full Q vectors from declared coplanar or explicit vector-rotation geometry, angstrom inverse with 2π convention.
- General lattice metrics, distinct plane/direction Miller–Bravais conversion, explicit right-handed crystal orientations, separate film/substrate objects.
- Geometric reflection overlays with frame/off-plane checks; optional full-cell structure-factor sums require atomic sites and scattering factors. A cell metric or the word “wurtzite” does **not** establish extinction rules.
- Point plots and histogram mean/sum reductions; empty bins remain missing. No hidden smoothing, Jacobian correction, count normalization or absorber multiplication.
- Separate count-rate calculation, angle-band profiles, brightest measured bin reporting and empirical Gaussian-plus-background fits. No automatic strain, mosaicity or size claims.
- Strict errors for unsupported binary/schema variants, missing geometry, missing wavelength and one-dimensional scans passed to the 2D mapper.

Read [coordinate conventions](docs/coordinates.md), [format support](docs/file_formats.md), [experimental results and limitations](docs/experimental_report.md), and [numerical export format](docs/data_format.md). The tests distinguish mathematical correctness and cross-format consistency from experimental calibration.

## Repository layout

- [src/rsm_toolkit](src/rsm_toolkit): active readers, geometry, crystals, overlays, plotting and CLI.
- [examples](examples), [tests](tests), [docs](docs): configurations, validation and usage.
- [new_data](new_data), historical data directories and [reference files](<Literature data for analysis>): preserved inputs.
- [analysis_docs](analysis_docs): unchanged Phase 1 scientific analysis.
- [outputs](outputs): generated figures, arrays and reports.

Retired notebooks/modules were removed from the active tree after byte-verified archiving. See [cleanup record](docs/legacy_cleanup.md), [notebook scientific content](docs/legacy_notebook_content.md) and [complete original source archive](docs/legacy_source.zip). Phase 1 source paths and line numbers refer to the matching archive entries; unpack into a separate directory to inspect them. Do not rerun the historical audit against the rebuilt tree to overwrite its evidence.
