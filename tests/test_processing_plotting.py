from dataclasses import replace
import numpy as np
import matplotlib.pyplot as plt
import pytest
from rsm_toolkit import *


def test_rate_and_profile(measurement):
    original=measurement.intensity.copy()
    np.testing.assert_array_equal(count_rate(measurement),original/2)
    np.testing.assert_array_equal(measurement.intensity,original)
    with pytest.raises(RSMError):count_rate(replace(measurement,counting_time_s=0))
    with pytest.raises(MissingMetadataError):count_rate(replace(measurement,counting_time_s=None))
    x,y,n=angular_profile(measurement,scan_motor="Theta",band_motor="TwoTheta",center=40,half_width=.41)
    assert len(x)==15 and np.all(n==3)
    expected=measurement.intensity[:,4:7].mean(axis=1)
    np.testing.assert_allclose(y,expected)
    with pytest.raises(RSMError,match="no finite samples"):
        angular_profile(measurement,scan_motor="Theta",band_motor="TwoTheta",center=90,half_width=.1)


def test_grid_constant_and_coverage(measurement):
    constant=replace(measurement,intensity=np.full(measurement.intensity.shape,7.))
    r=calculate_rsm(constant,RSMConfiguration(CoplanarGeometry(),allow_provisional=True))
    g=grid_rsm(r,(40,40))
    assert np.isnan(g.intensity).any()
    assert np.all(g.intensity[g.occupancy>0]==7)
    assert np.sum(g.occupancy)==constant.intensity.size
    np.testing.assert_allclose(np.nansum(grid_rsm(r,(40,40),statistic="sum").intensity),7*constant.intensity.size)
    with pytest.raises(RSMError):grid_rsm(r,components=(0,2))


def test_peak_report(rsm):
    b=brightest_point(rsm)
    assert b["index"]==[7,5]
    assert b["provisional"]
    assert "no phase" in b["method"]


def test_fit_with_baseline():
    x=np.linspace(-3,3,401)
    y=7+100*np.exp(-4*np.log(2)*((x-.2)/.7)**2)
    result=fit_gaussian_profile(x,y)
    assert result["fwhm"]==pytest.approx(.7,abs=1e-8)
    assert result["background"]==pytest.approx(7,abs=1e-8)
    assert result["center"]==pytest.approx(.2,abs=1e-8)
    with pytest.raises(RSMError):fit_gaussian_profile(x,np.ones_like(x))


@pytest.mark.parametrize("mode",["points","grid"])
@pytest.mark.parametrize("scale",["linear","log"])
def test_plot_dimensions_labels_and_preservation(rsm,mode,scale,tmp_path):
    original=rsm.intensity.copy()
    fig,ax=plot_rsm(rsm,mode=mode,intensity_scale=scale,bins=(20,20))
    assert "Q_y" in ax.get_xlabel() and "Q_z" in ax.get_ylabel()
    assert "-1" in ax.get_xlabel()
    assert any("PROVISIONAL" in t.get_text() for t in ax.texts)
    for suffix in ("png","pdf","svg"):
        target=tmp_path/f"figure.{suffix}"
        save_figure(fig,target,dpi=80)
        assert target.stat().st_size>1000
    plt.close(fig)
    np.testing.assert_array_equal(rsm.intensity,original)


def test_log_mask_and_no_silent_clipping(rsm):
    values=rsm.intensity.copy()
    values[0,0]=0;values[0,1]=-5
    m=replace(rsm.measurement,intensity=values)
    r=replace(rsm,measurement=m)
    with pytest.warns(UserWarning,match="2 nonpositive"):
        fig,ax=plot_rsm(r)
    assert r.intensity[0,1]==-5
    plt.close(fig)
    with pytest.raises(RSMError,match="No valid"):
        plot_rsm(replace(rsm,measurement=replace(rsm.measurement,intensity=np.zeros_like(values))))
    plt.close("all")


def test_overlay_frame_and_offplane(rsm):
    wrong=Reflection("wrong",np.array([0.,0.,2.]),"different")
    with pytest.raises(RSMError,match="frame"):plot_rsm(rsm,reflections=[wrong])
    off=Reflection("offplane",np.array([1.,0.,2.]),rsm.frame)
    with pytest.warns(UserWarning,match="off-plane"):
        fig,ax=plot_rsm(rsm,reflections=[off])
    assert len(ax.lines)==0
    plt.close("all")
