"""Separate reciprocal conversion, reductions and optional profile fitting."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import numpy as np
from scipy.optimize import curve_fit

from .configuration import RSMConfiguration
from .geometry import CoplanarGeometry
from .models import Measurement, RSM, readonly
from .errors import MissingMetadataError, RSMError


def calculate_rsm(measurement: Measurement, config: RSMConfiguration) -> RSM:
    geometry=config.geometry
    if geometry is None:
        raise MissingMetadataError("Select an explicit supported geometry; brand/filename is not a geometry definition.")
    if not geometry.calibration_verified and not config.allow_provisional:
        raise MissingMetadataError("Geometry calibration is unverified. Supply calibration or explicitly set allow_provisional=True.")
    wavelength=config.wavelength_angstrom
    if wavelength is None:
        wavelength=measurement.wavelength_angstrom
    elif measurement.wavelength_angstrom is not None and not np.isclose(wavelength,measurement.wavelength_angstrom,rtol=0,atol=1e-8) and not config.wavelength_override_reason:
        raise RSMError("Wavelength override conflicts with recorded value; supply wavelength_override_reason.")
    if wavelength is None:
        raise MissingMetadataError("No used wavelength in metadata; set wavelength_angstrom explicitly.")
    motors={}
    for name in geometry.required_motors():
        if name not in measurement.motors:
            raise MissingMetadataError(f"Missing geometry motor {name!r}.")
        unit=measurement.motor_units[name]
        if unit=="degree":
            motors[name]=measurement.motors[name]
        elif unit=="radian":
            motors[name]=np.rad2deg(measurement.motors[name])
        else:
            raise RSMError(f"Geometry motor {name} has unsupported angle unit {unit!r}.")
    if isinstance(geometry,CoplanarGeometry):
        plane=measurement.metadata.get("ipa_mode")
        if plane not in (None,"Coplanar"):
            raise RSMError(f"Recorded mode {plane} conflicts with coplanar geometry.")
        om=motors[geometry.omega_motor].ravel()
        tt=motors[geometry.detector_motor].ravel()
        points=np.column_stack([om-om.mean(),tt-tt.mean()])
        if not np.isfinite(points).all() or np.linalg.matrix_rank(points,tol=1e-8)<2:
            raise RSMError("Measurement has fewer than two independent angular dimensions; it is not a 2D RSM. Use geometry.transform for a 1D scan.")
    q=np.broadcast_to(geometry.transform(motors,float(wavelength)),measurement.intensity.shape+(3,))
    notes=list(measurement.warnings)
    if not geometry.calibration_verified:
        notes.append("PROVISIONAL: nominal/user-defined coordinates, not a calibrated crystal/surface frame.")
    if isinstance(geometry,CoplanarGeometry) and any(k in measurement.motors for k in ("Chi","Phi")):
        notes.append("Fixed Chi/Phi retained in measurement metadata but not applied: their axis order/zeroes require calibration. Qx=0 is a coplanar projection, not a measured transverse component.")
    sample=None
    if config.sample is not None:
        s=config.sample
        sample={"identifier":s.identifier,"substrate":s.substrate.name if s.substrate else None,
                "film":s.film.name if s.film else None,
                "note":"Sample identities supplied by user; no lattice/orientation inferred for measured Q."}
    configuration={"geometry":geometry.describe(),"wavelength_angstrom":float(wavelength),
                   "wavelength_source":"explicit" if config.wavelength_angstrom is not None else measurement.metadata.get("wavelength_source","measurement"),
                   "wavelength_override_reason":config.wavelength_override_reason,"sample":sample,
                   "intensity_processing":"none","q_units":"angstrom^-1; 2pi convention"}
    if config.sample_settings is not None:
        configuration["sample_settings"]=config.sample_settings
    configuration["plot_settings"]=config.plot_settings
    return RSM(measurement,q,float(wavelength),geometry.frame,not geometry.calibration_verified,configuration,tuple(notes))


@dataclass(frozen=True)
class Grid:
    x_edges: np.ndarray
    y_edges: np.ndarray
    intensity: np.ndarray
    occupancy: np.ndarray
    components: tuple[int,int]
    statistic: str


def grid_rsm(rsm:RSM,bins=(400,400),*,components=(1,2),statistic="mean") -> Grid:
    """Histogram reduction, no interpolation/smoothing. Empty cells are NaN.

    mean = sum(recorded values)/number of samples, not integrated cross section.
    sum is recorded-value sum, not a Jacobian-corrected reciprocal integral.
    """
    if statistic not in ("mean","sum"):
        raise RSMError("Grid statistic must be mean or sum.")
    if len(bins)!=2 or any(not isinstance(n,(int,np.integer)) or n<2 for n in bins):
        raise RSMError("Grid needs two integer bin counts >=2.")
    if len(set(components))!=2 or any(c not in (0,1,2) for c in components):
        raise RSMError("Select two distinct Cartesian Q components.")
    x,y=rsm.q[...,components[0]].ravel(),rsm.q[...,components[1]].ravel()
    signal=rsm.intensity.ravel()
    keep=np.isfinite(x)&np.isfinite(y)&np.isfinite(signal)
    if not np.any(keep) or np.ptp(x[keep])==0 or np.ptp(y[keep])==0:
        raise RSMError("Selected projection has no finite 2D extent.")
    count,xe,ye=np.histogram2d(x[keep],y[keep],bins=bins)
    total,_,_=np.histogram2d(x[keep],y[keep],bins=(xe,ye),weights=signal[keep])
    out=np.full(total.shape,np.nan)
    np.divide(total,count,out=out,where=count>0) if statistic=="mean" else np.copyto(out,total,where=count>0)
    return Grid(readonly(xe),readonly(ye),readonly(out.T),readonly(count.T),components,statistic)


def count_rate(measurement:Measurement) -> np.ndarray:
    """Explicit derived rate; never modifies recorded values or applies absorber."""
    if measurement.counting_time_s is None:
        raise MissingMetadataError("Count rate requires recorded/supplied counting time.")
    t=measurement.counting_time_s
    if not np.isfinite(t).all() or np.any(t<=0):
        raise RSMError("Count rate requires positive finite counting times.")
    if measurement.intensity_unit != "recorded counts":
        raise RSMError("Count-rate conversion requires intensity_unit='recorded counts'.")
    return measurement.intensity/t


def brightest_point(rsm:RSM) -> dict[str,Any]:
    """Brightest measured bin, not a subpixel fit or a phase identification."""
    valid=np.isfinite(rsm.intensity)
    if not valid.any() or np.max(rsm.intensity[valid])<=0:
        raise RSMError("No positive finite measured intensity for peak reporting.")
    flat=int(np.argmax(np.where(valid,rsm.intensity,-np.inf)))
    index=np.unravel_index(flat,rsm.intensity.shape)
    return {"method":"brightest measured bin; no phase assignment","index":list(map(int,index)),
            "q_angstrom_inverse":rsm.q[index].tolist(),"intensity":float(rsm.intensity[index]),
            "intensity_unit":rsm.measurement.intensity_unit,
            "motor_positions":{k:float(v[index]) for k,v in rsm.measurement.motors.items()},
            "frame":rsm.frame,"provisional":rsm.provisional}


def angular_profile(measurement:Measurement,*,scan_motor:str,band_motor:str,center:float,half_width:float):
    """Unweighted mean per exact recorded scan coordinate in an inclusive band.

    center/half_width have band_motor's recorded units. Return x, mean, N;
    no background, spike deletion, integration or implicit normalization.
    """
    if not np.isfinite([center,half_width]).all() or half_width<=0:
        raise RSMError("Profile center/half width must be finite with positive half width.")
    try:
        x,b=measurement.motors[scan_motor],measurement.motors[band_motor]
    except KeyError as exc:
        raise MissingMetadataError(f"Missing profile motor {exc.args[0]}.") from exc
    keep=(np.abs(b-center)<=half_width)&np.isfinite(x)&np.isfinite(measurement.intensity)
    if not keep.any():
        raise RSMError("Profile band contains no finite samples.")
    unique,inverse=np.unique(x[keep],return_inverse=True)
    count=np.bincount(inverse)
    return unique,np.bincount(inverse,weights=measurement.intensity[keep])/count,count


def fit_gaussian_profile(x,y,*,sigma=None):
    """Single Gaussian + constant background with explicit optional errors.

    No preprocessing or selection is hidden. Covariance is a local least-squares
    approximation, not verified confidence coverage. Width is in x units only.
    """
    x,y=np.asarray(x,dtype=float),np.asarray(y,dtype=float)
    if x.ndim!=1 or y.shape!=x.shape or len(x)<5 or not np.isfinite(x).all() or not np.isfinite(y).all() or np.ptp(x)==0 or np.ptp(y)==0:
        raise RSMError("Fit requires >=5 finite varying paired samples.")
    order=np.argsort(x)
    x,y=x[order],y[order]
    if np.any(np.diff(x)<=0):
        raise RSMError("Fit x coordinates must be unique.")
    if sigma is not None:
        sigma=np.asarray(sigma,dtype=float)
        if sigma.shape!=y.shape or not np.isfinite(sigma).all() or np.any(sigma<=0):
            raise RSMError("Fit sigma must match data and be positive finite.")
        sigma=sigma[order]
    def model(x,amplitude,center,width,background):
        return background+amplitude*np.exp(-4*np.log(2)*((x-center)/width)**2)
    p0=[np.ptp(y),x[np.argmax(y)],np.ptp(x)/5,np.min(y)]
    params,cov=curve_fit(model,x,y,p0=p0,sigma=sigma,absolute_sigma=sigma is not None,
                         bounds=([0,x.min(),np.finfo(float).eps,-np.inf],[np.inf,x.max(),np.inf,np.inf]),maxfev=10000)
    return {"amplitude":params[0],"center":params[1],"fwhm":params[2],"background":params[3],
            "covariance":cov,"residuals":y-model(x,*params),"x":x,"fitted":model(x,*params),
            "note":"Empirical width in x units; no strain/mosaicity/size inference."}
