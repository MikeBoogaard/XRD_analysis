# RSM Toolkit

Create X-ray reciprocal-space maps from Bruker RAW and BRML measurements, with theoretical substrate and film reflection positions. Use the desktop window or the Python and command-line interfaces. Measurements stay unchanged; plots and numerical results are saved separately.

## Quick start

Double-click **[Start RSM GUI.cmd](<Start RSM GUI.cmd>)** in this folder. If you have not installed the toolkit yet, follow **First-time setup** below.

1. Choose a measurement with **Browse…** on the **File** tab.
2. Enter your sample information, or select a **Preset**.
3. Press **Plot**.

Your map appears on the right. Click **Save results** to keep it. **Open saved output folder** takes you to the picture and numerical data.

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

Press **Plot**. The window stays responsive while the map is calculated. Cyan circles mark substrate reflections; magenta diamonds mark film reflections.

Adjust settings and press **Plot** as often as needed. Previews use temporary files and do not create runs in your output folder. Click **Save results** when satisfied: it saves the completed preview (including any FWHM results) into the current **Save in folder** location. Edits made after plotting do not change that preview; plot again to apply them. Unsaved previews are discarded when replaced or when the application closes.

Each **Save results** creates a new dated output folder, so previous results are not overwritten:

| File | Contents |
|---|---|
| `map.png` | Plot; open normally or insert in a report. |
| `map.npz` | Numerical intensity, angle and Q arrays. |
| `map.json` | Measurement metadata, settings and theoretical Q positions. |
| `settings.json` | Reusable desktop form. |
| `run.json` | Equivalent command-line configuration. |
| `warnings.txt` | Processing messages, including zeros masked by log display. |

Use **Load settings** to open a saved `settings.json`, choose the next measurement and update its fields. **Save settings** also saves an unfinished form. A failed preview reports its error and retains the previous successful preview.

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

## Film peak FWHM in the GUI

1. Select your measurement and usual map settings.
2. Open **4. Film FWHM** and enable **Fit film-region rocking-curve FWHM**.
3. Either click **Fill from theoretical film reflection**, or enter the film peak **2theta center**, the **band half width** (0.2 means center ?0.2 degrees), and the minimum/maximum **omega** for the fit. Use the measured film region from your scan; exclude the substrate peak and include both sides of the film peak. All angles are in degrees **after** applying the offsets on the Advanced tab.
4. Click **Plot**. The map shows a cyan outline of the selected band and omega range. Use the preview dropdown to switch from **Map** to **Film FWHM**.

The application averages recorded intensity over the selected 2theta band at each omega, then fits one pseudo-Voigt peak plus a constant background. The FWHM line marks half the fitted peak height above background. The lower panel shows residuals; inspect these and try nearby band widths/ranges to assess fit sensitivity. This is an empirical rocking-curve width in degrees, not a direct measurement of crystallite size, strain or mosaicity. It does not separate overlapping film/substrate peaks or remove instrumental broadening.

Click **Save results** to keep **fwhm.png**, **fwhm.csv** (profile, fit, residual and sample count), and **fwhm.json** (selection, source, geometry, parameters and approximate covariance) alongside the map. The settings file retains the selection. No log transform or automatic spike removal is applied to fit data. If fitting fails, the map preview remains available to save, a message explains the problem, and **FWHM_FAILED.txt** records it. Older settings files load with FWHM disabled.

### Fill FWHM angles from theory

Fill in the film material (including Zn percentage for CdZnS), Norm, InPlane, reflection and axis sense first. On **Film FWHM**, choose a **Suggested omega half width** and click **Fill from theoretical film reflection**. The button fills 2theta and the minimum/maximum omega. The default suggested range is theoretical omega ?2 degrees; it is a starting window, not a predicted peak width. The 2theta band half-width is retained.

Wavelength comes from Advanced if entered, otherwise from the selected measurement. The calculation uses the same film orientation and lattice model as the theoretical markers, even when markers are switched off. These are corrected physical angles, so extra instrument offsets are not added a second time. Off-plane or inaccessible reflections are rejected.

All fields remain manually editable. Reclick the button after changing materials, composition, reflection or orientation. Review the measured selection: the suggestion is not clipped to scan coverage, does not automatically exclude substrate intensity, and a strained or misaligned film can differ from its theoretical position.

### Find the measured film maximum near theory

As a third option alongside manual entry and theoretical fill, click **Find measured peak near theory** on **Film FWHM**. Select the measurement and fill in materials, composition and orientations first.

- **Search 2theta half width** (default 0.5 degrees) and **Search omega half width** (default 1 degree) define a rectangular angular region around the theoretical film position.
- The button finds the brightest finite positive recorded bin in that region, fills its 2theta center, and places the omega fit range around its measured omega using **Suggested omega half width**. The extraction band half-width stays unchanged.
- A message reports measured angles and shifts from theory, and flags a maximum near the search boundary. All angles include Advanced offsets, consistent with FWHM selection. No smoothing, log transform or intensity normalization is used for the search.

Keep the substrate outside the search box. This is a measured-bin maximum, not a fitted peak center or automatic film identification; a hot pixel or overlapping substrate can be selected. Review the resulting map selection, adjust search widths or edit the values manually. The search never falls back to a global maximum when the region is empty. Search widths and the resulting FWHM fields are saved with GUI settings. Re-run the search after changing the data, material, orientation or offsets.
