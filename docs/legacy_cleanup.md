# Legacy cleanup record

The active implementation is exclusively [src/rsm_toolkit](../src/rsm_toolkit). Before removal, the following sources were stored byte-for-byte in [legacy_source.zip](legacy_source.zip); [legacy_manifest.json](legacy_manifest.json) records SHA-256 for each entry. Notebook cell sources and saved textual output were extracted to [legacy_notebook_content.md](legacy_notebook_content.md). Complete notebook images, errors and metadata remain in the archive. [archive_legacy.py](archive_legacy.py) documents the non-destructive archive procedure and refuses to overwrite the archive.

## Removed from the active tree

| Former path | Scientific information and disposition |
|---|---|
| `Modules/geometry.py` | CIF metrics, HXRD conventions, hardcoded 0.35 alloy; replaced by general lattice/orientation and explicit optional Vegard model. Original assumptions retained in archive and Phase 1. |
| `Modules/theory.py` | Fixed-orientation reciprocal-plane display and CdS/Ge angle predictions. Individual reflection positions now configured generally. Full automatic reciprocal-plane enumeration remains an archived exploratory feature, not silently claimed as implemented. |
| `Modules/data_procesing.py` | Filename parsing, DAT import, hidden normalization; superseded by explicit readers/settings. |
| `Modules/data_analysis.py` | Filename grouping and selected-reflection peak routines; known scientific limitations retained in Phase 1. |
| `Modules/line_scan.py` | Band averaging; replaced by explicit angular_profile. |
| `Modules/fitting.py` | Pseudo-Voigt and point-removal conventions; archived, not equated to current Gaussian fit. No unique model information discarded. |
| `Modules/plotting.py` | Hardcoded CdS/Ge annotations, grouping, fixed cuts; general plotting and configured overlays replace active use. |
| `Modules/Colorsheme.py` | Historical colormap definitions retained in archive. |
| `RSM_main.ipynb`, `Theoretical_RSM_main.ipynb` | Full cell sources, saved failures and reference angle calculations retained in archive and extracted text. |
| Root `__pycache__` | Four Python 3.11 bytecode files archived, including `functions` whose source is absent, rather than discarding potentially unique historical information. |
| `Modules/__pycache__`, `build/` | Generated copies of archived source / previous package build, removed. |

All experimental files (including new_data and historical folders), CIFs, the reflection workbook, validation outputs, and Phase 1 analysis remain unchanged. Their existing preservation hashes still apply. Phase 1 links to removed sources now refer to paths inside the archive; extract it into a separate directory to recover identical source line references. The old audit script remains historical evidence, not a test of the new package.

## Dependencies

Core requirements remain NumPy, SciPy and Matplotlib. pandas and notebook tooling are not runtime dependencies of the package. No environment-wide uninstall was performed. xrayutilities remains an optional independent validation extra; lmfit, h5py and related pins are transitive dependencies of that reference environment, not dependencies introduced by the retired modules. Removing them from the tested reference lock would make that environment incomplete.

## Science retained and corrected

The original alloy used 0.35 without specimen evidence; no such default exists in the new workflow. The original in-plane vector passed through the reciprocal basis; the replacement distinguishes direct lattice directions from reciprocal-plane normals. Historical CdS/ZnS lengths are explicitly attributed in the example documentation. Crystal metrics determine reciprocal node positions; names alone do not establish extinction rules. The old reciprocal-plane display and empirical fitting choices remain inspectable but are not silently adopted as validated analysis.
