import hashlib
import json
from pathlib import Path
from importlib.resources import files
import numpy as np
import pytest
from rsm_toolkit.material_library import CIF_MATERIALS,reference_material
from rsm_toolkit.gui_workflow import preset,build_configuration,load_settings
from rsm_toolkit import load_configuration,RSMError

ROOT=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('name',list(CIF_MATERIALS))
def test_packaged_cif_matches_original(name):
    filename=CIF_MATERIALS[name]
    packaged=files('rsm_toolkit').joinpath('data','cif',filename).read_bytes()
    assert packaged==(ROOT/'Literature data for analysis/CIF'/filename).read_bytes()
    phase,cell=reference_material(name)
    assert cell.a>0 and cell.c>0
    assert filename in phase['reference']


@pytest.mark.parametrize('name,a,c',[('Ge (cubic)',5.762862,5.762862),('Ge (hexagonal)',3.9855,6.5772)])
def test_ge_cells_and_gui_film(name,a,c,tmp_path):
    f=preset(False)
    f.update(substrate=name,film=name,norm='0 0 1',reflection='0 0 2',inplane='1 0 0',film_reflection='0 0 2')
    p=tmp_path/'run.json';p.write_text(json.dumps(build_configuration(f)))
    config=load_configuration(p)
    assert config.sample.film.lattice.a==pytest.approx(a)
    assert config.sample.film.lattice.c==pytest.approx(c)
    q=config.sample.film_orientation.transform(config.sample.film.lattice.reciprocal_vector([0,0,2]))
    np.testing.assert_allclose(q,[0,0,4*np.pi/c],atol=1e-14)


def test_reciprocal_settings_are_not_silently_reinterpreted(tmp_path):
    f=preset(True);f.update(convention='Old InPlane: reciprocal reference',inplane='10-10',nominal=True)
    p=tmp_path/'settings.json';p.write_text(json.dumps({'schema':'rsm-gui-1','fields':f}))
    with pytest.raises(RSMError,match='equivalent direct'):load_settings(p)


def test_direct_settings_v1_load_safely(tmp_path):
    f=preset(False);f.update(convention='Direct crystal direction',nominal=True,substrate='CdS reference')
    p=tmp_path/'settings.json';p.write_text(json.dumps({'schema':'rsm-gui-1','fields':f}))
    loaded=load_settings(p)
    assert loaded['substrate']=='CdS'
    assert 'convention' not in loaded
    assert 'nominal' not in loaded
