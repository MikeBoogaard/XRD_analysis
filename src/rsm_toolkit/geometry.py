"""Explicit elastic kinematics; no implicit Bruker motor convention."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Mapping
import numpy as np
from .errors import RSMError, MissingMetadataError

HC_EV_ANGSTROM = 12398.419843320026


def wavelength_from_energy(energy_ev: float) -> float:
    if not np.isfinite(energy_ev) or energy_ev <= 0:
        raise RSMError("Photon energy must be positive finite eV.")
    return HC_EV_ANGSTROM / energy_ev


def validate_rotation(matrix) -> np.ndarray:
    r = np.asarray(matrix,dtype=float)
    if r.shape != (3,3) or not np.isfinite(r).all() or not np.allclose(r.T@r,np.eye(3),atol=1e-10,rtol=0) or not np.isclose(np.linalg.det(r),1,atol=1e-10,rtol=0):
        raise RSMError("Rotation must be a finite right-handed orthonormal 3x3 matrix.")
    return r


def rotation_matrix(axis, angle_deg) -> np.ndarray:
    """Active right-handed Rodrigues rotation, broadcasting angle arrays."""
    a = np.asarray(axis,dtype=float)
    if a.shape != (3,) or not np.isfinite(a).all() or np.linalg.norm(a)==0:
        raise RSMError("Rotation axis must be a nonzero finite Cartesian 3-vector.")
    angles = np.asarray(angle_deg,dtype=float)
    if not np.isfinite(angles).all():
        raise RSMError("Rotation angles must be finite degrees.")
    a = a/np.linalg.norm(a)
    x,y,z = a
    cross = np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
    t = np.deg2rad(angles)[...,None,None]
    return np.cos(t)*np.eye(3)+(1-np.cos(t))*np.outer(a,a)+np.sin(t)*cross


def _wave(wavelength):
    if not np.isfinite(wavelength) or wavelength<=0:
        raise RSMError("Wavelength must be positive finite angstrom.")
    return 2*np.pi/wavelength


@dataclass(frozen=True)
class CoplanarGeometry:
    """Nominal x transverse, y beam projection, z nominal outward normal.

    ki=k(0,cos(omega),-sin(omega)); kf=k(0,cos(2theta-omega),
    sin(2theta-omega)). Corrections: corrected = sign*recorded + offset.
    Fixed Chi/Phi are NOT silently interpreted as sample-frame rotations.
    """
    omega_motor: str = "Theta"
    detector_motor: str = "TwoTheta"
    omega_sign: int = 1
    detector_sign: int = 1
    omega_offset_deg: float = 0.0
    detector_offset_deg: float = 0.0
    frame: str = "nominal coplanar"
    calibration_verified: bool = False
    calibration_reference: str | None = None

    def __post_init__(self):
        if self.omega_sign not in (-1,1) or self.detector_sign not in (-1,1):
            raise RSMError("Motor signs must be +1 or -1.")
        if not np.isfinite([self.omega_offset_deg,self.detector_offset_deg]).all():
            raise RSMError("Angular offsets must be finite degrees.")
        if self.calibration_verified and not self.calibration_reference:
            raise MissingMetadataError("Verified geometry requires a calibration reference.")

    def transform(self, motors: Mapping[str,np.ndarray], wavelength: float) -> np.ndarray:
        try:
            om = self.omega_sign*np.asarray(motors[self.omega_motor])+self.omega_offset_deg
            tt = self.detector_sign*np.asarray(motors[self.detector_motor])+self.detector_offset_deg
        except KeyError as exc:
            raise MissingMetadataError(f"Missing geometry motor {exc.args[0]}.") from exc
        om,tt = np.broadcast_arrays(om,tt)
        if not np.isfinite(om).all() or not np.isfinite(tt).all():
            raise RSMError("Nonfinite diffraction angles cannot be mapped.")
        if np.any(np.abs(tt)>180):
            raise RSMError("Coplanar scattering angle must be within [-180,180] degrees.")
        omega, exit_angle = np.deg2rad(om), np.deg2rad(tt-om)
        k = _wave(wavelength)
        return np.stack([np.zeros_like(om),k*(np.cos(exit_angle)-np.cos(omega)),
                         k*(np.sin(exit_angle)+np.sin(omega))],axis=-1)

    def required_motors(self):
        return (self.omega_motor,self.detector_motor)

    def describe(self):
        return {"type":"coplanar",**asdict(self)}


@dataclass(frozen=True)
class MotorRotation:
    motor: str
    axis: tuple[float,float,float]
    sign: int = 1
    offset_deg: float = 0.0

    def __post_init__(self):
        rotation_matrix(self.axis,0)
        if self.sign not in (-1,1) or not np.isfinite(self.offset_deg):
            raise RSMError("Motor rotation requires sign +/-1 and finite offset.")


@dataclass(frozen=True)
class VectorGeometry:
    """Explicit extrinsic laboratory-axis rotations in application order.

    Each next R left-multiplies the previous orientation. For actual nested
    goniometers the caller must provide the physically equivalent extrinsic
    sequence; no instrument is selected from a brand name. q_sample=R_s^T q_lab.
    """
    incident_direction: tuple[float,float,float]
    detector_zero_direction: tuple[float,float,float]
    sample_rotations: tuple[MotorRotation,...]
    detector_rotations: tuple[MotorRotation,...]
    frame: str = "user-defined sample"
    calibration_verified: bool = False
    calibration_reference: str | None = None

    def __post_init__(self):
        for v in (self.incident_direction,self.detector_zero_direction):
            a=np.asarray(v,dtype=float)
            if a.shape!=(3,) or not np.isfinite(a).all() or not np.isclose(np.linalg.norm(a),1,atol=1e-12):
                raise RSMError("Beam directions must be Cartesian unit vectors.")
        if self.calibration_verified and not self.calibration_reference:
            raise MissingMetadataError("Verified geometry requires a calibration reference.")

    def required_motors(self):
        return tuple(dict.fromkeys(r.motor for r in self.sample_rotations+self.detector_rotations))

    def transform(self,motors,wavelength):
        def chain(rotations):
            result=np.eye(3)
            for r in rotations:
                if r.motor not in motors:
                    raise MissingMetadataError(f"Missing rotation motor {r.motor}.")
                result=rotation_matrix(r.axis,r.sign*np.asarray(motors[r.motor])+r.offset_deg)@result
            return result
        rs,rd=chain(self.sample_rotations),chain(self.detector_rotations)
        outgoing=np.einsum('...ij,j->...i',rd,self.detector_zero_direction)
        qlab=_wave(wavelength)*(outgoing-np.asarray(self.incident_direction))
        return np.einsum('...ji,...j->...i',rs,qlab)

    def describe(self):
        return {"type":"vector",**asdict(self)}
