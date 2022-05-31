import numpy as np
from scipy.signal import savgol_filter, wiener


def nan_helper(y):
    """Helper to handle indices and logical indices of NaNs.

    :param y: 1d numpy array with possible NaNs
    :return nans: logical indices of NaNs
    :return index: a function, with signature indices= index(logical_indices),
          to convert logical indices of NaNs to 'equivalent' indices
    Example:
        >>> # linear interpolation of NaNs
        >>> nans, x= nan_helper(y)
        >>> y[nans]= np.interp(x(nans), x(~nans), y[~nans])
    """

    return np.isnan(y), lambda z: z.nonzero()[0]


def interpolate_points(px, py, pz):
    """Interpolate 3D sequences

    :param px: np.ndarray of points x coordinates
    :param py: np.ndarray of points y coordinates
    :param pz: np.ndarray of points z coordinates
    :return: Interpolated points px, py and pz as numpy arrays
    """

    assert isinstance(px, np.ndarray) and isinstance(py, np.ndarray) and isinstance(pz, np.ndarray), \
        "Invalid input data for interpolation, must be numpy arrays"
    nans_x, x = nan_helper(px)
    nans_y, y = nan_helper(py)
    nans_z, z = nan_helper(pz)
    px[nans_x] = np.interp(x(nans_x), x(~nans_x), px[~nans_x])
    py[nans_y] = np.interp(y(nans_y), y(~nans_y), py[~nans_y])
    pz[nans_z] = np.interp(z(nans_z), z(~nans_z), pz[~nans_z])
    return px, py, pz


def smooth_points(px, py, pz, smooth_filter="savgol", window=7, poly=1):
    """ Smooth 3D seqeunces

    :param px: np.ndarray of points x coordinates
    :param py: np.ndarray of points y coordinates
    :param pz: np.ndarray of points z coordinates
    :param smooth_filter: type of filtering, possible values: "savgol", "weiner"
    :param window: window of smoothing
    :param poly: polynomial order of smoothing
    :return: Smoothed points px, py and pz as numpy arrays
    """

    assert smooth_filter == "savgol" or smooth_filter == "weiner", \
        "Invalid filtering type, please choose savgol or weiner"
    # Discard NaNs eventually
    valid = np.where(~np.isnan(px))
    if smooth_filter == "savgol":
        # Smooth
        px[valid] = savgol_filter(px[valid], window, poly)
        py[valid] = savgol_filter(py[valid], window, poly)
        pz[valid] = savgol_filter(pz[valid], window, poly)
    elif smooth_filter == "wiener":
        px[valid] = wiener(px[valid], window)
        py[valid] = wiener(py[valid], window)
        pz[valid] = wiener(pz[valid], window)
    return px, py, pz


def smooth_accelerations(accelerations, window=35, poly=1):
    """ Smooth 3D accelerations
    
    :param accelerations: dictionary as
                  {<id_br1>: {'ax': np.array(values),
                              'ay': np.array(values),
                              'az': np.array(values),
                              't': np.array(values)}
                              }
                  <id_br2>: {...}, ...
                  }
    :param window: window of smoothing
    :param poly: polynomial order of smoothing
    :return: Smoothed accelerations in the same format as input
    """

    for id_br in accelerations:
        accelerations[id_br]['ax'] = savgol_filter(accelerations[id_br]['ax'], window, poly)
        accelerations[id_br]['ay'] = savgol_filter(accelerations[id_br]['ay'], window, poly)
        accelerations[id_br]['az'] = savgol_filter(accelerations[id_br]['az'], window, poly)
    return accelerations
