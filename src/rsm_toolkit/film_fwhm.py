"""Explicit angular-band rocking-curve analysis, independent of display scaling."""
import json
import warnings
from dataclasses import replace
import numpy as np
from scipy.optimize import curve_fit, OptimizeWarning
from .errors import RSMError
from .processing import angular_profile


def pseudo_voigt(x, amplitude, center, fwhm, eta, background):
    u=(np.asarray(x)-center)/fwhm
    return background+amplitude*((1-eta)*np.exp(-4*np.log(2)*u*u)+eta/(1+4*u*u))


def fit_profile(x,y):
    x,y=np.asarray(x,float),np.asarray(y,float)
    if x.ndim!=1 or x.shape!=y.shape or x.size<8 or not np.isfinite([x,y]).all():
        raise RSMError('FWHM requires at least 8 finite profile points.')
    order=np.argsort(x); x,y=x[order],y[order]
    if np.any(np.diff(x)<=0) or np.ptp(y)<=0:
        raise RSMError('FWHM requires unique omega values and varying intensity.')
    # Scale intensity for numerical conditioning only; restore original units below.
    scale=np.ptp(y); base=y.min(); normalized=(y-base)/scale
    span=np.ptp(x)
    with warnings.catch_warnings():
        warnings.simplefilter('error',OptimizeWarning)
        try:
            p,cov=curve_fit(pseudo_voigt,x,normalized,
                p0=[1,x[np.argmax(y)],span/5,.5,0],
                bounds=([0,x.min(),np.finfo(float).eps,0,-np.inf],
                        [np.inf,x.max(),2*span,1,np.inf]),maxfev=20000)
        except (RuntimeError,ValueError,OptimizeWarning) as exc:
            raise RSMError(f'FWHM fit failed: {exc}') from exc
    p[0]*=scale; p[4]=p[4]*scale+base
    factors=np.array([scale,1,1,1,scale]); cov=cov*factors[:,None]*factors[None,:]
    if not np.isfinite(cov).all():raise RSMError('FWHM fit covariance is not finite.')
    if p[1]-p[2]/2<x.min() or p[1]+p[2]/2>x.max():
        raise RSMError('Fitted half-height points lie outside the omega range. Select a wider isolated peak region.')
    notes=['Single pseudo-Voigt plus constant background; unweighted least squares.',
           'Empirical omega width, not resolution-corrected mosaicity, strain or crystallite size.',
           'Covariance is a local approximation, not a validated confidence interval.']
    if p[2]<2*np.median(np.diff(x)):notes.append('Peak width is sampled by fewer than two median omega steps.')
    if p[3]<1e-5 or p[3]>1-1e-5:notes.append('Mixing fraction is at a model boundary; covariance may be unreliable.')
    fitted=pseudo_voigt(x,*p)
    return dict(zip(('amplitude','center_deg','fwhm_deg','eta','background'),map(float,p)),
                covariance=cov.tolist(),parameter_order=['amplitude','center_deg','fwhm_deg','eta','background'],
                x=x.tolist(),observed=y.tolist(),fitted=fitted.tolist(),residuals=(y-fitted).tolist(),notes=notes)


def analyze(rsm,geometry,selection,folder,map_axes):
    """Use corrected degree angles consistently for selection, axes and map boundaries."""
    m=rsm.measurement
    motors={}
    for name,sign,offset in ((geometry.omega_motor,geometry.omega_sign,geometry.omega_offset_deg),
                              (geometry.detector_motor,geometry.detector_sign,geometry.detector_offset_deg)):
        unit=m.motor_units[name]
        if unit not in ('degree','radian'):raise RSMError('FWHM requires angular motor units.')
        value=np.rad2deg(m.motors[name]) if unit=='radian' else m.motors[name]
        motors[name]=sign*value+offset
    corrected=replace(m,motors=motors,motor_units={k:'degree' for k in motors})
    center,half,low,high=selection
    x,y,n=angular_profile(corrected,scan_motor=geometry.omega_motor,band_motor=geometry.detector_motor,
                          center=center,half_width=half)
    keep=(x>=low)&(x<=high)
    result=fit_profile(x[keep],y[keep])
    result.update(source=m.source.__dict__,selection=dict(two_theta_center_deg=center,
        two_theta_half_width_deg=half,omega_min_deg=low,omega_max_deg=high),
        geometry=geometry.describe(),intensity_unit=m.intensity_unit,
        reduction='Arithmetic mean of finite recorded intensities per exact omega; no spike removal or log transform.',
        sample_counts=n[keep].tolist())
    np.savetxt(folder/'fwhm.csv',np.column_stack([result[k] for k in ('x','observed','fitted','residuals')]+[n[keep]]),
               delimiter=',',header='omega_deg,mean_intensity,fitted_intensity,residual,sample_count',comments='')
    (folder/'fwhm.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    import matplotlib.pyplot as plt
    fig,(ax,res)=plt.subplots(2,1,sharex=True,figsize=(8,6),height_ratios=[3,1],layout='constrained')
    try:
        ax.plot(x,y,'.',color='0.7',label='Band profile')
        ax.plot(result['x'],result['observed'],'.',label='Selected fit data')
        dense=np.linspace(min(result['x']),max(result['x']),600)
        p=[result[k] for k in ('amplitude','center_deg','fwhm_deg','eta','background')]
        ax.plot(dense,pseudo_voigt(dense,*p),label='Pseudo-Voigt + background')
        ax.hlines(p[4]+p[0]/2,p[1]-p[2]/2,p[1]+p[2]/2,color='red',label='FWHM')
        ax.set(title=f'Film-region rocking curve: FWHM = {p[2]:.5g} degrees',ylabel=m.intensity_unit)
        ax.legend(); res.plot(result['x'],result['residuals'],'.'); res.axhline(0,color='gray')
        res.set(xlabel='Corrected omega (degrees)',ylabel='Residual')
        fig.savefig(folder/'fwhm.png',dpi=180)
    finally:plt.close(fig)
    # Closed angular selection boundary transformed through the same geometry as the RSM.
    om=np.concatenate([np.linspace(low,high,150),np.linspace(high,low,150),[low]])
    tt=np.concatenate([np.full(150,center-half),np.full(150,center+half),[center-half]])
    q=geometry.transform({geometry.omega_motor:(om-geometry.omega_offset_deg)/geometry.omega_sign,
                          geometry.detector_motor:(tt-geometry.detector_offset_deg)/geometry.detector_sign},rsm.wavelength_angstrom)
    map_axes.plot(q[:,1],q[:,2],color='cyan',linestyle='--',linewidth=1,label='FWHM selection')
    map_axes.legend()
    return result
