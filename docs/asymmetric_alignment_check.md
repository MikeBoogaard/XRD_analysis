# Asymmetric alignment diagnostic

The user authorized testing the alignment plan. This is a separate diagnostic, not a replacement of the original reconstruction or an independently verified instrument calibration.

## Metadata evidence

There is no matching BRML for `rsm(12-30)along10-10.raw` in example_data. The RAW stores fixed Phi=-2.35 degrees and Chi=0.48 degrees, but neither alone supplies a calibrated crystal-to-instrument orientation or alignment history.

RAW type-60 records include Theta delta=1.5, TwoTheta delta=1, Phi delta=2, and Chi delta=0.75. They are identical in all four available RAW files. In the older **paired** S0159 BRML, the same Delta values appear alongside separate PositionOffset values and MeasurementPoints in alignment settings; InstructionContainer also has separate InternalOffset/ExternalOffset fields. These older measurements are schema evidence only, not calibration records for the new scan. Therefore applying RAW Delta as an angle correction is unjustified. The public [xylib RAW4 reader](https://github.com/wojdyr/xylib/blob/master/xylib/bruker_raw.cpp) likewise extracts type-60 flag/delta fields without establishing an already-applied angle correction.

The range AXIS_OFFSET_2THETA=71 equals the detector arm angle, not an omega correction. Unknown RAW metadata segments (types 5, 110, 300) remain undecoded; no claim is made that the binary contains no further calibration information. RAW material strings say Si (no database), conflicting with the supplied specimen identity, so they are not used to choose the crystal.

## Numerical experiment

The existing (11-20) surface and (12-30) reflection configuration is retained, including the explicitly provisional azimuth branch. A local correlated 2D Gaussian plus constant background was fitted to raw counts around the brightest bin, assumed to be the substrate. It is an unweighted empirical location estimator, not a Poisson model or phase identification. Half-window widths of 0.2, 0.3 and 0.4 degrees test sensitivity; the film feature is excluded by these windows. The omega step is 0.04 degrees: numerical fit stability is not an instrumental precision estimate.

| Quantity | Asymmetric (12-30) | Symmetric (11-20), check only |
|---|---:|---:|
| Fitted omega, degrees | 44.780231 | 21.887988 |
| Fitted 2theta, degrees | 69.328467 | 43.741345 |
| Theoretical omega, degrees | 45.572592 | 21.868986 |
| Theoretical 2theta, degrees | 69.358395 | 43.737972 |
| Observed minus theoretical 2theta, degrees | -0.029928 | +0.003373 |
| Omega-only direction correction, degrees | +0.777397 | -0.017315 |

For this nominal coplanar convention, alpha=atan2(Qy,Qz)=omega−2theta/2. The trial correction is alpha_theory−alpha_measured, rather than simply theoretical omega minus measured omega. Detector angles remain unchanged. This rotates all measured Q vectors in the scattering plane while preserving |Q| and every recorded intensity. It does not force radial agreement or independently calibrate the detector.

The asymmetric correction ranges from +0.777394 to +0.777407 degrees over the tested windows. Its fitted substrate Q discrepancy decreases from 0.062983 to 0.001752 inverse angstrom. Alignment of the reference peak is substantially enforced by this procedure: it is not independent validation. No correction was applied to the symmetric scan, no parameters were fitted to the film, and no claim of film strain/composition was inferred from the result.

## Outputs and reproduction

- [Before/after comparison](../outputs/alignment_check/comparison.png), visually inspected.
- [Full fit and metadata report](../outputs/alignment_check/report.json).
- [Separate diagnostic configuration](../outputs/alignment_check/omega_reference_trial.json), calibration_verified remains false.
- [Diagnostic numerical data](../outputs/alignment_check/omega_reference_trial_map.npz) and [metadata](../outputs/alignment_check/omega_reference_trial_map.json).

```powershell
.venv/Scripts/python examples/check_asymmetric_alignment.py
```

The [script](../examples/check_asymmetric_alignment.py) checks invariant intensities and Q magnitudes; its estimator has a synthetic centre-recovery test. It writes only into outputs/alignment_check and preserves original maps/configurations and experimental inputs.

## What this establishes

A scan-specific in-plane reference rotation can explain most of the geometric discrepancy under the declared assumptions. It does not distinguish sample tilt, omega zero, exported angle conventions or incorrect 3D alignment. A single coplanar peak cannot recover the phi/chi motor axes, ordering, zero references and sample orientation. Do not insert the raw phi value as a correction. Keep this trial separate until a matching BRML/alignment report or additional calibrated reference reflections can resolve the actual geometry. In particular, do not transfer this correction to other scans by default.
