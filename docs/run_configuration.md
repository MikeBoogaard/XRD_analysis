# One run configuration

Start with [cdzns_on_cds.json](../examples/cdzns_on_cds.json). It contains the instrument, substrate, film, orientation, reflection and plot settings together. Null means unknown; missing specimen metadata is never recovered from a filename. The shipped configuration produces a measured map with overlays disabled. Enabling them while information is missing produces an error before any figure/export is written.

From the repository root:

```powershell
.venv/Scripts/python -m rsm_toolkit map "example_data/22-40_RSM_S0159.raw" --config "examples/cdzns_on_cds.json" --output "outputs/cdzns_configured.png"
```

After supplying the information below and setting `plot.theoretical_overlays` to `true`, **the same command generates the overlay plot**. It automatically saves PNG, NPZ and JSON. The JSON contains full predicted Q vectors, d spacings, resolved lattice parameters, original run settings and provisional status. The current template is not a completed experimental overlay configuration. Reusing an output name overwrites it.

## Material and reflection

Each phase has independent `name`, `crystal_structure`, `lattice`, `composition`, `reference`, `orientation` and `reflections` fields. Structure names are descriptive: they do not automatically select lattice constants, symmetry operations, allowed reflections or form factors. Positions need the lattice metric; predicting intensities or extinctions additionally needs a motif and scattering factors. Optional `sites` supplies a full-cell list for the existing Python structure-factor API, not automatic CIF symmetry expansion.

For a measured hexagonal metric, set `lattice` to `{"system":"hexagonal","a":...,"c":...}` with lengths in angstrom. For other cells use `system: "general"` and `a,b,c,alpha,beta,gamma` (angles in degrees). Composition can remain null when the lattice is known. A CdZnS composition may be recorded as `{"Zn_cation_fraction":0.2}` **only if that value is independently known**; composition metadata alone never selects a lattice.

Alternatively replace the film lattice with null and add `vegard`:

```json
{
  "first": {"system":"hexagonal", "a":4.136, "c":6.716},
  "second": {"system":"hexagonal", "a":3.80579647, "c":6.23798163},
  "fraction_second": null
}
```

These end-member lengths are the original repository CdS/ZnS reference CIF values, not newly validated specimen metrics. Supply the known Zn fraction as `fraction_second`. Linear interpolation is an explicit approximate model for a relaxed alloy; it does not model epitaxial strain, temperature or bowing. Do not use both an explicit lattice and a Vegard model. The historical hardcoded 0.35 is not carried forward.

`reflections` is a list of three-index planes `(h,k,l)` or valid hexagonal four-index planes `(h,k,i,l)`, encoded as JSON arrays. For example `[[2,2,-4,0]]` denotes (22-40); it is an indexing example, **not confirmation of the measured reflection**. Separate film and substrate lists allow different epitaxial relationships.

## Orientation and exact frame relationship

For each phase, `orientation.surface_plane` specifies its reciprocal-plane normal along common sample +z. `orientation.in_plane_direction` specifies a **direct lattice direction** along common sample +y. Sample +x = +y cross +z. Hexagonal directions `[u,v,t,w]` must obey t=−u−v and are converted to `[2u+v,u+2v,w]`, unlike planes. The direction must actually lie in the surface plane; it is never silently projected. Film and substrate must refer to the same physical sample axes. Do not copy the substrate indices to a differently oriented film without evidence.

For a tilted film or general orientation relationship, supply `orientation: {"crystal_to_sample": [[...],[...],[...]]}` instead of indices. This proper rotation maps Cartesian crystal coordinates (the lattice basis convention in [coordinates.md](coordinates.md)) into common sample coordinates. Rows are sample-axis components in crystal Cartesian coordinates.

`sample.frame_alignment.sample_to_map` is a separate proper rotation from that common sample frame to the **actual configured instrument output frame**. `map_frame` must match `geometry.frame` exactly. Identity is valid only when their axes coincide; the toolkit never invents it. `reference` must describe the mounting/calibration evidence or explicit provisional assumptions. `verified` and `allow_provisional` are booleans. Unverified map geometry or alignment requires explicit `frame_alignment.allow_provisional: true`; every marker then says PROVISIONAL. This opt-in does not fill missing orientations or a missing transform.

The calculation is `Q_map = R_sample_to_map R_crystal_to_sample (2π A^(-T)) h`. Both experiment and theory use inverse angstrom with the 2π convention. Reflection vectors outside the configured omitted-axis tolerance are rejected instead of projected; vectors beyond elastic wavelength accessibility are rejected. A geometrically accessible position does not establish a nonzero structure factor or experimental visibility.

## Plot and compatibility

Substrate markers are cyan circles; film markers are magenta diamonds, each with a phase/reflection label and status. Plot settings include `mode` (points/grid), `intensity_scale` (log/linear), `bins`, `components`, `cmap`, `vmin`, `vmax`, `dynamic_range_decades`, `xlim`, `ylim`, `plane_tolerance`, `title` and `theoretical_overlays`. `--mode` and `--scale` override the corresponding JSON values. Geometry-only JSON files and the existing Python API still work.

## Numerical validation

Reciprocal vectors obey AᵀB = 2πI and d = 2π/|Bh|. This uses the angular-wavevector convention; IUCr's commonly used crystallographic reciprocal vectors omit the 2π factor. See the [IUCr reciprocal-lattice derivation](https://www.iucr.org/what-we-do/education/pamphlets/reciprocal-lattice).

Independent tests use `1/d² = 4(h²+hk+k²)/(3a²) + l²/c²`. For a hexagonal (22-40) vector with sample normal (10-10) and direct +y=[1,-2,1,0], the closed form is `(Qx,Qy,Qz)=(0,-4π/a,4π√3/a)`. Tests compare this formula against the general matrix calculation, change the map alignment, and check film/substrate separation. These are test orientations, not inferred metadata for the supplied scans. Existing xrayutilities comparisons continue to check the instrument conversion independently.
