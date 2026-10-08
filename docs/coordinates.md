# Coordinate conventions and physical validity

## Measurement versus interpretation

The importers preserve recorded angles and counts; they do not select a crystal phase, infer reflections, divide by time, or apply alignments. In the supplied BRML files `Theta` is explicitly displayed as Omega. `TwoThetaArm` is the scan's detector motor position; `TwoTheta` is the **per-bin absolute angle** obtained by adding the declared `TwoTheta_Relative` scale. Do not add a second pixel correction using detector distance: the source bins are already angularly calibrated/rebinned.

The method records used wavelength 1.5406 Å. This is distinct from the tube's alpha-average and other characteristic wavelengths. Imported used wavelength can be overridden only explicitly, with a reason if it conflicts with recorded information.

## Nominal coplanar model

Right-handed Cartesian axes: x is transverse, y points along the incident beam's projection into the nominal surface, z is the nominal outward normal. Angles are degrees at the public API. With t=2θ and k=2π/λ:

```
ki = k (0, cos(omega), -sin(omega))
kf = k (0, cos(t-omega), sin(t-omega))
Q  = kf - ki
Qx = 0
Qy = k [cos(t-omega) - cos(omega)]
Qz = k [sin(t-omega) + sin(omega)]
```

The model is equivalent to rotating a laboratory incident ray (0,1,0) by a detector rotation Rx(t) and expressing the difference in a sample basis rotated Rx(omega): Qsample=Rx(omega)ᵀ[Rx(t)ki−ki]. This equivalence is tested independently by the general vector engine and xrayutilities QConversion. These coordinate conventions are explicit choices, not universal meanings of the letters qy/qz.

The magnitude is 4π sin(θ)/λ for 0≤t≤180°. For ω=θ, Qy=0. At fixed t a rocking scan traces an arc of constant Q magnitude. For ω<θ, Qy is negative in this convention. Reversing an axis changes signs; it does not establish an alternative physical sample orientation.

Corrections are `corrected_angle = sign * recorded_angle + offset_deg`. Offsets are **additional** corrections. Imported alignment `Delta` values are preserved but never treated automatically as motor zero errors. Their meaning is not established by their names. A zero additional offset means no added correction, not a claim that the instrument is perfectly aligned.

## General vector geometry

`VectorGeometry` accepts incident and zero-detector unit vectors, and explicit sample/detector `MotorRotation` sequences. Each rotation has a Cartesian unit-axis direction, recorded motor name, sign and offset. Active right-handed rotations are applied in list order about fixed laboratory axes. The next matrix left-multiplies the previous matrix. Thus `[R1,R2]` produces R2 R1; swapping rotations usually changes the result.

`Qlab = (2π/λ)(Rdetector * exit_zero - incident)` and `Qsample = Rsample.T * Qlab`. A nested real goniometer must be translated into the physically equivalent rotation sequence; supplying names such as Chi or Phi does not define those axes. No unsupported Bruker 4/6-circle sequence is silently selected. General vector geometry is an explicit computational capability, not a calibrated model of every instrument.

## Crystal frames and reflection overlays

Cell lengths are Å, cell angles are degrees. A has direct vectors as columns, B=2π A⁻ᵀ, and G=B(h,k,l). `Lattice` supports positive-volume general metrics. `Orientation.crystal_to_sample` is a proper orthonormal rotation with determinant +1. `Orientation.from_surface` uses a reciprocal plane normal for +z and a **direct-space** tangent direction for +y; a non-tangent direction is rejected rather than silently projected.

For hexagonal planes, (h k i l) requires i=−h−k and becomes (h k l). For direct directions, [u v t w] requires t=−u−v and becomes [2u+v,u+2v,w]. Four-index notation is rejected for nonhexagonal metrics. Multi-digit signed integer tuples are supported. Do not drop the third index of a direction as if it were a plane.

A predicted G can exist geometrically but have zero structure factor. The package labels cell-only overlays accordingly. `Material.structure_factor` sums a complete, user-supplied cell motif and user-supplied scattering factors for the relevant Q and energy. It does not infer space groups from names, expand CIF symmetry, or guess atomic factors. Users needing full diffraction simulation should supply a validated structure model/library. `vegard_lattice` is an explicitly called linear hexagonal end-member approximation; no alloy fraction is set by default.

Overlays must declare the same frame as the map. The omitted Q component must fall within the selected plane tolerance; otherwise the overlay is not drawn. Full 3D Q remains in the numerical result.

## Experimental limitations

Both supplied BRML files declare Coplanar, Positive setup, Theta_Theta vertical goniometer, and UB usage Off. Their fixed Chi values are 0.3° and 0.44°, and Phi values 0.51° and 90°. These are retained, but their mounting/zero conventions do not establish a crystal-to-sample transformation. The nominal coplanar example therefore does not claim Qz is the exact physical surface normal or that Qx was measured to be zero.

The Eiger acquisition is an angularly rebinned 1D profile integrating a finite transverse ROI. It does not preserve the full transverse detector distribution. A reconstructed qx=0 map represents a coplanar projection/approximation. Noncoplanar reconstruction of the original area frames would require those frames and the validated detector/goniometer model.

No refraction, footprint, polarization, absorption, Lorentz, detector-efficiency, dead-time or resolution correction is added. The upstream detector ROI operation produces fractional recorded counts; a Poisson uncertainty cannot be inferred from these values alone. Imported absorption factors are preserved but not reapplied.

Scientific verification still requires a calibrated symmetric/asymmetric standard and the actual mounting/azimuth records. `calibration_verified` is an explicit user declaration accompanied by a reference, not an automatic certification by this toolkit.

## References

The independent general-rotation comparison uses [xrayutilities](https://github.com/dkriegner/xrayutilities), whose methods are described in [Kriegner et al., reciprocal-space conversion](https://arxiv.org/abs/1304.1732). Agreement tests the specified coordinate mathematics; it does not settle the physical motor convention of an uncalibrated experiment.
