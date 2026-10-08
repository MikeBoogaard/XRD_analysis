# Physics reconstruction and equation checks

The repository delegates crystallography and diffractometer transforms to xrayutilities; it does not contain their implementation or pin a version. The equations below distinguish exact local operations from physical reconstruction. Independent checks use standard elastic scattering and lattice duality, not a second invocation of the same library.

## 1. Photon energy and wavelength

**Principle:** E=hν, c=λν, hence λ=hc/E. With E in eV and λ in Å, hc≈12398.419843320026 eV Å. The notebook's E=8047.8 eV implies λ=1.5405974108849654 Å.

**Observed call:** [make_geometry](../Modules/geometry.py:43) uses `xu.lam2en(energy)` and passes the result as `wl`. The function name conventionally denotes wavelength-to-energy, opposite to the variable names. If both conversions implement the same numeric hc/x using eV and Å, the numerical result is nevertheless correct. This is not sufficient evidence for a wavelength-scale error; confirm the actual historical library's implementation and units. Do not “correct” this based on naming alone.

**Domain:** monochromatic photons in vacuum; no spectral doublet or energy distribution modeled. **Independent check:** compare against a calibrated source energy and a standard reference reflection. The value resembles a Cu Kα energy but the source spectrum and monochromator are not documented.

## 2. Reciprocal lattice and d spacing

Let A=[a₁ a₂ a₃] contain direct-lattice Cartesian vectors (Å). Define B=2πA⁻ᵀ, so aᵢ·bⱼ=2πδᵢⱼ. For integer plane indices h,k,l,

\[
\mathbf G_{hkl}=B(h,k,l)^T,\qquad d_{hkl}=\frac{2\pi}{|\mathbf G_{hkl}|}.
\]

This follows from constant lattice-plane phase G·r=2πn. Some crystallographic conventions omit 2π; this repository's expected Å⁻¹ scattering-vector convention includes it, consistent with the independent angle check below. [Crystal.Q calls](../Modules/geometry.py:41) delegate this construction. A CIF supplies cell dimensions and angles; atomic sites are not needed for peak-position geometry.

For the supplied hexagonal metrics a=b, α=β=90°, γ=120°,

\[
\frac1{d^2}=\frac{4}{3a^2}(h^2+hk+k^2)+\frac{l^2}{c^2}.
\]

Derivation: take a₁=(a,0,0), a₂=(-a/2,√3a/2,0), a₃=(0,0,c); invert A and calculate |Bh|²/(2π)². Hexagonal four-index planes satisfy i=-(h+k), so (h,k,i,l)→(h,k,l) is valid for **planes**. [hkil_to_hkl](../Modules/geometry.py:76) checks this only with a warning. It is not the direct-space direction conversion.

**Domain:** ideal periodic lattice, stated metric and indexing convention. **Checks:** independently invert A, verify AᵀB=2πI, evaluate known spacings, and compare to certified reference data. Unit-cell values in the supplied CIFs are assumptions, not calibration measurements of the samples.

An additional independent consistency check uses V=abc√(1+2cosα cosβ cosγ−cos²α−cos²β−cos²γ), from the determinant of the direct metric tensor. For hexagonal cells this reduces to V=(√3/2)a²c. The listed CdS dimensions imply 99.4952572701 Å³, while [CdS.cif line 13](<../Literature data for analysis/CIF/CdS.cif:13>) declares 102.03892544 Å³. Hex-Ge implies 90.4768155759 Å³, while [its CIF line 13](<../Literature data for analysis/CIF/Hex_Ge_100_paper.cif:13>) declares 95.0454714981 Å³. The other three CIF volumes agree with their metrics to the displayed precision. These are confirmed metadata inconsistencies, not proof that the library uses the wrong metric: its field precedence must be checked. They may indicate edited lattice dimensions with stale volume metadata, but that history is unverified.

## 3. Elastic scattering and angular conversion

Let incident and exit wavevectors have magnitude k₀=2π/λ. Momentum transfer is q=k_f−k_i. In a right-handed sample frame with +z the outward surface normal, +y in the scattering plane and incident beam projection along +y, let ω be the incident grazing angle and t=2θ the beam deflection. Then

\[
\mathbf k_i=k_0(0,\cos\omega,-\sin\omega),\quad
\mathbf k_f=k_0(0,\cos(t-\omega),\sin(t-\omega)),
\]
\[
q_x=0,\quad q_y=k_0[\cos(t-\omega)-\cos\omega],\quad
q_z=k_0[\sin(t-\omega)+\sin\omega].
\]

By sum-to-product identities,

\[
q_y=\frac{4\pi}{\lambda}\sin\theta\sin(\omega-\theta),\qquad
q_z=\frac{4\pi}{\lambda}\sin\theta\cos(\omega-\theta),\qquad
|q|=\frac{4\pi}{\lambda}|\sin\theta|.
\]

These are a **declared candidate convention** for the two-angle coplanar transform invoked at [data_procesing line 114](../Modules/data_procesing.py:114). Reversing the positive in-plane axis reverses qy; changing the definition of q also changes signs. Since the dependency is absent and no instrument axis definition is provided, the exact sign of the historical Ang2Q output has not been empirically established here. Do not use this derivation as a claim that every dataset's column 0 is absolute ω.

Angles inside sin/cos are radians; experimental degree values require multiplication by π/180. **Domain:** elastic monochromatic scattering, coplanar point-angle geometry, calibrated absolute angles, no refraction correction. A detector array is compatible only if each exported pixel already has a valid t; the repository has no detector distance, pixel pitch, beam-center or tilt model.

**Independent tests:** ω=θ gives qy=0 and qz=4πsinθ/λ; t=0 gives q=0; at fixed t, scanning ω traces a circle in qy–qz; magnitude is independent of ω. Test an asymmetric reference on both sides of the surface normal to settle the sign. A round-trip within one library checks internal consistency only.

## 4. Bragg law and predicted instrument angles

Set q=G for a reciprocal-lattice reflection. Combining the previous equations yields

\[
2d\sin\theta=\lambda,\qquad
2\theta=2\arcsin\left(\frac{\lambda|G|}{4\pi}\right).
\]

Higher diffraction orders can be represented by integer multiples of hkl. In the declared coplanar convention, let α=atan2(G_y,G_z), the signed tilt of the reciprocal vector from +z. Then ω=θ+α for that branch. `lo_hi` selects a library inverse-geometry branch; the code does not expose a complete instrument motion or accessibility model ([geometry line 40](../Modules/geometry.py:40)).

[theoretical_om_tt](../Modules/geometry.py:67) returns only the first and fourth Q2Ang values, discarding the intermediate angles (ordinarily chi/phi in HXRD). For a reflection outside the scattering plane, those may be necessary; two angles alone cannot specify the required orientation. Physical accessibility also requires λ|G|≤4π and instrument travel limits.

**Independent numerical check actually performed:** [theory](../Modules/theory.py:21) sets normal (110), in-plane (001), and asks for (300). Hexagonal reciprocal geometry puts (300) 30° from (110). Choosing the ω=θ−30° branch gives:

| Material | a (Å) | Magnitude of G300 (Å⁻¹) | Independent ω (°) | Independent 2θ (°) |
|---|---:|---:|---:|---:|
| CdS | 4.136 | 5.2624739775 | 10.1778763843 | 80.3557527687 |
| Hex-Ge | 3.9855 | 5.4611949243 | 12.0304359868 | 84.0608719736 |

These reproduce the stored output in [notebook lines 136–137](../RSM_main.ipynb:136). This verifies the metric/energy/branch calculation for that example. It does **not** prove that (300) lies in the fixed (001)-normal scattering plane at zero azimuth: a nonzero additional rotation may be required. Nor does it validate the material structure, instrument alignment or measured peaks.

## 5. Orientation frame

For normal n and in-plane reference v represented as Cartesian reciprocal vectors, a physically explicit orthonormal construction would be

\[
e_z=n/|n|,\quad v_\perp=v-(v\cdot e_z)e_z,\quad
e_y=v_\perp/|v_\perp|,\quad e_x=e_y\times e_z.
\]
\[
T=\begin{pmatrix}e_x^T\\e_y^T\\e_z^T\end{pmatrix},\quad G_s=T G_c.
\]

This is a **validation reference**, not a verified reproduction of HXRD's handling of nonorthogonal input vectors. [make_geometry](../Modules/geometry.py:41) supplies Q-derived n and v directly; [theoretical_Qy_Qz](../Modules/geometry.py:72) calls the library Transform. Projection is undefined when v is parallel to n. **Independent checks:** T Tᵀ=I, det T=+1, normal maps to +z, lengths/dot products preserved; compare the library basis and asymmetric peaks. See [coordinate analysis](./04_coordinate_systems.md).

## 6. Structure factors and alloy assumptions

The kinematic structure factor is F(G)=Σⱼ oⱼ fⱼ(G,E) exp(iG·rⱼ), optionally including Debye–Waller factors; ideal intensity is proportional to |F|² with experimental factors. Here oⱼ is occupancy, fⱼ the atomic scattering factor, and rⱼ the site position. This derives from coherent summation of scattered amplitudes. Atomic species/sites and symmetry in CIFs can affect allowed-reflection and theoretical-display behavior, but the local code contains **no measured-intensity simulation or structure-factor refinement**. The exact reflection selection and marker weighting in [show_reciprocal_space_plane calls](../Modules/theory.py:30) require library inspection. The internal key GeWZ is a code label, not evidence that elemental hexagonal Ge has the same binary wurtzite structure as CdS; establish the actual Ge polytype from its sites and experimental provenance.

The 0.35 argument to [Alloy](../Modules/geometry.py:17) suggests composition interpolation. A common reference model is Vegard's law a(x)=(1−x)a_A+xa_B (and similarly c), but neither interpolation nor component-fraction semantics is implemented locally. Do not assert the alloy is 35% Zn without checking the library and experiment. Independent validation would compare end members, an intermediate composition and measured lattice constants; strain, bowing and temperature can invalidate linearity.

## 7. Intensity, gridding and display

[Normalization](../Modules/data_procesing.py:110): I_j=C_j/τ, where C_j is input intensity and τ is a filename-derived scalar defaulting to 1. This is a count-rate interpretation only if C contains counts and τ is exposure in seconds. For independent Poisson counts, Var(I)=C/τ²; the implementation does not propagate this. Fractional/negative exported values require upstream provenance.

For a grid value J_ab, [plotting](../Modules/plotting.py:68) calculates M=max J, v_min=0.1/M, J'=max(J/M,v_min), v_max=max(J/M)=1 for M>0. Contour levels are geometric between v_min and 1; `LogNorm` uses [10v_min,1]. This is display scaling, not correction for background, detector response or photon flux. Domain requires finite positive maxima and sensible thresholds. M≤0 or small M can create invalid/equal/decreasing levels or color bounds. Check constant images, single occupied bins, masked bins, scaling of all input intensities, and sparse coverage. Exact gridding weights are unresolved; generic weighted binning would have J_ab=Σw_jab I_j/Σw_jab, but this is not verified for the unpinned library.

## 8. Peak and line statistics

**Strip mean, implemented:** for each exact ω=u, S_u={j:ω_j=u, |t_j−t_c|≤Δt}, A(u)=Σ_{S_u} I_j/|S_u| ([line_scan](../Modules/line_scan.py:41)). Δt is a half-width. The estimator is a sample mean, not ΣIΔt. Check a constant signal with differing detector-bin populations: mean stays constant, integrated signal need not. No Jacobian or bin-width weighting is included.

**Thresholded index centroid, implemented but inactive:** form M_rs=ΣI for matching omega index r and rounded-to-four-decimals t index s; zero values below 0.3 max M. Compute r̄=ΣrM/ΣM, s̄=ΣsM/ΣM; round to nearest integer and return the corresponding angles ([data_analysis](../Modules/data_analysis.py:31)). This equals a coordinate centroid only for uniformly spaced axes before rounding. It is neither a maximum nor a fitted subpixel center. Independent check: use irregular spacings and compare ΣωI/ΣI directly. Zero total weight is undefined, as observed in the audit.

**Alternating maxima, implemented:** [find_fixed_position](../Modules/data_procesing.py:152) uses finite-band line cuts and argmax near a predicted reference; it does not compute a centroid. Validate with known isolated and overlapping peaks, varied sampling and peak displacement; fix-free analysis must retain the fact that the fine qy pass reuses the preceding qz slice indices.

## 9. Profile model and width metrics

Let A≥0 be peak height, x₀ the center, w>0 the common FWHM, and 0≤η≤1 the Lorentzian height fraction. [pseudo_voigt](../Modules/fitting.py:127) implements

\[
P(x)=A\left[\eta\frac{(w/2)^2}{(x-x_0)^2+(w/2)^2}+(1-\eta)e^{-4\ln2(x-x_0)^2/w^2}\right].
\]

Both components equal A/2 at x=x₀±w/2; therefore the mixture's FWHM is exactly w. η is not an integrated-area fraction. This is an empirical mixture, not the convolution that defines a true Voigt. On an omega axis w is in degrees. Domain: one isolated peak described adequately by this shape, without a baseline in the current model. Independent checks: η=0/1 limits, half-height points, and synthetic peaks with baseline/overlap to quantify model bias. FWHM alone is not a validated mosaic spread, coherent domain size, strain or dislocation density; instrumental resolution and scan geometry must be separated.

[curve_fit](../Modules/fitting.py:78) minimizes Σ[y_j−P(x_j)]² with no sigma array. Initial values are (1, argmax position, 0.1, 0.5), with A,w≥0, x₀ constrained to selected data and η in [0,1]. The w=0 boundary is mathematically singular. Approximate interval w±1.96√Cov_ww ([line 92](../Modules/fitting.py:92)) relies on local linearization and the residual/noise assumptions of the fitter; it is not an experimentally validated 95% uncertainty, especially after intensity-dependent filtering or for bounded parameters. Check bootstrap/profile likelihood and repeat measurements, with an appropriate count/error model.

R²=1−Σresidual²/Σ(y−mean y)² ([line 96](../Modules/fitting.py:96)); undefined for constant y and not a goodness-of-physics certificate. Integral breadth β=trapezoid(y,x)/max(y) ([line 135](../Modules/fitting.py:135)) uses the selected **data**, not the fitted curve. For the full background-free model,

\[
\beta_\infty=w\left[\eta\frac\pi2+(1-\eta)\frac{\sqrt\pi}{2\sqrt{\ln2}}\right].
\]

This follows from Gaussian and Lorentzian integrals and provides an independent test. Finite ±2° truncation, deleted points, baseline and unsorted x change the reported breadth. Local implementation returns zero if max(y)=0, a computational convention rather than a physical result.
