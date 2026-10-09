import numpy as np
import pytest
from dataclasses import replace
from rsm_toolkit import *
from rsm_toolkit.geometry import validate_rotation


def test_symmetric_magnitude_and_scale():
    g=CoplanarGeometry()
    theta=np.array([0.,10.,35.,70.])
    q=g.transform({"Theta":theta,"TwoTheta":2*theta},1.54)
    np.testing.assert_allclose(q[:,:2],0,atol=1e-14)
    np.testing.assert_allclose(q[:,2],4*np.pi/1.54*np.sin(np.deg2rad(theta)),atol=1e-14)
    np.testing.assert_allclose(g.transform({"Theta":theta,"TwoTheta":2*theta},3.08),q/2,atol=1e-14)


def test_asymmetric_sign_and_rocking_arc():
    omega=np.array([10.,20.,30.])
    q=CoplanarGeometry().transform({"Theta":omega,"TwoTheta":40},1)
    np.testing.assert_allclose(np.linalg.norm(q,axis=1),4*np.pi*np.sin(np.deg2rad(20)),atol=1e-14)
    assert q[0,1]<0 and q[2,1]>0
    np.testing.assert_allclose(q[0,1],-q[2,1],atol=1e-14)
    np.testing.assert_allclose(q[0,2],q[2,2],atol=1e-14)


def test_rotations_and_order():
    rx=rotation_matrix((1,0,0),90)
    rz=rotation_matrix((0,0,1),90)
    np.testing.assert_allclose(rx@np.array([0,1,0]),[0,0,1],atol=1e-15)
    np.testing.assert_allclose(rx.T@rx,np.eye(3),atol=1e-15)
    assert np.linalg.det(rx)==pytest.approx(1)
    assert not np.allclose(rx@rz,rz@rx)
    with pytest.raises(RSMError):validate_rotation(np.diag([1,1,-1]))
    with pytest.raises(RSMError):rotation_matrix((0,0,0),10)


def test_vector_coplanar_independent_construction():
    vector=VectorGeometry((0,1,0),(0,1,0),(MotorRotation("om",(1,0,0)),),(MotorRotation("tt",(1,0,0)),))
    om,tt=np.meshgrid(np.arange(5.,50.,5),np.arange(10.,100.,10))
    a=vector.transform({"om":om,"tt":tt},1.54)
    b=CoplanarGeometry().transform({"Theta":om,"TwoTheta":tt},1.54)
    np.testing.assert_allclose(a,b,atol=4e-15,rtol=1e-14)


def test_vector_non_coplanar():
    # Detector rotated about z sends y -> -x. No sample rotation.
    g=VectorGeometry((0,1,0),(0,1,0),(),(MotorRotation("d",(0,0,1)),))
    np.testing.assert_allclose(g.transform({"d":90},2*np.pi),[-1,-1,0],atol=1e-15)
    ordered=VectorGeometry((0,1,0),(0,1,0),(),(MotorRotation("z",(0,0,1)),MotorRotation("y",(0,1,0))))
    np.testing.assert_allclose(ordered.transform({"z":90,"y":90},2*np.pi),[0,-1,1],atol=1e-15)


def test_offsets_and_signs():
    a=CoplanarGeometry(omega_sign=-1,omega_offset_deg=2,detector_offset_deg=1)
    np.testing.assert_allclose(a.transform({"Theta":-18,"TwoTheta":39},1),CoplanarGeometry().transform({"Theta":20,"TwoTheta":40},1))


def test_configuration_failures(measurement):
    with pytest.raises(MissingMetadataError,match="geometry"): calculate_rsm(measurement,RSMConfiguration())
    assert np.isfinite(calculate_rsm(measurement,RSMConfiguration(CoplanarGeometry())).q).all()
    with pytest.raises(MissingMetadataError):CoplanarGeometry(calibration_verified=True)
    with pytest.raises(MissingMetadataError,match="wavelength"):
        calculate_rsm(replace(measurement,wavelength_angstrom=None),RSMConfiguration(CoplanarGeometry(),allow_provisional=True))
    with pytest.raises(RSMError,match="override"):
        calculate_rsm(measurement,RSMConfiguration(CoplanarGeometry(),wavelength_angstrom=2,allow_provisional=True))


def test_radian_units_and_material_independence(measurement):
    cfg=RSMConfiguration(CoplanarGeometry(),allow_provisional=True)
    expected=calculate_rsm(measurement,cfg)
    radians=replace(measurement,motors={k:np.deg2rad(v) for k,v in measurement.motors.items()},motor_units={k:"radian" for k in measurement.motors})
    actual=calculate_rsm(radians,replace(cfg,sample=Sample(Material("unknown substrate"),Material("unknown film"))))
    np.testing.assert_allclose(actual.q,expected.q,atol=1e-14)
    with pytest.raises(RSMError,match="unit"):
        calculate_rsm(replace(measurement,motor_units={k:"mm" for k in measurement.motors}),cfg)


def test_one_dimensional_scan_rejected(measurement):
    m=replace(measurement,motors={"Theta":measurement.motors["TwoTheta"]/2,"TwoTheta":measurement.motors["TwoTheta"]})
    with pytest.raises(RSMError,match="not a 2D RSM"):
        calculate_rsm(m,RSMConfiguration(CoplanarGeometry(),allow_provisional=True))


def test_energy():
    assert wavelength_from_energy(8047.8)==pytest.approx(1.5405974108849654,abs=1e-14)
    with pytest.raises(RSMError):wavelength_from_energy(0)


def test_xrayutilities_independent_reference():
    xu=pytest.importorskip("xrayutilities")
    conversion=xu.experiment.QConversion(["x+"],["x+"],[0,1,0],wl=1.5406)
    om=np.array([0.,18.145,20.,24.5])
    tt=np.array([0.,96.33080998796127,40.,112.38127673366336])
    q=np.stack(conversion.point(om,tt),axis=-1)
    np.testing.assert_allclose(q,CoplanarGeometry().transform({"Theta":om,"TwoTheta":tt},1.5406),rtol=1e-12,atol=1e-12)
