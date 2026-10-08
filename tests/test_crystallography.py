import numpy as np
import pytest
from rsm_toolkit import *
from rsm_toolkit.crystallography import plane_indices,direction_indices


@pytest.mark.parametrize("hkl",[(1,0,0),(2,2,0),(3,0,0),(1,0,2),(0,0,2)])
def test_hexagonal_metric(hkl):
    a,c=4.136,6.716
    cell=Lattice.hexagonal(a,c)
    h,k,l=hkl
    expected=4*(h*h+h*k+k*k)/(3*a*a)+l*l/(c*c)
    assert 1/cell.d_spacing(hkl)**2==pytest.approx(expected,rel=1e-13)
    np.testing.assert_allclose(cell.direct_basis.T@cell.reciprocal_basis,2*np.pi*np.eye(3),atol=1e-14)


def test_general_metric():
    cell=Lattice(3,4,5,70,80,110)
    np.testing.assert_allclose(cell.direct_basis.T@cell.reciprocal_basis,2*np.pi*np.eye(3),atol=1e-14)
    q=cell.reciprocal_vector((2,-1,3))
    expected=(2*np.pi)**2*np.array([2,-1,3])@np.linalg.inv(cell.direct_basis.T@cell.direct_basis)@np.array([2,-1,3])
    assert q@q==pytest.approx(expected,rel=1e-13)


def test_indices_are_distinct():
    np.testing.assert_array_equal(plane_indices((1,1,-2,0)),[1,1,0])
    np.testing.assert_array_equal(direction_indices((1,1,-2,0)),[3,3,0])
    np.testing.assert_array_equal(plane_indices((12,-2,-10,4)),[12,-2,4])
    with pytest.raises(RSMError):plane_indices((1,-1,2,0))
    with pytest.raises(RSMError):direction_indices((1,-1,2,0))
    with pytest.raises(RSMError):Lattice(3,3,3).reciprocal_vector((1,0,-1,0))


def test_orientation_and_tangency():
    cell=Lattice.hexagonal(4,6)
    o=Orientation.from_surface(cell,(0,0,0,1),(1,-1,0,0))
    q=o.transform(cell.reciprocal_vector((0,0,0,2)))
    np.testing.assert_allclose(q,[0,0,4*np.pi/6],atol=1e-14)
    with pytest.raises(RSMError,match="not in the surface"):
        Orientation.from_surface(cell,(0,0,0,1),(0,0,0,1))


def test_structure_factor_not_inferred():
    unknown=Material("wurtzite",Lattice.hexagonal(4,6))
    with pytest.raises(MissingMetadataError):unknown.structure_factor((1,0,0),{"A":1})
    bcc=Material("A",Lattice(3,3,3),sites=(AtomSite("A",(0,0,0)),AtomSite("A",(.5,.5,.5))))
    assert abs(bcc.structure_factor((1,0,0),{"A":2}))<1e-14
    assert bcc.structure_factor((2,0,0),{"A":2}).real==pytest.approx(4)
    with pytest.raises(MissingMetadataError):bcc.structure_factor((2,0,0),{})


def test_phase_overlays_and_alloy():
    cell=Lattice.hexagonal(4,6)
    o=Orientation(np.eye(3))
    first=reflection_position(Material("substrate",cell),(0,0,2),o,frame="sample")
    second=reflection_position(Material("film",Lattice.hexagonal(4,7)),(0,0,2),o,frame="sample")
    assert first.q[2]!=second.q[2]
    with pytest.raises(MissingMetadataError):reflection_position(Material("unknown"),(0,0,2),o,frame="sample")
    alloy=vegard_lattice(cell,Lattice.hexagonal(3,5),.25)
    assert alloy.a==3.75 and alloy.c==5.75


@pytest.mark.parametrize("args",[(0,3,3),(3,3,3,10,10,170),(3,3,3,90,90,180)])
def test_invalid_cells(args):
    with pytest.raises(RSMError):Lattice(*args)
