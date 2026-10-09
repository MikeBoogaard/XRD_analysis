"""Check the local diagnostic estimator against a known synthetic peak."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest


def test_correlated_gaussian_center_recovery():
    path=Path(__file__).resolve().parents[1]/'examples/check_asymmetric_alignment.py'
    spec=importlib.util.spec_from_file_location('alignment_diagnostic',path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    om,tt=np.meshgrid(np.arange(44.4,45.2,.04),np.arange(69,69.7,.014),indexing='ij')
    u,v=(om-44.783)/.025,(tt-69.329)/.03
    intensity=4+1600*np.exp(-(u*u-.8*u*v+v*v)/(2*(1-.4**2)))
    m=SimpleNamespace(motors={'Theta':om,'TwoTheta':tt},intensity=intensity)
    fit=module.fit_peak(m,.3)
    assert fit['omega_deg']==pytest.approx(44.783,abs=1e-7)
    assert fit['two_theta_deg']==pytest.approx(69.329,abs=1e-7)
