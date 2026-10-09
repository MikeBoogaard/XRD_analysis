from pathlib import Path
import hashlib
import json
import numpy as np
import pytest
import matplotlib.pyplot as plt
from rsm_toolkit import *

ROOT=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("name",["22-40_RSM_S0159","2200_RSM_S0155"])
@pytest.mark.parametrize("extension",["brml","raw"])
def test_actual_map_pipeline(name,extension,tmp_path):
    source=ROOT/"example_data"/f"{name}.{extension}"
    before=hashlib.sha256(source.read_bytes()).hexdigest()
    m=load_xrd(source)
    r=calculate_rsm(m,load_configuration(ROOT/"examples/coplanar_provisional.json"))
    assert r.q.shape==(1401,477,3)
    assert r.provisional and np.isfinite(r.q).all()
    expected=4*np.pi/r.wavelength_angstrom*np.sin(np.deg2rad(m.motors["TwoTheta"])/2)
    np.testing.assert_allclose(np.linalg.norm(r.q,axis=-1),expected,atol=5e-14,rtol=1e-13)
    with pytest.warns(UserWarning,match="nonpositive"):
        fig,_=plot_rsm(r,mode="grid",bins=(100,100))
    save_figure(fig,tmp_path/"experimental.png",dpi=80)
    plt.close(fig)
    export_data(r,tmp_path/"experimental.npz")
    restored=load_export(tmp_path/"experimental.npz")
    np.testing.assert_array_equal(restored.q,r.q)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==before


def test_all_original_data_and_phase1_preserved():
    manifest=json.loads((ROOT/"docs/preserved_files.json").read_text())
    for name,digest in manifest.items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
