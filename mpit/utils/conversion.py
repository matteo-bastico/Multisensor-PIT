import math
import numpy as np

from scipy.signal import savgol_filter


def velocity_from_position(t, pos, window, poly):
    """

    :param t:
    :param pos:
    :param window:
    :param poly:
    :return:
    """
    dt = np.diff(t)
    dpos = np.diff(pos)
    vel = np.divide(dpos, dt)
    # smooth valid values
    valid_vel = np.where(~np.isnan(vel))
    vel_interp = savgol_filter(vel[valid_vel], window, poly, mode='interp')
    vel[valid_vel] = vel_interp
    return vel


def acceleration_from_position(t, pos, window, poly):
    """

    :param t:
    :param pos:
    :param window:
    :param poly:
    :return:
    """
    vel = velocity_from_position(t, pos, window, poly)
    dt = np.diff(t)
    dv = np.diff(vel)
    a = np.divide(dv, dt[:-1])
    valid_a = np.where(~np.isnan(a))
    a_interp = savgol_filter(a[valid_a], window, poly, mode='interp')
    vel[valid_a] = a_interp
    return a


def get_skeletons_point_accelerations(positions_point, window, poly, verbose=1):
    """ Compute accelerations of one skeleton point

    :param verbose: if >=1 logs
    :param positions_point: positions of one point in numpy format structured as following dict
                           {'t': np.array(values),
                              'skeletons' : {<id_sk1>: {'px': np.array(values),
                                                        'py': np.array(values),
                                                        'pz': np.array(values)},
                                             <id_sk2>: {...}, ...
                                             }
                           }
    :param window for smoothing
    :param poly for smoothing
    :return: accelerations of one point in numpy format structured as following dict
             {'t': np.array(values),
                  'skeletons' : {<id_sk1>: {'ax': np.array(values),
                                            'ay': np.array(values),
                                            'az': np.array(values)},
                                 <id_sk2>: {...}, ...
                                 }
              }
    """
    # Timestamps
    t = positions_point['t']
    # Skeletons
    skeletons = positions_point['skeletons']
    # Last two are lost for differentiation
    skeletons_accel = {'t': t[:-2]}
    accel_dict = {}
    # For each skeleton compute the accelerations of the point in x, y, z
    for id_sk, skeleton in skeletons.items():
        accel_dict[id_sk] = {}
        for axis, vals in skeleton.items():
            # Otherwise, filtering is not possible
            if len(vals) > window:
                # Generate name for accelerations field
                name = axis.replace('p', 'a')
                accel_dict[id_sk][name] = acceleration_from_position(t, vals, window, poly)
    skeletons_accel['skeletons'] = accel_dict
    if verbose >= 1:
        print("Acceleration correctly computed for skeletons points.")
        print('------------------------------------------------------------')
    return skeletons_accel


def rotation_matrix(axis, theta):
    """

    :param axis:
    :param theta:
    :return: the rotation matrix associated with counterclockwise rotation about
    the given axis by theta radians.
    """
    axis = np.asarray(axis)
    axis = axis / math.sqrt(np.dot(axis, axis))
    a = math.cos(theta / 2.0)
    b, c, d = -axis * math.sin(theta / 2.0)
    aa, bb, cc, dd = a * a, b * b, c * c, d * d
    bc, ad, ac, ab, bd, cd = b * c, a * d, a * c, a * b, b * d, c * d
    return np.array([[aa + bb - cc - dd, 2 * (bc + ad), 2 * (bd - ac)],
                     [2 * (bc - ad), aa + cc - bb - dd, 2 * (cd + ab)],
                     [2 * (bd + ac), 2 * (cd - ab), aa + dd - bb - cc]])


def angles_with_axis(vectors):
    """

    :param vectors:
    :return:
    """
    magnitude = np.linalg.norm(vectors, axis=1)
    angles = np.arccos(vectors / magnitude[:, None])
    return angles
