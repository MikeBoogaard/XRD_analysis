"""Independent metric/frame checks; fixture values are not experimental metadata."""
import copy
import json
from pathlib import Path
from dataclasses import replace
import numpy as np
import pytest
import matplotlib.pyplot as plt
from rsm_toolkit import (load_configuration, configured_reflections, plot_configured_rsm,
                        calculate_rsm, load_xrd, MissingMetadataError, RSMError)
from rsm_toolkit.overlays import phase_from_config

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def specification():
    value = json.loads((ROOT/'examples/coplanar_provisional.json').read_text())
    phase = {'name': 'synthetic hexagonal test cell',
             'lattice': {'system': 'hexagonal', 'a': 4., 'c': 6.},
             'orientation': {'surface_plane': [1,0,-1,0],
                             'in_plane_direction': [1,-2,1,0]},
             'reflections': [[2,2,-4,0]]}
    value['sample'] = {'substrate': phase, 'film': copy.deepcopy(phase),
                       'frame_alignment': {'map_frame': value['geometry']['frame'],
                           'sample_to_map': np.eye(3).tolist(), 'verified': False,
                           'allow_provisional': True, 'reference': 'synthetic test, not a mounting claim'}}
    value['sample']['film']['lattice']['a'] = 3.9
    value['plot'] = {'theoretical_overlays': True, 'mode': 'grid', 'bins': [40,40]}
    return value


def config(tmp_path, value):
    path = tmp_path/'run.json'
    path.write_text(json.dumps(value))
    return load_configuration(path)


@pytest.fixture(scope='module')
def measurement():
    return load_xrd(ROOT/'new_data/22-40_RSM_S0159.raw')


def test_actual_data_overlay_with_explicit_synthetic_model(tmp_path, specification, measurement):
    c = config(tmp_path, specification)
    r = calculate_rsm(measurement,c)
    reflections, report = configured_reflections(c,r)
    # Independent closed form for (22-40), m-plane normal and -a2 direct y.
    # |G|=8*pi/a; Qy=-4*pi/a, Qz=4*pi*sqrt(3)/a.
    for p, a in zip(reflections, (4.,3.9)):
        np.testing.assert_allclose(p.q,[0,-4*np.pi/a,4*np.pi*np.sqrt(3)/a],atol=2e-14)
    assert report[0]['d_angstrom'] == pytest.approx(1.)
    assert reflections[0].marker != reflections[1].marker
    assert reflections[0].color != reflections[1].color
    with pytest.warns(UserWarning,match='nonpositive'):
        fig,ax,_ = plot_configured_rsm(r,c)
    assert len(ax.lines) == 2
    assert all('PROVISIONAL' in p.status for p in reflections)
    np.testing.assert_array_equal(r.intensity,measurement.intensity)
    fig.savefig(tmp_path/'synthetic_model_on_real_data.png')
    plt.close(fig)


@pytest.mark.parametrize('change', ['orientation','lattice','reflection','alignment','frame','reference','provisional','offplane'])
def test_missing_or_inconsistent_metadata_refuses_overlay(tmp_path,specification,measurement,change):
    v = specification
    if change == 'orientation': v['sample']['film']['orientation'] = None
    if change == 'lattice':
        v['sample']['film']['lattice'] = None
        v['sample']['film']['orientation'] = None
    if change == 'reflection': v['sample']['film']['reflections'] = None
    if change == 'alignment': v['sample']['frame_alignment'] = None
    if change == 'frame': v['sample']['frame_alignment']['map_frame'] = 'different'
    if change == 'reference': v['sample']['frame_alignment']['reference'] = None
    if change == 'provisional': v['sample']['frame_alignment']['allow_provisional'] = False
    if change == 'offplane': v['sample']['film']['reflections'] = [[2,2,-4,1]]
    c = config(tmp_path,v)
    with pytest.raises(RSMError): configured_reflections(c,calculate_rsm(measurement,c))


def test_nonidentity_sample_to_map(tmp_path,specification,measurement):
    specification['sample']['frame_alignment']['sample_to_map'] = [[-1,0,0],[0,-1,0],[0,0,1]]
    c=config(tmp_path,specification)
    p,_=configured_reflections(c,calculate_rsm(measurement,c))
    assert p[0].q[1] == pytest.approx(np.pi)


def test_explicit_vegard_endpoints_and_unknown_fraction():
    phase={'name':'alloy','vegard':{'first':{'system':'hexagonal','a':4.,'c':6.},
                                  'second':{'system':'hexagonal','a':3.,'c':5.},
                                  'fraction_second':.2}}
    m,_=phase_from_config(phase)
    assert m.lattice.a == pytest.approx(3.8)
    assert m.lattice.c == pytest.approx(5.8)
    phase['vegard']['fraction_second']=None
    with pytest.raises(MissingMetadataError): phase_from_config(phase)


@pytest.mark.parametrize('field', ['verified','allow_provisional'])
def test_alignment_booleans_are_strict(tmp_path,specification,measurement,field):
    specification['sample']['frame_alignment'][field]='false'
    c=config(tmp_path,specification)
    with pytest.raises(RSMError,match='boolean'): configured_reflections(c,calculate_rsm(measurement,c))


def test_unknown_composition_with_measured_lattice_is_allowed(tmp_path,specification):
    specification['sample']['film']['composition']=None
    assert config(tmp_path,specification).sample.film.lattice.a==3.9


def test_json_typo_rejected(tmp_path,specification):
    specification['sample']['film']['orientation']['inplane']=[1,0,0]
    with pytest.raises(RSMError,match='Unknown orientation'): config(tmp_path,specification)


def test_inaccessible_reflection_rejected(tmp_path,specification,measurement):
    specification['sample']['film']['reflections']=[[20,20,-40,0]]
    c=config(tmp_path,specification)
    with pytest.raises(RSMError,match='inaccessible'):
        configured_reflections(c,calculate_rsm(measurement,c))


def test_retired_sources_preserved_in_archive():
    import hashlib
    import zipfile
    manifest=json.loads((ROOT/'docs/legacy_manifest.json').read_text())
    with zipfile.ZipFile(ROOT/'docs/legacy_source.zip') as archive:
        for name,digest in manifest.items():
            assert hashlib.sha256(archive.read(name)).hexdigest()==digest


def test_cli_saves_theory_and_old_cli_still_works(tmp_path,specification):
    from rsm_toolkit.cli import main
    path=tmp_path/'run.json'
    path.write_text(json.dumps(specification))
    output=tmp_path/'map.png'
    with pytest.warns(UserWarning):
        assert main(['map',str(ROOT/'new_data/22-40_RSM_S0159.raw'),
                     '--config',str(path),'--output',str(output)])==0
    saved=json.loads(output.with_suffix('.json').read_text())['rsm']['configuration']
    assert len(saved['theoretical_reflections'])==2
    assert saved['sample_settings']==specification['sample']
    assert output.exists() and output.with_suffix('.npz').exists()
    with pytest.warns(UserWarning):
        assert main(['map',str(ROOT/'new_data/22-40_RSM_S0159.raw'),
                     '--config',str(ROOT/'examples/coplanar_provisional.json'),
                     '--output',str(tmp_path/'old.png'),'--mode','grid'])==0
    plt.close('all')
