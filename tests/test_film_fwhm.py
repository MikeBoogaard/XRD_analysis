import json
from dataclasses import replace
import numpy as np
import pytest
from rsm_toolkit.film_fwhm import pseudo_voigt,fit_profile,analyze
from rsm_toolkit.errors import RSMError
from rsm_toolkit.gui_workflow import defaults,execute,save_settings,load_settings,fwhm_selection
from rsm_toolkit.geometry import CoplanarGeometry
from rsm_toolkit.models import Measurement,Provenance
from rsm_toolkit.processing import calculate_rsm
from rsm_toolkit.configuration import RSMConfiguration
import matplotlib.pyplot as plt

@pytest.mark.parametrize('eta',[0,.35,1])
def test_width_and_recovery(eta):
    x=np.linspace(-3,3,401)
    y=pseudo_voigt(x,100,.2,.7,eta,7)
    assert pseudo_voigt(.2+.7/2,100,.2,.7,eta,7)==pytest.approx(57)
    f=fit_profile(x,y)
    assert f['fwhm_deg']==pytest.approx(.7,abs=1e-4)
    assert f['background']==pytest.approx(7,abs=.002)

@pytest.mark.parametrize('x,y',[(np.arange(10),np.ones(10)),(np.arange(4),np.arange(4)),
                              (np.ones(10),np.arange(10))])
def test_invalid(x,y):
    with pytest.raises(RSMError):fit_profile(x,y)


def test_truncated_peak():
    x=np.linspace(-.1,.1,50)
    with pytest.raises(RSMError,match='half-height'):
        fit_profile(x,pseudo_voigt(x,100,0,1,.5,2))


def test_band_export_with_offsets(tmp_path):
    om,tt=np.meshgrid(np.linspace(15,25,101),np.linspace(39,41,21),indexing='ij')
    signal=pseudo_voigt(om,100,20,1,.3,4)+np.where(tt<39.5,1000,0)
    m=Measurement(signal,{'Theta':om,'TwoTheta':tt},{'Theta':'degree','TwoTheta':'degree'},Provenance('synthetic','test','test','test'),wavelength_angstrom=1.54)
    geometry=CoplanarGeometry(omega_offset_deg=2,detector_offset_deg=3)
    r=calculate_rsm(m,RSMConfiguration(geometry))
    fig,ax=plt.subplots()
    try: result=analyze(r,geometry,[43,.2,18,26],tmp_path,ax)
    finally:plt.close(fig)
    assert result['center_deg']==pytest.approx(22,abs=1e-5)
    assert result['fwhm_deg']==pytest.approx(1,abs=1e-5)
    assert (tmp_path/'fwhm.png').is_file()
    assert len(json.loads((tmp_path/'fwhm.json').read_text())['residuals'])>8
    np.testing.assert_array_equal(m.intensity,signal)


def test_settings(tmp_path):
    f=defaults();f.update(fwhm=True,fwhm_center='43',fwhm_min='18',fwhm_max='26')
    p=tmp_path/'settings.json';save_settings(p,f)
    assert load_settings(p)==f
    assert fwhm_selection(f)==[43,.2,18,26]
    f['fwhm_min']='27'
    with pytest.raises(RSMError):fwhm_selection(f)

@pytest.mark.parametrize('center,success',[('45',True),('120',False)])
def test_actual_raw_workflow(tmp_path,center,success):
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    f=defaults();f.update(file=str(root/'example_data/RSM(11-20)along0001.raw'),output=str(tmp_path),
        fwhm=True,fwhm_center=center,fwhm_min='19',fwhm_max='24')
    folder=execute(f)
    assert (folder/'map.png').is_file() and (folder/'map.npz').is_file()
    if success:
        result=json.loads((folder/'fwhm.json').read_text())
        assert 0<result['fwhm_deg']<5
        assert (folder/'fwhm.csv').is_file()
    else:assert (folder/'FWHM_FAILED.txt').is_file()

@pytest.mark.parametrize('asymmetric',[False,True])
def test_theoretical_fill_roundtrip(asymmetric):
    from rsm_toolkit.gui_workflow import preset,theoretical_fwhm_fields,build_configuration
    from rsm_toolkit.overlays import phase_from_config
    from rsm_toolkit.crystallography import reflection_position
    f=preset(asymmetric);f.update(wavelength='1.5406',fwhm_window='1.5',overlays=False)
    original=f.copy(); v=theoretical_fwhm_fields(f)
    assert f==original
    omega=(float(v['fwhm_min'])+float(v['fwhm_max']))/2
    tt=float(v['fwhm_center'])
    assert float(v['fwhm_max'])-float(v['fwhm_min'])==pytest.approx(3)
    config=build_configuration({**f,'overlays':True}); raw=config['sample']['film']
    material,orientation=phase_from_config(raw)
    target=np.asarray(config['sample']['frame_alignment']['sample_to_map'])@reflection_position(material,raw['reflections'][0],orientation,frame='test').q
    actual=CoplanarGeometry().transform({'Theta':omega,'TwoTheta':tt},1.5406)
    np.testing.assert_allclose(actual,target,atol=1e-8)
    assert tt==pytest.approx(np.degrees(2*np.arcsin(1.5406/(2*material.lattice.d_spacing(raw['reflections'][0])))))
    f.update(omega_offset='1',detector_offset='2')
    assert theoretical_fwhm_fields(f)==v  # Inputs are already corrected physical angles.


def test_theoretical_fill_errors_and_composition():
    from rsm_toolkit.gui_workflow import preset,theoretical_fwhm_fields
    f=preset(); f['wavelength']='1.5406'
    a=theoretical_fwhm_fields(f); f['zinc']='70'
    assert float(theoretical_fwhm_fields(f)['fwhm_center'])>float(a['fwhm_center'])
    for change in ({'film':'None'},{'wavelength':'100'},{'fwhm_window':'0'},{'zinc':''},{'inplane':''}):
        with pytest.raises(RSMError):theoretical_fwhm_fields({**f,**change})


def test_theoretical_fill_file_wavelength():
    from pathlib import Path
    from rsm_toolkit.gui_workflow import preset,theoretical_fwhm_fields
    from rsm_toolkit import load_xrd
    f=preset(); f['file']=str(Path(__file__).resolve().parents[1]/'example_data/RSM(11-20)along0001.raw')
    assert theoretical_fwhm_fields(f)==theoretical_fwhm_fields({**f,'wavelength':str(load_xrd(f['file']).wavelength_angstrom)})

@pytest.mark.parametrize('radians',[False,True])
def test_measured_search_local_and_offsets(monkeypatch,tmp_path,radians):
    from rsm_toolkit.gui_workflow import preset,theoretical_fwhm_fields,measured_fwhm_fields
    f=preset(); f.update(wavelength='1.5406',omega_offset='1',detector_offset='2')
    theory=theoretical_fwhm_fields(f); t=float(theory['fwhm_center']); o=(float(theory['fwhm_min'])+float(theory['fwhm_max']))/2
    om,tt=np.meshgrid(o+np.linspace(-2,2,81),t+np.linspace(-1,1,81),indexing='ij')
    signal=np.ones(om.shape);signal[44,44]=100;signal[0,0]=10000;signal[40,40]=np.nan
    motors={'Theta':om-1,'TwoTheta':tt-2}
    if radians:motors={k:np.deg2rad(v) for k,v in motors.items()}
    m=Measurement(signal,motors,{k:'radian' if radians else 'degree' for k in motors},Provenance('test','test','test','test'),wavelength_angstrom=1.5406)
    path=tmp_path/'scan.raw';path.touch();f['file']=str(path)
    monkeypatch.setattr('rsm_toolkit.load_xrd',lambda path:m)
    fields,report=measured_fwhm_fields(f)
    assert float(fields['fwhm_center'])==pytest.approx(t+.1)
    assert (float(fields['fwhm_min'])+float(fields['fwhm_max']))/2==pytest.approx(o+.2)
    assert 'Shift from theory' in report
    assert f['fwhm_center']==''
    monkeypatch.setattr('rsm_toolkit.load_xrd',lambda path:replace(m,intensity=np.zeros_like(signal)))
    with pytest.raises(RSMError,match='No positive'):measured_fwhm_fields(f)
    with pytest.raises(RSMError,match='positive'):measured_fwhm_fields({**f,'fwhm_search_tt':'0'})


def test_measured_search_actual():
    from pathlib import Path
    from rsm_toolkit.gui_workflow import preset,measured_fwhm_fields,theoretical_fwhm_fields
    f=preset();f['file']=str(Path(__file__).resolve().parents[1]/'example_data/RSM(11-20)along0001.raw')
    fields,report=measured_fwhm_fields(f);theory=theoretical_fwhm_fields(f)
    assert abs(float(fields['fwhm_center'])-float(theory['fwhm_center']))<=.5
    assert abs(float(fields['fwhm_min'])-float(theory['fwhm_min']))<=1
