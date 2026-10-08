# Retired notebook scientific content
Verbatim cell sources and textual outputs; embedded images and complete metadata remain in [legacy_source.zip](legacy_source.zip). These are historical observations, not validated inputs for new scans.

## RSM_main.ipynb

### Cell 1 (code)

````text
%reset -f
import pandas as pd
from pathlib import Path


%load_ext autoreload
%autoreload 2
from Modules import data_procesing
from Modules import plotting
from Modules import geometry
from Modules import data_analysis
from Modules import fitting
from Modules import theory
import warnings
warnings.filterwarnings("ignore")

%matplotlib tk



````

### Cell 2 (code)

````text
#Use file naming convention as described here:
#MatCdSK0202_Temp300_Norm10-10_RSM20-20_InPlane11-20_omscan=abs
X_ray_energy = 8047.8 
folder_path  = Path.cwd()
data_folder  = folder_path / "S0183"
subfolders   = list(data_folder.rglob("*.dat"))
literature_folder = folder_path / "Literature data for analysis"
crystals     = geometry.crystal_defenitions(literature_folder)


````

Stored output:

````text
XU.materials: Warning: element S used instead of S2-
XU.materials: Warning: element S used instead of S2-

````

### Cell 3 (code)

````text
data_dict,converted_data_dict, exp_geometry = data_procesing.initialize_data(subfolders, data_folder, X_ray_energy, crystals) #Conversion to reciprocal is based on the CdS crystal hardcoded
key_list                        = list(data_dict.keys())
````

Stored output:

````text
Warning: i ≠ -(h + k) → got i=2, expected 0
filename: MatCdSS0183_Temp200_Norm10-10_RSM22-40_InPlane1-120_omscan=abs.dat

````

### Cell 4 (code)

````text
linetrace_results, figure_count, vmax = (plotting.plot_RSM(
    converted_data_dict,
    key_list,
    crystals,
    data_dict,
    exp_geometry,
    X_ray_energy, 
    ttrange = 0.2,  #(degrees)
    plot_space="Reciprocal",
    close_rsm = False,
    close_linetrace = True,
    use_annotation  = True))                                                                                                                                
````

Stored error: UnboundLocalError: cannot access local variable 'com_tt_data' where it is not associated with a value

### Cell 5 (code)

````text
#Keep the linetrace figure open for this
fwhm_results = fitting.plot_analysis(
    exp_geometry,
    crystals,
    X_ray_energy,
    linetrace_results, 
    key_list, 
    figure_count, 
    vmax, 
    fittype = "pseudo voigt",
    print_linetrace = True)
````

### Cell 6 (code)

````text
theory.plot_full_theoretical_RSM(key_list, exp_geometry, crystals, X_ray_energy)
````

Stored output:

````text
10.177876384327154 80.35575276865431
12.03043598681558 84.0608719736312

````

## Theoretical_RSM_main.ipynb

### Cell 1 (code)

````text

````
