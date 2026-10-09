# Supported formats and evidence

## Supplied inventory

| Source | Actual signature/schema | Acquisition | RSM suitability |
|---|---|---|---|
| `example_data/22-40_RSM_S0159.brml` | ZIP; DIFFRAC 8.6.2.0 BRML; external Eiger memory profile | UltraFastRSM / OmegaTwoThetaScan / Coplanar | 1401×477 angular bins, sufficient for provisional nominal coplanar reconstruction |
| `example_data/22-40_RSM_S0159.raw` | RAW4.00; 1401 PSD Fix Scan ranges | Paired export of the above | Same coordinates and counts to export precision |
| `example_data/2200_RSM_S0155.brml` | Same BRML schema | Same scan mode and angular ranges, different fixed Chi/Phi and intensities | Same provisional capability |
| `example_data/2200_RSM_S0155.raw` | Same RAW4.00 scan variant | Paired export | Same provisional capability |

The names do not establish reflection indices or identify any legacy specimen group. In fact both files have the same omega/detector ranges despite different reflection-looking names. The sample context CdZnS-on-CdS comes from the user's instruction. No film composition, lattice metric or surface orientation is assumed.

## BRML

The manifest `Experiment0/DataContainer.xml` lists `Experiment0/RawData0.xml`; the reader follows these references. Explicit `scan_index` and `route_index` select one route; multiple routes are not silently averaged. Supplied scans each have one original Measured route and use:

- `ScanInformation/MeasurementPoints`: 1401.
- `ScanAxes`: Theta, displayed Omega, 17.5–24.5° in 0.005° steps; TwoTheta 95–109° in 0.01° steps. Fixed coupling factor 2 and offset 60° agree with the recorded motor arrays.
- `DataViews`: FixedRawDataView MeasuredTime (0.5 s), AbsorptionFactor (1), named ScanAxes fields, and three recorded auxiliary temperature/process channels. Every original Datum value remains in export metadata.
- `ScaleAxes/ScaleAxisInfoRegular` with AxisId TwoTheta_Relative: −3.3849452703970435 through +3.3812767336633618° at 0.0142147521093706° per bin, 477 bins. This is added to the detector-arm position, not to omega.
- `ExtMemoryRecordedRawDataView`: 477 counts per row, Eiger2R_250K, Size X=477 Y=1, linked through `ScanDataExternalLink` to the archive's MemoryMappedFiles member. The XML Datum rows do **not** contain these count profiles; interpreting their final scalar as intensity would be wrong.
- MethodAlignment/WaveLength: 1.5406 Å, independent of tube alternatives.
- FixedInformation: motors, detector and geometry settings; copied as structured metadata, not discarded.

**External payload evidence:** each linked member has exactly 1401×477×8=5,346,216 bytes, no header/trailer. The codec profile reads little-endian float64 in scan-major/channel-minor order. This layout is empirically established by all 668,277 intensities matching the independently decoded RAW export after float32 rounding for **each** pair. It is not claimed to be a manufacturer-published universal BRML binary specification. Consequently it is accepted only for the observed version, Eiger detector, external-view type, dimensions and link contract. Unknown external profiles fail. This is an explicitly documented and cross-validated supported profile, not arbitrary binary offset/dtype probing.

For inline original-count routes, named DataViews determine the count and motor fields; no fixed column number is assumed. Scalar and calibrated regular line-detector profiles are supported when required axes exist. Arbitrary area images, unfamiliar relative-axis types, different external encodings and absent coordinate descriptors are rejected explicitly. The supplied detector's calibration distance 301.9516065 mm and 0.075 mm pixel dimension are retained as metadata; they are not used to recalibrate an already rebinned angular scale.

ZIP members are read in memory, never extracted to source paths. Duplicate members, XML entities/DTDs, missing references, inconsistent dimensions/endpoints and malformed data raise explicit errors.

## RAW4.00

The reader uses public segment-relative field definitions from [xylib's RAW reader](https://github.com/wojdyr/xylib/blob/master/xylib/bruker_raw.cpp) and cross-checks with [GSAS-II's RAW reader](https://gsas-ii.readthedocs.io/en/latest/_modules/GSASII/imports/G2pwd_BrukerRAW.html), inspected 2026-10-08. No source-specific absolute data offset is used.

| Structure | Documented fields used |
|---|---|
| Preamble | 61 bytes; RAW4.00 signature; date and time |
| Metadata segment | uint32 type and byte length; advance by declared length |
| VarInfo type 10 | Name at +12, 24 bytes; text at +36 |
| Hardware type 30 | Wavelength doubles at +72 to +104; anode at +116 |
| Alignment type 60 | Name +12; flag +8; delta +68; retained, not applied |
| Range marker 0/160 | 160-byte fixed header; scan name +32; angle start +72, step +80, point count +88, dwell +92, used wavelength +112, record size +136, extra-header size +140 |
| Range DriveInfo type 50 | Name +12, position double +56 |
| Data | After 160 bytes plus declared extra-header length; declared point count × record size |

For the supplied PSD Fix Scan ranges, record size is four-byte float32. Range start/step describe absolute bin 2theta, while Theta and 2Theta DriveInfo describe fixed motor positions for that detector profile. Each range becomes one row. Independent BRML descriptors verify this interpretation, including the time unit seconds. The reader validates every segment boundary and the full chain to EOF, retains unknown segment type/offset/length, and does not decode undocumented HRXRD segment fields. It rejects ragged ranges, changing wavelengths, unfamiliar scan types, or other datum widths. RAW1.01/RAW2/older/newer variants are recognized as unsupported rather than treated as RAW4.

**Library evaluation:** the inspected xylib RAW4 implementation only handles Locked Coupled/Unlocked Coupled data and skips unknown scan types; GSAS-II likewise excludes PSD Fix Scan and its powder import clips low values. Neither is an appropriate unchanged backend for these RSM stacks. xrayutilities' documented I/O catalog does not supply a matching RAW4/Eiger memory reader; it remains useful for independent geometry checks. A narrow reader using the public range layout, with full paired-export tests and no intensity clipping, was therefore implemented. The failed restricted package-index lookup for xylib is not evidence about format support; that decision is based on the public reader source.

## Text and intermediate data

`load_dat` accepts a whitespace numeric table with explicit column names, angle units, optional wavelength/time, and no filename metadata. Decimal commas are converted to numeric decimal points before parsing; this is not a comma-separated CSV parser. Headers other than NumPy comment lines and ragged tables are rejected. Default columns are explicitly documented as Theta, TwoTheta, intensity; override them when using another schema.

NPZ + JSON round-tripping is documented in [data_format.md](data_format.md). Source arrays, full motor tables and provenance are retained. Unsupported formats do not trigger a plausible-data fallback.
