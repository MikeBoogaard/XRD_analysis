import os
import numpy as np
import xrayutilities as xu
from pathlib import Path
import re
from Modules import geometry
import pandas as pd


def string_to_hkil(RSM_peak):
    numbers = list(map(int, re.findall(r'-?\d', RSM_peak)))

    if len(numbers) != 4:
        raise ValueError("Expected exactly 4 indices for the RSM peak in file title (h, k, i, l)")

    h, k, i, l = numbers
    return h,k,i,l


def list_datafolders(folder_path, experiment_num):
    subfolders = []
    for f in os.scandir(folder_path):
        if f.is_dir():
            for string in experiment_num:
                if string in f.name:
                    subfolders.append(f.name)
                    break
    return subfolders


## experimental parameters
class exp_paramameters(object):
    def __init__(self, energy, inttime, tt_offset, om_align_offset, tt_align_offset, RSMpeak, sample_normal, sample_normal_inplane):
        self.energy          = np.array(energy)
        self.inttime         = np.array(inttime)
        self.tt_offset       = np.array(tt_offset)        
        self.om_align_offset = np.array(om_align_offset) #not used atm
        self.tt_align_offset = np.array(tt_align_offset) #not used atm
        self.RSMpeak         = np.array(RSMpeak)
        self.sample_normal   = np.array(sample_normal)
        self.sample_inplane  = np.array(sample_normal_inplane)



def extract_token(filename, prefix, stop="_"):
    """Extract a token from a filename like 'Mat=CdS'."""
    start = filename.find(prefix)
    if start == -1:
        raise ValueError(f"'{prefix}' not found in filename: {filename}")
    start += len(prefix)
    end = filename.find(stop, start)
    return filename[start:end]        
    
 


def exp_data_from_file_title(filename, X_ray_energy):       
        
        material    = extract_token(filename, "Mat")
        RSM_peak_str = extract_token(filename, "RSM")
        sample_normal_str  = extract_token(filename, "Norm")
        sample_inplane_str = extract_token(filename, "InPlane")

        omoff       = float(extract_token(filename, "omoff=", stop="_")) if "omoff=" in filename else 0
        inttime     = float(extract_token(filename, "int_", stop="s")) if "int_" in filename else 1
        
        h, k, i, l = string_to_hkil(RSM_peak_str)
        h, k, l = geometry.hkil_to_hkl(h, k, i, l)
        RSMpeak = h, k, l

        h, k, i, l = string_to_hkil(sample_normal_str)
        h, k, l = geometry.hkil_to_hkl(h, k, i, l)
        sample_normal = h, k, l

        h, k, i, l = string_to_hkil(sample_inplane_str)
        h, k, l = geometry.hkil_to_hkl(h, k, i, l)
        sample_inplane = h, k, l

        print("filename: " + filename)
        #print("RSM Peak: " + RSM_peak_str)
        #print("Material: " + material)
        #print("Sample Normal: " + sample_normal_str)
        #print("Sample Inplane: " + sample_inplane_str)
        #print("90deg" if '90deg' in filename else "no 90 deg")   
 

        exp_param = exp_paramameters(X_ray_energy, inttime, 0, omoff, 0, RSMpeak, sample_normal, sample_inplane)        
        
        return exp_param
    


def initialize_data(subfolders, data_folder, X_ray_energy, crystals):
    data_dict = {}
    converted_data_dict = {}
    exp_geometry = {}

    data_folder = Path(data_folder)

    for f, subfolder in enumerate(subfolders):
        file_path = data_folder / subfolder

        df = pd.read_csv(file_path, delimiter=r"\s+", decimal=",", engine="python", header=None)
        data = df.values
        
        exp_param = exp_data_from_file_title(file_path.name, X_ray_energy)

        om  = data[:, 0] #+ exp_param.om_offset
        tt  = data[:, 1] + exp_param.tt_offset
        psd = data[:, 2] / exp_param.inttime                     

        expwz     = geometry.make_geometry(crystals["CdSWZ"],   exp_param.sample_inplane, exp_param.sample_normal, X_ray_energy)

        qx, qy, qz = expwz.Ang2Q(om, tt)
        exp_data = np.array([qx, qy, qz, psd])

        #key = f"{sample_nr[f]}{file_path.name}"
        key = f"{file_path.name}"
        data_dict[key] = [om, tt, psd]
        converted_data_dict[key] = exp_data
        exp_geometry[key] = [exp_param.RSMpeak, exp_param.sample_normal, exp_param.sample_inplane]

    return data_dict, converted_data_dict, exp_geometry



def cut_range(unique_values, avg_psd, lower_bound, upper_bound):
    idx_lower = (np.abs(unique_values - lower_bound)).argmin()
    idx_upper = (np.abs(unique_values - upper_bound)).argmin()
    if idx_lower > idx_upper:
        idx_lower, idx_upper = idx_upper, idx_lower
    return unique_values[idx_lower:idx_upper], avg_psd[idx_lower:idx_upper]



### Ries' com finder
def get_cut_indices(qcut, cutpos, cutrange, cutindex=0): #cutpos can either be a number or a HXRD object if HXRD object is used cutindex needs to be passed otherwise default of 0 is used\n",
    cut_idx = np.sort([np.abs((qcut - cutpos[cutindex])-cutrange).argmin(), np.abs((qcut - cutpos[cutindex])+cutrange).argmin()])
    return cut_idx

def get_cut_data(cut_idx, q, qint):
    qcut = q[cut_idx[0]:cut_idx[1]]
    qintcut = qint[cut_idx[0]:cut_idx[1]]
    return qcut, qintcut
def get_qmax_pos(qcut, qint):
    data = np.append(qcut,qint)
    qmax_idx = qint.argmax()
    qmax = qcut[qmax_idx]
    return qmax_idx, qmax

#This can be improved by not getting the numerical maxium, but fitting a peak. However, this is slightly annoying by how i implemented the peak fitting.
def find_fixed_position(qy, qz, psd, fixed_position):
    #First rough Qy scan, Cut range might be adjusted\n",
    qycut, qy_int, qymask = xu.analysis.line_cuts.get_qy_scan([qy, qz], psd,[fixed_position[2]],500,intrange=0.1, intdir='q')
    cut_idx = get_cut_indices(qycut,fixed_position,0.1,1 )
    qycut, qy_int = get_cut_data(cut_idx, qycut, qy_int)
    qymax_idx, qymax = get_qmax_pos(qycut, qy_int)
    qzcut, qz_int, qymask = xu.analysis.line_cuts.get_qz_scan([qy, qz], psd,[get_qmax_pos(qycut,qy_int)[1]],500,intrange=0.1, intdir='q')
    cut_idx = get_cut_indices(qzcut,fixed_position,0.1,2 )
    qzcut, qz_int = get_cut_data(cut_idx, qzcut, qz_int)
    qzmax_idx, qzmax = get_qmax_pos(qzcut, qz_int)
    for i in range(2):
        #Fine qy pass\n",
        qycut, qy_int, qymask = xu.analysis.line_cuts.get_qy_scan([qy, qz], psd,[qzmax],500,intrange=0.1, intdir='q')
        qycut, qy_int = get_cut_data(cut_idx, qycut, qy_int)
        qymax_idx, qymax = get_qmax_pos(qycut, qy_int)
        #Fine Qz pass
        qzcut, qz_int, qymask = xu.analysis.line_cuts.get_qz_scan([qy, qz], psd,[get_qmax_pos(qycut,qy_int)[1]],500,intrange=0.01, intdir='q')
        cut_idx = get_cut_indices(qzcut,fixed_position,0.1,2 )
        qzcut, qz_int = get_cut_data(cut_idx, qzcut, qz_int)
        qzmax_idx, qzmax = get_qmax_pos(qzcut, qz_int)
    return qymax, qzmax