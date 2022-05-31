import numpy as np
import mpit.utils.filtering as filt


def filter_skeletons(frames, min_duration=5, verbose=1):
    """ Discard skeletons that appear for less than min_duration
    
    :param verbose: if >1 print logs
    :param frames: positions of one point in numpy format structured as following dict
                   {'t': np.array(values),
                      'skeletons' : {<id_sk1>: {'px': np.array(values),
                                                'py': np.array(values),
                                                'pz': np.array(values)},
                                     <id_sk2>: {...}, ...
                                     }
                   }
    :param min_duration: minimum duration in seconds for a skeleton to be valid
    :return: filtered positions of one point given in input
    """
    invalid_ids_x = []
    skeletons = frames['skeletons']
    for id_sk in skeletons:
        # Zero valid values
        if np.count_nonzero(~np.isnan(skeletons[id_sk]['px'])) == 0:
            invalid_ids_x.append(id_sk)
        # Some valid values
        else:
            valid_ts = np.where(~np.isnan(skeletons[id_sk]['px']))
            first_ts_x = frames['t'][valid_ts[0][0]]
            last_ts_x = frames['t'][valid_ts[0][-1]]
            sk_duration = last_ts_x - first_ts_x  # Duration of the skeleton
            if sk_duration < min_duration:
                invalid_ids_x.append(id_sk)
    if verbose >= 1:
        print("Removing", str(len(invalid_ids_x)), "invalid skeleton(s) with duration less than", str(min_duration),
              "seconds")
        print('------------------------------------------------------------')
    # Remove invalid skeleton
    for id_sk in invalid_ids_x:
        del skeletons[id_sk]
    frames['skeletons'] = skeletons
    return frames


def post_process_xy(x_frames, y_frames, smooth_filter="savgol", window=7, poly=1, verbose=1):
    """ Interpolate and smooth x and y points together such that they match in frames. x and y must be
        complementary. Skeletons are kept only if present in both sequences. The duration of the skeletons is filtered
        based on the time window x in order to keep the same duration in both sequences.
    
    :param smooth_filter: type of filtering, possible values: "savgol", "weiner"
    :param verbose: if >1 print logs
    :param x_frames: positions of the dominant point x in numpy format structured as following dict
                         {'t': np.array(values),
                              'skeletons' : {<id_sk1>: {'px': np.array(values),
                                                        'py': np.array(values),
                                                        'pz': np.array(values)},
                                             <id_sk2>: {...}, ...
                                             }
                         }
    :param y_frames: positions of y_frames point in numpy format structured as following dict
                         {'t': np.array(values),
                              'skeletons' : {<id_sk1>: {'px': np.array(values),
                                                        'py': np.array(values),
                                                        'pz': np.array(values)},
                                             <id_sk2>: {...}, ...
                                             }
                         }
    :param window: window of smoothing
    :param poly: polynomial order of smoothing
    :return: smoothed and interpolated sequences of input points with the same data structure
    """
    x_skeletons = x_frames['skeletons']
    x_t = x_frames['t']
    y_skeletons = y_frames['skeletons']
    y_t = y_frames['t']
    invalid_ids_x = []
    invalid_ids_y = []
    for id_sk in x_skeletons:
        # If id_sk is also in y, proceed with post-processing
        if id_sk in y_skeletons:
            try:
                # Get valid ts of x, first and last on px (should be the same on other coordinates)
                valid_ts_x = np.where(~np.isnan(x_skeletons[id_sk]['px']))
                first_ts_x = valid_ts_x[0][0]
                last_ts_x = valid_ts_x[0][-1]
                # Get valid ts
                ts = x_t[first_ts_x: last_ts_x]
                # Find first and last ts in y_frames, if not present there is IndexError then remove skeleton
                first_ts_y = np.where(y_t == ts[0])[0][0]
                last_ts_y = np.where(y_t == ts[-1])[0][0]
                # Set to nan to values of y outside the x window
                for coord in y_skeletons[id_sk]:  # Iterate over px, py, pz
                    y_skeletons[id_sk][coord][:first_ts_y] = np.nan
                    y_skeletons[id_sk][coord][last_ts_y + 1:] = np.nan
                # Extract skeleton window for x and y
                px_x = x_skeletons[id_sk]['px'][first_ts_x: last_ts_x]
                py_x = x_skeletons[id_sk]['py'][first_ts_x: last_ts_x]
                pz_x = x_skeletons[id_sk]['pz'][first_ts_x: last_ts_x]
                px_y = y_skeletons[id_sk]['px'][first_ts_y: last_ts_y + 1]
                py_y = y_skeletons[id_sk]['py'][first_ts_y: last_ts_y + 1]
                pz_y = y_skeletons[id_sk]['pz'][first_ts_y: last_ts_y + 1]
                # Interpolate and smooth valid points if not error
                px_interp_x, py_interp_x, pz_interp_x = filt.interpolate_points(px_x, py_x, pz_x)
                px_interp_y, py_interp_y, pz_interp_y = filt.interpolate_points(px_y, py_y, pz_y)
                px_smooth_x, py_smooth_x, pz_smooth_x = filt.smooth_points(px_interp_x, py_interp_x, pz_interp_x,
                                                                           smooth_filter=smooth_filter,
                                                                           window=window, poly=poly)
                px_smooth_y, py_smooth_y, pz_smooth_y = filt.smooth_points(px_interp_y, py_interp_y, pz_interp_y,
                                                                           smooth_filter=smooth_filter,
                                                                           window=window, poly=poly)
                # Set new Interpolated and filtered
                x_skeletons[id_sk]['px'][first_ts_x: last_ts_x] = px_smooth_x
                x_skeletons[id_sk]['py'][first_ts_x: last_ts_x] = py_smooth_x
                x_skeletons[id_sk]['pz'][first_ts_x: last_ts_x] = pz_smooth_x
                y_skeletons[id_sk]['px'][first_ts_y: last_ts_y + 1] = px_smooth_y
                y_skeletons[id_sk]['py'][first_ts_y: last_ts_y + 1] = py_smooth_y
                y_skeletons[id_sk]['pz'][first_ts_y: last_ts_y + 1] = pz_smooth_y
                # If error in filtering then remove skeleton from lists
            except Exception:
                invalid_ids_x.append(id_sk)
                invalid_ids_y.append(id_sk)
                continue
        else:
            invalid_ids_x.append(id_sk)
            continue
    # Remove invalid_ids_x
    for id_sk in invalid_ids_x:
        del x_skeletons[id_sk]
    # Remove invalid_ids_y
    for id_sk in invalid_ids_y:
        del y_skeletons[id_sk]
    if verbose >= 1:
        print("Removing", str(len(invalid_ids_x)), "and",  str(len(invalid_ids_y)),
              "skeleton(s) for incompatibility between x and y point sequences")
        print('------------------------------------------------------------')
    x_frames['skeletons'] = x_skeletons
    y_frames['skeletons'] = y_skeletons
    return x_frames, y_frames


def get_directions(x_frames, y_frames, smooth_filter="savgol", window=5, poly=1, verbose=1):
    """ Compute all the directions between x and y points. Assume that every skeleton in x is also present in y after
        the skeleton preprocessing.

    :param smooth_filter: type of filtering, possible values: "savgol", "weiner"
    :param verbose: if >1 print logs
    :param poly: polynomial order of smoothing
    :param x_frames: positions of the dominant point x in numpy format structured as following dict
                         {'t': np.array(values),
                              'skeletons' : {<id_sk1>: {'px': np.array(values),
                                                        'py': np.array(values),
                                                        'pz': np.array(values)},
                                             <id_sk2>: {...}, ...
                                             }
                         }
    :param y_frames: positions of y_frames point in numpy format structured as following dict
                         {'t': np.array(values),
                              'skeletons' : {<id_sk1>: {'px': np.array(values),
                                                        'py': np.array(values),
                                                        'pz': np.array(values)},
                                             <id_sk2>: {...}, ...
                                             }
                         }
    :param window: smoothing window
    :return: x_frames: same format as input (optionally filtered)
             y_frames: same format as input (optionally filtered)
             directions: dictionary of directions in the following format (each of them is a matrix which columns are
             x, y and z, the rows are the timestamps
             {'t': np.array(values),
                  'skeletons' : {<id_sk1>: np.array((ts,3)),
                                 <id_sk2>: ..., ...
                  }
             }
    """
    invalid_ids = []
    directions = {'t': x_frames['t'], 'skeletons': {}}
    # Compute directions
    for id_sk in x_frames['skeletons']:
        try:
            dx = -y_frames['skeletons'][id_sk]['px'] + x_frames['skeletons'][id_sk]['px']
            dy = -y_frames['skeletons'][id_sk]['py'] + x_frames['skeletons'][id_sk]['py']
            dz = -y_frames['skeletons'][id_sk]['pz'] + x_frames['skeletons'][id_sk]['pz']
            # Smooth direction
            dx_smooth, dy_smooth, dz_smooth = filt.smooth_points(dx, dy, dz, smooth_filter=smooth_filter,
                                                                 window=window, poly=poly)
            directions['skeletons'][id_sk] = np.stack((dx_smooth, dy_smooth, dz_smooth), axis=-1)
        # If not possible remove skeleton (error in smoothing)
        except Exception:
            invalid_ids.append(id_sk)
    if verbose >= 1:
        print("Directions computed, removing", str(len(invalid_ids)), "skeleton(s) for invalid calculations.")
        print('------------------------------------------------------------')
    # Remove invalid_ids
    for id_sk in invalid_ids:
        del x_frames['skeletons'][id_sk]
        del y_frames['skeletons'][id_sk]
    return x_frames, y_frames, directions


