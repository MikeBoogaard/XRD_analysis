"""Diagnostic only: test an empirical substrate-reference omega correction.

No instrument correction is inferred from RAW Delta fields. Run from repo root.
Original data, configurations and plots are not modified.
"""
import copy
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import least_squares
from rsm_toolkit import (load_xrd, load_configuration, calculate_rsm,
                        configured_reflections, plot_rsm, export_data)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'outputs/alignment_check'


def fit_peak(measurement, half_width):
    """Local unweighted correlated Gaussian + constant background on raw counts.

    Window centred on global brightest bin (assumed substrate); no Poisson
    likelihood or uncertainty claim for these fractional detector counts.
    """
    om, tt = measurement.motors['Theta'], measurement.motors['TwoTheta']
    intensity = measurement.intensity
    index = np.unravel_index(np.argmax(intensity), intensity.shape)
    o0, t0 = om[index], tt[index]
    mask = (abs(om-o0) <= half_width) & (abs(tt-t0) <= half_width)
    x, y, z = om[mask]-o0, tt[mask]-t0, intensity[mask]
    scale = z.max()

    def model(p):
        amplitude, ox, ty, sx, sy, rho, background = p
        u, v = (x-ox)/sx, (y-ty)/sy
        return background + amplitude*np.exp(-(u*u-2*rho*u*v+v*v)/(2*(1-rho*rho)))

    fit = least_squares(lambda p: model(p)-z/scale,
                        [1,0,0,.08,.08,0,0],
                        bounds=([0,-half_width,-half_width,.005,.005,-.95,0],
                                [3,half_width,half_width,half_width,half_width,.95,1]),
                        max_nfev=4000)
    if not fit.success or np.any(fit.active_mask):
        raise RuntimeError('Peak fit failed or hit a parameter bound; inspect before calibration.')
    return {'half_window_deg': half_width, 'omega_deg': float(o0+fit.x[1]),
            'two_theta_deg': float(t0+fit.x[2]), 'points': int(mask.sum()),
            'rms_fraction_of_max': float(np.sqrt(np.mean(fit.fun**2))),
            'parameters': fit.x.tolist(), 'status': 'empirical local fit; not phase identification'}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    results = {}
    for label, filename in [('12-30','rsm(12-30)along10-10.raw'),
                            ('11-20','RSM(11-20)along0001.raw')]:
        m = load_xrd(ROOT/'example_data'/filename)
        c = load_configuration(ROOT/f'examples/cdzns_{label}.json')
        r = calculate_rsm(m,c)
        predictions,_ = configured_reflections(c,r)
        substrate = predictions[0].q
        theta = np.rad2deg(np.arcsin(np.linalg.norm(substrate)*r.wavelength_angstrom/(4*np.pi)))
        alpha = np.rad2deg(np.arctan2(substrate[1],substrate[2]))
        fits = [fit_peak(m,w) for w in (.2,.3,.4)]
        for f in fits:
            # In this explicit positive-Qy branch alpha = omega - 2theta/2.
            f['omega_only_correction_deg'] = float(alpha-(f['omega_deg']-f['two_theta_deg']/2))
            f['two_theta_residual_deg'] = float(f['two_theta_deg']-2*theta)
        results[label] = {'source_sha256':m.source.sha256,
                          'theoretical_omega_deg':float(theta+alpha),
                          'theoretical_two_theta_deg':float(2*theta),
                          'theoretical_alpha_deg':float(alpha), 'fits':fits,
                          'raw_alignment_fields':[s for s in m.metadata['global_segments'] if s['type']==60],
                          'fixed_phi_deg':float(m.motors['Phi'].flat[0]),
                          'fixed_chi_deg':float(m.motors['Chi'].flat[0])}
        if label != '12-30':
            continue
        trial = json.loads((ROOT/'examples/cdzns_12-30.json').read_text())
        delta = fits[1]['omega_only_correction_deg']
        trial['geometry']['omega_offset_deg'] += delta
        trial['notes'] += (' DIAGNOSTIC: empirical omega-only substrate reference correction '
                           f'{delta:.9f} deg derived from local Gaussian centre; not recovered instrument metadata. '
                           'Assumes brightest peak is unstrained CdS and mismatch is an omega/frame zero error. '
                           'Detector angle unchanged; cannot determine phi/chi axis model from one peak.')
        trial['plot']['title']='DIAGNOSTIC substrate-reference alignment; not independently calibrated'
        path = OUT/'omega_reference_trial.json'
        path.write_text(json.dumps(trial,indent=2)+'\n',encoding='utf-8')
        tc = load_configuration(path)
        tr = calculate_rsm(m,tc)
        np.testing.assert_array_equal(r.intensity,tr.intensity)
        np.testing.assert_allclose(np.linalg.norm(r.q,axis=-1),np.linalg.norm(tr.q,axis=-1),atol=1e-14)
        measured_angles={'Theta':fits[1]['omega_deg'],'TwoTheta':fits[1]['two_theta_deg']}
        before=c.geometry.transform(measured_angles,r.wavelength_angstrom)
        after=tc.geometry.transform(measured_angles,r.wavelength_angstrom)
        results[label].update(q_before=before.tolist(),q_after=after.tolist(),q_theory=substrate.tolist(),
                             q_error_before=float(np.linalg.norm(before-substrate)),
                             q_error_after=float(np.linalg.norm(after-substrate)))
        fig,axes=plt.subplots(1,2,figsize=(16,7),layout='constrained')
        for data,ax,title in [(r,axes[0],'Original: no additional correction'),
                              (tr,axes[1],f'DIAGNOSTIC: omega + {delta:.4f} degrees')]:
            plot_rsm(data,ax=ax,reflections=predictions,dynamic_range_decades=4,title=title,
                     xlim=(.60,1.17),ylim=(4.35,4.95))
        fig.savefig(OUT/'comparison.png',dpi=180)
        plt.close(fig)
        export_data(tr,OUT/'omega_reference_trial_map.npz')
    (OUT/'report.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:{'theory_omega':v['theoretical_omega_deg'],
                          'theory_two_theta':v['theoretical_two_theta_deg'],
                          'fits':v['fits'], 'q_error_before':v.get('q_error_before'),
                          'q_error_after':v.get('q_error_after')} for k,v in results.items()},indent=2))


if __name__ == '__main__':
    main()
