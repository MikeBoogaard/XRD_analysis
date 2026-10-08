import numpy as np
from scipy.ndimage import center_of_mass
import matplotlib.pyplot as plt


def read_key_reflection(key):
    reflection = key[key.find("RSM") + len("RSM"):key.find("_",key.find("RSM") + len("RSM"))]
    return reflection 

def read_sampleID(key):
    sampleID = key[key.find("MatCdS") + len("MatCdS"):key.find("_",key.find("MatCdS") + len("MatCdS"))]
    return sampleID 

def read_inplane_direction(key):
    sampleID = key[key.find("InPlane") + len("InPlane"):key.find("_",key.find("InPlane") + len("InPlane"))]
    return sampleID 

def read_Temp(key):
    sampleID = key[key.find("Temp") + len("Temp"):key.find("_",key.find("Temp") + len("Temp"))]
    return sampleID 

def read_Norm(key):
    sampleID = key[key.find("Norm") + len("Norm"):key.find("_",key.find("Norm") + len("Norm"))]
    return sampleID 





#Kind of manually converts the data to a 2D matrix and then takes the COM of the data form a masked subset
def find_max_tt_om(data_dict, plot_space, CdS):
    plot_data_rs = np.transpose(data_dict)
    
    om = plot_data_rs[:, 0]
    tt = np.round(plot_data_rs[:, 1], 4)
    psd = plot_data_rs[:, 2]

    om_as = np.unique(om)
    tt_as = np.unique(tt)

    om_idx = np.searchsorted(om_as, om)
    tt_idx = np.searchsorted(tt_as, tt)

    matrix = np.zeros((len(om_as), len(tt_as)))
    np.add.at(matrix, (om_idx, tt_idx), psd)   

    matrix[matrix < 0.3 * np.max(matrix)] = 0 #ignores low values before determening the COM


    com_row, com_col = center_of_mass(matrix)        
        
    i = int(round(com_row))
    j = int(round(com_col))


    ommax = om_as[i]
    ttmax = tt_as[j]    

    

    return ttmax, ommax