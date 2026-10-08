# Coordinate systems and instrument conventions

## What is actually specified

[make_geometry](../Modules/geometry.py:40) gives HXRD two **reciprocal** Cartesian vectors derived from integer triples and `geometry='lo_hi'`. It does not specify a custom goniometer axis sequence or detector. [initialize_data](../Modules/data_procesing.py:108) passes two angle columns directly to Ang2Q. The actual axis definitions, rotations, sign conventions, sample mounting and encoder zero records are absent.

| Symbol / token | Local meaning | Unit / unresolved issue |
|---|---|---|
| omega, om | First measured column; incident/sample angle expected by HXRD | Degrees inferred; absolute versus relative rocking-angle origin unverified |
| theta | Half of the beam deflection in Bragg-law reconstruction | Not a stored local variable for measured data |
| 2theta, tt | Second measured column; detector scattering angle expected by HXRD | Degrees inferred; may already contain pixel and scan-dependent conversion upstream |
| energy | Notebook scalar 8047.8 | eV inferred from intended wavelength |
| wavelength, wl | HXRD wavelength argument | Å inferred from library convention and numerical check |
| qx | First Ang2Q result | Expected transverse component, Å⁻¹; saved in memory then ignored by plot |
| qy | Second Ang2Q result | Expected in-plane scattering component, horizontal plot axis |
| qz | Third Ang2Q result | Expected surface-normal component, vertical plot axis |
| Norm | Four-index token reduced to hkl, converted through crystal.Q | Plane normal in reciprocal space, not necessarily a direct lattice vector |
| InPlane | Four-index token reduced in exactly the same way | Ambiguous: filename says direction, implementation treats it as plane indices |
| chi / phi | Intermediate Q2Ang outputs | Discarded at [geometry line 67](../Modules/geometry.py:67); no measured columns provided |
| omoff | Optional title value | Stored but not applied |
| tt_offset | Added to second column | Always zero in filename construction |
| om_align_offset / tt_align_offset | Parameter-container fields | Unused |
| omscan=abs | Supplied filename suffix | Never interpreted; no guarantee of absolute angle handling |
| 90deg | Mentioned only in a commented print | No rotation implemented |
| Temp | Filename value used on a temperature plot | Label assumes °C; growth temperature versus measurement temperature is not specified |

“PSD” is merely the local name of the intensity column. A position-sensitive detector is plausible, but no manufacturer/model, pitch, distance, angular acceptance, channel mask or saturation threshold is recorded.

## Frame relationships

1. **Crystal direct frame:** defined by each CIF's cell metric and sites.
2. **Crystal reciprocal frame:** B=2πA⁻ᵀ; reflection G=B(h,k,l). Plane normals belong here.
3. **Oriented sample frame:** HXRD uses normal and in-plane references; theoretical vectors pass through Transform. A right-handed reference construction is given in [equations](./03_physics_and_equations.md).
4. **Instrument/laboratory frame:** incident and exit beams plus motor rotations determine q. Only a default two-angle HXRD interface is chosen locally. No explicit orientation matrix UB is stored.
5. **Plot frame:** qy versus qz, with qx dropped. This is a reciprocal-plane representation, not a full 3D map.

An ideal coplanar transform yields qx=0 in its scattering frame. That is a geometric model assumption, not experimental evidence of no off-plane scattering. To compare theory and measurement, both must share one sample frame, handedness, positive in-plane direction and orientation relation. The code creates a different material-derived HXRD frame for each phase using the same integer triples ([experiment_defenitions](../Modules/geometry.py:46)); this does not by itself specify a verified epitaxial relationship.

## Plane indices versus direction indices

For a hexagonal plane (h k i l), i=−h−k and dropping i is valid. For a direct direction [u v t w], t=−u−v and a₃(basal)=−a₁−a₂, giving

\[
u a_1+v a_2+t a_3+w c=(2u+v)a_1+(u+2v)a_2+w c.
\]

Thus the corresponding three-index direct coordinates are [U V W]=[2u+v,u+2v,w], up to common scaling. They must be mapped through the **direct** basis A, not B. [Filename conversion](../Modules/data_procesing.py:75) instead drops t and calls crystal.Q. For [11-20], direct coordinates are [330]∥[110]; using reciprocal (110) is generally a different Cartesian direction. High-symmetry cases such as [0001] can hide this error.

If the label intended a reciprocal-plane normal, the conversion might be appropriate, but then it should not be described as a crystallographic direct direction. This ambiguity cannot be settled by the filename alone.

## Supplied orientations and their implications

| Dataset | Parsed normal | Parsed in-plane vector | Issue |
|---|---|---|---|
| S0154 | Q(100) | Q(00-1) | Normal and in-plane are perpendicular under the hex metric; negative c establishes a meaningful axis sign that needs mounting confirmation |
| S0183 | Q(100) | Q(1,-1,0) | Token `1-120` violates its own redundant-index relation; accepted with warning. The resulting reciprocal vectors are not orthogonal (60° angle under the hex metric) |
| K0203 | Q(100) | Q(110) | Reciprocal vectors make 30°, not 90°; “in-plane” is not literally tangent if taken as the supplied reciprocal vector |

The dot-product statements derive from the hexagonal reciprocal metric and the source's token mapping ([parser](../Modules/data_procesing.py:67)). Library handling of nonperpendicular orientation references is unverified: it may project or otherwise orthogonalize them. The documentation must not invent that behavior. In either case, the encoded orientation needs checking against the actual sample cut and azimuth.

For the theoretical helper, normal Q(110) and in-plane Q(001) are hardcoded ([theory](../Modules/theory.py:21)), replacing all filename orientations. The queried (300) vector is outside their simple scattering plane; discarded azimuth/tilt outputs matter. A printed omega/2theta pair is not a complete motor solution.

## Rotation/sign validation protocol for a later rebuild

- Obtain a diagram with incident beam, outward normal, positive motor rotations, scan axis order and detector sense.
- Establish whether the supplied first column is ω, ω−θ, or an offset motor reading; `omscan=abs` is not sufficient evidence.
- Use a symmetric certified reflection to calibrate detector zero and check qy≈0 at ω=θ.
- Use known positive and negative asymmetric reflections to fix the qy sign and azimuth convention.
- Verify a direct-basis orientation matrix against measured reflections; explicitly distinguish plane normals and direct directions.
- Check noncoplanar peaks with all returned motor angles; reject or flag nonzero discarded components.
- Record handedness, inverse transforms, degree/radian boundaries and whether reciprocal units include 2π.

These are proposed validation steps, not experiments performed during this audit.
