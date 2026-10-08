from Modules import geometry

import numpy as np
import xrayutilities as xu
import matplotlib.pyplot as plt

from scipy.ndimage import center_of_mass
from matplotlib.colors import LogNorm
from lmfit.models import Gaussian2dModel
from mpl_toolkits.mplot3d import Axes3D





def plot_full_theoretical_RSM(key_list, exp_geometry, crystals, X_ray_energy):


    for index, key in enumerate(key_list):
        
        sample_normal  = [1,1,0]   
        sample_inplane = [0,0,1]

        experiments = geometry.experiment_defenitions(crystals, X_ray_energy, sample_inplane, sample_normal)
        CdS = experiments["expwz"]
        Ge = experiments["expwzGe"]
        CdZnS35 = experiments["expwzCdZnS35"]


        ax, _ = xu.materials.show_reciprocal_space_plane(crystals["CdSWZ"], CdS, ttmax=900, color='orange',                    label='CdS norm:    '+ str(sample_normal) + 'inpl:' +str(sample_inplane))  
        xu.materials.show_reciprocal_space_plane(        crystals["GeWZ"],  Ge, ttmax=900, ax=ax, color='red',              label='GeHex norm:'+ str(sample_normal) + 'inpl:' +str(sample_inplane))
        xu.materials.show_reciprocal_space_plane(        crystals["CdZnSWZ35"],  CdZnS35, ttmax=900, ax=ax, color='blue',              label='CdZnS norm:'+ str(sample_normal) + 'inpl:' +str(sample_inplane))
        

               
        omega, ttheta = geometry.theoretical_om_tt(CdS, crystals["CdSWZ"], (3,0,0))
        print(omega,ttheta)

        omega, ttheta = geometry.theoretical_om_tt(Ge, crystals["GeWZ"], (3,0,0))
        print(omega,ttheta)

        

        

       