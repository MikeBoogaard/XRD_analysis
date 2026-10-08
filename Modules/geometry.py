import numpy as np
import xrayutilities as xu
import os.path


def crystal_defenitions(literature_folder):

    cif_folder = os.path.join(literature_folder, "CIF")

    CdS_cif          = os.path.join(cif_folder, 'CdS.cif')
    ZnS_cif          = os.path.join(cif_folder, 'ZnS.cif')
    cubGe_cif       = os.path.join(cif_folder, 'Ge_mp-32_conventional_standard.cif')
    HexGe_cif        = os.path.join(cif_folder, 'Hex_Ge_100_Paper.cif')


    def create_CdZnS(alloy_percent):
            CdZnS = xu.materials.material.Alloy(CdSWZ, ZnSWZ, alloy_percent)
            return CdZnS




    CdSWZ         = xu.materials.Crystal.fromCIF(CdS_cif)
    ZnSWZ         = xu.materials.Crystal.fromCIF(ZnS_cif)
    GeWZ          = xu.materials.Crystal.fromCIF(HexGe_cif)
    CdZnSWZ35     = create_CdZnS(0.35)


    crystals = {
        "CdSWZ": CdSWZ,
        "GeWZ": GeWZ,
        "ZnSWZ": ZnSWZ,
        "CdZnSWZ35":  CdZnSWZ35

    }
    return crystals



def make_geometry(crystal, idir_hkl, ndir_hkl, energy, geometry="lo_hi"):
    idir = crystal.Q(*idir_hkl)
    ndir = crystal.Q(*ndir_hkl)
    wavelength = xu.lam2en(energy)
    return xu.HXRD(idir, ndir, geometry=geometry, wl=wavelength)

def experiment_defenitions(crystals, X_ray_energy, sample_inplane, sample_normal):
    
    expwz      = make_geometry(crystals["CdSWZ"],   sample_inplane, sample_normal, X_ray_energy)
    expwzGe    = make_geometry(crystals["GeWZ"],    sample_inplane, sample_normal, X_ray_energy)
    expZnS     = make_geometry(crystals["ZnSWZ"],    sample_inplane, sample_normal, X_ray_energy)
    expwzCdZnS35 = make_geometry(crystals["CdZnSWZ35"], sample_inplane, sample_normal, X_ray_energy)

    experiments = {
        "expwz": expwz,
        "expwzGe": expwzGe,
        "expZnS": expZnS,
        "expwzCdZnS35":  expwzCdZnS35
    }
    



    return experiments


def theoretical_om_tt(experiment, crystal, RSM_peak):
    [om, _, _, tt] = experiment.Q2Ang(crystal.Q(*RSM_peak))
    return om, tt


def theoretical_Qy_Qz(experiment, crystal, RSM_peak):
    [_, Qy, Qz] = experiment.Transform(crystal.Q(*RSM_peak))
    return Qy, Qz


def hkil_to_hkl(h, k, i, l):    
    if i != -(h + k):
        print(f"Warning: i ≠ -(h + k) → got i={i}, expected {-h - k}")
    return (h, k, l)


    