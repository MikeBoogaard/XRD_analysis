"""Lattice metrics and explicit crystal-to-sample orientations.

No space-group selection rules are inferred from a material's display name.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping
import numpy as np
from .errors import RSMError, MissingMetadataError
from .geometry import validate_rotation


def plane_indices(indices) -> np.ndarray:
    h=np.asarray(indices,dtype=float)
    if h.shape not in ((3,),(4,)) or not np.isfinite(h).all() or not np.all(h==np.round(h)):
        raise RSMError("Miller indices require three or four finite integers.")
    if h.size==4:
        if h[2] != -h[0]-h[1]:
            raise RSMError("Miller-Bravais planes require i=-(h+k).")
        h=h[[0,1,3]]
    if not np.any(h):
        raise RSMError("The zero reflection has no plane normal or d spacing.")
    return h


def direction_indices(indices) -> np.ndarray:
    u=np.asarray(indices,dtype=float)
    if u.shape not in ((3,),(4,)) or not np.isfinite(u).all() or not np.all(u==np.round(u)):
        raise RSMError("Direction indices require three or four finite integers.")
    if u.size==4:
        if u[2] != -u[0]-u[1]:
            raise RSMError("Four-index directions require t=-(u+v).")
        u=np.array([2*u[0]+u[1],u[0]+2*u[1],u[3]])
    if not np.any(u):
        raise RSMError("Zero direction is undefined.")
    return u


@dataclass(frozen=True)
class Lattice:
    a: float
    b: float
    c: float
    alpha: float = 90.0
    beta: float = 90.0
    gamma: float = 90.0

    def __post_init__(self):
        vals=[self.a,self.b,self.c,self.alpha,self.beta,self.gamma]
        if not np.isfinite(vals).all() or min(vals[:3])<=0 or not all(0<x<180 for x in vals[3:]):
            raise RSMError("Lattice lengths must be positive angstrom and angles in (0,180) degrees.")
        if np.linalg.det(self.direct_basis)<=1e-12:
            raise RSMError("Degenerate lattice metric.")

    @classmethod
    def hexagonal(cls,a:float,c:float):
        return cls(a,a,c,90,90,120)

    @property
    def direct_basis(self):
        al,be,ga=np.deg2rad([self.alpha,self.beta,self.gamma])
        cy=(np.cos(al)-np.cos(be)*np.cos(ga))/np.sin(ga)
        cz2=1-np.cos(be)**2-cy**2
        if cz2<=0:
            raise RSMError("Cell angles do not define a positive-volume lattice.")
        return np.array([[self.a,self.b*np.cos(ga),self.c*np.cos(be)],
                         [0,self.b*np.sin(ga),self.c*cy],[0,0,self.c*np.sqrt(cz2)]])

    @property
    def reciprocal_basis(self):
        return 2*np.pi*np.linalg.inv(self.direct_basis).T

    @property
    def is_hexagonal(self):
        return np.allclose([self.b,self.alpha,self.beta,self.gamma],[self.a,90,90,120],atol=1e-8,rtol=0)

    def reciprocal_vector(self,indices):
        if len(indices)==4 and not self.is_hexagonal:
            raise RSMError("Four-index notation requires a hexagonal metric.")
        return self.reciprocal_basis@plane_indices(indices)

    def direct_direction(self,indices):
        if len(indices)==4 and not self.is_hexagonal:
            raise RSMError("Four-index notation requires a hexagonal metric.")
        return self.direct_basis@direction_indices(indices)

    def d_spacing(self,indices):
        return 2*np.pi/np.linalg.norm(self.reciprocal_vector(indices))


@dataclass(frozen=True)
class Orientation:
    crystal_to_sample: np.ndarray

    def __post_init__(self):
        r=validate_rotation(self.crystal_to_sample).copy()
        r.setflags(write=False)
        object.__setattr__(self,"crystal_to_sample",r)

    @classmethod
    def from_surface(cls,lattice:Lattice,normal_plane,in_plane_direction):
        z=lattice.reciprocal_vector(normal_plane)
        z=z/np.linalg.norm(z)
        y=lattice.direct_direction(in_plane_direction)
        y=y/np.linalg.norm(y)
        if abs(np.dot(y,z))>1e-8:
            raise RSMError("The supplied direct direction is not in the surface plane; no silent projection is performed.")
        x=np.cross(y,z)
        return cls(np.stack([x,y,z]))

    def transform(self,vector):
        return np.einsum('ij,...j->...i',self.crystal_to_sample,vector)


@dataclass(frozen=True)
class AtomSite:
    element: str
    fractional_position: tuple[float,float,float]
    occupancy: float = 1.0

    def __post_init__(self):
        if np.asarray(self.fractional_position).shape!=(3,) or not np.isfinite(self.fractional_position).all() or not 0<=self.occupancy<=1:
            raise RSMError("Invalid fractional site or occupancy.")


@dataclass(frozen=True)
class Material:
    name: str
    lattice: Lattice | None = None
    crystal_structure: str | None = None
    composition: Mapping[str,float] | None = None
    sites: tuple[AtomSite,...] = ()
    reference: str | None = None

    def structure_factor(self,indices,scattering_factors:Mapping[str,complex]):
        """Explicit full-cell site sum. Factors must be supplied for this Q/energy.

        No symmetry expansion, thermal factors or anomalous terms are invented.
        A zero can demonstrate cancellation for these sites/factors, but a
        nonzero amplitude alone does not guarantee experimental observability.
        """
        if not self.sites:
            raise MissingMetadataError("Structure factor requires explicit full-cell atomic sites.")
        if self.lattice is None:
            raise MissingMetadataError("Structure factor requires a lattice/indexing convention.")
        self.lattice.reciprocal_vector(indices)
        h=plane_indices(indices)
        try:
            return sum(s.occupancy*scattering_factors[s.element]*np.exp(2j*np.pi*np.dot(h,s.fractional_position)) for s in self.sites)
        except KeyError as exc:
            raise MissingMetadataError(f"Missing scattering factor for {exc.args[0]}.") from exc


@dataclass(frozen=True)
class Sample:
    substrate: Material | None = None
    film: Material | None = None
    substrate_orientation: Orientation | None = None
    film_orientation: Orientation | None = None
    identifier: str | None = None


@dataclass(frozen=True)
class Reflection:
    label: str
    q: np.ndarray
    frame: str
    status: str = "geometric vector; structure-factor allowance unknown"


def reflection_position(material:Material,indices,orientation:Orientation,*,frame:str) -> Reflection:
    if material.lattice is None:
        raise MissingMetadataError(f"{material.name} lattice is unknown; measured Q does not require it, overlays do.")
    return Reflection(f"{material.name} {tuple(indices)}",orientation.transform(material.lattice.reciprocal_vector(indices)),frame)


def vegard_lattice(first:Lattice,second:Lattice,fraction_second:float) -> Lattice:
    """Explicit approximate linear interpolation of hexagonal a,c only."""
    if not first.is_hexagonal or not second.is_hexagonal or not 0<=fraction_second<=1:
        raise RSMError("Vegard model requires hexagonal end members and fraction in [0,1].")
    x=fraction_second
    return Lattice.hexagonal((1-x)*first.a+x*second.a,(1-x)*first.c+x*second.c)
