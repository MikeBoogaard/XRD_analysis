# RSM Toolkit

Create X-ray reciprocal-space maps from Bruker RAW and BRML measurements, with theoretical substrate and film reflection positions. Use the desktop window or the Python and command-line interfaces. Measurements stay unchanged; plots and numerical results are saved separately.

## Quick start

Double-click **[Start RSM GUI.cmd](<Start RSM GUI.cmd>)** in this folder. If you have not installed the toolkit yet, follow **First-time setup** below.

1. Choose a measurement with **Browse…** on the **File** tab.
2. Enter your sample information, or select a **Preset**.
3. Press **Plot and save**.

Your map appears on the right. **Open saved output folder** takes you to the picture and numerical data.

## Tutorial: create a map

### 1. Choose a file

On **1. File**, choose a `.raw` or `.brml` file, an output folder and a map name. The filename does not need to contain material or orientation information.

Choose **points** to show detector bins, or **grid** to show bin means. **log** displays a wide intensity range; **linear** uses a linear scale. The color-range field sets the number of decades shown in log mode.

To plot intensity only, leave **Show theoretical substrate / film markers** off. Material and orientation fields are only needed for theoretical markers.

### 2. Enter materials and orientations

Enable theoretical markers and open **2. Sample**:

| Field | Meaning |
|---|---|
| Substrate / film model | Select a bundled material or **Custom cell**. Select **None** for no film. |
| Zn (%) | For **CdZnS Vegard**, enter `35` for 35% Zn, not `0.35`. |
| Norm | Substrate surface plane, e.g. `11-20`. |
| RSM | Reflection being measured, e.g. `12-30`. This does not change the surface plane. |
| InPlane | A **direct crystal direction** lying in the surface plane, e.g. `1-100` or `0001` for a (11-20) hexagonal surface. |
| Film aligned | Check when film crystal axes align with substrate crystal axes. Otherwise fill the film's Norm and InPlane. |
| Film RSM | Leave blank to use the substrate reflection indices, or enter the film reflection separately. |

Use `1 1 -2 0` or compact `11-20` for four-index hexagonal notation. Use spaces for three-index notation, such as `0 0 1`, and for multi-digit indices. Three-index notation is required for cubic materials. InPlane is always a direct direction and must lie within the surface plane; inconsistent indices produce a clear error.

**Available materials:** CdS, CdZnS (Vegard), Ge (cubic), Ge (hexagonal), ZnS (wurtzite), ZnS (wurtzite, mp-560588), and Custom cell.

The material library reads cell lengths and angles from bundled CIF files. Ge phases and ZnS reference datasets are listed separately so you can choose the intended structure. CdZnS uses your Zn fraction with a relaxed linear alloy model based on the CdS and ZnS reference cells.

For **Custom cell**, enter `a b c alpha beta gamma`: lengths in angstrom and angles in degrees. For a hexagonal cell, use `a a c 90 90 120`, replacing a and c with your values. Custom fields are ignored when a library material is selected.

### 3. Check the geometry

The desktop interface uses coplanar omega/2theta geometry. On **3. Advanced**:

- Choose whether map **+Qy** points **Along InPlane** or **Opposite InPlane**. This sets the azimuth sense of the theoretical crystal frame.
- Leave extra angle offsets at **0** unless you intend to apply an additional correction. The program does not move peaks onto theoretical markers automatically.
- Leave wavelength blank to read it from the measurement.

For general 3D rotation sequences, use the JSON configuration and command-line interface.

### 4. Plot and save

Press **Plot and save**. The window stays responsive while the map is calculated. Cyan circles mark substrate reflections; magenta diamonds mark film reflections.

Every run creates a new dated output folder, so previous results are not overwritten:

| File | Contents |
|---|---|
| `map.png` | Plot; open normally or insert in a report. |
| `map.npz` | Numerical intensity, angle and Q arrays. |
| `map.json` | Measurement metadata, settings and theoretical Q positions. |
| `settings.json` | Reusable desktop form. |
| `run.json` | Equivalent command-line configuration. |
| `warnings.txt` | Processing messages, including zeros masked by log display. |

Use **Load settings** to open a saved `settings.json`, choose the next measurement and update its fields. **Save settings** also saves an unfinished form. A failed calculation reports its error; if a run folder was already created, it contains `FAILED.txt`.

## Presets

The **File** tab includes two CdZnS-on-CdS presets:

| Preset | Norm | RSM | Direct InPlane | Map +Qy |
|---|---|---|---|---|
| Symmetric (11-20), 35% Zn | 11-20 | 11-20 | 0001 | Along InPlane |
| Asymmetric (12-30), 35% Zn | 11-20 | 12-30 | 1-100 | Opposite InPlane |

Both use aligned film/substrate crystal axes and zero additional angle offsets. Selecting a preset fills the form and selects its supplied measurement when available. You can then choose a different file and change any setting.

## First-time setup

On Windows:

1. Install Python with **pip** and **Tcl/Tk** support. Python 3.12 is tested here. Enable **Add Python to PATH** during installation.
2. Open this repository folder in File Explorer, right-click empty space, and choose **Open in Terminal**. In VS Code, **Terminal → New Terminal** also works.
3. Run these commands, one at a time (internet access is needed to install dependencies):

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -e .
```

4. Double-click **Start RSM GUI.cmd**. A terminal window may remain behind the application; this is normal.

You only need setup once. The toolkit runs locally and does not upload measurements. If Python is not recognized, check the installation and reopen the terminal. If Tkinter is missing, install Python's Tcl/Tk component. On Linux, Tk may be a separate operating-system package; use `.venv/bin/python` instead of `.venv/Scripts/python`. The GUI requires a graphical display.

## Command-line and Python use

Launch the desktop window:

```powershell
.venv/Scripts/python -m rsm_toolkit gui
```

Inspect a measurement or plot with the `run.json` saved by the GUI:

```powershell
.venv/Scripts/python -m rsm_toolkit inspect "example_data/my_scan.raw"
.venv/Scripts/python -m rsm_toolkit map "example_data/my_scan.raw" --config "path/to/run.json" --output "outputs/my_map.png"
```

Replace the paths with your files. The map command also saves NPZ and JSON. Use `--mode grid` or `--scale linear` to override display settings. PNG, PDF and SVG output are supported.

```python
from rsm_toolkit import (
    load_xrd, load_configuration, calculate_rsm,
    plot_configured_rsm, save_figure,
)

measurement = load_xrd("example_data/my_scan.raw")
config = load_configuration("path/to/run.json")
rsm = calculate_rsm(measurement, config)
figure, axes, theory = plot_configured_rsm(rsm, config)
save_figure(figure, "outputs/my_map.png")
```

## Data and calculation conventions

Supported inputs include Bruker RAW4.00 PSD Fix Scan and the tested DIFFRAC 8.6.2.0 Eiger BRML profile. Unsupported formats report an error. Q is expressed in inverse angstrom with the 2π convention. Theory and measurement must share a coordinate frame; missing orientations and off-plane reflections are checked.

Theoretical markers are reciprocal-lattice positions. Their intensity and selection rules require additional structure-factor information. Log display masks nonpositive values without modifying data; grid display uses bin means without interpolation. Recorded Chi/Phi values are retained in metadata; the coplanar model uses omega and 2theta.

## Development

```powershell
.venv/Scripts/python -m pip install -e ".[test,reference]"
.venv/Scripts/python -m pytest
```

Python 3.10+; dependencies are NumPy, SciPy, Matplotlib and Pillow. Tkinter supplies the desktop interface. xrayutilities is an optional independent validation dependency. [requirements-tested.txt](requirements-tested.txt) records tested versions.

- [src/rsm_toolkit](src/rsm_toolkit): readers, calculations, plotting and GUI.
- [examples](examples): configurations and scripts.
- [tests](tests): numerical, file-format and GUI tests.
- [example_data](example_data): all bundled example measurements, including the CdZnS scans, S0154, S0183 and supplementary XRD data. GUI presets select files here.
- [CIF reference files](<Literature data for analysis/CIF>): crystallographic data.
- [outputs](outputs): figures and numerical results.
