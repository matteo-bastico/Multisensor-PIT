import math
import copy
import numpy as np
import pandas as pd

from mpit.utils.conversion import rotation_matrix
from mpit.comparison import compare_accel, compare_accel_der
from scipy.constants import g
from scipy.optimize import linear_sum_assignment


def add_gravity_to_skeletons_accelerations(accelerations, angle=0, verbose=1):
    """

    :param accelerations: dictionary in the following format:
                           {'t': <timestamps>, 
                            'skeletons':{'<id_br1>':{'ax': np.array(values),
                                                     'ay': np.array(values),
                                                     'az': np.array(values)},
                                         '<id_br2>':{'ax': np.array(values),
                                                     'ay': np.array(values),
                                                     'az': np.array(values)},
                                         ... }
                            }
    :param angle: angle of the camera with respect to the ground plane between -90 and 90 degrees
    :param verbose: if >=1 print logs
    :return: dictionary in the same format of the input with added gravity accelerations
    """
    # degree to radiant
    angle_rad = math.radians(angle)
    # default acceleration is in same direction of original y-axis (parallel to the ground pointing down)
    acc_g = [0, -g, 0]
    # rotation axis is -x
    axis = [1, 0, 0]
    # Generate rotation matrix around axis with angle angle_rad
    rot_mat = rotation_matrix(axis, angle_rad)
    # Obtain gravity accelerations components
    acc_g = np.dot(rot_mat, acc_g)
    for id_br in accelerations['skeletons']:
        accelerations['skeletons'][id_br]['ax'] += acc_g[0]
        accelerations['skeletons'][id_br]['ay'] += acc_g[1]
        accelerations['skeletons'][id_br]['az'] += acc_g[2]
    if verbose >= 1:
        print("Gravity added to skeleton accelerations")
        print('------------------------------------------------------------')
    return accelerations


def get_skeleton_accelerations_rotated(accelerations, directions, verbose=1):
    """ Rotate skeleton accelerations based on the directions provided
    
    :param accelerations: dictionary of accelerations in the following format:
                        { 't': <timestamps>, 
                          'skeletons':{'<id_br1>':{'ax': np.array(values),
                                                   'ay': np.array(values),
                                                   'az': np.array(values)},
                                         '<id_br2>':{'ax': np.array(values),
                                                     'ay': np.array(values),
                                                     'az': np.array(values)},
                                         ... }
                        }
    :param directions: dictionary of directions in the following format (each of them is a matrix which columns are
                       x, y and z, the rows are the timestamps
                         {'t': np.array(values),
                              'skeletons' : {<id_sk1>: np.array((ts,3)),
                                             <id_sk2>: ..., ...
                              }
                         }
    
    :param verbose: if >=1 print logs
    :return: dictionary of accelerations in the following format:
             { 't': <timestamps>,
               'skeletons':{'<id_br1>':{'u': np.array(values),
                                        'v': np.array(values),
                                        'w': np.array(values),
                                        'au: np.array(values),
                                        'av': np.array(values),
                                        'aw': np.array(values)},
                                         ... }
            }

    """
    skeletons_directions = directions['skeletons']
    skeletons = {}
    for id_sk in skeletons_directions:
        # Try to follow
        # https://math.stackexchange.com/questions/542801/rotate-3d-coordinate-system-such-that-z-axis-is-parallel-to-a-given-vector
        # Compute magnitudes of bracelet x-directions
        magnitudes = np.linalg.norm(skeletons_directions[id_sk], axis=1)
        # Compute bracelet x-directions normalized
        directions_norm = skeletons_directions[id_sk] / magnitudes[:, None]
        # Compute angles between x-axis of camera and normalized direction of bracelet x-axis
        angles = np.arccos(np.dot(directions_norm, (1, 0, 0)))
        # Compute vector product between x-axis of camera and normalized direction of bracelet x-axis = b
        b = np.cross((1, 0, 0), directions_norm)
        b_magnitudes = np.linalg.norm(b, axis=1)
        b_norm = b / (b_magnitudes[:, None] + np.finfo(float).eps)
        # Now compute the parameters of the quaternion rotation matrix
        q0 = np.cos(angles / 2)
        q1 = np.sin(angles / 2) * b_norm[:, 0]
        q2 = np.sin(angles / 2) * b_norm[:, 1]
        q3 = np.sin(angles / 2) * b_norm[:, 2]
        # Generate the Q matrix 3x3xn where n is the number of frames
        q_mat = np.array((
            (np.square(q0) + np.square(q1) - np.square(q2) - np.square(q3),
             2 * (np.multiply(q1, q2) - np.multiply(q0, q3)),
             2 * (np.multiply(q1, q3) + np.multiply(q0, q2))),
            (2 * (np.multiply(q2, q1) + np.multiply(q0, q3)),
             np.square(q0) - np.square(q1) + np.square(q2) - np.square(q3),
             2 * (np.multiply(q2, q3) - np.multiply(q0, q1))),
            (2 * (np.multiply(q3, q1) - np.multiply(q0, q2)), 2 * (np.multiply(q3, q2) + np.multiply(q0, q1)),
             np.square(q0) - np.square(q1) - np.square(q2) + np.square(q3)
             )))
        # Compute new axis directions
        u = []
        v = []
        w = []
        for i in range(np.shape(q_mat)[2]):
            u.append(np.dot(q_mat[:, :, i], (1, 0, 0)))
            v.append(np.dot(q_mat[:, :, i], (0, 1, 0)))
            w.append(np.dot(q_mat[:, :, i], (0, 0, 1)))
        u = np.array(u)
        v = np.array(v)
        w = np.array(w)
        acc_skeleton = accelerations['skeletons'][id_sk]
        acc_skeleton = np.transpose(np.vstack((acc_skeleton['ax'], acc_skeleton['ay'], acc_skeleton['az'])))
        # Extract accelerations in new coordinates
        au = np.einsum('ij,ij->i', acc_skeleton, u[:-2, :])
        av = np.einsum('ij,ij->i', acc_skeleton, v[:-2, :])
        aw = np.einsum('ij,ij->i', acc_skeleton, w[:-2, :])
        # Save accelerations and also axis
        skeletons[id_sk] = {'u': u, 'v': v, 'w': w, 'au': au, 'av': av, 'aw': aw}
    if verbose >= 1:
        print("Skeleton accelerations rotated correctly according to directions.")
        print('------------------------------------------------------------')
    return {'t': accelerations['t'], 'skeletons': skeletons}


def do_association(rotated_accel, accel_bracelet, weight, verbose=1):
    """

    :param verbose: if >=1 print logs
    :param rotated_accel: dictionary of accelerations in the following format:
                             { 't': <timestamps>,
                               'skeletons':{'<id_br1>':{'u': np.array(values),
                                                        'v': np.array(values),
                                                        'w': np.array(values),
                                                        'au: np.array(values),
                                                        'av': np.array(values),
                                                        'aw': np.array(values)},
                                                         ... }
                            }
    :param accel_bracelet: accelerations: dictionary as
                              {<id_br1>: {'ax': np.array(values),
                                          'ay': np.array(values),
                                          'az': np.array(values),
                                          't': np.array(values)}
                                          }
                              <id_br2>: {...}, ...
                              }
    :param weight: weight for derivative comparison
    :return: list of association in the from
            {'ts_start': ...,
             'ts_end': ...,
             'skeleton_id': ...,
             'bracelet_id': ...}
    """
    associations = []
    # Comparison raw
    normal_mse = compare_accel(rotated_accel, accel_bracelet)
    # Comparison derivative
    der_mse = compare_accel_der(copy.deepcopy(rotated_accel),
                                copy.deepcopy(accel_bracelet))
    # Combine results
    columns = []
    for id_br in accel_bracelet:
        columns.append(id_br)
    rows = []
    for id_sk in normal_mse:
        rows.append(id_sk)
    df_mse = pd.DataFrame(columns=columns, index=rows)
    for id_sk in normal_mse:
        # No probelm in the derivative then the two sets have same elements
        if set(normal_mse[id_sk]) & set(der_mse[id_sk]) == set(normal_mse[id_sk]):
            tot_weight = {k: weight * normal_mse[id_sk].get(k, 0) + (1 - weight) * der_mse[id_sk].get(k, 0) for k in
                          set(normal_mse[id_sk]) & set(der_mse[id_sk])}
            for id_br in tot_weight:
                df_mse.loc[id_sk][id_br] = tot_weight[id_br]
        # Likely problem in bracelets timestamps
        else:
            # Use only normal -> errors in derivatives of bracelet
            tot_weight = {k: normal_mse[id_sk].get(k, 0) for k in set(normal_mse[id_sk])}
            for id_br in tot_weight:
                df_mse.loc[id_sk][id_br] = tot_weight[id_br]
    np_mse = df_mse.to_numpy(dtype=float)
    np_mse = np_mse[:, np.logical_and(~np.isnan(np.array(np_mse)).any(axis=0),
                                      ~np.isinf(np.array(np_mse)).any(axis=0))]
    # If array is empty everything was NaN -> probably error in bracelet timestamps
    if np_mse.size > 0:
        # Hungarian
        row_ind, col_ind = linear_sum_assignment(np_mse)
        # print("Hungarian result:")
        if len(columns) >= len(rows):
            # Same number of sk and bracelets
            for i, (index, row) in enumerate(df_mse.iterrows()):
                # Extract timestamps
                valids = np.where(~np.isnan(rotated_accel['skeletons'][str(index)]['au']))
                valid_ts = rotated_accel['t'][valids]
                ts_start = valid_ts[0]
                ts_end = valid_ts[-1]
                # print("Skeleton %s associated with bracelet %s" % (str(index), str(df_mse.columns[col_ind[i]])))
                associations.append({'ts_start': ts_start, 'ts_end': ts_end,
                                     'skeleton_id': str(index), 'bracelet_id': str(df_mse.columns[col_ind[i]])})
        else:
            # Less bracelets than skeletons
            for row, col in zip(row_ind, col_ind):
                # Extract timestamps
                valids = np.where(~np.isnan(rotated_accel['skeletons'][str(rows[row])]['au']))
                valid_ts = rotated_accel['t'][valids]
                ts_start = valid_ts[0]
                ts_end = valid_ts[-1]
                # print("Skeleton %s associated with bracelet %s" % (str(rows[row]), str(columns[col])))
                associations.append({'ts_start': ts_start, 'ts_end': ts_end,
                                     'skeleton_id': str(rows[row]),
                                     'bracelet_id': str(columns[col])})
    if verbose >= 1:
        print("Association computed with DTW similarities")
        print('------------------------------------------------------------')
    return associations
