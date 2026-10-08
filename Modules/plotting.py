import numpy as np
import xrayutilities as xu
import matplotlib.pyplot as plt
import matplotlib as mpl
from Modules import data_analysis
from Modules import geometry
from Modules import line_scan
from Modules import data_procesing
from matplotlib.colors import LogNorm
from matplotlib.colors import LinearSegmentedColormap


mpl.rcParams.update({
    # Global font family and size
    "font.family": "DejaVu Sans",
    "font.size": 16,                  # or set to your Lettersize variable later

    # Ensure mathtext uses the same look
    "mathtext.fontset": "dejavusans",
    "mathtext.rm": "DejaVu Sans",
    "mathtext.it": "DejaVu Sans:italic",
    "mathtext.bf": "DejaVu Sans:bold",

    # Optional: make axes and colorbar titles/labels consistent
    "axes.titlesize": "medium",
    "axes.labelsize": "medium",
    "xtick.labelsize": "medium",
    "ytick.labelsize": "medium",
    "legend.fontsize": "medium",
    "figure.titlesize": "large",
})





def plot_RSM(converted_data_dict, key_list, crystals, data_dict, exp_geometry, X_ray_energy, ttrange,
             plot_space="Reciprocal", close_rsm = True, close_linetrace = True, use_annotation=False):


    Lettersize = 14
    figure_count = 0
    gridderSym = xu.FuzzyGridder2D(500, 300)
    gridderSym.KeepData(False)

    linetrace_results = {}

    for key in key_list:
        # --- Load data ---
        RSM_peak, sample_normal, sample_inplane = exp_geometry[key]
        experiments = geometry.experiment_defenitions(crystals, X_ray_energy, sample_inplane, sample_normal)
        CdS = experiments["expwz"]
        Ge = experiments["expwzGe"]
       

        plot_data = np.transpose(converted_data_dict[key])
        plot_data_real = np.transpose(data_dict[key])

        CdS_x_coo, CdS_y_coo = geometry.theoretical_Qy_Qz(CdS, crystals["CdSWZ"], RSM_peak)
        GeWZ_x_coo, GeWZ_y_coo = geometry.theoretical_Qy_Qz(Ge, crystals["GeWZ"], RSM_peak)
        GeWZ_x_coo_real, GeWZ_y_coo_real = geometry.theoretical_om_tt(Ge, crystals["GeWZ"], RSM_peak)

        # --- Plot RSM ---
        fig = plt.figure()
        fig.set_size_inches(12, 7.5)
        figure_count += 1

        gridderSym(plot_data[:, 1], plot_data[:, 2], plot_data[:, 3])
        intensity = gridderSym.data.transpose()
        vmin = 0.1 / np.max(intensity)
        intensity = intensity / np.max(intensity)
        vmax = np.max(intensity)
        intensity = np.where(intensity < vmin, vmin, intensity)

        levels_plot = np.logspace(np.log10(vmin), np.log10(vmax), 100)
        
        

        custom_colors = [
            (30/255, 20/255, 75/255),    # deep purple
            (184/255, 115/255, 51/255),  # copper brown
            (255/255, 159/255, 0/255),   # bright orange
            (255/255, 239/255, 213/255)  # papaya whip
        ]

        custom_cmap = LinearSegmentedColormap.from_list("custom_cmap", custom_colors)

        #cf = plt.contourf(gridderSym.xaxis, gridderSym.yaxis, intensity, levels=levels_plot,
        #                  norm=LogNorm(vmin=vmin, vmax=vmax), cmap="jet")
        cf = plt.contourf(gridderSym.xaxis, gridderSym.yaxis, intensity, levels=levels_plot,
                          norm=LogNorm(vmin=10*vmin, vmax=vmax), cmap=custom_cmap)
        
        #plt.title(f"{data_analysis.read_sampleID(key)} RSM of {data_analysis.read_key_reflection(key)}")
        plt.xlabel("$Q_{y}$ ($\\AA^{-1}$)", fontsize=Lettersize)
        plt.ylabel("$Q_{z}$ ($\\AA^{-1}$)", fontsize=Lettersize)
        plt.tick_params(axis='both', which='major', labelsize=Lettersize)
        
        cbar = plt.colorbar(cf)
        cbar.ax.tick_params(labelsize=Lettersize)
        cbar.set_ticks([0.000001, 0.00001, 0.0001, 0.001, 0.01, 0.1, 1])
        cbar.set_label("Normalized intensity", fontsize=Lettersize) 



        # --- Find COM ---
        fixed_position = [0, GeWZ_x_coo, GeWZ_y_coo]
        fixed_position_real = [0, GeWZ_x_coo_real, GeWZ_y_coo_real]
        #com_Qy_data, com_Qz_data = data_procesing.find_fixed_position(plot_data[:, 1], plot_data[:, 2], plot_data[:, 3], fixed_position)
        
        if data_analysis.read_key_reflection(key) == "20-20":
            com_om_data, com_tt_data = data_procesing.find_fixed_position(plot_data_real[:, 0], plot_data_real[:, 1], plot_data_real[:, 2], fixed_position_real)
            #com_Qy_data, com_Qz_data = data_procesing.find_fixed_position(plot_data[:, 1], plot_data[:, 2], plot_data[:, 3], fixed_position)
        

        #As there is no big graining of the substrate here, the theoretical value suffices
        if data_analysis.read_key_reflection(key) == "12-30":
            com_tt_data = GeWZ_y_coo_real


        # --- Annotation ---
        if use_annotation:
            labeloffsetx, labeloffsety = 0.01, 0.015
            plt.plot([CdS_x_coo], [CdS_y_coo], marker="X", markersize=10, color="black")
            plt.text(CdS_x_coo + labeloffsetx, CdS_y_coo + 2 * labeloffsety, "CdS", color=(255/255, 239/255, 213/255),fontsize=Lettersize)
            plt.plot([GeWZ_x_coo], [GeWZ_y_coo], marker="X", markersize=10, color="black")
            plt.text(GeWZ_x_coo + labeloffsetx, GeWZ_y_coo + labeloffsety, "Ge", color=(255/255, 239/255, 213/255),fontsize=Lettersize)
            #plt.plot([com_Qy_data],[com_Qz_data], marker="X",markersize = 10,color='red')
            #plt.text(com_Qy_data+labeloffsetx, com_Qz_data, r'Ge_data ', color='red',fontsize=12)

        # --- Line scan ---
        unique_om, avg_psd_om, y_om_low, z_om_low, y_om_high, z_om_high = line_scan.omega(
            plot_space, com_tt_data, ttrange, data_dict[key], CdS)

        plt.plot(y_om_low, z_om_low, color=(184/255, 115/255, 51/255), linestyle='--', linewidth=1.5)
        plt.plot(y_om_high, z_om_high, color=(184/255, 115/255, 51/255), linestyle='--', linewidth=1.5)

        # --- Line trace figure ---
        fig2 = plt.figure()
        figure_count += 1
        plt.plot(unique_om, avg_psd_om / vmax, marker="o", linestyle="None", markersize=3, color="r")
        plt.title(f"{data_analysis.read_sampleID(key)} along {data_analysis.read_inplane_direction(key)} omega linetrace")
        plt.xlabel("Omega (Degrees)")
        plt.ylabel("Intensity / max substrate Intensity")
        plt.grid(True)

        # Save results
        linetrace_results[key] = {
            "line_traces_figure": fig2,
            "unique_om": unique_om,
            "avg_psd_om": avg_psd_om,
        }
        
        
        
        if close_rsm:
                plt.close(fig)

        if close_linetrace:
                plt.close(fig2)

        

    return linetrace_results, figure_count, vmax



def plot_fwhm(fwhm_results, key_list):

    Lettersize = 14
    # Colors for the three groups
    colors = {
        ("20-20", "0001"): (30/255, 20/255, 75/255),
        ("20-20", "11-20"): (184/255, 115/255, 51/255),
        ("12-30", None):(255/255, 159/255, 0/255)
    }


    plt.figure(figsize=(8, 6))

    grouped_data = {
        ("20-20", "0001"): {"T": [], "fit": [], "lower": [], "upper": []},
        ("20-20", "11-20"): {"T": [], "fit": [], "lower": [], "upper": []},
        ("12-30", None): {"T": [], "fit": [], "lower": [], "upper": []}
    }

    for key in key_list:
        fwhm_fit = fwhm_results[key]["FWHM_fit"]
        fwhm_lower = fwhm_results[key]["FWHM_lower"]
        fwhm_upper = fwhm_results[key]["FWHM_upper"]

        
        #If the FWHM is bigger than this it doesnt really make sense anymore
        if fwhm_fit > 12:
            continue        

        T = data_analysis.read_Temp(key)
        RSM = data_analysis.read_key_reflection(key)
        inplane = data_analysis.read_inplane_direction(key)
        norm = data_analysis.read_Norm(key)
        

        # Assign to correct group
        if RSM == "20-20" and inplane == "0001":
            group = ("20-20", "0001")
        elif RSM == "20-20" and inplane == "11-20":
            group = ("20-20", "11-20")
        elif RSM == "12-30":
            group = ("12-30", None)
        else:
            continue

        grouped_data[group]["T"].append(float(T))
        grouped_data[group]["fit"].append(fwhm_fit)
        grouped_data[group]["lower"].append(fwhm_lower)
        grouped_data[group]["upper"].append(fwhm_upper)

    
    
    for group, data in grouped_data.items():
        if data["T"]:
            # Decide marker based on group
            if group == ("12-30", None):
                marker_style = 's'  # square
            elif group == ("20-20", "11-20"):
                marker_style = 'o'  # triangle
            else:
                marker_style = 'o'  # circle

            # Convert lists to arrays
            T_vals = np.array(data["T"])
            fit_vals = np.array(data["fit"])
            lower_vals = np.array(data["lower"])
            upper_vals = np.array(data["upper"])

            # Compute asymmetric error bars
            yerr = [fit_vals - lower_vals, upper_vals - fit_vals]

            # Plot all points in one call with dotted line
            plt.errorbar(
                T_vals, fit_vals,
                yerr=yerr,
                xerr = 1,
                fmt=marker_style,
                color=colors[group],
                capsize=8,
                elinewidth=1,
                capthick=1,
                linestyle=None,
                markersize=10 
            )

            # Add legend entry
            plt.plot([], [], color=colors[group], marker=marker_style, 
                    label = f"({ '2-200' if group[0] == '20-20' else '12-30' }) \u2225[{ group[1] if group[1] else '1-100' }]")





    plt.xlabel(r"Temperature ($^\circ$C)", fontsize=Lettersize)
    plt.ylabel("FWHM (deg)", fontsize=Lettersize)
    plt.tick_params(axis='both', which='major', labelsize=14) 
    #plt.title("FWHM vs Temperature")
    #plt.yscale('log')   
    plt.ylim(1, 11)
    plt.xlim(180,300)

    
    plt.axvspan(180, 195, color=(30/255, 20/255, 75/255), alpha=0.2)  # Left region
    plt.axvspan(285, 300, color=(30/255, 20/255, 75/255), alpha=0.2)  # Right region


    plt.text(183, 9, "No fit", rotation=0, fontsize=Lettersize, color='black')
    plt.text(288, 9, "No fit", rotation=0, fontsize=Lettersize, color='black')

    
    
    plt.grid(True, which='both', linestyle='--', alpha=0.7)

    
    plt.legend(
        loc='upper left',
        bbox_to_anchor=(0.52, 0.97),
        borderaxespad=0,
        fontsize=Lettersize
    )

    #plt.yticks([1, 2, 3, 4, 5, 7, 10])  


    
    
    plt.grid(True)
    plt.tight_layout()
    
    fig = plt.gcf()
    return fig













