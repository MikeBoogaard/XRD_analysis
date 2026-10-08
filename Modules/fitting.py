import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from Modules import geometry





def remove_spikes(x_data, y_data, threshold=2):
    cleaned_x = [x_data[0]]
    cleaned_y = [y_data[0]]

    for i in range(1, len(y_data)):
        if abs(y_data[i] - y_data[i-1]) <= threshold:
            cleaned_x.append(x_data[i])
            cleaned_y.append(y_data[i])
        # If the jump is too big, skip this point

    return np.array(cleaned_x), np.array(cleaned_y)



def plot_analysis(exp_geometry, crystals, X_ray_energy, linetrace_results, key_list, figure_count, vmax, fittype, print_linetrace = True):
    fwhm_results = {}
    for key in key_list:
        # Get figure for line traces
        fig_linetraces_fits = linetrace_results[key]["line_traces_figure"]

        # Extract data
        RSM_peak, sample_normal, sample_inplane = exp_geometry[key]
        experiments = geometry.experiment_defenitions(crystals, X_ray_energy, sample_inplane, sample_normal)
        CdS = experiments["expwz"]
        Ge = experiments["expwzGe"]



        CdS_om, CdS_tt = geometry.theoretical_om_tt(CdS, crystals["CdSWZ"], RSM_peak)
        GeWZ_om, GeWZ_tt = geometry.theoretical_om_tt(Ge, crystals["GeWZ"], RSM_peak)

        om = linetrace_results[key]["unique_om"]
        psd = linetrace_results[key]["avg_psd_om"]


        fwhm_fit, fwhm_lower, fwhm_upper = fitting(om, psd / vmax, fig_linetraces_fits, fittype, CdS_om, GeWZ_om, print_linetrace, color="r--")


        
        fwhm_results[key] = {
            "FWHM_fit": fwhm_fit,
            "FWHM_lower": fwhm_lower,
            "FWHM_upper": fwhm_upper
        }

        
    return fwhm_results


def fitting(x_data, y_data, fig_linetraces_fits, fittype, theoretical_CdS, theoretical_GeWZ, print_linetrace, color):


    
    x_data, y_data = remove_spikes(x_data, y_data, threshold=0.5) #To remove the monochromator streak
    #plt.plot(x_data,y_data)    
    sorted_indices = np.argsort(y_data)[::-1] 
    index_10th = sorted_indices[1]  
    peak_x = x_data[index_10th]


    # --- Restrict data to ±2° around peak ---
    range_mask = (x_data >= peak_x - 2) & (x_data <= peak_x + 2)
    x_data = x_data[range_mask]
    y_data = y_data[range_mask]

   
    if fittype == "pseudo voigt":
        p0 = [1.0, x_data[np.argmax(y_data)], 0.1, 0.5]
        optimized_fit_params, covariance_matrix = curve_fit(
            pseudo_voigt,
            x_data,
            y_data,
            p0=p0,
            bounds=([0, min(x_data), 0, 0], [np.inf, max(x_data), np.inf, 1]),
        )
        A_fit, x0_fit, fwhm_fit, eta_fit = optimized_fit_params
        y_fit = pseudo_voigt(x_data, *optimized_fit_params)



        #CHECK DIT
        # Confidence interval for FWHM
        fwhm_std = np.sqrt(covariance_matrix[2, 2])
        fwhm_lower = fwhm_fit - 1.96 * fwhm_std
        fwhm_upper = fwhm_fit + 1.96 * fwhm_std

    residuals = y_data - y_fit
    rss = np.sum(residuals**2)
    ss_total = np.sum((y_data - np.mean(y_data))**2)
    r_squared = 1 - (rss / ss_total)
    maximum = f"{np.max(y_data):.2e}"
    integral_breadth = get_integral_breadth(x_data, y_data)


    if print_linetrace:
        # Plot on the provided figure
        plt.figure(fig_linetraces_fits.number)
        plt.plot(
            x_data,
            y_fit,
            color,
            label=(
                f"FWHM     = {fwhm_fit:.4f} [{fwhm_lower:.4f}, {fwhm_upper:.4f}]\n"
                f"IB            = {integral_breadth:.4f}\n"
                f"Lor/Gau  = {eta_fit:.2f}/{1 - eta_fit:.2f}\n"
                f"Center    = {x0_fit:.2f}\n"
                f"Maximum = {maximum}\n"
                f"GeWZ     = {theoretical_GeWZ:.3f}\n"
                f"Rsquared = {r_squared:.3f}"
            ),
        )
        plt.legend()

    return fwhm_fit, fwhm_lower, fwhm_upper

    

def pseudo_voigt(x, A, x0, fwhm, eta):
    sigma = fwhm / (2 * np.sqrt(2 * np.log(2)))  # Gaussian sigma
    gamma = fwhm / 2                             # Lorentzian HWHM
    gaussian = A * np.exp(-((x - x0)**2) / (2 * sigma**2))
    lorentzian = A * (gamma**2 / ((x - x0)**2 + gamma**2))
    return eta * lorentzian + (1 - eta) * gaussian


def get_integral_breadth(x, y):

    area = np.trapezoid(y, x)
    peak_height = np.max(y)
    if peak_height == 0:
        return 0
    return area / peak_height



