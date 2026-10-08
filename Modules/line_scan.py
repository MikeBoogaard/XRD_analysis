import numpy as np 



def omega(plot_space, tt_com, ttrange, data_dict, CdS):

    om, tt, psd = data_dict           

    unique_om, avg_psd = average_psd_over_axis(tt, om, psd, tt_com, ttrange)

    if plot_space == "Reciprocal":
        x_om, y_om_low,  z_om_low = CdS.Ang2Q(om, tt_com-ttrange)
        x_om, y_om_high, z_om_high = CdS.Ang2Q(om, tt_com+ttrange)
    
    elif plot_space == "Real":
        y_om_low,  z_om_low  = unique_om, np.full_like(unique_om, tt_com - ttrange, dtype=float)
        y_om_high, z_om_high = unique_om, np.full_like(unique_om, tt_com + ttrange, dtype=float)        

    else:
        return

    return unique_om, avg_psd, y_om_low,  z_om_low, y_om_high, z_om_high




#Not sure how fair this is
def background_correction(avg_psd):

    left_tail = avg_psd[:10]
    right_tail = avg_psd[-10:]
    #background_level = np.mean(np.concatenate([left_tail, right_tail]))

    avg_corrected = avg_psd# - background_level

    return avg_corrected




def average_psd_over_axis(Y, Z, psd, center, range_):
    
    mask = (Y >= center - range_) & (Y <= center + range_)
    Z_filtered = Z[mask]
    psd_filtered = psd[mask]

    unique_Z = np.unique(Z_filtered)
    avg_psd = np.array([psd_filtered[Z_filtered == z].mean() for z in unique_Z])
    #avg_psd = background_correction(avg_psd)

    return unique_Z, avg_psd



    






