import json
from pathlib import Path
import subprocess
import sys
import numpy as np
import pytest
from rsm_toolkit.gui_workflow import (defaults,preset,build_configuration,indices,orientation,
                                      save_settings,load_settings,execute)
from rsm_toolkit import Lattice,RSMError,load_configuration,load_xrd,calculate_rsm,configured_reflections

ROOT=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('text', ['11-20','1 1 -2 0','(1,1,-2,0)','1 1 −2 0'])
def test_index_formats(text):
    assert indices(text)==[1,1,-2,0]


@pytest.mark.parametrize('text',['1-120','1x1-20','','123','1.0 1 -2 0'])
def test_invalid_indices_not_silently_accepted(text):
    with pytest.raises(RSMError):indices(text)


def test_direct_direction_validation():
    cell=Lattice.hexagonal(4.136,6.716)
    b=orientation(cell,'11-20','1-100')
    np.testing.assert_allclose(b.crystal_to_sample[1],[np.sqrt(3)/2,-.5,0],atol=1e-14)
    with pytest.raises(RSMError,match='not in the surface'):
        orientation(cell,'11-20','10-10')


def test_no_silent_assumptions():
    assert 'sample' not in build_configuration(defaults())
    f=preset(True)
    f['sense']='Choose axis sense'
    with pytest.raises(RSMError,match='axis sense'):build_configuration(f)
    f=preset(True)
    f['zinc']=''
    with pytest.raises(RSMError,match='Zn'):build_configuration(f)
    f['zinc']='135'
    with pytest.raises(RSMError,match='percentage'):build_configuration(f)
    f=defaults()
    assert 'sample' not in build_configuration(f)


@pytest.mark.parametrize('asymmetric',[False,True])
def test_gui_preset_reproduces_existing_scientific_configuration(tmp_path,asymmetric):
    label='12-30' if asymmetric else '11-20'
    name='rsm(12-30)along10-10.raw' if asymmetric else 'RSM(11-20)along0001.raw'
    document=build_configuration(preset(asymmetric))
    path=tmp_path/'run.json';path.write_text(json.dumps(document))
    config=load_configuration(path)
    old=load_configuration(ROOT/f'examples/cdzns_{label}.json')
    m=load_xrd(ROOT/'example_data'/name)
    r=calculate_rsm(m,config); original=calculate_rsm(m,old)
    np.testing.assert_array_equal(r.q,original.q)
    first,_=configured_reflections(config,r);second,_=configured_reflections(old,original)
    for a,b in zip(first,second):np.testing.assert_allclose(a.q,b.q,atol=1e-14)
    assert config.geometry.omega_offset_deg==0
    assert 'allow_provisional' not in document


def test_settings_roundtrip_and_wrong_file(tmp_path):
    f=preset(True);p=tmp_path/'settings.json';save_settings(p,f)
    assert load_settings(p)==f
    p.write_text(json.dumps(build_configuration(f)))
    with pytest.raises(RSMError,match='GUI settings'):load_settings(p)


def test_gui_worker_real_data_and_no_overwrite(tmp_path):
    f=preset(False)
    f.update(file=str(ROOT/'example_data/RSM(11-20)along0001.raw'),output=str(tmp_path),name='my map')
    request=tmp_path/'request.json';result=tmp_path/'result.json'
    save_settings(request,f)
    p=subprocess.run([sys.executable,'-m','rsm_toolkit.gui','--worker',str(request),str(result)],
                     capture_output=True,text=True,timeout=90)
    assert p.returncode==0,p.stderr
    folder=Path(json.loads(result.read_text())['folder'])
    assert all((folder/n).exists() for n in ['settings.json','run.json','map.png','map.npz','map.json','warnings.txt'])
    d=json.loads((folder/'map.json').read_text())
    assert len(d['rsm']['configuration']['theoretical_reflections'])==2
    assert 'provisional' not in d['rsm']
    assert load_settings(folder/'settings.json')==f
    with pytest.warns(UserWarning):second=execute(f)
    assert folder!=second and (folder/'map.png').exists()


def test_custom_cell_and_separate_film_orientation(tmp_path):
    f=preset(False)
    f.update(substrate='Custom cell',substrate_cell='3 3 3 90 90 90',
             norm='0 0 1',reflection='0 0 2',inplane='1 0 0',film='Custom cell',
             film_cell='4 4 4 90 90 90',aligned=False,film_norm='0 1 0',
             film_inplane='1 0 0',film_reflection='0 2 0')
    p=tmp_path/'run.json';p.write_text(json.dumps(build_configuration(f)))
    c=load_configuration(p)
    assert c.sample.substrate.lattice.a==3
    assert c.sample.film.lattice.a==4
    assert not np.allclose(c.sample.substrate_orientation.crystal_to_sample,
                           c.sample.film_orientation.crystal_to_sample)


def test_tk_form_smoke():
    import tkinter as tk
    from rsm_toolkit.gui import Application
    try:root=tk.Tk()
    except tk.TclError:pytest.skip('No Tk display available')
    root.withdraw()
    try:
        app=Application(root)
        app.example(True)
        root.update_idletasks()
        assert [image.width() for image in app.window_icons]==[16,32,48,256]
        assert Path(app.fields()['file']).is_file()
        assert app.fields()['inplane']=='1-100'
        assert build_configuration(app.fields())['geometry']['omega_offset_deg']==0
        app.reset()
        assert app.fields()['overlays'] is False
    finally:root.destroy()


def test_tk_plot_button_to_preview(tmp_path,monkeypatch):
    import time
    import tkinter as tk
    from rsm_toolkit.gui import Application
    try:root=tk.Tk()
    except tk.TclError:pytest.skip('No Tk display available')
    root.withdraw()
    errors=[]
    monkeypatch.setattr('rsm_toolkit.gui.messagebox.showerror',lambda *args:errors.append(args))
    app=None
    try:
        app=Application(root)
        app.example(True)
        app.variables['output'].set(str(tmp_path))
        app.variables['file'].set(str(ROOT/'example_data/rsm(12-30)along10-10.raw'))
        app.plot()
        deadline=time.monotonic()+60
        while app.process is not None and time.monotonic()<deadline:
            root.update()
            time.sleep(.02)
        assert not errors,errors
        assert app.process is None,'GUI worker did not finish'
        assert app.result_folder is not None
        assert app.image_source is not None
        assert (app.result_folder/'map.png').exists()
        assert 'Saved:' in app.status.get()
    finally:
        if app is not None and app.process is not None:
            app.process.terminate();app.process.wait(timeout=10)
            app.temp.cleanup()
        root.destroy()
